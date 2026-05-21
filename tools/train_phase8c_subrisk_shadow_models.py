import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import train_phase8b_policy_models as train8b


OUTPUT_ROOT = Path("outputs/phase8c_subrisk_models")
PHASE8A_ROOT = Path("outputs/phase8a_policy_dataset")
MODEL_DIR_8B = Path("outputs/phase8b_policy_training/models")
RANDOM_STATE = 8
THRESHOLDS = np.round(np.arange(0.05, 1.00, 0.01), 2)
SUBRISK_TARGETS = [
    "closed_empty_risk",
    "reuse_risk",
    "lightweight_p3_risk",
    "legacy_cadence_risk",
    "detector_needed",
    "lightweight_acc_allowed",
]


def boolish(df, column):
    return train8b.boolish(df.get(column), index=df.index)


def feature_names():
    schema = MODEL_DIR_8B / "shadow_feature_schema.csv"
    if schema.exists():
        return pd.read_csv(schema)["feature"].astype(str).tolist()
    selected = Path("outputs/phase8b_policy_training/selected_features.csv")
    if selected.exists():
        return pd.read_csv(selected)["feature"].astype(str).tolist()
    data, _, _, _, _ = train8b.load_phase8a(PHASE8A_ROOT)
    return train8b.choose_features(data)


def derive_subrisk_labels(df):
    action = df.get("action_bucket", pd.Series("", index=df.index)).fillna("").astype(str)
    unsafe_label = df.get("unsafe_action_label", pd.Series("", index=df.index)).fillna("").astype(str)
    category = df.get("category", pd.Series("", index=df.index)).fillna("").astype(str)
    best_safe = df.get("best_safe_action", pd.Series("OTHER", index=df.index)).fillna("OTHER").astype(str)
    unsafe_penalty = boolish(df, "unsafe_action_penalty").gt(0)
    current_safe = ~unsafe_penalty

    event_or_motion = (
        boolish(df, "active_event_memory").gt(0)
        | boolish(df, "global_motion_proxy").gt(0.5)
        | boolish(df, "gmq_event_hard_veto_active").gt(0)
        | boolish(df, "gmq_event_continuity_risk").gt(0.35)
    )
    low_trust = (
        boolish(df, "motion_comp_compensated_trust_low").gt(0)
        | boolish(df, "geometry_reuse_blocked").gt(0)
        | boolish(df, "reuse_invalidated_by_motion_comp").gt(0)
        | boolish(df, "reuse_invalidated_by_camera_jump").gt(0)
        | boolish(df, "camera_jump_suspect").gt(0)
        | boolish(df, "gmq_background_reliability").lt(0.35)
        | boolish(df, "gmq_temporal_consistency").lt(0.20)
    )
    stale_reuse = (
        boolish(df, "reuse_age").gt(6)
        | boolish(df, "reuse_age_eval").gt(6)
        | boolish(df, "reuse_age_raw").gt(10)
        | boolish(df, "reuse_allowed_by_eval_age").eq(0)
        | boolish(df, "reuse_allowed_by_raw_age").eq(0)
    )
    p3_low_trust = (
        boolish(df, "gmq_lightweight_p3_veto_active").gt(0)
        | boolish(df, "geometry_lightweight_p3_blocked").gt(0)
        | boolish(df, "lightweight_invalidated_by_motion_comp").gt(0)
        | boolish(df, "candidate_P3_quality").lt(0.25)
        | boolish(df, "candidate_P3_temporal_iou").lt(0.20)
    )
    cadence_not_preserved = (
        boolish(df, "ptz_detector_floor_cadence_allowed").eq(0)
        | boolish(df, "detector_like_action_thinned").gt(0)
        | boolish(df, "event_detect_acc_thinned").gt(0)
        | boolish(df, "ptz_cadence_thinning_active").gt(0)
    )

    out = pd.DataFrame(index=df.index)
    out["closed_empty_risk"] = (
        unsafe_label.eq("closed_empty_during_event_or_motion")
        | boolish(df, "closed_empty_blocked_final").gt(0)
        | boolish(df, "closed_empty_blocked_under_ptz").gt(0)
        | (action.eq("CLOSED_EMPTY") & event_or_motion)
    )
    out["reuse_risk"] = (
        unsafe_label.eq("reuse_under_low_trust")
        | boolish(df, "reuse_blocked_final").gt(0)
        | (action.eq("REUSE_ACC") & (low_trust | stale_reuse | event_or_motion))
    )
    out["lightweight_p3_risk"] = (
        unsafe_label.eq("lightweight_p3_under_ptz")
        | boolish(df, "lightweight_blocked_final").gt(0)
        | (
            action.eq("LIGHTWEIGHT_MASK_P3_FALLBACK")
            & (category.eq("PTZ") | boolish(df, "global_motion_proxy").gt(0.5) | p3_low_trust)
        )
    )
    out["legacy_cadence_risk"] = (
        unsafe_label.eq("legacy_safe_without_detector_cadence")
        | (
            action.eq("LEGACY_SAFE_P3_GUARD")
            & (cadence_not_preserved | boolish(df, "ptz_detector_floor_active").gt(0))
        )
    )
    out["detector_needed"] = boolish(df, "detector_needed").gt(0)
    out["lightweight_acc_allowed"] = (
        best_safe.eq("LIGHTWEIGHT_MASK_ACC")
        | (action.eq("LIGHTWEIGHT_MASK_ACC") & current_safe & ~p3_low_trust)
    )
    return out.astype(int)


def model_defs():
    return {
        "majority_baseline": None,
        "logistic_regression": LogisticRegression(
            max_iter=300,
            class_weight="balanced",
            solver="lbfgs",
        ),
        "shallow_decision_tree": DecisionTreeClassifier(
            max_depth=4,
            min_samples_leaf=30,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
    }


def make_pipeline(model):
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler(with_mean=False)),
            ("model", model),
        ]
    )


def split_for(split_name, splits, target_df, target):
    if split_name == "video_grouped":
        split_df = splits["video_grouped"]
        return train8b.choose_fold(split_df, target_df, target)
    if split_name == "category_holdout":
        split_df = splits["category_holdout"]
        return train8b.choose_fold(split_df, target_df, target, prefer_column="heldout_category", prefer_value="PTZ")
    if split_name == "ptz_holdout":
        split_df = splits["ptz_holdout"]
        train_keys = set(train8b.key_series(split_df[split_df["role"].eq("train")]))
        test_keys = set(train8b.key_series(split_df[split_df["role"].eq("test")]))
        return train_keys, test_keys, "direct"
    return set(), set(), "unavailable"


def binary_metrics(y_true, y_pred):
    y_true = pd.Series(y_true).astype(int)
    y_pred = pd.Series(y_pred).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    if y_true.nunique() > 1:
        balanced = balanced_accuracy_score(y_true, y_pred)
    else:
        balanced = accuracy_score(y_true, y_pred)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def majority_predict(y_train, count):
    majority = int(pd.Series(y_train).value_counts().idxmax())
    return pd.Series([majority] * count)


def target_sample(df, target, max_rows):
    if target == "lightweight_acc_allowed":
        scope = (
            df["action_bucket"].fillna("").astype(str).eq("LIGHTWEIGHT_MASK_ACC")
            | df["best_safe_action"].fillna("").astype(str).eq("LIGHTWEIGHT_MASK_ACC")
            | boolish(df, "gmq_acc_blocked_under_global_motion").gt(0)
            | boolish(df, "acc_blocked_final").gt(0)
        )
        scoped = df[scope].copy()
        if len(scoped) >= 100:
            df = scoped
    return train8b.target_aware_sample(df, target, max_rows)


def evaluate_models(data, features, splits, output_root, max_rows):
    models = model_defs()
    result_rows = []
    threshold_rows = []
    importance_rows = []
    recommendations = []
    split_names = ["video_grouped", "category_holdout", "ptz_holdout"]

    for target in SUBRISK_TARGETS:
        target_df = target_sample(data, target, max_rows)
        x = target_df[features].apply(pd.to_numeric, errors="coerce")
        y = target_df[target].astype(int)
        keys = train8b.key_series(target_df)
        best_candidate = None

        for split_name in split_names:
            train_keys, test_keys, detail = split_for(split_name, splits, target_df, target)
            train_mask = keys.isin(train_keys)
            test_mask = keys.isin(test_keys)
            if train_mask.sum() < 50 or test_mask.sum() < 10:
                result_rows.append({
                    "target": target,
                    "split_name": split_name,
                    "split_detail": detail,
                    "model": "skipped",
                    "reason": "too_few_rows",
                    "train_rows": int(train_mask.sum()),
                    "test_rows": int(test_mask.sum()),
                })
                continue
            if y[train_mask].nunique() < 2 or y[test_mask].nunique() < 2:
                result_rows.append({
                    "target": target,
                    "split_name": split_name,
                    "split_detail": detail,
                    "model": "skipped",
                    "reason": "single_label_split",
                    "train_rows": int(train_mask.sum()),
                    "test_rows": int(test_mask.sum()),
                    "train_positive_labels": int(y[train_mask].sum()),
                    "test_positive_labels": int(y[test_mask].sum()),
                })
                continue

            for model_name, model in models.items():
                if model is None:
                    pred = majority_predict(y[train_mask], int(test_mask.sum()))
                    scores = pred.astype(float).to_numpy()
                else:
                    pipe = make_pipeline(model)
                    pipe.fit(x[train_mask], y[train_mask])
                    pred = pd.Series(pipe.predict(x[test_mask])).astype(int)
                    if hasattr(pipe, "predict_proba"):
                        classes = [str(c) for c in pipe.named_steps["model"].classes_]
                        probs = pipe.predict_proba(x[test_mask])
                        scores = probs[:, classes.index("1")] if "1" in classes else probs.max(axis=1)
                    else:
                        scores = pred.astype(float).to_numpy()

                    fitted = pipe.named_steps["model"]
                    if hasattr(fitted, "feature_importances_"):
                        importances = fitted.feature_importances_
                    elif hasattr(fitted, "coef_"):
                        importances = np.abs(fitted.coef_[0])
                    else:
                        importances = np.zeros(len(features))
                    for idx in np.argsort(importances)[::-1][:20]:
                        if importances[idx] <= 0:
                            continue
                        importance_rows.append({
                            "target": target,
                            "split_name": split_name,
                            "model": model_name,
                            "feature": features[idx],
                            "importance": float(importances[idx]),
                        })

                metrics = binary_metrics(y[test_mask].reset_index(drop=True), pred.reset_index(drop=True))
                row = {
                    "target": target,
                    "split_name": split_name,
                    "split_detail": detail,
                    "model": model_name,
                    "train_rows": int(train_mask.sum()),
                    "test_rows": int(test_mask.sum()),
                    "train_positive_labels": int(y[train_mask].sum()),
                    "test_positive_labels": int(y[test_mask].sum()),
                    **metrics,
                }
                result_rows.append(row)

                if model_name == "majority_baseline":
                    continue
                labels = y[test_mask].reset_index(drop=True).astype(int)
                for threshold in THRESHOLDS:
                    flags = pd.Series(scores).ge(threshold).astype(int)
                    m = binary_metrics(labels, flags)
                    sweep_row = {
                        "target": target,
                        "split_name": split_name,
                        "split_detail": detail,
                        "model": model_name,
                        "threshold": float(threshold),
                        "flag_rate": float(flags.mean()),
                        "positive_labels": int(labels.sum()),
                        "rows": int(len(labels)),
                        **m,
                    }
                    threshold_rows.append(sweep_row)
                    if split_name == "video_grouped":
                        score_tuple = (
                            m["recall"] >= 0.90,
                            m["f1"],
                            m["balanced_accuracy"],
                            -float(flags.mean()),
                            model_name == "logistic_regression",
                        )
                        if best_candidate is None or score_tuple > best_candidate[0]:
                            best_candidate = (score_tuple, sweep_row)

        if best_candidate is not None:
            rec = dict(best_candidate[1])
            recommendations.append({
                "target": target,
                "recommended_model": rec["model"],
                "recommended_threshold": rec["threshold"],
                "video_grouped_recall": rec["recall"],
                "video_grouped_precision": rec["precision"],
                "video_grouped_f1": rec["f1"],
                "video_grouped_flag_rate": rec["flag_rate"],
                "selection_note": "video_grouped threshold prioritized recall>=0.90, then F1/balanced accuracy/selectivity",
            })

    results = pd.DataFrame(result_rows)
    thresholds = pd.DataFrame(threshold_rows)
    importance = pd.DataFrame(importance_rows)
    recs = pd.DataFrame(recommendations)
    results.to_csv(output_root / "subrisk_model_results.csv", index=False)
    thresholds.to_csv(output_root / "subrisk_threshold_sweep.csv", index=False)
    importance.to_csv(output_root / "subrisk_feature_importance.csv", index=False)
    recs.to_csv(output_root / "subrisk_runtime_model_recommendation.csv", index=False)
    return results, thresholds, importance, recs


def write_label_distribution(data, output_root):
    rows = []
    for target in SUBRISK_TARGETS:
        counts = data[target].astype(int).value_counts().to_dict()
        rows.append({
            "target": target,
            "rows": int(len(data)),
            "positive_labels": int(counts.get(1, 0)),
            "negative_labels": int(counts.get(0, 0)),
            "positive_rate": float(counts.get(1, 0) / max(1, len(data))),
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_root / "subrisk_label_distribution.csv", index=False)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase8a-root", default=str(PHASE8A_ROOT))
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    parser.add_argument("--max-rows", type=int, default=80000)
    args = parser.parse_args()

    phase8a_root = Path(args.phase8a_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    data, _, _, _, _ = train8b.load_phase8a(phase8a_root)
    labels = derive_subrisk_labels(data)
    for col in labels.columns:
        data[col] = labels[col]
    features = feature_names()
    splits = train8b.load_splits(phase8a_root)

    write_label_distribution(data, output_root)
    results, thresholds, importance, recs = evaluate_models(data, features, splits, output_root, args.max_rows)
    metadata = {
        "phase": "8C-1D-subrisk-shadow",
        "features": features,
        "targets": SUBRISK_TARGETS,
        "models": list(model_defs().keys()),
        "max_rows": args.max_rows,
        "outputs": [
            "subrisk_model_results.csv",
            "subrisk_threshold_sweep.csv",
            "subrisk_feature_importance.csv",
            "subrisk_runtime_model_recommendation.csv",
            "subrisk_label_distribution.csv",
        ],
    }
    (output_root / "training_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[DONE] wrote Phase 8C sub-risk model analysis under {output_root}")


if __name__ == "__main__":
    main()
