#!/usr/bin/env python
"""Tune Phase 8C sub-risk shadow thresholds from existing smoke scores.

This tool is intentionally post-hoc: it reads guarded smoke frame logs and
simulates candidate shadow decisions without changing runtime actions.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


SMOKE_ROOT = Path("outputs/asmag_tr_controller_online_guarded_cdnet_smoke")
OUT_ROOT = Path("outputs/phase8c_subrisk_models/threshold_tuning")
GUARDED_PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"

HARD_VIDEOS = {
    "continuousPan",
    "twoPositionPTZCam",
    "bridgeEntry",
    "cubicle",
    "fountain02",
    "turbulence2",
    "tramCrossroad_1fps",
}

RISK_TARGETS = [
    "closed_empty_risk",
    "reuse_risk",
    "lightweight_p3_risk",
    "legacy_cadence_risk",
]

TARGETS = RISK_TARGETS + ["detector_needed", "lightweight_acc_allowed"]

SCORE_COLS = {
    "closed_empty_risk": "ai_closed_empty_risk_score",
    "reuse_risk": "ai_reuse_risk_score",
    "lightweight_p3_risk": "ai_lightweight_p3_risk_score",
    "legacy_cadence_risk": "ai_legacy_cadence_risk_score",
    "detector_needed": "ai_detector_needed_score",
    "lightweight_acc_allowed": "ai_lightweight_acc_allowed_score",
}

DEFAULT_THRESHOLDS = {
    "closed_empty_risk": 0.9999,
    "reuse_risk": 0.9999,
    "lightweight_p3_risk": 0.99,
    "legacy_cadence_risk": 0.99,
    "detector_needed": 0.99,
    "lightweight_acc_allowed": 0.21,
}

RECOMMENDED_THRESHOLDS = {
    # Keep highly selective action-risk thresholds; lower detector slightly to
    # close cubicle/hard-video misses while keeping normal-frame detector rate bounded.
    "closed_empty_risk": 0.9999,
    "reuse_risk": 0.9999,
    "lightweight_p3_risk": 0.99,
    "legacy_cadence_risk": 0.99,
    "detector_needed": 0.85,
    "lightweight_acc_allowed": 0.21,
}

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
    "yolo_called",
    "reused_prediction",
    "closed_empty_blocked_final",
    "reuse_blocked_final",
    "lightweight_blocked_final",
    "acc_blocked_final",
    "ptz_closed_empty_kill_active",
    "closed_empty_blocked_under_ptz",
    "active_event_memory",
    "global_motion_proxy",
    "foreground_risk",
    "gmq_event_continuity_risk",
    "gmq_background_reliability",
    "gmq_temporal_consistency",
    "gmq_motion_compensation_enabled",
    "motion_comp_compensated_trust_low",
    "geometry_trust_score",
    "geometry_trust_band",
    "candidate_P3_quality",
    "candidate_P3_temporal_iou",
    "ai_shadow_enabled",
    "ai_closed_empty_risk_score",
    "ai_reuse_risk_score",
    "ai_lightweight_p3_risk_score",
    "ai_legacy_cadence_risk_score",
    "ai_detector_needed_score",
    "ai_lightweight_acc_allowed_score",
    "ai_subrisk_missing_feature_count",
]


def read_existing_columns(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        header = fh.readline().strip()
    return header.split(",")


def read_guarded_frames(root: Path) -> pd.DataFrame:
    paths = sorted(root.glob(f"raw_results/*/*/{GUARDED_PIPELINE}/frame_metrics.csv"))
    frames = []
    for path in paths:
        cols = [col for col in USECOLS if col in read_existing_columns(path)]
        if not cols:
            continue
        frames.append(pd.read_csv(path, usecols=cols, low_memory=False))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    for col in USECOLS:
        if col not in df.columns:
            df[col] = 0
    for col in USECOLS:
        if col not in {"category", "video", "pipeline", "action_label", "selected_mode", "Event_State", "geometry_trust_band"}:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ["category", "video", "pipeline", "action_label", "selected_mode", "Event_State", "geometry_trust_band"]:
        df[col] = df[col].fillna("").astype(str)

    df["known_guarded_safety_event"] = (
        df["closed_empty_blocked_final"].gt(0)
        | df["reuse_blocked_final"].gt(0)
        | df["lightweight_blocked_final"].gt(0)
        | df["ptz_closed_empty_kill_active"].gt(0)
        | df["closed_empty_blocked_under_ptz"].gt(0)
    )
    df["known_hard_video"] = df["video"].isin(HARD_VIDEOS)
    df["normal_frame"] = ~df["known_guarded_safety_event"]
    df["cubicle_frame"] = df["video"].eq("cubicle")
    df["cubicle_known_event"] = df["cubicle_frame"] & df["known_guarded_safety_event"]
    return df


def flag_series(df: pd.DataFrame, target: str, threshold: float) -> pd.Series:
    score = df[SCORE_COLS[target]].astype(float)
    if target == "lightweight_acc_allowed":
        return score.lt(threshold)
    return score.ge(threshold)


def proxy_label(df: pd.DataFrame, target: str) -> pd.Series:
    if target == "closed_empty_risk":
        return (
            df["closed_empty_blocked_final"].gt(0)
            | df["closed_empty_blocked_under_ptz"].gt(0)
            | df["ptz_closed_empty_kill_active"].gt(0)
        )
    if target == "reuse_risk":
        return df["reuse_blocked_final"].gt(0)
    if target == "lightweight_p3_risk":
        return df["lightweight_blocked_final"].gt(0)
    if target == "legacy_cadence_risk":
        return df["action_label"].eq("LEGACY_SAFE_P3_GUARD") & df["known_guarded_safety_event"]
    if target == "detector_needed":
        return df["known_guarded_safety_event"]
    if target == "lightweight_acc_allowed":
        return df["acc_blocked_final"].gt(0) | df["lightweight_blocked_final"].gt(0)
    return pd.Series(False, index=df.index)


def precision_recall_f1(flags: pd.Series, labels: pd.Series) -> tuple[float, float, float]:
    tp = int((flags & labels).sum())
    fp = int((flags & ~labels).sum())
    fn = int((~flags & labels).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def threshold_grid(df: pd.DataFrame, target: str) -> list[float]:
    base = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999]
    scores = df[SCORE_COLS[target]].astype(float)
    quantiles = scores.quantile([0.25, 0.50, 0.75, 0.90, 0.95, 0.975, 0.99]).tolist()
    vals = sorted({round(float(v), 6) for v in base + quantiles if 0 <= float(v) <= 1})
    return vals


def evaluate_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    known = df["known_guarded_safety_event"]
    hard = df["known_hard_video"]
    normal = df["normal_frame"]
    cubicle_known = df["cubicle_known_event"]
    for target in TARGETS:
        labels = proxy_label(df, target)
        for threshold in threshold_grid(df, target):
            flags = flag_series(df, target, threshold)
            precision, recall, f1 = precision_recall_f1(flags, labels)
            rows.append({
                "target": target,
                "threshold": threshold,
                "flag_definition": "score_below_threshold_not_allowed" if target == "lightweight_acc_allowed" else "score_at_or_above_threshold",
                "flag_rate": float(flags.mean()),
                "known_safety_event_recall": float(flags[known].mean()) if known.any() else 0.0,
                "hard_video_recall": float(flags[hard].mean()) if hard.any() else 0.0,
                "cubicle_recall": float(flags[cubicle_known].mean()) if cubicle_known.any() else 0.0,
                "normal_frame_flag_rate": float(flags[normal].mean()) if normal.any() else 0.0,
                "precision": precision,
                "proxy_label_recall": recall,
                "f1": f1,
                "proxy_positive_labels": int(labels.sum()),
            })
    return pd.DataFrame(rows)


def combined_flags(df: pd.DataFrame, thresholds: dict[str, float], include_detector: bool = True) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for target in TARGETS:
        out[target] = flag_series(df, target, thresholds[target])
    out["subrisk_any"] = out[RISK_TARGETS].any(axis=1)
    out["subrisk_or_detector"] = out["subrisk_any"] | out["detector_needed"] if include_detector else out["subrisk_any"]
    return out


def choose_recommendations(df: pd.DataFrame, sweep: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target in TARGETS:
        sub = sweep[sweep["target"].eq(target)].copy()
        selected_threshold = RECOMMENDED_THRESHOLDS[target]
        best = sub.iloc[(sub["threshold"] - selected_threshold).abs().argmin()]
        if target == "detector_needed":
            rec = "shadow_only"
            rationale = "shadow A/B recall candidate; improves cubicle but detector requests remain too broad for intervention"
        elif target in RISK_TARGETS:
            rec = "shadow_only" if target == "reuse_risk" else "deterministic_guard_only"
            rationale = "risk flag remains useful diagnostically; deterministic guard should dominate intervention"
        else:
            rec = "needs_retrain"
            rationale = "allowed-model direction is weak for direct intervention; keep advisory"
        rows.append({
            "target": target,
            "recommended_threshold": float(selected_threshold),
            "posthoc_threshold_evaluated": float(best["threshold"]),
            "flag_rate": float(best["flag_rate"]),
            "known_safety_event_recall": float(best["known_safety_event_recall"]),
            "hard_video_recall": float(best["hard_video_recall"]),
            "cubicle_recall": float(best["cubicle_recall"]),
            "normal_frame_flag_rate": float(best["normal_frame_flag_rate"]),
            "precision": float(best["precision"]),
            "f1": float(best["f1"]),
            "runtime_recommendation": rec,
            "rationale": rationale,
        })
    return pd.DataFrame(rows)


def cubicle_diagnosis(df: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    cub = df[df["video"].eq("cubicle")].copy()
    rows = []
    if cub.empty:
        return pd.DataFrame()
    known = cub["known_guarded_safety_event"]
    for target in TARGETS:
        score = cub[SCORE_COLS[target]].astype(float)
        flags = flag_series(cub, target, thresholds[target])
        known_score = score[known]
        rows.append({
            "target": target,
            "cubicle_frames": int(len(cub)),
            "cubicle_known_event_frames": int(known.sum()),
            "threshold": thresholds[target],
            "flag_rate_all_cubicle": float(flags.mean()),
            "recall_on_cubicle_known_events": float(flags[known].mean()) if known.any() else 0.0,
            "score_mean_known_events": float(known_score.mean()) if len(known_score) else 0.0,
            "score_p50_known_events": float(known_score.quantile(0.50)) if len(known_score) else 0.0,
            "score_p90_known_events": float(known_score.quantile(0.90)) if len(known_score) else 0.0,
            "score_max_known_events": float(known_score.max()) if len(known_score) else 0.0,
            "mean_missing_features": float(cub["ai_subrisk_missing_feature_count"].mean()),
            "foreground_risk_mean_known_events": float(cub.loc[known, "foreground_risk"].mean()) if known.any() else 0.0,
            "active_event_memory_rate_known_events": float(cub.loc[known, "active_event_memory"].gt(0).mean()) if known.any() else 0.0,
            "global_motion_mean_known_events": float(cub.loc[known, "global_motion_proxy"].mean()) if known.any() else 0.0,
            "diagnosis": cubicle_target_diagnosis(target, score, known, thresholds[target]),
        })
    return pd.DataFrame(rows)


def cubicle_target_diagnosis(target: str, score: pd.Series, known: pd.Series, threshold: float) -> str:
    known_scores = score[known]
    if known_scores.empty:
        return "no cubicle known-event labels available"
    hit_rate = (known_scores < threshold).mean() if target == "lightweight_acc_allowed" else (known_scores >= threshold).mean()
    if hit_rate >= 0.90:
        return "captures cubicle known events at recommended threshold"
    if known_scores.quantile(0.90) < threshold and target != "lightweight_acc_allowed":
        return "scores remain below threshold; cubicle appears low/medium risk for this model"
    if target == "lightweight_acc_allowed" and known_scores.quantile(0.10) >= threshold:
        return "allowed-score remains above not-allowed threshold; weak cubicle blocker"
    return "partial cubicle signal; threshold alone may trade off normal-frame over-flagging"


def simulate_drift(df: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    flags = combined_flags(df, thresholds)
    sim = df[[
        "category", "video", "frame_id", "raw_frame_id", "evaluated_index",
        "action_label", "known_guarded_safety_event", "known_hard_video", "normal_frame",
    ]].copy()
    sim["ai_sim_original_action"] = sim["action_label"]
    sim["closed_empty_risk_flag"] = flags["closed_empty_risk"].astype(int)
    sim["reuse_risk_flag"] = flags["reuse_risk"].astype(int)
    sim["lightweight_p3_risk_flag"] = flags["lightweight_p3_risk"].astype(int)
    sim["legacy_cadence_risk_flag"] = flags["legacy_cadence_risk"].astype(int)
    sim["detector_needed_flag"] = flags["detector_needed"].astype(int)
    sim["lightweight_acc_not_allowed_flag"] = flags["lightweight_acc_allowed"].astype(int)

    action = sim["action_label"].fillna("").astype(str)
    block_closed = action.eq("CLOSED_EMPTY") & flags["closed_empty_risk"]
    block_reuse = action.str.contains("REUSE", na=False) & flags["reuse_risk"]
    block_light = action.eq("LIGHTWEIGHT_MASK_P3_FALLBACK") & flags["lightweight_p3_risk"]
    block_legacy = action.eq("LEGACY_SAFE_P3_GUARD") & flags["legacy_cadence_risk"]
    request_detector = flags["detector_needed"]

    sim["ai_sim_would_block_action"] = (block_closed | block_reuse | block_light | block_legacy).astype(int)
    sim["ai_sim_would_request_detector"] = request_detector.astype(int)
    sim["ai_sim_intervention_allowed_by_deterministic_guard"] = (
        df["closed_empty_blocked_final"].gt(0)
        | df["reuse_blocked_final"].gt(0)
        | df["lightweight_blocked_final"].gt(0)
        | df["closed_empty_blocked_under_ptz"].gt(0)
        | df["ptz_closed_empty_kill_active"].gt(0)
    ).astype(int)

    interventions = []
    safe_actions = []
    for i in sim.index:
        kinds = []
        if bool(block_closed.loc[i]):
            kinds.append("block_closed_empty")
        if bool(block_reuse.loc[i]):
            kinds.append("block_reuse")
        if bool(block_light.loc[i]):
            kinds.append("block_lightweight_p3")
        if bool(block_legacy.loc[i]):
            kinds.append("block_legacy_cadence")
        if bool(request_detector.loc[i]):
            kinds.append("request_detector")
        interventions.append("+".join(kinds) if kinds else "none")
        safe_actions.append("DETECT_ACC" if kinds else sim.at[i, "ai_sim_original_action"])
    sim["ai_sim_intervention_type"] = interventions
    sim["ai_sim_recommended_safe_action"] = safe_actions
    return sim


def drift_summary(sim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rows.append(drift_summary_row("ALL", "ALL", sim))
    for (category, video), group in sim.groupby(["category", "video"], dropna=False):
        rows.append(drift_summary_row(category, video, group))
    return pd.DataFrame(rows).sort_values(["hard_video", "over_intervention_risk_score"], ascending=[False, False])


def drift_summary_row(category: str, video: str, group: pd.DataFrame) -> dict:
    any_intervention = group["ai_sim_intervention_type"].ne("none")
    normal = group["normal_frame"].astype(bool)
    known = group["known_guarded_safety_event"].astype(bool)
    return {
        "category": category,
        "video": video,
        "frames": int(len(group)),
        "hard_video": bool(group["known_hard_video"].any()),
        "simulated_intervention_rate": float(any_intervention.mean()),
        "simulated_detector_request_rate": float(group["ai_sim_would_request_detector"].mean()),
        "simulated_reuse_block_rate": float(group["ai_sim_intervention_type"].str.contains("block_reuse").mean()),
        "simulated_lightweight_block_rate": float(group["ai_sim_intervention_type"].str.contains("block_lightweight_p3").mean()),
        "simulated_closed_empty_block_rate": float(group["ai_sim_intervention_type"].str.contains("block_closed_empty").mean()),
        "interventions_in_known_hard_video_frames": int((any_intervention & group["known_hard_video"].astype(bool)).sum()),
        "interventions_in_known_safety_event_frames": int((any_intervention & known).sum()),
        "interventions_in_normal_frames": int((any_intervention & normal).sum()),
        "deterministic_guard_aligned_intervention_rate": float(group.loc[any_intervention, "ai_sim_intervention_allowed_by_deterministic_guard"].mean()) if any_intervention.any() else 0.0,
        "over_intervention_risk_score": float((any_intervention & normal).mean()),
    }


def hard_video_analysis(df: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    flags = combined_flags(df, thresholds)
    rows = []
    hard_df = df[df["video"].isin(HARD_VIDEOS)]
    if not hard_df.empty:
        idx = hard_df.index
        normal = hard_df["normal_frame"]
        rows.append({
            "video": "ALL_HARD_VIDEOS",
            "frames": int(len(hard_df)),
            "known_safety_events": int(hard_df["known_guarded_safety_event"].sum()),
            "subrisk_any_recall": float(flags.loc[idx, "subrisk_any"].mean()),
            "subrisk_or_detector_recall": float(flags.loc[idx, "subrisk_or_detector"].mean()),
            "normal_frame_warning_rate": float(flags.loc[idx[normal.values], "subrisk_or_detector"].mean()) if normal.any() else 0.0,
        })
    for video, group in hard_df.groupby("video"):
        idx = group.index
        rows.append({
            "video": video,
            "frames": int(len(group)),
            "known_safety_events": int(group["known_guarded_safety_event"].sum()),
            "subrisk_any_recall": float(flags.loc[idx, "subrisk_any"].mean()),
            "subrisk_or_detector_recall": float(flags.loc[idx, "subrisk_or_detector"].mean()),
            "normal_frame_warning_rate": float(flags.loc[idx[group["normal_frame"].values], "subrisk_or_detector"].mean()) if group["normal_frame"].any() else 0.0,
        })
    return pd.DataFrame(rows)


def cubicle_threshold_analysis(sweep: pd.DataFrame) -> pd.DataFrame:
    return sweep[sweep["target"].isin(TARGETS)][[
        "target", "threshold", "flag_rate", "known_safety_event_recall",
        "hard_video_recall", "cubicle_recall", "normal_frame_flag_rate",
        "precision", "f1",
    ]].sort_values(["cubicle_recall", "normal_frame_flag_rate"], ascending=[False, True])


def runtime_policy_recommendation(recs: pd.DataFrame) -> pd.DataFrame:
    out = recs[[
        "target", "recommended_threshold", "runtime_recommendation",
        "known_safety_event_recall", "hard_video_recall", "cubicle_recall",
        "normal_frame_flag_rate", "rationale",
    ]].copy()
    out["deterministic_guard_should_dominate"] = out["runtime_recommendation"].isin([
        "deterministic_guard_only", "shadow_only", "needs_retrain"
    ])
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

    sweep = evaluate_thresholds(df)
    recs = choose_recommendations(df, sweep)
    thresholds = {
        row["target"]: float(row["recommended_threshold"])
        for _, row in recs.iterrows()
    }

    sim = simulate_drift(df, thresholds)
    summary = drift_summary(sim)
    cubicle_diag = cubicle_diagnosis(df, thresholds)
    hard_analysis = hard_video_analysis(df, thresholds)

    sweep.to_csv(args.out / "subrisk_threshold_sweep.csv", index=False)
    recs.to_csv(args.out / "subrisk_threshold_recommendations.csv", index=False)
    cubicle_threshold_analysis(sweep).to_csv(args.out / "cubicle_threshold_analysis.csv", index=False)
    hard_analysis.to_csv(args.out / "hard_video_threshold_analysis.csv", index=False)
    cubicle_diag.to_csv(args.out / "cubicle_diagnosis.csv", index=False)
    sim.to_csv(args.out / "ai_shadow_drift_simulation.csv", index=False)
    summary.to_csv(args.out / "ai_shadow_drift_summary.csv", index=False)
    runtime_policy_recommendation(recs).to_csv(args.out / "subrisk_runtime_policy_recommendation.csv", index=False)

    print(f"[DONE] wrote threshold tuning outputs to {args.out}")
    print(recs.to_string(index=False))


if __name__ == "__main__":
    main()
