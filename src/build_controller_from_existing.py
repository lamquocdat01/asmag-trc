import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.append(str(Path(__file__).resolve().parent))

from metrics.cdnet_pixel_metrics import build_cdnet_metrics_summary
from metrics.edge_energy_metrics import summarize_edge_energy
from metrics.object_level_metrics import build_object_group_summary
from metrics.pareto_metrics import write_pareto_metrics
from run_experiment import (
    CONTROLLER_MODE_TO_PIPELINE,
    build_group_summary,
    build_research_summary,
    controller_mode_for_category,
    ensure,
)
from visualization.plots import create_summary_charts


BASE_PIPELINES = ["P2_FrameDiff", "P3_MOG2", "ASMAG_TR_ACC", "ASMAG_TR_FAST"]
OUTPUT_PIPELINES = [*BASE_PIPELINES, "ASMAG_TR_CONTROLLER"]


def read_csv(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def copy_pipeline_raw(source_root, target_root, category, video, pipeline):
    src = source_root / "raw_results" / category / video / pipeline
    dst = target_root / "raw_results" / category / video / pipeline
    if dst.exists():
        return
    if not src.exists():
        raise FileNotFoundError(src)
    ensure(dst.parent)
    shutil.copytree(src, dst)


def copy_controller_raw(source_root, target_root, category, video):
    mode = controller_mode_for_category(category)
    source_pipeline = CONTROLLER_MODE_TO_PIPELINE[mode]
    src = source_root / "raw_results" / category / video / source_pipeline
    dst = ensure(target_root / "raw_results" / category / video / "ASMAG_TR_CONTROLLER")
    if not src.exists():
        raise FileNotFoundError(src)

    for item in src.iterdir():
        if item.is_dir():
            out_dir = dst / item.name
            if not out_dir.exists():
                shutil.copytree(item, out_dir)
            continue
        if item.suffix.lower() != ".csv":
            shutil.copy2(item, dst / item.name)
            continue
        df = pd.read_csv(item)
        if "pipeline" in df.columns:
            df["pipeline"] = "ASMAG_TR_CONTROLLER"
        if item.name == "frame_metrics.csv":
            df["selected_mode"] = mode
            df["category_policy_mode"] = mode
            df["used_p3_fallback"] = int(mode == "P3_FALLBACK")
            df["used_acc"] = int(mode == "ACC")
            df["used_fast"] = int(mode == "FAST")
            if "yolo_called" in df.columns:
                df["activation"] = df["yolo_called"]
            if "energy_frame" in df.columns:
                df["energy_proxy"] = df["energy_frame"]
        df.to_csv(dst / item.name, index=False)


def collect_sequence_rows(target_root):
    event_rows, pixel_rows, edge_rows, object_rows, frame_rows = [], [], [], [], []
    for frame_path in target_root.glob("raw_results/*/*/*/frame_metrics.csv"):
        frame_rows.extend(pd.read_csv(frame_path).to_dict("records"))
    for root in target_root.glob("raw_results/*/*/*"):
        if not root.is_dir():
            continue
        paths = {
            "event": root / "sequence_event_summary.csv",
            "pixel": root / "sequence_pixel_summary.csv",
            "edge": root / "sequence_edge_summary.csv",
            "object": root / "sequence_object_summary.csv",
        }
        if all(path.exists() for path in paths.values()):
            event_rows.append(pd.read_csv(paths["event"]).iloc[0].to_dict())
            pixel_rows.append(pd.read_csv(paths["pixel"]).iloc[0].to_dict())
            edge_rows.append(pd.read_csv(paths["edge"]).iloc[0].to_dict())
            object_rows.append(pd.read_csv(paths["object"]).iloc[0].to_dict())
    return event_rows, pixel_rows, edge_rows, object_rows, frame_rows


def write_controller_mode_usage(target_root):
    summary = read_csv(target_root / "summary_by_video.csv")
    energy = read_csv(target_root / "summary_edge_energy_metrics.csv")
    objects = read_csv(target_root / "summary_object_metrics.csv")

    ctrl = summary[summary["pipeline"] == "ASMAG_TR_CONTROLLER"].copy()
    energy_video = energy[
        (energy["aggregation_level"] == "video")
        & (energy["pipeline"] == "ASMAG_TR_CONTROLLER")
    ][["category", "video", "Estimated_energy_per_frame", "processed_frames"]]
    obj = objects[objects["pipeline"] == "ASMAG_TR_CONTROLLER"][
        ["category", "video", "mAP_50"]
    ]

    ctrl = ctrl.merge(energy_video, on=["category", "video"], how="left")
    ctrl = ctrl.merge(obj, on=["category", "video"], how="left")
    ctrl["selected_mode"] = ctrl["category"].map(controller_mode_for_category)
    ctrl["frames"] = ctrl.get("evaluated_frames", ctrl["processed_frames"])
    out = pd.DataFrame(
        {
            "category": ctrl["category"],
            "video": ctrl["video"],
            "selected_mode": ctrl["selected_mode"],
            "frames": ctrl["frames"],
            "activation": ctrl["YOLO_activation_rate"],
            "energy_per_frame": ctrl["Estimated_energy_per_frame"],
            "FMeasure": ctrl["FMeasure"],
            "Event_F1": ctrl["Event_F1"],
            "mAP_50": ctrl["mAP_50"],
            "reuse_rate": ctrl["reused_prediction_rate"],
        }
    )
    out.to_csv(target_root / "controller_mode_usage.csv", index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="outputs/full_cdnet2014_sampled_full_metrics")
    parser.add_argument("--target", default="outputs/full_cdnet2014_controller_sampled_metrics")
    parser.add_argument("--config", default="configs/full_cdnet2014_controller_sampled_metrics.yaml")
    args = parser.parse_args()

    source_root = Path(args.source)
    target_root = ensure(args.target)
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    source_summary = read_csv(source_root / "summary_by_video.csv")
    sequences = (
        source_summary[["category", "video"]]
        .drop_duplicates()
        .sort_values(["category", "video"])
        .to_dict("records")
    )

    for seq in sequences:
        category, video = seq["category"], seq["video"]
        for pipeline in BASE_PIPELINES:
            copy_pipeline_raw(source_root, target_root, category, video, pipeline)
        copy_controller_raw(source_root, target_root, category, video)

    event_rows, pixel_rows, edge_rows, object_rows, frame_rows = collect_sequence_rows(target_root)
    pd.DataFrame(event_rows).to_csv(target_root / "summary_event_metrics.csv", index=False)
    pd.DataFrame(pixel_rows).to_csv(target_root / "summary_pixel_metrics.csv", index=False)
    pd.DataFrame(edge_rows).to_csv(target_root / "summary_edge_metrics.csv", index=False)
    pd.DataFrame(object_rows).to_csv(target_root / "summary_object_metrics.csv", index=False)

    build_cdnet_metrics_summary(frame_rows).to_csv(target_root / "summary_cdnet_metrics.csv", index=False)
    summarize_edge_energy(frame_rows, cfg.get("energy_proxy", {})).to_csv(
        target_root / "summary_edge_energy_metrics.csv", index=False
    )

    research_summary = build_research_summary(event_rows, pixel_rows, edge_rows)
    research_summary.to_csv(target_root / "summary_research_metrics.csv", index=False)
    build_group_summary(research_summary, ["category", "pipeline"]).to_csv(
        target_root / "summary_by_category.csv", index=False
    )
    build_group_summary(research_summary, ["category", "video", "pipeline"]).to_csv(
        target_root / "summary_by_video.csv", index=False
    )
    pd.DataFrame(build_object_group_summary(object_rows, ["pipeline"])).to_csv(
        target_root / "summary_object_by_pipeline.csv", index=False
    )
    pd.DataFrame(build_object_group_summary(object_rows, ["category", "pipeline"])).to_csv(
        target_root / "summary_object_by_category.csv", index=False
    )
    pd.DataFrame(build_object_group_summary(object_rows, ["category", "video", "pipeline"])).to_csv(
        target_root / "summary_object_by_video.csv", index=False
    )

    write_pareto_metrics(target_root, cfg.get("pareto", {}))
    create_summary_charts(target_root)
    write_controller_mode_usage(target_root)

    print(f"[DONE] Built ASMAG_TR_CONTROLLER output at {target_root}")


if __name__ == "__main__":
    main()
