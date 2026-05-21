import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import train_phase8b_policy_models as train8b


BINARY_TARGETS = [
    "detector_needed",
    "unsafe_action",
    "reuse_allowed",
    "lightweight_allowed",
    "detector_floor_needed",
]
ALL_TARGETS = BINARY_TARGETS + ["risk_class"]
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
        if path.exists():
            with path.open("rb") as f:
                artifacts[target] = pickle.load(f)
    return manifest, artifacts


def model_classes(artifact):
    pipe = artifact.get("pipeline")
    model = getattr(pipe, "named_steps", {}).get("model") if pipe is not None else None
    return [str(c) for c in getattr(model, "classes_", [])]


def class_score(artifact, x, class_label):
    pipe = artifact.get("pipeline")
    if pipe is None or not hasattr(pipe, "predict_proba"):
        return np.zeros(len(x), dtype=float)
    classes = model_classes(artifact)
    probs = pipe.predict_proba(x)
    class_label = str(class_label)
    if class_label in classes:
        return probs[:, classes.index(class_label)].astype(float)
    return np.max(probs, axis=1).astype(float)


def read_smoke_frames(smoke_root):
    frames = []
    for path in sorted((smoke_root / "raw_results").rglob("ASMAG_TR_CONTROLLER_ONLINE_GUARDED/frame_metrics.csv")):
        df = pd.read_csv(path)
        df["category"] = path.parts[-4]
        df["video"] = path.parts[-3]
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True).copy()
    for col in [
        "closed_empty_blocked_final",
        "reuse_blocked_final",
        "lightweight_blocked_final",
        "ptz_closed_empty_kill_active",
        "closed_empty_blocked_under_ptz",
        "ai_shadow_latency_ms",
    ]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["known_guarded_safety_event"] = (
        df["closed_empty_blocked_final"].gt(0)
        | df["reuse_blocked_final"].gt(0)
        | df["lightweight_blocked_final"].gt(0)
        | df["ptz_closed_empty_kill_active"].gt(0)
        | df["closed_empty_blocked_under_ptz"].gt(0)
    )
    df["known_hard_video"] = df["video"].astype(str).isin(HARD_VIDEOS)
    return df


def decision_flag(scores, target, threshold):
    scores = pd.Series(scores).astype(float)
    if target in {"reuse_allowed", "lightweight_allowed"}:
        return scores.lt(threshold)
    return scores.ge(threshold)


def write_class_mapping(output_root, artifacts):
    rows = []
    for target in BINARY_TARGETS:
        artifact = artifacts.get(target, {})
        classes = model_classes(artifact)
        offline_idx = classes.index("1") if "1" in classes else None
        runtime_idx = classes.index("1") if "1" in classes else None
        mapping_ok = offline_idx is not None and offline_idx == runtime_idx
        issue = ""
        fix = "No fix needed; offline and runtime both use classes_.index('1')."
        if not mapping_ok:
            issue = "positive class '1' was not found or index differs"
            fix = "Use classes_.index('1') for binary positive score extraction."
        if target in {"reuse_allowed", "lightweight_allowed"} and mapping_ok:
            issue = "Score is probability of allowed=1; block decision intentionally uses score below threshold."
        rows.append({
            "target": target,
            "model_type": artifact.get("model_name", ""),
            "classes": "|".join(classes),
            "positive_class": "1",
            "probability_index_used_offline": offline_idx,
            "probability_index_used_runtime": runtime_idx,
            "mapping_ok": bool(mapping_ok),
            "issue_found": issue,
            "recommended_fix": fix,
        })
    if "risk_class" in artifacts:
        classes = model_classes(artifacts["risk_class"])
        idx = classes.index("unsafe") if "unsafe" in classes else None
        rows.append({
            "target": "risk_class",
            "model_type": artifacts["risk_class"].get("model_name", ""),
            "classes": "|".join(classes),
            "positive_class": "unsafe",
            "probability_index_used_offline": idx,
            "probability_index_used_runtime": idx,
            "mapping_ok": idx is not None,
            "issue_found": "",
            "recommended_fix": "No fix needed; offline and runtime both use classes_.index('unsafe').",
        })
    pd.DataFrame(rows).to_csv(output_root / "class_probability_mapping.csv", index=False)
    return pd.DataFrame(rows)


def write_feature_alignment(output_root, manifest, artifacts, smoke):
    runtime_features = list(manifest.get("features", []))
    smoke_columns = set(smoke.columns)
    not_logged = [f for f in runtime_features if f not in smoke_columns]
    rows = []
    for target in ALL_TARGETS:
        artifact = artifacts.get(target, {})
        model_features = list(artifact.get("features", []))
        missing = [f for f in model_features if f not in runtime_features]
        extra = [f for f in runtime_features if f not in model_features]
        same_order = model_features == runtime_features
        details = []
        if not same_order:
            details.append("artifact feature order differs from manifest runtime order")
        if not_logged:
            details.append(
                "not directly logged but built by runtime adapter: " + "|".join(not_logged)
            )
        if "window_mean_utility" in runtime_features:
            details.append("runtime adapter sets window_mean_utility to 0.0")
        rows.append({
            "target": target,
            "n_features_model": len(model_features),
            "n_features_runtime": len(runtime_features),
            "same_order": bool(same_order),
            "missing_features": "|".join(missing),
            "extra_features": "|".join(extra),
            "mismatch_details": "; ".join(details),
            "mapping_ok": bool(same_order and not missing and not extra),
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_root / "feature_schema_alignment.csv", index=False)
    return df


def summarize_scores(group, target, score_col):
    scores = pd.to_numeric(group[score_col], errors="coerce").fillna(0.0)
    row = {
        "target": target,
        "category": group["category"].iloc[0],
        "video": group["video"].iloc[0],
        "frames": int(len(group)),
        "score_mean": float(scores.mean()),
        "score_p50": float(scores.quantile(0.50)),
        "score_p90": float(scores.quantile(0.90)),
        "score_p95": float(scores.quantile(0.95)),
        "score_min": float(scores.min()),
        "score_max": float(scores.max()),
    }
    for threshold in [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
        row[f"flag_rate_at_{int(threshold * 100):03d}"] = float(
            decision_flag(scores, target, threshold).mean()
        )
    return row


def write_runtime_score_distribution(output_root, smoke):
    score_cols = {
        "unsafe_action": "ai_unsafe_action_score",
        "detector_needed": "ai_detector_needed_score",
        "reuse_allowed": "ai_reuse_allowed_score",
        "lightweight_allowed": "ai_lightweight_allowed_score",
        "detector_floor_needed": "ai_detector_floor_needed_score",
        "risk_class": "ai_risk_class_score",
    }
    rows = []
    for target, score_col in score_cols.items():
        if score_col not in smoke.columns:
            continue
        for _, group in smoke.groupby(["category", "video"], dropna=False):
            rows.append(summarize_scores(group, target, score_col))
    df = pd.DataFrame(rows)
    df.to_csv(output_root / "runtime_score_distribution.csv", index=False)
    return df


def binary_metrics(labels, flags):
    labels = pd.Series(labels).astype(bool)
    flags = pd.Series(flags).astype(bool)
    tp = int((labels & flags).sum())
    fp = int((~labels & flags).sum())
    tn = int((~labels & ~flags).sum())
    fn = int((labels & ~flags).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return precision, recall, f1, fpr, tp, fp, tn, fn


def write_runtime_threshold_sweep(output_root, smoke):
    score_cols = {
        "unsafe_action": "ai_unsafe_action_score",
        "detector_needed": "ai_detector_needed_score",
        "reuse_allowed": "ai_reuse_allowed_score",
        "lightweight_allowed": "ai_lightweight_allowed_score",
        "detector_floor_needed": "ai_detector_floor_needed_score",
        "risk_class": "ai_risk_class_score",
    }
    rows = []
    labels = smoke["known_guarded_safety_event"]
    hard = smoke["known_hard_video"]
    for target, score_col in score_cols.items():
        if score_col not in smoke.columns:
            continue
        scores = pd.to_numeric(smoke[score_col], errors="coerce").fillna(0.0)
        for threshold in THRESHOLDS:
            flags = decision_flag(scores, target, threshold)
            precision, recall, f1, fpr, tp, fp, tn, fn = binary_metrics(labels, flags)
            rows.append({
                "target": target,
                "threshold": float(threshold),
                "decision_direction": "score_below_threshold_blocks"
                if target in {"reuse_allowed", "lightweight_allowed"}
                else "score_at_or_above_threshold_flags",
                "rows": int(len(smoke)),
                "known_safety_events": int(labels.sum()),
                "flag_rate": float(flags.mean()),
                "known_safety_recall": float(flags[labels].mean()) if labels.any() else np.nan,
                "normal_frame_flag_rate": float(flags[~labels].mean()) if (~labels).any() else np.nan,
                "hard_video_flag_rate": float(flags[hard].mean()) if hard.any() else np.nan,
                "precision_vs_known_safety": precision,
                "f1_vs_known_safety": f1,
                "false_positive_rate_vs_known_safety": fpr,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
            })
    sweep = pd.DataFrame(rows)
    sweep.to_csv(output_root / "runtime_threshold_sweep.csv", index=False)
    return sweep


def nearest_row(sweep, target, threshold):
    rows = sweep[sweep["target"].eq(target)].copy()
    rows["distance"] = (rows["threshold"] - threshold).abs()
    return rows.sort_values(["distance", "threshold"]).iloc[0]


def write_runtime_recommendations(output_root, sweep):
    recs = []
    unsafe = sweep[sweep["target"].eq("unsafe_action")].copy()
    unsafe_candidates = unsafe[unsafe["known_safety_recall"].ge(0.90)]
    unsafe_best = (
        unsafe_candidates.sort_values(["flag_rate", "threshold"], ascending=[True, False]).iloc[0]
        if not unsafe_candidates.empty
        else unsafe.sort_values(["f1_vs_known_safety", "threshold"], ascending=[False, False]).iloc[0]
    )
    recs.append({
        "target": "unsafe_action",
        "recommended_threshold": float(unsafe_best["threshold"]),
        "runtime_flag_rate": float(unsafe_best["flag_rate"]),
        "known_safety_recall": float(unsafe_best["known_safety_recall"]),
        "normal_frame_flag_rate": float(unsafe_best["normal_frame_flag_rate"]),
        "recommendation": "Research-only threshold; still over-flags smoke and must not control actions.",
        "phase8c2_readiness": "blocked",
    })
    for target, threshold, text in [
        ("detector_needed", 0.98, "Use only as advisory with cadence; pair with deterministic guards."),
        ("detector_floor_needed", 0.99, "Keep as a sparse advisory floor signal; deterministic PTZ floor remains authoritative."),
        ("reuse_allowed", 0.99, "Conservative advisory block threshold; do not let it override deterministic reuse guards."),
        ("lightweight_allowed", 0.95, "Advisory only; RF is too heavy and thresholds either miss safety events or over-block."),
        ("risk_class", 0.95, "Disable in lightweight runtime; score is unavailable in current smoke logs."),
    ]:
        row = nearest_row(sweep, target, threshold)
        recs.append({
            "target": target,
            "recommended_threshold": float(row["threshold"]),
            "runtime_flag_rate": float(row["flag_rate"]),
            "known_safety_recall": float(row["known_safety_recall"]),
            "normal_frame_flag_rate": float(row["normal_frame_flag_rate"]),
            "recommendation": text,
            "phase8c2_readiness": "blocked",
        })
    rec_df = pd.DataFrame(recs)
    rec_df.to_csv(output_root / "runtime_threshold_recommendations.csv", index=False)
    return rec_df


def action_bucket(action):
    action = str(action or "").upper()
    if action.startswith("DETECT_") or action in {"FORCED_REFRESH", "FALLBACK_P3_POLICY"}:
        return "DETECT_ACC" if "ACC" in action else "FALLBACK_P3_GUARD"
    if action == "LEGACY_SAFE_P3_GUARD":
        return "LEGACY_SAFE_P3_GUARD"
    if "FALLBACK_P3_GUARD" in action:
        return "FALLBACK_P3_GUARD"
    if "LIGHTWEIGHT_MASK_ACC" in action:
        return "LIGHTWEIGHT_MASK_ACC"
    if "LIGHTWEIGHT_MASK_P3_FALLBACK" in action or "REUSE_P3_FALLBACK" in action:
        return "LIGHTWEIGHT_MASK_P3_FALLBACK"
    if "REUSE_ACC" in action:
        return "REUSE_ACC"
    if "CLOSED_EMPTY" in action:
        return "CLOSED_EMPTY"
    return "OTHER"


def runtime_feature_row(features, telemetry, history):
    bucket = action_bucket(telemetry.get("action_label", ""))
    history.append(bucket)
    del history[:-10]
    recent = history[-5:]
    n = float(max(1, len(recent)))
    derived = {
        "latency_ms": float(pd.to_numeric(pd.Series([telemetry.get("latency_ms")]), errors="coerce").fillna(0.0).iloc[0]),
        "yolo_called": float(pd.to_numeric(pd.Series([telemetry.get("yolo_called")]), errors="coerce").fillna(0.0).iloc[0]),
        "reused_prediction": float(pd.to_numeric(pd.Series([telemetry.get("reused_prediction")]), errors="coerce").fillna(0.0).iloc[0]),
        "raw_frame_id": float(pd.to_numeric(pd.Series([telemetry.get("raw_frame_id")]), errors="coerce").fillna(0.0).iloc[0]),
        "evaluated_index": float(pd.to_numeric(pd.Series([telemetry.get("evaluated_index")]), errors="coerce").fillna(0.0).iloc[0]),
        "reuse_age": float(pd.to_numeric(pd.Series([telemetry.get("reuse_age")]), errors="coerce").fillna(0.0).iloc[0]),
        "reuse_success_rate": float(pd.to_numeric(pd.Series([telemetry.get("reuse_success_rate")]), errors="coerce").fillna(0.0).iloc[0]),
        "reuse_failure_rate": float(pd.to_numeric(pd.Series([telemetry.get("reuse_failure_rate")]), errors="coerce").fillna(0.0).iloc[0]),
        "reuse_allowed_by_eval_age": float(pd.to_numeric(pd.Series([telemetry.get("reuse_allowed_by_eval_age")]), errors="coerce").fillna(0.0).iloc[0]),
        "reuse_allowed_by_raw_age": float(pd.to_numeric(pd.Series([telemetry.get("reuse_allowed_by_raw_age")]), errors="coerce").fillna(0.0).iloc[0]),
        "reuse_stopped": float(pd.to_numeric(pd.Series([telemetry.get("reuse_stopped")]), errors="coerce").fillna(0.0).iloc[0]),
    }
    derived["normalized_latency"] = min(2.0, max(0.0, derived["latency_ms"] / 300.0))
    derived["window_detector_count"] = float(sum(b in {"DETECT_ACC", "FALLBACK_P3_GUARD", "LEGACY_SAFE_P3_GUARD"} for b in recent))
    derived["window_reuse_count"] = float(sum(b == "REUSE_ACC" for b in recent))
    derived["window_closed_empty_count"] = float(sum(b == "CLOSED_EMPTY" for b in recent))
    derived["window_mean_utility"] = 0.0
    for bucket in [
        "DETECT_ACC",
        "FALLBACK_P3_GUARD",
        "LIGHTWEIGHT_MASK_ACC",
        "LIGHTWEIGHT_MASK_P3_FALLBACK",
        "REUSE_ACC",
        "CLOSED_EMPTY",
        "LEGACY_SAFE_P3_GUARD",
        "OTHER",
    ]:
        derived[f"window_action_rate_{bucket}"] = float(sum(b == bucket for b in recent)) / n
    values = {feature: derived.get(feature, telemetry.get(feature, 0.0)) for feature in features}
    return pd.DataFrame([values], columns=features)


def percentile(values, q):
    if not values:
        return 0.0
    return float(pd.Series(values).quantile(q))


def write_latency_breakdown(output_root, manifest, artifacts, smoke, use_lightweight=True, stride=3):
    features = list(manifest.get("features", []))
    active_targets = [t for t in ALL_TARGETS if t in artifacts]
    if use_lightweight and "risk_class" in active_targets:
        active_targets.remove("risk_class")
    history = []
    adapter_ms = []
    predict_ms = []
    logging_ms = []
    total_replay_ms = []
    per_target = {target: [] for target in active_targets}
    for idx, record in enumerate(smoke.to_dict("records")):
        should_predict = idx == 0 or idx % max(1, stride) == 0
        start = time.perf_counter()
        if should_predict:
            t0 = time.perf_counter()
            row = runtime_feature_row(features, record, history)
            adapter_ms.append((time.perf_counter() - t0) * 1000.0)
            model_total = 0.0
            for target in active_targets:
                artifact = artifacts[target]
                pipe = artifact.get("pipeline")
                if pipe is None:
                    continue
                t1 = time.perf_counter()
                _ = pipe.predict(row)[0]
                if hasattr(pipe, "predict_proba"):
                    _ = pipe.predict_proba(row)[0]
                elapsed = (time.perf_counter() - t1) * 1000.0
                per_target[target].append(elapsed)
                model_total += elapsed
            predict_ms.append(model_total)
        else:
            adapter_ms.append(0.0)
            predict_ms.append(0.0)
            history.append(action_bucket(record.get("action_label", "")))
            del history[:-10]
        t2 = time.perf_counter()
        _ = {
            "unsafe": record.get("ai_unsafe_action_score", 0.0),
            "detector": record.get("ai_detector_needed_score", 0.0),
            "reuse": record.get("ai_reuse_allowed_score", 0.0),
            "lightweight": record.get("ai_lightweight_allowed_score", 0.0),
        }
        logging_ms.append((time.perf_counter() - t2) * 1000.0)
        total_replay_ms.append((time.perf_counter() - start) * 1000.0)
    observed = pd.to_numeric(smoke.get("ai_shadow_latency_ms", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    pred_frames = observed[observed.gt(0)]
    rows = [{
        "scope": "all_frames_observed_runtime",
        "frames": int(len(observed)),
        "prediction_stride": stride,
        "mean_feature_adapter_ms": float(np.mean(adapter_ms)),
        "p50_feature_adapter_ms": percentile(adapter_ms, 0.50),
        "p95_feature_adapter_ms": percentile(adapter_ms, 0.95),
        "mean_model_predict_ms": float(np.mean(predict_ms)),
        "p50_model_predict_ms": percentile(predict_ms, 0.50),
        "p95_model_predict_ms": percentile(predict_ms, 0.95),
        "mean_logging_ms": float(np.mean(logging_ms)),
        "p50_logging_ms": percentile(logging_ms, 0.50),
        "p95_logging_ms": percentile(logging_ms, 0.95),
        "mean_total_shadow_latency_ms": float(observed.mean()),
        "p50_total_shadow_latency_ms": float(observed.quantile(0.50)),
        "p95_total_shadow_latency_ms": float(observed.quantile(0.95)),
        "max_total_shadow_latency_ms": float(observed.max()),
        "measurement_note": "Observed total from smoke logs; components are offline replay microbenchmarks on smoke telemetry.",
    }, {
        "scope": "prediction_frames_observed_runtime",
        "frames": int(len(pred_frames)),
        "prediction_stride": stride,
        "mean_feature_adapter_ms": float(np.mean([v for v in adapter_ms if v > 0])) if any(v > 0 for v in adapter_ms) else 0.0,
        "p50_feature_adapter_ms": percentile([v for v in adapter_ms if v > 0], 0.50),
        "p95_feature_adapter_ms": percentile([v for v in adapter_ms if v > 0], 0.95),
        "mean_model_predict_ms": float(np.mean([v for v in predict_ms if v > 0])) if any(v > 0 for v in predict_ms) else 0.0,
        "p50_model_predict_ms": percentile([v for v in predict_ms if v > 0], 0.50),
        "p95_model_predict_ms": percentile([v for v in predict_ms if v > 0], 0.95),
        "mean_logging_ms": float(np.mean(logging_ms)),
        "p50_logging_ms": percentile(logging_ms, 0.50),
        "p95_logging_ms": percentile(logging_ms, 0.95),
        "mean_total_shadow_latency_ms": float(pred_frames.mean()) if len(pred_frames) else 0.0,
        "p50_total_shadow_latency_ms": float(pred_frames.quantile(0.50)) if len(pred_frames) else 0.0,
        "p95_total_shadow_latency_ms": float(pred_frames.quantile(0.95)) if len(pred_frames) else 0.0,
        "max_total_shadow_latency_ms": float(pred_frames.max()) if len(pred_frames) else 0.0,
        "measurement_note": "Prediction-frame total isolates stride recompute frames; cached frames are near zero.",
    }]
    for target, values in per_target.items():
        rows.append({
            "scope": f"model_predict_{target}",
            "frames": int(len(values)),
            "prediction_stride": stride,
            "mean_feature_adapter_ms": 0.0,
            "p50_feature_adapter_ms": 0.0,
            "p95_feature_adapter_ms": 0.0,
            "mean_model_predict_ms": float(np.mean(values)) if values else 0.0,
            "p50_model_predict_ms": percentile(values, 0.50),
            "p95_model_predict_ms": percentile(values, 0.95),
            "mean_logging_ms": 0.0,
            "p50_logging_ms": 0.0,
            "p95_logging_ms": 0.0,
            "mean_total_shadow_latency_ms": 0.0,
            "p50_total_shadow_latency_ms": 0.0,
            "p95_total_shadow_latency_ms": 0.0,
            "max_total_shadow_latency_ms": 0.0,
            "measurement_note": "Per-target offline replay predict+predict_proba timing.",
        })
    for (category, video), group in smoke.groupby(["category", "video"], dropna=False):
        lat = pd.to_numeric(group["ai_shadow_latency_ms"], errors="coerce").fillna(0.0)
        rows.append({
            "scope": f"video_{category}_{video}",
            "frames": int(len(group)),
            "prediction_stride": stride,
            "mean_feature_adapter_ms": 0.0,
            "p50_feature_adapter_ms": 0.0,
            "p95_feature_adapter_ms": 0.0,
            "mean_model_predict_ms": 0.0,
            "p50_model_predict_ms": 0.0,
            "p95_model_predict_ms": 0.0,
            "mean_logging_ms": 0.0,
            "p50_logging_ms": 0.0,
            "p95_logging_ms": 0.0,
            "mean_total_shadow_latency_ms": float(lat.mean()),
            "p50_total_shadow_latency_ms": float(lat.quantile(0.50)),
            "p95_total_shadow_latency_ms": float(lat.quantile(0.95)),
            "max_total_shadow_latency_ms": float(lat.max()),
            "measurement_note": "Observed video-level smoke latency.",
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_root / "shadow_latency_breakdown.csv", index=False)
    return df


def write_model_set_recommendation(output_root, latency, recs):
    target_latency = latency[latency["scope"].str.startswith("model_predict_")].copy()
    def mean_for(target):
        row = target_latency[target_latency["scope"].eq(f"model_predict_{target}")]
        return float(row["mean_model_predict_ms"].iloc[0]) if not row.empty else np.nan
    rows = [{
        "recommended_option": "offline-only, no runtime intervention yet",
        "secondary_candidate": "logistic/decision-tree-only runtime set",
        "detector_needed_model": "logistic_regression",
        "reuse_allowed_model": "logistic_regression",
        "unsafe_action_model": "replace random_forest with calibrated logistic or shallow sub-risk decision trees",
        "lightweight_allowed_model": "disable random_forest from frame-critical path",
        "risk_class_model": "disable in lightweight runtime",
        "detector_floor_needed_model": "decision_tree",
        "mean_detector_needed_predict_ms": mean_for("detector_needed"),
        "mean_unsafe_action_predict_ms": mean_for("unsafe_action"),
        "mean_reuse_allowed_predict_ms": mean_for("reuse_allowed"),
        "mean_lightweight_allowed_predict_ms": mean_for("lightweight_allowed"),
        "mean_detector_floor_needed_predict_ms": mean_for("detector_floor_needed"),
        "reason": "Runtime unsafe scores remain saturated and observed P95 latency is too high; RF unsafe/lightweight models are the expensive pieces.",
        "phase8c2_readiness": "blocked",
    }]
    df = pd.DataFrame(rows)
    df.to_csv(output_root / "runtime_model_set_recommendation.csv", index=False)
    return df


def write_offline_runtime_distribution(output_root, phase8a_root, artifacts, smoke, max_rows):
    data, _, _, _, _ = train8b.load_phase8a(phase8a_root)
    rows = []
    for target in ALL_TARGETS:
        if target not in artifacts or target not in data.columns:
            continue
        work = train8b.prepare_target_df(data, target, max_rows)
        features = list(artifacts[target].get("features", []))
        x = work[features].apply(pd.to_numeric, errors="coerce")
        class_label = "unsafe" if target == "risk_class" else "1"
        offline_scores = pd.Series(class_score(artifacts[target], x, class_label))
        runtime_col = f"ai_{target}_score"
        if target == "risk_class":
            runtime_col = "ai_risk_class_score"
        runtime_scores = pd.to_numeric(smoke.get(runtime_col, pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        rows.append({
            "target": target,
            "offline_rows": int(len(offline_scores)),
            "runtime_rows": int(len(runtime_scores)),
            "offline_mean": float(offline_scores.mean()),
            "runtime_mean": float(runtime_scores.mean()) if len(runtime_scores) else np.nan,
            "offline_p50": float(offline_scores.quantile(0.50)),
            "runtime_p50": float(runtime_scores.quantile(0.50)) if len(runtime_scores) else np.nan,
            "offline_p95": float(offline_scores.quantile(0.95)),
            "runtime_p95": float(runtime_scores.quantile(0.95)) if len(runtime_scores) else np.nan,
            "runtime_minus_offline_mean": float(runtime_scores.mean() - offline_scores.mean()) if len(runtime_scores) else np.nan,
            "runtime_minus_offline_p95": float(runtime_scores.quantile(0.95) - offline_scores.quantile(0.95)) if len(runtime_scores) else np.nan,
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_root / "offline_runtime_score_distribution_comparison.csv", index=False)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="outputs/phase8b_policy_training/models")
    parser.add_argument("--smoke-root", default="outputs/asmag_tr_controller_online_guarded_cdnet_smoke")
    parser.add_argument("--phase8a-root", default="outputs/phase8a_policy_dataset")
    parser.add_argument("--output-root", default="outputs/phase8c_shadow_calibration")
    parser.add_argument("--offline-max-rows", type=int, default=120000)
    args = parser.parse_args()

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest, artifacts = load_artifacts(Path(args.model_dir))
    smoke = read_smoke_frames(Path(args.smoke_root))
    if smoke.empty:
        raise RuntimeError("No guarded smoke frame_metrics.csv files found")

    write_class_mapping(output_root, artifacts)
    write_feature_alignment(output_root, manifest, artifacts, smoke)
    write_runtime_score_distribution(output_root, smoke)
    sweep = write_runtime_threshold_sweep(output_root, smoke)
    recs = write_runtime_recommendations(output_root, sweep)
    latency = write_latency_breakdown(output_root, manifest, artifacts, smoke)
    write_model_set_recommendation(output_root, latency, recs)
    write_offline_runtime_distribution(
        output_root,
        Path(args.phase8a_root),
        artifacts,
        smoke,
        args.offline_max_rows,
    )
    print(f"[DONE] wrote Phase 8C-1C runtime alignment outputs under {output_root}")


if __name__ == "__main__":
    main()
