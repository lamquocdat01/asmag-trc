import argparse
import json
import pickle
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import train_phase8b_policy_models as train8b
from tools import train_phase8c_subrisk_shadow_models as subrisk


PHASE8A_ROOT = Path("outputs/phase8a_policy_dataset")
SUBRISK_ROOT = Path("outputs/phase8c_subrisk_models")
OUTPUT_DIR = SUBRISK_ROOT / "runtime_models"
RUNTIME_THRESHOLD_FLOORS = {
    "closed_empty_risk": 0.9999,
    "reuse_risk": 0.9999,
    "lightweight_p3_risk": 0.99,
    "legacy_cadence_risk": 0.99,
    "detector_needed": 0.99,
}


def build_model(model_name):
    models = subrisk.model_defs()
    if model_name not in models or models[model_name] is None:
        model_name = "logistic_regression"
    return model_name, subrisk.make_pipeline(models[model_name])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase8a-root", default=str(PHASE8A_ROOT))
    parser.add_argument("--subrisk-root", default=str(SUBRISK_ROOT))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--max-rows", type=int, default=80000)
    args = parser.parse_args()

    phase8a_root = Path(args.phase8a_root)
    subrisk_root = Path(args.subrisk_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rec_path = subrisk_root / "subrisk_runtime_model_recommendation.csv"
    if not rec_path.exists():
        raise RuntimeError(f"missing recommendations: {rec_path}")
    recs = pd.read_csv(rec_path).set_index("target")

    data, _, _, _, _ = train8b.load_phase8a(phase8a_root)
    labels = subrisk.derive_subrisk_labels(data)
    for col in labels.columns:
        data[col] = labels[col]
    features = subrisk.feature_names()

    manifest = {
        "phase": "8C-1D-subrisk-lightweight-shadow",
        "runtime_model_set": "subrisk_lightweight",
        "source_phase8a_root": str(phase8a_root),
        "source_subrisk_root": str(subrisk_root),
        "features": features,
        "models": {},
        "runtime_threshold_floors": RUNTIME_THRESHOLD_FLOORS,
        "shadow_only": True,
        "broad_unsafe_action_runtime_model": "excluded",
    }

    for target in subrisk.SUBRISK_TARGETS:
        if target not in recs.index:
            raise RuntimeError(f"missing recommendation for {target}")
        row = recs.loc[target]
        model_name, pipe = build_model(str(row["recommended_model"]))
        threshold = max(float(row["recommended_threshold"]), float(RUNTIME_THRESHOLD_FLOORS.get(target, 0.0)))
        target_df = subrisk.target_sample(data, target, args.max_rows)
        x = target_df[features].apply(pd.to_numeric, errors="coerce")
        y = target_df[target].astype(int)
        if y.nunique() < 2:
            raise RuntimeError(f"target {target} has a single label after sampling")
        pipe.fit(x, y)
        model = pipe.named_steps.get("model")
        if hasattr(model, "n_jobs"):
            model.n_jobs = 1
        classes = [str(c) for c in getattr(model, "classes_", [])]
        class_mapping = {label: idx for idx, label in enumerate(classes)}
        artifact = {
            "target": target,
            "model_type": model_name,
            "pipeline": pipe,
            "feature_names": features,
            "features": features,
            "classes": classes,
            "class_mapping": class_mapping,
            "positive_class": "1",
            "positive_class_index": class_mapping.get("1"),
            "threshold": threshold,
            "label_distribution": y.value_counts().sort_index().astype(int).to_dict(),
            "max_rows": args.max_rows,
            "shadow_only": True,
        }
        path = output_dir / f"{target}.pkl"
        with path.open("wb") as f:
            pickle.dump(artifact, f)
        manifest["models"][target] = {
            "target": target,
            "model_type": model_name,
            "path": str(path),
            "classes": classes,
            "class_mapping": class_mapping,
            "positive_class": "1",
            "positive_class_index": class_mapping.get("1"),
            "threshold": threshold,
            "label_distribution": artifact["label_distribution"],
        }

    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    pd.Series(features, name="feature").to_csv(output_dir / "shadow_feature_schema.csv", index=False)
    print(f"[DONE] exported Phase 8C sub-risk runtime models under {output_dir}")


if __name__ == "__main__":
    main()
