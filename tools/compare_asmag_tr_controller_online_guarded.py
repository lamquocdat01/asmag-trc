import argparse
import json
from pathlib import Path

import pandas as pd


PIPELINES = [
    "P3_MOG2",
    "ASMAG_TR_CONTROLLER",
    "ONLINE_CALIBRATED",
    "ASMAG_TR_CONTROLLER_ONLINE_GUARDED",
]

GUARDED = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
OLD_ONLINE = "ONLINE_CALIBRATED"


def normalize_pipeline_names(df):
    if df.empty:
        return df
    pipeline_col = "Pipeline" if "Pipeline" in df.columns else "pipeline"
    df[pipeline_col] = df[pipeline_col].replace({
        "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED": OLD_ONLINE,
    })
    return df


def read_final_summary(root):
    path = root / "final_main_comparison.csv"
    if path.exists():
        df = normalize_pipeline_names(pd.read_csv(path))
        if "Pipeline" not in df.columns and "pipeline" in df.columns:
            df = df.rename(columns={"pipeline": "Pipeline"})
        df = df[df["Pipeline"].isin(PIPELINES)].copy()
        if set(PIPELINES).issubset(set(df["Pipeline"].astype(str))):
            return df

    per_video = read_per_video(root)
    if per_video.empty:
        return pd.DataFrame()
    metric_cols = [
        "CDnet_FMeasure",
        "Event_F1",
        "mAP_50",
        "Activation",
        "Avg_FPS",
        "P95_latency_ms",
        "Energy/frame",
        "simulated_runtime_energy/frame",
        "reused_prediction_rate",
    ]
    available = [c for c in metric_cols if c in per_video.columns]
    out = per_video.groupby("Pipeline", as_index=False)[available].mean(numeric_only=True)
    return out[out["Pipeline"].isin(PIPELINES)].copy()


def read_per_video(root):
    for name in ["per_video_summary.csv", "official_like_results.csv"]:
        path = root / name
        if path.exists():
            df = normalize_pipeline_names(pd.read_csv(path))
            if "Pipeline" not in df.columns and "pipeline" in df.columns:
                df = df.rename(columns={"pipeline": "Pipeline"})
            if "CDnet_FMeasure" not in df.columns and "FMeasure" in df.columns:
                df = df.rename(columns={"FMeasure": "CDnet_FMeasure"})
            if "Activation" not in df.columns and "YOLO_activation_rate" in df.columns:
                df = df.rename(columns={"YOLO_activation_rate": "Activation"})
            if "Avg_FPS" not in df.columns and "avg_FPS" in df.columns:
                df = df.rename(columns={"avg_FPS": "Avg_FPS"})
            df = df[df["Pipeline"].isin(PIPELINES)].copy()
            if set(PIPELINES).issubset(set(df["Pipeline"].astype(str))):
                return df
            raw_df = read_per_video_from_raw(root)
            return raw_df if not raw_df.empty else df
    raw_df = read_per_video_from_raw(root)
    if not raw_df.empty:
        return raw_df
    return pd.DataFrame()


def read_per_video_from_raw(root):
    raw = root / "raw_results"
    if not raw.exists():
        return pd.DataFrame()
    rows = []
    for pipeline in PIPELINES:
        for pixel_path in raw.rglob(f"{pipeline}/sequence_pixel_summary.csv"):
            seq_dir = pixel_path.parent
            try:
                pixel = pd.read_csv(pixel_path).iloc[0].to_dict()
            except Exception:
                continue
            row = {
                "category": pixel.get("category", seq_dir.parent.parent.name),
                "video": pixel.get("video", seq_dir.parent.name),
                "Pipeline": pipeline,
                "CDnet_FMeasure": pixel.get("FMeasure", pixel.get("CDnet_FMeasure", 0.0)),
            }
            event_path = seq_dir / "sequence_event_summary.csv"
            if event_path.exists():
                event = pd.read_csv(event_path).iloc[0].to_dict()
                row["Event_F1"] = event.get("Event_F1", 0.0)
            edge_path = seq_dir / "sequence_edge_summary.csv"
            if edge_path.exists():
                edge = pd.read_csv(edge_path).iloc[0].to_dict()
                row["Activation"] = edge.get("YOLO_activation_rate", edge.get("Activation", 0.0))
                row["Avg_FPS"] = edge.get("avg_FPS", edge.get("Avg_FPS", 0.0))
                row["P95_latency_ms"] = edge.get("P95_latency_ms", 0.0)
                row["Energy/frame"] = edge.get("Energy/frame", 0.0)
                row["simulated_runtime_energy/frame"] = edge.get("simulated_runtime_energy/frame", 0.0)
                row["reused_prediction_rate"] = edge.get("reused_prediction_rate", 0.0)
            object_path = seq_dir / "sequence_object_summary.csv"
            if object_path.exists():
                obj = pd.read_csv(object_path).iloc[0].to_dict()
                row["mAP_50"] = obj.get("mAP_50", 0.0)
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return normalize_pipeline_names(pd.DataFrame(rows))


def metric_delta(summary, reference):
    if summary.empty:
        return pd.DataFrame()
    guarded = summary[summary["Pipeline"] == GUARDED]
    ref = summary[summary["Pipeline"] == reference]
    if guarded.empty or ref.empty:
        return pd.DataFrame()
    guarded = guarded.iloc[0]
    ref = ref.iloc[0]
    rows = []
    for metric in [
        "CDnet_FMeasure",
        "Event_F1",
        "mAP_50",
        "Activation",
        "Avg_FPS",
        "P95_latency_ms",
        "Energy/frame",
        "simulated_runtime_energy/frame",
        "AE_Score",
    ]:
        if metric not in summary.columns:
            continue
        rows.append({
            "metric": metric,
            "pipeline": GUARDED,
            "reference_pipeline": reference,
            "pipeline_value": guarded.get(metric, 0.0),
            "reference_value": ref.get(metric, 0.0),
            "delta": guarded.get(metric, 0.0) - ref.get(metric, 0.0),
        })
    return pd.DataFrame(rows)


def build_per_video_failure_delta(per_video):
    if per_video.empty:
        return pd.DataFrame()
    metrics = ["CDnet_FMeasure", "Event_F1", "Activation", "P95_latency_ms", "Avg_FPS", "reused_prediction_rate"]
    available = [m for m in metrics if m in per_video.columns]
    rows = []
    grouped = per_video.groupby(["category", "video"], sort=False)
    for (category, video), group in grouped:
        by_pipeline = group.set_index("Pipeline")
        if GUARDED not in by_pipeline.index:
            continue
        row = {"category": category, "video": video}
        for metric in available:
            guarded_value = by_pipeline.loc[GUARDED].get(metric, 0.0)
            row[f"{GUARDED}_{metric}"] = guarded_value
            for ref in ["P3_MOG2", "ASMAG_TR_CONTROLLER", OLD_ONLINE]:
                if ref in by_pipeline.index:
                    ref_value = by_pipeline.loc[ref].get(metric, 0.0)
                    row[f"delta_{metric}_vs_{ref}"] = guarded_value - ref_value
        rows.append(row)
    out = pd.DataFrame(rows)
    sort_col = f"delta_CDnet_FMeasure_vs_{OLD_ONLINE}"
    if sort_col in out.columns:
        out = out.sort_values(sort_col)
    return out


def build_mode_action_summary(root):
    raw = root / "raw_results"
    if not raw.exists():
        return pd.DataFrame()
    frames = []
    usecols = [
        "category",
        "video",
        "pipeline",
        "selected_mode",
        "selected_mode_before_guard",
        "selected_mode_after_guard",
        "action_label",
        "action_reason",
        "latency_ms",
        "yolo_called",
        "reused_prediction",
        "cache_hit_gate_features",
        "motion_disagreement",
        "detector_like_action_thinned",
        "ptz_cadence_thinning_active",
        "event_safe_cadence_thinning_active",
    ]
    for path in raw.rglob(f"{GUARDED}/frame_metrics.csv"):
        header = pd.read_csv(path, nrows=0)
        cols = [c for c in usecols if c in header.columns]
        if cols:
            frames.append(pd.read_csv(path, usecols=cols))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    for col in ["action_label", "selected_mode_after_guard"]:
        if col not in df.columns:
            df[col] = ""
    df["detector_like_action"] = df["action_label"].astype(str).isin(
        ["DETECT_ACC", "DETECT_P3_FALLBACK", "FORCED_REFRESH", "FALLBACK_P3_GUARD",
         "FALLBACK_P3_POLICY", "LEGACY_SAFE_P3_GUARD"]
    ).astype(float)
    for col in ["detector_like_action_thinned", "ptz_cadence_thinning_active", "event_safe_cadence_thinning_active"]:
        if col not in df.columns:
            df[col] = 0
    group_cols = ["selected_mode_after_guard", "action_label"]
    summary = df.groupby(group_cols, dropna=False).agg(
        frames=("pipeline", "size"),
        mean_latency_ms=("latency_ms", "mean"),
        p95_latency_ms=("latency_ms", lambda s: s.quantile(0.95)),
        yolo_rate=("yolo_called", "mean"),
        reuse_rate=("reused_prediction", "mean"),
        cache_hit_rate=("cache_hit_gate_features", "mean"),
        mean_motion_disagreement=("motion_disagreement", "mean"),
        detector_like_action_rate=("detector_like_action", "mean"),
        detector_like_action_thinned_rate=("detector_like_action_thinned", "mean"),
        ptz_cadence_thinning_rate=("ptz_cadence_thinning_active", "mean"),
        event_safe_cadence_thinning_rate=("event_safe_cadence_thinning_active", "mean"),
    ).reset_index()
    return summary.sort_values(["selected_mode_after_guard", "action_label"])

def read_guarded_frames(root, usecols=None):
    raw = root / "raw_results"
    if not raw.exists():
        return pd.DataFrame()
    frames = []
    for path in raw.rglob(f"{GUARDED}/frame_metrics.csv"):
        header = pd.read_csv(path, nrows=0)
        if usecols is None:
            cols = list(header.columns)
        else:
            cols = [c for c in usecols if c in header.columns]
        if cols:
            frames.append(pd.read_csv(path, usecols=cols))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)

def build_gmq_action_summary(root):
    usecols = [
        "category", "video", "pipeline", "action_label", "gmq_action_reason",
        "gmq_guard_active", "gmq_action_score", "gmq_global_motion_risk",
        "gmq_background_reliability", "gmq_p3_veto_active",
        "gmq_lightweight_p3_veto_active", "gmq_full_p3_veto_active",
        "gmq_ptz_safe_override_active", "gmq_ptz_safe_branch_forced",
        "gmq_acc_blocked_under_global_motion", "gmq_event_hard_veto_active",
        "gmq_lazy_eval_active", "gmq_quality_compute_ms",
        "ptz_emergency_active", "final_sanitizer_active",
        "closed_empty_blocked_final", "reuse_blocked_final",
        "lightweight_blocked_final", "acc_blocked_final",
        "ptz_closed_empty_kill_active", "closed_empty_attempted_under_ptz",
        "closed_empty_blocked_under_ptz", "closed_empty_kill_cadence_override_used",
        "gmq_closed_empty_veto_active", "gmq_legacy_safe_branch_active",
        "yolo_called", "reused_prediction", "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "action_label" not in df.columns:
        return pd.DataFrame()
    for col in [
        "gmq_guard_active", "gmq_p3_veto_active", "gmq_lightweight_p3_veto_active",
        "gmq_full_p3_veto_active", "gmq_closed_empty_veto_active",
        "gmq_legacy_safe_branch_active", "gmq_ptz_safe_override_active",
        "gmq_ptz_safe_branch_forced", "gmq_acc_blocked_under_global_motion",
        "gmq_event_hard_veto_active", "gmq_lazy_eval_active",
        "ptz_emergency_active", "final_sanitizer_active",
        "closed_empty_blocked_final", "reuse_blocked_final",
        "lightweight_blocked_final", "acc_blocked_final",
        "ptz_closed_empty_kill_active", "closed_empty_attempted_under_ptz",
        "closed_empty_blocked_under_ptz", "closed_empty_kill_cadence_override_used",
    ]:
        if col not in df.columns:
            df[col] = 0
    summary = df.groupby("action_label", dropna=False).agg(
        frames=("pipeline", "size"),
        yolo_rate=("yolo_called", "mean"),
        reuse_rate=("reused_prediction", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        p95_latency_ms=("latency_ms", lambda s: s.quantile(0.95)),
        mean_fmeasure=("FMeasure", "mean"),
        gmq_guard_rate=("gmq_guard_active", "mean"),
        p3_veto_rate=("gmq_p3_veto_active", "mean"),
        lightweight_p3_veto_rate=("gmq_lightweight_p3_veto_active", "mean"),
        full_p3_veto_rate=("gmq_full_p3_veto_active", "mean"),
        closed_empty_veto_rate=("gmq_closed_empty_veto_active", "mean"),
        legacy_safe_rate=("gmq_legacy_safe_branch_active", "mean"),
        ptz_safe_override_rate=("gmq_ptz_safe_override_active", "mean"),
        ptz_safe_branch_forced_rate=("gmq_ptz_safe_branch_forced", "mean"),
        acc_blocked_under_global_motion_rate=("gmq_acc_blocked_under_global_motion", "mean"),
        event_hard_veto_rate=("gmq_event_hard_veto_active", "mean"),
        gmq_lazy_eval_rate=("gmq_lazy_eval_active", "mean"),
        mean_gmq_quality_compute_ms=("gmq_quality_compute_ms", "mean"),
        ptz_emergency_rate=("ptz_emergency_active", "mean"),
        final_sanitizer_rate=("final_sanitizer_active", "mean"),
        closed_empty_blocked_final_rate=("closed_empty_blocked_final", "mean"),
        reuse_blocked_final_rate=("reuse_blocked_final", "mean"),
        lightweight_blocked_final_rate=("lightweight_blocked_final", "mean"),
        acc_blocked_final_rate=("acc_blocked_final", "mean"),
        ptz_closed_empty_kill_rate=("ptz_closed_empty_kill_active", "mean"),
        closed_empty_attempted_under_ptz_rate=("closed_empty_attempted_under_ptz", "mean"),
        closed_empty_blocked_under_ptz_rate=("closed_empty_blocked_under_ptz", "mean"),
        closed_empty_kill_cadence_override_rate=("closed_empty_kill_cadence_override_used", "mean"),
        mean_gmq_score=("gmq_action_score", "mean"),
        mean_global_motion_risk=("gmq_global_motion_risk", "mean"),
        mean_background_reliability=("gmq_background_reliability", "mean"),
    ).reset_index()
    return summary.sort_values("frames", ascending=False)

def build_gmq_quality_summary(root):
    usecols = [
        "category", "video", "pipeline",
        "gmq_p3_quality", "gmq_acc_quality", "gmq_fast_quality",
        "gmq_candidate_disagreement", "gmq_temporal_consistency",
        "gmq_spatial_spread", "gmq_background_reliability",
        "gmq_global_motion_risk", "gmq_best_candidate_mode",
        "candidate_P3_area_ratio", "candidate_ACC_area_ratio", "candidate_FAST_area_ratio",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty:
        return pd.DataFrame()
    numeric = [
        c for c in usecols
        if c not in {"category", "video", "pipeline", "gmq_best_candidate_mode"} and c in df.columns
    ]
    grouped = df.groupby(["category", "video"], dropna=False)
    summary = grouped[numeric].agg(["mean", "median", lambda s: s.quantile(0.95)])
    summary.columns = [
        f"{metric}_{stat if isinstance(stat, str) else 'p95'}"
        for metric, stat in summary.columns
    ]
    summary = summary.reset_index()
    if "gmq_best_candidate_mode" in df.columns:
        dist = (
            df.groupby(["category", "video", "gmq_best_candidate_mode"], dropna=False)
            .size()
            .reset_index(name="frames")
        )
        total = dist.groupby(["category", "video"])["frames"].transform("sum")
        dist["rate"] = dist["frames"] / total
        best = dist.sort_values(["category", "video", "frames"], ascending=[True, True, False]).groupby(["category", "video"]).head(1)
        best = best.rename(columns={"gmq_best_candidate_mode": "top_gmq_best_candidate_mode", "rate": "top_gmq_best_candidate_rate"})
        summary = summary.merge(best[["category", "video", "top_gmq_best_candidate_mode", "top_gmq_best_candidate_rate"]], on=["category", "video"], how="left")
    return summary

def build_gmq_legacy_safe_summary(root):
    usecols = [
        "category", "video", "pipeline", "action_label",
        "gmq_legacy_safe_branch_active", "gmq_legacy_safe_reason",
        "gmq_p3_veto_active", "gmq_lightweight_p3_veto_active",
        "gmq_full_p3_veto_active", "gmq_ptz_safe_override_active",
        "gmq_ptz_safe_branch_forced", "gmq_acc_blocked_under_global_motion",
        "ptz_emergency_active", "final_sanitizer_active",
        "gmq_global_motion_risk",
        "gmq_background_reliability", "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "gmq_legacy_safe_branch_active" not in df.columns:
        return pd.DataFrame()
    for col in [
        "gmq_p3_veto_active", "gmq_lightweight_p3_veto_active", "gmq_full_p3_veto_active",
        "gmq_ptz_safe_override_active", "gmq_ptz_safe_branch_forced",
        "gmq_acc_blocked_under_global_motion",
        "ptz_emergency_active", "final_sanitizer_active",
    ]:
        if col not in df.columns:
            df[col] = 0
    return df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        legacy_safe_frames=("gmq_legacy_safe_branch_active", "sum"),
        legacy_safe_rate=("gmq_legacy_safe_branch_active", "mean"),
        p3_veto_rate=("gmq_p3_veto_active", "mean"),
        lightweight_p3_veto_rate=("gmq_lightweight_p3_veto_active", "mean"),
        full_p3_veto_rate=("gmq_full_p3_veto_active", "mean"),
        ptz_safe_override_rate=("gmq_ptz_safe_override_active", "mean"),
        ptz_safe_branch_forced_rate=("gmq_ptz_safe_branch_forced", "mean"),
        acc_blocked_under_global_motion_rate=("gmq_acc_blocked_under_global_motion", "mean"),
        ptz_emergency_rate=("ptz_emergency_active", "mean"),
        final_sanitizer_rate=("final_sanitizer_active", "mean"),
        mean_global_motion_risk=("gmq_global_motion_risk", "mean"),
        mean_background_reliability=("gmq_background_reliability", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()

def build_gmq_event_continuity_summary(root):
    usecols = [
        "category", "video", "pipeline", "action_label", "Event_State", "raw_frame_id",
        "gmq_event_continuity_risk", "gmq_closed_empty_veto_active",
        "gmq_event_hard_veto_active", "gmq_confident_empty_evidence",
        "final_sanitizer_active", "closed_empty_blocked_final",
        "event_closed_empty_attempt_count", "event_closed_empty_blocked_count",
        "event_closed_empty_final_count", "event_fn_risk_frames",
        "active_event_memory", "closed_empty_blocked_by_event_guard",
        "event_guard_reason", "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "gmq_event_continuity_risk" not in df.columns:
        return pd.DataFrame()
    for col in [
        "gmq_event_hard_veto_active", "gmq_confident_empty_evidence",
        "final_sanitizer_active", "closed_empty_blocked_final",
        "event_closed_empty_attempt_count", "event_closed_empty_blocked_count",
        "event_closed_empty_final_count", "event_fn_risk_frames",
    ]:
        if col not in df.columns:
            df[col] = 0
    closed_empty = df["action_label"].fillna("").astype(str).str.startswith("CLOSED_EMPTY") if "action_label" in df.columns else pd.Series(False, index=df.index)
    event_fn = df["Event_State"].fillna("").astype(str).eq("FN") if "Event_State" in df.columns else pd.Series(False, index=df.index)
    df = df.copy()
    df["closed_empty_frame"] = closed_empty.astype(int)
    df["closed_empty_event_fn"] = (closed_empty & event_fn).astype(int)
    return df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        mean_event_continuity_risk=("gmq_event_continuity_risk", "mean"),
        active_event_memory_rate=("active_event_memory", "mean"),
        closed_empty_veto_frames=("gmq_closed_empty_veto_active", "sum"),
        event_hard_veto_frames=("gmq_event_hard_veto_active", "sum"),
        confident_empty_evidence_rate=("gmq_confident_empty_evidence", "mean"),
        final_sanitizer_frames=("final_sanitizer_active", "sum"),
        closed_empty_blocked_final_frames=("closed_empty_blocked_final", "sum"),
        event_closed_empty_attempt_count=("event_closed_empty_attempt_count", "sum"),
        event_closed_empty_blocked_count=("event_closed_empty_blocked_count", "sum"),
        event_closed_empty_final_count=("event_closed_empty_final_count", "sum"),
        event_fn_risk_frames=("event_fn_risk_frames", "sum"),
        event_guard_block_frames=("closed_empty_blocked_by_event_guard", "sum"),
        closed_empty_frames=("closed_empty_frame", "sum"),
        closed_empty_event_fn_count=("closed_empty_event_fn", "sum"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()

def build_ptz_closed_empty_summary(root):
    usecols = [
        "category", "video", "pipeline", "action_label", "Event_State",
        "ptz_closed_empty_kill_active", "ptz_closed_empty_kill_reason",
        "closed_empty_attempted_under_ptz", "closed_empty_blocked_under_ptz",
        "closed_empty_replacement_action", "closed_empty_replacement_source",
        "closed_empty_replacement_quality", "closed_empty_kill_cadence_override_used",
        "event_closed_empty_final_count", "gmq_global_motion_risk",
        "global_motion_escape_active", "ptz_emergency_active",
        "gmq_legacy_safe_branch_active", "rolling_acc_dominance_under_global_motion",
        "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "action_label" not in df.columns:
        return pd.DataFrame()
    for col in [
        "ptz_closed_empty_kill_active", "closed_empty_attempted_under_ptz",
        "closed_empty_blocked_under_ptz", "closed_empty_kill_cadence_override_used",
        "event_closed_empty_final_count", "global_motion_escape_active",
        "ptz_emergency_active", "gmq_legacy_safe_branch_active",
    ]:
        if col not in df.columns:
            df[col] = 0
    closed_empty = df["action_label"].fillna("").astype(str).str.startswith("CLOSED_EMPTY")
    event_fn = df["Event_State"].fillna("").astype(str).eq("FN") if "Event_State" in df.columns else pd.Series(False, index=df.index)
    df = df.copy()
    df["closed_empty_frame"] = closed_empty.astype(int)
    df["closed_empty_event_fn"] = (closed_empty & event_fn).astype(int)
    summary = df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        closed_empty_frames=("closed_empty_frame", "sum"),
        closed_empty_rate=("closed_empty_frame", "mean"),
        closed_empty_event_fn_count=("closed_empty_event_fn", "sum"),
        event_closed_empty_final_count=("event_closed_empty_final_count", "sum"),
        ptz_closed_empty_kill_frames=("ptz_closed_empty_kill_active", "sum"),
        ptz_closed_empty_kill_rate=("ptz_closed_empty_kill_active", "mean"),
        closed_empty_attempted_under_ptz=("closed_empty_attempted_under_ptz", "sum"),
        closed_empty_blocked_under_ptz=("closed_empty_blocked_under_ptz", "sum"),
        cadence_override_frames=("closed_empty_kill_cadence_override_used", "sum"),
        global_motion_escape_rate=("global_motion_escape_active", "mean"),
        ptz_emergency_rate=("ptz_emergency_active", "mean"),
        legacy_safe_rate=("gmq_legacy_safe_branch_active", "mean"),
        mean_global_motion_risk=("gmq_global_motion_risk", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()
    if "closed_empty_replacement_action" in df.columns:
        repl = (
            df[df["ptz_closed_empty_kill_active"].fillna(0).astype(float) > 0]
            .groupby(["category", "video", "closed_empty_replacement_action"], dropna=False)
            .size()
            .reset_index(name="frames")
        )
        if not repl.empty:
            repl["piece"] = repl["closed_empty_replacement_action"].fillna("").astype(str) + ":" + repl["frames"].astype(str)
            repl_dist = repl.groupby(["category", "video"])["piece"].apply(";".join).reset_index(name="replacement_action_distribution")
            summary = summary.merge(repl_dist, on=["category", "video"], how="left")
    if "closed_empty_replacement_source" in df.columns:
        source = (
            df[df["ptz_closed_empty_kill_active"].fillna(0).astype(float) > 0]
            .groupby(["category", "video", "closed_empty_replacement_source"], dropna=False)
            .size()
            .reset_index(name="frames")
        )
        if not source.empty:
            source["piece"] = source["closed_empty_replacement_source"].fillna("").astype(str) + ":" + source["frames"].astype(str)
            source_dist = source.groupby(["category", "video"])["piece"].apply(";".join).reset_index(name="replacement_source_distribution")
            summary = summary.merge(source_dist, on=["category", "video"], how="left")
    return summary

def build_motion_comp_summary(root, ptz_only=False):
    usecols = [
        "category", "video", "pipeline", "action_label",
        "motion_comp_probe_active", "motion_comp_compute_ms",
        "motion_comp_pre_risk_gate_active",
        "motion_comp_confirmed_camera_motion_gate",
        "motion_comp_behavior_allowed",
        "motion_comp_probe_only_active",
        "motion_comp_behavior_applied",
        "motion_comp_diagnostics_only",
        "gmq_non_ptz_motion_comp_behavior_suppressed",
        "ptz_detector_floor_blocked_by_budget",
        "ptz_detector_floor_blocked_by_interval",
        "position_switch_guard_active",
        "motion_comp_dx", "motion_comp_dy", "motion_comp_shift_mag",
        "motion_comp_response", "motion_comp_residual_ratio",
        "motion_comp_temporal_iou_p3", "motion_comp_temporal_iou_acc",
        "motion_comp_temporal_iou_fast", "motion_comp_temporal_iou_final",
        "motion_comp_trust_band",
        "motion_comp_reuse_safe", "reuse_invalidated_by_motion_comp",
        "lightweight_invalidated_by_motion_comp", "ptz_detector_floor_active",
        "zoom_scale_suspect", "camera_jump_suspect",
        "ptz_cadence_thinning_active", "detector_like_action_thinned",
        "replacement_action_after_thinning", "ptz_legacy_safe_rate_window",
        "event_safe_cadence_thinning_active", "event_detect_acc_thinned",
        "event_replacement_action", "event_detect_acc_rate_window",
        "continuous_pan_signature_active", "continuous_pan_trust_relaxed",
        "continuous_pan_anchor_cadence_active", "continuous_pan_anchor_due",
        "continuous_pan_anchor_action", "continuous_pan_inter_anchor_action",
        "continuous_pan_legacy_safe_rate_window", "continuous_pan_legacy_safe_thinned",
        "continuous_pan_lightweight_acc_used", "continuous_pan_lightweight_p3_blocked",
        "continuous_pan_reuse_acc_used", "continuous_pan_rules_suppressed_for_position_switch",
        "continuous_pan_rules_suppressed_non_ptz", "continuous_pan_shift_stability",
        "continuous_pan_real_high_trust", "continuous_pan_relaxed_medium_trust",
        "continuous_pan_reuse_blocked_by_relaxed_trust", "continuous_pan_reuse_cap_active",
        "continuous_pan_reuse_replaced", "continuous_pan_reuse_rate_window",
        "continuous_pan_detector_anchor_rate_window", "continuous_pan_anchor_rate_too_low",
        "continuous_pan_anchor_rate_too_high", "continuous_pan_anchor_rate_corrected",
        "continuous_pan_inter_anchor_lightweight_acc_selected",
        "continuous_pan_suppressed_by_shift_instability",
        "continuous_pan_suppressed_by_position_switch", "position_switch_override_used",
        "position_switch_reset_active", "position_switch_detector_burst_active",
        "position_switch_exit_to_fast_path", "non_ptz_motion_comp_behavior_forced_off",
        "closed_empty_blocked_final", "event_closed_empty_final_count",
        "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "motion_comp_probe_active" not in df.columns:
        return pd.DataFrame()
    if ptz_only:
        df = df[df["category"].astype(str).eq("PTZ")].copy()
        if df.empty:
            return pd.DataFrame()
    for col in [
        "motion_comp_probe_active", "motion_comp_reuse_safe",
        "motion_comp_pre_risk_gate_active", "motion_comp_confirmed_camera_motion_gate",
        "motion_comp_behavior_allowed", "motion_comp_probe_only_active",
        "motion_comp_behavior_applied", "motion_comp_diagnostics_only",
        "gmq_non_ptz_motion_comp_behavior_suppressed",
        "ptz_detector_floor_blocked_by_budget", "ptz_detector_floor_blocked_by_interval",
        "position_switch_guard_active",
        "reuse_invalidated_by_motion_comp", "lightweight_invalidated_by_motion_comp",
        "ptz_detector_floor_active", "zoom_scale_suspect", "camera_jump_suspect",
        "ptz_cadence_thinning_active", "detector_like_action_thinned",
        "event_safe_cadence_thinning_active", "event_detect_acc_thinned",
        "continuous_pan_signature_active", "continuous_pan_trust_relaxed",
        "continuous_pan_anchor_cadence_active", "continuous_pan_anchor_due",
        "continuous_pan_legacy_safe_thinned", "continuous_pan_lightweight_acc_used",
        "continuous_pan_lightweight_p3_blocked", "continuous_pan_reuse_acc_used",
        "continuous_pan_rules_suppressed_for_position_switch",
        "continuous_pan_rules_suppressed_non_ptz",
        "continuous_pan_real_high_trust", "continuous_pan_relaxed_medium_trust",
        "continuous_pan_reuse_blocked_by_relaxed_trust", "continuous_pan_reuse_cap_active",
        "continuous_pan_reuse_replaced", "continuous_pan_anchor_rate_too_low",
        "continuous_pan_anchor_rate_too_high", "continuous_pan_anchor_rate_corrected",
        "continuous_pan_inter_anchor_lightweight_acc_selected",
        "continuous_pan_suppressed_by_shift_instability",
        "continuous_pan_suppressed_by_position_switch", "position_switch_override_used",
        "position_switch_reset_active", "position_switch_detector_burst_active",
        "position_switch_exit_to_fast_path", "non_ptz_motion_comp_behavior_forced_off",
        "closed_empty_blocked_final", "event_closed_empty_final_count",
    ]:
        if col not in df.columns:
            df[col] = 0
    if "motion_comp_trust_band" not in df.columns:
        df["motion_comp_trust_band"] = ""
    numeric_cols = [
        "motion_comp_compute_ms", "motion_comp_dx", "motion_comp_dy",
        "motion_comp_shift_mag", "motion_comp_response",
        "motion_comp_residual_ratio", "motion_comp_temporal_iou_p3",
        "motion_comp_temporal_iou_acc", "motion_comp_temporal_iou_fast",
        "motion_comp_temporal_iou_final", "ptz_legacy_safe_rate_window",
        "event_detect_acc_rate_window", "continuous_pan_legacy_safe_rate_window",
        "continuous_pan_shift_stability", "continuous_pan_reuse_rate_window",
        "continuous_pan_detector_anchor_rate_window", "latency_ms", "FMeasure",
    ]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0.0
    grouped = df.groupby(["category", "video"], dropna=False)
    summary = grouped.agg(
        frames=("pipeline", "size"),
        probe_active_frames=("motion_comp_probe_active", "sum"),
        probe_active_rate=("motion_comp_probe_active", "mean"),
        motion_comp_pre_risk_gate_rate=("motion_comp_pre_risk_gate_active", "mean"),
        motion_comp_confirmed_camera_motion_gate_rate=("motion_comp_confirmed_camera_motion_gate", "mean"),
        motion_comp_behavior_allowed_rate=("motion_comp_behavior_allowed", "mean"),
        motion_comp_probe_only_rate=("motion_comp_probe_only_active", "mean"),
        motion_comp_behavior_applied_rate=("motion_comp_behavior_applied", "mean"),
        motion_comp_diagnostics_only_rate=("motion_comp_diagnostics_only", "mean"),
        motion_comp_behavior_blocked_rate=("gmq_non_ptz_motion_comp_behavior_suppressed", "mean"),
        mean_compute_ms=("motion_comp_compute_ms", "mean"),
        mean_dx=("motion_comp_dx", "mean"),
        mean_dy=("motion_comp_dy", "mean"),
        mean_shift_mag=("motion_comp_shift_mag", "mean"),
        p95_shift_mag=("motion_comp_shift_mag", lambda s: s.quantile(0.95)),
        response_mean=("motion_comp_response", "mean"),
        response_p50=("motion_comp_response", "median"),
        response_p95=("motion_comp_response", lambda s: s.quantile(0.95)),
        residual_mean=("motion_comp_residual_ratio", "mean"),
        residual_p50=("motion_comp_residual_ratio", "median"),
        residual_p95=("motion_comp_residual_ratio", lambda s: s.quantile(0.95)),
        compensated_iou_p3_mean=("motion_comp_temporal_iou_p3", "mean"),
        compensated_iou_acc_mean=("motion_comp_temporal_iou_acc", "mean"),
        compensated_iou_fast_mean=("motion_comp_temporal_iou_fast", "mean"),
        compensated_iou_final_mean=("motion_comp_temporal_iou_final", "mean"),
        trust_band_high_rate=("motion_comp_trust_band", lambda s: s.astype(str).eq("high").mean()),
        trust_band_medium_rate=("motion_comp_trust_band", lambda s: s.astype(str).eq("medium").mean()),
        trust_band_low_rate=("motion_comp_trust_band", lambda s: s.astype(str).eq("low").mean()),
        trust_band_unknown_rate=("motion_comp_trust_band", lambda s: s.astype(str).eq("unknown").mean()),
        reuse_safe_rate=("motion_comp_reuse_safe", "mean"),
        reuse_invalidation_count=("reuse_invalidated_by_motion_comp", "sum"),
        reuse_invalidation_rate=("reuse_invalidated_by_motion_comp", "mean"),
        lightweight_invalidation_count=("lightweight_invalidated_by_motion_comp", "sum"),
        lightweight_invalidation_rate=("lightweight_invalidated_by_motion_comp", "mean"),
        ptz_detector_floor_count=("ptz_detector_floor_active", "sum"),
        ptz_detector_floor_rate=("ptz_detector_floor_active", "mean"),
        ptz_detector_floor_budget_block_rate=("ptz_detector_floor_blocked_by_budget", "mean"),
        ptz_detector_floor_interval_block_rate=("ptz_detector_floor_blocked_by_interval", "mean"),
        position_switch_guard_rate=("position_switch_guard_active", "mean"),
        position_switch_reset_rate=("position_switch_reset_active", "mean"),
        position_switch_detector_burst_rate=("position_switch_detector_burst_active", "mean"),
        position_switch_exit_to_fast_path_rate=("position_switch_exit_to_fast_path", "mean"),
        non_ptz_motion_comp_behavior_suppressed_rate=("gmq_non_ptz_motion_comp_behavior_suppressed", "mean"),
        non_ptz_motion_comp_behavior_forced_off_count=("non_ptz_motion_comp_behavior_forced_off", "sum"),
        non_ptz_motion_comp_behavior_forced_off_rate=("non_ptz_motion_comp_behavior_forced_off", "mean"),
        ptz_cadence_thinning_rate=("ptz_cadence_thinning_active", "mean"),
        detector_like_action_thinned_count=("detector_like_action_thinned", "sum"),
        detector_like_action_thinned_rate=("detector_like_action_thinned", "mean"),
        ptz_legacy_safe_rate_window_mean=("ptz_legacy_safe_rate_window", "mean"),
        event_safe_cadence_thinning_rate=("event_safe_cadence_thinning_active", "mean"),
        event_detect_acc_thinned_count=("event_detect_acc_thinned", "sum"),
        event_detect_acc_thinned_rate=("event_detect_acc_thinned", "mean"),
        event_detect_acc_rate_window_mean=("event_detect_acc_rate_window", "mean"),
        continuous_pan_signature_rate=("continuous_pan_signature_active", "mean"),
        continuous_pan_trust_relaxation_rate=("continuous_pan_trust_relaxed", "mean"),
        continuous_pan_anchor_cadence_rate=("continuous_pan_anchor_cadence_active", "mean"),
        continuous_pan_anchor_action_rate=("continuous_pan_anchor_due", "mean"),
        continuous_pan_inter_anchor_lightweight_acc_rate=("continuous_pan_lightweight_acc_used", "mean"),
        continuous_pan_legacy_safe_rate=("continuous_pan_legacy_safe_thinned", "mean"),
        continuous_pan_legacy_safe_rate_window_mean=("continuous_pan_legacy_safe_rate_window", "mean"),
        continuous_pan_lightweight_p3_block_rate=("continuous_pan_lightweight_p3_blocked", "mean"),
        continuous_pan_reuse_acc_rate=("continuous_pan_reuse_acc_used", "mean"),
        continuous_pan_rules_suppressed_for_position_switch_rate=("continuous_pan_rules_suppressed_for_position_switch", "mean"),
        continuous_pan_rules_suppressed_non_ptz_rate=("continuous_pan_rules_suppressed_non_ptz", "mean"),
        continuous_pan_shift_stability_mean=("continuous_pan_shift_stability", "mean"),
        continuous_pan_real_high_trust_rate=("continuous_pan_real_high_trust", "mean"),
        continuous_pan_relaxed_medium_trust_rate=("continuous_pan_relaxed_medium_trust", "mean"),
        continuous_pan_reuse_blocked_by_relaxed_trust_rate=("continuous_pan_reuse_blocked_by_relaxed_trust", "mean"),
        continuous_pan_reuse_cap_active_rate=("continuous_pan_reuse_cap_active", "mean"),
        continuous_pan_reuse_replaced_rate=("continuous_pan_reuse_replaced", "mean"),
        continuous_pan_reuse_rate_window_mean=("continuous_pan_reuse_rate_window", "mean"),
        continuous_pan_detector_anchor_rate_window_mean=("continuous_pan_detector_anchor_rate_window", "mean"),
        continuous_pan_anchor_rate_too_low_rate=("continuous_pan_anchor_rate_too_low", "mean"),
        continuous_pan_anchor_rate_too_high_rate=("continuous_pan_anchor_rate_too_high", "mean"),
        continuous_pan_anchor_rate_corrected_rate=("continuous_pan_anchor_rate_corrected", "mean"),
        continuous_pan_inter_anchor_lightweight_acc_selected_rate=("continuous_pan_inter_anchor_lightweight_acc_selected", "mean"),
        continuous_pan_suppressed_by_shift_instability_rate=("continuous_pan_suppressed_by_shift_instability", "mean"),
        continuous_pan_suppressed_by_position_switch_rate=("continuous_pan_suppressed_by_position_switch", "mean"),
        position_switch_override_used_rate=("position_switch_override_used", "mean"),
        zoom_scale_suspect_count=("zoom_scale_suspect", "sum"),
        zoom_scale_suspect_rate=("zoom_scale_suspect", "mean"),
        camera_jump_suspect_count=("camera_jump_suspect", "sum"),
        camera_jump_suspect_rate=("camera_jump_suspect", "mean"),
        closed_empty_final_block_count=("closed_empty_blocked_final", "sum"),
        event_closed_empty_final_count=("event_closed_empty_final_count", "sum"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()
    deltas = build_per_video_failure_delta(read_per_video(root))
    if not deltas.empty:
        keep = [
            "category", "video",
            f"{GUARDED}_CDnet_FMeasure",
            f"delta_CDnet_FMeasure_vs_{OLD_ONLINE}",
            f"{GUARDED}_Event_F1",
            f"delta_Event_F1_vs_{OLD_ONLINE}",
            f"{GUARDED}_Avg_FPS",
            f"delta_Avg_FPS_vs_{OLD_ONLINE}",
            f"{GUARDED}_P95_latency_ms",
            f"delta_P95_latency_ms_vs_{OLD_ONLINE}",
        ]
        keep = [c for c in keep if c in deltas.columns]
        summary = summary.merge(deltas[keep], on=["category", "video"], how="left")
    return summary

def build_low_framerate_guard_summary(root):
    usecols = [
        "category", "video", "pipeline", "action_label",
        "low_framerate_cadence_guard_active",
        "low_framerate_reuse_blocked",
        "low_framerate_detector_floor_active",
        "reused_prediction", "yolo_called", "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "low_framerate_cadence_guard_active" not in df.columns:
        return pd.DataFrame()
    for col in [
        "low_framerate_cadence_guard_active",
        "low_framerate_reuse_blocked",
        "low_framerate_detector_floor_active",
        "reused_prediction",
        "yolo_called",
    ]:
        if col not in df.columns:
            df[col] = 0
    summary = df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        low_framerate_guard_count=("low_framerate_cadence_guard_active", "sum"),
        low_framerate_guard_rate=("low_framerate_cadence_guard_active", "mean"),
        low_framerate_reuse_blocked_count=("low_framerate_reuse_blocked", "sum"),
        low_framerate_reuse_blocked_rate=("low_framerate_reuse_blocked", "mean"),
        low_framerate_detector_floor_count=("low_framerate_detector_floor_active", "sum"),
        low_framerate_detector_floor_rate=("low_framerate_detector_floor_active", "mean"),
        yolo_rate=("yolo_called", "mean"),
        reuse_rate=("reused_prediction", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()
    deltas = build_per_video_failure_delta(read_per_video(root))
    if not deltas.empty:
        keep = [
            "category", "video",
            f"{GUARDED}_CDnet_FMeasure",
            f"delta_CDnet_FMeasure_vs_{OLD_ONLINE}",
            f"{GUARDED}_Event_F1",
            f"delta_Event_F1_vs_{OLD_ONLINE}",
        ]
        keep = [c for c in keep if c in deltas.columns]
        summary = summary.merge(deltas[keep], on=["category", "video"], how="left")
    return summary


def build_cadence_thinning_summary(root):
    usecols = [
        "category", "video", "pipeline", "action_label",
        "ptz_cadence_thinning_active", "detector_like_action_thinned",
        "replacement_action_after_thinning", "ptz_legacy_safe_rate_window",
        "event_safe_cadence_thinning_active", "event_detect_acc_thinned",
        "event_replacement_action", "event_detect_acc_rate_window",
        "continuous_pan_signature_active", "continuous_pan_trust_relaxed",
        "continuous_pan_anchor_cadence_active", "continuous_pan_anchor_due",
        "continuous_pan_anchor_action", "continuous_pan_inter_anchor_action",
        "continuous_pan_legacy_safe_rate_window", "continuous_pan_legacy_safe_thinned",
        "continuous_pan_lightweight_acc_used", "continuous_pan_lightweight_p3_blocked",
        "continuous_pan_reuse_acc_used", "continuous_pan_rules_suppressed_for_position_switch",
        "continuous_pan_real_high_trust", "continuous_pan_relaxed_medium_trust",
        "continuous_pan_reuse_blocked_by_relaxed_trust", "continuous_pan_reuse_cap_active",
        "continuous_pan_reuse_replaced", "continuous_pan_reuse_rate_window",
        "continuous_pan_detector_anchor_rate_window", "continuous_pan_anchor_rate_too_low",
        "continuous_pan_anchor_rate_too_high", "continuous_pan_anchor_rate_corrected",
        "continuous_pan_inter_anchor_lightweight_acc_selected",
        "continuous_pan_suppressed_by_shift_instability",
        "continuous_pan_suppressed_by_position_switch", "position_switch_override_used",
        "position_switch_reset_active", "position_switch_detector_burst_active",
        "position_switch_exit_to_fast_path", "non_ptz_motion_comp_behavior_forced_off",
        "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty:
        return pd.DataFrame()
    for col in [
        "ptz_cadence_thinning_active", "detector_like_action_thinned",
        "event_safe_cadence_thinning_active", "event_detect_acc_thinned",
        "continuous_pan_signature_active", "continuous_pan_trust_relaxed",
        "continuous_pan_anchor_cadence_active", "continuous_pan_anchor_due",
        "continuous_pan_legacy_safe_thinned", "continuous_pan_lightweight_acc_used",
        "continuous_pan_lightweight_p3_blocked", "continuous_pan_reuse_acc_used",
        "continuous_pan_rules_suppressed_for_position_switch",
        "continuous_pan_real_high_trust", "continuous_pan_relaxed_medium_trust",
        "continuous_pan_reuse_blocked_by_relaxed_trust", "continuous_pan_reuse_cap_active",
        "continuous_pan_reuse_replaced", "continuous_pan_anchor_rate_too_low",
        "continuous_pan_anchor_rate_too_high", "continuous_pan_anchor_rate_corrected",
        "continuous_pan_inter_anchor_lightweight_acc_selected",
        "continuous_pan_suppressed_by_shift_instability",
        "continuous_pan_suppressed_by_position_switch", "position_switch_override_used",
        "position_switch_reset_active", "position_switch_detector_burst_active",
        "position_switch_exit_to_fast_path", "non_ptz_motion_comp_behavior_forced_off",
    ]:
        if col not in df.columns:
            df[col] = 0
    for col in [
        "replacement_action_after_thinning", "event_replacement_action", "action_label",
        "continuous_pan_anchor_action", "continuous_pan_inter_anchor_action",
    ]:
        if col not in df.columns:
            df[col] = ""
    for col in [
        "ptz_legacy_safe_rate_window", "event_detect_acc_rate_window",
        "continuous_pan_legacy_safe_rate_window", "continuous_pan_reuse_rate_window",
        "continuous_pan_detector_anchor_rate_window", "latency_ms", "FMeasure",
    ]:
        if col not in df.columns:
            df[col] = 0.0
    df["detector_like_action"] = df["action_label"].astype(str).isin(
        [
            "DETECT_ACC",
            "DETECT_P3_FALLBACK",
            "FORCED_REFRESH",
            "FALLBACK_P3_GUARD",
            "FALLBACK_P3_POLICY",
            "LEGACY_SAFE_P3_GUARD",
        ]
    ).astype(float)
    df["legacy_safe_action"] = df["action_label"].astype(str).eq("LEGACY_SAFE_P3_GUARD").astype(float)
    df["detect_acc_action"] = df["action_label"].astype(str).eq("DETECT_ACC").astype(float)
    df["reuse_acc_action"] = df["action_label"].astype(str).eq("REUSE_ACC").astype(float)
    df["lightweight_acc_action"] = df["action_label"].astype(str).eq("LIGHTWEIGHT_MASK_ACC").astype(float)
    summary = df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        detector_like_action_rate=("detector_like_action", "mean"),
        legacy_safe_action_rate=("legacy_safe_action", "mean"),
        detect_acc_action_rate=("detect_acc_action", "mean"),
        ptz_cadence_thinning_count=("ptz_cadence_thinning_active", "sum"),
        ptz_cadence_thinning_rate=("ptz_cadence_thinning_active", "mean"),
        detector_like_action_thinned_count=("detector_like_action_thinned", "sum"),
        event_safe_cadence_thinning_count=("event_safe_cadence_thinning_active", "sum"),
        event_safe_cadence_thinning_rate=("event_safe_cadence_thinning_active", "mean"),
        event_detect_acc_thinned_count=("event_detect_acc_thinned", "sum"),
        continuous_pan_signature_rate=("continuous_pan_signature_active", "mean"),
        continuous_pan_trust_relaxation_rate=("continuous_pan_trust_relaxed", "mean"),
        continuous_pan_anchor_cadence_rate=("continuous_pan_anchor_cadence_active", "mean"),
        continuous_pan_anchor_action_rate=("continuous_pan_anchor_due", "mean"),
        continuous_pan_inter_anchor_lightweight_acc_rate=("continuous_pan_lightweight_acc_used", "mean"),
        continuous_pan_legacy_safe_rate=("legacy_safe_action", "mean"),
        continuous_pan_detector_anchor_rate=("detector_like_action", "mean"),
        continuous_pan_lightweight_acc_rate=("lightweight_acc_action", "mean"),
        continuous_pan_reuse_acc_rate=("reuse_acc_action", "mean"),
        continuous_pan_legacy_safe_thinned_rate=("continuous_pan_legacy_safe_thinned", "mean"),
        continuous_pan_lightweight_p3_block_rate=("continuous_pan_lightweight_p3_blocked", "mean"),
        continuous_pan_reuse_acc_policy_rate=("continuous_pan_reuse_acc_used", "mean"),
        continuous_pan_rules_suppressed_for_position_switch_rate=("continuous_pan_rules_suppressed_for_position_switch", "mean"),
        continuous_pan_real_high_trust_rate=("continuous_pan_real_high_trust", "mean"),
        continuous_pan_relaxed_medium_trust_rate=("continuous_pan_relaxed_medium_trust", "mean"),
        continuous_pan_reuse_blocked_by_relaxed_trust_rate=("continuous_pan_reuse_blocked_by_relaxed_trust", "mean"),
        continuous_pan_reuse_cap_active_rate=("continuous_pan_reuse_cap_active", "mean"),
        continuous_pan_reuse_replaced_rate=("continuous_pan_reuse_replaced", "mean"),
        continuous_pan_reuse_rate_window_mean=("continuous_pan_reuse_rate_window", "mean"),
        continuous_pan_detector_anchor_rate_window_mean=("continuous_pan_detector_anchor_rate_window", "mean"),
        continuous_pan_anchor_rate_too_low_rate=("continuous_pan_anchor_rate_too_low", "mean"),
        continuous_pan_anchor_rate_too_high_rate=("continuous_pan_anchor_rate_too_high", "mean"),
        continuous_pan_anchor_rate_corrected_rate=("continuous_pan_anchor_rate_corrected", "mean"),
        continuous_pan_inter_anchor_lightweight_acc_selected_rate=("continuous_pan_inter_anchor_lightweight_acc_selected", "mean"),
        continuous_pan_position_switch_suppression_rate=("continuous_pan_suppressed_by_position_switch", "mean"),
        continuous_pan_shift_instability_suppression_rate=("continuous_pan_suppressed_by_shift_instability", "mean"),
        position_switch_override_used_rate=("position_switch_override_used", "mean"),
        position_switch_reset_rate=("position_switch_reset_active", "mean"),
        position_switch_detector_burst_rate=("position_switch_detector_burst_active", "mean"),
        position_switch_exit_to_fast_path_rate=("position_switch_exit_to_fast_path", "mean"),
        non_ptz_forced_off_count=("non_ptz_motion_comp_behavior_forced_off", "sum"),
        ptz_legacy_safe_rate_window_mean=("ptz_legacy_safe_rate_window", "mean"),
        continuous_pan_legacy_safe_rate_window_mean=("continuous_pan_legacy_safe_rate_window", "mean"),
        event_detect_acc_rate_window_mean=("event_detect_acc_rate_window", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()
    ptz_repl = (
        df[df["replacement_action_after_thinning"].astype(str).ne("")]
        .groupby(["category", "video", "replacement_action_after_thinning"])
        .size()
        .reset_index(name="count")
    )
    if not ptz_repl.empty:
        ptz_repl["piece"] = ptz_repl["replacement_action_after_thinning"].astype(str) + ":" + ptz_repl["count"].astype(str)
        dist = ptz_repl.groupby(["category", "video"])["piece"].apply(";".join).reset_index(
            name="ptz_replacement_distribution"
        )
        summary = summary.merge(dist, on=["category", "video"], how="left")
    event_repl = (
        df[df["event_replacement_action"].astype(str).ne("")]
        .groupby(["category", "video", "event_replacement_action"])
        .size()
        .reset_index(name="count")
    )
    if not event_repl.empty:
        event_repl["piece"] = event_repl["event_replacement_action"].astype(str) + ":" + event_repl["count"].astype(str)
        dist = event_repl.groupby(["category", "video"])["piece"].apply(";".join).reset_index(
            name="event_replacement_distribution"
        )
        summary = summary.merge(dist, on=["category", "video"], how="left")
    pan_repl = (
        df[df["continuous_pan_inter_anchor_action"].astype(str).ne("")]
        .groupby(["category", "video", "continuous_pan_inter_anchor_action"])
        .size()
        .reset_index(name="count")
    )
    if not pan_repl.empty:
        pan_repl["piece"] = pan_repl["continuous_pan_inter_anchor_action"].astype(str) + ":" + pan_repl["count"].astype(str)
        dist = pan_repl.groupby(["category", "video"])["piece"].apply(";".join).reset_index(
            name="continuous_pan_inter_anchor_distribution"
        )
        summary = summary.merge(dist, on=["category", "video"], how="left")
    return summary


def build_continuous_pan_policy_summary(root):
    cadence = build_cadence_thinning_summary(root)
    if cadence.empty:
        return cadence
    cols = [
        "category", "video", "frames",
        "continuous_pan_signature_rate",
        "continuous_pan_anchor_cadence_rate",
        "continuous_pan_detector_anchor_rate",
        "continuous_pan_lightweight_acc_rate",
        "continuous_pan_reuse_acc_rate",
        "continuous_pan_real_high_trust_rate",
        "continuous_pan_relaxed_medium_trust_rate",
        "continuous_pan_reuse_blocked_by_relaxed_trust_rate",
        "continuous_pan_position_switch_suppression_rate",
        "position_switch_reset_rate",
        "position_switch_detector_burst_rate",
        "continuous_pan_reuse_cap_active_rate",
        "continuous_pan_reuse_replaced_rate",
        "continuous_pan_detector_anchor_rate_window_mean",
        "continuous_pan_reuse_rate_window_mean",
        "continuous_pan_inter_anchor_distribution",
        "mean_latency_ms",
        "mean_fmeasure",
    ]
    cols = [c for c in cols if c in cadence.columns]
    return cadence[cols].copy()


def _read_geometry_frames(root):
    usecols = [
        "category", "video", "pipeline", "action_label",
        "geometry_probe_active", "geometry_probe_compute_ms", "geometry_probe_success",
        "geometry_probe_failure_reason", "geometry_probe_matches", "geometry_probe_inliers",
        "geometry_probe_inlier_ratio", "geometry_dx", "geometry_dy", "geometry_shift_mag",
        "geometry_scale", "geometry_rotation_deg", "geometry_model_type",
        "geometry_comp_iou_p3", "geometry_comp_iou_acc", "geometry_comp_iou_fast",
        "geometry_comp_iou_best", "geometry_residual_ratio",
        "geometry_improves_over_translation", "geometry_trust_score", "geometry_trust_band",
        "geometry_action_selection_active", "geometry_action_selection_reason",
        "geometry_selected_action_before", "geometry_selected_action_after",
        "geometry_reuse_blocked", "geometry_lightweight_p3_blocked",
        "geometry_lightweight_acc_allowed", "continuous_pan_geometry_trust_used",
        "continuous_pan_geometry_anchor_due", "continuous_pan_geometry_inter_anchor_action",
        "geometry_position_switch_active", "geometry_position_switch_reason",
        "geometry_position_switch_detector_burst", "geometry_position_switch_exit",
        "geometry_behavior_suppressed_non_ptz", "geometry_behavior_suppressed_event_only",
        "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty:
        return df
    for col in [
        "geometry_probe_active", "geometry_probe_success", "geometry_improves_over_translation",
        "geometry_action_selection_active", "geometry_reuse_blocked",
        "geometry_lightweight_p3_blocked", "geometry_lightweight_acc_allowed",
        "continuous_pan_geometry_trust_used", "continuous_pan_geometry_anchor_due",
        "geometry_position_switch_active", "geometry_position_switch_detector_burst",
        "geometry_position_switch_exit", "geometry_behavior_suppressed_non_ptz",
        "geometry_behavior_suppressed_event_only",
    ]:
        if col not in df.columns:
            df[col] = 0
    for col in [
        "geometry_probe_compute_ms", "geometry_probe_matches", "geometry_probe_inliers",
        "geometry_probe_inlier_ratio", "geometry_dx", "geometry_dy", "geometry_shift_mag",
        "geometry_scale", "geometry_rotation_deg", "geometry_comp_iou_p3",
        "geometry_comp_iou_acc", "geometry_comp_iou_fast", "geometry_comp_iou_best",
        "geometry_residual_ratio", "geometry_trust_score", "latency_ms", "FMeasure",
    ]:
        if col not in df.columns:
            df[col] = 0.0
    for col in [
        "geometry_probe_failure_reason", "geometry_model_type", "geometry_trust_band",
        "geometry_action_selection_reason", "geometry_selected_action_before",
        "geometry_selected_action_after", "continuous_pan_geometry_inter_anchor_action",
        "geometry_position_switch_reason", "action_label",
    ]:
        if col not in df.columns:
            df[col] = ""
    return df


def build_geometry_probe_summary(root):
    df = _read_geometry_frames(root)
    if df.empty or "geometry_probe_active" not in df.columns:
        return pd.DataFrame()
    summary = df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        geometry_probe_rate=("geometry_probe_active", "mean"),
        geometry_probe_success_rate=("geometry_probe_success", "mean"),
        geometry_compute_ms_mean=("geometry_probe_compute_ms", "mean"),
        geometry_compute_ms_p95=("geometry_probe_compute_ms", lambda s: s.quantile(0.95)),
        geometry_matches_mean=("geometry_probe_matches", "mean"),
        geometry_inliers_mean=("geometry_probe_inliers", "mean"),
        geometry_inlier_ratio_mean=("geometry_probe_inlier_ratio", "mean"),
        geometry_inlier_ratio_p95=("geometry_probe_inlier_ratio", lambda s: s.quantile(0.95)),
        geometry_scale_mean=("geometry_scale", "mean"),
        geometry_scale_p95=("geometry_scale", lambda s: s.quantile(0.95)),
        geometry_rotation_abs_mean=("geometry_rotation_deg", lambda s: s.abs().mean()),
        geometry_rotation_abs_p95=("geometry_rotation_deg", lambda s: s.abs().quantile(0.95)),
        geometry_shift_mag_mean=("geometry_shift_mag", "mean"),
        geometry_shift_mag_p95=("geometry_shift_mag", lambda s: s.quantile(0.95)),
        geometry_residual_mean=("geometry_residual_ratio", "mean"),
        geometry_residual_p95=("geometry_residual_ratio", lambda s: s.quantile(0.95)),
        geometry_improves_over_translation_rate=("geometry_improves_over_translation", "mean"),
        geometry_behavior_suppressed_non_ptz_rate=("geometry_behavior_suppressed_non_ptz", "mean"),
        geometry_behavior_suppressed_event_only_rate=("geometry_behavior_suppressed_event_only", "mean"),
    ).reset_index()
    deltas = build_per_video_failure_delta(read_per_video(root))
    if not deltas.empty:
        keep = [
            "category", "video",
            f"{GUARDED}_CDnet_FMeasure", f"delta_CDnet_FMeasure_vs_{OLD_ONLINE}",
            f"{GUARDED}_Event_F1", f"delta_Event_F1_vs_{OLD_ONLINE}",
            f"{GUARDED}_Avg_FPS", f"delta_Avg_FPS_vs_{OLD_ONLINE}",
            f"{GUARDED}_P95_latency_ms", f"delta_P95_latency_ms_vs_{OLD_ONLINE}",
        ]
        keep = [c for c in keep if c in deltas.columns]
        summary = summary.merge(deltas[keep], on=["category", "video"], how="left")
    return summary


def build_geometry_trust_summary(root):
    df = _read_geometry_frames(root)
    if df.empty:
        return pd.DataFrame()
    return df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        geometry_trust_high_rate=("geometry_trust_band", lambda s: s.astype(str).eq("high").mean()),
        geometry_trust_medium_rate=("geometry_trust_band", lambda s: s.astype(str).eq("medium").mean()),
        geometry_trust_low_rate=("geometry_trust_band", lambda s: s.astype(str).eq("low").mean()),
        geometry_trust_unknown_rate=("geometry_trust_band", lambda s: s.astype(str).eq("unknown").mean()),
        geometry_trust_score_mean=("geometry_trust_score", "mean"),
        geometry_comp_iou_best_mean=("geometry_comp_iou_best", "mean"),
        geometry_comp_iou_best_p95=("geometry_comp_iou_best", lambda s: s.quantile(0.95)),
        geometry_residual_mean=("geometry_residual_ratio", "mean"),
        geometry_residual_p95=("geometry_residual_ratio", lambda s: s.quantile(0.95)),
        continuous_pan_geometry_trust_used_rate=("continuous_pan_geometry_trust_used", "mean"),
        geometry_position_switch_rate=("geometry_position_switch_active", "mean"),
        geometry_position_switch_detector_burst_rate=("geometry_position_switch_detector_burst", "mean"),
    ).reset_index()


def build_geometry_action_summary(root):
    df = _read_geometry_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        geometry_action_selection_rate=("geometry_action_selection_active", "mean"),
        geometry_reuse_blocked_rate=("geometry_reuse_blocked", "mean"),
        geometry_lightweight_p3_blocked_rate=("geometry_lightweight_p3_blocked", "mean"),
        geometry_lightweight_acc_allowed_rate=("geometry_lightweight_acc_allowed", "mean"),
        continuous_pan_geometry_anchor_due_rate=("continuous_pan_geometry_anchor_due", "mean"),
        geometry_position_switch_detector_burst_rate=("geometry_position_switch_detector_burst", "mean"),
    ).reset_index()
    replacements = (
        df[df["geometry_selected_action_after"].astype(str).ne("")]
        .groupby(["category", "video", "geometry_selected_action_before", "geometry_selected_action_after"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    if not replacements.empty:
        replacements["piece"] = (
            replacements["geometry_selected_action_before"].fillna("").astype(str)
            + "->"
            + replacements["geometry_selected_action_after"].fillna("").astype(str)
            + ":"
            + replacements["count"].astype(str)
        )
        dist = replacements.groupby(["category", "video"])["piece"].apply(";".join).reset_index(
            name="geometry_action_replacement_distribution"
        )
        summary = summary.merge(dist, on=["category", "video"], how="left")
    pan = (
        df[df["continuous_pan_geometry_inter_anchor_action"].astype(str).ne("")]
        .groupby(["category", "video", "continuous_pan_geometry_inter_anchor_action"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    if not pan.empty:
        pan["piece"] = pan["continuous_pan_geometry_inter_anchor_action"].astype(str) + ":" + pan["count"].astype(str)
        dist = pan.groupby(["category", "video"])["piece"].apply(";".join).reset_index(
            name="continuous_pan_geometry_action_distribution"
        )
        summary = summary.merge(dist, on=["category", "video"], how="left")
    return summary


def _read_teacher_frames(root):
    usecols = [
        "category", "video", "pipeline", "action_label", "Event_State",
        "teacher_ranker_active", "teacher_ranker_scope_reason",
        "teacher_ranker_behavior_applied", "teacher_safety_guard_active",
        "teacher_safety_guard_reason", "teacher_blocked_action",
        "teacher_blocked_reason", "teacher_ranker_trust_state",
        "teacher_ranked_candidates", "teacher_top_candidate",
        "teacher_selected_action_before", "teacher_selected_action_after",
        "teacher_ranker_reason", "continuous_pan_teacher_policy_active",
        "continuous_pan_teacher_anchor_action",
        "continuous_pan_teacher_inter_anchor_action",
        "continuous_pan_teacher_blocked_reuse",
        "continuous_pan_teacher_blocked_lightweight_p3",
        "continuous_pan_teacher_blocked_legacy_weak",
        "teacher_position_switch_protection_active",
        "teacher_position_switch_reason",
        "teacher_position_switch_detector_burst",
        "teacher_position_switch_exit_to_fast_path",
        "teacher_event_behavior_suppressed",
        "teacher_bridge_event_safety_preserved",
        "teacher_non_ptz_suppressed",
        "teacher_non_ptz_suppression_reason",
        "geometry_trust_band", "frames_since_last_detector",
        "latency_ms", "FMeasure",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty:
        return df
    bool_cols = [
        "teacher_ranker_active", "teacher_ranker_behavior_applied",
        "teacher_safety_guard_active", "continuous_pan_teacher_policy_active",
        "continuous_pan_teacher_blocked_reuse",
        "continuous_pan_teacher_blocked_lightweight_p3",
        "continuous_pan_teacher_blocked_legacy_weak",
        "teacher_position_switch_protection_active",
        "teacher_position_switch_detector_burst",
        "teacher_position_switch_exit_to_fast_path",
        "teacher_event_behavior_suppressed",
        "teacher_bridge_event_safety_preserved",
        "teacher_non_ptz_suppressed",
    ]
    for col in bool_cols:
        if col not in df.columns:
            df[col] = 0
    text_cols = [
        "teacher_ranker_scope_reason", "teacher_safety_guard_reason",
        "teacher_blocked_action", "teacher_blocked_reason",
        "teacher_ranker_trust_state", "teacher_ranked_candidates",
        "teacher_top_candidate", "teacher_selected_action_before",
        "teacher_selected_action_after", "teacher_ranker_reason",
        "continuous_pan_teacher_anchor_action",
        "continuous_pan_teacher_inter_anchor_action",
        "teacher_position_switch_reason",
        "teacher_non_ptz_suppression_reason", "geometry_trust_band",
        "action_label", "Event_State",
    ]
    for col in text_cols:
        if col not in df.columns:
            df[col] = ""
    for col in ["frames_since_last_detector", "latency_ms", "FMeasure"]:
        if col not in df.columns:
            df[col] = 0.0
    action = df["action_label"].fillna("").astype(str)
    df["detector_like_anchor"] = action.isin(
        ["DETECT_ACC", "DETECT_P3_FALLBACK", "FORCED_REFRESH", "FALLBACK_P3_GUARD", "FALLBACK_P3_POLICY"]
    ).astype(float)
    df["lightweight_acc_action"] = action.eq("LIGHTWEIGHT_MASK_ACC").astype(float)
    df["reuse_acc_action"] = action.eq("REUSE_ACC").astype(float)
    df["legacy_safe_action"] = action.eq("LEGACY_SAFE_P3_GUARD").astype(float)
    df["fallback_p3_guard_action"] = action.eq("FALLBACK_P3_GUARD").astype(float)
    df["detect_acc_action"] = action.eq("DETECT_ACC").astype(float)
    df["closed_empty_action"] = action.str.startswith("CLOSED_EMPTY").astype(float)
    return df


def _merge_teacher_metric_deltas(summary, root):
    deltas = build_per_video_failure_delta(read_per_video(root))
    if deltas.empty:
        return summary
    keep = [
        "category", "video",
        f"{GUARDED}_CDnet_FMeasure", f"delta_CDnet_FMeasure_vs_{OLD_ONLINE}",
        f"{GUARDED}_Event_F1", f"delta_Event_F1_vs_{OLD_ONLINE}",
        f"{GUARDED}_Avg_FPS", f"delta_Avg_FPS_vs_{OLD_ONLINE}",
        f"{GUARDED}_P95_latency_ms", f"delta_P95_latency_ms_vs_{OLD_ONLINE}",
    ]
    keep = [c for c in keep if c in deltas.columns]
    return summary.merge(deltas[keep], on=["category", "video"], how="left")


def _merge_distribution(summary, df, column, name, active_col=None):
    working = df
    if active_col and active_col in working.columns:
        working = working[working[active_col].fillna(0).astype(float) > 0]
    dist = (
        working[working[column].fillna("").astype(str).ne("")]
        .groupby(["category", "video", column], dropna=False)
        .size()
        .reset_index(name="count")
    )
    if dist.empty:
        return summary
    dist["piece"] = dist[column].fillna("").astype(str) + ":" + dist["count"].astype(str)
    pieces = dist.groupby(["category", "video"])["piece"].apply(";".join).reset_index(name=name)
    return summary.merge(pieces, on=["category", "video"], how="left")


def build_teacher_ranker_summary(root):
    df = _read_teacher_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        ranker_active_rate=("teacher_ranker_active", "mean"),
        behavior_applied_rate=("teacher_ranker_behavior_applied", "mean"),
        trust_high_rate=("teacher_ranker_trust_state", lambda s: s.astype(str).eq("high").mean()),
        trust_medium_rate=("teacher_ranker_trust_state", lambda s: s.astype(str).eq("medium").mean()),
        trust_low_rate=("teacher_ranker_trust_state", lambda s: s.astype(str).eq("low").mean()),
        safety_guard_rate=("teacher_safety_guard_active", "mean"),
        detector_like_anchor_rate=("detector_like_anchor", "mean"),
        lightweight_mask_acc_rate=("lightweight_acc_action", "mean"),
        reuse_acc_rate=("reuse_acc_action", "mean"),
        legacy_safe_p3_guard_rate=("legacy_safe_action", "mean"),
        fallback_p3_guard_rate=("fallback_p3_guard_action", "mean"),
        detect_acc_rate=("detect_acc_action", "mean"),
        closed_empty_rate=("closed_empty_action", "mean"),
        position_switch_protection_rate=("teacher_position_switch_protection_active", "mean"),
        event_suppression_rate=("teacher_event_behavior_suppressed", "mean"),
        non_ptz_suppressed_rate=("teacher_non_ptz_suppressed", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()
    summary = _merge_distribution(summary, df, "teacher_ranker_trust_state", "trust_state_distribution", "teacher_ranker_active")
    summary = _merge_distribution(summary, df, "teacher_top_candidate", "top_candidate_distribution", "teacher_ranker_active")
    summary = _merge_distribution(summary, df, "teacher_ranker_reason", "ranker_reason_distribution", "teacher_ranker_active")
    return _merge_teacher_metric_deltas(summary, root)


def build_teacher_action_summary(root):
    df = _read_teacher_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        ranker_active_rate=("teacher_ranker_active", "mean"),
        behavior_applied_rate=("teacher_ranker_behavior_applied", "mean"),
        detector_like_anchor_rate=("detector_like_anchor", "mean"),
        lightweight_mask_acc_rate=("lightweight_acc_action", "mean"),
        reuse_acc_rate=("reuse_acc_action", "mean"),
        legacy_safe_p3_guard_rate=("legacy_safe_action", "mean"),
        fallback_p3_guard_rate=("fallback_p3_guard_action", "mean"),
        detect_acc_rate=("detect_acc_action", "mean"),
        closed_empty_rate=("closed_empty_action", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()
    summary = _merge_distribution(summary, df, "teacher_selected_action_before", "selected_action_before_distribution", "teacher_ranker_active")
    summary = _merge_distribution(summary, df, "teacher_selected_action_after", "selected_action_after_distribution", "teacher_ranker_active")
    summary = _merge_distribution(summary, df, "action_label", "final_action_distribution")
    return _merge_teacher_metric_deltas(summary, root)


def build_teacher_safety_guard_summary(root):
    df = _read_teacher_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = df.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        ranker_active_rate=("teacher_ranker_active", "mean"),
        behavior_applied_rate=("teacher_ranker_behavior_applied", "mean"),
        safety_guard_count=("teacher_safety_guard_active", "sum"),
        safety_guard_rate=("teacher_safety_guard_active", "mean"),
        blocked_reuse_rate=("continuous_pan_teacher_blocked_reuse", "mean"),
        blocked_lightweight_p3_rate=("continuous_pan_teacher_blocked_lightweight_p3", "mean"),
        blocked_legacy_weak_rate=("continuous_pan_teacher_blocked_legacy_weak", "mean"),
        detector_like_anchor_rate=("detector_like_anchor", "mean"),
        lightweight_mask_acc_rate=("lightweight_acc_action", "mean"),
        reuse_acc_rate=("reuse_acc_action", "mean"),
        legacy_safe_p3_guard_rate=("legacy_safe_action", "mean"),
        fallback_p3_guard_rate=("fallback_p3_guard_action", "mean"),
        detect_acc_rate=("detect_acc_action", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()
    summary = _merge_distribution(summary, df, "teacher_blocked_action", "blocked_action_distribution", "teacher_safety_guard_active")
    summary = _merge_distribution(summary, df, "teacher_blocked_reason", "blocked_reason_distribution", "teacher_safety_guard_active")
    return _merge_teacher_metric_deltas(summary, root)


def build_teacher_continuous_pan_summary(root):
    df = _read_teacher_frames(root)
    if df.empty:
        return pd.DataFrame()
    pan = df[df["video"].astype(str).eq("continuousPan") | (df["continuous_pan_teacher_policy_active"].fillna(0).astype(float) > 0)].copy()
    if pan.empty:
        return pd.DataFrame()
    summary = pan.groupby(["category", "video"], dropna=False).agg(
        frames=("pipeline", "size"),
        ranker_active_rate=("teacher_ranker_active", "mean"),
        behavior_applied_rate=("teacher_ranker_behavior_applied", "mean"),
        continuous_pan_teacher_policy_rate=("continuous_pan_teacher_policy_active", "mean"),
        trust_high_rate=("teacher_ranker_trust_state", lambda s: s.astype(str).eq("high").mean()),
        trust_medium_rate=("teacher_ranker_trust_state", lambda s: s.astype(str).eq("medium").mean()),
        trust_low_rate=("teacher_ranker_trust_state", lambda s: s.astype(str).eq("low").mean()),
        blocked_reuse_rate=("continuous_pan_teacher_blocked_reuse", "mean"),
        blocked_lightweight_p3_rate=("continuous_pan_teacher_blocked_lightweight_p3", "mean"),
        blocked_legacy_weak_rate=("continuous_pan_teacher_blocked_legacy_weak", "mean"),
        detector_like_anchor_rate=("detector_like_anchor", "mean"),
        lightweight_mask_acc_rate=("lightweight_acc_action", "mean"),
        reuse_acc_rate=("reuse_acc_action", "mean"),
        legacy_safe_p3_guard_rate=("legacy_safe_action", "mean"),
        fallback_p3_guard_rate=("fallback_p3_guard_action", "mean"),
        detect_acc_rate=("detect_acc_action", "mean"),
        closed_empty_rate=("closed_empty_action", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        mean_fmeasure=("FMeasure", "mean"),
    ).reset_index()
    summary = _merge_distribution(summary, pan, "continuous_pan_teacher_anchor_action", "anchor_action_distribution", "continuous_pan_teacher_policy_active")
    summary = _merge_distribution(summary, pan, "continuous_pan_teacher_inter_anchor_action", "inter_anchor_action_distribution", "continuous_pan_teacher_policy_active")
    return _merge_teacher_metric_deltas(summary, root)

def _read_ai_shadow_frames(root):
    usecols = [
        "category", "video", "pipeline", "frame_id", "evaluated_index",
        "action_label", "Event_State", "FMeasure", "latency_ms",
        "reused_prediction", "yolo_called", "final_sanitizer_active",
        "closed_empty_blocked_final", "reuse_blocked_final",
        "lightweight_blocked_final", "ptz_closed_empty_kill_active",
        "closed_empty_attempted_under_ptz", "closed_empty_blocked_under_ptz",
        "active_event_memory", "global_motion_proxy",
        "ai_shadow_enabled", "ai_detector_needed_pred", "ai_detector_needed_score",
        "ai_unsafe_action_pred", "ai_unsafe_action_score",
        "ai_reuse_allowed_pred", "ai_reuse_allowed_score",
        "ai_lightweight_allowed_pred", "ai_lightweight_allowed_score",
        "ai_risk_class_pred", "ai_risk_class_score",
        "ai_detector_floor_needed_pred", "ai_detector_floor_needed_score",
        "ai_disagree_with_current_action", "ai_would_block_reuse",
        "ai_would_block_lightweight", "ai_would_request_detector",
        "ai_would_flag_unsafe", "ai_missing_feature_count",
        "ai_shadow_latency_ms",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "ai_shadow_enabled" not in df.columns:
        return pd.DataFrame()
    for col in [
        "ai_shadow_enabled", "ai_disagree_with_current_action",
        "ai_would_block_reuse", "ai_would_block_lightweight",
        "ai_would_request_detector", "ai_would_flag_unsafe",
        "ai_missing_feature_count", "ai_shadow_latency_ms",
        "closed_empty_blocked_final", "reuse_blocked_final",
        "lightweight_blocked_final", "ptz_closed_empty_kill_active",
        "closed_empty_attempted_under_ptz", "closed_empty_blocked_under_ptz",
        "active_event_memory", "global_motion_proxy",
    ]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ["ai_unsafe_action_pred", "ai_detector_needed_pred", "ai_risk_class_pred"]:
        if col not in df.columns:
            df[col] = ""
    action = df.get("action_label", pd.Series("", index=df.index)).fillna("").astype(str)
    df["current_reuse_action"] = action.eq("REUSE_ACC").astype(float)
    df["current_lightweight_action"] = action.str.startswith("LIGHTWEIGHT").astype(float)
    df["current_detector_like_action"] = (
        action.str.startswith("DETECT_")
        | action.isin(["FALLBACK_P3_GUARD", "LEGACY_SAFE_P3_GUARD", "FORCED_REFRESH", "FALLBACK_P3_POLICY"])
    ).astype(float)
    df["known_guarded_safety_event"] = (
        df["closed_empty_blocked_final"].gt(0)
        | df["reuse_blocked_final"].gt(0)
        | df["lightweight_blocked_final"].gt(0)
        | df["ptz_closed_empty_kill_active"].gt(0)
        | df["closed_empty_blocked_under_ptz"].gt(0)
    ).astype(float)
    df["known_hard_video"] = df["video"].astype(str).isin(["continuousPan", "twoPositionPTZCam", "bridgeEntry", "cubicle"]).astype(float)
    return df


def build_ai_shadow_summary(root):
    df = _read_ai_shadow_frames(root)
    if df.empty:
        return pd.DataFrame()
    return pd.DataFrame([{
        "frames": len(df),
        "shadow_enabled_rate": df["ai_shadow_enabled"].mean(),
        "disagreement_rate": df["ai_disagree_with_current_action"].mean(),
        "unsafe_flag_rate": df["ai_would_flag_unsafe"].mean(),
        "detector_request_rate": df["ai_would_request_detector"].mean(),
        "block_reuse_rate": df["ai_would_block_reuse"].mean(),
        "block_lightweight_rate": df["ai_would_block_lightweight"].mean(),
        "mean_missing_features": df["ai_missing_feature_count"].mean(),
        "p95_missing_features": df["ai_missing_feature_count"].quantile(0.95),
        "mean_shadow_latency_ms": df["ai_shadow_latency_ms"].mean(),
        "p95_shadow_latency_ms": df["ai_shadow_latency_ms"].quantile(0.95),
        "known_safety_event_warning_rate": df.loc[df["known_guarded_safety_event"].gt(0), "ai_would_flag_unsafe"].mean()
        if df["known_guarded_safety_event"].gt(0).any() else 0.0,
    }])


def build_ai_shadow_video_summary(root):
    df = _read_ai_shadow_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        known = group["known_guarded_safety_event"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "ai_enabled_rate": group["ai_shadow_enabled"].mean(),
            "ai_disagreement_rate": group["ai_disagree_with_current_action"].mean(),
            "ai_unsafe_flag_rate": group["ai_would_flag_unsafe"].mean(),
            "ai_detector_request_rate": group["ai_would_request_detector"].mean(),
            "ai_block_reuse_rate": group["ai_would_block_reuse"].mean(),
            "ai_block_lightweight_rate": group["ai_would_block_lightweight"].mean(),
            "current_reuse_rate": group["current_reuse_action"].mean(),
            "current_lightweight_rate": group["current_lightweight_action"].mean(),
            "current_detector_like_rate": group["current_detector_like_action"].mean(),
            "known_guarded_safety_events": int(known.sum()),
            "known_guarded_safety_event_warning_rate": float(group.loc[known, "ai_would_flag_unsafe"].mean()) if known.any() else 0.0,
            "mean_missing_features": group["ai_missing_feature_count"].mean(),
            "mean_shadow_latency_ms": group["ai_shadow_latency_ms"].mean(),
            "p95_shadow_latency_ms": group["ai_shadow_latency_ms"].quantile(0.95),
            "mean_fmeasure": group["FMeasure"].mean(),
        })
    return pd.DataFrame(rows)


def build_ai_shadow_disagreement_summary(root):
    df = _read_ai_shadow_frames(root)
    if df.empty:
        return pd.DataFrame()
    return df.groupby(["category", "video", "action_label"], dropna=False).agg(
        frames=("pipeline", "size"),
        ai_disagreements=("ai_disagree_with_current_action", "sum"),
        ai_disagreement_rate=("ai_disagree_with_current_action", "mean"),
        ai_detector_requests=("ai_would_request_detector", "sum"),
        ai_unsafe_flags=("ai_would_flag_unsafe", "sum"),
        ai_block_reuse=("ai_would_block_reuse", "sum"),
        ai_block_lightweight=("ai_would_block_lightweight", "sum"),
        mean_shadow_latency_ms=("ai_shadow_latency_ms", "mean"),
    ).reset_index().sort_values(["ai_disagreements", "frames"], ascending=False)


def build_ai_shadow_safety_summary(root):
    df = _read_ai_shadow_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        known = group["known_guarded_safety_event"].gt(0)
        hard = group["known_hard_video"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "frames": len(group),
            "known_guarded_safety_events": int(known.sum()),
            "hard_video": bool(hard.any()),
            "ai_unsafe_flags": int(group["ai_would_flag_unsafe"].sum()),
            "ai_detector_requests": int(group["ai_would_request_detector"].sum()),
            "ai_block_reuse": int(group["ai_would_block_reuse"].sum()),
            "ai_block_lightweight": int(group["ai_would_block_lightweight"].sum()),
            "known_event_ai_warning_rate": float(group.loc[known, "ai_would_flag_unsafe"].mean()) if known.any() else 0.0,
            "hard_video_ai_warning_rate": float(group.loc[hard, "ai_would_flag_unsafe"].mean()) if hard.any() else 0.0,
            "mean_missing_features": float(group["ai_missing_feature_count"].mean()),
            "mean_shadow_latency_ms": float(group["ai_shadow_latency_ms"].mean()),
        })
    return pd.DataFrame(rows).sort_values(["hard_video", "known_guarded_safety_events", "ai_unsafe_flags"], ascending=False)

def _read_ai_subrisk_frames(root):
    usecols = [
        "category", "video", "pipeline", "frame_id", "evaluated_index",
        "action_label", "Event_State", "FMeasure", "latency_ms",
        "closed_empty_blocked_final", "reuse_blocked_final",
        "lightweight_blocked_final", "ptz_closed_empty_kill_active",
        "closed_empty_blocked_under_ptz", "active_event_memory", "global_motion_proxy",
        "ai_shadow_enabled", "ai_closed_empty_risk_pred", "ai_closed_empty_risk_score",
        "ai_reuse_risk_pred", "ai_reuse_risk_score",
        "ai_lightweight_p3_risk_pred", "ai_lightweight_p3_risk_score",
        "ai_legacy_cadence_risk_pred", "ai_legacy_cadence_risk_score",
        "ai_detector_needed_pred", "ai_detector_needed_score",
        "ai_lightweight_acc_allowed_pred", "ai_lightweight_acc_allowed_score",
        "ai_subrisk_any_flag", "ai_subrisk_latency_ms",
        "ai_subrisk_missing_feature_count",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "ai_shadow_enabled" not in df.columns:
        return pd.DataFrame()
    numeric = [
        "ai_shadow_enabled", "ai_closed_empty_risk_score", "ai_reuse_risk_score",
        "ai_lightweight_p3_risk_score", "ai_legacy_cadence_risk_score",
        "ai_detector_needed_score", "ai_lightweight_acc_allowed_score",
        "ai_subrisk_any_flag", "ai_subrisk_latency_ms", "ai_subrisk_missing_feature_count",
        "closed_empty_blocked_final", "reuse_blocked_final", "lightweight_blocked_final",
        "ptz_closed_empty_kill_active", "closed_empty_blocked_under_ptz",
    ]
    for col in numeric:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    pred_cols = [
        "ai_closed_empty_risk_pred", "ai_reuse_risk_pred",
        "ai_lightweight_p3_risk_pred", "ai_legacy_cadence_risk_pred",
        "ai_detector_needed_pred", "ai_lightweight_acc_allowed_pred",
    ]
    for col in pred_cols:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    df["ai_closed_empty_risk_flag"] = df["ai_closed_empty_risk_pred"].eq("1").astype(float)
    df["ai_reuse_risk_flag"] = df["ai_reuse_risk_pred"].eq("1").astype(float)
    df["ai_lightweight_p3_risk_flag"] = df["ai_lightweight_p3_risk_pred"].eq("1").astype(float)
    df["ai_legacy_cadence_risk_flag"] = df["ai_legacy_cadence_risk_pred"].eq("1").astype(float)
    df["ai_detector_needed_flag"] = df["ai_detector_needed_pred"].eq("1").astype(float)
    df["ai_lightweight_acc_not_allowed_flag"] = df["ai_lightweight_acc_allowed_pred"].eq("0").astype(float)
    df["known_guarded_safety_event"] = (
        df["closed_empty_blocked_final"].gt(0)
        | df["reuse_blocked_final"].gt(0)
        | df["lightweight_blocked_final"].gt(0)
        | df["ptz_closed_empty_kill_active"].gt(0)
        | df["closed_empty_blocked_under_ptz"].gt(0)
    ).astype(float)
    df["known_hard_video"] = df["video"].astype(str).isin(["continuousPan", "twoPositionPTZCam", "bridgeEntry", "cubicle"]).astype(float)
    df["ai_subrisk_or_detector_warning"] = (
        df["ai_subrisk_any_flag"].gt(0) | df["ai_detector_needed_flag"].gt(0)
    ).astype(float)
    return df


def build_ai_subrisk_shadow_summary(root):
    df = _read_ai_subrisk_frames(root)
    if df.empty:
        return pd.DataFrame()
    known = df["known_guarded_safety_event"].gt(0)
    hard = df["known_hard_video"].gt(0)
    normal = ~known
    return pd.DataFrame([{
        "frames": int(len(df)),
        "shadow_enabled_rate": float(df["ai_shadow_enabled"].mean()),
        "closed_empty_risk_flag_rate": float(df["ai_closed_empty_risk_flag"].mean()),
        "reuse_risk_flag_rate": float(df["ai_reuse_risk_flag"].mean()),
        "lightweight_p3_risk_flag_rate": float(df["ai_lightweight_p3_risk_flag"].mean()),
        "legacy_cadence_risk_flag_rate": float(df["ai_legacy_cadence_risk_flag"].mean()),
        "detector_needed_flag_rate": float(df["ai_detector_needed_flag"].mean()),
        "lightweight_acc_not_allowed_rate": float(df["ai_lightweight_acc_not_allowed_flag"].mean()),
        "subrisk_any_flag_rate": float(df["ai_subrisk_any_flag"].mean()),
        "subrisk_or_detector_warning_rate": float(df["ai_subrisk_or_detector_warning"].mean()),
        "normal_frame_subrisk_any_flag_rate": float(df.loc[normal, "ai_subrisk_any_flag"].mean()) if normal.any() else 0.0,
        "known_safety_event_subrisk_warning_rate": float(df.loc[known, "ai_subrisk_or_detector_warning"].mean()) if known.any() else 0.0,
        "hard_video_subrisk_warning_rate": float(df.loc[hard, "ai_subrisk_or_detector_warning"].mean()) if hard.any() else 0.0,
        "mean_missing_features": float(df["ai_subrisk_missing_feature_count"].mean()),
        "p95_missing_features": float(df["ai_subrisk_missing_feature_count"].quantile(0.95)),
        "mean_subrisk_latency_ms": float(df["ai_subrisk_latency_ms"].mean()),
        "p95_subrisk_latency_ms": float(df["ai_subrisk_latency_ms"].quantile(0.95)),
    }])


def build_ai_subrisk_video_summary(root):
    df = _read_ai_subrisk_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        known = group["known_guarded_safety_event"].gt(0)
        hard = group["known_hard_video"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "closed_empty_risk_flag_rate": float(group["ai_closed_empty_risk_flag"].mean()),
            "reuse_risk_flag_rate": float(group["ai_reuse_risk_flag"].mean()),
            "lightweight_p3_risk_flag_rate": float(group["ai_lightweight_p3_risk_flag"].mean()),
            "legacy_cadence_risk_flag_rate": float(group["ai_legacy_cadence_risk_flag"].mean()),
            "detector_needed_flag_rate": float(group["ai_detector_needed_flag"].mean()),
            "lightweight_acc_not_allowed_rate": float(group["ai_lightweight_acc_not_allowed_flag"].mean()),
            "subrisk_any_flag_rate": float(group["ai_subrisk_any_flag"].mean()),
            "known_guarded_safety_events": int(known.sum()),
            "known_event_subrisk_warning_rate": float(group.loc[known, "ai_subrisk_or_detector_warning"].mean()) if known.any() else 0.0,
            "hard_video": bool(hard.any()),
            "hard_video_subrisk_warning_rate": float(group.loc[hard, "ai_subrisk_or_detector_warning"].mean()) if hard.any() else 0.0,
            "mean_missing_features": float(group["ai_subrisk_missing_feature_count"].mean()),
            "mean_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].mean()),
            "p95_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].quantile(0.95)),
        })
    return pd.DataFrame(rows)


def build_ai_subrisk_latency_summary(root):
    df = _read_ai_subrisk_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for label, group in [("all", df), ("prediction_frames", df[df["ai_subrisk_latency_ms"].gt(0)])]:
        if group.empty:
            continue
        rows.append({
            "scope": label,
            "frames": int(len(group)),
            "mean_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].mean()),
            "p50_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].quantile(0.50)),
            "p95_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].quantile(0.95)),
            "max_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].max()),
            "mean_missing_features": float(group["ai_subrisk_missing_feature_count"].mean()),
            "p95_missing_features": float(group["ai_subrisk_missing_feature_count"].quantile(0.95)),
        })
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "scope": f"video_{category}_{video}",
            "frames": int(len(group)),
            "mean_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].mean()),
            "p50_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].quantile(0.50)),
            "p95_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].quantile(0.95)),
            "max_subrisk_latency_ms": float(group["ai_subrisk_latency_ms"].max()),
            "mean_missing_features": float(group["ai_subrisk_missing_feature_count"].mean()),
            "p95_missing_features": float(group["ai_subrisk_missing_feature_count"].quantile(0.95)),
        })
    return pd.DataFrame(rows)


def build_ai_subrisk_threshold_summary(root):
    df = _read_ai_subrisk_frames(root)
    if df.empty:
        return pd.DataFrame()
    targets = {
        "closed_empty_risk": "ai_closed_empty_risk_score",
        "reuse_risk": "ai_reuse_risk_score",
        "lightweight_p3_risk": "ai_lightweight_p3_risk_score",
        "legacy_cadence_risk": "ai_legacy_cadence_risk_score",
        "detector_needed": "ai_detector_needed_score",
        "lightweight_acc_allowed": "ai_lightweight_acc_allowed_score",
    }
    known = df["known_guarded_safety_event"].gt(0)
    rows = []
    for target, score_col in targets.items():
        if score_col not in df.columns:
            continue
        scores = pd.to_numeric(df[score_col], errors="coerce").fillna(0.0)
        for threshold in [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]:
            flag = scores.ge(threshold)
            if target == "lightweight_acc_allowed":
                flag = scores.lt(threshold)
            rows.append({
                "target": target,
                "threshold": threshold,
                "flag_definition": "score_below_threshold_not_allowed" if target == "lightweight_acc_allowed" else "score_at_or_above_threshold",
                "flag_rate": float(flag.mean()),
                "known_safety_event_flag_rate": float(flag[known].mean()) if known.any() else 0.0,
                "normal_frame_flag_rate": float(flag[~known].mean()) if (~known).any() else 0.0,
            })
    return pd.DataFrame(rows)


def _read_ai_intervention_frames(root):
    usecols = [
        "category", "video", "pipeline", "frame_id", "evaluated_index",
        "action_label", "Event_State", "FMeasure", "Recall", "yolo_called",
        "raw_frame_id",
        "active_event_memory",
        "foreground_risk",
        "reuse_age",
        "closed_empty_blocked_final", "reuse_blocked_final",
        "lightweight_blocked_final", "ptz_closed_empty_kill_active",
        "closed_empty_blocked_under_ptz", "event_closed_empty_final_count",
        "ai_intervention_enabled", "ai_intervention_mode", "ai_intervention_budget_profile",
        "ai_intervention_guard_active", "ai_intervention_guard_reason",
        "ai_intervention_blocked_no_guard", "ai_intervention_budget_remaining_detector",
        "ai_intervention_budget_remaining_reuse", "ai_intervention_budget_remaining_lightweight",
        "ai_intervention_budget_blocked", "ai_intervention_cadence_blocked",
        "ai_intervention_risk_high", "ai_intervention_applied",
        "ai_intervention_type", "ai_intervention_original_action",
        "ai_intervention_final_action", "ai_intervention_detector_requested",
        "ai_intervention_reuse_blocked", "ai_intervention_lightweight_blocked",
        "ai_intervention_closed_empty_blocked", "ai_intervention_legacy_blocked",
        "ai_intervention_dry_run", "ai_action_block_first_active",
        "ai_block_only_no_detector", "ai_detector_last_resort_used",
        "ai_detector_request_source", "ai_safe_replacement_source",
        "ai_detector_request_blocked_no_refresh_model",
        "ai_detector_request_blocked_interval", "ai_detector_request_blocked_budget",
        "ai_detector_request_event_refresh_specific",
        "ai_detector_request_rejected_event_foreground_only",
        "ai_sparse_detector_budget_active", "ai_detector_budget_used_per_100",
        "ai_detector_budget_remaining", "ai_detector_interval_remaining",
        "ai_event_foreground_block_only_active",
        "ai_event_foreground_block_only_reason",
        "ai_event_foreground_block_only_no_detector",
        "ai_event_foreground_safe_replacement_source",
        "ai_cubicle_like_event_continuity_active",
        "ai_cubicle_like_event_continuity_reason",
        "ai_cubicle_like_no_detector",
        "ai_cubicle_like_safe_replacement_source",
        "ai_cubicle_like_rejected_reason",
        "ai_cubicle_like_cap_used",
        "ai_cubicle_like_is_non_ptz_context",
        "ai_cubicle_like_camera_motion_score",
        "ai_cubicle_micro_bump_active",
        "ai_cubicle_micro_bump_reason",
        "ai_cubicle_micro_bump_no_detector",
        "ai_cubicle_micro_bump_cap_used",
        "ai_cubicle_micro_bump_rejected_reason",
        "ai_exact_cubicle_event_fn_stabilizer_active",
        "ai_exact_cubicle_event_fn_stabilizer_reason",
        "ai_exact_cubicle_event_fn_stabilizer_no_detector",
        "ai_exact_cubicle_event_fn_stabilizer_rejected_reason",
        "ai_exact_cubicle_event_fn_stabilizer_cap_used",
        "ai_exact_cubicle_event_fn_stabilizer_frame",
        "ai_exact_cubicle_event_fn_stabilizer_would_be_unprotected_fn",
        "ai_exact_cubicle_event_fn_stabilizer_safe_replacement_source",
        "ai_exact_cubicle_event_fn_pre_signal",
        "ai_exact_cubicle_event_fn_pre_signal_reason",
        "ai_exact_cubicle_event_fn_pre_signal_bypassed_early_normal",
        "ai_exact_cubicle_event_fn_pre_signal_frame",
        "ai_exact_cubicle_event_fn_pre_signal_action",
        "ai_exact_cubicle_event_fn_pre_signal_recent_memory",
        "ai_exact_cubicle_event_fn_pre_signal_foreground_risk",
        "ai_exact_cubicle_event_fn_final_normal_suppressed_after_presignal",
        "ai_exact_cubicle_late_event_rescue_active",
        "ai_exact_cubicle_late_event_rescue_reason",
        "ai_exact_cubicle_late_event_rescue_rejected_reason",
        "ai_exact_cubicle_late_event_rescue_no_detector",
        "ai_exact_cubicle_late_event_rescue_cap_used",
        "ai_exact_cubicle_late_event_rescue_frame",
        "ai_exact_cubicle_late_event_rescue_action",
        "ai_exact_cubicle_late_event_rescue_event_score",
        "ai_exact_cubicle_late_event_rescue_foreground_loss_score",
        "ai_exact_cubicle_late_event_rescue_active_memory",
        "ai_exact_cubicle_late_event_rescue_final_normal_suppressed",
        "ai_cubicle_live_mismatch_reserve_active",
        "ai_cubicle_live_mismatch_reserve_reason",
        "ai_cubicle_live_mismatch_reserve_rejected_reason",
        "ai_cubicle_live_mismatch_reserve_frame",
        "ai_cubicle_live_mismatch_reserve_no_detector",
        "ai_cubicle_live_mismatch_reserve_cap_used",
        "ai_non_cubicle_budget_reclaim_active",
        "ai_non_cubicle_budget_reclaim_rejected",
        "ai_non_cubicle_budget_reclaim_reason",
        "ai_non_cubicle_event_fg_cap_used",
        "ai_non_cubicle_event_fg_would_have_proposed_before_reclaim",
        "ai_non_cubicle_event_fg_reclaimed_count",
        "ai_non_cubicle_event_fg_preserved_count",
        "ai_lowframerate_trim_active",
        "ai_lowframerate_trim_rejected",
        "ai_lowframerate_trim_reason",
        "ai_lowframerate_trim_video",
        "ai_lowframerate_trim_frame",
        "ai_lowframerate_trim_would_have_proposed_before_trim",
        "ai_lowframerate_trim_reclaimed_count",
        "ai_lowframerate_trim_preserved_count",
        "ai_fountain01_quiet_guard_active",
        "ai_fountain01_quiet_guard_rejected",
        "ai_fountain01_quiet_guard_reason",
        "ai_fountain01_quiet_guard_suppressed_path",
        "ai_fountain01_quiet_guard_would_have_proposed_before_guard",
        "ai_fountain01_quiet_guard_reclaimed_count",
        "ai_fountain01_quiet_guard_preserved_count",
        "ai_lowframerate_targeted_retighten_active",
        "ai_lowframerate_targeted_retighten_rejected",
        "ai_lowframerate_targeted_retighten_reason",
        "ai_lowframerate_targeted_retighten_would_have_proposed_before_guard",
        "ai_lowframerate_targeted_retighten_reclaimed_count",
        "ai_lowframerate_targeted_retighten_preserved_count",
        "ai_port_lf_detector_retighten_active",
        "ai_port_lf_detector_retighten_reason",
        "ai_port_lf_detector_retighten_rejected_reason",
        "ai_port_lf_detector_retighten_suppressed_detector",
        "ai_port_lf_detector_retighten_kept_detector",
        "ai_port_lf_detector_retighten_kept_detector_reason",
        "ai_port_lf_detector_retighten_event_state",
        "ai_port_lf_detector_retighten_no_detector_fallback",
        "ai_port_lf_detector_retighten_created_unprotected_fn",
        "ai_port_lf_detector_retighten_protected_fn_detector_kept",
        "ai_port_lf_detector_retighten_suppressed_count",
        "ai_port_lf_detector_retighten_kept_count",
        "ai_port_lf_detector_retighten_protected_fn_detector_kept_count",
        "ai_port_lf_detector_retighten_created_unprotected_fn_count",
        "ai_port_lf_detector_retighten_v2_active",
        "ai_port_lf_detector_retighten_v2_reason",
        "ai_port_lf_detector_retighten_v2_rejected_reason",
        "ai_port_lf_detector_retighten_v2_suppressed_detector",
        "ai_port_lf_detector_retighten_v2_kept_detector",
        "ai_port_lf_detector_retighten_v2_kept_detector_reason",
        "ai_port_lf_detector_retighten_v2_suppressed_event_state",
        "ai_port_lf_detector_retighten_v2_true_emergency",
        "ai_port_lf_detector_retighten_v2_generic_refresh_not_emergency",
        "ai_port_lf_detector_retighten_v2_no_detector_fallback",
        "ai_port_lf_detector_retighten_v2_fallback_source",
        "ai_port_lf_detector_retighten_v2_created_unprotected_fn",
        "ai_port_lf_detector_retighten_v2_protected_fn_detector_kept",
        "ai_port_lf_detector_retighten_v2_suppressed_count",
        "ai_port_lf_detector_retighten_v2_kept_count",
        "ai_port_lf_detector_retighten_v2_actual_fn_detector_kept_count",
        "ai_port_lf_detector_retighten_v2_true_emergency_detector_kept_count",
        "ai_port_lf_detector_retighten_v2_generic_refresh_suppressed_count",
        "ai_port_lf_detector_retighten_v2_fp_tn_suppressed_count",
        "ai_port_lf_detector_retighten_v2_created_unprotected_fn_count",
        "ai_port_lf_detector_retighten_v3_active",
        "ai_port_lf_detector_retighten_v3_decision_time_event_state",
        "ai_port_lf_detector_retighten_v3_final_event_state",
        "ai_port_lf_detector_retighten_v3_suppressed_detector",
        "ai_port_lf_detector_retighten_v3_kept_detector",
        "ai_port_lf_detector_retighten_v3_kept_detector_reason",
        "ai_port_lf_detector_retighten_v3_suppressed_reason",
        "ai_port_lf_detector_retighten_v3_generic_refresh_not_emergency",
        "ai_port_lf_detector_retighten_v3_generic_event_fg_not_likely_fn",
        "ai_port_lf_detector_retighten_v3_true_emergency",
        "ai_port_lf_detector_retighten_v3_explicit_likely_unprotected_fn",
        "ai_port_lf_detector_retighten_v3_no_detector_fallback",
        "ai_port_lf_detector_retighten_v3_fallback_source",
        "ai_port_lf_detector_retighten_v3_created_unprotected_fn",
        "ai_port_lf_detector_retighten_v3_protected_fn_detector_kept",
        "ai_port_lf_detector_retighten_v3_suppressed_count",
        "ai_port_lf_detector_retighten_v3_kept_count",
        "ai_port_lf_detector_retighten_v3_actual_fn_detector_kept_count",
        "ai_port_lf_detector_retighten_v3_true_emergency_detector_kept_count",
        "ai_port_lf_detector_retighten_v3_generic_refresh_suppressed_count",
        "ai_port_lf_detector_retighten_v3_final_fp_tn_suppressed_count",
        "ai_port_lf_detector_retighten_v3_created_unprotected_fn_count",
        "ai_port_lf_detector_retighten_v4_active",
        "ai_port_lf_detector_retighten_v4_suppressed_detector",
        "ai_port_lf_detector_retighten_v4_kept_detector",
        "ai_port_lf_detector_retighten_v4_kept_detector_reason",
        "ai_port_lf_detector_retighten_v4_suppressed_reason",
        "ai_port_lf_detector_retighten_v4_pre_fn_context_kept",
        "ai_port_lf_detector_retighten_v4_final_event_state",
        "ai_port_lf_detector_retighten_v4_created_unprotected_fn",
        "ai_port_lf_detector_retighten_v4_suppressed_count",
        "ai_port_lf_detector_retighten_v4_kept_count",
        "ai_port_lf_detector_retighten_v4_actual_fn_detector_kept_count",
        "ai_port_lf_detector_retighten_v4_true_emergency_detector_kept_count",
        "ai_port_lf_detector_retighten_v4_pre_fn_context_kept_count",
        "ai_port_lf_detector_retighten_v4_final_fp_tn_suppressed_count",
        "ai_port_lf_detector_retighten_v4_created_unprotected_fn_count",
        "ai_port_v4_preserve_active",
        "ai_port_lf_v4_hard_lock_active",
        "ai_port_lf_v4_hard_lock_deviation_from_4e4",
        "ai_port_lf_post_suppression_holdout_active",
        "ai_port_lf_post_suppression_holdout_reason",
        "ai_port_lf_post_suppression_holdout_rejected_reason",
        "ai_port_lf_post_suppression_holdout_no_detector",
        "ai_port_lf_post_suppression_holdout_frame",
        "ai_port_lf_post_suppression_holdout_protected_event_fn",
        "ai_port_lf_post_suppression_holdout_final_normal_suppressed",
        "ai_port_lf_post_suppression_holdout_count",
        "ai_port_lf_post_suppression_holdout_protected_event_fn_count",
        "ai_ptz_intermittent_pan_cap_active",
        "ai_ptz_intermittent_pan_cap_rejected",
        "ai_ptz_intermittent_pan_cap_reason",
        "ai_ptz_intermittent_pan_would_have_proposed_before_cap",
        "ai_ptz_intermittent_pan_reclaimed_count",
        "ai_ptz_intermittent_pan_preserved_count",
        "ai_ptz_intermittent_pan_fn_rescue_active",
        "ai_ptz_intermittent_pan_fn_rescue_reason",
        "ai_ptz_intermittent_pan_fn_rescue_rejected_reason",
        "ai_ptz_intermittent_pan_fn_rescue_no_detector",
        "ai_ptz_intermittent_pan_fn_rescue_frame",
        "ai_ptz_intermittent_pan_fn_rescue_cap_used",
        "ai_ptz_intermittent_pan_preserve_2k_rescue_active",
        "ai_ptz_intermittent_pan_preserve_2k_rescue_reason",
        "ai_ptz_intermittent_pan_preserve_2k_rescue_protected_before_later_caps",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_active",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_reason",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_rejected_reason",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_frame",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_no_detector",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_cap_used",
        "ai_copymachine_shadow_guard_active",
        "ai_copymachine_shadow_guard_rejected",
        "ai_copymachine_shadow_guard_reason",
        "ai_copymachine_shadow_would_have_proposed_before_guard",
        "ai_copymachine_shadow_reclaimed_count",
        "ai_copymachine_shadow_preserved_count",
        "ai_copymachine_fn_rescue_active",
        "ai_copymachine_fn_rescue_reason",
        "ai_copymachine_fn_rescue_rejected_reason",
        "ai_copymachine_fn_rescue_no_detector",
        "ai_copymachine_fn_rescue_frame",
        "ai_copymachine_fn_rescue_cap_used",
        "ai_copymachine_rescue_first_candidate",
        "ai_copymachine_rescue_first_active",
        "ai_copymachine_rescue_first_reason",
        "ai_copymachine_rescue_first_protected_before_cap",
        "ai_copymachine_rescue_first_rejected_reason",
        "ai_copymachine_rescue_first_no_detector",
        "ai_copymachine_rescue_first_final_normal_suppressed",
        "ai_copymachine_live_cap_reserve_active",
        "ai_copymachine_live_cap_reserve_reason",
        "ai_copymachine_live_cap_reserve_rejected_reason",
        "ai_copymachine_live_cap_reserve_no_detector",
        "ai_copymachine_live_cap_reserve_cap_used",
        "ai_copymachine_live_cap_reserve_frame",
        "ai_copymachine_cap_suppressed_generic_only",
        "ai_copymachine_cap_suppressed_generic_count",
        "ai_parking_iom_rescue_candidate",
        "ai_parking_iom_rescue_active",
        "ai_parking_iom_rescue_reason",
        "ai_parking_iom_rescue_rejected_reason",
        "ai_parking_iom_rescue_no_detector",
        "ai_parking_iom_rescue_frame",
        "ai_parking_iom_rescue_cap_used",
        "ai_parking_iom_rescue_first_protected_before_cap",
        "ai_parking_iom_cap_active",
        "ai_parking_iom_cap_suppressed_generic_only",
        "ai_parking_iom_cap_reclaimed_count",
        "ai_parking_iom_cap_preserved_count",
        "ai_parking_iom_final_normal_suppressed",
        "ai_parking_iom_preserve_fn_risk_candidate",
        "ai_parking_iom_preserve_fn_risk_active",
        "ai_parking_iom_preserve_fn_risk_reason",
        "ai_parking_iom_preserve_fn_risk_rejected_reason",
        "ai_parking_iom_preserve_fn_risk_protected_before_cap",
        "ai_parking_iom_preserve_fn_risk_count",
        "ai_parking_live_cap_reserve_active",
        "ai_parking_live_cap_reserve_reason",
        "ai_parking_live_cap_reserve_rejected_reason",
        "ai_parking_live_cap_reserve_no_detector",
        "ai_parking_live_cap_reserve_cap_used",
        "ai_parking_live_cap_reserve_frame",
        "ai_parking_live_burst_bridge_active",
        "ai_parking_live_burst_bridge_reason",
        "ai_parking_live_burst_bridge_rejected_reason",
        "ai_parking_live_burst_bridge_no_detector",
        "ai_parking_live_burst_bridge_cap_used",
        "ai_parking_live_burst_bridge_frame",
        "ai_parking_iom_cap_suppressed_generic_nonrisk_only",
        "ai_parking_iom_cap_skipped_preserved_fn_risk",
        "ai_parking_iom_cap_skipped_preserved_fn_risk_count",
        "ai_parking_iom_cap_soft_budget_exceeded",
        "ai_parking_iom_rescue_likely_unprotected_fn",
        "ai_parking_iom_rescue_protected_event_fn",
        "ai_parking_iom_rescue_false_positive_activation",
        "ai_parking_carryover_lock_active",
        "ai_parking_carryover_lock_reason",
        "ai_parking_carryover_lock_rejected_reason",
        "ai_parking_carryover_lock_no_detector",
        "ai_parking_carryover_lock_frame",
        "ai_parking_carryover_lock_cap_used",
        "ai_parking_carryover_lock_protected_event_fn",
        "ai_parking_carryover_lock_final_normal_suppressed",
        "ai_parking_iom_post_preservation_trim_active",
        "ai_parking_iom_post_preservation_trim_reason",
        "ai_parking_iom_post_preservation_trim_rejected_reason",
        "ai_parking_iom_post_preservation_trim_candidate",
        "ai_parking_iom_post_preservation_trim_suppressed_generic_nonrisk",
        "ai_parking_iom_post_preservation_trim_skipped_preserved_fn_risk",
        "ai_parking_iom_post_preservation_trim_skipped_rescue_frame",
        "ai_parking_iom_post_preservation_trim_skipped_likely_unprotected_fn",
        "ai_parking_iom_post_preservation_trim_count",
        "ai_parking_iom_post_preservation_trim_final_rate",
        "ai_parking_post_lock_trim_active",
        "ai_parking_post_lock_trim_candidate",
        "ai_parking_post_lock_trim_reason",
        "ai_parking_post_lock_trim_rejected_reason",
        "ai_parking_post_lock_trim_hard_protected",
        "ai_parking_post_lock_trim_soft_candidate",
        "ai_parking_post_lock_trim_suppressed",
        "ai_parking_post_lock_trim_skipped_hard_protected",
        "ai_parking_post_lock_trim_skipped_fn_protected",
        "ai_parking_post_lock_trim_skipped_likely_unprotected_fn",
        "ai_parking_post_lock_trim_count",
        "ai_parking_post_lock_trim_final_rate",
        "ai_parking_post_lock_trim_accidental_hard_trim_count",
        "ai_parking_post_lock_trim_accidental_fn_protected_trim_count",
        "ai_parking_post_lock_deduplicate_active",
        "ai_parking_post_lock_deduplicate_count",
        "ai_parking_restore_4d3_trim_active",
        "ai_parking_restore_4d3_trim_count",
        "ai_parking_restore_4d3_trim_reason",
        "ai_parking_restore_4d3_trim_blocked_by_later_hardprotect",
        "ai_parking_post_lock_trim_4d5_active",
        "ai_parking_post_lock_trim_4d5_candidate",
        "ai_parking_post_lock_trim_4d5_soft_candidate",
        "ai_parking_post_lock_trim_4d5_rejected_reason",
        "ai_parking_post_lock_trim_4d5_suppressed",
        "ai_parking_post_lock_trim_4d5_skipped_fn_protected",
        "ai_parking_post_lock_trim_4d5_skipped_rescue_frame",
        "ai_parking_post_lock_trim_4d5_skipped_likely_unprotected_fn",
        "ai_parking_post_lock_trim_4d5_trim_count",
        "ai_parking_post_lock_trim_4d5_final_rate",
        "ai_parking_post_lock_trim_4d5_accidental_fn_protected_trim_count",
        "ai_parking_post_lock_trim_4d5_accidental_rescue_trim_count",
        "ai_parking_post_lock_trim_4d6_active",
        "ai_parking_post_lock_trim_4d6_candidate",
        "ai_parking_post_lock_trim_4d6_suppressed",
        "ai_parking_post_lock_trim_4d6_reason",
        "ai_parking_post_lock_trim_4d6_rejected_reason",
        "ai_parking_post_lock_trim_4d6_trim_count",
        "ai_parking_post_lock_trim_4d6_final_rate",
        "ai_parking_post_lock_trim_4d6_accidental_fn_protected_trim_count",
        "ai_parking_post_lock_trim_4d6_accidental_rescue_trim_count",
        "ai_parking_restore_4d6_trim_stack_active",
        "ai_parking_restore_4d6_trim_4d3_count",
        "ai_parking_restore_4d6_trim_4d5_count",
        "ai_parking_restore_4d6_trim_4d6_count",
        "ai_parking_restore_4d6_trim_extra_count",
        "ai_parking_restore_4d6_trim_final_rate",
        "ai_parking_restore_4d6_trim_accidental_fn_protected_trim_count",
        "ai_parking_restore_4d6_trim_accidental_rescue_trim_count",
        "ai_parking_restore_4d6_fn_fallback_active",
        "ai_parking_restore_4d6_fn_fallback_no_detector",
        "ai_parking_restore_4d6_fn_fallback_protected_event_fn",
        "ai_parking_restore_4d6_fn_fallback_count",
        "ai_parking_restore_4d6_fn_fallback_protected_event_fn_count",
        "ai_parking_4d6_hard_restore_active",
        "ai_parking_4d6_hard_restore_final_rate",
        "ai_parking_4d6_hard_restore_accidental_fn_trim_count",
        "ai_parking_4d6_hard_restore_accidental_rescue_trim_count",
        "ai_parking_4d6_hard_restore_safe_trim_active",
        "ai_parking_4d6_hard_restore_safe_trim_count",
        "ai_parking_4d6_hard_restore_fn_fallback_active",
        "ai_parking_4d6_hard_restore_fn_fallback_no_detector",
        "ai_parking_4d6_hard_restore_fn_fallback_protected_event_fn",
        "ai_parking_4d6_hard_restore_fn_fallback_count",
        "ai_parking_4d6_hard_restore_fn_fallback_protected_event_fn_count",
        "ai_sofa_iom_rescue_candidate",
        "ai_sofa_iom_rescue_active",
        "ai_sofa_iom_rescue_reason",
        "ai_sofa_iom_rescue_rejected_reason",
        "ai_sofa_iom_rescue_no_detector",
        "ai_sofa_iom_rescue_frame",
        "ai_sofa_iom_rescue_cap_used",
        "ai_sofa_iom_rescue_protected_event_fn",
        "ai_sofa_iom_rescue_final_normal_suppressed",
        "ai_sofa_iom_rescue_first_protected_before_cap",
        "ai_sofa_iom_carryover_lock_active",
        "ai_sofa_iom_carryover_lock_reason",
        "ai_sofa_iom_carryover_lock_rejected_reason",
        "ai_sofa_iom_carryover_lock_no_detector",
        "ai_sofa_iom_carryover_lock_frame",
        "ai_sofa_iom_carryover_lock_cap_used",
        "ai_sofa_iom_carryover_lock_protected_event_fn",
        "ai_sofa_iom_carryover_lock_final_normal_suppressed",
        "ai_sofa_iom_proposal_guard_active",
        "ai_sofa_iom_proposal_guard_suppressed_generic_nonrisk",
        "ai_sofa_iom_proposal_guard_skipped_rescue_frame",
        "ai_sofa_iom_proposal_guard_suppressed_count",
        "ai_sofa_iom_proposal_guard_skipped_rescue_count",
        "ai_sofa_iom_proposal_guard_final_rate",
        "ai_snowfall_weather_rescue_candidate",
        "ai_snowfall_weather_rescue_active",
        "ai_snowfall_weather_rescue_reason",
        "ai_snowfall_weather_rescue_rejected_reason",
        "ai_snowfall_weather_rescue_no_detector",
        "ai_snowfall_weather_rescue_frame",
        "ai_snowfall_weather_rescue_cap_used",
        "ai_snowfall_weather_rescue_protected_event_fn",
        "ai_snowfall_weather_rescue_final_normal_suppressed",
        "ai_snowfall_weather_localized_guard_active",
        "ai_snowfall_weather_localized_guard_rejected_reason",
        "ai_snowfall_weather_proposal_guard_active",
        "ai_snowfall_weather_proposal_guard_suppressed_generic_nonrisk",
        "ai_snowfall_weather_proposal_guard_skipped_rescue_frame",
        "ai_snowfall_weather_proposal_guard_suppressed_count",
        "ai_snowfall_weather_proposal_guard_skipped_rescue_count",
        "ai_snowfall_weather_proposal_guard_final_rate",
        "ai_snowfall_weather_possible_mask_quality_exposure",
        "ai_snowfall_actual_fn_rescue_candidate",
        "ai_snowfall_actual_fn_rescue_active",
        "ai_snowfall_actual_fn_rescue_reason",
        "ai_snowfall_actual_fn_rescue_rejected_reason",
        "ai_snowfall_actual_fn_rescue_no_detector",
        "ai_snowfall_actual_fn_rescue_frame",
        "ai_snowfall_actual_fn_rescue_protected_event_fn",
        "ai_snowfall_actual_fn_rescue_final_normal_suppressed",
        "ai_snowfall_actual_fn_rescue_cap_used",
        "ai_snowfall_actual_fn_cap_increase_active",
        "ai_snowfall_actual_fn_cap_increase_reason",
        "ai_snowfall_actual_fn_rescue_cap_exhausted_after_d3",
        "ai_snowfall_mask_quality_row_skipped",
        "ai_snowfall_weather_budget_available_but_actual_fn_rescued",
        "ai_parking_live_post_trim_2q3_active",
        "ai_parking_live_post_trim_2q3_candidate",
        "ai_parking_live_post_trim_2q3_reason",
        "ai_parking_live_post_trim_2q3_rejected_reason",
        "ai_parking_live_post_trim_2q3_suppressed_generic_nonrisk",
        "ai_parking_live_post_trim_2q3_skipped_rescue_frame",
        "ai_parking_live_post_trim_2q3_skipped_live_reserve_frame",
        "ai_parking_live_post_trim_2q3_skipped_preserved_fn_risk",
        "ai_parking_live_post_trim_2q3_skipped_likely_unprotected_fn",
        "ai_parking_live_post_trim_2q3_trim_count",
        "ai_parking_live_post_trim_2q3_final_rate",
        "ai_parking_live_post_trim_2q3_accidental_protected_trim_count",
        "ai_parking_soft_preserved_trim_active",
        "ai_parking_soft_preserved_trim_candidate",
        "ai_parking_soft_preserved_trim_reason",
        "ai_parking_soft_preserved_trim_rejected_reason",
        "ai_parking_soft_preserved_trim_hard_protected",
        "ai_parking_soft_preserved_trim_soft_preserved",
        "ai_parking_soft_preserved_trim_suppressed",
        "ai_parking_soft_preserved_trim_skipped_hard_protected",
        "ai_parking_soft_preserved_trim_skipped_rescue_frame",
        "ai_parking_soft_preserved_trim_skipped_live_reserve_frame",
        "ai_parking_soft_preserved_trim_skipped_likely_unprotected_fn",
        "ai_parking_soft_preserved_trim_trim_count",
        "ai_parking_soft_preserved_trim_final_rate",
        "ai_parking_soft_preserved_trim_accidental_hard_protected_trim_count",
        "ai_turbulence2_pressure_guard_active",
        "ai_turbulence2_pressure_guard_rejected",
        "ai_turbulence2_pressure_guard_reason",
        "ai_turbulence2_pressure_guard_suppressed_generic_nonrisk",
        "ai_turbulence2_pressure_guard_suppressed_detector_refresh",
        "ai_turbulence2_pressure_guard_reclaimed_count",
        "ai_turbulence2_pressure_guard_preserved_count",
        "ai_turbulence2_fn_rescue_candidate",
        "ai_turbulence2_fn_rescue_active",
        "ai_turbulence2_fn_rescue_reason",
        "ai_turbulence2_fn_rescue_rejected_reason",
        "ai_turbulence2_fn_rescue_no_detector",
        "ai_turbulence2_fn_rescue_frame",
        "ai_turbulence2_fn_rescue_protected_event_fn",
        "ai_turbulence2_fn_rescue_final_normal_suppressed",
        "ai_turbulence2_rescue_protected_before_guard",
        "ai_turbulence2_carryover_reserve_candidate",
        "ai_turbulence2_carryover_reserve_active",
        "ai_turbulence2_carryover_reserve_reason",
        "ai_turbulence2_carryover_reserve_rejected_reason",
        "ai_turbulence2_carryover_reserve_no_detector",
        "ai_turbulence2_carryover_reserve_frame",
        "ai_turbulence2_carryover_reserve_cap_used",
        "ai_turbulence2_carryover_reserve_protected_event_fn",
        "ai_turbulence2_carryover_reserve_final_normal_suppressed",
        "ai_thermal_lakeside_fn_rescue_candidate",
        "ai_thermal_lakeside_fn_rescue_active",
        "ai_thermal_lakeside_fn_rescue_reason",
        "ai_thermal_lakeside_fn_rescue_rejected_reason",
        "ai_thermal_lakeside_fn_rescue_no_detector",
        "ai_thermal_lakeside_fn_rescue_frame",
        "ai_thermal_lakeside_fn_rescue_cap_used",
        "ai_thermal_lakeside_fn_rescue_protected_event_fn",
        "ai_thermal_lakeside_fn_rescue_final_normal_suppressed",
        "ai_thermal_lakeside_early_memory_rescue_candidate",
        "ai_thermal_lakeside_early_memory_rescue_active",
        "ai_thermal_lakeside_early_memory_rescue_reason",
        "ai_thermal_lakeside_early_memory_rescue_rejected_reason",
        "ai_thermal_lakeside_early_memory_rescue_protected_event_fn",
        "ai_thermal_lakeside_post_rescue_trim_active",
        "ai_thermal_lakeside_post_rescue_trim_candidate",
        "ai_thermal_lakeside_post_rescue_trim_reason",
        "ai_thermal_lakeside_post_rescue_trim_rejected_reason",
        "ai_thermal_lakeside_post_rescue_trim_hard_protected",
        "ai_thermal_lakeside_post_rescue_trim_soft_candidate",
        "ai_thermal_lakeside_post_rescue_trim_suppressed",
        "ai_thermal_lakeside_post_rescue_trim_skipped_hard_protected",
        "ai_thermal_lakeside_post_rescue_trim_skipped_fn_protected",
        "ai_thermal_lakeside_post_rescue_trim_count",
        "ai_thermal_lakeside_post_rescue_trim_final_rate",
        "ai_thermal_lakeside_post_rescue_trim_accidental_hard_protected_trim_count",
        "ai_thermal_lakeside_rescue_cap_refine_active",
        "ai_thermal_lakeside_rescue_cap_refine_reason",
        "ai_thermal_lakeside_hard_protect_refine_active",
        "ai_thermal_lakeside_hard_protect_refine_reason",
        "ai_thermal_lakeside_fg_loss_only_soft_candidate",
        "ai_thermal_lakeside_fg_loss_soft_trim_candidate",
        "ai_thermal_lakeside_fg_loss_soft_trim_suppressed",
        "ai_thermal_lakeside_fg_loss_soft_trim_skipped_hard_protected",
        "ai_thermal_lakeside_fg_loss_soft_trim_skipped_likely_unprotected_fn",
        "ai_thermal_lakeside_fg_loss_soft_trim_skipped_rescue_frame",
        "ai_thermal_lakeside_fg_loss_soft_trim_count",
        "ai_thermal_lakeside_fg_loss_soft_trim_final_rate",
        "ai_thermal_lakeside_fg_loss_soft_trim_accidental_hard_protected_trim_count",
        "ai_thermal_lakeside_detector_retighten_active",
        "ai_thermal_lakeside_detector_retighten_reason",
        "ai_thermal_lakeside_highscore_soften_active",
        "ai_thermal_lakeside_highscore_soften_reason",
        "ai_thermal_lakeside_highscore_soften_rejected_reason",
        "ai_thermal_lakeside_highscore_soft_candidate",
        "ai_thermal_lakeside_highscore_soft_trim_candidate",
        "ai_thermal_lakeside_highscore_soft_trim_suppressed",
        "ai_thermal_lakeside_highscore_soft_trim_skipped_hard_protected",
        "ai_thermal_lakeside_highscore_soft_trim_skipped_rescue_frame",
        "ai_thermal_lakeside_highscore_soft_trim_skipped_likely_unprotected_fn",
        "ai_thermal_lakeside_highscore_soft_trim_count",
        "ai_thermal_lakeside_highscore_soft_trim_final_rate",
        "ai_thermal_lakeside_highscore_soft_trim_accidental_hard_protected_trim_count",
        "ai_thermal_lakeside_highscore_soft_trim_accidental_rescue_trim_count",
        "ai_thermal_lakeside_drift_recap_active",
        "ai_thermal_lakeside_drift_recap_suppressed",
        "ai_thermal_lakeside_drift_recap_reason",
        "ai_thermal_lakeside_drift_recap_final_rate",
        "ai_thermal_lakeside_drift_recap_accidental_hard_trim_count",
        "ai_thermal_lakeside_carryover_lock_active",
        "ai_thermal_lakeside_carryover_lock_reason",
        "ai_thermal_lakeside_carryover_lock_trim_count",
        "ai_step4d3_carryover_lock_video",
        "ai_tunnel_exit_lf_preserve_fn_risk_candidate",
        "ai_tunnel_exit_lf_preserve_fn_risk_active",
        "ai_tunnel_exit_lf_preserve_fn_risk_reason",
        "ai_tunnel_exit_lf_preserve_fn_risk_rejected_reason",
        "ai_tunnel_exit_lf_rescue_candidate",
        "ai_tunnel_exit_lf_rescue_active",
        "ai_tunnel_exit_lf_rescue_reason",
        "ai_tunnel_exit_lf_rescue_rejected_reason",
        "ai_tunnel_exit_lf_rescue_no_detector",
        "ai_tunnel_exit_lf_rescue_protected_event_fn",
        "ai_tunnel_exit_lf_rescue_final_normal_suppressed",
        "ai_tunnel_exit_lf_post_trim_active",
        "ai_tunnel_exit_lf_post_trim_suppressed_generic_nonrisk",
        "ai_tunnel_exit_lf_post_trim_skipped_preserved_fn_risk",
        "ai_tunnel_exit_lf_post_trim_skipped_rescue_frame",
        "ai_tunnel_exit_lf_post_trim_final_rate",
        "ai_normal_frame_suppressor_active", "ai_normal_frame_suppressor_reason",
        "ai_final_normal_frame_suppressor_active",
        "ai_final_normal_frame_suppressor_reason",
        "ai_final_normal_frame_suppressed_path",
        "ai_final_normal_frame_suppressed_video",
        "ai_final_normal_frame_suppressed_frame",
        "ai_live_mismatch_final_normal_suppressed",
        "ai_live_reserve_final_normal_suppressed",
        "ai_live_reserve_trim_skipped",
        "ai_intervention_budget_remaining_closed_empty",
        "ai_event_foreground_risk_pred", "ai_event_foreground_risk_score",
        "ai_foreground_loss_risk_pred", "ai_foreground_loss_risk_score",
        "ai_event_continuity_risk_pred", "ai_event_continuity_risk_score",
        "ai_detector_refresh_needed_for_event_pred", "ai_detector_refresh_needed_for_event_score",
    ]
    df = read_guarded_frames(root, usecols)
    if df.empty or "ai_intervention_enabled" not in df.columns:
        return pd.DataFrame()
    numeric = [
        "FMeasure", "Recall", "yolo_called", "active_event_memory", "foreground_risk", "reuse_age", "closed_empty_blocked_final",
        "reuse_blocked_final", "lightweight_blocked_final", "ptz_closed_empty_kill_active",
        "closed_empty_blocked_under_ptz", "event_closed_empty_final_count",
        "ai_intervention_enabled", "ai_intervention_guard_active",
        "ai_intervention_blocked_no_guard", "ai_intervention_budget_remaining_detector",
        "ai_intervention_budget_remaining_reuse", "ai_intervention_budget_remaining_lightweight",
        "ai_intervention_budget_remaining_closed_empty",
        "ai_intervention_budget_blocked", "ai_intervention_cadence_blocked",
        "ai_intervention_risk_high", "ai_intervention_applied",
        "ai_intervention_detector_requested", "ai_intervention_reuse_blocked",
        "ai_intervention_lightweight_blocked", "ai_intervention_closed_empty_blocked",
        "ai_intervention_legacy_blocked", "ai_intervention_dry_run",
        "ai_action_block_first_active", "ai_block_only_no_detector",
        "ai_detector_last_resort_used", "ai_detector_request_blocked_no_refresh_model",
        "ai_detector_request_blocked_interval", "ai_detector_request_blocked_budget",
        "ai_detector_request_event_refresh_specific",
        "ai_detector_request_rejected_event_foreground_only",
        "ai_sparse_detector_budget_active", "ai_detector_budget_used_per_100",
        "ai_detector_budget_remaining", "ai_detector_interval_remaining",
        "ai_event_foreground_block_only_active",
        "ai_event_foreground_block_only_no_detector",
        "ai_cubicle_like_event_continuity_active",
        "ai_cubicle_like_no_detector",
        "ai_cubicle_like_cap_used",
        "ai_cubicle_like_is_non_ptz_context",
        "ai_cubicle_like_camera_motion_score",
        "ai_cubicle_micro_bump_active",
        "ai_cubicle_micro_bump_no_detector",
        "ai_cubicle_micro_bump_cap_used",
        "ai_exact_cubicle_event_fn_stabilizer_active",
        "ai_exact_cubicle_event_fn_stabilizer_no_detector",
        "ai_exact_cubicle_event_fn_stabilizer_cap_used",
        "ai_exact_cubicle_event_fn_stabilizer_would_be_unprotected_fn",
        "ai_exact_cubicle_event_fn_pre_signal",
        "ai_exact_cubicle_event_fn_pre_signal_bypassed_early_normal",
        "ai_exact_cubicle_event_fn_pre_signal_recent_memory",
        "ai_exact_cubicle_event_fn_pre_signal_foreground_risk",
        "ai_exact_cubicle_event_fn_final_normal_suppressed_after_presignal",
        "ai_exact_cubicle_late_event_rescue_active",
        "ai_exact_cubicle_late_event_rescue_no_detector",
        "ai_exact_cubicle_late_event_rescue_cap_used",
        "ai_exact_cubicle_late_event_rescue_event_score",
        "ai_exact_cubicle_late_event_rescue_foreground_loss_score",
        "ai_exact_cubicle_late_event_rescue_active_memory",
        "ai_exact_cubicle_late_event_rescue_final_normal_suppressed",
        "ai_cubicle_live_mismatch_reserve_active",
        "ai_cubicle_live_mismatch_reserve_no_detector",
        "ai_cubicle_live_mismatch_reserve_cap_used",
        "ai_non_cubicle_budget_reclaim_active",
        "ai_non_cubicle_budget_reclaim_rejected",
        "ai_non_cubicle_event_fg_cap_used",
        "ai_non_cubicle_event_fg_would_have_proposed_before_reclaim",
        "ai_non_cubicle_event_fg_reclaimed_count",
        "ai_non_cubicle_event_fg_preserved_count",
        "ai_lowframerate_trim_active",
        "ai_lowframerate_trim_rejected",
        "ai_lowframerate_trim_would_have_proposed_before_trim",
        "ai_lowframerate_trim_reclaimed_count",
        "ai_lowframerate_trim_preserved_count",
        "ai_fountain01_quiet_guard_active",
        "ai_fountain01_quiet_guard_rejected",
        "ai_fountain01_quiet_guard_would_have_proposed_before_guard",
        "ai_fountain01_quiet_guard_reclaimed_count",
        "ai_fountain01_quiet_guard_preserved_count",
        "ai_lowframerate_targeted_retighten_active",
        "ai_lowframerate_targeted_retighten_rejected",
        "ai_lowframerate_targeted_retighten_would_have_proposed_before_guard",
        "ai_lowframerate_targeted_retighten_reclaimed_count",
        "ai_lowframerate_targeted_retighten_preserved_count",
        "ai_port_lf_detector_retighten_active",
        "ai_port_lf_detector_retighten_suppressed_detector",
        "ai_port_lf_detector_retighten_kept_detector",
        "ai_port_lf_detector_retighten_no_detector_fallback",
        "ai_port_lf_detector_retighten_created_unprotected_fn",
        "ai_port_lf_detector_retighten_protected_fn_detector_kept",
        "ai_port_lf_detector_retighten_suppressed_count",
        "ai_port_lf_detector_retighten_kept_count",
        "ai_port_lf_detector_retighten_protected_fn_detector_kept_count",
        "ai_port_lf_detector_retighten_created_unprotected_fn_count",
        "ai_port_lf_detector_retighten_v2_active",
        "ai_port_lf_detector_retighten_v2_suppressed_detector",
        "ai_port_lf_detector_retighten_v2_kept_detector",
        "ai_port_lf_detector_retighten_v2_true_emergency",
        "ai_port_lf_detector_retighten_v2_generic_refresh_not_emergency",
        "ai_port_lf_detector_retighten_v2_no_detector_fallback",
        "ai_port_lf_detector_retighten_v2_created_unprotected_fn",
        "ai_port_lf_detector_retighten_v2_protected_fn_detector_kept",
        "ai_port_lf_detector_retighten_v2_suppressed_count",
        "ai_port_lf_detector_retighten_v2_kept_count",
        "ai_port_lf_detector_retighten_v2_actual_fn_detector_kept_count",
        "ai_port_lf_detector_retighten_v2_true_emergency_detector_kept_count",
        "ai_port_lf_detector_retighten_v2_generic_refresh_suppressed_count",
        "ai_port_lf_detector_retighten_v2_fp_tn_suppressed_count",
        "ai_port_lf_detector_retighten_v2_created_unprotected_fn_count",
        "ai_port_lf_detector_retighten_v3_active",
        "ai_port_lf_detector_retighten_v3_suppressed_detector",
        "ai_port_lf_detector_retighten_v3_kept_detector",
        "ai_port_lf_detector_retighten_v3_generic_refresh_not_emergency",
        "ai_port_lf_detector_retighten_v3_generic_event_fg_not_likely_fn",
        "ai_port_lf_detector_retighten_v3_true_emergency",
        "ai_port_lf_detector_retighten_v3_explicit_likely_unprotected_fn",
        "ai_port_lf_detector_retighten_v3_no_detector_fallback",
        "ai_port_lf_detector_retighten_v3_created_unprotected_fn",
        "ai_port_lf_detector_retighten_v3_protected_fn_detector_kept",
        "ai_port_lf_detector_retighten_v3_suppressed_count",
        "ai_port_lf_detector_retighten_v3_kept_count",
        "ai_port_lf_detector_retighten_v3_actual_fn_detector_kept_count",
        "ai_port_lf_detector_retighten_v3_true_emergency_detector_kept_count",
        "ai_port_lf_detector_retighten_v3_generic_refresh_suppressed_count",
        "ai_port_lf_detector_retighten_v3_final_fp_tn_suppressed_count",
        "ai_port_lf_detector_retighten_v3_created_unprotected_fn_count",
        "ai_port_lf_detector_retighten_v4_active",
        "ai_port_lf_detector_retighten_v4_suppressed_detector",
        "ai_port_lf_detector_retighten_v4_kept_detector",
        "ai_port_lf_detector_retighten_v4_pre_fn_context_kept",
        "ai_port_lf_detector_retighten_v4_created_unprotected_fn",
        "ai_port_lf_detector_retighten_v4_suppressed_count",
        "ai_port_lf_detector_retighten_v4_kept_count",
        "ai_port_lf_detector_retighten_v4_actual_fn_detector_kept_count",
        "ai_port_lf_detector_retighten_v4_true_emergency_detector_kept_count",
        "ai_port_lf_detector_retighten_v4_pre_fn_context_kept_count",
        "ai_port_lf_detector_retighten_v4_final_fp_tn_suppressed_count",
        "ai_port_lf_detector_retighten_v4_created_unprotected_fn_count",
        "ai_port_v4_preserve_active",
        "ai_port_lf_post_suppression_holdout_active",
        "ai_port_lf_post_suppression_holdout_no_detector",
        "ai_port_lf_post_suppression_holdout_protected_event_fn",
        "ai_port_lf_post_suppression_holdout_final_normal_suppressed",
        "ai_port_lf_post_suppression_holdout_count",
        "ai_port_lf_post_suppression_holdout_protected_event_fn_count",
        "ai_ptz_intermittent_pan_cap_active",
        "ai_ptz_intermittent_pan_cap_rejected",
        "ai_ptz_intermittent_pan_would_have_proposed_before_cap",
        "ai_ptz_intermittent_pan_reclaimed_count",
        "ai_ptz_intermittent_pan_preserved_count",
        "ai_ptz_intermittent_pan_fn_rescue_active",
        "ai_ptz_intermittent_pan_fn_rescue_no_detector",
        "ai_ptz_intermittent_pan_fn_rescue_cap_used",
        "ai_ptz_intermittent_pan_preserve_2k_rescue_active",
        "ai_ptz_intermittent_pan_preserve_2k_rescue_protected_before_later_caps",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_active",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_no_detector",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_cap_used",
        "ai_copymachine_shadow_guard_active",
        "ai_copymachine_shadow_guard_rejected",
        "ai_copymachine_shadow_would_have_proposed_before_guard",
        "ai_copymachine_shadow_reclaimed_count",
        "ai_copymachine_shadow_preserved_count",
        "ai_copymachine_fn_rescue_active",
        "ai_copymachine_fn_rescue_no_detector",
        "ai_copymachine_fn_rescue_cap_used",
        "ai_copymachine_rescue_first_candidate",
        "ai_copymachine_rescue_first_active",
        "ai_copymachine_rescue_first_protected_before_cap",
        "ai_copymachine_rescue_first_no_detector",
        "ai_copymachine_rescue_first_final_normal_suppressed",
        "ai_copymachine_live_cap_reserve_active",
        "ai_copymachine_live_cap_reserve_no_detector",
        "ai_copymachine_live_cap_reserve_cap_used",
        "ai_copymachine_cap_suppressed_generic_only",
        "ai_copymachine_cap_suppressed_generic_count",
        "ai_parking_iom_rescue_candidate",
        "ai_parking_iom_rescue_active",
        "ai_parking_iom_rescue_no_detector",
        "ai_parking_iom_rescue_cap_used",
        "ai_parking_iom_rescue_first_protected_before_cap",
        "ai_parking_iom_cap_active",
        "ai_parking_iom_cap_suppressed_generic_only",
        "ai_parking_iom_cap_reclaimed_count",
        "ai_parking_iom_cap_preserved_count",
        "ai_parking_iom_final_normal_suppressed",
        "ai_parking_iom_preserve_fn_risk_candidate",
        "ai_parking_iom_preserve_fn_risk_active",
        "ai_parking_iom_preserve_fn_risk_protected_before_cap",
        "ai_parking_iom_preserve_fn_risk_count",
        "ai_parking_live_cap_reserve_active",
        "ai_parking_live_cap_reserve_no_detector",
        "ai_parking_live_cap_reserve_cap_used",
        "ai_parking_live_burst_bridge_active",
        "ai_parking_live_burst_bridge_no_detector",
        "ai_parking_live_burst_bridge_cap_used",
        "ai_parking_iom_cap_suppressed_generic_nonrisk_only",
        "ai_parking_iom_cap_skipped_preserved_fn_risk",
        "ai_parking_iom_cap_skipped_preserved_fn_risk_count",
        "ai_parking_iom_cap_soft_budget_exceeded",
        "ai_parking_iom_rescue_likely_unprotected_fn",
        "ai_parking_iom_rescue_protected_event_fn",
        "ai_parking_iom_rescue_false_positive_activation",
        "ai_parking_carryover_lock_active",
        "ai_parking_carryover_lock_no_detector",
        "ai_parking_carryover_lock_cap_used",
        "ai_parking_carryover_lock_protected_event_fn",
        "ai_parking_carryover_lock_final_normal_suppressed",
        "ai_parking_iom_post_preservation_trim_active",
        "ai_parking_iom_post_preservation_trim_candidate",
        "ai_parking_iom_post_preservation_trim_suppressed_generic_nonrisk",
        "ai_parking_iom_post_preservation_trim_skipped_preserved_fn_risk",
        "ai_parking_iom_post_preservation_trim_skipped_rescue_frame",
        "ai_parking_iom_post_preservation_trim_skipped_likely_unprotected_fn",
        "ai_parking_iom_post_preservation_trim_count",
        "ai_parking_iom_post_preservation_trim_final_rate",
        "ai_parking_post_lock_trim_active",
        "ai_parking_post_lock_trim_candidate",
        "ai_parking_post_lock_trim_hard_protected",
        "ai_parking_post_lock_trim_soft_candidate",
        "ai_parking_post_lock_trim_suppressed",
        "ai_parking_post_lock_trim_skipped_hard_protected",
        "ai_parking_post_lock_trim_skipped_fn_protected",
        "ai_parking_post_lock_trim_skipped_likely_unprotected_fn",
        "ai_parking_post_lock_trim_count",
        "ai_parking_post_lock_trim_final_rate",
        "ai_parking_post_lock_trim_accidental_hard_trim_count",
        "ai_parking_post_lock_trim_accidental_fn_protected_trim_count",
        "ai_parking_post_lock_deduplicate_active",
        "ai_parking_post_lock_deduplicate_count",
        "ai_parking_restore_4d3_trim_active",
        "ai_parking_restore_4d3_trim_count",
        "ai_parking_restore_4d3_trim_blocked_by_later_hardprotect",
        "ai_parking_post_lock_trim_4d5_active",
        "ai_parking_post_lock_trim_4d5_candidate",
        "ai_parking_post_lock_trim_4d5_soft_candidate",
        "ai_parking_post_lock_trim_4d5_suppressed",
        "ai_parking_post_lock_trim_4d5_skipped_fn_protected",
        "ai_parking_post_lock_trim_4d5_skipped_rescue_frame",
        "ai_parking_post_lock_trim_4d5_skipped_likely_unprotected_fn",
        "ai_parking_post_lock_trim_4d5_trim_count",
        "ai_parking_post_lock_trim_4d5_final_rate",
        "ai_parking_post_lock_trim_4d5_accidental_fn_protected_trim_count",
        "ai_parking_post_lock_trim_4d5_accidental_rescue_trim_count",
        "ai_parking_post_lock_trim_4d6_active",
        "ai_parking_post_lock_trim_4d6_candidate",
        "ai_parking_post_lock_trim_4d6_suppressed",
        "ai_parking_post_lock_trim_4d6_trim_count",
        "ai_parking_post_lock_trim_4d6_final_rate",
        "ai_parking_post_lock_trim_4d6_accidental_fn_protected_trim_count",
        "ai_parking_post_lock_trim_4d6_accidental_rescue_trim_count",
        "ai_parking_restore_4d6_trim_stack_active",
        "ai_parking_restore_4d6_trim_4d3_count",
        "ai_parking_restore_4d6_trim_4d5_count",
        "ai_parking_restore_4d6_trim_4d6_count",
        "ai_parking_restore_4d6_trim_extra_count",
        "ai_parking_restore_4d6_trim_final_rate",
        "ai_parking_restore_4d6_trim_accidental_fn_protected_trim_count",
        "ai_parking_restore_4d6_trim_accidental_rescue_trim_count",
        "ai_parking_restore_4d6_fn_fallback_active",
        "ai_parking_restore_4d6_fn_fallback_no_detector",
        "ai_parking_restore_4d6_fn_fallback_protected_event_fn",
        "ai_parking_restore_4d6_fn_fallback_count",
        "ai_parking_restore_4d6_fn_fallback_protected_event_fn_count",
        "ai_sofa_iom_rescue_candidate",
        "ai_sofa_iom_rescue_active",
        "ai_sofa_iom_rescue_no_detector",
        "ai_sofa_iom_rescue_cap_used",
        "ai_sofa_iom_rescue_protected_event_fn",
        "ai_sofa_iom_rescue_final_normal_suppressed",
        "ai_sofa_iom_rescue_first_protected_before_cap",
        "ai_sofa_iom_carryover_lock_active",
        "ai_sofa_iom_carryover_lock_no_detector",
        "ai_sofa_iom_carryover_lock_cap_used",
        "ai_sofa_iom_carryover_lock_protected_event_fn",
        "ai_sofa_iom_carryover_lock_final_normal_suppressed",
        "ai_sofa_iom_proposal_guard_active",
        "ai_sofa_iom_proposal_guard_suppressed_generic_nonrisk",
        "ai_sofa_iom_proposal_guard_skipped_rescue_frame",
        "ai_sofa_iom_proposal_guard_suppressed_count",
        "ai_sofa_iom_proposal_guard_skipped_rescue_count",
        "ai_sofa_iom_proposal_guard_final_rate",
        "ai_snowfall_weather_rescue_candidate",
        "ai_snowfall_weather_rescue_active",
        "ai_snowfall_weather_rescue_no_detector",
        "ai_snowfall_weather_rescue_cap_used",
        "ai_snowfall_weather_rescue_protected_event_fn",
        "ai_snowfall_weather_rescue_final_normal_suppressed",
        "ai_snowfall_weather_localized_guard_active",
        "ai_snowfall_weather_proposal_guard_active",
        "ai_snowfall_weather_proposal_guard_suppressed_generic_nonrisk",
        "ai_snowfall_weather_proposal_guard_skipped_rescue_frame",
        "ai_snowfall_weather_proposal_guard_suppressed_count",
        "ai_snowfall_weather_proposal_guard_skipped_rescue_count",
        "ai_snowfall_weather_proposal_guard_final_rate",
        "ai_snowfall_weather_possible_mask_quality_exposure",
        "ai_snowfall_actual_fn_rescue_candidate",
        "ai_snowfall_actual_fn_rescue_active",
        "ai_snowfall_actual_fn_rescue_no_detector",
        "ai_snowfall_actual_fn_rescue_protected_event_fn",
        "ai_snowfall_actual_fn_rescue_final_normal_suppressed",
        "ai_snowfall_actual_fn_rescue_cap_used",
        "ai_snowfall_actual_fn_cap_increase_active",
        "ai_snowfall_actual_fn_rescue_cap_exhausted_after_d3",
        "ai_snowfall_mask_quality_row_skipped",
        "ai_parking_live_post_trim_2q3_active",
        "ai_parking_live_post_trim_2q3_candidate",
        "ai_parking_live_post_trim_2q3_suppressed_generic_nonrisk",
        "ai_parking_live_post_trim_2q3_skipped_rescue_frame",
        "ai_parking_live_post_trim_2q3_skipped_live_reserve_frame",
        "ai_parking_live_post_trim_2q3_skipped_preserved_fn_risk",
        "ai_parking_live_post_trim_2q3_skipped_likely_unprotected_fn",
        "ai_parking_live_post_trim_2q3_trim_count",
        "ai_parking_live_post_trim_2q3_final_rate",
        "ai_parking_live_post_trim_2q3_accidental_protected_trim_count",
        "ai_parking_soft_preserved_trim_active",
        "ai_parking_soft_preserved_trim_candidate",
        "ai_parking_soft_preserved_trim_hard_protected",
        "ai_parking_soft_preserved_trim_soft_preserved",
        "ai_parking_soft_preserved_trim_suppressed",
        "ai_parking_soft_preserved_trim_skipped_hard_protected",
        "ai_parking_soft_preserved_trim_skipped_rescue_frame",
        "ai_parking_soft_preserved_trim_skipped_live_reserve_frame",
        "ai_parking_soft_preserved_trim_skipped_likely_unprotected_fn",
        "ai_parking_soft_preserved_trim_trim_count",
        "ai_parking_soft_preserved_trim_final_rate",
        "ai_parking_soft_preserved_trim_accidental_hard_protected_trim_count",
        "ai_turbulence2_pressure_guard_active",
        "ai_turbulence2_pressure_guard_rejected",
        "ai_turbulence2_pressure_guard_suppressed_generic_nonrisk",
        "ai_turbulence2_pressure_guard_suppressed_detector_refresh",
        "ai_turbulence2_pressure_guard_reclaimed_count",
        "ai_turbulence2_pressure_guard_preserved_count",
        "ai_turbulence2_fn_rescue_candidate",
        "ai_turbulence2_fn_rescue_active",
        "ai_turbulence2_fn_rescue_no_detector",
        "ai_turbulence2_fn_rescue_protected_event_fn",
        "ai_turbulence2_fn_rescue_final_normal_suppressed",
        "ai_turbulence2_rescue_protected_before_guard",
        "ai_turbulence2_carryover_reserve_candidate",
        "ai_turbulence2_carryover_reserve_active",
        "ai_turbulence2_carryover_reserve_no_detector",
        "ai_turbulence2_carryover_reserve_cap_used",
        "ai_turbulence2_carryover_reserve_protected_event_fn",
        "ai_turbulence2_carryover_reserve_final_normal_suppressed",
        "ai_thermal_lakeside_fn_rescue_candidate",
        "ai_thermal_lakeside_fn_rescue_active",
        "ai_thermal_lakeside_fn_rescue_no_detector",
        "ai_thermal_lakeside_fn_rescue_cap_used",
        "ai_thermal_lakeside_fn_rescue_protected_event_fn",
        "ai_thermal_lakeside_fn_rescue_final_normal_suppressed",
        "ai_thermal_lakeside_early_memory_rescue_candidate",
        "ai_thermal_lakeside_early_memory_rescue_active",
        "ai_thermal_lakeside_early_memory_rescue_protected_event_fn",
        "ai_thermal_lakeside_post_rescue_trim_active",
        "ai_thermal_lakeside_post_rescue_trim_candidate",
        "ai_thermal_lakeside_post_rescue_trim_hard_protected",
        "ai_thermal_lakeside_post_rescue_trim_soft_candidate",
        "ai_thermal_lakeside_post_rescue_trim_suppressed",
        "ai_thermal_lakeside_post_rescue_trim_skipped_hard_protected",
        "ai_thermal_lakeside_post_rescue_trim_skipped_fn_protected",
        "ai_thermal_lakeside_post_rescue_trim_count",
        "ai_thermal_lakeside_post_rescue_trim_final_rate",
        "ai_thermal_lakeside_post_rescue_trim_accidental_hard_protected_trim_count",
        "ai_thermal_lakeside_rescue_cap_refine_active",
        "ai_thermal_lakeside_hard_protect_refine_active",
        "ai_thermal_lakeside_fg_loss_only_soft_candidate",
        "ai_thermal_lakeside_fg_loss_soft_trim_candidate",
        "ai_thermal_lakeside_fg_loss_soft_trim_suppressed",
        "ai_thermal_lakeside_fg_loss_soft_trim_skipped_hard_protected",
        "ai_thermal_lakeside_fg_loss_soft_trim_skipped_likely_unprotected_fn",
        "ai_thermal_lakeside_fg_loss_soft_trim_skipped_rescue_frame",
        "ai_thermal_lakeside_fg_loss_soft_trim_count",
        "ai_thermal_lakeside_fg_loss_soft_trim_final_rate",
        "ai_thermal_lakeside_fg_loss_soft_trim_accidental_hard_protected_trim_count",
        "ai_thermal_lakeside_detector_retighten_active",
        "ai_thermal_lakeside_highscore_soften_active",
        "ai_thermal_lakeside_highscore_soft_candidate",
        "ai_thermal_lakeside_highscore_soft_trim_candidate",
        "ai_thermal_lakeside_highscore_soft_trim_suppressed",
        "ai_thermal_lakeside_highscore_soft_trim_skipped_hard_protected",
        "ai_thermal_lakeside_highscore_soft_trim_skipped_rescue_frame",
        "ai_thermal_lakeside_highscore_soft_trim_skipped_likely_unprotected_fn",
        "ai_thermal_lakeside_highscore_soft_trim_count",
        "ai_thermal_lakeside_highscore_soft_trim_final_rate",
        "ai_thermal_lakeside_highscore_soft_trim_accidental_hard_protected_trim_count",
        "ai_thermal_lakeside_highscore_soft_trim_accidental_rescue_trim_count",
        "ai_thermal_lakeside_drift_recap_active",
        "ai_thermal_lakeside_drift_recap_suppressed",
        "ai_thermal_lakeside_drift_recap_final_rate",
        "ai_thermal_lakeside_drift_recap_accidental_hard_trim_count",
        "ai_thermal_lakeside_carryover_lock_active",
        "ai_thermal_lakeside_carryover_lock_trim_count",
        "ai_tunnel_exit_lf_preserve_fn_risk_candidate",
        "ai_tunnel_exit_lf_preserve_fn_risk_active",
        "ai_tunnel_exit_lf_rescue_candidate",
        "ai_tunnel_exit_lf_rescue_active",
        "ai_tunnel_exit_lf_rescue_no_detector",
        "ai_tunnel_exit_lf_rescue_protected_event_fn",
        "ai_tunnel_exit_lf_rescue_final_normal_suppressed",
        "ai_tunnel_exit_lf_post_trim_active",
        "ai_tunnel_exit_lf_post_trim_suppressed_generic_nonrisk",
        "ai_tunnel_exit_lf_post_trim_skipped_preserved_fn_risk",
        "ai_tunnel_exit_lf_post_trim_skipped_rescue_frame",
        "ai_tunnel_exit_lf_post_trim_final_rate",
        "ai_normal_frame_suppressor_active", "ai_event_foreground_risk_score",
        "ai_final_normal_frame_suppressor_active",
        "ai_live_mismatch_final_normal_suppressed",
        "ai_live_reserve_final_normal_suppressed",
        "ai_live_reserve_trim_skipped",
        "ai_foreground_loss_risk_score", "ai_event_continuity_risk_score",
        "ai_detector_refresh_needed_for_event_score",
    ]
    for col in numeric:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in [
        "category", "video", "pipeline", "action_label", "Event_State",
        "ai_intervention_mode", "ai_intervention_budget_profile",
        "ai_intervention_guard_reason", "ai_intervention_type",
        "ai_intervention_original_action", "ai_intervention_final_action",
        "ai_detector_request_source", "ai_safe_replacement_source",
        "ai_event_foreground_block_only_reason",
        "ai_event_foreground_safe_replacement_source",
        "ai_cubicle_like_event_continuity_reason",
        "ai_cubicle_like_safe_replacement_source",
        "ai_cubicle_like_rejected_reason",
        "ai_cubicle_micro_bump_reason",
        "ai_cubicle_micro_bump_rejected_reason",
        "ai_exact_cubicle_event_fn_stabilizer_reason",
        "ai_exact_cubicle_event_fn_stabilizer_rejected_reason",
        "ai_exact_cubicle_event_fn_stabilizer_frame",
        "ai_exact_cubicle_event_fn_stabilizer_safe_replacement_source",
        "ai_exact_cubicle_event_fn_pre_signal_reason",
        "ai_exact_cubicle_event_fn_pre_signal_frame",
        "ai_exact_cubicle_event_fn_pre_signal_action",
        "ai_exact_cubicle_late_event_rescue_reason",
        "ai_exact_cubicle_late_event_rescue_rejected_reason",
        "ai_exact_cubicle_late_event_rescue_frame",
        "ai_exact_cubicle_late_event_rescue_action",
        "ai_cubicle_live_mismatch_reserve_reason",
        "ai_cubicle_live_mismatch_reserve_rejected_reason",
        "ai_cubicle_live_mismatch_reserve_frame",
        "ai_non_cubicle_budget_reclaim_reason",
        "ai_lowframerate_trim_reason",
        "ai_lowframerate_trim_video",
        "ai_lowframerate_trim_frame",
        "ai_fountain01_quiet_guard_reason",
        "ai_fountain01_quiet_guard_suppressed_path",
        "ai_lowframerate_targeted_retighten_reason",
        "ai_port_lf_detector_retighten_reason",
        "ai_port_lf_detector_retighten_rejected_reason",
        "ai_port_lf_detector_retighten_kept_detector_reason",
        "ai_port_lf_detector_retighten_event_state",
        "ai_port_lf_detector_retighten_v2_reason",
        "ai_port_lf_detector_retighten_v2_rejected_reason",
        "ai_port_lf_detector_retighten_v2_kept_detector_reason",
        "ai_port_lf_detector_retighten_v2_suppressed_event_state",
        "ai_port_lf_detector_retighten_v2_fallback_source",
        "ai_port_lf_detector_retighten_v3_decision_time_event_state",
        "ai_port_lf_detector_retighten_v3_final_event_state",
        "ai_port_lf_detector_retighten_v3_kept_detector_reason",
        "ai_port_lf_detector_retighten_v3_suppressed_reason",
        "ai_port_lf_detector_retighten_v3_fallback_source",
        "ai_port_lf_detector_retighten_v4_kept_detector_reason",
        "ai_port_lf_detector_retighten_v4_suppressed_reason",
        "ai_port_lf_detector_retighten_v4_final_event_state",
        "ai_port_v4_preserve_reason",
        "ai_port_lf_v4_hard_lock_reason",
        "ai_port_lf_v4_hard_lock_frame_1350_status",
        "ai_port_lf_v4_hard_lock_frame_1355_status",
        "ai_port_lf_post_suppression_holdout_reason",
        "ai_port_lf_post_suppression_holdout_rejected_reason",
        "ai_port_lf_post_suppression_holdout_frame",
        "ai_ptz_intermittent_pan_cap_reason",
        "ai_ptz_intermittent_pan_fn_rescue_reason",
        "ai_ptz_intermittent_pan_fn_rescue_rejected_reason",
        "ai_ptz_intermittent_pan_fn_rescue_frame",
        "ai_ptz_intermittent_pan_preserve_2k_rescue_reason",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_reason",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_rejected_reason",
        "ai_ptz_intermittent_pan_live_mismatch_rescue_frame",
        "ai_copymachine_shadow_guard_reason",
        "ai_copymachine_fn_rescue_reason",
        "ai_copymachine_fn_rescue_rejected_reason",
        "ai_copymachine_fn_rescue_frame",
        "ai_copymachine_rescue_first_reason",
        "ai_copymachine_rescue_first_rejected_reason",
        "ai_copymachine_live_cap_reserve_reason",
        "ai_copymachine_live_cap_reserve_rejected_reason",
        "ai_copymachine_live_cap_reserve_frame",
        "ai_parking_iom_rescue_reason",
        "ai_parking_iom_rescue_rejected_reason",
        "ai_parking_iom_rescue_frame",
        "ai_parking_carryover_lock_reason",
        "ai_parking_carryover_lock_rejected_reason",
        "ai_parking_carryover_lock_frame",
        "ai_parking_iom_preserve_fn_risk_reason",
        "ai_parking_iom_preserve_fn_risk_rejected_reason",
        "ai_parking_live_cap_reserve_reason",
        "ai_parking_live_cap_reserve_rejected_reason",
        "ai_parking_live_cap_reserve_frame",
        "ai_parking_live_burst_bridge_reason",
        "ai_parking_live_burst_bridge_rejected_reason",
        "ai_parking_live_burst_bridge_frame",
        "ai_parking_iom_post_preservation_trim_reason",
        "ai_parking_iom_post_preservation_trim_rejected_reason",
        "ai_parking_post_lock_trim_reason",
        "ai_parking_post_lock_trim_rejected_reason",
        "ai_parking_restore_4d3_trim_reason",
        "ai_parking_post_lock_trim_4d5_rejected_reason",
        "ai_parking_post_lock_trim_4d6_reason",
        "ai_parking_post_lock_trim_4d6_rejected_reason",
        "ai_parking_restore_4d6_trim_stack_reason",
        "ai_parking_restore_4d6_fn_fallback_reason",
        "ai_parking_4d6_hard_restore_reason",
        "ai_parking_4d6_hard_restore_trim_stack_status",
        "ai_parking_4d6_hard_restore_safe_trim_reason",
        "ai_parking_4d6_hard_restore_fn_fallback_reason",
        "ai_snowfall_carryover_gate_lock_status",
        "ai_lakeside_carryover_gate_lock_status",
        "ai_sofa_iom_rescue_reason",
        "ai_sofa_iom_rescue_rejected_reason",
        "ai_sofa_iom_rescue_frame",
        "ai_sofa_iom_carryover_lock_reason",
        "ai_sofa_iom_carryover_lock_rejected_reason",
        "ai_sofa_iom_carryover_lock_frame",
        "ai_snowfall_weather_rescue_reason",
        "ai_snowfall_weather_rescue_rejected_reason",
        "ai_snowfall_weather_rescue_frame",
        "ai_snowfall_weather_localized_guard_rejected_reason",
        "ai_snowfall_actual_fn_rescue_reason",
        "ai_snowfall_actual_fn_rescue_rejected_reason",
        "ai_snowfall_actual_fn_rescue_frame",
        "ai_snowfall_actual_fn_cap_increase_reason",
        "ai_parking_live_post_trim_2q3_reason",
        "ai_parking_live_post_trim_2q3_rejected_reason",
        "ai_parking_soft_preserved_trim_reason",
        "ai_parking_soft_preserved_trim_rejected_reason",
        "ai_turbulence2_pressure_guard_reason",
        "ai_turbulence2_fn_rescue_reason",
        "ai_turbulence2_fn_rescue_rejected_reason",
        "ai_turbulence2_fn_rescue_frame",
        "ai_turbulence2_carryover_reserve_reason",
        "ai_turbulence2_carryover_reserve_rejected_reason",
        "ai_turbulence2_carryover_reserve_frame",
        "ai_thermal_lakeside_fn_rescue_reason",
        "ai_thermal_lakeside_fn_rescue_rejected_reason",
        "ai_thermal_lakeside_fn_rescue_frame",
        "ai_thermal_lakeside_early_memory_rescue_reason",
        "ai_thermal_lakeside_early_memory_rescue_rejected_reason",
        "ai_thermal_lakeside_highscore_soften_reason",
        "ai_thermal_lakeside_highscore_soften_rejected_reason",
        "ai_thermal_lakeside_drift_recap_reason",
        "ai_thermal_lakeside_carryover_lock_reason",
        "ai_step4d3_carryover_lock_video",
        "ai_tunnel_exit_lf_preserve_fn_risk_reason",
        "ai_tunnel_exit_lf_preserve_fn_risk_rejected_reason",
        "ai_tunnel_exit_lf_rescue_reason",
        "ai_tunnel_exit_lf_rescue_rejected_reason",
        "ai_normal_frame_suppressor_reason",
        "ai_final_normal_frame_suppressor_reason",
        "ai_final_normal_frame_suppressed_path",
        "ai_final_normal_frame_suppressed_video",
        "ai_final_normal_frame_suppressed_frame",
    ]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    df["known_guarded_safety_event"] = (
        df["closed_empty_blocked_final"].gt(0)
        | df["reuse_blocked_final"].gt(0)
        | df["lightweight_blocked_final"].gt(0)
        | df["ptz_closed_empty_kill_active"].gt(0)
        | df["closed_empty_blocked_under_ptz"].gt(0)
        | df["active_event_memory"].gt(0)
        | df["Event_State"].astype(str).isin(["TP", "FN"])
    ).astype(float)
    df["known_hard_video"] = df["video"].astype(str).isin([
        "continuousPan", "twoPositionPTZCam", "bridgeEntry", "cubicle",
        "fountain02", "turbulence2", "tramCrossroad_1fps", "tunnelExit_0_35fps",
    ]).astype(float)
    df["normal_frame"] = (df["known_guarded_safety_event"] <= 0).astype(float)
    df["action_changed"] = (
        df["ai_intervention_original_action"].astype(str)
        != df["ai_intervention_final_action"].astype(str)
    ).astype(float)
    return df


def build_ai_intervention_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    applied = df["ai_intervention_applied"].gt(0)
    return pd.DataFrame([{
        "frames": int(len(df)),
        "enabled_rate": float(df["ai_intervention_enabled"].mean()),
        "intervention_rate": float(applied.mean()),
        "detector_request_rate": float(df["ai_intervention_detector_requested"].mean()),
        "reuse_block_rate": float(df["ai_intervention_reuse_blocked"].mean()),
        "lightweight_block_rate": float(df["ai_intervention_lightweight_blocked"].mean()),
        "closed_empty_block_rate": float(df["ai_intervention_closed_empty_blocked"].mean()),
        "normal_frame_intervention_count": int((applied & df["normal_frame"].gt(0)).sum()),
        "known_event_intervention_count": int((applied & df["known_guarded_safety_event"].gt(0)).sum()),
        "deterministic_guard_alignment_rate": float(df.loc[applied, "ai_intervention_guard_active"].mean()) if applied.any() else 0.0,
        "budget_blocked_rate": float(df["ai_intervention_budget_blocked"].mean()),
        "cadence_blocked_rate": float(df["ai_intervention_cadence_blocked"].mean()),
        "action_change_rate": float(df["action_changed"].mean()),
    }])


def build_ai_intervention_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        applied = group["ai_intervention_applied"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        normal = group["normal_frame"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "intervention_rate": float(applied.mean()),
            "detector_request_rate": float(group["ai_intervention_detector_requested"].mean()),
            "reuse_block_rate": float(group["ai_intervention_reuse_blocked"].mean()),
            "lightweight_block_rate": float(group["ai_intervention_lightweight_blocked"].mean()),
            "normal_frame_intervention_count": int((applied & normal).sum()),
            "known_event_intervention_count": int((applied & known).sum()),
            "known_event_recall": float(applied[known].mean()) if known.any() else 0.0,
            "guard_alignment_rate": float(group.loc[applied, "ai_intervention_guard_active"].mean()) if applied.any() else 0.0,
            "mean_fmeasure": float(group["FMeasure"].mean()),
            "event_fn_count": int(group["Event_State"].astype(str).eq("FN").sum()),
            "closed_empty_final_count": int(group["event_closed_empty_final_count"].sum()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_budget_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        profiles = group["ai_intervention_budget_profile"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "budget_profile": str(profiles.iloc[0]) if not profiles.empty else "",
            "detector_requests": int(group["ai_intervention_detector_requested"].sum()),
            "reuse_blocks": int(group["ai_intervention_reuse_blocked"].sum()),
            "lightweight_blocks": int(group["ai_intervention_lightweight_blocked"].sum()),
            "closed_empty_blocks": int(group["ai_intervention_closed_empty_blocked"].sum()),
            "min_remaining_detector": float(group["ai_intervention_budget_remaining_detector"].min()),
            "min_remaining_reuse": float(group["ai_intervention_budget_remaining_reuse"].min()),
            "min_remaining_lightweight": float(group["ai_intervention_budget_remaining_lightweight"].min()),
            "min_remaining_closed_empty": float(group["ai_intervention_budget_remaining_closed_empty"].min()),
            "budget_blocked_frames": int(group["ai_intervention_budget_blocked"].sum()),
            "cadence_blocked_frames": int(group["ai_intervention_cadence_blocked"].sum()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2b_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    proposed = df["ai_intervention_applied"].gt(0)
    detector = df["ai_intervention_detector_requested"].gt(0)
    block_only = df["ai_block_only_no_detector"].gt(0)
    return pd.DataFrame([{
        "frames": int(len(df)),
        "dry_run_rate": float(df["ai_intervention_dry_run"].mean()),
        "enabled_rate": float(df["ai_intervention_enabled"].mean()),
        "proposed_intervention_rate": float(proposed.mean()),
        "proposed_detector_request_rate": float(detector.mean()),
        "block_only_rate": float(block_only.mean()),
        "detector_last_resort_rate": float(df["ai_detector_last_resort_used"].mean()),
        "normal_frame_proposed_interventions": int((proposed & df["normal_frame"].gt(0)).sum()),
        "known_event_proposed_interventions": int((proposed & df["known_guarded_safety_event"].gt(0)).sum()),
        "guard_alignment_rate": float(df.loc[proposed, "ai_intervention_guard_active"].mean()) if proposed.any() else 0.0,
        "detector_budget_block_rate": float(df["ai_detector_request_blocked_budget"].mean()),
        "detector_interval_block_rate": float(df["ai_detector_request_blocked_interval"].mean()),
        "detector_no_refresh_model_block_rate": float(df["ai_detector_request_blocked_no_refresh_model"].mean()),
        "normal_frame_suppressor_rate": float(df["ai_normal_frame_suppressor_active"].mean()),
        "sparse_detector_budget_active_rate": float(df["ai_sparse_detector_budget_active"].mean()),
        "action_change_rate": float(df["action_changed"].mean()),
    }])


def build_ai_intervention_2b_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        proposed = group["ai_intervention_applied"].gt(0)
        detector = group["ai_intervention_detector_requested"].gt(0)
        normal = group["normal_frame"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "proposed_intervention_rate": float(proposed.mean()),
            "proposed_detector_request_rate": float(detector.mean()),
            "block_only_rate": float(group["ai_block_only_no_detector"].mean()),
            "detector_last_resort_rate": float(group["ai_detector_last_resort_used"].mean()),
            "normal_frame_proposed_interventions": int((proposed & normal).sum()),
            "known_event_proposed_interventions": int((proposed & known).sum()),
            "known_event_recall": float(proposed[known].mean()) if known.any() else 0.0,
            "guard_alignment_rate": float(group.loc[proposed, "ai_intervention_guard_active"].mean()) if proposed.any() else 0.0,
            "detector_budget_used_max": int(group["ai_detector_budget_used_per_100"].max()),
            "mean_fmeasure": float(group["FMeasure"].mean()),
            "event_fn_count": int(group["Event_State"].astype(str).eq("FN").sum()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2b_budget_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "category": category,
            "video": video,
            "detector_requests": int(group["ai_intervention_detector_requested"].sum()),
            "reuse_blocks": int(group["ai_intervention_reuse_blocked"].sum()),
            "lightweight_blocks": int(group["ai_intervention_lightweight_blocked"].sum()),
            "closed_empty_blocks": int(group["ai_intervention_closed_empty_blocked"].sum()),
            "block_only_frames": int(group["ai_block_only_no_detector"].sum()),
            "detector_last_resort_frames": int(group["ai_detector_last_resort_used"].sum()),
            "max_detector_budget_used": int(group["ai_detector_budget_used_per_100"].max()),
            "min_detector_budget_remaining": float(group["ai_detector_budget_remaining"].min()),
            "detector_blocked_budget_frames": int(group["ai_detector_request_blocked_budget"].sum()),
            "detector_blocked_interval_frames": int(group["ai_detector_request_blocked_interval"].sum()),
            "detector_blocked_no_refresh_model_frames": int(group["ai_detector_request_blocked_no_refresh_model"].sum()),
            "normal_frame_suppressed_frames": int(group["ai_normal_frame_suppressor_active"].sum()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2b_dryrun_vs_live(root):
    root = Path(root)
    name = root.name
    if name.endswith("_2b_live"):
        live_root = root
        dry_root = root.with_name(name.replace("_2b_live", "_2b_dryrun"))
    elif name.endswith("_2b_dryrun"):
        dry_root = root
        live_root = root.with_name(name.replace("_2b_dryrun", "_2b_live"))
    else:
        return pd.DataFrame()
    if not dry_root.exists() or not live_root.exists():
        return pd.DataFrame()
    dry = build_ai_intervention_2b_summary(dry_root)
    live = build_ai_intervention_2b_summary(live_root)
    if dry.empty or live.empty:
        return pd.DataFrame()
    rows = []
    for metric in [
        "proposed_intervention_rate",
        "proposed_detector_request_rate",
        "block_only_rate",
        "normal_frame_proposed_interventions",
        "guard_alignment_rate",
    ]:
        rows.append({
            "metric": metric,
            "dryrun": dry.iloc[0].get(metric, 0.0),
            "live": live.iloc[0].get(metric, 0.0),
            "delta_live_minus_dryrun": live.iloc[0].get(metric, 0.0) - dry.iloc[0].get(metric, 0.0),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2c_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    proposed = df["ai_intervention_applied"].gt(0)
    detector = df["ai_intervention_detector_requested"].gt(0)
    block_only = df["ai_block_only_no_detector"].gt(0)
    event_fg_block_only = df["ai_event_foreground_block_only_no_detector"].gt(0)
    cubicle = df["video"].astype(str).eq("cubicle")
    cubicle_known = cubicle & df["known_guarded_safety_event"].gt(0)
    bridge = df["video"].astype(str).eq("bridgeEntry")
    continuous_pan = df["video"].astype(str).eq("continuousPan")
    return pd.DataFrame([{
        "frames": int(len(df)),
        "dry_run_rate": float(df["ai_intervention_dry_run"].mean()),
        "enabled_rate": float(df["ai_intervention_enabled"].mean()),
        "proposed_intervention_rate": float(proposed.mean()),
        "proposed_detector_request_rate": float(detector.mean()),
        "block_only_rate": float(block_only.mean()),
        "event_foreground_block_only_rate": float(event_fg_block_only.mean()),
        "event_refresh_specific_detector_rate": float(df["ai_detector_request_event_refresh_specific"].mean()),
        "event_foreground_detector_rejected_rate": float(df["ai_detector_request_rejected_event_foreground_only"].mean()),
        "normal_frame_proposed_interventions": int((proposed & df["normal_frame"].gt(0)).sum()),
        "known_event_proposed_interventions": int((proposed & df["known_guarded_safety_event"].gt(0)).sum()),
        "guard_alignment_rate": float(df.loc[proposed, "ai_intervention_guard_active"].mean()) if proposed.any() else 0.0,
        "cubicle_proposed_known_event_recall": float(proposed[cubicle_known].mean()) if cubicle_known.any() else 0.0,
        "cubicle_normal_frame_proposed_interventions": int((proposed & cubicle & df["normal_frame"].gt(0)).sum()),
        "bridgeEntry_event_fn_count": int(df.loc[bridge, "Event_State"].astype(str).eq("FN").sum()),
        "continuousPan_proposed_intervention_rate": float(proposed[continuous_pan].mean()) if continuous_pan.any() else 0.0,
        "detector_budget_block_rate": float(df["ai_detector_request_blocked_budget"].mean()),
        "detector_interval_block_rate": float(df["ai_detector_request_blocked_interval"].mean()),
        "detector_no_refresh_model_block_rate": float(df["ai_detector_request_blocked_no_refresh_model"].mean()),
        "normal_frame_suppressor_rate": float(df["ai_normal_frame_suppressor_active"].mean()),
        "sparse_detector_budget_active_rate": float(df["ai_sparse_detector_budget_active"].mean()),
    }])


def build_ai_intervention_2c_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        proposed = group["ai_intervention_applied"].gt(0)
        detector = group["ai_intervention_detector_requested"].gt(0)
        normal = group["normal_frame"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "proposed_intervention_rate": float(proposed.mean()),
            "proposed_detector_request_rate": float(detector.mean()),
            "block_only_rate": float(group["ai_block_only_no_detector"].mean()),
            "event_foreground_block_only_rate": float(group["ai_event_foreground_block_only_no_detector"].mean()),
            "event_foreground_override_active_rate": float(group["ai_event_foreground_block_only_active"].mean()),
            "normal_frame_proposed_interventions": int((proposed & normal).sum()),
            "known_event_proposed_interventions": int((proposed & known).sum()),
            "known_event_recall": float(proposed[known].mean()) if known.any() else 0.0,
            "guard_alignment_rate": float(group.loc[proposed, "ai_intervention_guard_active"].mean()) if proposed.any() else 0.0,
            "detector_budget_used_max": int(group["ai_detector_budget_used_per_100"].max()),
            "detector_rejected_event_foreground_only_frames": int(group["ai_detector_request_rejected_event_foreground_only"].sum()),
            "mean_fmeasure": float(group["FMeasure"].mean()),
            "event_fn_count": int(group["Event_State"].astype(str).eq("FN").sum()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2c_event_foreground_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        proposed = group["ai_intervention_applied"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        event_fg_active = group["ai_event_foreground_block_only_active"].gt(0)
        event_fg_block_only = group["ai_event_foreground_block_only_no_detector"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "event_foreground_override_active_frames": int(event_fg_active.sum()),
            "event_foreground_block_only_frames": int(event_fg_block_only.sum()),
            "event_foreground_block_only_rate": float(event_fg_block_only.mean()),
            "event_foreground_known_event_recall": float(event_fg_block_only[known].mean()) if known.any() else 0.0,
            "combined_proposed_known_event_recall": float(proposed[known].mean()) if known.any() else 0.0,
            "event_foreground_normal_frame_interventions": int((event_fg_block_only & group["normal_frame"].gt(0)).sum()),
            "closed_empty_blocks": int(group["ai_intervention_closed_empty_blocked"].sum()),
            "reuse_blocks": int(group["ai_intervention_reuse_blocked"].sum()),
            "lightweight_blocks": int(group["ai_intervention_lightweight_blocked"].sum()),
            "detector_requests": int(group["ai_intervention_detector_requested"].sum()),
            "detector_rejected_event_foreground_only_frames": int(group["ai_detector_request_rejected_event_foreground_only"].sum()),
            "event_fn_count": int(group["Event_State"].astype(str).eq("FN").sum()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2c_dryrun_vs_live(root):
    root = Path(root)
    name = root.name
    if name.endswith("_2c_live"):
        live_root = root
        dry_root = root.with_name(name.replace("_2c_live", "_2c_dryrun"))
    elif name.endswith("_2c_dryrun"):
        dry_root = root
        live_root = root.with_name(name.replace("_2c_dryrun", "_2c_live"))
    else:
        return pd.DataFrame()
    if not dry_root.exists() or not live_root.exists():
        return pd.DataFrame()
    dry = build_ai_intervention_2c_summary(dry_root)
    live = build_ai_intervention_2c_summary(live_root)
    if dry.empty or live.empty:
        return pd.DataFrame()
    rows = []
    for metric in [
        "proposed_intervention_rate",
        "proposed_detector_request_rate",
        "block_only_rate",
        "event_foreground_block_only_rate",
        "normal_frame_proposed_interventions",
        "cubicle_proposed_known_event_recall",
        "guard_alignment_rate",
    ]:
        rows.append({
            "metric": metric,
            "dryrun": dry.iloc[0].get(metric, 0.0),
            "live": live.iloc[0].get(metric, 0.0),
            "delta_live_minus_dryrun": live.iloc[0].get(metric, 0.0) - dry.iloc[0].get(metric, 0.0),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2d_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    proposed = df["ai_intervention_applied"].gt(0)
    detector = df["ai_intervention_detector_requested"].gt(0)
    block_only = df["ai_block_only_no_detector"].gt(0)
    event_fg_block_only = df["ai_event_foreground_block_only_no_detector"].gt(0)
    cubicle_like = df["ai_cubicle_like_event_continuity_active"].gt(0)
    cubicle = df["video"].astype(str).eq("cubicle")
    cubicle_known = cubicle & df["known_guarded_safety_event"].gt(0)
    cubicle_fn = cubicle & df["Event_State"].astype(str).eq("FN")
    bridge = df["video"].astype(str).eq("bridgeEntry")
    continuous_pan = df["video"].astype(str).eq("continuousPan")
    return pd.DataFrame([{
        "frames": int(len(df)),
        "dry_run_rate": float(df["ai_intervention_dry_run"].mean()),
        "enabled_rate": float(df["ai_intervention_enabled"].mean()),
        "proposed_intervention_rate": float(proposed.mean()),
        "proposed_detector_request_rate": float(detector.mean()),
        "block_only_rate": float(block_only.mean()),
        "event_foreground_block_only_rate": float(event_fg_block_only.mean()),
        "cubicle_like_proposal_rate": float(cubicle_like.mean()),
        "cubicle_like_no_detector_rate": float(df["ai_cubicle_like_no_detector"].mean()),
        "event_refresh_specific_detector_rate": float(df["ai_detector_request_event_refresh_specific"].mean()),
        "event_foreground_detector_rejected_rate": float(df["ai_detector_request_rejected_event_foreground_only"].mean()),
        "normal_frame_proposed_interventions": int((proposed & df["normal_frame"].gt(0)).sum()),
        "known_event_proposed_interventions": int((proposed & df["known_guarded_safety_event"].gt(0)).sum()),
        "guard_alignment_rate": float(df.loc[proposed, "ai_intervention_guard_active"].mean()) if proposed.any() else 0.0,
        "cubicle_proposed_known_event_recall": float(proposed[cubicle_known].mean()) if cubicle_known.any() else 0.0,
        "cubicle_normal_frame_proposed_interventions": int((proposed & cubicle & df["normal_frame"].gt(0)).sum()),
        "cubicle_event_fn_count": int(cubicle_fn.sum()),
        "cubicle_proposed_event_fn_count": int((proposed & cubicle_fn).sum()),
        "cubicle_unprotected_event_fn_count": int((~proposed & cubicle_fn).sum()),
        "bridgeEntry_event_fn_count": int(df.loc[bridge, "Event_State"].astype(str).eq("FN").sum()),
        "bridgeEntry_detector_budget_used_max": int(df.loc[bridge, "ai_detector_budget_used_per_100"].max()) if bridge.any() else 0,
        "continuousPan_proposed_intervention_rate": float(proposed[continuous_pan].mean()) if continuous_pan.any() else 0.0,
        "detector_budget_block_rate": float(df["ai_detector_request_blocked_budget"].mean()),
        "detector_interval_block_rate": float(df["ai_detector_request_blocked_interval"].mean()),
        "detector_no_refresh_model_block_rate": float(df["ai_detector_request_blocked_no_refresh_model"].mean()),
        "normal_frame_suppressor_rate": float(df["ai_normal_frame_suppressor_active"].mean()),
        "sparse_detector_budget_active_rate": float(df["ai_sparse_detector_budget_active"].mean()),
    }])


def build_ai_intervention_2d_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        proposed = group["ai_intervention_applied"].gt(0)
        detector = group["ai_intervention_detector_requested"].gt(0)
        normal = group["normal_frame"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "proposed_intervention_rate": float(proposed.mean()),
            "proposed_detector_request_rate": float(detector.mean()),
            "block_only_rate": float(group["ai_block_only_no_detector"].mean()),
            "event_foreground_block_only_rate": float(group["ai_event_foreground_block_only_no_detector"].mean()),
            "cubicle_like_proposal_rate": float(group["ai_cubicle_like_event_continuity_active"].mean()),
            "cubicle_like_no_detector_rate": float(group["ai_cubicle_like_no_detector"].mean()),
            "normal_frame_proposed_interventions": int((proposed & normal).sum()),
            "known_event_proposed_interventions": int((proposed & known).sum()),
            "known_event_recall": float(proposed[known].mean()) if known.any() else 0.0,
            "guard_alignment_rate": float(group.loc[proposed, "ai_intervention_guard_active"].mean()) if proposed.any() else 0.0,
            "detector_budget_used_max": int(group["ai_detector_budget_used_per_100"].max()),
            "cubicle_like_cap_used_max": int(group["ai_cubicle_like_cap_used"].max()),
            "detector_rejected_event_foreground_only_frames": int(group["ai_detector_request_rejected_event_foreground_only"].sum()),
            "mean_fmeasure": float(group["FMeasure"].mean()),
            "event_fn_count": int(fn.sum()),
            "proposed_event_fn_count": int((proposed & fn).sum()),
            "unprotected_event_fn_count": int((~proposed & fn).sum()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2d_event_foreground_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        proposed = group["ai_intervention_applied"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        event_fg_block_only = group["ai_event_foreground_block_only_no_detector"].gt(0)
        cubicle_like = group["ai_cubicle_like_event_continuity_active"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "event_foreground_block_only_frames": int(event_fg_block_only.sum()),
            "event_foreground_block_only_rate": float(event_fg_block_only.mean()),
            "cubicle_like_event_continuity_frames": int(cubicle_like.sum()),
            "cubicle_like_event_continuity_rate": float(cubicle_like.mean()),
            "event_foreground_known_event_recall": float(event_fg_block_only[known].mean()) if known.any() else 0.0,
            "cubicle_like_known_event_recall": float(cubicle_like[known].mean()) if known.any() else 0.0,
            "combined_proposed_known_event_recall": float(proposed[known].mean()) if known.any() else 0.0,
            "event_foreground_normal_frame_interventions": int(((event_fg_block_only | cubicle_like) & group["normal_frame"].gt(0)).sum()),
            "detector_requests": int(group["ai_intervention_detector_requested"].sum()),
            "detector_rejected_event_foreground_only_frames": int(group["ai_detector_request_rejected_event_foreground_only"].sum()),
            "event_fn_count": int(group["Event_State"].astype(str).eq("FN").sum()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2d_cubicle_like_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        active = group["ai_cubicle_like_event_continuity_active"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        normal = group["normal_frame"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "cubicle_like_active_frames": int(active.sum()),
            "cubicle_like_active_rate": float(active.mean()),
            "cubicle_like_no_detector_frames": int(group["ai_cubicle_like_no_detector"].sum()),
            "cubicle_like_known_event_recall": float(active[known].mean()) if known.any() else 0.0,
            "cubicle_like_normal_frame_interventions": int((active & normal).sum()),
            "cubicle_like_event_fn_covered": int((active & fn).sum()),
            "cubicle_like_cap_used_max": int(group["ai_cubicle_like_cap_used"].max()),
            "cubicle_like_non_ptz_context_rate": float(group["ai_cubicle_like_is_non_ptz_context"].mean()),
            "cubicle_like_camera_motion_score_max": float(group["ai_cubicle_like_camera_motion_score"].max()),
            "cubicle_like_rejection_distribution": ";".join(
                f"{k}:{v}" for k, v in group["ai_cubicle_like_rejected_reason"].replace("", pd.NA).dropna().value_counts().sort_index().items()
            ),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2d_dryrun_vs_live(root):
    root = Path(root)
    name = root.name
    if name.endswith("_2d_live"):
        live_root = root
        dry_root = root.with_name(name.replace("_2d_live", "_2d_dryrun"))
    elif name.endswith("_2d_dryrun"):
        dry_root = root
        live_root = root.with_name(name.replace("_2d_dryrun", "_2d_live"))
    else:
        return pd.DataFrame()
    if not dry_root.exists() or not live_root.exists():
        return pd.DataFrame()
    dry = build_ai_intervention_2d_summary(dry_root)
    live = build_ai_intervention_2d_summary(live_root)
    if dry.empty or live.empty:
        return pd.DataFrame()
    rows = []
    for metric in [
        "proposed_intervention_rate",
        "proposed_detector_request_rate",
        "block_only_rate",
        "event_foreground_block_only_rate",
        "cubicle_like_proposal_rate",
        "normal_frame_proposed_interventions",
        "cubicle_proposed_known_event_recall",
        "cubicle_unprotected_event_fn_count",
        "bridgeEntry_detector_budget_used_max",
        "continuousPan_proposed_intervention_rate",
        "guard_alignment_rate",
    ]:
        rows.append({
            "metric": metric,
            "dryrun": dry.iloc[0].get(metric, 0.0),
            "live": live.iloc[0].get(metric, 0.0),
            "delta_live_minus_dryrun": live.iloc[0].get(metric, 0.0) - dry.iloc[0].get(metric, 0.0),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2e_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = build_ai_intervention_2d_summary(root)
    if summary.empty:
        return summary
    rejected = df["ai_non_cubicle_budget_reclaim_rejected"].gt(0)
    would_have = df["ai_non_cubicle_event_fg_would_have_proposed_before_reclaim"].gt(0)
    summary = summary.copy()
    summary["non_cubicle_budget_reclaim_active_rate"] = float(df["ai_non_cubicle_budget_reclaim_active"].mean())
    summary["non_cubicle_event_fg_would_have_proposed_frames"] = int(would_have.sum())
    summary["non_cubicle_reclaimed_proposals"] = int(rejected.sum())
    summary["non_cubicle_reclaimed_proposal_rate"] = float(rejected.mean())
    summary["non_cubicle_event_fg_cap_used_max"] = int(df["ai_non_cubicle_event_fg_cap_used"].max())
    return summary


def build_ai_intervention_2e_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2d_video_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "category": category,
            "video": video,
            "non_cubicle_reclaim_active_frames": int(group["ai_non_cubicle_budget_reclaim_active"].sum()),
            "non_cubicle_reclaimed_proposals": int(group["ai_non_cubicle_budget_reclaim_rejected"].sum()),
            "non_cubicle_would_have_proposed_frames": int(group["ai_non_cubicle_event_fg_would_have_proposed_before_reclaim"].sum()),
            "non_cubicle_event_fg_cap_used_max": int(group["ai_non_cubicle_event_fg_cap_used"].max()),
            "non_cubicle_reclaimed_count_max": int(group["ai_non_cubicle_event_fg_reclaimed_count"].max()),
            "non_cubicle_preserved_count_max": int(group["ai_non_cubicle_event_fg_preserved_count"].max()),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2e_event_foreground_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2d_event_foreground_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "category": category,
            "video": video,
            "non_cubicle_event_fg_reclaimed_frames": int(group["ai_non_cubicle_budget_reclaim_rejected"].sum()),
            "non_cubicle_event_fg_preserved_count_max": int(group["ai_non_cubicle_event_fg_preserved_count"].max()),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2e_cubicle_like_summary(root):
    return build_ai_intervention_2d_cubicle_like_summary(root)


def build_ai_intervention_2e_budget_reclaim_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        reasons = group["ai_non_cubicle_budget_reclaim_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "reclaim_active_frames": int(group["ai_non_cubicle_budget_reclaim_active"].sum()),
            "would_have_proposed_before_reclaim_frames": int(group["ai_non_cubicle_event_fg_would_have_proposed_before_reclaim"].sum()),
            "reclaimed_proposals": int(group["ai_non_cubicle_budget_reclaim_rejected"].sum()),
            "preserved_count_max": int(group["ai_non_cubicle_event_fg_preserved_count"].max()),
            "reclaimed_count_max": int(group["ai_non_cubicle_event_fg_reclaimed_count"].max()),
            "event_fg_cap_used_max": int(group["ai_non_cubicle_event_fg_cap_used"].max()),
            "reason_distribution": ";".join(f"{k}:{v}" for k, v in reasons.value_counts().sort_index().items()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2e_dryrun_vs_live(root):
    root = Path(root)
    name = root.name
    if name.endswith("_2e_live"):
        live_root = root
        dry_root = root.with_name(name.replace("_2e_live", "_2e_dryrun"))
    elif name.endswith("_2e_dryrun"):
        dry_root = root
        live_root = root.with_name(name.replace("_2e_dryrun", "_2e_live"))
    else:
        return pd.DataFrame()
    if not dry_root.exists() or not live_root.exists():
        return pd.DataFrame()
    dry = build_ai_intervention_2e_summary(dry_root)
    live = build_ai_intervention_2e_summary(live_root)
    if dry.empty or live.empty:
        return pd.DataFrame()
    rows = []
    for metric in [
        "proposed_intervention_rate",
        "proposed_detector_request_rate",
        "block_only_rate",
        "event_foreground_block_only_rate",
        "cubicle_like_proposal_rate",
        "normal_frame_proposed_interventions",
        "cubicle_proposed_known_event_recall",
        "cubicle_unprotected_event_fn_count",
        "bridgeEntry_detector_budget_used_max",
        "continuousPan_proposed_intervention_rate",
        "non_cubicle_reclaimed_proposals",
        "guard_alignment_rate",
    ]:
        rows.append({
            "metric": metric,
            "dryrun": dry.iloc[0].get(metric, 0.0),
            "live": live.iloc[0].get(metric, 0.0),
            "delta_live_minus_dryrun": live.iloc[0].get(metric, 0.0) - dry.iloc[0].get(metric, 0.0),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2f_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = build_ai_intervention_2e_summary(root)
    if summary.empty:
        return summary
    micro = df["ai_cubicle_micro_bump_active"].gt(0)
    final_suppressed = df["ai_final_normal_frame_suppressor_active"].gt(0)
    summary = summary.copy()
    summary["cubicle_micro_bump_rate"] = float(micro.mean())
    summary["cubicle_micro_bump_frames"] = int(micro.sum())
    summary["cubicle_micro_bump_no_detector_rate"] = float(df["ai_cubicle_micro_bump_no_detector"].mean())
    summary["final_normal_frame_suppressed_frames"] = int(final_suppressed.sum())
    summary["final_normal_frame_suppressor_rate"] = float(final_suppressed.mean())
    return summary


def build_ai_intervention_2f_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2e_video_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "category": category,
            "video": video,
            "cubicle_micro_bump_frames": int(group["ai_cubicle_micro_bump_active"].sum()),
            "cubicle_micro_bump_no_detector_frames": int(group["ai_cubicle_micro_bump_no_detector"].sum()),
            "cubicle_micro_bump_cap_used_max": int(group["ai_cubicle_micro_bump_cap_used"].max()),
            "final_normal_frame_suppressed_frames": int(group["ai_final_normal_frame_suppressor_active"].sum()),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2f_event_foreground_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2e_event_foreground_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        known = group["known_guarded_safety_event"].gt(0)
        micro = group["ai_cubicle_micro_bump_active"].gt(0)
        proposed = group["ai_intervention_applied"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "cubicle_micro_bump_frames": int(micro.sum()),
            "cubicle_micro_bump_known_event_recall": float(micro[known].mean()) if known.any() else 0.0,
            "combined_with_micro_proposed_known_event_recall": float(proposed[known].mean()) if known.any() else 0.0,
            "final_normal_frame_suppressed_frames": int(group["ai_final_normal_frame_suppressor_active"].sum()),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2f_cubicle_like_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2e_cubicle_like_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        micro = group["ai_cubicle_micro_bump_active"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        normal = group["normal_frame"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        rejected = group["ai_cubicle_micro_bump_rejected_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "cubicle_micro_bump_frames": int(micro.sum()),
            "cubicle_micro_bump_rate": float(micro.mean()),
            "cubicle_micro_bump_no_detector_frames": int(group["ai_cubicle_micro_bump_no_detector"].sum()),
            "cubicle_micro_bump_known_event_recall": float(micro[known].mean()) if known.any() else 0.0,
            "cubicle_micro_bump_normal_frame_interventions": int((micro & normal).sum()),
            "cubicle_micro_bump_event_fn_covered": int((micro & fn).sum()),
            "cubicle_micro_bump_cap_used_max": int(group["ai_cubicle_micro_bump_cap_used"].max()),
            "cubicle_micro_bump_rejection_distribution": ";".join(
                f"{k}:{v}" for k, v in rejected.value_counts().sort_index().items()
            ),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2f_budget_reclaim_summary(root):
    return build_ai_intervention_2e_budget_reclaim_summary(root)


def _normal_frame_proposal_rows(root, phase_label):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    proposed = df["ai_intervention_applied"].gt(0)
    normal = df["normal_frame"].gt(0)
    rows = df.loc[proposed & normal].copy()
    if rows.empty:
        return pd.DataFrame(columns=[
            "phase", "category", "video", "pipeline", "frame_id", "raw_frame_id",
            "evaluated_index", "action_label", "Event_State", "ai_intervention_type",
            "ai_intervention_original_action", "ai_event_foreground_block_only_reason",
            "ai_non_cubicle_budget_reclaim_reason",
        ])
    out = rows[[
        "category", "video", "pipeline", "frame_id", "raw_frame_id", "evaluated_index",
        "action_label", "Event_State", "ai_intervention_type",
        "ai_intervention_original_action", "ai_event_foreground_block_only_reason",
        "ai_non_cubicle_budget_reclaim_reason",
    ]].copy()
    out.insert(0, "phase", phase_label)
    return out


def build_ai_intervention_2f_normal_frame_suppression_summary(root):
    root = Path(root)
    rows = []
    previous_root = None
    if root.name.endswith("_2f_dryrun"):
        previous_root = root.with_name(root.name.replace("_2f_dryrun", "_2e_dryrun"))
    elif root.name.endswith("_2f_live"):
        previous_root = root.with_name(root.name.replace("_2f_live", "_2e_dryrun"))
    if previous_root is not None and previous_root.exists():
        rows.append(_normal_frame_proposal_rows(previous_root, "8C-2E_prior_normal_proposal"))
    current = _read_ai_intervention_frames(root)
    if not current.empty:
        suppressed = current[current["ai_final_normal_frame_suppressor_active"].gt(0)].copy()
        if not suppressed.empty:
            out = suppressed[[
                "category", "video", "pipeline", "frame_id", "raw_frame_id",
                "evaluated_index", "action_label", "Event_State",
                "ai_final_normal_frame_suppressed_path",
                "ai_final_normal_frame_suppressor_reason",
                "ai_final_normal_frame_suppressed_frame",
            ]].copy()
            out.insert(0, "phase", "8C-2F_suppressed")
            rows.append(out)
    if rows:
        return pd.concat(rows, ignore_index=True, sort=False)
    return pd.DataFrame()


def build_ai_intervention_2f_dryrun_vs_live(root):
    root = Path(root)
    name = root.name
    if name.endswith("_2f_live"):
        live_root = root
        dry_root = root.with_name(name.replace("_2f_live", "_2f_dryrun"))
    elif name.endswith("_2f_dryrun"):
        dry_root = root
        live_root = root.with_name(name.replace("_2f_dryrun", "_2f_live"))
    else:
        return pd.DataFrame()
    live_progress = live_root / "run_progress.csv"
    if not dry_root.exists() or not live_progress.exists() or live_progress.stat().st_size <= 0:
        return pd.DataFrame()
    try:
        progress = pd.read_csv(live_progress)
    except Exception:
        return pd.DataFrame()
    if progress.empty or not progress["status"].astype(str).eq("completed").any():
        return pd.DataFrame()
    dry = build_ai_intervention_2f_summary(dry_root)
    live = build_ai_intervention_2f_summary(live_root)
    if dry.empty or live.empty:
        return pd.DataFrame()
    rows = []
    for metric in [
        "proposed_intervention_rate",
        "proposed_detector_request_rate",
        "block_only_rate",
        "event_foreground_block_only_rate",
        "cubicle_like_proposal_rate",
        "normal_frame_proposed_interventions",
        "cubicle_proposed_known_event_recall",
        "cubicle_unprotected_event_fn_count",
        "bridgeEntry_detector_budget_used_max",
        "continuousPan_proposed_intervention_rate",
        "non_cubicle_reclaimed_proposals",
        "cubicle_micro_bump_frames",
        "final_normal_frame_suppressed_frames",
        "guard_alignment_rate",
    ]:
        rows.append({
            "metric": metric,
            "dryrun": dry.iloc[0].get(metric, 0.0),
            "live": live.iloc[0].get(metric, 0.0),
            "delta_live_minus_dryrun": live.iloc[0].get(metric, 0.0) - dry.iloc[0].get(metric, 0.0),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2g_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = build_ai_intervention_2f_summary(root)
    if summary.empty:
        return summary
    trimmed = df["ai_lowframerate_trim_rejected"].gt(0)
    would_have = df["ai_lowframerate_trim_would_have_proposed_before_trim"].gt(0)
    active = df["ai_lowframerate_trim_active"].gt(0)
    lowframe = df["category"].astype(str).eq("lowFramerate") & df["video"].astype(str).eq("tramCrossroad_1fps")
    proposed = df["ai_intervention_applied"].gt(0)
    summary = summary.copy()
    summary["lowframerate_trim_active_rate"] = float(active.mean())
    summary["lowframerate_trim_would_have_proposed_frames"] = int(would_have.sum())
    summary["lowframerate_trim_reclaimed_proposals"] = int(trimmed.sum())
    summary["lowframerate_trim_reclaimed_rate"] = float(trimmed.mean())
    summary["lowframerate_trim_reclaimed_count_max"] = int(df["ai_lowframerate_trim_reclaimed_count"].max())
    summary["lowframerate_trim_preserved_count_max"] = int(df["ai_lowframerate_trim_preserved_count"].max())
    summary["lowFramerate_tramCrossroad_1fps_proposed_intervention_rate"] = (
        float(proposed[lowframe].mean()) if lowframe.any() else 0.0
    )
    return summary


def build_ai_intervention_2g_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2f_video_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "category": category,
            "video": video,
            "lowframerate_trim_active_frames": int(group["ai_lowframerate_trim_active"].sum()),
            "lowframerate_trim_would_have_proposed_frames": int(group["ai_lowframerate_trim_would_have_proposed_before_trim"].sum()),
            "lowframerate_trim_reclaimed_proposals": int(group["ai_lowframerate_trim_rejected"].sum()),
            "lowframerate_trim_reclaimed_count_max": int(group["ai_lowframerate_trim_reclaimed_count"].max()),
            "lowframerate_trim_preserved_count_max": int(group["ai_lowframerate_trim_preserved_count"].max()),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2g_event_foreground_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2f_event_foreground_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "category": category,
            "video": video,
            "lowframerate_trim_reclaimed_event_fg_frames": int(group["ai_lowframerate_trim_rejected"].sum()),
            "lowframerate_trim_would_have_proposed_frames": int(group["ai_lowframerate_trim_would_have_proposed_before_trim"].sum()),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2g_cubicle_like_summary(root):
    return build_ai_intervention_2f_cubicle_like_summary(root)


def build_ai_intervention_2g_budget_reclaim_summary(root):
    return build_ai_intervention_2f_budget_reclaim_summary(root)


def build_ai_intervention_2g_normal_frame_suppression_summary(root):
    root = Path(root)
    previous_root = None
    if root.name.endswith("_2g_dryrun"):
        previous_root = root.with_name(root.name.replace("_2g_dryrun", "_2f_dryrun"))
    elif root.name.endswith("_2g_live"):
        previous_root = root.with_name(root.name.replace("_2g_live", "_2f_dryrun"))
    current_rows = build_ai_intervention_2f_normal_frame_suppression_summary(root)
    if previous_root is not None and previous_root.exists():
        prior = _normal_frame_proposal_rows(previous_root, "8C-2F_prior_normal_proposal")
        if not prior.empty:
            if current_rows.empty:
                return prior
            return pd.concat([prior, current_rows], ignore_index=True, sort=False)
    return current_rows


def build_ai_intervention_2g_lowframerate_trim_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        active = group["ai_lowframerate_trim_active"].gt(0)
        if not active.any() and not (category == "lowFramerate" and video == "tramCrossroad_1fps"):
            continue
        proposed = group["ai_intervention_applied"].gt(0)
        trimmed = group["ai_lowframerate_trim_rejected"].gt(0)
        would_have = group["ai_lowframerate_trim_would_have_proposed_before_trim"].gt(0)
        reasons = group["ai_lowframerate_trim_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "proposed_intervention_rate_after_trim": float(proposed.mean()),
            "would_have_proposed_before_trim_frames": int(would_have.sum()),
            "trim_reclaimed_proposals": int(trimmed.sum()),
            "trim_preserved_count_max": int(group["ai_lowframerate_trim_preserved_count"].max()),
            "trim_reclaimed_count_max": int(group["ai_lowframerate_trim_reclaimed_count"].max()),
            "event_foreground_block_only_frames_after_trim": int(group["ai_event_foreground_block_only_no_detector"].sum()),
            "detector_requests_after_trim": int(group["ai_intervention_detector_requested"].sum()),
            "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
            "reason_distribution": ";".join(f"{k}:{v}" for k, v in reasons.value_counts().sort_index().items()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2g_dryrun_vs_live(root):
    root = Path(root)
    name = root.name
    if name.endswith("_2g_live"):
        live_root = root
        dry_root = root.with_name(name.replace("_2g_live", "_2g_dryrun"))
    elif name.endswith("_2g_dryrun"):
        dry_root = root
        live_root = root.with_name(name.replace("_2g_dryrun", "_2g_live"))
    else:
        return pd.DataFrame()
    live_progress = live_root / "run_progress.csv"
    if not dry_root.exists() or not live_progress.exists() or live_progress.stat().st_size <= 0:
        return pd.DataFrame()
    try:
        progress = pd.read_csv(live_progress)
    except Exception:
        return pd.DataFrame()
    if progress.empty or not progress["status"].astype(str).eq("completed").any():
        return pd.DataFrame()
    dry = build_ai_intervention_2g_summary(dry_root)
    live = build_ai_intervention_2g_summary(live_root)
    if dry.empty or live.empty:
        return pd.DataFrame()
    rows = []
    for metric in [
        "proposed_intervention_rate",
        "proposed_detector_request_rate",
        "block_only_rate",
        "event_foreground_block_only_rate",
        "cubicle_like_proposal_rate",
        "normal_frame_proposed_interventions",
        "cubicle_proposed_known_event_recall",
        "cubicle_unprotected_event_fn_count",
        "bridgeEntry_detector_budget_used_max",
        "continuousPan_proposed_intervention_rate",
        "non_cubicle_reclaimed_proposals",
        "cubicle_micro_bump_frames",
        "lowframerate_trim_reclaimed_proposals",
        "lowFramerate_tramCrossroad_1fps_proposed_intervention_rate",
        "guard_alignment_rate",
    ]:
        rows.append({
            "metric": metric,
            "dryrun": dry.iloc[0].get(metric, 0.0),
            "live": live.iloc[0].get(metric, 0.0),
            "delta_live_minus_dryrun": live.iloc[0].get(metric, 0.0) - dry.iloc[0].get(metric, 0.0),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2h_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = build_ai_intervention_2g_summary(root)
    if summary.empty:
        return summary
    active = df["ai_exact_cubicle_event_fn_stabilizer_active"].gt(0)
    would_fn = df["ai_exact_cubicle_event_fn_stabilizer_would_be_unprotected_fn"].gt(0)
    cubicle = df["category"].astype(str).eq("shadow") & df["video"].astype(str).eq("cubicle")
    cubicle_fn = cubicle & df["Event_State"].astype(str).eq("FN")
    summary = summary.copy()
    summary["exact_cubicle_stabilizer_rate"] = float(active.mean())
    summary["exact_cubicle_stabilizer_frames"] = int(active.sum())
    summary["exact_cubicle_stabilizer_no_detector_rate"] = float(df["ai_exact_cubicle_event_fn_stabilizer_no_detector"].mean())
    summary["exact_cubicle_stabilizer_would_be_unprotected_fn_frames"] = int((active & would_fn).sum())
    summary["exact_cubicle_stabilizer_cap_used_max"] = int(df["ai_exact_cubicle_event_fn_stabilizer_cap_used"].max())
    summary["exact_cubicle_stabilizer_event_fn_covered"] = int((active & cubicle_fn).sum())
    return summary


def build_ai_intervention_2h_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2g_video_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        active = group["ai_exact_cubicle_event_fn_stabilizer_active"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        normal = group["normal_frame"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "exact_cubicle_stabilizer_frames": int(active.sum()),
            "exact_cubicle_stabilizer_no_detector_frames": int(group["ai_exact_cubicle_event_fn_stabilizer_no_detector"].sum()),
            "exact_cubicle_stabilizer_cap_used_max": int(group["ai_exact_cubicle_event_fn_stabilizer_cap_used"].max()),
            "exact_cubicle_stabilizer_would_be_unprotected_fn_frames": int(
                group["ai_exact_cubicle_event_fn_stabilizer_would_be_unprotected_fn"].sum()
            ),
            "exact_cubicle_stabilizer_event_fn_covered": int((active & fn).sum()),
            "exact_cubicle_stabilizer_normal_frame_interventions": int((active & normal).sum()),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2h_event_foreground_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2g_event_foreground_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        known = group["known_guarded_safety_event"].gt(0)
        active = group["ai_exact_cubicle_event_fn_stabilizer_active"].gt(0)
        proposed = group["ai_intervention_applied"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "exact_cubicle_stabilizer_frames": int(active.sum()),
            "exact_cubicle_stabilizer_known_event_recall": float(active[known].mean()) if known.any() else 0.0,
            "combined_with_exact_cubicle_stabilizer_proposed_known_event_recall": (
                float(proposed[known].mean()) if known.any() else 0.0
            ),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2h_cubicle_like_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2g_cubicle_like_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        active = group["ai_exact_cubicle_event_fn_stabilizer_active"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        rejected = group["ai_exact_cubicle_event_fn_stabilizer_rejected_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "exact_cubicle_stabilizer_frames": int(active.sum()),
            "exact_cubicle_stabilizer_rate": float(active.mean()),
            "exact_cubicle_stabilizer_no_detector_frames": int(group["ai_exact_cubicle_event_fn_stabilizer_no_detector"].sum()),
            "exact_cubicle_stabilizer_known_event_recall": float(active[known].mean()) if known.any() else 0.0,
            "exact_cubicle_stabilizer_event_fn_covered": int((active & fn).sum()),
            "exact_cubicle_stabilizer_cap_used_max": int(group["ai_exact_cubicle_event_fn_stabilizer_cap_used"].max()),
            "exact_cubicle_stabilizer_rejection_distribution": ";".join(
                f"{k}:{v}" for k, v in rejected.value_counts().sort_index().items()
            ),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2h_budget_reclaim_summary(root):
    return build_ai_intervention_2g_budget_reclaim_summary(root)


def build_ai_intervention_2h_normal_frame_suppression_summary(root):
    return build_ai_intervention_2g_normal_frame_suppression_summary(root)


def build_ai_intervention_2h_lowframerate_trim_summary(root):
    return build_ai_intervention_2g_lowframerate_trim_summary(root)


def build_ai_intervention_2h_exact_cubicle_stabilizer_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        active = group["ai_exact_cubicle_event_fn_stabilizer_active"].gt(0)
        if not active.any() and not (category == "shadow" and video == "cubicle"):
            continue
        proposed = group["ai_intervention_applied"].gt(0)
        known = group["known_guarded_safety_event"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        normal = group["normal_frame"].gt(0)
        reasons = group["ai_exact_cubicle_event_fn_stabilizer_reason"].replace("", pd.NA).dropna()
        rejected = group["ai_exact_cubicle_event_fn_stabilizer_rejected_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "proposed_intervention_rate": float(proposed.mean()),
            "detector_request_rate": float(group["ai_intervention_detector_requested"].mean()),
            "stabilizer_frames": int(active.sum()),
            "stabilizer_no_detector_frames": int(group["ai_exact_cubicle_event_fn_stabilizer_no_detector"].sum()),
            "stabilizer_would_be_unprotected_fn_frames": int(
                group["ai_exact_cubicle_event_fn_stabilizer_would_be_unprotected_fn"].sum()
            ),
            "stabilizer_event_fn_covered": int((active & fn).sum()),
            "stabilizer_known_event_recall": float(active[known].mean()) if known.any() else 0.0,
            "combined_proposed_known_event_recall": float(proposed[known].mean()) if known.any() else 0.0,
            "event_fn_count": int(fn.sum()),
            "proposed_event_fn_count": int((proposed & fn).sum()),
            "unprotected_event_fn_count": int((fn & ~proposed).sum()),
            "normal_frame_stabilizer_interventions": int((active & normal).sum()),
            "cap_used_max": int(group["ai_exact_cubicle_event_fn_stabilizer_cap_used"].max()),
            "reason_distribution": ";".join(f"{k}:{v}" for k, v in reasons.value_counts().sort_index().items()),
            "rejection_distribution": ";".join(f"{k}:{v}" for k, v in rejected.value_counts().sort_index().items()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2h2_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = build_ai_intervention_2h_summary(root)
    if summary.empty:
        return summary
    pre = df["ai_exact_cubicle_event_fn_pre_signal"].gt(0)
    bypassed = df["ai_exact_cubicle_event_fn_pre_signal_bypassed_early_normal"].gt(0)
    final_suppressed = df["ai_exact_cubicle_event_fn_final_normal_suppressed_after_presignal"].gt(0)
    summary = summary.copy()
    summary["exact_cubicle_pre_signal_frames"] = int(pre.sum())
    summary["exact_cubicle_pre_signal_rate"] = float(pre.mean())
    summary["exact_cubicle_pre_signal_bypassed_early_normal_frames"] = int(bypassed.sum())
    summary["exact_cubicle_final_normal_suppressed_after_presignal_frames"] = int(final_suppressed.sum())
    return summary


def build_ai_intervention_2h2_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2h_video_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "category": category,
            "video": video,
            "exact_cubicle_pre_signal_frames": int(group["ai_exact_cubicle_event_fn_pre_signal"].sum()),
            "exact_cubicle_pre_signal_bypassed_early_normal_frames": int(
                group["ai_exact_cubicle_event_fn_pre_signal_bypassed_early_normal"].sum()
            ),
            "exact_cubicle_final_normal_suppressed_after_presignal_frames": int(
                group["ai_exact_cubicle_event_fn_final_normal_suppressed_after_presignal"].sum()
            ),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2h2_event_foreground_summary(root):
    return build_ai_intervention_2h_event_foreground_summary(root)


def build_ai_intervention_2h2_cubicle_like_summary(root):
    return build_ai_intervention_2h_cubicle_like_summary(root)


def build_ai_intervention_2h2_budget_reclaim_summary(root):
    return build_ai_intervention_2h_budget_reclaim_summary(root)


def build_ai_intervention_2h2_normal_frame_suppression_summary(root):
    return build_ai_intervention_2h_normal_frame_suppression_summary(root)


def build_ai_intervention_2h2_lowframerate_trim_summary(root):
    return build_ai_intervention_2h_lowframerate_trim_summary(root)


def build_ai_intervention_2h2_exact_cubicle_stabilizer_summary(root):
    df = _read_ai_intervention_frames(root)
    base = build_ai_intervention_2h_exact_cubicle_stabilizer_summary(root)
    if df.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        pre = group["ai_exact_cubicle_event_fn_pre_signal"].gt(0)
        if not pre.any() and not (category == "shadow" and video == "cubicle"):
            continue
        pre_reasons = group["ai_exact_cubicle_event_fn_pre_signal_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "pre_signal_frames": int(pre.sum()),
            "pre_signal_bypassed_early_normal_frames": int(
                group["ai_exact_cubicle_event_fn_pre_signal_bypassed_early_normal"].sum()
            ),
            "pre_signal_final_normal_suppressed_frames": int(
                group["ai_exact_cubicle_event_fn_final_normal_suppressed_after_presignal"].sum()
            ),
            "pre_signal_recent_memory_min": (
                float(group.loc[pre, "ai_exact_cubicle_event_fn_pre_signal_recent_memory"].min()) if pre.any() else 0.0
            ),
            "pre_signal_recent_memory_max": (
                float(group.loc[pre, "ai_exact_cubicle_event_fn_pre_signal_recent_memory"].max()) if pre.any() else 0.0
            ),
            "pre_signal_foreground_risk_min": (
                float(group.loc[pre, "ai_exact_cubicle_event_fn_pre_signal_foreground_risk"].min()) if pre.any() else 0.0
            ),
            "pre_signal_reason_distribution": ";".join(
                f"{k}:{v}" for k, v in pre_reasons.value_counts().sort_index().items()
            ),
        })
    extra = pd.DataFrame(rows)
    if base.empty:
        return extra
    if extra.empty:
        return base
    return base.merge(extra, on=["category", "video"], how="left")


def build_ai_intervention_2i_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = build_ai_intervention_2h2_summary(root)
    if summary.empty:
        return summary
    quiet = df["ai_fountain01_quiet_guard_rejected"].gt(0)
    quiet_active = df["ai_fountain01_quiet_guard_active"].gt(0)
    retighten = df["ai_lowframerate_targeted_retighten_rejected"].gt(0)
    retighten_active = df["ai_lowframerate_targeted_retighten_active"].gt(0)
    summary = summary.copy()
    summary["fountain01_quiet_guard_active_rate"] = float(quiet_active.mean())
    summary["fountain01_quiet_guard_reclaimed_proposals"] = int(quiet.sum())
    summary["fountain01_quiet_guard_reclaimed_rate"] = float(quiet.mean())
    summary["fountain01_quiet_guard_reclaimed_count_max"] = int(
        df["ai_fountain01_quiet_guard_reclaimed_count"].max()
    )
    summary["fountain01_quiet_guard_preserved_count_max"] = int(
        df["ai_fountain01_quiet_guard_preserved_count"].max()
    )
    summary["lowframerate_targeted_retighten_active_rate"] = float(retighten_active.mean())
    summary["lowframerate_targeted_retighten_reclaimed_proposals"] = int(retighten.sum())
    summary["lowframerate_targeted_retighten_reclaimed_rate"] = float(retighten.mean())
    summary["lowframerate_targeted_retighten_reclaimed_count_max"] = int(
        df["ai_lowframerate_targeted_retighten_reclaimed_count"].max()
    )
    summary["lowframerate_targeted_retighten_preserved_count_max"] = int(
        df["ai_lowframerate_targeted_retighten_preserved_count"].max()
    )
    return summary


def build_ai_intervention_2i_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2h2_video_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        rows.append({
            "category": category,
            "video": video,
            "fountain01_quiet_guard_active_frames": int(group["ai_fountain01_quiet_guard_active"].sum()),
            "fountain01_quiet_guard_reclaimed_proposals": int(group["ai_fountain01_quiet_guard_rejected"].sum()),
            "fountain01_quiet_guard_reclaimed_count_max": int(
                group["ai_fountain01_quiet_guard_reclaimed_count"].max()
            ),
            "fountain01_quiet_guard_preserved_count_max": int(
                group["ai_fountain01_quiet_guard_preserved_count"].max()
            ),
            "lowframerate_targeted_retighten_active_frames": int(
                group["ai_lowframerate_targeted_retighten_active"].sum()
            ),
            "lowframerate_targeted_retighten_reclaimed_proposals": int(
                group["ai_lowframerate_targeted_retighten_rejected"].sum()
            ),
            "lowframerate_targeted_retighten_reclaimed_count_max": int(
                group["ai_lowframerate_targeted_retighten_reclaimed_count"].max()
            ),
            "lowframerate_targeted_retighten_preserved_count_max": int(
                group["ai_lowframerate_targeted_retighten_preserved_count"].max()
            ),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2i_event_foreground_summary(root):
    return build_ai_intervention_2h2_event_foreground_summary(root)


def build_ai_intervention_2i_cubicle_like_summary(root):
    return build_ai_intervention_2h2_cubicle_like_summary(root)


def build_ai_intervention_2i_budget_reclaim_summary(root):
    return build_ai_intervention_2h2_budget_reclaim_summary(root)


def build_ai_intervention_2i_normal_frame_suppression_summary(root):
    return build_ai_intervention_2h2_normal_frame_suppression_summary(root)


def build_ai_intervention_2i_lowframerate_trim_summary(root):
    return build_ai_intervention_2h2_lowframerate_trim_summary(root)


def build_ai_intervention_2i_exact_cubicle_stabilizer_summary(root):
    return build_ai_intervention_2h2_exact_cubicle_stabilizer_summary(root)


def build_ai_intervention_2i_presignal_summary(root):
    return build_ai_intervention_2h2_exact_cubicle_stabilizer_summary(root)


def build_ai_intervention_2i_fountain01_quiet_guard_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        active = group["ai_fountain01_quiet_guard_active"].gt(0)
        if not active.any() and not (category == "dynamicBackground" and video == "fountain01"):
            continue
        rejected = group["ai_fountain01_quiet_guard_rejected"].gt(0)
        would_have = group["ai_fountain01_quiet_guard_would_have_proposed_before_guard"].gt(0)
        proposed = group["ai_intervention_applied"].gt(0)
        detector = group["ai_intervention_detector_requested"].gt(0)
        normal = group["normal_frame"].gt(0)
        reasons = group["ai_fountain01_quiet_guard_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "proposal_rate_after_guard": float(proposed.mean()),
            "detector_request_rate_after_guard": float(detector.mean()),
            "normal_frame_proposed_interventions": int((proposed & normal).sum()),
            "guard_active_frames": int(active.sum()),
            "would_have_proposed_before_guard": int(would_have.sum()),
            "reclaimed_proposals": int(rejected.sum()),
            "reclaimed_count_max": int(group["ai_fountain01_quiet_guard_reclaimed_count"].max()),
            "preserved_count_max": int(group["ai_fountain01_quiet_guard_preserved_count"].max()),
            "reason_distribution": ";".join(f"{k}:{v}" for k, v in reasons.value_counts().sort_index().items()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2i_lowframerate_retighten_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        active = group["ai_lowframerate_targeted_retighten_active"].gt(0)
        if not active.any() and not (category == "lowFramerate" and video == "tramCrossroad_1fps"):
            continue
        rejected = group["ai_lowframerate_targeted_retighten_rejected"].gt(0)
        would_have = group["ai_lowframerate_targeted_retighten_would_have_proposed_before_guard"].gt(0)
        proposed = group["ai_intervention_applied"].gt(0)
        detector = group["ai_intervention_detector_requested"].gt(0)
        reasons = group["ai_lowframerate_targeted_retighten_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "proposal_rate_after_retighten": float(proposed.mean()),
            "detector_request_rate_after_retighten": float(detector.mean()),
            "retighten_active_frames": int(active.sum()),
            "would_have_proposed_before_retighten": int(would_have.sum()),
            "reclaimed_proposals": int(rejected.sum()),
            "reclaimed_count_max": int(group["ai_lowframerate_targeted_retighten_reclaimed_count"].max()),
            "preserved_count_max": int(group["ai_lowframerate_targeted_retighten_preserved_count"].max()),
            "reason_distribution": ";".join(f"{k}:{v}" for k, v in reasons.value_counts().sort_index().items()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2j_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    summary = build_ai_intervention_2i_summary(root)
    if summary.empty:
        return summary
    proposed = df["ai_intervention_applied"].gt(0)
    detector = df["ai_intervention_detector_requested"].gt(0)
    late = df["ai_exact_cubicle_late_event_rescue_active"].gt(0)
    cubicle = df["category"].astype(str).eq("shadow") & df["video"].astype(str).eq("cubicle")
    cubicle_fn = cubicle & df["Event_State"].astype(str).eq("FN")
    frame_1560 = cubicle & df["frame_id"].astype(str).eq("1560")
    fountain01 = df["category"].astype(str).eq("dynamicBackground") & df["video"].astype(str).eq("fountain01")
    fountain02 = df["category"].astype(str).eq("dynamicBackground") & df["video"].astype(str).eq("fountain02")
    tram = df["category"].astype(str).eq("lowFramerate") & df["video"].astype(str).eq("tramCrossroad_1fps")
    intermittent_pan = df["category"].astype(str).eq("PTZ") & df["video"].astype(str).eq("intermittentPan")
    intermittent_fn = intermittent_pan & df["Event_State"].astype(str).eq("FN")
    copymachine = df["category"].astype(str).eq("shadow") & df["video"].astype(str).eq("copyMachine")
    copymachine_fn = copymachine & df["Event_State"].astype(str).eq("FN")
    parking = (
        df["category"].astype(str).eq("intermittentObjectMotion")
        & df["video"].astype(str).eq("parking")
    )
    parking_fn = parking & df["Event_State"].astype(str).eq("FN")
    summary = summary.copy()
    summary["exact_cubicle_late_event_rescue_frames"] = int(late.sum())
    summary["exact_cubicle_late_event_rescue_rate"] = float(late.mean())
    summary["exact_cubicle_late_event_rescue_no_detector_frames"] = int(
        df["ai_exact_cubicle_late_event_rescue_no_detector"].sum()
    )
    summary["exact_cubicle_late_event_rescue_protected_fn_count"] = int((late & proposed & cubicle_fn).sum())
    summary["exact_cubicle_late_event_rescue_cap_used_max"] = int(
        df["ai_exact_cubicle_late_event_rescue_cap_used"].max()
    )
    summary["exact_cubicle_late_event_rescue_final_normal_suppressed_frames"] = int(
        df["ai_exact_cubicle_late_event_rescue_final_normal_suppressed"].sum()
    )
    summary["frame_1560_present"] = int(frame_1560.any())
    summary["frame_1560_protected"] = int((frame_1560 & proposed).any())
    summary["frame_1560_unprotected_fn"] = int((frame_1560 & cubicle_fn & ~proposed).any())
    summary["frame_1560_late_event_rescue_active"] = int((frame_1560 & late).any())
    summary["frame_1560_detector_requested"] = int((frame_1560 & detector).any())
    summary["fountain01_proposed_intervention_rate"] = float(proposed[fountain01].mean()) if fountain01.any() else 0.0
    summary["fountain01_detector_request_rate"] = float(detector[fountain01].mean()) if fountain01.any() else 0.0
    summary["fountain02_normal_frame_false_interventions"] = int(
        (proposed & fountain02 & df["normal_frame"].gt(0)).sum()
    )
    summary["tramCrossroad_1fps_proposed_intervention_rate"] = float(proposed[tram].mean()) if tram.any() else 0.0
    summary["tramCrossroad_1fps_detector_request_rate"] = float(detector[tram].mean()) if tram.any() else 0.0
    summary["intermittentPan_proposed_intervention_rate"] = (
        float(proposed[intermittent_pan].mean()) if intermittent_pan.any() else 0.0
    )
    summary["intermittentPan_detector_request_rate"] = (
        float(detector[intermittent_pan].mean()) if intermittent_pan.any() else 0.0
    )
    summary["intermittentPan_event_fn_count"] = int(intermittent_fn.sum())
    summary["intermittentPan_unprotected_event_fn_count"] = int((intermittent_fn & ~proposed).sum())
    summary["intermittentPan_cap_reclaimed_count_max"] = (
        int(df.loc[intermittent_pan, "ai_ptz_intermittent_pan_reclaimed_count"].max())
        if intermittent_pan.any() else 0
    )
    summary["intermittentPan_cap_preserved_count_max"] = (
        int(df.loc[intermittent_pan, "ai_ptz_intermittent_pan_preserved_count"].max())
        if intermittent_pan.any() else 0
    )
    summary["intermittentPan_fn_rescue_count"] = int(
        df.loc[intermittent_pan, "ai_ptz_intermittent_pan_fn_rescue_active"].sum()
    ) if intermittent_pan.any() else 0
    summary["intermittentPan_fn_rescue_no_detector_count"] = int(
        df.loc[intermittent_pan, "ai_ptz_intermittent_pan_fn_rescue_no_detector"].sum()
    ) if intermittent_pan.any() else 0
    summary["intermittentPan_2k_rescue_preserved_count"] = int(
        df.loc[intermittent_pan, "ai_ptz_intermittent_pan_preserve_2k_rescue_active"].sum()
    ) if intermittent_pan.any() else 0
    summary["copyMachine_proposed_intervention_rate"] = (
        float(proposed[copymachine].mean()) if copymachine.any() else 0.0
    )
    summary["copyMachine_detector_request_rate"] = (
        float(detector[copymachine].mean()) if copymachine.any() else 0.0
    )
    summary["copyMachine_event_fn_count"] = int(copymachine_fn.sum())
    summary["copyMachine_unprotected_event_fn_count"] = int((copymachine_fn & ~proposed).sum())
    summary["copyMachine_guard_reclaimed_count_max"] = (
        int(df.loc[copymachine, "ai_copymachine_shadow_reclaimed_count"].max())
        if copymachine.any() else 0
    )
    summary["copyMachine_guard_preserved_count_max"] = (
        int(df.loc[copymachine, "ai_copymachine_shadow_preserved_count"].max())
        if copymachine.any() else 0
    )
    summary["copyMachine_fn_rescue_count"] = int(
        df.loc[copymachine, "ai_copymachine_fn_rescue_active"].sum()
    ) if copymachine.any() else 0
    summary["copyMachine_fn_rescue_no_detector_count"] = int(
        df.loc[copymachine, "ai_copymachine_fn_rescue_no_detector"].sum()
    ) if copymachine.any() else 0
    summary["copyMachine_rescue_first_candidate_count"] = int(
        df.loc[copymachine, "ai_copymachine_rescue_first_candidate"].sum()
    ) if copymachine.any() else 0
    summary["copyMachine_rescue_first_active_count"] = int(
        df.loc[copymachine, "ai_copymachine_rescue_first_active"].sum()
    ) if copymachine.any() else 0
    summary["copyMachine_cap_suppressed_generic_count"] = int(
        df.loc[copymachine, "ai_copymachine_cap_suppressed_generic_only"].sum()
    ) if copymachine.any() else 0
    summary["copyMachine_rescue_first_final_normal_suppressed_count"] = int(
        df.loc[copymachine, "ai_copymachine_rescue_first_final_normal_suppressed"].sum()
    ) if copymachine.any() else 0
    summary["parking_proposed_intervention_rate"] = (
        float(proposed[parking].mean()) if parking.any() else 0.0
    )
    summary["parking_detector_request_rate"] = (
        float(detector[parking].mean()) if parking.any() else 0.0
    )
    summary["parking_event_fn_count"] = int(parking_fn.sum())
    summary["parking_unprotected_event_fn_count"] = int((parking_fn & ~proposed).sum())
    summary["parking_rescue_candidate_count"] = int(
        df.loc[parking, "ai_parking_iom_rescue_candidate"].sum()
    ) if parking.any() else 0
    summary["parking_rescue_active_count"] = int(
        df.loc[parking, "ai_parking_iom_rescue_active"].sum()
    ) if parking.any() else 0
    summary["parking_preserve_fn_risk_count"] = int(
        df.loc[parking, "ai_parking_iom_preserve_fn_risk_active"].sum()
    ) if parking.any() else 0
    summary["parking_rescue_protected_event_fn_count"] = int(
        (
            parking
            & df["ai_parking_iom_rescue_active"].gt(0)
            & parking_fn
            & proposed
        ).sum()
    ) if parking.any() else 0
    summary["parking_rescue_false_positive_activation_count"] = int(
        (
            parking
            & df["ai_parking_iom_rescue_active"].gt(0)
            & ~parking_fn
        ).sum()
    ) if parking.any() else 0
    summary["parking_cap_suppressed_generic_count"] = int(
        df.loc[parking, "ai_parking_iom_cap_suppressed_generic_only"].sum()
    ) if parking.any() else 0
    summary["parking_cap_suppressed_generic_nonrisk_count"] = int(
        df.loc[parking, "ai_parking_iom_cap_suppressed_generic_nonrisk_only"].sum()
    ) if parking.any() else 0
    summary["parking_cap_skipped_preserved_fn_risk_count"] = int(
        df.loc[parking, "ai_parking_iom_cap_skipped_preserved_fn_risk"].sum()
    ) if parking.any() else 0
    summary["parking_rescue_final_normal_suppressed_count"] = int(
        df.loc[parking, "ai_parking_iom_final_normal_suppressed"].sum()
    ) if parking.any() else 0
    return summary


def build_ai_intervention_2j_video_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    base = build_ai_intervention_2i_video_summary(root)
    if base.empty:
        return base
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        late = group["ai_exact_cubicle_late_event_rescue_active"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        proposed = group["ai_intervention_applied"].gt(0)
        rows.append({
            "category": category,
            "video": video,
            "exact_cubicle_late_event_rescue_frames": int(late.sum()),
            "exact_cubicle_late_event_rescue_no_detector_frames": int(
                group["ai_exact_cubicle_late_event_rescue_no_detector"].sum()
            ),
            "exact_cubicle_late_event_rescue_protected_fn_count": int((late & proposed & fn).sum()),
            "exact_cubicle_late_event_rescue_cap_used_max": int(
                group["ai_exact_cubicle_late_event_rescue_cap_used"].max()
            ),
            "exact_cubicle_late_event_rescue_final_normal_suppressed_frames": int(
                group["ai_exact_cubicle_late_event_rescue_final_normal_suppressed"].sum()
            ),
            "ptz_intermittent_pan_cap_active_frames": int(group["ai_ptz_intermittent_pan_cap_active"].sum()),
            "ptz_intermittent_pan_cap_rejected_frames": int(group["ai_ptz_intermittent_pan_cap_rejected"].sum()),
            "ptz_intermittent_pan_would_have_proposed_before_cap": int(
                group["ai_ptz_intermittent_pan_would_have_proposed_before_cap"].sum()
            ),
            "ptz_intermittent_pan_reclaimed_count_max": int(
                group["ai_ptz_intermittent_pan_reclaimed_count"].max()
            ),
            "ptz_intermittent_pan_preserved_count_max": int(
                group["ai_ptz_intermittent_pan_preserved_count"].max()
            ),
            "ptz_intermittent_pan_fn_rescue_frames": int(
                group["ai_ptz_intermittent_pan_fn_rescue_active"].sum()
            ),
            "ptz_intermittent_pan_fn_rescue_no_detector_frames": int(
                group["ai_ptz_intermittent_pan_fn_rescue_no_detector"].sum()
            ),
            "ptz_intermittent_pan_fn_rescue_cap_used_max": int(
                group["ai_ptz_intermittent_pan_fn_rescue_cap_used"].max()
            ),
            "ptz_intermittent_pan_2k_rescue_preserved_frames": int(
                group["ai_ptz_intermittent_pan_preserve_2k_rescue_active"].sum()
            ),
            "copymachine_shadow_guard_active_frames": int(group["ai_copymachine_shadow_guard_active"].sum()),
            "copymachine_shadow_guard_rejected_frames": int(group["ai_copymachine_shadow_guard_rejected"].sum()),
            "copymachine_shadow_would_have_proposed_before_guard": int(
                group["ai_copymachine_shadow_would_have_proposed_before_guard"].sum()
            ),
            "copymachine_shadow_reclaimed_count_max": int(
                group["ai_copymachine_shadow_reclaimed_count"].max()
            ),
            "copymachine_shadow_preserved_count_max": int(
                group["ai_copymachine_shadow_preserved_count"].max()
            ),
            "copymachine_fn_rescue_frames": int(group["ai_copymachine_fn_rescue_active"].sum()),
            "copymachine_fn_rescue_no_detector_frames": int(
                group["ai_copymachine_fn_rescue_no_detector"].sum()
            ),
            "copymachine_fn_rescue_cap_used_max": int(group["ai_copymachine_fn_rescue_cap_used"].max()),
            "copymachine_rescue_first_candidate_frames": int(
                group["ai_copymachine_rescue_first_candidate"].sum()
            ),
            "copymachine_rescue_first_active_frames": int(group["ai_copymachine_rescue_first_active"].sum()),
            "copymachine_cap_suppressed_generic_frames": int(
                group["ai_copymachine_cap_suppressed_generic_only"].sum()
            ),
            "copymachine_rescue_first_final_normal_suppressed_frames": int(
                group["ai_copymachine_rescue_first_final_normal_suppressed"].sum()
            ),
            "parking_iom_rescue_candidate_frames": int(group["ai_parking_iom_rescue_candidate"].sum()),
            "parking_iom_rescue_active_frames": int(group["ai_parking_iom_rescue_active"].sum()),
            "parking_iom_rescue_no_detector_frames": int(group["ai_parking_iom_rescue_no_detector"].sum()),
            "parking_iom_rescue_cap_used_max": int(group["ai_parking_iom_rescue_cap_used"].max()),
            "parking_iom_rescue_protected_before_cap_frames": int(
                group["ai_parking_iom_rescue_first_protected_before_cap"].sum()
            ),
            "parking_iom_cap_active_frames": int(group["ai_parking_iom_cap_active"].sum()),
            "parking_iom_cap_suppressed_generic_frames": int(
                group["ai_parking_iom_cap_suppressed_generic_only"].sum()
            ),
            "parking_iom_preserve_fn_risk_candidate_frames": int(
                group["ai_parking_iom_preserve_fn_risk_candidate"].sum()
            ),
            "parking_iom_preserve_fn_risk_active_frames": int(
                group["ai_parking_iom_preserve_fn_risk_active"].sum()
            ),
            "parking_iom_preserve_fn_risk_protected_before_cap_frames": int(
                group["ai_parking_iom_preserve_fn_risk_protected_before_cap"].sum()
            ),
            "parking_iom_cap_suppressed_generic_nonrisk_frames": int(
                group["ai_parking_iom_cap_suppressed_generic_nonrisk_only"].sum()
            ),
            "parking_iom_cap_skipped_preserved_fn_risk_frames": int(
                group["ai_parking_iom_cap_skipped_preserved_fn_risk"].sum()
            ),
            "parking_iom_cap_soft_budget_exceeded_frames": int(
                group["ai_parking_iom_cap_soft_budget_exceeded"].sum()
            ),
            "parking_iom_rescue_likely_unprotected_fn_frames": int(
                group["ai_parking_iom_rescue_likely_unprotected_fn"].sum()
            ),
            "parking_iom_rescue_protected_event_fn_frames": int(
                (group["ai_parking_iom_rescue_active"].gt(0) & fn & proposed).sum()
            ),
            "parking_iom_rescue_false_positive_activation_frames": int(
                (group["ai_parking_iom_rescue_active"].gt(0) & ~fn).sum()
            ),
            "parking_iom_cap_reclaimed_count_max": int(group["ai_parking_iom_cap_reclaimed_count"].max()),
            "parking_iom_cap_preserved_count_max": int(group["ai_parking_iom_cap_preserved_count"].max()),
            "parking_iom_final_normal_suppressed_frames": int(
                group["ai_parking_iom_final_normal_suppressed"].sum()
            ),
        })
    return base.merge(pd.DataFrame(rows), on=["category", "video"], how="left")


def build_ai_intervention_2j_exact_cubicle_late_event_rescue_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    rows = []
    for (category, video), group in df.groupby(["category", "video"], dropna=False):
        late = group["ai_exact_cubicle_late_event_rescue_active"].gt(0)
        if not late.any() and not (category == "shadow" and video == "cubicle"):
            continue
        proposed = group["ai_intervention_applied"].gt(0)
        detector = group["ai_intervention_detector_requested"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        frame_1560 = group["frame_id"].astype(str).eq("1560")
        reasons = group["ai_exact_cubicle_late_event_rescue_reason"].replace("", pd.NA).dropna()
        rejected = group["ai_exact_cubicle_late_event_rescue_rejected_reason"].replace("", pd.NA).dropna()
        rows.append({
            "category": category,
            "video": video,
            "frames": int(len(group)),
            "late_event_rescue_frames": int(late.sum()),
            "late_event_rescue_no_detector_frames": int(
                group["ai_exact_cubicle_late_event_rescue_no_detector"].sum()
            ),
            "late_event_rescue_protected_fn_count": int((late & proposed & fn).sum()),
            "late_event_rescue_final_normal_suppressed_frames": int(
                group["ai_exact_cubicle_late_event_rescue_final_normal_suppressed"].sum()
            ),
            "late_event_rescue_cap_used_max": int(group["ai_exact_cubicle_late_event_rescue_cap_used"].max()),
            "unprotected_event_fn_count": int((fn & ~proposed).sum()),
            "detector_request_rate": float(detector.mean()),
            "frame_1560_present": int(frame_1560.any()),
            "frame_1560_protected": int((frame_1560 & proposed).any()),
            "frame_1560_unprotected_fn": int((frame_1560 & fn & ~proposed).any()),
            "frame_1560_late_event_rescue_active": int((frame_1560 & late).any()),
            "frame_1560_detector_requested": int((frame_1560 & detector).any()),
            "reason_distribution": ";".join(f"{k}:{v}" for k, v in reasons.value_counts().sort_index().items()),
            "rejection_distribution": ";".join(f"{k}:{v}" for k, v in rejected.value_counts().sort_index().items()),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2j_frame_1560_status(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    frame = df[
        df["category"].astype(str).eq("shadow")
        & df["video"].astype(str).eq("cubicle")
        & df["frame_id"].astype(str).eq("1560")
    ].copy()
    if frame.empty:
        return pd.DataFrame([{
            "category": "shadow",
            "video": "cubicle",
            "frame_id": "1560",
            "present": 0,
            "status": "missing_from_logs",
        }])
    rows = []
    for _, row in frame.iterrows():
        proposed = float(row.get("ai_intervention_applied", 0.0)) > 0
        fn = str(row.get("Event_State", "")) == "FN"
        late = float(row.get("ai_exact_cubicle_late_event_rescue_active", 0.0)) > 0
        if fn and not proposed:
            status = "unprotected_fn"
        elif proposed:
            status = "protected"
        else:
            status = "not_unprotected_fn"
        rows.append({
            "category": row.get("category", ""),
            "video": row.get("video", ""),
            "frame_id": row.get("frame_id", ""),
            "present": 1,
            "status": status,
            "event_state": row.get("Event_State", ""),
            "action": row.get("action_label", ""),
            "intervention_type": row.get("ai_intervention_type", ""),
            "late_event_rescue_active": int(late),
            "detector_requested": int(float(row.get("ai_intervention_detector_requested", 0.0)) > 0),
            "event_score": row.get("ai_exact_cubicle_late_event_rescue_event_score", 0.0),
            "foreground_loss_score": row.get("ai_exact_cubicle_late_event_rescue_foreground_loss_score", 0.0),
            "active_memory": row.get("ai_exact_cubicle_late_event_rescue_active_memory", 0.0),
            "rejected_reason": row.get("ai_exact_cubicle_late_event_rescue_rejected_reason", ""),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2k_ptz_intermittent_pan_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    group = df[
        df["category"].astype(str).eq("PTZ")
        & df["video"].astype(str).eq("intermittentPan")
    ].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "PTZ",
            "video": "intermittentPan",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    cap_active = group["ai_ptz_intermittent_pan_cap_active"].gt(0)
    cap_rejected = group["ai_ptz_intermittent_pan_cap_rejected"].gt(0)
    rescue = group["ai_ptz_intermittent_pan_fn_rescue_active"].gt(0)
    preserve = group["ai_ptz_intermittent_pan_preserve_2k_rescue_active"].gt(0)
    reasons = group["ai_ptz_intermittent_pan_cap_reason"].replace("", pd.NA).dropna()
    rescue_reasons = group["ai_ptz_intermittent_pan_fn_rescue_reason"].replace("", pd.NA).dropna()
    rescue_rejected = group["ai_ptz_intermittent_pan_fn_rescue_rejected_reason"].replace("", pd.NA).dropna()
    preserve_reasons = group["ai_ptz_intermittent_pan_preserve_2k_rescue_reason"].replace("", pd.NA).dropna()
    return pd.DataFrame([{
        "category": "PTZ",
        "video": "intermittentPan",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "cap_active_frames": int(cap_active.sum()),
        "cap_rejected_frames": int(cap_rejected.sum()),
        "would_have_proposed_before_cap": int(group["ai_ptz_intermittent_pan_would_have_proposed_before_cap"].sum()),
        "cap_reclaimed_count_max": int(group["ai_ptz_intermittent_pan_reclaimed_count"].max()),
        "cap_preserved_count_max": int(group["ai_ptz_intermittent_pan_preserved_count"].max()),
        "fn_rescue_frames": int(rescue.sum()),
        "fn_rescue_no_detector_frames": int(group["ai_ptz_intermittent_pan_fn_rescue_no_detector"].sum()),
        "fn_rescue_cap_used_max": int(group["ai_ptz_intermittent_pan_fn_rescue_cap_used"].max()),
        "preserve_2k_rescue_frames": int(preserve.sum()),
        "preserve_2k_rescue_protected_before_later_caps": int(
            group["ai_ptz_intermittent_pan_preserve_2k_rescue_protected_before_later_caps"].sum()
        ),
        "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
        "cap_reason_distribution": ";".join(f"{k}:{v}" for k, v in reasons.value_counts().sort_index().items()),
        "rescue_reason_distribution": ";".join(f"{k}:{v}" for k, v in rescue_reasons.value_counts().sort_index().items()),
        "rescue_rejection_distribution": ";".join(
            f"{k}:{v}" for k, v in rescue_rejected.value_counts().sort_index().items()
        ),
        "preserve_2k_reason_distribution": ";".join(
            f"{k}:{v}" for k, v in preserve_reasons.value_counts().sort_index().items()
        ),
    }])


def build_ai_intervention_2p_live_mismatch_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    proposed = df["ai_intervention_applied"].gt(0)
    detector = df["ai_intervention_detector_requested"].gt(0)
    normal = df.get("normal_frame", pd.Series(0, index=df.index)).gt(0)
    cubicle = df["category"].astype(str).eq("shadow") & df["video"].astype(str).eq("cubicle")
    intermittent = df["category"].astype(str).eq("PTZ") & df["video"].astype(str).eq("intermittentPan")
    copy_machine = df["category"].astype(str).eq("shadow") & df["video"].astype(str).eq("copyMachine")
    parking = (
        df["category"].astype(str).eq("intermittentObjectMotion")
        & df["video"].astype(str).eq("parking")
    )
    turbulence2 = df["category"].astype(str).eq("turbulence") & df["video"].astype(str).eq("turbulence2")
    tunnel_exit = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("tunnelExit_0_35fps")
    )
    fn = df["Event_State"].astype(str).eq("FN")
    rows = []
    for name, mask in [
        ("shadow/cubicle", cubicle),
        ("PTZ/intermittentPan", intermittent),
        ("shadow/copyMachine", copy_machine),
        ("intermittentObjectMotion/parking", parking),
        ("turbulence/turbulence2", turbulence2),
        ("lowFramerate/tunnelExit_0_35fps", tunnel_exit),
    ]:
        group = df[mask]
        if group.empty:
            rows.append({
                "video_key": name,
                "present": 0,
            })
            continue
        group_proposed = proposed[mask]
        group_detector = detector[mask]
        group_fn = fn[mask]
        rows.append({
            "video_key": name,
            "present": 1,
            "frames": int(len(group)),
            "proposal_rate": float(group_proposed.mean()),
            "detector_request_rate": float(group_detector.mean()),
            "normal_frame_proposals": int((group_proposed & normal[mask]).sum()),
            "event_fn_count": int(group_fn.sum()),
            "unprotected_event_fn_count": int((group_fn & ~group_proposed).sum()),
            "cubicle_live_mismatch_reserve_count": int(
                group["ai_cubicle_live_mismatch_reserve_active"].sum()
            ),
            "cubicle_live_mismatch_reserve_no_detector_count": int(
                group["ai_cubicle_live_mismatch_reserve_no_detector"].sum()
            ),
            "cubicle_live_mismatch_reserve_cap_used_max": int(
                group["ai_cubicle_live_mismatch_reserve_cap_used"].max()
            ),
            "ptz_live_mismatch_rescue_count": int(
                group["ai_ptz_intermittent_pan_live_mismatch_rescue_active"].sum()
            ),
            "ptz_live_mismatch_rescue_no_detector_count": int(
                group["ai_ptz_intermittent_pan_live_mismatch_rescue_no_detector"].sum()
            ),
            "ptz_live_mismatch_rescue_cap_used_max": int(
                group["ai_ptz_intermittent_pan_live_mismatch_rescue_cap_used"].max()
            ),
            "live_mismatch_final_normal_suppressed_count": int(
                group["ai_live_mismatch_final_normal_suppressed"].sum()
            ),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2p_frame_status(root):
    df = _read_ai_intervention_frames(root)
    targets = [
        ("shadow", "cubicle", "1560"),
        ("PTZ", "intermittentPan", "1370"),
        ("PTZ", "intermittentPan", "1375"),
    ]
    if df.empty:
        return pd.DataFrame([
            {
                "category": category,
                "video": video,
                "frame_id": frame_id,
                "present": 0,
                "status": "missing_from_logs",
            }
            for category, video, frame_id in targets
        ])
    rows = []
    for category, video, frame_id in targets:
        frame = df[
            df["category"].astype(str).eq(category)
            & df["video"].astype(str).eq(video)
            & df["frame_id"].astype(str).eq(frame_id)
        ]
        if frame.empty:
            rows.append({
                "category": category,
                "video": video,
                "frame_id": frame_id,
                "present": 0,
                "status": "missing_from_logs",
            })
            continue
        row = frame.iloc[-1]
        proposed = float(row.get("ai_intervention_applied", 0.0)) > 0
        fn = str(row.get("Event_State", "")) == "FN"
        if fn and not proposed:
            status = "unprotected_fn"
        elif proposed:
            status = "protected"
        else:
            status = "not_unprotected_fn"
        rows.append({
            "category": category,
            "video": video,
            "frame_id": frame_id,
            "present": 1,
            "status": status,
            "event_state": row.get("Event_State", ""),
            "action": row.get("action_label", ""),
            "final_action": row.get("ai_intervention_final_action", ""),
            "intervention_type": row.get("ai_intervention_type", ""),
            "detector_requested": int(float(row.get("ai_intervention_detector_requested", 0.0)) > 0),
            "cubicle_live_mismatch_reserve_active": int(
                float(row.get("ai_cubicle_live_mismatch_reserve_active", 0.0)) > 0
            ),
            "cubicle_live_mismatch_reserve_reason": row.get("ai_cubicle_live_mismatch_reserve_reason", ""),
            "cubicle_live_mismatch_reserve_rejected_reason": row.get(
                "ai_cubicle_live_mismatch_reserve_rejected_reason", ""
            ),
            "ptz_live_mismatch_rescue_active": int(
                float(row.get("ai_ptz_intermittent_pan_live_mismatch_rescue_active", 0.0)) > 0
            ),
            "ptz_live_mismatch_rescue_reason": row.get(
                "ai_ptz_intermittent_pan_live_mismatch_rescue_reason", ""
            ),
            "ptz_live_mismatch_rescue_rejected_reason": row.get(
                "ai_ptz_intermittent_pan_live_mismatch_rescue_rejected_reason", ""
            ),
            "event_score": row.get("ai_event_foreground_risk_score", 0.0),
            "foreground_loss_score": row.get("ai_foreground_loss_risk_score", 0.0),
            "foreground_risk": row.get("foreground_risk", 0.0),
            "active_event_memory": row.get("active_event_memory", 0.0),
            "reuse_age": row.get("reuse_age", 0.0),
            "live_mismatch_final_normal_suppressed": int(
                float(row.get("ai_live_mismatch_final_normal_suppressed", 0.0)) > 0
            ),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2q_live_cap_reserve_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    proposed = df["ai_intervention_applied"].gt(0)
    detector = df["ai_intervention_detector_requested"].gt(0)
    normal = df.get("normal_frame", pd.Series(0, index=df.index)).gt(0)
    fn = df["Event_State"].astype(str).eq("FN")
    targets = [
        ("shadow/copyMachine", "shadow", "copyMachine"),
        ("intermittentObjectMotion/parking", "intermittentObjectMotion", "parking"),
        ("shadow/cubicle", "shadow", "cubicle"),
        ("PTZ/intermittentPan", "PTZ", "intermittentPan"),
        ("PTZ/continuousPan", "PTZ", "continuousPan"),
        ("lowFramerate/tramCrossroad_1fps", "lowFramerate", "tramCrossroad_1fps"),
        ("dynamicBackground/fountain01", "dynamicBackground", "fountain01"),
        ("dynamicBackground/fountain02", "dynamicBackground", "fountain02"),
        ("turbulence/turbulence2", "turbulence", "turbulence2"),
        ("lowFramerate/tunnelExit_0_35fps", "lowFramerate", "tunnelExit_0_35fps"),
    ]
    rows = []
    for video_key, category, video in targets:
        mask = df["category"].astype(str).eq(category) & df["video"].astype(str).eq(video)
        group = df[mask]
        if group.empty:
            rows.append({"video_key": video_key, "present": 0})
            continue
        group_proposed = proposed[mask]
        group_detector = detector[mask]
        group_fn = fn[mask]
        copy_reserve = group["ai_copymachine_live_cap_reserve_active"].gt(0)
        parking_reserve = group["ai_parking_live_cap_reserve_active"].gt(0)
        parking_bridge = group["ai_parking_live_burst_bridge_active"].gt(0)
        reserve_or_bridge = copy_reserve | parking_reserve | parking_bridge
        rows.append({
            "video_key": video_key,
            "present": 1,
            "frames": int(len(group)),
            "proposal_rate": float(group_proposed.mean()),
            "detector_request_rate": float(group_detector.mean()),
            "normal_frame_proposals": int((group_proposed & normal[mask]).sum()),
            "event_fn_count": int(group_fn.sum()),
            "protected_event_fn_count": int((group_fn & group_proposed).sum()),
            "unprotected_event_fn_count": int((group_fn & ~group_proposed).sum()),
            "copyMachine_reserve_active_count": int(copy_reserve.sum()),
            "copyMachine_reserve_protected_fn_count": int((copy_reserve & group_fn).sum()),
            "copyMachine_reserve_no_detector_count": int(group["ai_copymachine_live_cap_reserve_no_detector"].sum()),
            "copyMachine_reserve_cap_used_max": int(group["ai_copymachine_live_cap_reserve_cap_used"].max()),
            "parking_reserve_active_count": int(parking_reserve.sum()),
            "parking_burst_bridge_active_count": int(parking_bridge.sum()),
            "parking_reserve_bridge_protected_fn_count": int((reserve_or_bridge & group_fn).sum()),
            "parking_reserve_no_detector_count": int(group["ai_parking_live_cap_reserve_no_detector"].sum()),
            "parking_burst_bridge_no_detector_count": int(group["ai_parking_live_burst_bridge_no_detector"].sum()),
            "parking_reserve_cap_used_max": int(group["ai_parking_live_cap_reserve_cap_used"].max()),
            "parking_burst_bridge_cap_used_max": int(group["ai_parking_live_burst_bridge_cap_used"].max()),
            "live_reserve_final_normal_suppressed_count": int(group["ai_live_reserve_final_normal_suppressed"].sum()),
            "live_reserve_trim_skipped_count": int(group["ai_live_reserve_trim_skipped"].sum()),
            "reserve_or_bridge_trimmed_count": int(
                (reserve_or_bridge & group["ai_parking_iom_post_preservation_trim_suppressed_generic_nonrisk"].gt(0)).sum()
            ),
        })
    return pd.DataFrame(rows)


def build_ai_intervention_2l_copymachine_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    group = df[
        df["category"].astype(str).eq("shadow")
        & df["video"].astype(str).eq("copyMachine")
    ].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "shadow",
            "video": "copyMachine",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    guard_active = group["ai_copymachine_shadow_guard_active"].gt(0)
    guard_rejected = group["ai_copymachine_shadow_guard_rejected"].gt(0)
    rescue = group["ai_copymachine_fn_rescue_active"].gt(0)
    rescue_first = group["ai_copymachine_rescue_first_active"].gt(0)
    guard_reasons = group["ai_copymachine_shadow_guard_reason"].replace("", pd.NA).dropna()
    rescue_reasons = group["ai_copymachine_fn_rescue_reason"].replace("", pd.NA).dropna()
    rescue_rejected = group["ai_copymachine_fn_rescue_rejected_reason"].replace("", pd.NA).dropna()
    rescue_first_reasons = group["ai_copymachine_rescue_first_reason"].replace("", pd.NA).dropna()
    rescue_first_rejected = group["ai_copymachine_rescue_first_rejected_reason"].replace("", pd.NA).dropna()
    return pd.DataFrame([{
        "category": "shadow",
        "video": "copyMachine",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "guard_active_frames": int(guard_active.sum()),
        "guard_rejected_frames": int(guard_rejected.sum()),
        "would_have_proposed_before_guard": int(
            group["ai_copymachine_shadow_would_have_proposed_before_guard"].sum()
        ),
        "guard_reclaimed_count_max": int(group["ai_copymachine_shadow_reclaimed_count"].max()),
        "guard_preserved_count_max": int(group["ai_copymachine_shadow_preserved_count"].max()),
        "fn_rescue_frames": int(rescue.sum()),
        "fn_rescue_no_detector_frames": int(group["ai_copymachine_fn_rescue_no_detector"].sum()),
        "fn_rescue_cap_used_max": int(group["ai_copymachine_fn_rescue_cap_used"].max()),
        "rescue_first_candidate_frames": int(group["ai_copymachine_rescue_first_candidate"].sum()),
        "rescue_first_active_frames": int(rescue_first.sum()),
        "rescue_first_protected_before_cap_frames": int(
            group["ai_copymachine_rescue_first_protected_before_cap"].sum()
        ),
        "rescue_first_no_detector_frames": int(group["ai_copymachine_rescue_first_no_detector"].sum()),
        "cap_suppressed_generic_frames": int(group["ai_copymachine_cap_suppressed_generic_only"].sum()),
        "cap_suppressed_generic_count_max": int(group["ai_copymachine_cap_suppressed_generic_count"].max()),
        "rescue_first_final_normal_suppressed_frames": int(
            group["ai_copymachine_rescue_first_final_normal_suppressed"].sum()
        ),
        "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
        "guard_reason_distribution": ";".join(
            f"{k}:{v}" for k, v in guard_reasons.value_counts().sort_index().items()
        ),
        "rescue_reason_distribution": ";".join(
            f"{k}:{v}" for k, v in rescue_reasons.value_counts().sort_index().items()
        ),
        "rescue_rejection_distribution": ";".join(
            f"{k}:{v}" for k, v in rescue_rejected.value_counts().sort_index().items()
        ),
        "rescue_first_reason_distribution": ";".join(
            f"{k}:{v}" for k, v in rescue_first_reasons.value_counts().sort_index().items()
        ),
        "rescue_first_rejection_distribution": ";".join(
            f"{k}:{v}" for k, v in rescue_first_rejected.value_counts().sort_index().items()
        ),
    }])


def build_ai_intervention_2l2_rescue_first_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    proposed = df["ai_intervention_applied"].gt(0)
    detector = df["ai_intervention_detector_requested"].gt(0)
    rows = []
    for category, video in [("shadow", "copyMachine"), ("PTZ", "intermittentPan"), ("PTZ", "continuousPan")]:
        group = df[df["category"].astype(str).eq(category) & df["video"].astype(str).eq(video)].copy()
        if group.empty:
            rows.append({"category": category, "video": video, "present": 0})
            continue
        mask = group.index
        fn = group["Event_State"].astype(str).eq("FN")
        row = {
            "category": category,
            "video": video,
            "present": 1,
            "frames": int(len(group)),
            "proposal_rate": float(proposed.loc[mask].mean()),
            "detector_request_rate": float(detector.loc[mask].mean()),
            "event_fn_count": int(fn.sum()),
            "unprotected_event_fn_count": int((fn & ~proposed.loc[mask]).sum()),
            "normal_frame_proposed_interventions": int((proposed.loc[mask] & group["normal_frame"].gt(0)).sum()),
        }
        if category == "shadow" and video == "copyMachine":
            row.update({
                "rescue_first_candidate_frames": int(group["ai_copymachine_rescue_first_candidate"].sum()),
                "rescue_first_active_frames": int(group["ai_copymachine_rescue_first_active"].sum()),
                "rescue_first_protected_before_cap_frames": int(
                    group["ai_copymachine_rescue_first_protected_before_cap"].sum()
                ),
                "cap_suppressed_generic_frames": int(group["ai_copymachine_cap_suppressed_generic_only"].sum()),
                "rescue_first_final_normal_suppressed_frames": int(
                    group["ai_copymachine_rescue_first_final_normal_suppressed"].sum()
                ),
            })
        if category == "PTZ" and video == "intermittentPan":
            row.update({
                "preserve_2k_rescue_frames": int(
                    group["ai_ptz_intermittent_pan_preserve_2k_rescue_active"].sum()
                ),
                "preserve_2k_rescue_protected_before_later_caps": int(
                    group["ai_ptz_intermittent_pan_preserve_2k_rescue_protected_before_later_caps"].sum()
                ),
            })
        rows.append(row)
    return pd.DataFrame(rows)


def build_ai_intervention_2m_parking_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    parking = (
        df["category"].astype(str).eq("intermittentObjectMotion")
        & df["video"].astype(str).eq("parking")
    )
    group = df[parking].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "intermittentObjectMotion",
            "video": "parking",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    reason_counts = (
        group.loc[group["ai_parking_iom_rescue_reason"].astype(str).ne(""), "ai_parking_iom_rescue_reason"]
        .value_counts()
        .to_dict()
    )
    rejected_counts = (
        group.loc[
            group["ai_parking_iom_rescue_rejected_reason"].astype(str).ne(""),
            "ai_parking_iom_rescue_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    preserve_reason_counts = (
        group.loc[
            group["ai_parking_iom_preserve_fn_risk_reason"].astype(str).ne(""),
            "ai_parking_iom_preserve_fn_risk_reason",
        ]
        .value_counts()
        .to_dict()
    )
    preserve_rejected_counts = (
        group.loc[
            group["ai_parking_iom_preserve_fn_risk_rejected_reason"].astype(str).ne(""),
            "ai_parking_iom_preserve_fn_risk_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    trim_reason_counts = (
        group.loc[
            group["ai_parking_iom_post_preservation_trim_reason"].astype(str).ne(""),
            "ai_parking_iom_post_preservation_trim_reason",
        ]
        .value_counts()
        .to_dict()
    )
    trim_rejected_counts = (
        group.loc[
            group["ai_parking_iom_post_preservation_trim_rejected_reason"].astype(str).ne(""),
            "ai_parking_iom_post_preservation_trim_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    post_lock_trim_reason_counts = (
        group.loc[
            group["ai_parking_post_lock_trim_reason"].astype(str).ne(""),
            "ai_parking_post_lock_trim_reason",
        ]
        .value_counts()
        .to_dict()
    )
    post_lock_trim_rejected_counts = (
        group.loc[
            group["ai_parking_post_lock_trim_rejected_reason"].astype(str).ne(""),
            "ai_parking_post_lock_trim_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    restore_4d3_trim_reason_counts = (
        group.loc[
            group["ai_parking_restore_4d3_trim_reason"].astype(str).ne(""),
            "ai_parking_restore_4d3_trim_reason",
        ]
        .value_counts()
        .to_dict()
    )
    post_lock_trim_4d5_rejected_counts = (
        group.loc[
            group["ai_parking_post_lock_trim_4d5_rejected_reason"].astype(str).ne(""),
            "ai_parking_post_lock_trim_4d5_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    post_lock_trim_4d6_reason_counts = (
        group.loc[
            group["ai_parking_post_lock_trim_4d6_reason"].astype(str).ne(""),
            "ai_parking_post_lock_trim_4d6_reason",
        ]
        .value_counts()
        .to_dict()
    )
    post_lock_trim_4d6_rejected_counts = (
        group.loc[
            group["ai_parking_post_lock_trim_4d6_rejected_reason"].astype(str).ne(""),
            "ai_parking_post_lock_trim_4d6_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    trim_2q3_reason_counts = (
        group.loc[
            group["ai_parking_live_post_trim_2q3_reason"].astype(str).ne(""),
            "ai_parking_live_post_trim_2q3_reason",
        ]
        .value_counts()
        .to_dict()
    )
    trim_2q3_rejected_counts = (
        group.loc[
            group["ai_parking_live_post_trim_2q3_rejected_reason"].astype(str).ne(""),
            "ai_parking_live_post_trim_2q3_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    soft_trim_reason_counts = (
        group.loc[
            group["ai_parking_soft_preserved_trim_reason"].astype(str).ne(""),
            "ai_parking_soft_preserved_trim_reason",
        ]
        .value_counts()
        .to_dict()
    )
    soft_trim_rejected_counts = (
        group.loc[
            group["ai_parking_soft_preserved_trim_rejected_reason"].astype(str).ne(""),
            "ai_parking_soft_preserved_trim_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    trim_suppressed = group["ai_parking_iom_post_preservation_trim_suppressed_generic_nonrisk"].gt(0)
    post_lock_trim_suppressed = group["ai_parking_post_lock_trim_suppressed"].gt(0)
    post_lock_trim_4d5_suppressed = group["ai_parking_post_lock_trim_4d5_suppressed"].gt(0)
    post_lock_trim_4d6_suppressed = group["ai_parking_post_lock_trim_4d6_suppressed"].gt(0)
    trim_2q3_suppressed = group["ai_parking_live_post_trim_2q3_suppressed_generic_nonrisk"].gt(0)
    soft_trim_suppressed = group["ai_parking_soft_preserved_trim_suppressed"].gt(0)
    hard_protected = group["ai_parking_soft_preserved_trim_hard_protected"].gt(0)
    post_lock_hard_protected = group["ai_parking_post_lock_trim_hard_protected"].gt(0)
    protected_by_preserve_or_rescue = (
        group["ai_parking_iom_preserve_fn_risk_active"].gt(0)
        | group["ai_parking_iom_rescue_active"].gt(0)
        | group["ai_parking_carryover_lock_active"].gt(0)
        | group["ai_parking_live_cap_reserve_active"].gt(0)
        | group["ai_parking_live_burst_bridge_active"].gt(0)
    )
    return pd.DataFrame([{
        "category": "intermittentObjectMotion",
        "video": "parking",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
        "rescue_candidate_frames": int(group["ai_parking_iom_rescue_candidate"].sum()),
        "rescue_active_frames": int(group["ai_parking_iom_rescue_active"].sum()),
        "rescue_no_detector_frames": int(group["ai_parking_iom_rescue_no_detector"].sum()),
        "rescue_likely_unprotected_fn_frames": int(group["ai_parking_iom_rescue_likely_unprotected_fn"].sum()),
        "rescue_protected_event_fn_frames": int(
            (group["ai_parking_iom_rescue_active"].gt(0) & fn & proposed).sum()
        ),
        "rescue_false_positive_activation_frames": int(
            (group["ai_parking_iom_rescue_active"].gt(0) & ~fn).sum()
        ),
        "rescue_protected_before_cap_frames": int(
            group["ai_parking_iom_rescue_first_protected_before_cap"].sum()
        ),
        "rescue_cap_used_max": int(group["ai_parking_iom_rescue_cap_used"].max()),
        "preserve_fn_risk_candidate_frames": int(group["ai_parking_iom_preserve_fn_risk_candidate"].sum()),
        "preserve_fn_risk_active_frames": int(group["ai_parking_iom_preserve_fn_risk_active"].sum()),
        "preserve_fn_risk_protected_before_cap_frames": int(
            group["ai_parking_iom_preserve_fn_risk_protected_before_cap"].sum()
        ),
        "preserve_fn_risk_count_max": int(group["ai_parking_iom_preserve_fn_risk_count"].max()),
        "cap_active_frames": int(group["ai_parking_iom_cap_active"].sum()),
        "cap_suppressed_generic_frames": int(group["ai_parking_iom_cap_suppressed_generic_only"].sum()),
        "cap_suppressed_generic_nonrisk_frames": int(
            group["ai_parking_iom_cap_suppressed_generic_nonrisk_only"].sum()
        ),
        "cap_skipped_preserved_fn_risk_frames": int(
            group["ai_parking_iom_cap_skipped_preserved_fn_risk"].sum()
        ),
        "cap_skipped_preserved_fn_risk_count_max": int(
            group["ai_parking_iom_cap_skipped_preserved_fn_risk_count"].max()
        ),
        "cap_soft_budget_exceeded_frames": int(group["ai_parking_iom_cap_soft_budget_exceeded"].sum()),
        "cap_reclaimed_count_max": int(group["ai_parking_iom_cap_reclaimed_count"].max()),
        "cap_preserved_count_max": int(group["ai_parking_iom_cap_preserved_count"].max()),
        "rescue_final_normal_suppressed_frames": int(group["ai_parking_iom_final_normal_suppressed"].sum()),
        "post_preservation_trim_active_frames": int(group["ai_parking_iom_post_preservation_trim_active"].sum()),
        "post_preservation_trim_candidate_frames": int(group["ai_parking_iom_post_preservation_trim_candidate"].sum()),
        "post_preservation_trim_suppressed_generic_nonrisk_frames": int(trim_suppressed.sum()),
        "post_preservation_trim_count_max": int(group["ai_parking_iom_post_preservation_trim_count"].max()),
        "post_preservation_trim_final_rate_max": float(
            group["ai_parking_iom_post_preservation_trim_final_rate"].max()
        ),
        "post_preservation_trim_skipped_preserved_fn_risk_frames": int(
            group["ai_parking_iom_post_preservation_trim_skipped_preserved_fn_risk"].sum()
        ),
        "post_preservation_trim_skipped_rescue_frame_frames": int(
            group["ai_parking_iom_post_preservation_trim_skipped_rescue_frame"].sum()
        ),
        "post_preservation_trim_skipped_likely_unprotected_fn_frames": int(
            group["ai_parking_iom_post_preservation_trim_skipped_likely_unprotected_fn"].sum()
        ),
        "post_preservation_trim_accidentally_trimmed_preserved_or_rescue_frames": int(
            (trim_suppressed & protected_by_preserve_or_rescue).sum()
        ),
        "carryover_lock_active_frames": int(group["ai_parking_carryover_lock_active"].sum()),
        "carryover_lock_protected_event_fn_frames": int(
            (group["ai_parking_carryover_lock_active"].gt(0) & fn & proposed).sum()
        ),
        "carryover_lock_cap_used_max": int(group["ai_parking_carryover_lock_cap_used"].max()),
        "post_lock_trim_active_frames": int(group["ai_parking_post_lock_trim_active"].sum()),
        "post_lock_trim_candidate_frames": int(group["ai_parking_post_lock_trim_candidate"].sum()),
        "post_lock_trim_soft_candidate_frames": int(group["ai_parking_post_lock_trim_soft_candidate"].sum()),
        "post_lock_trim_suppressed_frames": int(post_lock_trim_suppressed.sum()),
        "post_lock_trim_count_max": int(group["ai_parking_post_lock_trim_count"].max()),
        "post_lock_trim_final_rate_max": float(group["ai_parking_post_lock_trim_final_rate"].max()),
        "post_lock_trim_hard_protected_frames": int(post_lock_hard_protected.sum()),
        "post_lock_trim_skipped_hard_protected_frames": int(
            group["ai_parking_post_lock_trim_skipped_hard_protected"].sum()
        ),
        "post_lock_trim_skipped_fn_protected_frames": int(
            group["ai_parking_post_lock_trim_skipped_fn_protected"].sum()
        ),
        "post_lock_trim_skipped_likely_unprotected_fn_frames": int(
            group["ai_parking_post_lock_trim_skipped_likely_unprotected_fn"].sum()
        ),
        "post_lock_trim_accidental_hard_trim_count_max": int(
            group["ai_parking_post_lock_trim_accidental_hard_trim_count"].max()
        ),
        "post_lock_trim_accidental_fn_protected_trim_count_max": int(
            group["ai_parking_post_lock_trim_accidental_fn_protected_trim_count"].max()
        ),
        "post_lock_trim_accidentally_trimmed_hard_frame_count": int(
            (post_lock_trim_suppressed & post_lock_hard_protected).sum()
        ),
        "post_lock_trim_accidentally_trimmed_fn_protected_frame_count": int(
            (
                post_lock_trim_suppressed
                & (
                    group["ai_parking_iom_rescue_protected_event_fn"].gt(0)
                    | group["ai_parking_carryover_lock_protected_event_fn"].gt(0)
                    | (fn & protected_by_preserve_or_rescue)
                )
            ).sum()
        ),
        "post_lock_deduplicate_active_frames": int(
            group["ai_parking_post_lock_deduplicate_active"].sum()
        ),
        "post_lock_deduplicate_count_max": int(
            group["ai_parking_post_lock_deduplicate_count"].max()
        ),
        "restore_4d3_trim_active_frames": int(group["ai_parking_restore_4d3_trim_active"].sum()),
        "restore_4d3_trim_count_max": int(group["ai_parking_restore_4d3_trim_count"].max()),
        "restore_4d3_trim_blocked_by_later_hardprotect_frames": int(
            group["ai_parking_restore_4d3_trim_blocked_by_later_hardprotect"].sum()
        ),
        "post_lock_trim_4d5_active_frames": int(group["ai_parking_post_lock_trim_4d5_active"].sum()),
        "post_lock_trim_4d5_candidate_frames": int(group["ai_parking_post_lock_trim_4d5_candidate"].sum()),
        "post_lock_trim_4d5_soft_candidate_frames": int(
            group["ai_parking_post_lock_trim_4d5_soft_candidate"].sum()
        ),
        "post_lock_trim_4d5_suppressed_frames": int(post_lock_trim_4d5_suppressed.sum()),
        "post_lock_trim_4d5_trim_count_max": int(group["ai_parking_post_lock_trim_4d5_trim_count"].max()),
        "post_lock_trim_4d5_final_rate_max": float(
            group["ai_parking_post_lock_trim_4d5_final_rate"].max()
        ),
        "post_lock_trim_4d5_skipped_fn_protected_frames": int(
            group["ai_parking_post_lock_trim_4d5_skipped_fn_protected"].sum()
        ),
        "post_lock_trim_4d5_skipped_rescue_frame_frames": int(
            group["ai_parking_post_lock_trim_4d5_skipped_rescue_frame"].sum()
        ),
        "post_lock_trim_4d5_skipped_likely_unprotected_fn_frames": int(
            group["ai_parking_post_lock_trim_4d5_skipped_likely_unprotected_fn"].sum()
        ),
        "post_lock_trim_4d5_accidental_fn_protected_trim_count_max": int(
            group["ai_parking_post_lock_trim_4d5_accidental_fn_protected_trim_count"].max()
        ),
        "post_lock_trim_4d5_accidental_rescue_trim_count_max": int(
            group["ai_parking_post_lock_trim_4d5_accidental_rescue_trim_count"].max()
        ),
        "post_lock_trim_4d5_accidentally_trimmed_fn_protected_frame_count": int(
            (
                post_lock_trim_4d5_suppressed
                & (
                    group["ai_parking_iom_rescue_protected_event_fn"].gt(0)
                    | group["ai_parking_carryover_lock_protected_event_fn"].gt(0)
                    | (fn & protected_by_preserve_or_rescue)
                )
            ).sum()
        ),
        "post_lock_trim_4d5_accidentally_trimmed_rescue_frame_count": int(
            (
                post_lock_trim_4d5_suppressed
                & (
                    group["ai_parking_iom_rescue_active"].gt(0)
                    | group["ai_parking_carryover_lock_active"].gt(0)
                    | group["ai_parking_live_cap_reserve_active"].gt(0)
                    | group["ai_parking_live_burst_bridge_active"].gt(0)
                )
            ).sum()
        ),
        "post_lock_trim_4d6_active_frames": int(group["ai_parking_post_lock_trim_4d6_active"].sum()),
        "post_lock_trim_4d6_candidate_frames": int(group["ai_parking_post_lock_trim_4d6_candidate"].sum()),
        "post_lock_trim_4d6_suppressed_frames": int(post_lock_trim_4d6_suppressed.sum()),
        "post_lock_trim_4d6_trim_count_max": int(group["ai_parking_post_lock_trim_4d6_trim_count"].max()),
        "post_lock_trim_4d6_final_rate_max": float(
            group["ai_parking_post_lock_trim_4d6_final_rate"].max()
        ),
        "post_lock_trim_4d6_accidental_fn_protected_trim_count_max": int(
            group["ai_parking_post_lock_trim_4d6_accidental_fn_protected_trim_count"].max()
        ),
        "post_lock_trim_4d6_accidental_rescue_trim_count_max": int(
            group["ai_parking_post_lock_trim_4d6_accidental_rescue_trim_count"].max()
        ),
        "post_lock_trim_4d6_accidentally_trimmed_fn_protected_frame_count": int(
            (
                post_lock_trim_4d6_suppressed
                & (
                    group["ai_parking_iom_rescue_protected_event_fn"].gt(0)
                    | group["ai_parking_carryover_lock_protected_event_fn"].gt(0)
                    | (fn & protected_by_preserve_or_rescue)
                )
            ).sum()
        ),
        "post_lock_trim_4d6_accidentally_trimmed_rescue_frame_count": int(
            (
                post_lock_trim_4d6_suppressed
                & (
                    group["ai_parking_iom_rescue_active"].gt(0)
                    | group["ai_parking_carryover_lock_active"].gt(0)
                    | group["ai_parking_live_cap_reserve_active"].gt(0)
                    | group["ai_parking_live_burst_bridge_active"].gt(0)
                )
            ).sum()
        ),
        "live_post_trim_2q3_active_frames": int(group["ai_parking_live_post_trim_2q3_active"].sum()),
        "live_post_trim_2q3_candidate_frames": int(group["ai_parking_live_post_trim_2q3_candidate"].sum()),
        "live_post_trim_2q3_suppressed_generic_nonrisk_frames": int(trim_2q3_suppressed.sum()),
        "live_post_trim_2q3_skipped_rescue_frame_frames": int(
            group["ai_parking_live_post_trim_2q3_skipped_rescue_frame"].sum()
        ),
        "live_post_trim_2q3_skipped_live_reserve_frame_frames": int(
            group["ai_parking_live_post_trim_2q3_skipped_live_reserve_frame"].sum()
        ),
        "live_post_trim_2q3_skipped_preserved_fn_risk_frames": int(
            group["ai_parking_live_post_trim_2q3_skipped_preserved_fn_risk"].sum()
        ),
        "live_post_trim_2q3_skipped_likely_unprotected_fn_frames": int(
            group["ai_parking_live_post_trim_2q3_skipped_likely_unprotected_fn"].sum()
        ),
        "live_post_trim_2q3_trim_count_max": int(group["ai_parking_live_post_trim_2q3_trim_count"].max()),
        "live_post_trim_2q3_final_rate_max": float(
            group["ai_parking_live_post_trim_2q3_final_rate"].max()
        ),
        "live_post_trim_2q3_accidental_protected_trim_count_max": int(
            group["ai_parking_live_post_trim_2q3_accidental_protected_trim_count"].max()
        ),
        "live_post_trim_2q3_accidentally_trimmed_protected_frame_count": int(
            (trim_2q3_suppressed & protected_by_preserve_or_rescue).sum()
        ),
        "soft_preserved_trim_active_frames": int(group["ai_parking_soft_preserved_trim_active"].sum()),
        "soft_preserved_trim_candidate_frames": int(group["ai_parking_soft_preserved_trim_candidate"].sum()),
        "soft_preserved_trim_hard_protected_frames": int(hard_protected.sum()),
        "soft_preserved_trim_soft_preserved_frames": int(
            group["ai_parking_soft_preserved_trim_soft_preserved"].sum()
        ),
        "soft_preserved_trim_suppressed_frames": int(soft_trim_suppressed.sum()),
        "soft_preserved_trim_skipped_hard_protected_frames": int(
            group["ai_parking_soft_preserved_trim_skipped_hard_protected"].sum()
        ),
        "soft_preserved_trim_skipped_rescue_frame_frames": int(
            group["ai_parking_soft_preserved_trim_skipped_rescue_frame"].sum()
        ),
        "soft_preserved_trim_skipped_live_reserve_frame_frames": int(
            group["ai_parking_soft_preserved_trim_skipped_live_reserve_frame"].sum()
        ),
        "soft_preserved_trim_skipped_likely_unprotected_fn_frames": int(
            group["ai_parking_soft_preserved_trim_skipped_likely_unprotected_fn"].sum()
        ),
        "soft_preserved_trim_trim_count_max": int(
            group["ai_parking_soft_preserved_trim_trim_count"].max()
        ),
        "soft_preserved_trim_final_rate_max": float(
            group["ai_parking_soft_preserved_trim_final_rate"].max()
        ),
        "soft_preserved_trim_accidental_hard_protected_trim_count_max": int(
            group["ai_parking_soft_preserved_trim_accidental_hard_protected_trim_count"].max()
        ),
        "soft_preserved_trim_accidentally_trimmed_hard_protected_frame_count": int(
            (soft_trim_suppressed & hard_protected).sum()
        ),
        "rescue_reason_counts": json.dumps(reason_counts, sort_keys=True),
        "rescue_rejected_reason_counts": json.dumps(rejected_counts, sort_keys=True),
        "preserve_fn_risk_reason_counts": json.dumps(preserve_reason_counts, sort_keys=True),
        "preserve_fn_risk_rejected_reason_counts": json.dumps(preserve_rejected_counts, sort_keys=True),
        "post_preservation_trim_reason_counts": json.dumps(trim_reason_counts, sort_keys=True),
        "post_preservation_trim_rejected_reason_counts": json.dumps(trim_rejected_counts, sort_keys=True),
        "post_lock_trim_reason_counts": json.dumps(post_lock_trim_reason_counts, sort_keys=True),
        "post_lock_trim_rejected_reason_counts": json.dumps(
            post_lock_trim_rejected_counts,
            sort_keys=True,
        ),
        "restore_4d3_trim_reason_counts": json.dumps(
            restore_4d3_trim_reason_counts,
            sort_keys=True,
        ),
        "post_lock_trim_4d5_rejected_reason_counts": json.dumps(
            post_lock_trim_4d5_rejected_counts,
            sort_keys=True,
        ),
        "post_lock_trim_4d6_reason_counts": json.dumps(
            post_lock_trim_4d6_reason_counts,
            sort_keys=True,
        ),
        "post_lock_trim_4d6_rejected_reason_counts": json.dumps(
            post_lock_trim_4d6_rejected_counts,
            sort_keys=True,
        ),
        "live_post_trim_2q3_reason_counts": json.dumps(trim_2q3_reason_counts, sort_keys=True),
        "live_post_trim_2q3_rejected_reason_counts": json.dumps(trim_2q3_rejected_counts, sort_keys=True),
        "soft_preserved_trim_reason_counts": json.dumps(soft_trim_reason_counts, sort_keys=True),
        "soft_preserved_trim_rejected_reason_counts": json.dumps(soft_trim_rejected_counts, sort_keys=True),
    }])


def build_ai_intervention_2m2_parking_summary(root):
    return build_ai_intervention_2m_parking_summary(root)


def build_ai_intervention_2m3_parking_summary(root):
    return build_ai_intervention_2m_parking_summary(root)


def build_ai_intervention_2q3_parking_live_trim_summary(root):
    return build_ai_intervention_2m_parking_summary(root)


def build_ai_intervention_2q4_parking_soft_trim_summary(root):
    return build_ai_intervention_2m_parking_summary(root)


def build_ai_intervention_2n_turbulence2_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("turbulence")
        & df["video"].astype(str).eq("turbulence2")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "turbulence",
            "video": "turbulence2",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    rescue = group["ai_turbulence2_fn_rescue_active"].gt(0)
    carryover = group["ai_turbulence2_carryover_reserve_active"].gt(0)
    guard_suppressed = group["ai_turbulence2_pressure_guard_suppressed_generic_nonrisk"].gt(0)
    protected_before_guard = group["ai_turbulence2_rescue_protected_before_guard"].gt(0)
    guard_reason_counts = (
        group.loc[
            group["ai_turbulence2_pressure_guard_reason"].astype(str).ne(""),
            "ai_turbulence2_pressure_guard_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rescue_reason_counts = (
        group.loc[
            group["ai_turbulence2_fn_rescue_reason"].astype(str).ne(""),
            "ai_turbulence2_fn_rescue_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rescue_rejected_counts = (
        group.loc[
            group["ai_turbulence2_fn_rescue_rejected_reason"].astype(str).ne(""),
            "ai_turbulence2_fn_rescue_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    carryover_reason_counts = (
        group.loc[
            group["ai_turbulence2_carryover_reserve_reason"].astype(str).ne(""),
            "ai_turbulence2_carryover_reserve_reason",
        ]
        .value_counts()
        .to_dict()
    )
    carryover_rejected_counts = (
        group.loc[
            group["ai_turbulence2_carryover_reserve_rejected_reason"].astype(str).ne(""),
            "ai_turbulence2_carryover_reserve_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    frame_status = {}
    for frame in [950, 975, 985]:
        rows = group[group["raw_frame_id"].astype(str).eq(str(frame))]
        if rows.empty:
            frame_status[str(frame)] = {"present": 0}
            continue
        row = rows.iloc[0]
        frame_status[str(frame)] = {
            "present": 1,
            "event_state": str(row.get("Event_State", "")),
            "action": str(row.get("action_label", "")),
            "final_action": str(row.get("ai_intervention_final_action", "")),
            "proposed": int(float(row.get("ai_intervention_applied", 0) or 0) > 0),
            "detector_requested": int(float(row.get("ai_intervention_detector_requested", 0) or 0) > 0),
            "rescue_rejected_reason": str(row.get("ai_turbulence2_fn_rescue_rejected_reason", "")),
            "carryover_active": int(float(row.get("ai_turbulence2_carryover_reserve_active", 0) or 0) > 0),
            "carryover_rejected_reason": str(
                row.get("ai_turbulence2_carryover_reserve_rejected_reason", "")
            ),
        }
    return pd.DataFrame([{
        "category": "turbulence",
        "video": "turbulence2",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
        "rescue_candidate_frames": int(group["ai_turbulence2_fn_rescue_candidate"].sum()),
        "rescue_active_frames": int(rescue.sum()),
        "rescue_no_detector_frames": int(group["ai_turbulence2_fn_rescue_no_detector"].sum()),
        "rescue_protected_event_fn_frames": int((rescue & fn & proposed).sum()),
        "rescue_final_normal_suppressed_frames": int(
            group["ai_turbulence2_fn_rescue_final_normal_suppressed"].sum()
        ),
        "rescue_protected_before_guard_frames": int(protected_before_guard.sum()),
        "carryover_reserve_candidate_frames": int(
            group["ai_turbulence2_carryover_reserve_candidate"].sum()
        ),
        "carryover_reserve_active_frames": int(carryover.sum()),
        "carryover_reserve_no_detector_frames": int(
            group["ai_turbulence2_carryover_reserve_no_detector"].sum()
        ),
        "carryover_reserve_cap_used_max": int(
            group["ai_turbulence2_carryover_reserve_cap_used"].max()
        ),
        "carryover_reserve_protected_event_fn_frames": int((carryover & fn & proposed).sum()),
        "carryover_reserve_final_normal_suppressed_frames": int(
            group["ai_turbulence2_carryover_reserve_final_normal_suppressed"].sum()
        ),
        "pressure_guard_active_frames": int(group["ai_turbulence2_pressure_guard_active"].sum()),
        "pressure_guard_rejected_frames": int(group["ai_turbulence2_pressure_guard_rejected"].sum()),
        "pressure_guard_suppressed_generic_nonrisk_frames": int(guard_suppressed.sum()),
        "pressure_guard_suppressed_detector_refresh_frames": int(
            group["ai_turbulence2_pressure_guard_suppressed_detector_refresh"].sum()
        ),
        "pressure_guard_reclaimed_count_max": int(
            group["ai_turbulence2_pressure_guard_reclaimed_count"].max()
        ),
        "pressure_guard_preserved_count_max": int(
            group["ai_turbulence2_pressure_guard_preserved_count"].max()
        ),
        "protected_rescue_frames_accidentally_suppressed_count": int(
            (guard_suppressed & protected_before_guard).sum()
        ),
        "pressure_guard_reason_counts": json.dumps(guard_reason_counts, sort_keys=True),
        "rescue_reason_counts": json.dumps(rescue_reason_counts, sort_keys=True),
        "rescue_rejected_reason_counts": json.dumps(rescue_rejected_counts, sort_keys=True),
        "carryover_reserve_reason_counts": json.dumps(carryover_reason_counts, sort_keys=True),
        "carryover_reserve_rejected_reason_counts": json.dumps(carryover_rejected_counts, sort_keys=True),
        "frames_950_975_985_status": json.dumps(frame_status, sort_keys=True),
    }])


def build_ai_intervention_2q2_turbulence_carryover_summary(root):
    return build_ai_intervention_2n_turbulence2_summary(root)


def build_ai_intervention_4b_lakeside_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("thermal")
        & df["video"].astype(str).eq("lakeSide")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "thermal",
            "video": "lakeSide",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    rescue = group["ai_thermal_lakeside_fn_rescue_active"].gt(0)
    early = group["ai_thermal_lakeside_early_memory_rescue_active"].gt(0)
    rescue_candidate = group["ai_thermal_lakeside_fn_rescue_candidate"].gt(0)
    trim_candidate = group["ai_thermal_lakeside_post_rescue_trim_candidate"].gt(0)
    trim_suppressed = group["ai_thermal_lakeside_post_rescue_trim_suppressed"].gt(0)
    trim_hard = group["ai_thermal_lakeside_post_rescue_trim_hard_protected"].gt(0)
    fg_loss_soft_candidate = group["ai_thermal_lakeside_fg_loss_soft_trim_candidate"].gt(0)
    fg_loss_soft_suppressed = group["ai_thermal_lakeside_fg_loss_soft_trim_suppressed"].gt(0)
    detector_retighten = group["ai_thermal_lakeside_detector_retighten_active"].gt(0)
    highscore_soft_candidate = group["ai_thermal_lakeside_highscore_soft_candidate"].gt(0)
    highscore_trim_candidate = group["ai_thermal_lakeside_highscore_soft_trim_candidate"].gt(0)
    highscore_trim_suppressed = group["ai_thermal_lakeside_highscore_soft_trim_suppressed"].gt(0)
    drift_recap_active = group["ai_thermal_lakeside_drift_recap_active"].gt(0)
    drift_recap_suppressed = group["ai_thermal_lakeside_drift_recap_suppressed"].gt(0)
    carryover_lock = group["ai_thermal_lakeside_carryover_lock_active"].gt(0)
    cap_refine = group["ai_thermal_lakeside_rescue_cap_refine_active"].gt(0)
    cap_candidate = (
        rescue_candidate
        | group["ai_thermal_lakeside_fn_rescue_rejected_reason"].astype(str).str.contains(
            "cap", case=False, na=False
        )
    )
    rescue_reason_counts = (
        group.loc[
            group["ai_thermal_lakeside_fn_rescue_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_fn_rescue_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rescue_rejected_counts = (
        group.loc[
            group["ai_thermal_lakeside_fn_rescue_rejected_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_fn_rescue_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    early_reason_counts = (
        group.loc[
            group["ai_thermal_lakeside_early_memory_rescue_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_early_memory_rescue_reason",
        ]
        .value_counts()
        .to_dict()
    )
    early_rejected_counts = (
        group.loc[
            group["ai_thermal_lakeside_early_memory_rescue_rejected_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_early_memory_rescue_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    trim_reason_counts = (
        group.loc[
            group["ai_thermal_lakeside_post_rescue_trim_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_post_rescue_trim_reason",
        ]
        .value_counts()
        .to_dict()
    )
    trim_rejected_counts = (
        group.loc[
            group["ai_thermal_lakeside_post_rescue_trim_rejected_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_post_rescue_trim_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    cap_refine_reason_counts = (
        group.loc[
            group["ai_thermal_lakeside_rescue_cap_refine_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_rescue_cap_refine_reason",
        ]
        .value_counts()
        .to_dict()
    )
    hard_refine_reason_counts = (
        group.loc[
            group["ai_thermal_lakeside_hard_protect_refine_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_hard_protect_refine_reason",
        ]
        .value_counts()
        .to_dict()
    )
    detector_retighten_reason_counts = (
        group.loc[
            group["ai_thermal_lakeside_detector_retighten_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_detector_retighten_reason",
        ]
        .value_counts()
        .to_dict()
    )
    highscore_soften_reason_counts = (
        group.loc[
            group["ai_thermal_lakeside_highscore_soften_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_highscore_soften_reason",
        ]
        .value_counts()
        .to_dict()
    )
    highscore_soften_rejected_counts = (
        group.loc[
            group["ai_thermal_lakeside_highscore_soften_rejected_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_highscore_soften_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    drift_recap_reason_counts = (
        group.loc[
            group["ai_thermal_lakeside_drift_recap_reason"].astype(str).ne(""),
            "ai_thermal_lakeside_drift_recap_reason",
        ]
        .value_counts()
        .to_dict()
    )
    return pd.DataFrame([{
        "category": "thermal",
        "video": "lakeSide",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
        "cap_exhausted_rescue_candidate_frames": int(cap_candidate.sum()),
        "rescue_candidate_frames": int(rescue_candidate.sum()),
        "rescue_active_frames": int(rescue.sum()),
        "rescue_no_detector_frames": int(group["ai_thermal_lakeside_fn_rescue_no_detector"].sum()),
        "rescue_cap_used_max": int(group["ai_thermal_lakeside_fn_rescue_cap_used"].max()),
        "rescue_protected_event_fn_frames": int((rescue & fn & proposed).sum()),
        "rescue_final_normal_suppressed_frames": int(
            group["ai_thermal_lakeside_fn_rescue_final_normal_suppressed"].sum()
        ),
        "early_memory_candidate_frames": int(
            group["ai_thermal_lakeside_early_memory_rescue_candidate"].sum()
        ),
        "early_memory_active_frames": int(early.sum()),
        "early_memory_protected_event_fn_frames": int((early & fn & proposed).sum()),
        "newly_protected_event_fn_frames": int(((rescue | early) & fn & proposed).sum()),
        "post_rescue_trim_candidate_frames": int(trim_candidate.sum()),
        "post_rescue_trim_soft_candidate_frames": int(
            group["ai_thermal_lakeside_post_rescue_trim_soft_candidate"].sum()
        ),
        "post_rescue_trim_count": int(group["ai_thermal_lakeside_post_rescue_trim_count"].max()),
        "post_rescue_trim_suppressed_frames": int(trim_suppressed.sum()),
        "post_rescue_trim_hard_protected_frames": int(trim_hard.sum()),
        "hard_protected_count": int(trim_hard.sum()),
        "hard_protect_refine_active_frames": int(
            group["ai_thermal_lakeside_hard_protect_refine_active"].sum()
        ),
        "foreground_loss_only_soft_candidate_frames": int(
            group["ai_thermal_lakeside_fg_loss_only_soft_candidate"].sum()
        ),
        "fg_loss_soft_trim_candidate_frames": int(fg_loss_soft_candidate.sum()),
        "fg_loss_soft_trim_suppressed_frames": int(fg_loss_soft_suppressed.sum()),
        "fg_loss_soft_trim_count": int(
            group["ai_thermal_lakeside_fg_loss_soft_trim_count"].max()
        ),
        "fg_loss_soft_trim_skipped_hard_protected_frames": int(
            group["ai_thermal_lakeside_fg_loss_soft_trim_skipped_hard_protected"].sum()
        ),
        "fg_loss_soft_trim_skipped_likely_unprotected_fn_frames": int(
            group["ai_thermal_lakeside_fg_loss_soft_trim_skipped_likely_unprotected_fn"].sum()
        ),
        "fg_loss_soft_trim_skipped_rescue_frame_frames": int(
            group["ai_thermal_lakeside_fg_loss_soft_trim_skipped_rescue_frame"].sum()
        ),
        "fg_loss_soft_trim_accidental_hard_protected_trim_count": int(
            group["ai_thermal_lakeside_fg_loss_soft_trim_accidental_hard_protected_trim_count"].max()
        ),
        "fg_loss_soft_trim_accidental_rescue_protected_trim_count": int(
            (fg_loss_soft_suppressed & (rescue | early)).sum()
        ),
        "detector_retighten_active_frames": int(detector_retighten.sum()),
        "detector_retighten_count": int(group["ai_thermal_lakeside_detector_retighten_active"].sum()),
        "highscore_soften_active_frames": int(
            group["ai_thermal_lakeside_highscore_soften_active"].sum()
        ),
        "highscore_soft_candidate_frames": int(highscore_soft_candidate.sum()),
        "highscore_soft_trim_candidate_frames": int(highscore_trim_candidate.sum()),
        "highscore_soft_trim_suppressed_frames": int(highscore_trim_suppressed.sum()),
        "highscore_soft_trim_count": int(
            group["ai_thermal_lakeside_highscore_soft_trim_count"].max()
        ),
        "highscore_soft_trim_skipped_hard_protected_frames": int(
            group["ai_thermal_lakeside_highscore_soft_trim_skipped_hard_protected"].sum()
        ),
        "highscore_soft_trim_skipped_rescue_frame_frames": int(
            group["ai_thermal_lakeside_highscore_soft_trim_skipped_rescue_frame"].sum()
        ),
        "highscore_soft_trim_skipped_likely_unprotected_fn_frames": int(
            group["ai_thermal_lakeside_highscore_soft_trim_skipped_likely_unprotected_fn"].sum()
        ),
        "highscore_soft_trim_accidental_hard_protected_trim_count": int(
            group["ai_thermal_lakeside_highscore_soft_trim_accidental_hard_protected_trim_count"].max()
        ),
        "highscore_soft_trim_accidental_rescue_trim_count": int(
            group["ai_thermal_lakeside_highscore_soft_trim_accidental_rescue_trim_count"].max()
        ),
        "drift_recap_active_frames": int(drift_recap_active.sum()),
        "drift_recap_suppressed_frames": int(drift_recap_suppressed.sum()),
        "drift_recap_count": int(group["ai_thermal_lakeside_drift_recap_suppressed"].sum()),
        "drift_recap_final_rate_max": float(
            group["ai_thermal_lakeside_drift_recap_final_rate"].max()
        ),
        "drift_recap_accidental_hard_trim_count": int(
            group["ai_thermal_lakeside_drift_recap_accidental_hard_trim_count"].max()
        ),
        "carryover_lock_active_frames": int(carryover_lock.sum()),
        "carryover_lock_trim_count": int(group["ai_thermal_lakeside_carryover_lock_trim_count"].max()),
        "total_trim_count": int(group["ai_thermal_lakeside_post_rescue_trim_count"].max()),
        "total_accidental_hard_protected_trim_count": int(
            group["ai_thermal_lakeside_post_rescue_trim_accidental_hard_protected_trim_count"].max()
            + group["ai_thermal_lakeside_highscore_soft_trim_accidental_hard_protected_trim_count"].max()
            + group["ai_thermal_lakeside_drift_recap_accidental_hard_trim_count"].max()
        ),
        "total_accidental_rescue_trim_count": int(
            group["ai_thermal_lakeside_highscore_soft_trim_accidental_rescue_trim_count"].max()
        ),
        "post_rescue_trim_skipped_hard_protected_frames": int(
            group["ai_thermal_lakeside_post_rescue_trim_skipped_hard_protected"].sum()
        ),
        "post_rescue_trim_skipped_fn_protected_frames": int(
            group["ai_thermal_lakeside_post_rescue_trim_skipped_fn_protected"].sum()
        ),
        "post_rescue_trim_accidental_hard_protected_trim_count": int(
            group["ai_thermal_lakeside_post_rescue_trim_accidental_hard_protected_trim_count"].max()
        ),
        "post_rescue_trim_final_rate_max": float(
            group["ai_thermal_lakeside_post_rescue_trim_final_rate"].max()
        ),
        "final_proposal_rate": float(proposed.mean()),
        "rescue_cap_refine_active_frames": int(cap_refine.sum()),
        "final_normal_suppressed_frames": int(
            group["ai_thermal_lakeside_fn_rescue_final_normal_suppressed"].sum()
        ),
        "rescue_reason_counts": json.dumps(rescue_reason_counts, sort_keys=True),
        "rescue_rejected_reason_counts": json.dumps(rescue_rejected_counts, sort_keys=True),
        "early_memory_reason_counts": json.dumps(early_reason_counts, sort_keys=True),
        "early_memory_rejected_reason_counts": json.dumps(early_rejected_counts, sort_keys=True),
        "post_rescue_trim_reason_counts": json.dumps(trim_reason_counts, sort_keys=True),
        "post_rescue_trim_rejected_reason_counts": json.dumps(trim_rejected_counts, sort_keys=True),
        "rescue_cap_refine_reason_counts": json.dumps(cap_refine_reason_counts, sort_keys=True),
        "hard_protect_refine_reason_counts": json.dumps(hard_refine_reason_counts, sort_keys=True),
        "detector_retighten_reason_counts": json.dumps(detector_retighten_reason_counts, sort_keys=True),
        "highscore_soften_reason_counts": json.dumps(highscore_soften_reason_counts, sort_keys=True),
        "highscore_soften_rejected_reason_counts": json.dumps(highscore_soften_rejected_counts, sort_keys=True),
        "drift_recap_reason_counts": json.dumps(drift_recap_reason_counts, sort_keys=True),
    }])


def build_ai_intervention_4c_sofa_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("intermittentObjectMotion")
        & df["video"].astype(str).eq("sofa")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "intermittentObjectMotion",
            "video": "sofa",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    rescue = group["ai_sofa_iom_rescue_active"].gt(0)
    carryover_lock = group["ai_sofa_iom_carryover_lock_active"].gt(0)
    guard_suppressed = group["ai_sofa_iom_proposal_guard_suppressed_generic_nonrisk"].gt(0)
    rescue_reason_counts = (
        group.loc[
            group["ai_sofa_iom_rescue_reason"].astype(str).ne(""),
            "ai_sofa_iom_rescue_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rescue_rejected_counts = (
        group.loc[
            group["ai_sofa_iom_rescue_rejected_reason"].astype(str).ne(""),
            "ai_sofa_iom_rescue_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    return pd.DataFrame([{
        "category": "intermittentObjectMotion",
        "video": "sofa",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
        "rescue_candidate_frames": int(group["ai_sofa_iom_rescue_candidate"].sum()),
        "rescue_active_frames": int(rescue.sum()),
        "carryover_lock_active_frames": int(carryover_lock.sum()),
        "carryover_lock_no_detector_frames": int(group["ai_sofa_iom_carryover_lock_no_detector"].sum()),
        "carryover_lock_cap_used_max": int(group["ai_sofa_iom_carryover_lock_cap_used"].max()),
        "carryover_lock_protected_event_fn_frames": int((carryover_lock & fn & proposed).sum()),
        "rescue_no_detector_frames": int(group["ai_sofa_iom_rescue_no_detector"].sum()),
        "rescue_cap_used_max": int(group["ai_sofa_iom_rescue_cap_used"].max()),
        "rescue_protected_event_fn_frames": int((rescue & fn & proposed).sum()),
        "rescue_first_protected_before_cap_frames": int(
            group["ai_sofa_iom_rescue_first_protected_before_cap"].sum()
        ),
        "rescue_final_normal_suppressed_frames": int(
            group["ai_sofa_iom_rescue_final_normal_suppressed"].sum()
            + group["ai_sofa_iom_carryover_lock_final_normal_suppressed"].sum()
        ),
        "proposal_guard_active_frames": int(group["ai_sofa_iom_proposal_guard_active"].sum()),
        "proposal_guard_suppressed_generic_nonrisk_frames": int(guard_suppressed.sum()),
        "proposal_guard_suppressed_count_max": int(
            group["ai_sofa_iom_proposal_guard_suppressed_count"].max()
        ),
        "proposal_guard_skipped_rescue_frame_frames": int(
            group["ai_sofa_iom_proposal_guard_skipped_rescue_frame"].sum()
        ),
        "proposal_guard_skipped_rescue_count_max": int(
            group["ai_sofa_iom_proposal_guard_skipped_rescue_count"].max()
        ),
        "proposal_guard_final_rate_max": float(
            group["ai_sofa_iom_proposal_guard_final_rate"].max()
        ),
        "rescue_reason_counts": json.dumps(rescue_reason_counts, sort_keys=True),
        "rescue_rejected_reason_counts": json.dumps(rescue_rejected_counts, sort_keys=True),
    }])


def build_ai_intervention_4d_snowfall_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("badWeather")
        & df["video"].astype(str).eq("snowFall")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "badWeather",
            "video": "snowFall",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    rescue = group["ai_snowfall_weather_rescue_active"].gt(0)
    actual_fn_rescue = group["ai_snowfall_actual_fn_rescue_active"].gt(0)
    any_rescue = rescue | actual_fn_rescue
    guard_suppressed = group["ai_snowfall_weather_proposal_guard_suppressed_generic_nonrisk"].gt(0)
    rescue_reason_counts = (
        group.loc[
            group["ai_snowfall_weather_rescue_reason"].astype(str).ne(""),
            "ai_snowfall_weather_rescue_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rescue_rejected_counts = (
        group.loc[
            group["ai_snowfall_weather_rescue_rejected_reason"].astype(str).ne(""),
            "ai_snowfall_weather_rescue_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    localized_rejected_counts = (
        group.loc[
            group["ai_snowfall_weather_localized_guard_rejected_reason"].astype(str).ne(""),
            "ai_snowfall_weather_localized_guard_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    actual_fn_rescue_reason_counts = (
        group.loc[
            group["ai_snowfall_actual_fn_rescue_reason"].astype(str).ne(""),
            "ai_snowfall_actual_fn_rescue_reason",
        ]
        .value_counts()
        .to_dict()
    )
    actual_fn_rescue_rejected_counts = (
        group.loc[
            group["ai_snowfall_actual_fn_rescue_rejected_reason"].astype(str).ne(""),
            "ai_snowfall_actual_fn_rescue_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    return pd.DataFrame([{
        "category": "badWeather",
        "video": "snowFall",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
        "rescue_candidate_frames": int(group["ai_snowfall_weather_rescue_candidate"].sum()),
        "rescue_active_frames": int(any_rescue.sum()),
        "rescue_no_detector_frames": int(
            group["ai_snowfall_weather_rescue_no_detector"].sum()
            + group["ai_snowfall_actual_fn_rescue_no_detector"].sum()
        ),
        "rescue_cap_used_max": int(group["ai_snowfall_weather_rescue_cap_used"].max()),
        "rescue_protected_event_fn_frames": int((any_rescue & fn & proposed).sum()),
        "rescue_final_normal_suppressed_frames": int(
            group["ai_snowfall_weather_rescue_final_normal_suppressed"].sum()
            + group["ai_snowfall_actual_fn_rescue_final_normal_suppressed"].sum()
        ),
        "actual_fn_rescue_candidate_frames": int(
            group["ai_snowfall_actual_fn_rescue_candidate"].sum()
        ),
        "actual_fn_rescue_active_frames": int(actual_fn_rescue.sum()),
        "actual_fn_rescue_no_detector_frames": int(
            group["ai_snowfall_actual_fn_rescue_no_detector"].sum()
        ),
        "actual_fn_rescue_cap_used_max": int(
            group["ai_snowfall_actual_fn_rescue_cap_used"].max()
        ),
        "actual_fn_rescue_protected_event_fn_frames": int((actual_fn_rescue & fn & proposed).sum()),
        "actual_fn_rescue_final_normal_suppressed_frames": int(
            group["ai_snowfall_actual_fn_rescue_final_normal_suppressed"].sum()
        ),
        "budget_available_but_actual_fn_rescued_frames": int(
            group["ai_snowfall_weather_budget_available_but_actual_fn_rescued"].sum()
        ),
        "actual_fn_cap_increase_active_frames": int(
            group["ai_snowfall_actual_fn_cap_increase_active"].sum()
        ),
        "actual_fn_cap_exhausted_after_d3_frames": int(
            group["ai_snowfall_actual_fn_rescue_cap_exhausted_after_d3"].sum()
        ),
        "mask_quality_row_skipped_frames": int(
            group["ai_snowfall_mask_quality_row_skipped"].sum()
        ),
        "localized_guard_active_frames": int(group["ai_snowfall_weather_localized_guard_active"].sum()),
        "proposal_guard_active_frames": int(group["ai_snowfall_weather_proposal_guard_active"].sum()),
        "proposal_guard_suppressed_generic_nonrisk_frames": int(guard_suppressed.sum()),
        "proposal_guard_suppressed_count_max": int(
            group["ai_snowfall_weather_proposal_guard_suppressed_count"].max()
        ),
        "proposal_guard_skipped_rescue_frame_frames": int(
            group["ai_snowfall_weather_proposal_guard_skipped_rescue_frame"].sum()
        ),
        "proposal_guard_skipped_rescue_count_max": int(
            group["ai_snowfall_weather_proposal_guard_skipped_rescue_count"].max()
        ),
        "proposal_guard_final_rate_max": float(
            group["ai_snowfall_weather_proposal_guard_final_rate"].max()
        ),
        "possible_mask_quality_rows": int(
            group["ai_snowfall_weather_possible_mask_quality_exposure"].sum()
        ),
        "rescue_reason_counts": json.dumps(rescue_reason_counts, sort_keys=True),
        "rescue_rejected_reason_counts": json.dumps(rescue_rejected_counts, sort_keys=True),
        "localized_guard_rejected_reason_counts": json.dumps(localized_rejected_counts, sort_keys=True),
        "actual_fn_rescue_reason_counts": json.dumps(actual_fn_rescue_reason_counts, sort_keys=True),
        "actual_fn_rescue_rejected_reason_counts": json.dumps(
            actual_fn_rescue_rejected_counts,
            sort_keys=True,
        ),
    }])


def build_ai_intervention_4d3_carryover_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    targets = [
        ("thermal", "lakeSide"),
        ("intermittentObjectMotion", "sofa"),
        ("badWeather", "snowFall"),
        ("lowFramerate", "port_0_17fps"),
        ("intermittentObjectMotion", "parking"),
        ("shadow", "copyMachine"),
        ("turbulence", "turbulence2"),
        ("lowFramerate", "tunnelExit_0_35fps"),
        ("shadow", "cubicle"),
        ("PTZ", "continuousPan"),
        ("PTZ", "intermittentPan"),
        ("dynamicBackground", "fountain01"),
        ("dynamicBackground", "fountain02"),
        ("nightVideos", "bridgeEntry"),
    ]
    rows = []
    for category, video in targets:
        mask = df["category"].astype(str).eq(category) & df["video"].astype(str).eq(video)
        group = df[mask].copy()
        if group.empty:
            rows.append({"category": category, "video": video, "present": 0})
            continue
        proposed = group["ai_intervention_applied"].gt(0)
        detector = group["ai_intervention_detector_requested"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        row = {
            "category": category,
            "video": video,
            "present": 1,
            "frames": int(len(group)),
            "proposal_rate": float(proposed.mean()),
            "detector_request_rate": float(detector.mean()),
            "event_fn_count": int(fn.sum()),
            "protected_event_fn_count": int((fn & proposed).sum()),
            "unprotected_event_fn_count": int((fn & ~proposed).sum()),
            "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
            "final_normal_suppressor_frames": int(group["ai_final_normal_frame_suppressor_active"].sum()),
            "step4d3_carryover_lock_frames": int(
                group["ai_step4d3_carryover_lock_video"].astype(str).ne("").sum()
            ),
            "snowfall_actual_fn_candidates": int(group["ai_snowfall_actual_fn_rescue_candidate"].sum()),
            "snowfall_actual_fn_activations": int(group["ai_snowfall_actual_fn_rescue_active"].sum()),
            "snowfall_actual_fn_cap_used_max": int(group["ai_snowfall_actual_fn_rescue_cap_used"].max()),
            "snowfall_cap_exhausted_after_d3": int(
                group["ai_snowfall_actual_fn_rescue_cap_exhausted_after_d3"].sum()
            ),
            "snowfall_mask_quality_skipped": int(group["ai_snowfall_mask_quality_row_skipped"].sum()),
            "lakeside_carryover_lock_active_frames": int(
                group["ai_thermal_lakeside_carryover_lock_active"].sum()
            ),
            "lakeside_carryover_lock_trim_count_max": int(
                group["ai_thermal_lakeside_carryover_lock_trim_count"].max()
            ),
            "sofa_carryover_lock_active_frames": int(group["ai_sofa_iom_carryover_lock_active"].sum()),
            "sofa_carryover_lock_cap_used_max": int(group["ai_sofa_iom_carryover_lock_cap_used"].max()),
            "parking_carryover_lock_active_frames": int(group["ai_parking_carryover_lock_active"].sum()),
            "parking_carryover_lock_cap_used_max": int(group["ai_parking_carryover_lock_cap_used"].max()),
            "parking_post_lock_trim_candidate_frames": int(
                group["ai_parking_post_lock_trim_candidate"].sum()
            ),
            "parking_post_lock_trim_suppressed_frames": int(
                group["ai_parking_post_lock_trim_suppressed"].sum()
            ),
            "parking_post_lock_trim_count_max": int(
                group["ai_parking_post_lock_trim_count"].max()
            ),
            "parking_post_lock_trim_accidental_hard_trim_count_max": int(
                group["ai_parking_post_lock_trim_accidental_hard_trim_count"].max()
            ),
            "parking_post_lock_trim_accidental_fn_protected_trim_count_max": int(
                group["ai_parking_post_lock_trim_accidental_fn_protected_trim_count"].max()
            ),
            "parking_post_lock_deduplicate_count_max": int(
                group["ai_parking_post_lock_deduplicate_count"].max()
            ),
            "parking_restore_4d3_trim_count_max": int(
                group["ai_parking_restore_4d3_trim_count"].max()
            ),
            "parking_restore_4d3_trim_blocked_by_later_hardprotect_frames": int(
                group["ai_parking_restore_4d3_trim_blocked_by_later_hardprotect"].sum()
            ),
            "parking_post_lock_trim_4d5_soft_candidate_frames": int(
                group["ai_parking_post_lock_trim_4d5_soft_candidate"].sum()
            ),
            "parking_post_lock_trim_4d5_suppressed_frames": int(
                group["ai_parking_post_lock_trim_4d5_suppressed"].sum()
            ),
            "parking_post_lock_trim_4d5_count_max": int(
                group["ai_parking_post_lock_trim_4d5_trim_count"].max()
            ),
            "parking_post_lock_trim_4d5_accidental_fn_protected_trim_count_max": int(
                group["ai_parking_post_lock_trim_4d5_accidental_fn_protected_trim_count"].max()
            ),
            "parking_post_lock_trim_4d5_accidental_rescue_trim_count_max": int(
                group["ai_parking_post_lock_trim_4d5_accidental_rescue_trim_count"].max()
            ),
            "parking_post_lock_trim_4d6_suppressed_frames": int(
                group["ai_parking_post_lock_trim_4d6_suppressed"].sum()
            ),
            "parking_post_lock_trim_4d6_count_max": int(
                group["ai_parking_post_lock_trim_4d6_trim_count"].max()
            ),
            "parking_post_lock_trim_4d6_accidental_fn_protected_trim_count_max": int(
                group["ai_parking_post_lock_trim_4d6_accidental_fn_protected_trim_count"].max()
            ),
            "parking_post_lock_trim_4d6_accidental_rescue_trim_count_max": int(
                group["ai_parking_post_lock_trim_4d6_accidental_rescue_trim_count"].max()
            ),
            "port_lf_detector_retighten_active_frames": int(
                group["ai_port_lf_detector_retighten_active"].sum()
            ),
            "port_lf_detector_requests_before_retighten": int(
                group["ai_port_lf_detector_retighten_suppressed_detector"].sum()
                + group["ai_port_lf_detector_retighten_kept_detector"].sum()
            ),
            "port_lf_detector_requests_suppressed": int(
                group["ai_port_lf_detector_retighten_suppressed_detector"].sum()
            ),
            "port_lf_detector_requests_kept": int(
                group["ai_port_lf_detector_retighten_kept_detector"].sum()
            ),
            "port_lf_protected_fn_detector_kept": int(
                group["ai_port_lf_detector_retighten_protected_fn_detector_kept"].sum()
            ),
            "port_lf_suppressed_fp_tn_detector_frames": int(
                (
                    group["ai_port_lf_detector_retighten_suppressed_detector"].gt(0)
                    & group["Event_State"].astype(str).isin(["FP", "TN"])
                ).sum()
            ),
            "port_lf_created_unprotected_fn_count_max": int(
                group["ai_port_lf_detector_retighten_created_unprotected_fn_count"].max()
            ),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def build_ai_intervention_4e_port_detector_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "lowFramerate",
            "video": "port_0_17fps",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    suppressed = group["ai_port_lf_detector_retighten_suppressed_detector"].gt(0)
    kept = group["ai_port_lf_detector_retighten_kept_detector"].gt(0)
    fp_tn = group["Event_State"].astype(str).isin(["FP", "TN"])
    reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_reason",
        ]
        .value_counts()
        .to_dict()
    )
    kept_reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_kept_detector_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_kept_detector_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rejected_reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_rejected_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    return pd.DataFrame([{
        "category": "lowFramerate",
        "video": "port_0_17fps",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "detector_requests_before_retighten": int(suppressed.sum() + kept.sum()),
        "detector_requests_suppressed": int(suppressed.sum()),
        "detector_requests_kept": int(kept.sum()),
        "kept_detectors_that_protected_fn": int(
            group["ai_port_lf_detector_retighten_protected_fn_detector_kept"].sum()
        ),
        "suppressed_detector_fp_tn_frames": int((suppressed & fp_tn).sum()),
        "no_detector_fallback_frames": int(
            group["ai_port_lf_detector_retighten_no_detector_fallback"].sum()
        ),
        "created_unprotected_fn_frames": int(
            group["ai_port_lf_detector_retighten_created_unprotected_fn"].sum()
        ),
        "created_unprotected_fn_count_max": int(
            group["ai_port_lf_detector_retighten_created_unprotected_fn_count"].max()
        ),
        "suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_suppressed_count"].max()
        ),
        "kept_count_max": int(group["ai_port_lf_detector_retighten_kept_count"].max()),
        "protected_fn_detector_kept_count_max": int(
            group["ai_port_lf_detector_retighten_protected_fn_detector_kept_count"].max()
        ),
        "retighten_reason_counts": json.dumps(reason_counts, sort_keys=True),
        "kept_detector_reason_counts": json.dumps(kept_reason_counts, sort_keys=True),
        "rejected_reason_counts": json.dumps(rejected_reason_counts, sort_keys=True),
    }])


def build_ai_intervention_4e2_port_detector_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "lowFramerate",
            "video": "port_0_17fps",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    suppressed = group["ai_port_lf_detector_retighten_v2_suppressed_detector"].gt(0)
    kept = group["ai_port_lf_detector_retighten_v2_kept_detector"].gt(0)
    fp_tn = group["Event_State"].astype(str).isin(["FP", "TN"])
    generic_refresh = group["ai_port_lf_detector_retighten_v2_generic_refresh_not_emergency"].gt(0)
    true_emergency = group["ai_port_lf_detector_retighten_v2_true_emergency"].gt(0)
    reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_v2_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_v2_reason",
        ]
        .value_counts()
        .to_dict()
    )
    kept_reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_v2_kept_detector_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_v2_kept_detector_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rejected_reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_v2_rejected_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_v2_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    return pd.DataFrame([{
        "category": "lowFramerate",
        "video": "port_0_17fps",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "detector_requests_before_retighten": int(suppressed.sum() + kept.sum()),
        "detector_requests_suppressed": int(suppressed.sum()),
        "detector_requests_kept": int(kept.sum()),
        "actual_fn_detector_kept_count": int(
            group["ai_port_lf_detector_retighten_v2_protected_fn_detector_kept"].sum()
        ),
        "true_deterministic_emergency_detector_kept_count": int((kept & true_emergency).sum()),
        "generic_refresh_suppressed_count": int((suppressed & generic_refresh).sum()),
        "fp_tn_detector_suppressed_count": int((suppressed & fp_tn).sum()),
        "no_detector_fallback_frames": int(
            group["ai_port_lf_detector_retighten_v2_no_detector_fallback"].sum()
        ),
        "created_unprotected_fn_frames": int(
            group["ai_port_lf_detector_retighten_v2_created_unprotected_fn"].sum()
        ),
        "created_unprotected_fn_count_max": int(
            group["ai_port_lf_detector_retighten_v2_created_unprotected_fn_count"].max()
        ),
        "suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_v2_suppressed_count"].max()
        ),
        "kept_count_max": int(group["ai_port_lf_detector_retighten_v2_kept_count"].max()),
        "actual_fn_detector_kept_count_max": int(
            group["ai_port_lf_detector_retighten_v2_actual_fn_detector_kept_count"].max()
        ),
        "true_emergency_detector_kept_count_max": int(
            group["ai_port_lf_detector_retighten_v2_true_emergency_detector_kept_count"].max()
        ),
        "generic_refresh_suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_v2_generic_refresh_suppressed_count"].max()
        ),
        "fp_tn_suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_v2_fp_tn_suppressed_count"].max()
        ),
        "retighten_reason_counts": json.dumps(reason_counts, sort_keys=True),
        "kept_detector_reason_counts": json.dumps(kept_reason_counts, sort_keys=True),
        "rejected_reason_counts": json.dumps(rejected_reason_counts, sort_keys=True),
    }])


def build_ai_intervention_4e2_port_detector_rows(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
        & (
            df["ai_port_lf_detector_retighten_v2_suppressed_detector"].gt(0)
            | df["ai_port_lf_detector_retighten_v2_kept_detector"].gt(0)
        )
    )
    rows = df[mask].copy()
    if rows.empty:
        return pd.DataFrame()
    rows["retighten_v2_decision"] = rows.apply(
        lambda r: "suppressed_detector"
        if float(r.get("ai_port_lf_detector_retighten_v2_suppressed_detector", 0)) > 0
        else "kept_detector",
        axis=1,
    )
    cols = [
        "category",
        "video",
        "frame_id",
        "Event_State",
        "ai_intervention_final_action",
        "ai_detector_request_source",
        "retighten_v2_decision",
        "ai_port_lf_detector_retighten_v2_reason",
        "ai_port_lf_detector_retighten_v2_rejected_reason",
        "ai_port_lf_detector_retighten_v2_kept_detector_reason",
        "ai_port_lf_detector_retighten_v2_true_emergency",
        "ai_port_lf_detector_retighten_v2_generic_refresh_not_emergency",
        "ai_port_lf_detector_retighten_v2_no_detector_fallback",
        "ai_port_lf_detector_retighten_v2_fallback_source",
        "ai_port_lf_detector_retighten_v2_created_unprotected_fn",
        "ai_port_lf_detector_retighten_v2_protected_fn_detector_kept",
    ]
    for col in cols:
        if col not in rows.columns:
            rows[col] = ""
    return rows[cols].sort_values(["category", "video", "frame_id"])


def build_ai_intervention_4e3_port_detector_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "lowFramerate",
            "video": "port_0_17fps",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    final_fp_tn = group["ai_port_lf_detector_retighten_v3_final_event_state"].astype(str).isin(["FP", "TN"])
    suppressed = group["ai_port_lf_detector_retighten_v3_suppressed_detector"].gt(0)
    kept = group["ai_port_lf_detector_retighten_v3_kept_detector"].gt(0)
    generic_refresh = group["ai_port_lf_detector_retighten_v3_generic_refresh_not_emergency"].gt(0)
    true_emergency = group["ai_port_lf_detector_retighten_v3_true_emergency"].gt(0)
    kept_reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_v3_kept_detector_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_v3_kept_detector_reason",
        ]
        .value_counts()
        .to_dict()
    )
    suppressed_reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_v3_suppressed_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_v3_suppressed_reason",
        ]
        .value_counts()
        .to_dict()
    )
    return pd.DataFrame([{
        "category": "lowFramerate",
        "video": "port_0_17fps",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "detector_requests_before_retighten": int(suppressed.sum() + kept.sum()),
        "detector_requests_suppressed": int(suppressed.sum()),
        "detector_requests_kept": int(kept.sum()),
        "actual_fn_detector_kept_count": int(
            group["ai_port_lf_detector_retighten_v3_protected_fn_detector_kept"].sum()
        ),
        "final_fp_tn_detector_suppressed_count": int((suppressed & final_fp_tn).sum()),
        "true_deterministic_emergency_detector_kept_count": int((kept & true_emergency).sum()),
        "generic_refresh_suppressed_count": int((suppressed & generic_refresh).sum()),
        "no_detector_fallback_frames": int(
            group["ai_port_lf_detector_retighten_v3_no_detector_fallback"].sum()
        ),
        "created_unprotected_fn_frames": int(
            group["ai_port_lf_detector_retighten_v3_created_unprotected_fn"].sum()
        ),
        "created_unprotected_fn_count_max": int(
            group["ai_port_lf_detector_retighten_v3_created_unprotected_fn_count"].max()
        ),
        "suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_v3_suppressed_count"].max()
        ),
        "kept_count_max": int(group["ai_port_lf_detector_retighten_v3_kept_count"].max()),
        "actual_fn_detector_kept_count_max": int(
            group["ai_port_lf_detector_retighten_v3_actual_fn_detector_kept_count"].max()
        ),
        "true_emergency_detector_kept_count_max": int(
            group["ai_port_lf_detector_retighten_v3_true_emergency_detector_kept_count"].max()
        ),
        "generic_refresh_suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_v3_generic_refresh_suppressed_count"].max()
        ),
        "final_fp_tn_suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_v3_final_fp_tn_suppressed_count"].max()
        ),
        "kept_detector_reason_counts": json.dumps(kept_reason_counts, sort_keys=True),
        "suppressed_reason_counts": json.dumps(suppressed_reason_counts, sort_keys=True),
    }])


def build_ai_intervention_4e3_port_detector_rows(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
        & (
            df["ai_port_lf_detector_retighten_v3_suppressed_detector"].gt(0)
            | df["ai_port_lf_detector_retighten_v3_kept_detector"].gt(0)
        )
    )
    rows = df[mask].copy()
    if rows.empty:
        return pd.DataFrame()
    rows["retighten_v3_decision"] = rows.apply(
        lambda r: "suppressed_detector"
        if float(r.get("ai_port_lf_detector_retighten_v3_suppressed_detector", 0)) > 0
        else "kept_detector",
        axis=1,
    )
    cols = [
        "category",
        "video",
        "frame_id",
        "Event_State",
        "ai_intervention_final_action",
        "ai_detector_request_source",
        "retighten_v3_decision",
        "ai_port_lf_detector_retighten_v3_decision_time_event_state",
        "ai_port_lf_detector_retighten_v3_final_event_state",
        "ai_port_lf_detector_retighten_v3_kept_detector_reason",
        "ai_port_lf_detector_retighten_v3_suppressed_reason",
        "ai_port_lf_detector_retighten_v3_true_emergency",
        "ai_port_lf_detector_retighten_v3_explicit_likely_unprotected_fn",
        "ai_port_lf_detector_retighten_v3_generic_refresh_not_emergency",
        "ai_port_lf_detector_retighten_v3_generic_event_fg_not_likely_fn",
        "ai_port_lf_detector_retighten_v3_no_detector_fallback",
        "ai_port_lf_detector_retighten_v3_fallback_source",
        "ai_port_lf_detector_retighten_v3_created_unprotected_fn",
        "ai_port_lf_detector_retighten_v3_protected_fn_detector_kept",
    ]
    for col in cols:
        if col not in rows.columns:
            rows[col] = ""
    return rows[cols].sort_values(["category", "video", "frame_id"])


def build_ai_intervention_4e4_port_detector_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "lowFramerate",
            "video": "port_0_17fps",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    final_fp_tn = group["ai_port_lf_detector_retighten_v4_final_event_state"].astype(str).isin(["FP", "TN"])
    suppressed = group["ai_port_lf_detector_retighten_v4_suppressed_detector"].gt(0)
    kept = group["ai_port_lf_detector_retighten_v4_kept_detector"].gt(0)
    pre_fn_kept = group["ai_port_lf_detector_retighten_v4_pre_fn_context_kept"].gt(0)
    holdout = group["ai_port_lf_post_suppression_holdout_active"].gt(0)
    kept_reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_v4_kept_detector_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_v4_kept_detector_reason",
        ]
        .value_counts()
        .to_dict()
    )
    suppressed_reason_counts = (
        group.loc[
            group["ai_port_lf_detector_retighten_v4_suppressed_reason"].astype(str).ne(""),
            "ai_port_lf_detector_retighten_v4_suppressed_reason",
        ]
        .value_counts()
        .to_dict()
    )

    def frame_status(frame_id):
        frame = group[group["frame_id"].astype(float).astype(int).eq(frame_id)]
        if frame.empty:
            return {"present": 0}
        row = frame.iloc[-1]
        row_fn = str(row.get("Event_State", "")) == "FN"
        row_protected = float(row.get("ai_intervention_applied", 0) or 0) > 0
        return {
            "present": 1,
            "event_state": str(row.get("Event_State", "")),
            "protected": int(row_protected),
            "unprotected_fn": int(row_fn and not row_protected),
            "action": str(row.get("ai_intervention_final_action", "")),
            "holdout_active": int(float(row.get("ai_port_lf_post_suppression_holdout_active", 0) or 0) > 0),
            "detector_requested": int(float(row.get("ai_intervention_detector_requested", 0) or 0) > 0),
        }

    frame_1350 = frame_status(1350)
    frame_1355 = frame_status(1355)
    return pd.DataFrame([{
        "category": "lowFramerate",
        "video": "port_0_17fps",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "detector_requests_before_retighten": int(suppressed.sum() + kept.sum()),
        "detector_requests_suppressed": int(suppressed.sum()),
        "detector_requests_kept": int(kept.sum()),
        "pre_fn_context_detectors_kept": int(pre_fn_kept.sum()),
        "final_fp_tn_detector_suppressed_count": int((suppressed & final_fp_tn).sum()),
        "actual_fn_detector_kept_count": int(
            group["ai_port_lf_detector_retighten_v4_actual_fn_detector_kept_count"].max()
        ),
        "true_emergency_detector_kept_count": int(
            group["ai_port_lf_detector_retighten_v4_true_emergency_detector_kept_count"].max()
        ),
        "holdout_activations": int(holdout.sum()),
        "holdout_protected_event_fn_count": int(
            group["ai_port_lf_post_suppression_holdout_protected_event_fn"].sum()
        ),
        "holdout_protected_event_fn_count_max": int(
            group["ai_port_lf_post_suppression_holdout_protected_event_fn_count"].max()
        ),
        "created_unprotected_fn_frames": int(
            group["ai_port_lf_detector_retighten_v4_created_unprotected_fn"].sum()
        ),
        "created_unprotected_fn_count_max": int(
            group["ai_port_lf_detector_retighten_v4_created_unprotected_fn_count"].max()
        ),
        "suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_v4_suppressed_count"].max()
        ),
        "kept_count_max": int(group["ai_port_lf_detector_retighten_v4_kept_count"].max()),
        "pre_fn_context_kept_count_max": int(
            group["ai_port_lf_detector_retighten_v4_pre_fn_context_kept_count"].max()
        ),
        "final_fp_tn_suppressed_count_max": int(
            group["ai_port_lf_detector_retighten_v4_final_fp_tn_suppressed_count"].max()
        ),
        "frame_1350_status": json.dumps(frame_1350, sort_keys=True),
        "frame_1355_status": json.dumps(frame_1355, sort_keys=True),
        "kept_detector_reason_counts": json.dumps(kept_reason_counts, sort_keys=True),
        "suppressed_reason_counts": json.dumps(suppressed_reason_counts, sort_keys=True),
    }])


def build_ai_intervention_4e4_port_detector_rows(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    port = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
    )
    audited = (
        df["ai_port_lf_detector_retighten_v4_suppressed_detector"].gt(0)
        | df["ai_port_lf_detector_retighten_v4_kept_detector"].gt(0)
        | df["ai_port_lf_post_suppression_holdout_active"].gt(0)
        | df["frame_id"].astype(float).astype(int).isin([1350, 1355])
    )
    rows = df[port & audited].copy()
    if rows.empty:
        return pd.DataFrame()
    rows["retighten_v4_decision"] = rows.apply(
        lambda r: "suppressed_detector"
        if float(r.get("ai_port_lf_detector_retighten_v4_suppressed_detector", 0)) > 0
        else (
            "kept_detector"
            if float(r.get("ai_port_lf_detector_retighten_v4_kept_detector", 0)) > 0
            else (
                "holdout"
                if float(r.get("ai_port_lf_post_suppression_holdout_active", 0)) > 0
                else "frame_status"
            )
        ),
        axis=1,
    )
    rows["protected_event_fn"] = (
        rows["Event_State"].astype(str).eq("FN")
        & rows["ai_intervention_applied"].gt(0)
    ).astype(int)
    rows["unprotected_event_fn"] = (
        rows["Event_State"].astype(str).eq("FN")
        & ~rows["ai_intervention_applied"].gt(0)
    ).astype(int)
    cols = [
        "category",
        "video",
        "frame_id",
        "Event_State",
        "protected_event_fn",
        "unprotected_event_fn",
        "ai_intervention_final_action",
        "ai_detector_request_source",
        "retighten_v4_decision",
        "ai_port_lf_detector_retighten_v4_final_event_state",
        "ai_port_lf_detector_retighten_v4_kept_detector_reason",
        "ai_port_lf_detector_retighten_v4_suppressed_reason",
        "ai_port_lf_detector_retighten_v4_pre_fn_context_kept",
        "ai_port_lf_detector_retighten_v4_created_unprotected_fn",
        "ai_port_lf_post_suppression_holdout_active",
        "ai_port_lf_post_suppression_holdout_reason",
        "ai_port_lf_post_suppression_holdout_rejected_reason",
        "ai_port_lf_post_suppression_holdout_no_detector",
        "ai_port_lf_post_suppression_holdout_protected_event_fn",
        "ai_port_lf_post_suppression_holdout_final_normal_suppressed",
    ]
    for col in cols:
        if col not in rows.columns:
            rows[col] = ""
    return rows[cols].sort_values(["category", "video", "frame_id"])


def build_ai_intervention_4e5_port_parking_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    out = []

    def frame_status(group, frame_id):
        frame = group[group["frame_id"].astype(float).astype(int).eq(frame_id)]
        if frame.empty:
            return {"present": 0}
        row = frame.iloc[-1]
        row_fn = str(row.get("Event_State", "")) == "FN"
        row_protected = float(row.get("ai_intervention_applied", 0) or 0) > 0
        return {
            "present": 1,
            "event_state": str(row.get("Event_State", "")),
            "protected": int(row_protected),
            "unprotected_fn": int(row_fn and not row_protected),
            "action": str(row.get("ai_intervention_final_action", "")),
            "detector_requested": int(float(row.get("ai_intervention_detector_requested", 0) or 0) > 0),
        }

    port = df[
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
    ].copy()
    if not port.empty:
        proposed = port["ai_intervention_applied"].gt(0)
        detector = port["ai_intervention_detector_requested"].gt(0)
        fn = port["Event_State"].astype(str).eq("FN")
        out.append({
            "scope": "port_v4_preserve",
            "category": "lowFramerate",
            "video": "port_0_17fps",
            "present": 1,
            "frames": int(len(port)),
            "proposal_rate": float(proposed.mean()),
            "detector_request_rate": float(detector.mean()),
            "event_fn_count": int(fn.sum()),
            "protected_event_fn_count": int((fn & proposed).sum()),
            "unprotected_event_fn_count": int((fn & ~proposed).sum()),
            "detector_requests_before_retighten": int(
                port["ai_port_lf_detector_retighten_v4_suppressed_detector"].sum()
                + port["ai_port_lf_detector_retighten_v4_kept_detector"].sum()
            ),
            "detector_requests_suppressed": int(
                port["ai_port_lf_detector_retighten_v4_suppressed_detector"].sum()
            ),
            "detector_requests_kept": int(
                port["ai_port_lf_detector_retighten_v4_kept_detector"].sum()
            ),
            "actual_fn_detector_kept_count": int(
                port["ai_port_lf_detector_retighten_v4_actual_fn_detector_kept_count"].max()
            ),
            "pre_fn_context_detectors_kept": int(
                port["ai_port_lf_detector_retighten_v4_pre_fn_context_kept_count"].max()
            ),
            "final_fp_tn_detector_suppressed_count": int(
                port["ai_port_lf_detector_retighten_v4_final_fp_tn_suppressed_count"].max()
            ),
            "created_unprotected_fn_count": int(
                port["ai_port_lf_detector_retighten_v4_created_unprotected_fn_count"].max()
            ),
            "port_v4_preserve_active_frames": int(port["ai_port_v4_preserve_active"].sum()),
            "frame_1350_status": json.dumps(frame_status(port, 1350), sort_keys=True),
            "frame_1355_status": json.dumps(frame_status(port, 1355), sort_keys=True),
        })
    else:
        out.append({"scope": "port_v4_preserve", "category": "lowFramerate", "video": "port_0_17fps", "present": 0})

    parking = df[
        df["category"].astype(str).eq("intermittentObjectMotion")
        & df["video"].astype(str).eq("parking")
    ].copy()
    if not parking.empty:
        proposed = parking["ai_intervention_applied"].gt(0)
        detector = parking["ai_intervention_detector_requested"].gt(0)
        fn = parking["Event_State"].astype(str).eq("FN")
        out.append({
            "scope": "parking_restore_4d6",
            "category": "intermittentObjectMotion",
            "video": "parking",
            "present": 1,
            "frames": int(len(parking)),
            "proposal_rate": float(proposed.mean()),
            "detector_request_rate": float(detector.mean()),
            "event_fn_count": int(fn.sum()),
            "protected_event_fn_count": int((fn & proposed).sum()),
            "unprotected_event_fn_count": int((fn & ~proposed).sum()),
            "restored_4d3_trim_count": int(parking["ai_parking_restore_4d6_trim_4d3_count"].max()),
            "restored_4d5_trim_count": int(parking["ai_parking_restore_4d6_trim_4d5_count"].max()),
            "restored_4d6_trim_count": int(parking["ai_parking_restore_4d6_trim_4d6_count"].max()),
            "restore_extra_trim_count": int(parking["ai_parking_restore_4d6_trim_extra_count"].max()),
            "parking_fn_fallback_activations": int(
                parking["ai_parking_restore_4d6_fn_fallback_active"].sum()
            ),
            "parking_fn_fallback_protected_event_fn_count": int(
                parking["ai_parking_restore_4d6_fn_fallback_protected_event_fn"].sum()
            ),
            "parking_fn_fallback_protected_event_fn_count_max": int(
                parking["ai_parking_restore_4d6_fn_fallback_protected_event_fn_count"].max()
            ),
            "accidental_fn_protected_trim_count": int(
                parking["ai_parking_restore_4d6_trim_accidental_fn_protected_trim_count"].max()
            ),
            "accidental_rescue_trim_count": int(
                parking["ai_parking_restore_4d6_trim_accidental_rescue_trim_count"].max()
            ),
            "restore_trim_stack_active_frames": int(
                parking["ai_parking_restore_4d6_trim_stack_active"].sum()
            ),
        })
    else:
        out.append({"scope": "parking_restore_4d6", "category": "intermittentObjectMotion", "video": "parking", "present": 0})
    return pd.DataFrame(out)


def build_ai_intervention_4e5_parking_rows(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    parking = (
        df["category"].astype(str).eq("intermittentObjectMotion")
        & df["video"].astype(str).eq("parking")
    )
    audited = (
        df["ai_parking_restore_4d6_fn_fallback_active"].gt(0)
        | df["ai_parking_restore_4d6_trim_extra_count"].gt(0)
        | df["ai_parking_post_lock_trim_4d6_suppressed"].gt(0)
        | df["Event_State"].astype(str).eq("FN")
    )
    rows = df[parking & audited].copy()
    if rows.empty:
        return pd.DataFrame()
    rows["protected_event_fn"] = (
        rows["Event_State"].astype(str).eq("FN")
        & rows["ai_intervention_applied"].gt(0)
    ).astype(int)
    rows["unprotected_event_fn"] = (
        rows["Event_State"].astype(str).eq("FN")
        & ~rows["ai_intervention_applied"].gt(0)
    ).astype(int)
    cols = [
        "category",
        "video",
        "frame_id",
        "Event_State",
        "protected_event_fn",
        "unprotected_event_fn",
        "ai_intervention_applied",
        "ai_intervention_type",
        "ai_intervention_final_action",
        "ai_parking_restore_4d6_trim_stack_active",
        "ai_parking_restore_4d6_trim_stack_reason",
        "ai_parking_restore_4d6_trim_extra_count",
        "ai_parking_restore_4d6_fn_fallback_active",
        "ai_parking_restore_4d6_fn_fallback_reason",
        "ai_parking_restore_4d6_fn_fallback_no_detector",
        "ai_parking_restore_4d6_fn_fallback_protected_event_fn",
        "ai_parking_post_lock_trim_4d6_suppressed",
        "ai_parking_post_lock_trim_4d6_reason",
        "ai_parking_post_lock_trim_4d6_rejected_reason",
    ]
    for col in cols:
        if col not in rows.columns:
            rows[col] = ""
    return rows[cols].sort_values(["category", "video", "frame_id"])


def build_ai_intervention_4e6_port_parking_rebase_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    out = []

    def frame_status(group, frame_id):
        frame = group[group["frame_id"].astype(float).astype(int).eq(frame_id)]
        if frame.empty:
            return {"present": 0}
        row = frame.iloc[-1]
        row_fn = str(row.get("Event_State", "")) == "FN"
        row_protected = float(row.get("ai_intervention_applied", 0) or 0) > 0
        return {
            "present": 1,
            "event_state": str(row.get("Event_State", "")),
            "protected": int(row_protected),
            "unprotected_fn": int(row_fn and not row_protected),
            "action": str(row.get("ai_intervention_final_action", "")),
            "detector_requested": int(float(row.get("ai_intervention_detector_requested", 0) or 0) > 0),
            "hard_lock_status": str(
                row.get(f"ai_port_lf_v4_hard_lock_frame_{frame_id}_status", "")
            ),
        }

    port = df[
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
    ].copy()
    if not port.empty:
        proposed = port["ai_intervention_applied"].gt(0)
        detector = port["ai_intervention_detector_requested"].gt(0)
        fn = port["Event_State"].astype(str).eq("FN")
        out.append({
            "scope": "port_v4_hard_lock",
            "category": "lowFramerate",
            "video": "port_0_17fps",
            "present": 1,
            "frames": int(len(port)),
            "proposal_rate": float(proposed.mean()),
            "detector_request_rate": float(detector.mean()),
            "event_fn_count": int(fn.sum()),
            "protected_event_fn_count": int((fn & proposed).sum()),
            "unprotected_event_fn_count": int((fn & ~proposed).sum()),
            "detector_requests_before_retighten": int(
                port["ai_port_lf_detector_retighten_v4_suppressed_detector"].sum()
                + port["ai_port_lf_detector_retighten_v4_kept_detector"].sum()
            ),
            "detector_requests_suppressed": int(
                port["ai_port_lf_detector_retighten_v4_suppressed_detector"].sum()
            ),
            "detector_requests_kept": int(
                port["ai_port_lf_detector_retighten_v4_kept_detector"].sum()
            ),
            "actual_fn_detector_kept_count": int(
                port["ai_port_lf_detector_retighten_v4_actual_fn_detector_kept_count"].max()
            ),
            "pre_fn_context_detectors_kept": int(
                port["ai_port_lf_detector_retighten_v4_pre_fn_context_kept_count"].max()
            ),
            "final_fp_tn_detector_suppressed_count": int(
                port["ai_port_lf_detector_retighten_v4_final_fp_tn_suppressed_count"].max()
            ),
            "created_unprotected_fn_count": int(
                port["ai_port_lf_detector_retighten_v4_created_unprotected_fn_count"].max()
            ),
            "hard_lock_active_frames": int(port["ai_port_lf_v4_hard_lock_active"].sum()),
            "hard_lock_deviation_count": int(
                port["ai_port_lf_v4_hard_lock_deviation_from_4e4"].max()
            ),
            "holdout_activations": int(port["ai_port_lf_post_suppression_holdout_active"].sum()),
            "frame_1350_status": json.dumps(frame_status(port, 1350), sort_keys=True),
            "frame_1355_status": json.dumps(frame_status(port, 1355), sort_keys=True),
        })
    else:
        out.append({"scope": "port_v4_hard_lock", "category": "lowFramerate", "video": "port_0_17fps", "present": 0})

    parking = df[
        df["category"].astype(str).eq("intermittentObjectMotion")
        & df["video"].astype(str).eq("parking")
    ].copy()
    if not parking.empty:
        proposed = parking["ai_intervention_applied"].gt(0)
        detector = parking["ai_intervention_detector_requested"].gt(0)
        fn = parking["Event_State"].astype(str).eq("FN")
        out.append({
            "scope": "parking_4d6_hard_restore",
            "category": "intermittentObjectMotion",
            "video": "parking",
            "present": 1,
            "frames": int(len(parking)),
            "proposal_rate": float(proposed.mean()),
            "detector_request_rate": float(detector.mean()),
            "event_fn_count": int(fn.sum()),
            "protected_event_fn_count": int((fn & proposed).sum()),
            "unprotected_event_fn_count": int((fn & ~proposed).sum()),
            "restored_4d3_trim_count": int(parking["ai_parking_restore_4d6_trim_4d3_count"].max()),
            "restored_4d5_trim_count": int(parking["ai_parking_restore_4d6_trim_4d5_count"].max()),
            "restored_4d6_trim_count": int(parking["ai_parking_restore_4d6_trim_4d6_count"].max()),
            "hard_restore_safe_trim_count": int(parking["ai_parking_4d6_hard_restore_safe_trim_count"].max()),
            "hard_restore_fn_fallback_activations": int(
                parking["ai_parking_4d6_hard_restore_fn_fallback_active"].sum()
            ),
            "hard_restore_fn_fallback_protected_event_fn_count": int(
                parking["ai_parking_4d6_hard_restore_fn_fallback_protected_event_fn"].sum()
            ),
            "accidental_fn_trim_count": int(
                parking["ai_parking_4d6_hard_restore_accidental_fn_trim_count"].max()
            ),
            "accidental_rescue_trim_count": int(
                parking["ai_parking_4d6_hard_restore_accidental_rescue_trim_count"].max()
            ),
            "hard_restore_active_frames": int(parking["ai_parking_4d6_hard_restore_active"].sum()),
            "trim_stack_status": str(
                parking["ai_parking_4d6_hard_restore_trim_stack_status"].iloc[-1]
            ),
        })
    else:
        out.append({"scope": "parking_4d6_hard_restore", "category": "intermittentObjectMotion", "video": "parking", "present": 0})

    for category, video, scope, lock_col in [
        ("badWeather", "snowFall", "snowfall_carryover_gate_lock", "ai_snowfall_carryover_gate_lock_status"),
        ("thermal", "lakeSide", "lakeside_carryover_gate_lock", "ai_lakeside_carryover_gate_lock_status"),
    ]:
        group = df[
            df["category"].astype(str).eq(category)
            & df["video"].astype(str).eq(video)
        ].copy()
        if group.empty:
            out.append({"scope": scope, "category": category, "video": video, "present": 0})
            continue
        proposed = group["ai_intervention_applied"].gt(0)
        detector = group["ai_intervention_detector_requested"].gt(0)
        fn = group["Event_State"].astype(str).eq("FN")
        status_values = group[lock_col].astype(str)
        status_values = status_values[status_values.ne("")]
        out.append({
            "scope": scope,
            "category": category,
            "video": video,
            "present": 1,
            "frames": int(len(group)),
            "proposal_rate": float(proposed.mean()),
            "detector_request_rate": float(detector.mean()),
            "event_fn_count": int(fn.sum()),
            "protected_event_fn_count": int((fn & proposed).sum()),
            "unprotected_event_fn_count": int((fn & ~proposed).sum()),
            "gate_lock_status": status_values.iloc[-1] if not status_values.empty else "",
        })
    return pd.DataFrame(out)


def build_ai_intervention_4e6_port_parking_rebase_rows(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    port = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("port_0_17fps")
        & (
            df["ai_port_lf_detector_retighten_v4_suppressed_detector"].gt(0)
            | df["ai_port_lf_detector_retighten_v4_kept_detector"].gt(0)
            | df["ai_port_lf_v4_hard_lock_active"].gt(0)
            | df["ai_port_lf_post_suppression_holdout_active"].gt(0)
            | df["frame_id"].astype(float).astype(int).isin([1350, 1355])
        )
    )
    parking = (
        df["category"].astype(str).eq("intermittentObjectMotion")
        & df["video"].astype(str).eq("parking")
        & (
            df["ai_parking_4d6_hard_restore_safe_trim_active"].gt(0)
            | df["ai_parking_4d6_hard_restore_fn_fallback_active"].gt(0)
            | df["ai_parking_post_lock_trim_4d6_suppressed"].gt(0)
            | df["Event_State"].astype(str).eq("FN")
        )
    )
    rows = df[port | parking].copy()
    if rows.empty:
        return pd.DataFrame()
    rows["protected_event_fn"] = (
        rows["Event_State"].astype(str).eq("FN")
        & rows["ai_intervention_applied"].gt(0)
    ).astype(int)
    rows["unprotected_event_fn"] = (
        rows["Event_State"].astype(str).eq("FN")
        & ~rows["ai_intervention_applied"].gt(0)
    ).astype(int)
    cols = [
        "category",
        "video",
        "frame_id",
        "Event_State",
        "protected_event_fn",
        "unprotected_event_fn",
        "ai_intervention_applied",
        "ai_intervention_detector_requested",
        "ai_intervention_final_action",
        "ai_detector_request_source",
        "ai_port_lf_detector_retighten_v4_kept_detector",
        "ai_port_lf_detector_retighten_v4_suppressed_detector",
        "ai_port_lf_detector_retighten_v4_kept_detector_reason",
        "ai_port_lf_detector_retighten_v4_suppressed_reason",
        "ai_port_lf_v4_hard_lock_active",
        "ai_port_lf_v4_hard_lock_reason",
        "ai_port_lf_v4_hard_lock_deviation_from_4e4",
        "ai_port_lf_v4_hard_lock_frame_1350_status",
        "ai_port_lf_v4_hard_lock_frame_1355_status",
        "ai_port_lf_post_suppression_holdout_active",
        "ai_port_lf_post_suppression_holdout_reason",
        "ai_parking_4d6_hard_restore_active",
        "ai_parking_4d6_hard_restore_reason",
        "ai_parking_4d6_hard_restore_trim_stack_status",
        "ai_parking_4d6_hard_restore_safe_trim_active",
        "ai_parking_4d6_hard_restore_safe_trim_reason",
        "ai_parking_4d6_hard_restore_fn_fallback_active",
        "ai_parking_4d6_hard_restore_fn_fallback_reason",
        "ai_parking_4d6_hard_restore_fn_fallback_protected_event_fn",
        "ai_parking_4d6_hard_restore_accidental_fn_trim_count",
        "ai_parking_4d6_hard_restore_accidental_rescue_trim_count",
    ]
    for col in cols:
        if col not in rows.columns:
            rows[col] = ""
    return rows[cols].sort_values(["category", "video", "frame_id"])


def build_ai_intervention_2o_tunnel_exit_summary(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    mask = (
        df["category"].astype(str).eq("lowFramerate")
        & df["video"].astype(str).eq("tunnelExit_0_35fps")
    )
    group = df[mask].copy()
    if group.empty:
        return pd.DataFrame([{
            "category": "lowFramerate",
            "video": "tunnelExit_0_35fps",
            "present": 0,
        }])
    proposed = group["ai_intervention_applied"].gt(0)
    detector = group["ai_intervention_detector_requested"].gt(0)
    fn = group["Event_State"].astype(str).eq("FN")
    preserved = group["ai_tunnel_exit_lf_preserve_fn_risk_active"].gt(0)
    rescue = group["ai_tunnel_exit_lf_rescue_active"].gt(0)
    trimmed = group["ai_tunnel_exit_lf_post_trim_suppressed_generic_nonrisk"].gt(0)
    protected = preserved | rescue
    preserve_reason_counts = (
        group.loc[
            group["ai_tunnel_exit_lf_preserve_fn_risk_reason"].astype(str).ne(""),
            "ai_tunnel_exit_lf_preserve_fn_risk_reason",
        ]
        .value_counts()
        .to_dict()
    )
    preserve_rejected_counts = (
        group.loc[
            group["ai_tunnel_exit_lf_preserve_fn_risk_rejected_reason"].astype(str).ne(""),
            "ai_tunnel_exit_lf_preserve_fn_risk_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rescue_reason_counts = (
        group.loc[
            group["ai_tunnel_exit_lf_rescue_reason"].astype(str).ne(""),
            "ai_tunnel_exit_lf_rescue_reason",
        ]
        .value_counts()
        .to_dict()
    )
    rescue_rejected_counts = (
        group.loc[
            group["ai_tunnel_exit_lf_rescue_rejected_reason"].astype(str).ne(""),
            "ai_tunnel_exit_lf_rescue_rejected_reason",
        ]
        .value_counts()
        .to_dict()
    )
    return pd.DataFrame([{
        "category": "lowFramerate",
        "video": "tunnelExit_0_35fps",
        "present": 1,
        "frames": int(len(group)),
        "proposal_rate": float(proposed.mean()),
        "detector_request_rate": float(detector.mean()),
        "event_fn_count": int(fn.sum()),
        "protected_event_fn_count": int((fn & proposed).sum()),
        "unprotected_event_fn_count": int((fn & ~proposed).sum()),
        "normal_frame_proposed_interventions": int((proposed & group["normal_frame"].gt(0)).sum()),
        "preserved_fn_risk_candidate_frames": int(group["ai_tunnel_exit_lf_preserve_fn_risk_candidate"].sum()),
        "preserved_fn_risk_active_frames": int(preserved.sum()),
        "rescue_candidate_frames": int(group["ai_tunnel_exit_lf_rescue_candidate"].sum()),
        "rescue_active_frames": int(rescue.sum()),
        "rescue_no_detector_frames": int(group["ai_tunnel_exit_lf_rescue_no_detector"].sum()),
        "rescue_protected_event_fn_frames": int((rescue & fn & proposed).sum()),
        "rescue_final_normal_suppressed_frames": int(
            group["ai_tunnel_exit_lf_rescue_final_normal_suppressed"].sum()
        ),
        "generic_post_trim_suppressions": int(trimmed.sum()),
        "post_trim_active_frames": int(group["ai_tunnel_exit_lf_post_trim_active"].sum()),
        "post_trim_final_rate_max": float(group["ai_tunnel_exit_lf_post_trim_final_rate"].max()),
        "preserved_rescue_frames_accidentally_trimmed_count": int((trimmed & protected).sum()),
        "post_trim_skipped_preserved_fn_risk_frames": int(
            group["ai_tunnel_exit_lf_post_trim_skipped_preserved_fn_risk"].sum()
        ),
        "post_trim_skipped_rescue_frame_frames": int(
            group["ai_tunnel_exit_lf_post_trim_skipped_rescue_frame"].sum()
        ),
        "preserve_reason_counts": json.dumps(preserve_reason_counts, sort_keys=True),
        "preserve_rejected_reason_counts": json.dumps(preserve_rejected_counts, sort_keys=True),
        "rescue_reason_counts": json.dumps(rescue_reason_counts, sort_keys=True),
        "rescue_rejected_reason_counts": json.dumps(rescue_rejected_counts, sort_keys=True),
    }])


def build_ai_intervention_action_delta(root):
    df = _read_ai_intervention_frames(root)
    if df.empty:
        return pd.DataFrame()
    changed = df[df["ai_intervention_applied"].gt(0)].copy()
    if changed.empty:
        return pd.DataFrame(columns=["original_action", "final_action", "intervention_type", "frames"])
    return (
        changed.groupby([
            "ai_intervention_original_action",
            "ai_intervention_final_action",
            "ai_intervention_type",
        ], dropna=False)
        .size()
        .reset_index(name="frames")
        .rename(columns={
            "ai_intervention_original_action": "original_action",
            "ai_intervention_final_action": "final_action",
            "ai_intervention_type": "intervention_type",
        })
    )


def build_ai_intervention_safety_summary(root):
    df = _read_ai_intervention_frames(root)
    final_summary = read_final_summary(root)
    rows = []
    if not final_summary.empty:
        for _, row in final_summary.iterrows():
            rows.append({
                "scope": "aggregate_pipeline",
                "name": row.get("Pipeline", ""),
                "FMeasure": row.get("CDnet_FMeasure", row.get("FMeasure", 0.0)),
                "Event_F1": row.get("Event_F1", 0.0),
                "Avg_FPS": row.get("Avg_FPS", 0.0),
                "P95_latency_ms": row.get("P95_latency_ms", row.get("P95_latency", 0.0)),
                "Activation": row.get("Activation", 0.0),
                "event_fn_count": "",
                "closed_empty_final_count": "",
                "intervention_rate": "",
            })
    if not df.empty:
        for video in ["bridgeEntry", "cubicle", "continuousPan"]:
            group = df[df["video"].eq(video)]
            if group.empty:
                continue
            rows.append({
                "scope": "video_focus",
                "name": video,
                "FMeasure": float(group["FMeasure"].mean()),
                "Event_F1": "",
                "Avg_FPS": "",
                "P95_latency_ms": "",
                "Activation": float(group["yolo_called"].mean()),
                "event_fn_count": int(group["Event_State"].astype(str).eq("FN").sum()),
                "closed_empty_final_count": int(group["event_closed_empty_final_count"].sum()),
                "intervention_rate": float(group["ai_intervention_applied"].mean()),
            })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default="outputs/asmag_tr_controller_online_guarded_cdnet_smoke",
        help="Experiment output folder to compare.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    summary = read_final_summary(root)
    summary.to_csv(root / "comparison_summary.csv", index=False)

    metric_delta(summary, OLD_ONLINE).to_csv(root / "gain_vs_old_online.csv", index=False)
    metric_delta(summary, "P3_MOG2").to_csv(root / "gain_vs_p3.csv", index=False)
    metric_delta(summary, "ASMAG_TR_CONTROLLER").to_csv(root / "gain_vs_controller.csv", index=False)

    per_video = read_per_video(root)
    build_per_video_failure_delta(per_video).to_csv(root / "per_video_failure_delta.csv", index=False)
    build_mode_action_summary(root).to_csv(root / "mode_action_summary.csv", index=False)
    build_gmq_action_summary(root).to_csv(root / "gmq_action_summary.csv", index=False)
    build_gmq_quality_summary(root).to_csv(root / "gmq_quality_summary.csv", index=False)
    build_gmq_legacy_safe_summary(root).to_csv(root / "gmq_legacy_safe_summary.csv", index=False)
    build_gmq_event_continuity_summary(root).to_csv(root / "gmq_event_continuity_summary.csv", index=False)
    build_ptz_closed_empty_summary(root).to_csv(root / "ptz_closed_empty_summary.csv", index=False)
    build_motion_comp_summary(root).to_csv(root / "motion_comp_summary.csv", index=False)
    build_motion_comp_summary(root, ptz_only=True).to_csv(root / "ptz_motion_comp_summary.csv", index=False)
    build_low_framerate_guard_summary(root).to_csv(root / "low_framerate_guard_summary.csv", index=False)
    cadence = build_cadence_thinning_summary(root)
    cadence.to_csv(root / "cadence_thinning_summary.csv", index=False)
    build_continuous_pan_policy_summary(root).to_csv(root / "continuous_pan_policy_summary.csv", index=False)
    build_geometry_probe_summary(root).to_csv(root / "geometry_probe_summary.csv", index=False)
    build_geometry_trust_summary(root).to_csv(root / "geometry_trust_summary.csv", index=False)
    build_geometry_action_summary(root).to_csv(root / "geometry_action_summary.csv", index=False)
    build_teacher_ranker_summary(root).to_csv(root / "teacher_ranker_summary.csv", index=False)
    build_teacher_action_summary(root).to_csv(root / "teacher_action_summary.csv", index=False)
    build_teacher_safety_guard_summary(root).to_csv(root / "teacher_safety_guard_summary.csv", index=False)
    build_teacher_continuous_pan_summary(root).to_csv(root / "teacher_continuous_pan_summary.csv", index=False)
    build_ai_shadow_summary(root).to_csv(root / "ai_shadow_summary.csv", index=False)
    build_ai_shadow_disagreement_summary(root).to_csv(root / "ai_shadow_disagreement_summary.csv", index=False)
    build_ai_shadow_safety_summary(root).to_csv(root / "ai_shadow_safety_summary.csv", index=False)
    build_ai_shadow_video_summary(root).to_csv(root / "ai_shadow_video_summary.csv", index=False)
    build_ai_subrisk_shadow_summary(root).to_csv(root / "ai_subrisk_shadow_summary.csv", index=False)
    build_ai_subrisk_video_summary(root).to_csv(root / "ai_subrisk_video_summary.csv", index=False)
    build_ai_subrisk_latency_summary(root).to_csv(root / "ai_subrisk_latency_summary.csv", index=False)
    build_ai_subrisk_threshold_summary(root).to_csv(root / "ai_subrisk_threshold_summary.csv", index=False)
    build_ai_intervention_summary(root).to_csv(root / "ai_intervention_summary.csv", index=False)
    build_ai_intervention_video_summary(root).to_csv(root / "ai_intervention_video_summary.csv", index=False)
    build_ai_intervention_budget_summary(root).to_csv(root / "ai_intervention_budget_summary.csv", index=False)
    build_ai_intervention_action_delta(root).to_csv(root / "ai_intervention_action_delta.csv", index=False)
    build_ai_intervention_safety_summary(root).to_csv(root / "ai_intervention_safety_summary.csv", index=False)
    build_ai_intervention_2b_summary(root).to_csv(root / "ai_intervention_2b_summary.csv", index=False)
    build_ai_intervention_2b_video_summary(root).to_csv(root / "ai_intervention_2b_video_summary.csv", index=False)
    build_ai_intervention_2b_budget_summary(root).to_csv(root / "ai_intervention_2b_budget_summary.csv", index=False)
    build_ai_intervention_2b_dryrun_vs_live(root).to_csv(root / "ai_intervention_2b_dryrun_vs_live.csv", index=False)
    build_ai_intervention_2c_summary(root).to_csv(root / "ai_intervention_2c_summary.csv", index=False)
    build_ai_intervention_2c_video_summary(root).to_csv(root / "ai_intervention_2c_video_summary.csv", index=False)
    build_ai_intervention_2c_event_foreground_summary(root).to_csv(root / "ai_intervention_2c_event_foreground_summary.csv", index=False)
    build_ai_intervention_2c_dryrun_vs_live(root).to_csv(root / "ai_intervention_2c_dryrun_vs_live.csv", index=False)
    build_ai_intervention_2d_summary(root).to_csv(root / "ai_intervention_2d_summary.csv", index=False)
    build_ai_intervention_2d_video_summary(root).to_csv(root / "ai_intervention_2d_video_summary.csv", index=False)
    build_ai_intervention_2d_event_foreground_summary(root).to_csv(root / "ai_intervention_2d_event_foreground_summary.csv", index=False)
    build_ai_intervention_2d_cubicle_like_summary(root).to_csv(root / "ai_intervention_2d_cubicle_like_summary.csv", index=False)
    build_ai_intervention_2d_dryrun_vs_live(root).to_csv(root / "ai_intervention_2d_dryrun_vs_live.csv", index=False)
    build_ai_intervention_2e_summary(root).to_csv(root / "ai_intervention_2e_summary.csv", index=False)
    build_ai_intervention_2e_video_summary(root).to_csv(root / "ai_intervention_2e_video_summary.csv", index=False)
    build_ai_intervention_2e_event_foreground_summary(root).to_csv(root / "ai_intervention_2e_event_foreground_summary.csv", index=False)
    build_ai_intervention_2e_cubicle_like_summary(root).to_csv(root / "ai_intervention_2e_cubicle_like_summary.csv", index=False)
    build_ai_intervention_2e_budget_reclaim_summary(root).to_csv(root / "ai_intervention_2e_budget_reclaim_summary.csv", index=False)
    build_ai_intervention_2e_dryrun_vs_live(root).to_csv(root / "ai_intervention_2e_dryrun_vs_live.csv", index=False)
    build_ai_intervention_2f_summary(root).to_csv(root / "ai_intervention_2f_summary.csv", index=False)
    build_ai_intervention_2f_video_summary(root).to_csv(root / "ai_intervention_2f_video_summary.csv", index=False)
    build_ai_intervention_2f_event_foreground_summary(root).to_csv(root / "ai_intervention_2f_event_foreground_summary.csv", index=False)
    build_ai_intervention_2f_cubicle_like_summary(root).to_csv(root / "ai_intervention_2f_cubicle_like_summary.csv", index=False)
    build_ai_intervention_2f_budget_reclaim_summary(root).to_csv(root / "ai_intervention_2f_budget_reclaim_summary.csv", index=False)
    build_ai_intervention_2f_normal_frame_suppression_summary(root).to_csv(root / "ai_intervention_2f_normal_frame_suppression_summary.csv", index=False)
    two_f_dryrun_vs_live = build_ai_intervention_2f_dryrun_vs_live(root)
    if not two_f_dryrun_vs_live.empty:
        two_f_dryrun_vs_live.to_csv(root / "ai_intervention_2f_dryrun_vs_live.csv", index=False)
    build_ai_intervention_2g_summary(root).to_csv(root / "ai_intervention_2g_summary.csv", index=False)
    build_ai_intervention_2g_video_summary(root).to_csv(root / "ai_intervention_2g_video_summary.csv", index=False)
    build_ai_intervention_2g_event_foreground_summary(root).to_csv(root / "ai_intervention_2g_event_foreground_summary.csv", index=False)
    build_ai_intervention_2g_cubicle_like_summary(root).to_csv(root / "ai_intervention_2g_cubicle_like_summary.csv", index=False)
    build_ai_intervention_2g_budget_reclaim_summary(root).to_csv(root / "ai_intervention_2g_budget_reclaim_summary.csv", index=False)
    build_ai_intervention_2g_normal_frame_suppression_summary(root).to_csv(root / "ai_intervention_2g_normal_frame_suppression_summary.csv", index=False)
    build_ai_intervention_2g_lowframerate_trim_summary(root).to_csv(root / "ai_intervention_2g_lowframerate_trim_summary.csv", index=False)
    two_g_dryrun_vs_live = build_ai_intervention_2g_dryrun_vs_live(root)
    if not two_g_dryrun_vs_live.empty:
        two_g_dryrun_vs_live.to_csv(root / "ai_intervention_2g_dryrun_vs_live.csv", index=False)
    build_ai_intervention_2h_summary(root).to_csv(root / "ai_intervention_2h_summary.csv", index=False)
    build_ai_intervention_2h_video_summary(root).to_csv(root / "ai_intervention_2h_video_summary.csv", index=False)
    build_ai_intervention_2h_event_foreground_summary(root).to_csv(root / "ai_intervention_2h_event_foreground_summary.csv", index=False)
    build_ai_intervention_2h_cubicle_like_summary(root).to_csv(root / "ai_intervention_2h_cubicle_like_summary.csv", index=False)
    build_ai_intervention_2h_budget_reclaim_summary(root).to_csv(root / "ai_intervention_2h_budget_reclaim_summary.csv", index=False)
    build_ai_intervention_2h_normal_frame_suppression_summary(root).to_csv(
        root / "ai_intervention_2h_normal_frame_suppression_summary.csv",
        index=False,
    )
    build_ai_intervention_2h_lowframerate_trim_summary(root).to_csv(root / "ai_intervention_2h_lowframerate_trim_summary.csv", index=False)
    build_ai_intervention_2h_exact_cubicle_stabilizer_summary(root).to_csv(
        root / "ai_intervention_2h_exact_cubicle_stabilizer_summary.csv",
        index=False,
    )
    build_ai_intervention_2h2_summary(root).to_csv(root / "ai_intervention_2h2_summary.csv", index=False)
    build_ai_intervention_2h2_video_summary(root).to_csv(root / "ai_intervention_2h2_video_summary.csv", index=False)
    build_ai_intervention_2h2_event_foreground_summary(root).to_csv(root / "ai_intervention_2h2_event_foreground_summary.csv", index=False)
    build_ai_intervention_2h2_cubicle_like_summary(root).to_csv(root / "ai_intervention_2h2_cubicle_like_summary.csv", index=False)
    build_ai_intervention_2h2_budget_reclaim_summary(root).to_csv(root / "ai_intervention_2h2_budget_reclaim_summary.csv", index=False)
    build_ai_intervention_2h2_normal_frame_suppression_summary(root).to_csv(
        root / "ai_intervention_2h2_normal_frame_suppression_summary.csv",
        index=False,
    )
    build_ai_intervention_2h2_lowframerate_trim_summary(root).to_csv(root / "ai_intervention_2h2_lowframerate_trim_summary.csv", index=False)
    build_ai_intervention_2h2_exact_cubicle_stabilizer_summary(root).to_csv(
        root / "ai_intervention_2h2_exact_cubicle_stabilizer_summary.csv",
        index=False,
    )
    build_ai_intervention_2i_summary(root).to_csv(root / "ai_intervention_2i_summary.csv", index=False)
    build_ai_intervention_2i_video_summary(root).to_csv(root / "ai_intervention_2i_video_summary.csv", index=False)
    build_ai_intervention_2i_event_foreground_summary(root).to_csv(root / "ai_intervention_2i_event_foreground_summary.csv", index=False)
    build_ai_intervention_2i_cubicle_like_summary(root).to_csv(root / "ai_intervention_2i_cubicle_like_summary.csv", index=False)
    build_ai_intervention_2i_budget_reclaim_summary(root).to_csv(root / "ai_intervention_2i_budget_reclaim_summary.csv", index=False)
    build_ai_intervention_2i_normal_frame_suppression_summary(root).to_csv(
        root / "ai_intervention_2i_normal_frame_suppression_summary.csv",
        index=False,
    )
    build_ai_intervention_2i_lowframerate_trim_summary(root).to_csv(root / "ai_intervention_2i_lowframerate_trim_summary.csv", index=False)
    build_ai_intervention_2i_exact_cubicle_stabilizer_summary(root).to_csv(
        root / "ai_intervention_2i_exact_cubicle_stabilizer_summary.csv",
        index=False,
    )
    build_ai_intervention_2i_presignal_summary(root).to_csv(root / "ai_intervention_2i_presignal_summary.csv", index=False)
    build_ai_intervention_2i_fountain01_quiet_guard_summary(root).to_csv(
        root / "ai_intervention_2i_fountain01_quiet_guard_summary.csv",
        index=False,
    )
    build_ai_intervention_2i_lowframerate_retighten_summary(root).to_csv(
        root / "ai_intervention_2i_lowframerate_retighten_summary.csv",
        index=False,
    )
    build_ai_intervention_2j_summary(root).to_csv(root / "ai_intervention_2j_summary.csv", index=False)
    build_ai_intervention_2j_video_summary(root).to_csv(root / "ai_intervention_2j_video_summary.csv", index=False)
    build_ai_intervention_2j_exact_cubicle_late_event_rescue_summary(root).to_csv(
        root / "ai_intervention_2j_exact_cubicle_late_event_rescue_summary.csv",
        index=False,
    )
    build_ai_intervention_2j_frame_1560_status(root).to_csv(
        root / "ai_intervention_2j_frame_1560_status.csv",
        index=False,
    )
    build_ai_intervention_2k_ptz_intermittent_pan_summary(root).to_csv(
        root / "ai_intervention_2k_ptz_intermittent_pan_summary.csv",
        index=False,
    )
    build_ai_intervention_2p_live_mismatch_summary(root).to_csv(
        root / "ai_intervention_2p_live_mismatch_summary.csv",
        index=False,
    )
    build_ai_intervention_2p_frame_status(root).to_csv(
        root / "ai_intervention_2p_frame_status.csv",
        index=False,
    )
    build_ai_intervention_2q_live_cap_reserve_summary(root).to_csv(
        root / "ai_intervention_2q_live_cap_reserve_summary.csv",
        index=False,
    )
    build_ai_intervention_2l_copymachine_summary(root).to_csv(
        root / "ai_intervention_2l_copymachine_summary.csv",
        index=False,
    )
    build_ai_intervention_2l2_rescue_first_summary(root).to_csv(
        root / "ai_intervention_2l2_rescue_first_summary.csv",
        index=False,
    )
    build_ai_intervention_2m_parking_summary(root).to_csv(
        root / "ai_intervention_2m_parking_summary.csv",
        index=False,
    )
    build_ai_intervention_2m2_parking_summary(root).to_csv(
        root / "ai_intervention_2m2_parking_summary.csv",
        index=False,
    )
    build_ai_intervention_2m3_parking_summary(root).to_csv(
        root / "ai_intervention_2m3_parking_summary.csv",
        index=False,
    )
    build_ai_intervention_2q3_parking_live_trim_summary(root).to_csv(
        root / "ai_intervention_2q3_parking_live_trim_summary.csv",
        index=False,
    )
    build_ai_intervention_2q4_parking_soft_trim_summary(root).to_csv(
        root / "ai_intervention_2q4_parking_soft_trim_summary.csv",
        index=False,
    )
    build_ai_intervention_2n_turbulence2_summary(root).to_csv(
        root / "ai_intervention_2n_turbulence2_summary.csv",
        index=False,
    )
    build_ai_intervention_2q2_turbulence_carryover_summary(root).to_csv(
        root / "ai_intervention_2q2_turbulence_carryover_summary.csv",
        index=False,
    )
    build_ai_intervention_4b_lakeside_summary(root).to_csv(
        root / "ai_intervention_4b_lakeside_summary.csv",
        index=False,
    )
    build_ai_intervention_4c_sofa_summary(root).to_csv(
        root / "ai_intervention_4c_sofa_summary.csv",
        index=False,
    )
    build_ai_intervention_4d_snowfall_summary(root).to_csv(
        root / "ai_intervention_4d_snowfall_summary.csv",
        index=False,
    )
    build_ai_intervention_4d3_carryover_summary(root).to_csv(
        root / "ai_intervention_4d3_carryover_summary.csv",
        index=False,
    )
    build_ai_intervention_4d3_carryover_summary(root).to_csv(
        root / "ai_intervention_4d4_carryover_summary.csv",
        index=False,
    )
    build_ai_intervention_4d3_carryover_summary(root).to_csv(
        root / "ai_intervention_4d5_carryover_summary.csv",
        index=False,
    )
    build_ai_intervention_4d3_carryover_summary(root).to_csv(
        root / "ai_intervention_4d6_carryover_summary.csv",
        index=False,
    )
    build_ai_intervention_4d3_carryover_summary(root).to_csv(
        root / "ai_intervention_4e_carryover_summary.csv",
        index=False,
    )
    build_ai_intervention_4e_port_detector_summary(root).to_csv(
        root / "ai_intervention_4e_port_detector_summary.csv",
        index=False,
    )
    build_ai_intervention_4e2_port_detector_summary(root).to_csv(
        root / "ai_intervention_4e2_port_detector_summary.csv",
        index=False,
    )
    build_ai_intervention_4e2_port_detector_rows(root).to_csv(
        root / "ai_intervention_4e2_port_detector_rows.csv",
        index=False,
    )
    build_ai_intervention_4e3_port_detector_summary(root).to_csv(
        root / "ai_intervention_4e3_port_detector_summary.csv",
        index=False,
    )
    build_ai_intervention_4e3_port_detector_rows(root).to_csv(
        root / "ai_intervention_4e3_port_detector_rows.csv",
        index=False,
    )
    build_ai_intervention_4e4_port_detector_summary(root).to_csv(
        root / "ai_intervention_4e4_port_detector_summary.csv",
        index=False,
    )
    build_ai_intervention_4e4_port_detector_rows(root).to_csv(
        root / "ai_intervention_4e4_port_detector_rows.csv",
        index=False,
    )
    build_ai_intervention_4e5_port_parking_summary(root).to_csv(
        root / "ai_intervention_4e5_port_parking_summary.csv",
        index=False,
    )
    build_ai_intervention_4e5_parking_rows(root).to_csv(
        root / "ai_intervention_4e5_parking_rows.csv",
        index=False,
    )
    build_ai_intervention_4e6_port_parking_rebase_summary(root).to_csv(
        root / "ai_intervention_4e6_port_parking_rebase_summary.csv",
        index=False,
    )
    build_ai_intervention_4e6_port_parking_rebase_rows(root).to_csv(
        root / "ai_intervention_4e6_port_parking_rebase_rows.csv",
        index=False,
    )
    build_ai_intervention_2o_tunnel_exit_summary(root).to_csv(
        root / "ai_intervention_2o_tunnel_exit_summary.csv",
        index=False,
    )

    print(f"[DONE] wrote guarded comparison files under {root}")


if __name__ == "__main__":
    main()
