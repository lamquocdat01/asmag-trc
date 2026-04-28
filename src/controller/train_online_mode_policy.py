import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text


FEATURE_COLUMNS = [
    "motion_density_mean",
    "motion_density_std",
    "component_count_mean",
    "component_count_std",
    "fd_mog_disagreement",
    "knn_mog_disagreement",
    "illumination_variance",
    "reuse_success_rate",
    "active_frame_rate",
    "gate_closed_rate",
]

MODE_ORDER = ["FAST", "ACC", "P3_FALLBACK"]

CONTROLLER_CATEGORY_POLICY = {
    "baseline": "FAST",
    "badWeather": "ACC",
    "intermittentObjectMotion": "ACC",
    "thermal": "ACC",
    "PTZ": "P3_FALLBACK",
    "cameraJitter": "P3_FALLBACK",
    "dynamicBackground": "P3_FALLBACK",
    "lowFramerate": "P3_FALLBACK",
    "nightVideos": "P3_FALLBACK",
    "shadow": "P3_FALLBACK",
    "turbulence": "P3_FALLBACK",
}


def pseudo_label_for_category(category):
    return CONTROLLER_CATEGORY_POLICY.get(str(category), "P3_FALLBACK")


def has_required_features(path):
    try:
        header = pd.read_csv(path, nrows=0)
    except Exception:
        return False
    return all(col in header.columns for col in FEATURE_COLUMNS)


def load_feature_rows(input_roots, include_pipelines):
    frames = []
    skipped = []
    include_pipelines = set(include_pipelines)
    for root in input_roots:
        root = Path(root)
        if not root.exists():
            skipped.append({"path": str(root), "reason": "missing input root"})
            continue
        for path in root.rglob("frame_metrics.csv"):
            if not has_required_features(path):
                skipped.append({"path": str(path), "reason": "missing rolling feature columns"})
                continue
            df = pd.read_csv(path)
            if df.empty:
                skipped.append({"path": str(path), "reason": "empty frame metrics"})
                continue
            if include_pipelines:
                df = df[df["pipeline"].isin(include_pipelines)].copy()
            if df.empty:
                continue
            df["pseudo_mode"] = df["category"].map(pseudo_label_for_category)
            df["group_id"] = df["category"].astype(str) + "/" + df["video"].astype(str)
            df["source_file"] = str(path)
            keep = ["category", "video", "pipeline", "frame_id", "group_id", "pseudo_mode", "source_file"] + FEATURE_COLUMNS
            frames.append(df[keep])
    if not frames:
        raise RuntimeError("No frame-level rows with the required rolling feature columns were found.")
    data = pd.concat(frames, ignore_index=True)
    data[FEATURE_COLUMNS] = data[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return data, pd.DataFrame(skipped)


def split_by_video(data, validation_size, random_state):
    groups = data["group_id"].astype(str)
    unique_modes = set(data["pseudo_mode"].unique())
    splitter = GroupShuffleSplit(n_splits=32, test_size=validation_size, random_state=random_state)
    best = None
    for train_idx, val_idx in splitter.split(data, data["pseudo_mode"], groups):
        train_modes = set(data.iloc[train_idx]["pseudo_mode"].unique())
        val_modes = set(data.iloc[val_idx]["pseudo_mode"].unique())
        score = len(train_modes & unique_modes) + len(val_modes & unique_modes)
        candidate = (score, train_idx, val_idx)
        if best is None or candidate[0] > best[0]:
            best = candidate
        if train_modes == unique_modes and val_modes == unique_modes:
            return train_idx, val_idx
    return best[1], best[2]


def candidate_models(random_state):
    models = {
        "decision_tree_depth3": DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=random_state),
        "decision_tree_depth5": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=random_state),
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_state),
        ),
        "random_forest_small": RandomForestClassifier(
            n_estimators=80,
            max_depth=5,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=1,
        ),
    }
    return models


def score_model(model, x_val, y_val):
    pred = model.predict(x_val)
    return {
        "mode_accuracy": accuracy_score(y_val, pred),
        "macro_f1": f1_score(y_val, pred, labels=MODE_ORDER, average="macro", zero_division=0),
        "p3_fallback_recall": recall_score(
            y_val,
            pred,
            labels=["P3_FALLBACK"],
            average="macro",
            zero_division=0,
        ),
    }


def model_feature_importance(model):
    estimator = model
    if hasattr(model, "named_steps"):
        estimator = list(model.named_steps.values())[-1]
    if hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        values = np.mean(np.abs(estimator.coef_), axis=0)
    else:
        values = np.zeros(len(FEATURE_COLUMNS), dtype=float)
    total = float(np.sum(np.abs(values)))
    if total > 0:
        values = values / total
    return pd.DataFrame({"feature": FEATURE_COLUMNS, "importance": values}).sort_values("importance", ascending=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-roots",
        nargs="+",
        default=[
            "outputs/q2_core_extended_online_controller_p3tuned",
            "outputs/full_cdnet2014_controller_sampled_metrics",
        ],
    )
    parser.add_argument("--output-dir", default="outputs/q2_core_extended_online_controller_calibrated")
    parser.add_argument("--model-out", default="")
    parser.add_argument("--validation-size", type=float, default=0.25)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument(
        "--include-pipelines",
        nargs="*",
        default=["ASMAG_TR_CONTROLLER_ONLINE_P3TUNED", "ASMAG_TR_CONTROLLER_ONLINE"],
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_out = Path(args.model_out) if args.model_out else out_dir / "online_mode_policy.pkl"

    data, skipped = load_feature_rows(args.input_roots, args.include_pipelines)
    data.to_csv(out_dir / "online_policy_training_rows.csv", index=False)
    if not skipped.empty:
        skipped.to_csv(out_dir / "online_policy_skipped_sources.csv", index=False)

    train_idx, val_idx = split_by_video(data, args.validation_size, args.random_state)
    train = data.iloc[train_idx].copy()
    val = data.iloc[val_idx].copy()
    train.to_csv(out_dir / "online_policy_train_split.csv", index=False)
    val.to_csv(out_dir / "online_policy_validation_split.csv", index=False)

    x_train = train[FEATURE_COLUMNS].astype(float)
    y_train = train["pseudo_mode"].astype(str)
    x_val = val[FEATURE_COLUMNS].astype(float)
    y_val = val["pseudo_mode"].astype(str)

    metrics = []
    fitted = {}
    for name, model in candidate_models(args.random_state).items():
        model.fit(x_train, y_train)
        scores = score_model(model, x_val, y_val)
        fitted[name] = model
        metrics.append(
            {
                "policy": name,
                **scores,
                "selection_score": 0.40 * scores["mode_accuracy"] + 0.35 * scores["macro_f1"] + 0.25 * scores["p3_fallback_recall"],
            }
        )

    metrics_df = pd.DataFrame(metrics).sort_values(
        ["selection_score", "macro_f1", "p3_fallback_recall", "mode_accuracy"],
        ascending=False,
    )
    metrics_df.to_csv(out_dir / "online_policy_validation_metrics.csv", index=False)
    best_name = str(metrics_df.iloc[0]["policy"])
    best_model = fitted[best_name]

    val_pred = best_model.predict(x_val)
    confusion = pd.DataFrame(
        confusion_matrix(y_val, val_pred, labels=MODE_ORDER),
        index=[f"true_{m}" for m in MODE_ORDER],
        columns=[f"pred_{m}" for m in MODE_ORDER],
    )
    confusion.to_csv(out_dir / "mode_confusion_matrix.csv")

    importance = model_feature_importance(best_model)
    importance.to_csv(out_dir / "online_policy_feature_importance.csv", index=False)

    artifact = {
        "model": best_model,
        "policy_name": best_name,
        "feature_columns": FEATURE_COLUMNS,
        "mode_order": MODE_ORDER,
        "category_policy": CONTROLLER_CATEGORY_POLICY,
        "validation_metrics": metrics_df.to_dict("records"),
    }
    with model_out.open("wb") as f:
        pickle.dump(artifact, f)

    if isinstance(best_model, DecisionTreeClassifier):
        (out_dir / "online_policy_tree_rules.txt").write_text(
            export_text(best_model, feature_names=FEATURE_COLUMNS),
            encoding="utf-8",
        )

    summary = [
        "# Online Mode Policy Training Summary",
        "",
        f"- Training rows: `{len(train)}`",
        f"- Validation rows: `{len(val)}`",
        f"- Video groups train/validation: `{train['group_id'].nunique()}` / `{val['group_id'].nunique()}`",
        f"- Selected policy: `{best_name}`",
        f"- Model artifact: `{model_out}`",
        "",
        "## Validation Metrics",
        "",
        metrics_df.to_markdown(index=False),
        "",
        "## Label Distribution",
        "",
        data["pseudo_mode"].value_counts().reindex(MODE_ORDER, fill_value=0).rename_axis("mode").reset_index(name="frames").to_markdown(index=False),
    ]
    (out_dir / "online_policy_training_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print(f"[TRAIN] selected={best_name}")
    print(metrics_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print(f"[MODEL] {model_out}")


if __name__ == "__main__":
    main()
