import argparse
import copy
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.append(str(Path(__file__).resolve().parent))

from data.cdnet_loader import scan_cdnet
from detectors.detectors import create_detector
from run_experiment import build_research_summary, ensure, process_sequence, unpack_sequence_result


GRID = [
    {"config_id": "A", "reuse_max_eval_age": 3, "sample_interval": 5, "open_threshold": 0.65},
    {"config_id": "B", "reuse_max_eval_age": 5, "sample_interval": 5, "open_threshold": 0.65},
    {"config_id": "C", "reuse_max_eval_age": 5, "sample_interval": 8, "open_threshold": 0.70},
    {"config_id": "D", "reuse_max_eval_age": 8, "sample_interval": 8, "open_threshold": 0.70},
    {"config_id": "E", "reuse_max_eval_age": 8, "sample_interval": 10, "open_threshold": 0.75},
]


def normalized(series):
    min_v = float(series.min())
    max_v = float(series.max())
    if max_v <= min_v:
        return pd.Series([1.0] * len(series), index=series.index)
    return (series - min_v) / (max_v - min_v)


def summarize_config(config_id, params, event_rows, pixel_rows, edge_rows):
    research = build_research_summary(event_rows, pixel_rows, edge_rows)
    if research.empty:
        row = {
            "config_id": config_id,
            "reuse_max_eval_age": params["reuse_max_eval_age"],
            "sample_interval": params["sample_interval"],
            "open_threshold": params["open_threshold"],
            "FMeasure": 0.0,
            "Event_F1": 0.0,
            "Activation": 0.0,
            "Avg_FPS": 0.0,
            "P95_latency": 0.0,
            "Reuse_rate": 0.0,
            "reused_prediction_count": 0,
        }
        return row

    return {
        "config_id": config_id,
        "reuse_max_eval_age": params["reuse_max_eval_age"],
        "sample_interval": params["sample_interval"],
        "open_threshold": params["open_threshold"],
        "FMeasure": float(research["FMeasure"].mean()),
        "Event_F1": float(research["Event_F1"].mean()),
        "Activation": float(research["YOLO_activation_rate"].mean()),
        "Avg_FPS": float(research["avg_FPS"].mean()),
        "P95_latency": float(research["P95_latency_ms"].mean()),
        "Reuse_rate": float(research["reused_prediction_rate"].mean()),
        "reused_prediction_count": int(research.get("reused_prediction_count", pd.Series([0])).sum()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/q2_core_6categories_debug.yaml")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        base_cfg = yaml.safe_load(f)

    base_exp = base_cfg.get("experiment_name", "q2_core_6categories_debug")
    output_root = Path(base_cfg.get("output_root", "outputs"))
    final_out_dir = ensure(output_root / base_exp)
    grid_out_dir = ensure(final_out_dir / "grid_search")

    sequences = scan_cdnet(base_cfg["dataset_root"], base_cfg["categories"], base_cfg.get("videos", "auto"))
    if not sequences:
        print("[ERROR] No sequences found. Check dataset_root/categories.")
        return

    detector = create_detector(
        base_cfg.get("detector_mode", "mock"),
        base_cfg.get("model_path", ""),
        base_cfg.get("model_name", "mock_detector"),
    )

    result_rows = []
    for params in GRID:
        cfg = copy.deepcopy(base_cfg)
        cfg["experiment_name"] = f"{base_exp}/grid_search/{params['config_id']}"
        cfg["pipelines"] = ["P4_EFFICIENT_REUSE"]
        cfg.setdefault("evaluation", {})
        cfg["evaluation"]["use_temporal_roi"] = True
        cfg["evaluation"]["warmup_frames"] = 50
        cfg["evaluation"]["frame_step"] = 10
        cfg["evaluation"]["max_frames_per_video"] = 500
        cfg["evaluation"]["save_binary_masks"] = False
        cfg["evaluation"]["save_qualitative_samples"] = False
        cfg.setdefault("p4_efficient", {})
        cfg["p4_efficient"].update({
            "reuse_max_eval_age": params["reuse_max_eval_age"],
            "reuse_max_raw_age": None,
            "sample_interval": params["sample_interval"],
            "open_threshold": params["open_threshold"],
        })

        print(
            f"\n[GRID {params['config_id']}] "
            f"reuse_max_eval_age={params['reuse_max_eval_age']} | "
            f"sample_interval={params['sample_interval']} | "
            f"open_threshold={params['open_threshold']}"
        )

        event_rows, pixel_rows, edge_rows = [], [], []
        for seq in sequences:
            print(f"  [SEQ] {seq['category']}/{seq['video']}")
            ev, px, ed, _ = unpack_sequence_result(process_sequence(cfg, seq, "P4_EFFICIENT_REUSE", detector))
            event_rows.append(ev)
            pixel_rows.append(px)
            edge_rows.append(ed)
            print(
                f"    EventF1={ev.get('Event_F1', 0):.3f} | "
                f"FMeasure={px.get('FMeasure', 0):.3f} | "
                f"Activation={ed.get('YOLO_activation_rate', 0):.3f} | "
                f"Reuse={ed.get('reused_prediction_rate', 0):.3f}"
            )

        run_dir = output_root / cfg["experiment_name"]
        ensure(run_dir)
        pd.DataFrame(event_rows).to_csv(run_dir / "summary_event_metrics.csv", index=False)
        pd.DataFrame(pixel_rows).to_csv(run_dir / "summary_pixel_metrics.csv", index=False)
        pd.DataFrame(edge_rows).to_csv(run_dir / "summary_edge_metrics.csv", index=False)
        research = build_research_summary(event_rows, pixel_rows, edge_rows)
        research.to_csv(run_dir / "summary_research_metrics.csv", index=False)

        result_rows.append(summarize_config(params["config_id"], params, event_rows, pixel_rows, edge_rows))

    results = pd.DataFrame(result_rows)
    results["normalized_Avg_FPS"] = normalized(results["Avg_FPS"])
    results["Research_Score"] = (
        0.4 * results["FMeasure"]
        + 0.3 * results["Event_F1"]
        + 0.2 * (1.0 - results["Activation"])
        + 0.1 * results["normalized_Avg_FPS"]
    )
    results = results.sort_values("Research_Score", ascending=False)
    out_path = final_out_dir / "p4_reuse_grid_search.csv"
    results.to_csv(out_path, index=False)

    print(f"\n[DONE] {out_path}")
    print("\n[TOP 3]")
    cols = [
        "config_id",
        "reuse_max_eval_age",
        "sample_interval",
        "open_threshold",
        "FMeasure",
        "Event_F1",
        "Activation",
        "Avg_FPS",
        "Reuse_rate",
        "Research_Score",
    ]
    print(results[cols].head(3).to_string(index=False, float_format=lambda x: f"{x:.4f}"))


if __name__ == "__main__":
    main()
