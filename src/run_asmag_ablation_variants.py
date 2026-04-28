import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.append(str(Path(__file__).resolve().parent))

from data.cdnet_loader import scan_cdnet
from detectors.detectors import create_detector
from run_experiment import (
    build_asmag_ablation_table,
    build_research_summary,
    ensure,
    process_sequence,
    unpack_sequence_result,
)


ABLATION_PIPELINES = [
    "P4_PRECISION",
    "P4_BALANCED",
    "P4_EFFICIENT",
    "P4_EFFICIENT_REUSE",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/q2_core_6categories_debug.yaml")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    out_root = ensure(Path(cfg.get("output_root", "outputs")) / cfg["experiment_name"])
    sequences = scan_cdnet(cfg["dataset_root"], cfg["categories"], cfg.get("videos", "auto"))
    if not sequences:
        print("[ERROR] No sequences found. Check dataset_root/categories.")
        return

    detector = create_detector(
        cfg.get("detector_mode", "mock"),
        cfg.get("model_path", ""),
        cfg.get("model_name", "mock_detector"),
    )

    event_rows, pixel_rows, edge_rows = [], [], []
    for seq in sequences:
        print(f"\n[SEQ] {seq['category']}/{seq['video']}")
        for pipeline in ABLATION_PIPELINES:
            print(f"  - Running {pipeline} ...")
            ev, px, ed, _ = unpack_sequence_result(process_sequence(cfg, seq, pipeline, detector))
            event_rows.append(ev)
            pixel_rows.append(px)
            edge_rows.append(ed)
            print(
                f"    EventF1={ev.get('Event_F1', 0):.3f} | "
                f"FMeasure={px.get('FMeasure', 0):.3f} | "
                f"Activation={ed.get('YOLO_activation_rate', 0):.3f}"
            )

    ablation_research = build_research_summary(event_rows, pixel_rows, edge_rows)
    ablation_path = out_root / "asmag_ablation_variant_metrics.csv"
    ablation_research.to_csv(ablation_path, index=False)

    main_path = out_root / "summary_research_metrics.csv"
    if main_path.exists():
        main_research = pd.read_csv(main_path)
        combined = pd.concat([main_research, ablation_research], ignore_index=True)
    else:
        combined = ablation_research

    table = build_asmag_ablation_table(combined)
    table.to_csv(out_root / "asmag_ablation_table.csv", index=False)
    print(f"\n[DONE] {ablation_path}")
    print(f"[DONE] {out_root / 'asmag_ablation_table.csv'}")


if __name__ == "__main__":
    main()
