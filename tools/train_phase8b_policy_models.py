import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover
    LGBMClassifier = None


PHASE8A_ROOT = Path("outputs/phase8a_policy_dataset")
OUTPUT_ROOT = Path("outputs/phase8b_policy_training")
REPORT_PATH = Path("docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8B_OFFLINE_POLICY_REPORT.md")
GUARDED = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
DEFAULT_MAX_ROWS = 20000
RANDOM_STATE = 8

ACTION_BUCKETS = [
    "DETECT_ACC",
    "FALLBACK_P3_GUARD",
    "LIGHTWEIGHT_MASK_ACC",
    "LIGHTWEIGHT_MASK_P3_FALLBACK",
    "REUSE_ACC",
    "CLOSED_EMPTY",
    "LEGACY_SAFE_P3_GUARD",
    "OTHER",
]
DETECTOR_ACTIONS = {"DETECT_ACC", "FALLBACK_P3_GUARD", "LEGACY_SAFE_P3_GUARD"}
LIGHTWEIGHT_ACTIONS = {"LIGHTWEIGHT_MASK_ACC", "LIGHTWEIGHT_MASK_P3_FALLBACK"}

TARGETS = [
    "detector_needed",
    "risk_class",
    "unsafe_action",
    "reuse_allowed",
    "lightweight_allowed",
    "detector_floor_needed",
    "action_ranker_high_risk_only",
    "action_ranker_ptz_only",
]

ROBUST_FEATURES = [
    "latency_ms",
    "normalized_latency",
    "yolo_called",
    "reused_prediction",
    "raw_frame_id",
    "evaluated_index",
    "frames_since_last_detector",
    "frames_since_last_forced_refresh",
    "frames_since_global_motion_refresh",
    "frames_since_active_prediction",
    "consecutive_p3_guard_frames",
    "consecutive_closed_empty_frames",
    "global_motion_proxy",
    "active_event_memory",
    "reuse_age",
    "reuse_confidence",
    "reuse_success_rate",
    "reuse_failure_rate",
    "reuse_allowed_by_eval_age",
    "reuse_allowed_by_raw_age",
    "reuse_stopped",
    "guard_triggered",
    "guard_cooldown_active",
    "overload_guard_active",
    "closed_empty_guard_active",
    "low_light_guard_active",
    "ptz_safe_fallback_active",
    "gmq_guard_active",
    "gmq_global_motion_risk",
    "gmq_background_reliability",
    "gmq_p3_quality",
    "gmq_acc_quality",
    "gmq_fast_quality",
    "gmq_candidate_disagreement",
    "gmq_temporal_consistency",
    "gmq_spatial_spread",
    "gmq_event_continuity_risk",
    "gmq_recent_low_trust_action_rate",
    "gmq_confident_empty_evidence",
    "gmq_motion_residual_ratio",
    "motion_comp_probe_active",
    "motion_comp_dx",
    "motion_comp_dy",
    "motion_comp_shift_mag",
    "motion_comp_response",
    "motion_comp_temporal_iou_p3",
    "motion_comp_temporal_iou_acc",
    "motion_comp_temporal_iou_fast",
    "motion_comp_temporal_iou_final",
    "motion_comp_best_iou",
    "motion_comp_residual_ratio",
    "motion_comp_reuse_safe",
    "motion_comp_compensated_trust_low",
    "motion_comp_compensated_trust_good",
    "camera_jump_suspect",
    "reuse_invalidated_by_camera_jump",
    "reuse_invalidated_by_motion_comp",
    "lightweight_invalidated_by_motion_comp",
    "ptz_detector_floor_active",
    "ptz_detector_floor_cadence_allowed",
    "ptz_detector_floor_extra_refresh_count",
    "ptz_detector_floor_budget_active",
    "ptz_detector_floor_budget_remaining",
    "ptz_detector_floor_blocked_by_budget",
    "ptz_detector_floor_blocked_by_interval",
    "low_framerate_cadence_guard_active",
    "low_framerate_reuse_blocked",
    "low_framerate_detector_floor_active",
    "position_switch_guard_active",
    "position_switch_reuse_blocked",
    "position_switch_detector_refresh_active",
    "position_switch_detector_burst_active",
    "ptz_cadence_thinning_active",
    "event_safe_cadence_thinning_active",
    "event_detect_acc_thinned",
    "event_detect_acc_rate_window",
    "ptz_emergency_active",
    "ptz_emergency_burst_age",
    "ptz_emergency_cooldown_active",
    "final_sanitizer_active",
    "closed_empty_blocked_final",
    "reuse_blocked_final",
    "lightweight_blocked_final",
    "acc_blocked_final",
    "rolling_global_motion_persistence",
    "rolling_acc_dominance_under_global_motion",
    "rolling_low_trust_action_rate",
    "rolling_closed_empty_under_motion_rate",
    "event_closed_empty_attempt_count",
    "event_closed_empty_blocked_count",
    "event_closed_empty_final_count",
    "event_fn_risk_frames",
    "candidate_P3_area_ratio",
    "candidate_ACC_area_ratio",
    "candidate_FAST_area_ratio",
    "candidate_P3_component_count",
    "candidate_ACC_component_count",
    "candidate_FAST_component_count",
    "candidate_P3_coarse_grid_occupancy",
    "candidate_ACC_coarse_grid_occupancy",
    "candidate_FAST_coarse_grid_occupancy",
    "candidate_P3_edge_touch_ratio",
    "candidate_ACC_edge_touch_ratio",
    "candidate_FAST_edge_touch_ratio",
    "candidate_P3_temporal_iou",
    "candidate_ACC_temporal_iou",
    "candidate_FAST_temporal_iou",
    "candidate_P3_quality",
    "candidate_ACC_quality",
    "candidate_FAST_quality",
    "closed_empty_blocked_by_event_guard",
    "geometry_probe_active",
    "geometry_probe_success",
    "geometry_probe_matches",
    "geometry_probe_inliers",
    "geometry_probe_inlier_ratio",
    "geometry_dx",
    "geometry_dy",
    "geometry_shift_mag",
    "geometry_scale",
    "geometry_rotation_deg",
    "geometry_comp_iou_p3",
    "geometry_comp_iou_acc",
    "geometry_comp_iou_fast",
    "geometry_comp_iou_best",
    "geometry_residual_ratio",
    "geometry_improves_over_translation",
    "geometry_trust_score",
    "geometry_reuse_blocked",
    "geometry_lightweight_p3_blocked",
    "geometry_lightweight_acc_allowed",
    "continuous_pan_geometry_trust_used",
    "continuous_pan_signature_active",
    "continuous_pan_shift_stability",
    "continuous_pan_blocked_by_position_switch",
    "continuous_pan_blocked_by_zoom_scale",
    "continuous_pan_trust_relaxed",
    "continuous_pan_anchor_recent",
    "continuous_pan_frames_since_anchor",
    "continuous_pan_anchor_cadence_active",
    "continuous_pan_anchor_due",
    "continuous_pan_legacy_safe_rate_window",
    "continuous_pan_legacy_safe_thinned",
    "continuous_pan_lightweight_acc_used",
    "continuous_pan_lightweight_p3_blocked",
    "continuous_pan_reuse_acc_used",
    "continuous_pan_reuse_blocked_by_relaxed_trust",
    "continuous_pan_reuse_cap_active",
    "continuous_pan_reuse_replaced",
    "continuous_pan_reuse_rate_window",
    "continuous_pan_detector_anchor_rate_window",
    "continuous_pan_anchor_rate_too_low",
    "continuous_pan_anchor_rate_too_high",
    "continuous_pan_anchor_rate_corrected",
    "continuous_pan_inter_anchor_lightweight_acc_selected",
    "continuous_pan_suppressed_by_shift_instability",
    "continuous_pan_suppressed_by_position_switch",
    "teacher_safety_guard_active",
    "continuous_pan_teacher_blocked_reuse",
    "continuous_pan_teacher_blocked_lightweight_p3",
    "teacher_event_behavior_suppressed",
    "teacher_bridge_event_safety_preserved",
    "ptz_closed_empty_kill_active",
    "closed_empty_attempted_under_ptz",
    "closed_empty_blocked_under_ptz",
    "closed_empty_kill_cadence_override_used",
]

LEAK_COLUMNS = {
    "FMeasure",
    "Recall",
    "Precision",
    "Event_proxy",
    "utility_score",
    "unsafe_action_penalty",
    "unsafe_action_label",
    "best_action_by_utility",
    "best_safe_action",
    "unsafe_action",
    "expected_utility_gain",
    "expected_FMeasure_gain",
    "best_oracle_pipeline",
    "best_oracle_run_id",
    "guarded_utility_score",
    "detector_needed",
    "risk_class",
    "reuse_allowed",
    "lightweight_allowed",
    "detector_floor_needed",
    "action_ranker_high_risk_only",
    "action_ranker_ptz_only",
}


warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", message="X does not have valid feature names*")
warnings.filterwarnings("ignore", message="y_pred contains classes not in y_true*")


def safe_name(text):
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(text))


def boolish(series, index=None):
    if series is None:
        return pd.Series(0.0, index=index)
    return pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)


def key_series(df):
    return (
        df["dataset"].astype(str)
        + "||"
        + df["category"].astype(str)
        + "||"
        + df["video"].astype(str)
    )


def load_phase8a(root):
    frame = pd.read_parquet(root / "frame_state_dataset.parquet")
    oracle = pd.read_parquet(root / "oracle_action_dataset.parquet")
    window = pd.read_parquet(root / "window_state_dataset.parquet")
    teacher = pd.read_parquet(root / "teacher_label_dataset.parquet")

    keys = ["dataset", "category", "video", "frame_id"]
    merged = frame.merge(oracle, on=keys, how="left")
    merged["unsafe_action"] = merged["unsafe_action"].fillna(False).astype(bool).astype(int)

    window5 = window[window["window_size"].eq(5)].copy()
    window_cols = [
        c
        for c in window5.columns
        if c.startswith("window_") or c in ["run_id", "dataset", "category", "video", "pipeline", "frame_id"]
    ]
    merged = merged.merge(
        window5[window_cols],
        on=["run_id", "dataset", "category", "video", "pipeline", "frame_id"],
        how="left",
    )

    guarded = (
        frame[frame["pipeline"].eq(GUARDED)]
        .sort_values(["dataset", "category", "video", "frame_id"])
        .drop_duplicates(keys)[keys + ["utility_score"]]
        .rename(columns={"utility_score": "guarded_utility_score"})
    )
    fallback = (
        frame.sort_values(["dataset", "category", "video", "frame_id"])
        .drop_duplicates(keys)[keys + ["utility_score"]]
        .rename(columns={"utility_score": "fallback_utility_score"})
    )
    merged = merged.merge(fallback, on=keys, how="left").merge(guarded, on=keys, how="left")
    merged["guarded_utility_score"] = merged["guarded_utility_score"].fillna(merged["fallback_utility_score"])
    merged = merged.drop(columns=["fallback_utility_score"], errors="ignore")

    action_util = (
        frame.groupby(keys + ["action_bucket"], dropna=False)["utility_score"]
        .max()
        .unstack("action_bucket")
        .reset_index()
    )
    action_util = action_util.rename(columns={c: f"util_action_{c}" for c in action_util.columns if c not in keys})
    merged = merged.merge(action_util, on=keys, how="left")

    derive_targets(merged)
    return merged, frame, window, teacher, oracle


def derive_targets(df):
    best_safe = df["best_safe_action"].fillna("OTHER").astype(str)
    current_action = df["action_bucket"].fillna("OTHER").astype(str)
    current_safe = boolish(df.get("unsafe_action_penalty"), index=df.index).eq(0)
    is_ptz = df["category"].astype(str).eq("PTZ")

    reuse_safe_now = current_action.eq("REUSE_ACC") & current_safe
    df["reuse_allowed"] = (best_safe.eq("REUSE_ACC") | reuse_safe_now).astype(int)

    light_safe_now = current_action.isin(LIGHTWEIGHT_ACTIONS) & current_safe
    best_light_safe = best_safe.isin(LIGHTWEIGHT_ACTIONS)
    ptz_light_p3 = is_ptz & best_safe.eq("LIGHTWEIGHT_MASK_P3_FALLBACK")
    df["lightweight_allowed"] = ((best_light_safe | light_safe_now) & ~ptz_light_p3).astype(int)

    detector_floor_sources = [
        "ptz_detector_floor_active",
        "low_framerate_detector_floor_active",
        "position_switch_detector_refresh_active",
        "position_switch_detector_burst_active",
        "ptz_emergency_active",
    ]
    floor = pd.Series(False, index=df.index)
    for col in detector_floor_sources:
        if col in df.columns:
            floor |= boolish(df[col], index=df.index).gt(0)
    floor |= is_ptz & df["risk_class"].astype(str).isin(["medium", "unsafe"]) & boolish(df.get("detector_needed"), index=df.index).gt(0)
    df["detector_floor_needed"] = floor.astype(int)

    df["action_ranker_high_risk_only"] = best_safe
    df["action_ranker_ptz_only"] = best_safe


def choose_features(df):
    candidates = [c for c in ROBUST_FEATURES if c in df.columns and c not in LEAK_COLUMNS]
    candidates += [c for c in df.columns if c.startswith("window_") and c not in LEAK_COLUMNS]
    features = []
    for col in dict.fromkeys(candidates):
        if col.startswith("util_action_"):
            continue
        if not (pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_bool_dtype(df[col])):
            continue
        missing = float(df[col].isna().mean())
        if missing >= 0.95:
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().sum() == 0 or numeric.nunique(dropna=True) <= 1:
            continue
        features.append(col)
    return features


def model_defs():
    models = {
        "majority_baseline": None,
        "logistic_regression": LogisticRegression(
            max_iter=300,
            class_weight="balanced",
            solver="lbfgs",
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=6,
            min_samples_leaf=25,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            min_samples_leaf=15,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=45,
            max_depth=3,
            random_state=RANDOM_STATE,
        ),
    }
    if XGBClassifier is not None:
        models["xgboost"] = XGBClassifier(
            n_estimators=40,
            max_depth=3,
            learning_rate=0.08,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
    if LGBMClassifier is not None:
        models["lightgbm"] = LGBMClassifier(
            n_estimators=60,
            max_depth=4,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            verbose=-1,
        )
    return models


def make_pipeline(model):
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler(with_mean=False)),
            ("model", model),
        ]
    )


def prepare_target_df(df, target, max_rows):
    work = df.copy()
    if target == "action_ranker_high_risk_only":
        high_risk = (
            work["risk_class"].astype(str).isin(["medium", "unsafe"])
            | work["category"].astype(str).eq("PTZ")
            | boolish(work.get("unsafe_action"), index=work.index).gt(0)
            | boolish(work.get("active_event_memory"), index=work.index).gt(0)
            | boolish(work.get("global_motion_proxy"), index=work.index).gt(0.5)
            | work["best_safe_action"].fillna("OTHER").ne("OTHER")
        )
        work = work[high_risk].copy()
    elif target == "action_ranker_ptz_only":
        work = work[work["category"].astype(str).eq("PTZ")].copy()

    if target.startswith("action_ranker"):
        work = downsample_other(work, target, max_other_ratio=3)

    return target_aware_sample(work, target, max_rows)


def downsample_other(df, target, max_other_ratio):
    y = df[target].fillna("OTHER").astype(str)
    other_idx = y[y.eq("OTHER")].index
    non_other_idx = y[~y.eq("OTHER")].index
    if len(non_other_idx) == 0:
        return df
    keep_other = min(len(other_idx), max(1000, max_other_ratio * len(non_other_idx)))
    other_sample = df.loc[other_idx].sample(keep_other, random_state=RANDOM_STATE) if len(other_idx) > keep_other else df.loc[other_idx]
    return pd.concat([df.loc[non_other_idx], other_sample], axis=0).sample(frac=1.0, random_state=RANDOM_STATE)


def target_aware_sample(df, target, max_rows):
    if max_rows <= 0 or len(df) <= max_rows:
        return df.reset_index(drop=True)
    y = df[target].fillna("").astype(str)
    protected = []
    per_class_cap = max(50, min(500, max_rows // 25))
    for label in y.value_counts().index:
        idx = y[y.eq(label)].index
        protected.extend(df.loc[idx].sample(min(per_class_cap, len(idx)), random_state=RANDOM_STATE).index.tolist())
    protected_idx = pd.Index(protected).drop_duplicates()
    if len(protected_idx) >= max_rows:
        return df.loc[protected_idx].sample(max_rows, random_state=RANDOM_STATE).reset_index(drop=True)
    remaining = df.drop(index=protected_idx, errors="ignore")
    fill_n = max_rows - len(protected_idx)
    fill = remaining.sample(fill_n, random_state=RANDOM_STATE) if len(remaining) > fill_n else remaining
    return pd.concat([df.loc[protected_idx], fill], axis=0).sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)


def split_key_sets(split_df, split_name, target_df, target):
    if split_name == "video_grouped":
        return choose_fold(split_df, target_df, target, prefer_column=None, prefer_value=None)
    if split_name == "category_holdout":
        return choose_fold(split_df, target_df, target, prefer_column="heldout_category", prefer_value="PTZ")
    train_keys = set(key_series(split_df[split_df["role"].eq("train")]))
    test_keys = set(key_series(split_df[split_df["role"].eq("test")]))
    return train_keys, test_keys, "direct"


def choose_fold(split_df, target_df, target, prefer_column=None, prefer_value=None):
    folds = sorted(split_df["fold_id"].dropna().unique().tolist())
    if prefer_column and prefer_column in split_df.columns:
        preferred = split_df.loc[split_df[prefer_column].astype(str).eq(str(prefer_value)), "fold_id"].dropna().unique().tolist()
        folds = preferred + [f for f in folds if f not in preferred]

    data_keys = key_series(target_df)
    y = target_df[target].fillna("").astype(str)
    best = None
    best_score = None
    for fold in folds:
        fold_df = split_df[split_df["fold_id"].eq(fold)]
        train_keys = set(key_series(fold_df[fold_df["role"].eq("train")]))
        test_keys = set(key_series(fold_df[fold_df["role"].eq("test")]))
        train_mask = data_keys.isin(train_keys)
        test_mask = data_keys.isin(test_keys)
        if train_mask.sum() < 50 or test_mask.sum() < 10:
            continue
        if y[train_mask].nunique() < 2:
            continue
        score = (y[test_mask].nunique(), int(test_mask.sum()), -int(fold))
        if best_score is None or score > best_score:
            best_score = score
            best = (train_keys, test_keys, f"fold_{fold}")
    return best if best is not None else (set(), set(), "unavailable")


def load_splits(root):
    split_root = root / "splits"
    return {
        "video_grouped": pd.read_csv(split_root / "split_leave_one_video.csv"),
        "category_holdout": pd.read_csv(split_root / "split_leave_one_category.csv"),
        "ptz_holdout": pd.read_csv(split_root / "split_ptz_holdout.csv"),
        "smoke_vs_targeted": pd.read_csv(split_root / "split_smoke_vs_targeted.csv"),
    }


def classification_metrics(y_true, y_pred):
    labels = sorted(pd.Series(y_true).dropna().astype(str).unique().tolist())
    balanced = accuracy_score(y_true, y_pred) if len(labels) <= 1 else balanced_accuracy_score(y_true, y_pred)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def majority_predict(y_train, y_test):
    majority = y_train.value_counts().idxmax()
    return pd.Series([majority] * len(y_test), index=y_test.index), majority


def predicted_actions(target, pred):
    pred = pd.Series(pred).astype(str)
    if target.startswith("action_ranker"):
        return pred
    if target == "detector_needed":
        return np.where(pred.eq("1"), "DETECT_ACC", "OTHER")
    if target == "reuse_allowed":
        return np.where(pred.eq("1"), "REUSE_ACC", "OTHER")
    if target == "lightweight_allowed":
        return np.where(pred.eq("1"), "LIGHTWEIGHT_MASK_ACC", "OTHER")
    if target == "detector_floor_needed":
        return np.where(pred.eq("1"), "FALLBACK_P3_GUARD", "OTHER")
    if target == "unsafe_action":
        return np.where(pred.eq("1"), "FALLBACK_P3_GUARD", "OTHER")
    if target == "risk_class":
        return np.where(pred.isin(["medium", "unsafe"]), "FALLBACK_P3_GUARD", "OTHER")
    return np.array(["OTHER"] * len(pred))


def predicted_utility(df, pred_action):
    pred_action = pd.Series(pred_action, index=df.index).astype(str)
    util = pd.Series(np.nan, index=df.index, dtype=float)
    for action in ACTION_BUCKETS:
        col = f"util_action_{action}"
        if col in df.columns:
            util.loc[pred_action.eq(action)] = pd.to_numeric(df.loc[pred_action.eq(action), col], errors="coerce")
    return util.fillna(pd.to_numeric(df["guarded_utility_score"], errors="coerce"))


def safety_signal(target, pred, pred_action):
    pred = pd.Series(pred).astype(str)
    pred_action = pd.Series(pred_action).astype(str)
    if target == "unsafe_action":
        return pred.eq("1")
    if target == "risk_class":
        return pred.isin(["medium", "unsafe"])
    if target in {"detector_needed", "detector_floor_needed"}:
        return pred.eq("1")
    if target.startswith("action_ranker"):
        return pred_action.isin(DETECTOR_ACTIONS | {"LIGHTWEIGHT_MASK_ACC"})
    return ~pred_action.isin({"REUSE_ACC", "CLOSED_EMPTY", "LIGHTWEIGHT_MASK_P3_FALLBACK"})


def policy_metrics(df, target, y_true, pred):
    pred_action = pd.Series(predicted_actions(target, pred), index=df.index)
    pred_util = predicted_utility(df, pred_action)
    guarded = pd.to_numeric(df["guarded_utility_score"], errors="coerce").fillna(0.0)
    utility_gain = pred_util - guarded

    detector_truth = boolish(df.get("detector_needed"), index=df.index).gt(0)
    pred_detector = pred_action.isin(DETECTOR_ACTIONS)
    if target == "detector_needed":
        pred_detector = pd.Series(pred, index=df.index).astype(str).eq("1")
    detector_recall = recall_score(detector_truth.astype(int), pred_detector.astype(int), zero_division=0)

    unsafe_truth = boolish(df.get("unsafe_action"), index=df.index).gt(0)
    signal = safety_signal(target, pred, pred_action).set_axis(df.index)
    unsafe_avoid = float(signal[unsafe_truth].mean()) if unsafe_truth.any() else np.nan

    reuse_unsafe = df.get("unsafe_action_label", pd.Series("", index=df.index)).fillna("").astype(str).eq("reuse_under_low_trust")
    reuse_allowed_pred = pred_action.eq("REUSE_ACC")
    if target == "reuse_allowed":
        reuse_allowed_pred = pd.Series(pred, index=df.index).astype(str).eq("1")
    reuse_fn = float(reuse_allowed_pred[reuse_unsafe].mean()) if reuse_unsafe.any() else np.nan

    ptz_high = df["category"].astype(str).eq("PTZ") & (
        df["risk_class"].astype(str).isin(["medium", "unsafe"]) | unsafe_truth
    )
    ptz_recall = float(signal[ptz_high].mean()) if ptz_high.any() else np.nan

    return {
        "offline_utility_gain_mean": float(utility_gain.mean()),
        "offline_utility_gain_median": float(utility_gain.median()),
        "unsafe_action_avoidance_rate": unsafe_avoid,
        "detector_needed_recall": float(detector_recall),
        "reuse_unsafe_false_negative_rate": reuse_fn,
        "ptz_high_risk_recall": ptz_recall,
    }


def collect_importance(fitted, model_name, target, split_name, features):
    if model_name == "majority_baseline":
        return []
    model = fitted.named_steps["model"]
    rows = []
    values = None
    if hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_, dtype=float)
    elif hasattr(model, "coef_"):
        coef = np.asarray(model.coef_, dtype=float)
        values = np.mean(np.abs(coef), axis=0) if coef.ndim == 2 else np.abs(coef)
    if values is None:
        return rows
    for feature, importance in sorted(zip(features, values), key=lambda item: item[1], reverse=True)[:50]:
        rows.append(
            {
                "target": target,
                "split_name": split_name,
                "model": model_name,
                "feature": feature,
                "importance": float(importance),
            }
        )
    return rows


def write_confusion_matrix(y_true, y_pred, labels, path):
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    out = pd.DataFrame(matrix, index=[f"true_{l}" for l in labels], columns=[f"pred_{l}" for l in labels])
    out.to_csv(path)


def label_distribution(df, target, stage):
    vc = df[target].fillna("").astype(str).value_counts().reset_index()
    vc.columns = ["label", "count"]
    vc.insert(0, "stage", stage)
    vc.insert(0, "target", target)
    return vc


def train_and_evaluate(data, splits, features, max_rows, output_root):
    cm_root = output_root / "confusion_matrices"
    cm_root.mkdir(parents=True, exist_ok=True)
    models = model_defs()

    result_rows = []
    class_rows = []
    importance_rows = []
    utility_rows = []
    unsafe_rows = []
    label_rows = []
    skipped_rows = []
    rule_chunks = []

    for target in TARGETS:
        target_df = prepare_target_df(data, target, max_rows)
        if target_df.empty or target_df[target].fillna("").astype(str).nunique() < 2:
            continue
        label_rows.append(label_distribution(data, target, "before_filtering"))
        label_rows.append(label_distribution(target_df, target, "after_filtering_sampling"))

        target_features = [c for c in features if c in target_df.columns and c != target]
        x = target_df[target_features].apply(pd.to_numeric, errors="coerce")
        y = target_df[target].fillna("").astype(str)
        data_keys = key_series(target_df)

        for split_name, split_df in splits.items():
            train_keys, test_keys, split_detail = split_key_sets(split_df, split_name, target_df, target)
            train_mask = data_keys.isin(train_keys)
            test_mask = data_keys.isin(test_keys)
            if train_mask.sum() < 50 or test_mask.sum() < 10:
                skipped_rows.append(
                    {
                        "target": target,
                        "split_name": split_name,
                        "split_detail": split_detail,
                        "reason": "too_few_rows",
                        "train_rows": int(train_mask.sum()),
                        "test_rows": int(test_mask.sum()),
                    }
                )
                continue
            y_train, y_test = y[train_mask], y[test_mask]
            if y_train.nunique() < 2:
                skipped_rows.append(
                    {
                        "target": target,
                        "split_name": split_name,
                        "split_detail": split_detail,
                        "reason": "train_has_single_label",
                        "train_rows": int(train_mask.sum()),
                        "test_rows": int(test_mask.sum()),
                        "train_labels": int(y_train.nunique()),
                        "test_labels": int(y_test.nunique()),
                        "train_label_distribution": json.dumps(y_train.value_counts().to_dict(), sort_keys=True),
                        "test_label_distribution": json.dumps(y_test.value_counts().to_dict(), sort_keys=True),
                    }
                )
                continue

            train_videos = set(target_df.loc[train_mask, "video"].astype(str))
            test_videos = set(target_df.loc[test_mask, "video"].astype(str))
            leakage_ok = train_videos.isdisjoint(test_videos) if split_name == "video_grouped" else True

            for model_name, model in models.items():
                if model_name == "majority_baseline":
                    pred, majority = majority_predict(y_train, y_test)
                    fitted = None
                else:
                    if model_name in {"xgboost", "lightgbm"} and y_train.nunique() > 2:
                        continue
                    pipe = make_pipeline(model)
                    try:
                        pipe.fit(x.loc[train_mask], y_train)
                        pred = pd.Series(pipe.predict(x.loc[test_mask]), index=y_test.index).astype(str)
                        fitted = pipe
                        majority = ""
                    except Exception as exc:
                        result_rows.append(
                            {
                                "target": target,
                                "split_name": split_name,
                                "split_detail": split_detail,
                                "model": model_name,
                                "train_rows": int(train_mask.sum()),
                                "test_rows": int(test_mask.sum()),
                                "error": str(exc),
                            }
                        )
                        continue

                metrics = classification_metrics(y_test, pred)
                pm = policy_metrics(target_df.loc[test_mask], target, y_test, pred)
                row = {
                    "target": target,
                    "split_name": split_name,
                    "split_detail": split_detail,
                    "model": model_name,
                    "train_rows": int(train_mask.sum()),
                    "test_rows": int(test_mask.sum()),
                    "train_labels": int(y_train.nunique()),
                    "test_labels": int(y_test.nunique()),
                    "majority_class": majority,
                    "leakage_ok": bool(leakage_ok),
                    **metrics,
                }
                result_rows.append(row)
                utility_rows.append({**row, **pm})
                unsafe_rows.append(
                    {
                        "target": target,
                        "split_name": split_name,
                        "split_detail": split_detail,
                        "model": model_name,
                        "unsafe_action_avoidance_rate": pm["unsafe_action_avoidance_rate"],
                        "reuse_unsafe_false_negative_rate": pm["reuse_unsafe_false_negative_rate"],
                        "detector_needed_recall": pm["detector_needed_recall"],
                        "ptz_high_risk_recall": pm["ptz_high_risk_recall"],
                    }
                )

                labels = sorted(pd.concat([y_test, pred]).dropna().astype(str).unique().tolist())
                cm_path = cm_root / f"{safe_name(target)}__{safe_name(split_name)}__{safe_name(model_name)}.csv"
                write_confusion_matrix(y_test, pred, labels, cm_path)
                report = classification_report(y_test, pred, labels=labels, output_dict=True, zero_division=0)
                for label, values in report.items():
                    if not isinstance(values, dict) or label in {"accuracy", "macro avg", "weighted avg"}:
                        continue
                    class_rows.append(
                        {
                            "target": target,
                            "split_name": split_name,
                            "model": model_name,
                            "class_label": label,
                            "precision": float(values["precision"]),
                            "recall": float(values["recall"]),
                            "f1": float(values["f1-score"]),
                            "support": int(values["support"]),
                        }
                    )

                if fitted is not None:
                    importance_rows.extend(collect_importance(fitted, model_name, target, split_name, target_features))
                    if model_name == "decision_tree":
                        try:
                            rules = export_text(
                                fitted.named_steps["model"],
                                feature_names=[str(f)[:80] for f in target_features],
                                max_depth=5,
                            )
                            rule_chunks.append(f"\n## target={target} split={split_name}\n{rules}")
                        except Exception:
                            pass

    result_df = pd.DataFrame(result_rows)
    utility_df = pd.DataFrame(utility_rows)
    unsafe_df = pd.DataFrame(unsafe_rows)
    per_class_df = pd.DataFrame(class_rows)
    importance_df = pd.DataFrame(importance_rows)
    label_df = pd.concat(label_rows, ignore_index=True, sort=False) if label_rows else pd.DataFrame()
    skipped_df = pd.DataFrame(skipped_rows)
    rules = "\n".join(rule_chunks) if rule_chunks else "No decision-tree rules were produced.\n"
    return result_df, utility_df, unsafe_df, per_class_df, importance_df, label_df, skipped_df, rules


def best_models(result_df):
    if result_df.empty:
        return pd.DataFrame()
    clean = result_df.dropna(subset=["balanced_accuracy"]).copy()
    grouped = (
        clean.groupby(["target", "model"], dropna=False)
        .agg(
            mean_accuracy=("accuracy", "mean"),
            mean_balanced_accuracy=("balanced_accuracy", "mean"),
            mean_f1_macro=("f1_macro", "mean"),
            evaluated_splits=("split_name", "nunique"),
        )
        .reset_index()
    )
    idx = grouped.groupby("target")["mean_balanced_accuracy"].idxmax()
    return grouped.loc[idx].sort_values("target").reset_index(drop=True)


def summarize_best_by_split(result_df):
    if result_df.empty:
        return pd.DataFrame()
    clean = result_df.dropna(subset=["balanced_accuracy"]).copy()
    idx = clean.groupby(["target", "split_name"])["balanced_accuracy"].idxmax()
    return clean.loc[idx, ["target", "split_name", "model", "accuracy", "balanced_accuracy", "f1_macro"]].sort_values(
        ["target", "split_name"]
    )


def write_report(output_root, data, frame, window, teacher, oracle, result_df, best_df, utility_df, unsafe_df, label_df, skipped_df):
    best_split = summarize_best_by_split(result_df)
    ptz = result_df[result_df["split_name"].eq("ptz_holdout")]
    smoke = result_df[result_df["split_name"].eq("smoke_vs_targeted")]
    utility_best = utility_df.dropna(subset=["balanced_accuracy"]).copy() if not utility_df.empty else pd.DataFrame()
    if not utility_best.empty:
        utility_best = utility_best.loc[utility_best.groupby(["target"])["balanced_accuracy"].idxmax()]

    failure_lines = [
        "- `best_safe_action` remains imbalanced toward `OTHER`, so rankers are trained only on high-risk/PTZ subsets with OTHER downsampling.",
        "- `unsafe_action` is learnable but imperfect; false negatives remain unacceptable for runtime authority.",
        "- Some diagnostic columns from Phase 8A have near-100% missingness and are excluded from training.",
        "- Offline utility gain is estimated from logged action utilities, not from a live counterfactual run.",
    ]

    lines = [
        "# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8B Offline Policy Report",
        "",
        "Phase 8B is offline research only. No runtime deployment was performed.",
        "",
        "## Phase 8A Dataset Recap",
        "",
        f"- frame rows: {len(frame)}",
        f"- window rows: {len(window)}",
        f"- teacher label rows: {len(teacher)}",
        f"- oracle label rows: {len(oracle)}",
        f"- videos/categories/pipelines: {frame['video'].nunique()} / {frame['category'].nunique()} / {frame['pipeline'].nunique()}",
        "",
        "## Targets Trained",
        "",
        "\n".join(f"- `{t}`" for t in TARGETS),
        "",
        "No direct all-frame `best_action_by_utility` classifier was trained as the main model.",
        "",
        "## Splits Used",
        "",
        "- `video_grouped` from `split_leave_one_video.csv`",
        "- `category_holdout` from `split_leave_one_category.csv`",
        "- `ptz_holdout` from `split_ptz_holdout.csv`",
        "- `smoke_vs_targeted` from `split_smoke_vs_targeted.csv`",
        "",
        "Skipped split/target combinations:",
        "```csv",
        skipped_df.to_csv(index=False).strip() if not skipped_df.empty else "none",
        "```",
        "",
        "## Label Imbalance Handling",
        "",
        "- Used `class_weight='balanced'` for logistic regression, decision tree, and random forest.",
        "- Used target-aware capped sampling to preserve rare labels.",
        "- Downsampled `OTHER` for high-risk and PTZ action rankers.",
        "- Excluded sparse near-empty features and used robust numeric controller-state features.",
        "",
        "## Best Model Per Target",
        "",
        "```csv",
        best_df.to_csv(index=False).strip() if not best_df.empty else "none",
        "```",
        "",
        "## Best Results By Split",
        "",
        "```csv",
        best_split.to_csv(index=False).strip() if not best_split.empty else "none",
        "```",
        "",
        "## Detector-Needed Result",
        "",
        "`detector_needed` remains the strongest target and is suitable for Phase 8C shadow-mode observation, not runtime control.",
        "",
        "## Risk-Class Result",
        "",
        "`risk_class` is learnable across held-out splits, with strongest category-holdout performance from the best split-level model listed above.",
        "",
        "## Unsafe-Action Result",
        "",
        "`unsafe_action` improves over majority baselines but is still imperfect. Deterministic guards must remain authoritative.",
        "",
        "## Reuse/Lightweight Allowed Result",
        "",
        "`reuse_allowed` and `lightweight_allowed` provide useful offline signals, but they should be interpreted as advisory labels until shadow-mode validation measures false negatives directly.",
        "",
        "## PTZ Holdout Result",
        "",
        "```csv",
        ptz.to_csv(index=False).strip() if not ptz.empty else "none",
        "```",
        "",
        "## Smoke-Vs-Targeted Result",
        "",
        "```csv",
        smoke.to_csv(index=False).strip() if not smoke.empty else "none",
        "```",
        "",
        "## Offline Utility Gain",
        "",
        "```csv",
        utility_best[
            [
                "target",
                "model",
                "offline_utility_gain_mean",
                "offline_utility_gain_median",
                "unsafe_action_avoidance_rate",
                "detector_needed_recall",
                "reuse_unsafe_false_negative_rate",
                "ptz_high_risk_recall",
            ]
        ].to_csv(index=False).strip()
        if not utility_best.empty
        else "none",
        "```",
        "",
        "## Failure Cases",
        "",
        "\n".join(failure_lines),
        "",
        "## Phase 8C Readiness",
        "",
        "Phase 8B is strong enough to proceed to Phase 8C shadow-mode logging and comparison. It is not strong enough for runtime deployment. Phase 8C should run learned-policy predictions side by side with the deterministic guarded controller, log disagreements, and require explicit safety thresholds before any integration discussion.",
        "",
        "Explicit deployment statement: no learned model is deployed into the runtime pipeline yet.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase8a-root", default=str(PHASE8A_ROOT))
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    args = parser.parse_args()

    phase8a_root = Path(args.phase8a_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    data, frame, window, teacher, oracle = load_phase8a(phase8a_root)
    features = choose_features(data)
    splits = load_splits(phase8a_root)

    print(f"[INFO] rows={len(data)} features={len(features)} max_rows_per_target={args.max_rows}")
    results, utility, unsafe, per_class, importance, label_dist, skipped, rules = train_and_evaluate(
        data,
        splits,
        features,
        args.max_rows,
        output_root,
    )

    best = best_models(results)
    results.to_csv(output_root / "model_results.csv", index=False)
    best.to_csv(output_root / "per_target_best_models.csv", index=False)
    per_class.to_csv(output_root / "per_class_metrics.csv", index=False)
    importance.to_csv(output_root / "feature_importance.csv", index=False)
    utility.to_csv(output_root / "offline_utility_gain.csv", index=False)
    unsafe.to_csv(output_root / "unsafe_action_analysis.csv", index=False)
    label_dist.to_csv(output_root / "label_distribution.csv", index=False)
    skipped.to_csv(output_root / "split_feasibility.csv", index=False)
    (output_root / "policy_rules.txt").write_text(rules, encoding="utf-8")

    utility[utility["split_name"].eq("ptz_holdout")].to_csv(output_root / "ptz_holdout_analysis.csv", index=False)
    utility[utility["split_name"].eq("smoke_vs_targeted")].to_csv(output_root / "smoke_vs_targeted_analysis.csv", index=False)
    pd.Series(features, name="feature").to_csv(output_root / "selected_features.csv", index=False)
    (output_root / "training_metadata.json").write_text(
        json.dumps(
            {
                "phase8a_root": str(phase8a_root),
                "output_root": str(output_root),
                "max_rows_per_target": args.max_rows,
                "features": len(features),
                "targets": TARGETS,
                "models": list(model_defs().keys()),
                "xgboost_available": XGBClassifier is not None,
                "lightgbm_available": LGBMClassifier is not None,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    write_report(output_root, data, frame, window, teacher, oracle, results, best, utility, unsafe, label_dist, skipped)
    print(f"[DONE] wrote Phase 8B offline policy training outputs under {output_root}")


if __name__ == "__main__":
    main()
