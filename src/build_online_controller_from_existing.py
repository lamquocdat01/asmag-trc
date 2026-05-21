import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.append(str(Path(__file__).resolve().parent))

from metrics.cdnet_pixel_metrics import build_cdnet_metrics_summary
from metrics.edge_energy_metrics import summarize_edge_energy
from metrics.metrics import aggregate_pixel, summarize_event
from metrics.pareto_metrics import write_pareto_metrics
from run_experiment import (
    CONTROLLER_MODE_TO_PIPELINE,
    OnlineSceneDifficultyEstimator,
    build_group_summary,
    build_research_summary,
    controller_mode_for_category,
    ensure,
)
from visualization.plots import create_summary_charts


BASELINE_PIPELINES = ["P3_MOG2", "ASMAG_TR_CONTROLLER", "ASMAG_TR_CONTROLLER_ONLINE"]
SOURCE_BY_MODE = {
    "FAST": "ASMAG_TR_FAST",
    "ACC": "ASMAG_TR_ACC",
    "P3_FALLBACK": "P3_MOG2",
}


def sequence_keys(summary_path):
    summary = pd.read_csv(summary_path)
    return (
        summary[["category", "video"]]
        .drop_duplicates()
        .sort_values(["category", "video"])
        .to_dict("records")
    )


def read_frame_metrics(root, category, video, pipeline):
    path = root / "raw_results" / category / video / pipeline / "frame_metrics.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def copy_sequence(source_root, target_root, category, video, source_pipeline, target_pipeline):
    src = source_root / "raw_results" / category / video / source_pipeline
    dst = ensure(target_root / "raw_results" / category / video / target_pipeline)
    for item in src.iterdir():
        if item.name == "frame_metrics.csv":
            continue
        if item.is_dir():
            out_dir = dst / item.name
            if not out_dir.exists():
                shutil.copytree(item, out_dir)
            continue
        df = pd.read_csv(item) if item.suffix.lower() == ".csv" else None
        if df is not None and "pipeline" in df.columns:
            df["pipeline"] = target_pipeline
            df.to_csv(dst / item.name, index=False)
        else:
            shutil.copy2(item, dst / item.name)


def build_category_controller(source_root, target_root, category, video):
    mode = controller_mode_for_category(category)
    source_pipeline = CONTROLLER_MODE_TO_PIPELINE[mode]
    copy_sequence(source_root, target_root, category, video, source_pipeline, "ASMAG_TR_CONTROLLER")
    frame_df = read_frame_metrics(source_root, category, video, source_pipeline).copy()
    frame_df["pipeline"] = "ASMAG_TR_CONTROLLER"
    frame_df["selected_mode"] = mode
    frame_df["category_policy_mode"] = mode
    frame_df["used_p3_fallback"] = int(mode == "P3_FALLBACK")
    frame_df["used_acc"] = int(mode == "ACC")
    frame_df["used_fast"] = int(mode == "FAST")
    frame_df["activation"] = frame_df.get("yolo_called", 0)
    frame_df["energy_proxy"] = frame_df.get("energy_frame", 0)
    out = ensure(target_root / "raw_results" / category / video / "ASMAG_TR_CONTROLLER")
    frame_df.to_csv(out / "frame_metrics.csv", index=False)


def build_online_sequence(source_root, target_root, category, video, online_cfg):
    sources = {
        "FAST": read_frame_metrics(source_root, category, video, "ASMAG_TR_FAST"),
        "ACC": read_frame_metrics(source_root, category, video, "ASMAG_TR_ACC"),
        "P3_FALLBACK": read_frame_metrics(source_root, category, video, "P3_MOG2"),
    }
    telemetry = sources["ACC"].copy()
    estimator = OnlineSceneDifficultyEstimator(online_cfg)
    rows = []
    for i, tel in telemetry.iterrows():
        gate_info = tel.to_dict()
        if "image_area" not in gate_info:
            fg = float(tel.get("TP_pixel", 0) + tel.get("TN_pixel", 0) + tel.get("FP_pixel", 0) + tel.get("FN_pixel", 0))
            gate_info["image_area"] = max(1.0, fg)
        features = estimator.update(
            gate_info,
            bool(tel.get("gate_open", 0)),
            int(tel.get("reused_prediction", 0)),
            int(tel.get("Is_Active", 0)),
            int(tel.get("evaluated_index", i)),
        )
        mode = features["selected_mode"]
        source_row = sources[mode].iloc[i].copy()
        source_row["pipeline"] = "ASMAG_TR_CONTROLLER_ONLINE"
        source_row["selected_mode"] = mode
        source_row["category_policy_mode"] = "ONLINE"
        source_row["used_p3_fallback"] = int(mode == "P3_FALLBACK")
        source_row["used_acc"] = int(mode == "ACC")
        source_row["used_fast"] = int(mode == "FAST")
        source_row["activation"] = source_row.get("yolo_called", 0)
        source_row["energy_proxy"] = source_row.get("energy_frame", 0)
        for key, value in features.items():
            source_row[key] = value
        rows.append(source_row.to_dict())
    out = ensure(target_root / "raw_results" / category / video / "ASMAG_TR_CONTROLLER_ONLINE")
    frame_df = pd.DataFrame(rows)
    frame_df.to_csv(out / "frame_metrics.csv", index=False)
    px_cols = [
        "TP_pixel", "TN_pixel", "FP_pixel", "FN_pixel", "Recall", "Specificity",
        "FPR", "FNR", "Precision", "FMeasure", "PWC",
    ]
    pxsum = aggregate_pixel(frame_df[px_cols].to_dict("records"))
    ev = summarize_event(frame_df)
    edge = {
        "avg_CPU": float(frame_df["CPU_Usage"].mean()) if "CPU_Usage" in frame_df else 0,
        "median_CPU": float(frame_df["CPU_Usage"].median()) if "CPU_Usage" in frame_df else 0,
        "avg_RAM": float(frame_df["RAM_Usage"].mean()) if "RAM_Usage" in frame_df else 0,
        "avg_FPS": float(frame_df["FPS"].mean()) if "FPS" in frame_df else 0,
        "median_FPS": float(frame_df["FPS"].median()) if "FPS" in frame_df else 0,
        "P95_latency_ms": float(frame_df["latency_ms"].quantile(0.95)) if "latency_ms" in frame_df else 0,
        "YOLO_activation_rate": float(frame_df["yolo_called"].mean()),
        "processed_frames": len(frame_df),
        "temporal_roi_start": "",
        "temporal_roi_end": "",
        "evaluated_frames": len(frame_df),
        "skipped_frames_before_roi": "",
        "warmup_frames": "",
        "reused_prediction_count": int(frame_df["reused_prediction"].sum()),
        "reused_prediction_rate": float(frame_df["reused_prediction"].mean()),
    }
    common = {"category": category, "video": video, "pipeline": "ASMAG_TR_CONTROLLER_ONLINE"}
    pd.DataFrame([{**common, **ev}]).to_csv(out / "sequence_event_summary.csv", index=False)
    pd.DataFrame([{**common, **pxsum}]).to_csv(out / "sequence_pixel_summary.csv", index=False)
    pd.DataFrame([{**common, **edge}]).to_csv(out / "sequence_edge_summary.csv", index=False)

    mode_counts = frame_df["selected_mode"].value_counts()
    obj_source = mode_counts.idxmax() if not mode_counts.empty else "P3_FALLBACK"
    obj_path = source_root / "raw_results" / category / video / SOURCE_BY_MODE[obj_source] / "sequence_object_summary.csv"
    obj = pd.read_csv(obj_path).iloc[0].to_dict()
    obj["pipeline"] = "ASMAG_TR_CONTROLLER_ONLINE"
    pd.DataFrame([obj]).to_csv(out / "sequence_object_summary.csv", index=False)


def collect(target_root):
    event_rows, pixel_rows, edge_rows, object_rows, frame_rows = [], [], [], [], []
    for root in target_root.glob("raw_results/*/*/*"):
        if not root.is_dir():
            continue
        frame_path = root / "frame_metrics.csv"
        if frame_path.exists():
            frame_rows.extend(pd.read_csv(frame_path).to_dict("records"))
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="outputs/q2_core_extended_full_metrics")
    parser.add_argument("--target", default="outputs/q2_core_extended_online_controller_sim")
    parser.add_argument("--config", default="configs/q2_core_extended_online_controller.yaml")
    args = parser.parse_args()

    source_root = Path(args.source)
    target_root = ensure(args.target)
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    sequences = sequence_keys(source_root / "summary_by_video.csv")

    for seq in sequences:
        category, video = seq["category"], seq["video"]
        copy_sequence(source_root, target_root, category, video, "P3_MOG2", "P3_MOG2")
        frame_p3 = read_frame_metrics(source_root, category, video, "P3_MOG2")
        p3_out = ensure(target_root / "raw_results" / category / video / "P3_MOG2")
        frame_p3.to_csv(p3_out / "frame_metrics.csv", index=False)
        build_category_controller(source_root, target_root, category, video)
        build_online_sequence(source_root, target_root, category, video, cfg.get("online_controller", {}))

    event_rows, pixel_rows, edge_rows, object_rows, frame_rows = collect(target_root)
    pd.DataFrame(event_rows).to_csv(target_root / "summary_event_metrics.csv", index=False)
    pd.DataFrame(pixel_rows).to_csv(target_root / "summary_pixel_metrics.csv", index=False)
    pd.DataFrame(edge_rows).to_csv(target_root / "summary_edge_metrics.csv", index=False)
    pd.DataFrame(object_rows).to_csv(target_root / "summary_object_metrics.csv", index=False)
    build_cdnet_metrics_summary(frame_rows).to_csv(target_root / "summary_cdnet_metrics.csv", index=False)
    summarize_edge_energy(frame_rows, cfg.get("energy_proxy", {})).to_csv(target_root / "summary_edge_energy_metrics.csv", index=False)
    research = build_research_summary(event_rows, pixel_rows, edge_rows)
    research.to_csv(target_root / "summary_research_metrics.csv", index=False)
    build_group_summary(research, ["category", "pipeline"]).to_csv(target_root / "summary_by_category.csv", index=False)
    build_group_summary(research, ["category", "video", "pipeline"]).to_csv(target_root / "summary_by_video.csv", index=False)
    write_pareto_metrics(target_root, cfg.get("pareto", {}))
    create_summary_charts(target_root)
    print(f"[DONE] Built online-controller simulation at {target_root}")


if __name__ == "__main__":
    main()
