import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.exceptions import ConvergenceWarning

try:
    from sklearn.linear_model import LogisticRegression
except Exception:  # pragma: no cover
    LogisticRegression = None


OUTPUT_ROOT = Path("outputs/phase8a_policy_dataset")
TARGETS = ["best_action_by_utility", "risk_class", "unsafe_action", "detector_needed"]
METRIC_LEAK_COLUMNS = {
    "FMeasure",
    "Recall",
    "Precision",
    "Event_proxy",
    "utility_score",
    "unsafe_action_penalty",
    "unsafe_action_label",
    "best_action_by_utility",
    "best_safe_action",
    "expected_utility_gain",
    "expected_FMeasure_gain",
    "best_oracle_pipeline",
    "best_oracle_run_id",
    "risk_class",
    "unsafe_action",
    "detector_needed",
}
META_COLUMNS = {
    "run_id",
    "run_name",
    "source_folder",
    "dataset",
    "category",
    "video",
    "frame_id",
    "pipeline",
    "action_label",
    "action_bucket",
    "Event_State",
}


warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", message="Skipping features without any observed values*")
warnings.filterwarnings("ignore", message="y_pred contains classes not in y_true*")


def one_hot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_data(root):
    frame = pd.read_parquet(root / "frame_state_dataset.parquet")
    oracle = pd.read_parquet(root / "oracle_action_dataset.parquet")
    oracle_keys = ["dataset", "category", "video", "frame_id"]
    merged = frame.merge(oracle, on=oracle_keys, how="left")
    merged["unsafe_action"] = merged["unsafe_action"].fillna(False).astype(bool).astype(int)
    if "detector_needed" not in merged.columns:
        merged["detector_needed"] = merged["action_bucket"].isin(["DETECT_ACC", "FALLBACK_P3_GUARD", "LEGACY_SAFE_P3_GUARD"]).astype(int)
    for target in TARGETS:
        if target not in merged.columns:
            merged[target] = ""
    return merged


def make_splits(df):
    video_names = sorted(df["video"].astype(str).unique())
    if len(video_names) <= 1:
        return {}
    heldout_video = video_names[-1]
    video_split = ("video_grouped", df["video"].astype(str).ne(heldout_video), df["video"].astype(str).eq(heldout_video))

    categories = sorted(df["category"].astype(str).unique())
    splits = {"video_grouped": video_split}
    if len(categories) > 1:
        heldout_category = "PTZ" if "PTZ" in categories else categories[-1]
        splits["category_holdout"] = (
            "category_holdout",
            df["category"].astype(str).ne(heldout_category),
            df["category"].astype(str).eq(heldout_category),
        )
    return splits


def candidate_features(df):
    drop = METRIC_LEAK_COLUMNS | META_COLUMNS
    features = []
    for col in df.columns:
        if col in drop:
            continue
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_bool_dtype(df[col]):
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() > 0 and numeric.nunique(dropna=True) > 1:
                features.append(col)
        elif df[col].dtype == object and df[col].nunique(dropna=True) <= 50:
            if df[col].notna().sum() > 0 and df[col].nunique(dropna=True) > 1:
                features.append(col)
    return features


def build_preprocessor(x):
    numeric = [c for c in x.columns if pd.api.types.is_numeric_dtype(x[c]) or pd.api.types.is_bool_dtype(x[c])]
    categorical = [c for c in x.columns if c not in numeric]
    return ColumnTransformer(
        transformers=[
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler(with_mean=False))]), numeric),
            ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", one_hot_encoder())]), categorical),
        ],
        remainder="drop",
    )


def models():
    out = {"decision_tree": DecisionTreeClassifier(max_depth=5, min_samples_leaf=20, random_state=8)}
    if LogisticRegression is not None:
        out["logistic_regression"] = LogisticRegression(max_iter=150, class_weight="balanced", solver="liblinear")
    out["random_forest"] = RandomForestClassifier(n_estimators=40, max_depth=7, min_samples_leaf=10, random_state=8, n_jobs=-1)
    out["gradient_boosting"] = GradientBoostingClassifier(n_estimators=40, max_depth=3, random_state=8)
    return out


def majority_eval(y_train, y_test):
    if len(y_train) == 0 or len(y_test) == 0:
        return None, {}
    majority = y_train.value_counts().idxmax()
    pred = pd.Series([majority] * len(y_test), index=y_test.index)
    return majority, metric_dict(y_test, pred)


def metric_dict(y_true, y_pred):
    labels = sorted(pd.Series(y_true).dropna().astype(str).unique().tolist())
    if len(labels) <= 1:
        bal = accuracy_score(y_true, y_pred)
    else:
        bal = balanced_accuracy_score(y_true, y_pred)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(bal),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def transformed_feature_names(pipe, original_features):
    pre = pipe.named_steps["preprocess"]
    try:
        return list(pre.get_feature_names_out(original_features))
    except Exception:
        return list(original_features)


def collect_importances(pipe, model_name, target, split_name, original_features):
    clf = pipe.named_steps["model"]
    if not hasattr(clf, "feature_importances_"):
        return pd.DataFrame()
    names = transformed_feature_names(pipe, original_features)
    values = clf.feature_importances_
    n = min(len(names), len(values))
    rows = []
    for name, value in sorted(zip(names[:n], values[:n]), key=lambda item: item[1], reverse=True)[:40]:
        rows.append(
            {
                "target": target,
                "split_name": split_name,
                "model": model_name,
                "feature": name,
                "importance": float(value),
            }
        )
    return pd.DataFrame(rows)


def fit_and_eval(df, max_rows):
    if len(df) > max_rows:
        df = df.sample(max_rows, random_state=8).reset_index(drop=True)
    features = candidate_features(df)
    x = df[features].copy()
    for col in x.columns:
        if x[col].dtype == object:
            x[col] = x[col].fillna("").astype(str)
    split_defs = make_splits(df)
    results = []
    importances = []
    rule_chunks = []

    for target in TARGETS:
        if target not in df.columns:
            continue
        y = df[target].fillna("").astype(str)
        if y.nunique() < 2:
            continue
        for split_name, train_mask, test_mask in split_defs.values():
            train_mask = pd.Series(train_mask, index=df.index).fillna(False)
            test_mask = pd.Series(test_mask, index=df.index).fillna(False)
            if train_mask.sum() < 20 or test_mask.sum() < 5:
                continue
            y_train, y_test = y[train_mask], y[test_mask]
            if y_train.nunique() < 2:
                continue

            majority, metrics = majority_eval(y_train, y_test)
            if metrics:
                results.append(
                    {
                        "target": target,
                        "split_name": split_name,
                        "model": "majority_baseline",
                        "train_rows": int(train_mask.sum()),
                        "test_rows": int(test_mask.sum()),
                        "majority_class": majority,
                        **metrics,
                    }
                )

            for model_name, model in models().items():
                pipe = Pipeline([("preprocess", build_preprocessor(x)), ("model", model)])
                try:
                    pipe.fit(x.loc[train_mask], y_train)
                    pred = pipe.predict(x.loc[test_mask])
                except Exception as exc:
                    results.append(
                        {
                            "target": target,
                            "split_name": split_name,
                            "model": model_name,
                            "train_rows": int(train_mask.sum()),
                            "test_rows": int(test_mask.sum()),
                            "error": str(exc),
                        }
                    )
                    continue
                results.append(
                    {
                        "target": target,
                        "split_name": split_name,
                        "model": model_name,
                        "train_rows": int(train_mask.sum()),
                        "test_rows": int(test_mask.sum()),
                        "majority_class": "",
                        **metric_dict(y_test, pred),
                    }
                )
                imp = collect_importances(pipe, model_name, target, split_name, features)
                if not imp.empty:
                    importances.append(imp)
                if model_name == "decision_tree":
                    try:
                        tree = pipe.named_steps["model"]
                        names = transformed_feature_names(pipe, features)
                        rule_chunks.append(
                            f"\n## target={target} split={split_name}\n"
                            + export_text(tree, feature_names=[str(n)[:80] for n in names], max_depth=5)
                        )
                    except Exception:
                        pass
    result_df = pd.DataFrame(results)
    importance_df = pd.concat(importances, ignore_index=True, sort=False) if importances else pd.DataFrame()
    return result_df, importance_df, "\n".join(rule_chunks)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(OUTPUT_ROOT))
    parser.add_argument("--max-rows", type=int, default=30000)
    args = parser.parse_args()
    root = Path(args.root)
    df = load_data(root)
    results, importances, rules = fit_and_eval(df, args.max_rows)
    results.to_csv(root / "model_probe_results.csv", index=False)
    importances.to_csv(root / "policy_feature_importance.csv", index=False)
    (root / "policy_rule_candidates.txt").write_text(rules or "No decision-tree rules were produced.\n", encoding="utf-8")
    print(f"[DONE] wrote Phase 8A model probe outputs under {root}")


if __name__ == "__main__":
    main()
