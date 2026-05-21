#!/usr/bin/env python
"""Train lightweight Phase 8C event/foreground risk shadows.

This is post-hoc research only. Labels may use evaluation metrics, but model
features are limited to runtime-observable controller/guard signals.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


SMOKE_ROOT = Path("outputs/asmag_tr_controller_online_guarded_cdnet_smoke")
OUT_ROOT = Path("outputs/phase8c_event_foreground_risk")
GUARDED_PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
RANDOM_STATE = 8

TARGETS = [
    "event_foreground_risk",
    "foreground_loss_risk",
    "event_continuity_risk",
    "detector_refresh_needed_for_event",
]

FEATURES = [
    "active_event_memory",
    "foreground_risk",
    "global_motion_proxy",
    "gmq_event_continuity_risk",
    "gmq_background_reliability",
    "gmq_temporal_consistency",
    "gmq_confident_empty_evidence",
    "frames_since_last_detector",
    "frames_since_active_prediction",
    "reuse_age",
    "reuse_confidence",
    "reused_prediction",
    "reuse_success_rate",
    "reuse_failure_rate",
    "candidate_P3_area_ratio",
    "candidate_ACC_area_ratio",
    "candidate_FAST_area_ratio",
    "candidate_P3_quality",
    "candidate_ACC_quality",
    "candidate_FAST_quality",
    "candidate_P3_temporal_iou",
    "candidate_ACC_temporal_iou",
    "low_light_guard_active",
    "illumination_proxy",
    "final_sanitizer_active",
    "closed_empty_blocked_final",
    "closed_empty_blocked_under_ptz",
    "event_closed_empty_attempt_count",
    "event_closed_empty_blocked_count",
    "event_fn_risk_frames",
    "reuse_blocked_final",
    "lightweight_blocked_final",
    "ptz_closed_empty_kill_active",
    "low_framerate_detector_floor_active",
    "ptz_detector_floor_active",
    "motion_comp_compensated_trust_low",
    "geometry_trust_score",
    "continuous_pan_signature_active",
]

USECOLS = [
    "category",
    "video",
    "pipeline",
    "frame_id",
    "raw_frame_id",
    "evaluated_index",
    "action_label",
    "selected_mode",
    "Event_State",
    "Recall",
    "FMeasure",
] + FEATURES


def read_existing_columns(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        return fh.readline().strip().split(",")


def read_guarded_frames(root: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(root.glob(f"raw_results/*/*/{GUARDED_PIPELINE}/frame_metrics.csv")):
        existing = set(read_existing_columns(path))
        cols = [col for col in USECOLS if col in existing]
        if cols:
            frames.append(pd.read_csv(path, usecols=cols, low_memory=False))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    for col in USECOLS:
        if col not in df.columns:
            df[col] = 0
    for col in df.columns:
        if col in {"category", "video", "pipeline", "action_label", "selected_mode", "Event_State"}:
            df[col] = df[col].fillna("").astype(str)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def derive_labels(df: pd.DataFrame) -> pd.DataFrame:
    recall = df["Recall"].astype(float)
    fmeasure = df["FMeasure"].astype(float)
    event_state = df["Event_State"].astype(str)
    active_event = df["active_event_memory"].gt(0)
    foreground = df["foreground_risk"].gt(0.5)
    strong_foreground = df["foreground_risk"].gt(0.8)
    quality_loss = recall.lt(0.70) | fmeasure.lt(0.35) | event_state.eq("FN")
    known_guard = (
        df["closed_empty_blocked_final"].gt(0)
        | df["reuse_blocked_final"].gt(0)
        | df["lightweight_blocked_final"].gt(0)
        | df["ptz_closed_empty_kill_active"].gt(0)
        | df["closed_empty_blocked_under_ptz"].gt(0)
    )
    stale_detector = df["frames_since_last_detector"].gt(4)
    stale_reuse = df["reuse_age"].gt(3) | df["reuse_confidence"].lt(0.35)
    event_continuity = df["gmq_event_continuity_risk"].gt(0.35) | df["event_fn_risk_frames"].gt(0)
    closed_empty_event = (
        df["event_closed_empty_attempt_count"].gt(0)
        | df["event_closed_empty_blocked_count"].gt(0)
        | df["closed_empty_blocked_final"].gt(0)
    )

    labels = pd.DataFrame(index=df.index)
    labels["event_foreground_risk"] = known_guard | (
        (active_event | event_continuity)
        & strong_foreground
        & (quality_loss | closed_empty_event | df["event_fn_risk_frames"].gt(0))
    )
    labels["foreground_loss_risk"] = foreground & active_event & (
        quality_loss
        | known_guard
        | df["closed_empty_blocked_final"].gt(0)
        | df["final_sanitizer_active"].gt(0)
    )
    labels["event_continuity_risk"] = known_guard | (
        (active_event | event_continuity)
        & (quality_loss | stale_detector | df["frames_since_active_prediction"].gt(4))
    )
    labels["detector_refresh_needed_for_event"] = known_guard | (
        (active_event | event_continuity | strong_foreground)
        & (stale_detector | quality_loss | closed_empty_event | df["event_fn_risk_frames"].gt(0))
    )
    return labels.astype(int)


def model_defs() -> dict[str, object | None]:
    return {
        "majority_baseline": None,
        "logistic_regression": LogisticRegression(max_iter=500, class_weight="balanced", solver="lbfgs"),
        "shallow_decision_tree": DecisionTreeClassifier(
            max_depth=4,
            min_samples_leaf=20,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
    }


def make_pipeline(model: object) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler(with_mean=False)),
        ("model", model),
    ])


def binary_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    y_true = pd.Series(y_true).astype(int)
    y_pred = pd.Series(y_pred).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    balanced = balanced_accuracy_score(y_true, y_pred) if y_true.nunique() > 1 else accuracy_score(y_true, y_pred)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def threshold_metrics(y_true: pd.Series, score: np.ndarray, threshold: float) -> dict[str, float]:
    pred = pd.Series(score >= threshold, index=y_true.index).astype(int)
    metrics = binary_metrics(y_true, pred)
    metrics["threshold"] = float(threshold)
    metrics["flag_rate"] = float(pred.mean())
    return metrics


def threshold_grid(scores: np.ndarray) -> list[float]:
    base = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    qs = pd.Series(scores).quantile([0.25, 0.5, 0.75, 0.9, 0.95]).tolist()
    return sorted({round(float(v), 6) for v in base + qs if 0 <= float(v) <= 1})


def score_positive(pipe: Pipeline, x: pd.DataFrame) -> np.ndarray:
    probs = pipe.predict_proba(x)
    classes = list(pipe.named_steps["model"].classes_)
    idx = classes.index(1)
    return probs[:, idx]


def evaluate_models(df: pd.DataFrame, labels: pd.DataFrame, out: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    models = model_defs()
    x_all = df[FEATURES].apply(pd.to_numeric, errors="coerce")
    videos = sorted(df["video"].unique())
    result_rows = []
    threshold_rows = []
    importance_rows = []
    score_frame = df[["category", "video", "frame_id", "raw_frame_id", "evaluated_index"]].copy()
    recommendations = []
    runtime_models = {}

    for target in TARGETS:
        y_all = labels[target].astype(int)
        best_candidate = None
        for test_video in videos:
            train_mask = ~df["video"].eq(test_video)
            test_mask = df["video"].eq(test_video)
            y_train = y_all[train_mask]
            y_test = y_all[test_mask]
            if len(y_test) == 0 or y_train.nunique() < 2:
                continue
            for model_name, model in models.items():
                if model is None:
                    majority = int(y_train.value_counts().idxmax())
                    pred = pd.Series([majority] * int(test_mask.sum()), index=y_test.index)
                    row = {
                        "target": target,
                        "split_name": "leave_one_video",
                        "heldout_video": test_video,
                        "model": model_name,
                        "train_rows": int(train_mask.sum()),
                        "test_rows": int(test_mask.sum()),
                        "train_positive_labels": int(y_train.sum()),
                        "test_positive_labels": int(y_test.sum()),
                    }
                    row.update(binary_metrics(y_test, pred))
                    result_rows.append(row)
                    continue

                pipe = make_pipeline(model)
                pipe.fit(x_all.loc[train_mask], y_train)
                score = score_positive(pipe, x_all.loc[test_mask])
                pred = (score >= 0.5).astype(int)
                row = {
                    "target": target,
                    "split_name": "leave_one_video",
                    "heldout_video": test_video,
                    "model": model_name,
                    "train_rows": int(train_mask.sum()),
                    "test_rows": int(test_mask.sum()),
                    "train_positive_labels": int(y_train.sum()),
                    "test_positive_labels": int(y_test.sum()),
                }
                row.update(binary_metrics(y_test, pd.Series(pred, index=y_test.index)))
                result_rows.append(row)
                for threshold in threshold_grid(score):
                    trow = {
                        "target": target,
                        "split_name": "leave_one_video",
                        "heldout_video": test_video,
                        "model": model_name,
                    }
                    trow.update(threshold_metrics(y_test, score, threshold))
                    threshold_rows.append(trow)
                    candidate = trow.copy()
                    candidate["score"] = candidate["f1"] + 0.5 * candidate["recall"] - 0.2 * candidate["flag_rate"]
                    if best_candidate is None or candidate["score"] > best_candidate["score"]:
                        best_candidate = candidate

        # Fit final model for per-frame scores and importance.
        target_results = pd.DataFrame(result_rows)
        target_model_rows = target_results[
            target_results["target"].eq(target)
            & target_results["model"].isin(["logistic_regression", "shallow_decision_tree"])
        ]
        if target_model_rows.empty:
            recommended_model = "logistic_regression"
        else:
            avg = target_model_rows.groupby("model", as_index=False)[["f1", "recall", "balanced_accuracy"]].mean()
            recommended_model = avg.sort_values(["f1", "recall", "balanced_accuracy"], ascending=False).iloc[0]["model"]
        threshold = float(best_candidate["threshold"]) if best_candidate else 0.5
        model = models[recommended_model]
        pipe = make_pipeline(model)
        pipe.fit(x_all, y_all)
        score_frame[f"{target}_score"] = score_positive(pipe, x_all)
        score_frame[f"{target}_label"] = y_all.values
        threshold = choose_runtime_threshold(
            df,
            y_all,
            score_frame[f"{target}_score"],
            target,
            fallback=threshold,
        )
        score_frame[f"{target}_pred"] = (score_frame[f"{target}_score"] >= threshold).astype(int)
        runtime_models[target] = {
            "pipeline": pipe,
            "feature_names": list(FEATURES),
            "features": list(FEATURES),
            "target": target,
            "model_type": recommended_model,
            "threshold": threshold,
            "positive_class": "1",
            "positive_class_index": list(pipe.named_steps["model"].classes_).index(1),
            "classes": [str(c) for c in pipe.named_steps["model"].classes_],
        }
        recommendations.append({
            "target": target,
            "recommended_model": recommended_model,
            "recommended_threshold": threshold,
            "positive_labels": int(y_all.sum()),
            "positive_rate": float(y_all.mean()),
            "selection_note": "leave-one-video F1/recall/flag-rate lightweight selection",
        })
        estimator = pipe.named_steps["model"]
        if hasattr(estimator, "coef_"):
            vals = estimator.coef_[0]
        elif hasattr(estimator, "feature_importances_"):
            vals = estimator.feature_importances_
        else:
            vals = np.zeros(len(FEATURES))
        for feature, value in zip(FEATURES, vals):
            importance_rows.append({
                "target": target,
                "model": recommended_model,
                "feature": feature,
                "importance": float(value),
                "abs_importance": float(abs(value)),
            })

    results = pd.DataFrame(result_rows)
    thresholds = pd.DataFrame(threshold_rows)
    recommendations_df = pd.DataFrame(recommendations)
    importance = pd.DataFrame(importance_rows).sort_values(["target", "abs_importance"], ascending=[True, False])
    export_runtime_models(out, runtime_models)
    return results, thresholds, importance, recommendations_df, score_frame


def export_runtime_models(out: Path, runtime_models: dict[str, dict]) -> None:
    model_dir = out / "runtime_models"
    model_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "phase": "8C-2-event-foreground-risk",
        "runtime_model_set": "event_foreground_lightweight",
        "features": list(FEATURES),
        "models": {},
        "shadow_or_intervention_only": True,
    }
    for target, artifact in runtime_models.items():
        path = model_dir / f"{target}.pkl"
        with path.open("wb") as fh:
            pickle.dump(artifact, fh)
        manifest["models"][target] = {
            "target": target,
            "model_type": artifact["model_type"],
            "path": str(path),
            "classes": artifact["classes"],
            "positive_class": artifact["positive_class"],
            "positive_class_index": artifact["positive_class_index"],
            "threshold": artifact["threshold"],
        }
    (model_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def choose_runtime_threshold(
    df: pd.DataFrame,
    labels: pd.Series,
    scores: pd.Series,
    target: str,
    fallback: float,
) -> float:
    known = df["known_guarded_safety_event"].astype(bool)
    cubicle_known = df["video"].eq("cubicle") & known
    normal = ~known
    rows = []
    for threshold in threshold_grid(scores.to_numpy()):
        flags = scores.ge(threshold)
        metrics = threshold_metrics(labels, scores.to_numpy(), threshold)
        rows.append({
            "threshold": threshold,
            "label_f1": metrics["f1"],
            "label_recall": metrics["recall"],
            "known_recall": float(flags[known].mean()) if known.any() else 0.0,
            "cubicle_recall": float(flags[cubicle_known].mean()) if cubicle_known.any() else 0.0,
            "normal_warning_rate": float(flags[normal].mean()) if normal.any() else 0.0,
            "flag_rate": float(flags.mean()),
        })
    table = pd.DataFrame(rows)
    if table.empty:
        return fallback
    eligible = table[
        table["known_recall"].ge(0.80)
        & table["cubicle_recall"].ge(0.80)
        & table["normal_warning_rate"].le(0.45)
    ]
    if eligible.empty:
        eligible = table[
            table["known_recall"].ge(0.75)
            & table["cubicle_recall"].ge(0.75)
        ]
    if eligible.empty:
        eligible = table.sort_values(
            ["cubicle_recall", "known_recall", "normal_warning_rate"],
            ascending=[False, False, True],
        ).head(1)
    best = eligible.sort_values(
        ["normal_warning_rate", "flag_rate", "label_f1"],
        ascending=[True, True, False],
    ).iloc[0]
    return float(best["threshold"])


def cubicle_analysis(df: pd.DataFrame, score_frame: pd.DataFrame, recs: pd.DataFrame) -> pd.DataFrame:
    merged = df[["category", "video", "frame_id", "known_guarded_safety_event", "foreground_risk", "active_event_memory", "global_motion_proxy"]].copy()
    merged = pd.concat([merged.reset_index(drop=True), score_frame.drop(columns=["category", "video", "frame_id", "raw_frame_id", "evaluated_index"]).reset_index(drop=True)], axis=1)
    rows = []
    for target in TARGETS:
        thr = float(recs.loc[recs["target"].eq(target), "recommended_threshold"].iloc[0])
        score_col = f"{target}_score"
        flags = merged[score_col].ge(thr)
        for scope_name, mask in {
            "cubicle": merged["video"].eq("cubicle"),
            "bridgeEntry": merged["video"].eq("bridgeEntry"),
            "continuousPan": merged["video"].eq("continuousPan"),
            "non_ptz": ~merged["category"].eq("PTZ"),
        }.items():
            scope = merged[mask]
            if scope.empty:
                continue
            scope_flags = flags[mask]
            known = scope["known_guarded_safety_event"].astype(bool)
            normal = ~known
            rows.append({
                "target": target,
                "scope": scope_name,
                "threshold": thr,
                "frames": int(len(scope)),
                "known_safety_events": int(known.sum()),
                "recall_on_known_events": float(scope_flags[known].mean()) if known.any() else 0.0,
                "normal_frame_warning_rate": float(scope_flags[normal].mean()) if normal.any() else 0.0,
                "all_frame_warning_rate": float(scope_flags.mean()),
                "mean_score_known_events": float(scope.loc[known, score_col].mean()) if known.any() else 0.0,
                "mean_foreground_risk_known_events": float(scope.loc[known, "foreground_risk"].mean()) if known.any() else 0.0,
                "active_event_rate_known_events": float(scope.loc[known, "active_event_memory"].gt(0).mean()) if known.any() else 0.0,
            })
    return pd.DataFrame(rows)


def add_known_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["known_guarded_safety_event"] = (
        out["closed_empty_blocked_final"].gt(0)
        | out["reuse_blocked_final"].gt(0)
        | out["lightweight_blocked_final"].gt(0)
        | out["ptz_closed_empty_kill_active"].gt(0)
        | out["closed_empty_blocked_under_ptz"].gt(0)
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=SMOKE_ROOT)
    parser.add_argument("--out", type=Path, default=OUT_ROOT)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    df = read_guarded_frames(args.root)
    if df.empty:
        raise SystemExit(f"No guarded frame metrics found under {args.root}")
    df = add_known_flags(df)
    labels = derive_labels(df)
    train_df = pd.concat([df, labels], axis=1)

    results, thresholds, importance, recs, scores = evaluate_models(train_df, labels, args.out)
    cubicle = cubicle_analysis(train_df, scores, recs)

    results.to_csv(args.out / "event_foreground_model_results.csv", index=False)
    thresholds.to_csv(args.out / "event_foreground_threshold_sweep.csv", index=False)
    importance.to_csv(args.out / "event_foreground_feature_importance.csv", index=False)
    recs.to_csv(args.out / "event_foreground_runtime_recommendation.csv", index=False)
    cubicle.to_csv(args.out / "cubicle_event_foreground_analysis.csv", index=False)
    scores.to_csv(args.out / "event_foreground_frame_scores.csv", index=False)

    print(f"[DONE] wrote event/foreground model outputs to {args.out}")
    print(recs.to_string(index=False))


if __name__ == "__main__":
    main()
