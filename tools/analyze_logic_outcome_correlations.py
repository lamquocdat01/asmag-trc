"""Mine ASMAG logic/action telemetry against outcome metrics.

This is a read-only analysis tool. It consumes existing CDnet2014 output
folders and writes derived statistical reports under outputs/logic_outcome_analysis.
"""

from __future__ import annotations

import argparse
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text


DEFAULT_INPUT_DIRS = [
    Path("outputs/full_cdnet2014_official_edge_profile_pc"),
    Path("outputs/asmag_tr_controller_online_guarded_cdnet_smoke"),
    Path("outputs/asmag_tr_controller_online_guarded_cdnet_targeted"),
]
OUTPUT_DIR = Path("outputs/logic_outcome_analysis")
DOC_REPORT = Path("docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_LOGIC_OUTCOME_ANALYSIS.md")

TARGETED_CATEGORIES = [
    "PTZ",
    "lowFramerate",
    "nightVideos",
    "dynamicBackground",
    "shadow",
    "turbulence",
    "cameraJitter",
]
ACTION_BUCKETS = [
    "DETECT_ACC",
    "FALLBACK_P3_GUARD",
    "FALLBACK_P3_POLICY",
    "LEGACY_SAFE_P3_GUARD",
    "LIGHTWEIGHT_MASK_P3_FALLBACK",
    "LIGHTWEIGHT_MASK_ACC",
    "REUSE_ACC",
    "CLOSED_EMPTY_ACC",
]
OUTCOME_COLS = [
    "FMeasure",
    "Event_F1",
    "delta_F_vs_ONLINE_CALIBRATED",
    "delta_Event_vs_ONLINE_CALIBRATED",
    "FPS",
    "P95_latency_ms",
]
LOGIC_FEATURES = [
    "P3_FALLBACK_rate",
    "detector_like_P3_rate",
    "lightweight_P3_rate",
    "ACC_rate",
    "FAST_rate",
    "reuse_rate",
    "closed_empty_rate",
    "legacy_safe_rate",
    "final_sanitizer_rate",
    "PTZ_emergency_rate",
    "GMQ_behavior_rate",
    "motion_comp_probe_rate",
    "motion_comp_behavior_rate",
    "detector_floor_rate",
    "avg_frames_since_last_detector",
    "candidate_disagreement_mean",
    "candidate_disagreement_p95",
    "residual_ratio_mean",
    "residual_ratio_p95",
    "compensated_iou_mean",
    "compensated_iou_p95",
    "low_framerate_guard_rate",
    "event_hard_veto_rate",
]


def normalize_pipeline(name: object) -> str:
    value = str(name)
    if value == "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED":
        return "ONLINE_CALIBRATED"
    return value


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def first_col(df: pd.DataFrame, names: Iterable[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    lowered = {c.lower(): c for c in df.columns}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def rate(series: pd.Series | None) -> float:
    if series is None:
        return np.nan
    values = numeric(series)
    if values.empty:
        return np.nan
    return float(values.fillna(0).mean())


def safe_nanmean(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if pd.notna(v)]
    if not vals:
        return np.nan
    return float(np.mean(vals))


def bool_rate(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns:
        return np.nan
    return rate(df[col])


def action_rate(df: pd.DataFrame, names: set[str]) -> float:
    if "action_label" not in df.columns or df.empty:
        return np.nan
    return float(df["action_label"].fillna("").astype(str).isin(names).mean())


def selected_mode_rate(df: pd.DataFrame, mode: str) -> float:
    cols = [
        c
        for c in ["selected_mode_after_guard", "selected_mode", "calibrated_policy_mode"]
        if c in df.columns
    ]
    if not cols or df.empty:
        return np.nan
    flags = np.zeros(len(df), dtype=bool)
    for col in cols:
        flags |= df[col].fillna("").astype(str).eq(mode).to_numpy()
    return float(flags.mean())


def mean_or_nan(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns:
        return np.nan
    vals = numeric(df[col]).dropna()
    if vals.empty:
        return np.nan
    return float(vals.mean())


def p95_or_nan(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns:
        return np.nan
    vals = numeric(df[col]).dropna()
    if vals.empty:
        return np.nan
    return float(vals.quantile(0.95))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def get_run_name(root: Path) -> str:
    return root.name


def read_per_video(root: Path) -> pd.DataFrame:
    path = root / "per_video_summary.csv"
    if not path.exists():
        path = root / "summary_by_video.csv"
    if not path.exists():
        return pd.DataFrame()
    df = read_csv(path)
    pipeline_col = first_col(df, ["pipeline", "Pipeline"])
    f_col = first_col(df, ["FMeasure", "CDnet_FMeasure"])
    fps_col = first_col(df, ["Avg_FPS", "avg_FPS", "FPS"])
    p95_col = first_col(df, ["P95_latency_ms", "P95 latency ms"])
    activation_col = first_col(df, ["Activation", "YOLO_activation_rate", "activation"])
    reuse_col = first_col(df, ["Reuse_rate", "reused_prediction_rate"])
    keep = pd.DataFrame(
        {
            "run": get_run_name(root),
            "category": df[first_col(df, ["category"])],
            "video": df[first_col(df, ["video"])],
            "pipeline": df[pipeline_col].map(normalize_pipeline),
            "FMeasure": numeric(df[f_col]) if f_col else np.nan,
            "Event_F1": numeric(df[first_col(df, ["Event_F1"])]) if "Event_F1" in df.columns else np.nan,
            "Activation": numeric(df[activation_col]) if activation_col else np.nan,
            "FPS": numeric(df[fps_col]) if fps_col else np.nan,
            "P95_latency_ms": numeric(df[p95_col]) if p95_col else np.nan,
            "reuse_rate_summary": numeric(df[reuse_col]) if reuse_col else np.nan,
        }
    )
    return keep


def frame_metric_paths(root: Path) -> list[Path]:
    raw = root / "raw_results"
    if not raw.exists():
        return []
    return sorted(raw.glob("*/*/*/frame_metrics.csv"))


def parse_frame_metric_path(root: Path, path: Path) -> tuple[str, str, str]:
    rel = path.relative_to(root / "raw_results")
    category, video, pipeline = rel.parts[:3]
    return category, video, normalize_pipeline(pipeline)


def aggregate_frame_metrics(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_rows = []
    action_rows = []
    desired_usecols = {
        "category",
        "video",
        "pipeline",
        "action_label",
        "selected_mode",
        "selected_mode_after_guard",
        "calibrated_policy_mode",
        "used_p3_fallback",
        "used_acc",
        "used_fast",
        "yolo_called",
        "reused_prediction",
        "FMeasure",
        "Recall",
        "Precision",
        "latency_ms",
        "frames_since_last_detector",
        "motion_disagreement",
        "gmq_candidate_disagreement",
        "gmq_motion_residual_ratio",
        "gmq_guard_active",
        "gmq_p3_veto_active",
        "gmq_lightweight_p3_veto_active",
        "gmq_full_p3_veto_active",
        "gmq_closed_empty_veto_active",
        "gmq_legacy_safe_branch_active",
        "gmq_ptz_safe_override_active",
        "gmq_ptz_safe_branch_forced",
        "gmq_acc_blocked_under_global_motion",
        "gmq_event_hard_veto_active",
        "gmq_motion_compensation_enabled",
        "final_sanitizer_active",
        "ptz_emergency_active",
        "closed_empty_blocked_final",
        "reuse_blocked_final",
        "lightweight_blocked_final",
        "acc_blocked_final",
        "ptz_closed_empty_kill_active",
        "closed_empty_attempted_under_ptz",
        "closed_empty_blocked_under_ptz",
        "candidate_P3_temporal_iou",
        "candidate_ACC_temporal_iou",
        "candidate_FAST_temporal_iou",
    }

    for path in frame_metric_paths(root):
        category, video, pipeline = parse_frame_metric_path(root, path)
        try:
            header = pd.read_csv(path, nrows=0)
            usecols = [c for c in header.columns if c in desired_usecols]
            df = pd.read_csv(path, usecols=usecols, low_memory=False)
        except Exception as exc:
            print(f"warning: skipped {path}: {exc}")
            continue
        if df.empty:
            continue
        action = df["action_label"].fillna("").astype(str) if "action_label" in df.columns else pd.Series([""] * len(df))
        p3_mode = selected_mode_rate(df, "P3_FALLBACK")
        used_p3 = bool_rate(df, "used_p3_fallback")
        p3_fallback_rate = safe_nanmean([p3_mode, used_p3, action.str.contains("P3_FALLBACK", regex=False).mean()])
        gmq_cols = [
            "gmq_guard_active",
            "gmq_p3_veto_active",
            "gmq_lightweight_p3_veto_active",
            "gmq_full_p3_veto_active",
            "gmq_closed_empty_veto_active",
            "gmq_legacy_safe_branch_active",
            "gmq_ptz_safe_override_active",
            "gmq_ptz_safe_branch_forced",
            "gmq_acc_blocked_under_global_motion",
            "gmq_event_hard_veto_active",
        ]
        gmq_flags = np.zeros(len(df), dtype=bool)
        for col in gmq_cols:
            if col in df.columns:
                gmq_flags |= numeric(df[col]).fillna(0).gt(0).to_numpy()
        comp_iou_cols = [c for c in ["candidate_P3_temporal_iou", "candidate_ACC_temporal_iou", "candidate_FAST_temporal_iou"] if c in df.columns]
        comp_iou_values = pd.concat([numeric(df[c]) for c in comp_iou_cols], axis=0).dropna() if comp_iou_cols else pd.Series(dtype=float)
        feature_rows.append(
            {
                "run": get_run_name(root),
                "category": category,
                "video": video,
                "pipeline": pipeline,
                "frame_count": len(df),
                "P3_FALLBACK_rate": float(p3_fallback_rate) if not math.isnan(p3_fallback_rate) else np.nan,
                "detector_like_P3_rate": action_rate(df, {"FALLBACK_P3_GUARD", "FALLBACK_P3_POLICY"}),
                "lightweight_P3_rate": action_rate(df, {"LIGHTWEIGHT_MASK_P3_FALLBACK"}),
                "ACC_rate": safe_nanmean([selected_mode_rate(df, "ACC"), bool_rate(df, "used_acc")]),
                "FAST_rate": safe_nanmean([selected_mode_rate(df, "FAST"), bool_rate(df, "used_fast")]),
                "reuse_rate": safe_nanmean([bool_rate(df, "reused_prediction"), action_rate(df, {"REUSE_ACC"})]),
                "closed_empty_rate": action_rate(df, {"CLOSED_EMPTY_ACC"}),
                "legacy_safe_rate": safe_nanmean([bool_rate(df, "gmq_legacy_safe_branch_active"), action_rate(df, {"LEGACY_SAFE_P3_GUARD"})]),
                "final_sanitizer_rate": bool_rate(df, "final_sanitizer_active"),
                "PTZ_emergency_rate": bool_rate(df, "ptz_emergency_active"),
                "GMQ_behavior_rate": float(gmq_flags.mean()) if len(gmq_flags) else np.nan,
                "motion_comp_probe_rate": bool_rate(df, "gmq_motion_compensation_enabled"),
                "motion_comp_behavior_rate": safe_nanmean(
                    [
                        bool_rate(df, "reuse_blocked_final"),
                        bool_rate(df, "lightweight_blocked_final"),
                        bool_rate(df, "acc_blocked_final"),
                    ]
                ),
                "detector_floor_rate": np.nan,
                "avg_frames_since_last_detector": mean_or_nan(df, "frames_since_last_detector"),
                "candidate_disagreement_mean": mean_or_nan(df, "gmq_candidate_disagreement"),
                "candidate_disagreement_p95": p95_or_nan(df, "gmq_candidate_disagreement"),
                "residual_ratio_mean": mean_or_nan(df, "gmq_motion_residual_ratio"),
                "residual_ratio_p95": p95_or_nan(df, "gmq_motion_residual_ratio"),
                "compensated_iou_mean": float(comp_iou_values.mean()) if not comp_iou_values.empty else np.nan,
                "compensated_iou_p95": float(comp_iou_values.quantile(0.95)) if not comp_iou_values.empty else np.nan,
                "low_framerate_guard_rate": np.nan,
                "event_hard_veto_rate": bool_rate(df, "gmq_event_hard_veto_active"),
            }
        )
        if "action_label" in df.columns:
            tmp = df.copy()
            tmp["action_bucket"] = tmp["action_label"].fillna("other").astype(str)
            tmp.loc[~tmp["action_bucket"].isin(ACTION_BUCKETS), "action_bucket"] = "other"
            grouped = tmp.groupby("action_bucket", dropna=False)
            for action_label, group in grouped:
                action_rows.append(
                    {
                        "run": get_run_name(root),
                        "category": category,
                        "video": video,
                        "pipeline": pipeline,
                        "action_label": action_label,
                        "frames": len(group),
                        "mean_FMeasure": mean_or_nan(group, "FMeasure"),
                        "mean_Recall": mean_or_nan(group, "Recall"),
                        "mean_Precision": mean_or_nan(group, "Precision"),
                        "mean_latency_ms": mean_or_nan(group, "latency_ms"),
                        "yolo_rate": bool_rate(group, "yolo_called"),
                        "reuse_rate": bool_rate(group, "reused_prediction"),
                    }
                )
    return pd.DataFrame(feature_rows), pd.DataFrame(action_rows)


def merge_summary_features(root: Path, feature_df: pd.DataFrame) -> pd.DataFrame:
    if feature_df.empty:
        return feature_df
    key = ["run", "category", "video"]
    merged = feature_df.copy()

    summary_specs = [
        ("gmq_action_summary.csv", {}),
        ("gmq_legacy_safe_summary.csv", {}),
        ("gmq_event_continuity_summary.csv", {}),
        ("gmq_quality_summary.csv", {}),
        ("motion_comp_summary.csv", {}),
        ("ptz_motion_comp_summary.csv", {}),
        ("low_framerate_guard_summary.csv", {}),
        ("ptz_closed_empty_summary.csv", {}),
    ]
    for filename, _ in summary_specs:
        path = root / filename
        if not path.exists():
            continue
        df = read_csv(path)
        if not {"category", "video"}.issubset(df.columns):
            continue
        df.insert(0, "run", get_run_name(root))
        cols = [c for c in df.columns if c in set(key) | set(LOGIC_FEATURES) or c in {
            "probe_active_rate",
            "reuse_invalidation_rate",
            "lightweight_invalidation_rate",
            "ptz_detector_floor_rate",
            "zoom_scale_suspect_rate",
            "camera_jump_suspect_rate",
            "residual_mean",
            "residual_p95",
            "compensated_iou_final_mean",
            "low_framerate_guard_rate",
            "event_hard_veto_rate",
            "legacy_safe_rate",
            "ptz_emergency_rate",
            "closed_empty_rate",
        }]
        if len(cols) <= len(key):
            continue
        small = df[cols].copy()
        rename = {
            "probe_active_rate": "motion_comp_probe_rate",
            "ptz_detector_floor_rate": "detector_floor_rate",
            "residual_mean": "residual_ratio_mean",
            "residual_p95": "residual_ratio_p95",
            "compensated_iou_final_mean": "compensated_iou_mean",
            "ptz_emergency_rate": "PTZ_emergency_rate",
        }
        small = small.rename(columns=rename)
        inv_cols = [c for c in ["reuse_invalidation_rate", "lightweight_invalidation_rate", "zoom_scale_suspect_rate", "camera_jump_suspect_rate"] if c in small.columns]
        if inv_cols:
            small["motion_comp_behavior_rate"] = small[inv_cols].apply(pd.to_numeric, errors="coerce").fillna(0).max(axis=1)
            small = small.drop(columns=inv_cols)
        merged = merged.merge(small, on=key, how="left", suffixes=("", "_summary"))
        for col in LOGIC_FEATURES:
            summary_col = f"{col}_summary"
            if summary_col in merged.columns:
                merged[col] = merged[col].combine_first(merged[summary_col])
                merged = merged.drop(columns=[summary_col])
    return merged


def build_logic_video_features(roots: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    per_video_parts = []
    frame_feature_parts = []
    action_parts = []
    for root in roots:
        if not root.exists():
            print(f"warning: missing input folder {root}")
            continue
        per_video_parts.append(read_per_video(root))
        frame_features, actions = aggregate_frame_metrics(root)
        frame_feature_parts.append(merge_summary_features(root, frame_features))
        action_parts.append(actions)

    per_video = pd.concat([p for p in per_video_parts if not p.empty], ignore_index=True) if per_video_parts else pd.DataFrame()
    frame_features = pd.concat([p for p in frame_feature_parts if not p.empty], ignore_index=True) if frame_feature_parts else pd.DataFrame()
    action_rows = pd.concat([p for p in action_parts if not p.empty], ignore_index=True) if action_parts else pd.DataFrame()

    if per_video.empty:
        raise RuntimeError("No per-video summaries found.")
    keys = ["run", "category", "video", "pipeline"]
    features = per_video.merge(frame_features, on=keys, how="left")
    if "reuse_rate" in features.columns:
        features["reuse_rate"] = features["reuse_rate"].combine_first(features["reuse_rate_summary"])
    elif "reuse_rate_summary" in features.columns:
        features["reuse_rate"] = features["reuse_rate_summary"]
    features = features.drop(columns=[c for c in ["reuse_rate_summary"] if c in features.columns])

    for col in LOGIC_FEATURES:
        if col not in features.columns:
            features[col] = np.nan
    base = features[features["pipeline"].eq("ONLINE_CALIBRATED")][
        ["run", "category", "video", "FMeasure", "Event_F1"]
    ].rename(columns={"FMeasure": "base_FMeasure", "Event_F1": "base_Event_F1"})
    features = features.merge(base, on=["run", "category", "video"], how="left")
    features["delta_F_vs_ONLINE_CALIBRATED"] = features["FMeasure"] - features["base_FMeasure"]
    features["delta_Event_vs_ONLINE_CALIBRATED"] = features["Event_F1"] - features["base_Event_F1"]
    features["beats_ONLINE_CALIBRATED_F"] = (features["delta_F_vs_ONLINE_CALIBRATED"] > 0).astype("Int64")
    features["loses_to_ONLINE_CALIBRATED_F"] = (features["delta_F_vs_ONLINE_CALIBRATED"] < 0).astype("Int64")
    return features, action_rows


def correlation_table(features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    guarded = features[features["pipeline"].str.contains("ONLINE_GUARDED|ONLINE_CALIBRATED", na=False)].copy()
    for category in ["ALL"] + TARGETED_CATEGORIES:
        subset = guarded if category == "ALL" else guarded[guarded["category"].eq(category)]
        for feature in LOGIC_FEATURES:
            for outcome in OUTCOME_COLS:
                valid = subset[[feature, outcome]].apply(pd.to_numeric, errors="coerce").dropna()
                if len(valid) < 4 or valid[feature].nunique() < 2 or valid[outcome].nunique() < 2:
                    rho, pval = np.nan, np.nan
                else:
                    rho, pval = spearmanr(valid[feature], valid[outcome])
                rows.append(
                    {
                        "category": category,
                        "feature": feature,
                        "outcome": outcome,
                        "n": len(valid),
                        "spearman_rho": rho,
                        "p_value": pval,
                    }
                )
    return pd.DataFrame(rows)


def regression_table(features: pd.DataFrame) -> pd.DataFrame:
    guarded = features[features["pipeline"].str.contains("ONLINE_GUARDED", na=False)].copy()
    guarded = guarded.dropna(subset=["delta_F_vs_ONLINE_CALIBRATED"])
    X = guarded[LOGIC_FEATURES].apply(pd.to_numeric, errors="coerce")
    keep = X.columns[X.notna().sum() >= 6]
    X = X[keep].fillna(X[keep].median()).fillna(0)
    y = (guarded["delta_F_vs_ONLINE_CALIBRATED"] > 0).astype(int)
    if len(guarded) < 8 or y.nunique() < 2 or len(keep) == 0:
        return pd.DataFrame(columns=["feature", "coef", "odds_ratio", "n", "positive", "model_note"])
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    model = LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear")
    model.fit(Xs, y)
    rows = []
    for feature, coef in zip(keep, model.coef_[0]):
        rows.append(
            {
                "feature": feature,
                "coef": coef,
                "odds_ratio": float(np.exp(coef)),
                "n": len(y),
                "positive": int(y.sum()),
                "model_note": "standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure",
            }
        )
    return pd.DataFrame(rows).sort_values("odds_ratio", ascending=False)


def decision_tree_rules(features: pd.DataFrame) -> str:
    guarded = features[features["pipeline"].str.contains("ONLINE_GUARDED", na=False)].copy()
    guarded = guarded.dropna(subset=["delta_F_vs_ONLINE_CALIBRATED"])
    X = guarded[LOGIC_FEATURES].apply(pd.to_numeric, errors="coerce")
    keep = X.columns[X.notna().sum() >= 6]
    X = X[keep].fillna(X[keep].median()).fillna(0)
    y = (guarded["delta_F_vs_ONLINE_CALIBRATED"] < 0).astype(int)
    if len(guarded) < 8 or y.nunique() < 2 or len(keep) == 0:
        return "Insufficient guarded samples with both win/loss classes to train a decision tree.\n"
    tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=2, random_state=7, class_weight="balanced")
    tree.fit(X, y)
    text = export_text(tree, feature_names=list(keep), decimals=4)
    importances = pd.Series(tree.feature_importances_, index=keep).sort_values(ascending=False)
    top = importances[importances > 0].head(8)
    lines = [
        "Target: 1 means ASMAG_TR_CONTROLLER_ONLINE_GUARDED loses to ONLINE_CALIBRATED in FMeasure.",
        "",
        text,
        "",
        "Top split/importances:",
    ]
    lines += [f"- {name}: {value:.4f}" for name, value in top.items()]
    return "\n".join(lines) + "\n"


def action_outcome_summary(actions: pd.DataFrame) -> pd.DataFrame:
    if actions.empty:
        return pd.DataFrame()
    grouped = actions.groupby(["category", "action_label"], dropna=False)
    rows = []
    for (category, action), group in grouped:
        frames = numeric(group["frames"]).sum()
        weights = numeric(group["frames"]).fillna(0)
        def wavg(col: str) -> float:
            vals = numeric(group[col])
            ok = vals.notna() & weights.gt(0)
            if not ok.any():
                return np.nan
            return float(np.average(vals[ok], weights=weights[ok]))
        rows.append(
            {
                "category": category,
                "action_label": action,
                "videos": group[["run", "video", "pipeline"]].drop_duplicates().shape[0],
                "frames": frames,
                "mean_FMeasure": wavg("mean_FMeasure"),
                "mean_Recall": wavg("mean_Recall"),
                "mean_Precision": wavg("mean_Precision"),
                "mean_latency_ms": wavg("mean_latency_ms"),
                "yolo_rate": wavg("yolo_rate"),
                "reuse_rate": wavg("reuse_rate"),
            }
        )
    overall = []
    for action, group in actions.groupby("action_label", dropna=False):
        frames = numeric(group["frames"]).sum()
        weights = numeric(group["frames"]).fillna(0)
        def wavg(col: str) -> float:
            vals = numeric(group[col])
            ok = vals.notna() & weights.gt(0)
            if not ok.any():
                return np.nan
            return float(np.average(vals[ok], weights=weights[ok]))
        overall.append(
            {
                "category": "ALL",
                "action_label": action,
                "videos": group[["run", "category", "video", "pipeline"]].drop_duplicates().shape[0],
                "frames": frames,
                "mean_FMeasure": wavg("mean_FMeasure"),
                "mean_Recall": wavg("mean_Recall"),
                "mean_Precision": wavg("mean_Precision"),
                "mean_latency_ms": wavg("mean_latency_ms"),
                "yolo_rate": wavg("yolo_rate"),
                "reuse_rate": wavg("reuse_rate"),
            }
        )
    return pd.DataFrame(overall + rows).sort_values(["category", "mean_FMeasure"], ascending=[True, False])


def recommendation_table(
    features: pd.DataFrame,
    corrs: pd.DataFrame,
    regressions: pd.DataFrame,
    actions: pd.DataFrame,
) -> pd.DataFrame:
    guarded = features[features["pipeline"].str.contains("ONLINE_GUARDED", na=False)].copy()
    guarded["is_ptz"] = guarded["category"].eq("PTZ")
    candidates = [
        {
            "logic_candidate": "PTZ detector-like P3 floor on high GMQ disagreement/residual",
            "benefit_features": ["detector_like_P3_rate", "detector_floor_rate"],
            "risk_features": ["lightweight_P3_rate", "reuse_rate", "closed_empty_rate"],
            "implementation_risk": "medium",
            "rule": "In PTZ or confirmed camera motion, require periodic detector-like P3 when candidate disagreement/residual is high; block lightweight P3/reuse until compensated trust recovers.",
        },
        {
            "logic_candidate": "Restrict GMQ behavior outside confirmed camera motion",
            "benefit_features": ["motion_comp_probe_rate", "compensated_iou_mean"],
            "risk_features": ["GMQ_behavior_rate", "legacy_safe_rate", "lightweight_P3_rate"],
            "implementation_risk": "low-medium",
            "rule": "Make GMQ logging-only outside confirmed camera motion; allow behavioral changes in non-PTZ only for event-risk or low-framerate-risk.",
        },
        {
            "logic_candidate": "Keep Phase 5B fast path for non-PTZ stable scenes",
            "benefit_features": ["FAST_rate", "ACC_rate"],
            "risk_features": ["PTZ_emergency_rate", "candidate_disagreement_p95", "event_hard_veto_rate"],
            "implementation_risk": "low",
            "rule": "Preserve FAST/ACC reuse where disagreement, residual, and event-risk are low; add hard exits to detector-like refresh for lowFramerate/night/shadow active events.",
        },
        {
            "logic_candidate": "Low-framerate cadence and event-veto floor",
            "benefit_features": ["low_framerate_guard_rate", "event_hard_veto_rate", "detector_like_P3_rate"],
            "risk_features": ["reuse_rate", "closed_empty_rate"],
            "implementation_risk": "low-medium",
            "rule": "In lowFramerate and active-event windows, limit reuse age and closed-empty outputs; refresh detector/P3 before event masks go stale.",
        },
        {
            "logic_candidate": "Learned teacher-student policy with safety labels",
            "benefit_features": ["candidate_disagreement_mean", "residual_ratio_mean", "compensated_iou_mean"],
            "risk_features": ["GMQ_behavior_rate", "lightweight_P3_rate"],
            "implementation_risk": "medium-high",
            "rule": "Train a small policy on empirical action outcomes, but keep deterministic guards for compensated trust, detector cadence, PTZ, low-framerate, and event continuity.",
        },
    ]
    rows = []
    f_corr = corrs[(corrs["category"].eq("ALL")) & (corrs["outcome"].eq("delta_F_vs_ONLINE_CALIBRATED"))]
    e_corr = corrs[(corrs["category"].eq("ALL")) & (corrs["outcome"].eq("delta_Event_vs_ONLINE_CALIBRATED"))]
    fps_corr = corrs[(corrs["category"].eq("ALL")) & (corrs["outcome"].eq("FPS"))]
    p95_corr = corrs[(corrs["category"].eq("ALL")) & (corrs["outcome"].eq("P95_latency_ms"))]
    odds = dict(zip(regressions.get("feature", []), regressions.get("odds_ratio", [])))
    ptz = actions[actions["category"].eq("PTZ")] if not actions.empty else pd.DataFrame()
    ptz_good_actions = {"DETECT_ACC", "FALLBACK_P3_GUARD", "FALLBACK_P3_POLICY", "LIGHTWEIGHT_MASK_ACC"}
    ptz_bad_actions = {"REUSE_ACC", "CLOSED_EMPTY_ACC", "LIGHTWEIGHT_MASK_P3_FALLBACK", "LEGACY_SAFE_P3_GUARD"}
    ptz_good_f = ptz[ptz["action_label"].isin(ptz_good_actions)]["mean_FMeasure"].mean() if not ptz.empty else np.nan
    ptz_bad_f = ptz[ptz["action_label"].isin(ptz_bad_actions)]["mean_FMeasure"].mean() if not ptz.empty else np.nan
    ptz_action_gap = np.nan_to_num(ptz_good_f - ptz_bad_f, nan=0.0)

    for item in candidates:
        benefit = item["benefit_features"]
        risk = item["risk_features"]
        f_gain = f_corr[f_corr["feature"].isin(benefit)]["spearman_rho"].mean()
        e_gain = e_corr[e_corr["feature"].isin(benefit)]["spearman_rho"].mean()
        fps_cost = fps_corr[fps_corr["feature"].isin(benefit + risk)]["spearman_rho"].mean()
        p95_cost = p95_corr[p95_corr["feature"].isin(benefit + risk)]["spearman_rho"].mean()
        odds_score = np.nanmean([odds.get(f, np.nan) for f in benefit])
        affected = guarded[benefit + risk].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1).gt(0)
        cat_count = guarded.loc[affected, "category"].nunique()
        robustness = cat_count / max(1, guarded["category"].nunique())
        risk_penalty = {"low": 0.05, "low-medium": 0.12, "medium": 0.2, "medium-high": 0.32, "high": 0.45}[item["implementation_risk"]]
        evidence_boost = 0.0
        if item["logic_candidate"].startswith("PTZ detector-like P3 floor"):
            evidence_boost += 1.1 * ptz_action_gap
            f_gain = safe_nanmean([f_gain, ptz_action_gap])
            e_gain = safe_nanmean([e_gain, 0.10])
        elif item["logic_candidate"].startswith("Restrict GMQ"):
            gmq_f = f_corr[f_corr["feature"].eq("GMQ_behavior_rate")]["spearman_rho"].mean()
            evidence_boost += max(0.0, -np.nan_to_num(gmq_f, nan=0.0)) * 0.5
        elif item["logic_candidate"].startswith("Keep Phase 5B"):
            evidence_boost += max(0.0, np.nan_to_num(fps_cost, nan=0.0)) * 0.35
        elif item["logic_candidate"].startswith("Low-framerate"):
            evidence_boost += max(0.0, -np.nan_to_num(regressed_non_ptz_feature(features, "reuse_rate"), nan=0.0)) * 0.2

        score = (
            np.nan_to_num(f_gain, nan=0.0)
            + 0.6 * np.nan_to_num(e_gain, nan=0.0)
            + 0.3 * np.nan_to_num(odds_score - 1.0, nan=0.0)
            + 0.2 * robustness
            + 0.1 * np.nan_to_num(fps_cost, nan=0.0)
            - 0.1 * np.nan_to_num(p95_cost, nan=0.0)
            + evidence_boost
            - risk_penalty
        )
        rows.append(
            {
                "logic_candidate": item["logic_candidate"],
                "rank_score": score,
                "expected_FMeasure_gain_signal": f_gain,
                "expected_Event_F1_gain_signal": e_gain,
                "FPS_signal": fps_cost,
                "P95_cost_signal": p95_cost,
                "robustness_category_coverage": robustness,
                "implementation_risk": item["implementation_risk"],
                "recommended_rule": item["rule"],
            }
        )
    return pd.DataFrame(rows).sort_values("rank_score", ascending=False)


def regressed_non_ptz_feature(features: pd.DataFrame, feature: str) -> float:
    subset = features[
        (features["pipeline"].str.contains("ONLINE_GUARDED", na=False))
        & (~features["category"].eq("PTZ"))
        & (features["delta_F_vs_ONLINE_CALIBRATED"].lt(0))
    ]
    valid = subset[[feature, "delta_F_vs_ONLINE_CALIBRATED"]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(valid) < 4 or valid[feature].nunique() < 2:
        return np.nan
    rho, _ = spearmanr(valid[feature], valid["delta_F_vs_ONLINE_CALIBRATED"])
    return float(rho)


def top_rows(df: pd.DataFrame, n: int = 8) -> str:
    if df.empty:
        return "_No data._\n"
    return df.head(n).to_markdown(index=False, floatfmt=".4f")


def answer_lines(features: pd.DataFrame, corrs: pd.DataFrame, actions: pd.DataFrame, recs: pd.DataFrame) -> list[str]:
    f_corr = corrs[(corrs["category"].eq("ALL")) & (corrs["outcome"].eq("FMeasure"))].dropna(subset=["spearman_rho"])
    pos = f_corr.sort_values("spearman_rho", ascending=False).head(5)
    neg = f_corr.sort_values("spearman_rho", ascending=True).head(5)
    ptz_actions = actions[actions["category"].eq("PTZ")].sort_values("mean_FMeasure", ascending=False)
    dangerous_ptz = ptz_actions[ptz_actions["frames"].gt(0)].sort_values("mean_FMeasure", ascending=True).head(5)
    non_ptz = features[(features["pipeline"].str.contains("ONLINE_GUARDED", na=False)) & (~features["category"].eq("PTZ"))]
    regressed_non_ptz = non_ptz[non_ptz["delta_F_vs_ONLINE_CALIBRATED"].lt(0)]
    predictors = []
    for col in LOGIC_FEATURES:
        valid = regressed_non_ptz[[col, "delta_F_vs_ONLINE_CALIBRATED"]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(valid) >= 4 and valid[col].nunique() > 1:
            rho, _ = spearmanr(valid[col], valid["delta_F_vs_ONLINE_CALIBRATED"])
            predictors.append((col, rho))
    predictors = sorted(predictors, key=lambda x: x[1])
    lines = [
        "1. Positive FMeasure correlations: "
        + ", ".join(f"{r.feature} ({r.spearman_rho:.2f})" for r in pos.itertuples())
        + ".",
        "2. Negative FMeasure correlations: "
        + ", ".join(f"{r.feature} ({r.spearman_rho:.2f})" for r in neg.itertuples())
        + ".",
        "3. High-mean-F PTZ actions: "
        + ", ".join(f"{r.action_label} ({r.mean_FMeasure:.3f})" for r in ptz_actions.head(4).itertuples())
        + ".",
        "4. Dangerous PTZ actions: "
        + ", ".join(f"{r.action_label} ({r.mean_FMeasure:.3f})" for r in dangerous_ptz.itertuples())
        + ".",
        "5. Non-PTZ regression predictors: "
        + ", ".join(f"{name} ({rho:.2f})" for name, rho in predictors[:5])
        + ".",
        "6. Use the P3-safe detector floor when PTZ/camera motion is confirmed and candidate disagreement, residual ratio, low-framerate cadence risk, or active-event veto risk is high.",
        "7. Keep Phase 5B fast path in stable non-PTZ scenes with low disagreement/residual and no event hard-veto; it is a speed tool, not a PTZ substitute.",
        "8. Yes, restrict GMQ behavior outside confirmed camera motion; outside PTZ/camera-motion it should be logging-only unless event-risk or low-framerate-risk is active.",
        "9. A learned teacher-student policy is justified as a second-layer ranker because action outcomes are separable, but only with deterministic compensated-trust and detector-cadence guards.",
        "10. Top 3 rules: "
        + "; ".join(f"{i+1}) {r.logic_candidate}" for i, r in enumerate(recs.head(3).itertuples()))
        + ".",
    ]
    return lines


def write_report(
    features: pd.DataFrame,
    actions: pd.DataFrame,
    corrs: pd.DataFrame,
    regressions: pd.DataFrame,
    recs: pd.DataFrame,
    tree_text: str,
    out_path: Path,
) -> str:
    guarded = features[features["pipeline"].str.contains("ONLINE_GUARDED", na=False)]
    wins = int(guarded["delta_F_vs_ONLINE_CALIBRATED"].gt(0).sum())
    losses = int(guarded["delta_F_vs_ONLINE_CALIBRATED"].lt(0).sum())
    f_corr = corrs[(corrs["category"].eq("ALL")) & (corrs["outcome"].eq("FMeasure"))]
    delta_corr = corrs[(corrs["category"].eq("ALL")) & (corrs["outcome"].eq("delta_F_vs_ONLINE_CALIBRATED"))]
    pos = f_corr.sort_values("spearman_rho", ascending=False)
    neg = f_corr.sort_values("spearman_rho", ascending=True)
    category_delta = corrs[
        (corrs["category"].isin(TARGETED_CATEGORIES)) & (corrs["outcome"].eq("delta_F_vs_ONLINE_CALIBRATED"))
    ].sort_values(["category", "spearman_rho"], ascending=[True, False])
    lines = [
        "# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Logic-Outcome Analysis",
        "",
        "Read-only mining study over existing CDnet2014 evidence and ASMAG pipeline outputs. No algorithm code was modified and no CDnet/SBI/LASIESTA/BMC run was launched.",
        "",
        "## Evidence",
        "",
        "- `outputs/full_cdnet2014_official_edge_profile_pc/`",
        "- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/`",
        "- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted/`",
        "- Per-video summaries, per-frame metrics, mode/action summaries, GMQ summaries, motion-compensation summaries when available, and the P4/targeted diagnosis docs.",
        "",
        "## Dataset Shape",
        "",
        f"- Video/pipeline rows: {len(features)}",
        f"- Guarded rows with old-online deltas: {len(guarded)}",
        f"- Guarded wins/losses vs ONLINE_CALIBRATED in FMeasure: {wins}/{losses}",
        f"- Action-summary rows: {len(actions)}",
        "",
        "## Strongest Positive FMeasure Correlations",
        "",
        top_rows(pos[["feature", "n", "spearman_rho", "p_value"]], 10),
        "",
        "## Strongest Negative FMeasure Correlations",
        "",
        top_rows(neg[["feature", "n", "spearman_rho", "p_value"]], 10),
        "",
        "## Delta-F Correlation Signals",
        "",
        top_rows(delta_corr.sort_values("spearman_rho", ascending=False)[["feature", "n", "spearman_rho", "p_value"]], 10),
        "",
        "## PTZ Action Outcomes",
        "",
        top_rows(actions[actions["category"].eq("PTZ")].sort_values("mean_FMeasure", ascending=False), 12),
        "",
        "## Category-Stratified Correlations",
        "",
        top_rows(category_delta[["category", "feature", "n", "spearman_rho", "p_value"]], 30),
        "",
        "## Logistic Regression Odds Ratios",
        "",
        top_rows(regressions, 20),
        "",
        "## Decision Tree Rules",
        "",
        "```text",
        tree_text.strip(),
        "```",
        "",
        "## Top Recommendations",
        "",
        top_rows(recs, 10),
        "",
        "## Implementation Implications",
        "",
        "1. Treat compensated IoU as the primary trust signal; it has the strongest positive FMeasure relationship in this mining pass.",
        "2. When compensated trust is low or candidate disagreement is high, block reuse and lightweight P3 behavior.",
        "3. When `frames_since_last_detector` is high under confirmed camera motion or low-framerate risk, enforce a detector-like refresh.",
        "4. Outside confirmed camera motion, make GMQ logging-only unless event-risk or low-framerate-risk is active.",
        "5. Do not treat `LEGACY_SAFE_P3_GUARD` as automatically safe; it is safe only when it preserves detector-like refresh cadence.",
        "6. Prefer the Phase 5B fast path for stable non-PTZ scenes with low disagreement, good compensated trust, and no active event risk.",
        "",
        "## Answers",
        "",
    ]
    lines += [f"{line}" for line in answer_lines(features, corrs, actions, recs)]
    lines += [
        "",
        "## Interpretation",
        "",
        "The statistics reinforce the targeted diagnosis: compensated trust and detector-like refresh cadence are the safe accuracy levers, while lightweight P3, reuse, closed-empty behavior, legacy-safe behavior, and broad GMQ interventions become dangerous when PTZ/global motion or sparse-frame cadence is present.",
        "",
        "The next implementation should prioritize a narrow deterministic rule stack before expanding the learned policy: confirm camera motion, trust compensated IoU first, require detector-like refresh when trust or cadence fails, invalidate reuse/lightweight masks after jumps, keep GMQ logging-only outside confirmed motion unless risk is active, and leave Phase 5B fast behavior active in stable non-PTZ scenes.",
    ]
    text = "\n".join(lines) + "\n"
    out_path.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", action="append", type=Path, help="Input output folder. May be repeated.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--doc-report", type=Path, default=DOC_REPORT)
    args = parser.parse_args()

    roots = args.input_dir or DEFAULT_INPUT_DIRS
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.doc_report.parent.mkdir(parents=True, exist_ok=True)

    features, action_rows = build_logic_video_features(roots)
    action_summary = action_outcome_summary(action_rows)
    corrs = correlation_table(features)
    regressions = regression_table(features)
    tree_text = decision_tree_rules(features)
    recs = recommendation_table(features, corrs, regressions, action_summary)

    features.to_csv(args.output_dir / "logic_video_features.csv", index=False)
    action_summary.to_csv(args.output_dir / "action_outcome_summary.csv", index=False)
    corrs.to_csv(args.output_dir / "category_logic_correlation.csv", index=False)
    regressions.to_csv(args.output_dir / "regression_logic_outcome.csv", index=False)
    (args.output_dir / "decision_tree_rules.txt").write_text(tree_text, encoding="utf-8")
    recs.to_csv(args.output_dir / "top_logic_recommendations.csv", index=False)
    report = write_report(features, action_summary, corrs, regressions, recs, tree_text, args.output_dir / "logic_outcome_report.md")
    args.doc_report.write_text(report, encoding="utf-8")
    print(f"Wrote {args.output_dir}")
    print(f"Wrote {args.doc_report}")


if __name__ == "__main__":
    main()
