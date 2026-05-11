import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import train_phase8b_policy_models as train8b


PHASE8A_ROOT = Path("outputs/phase8a_policy_dataset")
MODEL_DIR = Path("outputs/phase8b_policy_training/models")
SMOKE_ROOT = Path("outputs/asmag_tr_controller_online_guarded_cdnet_smoke")
OUTPUT_ROOT = Path("outputs/phase8c_shadow_calibration")
HARD_VIDEOS = {"continuousPan", "twoPositionPTZCam", "bridgeEntry", "cubicle"}
THRESHOLDS = np.round(np.arange(0.50, 1.00, 0.01), 2)


def load_artifacts(model_dir):
    manifest_path = model_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = {}
    for target, info in manifest.get("models", {}).items():
        path = Path(info.get("path", ""))
        if not path.exists():
            path = model_dir / f"{target}.pkl"
        if not path.exists():
            continue
        with path.open("rb") as f:
            artifacts[target] = pickle.load(f)
    return manifest, artifacts


def class_scores(artifact, x, class_label):
    pipe = artifact.get("pipeline")
    if pipe is None:
        return np.zeros(len(x), dtype=float)
    if hasattr(pipe, "predict_proba"):
        try:
            classes = [str(c) for c in pipe.named_steps["model"].classes_]
            probs = pipe.predict_proba(x)
            if str(class_label) in classes:
                return probs[:, classes.index(str(class_label))].astype(float)
        except Exception:
            pass
    pred = pd.Series(pipe.predict(x)).astype(str)
    return pred.eq(str(class_label)).astype(float).to_numpy()


def binary_metrics(y_true, y_pred):
    y_true = pd.Series(y_true).astype(int).to_numpy()
    y_pred = pd.Series(y_pred).astype(int).to_numpy()
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def threshold_sweep(scores, labels, threshold_mode="positive_above"):
    labels = pd.Series(labels).fillna(0).astype(int)
    rows = []
    for threshold in THRESHOLDS:
        if threshold_mode == "negative_below":
            pred = pd.Series(scores).lt(threshold).astype(int)
        else:
            pred = pd.Series(scores).ge(threshold).astype(int)
        row = {
            "threshold": float(threshold),
            "flag_rate": float(pred.mean()),
            "positive_labels": int(labels.sum()),
            "rows": int(len(labels)),
        }
        row.update(binary_metrics(labels, pred))
        rows.append(row)
    return pd.DataFrame(rows)


def add_smoke_unsafe_columns(sweep, smoke_root):
    paths = sorted((smoke_root / "raw_results").rglob("ASMAG_TR_CONTROLLER_ONLINE_GUARDED/frame_metrics.csv"))
    if not paths:
        return sweep
    frames = []
    for path in paths:
        df = pd.read_csv(path)
        df["category"] = path.parts[-4]
        df["video"] = path.parts[-3]
        frames.append(df)
    smoke = pd.concat(frames, ignore_index=True)
    if "ai_unsafe_action_score" not in smoke.columns:
        return sweep
    for col in [
        "closed_empty_blocked_final",
        "reuse_blocked_final",
        "lightweight_blocked_final",
        "ptz_closed_empty_kill_active",
        "closed_empty_blocked_under_ptz",
    ]:
        if col not in smoke.columns:
            smoke[col] = 0
        smoke[col] = pd.to_numeric(smoke[col], errors="coerce").fillna(0.0)
    known = (
        smoke["closed_empty_blocked_final"].gt(0)
        | smoke["reuse_blocked_final"].gt(0)
        | smoke["lightweight_blocked_final"].gt(0)
        | smoke["ptz_closed_empty_kill_active"].gt(0)
        | smoke["closed_empty_blocked_under_ptz"].gt(0)
    )
    hard = smoke["video"].astype(str).isin(HARD_VIDEOS)
    smoke_scores = pd.to_numeric(smoke["ai_unsafe_action_score"], errors="coerce").fillna(0.0)
    smoke_rows = []
    for threshold in THRESHOLDS:
        pred = smoke_scores.ge(threshold)
        smoke_rows.append({
            "threshold": float(threshold),
            "smoke_flag_rate": float(pred.mean()),
            "smoke_known_recall": float(pred[known].mean()) if known.any() else np.nan,
            "smoke_hard_video_recall": float(pred[hard].mean()) if hard.any() else np.nan,
            "smoke_known_events": int(known.sum()),
            "smoke_hard_frames": int(hard.sum()),
        })
    return sweep.merge(pd.DataFrame(smoke_rows), on="threshold", how="left")


def choose_unsafe_threshold(sweep):
    work = sweep.copy()
    if "smoke_known_recall" in work.columns and work["smoke_known_recall"].notna().any():
        candidates = work[work["smoke_known_recall"].ge(0.95)].copy()
        if not candidates.empty:
            return candidates.sort_values(["smoke_flag_rate", "threshold"], ascending=[True, False]).iloc[0]
    candidates = work[work["recall"].ge(0.95)].copy()
    if not candidates.empty:
        return candidates.sort_values(["flag_rate", "f1", "threshold"], ascending=[True, False, False]).iloc[0]
    return work.sort_values(["f1", "recall", "threshold"], ascending=[False, False, False]).iloc[0]


def target_frame(data, target, artifact, max_rows):
    target_df = train8b.prepare_target_df(data, target, max_rows).copy()
    features = artifact.get("features", [])
    x = target_df[features].apply(pd.to_numeric, errors="coerce")
    return target_df, x


def calibrate_targets(data, artifacts, output_root, max_rows, smoke_root):
    recommendations = []
    sweep_specs = {
        "unsafe_action": ("unsafe_threshold_sweep.csv", "1", "positive_above", "unsafe_flag", False),
        "detector_needed": ("detector_threshold_sweep.csv", "1", "positive_above", "detector_request", False),
        "reuse_allowed": ("reuse_threshold_sweep.csv", "1", "negative_below", "reuse_block", True),
        "lightweight_allowed": ("lightweight_threshold_sweep.csv", "1", "negative_below", "lightweight_block", True),
        "detector_floor_needed": ("detector_floor_threshold_sweep.csv", "1", "positive_above", "detector_floor_request", False),
    }
    sweeps = {}
    for target, (filename, class_label, mode, decision_name, invert_label) in sweep_specs.items():
        if target not in artifacts or target not in data.columns:
            continue
        target_df, x = target_frame(data, target, artifacts[target], max_rows)
        scores = class_scores(artifacts[target], x, class_label)
        labels = target_df[target].fillna(0).astype(int)
        if invert_label:
            labels = 1 - labels
        sweep = threshold_sweep(scores, labels, threshold_mode=mode)
        if target == "unsafe_action":
            sweep = add_smoke_unsafe_columns(sweep, smoke_root)
            best = choose_unsafe_threshold(sweep)
        else:
            viable = sweep[sweep["recall"].ge(0.90)]
            best = viable.sort_values(["f1", "threshold"], ascending=[False, False]).iloc[0] if not viable.empty else sweep.sort_values("f1", ascending=False).iloc[0]
        sweep.to_csv(output_root / filename, index=False)
        sweeps[target] = sweep
        recommendations.append({
            "target": target,
            "decision_name": decision_name,
            "recommended_threshold": float(best["threshold"]),
            "offline_flag_rate": float(best["flag_rate"]),
            "offline_precision": float(best["precision"]),
            "offline_recall": float(best["recall"]),
            "offline_f1": float(best["f1"]),
            "offline_false_positive_rate": float(best["false_positive_rate"]),
            "smoke_flag_rate": float(best.get("smoke_flag_rate", np.nan)),
            "smoke_known_recall": float(best.get("smoke_known_recall", np.nan)),
            "smoke_hard_video_recall": float(best.get("smoke_hard_video_recall", np.nan)),
        })

    if "risk_class" in artifacts and "risk_class" in data.columns:
        target_df, x = target_frame(data, "risk_class", artifacts["risk_class"], max_rows)
        scores = class_scores(artifacts["risk_class"], x, "unsafe")
        labels = target_df["risk_class"].fillna("").astype(str).eq("unsafe").astype(int)
        sweep = threshold_sweep(scores, labels, threshold_mode="positive_above")
        sweep.to_csv(output_root / "risk_class_unsafe_threshold_sweep.csv", index=False)
        best = sweep[sweep["recall"].ge(0.90)]
        best = best.sort_values(["flag_rate", "f1"], ascending=[True, False]).iloc[0] if not best.empty else sweep.sort_values("f1", ascending=False).iloc[0]
        recommendations.append({
            "target": "risk_class",
            "decision_name": "risk_unsafe_flag",
            "recommended_threshold": float(best["threshold"]),
            "offline_flag_rate": float(best["flag_rate"]),
            "offline_precision": float(best["precision"]),
            "offline_recall": float(best["recall"]),
            "offline_f1": float(best["f1"]),
            "offline_false_positive_rate": float(best["false_positive_rate"]),
            "smoke_flag_rate": np.nan,
            "smoke_known_recall": np.nan,
            "smoke_hard_video_recall": np.nan,
        })

    rec_df = pd.DataFrame(recommendations)
    rec_df.to_csv(output_root / "calibration_recommendations.csv", index=False)
    return rec_df, sweeps


def derive_subrisk_labels(data):
    label = data.get("unsafe_action_label", pd.Series("", index=data.index)).fillna("").astype(str)
    action = data.get("action_bucket", pd.Series("", index=data.index)).fillna("").astype(str)
    category = data.get("category", pd.Series("", index=data.index)).fillna("").astype(str)
    out = pd.DataFrame(index=data.index)
    out["closed_empty_unsafe"] = label.eq("closed_empty_during_event_or_motion") | (
        action.eq("CLOSED_EMPTY")
        & (
            train8b.boolish(data.get("active_event_memory"), index=data.index).gt(0)
            | train8b.boolish(data.get("global_motion_proxy"), index=data.index).gt(0.5)
        )
    )
    out["reuse_unsafe"] = label.eq("reuse_under_low_trust") | (
        action.eq("REUSE_ACC")
        & (
            train8b.boolish(data.get("reuse_blocked_final"), index=data.index).gt(0)
            | train8b.boolish(data.get("geometry_reuse_blocked"), index=data.index).gt(0)
            | train8b.boolish(data.get("motion_comp_compensated_trust_low"), index=data.index).gt(0)
        )
    )
    out["lightweight_p3_unsafe"] = label.eq("lightweight_p3_under_ptz") | (
        action.eq("LIGHTWEIGHT_MASK_P3_FALLBACK") & category.eq("PTZ")
    )
    out["legacy_cadence_unsafe"] = label.eq("legacy_safe_without_detector_cadence") | (
        action.eq("LEGACY_SAFE_P3_GUARD")
        & train8b.boolish(data.get("ptz_detector_floor_cadence_allowed"), index=data.index).eq(0)
        & category.eq("PTZ")
    )
    return out.astype(int)


def probe_subrisks(data, features, output_root, max_rows):
    labels = derive_subrisk_labels(data)
    probe_rows = []
    importance_rows = []
    x_all = data[features].apply(pd.to_numeric, errors="coerce")
    groups = train8b.key_series(data)
    for target in labels.columns:
        y_all = labels[target]
        positives = int(y_all.sum())
        if positives < 20 or y_all.nunique() < 2:
            probe_rows.append({
                "subrisk": target,
                "model": "skipped",
                "rows": int(len(y_all)),
                "positive_labels": positives,
                "reason": "insufficient positive labels",
            })
            continue
        work = data.copy()
        work[target] = y_all
        sample = train8b.target_aware_sample(work, target, max_rows)
        x = sample[features].apply(pd.to_numeric, errors="coerce")
        y = sample[target].astype(int)
        sample_groups = train8b.key_series(sample)
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=8)
        train_idx, test_idx = next(splitter.split(x, y, groups=sample_groups))
        models = {
            "logistic_regression": LogisticRegression(max_iter=300, class_weight="balanced"),
            "decision_tree": DecisionTreeClassifier(max_depth=5, min_samples_leaf=20, class_weight="balanced", random_state=8),
            "random_forest": RandomForestClassifier(n_estimators=25, max_depth=6, min_samples_leaf=20, class_weight="balanced", random_state=8, n_jobs=1),
        }
        for model_name, model in models.items():
            pipe = Pipeline([
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler(with_mean=False)),
                ("model", model),
            ])
            pipe.fit(x.iloc[train_idx], y.iloc[train_idx])
            pred = pipe.predict(x.iloc[test_idx])
            precision, recall, f1, _ = precision_recall_fscore_support(
                y.iloc[test_idx], pred, average="binary", zero_division=0
            )
            probe_rows.append({
                "subrisk": target,
                "model": model_name,
                "rows": int(len(sample)),
                "positive_labels": int(y.sum()),
                "test_rows": int(len(test_idx)),
                "test_positive_labels": int(y.iloc[test_idx].sum()),
                "accuracy": float((pred == y.iloc[test_idx]).mean()),
                "balanced_accuracy": float(balanced_accuracy_score(y.iloc[test_idx], pred)),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
            })
            fitted = pipe.named_steps["model"]
            if hasattr(fitted, "feature_importances_"):
                importances = fitted.feature_importances_
            elif hasattr(fitted, "coef_"):
                importances = np.abs(fitted.coef_[0])
            else:
                importances = np.zeros(len(features))
            top_idx = np.argsort(importances)[::-1][:20]
            for idx in top_idx:
                if importances[idx] <= 0:
                    continue
                importance_rows.append({
                    "subrisk": target,
                    "model": model_name,
                    "feature": features[idx],
                    "importance": float(importances[idx]),
                })
    probe = pd.DataFrame(probe_rows)
    importance = pd.DataFrame(importance_rows)
    probe.to_csv(output_root / "subrisk_model_probe.csv", index=False)
    importance.to_csv(output_root / "subrisk_feature_importance.csv", index=False)
    return probe, importance


def write_report(output_root, recommendations, subrisk_probe):
    unsafe = recommendations[recommendations["target"].eq("unsafe_action")]
    unsafe_row = unsafe.iloc[0].to_dict() if not unsafe.empty else {}
    lines = [
        "# Phase 8C-1B Shadow Calibration Report",
        "",
        "This is an offline calibration analysis only. No AI intervention is enabled.",
        "",
        "## Recommended Thresholds",
        "",
        recommendations.to_markdown(index=False) if not recommendations.empty else "No recommendations generated.",
        "",
        "## Unsafe Calibration",
        "",
        f"Recommended unsafe threshold: `{unsafe_row.get('recommended_threshold', 'n/a')}`.",
        f"Offline flag rate at recommendation: `{unsafe_row.get('offline_flag_rate', np.nan):.4f}`.",
        f"Smoke flag rate at recommendation: `{unsafe_row.get('smoke_flag_rate', np.nan):.4f}`.",
        f"Smoke known-event recall at recommendation: `{unsafe_row.get('smoke_known_recall', np.nan):.4f}`.",
        f"Smoke hard-video recall at recommendation: `{unsafe_row.get('smoke_hard_video_recall', np.nan):.4f}`.",
        "",
        "## Sub-risk Probe",
        "",
        subrisk_probe.to_markdown(index=False) if not subrisk_probe.empty else "No sub-risk probe rows generated.",
        "",
        "## Decision",
        "",
        "Phase 8C-2 limited intervention remains blocked unless smoke rerun confirms non-saturated unsafe flags, low missing features, and acceptable latency.",
    ]
    (output_root / "calibration_report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase8a-root", default=str(PHASE8A_ROOT))
    parser.add_argument("--model-dir", default=str(MODEL_DIR))
    parser.add_argument("--smoke-root", default=str(SMOKE_ROOT))
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    parser.add_argument("--max-rows", type=int, default=120000)
    parser.add_argument("--subrisk-max-rows", type=int, default=60000)
    args = parser.parse_args()

    smoke_root = Path(args.smoke_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    _, artifacts = load_artifacts(Path(args.model_dir))
    data, _, _, _, _ = train8b.load_phase8a(Path(args.phase8a_root))
    features = next(iter(artifacts.values())).get("features", train8b.choose_features(data))

    recommendations, _ = calibrate_targets(data, artifacts, output_root, args.max_rows, smoke_root)
    subrisk_probe, _ = probe_subrisks(data, features, output_root, args.subrisk_max_rows)
    write_report(output_root, recommendations, subrisk_probe)
    print(f"[DONE] wrote Phase 8C shadow calibration under {output_root}")


if __name__ == "__main__":
    main()
