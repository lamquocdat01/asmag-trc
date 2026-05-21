import argparse
import json
import pickle
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import train_phase8b_policy_models as train8b


DEFAULT_TARGET_MODELS = {
    "detector_needed": "logistic_regression",
    "unsafe_action": "random_forest",
    "reuse_allowed": "logistic_regression",
    "lightweight_allowed": "random_forest",
    "risk_class": "random_forest",
    "detector_floor_needed": "decision_tree",
}


def selected_model_for_target(results: pd.DataFrame, target: str) -> str:
    target_rows = results[results["target"].eq(target)].copy()
    if target_rows.empty:
        return DEFAULT_TARGET_MODELS[target]
    grouped = (
        target_rows.groupby("model", as_index=False)
        .agg(mean_balanced_accuracy=("balanced_accuracy", "mean"), evaluated_splits=("split_name", "nunique"))
        .sort_values(["mean_balanced_accuracy", "evaluated_splits"], ascending=False)
    )
    grouped = grouped[grouped["model"].ne("majority_baseline")]
    if grouped.empty:
        return DEFAULT_TARGET_MODELS[target]
    return str(grouped.iloc[0]["model"])


def fit_shadow_model(data: pd.DataFrame, features: list[str], target: str, model_name: str, max_rows: int):
    models = train8b.model_defs()
    if model_name not in models or models[model_name] is None:
        model_name = DEFAULT_TARGET_MODELS[target]
    target_df = train8b.prepare_target_df(data, target, max_rows)
    if target_df.empty or target_df[target].fillna("").astype(str).nunique() < 2:
        raise RuntimeError(f"target {target} has insufficient labels for export")
    x = target_df[features].apply(pd.to_numeric, errors="coerce")
    y = target_df[target].fillna("").astype(str)
    pipe = train8b.make_pipeline(models[model_name])
    pipe.fit(x, y)
    model = pipe.named_steps.get("model")
    if hasattr(model, "n_jobs"):
        model.n_jobs = 1
    return pipe, target_df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase8a-root", default="outputs/phase8a_policy_dataset")
    parser.add_argument("--phase8b-root", default="outputs/phase8b_policy_training")
    parser.add_argument("--output-dir", default="outputs/phase8b_policy_training/models")
    parser.add_argument("--max-rows", type=int, default=30000)
    args = parser.parse_args()

    phase8a_root = Path(args.phase8a_root)
    phase8b_root = Path(args.phase8b_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data, _, _, _, _ = train8b.load_phase8a(phase8a_root)
    features = train8b.choose_features(data)
    results_path = phase8b_root / "model_results.csv"
    results = pd.read_csv(results_path) if results_path.exists() else pd.DataFrame()

    manifest = {
        "phase": "8C-1-shadow-mode",
        "source_phase8a_root": str(phase8a_root),
        "source_phase8b_root": str(phase8b_root),
        "features": features,
        "models": {},
        "excluded_runtime_selectors": ["action_ranker_high_risk_only", "action_ranker_ptz_only"],
    }

    for target in DEFAULT_TARGET_MODELS:
        model_name = selected_model_for_target(results, target)
        pipe, target_df = fit_shadow_model(data, features, target, model_name, args.max_rows)
        artifact = {
            "target": target,
            "model_name": model_name,
            "pipeline": pipe,
            "features": features,
            "classes": [str(c) for c in pipe.named_steps["model"].classes_],
            "label_distribution": target_df[target].fillna("").astype(str).value_counts().to_dict(),
            "max_rows": args.max_rows,
            "shadow_only": True,
        }
        artifact_path = output_dir / f"{target}.pkl"
        with artifact_path.open("wb") as f:
            pickle.dump(artifact, f)
        manifest["models"][target] = {
            "model_name": model_name,
            "path": str(artifact_path),
            "classes": artifact["classes"],
            "label_distribution": artifact["label_distribution"],
        }

    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    pd.Series(features, name="feature").to_csv(output_dir / "shadow_feature_schema.csv", index=False)
    print(f"[DONE] exported Phase 8B shadow models under {output_dir}")


if __name__ == "__main__":
    main()
