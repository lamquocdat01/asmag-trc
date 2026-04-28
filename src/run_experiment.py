import os, sys, time, argparse
from pathlib import Path
import yaml
import cv2
import numpy as np
import pandas as pd
import psutil

# allow running from project root
sys.path.append(str(Path(__file__).resolve().parent))

from data.cdnet_loader import (
    frame_number,
    scan_cdnet,
    list_frames,
    read_frame,
    read_gt,
    read_gt_for_frame,
    make_synthetic_sequence,
)
from detectors.detectors import create_detector
from evaluation.mask_to_boxes import mask_to_boxes
from gating.gates import (
    FrameDiffGate,
    MOG2Gate,
    ASMAGPlusGate,
    ASMAGPlusPrecisionGate,
    ASMAGPlusBalancedGate,
    ASMAGPlusEfficientGate,
)
from metrics.metrics import pixel_metrics, event_state_from_masks, summarize_event, aggregate_pixel, valid_gt_mask
from metrics.cdnet_pixel_metrics import build_cdnet_metrics_summary
from metrics.edge_energy_metrics import energy_usage_flags, frame_energy, summarize_edge_energy
from metrics.object_level_metrics import (
    assign_proxy_scores,
    build_object_group_summary,
    object_counts_at_threshold,
    summarize_object_records,
)
from metrics.pareto_metrics import write_pareto_metrics
from visualization.plots import create_summary_charts

PIPELINE_ALIASES = {
    "P4_PRECISION": "P4_ASMAG_PLUS_PRECISION",
    "P4_BALANCED": "P4_ASMAG_PLUS_BALANCED",
    "P4_EFFICIENT": "P4_ASMAG_PLUS_EFFICIENT",
    "P4_EFFICIENT_REUSE": "P4_ASMAG_PLUS_EFFICIENT_REUSE",
    "ASMAG_TR_ACC": "P4_ASMAG_PLUS_EFFICIENT_REUSE",
    "ASMAG_TR_FAST": "P4_ASMAG_PLUS_EFFICIENT_REUSE",
}

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

CONTROLLER_MODE_TO_PIPELINE = {
    "FAST": "ASMAG_TR_FAST",
    "ACC": "ASMAG_TR_ACC",
    "P3_FALLBACK": "P3_MOG2",
}

def canonical_pipeline_name(pipeline_name):
    return PIPELINE_ALIASES.get(pipeline_name, pipeline_name)

def controller_mode_for_category(category):
    return CONTROLLER_CATEGORY_POLICY.get(category, "P3_FALLBACK")

def effective_pipeline_name(pipeline_name, category):
    if pipeline_name != "ASMAG_TR_CONTROLLER":
        return pipeline_name
    return CONTROLLER_MODE_TO_PIPELINE[controller_mode_for_category(category)]

def p4_efficient_cfg_for_pipeline(cfg, pipeline_name):
    efficient_cfg = dict(cfg.get("p4_asmag_plus", {}))
    efficient_cfg.update(cfg.get("p4_efficient", {}))
    if pipeline_name == "ASMAG_TR_ACC":
        efficient_cfg.update({
            "reuse_max_eval_age": 5,
            "reuse_max_raw_age": None,
            "sample_interval": 5,
            "open_threshold": 0.65,
        })
    elif pipeline_name == "ASMAG_TR_FAST":
        efficient_cfg.update({
            "reuse_max_eval_age": 8,
            "reuse_max_raw_age": None,
            "sample_interval": 10,
            "open_threshold": 0.75,
        })
    return efficient_cfg

def ensure(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)

def sequence_summary_paths(out_root, category, video, pipeline):
    seq_out = Path(out_root) / "raw_results" / category / video / pipeline
    return [
        seq_out / "sequence_event_summary.csv",
        seq_out / "sequence_pixel_summary.csv",
        seq_out / "sequence_edge_summary.csv",
        seq_out / "sequence_object_summary.csv",
    ]

def sequence_result_complete(out_root, category, video, pipeline):
    return all(path.exists() for path in sequence_summary_paths(out_root, category, video, pipeline))

def expected_eval_frame_count(seq, cfg):
    eval_cfg = cfg.get("evaluation", {})
    frame_step = max(1, int(eval_cfg.get("frame_step", 1)))
    max_frames = eval_cfg.get("max_frames_per_video", None)
    use_temporal_roi = bool(eval_cfg.get("use_temporal_roi", False))
    if use_temporal_roi and seq.get("roi_start") is not None and seq.get("roi_end") is not None:
        total = max(0, int(seq["roi_end"]) - int(seq["roi_start"]) + 1)
    else:
        try:
            frame_files, _ = list_frames(seq["input_dir"], seq["gt_dir"])
            total = len(frame_files)
        except Exception:
            total = 0
    if max_frames not in (None, "", "null", "None"):
        total = min(total, int(max_frames))
    return (total + frame_step - 1) // frame_step if total > 0 else 0

def initialize_run_progress(out_root, sequences, pipelines, cfg):
    progress_path = Path(out_root) / "run_progress.csv"
    expected_by_seq = {
        (seq["category"], seq["video"]): expected_eval_frame_count(seq, cfg)
        for seq in sequences
    }
    if progress_path.exists():
        progress = pd.read_csv(progress_path)
        for col in ["status", "updated_at", "message"]:
            if col in progress.columns:
                progress[col] = progress[col].fillna("").astype(str)
    else:
        progress = pd.DataFrame(
            [
                {
                    "category": seq["category"],
                    "video": seq["video"],
                    "pipeline": pipeline,
                    "status": "pending",
                    "expected_eval_frames": expected_by_seq[(seq["category"], seq["video"])],
                    "updated_at": "",
                    "message": "",
                }
                for seq in sequences
                for pipeline in pipelines
            ]
        )
    for idx, row in progress.iterrows():
        if sequence_result_complete(out_root, row["category"], row["video"], row["pipeline"]):
            progress.loc[idx, "status"] = "completed"
            progress.loc[idx, "message"] = "checkpoint exists"
        elif str(progress.loc[idx, "status"]) == "running":
            progress.loc[idx, "status"] = "pending"
            progress.loc[idx, "message"] = "reset stale running state"
    progress.to_csv(progress_path, index=False)
    return progress_path

def update_run_progress(progress_path, category, video, pipeline, status, message=""):
    progress_path = Path(progress_path)
    if not progress_path.exists():
        return
    progress = pd.read_csv(progress_path)
    for col in ["status", "updated_at", "message"]:
        if col in progress.columns:
            progress[col] = progress[col].fillna("").astype(str)
    mask = (
        (progress["category"] == category)
        & (progress["video"] == video)
        & (progress["pipeline"] == pipeline)
    )
    if mask.any():
        progress.loc[mask, "status"] = status
        progress.loc[mask, "updated_at"] = pd.Timestamp.now().isoformat(timespec="seconds")
        progress.loc[mask, "message"] = str(message)[:500]
    progress.to_csv(progress_path, index=False)

def build_research_summary(event_rows, pixel_rows, edge_rows):
    keys = ["category", "video", "pipeline"]
    ev_df = pd.DataFrame(event_rows)
    px_df = pd.DataFrame(pixel_rows)
    edge_df = pd.DataFrame(edge_rows)
    if ev_df.empty:
        return pd.DataFrame()

    summary = ev_df.merge(px_df, on=keys, how="left").merge(edge_df, on=keys, how="left")
    summary["CPU_reduction_rate"] = 0.0

    for _, group in summary.groupby(["category", "video"], sort=False):
        baseline = group[group["pipeline"] == "P1_YOLO_Only"]
        if baseline.empty or "avg_CPU" not in baseline:
            continue
        baseline_cpu = float(baseline["avg_CPU"].iloc[0])
        if baseline_cpu <= 0:
            continue
        idx = group.index
        summary.loc[idx, "CPU_reduction_rate"] = (
            (baseline_cpu - summary.loc[idx, "avg_CPU"].astype(float)) / baseline_cpu
        )

    summary["EE_Gate_Score"] = (
        summary["Event_Accuracy"].astype(float) * (1.0 + summary["CPU_reduction_rate"].astype(float))
    )
    return summary

def build_group_summary(research_summary, group_cols):
    if research_summary.empty:
        return pd.DataFrame()
    metric_cols = [
        "Event_Accuracy",
        "Event_F1",
        "MCC",
        "Recall",
        "Precision",
        "FMeasure",
        "PWC",
        "avg_CPU",
        "avg_RAM",
        "avg_FPS",
        "P95_latency_ms",
        "YOLO_activation_rate",
        "reused_prediction_rate",
        "EE_Gate_Score",
    ]
    available_metrics = [c for c in metric_cols if c in research_summary.columns]
    return research_summary.groupby(group_cols, as_index=False)[available_metrics].mean()

def unpack_sequence_result(result):
    if len(result) == 4:
        return result
    ev, px, ed = result
    return ev, px, ed, {}

def print_pipeline_final_table(out_root, pareto_summary):
    if pareto_summary is None or pareto_summary.empty:
        return
    out_root = Path(out_root)
    table = pareto_summary.copy()

    object_path = out_root / "summary_object_metrics.csv"
    if object_path.exists():
        obj = pd.read_csv(object_path)
        if "mAP_50_95_proxy" in obj.columns:
            obj = obj.groupby("pipeline", as_index=False)["mAP_50_95_proxy"].mean()
            table = table.merge(obj, on="pipeline", how="left")

    energy_path = out_root / "summary_edge_energy_metrics.csv"
    if energy_path.exists():
        energy = pd.read_csv(energy_path)
        if "aggregation_level" in energy.columns:
            energy = energy[energy["aggregation_level"] == "pipeline"].copy()
        energy_cols = [
            "pipeline",
            "Energy_reduction_rate_vs_P1_YOLO_Only",
        ]
        energy_cols = [col for col in energy_cols if col in energy.columns]
        table = table.merge(energy[energy_cols], on="pipeline", how="left")

    edge_path = out_root / "summary_edge_metrics.csv"
    if edge_path.exists():
        edge = pd.read_csv(edge_path)
        if "reused_prediction_rate" in edge.columns:
            edge = edge.groupby("pipeline", as_index=False)["reused_prediction_rate"].mean()
            table = table.merge(edge, on="pipeline", how="left")

    table = table.rename(
        columns={
            "pipeline": "Pipeline",
            "Energy_reduction_rate_vs_P1_YOLO_Only": "Energy_reduction_rate_vs_P1",
            "reused_prediction_rate": "Reuse_rate",
        }
    )
    cols = [
        "Pipeline",
        "FMeasure",
        "Event_F1",
        "mAP_50",
        "mAP_50_95_proxy",
        "Activation",
        "Avg_FPS",
        "P95_latency_ms",
        "Estimated_energy_per_frame",
        "Energy_reduction_rate_vs_P1",
        "Reuse_rate",
        "AE_Score",
        "Pareto_Efficient",
    ]
    for col in cols:
        if col not in table.columns:
            table[col] = 0.0
    print("\n[FINAL PIPELINE SUMMARY]")
    print(table[cols].to_string(index=False, float_format=lambda x: f"{x:.4f}"))

def build_p4_precision_comparison(event_rows, pixel_rows, edge_rows):
    research = build_research_summary(event_rows, pixel_rows, edge_rows)
    if research.empty:
        return pd.DataFrame()
    pipelines = ["P3_MOG2", "P4_ASMAG_PLUS", "P4_ASMAG_PLUS_PRECISION", "P4_PRECISION"]
    cols = [
        "pipeline",
        "FP_pixel",
        "FN_pixel",
        "Precision",
        "Recall",
        "FMeasure",
        "Event_F1",
        "YOLO_activation_rate",
        "P95_latency_ms",
        "avg_FPS",
    ]
    comparison = research[research["pipeline"].isin(pipelines)][cols].copy()
    comparison = comparison.rename(columns={"pipeline": "Pipeline", "avg_FPS": "Avg_FPS"})
    return comparison

def build_p4_balanced_comparison(event_rows, pixel_rows, edge_rows):
    research = build_research_summary(event_rows, pixel_rows, edge_rows)
    if research.empty:
        return pd.DataFrame()
    pipelines = [
        "P3_MOG2",
        "P4_ASMAG_PLUS",
        "P4_ASMAG_PLUS_PRECISION",
        "P4_ASMAG_PLUS_BALANCED",
        "P4_PRECISION",
        "P4_BALANCED",
    ]
    cols = [
        "pipeline",
        "FP_pixel",
        "FN_pixel",
        "Precision",
        "Recall",
        "FMeasure",
        "Event_F1",
        "YOLO_activation_rate",
        "P95_latency_ms",
        "avg_FPS",
    ]
    comparison = research[research["pipeline"].isin(pipelines)][cols].copy()
    comparison = comparison.rename(columns={"pipeline": "Pipeline", "avg_FPS": "Avg_FPS"})
    return comparison

def build_p4_efficient_comparison(event_rows, pixel_rows, edge_rows):
    research = build_research_summary(event_rows, pixel_rows, edge_rows)
    if research.empty:
        return pd.DataFrame()
    pipelines = ["P1_YOLO_Only", "P2_FrameDiff", "P3_MOG2", "P4_ASMAG_PLUS", "P4_ASMAG_PLUS_EFFICIENT", "P4_EFFICIENT"]
    cols = [
        "pipeline",
        "FP_pixel",
        "FN_pixel",
        "Precision",
        "Recall",
        "FMeasure",
        "Event_F1",
        "YOLO_activation_rate",
        "P95_latency_ms",
        "avg_FPS",
    ]
    comparison = research[research["pipeline"].isin(pipelines)][cols].copy()
    comparison = comparison.rename(columns={
        "pipeline": "Pipeline",
        "FP_pixel": "FP",
        "FN_pixel": "FN",
        "YOLO_activation_rate": "Activation",
        "P95_latency_ms": "P95 latency",
        "avg_FPS": "Avg FPS",
    })
    return comparison

def build_p4_reuse_comparison(event_rows, pixel_rows, edge_rows):
    research = build_research_summary(event_rows, pixel_rows, edge_rows)
    if research.empty:
        return pd.DataFrame()
    pipelines = ["P4_ASMAG_PLUS", "P4_ASMAG_PLUS_EFFICIENT", "P4_ASMAG_PLUS_EFFICIENT_REUSE"]
    cols = [
        "pipeline",
        "FMeasure",
        "Event_F1",
        "YOLO_activation_rate",
        "P95_latency_ms",
        "avg_FPS",
        "reused_prediction_rate",
        "FP_pixel",
        "FN_pixel",
        "Precision",
        "Recall",
    ]
    comparison = research[research["pipeline"].isin(pipelines)][cols].copy()
    comparison = comparison.rename(columns={
        "pipeline": "Pipeline",
        "YOLO_activation_rate": "Activation",
        "P95_latency_ms": "P95_latency",
        "avg_FPS": "Avg_FPS",
        "FP_pixel": "FP",
        "FN_pixel": "FN",
    })
    return comparison

def normalized(series):
    min_v = float(series.min())
    max_v = float(series.max())
    if max_v <= min_v:
        return pd.Series([1.0] * len(series), index=series.index)
    return (series - min_v) / (max_v - min_v)

def add_research_score(df):
    if df.empty:
        return df
    out = df.copy()
    fps_col = "Avg_FPS" if "Avg_FPS" in out.columns else "avg_FPS"
    activation_col = "Activation" if "Activation" in out.columns else "YOLO_activation_rate"
    out["normalized_Avg_FPS"] = normalized(out[fps_col].astype(float))
    out["Research_Score"] = (
        0.4 * out["FMeasure"].astype(float)
        + 0.3 * out["Event_F1"].astype(float)
        + 0.2 * (1.0 - out[activation_col].astype(float))
        + 0.1 * out["normalized_Avg_FPS"].astype(float)
    )
    return out

def build_pipeline_comparison(research_summary, pipelines=None):
    if research_summary.empty:
        return pd.DataFrame()
    df = research_summary.copy()
    if pipelines:
        df = df[df["pipeline"].isin(pipelines)]
    grouped = df.groupby("pipeline", as_index=False).agg(
        FMeasure=("FMeasure", "mean"),
        Event_F1=("Event_F1", "mean"),
        Activation=("YOLO_activation_rate", "mean"),
        Avg_FPS=("avg_FPS", "mean"),
        P95_latency=("P95_latency_ms", "mean"),
        Reuse_rate=("reused_prediction_rate", "mean"),
        reused_prediction_count=("reused_prediction_count", "sum"),
    )
    grouped = grouped.rename(columns={"pipeline": "Pipeline"})
    return add_research_score(grouped)

def build_asmag_ablation_table(research_summary):
    desired = [
        ("P4_ASMAG_PLUS", "P4_ASMAG_PLUS"),
        ("P4_PRECISION", "P4_PRECISION"),
        ("P4_BALANCED", "P4_BALANCED"),
        ("P4_EFFICIENT", "P4_EFFICIENT"),
        ("P4_EFFICIENT_REUSE", "P4_EFFICIENT_REUSE"),
        ("ASMAG_TR_ACC", "ASMAG_TR_ACC"),
        ("ASMAG_TR_FAST", "ASMAG_TR_FAST"),
    ]
    comparison = build_pipeline_comparison(research_summary)
    rows = []
    for label, pipeline in desired:
        found = comparison[comparison["Pipeline"] == pipeline]
        if found.empty:
            row = {
                "Pipeline": label,
                "FMeasure": None,
                "Event_F1": None,
                "Activation": None,
                "Avg_FPS": None,
                "P95_latency": None,
                "Reuse_rate": None,
                "reused_prediction_count": None,
                "normalized_Avg_FPS": None,
                "Research_Score": None,
                "status": "not_run_in_this_experiment",
            }
        else:
            row = found.iloc[0].to_dict()
            row["Pipeline"] = label
            row["status"] = "ok"
        rows.append(row)
    return pd.DataFrame(rows)

def cpu_ram_percent(proc, simulated_cores=2, simulated_ram_gb=4):
    cpu = proc.cpu_percent(interval=None) / max(1, simulated_cores)
    ram = (proc.memory_info().rss / (1024*1024)) / (simulated_ram_gb*1024) * 100
    return cpu, ram

def draw_qualitative(frame, gt, pred_mask, out_path):
    if gt.ndim == 3:
        gt = gt[:, :, 0]
    vis = frame.copy()
    overlay = vis.copy()
    overlay[pred_mask > 0] = (0, 255, 255)
    overlay[gt == 255] = (0, 255, 0)
    vis = cv2.addWeighted(vis, 0.65, overlay, 0.35, 0)
    cv2.imwrite(str(out_path), vis)

def mask_area(mask):
    return int(np.sum(mask > 0)) if mask is not None else 0

def mask_panel(mask, title):
    if mask.ndim == 3:
        mask = mask[:, :, 0]
    panel = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    panel[mask > 0] = (255, 255, 255)
    return label_panel(panel, title)

def gt_panel(gt, title="GT"):
    if gt.ndim == 3:
        gt = gt[:, :, 0]
    panel = np.zeros((gt.shape[0], gt.shape[1], 3), dtype=np.uint8)
    panel[gt == 0] = (20, 20, 20)
    panel[(gt == 50) | (gt == 85)] = (120, 120, 120)
    panel[gt == 170] = (0, 180, 180)
    panel[gt == 255] = (0, 220, 0)
    return label_panel(panel, title)

def label_panel(img, title):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 24), (0, 0, 0), -1)
    cv2.putText(out, title, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
    return out

def write_p4_diagnostics(out_root, diagnostics, always_frames=None, top_n=10):
    if not diagnostics:
        return
    always_frames = set(always_frames or [])
    selected = set(always_frames)
    selected.update(d["frame_id"] for d in sorted(diagnostics, key=lambda x: x["FP_pixel"], reverse=True)[:top_n])
    diag_dir = ensure(Path(out_root) / "p4_diagnostics")
    rows = []

    for d in diagnostics:
        if d["frame_id"] not in selected:
            continue
        frame_dir = ensure(diag_dir / f"frame_{d['frame_id']:06d}")
        masks = d["masks"]
        for name in [
            "fd_mask",
            "mog_mask",
            "knn_mask",
            "gate_mask_before_filter",
            "filter_mask_after_component",
            "final_pred_mask",
        ]:
            cv2.imwrite(str(frame_dir / f"{name}.png"), masks[name])

        if d["frame_id"] in always_frames:
            panels = [
                label_panel(d["frame"], f"original {d['frame_id']:06d}"),
                gt_panel(d["gt"], "GT"),
                mask_panel(masks["fd_mask"], "fd_mask"),
                mask_panel(masks["mog_mask"], "mog_mask"),
                mask_panel(masks["knn_mask"], "knn_mask"),
                mask_panel(masks["gate_mask_before_filter"], "gate_mask"),
                mask_panel(masks["filter_mask_after_component"], "filter_mask"),
                mask_panel(masks["final_pred_mask"], "final_pred_mask"),
            ]
            cv2.imwrite(str(diag_dir / f"grid_{d['frame_id']:06d}.png"), np.hstack(panels))

        row = {k: d[k] for k in [
            "frame_id",
            "fd_area",
            "mog_area",
            "knn_area",
            "gate_area",
            "filter_area",
            "final_area",
            "gt_area",
            "FP_pixel",
            "FN_pixel",
            "FMeasure",
            "gate_score",
            "component_entropy_mean",
            "kept_components",
            "watchdog_triggered",
        ]}
        rows.append(row)

    pd.DataFrame(rows).sort_values(["FP_pixel", "frame_id"], ascending=[False, True]).to_csv(
        diag_dir / "p4_mask_source_diagnostics.csv", index=False
    )

def process_sequence(cfg, seq, pipeline_name, detector, frames_source=None, gts_source=None):
    controller_selected_mode = controller_mode_for_category(seq["category"]) if pipeline_name == "ASMAG_TR_CONTROLLER" else ""
    category_policy_mode = controller_selected_mode
    execution_pipeline_name = effective_pipeline_name(pipeline_name, seq["category"])
    pipeline_key = canonical_pipeline_name(execution_pipeline_name)
    exp = cfg["experiment_name"]
    out_root = Path(cfg.get("output_root", "outputs")) / exp
    seq_out = ensure(out_root / "raw_results" / seq["category"] / seq["video"] / pipeline_name)
    mask_dir = ensure(seq_out / "masks")
    resume_paths = {
        "event": seq_out / "sequence_event_summary.csv",
        "pixel": seq_out / "sequence_pixel_summary.csv",
        "edge": seq_out / "sequence_edge_summary.csv",
        "object": seq_out / "sequence_object_summary.csv",
    }
    if bool(cfg.get("resume_existing_results", False)) and all(path.exists() for path in resume_paths.values()):
        return tuple(pd.read_csv(path).iloc[0].to_dict() for path in resume_paths.values())

    eval_cfg = cfg.get("evaluation", {})
    cdnet_gt_config = cfg.get("cdnet_gt", {})
    energy_cfg = cfg.get("energy_proxy", {})
    frame_step = int(eval_cfg.get("frame_step", 1))
    max_frames = eval_cfg.get("max_frames_per_video", None)
    save_masks = bool(eval_cfg.get("save_binary_masks", True))
    save_qual = bool(eval_cfg.get("save_qualitative_samples", False))
    use_temporal_roi = bool(eval_cfg.get("use_temporal_roi", False))
    warmup_frames = int(eval_cfg.get("warmup_frames", eval_cfg.get("warmup_frames_before_roi", 0)))
    temporal_roi_start, temporal_roi_end = None, None
    skipped_frames_before_roi = 0

    if frames_source is None:
        frame_files, gt_files = list_frames(seq["input_dir"], seq["gt_dir"])
        gt_by_number = {frame_number(p): p for p in gt_files if frame_number(p) is not None}
        roi_start, roi_end = seq.get("roi_start"), seq.get("roi_end")
        temporal_roi_start, temporal_roi_end = roi_start, roi_end
        eval_positions = []
        if use_temporal_roi and roi_start is not None and roi_end is not None:
            eval_positions = [
                i for i, p in enumerate(frame_files)
                if frame_number(p) is not None and roi_start <= frame_number(p) <= roi_end
            ]
            skipped_frames_before_roi = eval_positions[0] if eval_positions else 0
        else:
            eval_positions = list(range(len(frame_files)))
    else:
        frame_files, gt_files = frames_source, gts_source
        gt_by_number = {}
        eval_positions = list(range(len(frames_source)))

    if max_frames:
        eval_positions = eval_positions[:int(max_frames)]
    eval_positions = eval_positions[::frame_step]
    eval_position_set = set(eval_positions)
    uses_bg_subtractor = pipeline_key in {
        "P3_MOG2",
        "P4_ASMAG_PLUS",
        "P4_ASMAG_PLUS_PRECISION",
        "P4_ASMAG_PLUS_BALANCED",
        "P4_ASMAG_PLUS_EFFICIENT",
        "P4_ASMAG_PLUS_EFFICIENT_REUSE",
    }
    if eval_positions and frames_source is None and uses_bg_subtractor:
        loop_positions = range(eval_positions[0], eval_positions[-1] + 1)
    else:
        loop_positions = eval_positions
    if eval_positions and frames_source is None and uses_bg_subtractor and warmup_frames > 0:
        warmup_start = max(0, eval_positions[0] - warmup_frames)
        warmup_positions = range(warmup_start, eval_positions[0])
    else:
        warmup_positions = []

    if pipeline_key == "P2_FrameDiff":
        gate = FrameDiffGate(min_area_ratio=cfg.get("p4_asmag_plus", {}).get("min_area_ratio", 0.001))
    elif pipeline_key == "P3_MOG2":
        gate = MOG2Gate(min_area_ratio=cfg.get("p4_asmag_plus", {}).get("min_area_ratio", 0.001))
    elif pipeline_key == "P4_ASMAG_PLUS":
        gate = ASMAGPlusGate(cfg.get("p4_asmag_plus", {}))
    elif pipeline_key == "P4_ASMAG_PLUS_PRECISION":
        precision_cfg = dict(cfg.get("p4_asmag_plus", {}))
        precision_cfg.update(cfg.get("p4_precision", {}))
        gate = ASMAGPlusPrecisionGate(precision_cfg)
    elif pipeline_key == "P4_ASMAG_PLUS_BALANCED":
        balanced_cfg = dict(cfg.get("p4_asmag_plus", {}))
        balanced_cfg.update(cfg.get("p4_balanced", {}))
        gate = ASMAGPlusBalancedGate(balanced_cfg)
    elif pipeline_key in {"P4_ASMAG_PLUS_EFFICIENT", "P4_ASMAG_PLUS_EFFICIENT_REUSE"}:
        gate = ASMAGPlusEfficientGate(p4_efficient_cfg_for_pipeline(cfg, execution_pipeline_name))
    else:
        gate = None

    proc = psutil.Process(os.getpid())
    proc.cpu_percent(interval=None)
    edge = cfg.get("edge_profile", {})
    delay = float(edge.get("delay_penalty_sec", 0.0))
    cores = int(edge.get("simulated_cores", 2))
    ram_gb = float(edge.get("simulated_ram_gb", 4))

    rows, px_rows, edge_rows, object_records = [], [], [], []
    p4_diagnostics = []
    prev = None
    yolo_calls = 0
    processed = 0
    warmup_processed = 0
    reused_predictions = 0
    last_valid_pred_mask = None
    last_detection_frame_id = None
    last_detection_eval_index = None
    last_detection_raw_frame_id = None

    for idx in warmup_positions:
        frame = read_frame(frame_files[idx])
        if frame is None:
            continue
        gate.process(frame, prev)
        prev = frame.copy()
        warmup_processed += 1

    if warmup_processed and hasattr(gate, "reset_runtime_state"):
        gate.reset_runtime_state()

    for idx in loop_positions:
        if frames_source is None:
            frame = read_frame(frame_files[idx])
            if frame is None:
                continue
            gt = read_gt_for_frame(gt_by_number, frame_files[idx], frame.shape)
        else:
            frame = frames_source[idx]
            gt = gts_source[idx]

        should_evaluate = idx in eval_position_set
        if not should_evaluate:
            if pipeline_key != "P1_YOLO_Only":
                gate.process(frame, prev, {"is_evaluation": False})
            prev = frame.copy()
            continue

        t0 = time.time()
        frame_label = frame_number(frame_files[idx]) if frames_source is None else idx
        evaluated_index = processed

        gate_open = True
        gate_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        gate_info = {"gate_score": 1.0, "motion_area": 0, "watchdog_triggered": 0}

        if pipeline_key != "P1_YOLO_Only":
            gate_open, gate_mask, gate_info = gate.process(
                frame,
                prev,
                {
                    "is_evaluation": True,
                    "evaluated_index": evaluated_index,
                    "raw_frame_id": frame_label,
                },
            )

        detection = None
        pred_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        reused_prediction = 0
        reuse_age = ""
        reuse_age_eval = ""
        reuse_age_raw = ""
        reuse_allowed_by_eval_age = 0
        reuse_allowed_by_raw_age = 0
        reuse_stopped = 0
        if gate_open:
            yolo_calls += 1
            detection = detector.predict(frame, proposal_mask=gate_mask if pipeline_key != "P1_YOLO_Only" else None)
            if pipeline_key in {"P4_ASMAG_PLUS_PRECISION", "P4_ASMAG_PLUS_BALANCED"}:
                pred_mask = gate_mask.copy()
            elif detection.masks:
                for m in detection.masks:
                    pred_mask = cv2.bitwise_or(pred_mask, m)
            elif detection.boxes:
                for x1,y1,x2,y2 in detection.boxes:
                    cv2.rectangle(pred_mask, (x1,y1), (x2,y2), 255, -1)
            else:
                pred_mask = gate_mask.copy()
            if np.sum(pred_mask > 0) > 0:
                last_valid_pred_mask = pred_mask.copy()
                last_detection_frame_id = frame_label
                last_detection_eval_index = evaluated_index
                last_detection_raw_frame_id = frame_label
        else:
            if pipeline_key == "P4_ASMAG_PLUS_EFFICIENT_REUSE":
                reuse_cfg = cfg.get("p4_efficient", {})
                reuse_max_eval_age = int(reuse_cfg.get("reuse_max_eval_age", reuse_cfg.get("reuse_max_age", 5)))
                reuse_max_raw_age_cfg = reuse_cfg.get("reuse_max_raw_age", None)
                use_raw_age_limit = reuse_max_raw_age_cfg not in (None, "", "null", "None")
                reuse_max_raw_age = int(reuse_max_raw_age_cfg) if use_raw_age_limit else None
                reuse_stop_closed_streak = int(reuse_cfg.get("reuse_stop_closed_streak", 8))
                closed_streak = int(gate_info.get("closed_streak", 0))
                smooth = float(gate_info.get("gate_score_smooth", gate_info.get("gate_score", 0)))
                close_t = float(reuse_cfg.get("close_threshold", 0.45))
                if (
                    last_valid_pred_mask is not None
                    and last_detection_eval_index is not None
                    and last_detection_raw_frame_id is not None
                ):
                    reuse_age_eval_val = evaluated_index - last_detection_eval_index
                    reuse_age_raw_val = frame_label - last_detection_raw_frame_id
                    reuse_age = reuse_age_eval_val
                    reuse_age_eval = reuse_age_eval_val
                    reuse_age_raw = reuse_age_raw_val
                    reuse_allowed_by_eval_age = int(reuse_age_eval_val <= reuse_max_eval_age)
                    reuse_allowed_by_raw_age = int((not use_raw_age_limit) or (reuse_age_raw_val <= reuse_max_raw_age))
                    if closed_streak >= reuse_stop_closed_streak and smooth < close_t:
                        reuse_stopped = 1
                    elif reuse_allowed_by_eval_age and reuse_allowed_by_raw_age:
                        pred_mask = last_valid_pred_mask.copy()
                        reused_prediction = 1
                        reused_predictions += 1
                    else:
                        pred_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                else:
                    pred_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            else:
                pred_mask = np.zeros(frame.shape[:2], dtype=np.uint8)

        if pipeline_key in {"P4_ASMAG_PLUS", "P4_ASMAG_PLUS_PRECISION", "P4_ASMAG_PLUS_BALANCED", "P4_ASMAG_PLUS_EFFICIENT", "P4_ASMAG_PLUS_EFFICIENT_REUSE"} and hasattr(gate, "update_after_detection"):
            gate.update_after_detection(bool(gate_open and np.sum(pred_mask > 0) > 0))

        if delay > 0:
            time.sleep(delay)
        latency_ms = (time.time()-t0)*1000
        fps = 1000.0/latency_ms if latency_ms > 0 else 0
        cpu, ram = cpu_ram_percent(proc, cores, ram_gb)

        pred_alert = bool(np.sum(pred_mask > 0) > 0)
        e_state, is_active = event_state_from_masks(pred_alert, gt, cdnet_gt_config)
        px = pixel_metrics(pred_mask, gt, cdnet_gt_config)
        px_rows.append(px)

        gt_fg, _, _ = valid_gt_mask(gt, cdnet_gt_config)
        gt_object_mask = (gt_fg.astype(np.uint8) * 255)
        object_cfg = cfg.get("object_level_metrics", {})
        pred_min_area = int(object_cfg.get("min_pred_area", eval_cfg.get("object_min_area", 20)))
        gt_min_area = int(object_cfg.get("min_gt_area", eval_cfg.get("object_min_area", 20)))
        pred_boxes = mask_to_boxes(pred_mask, min_area=pred_min_area)
        gt_boxes = mask_to_boxes(gt_object_mask, min_area=gt_min_area)
        detector_boxes = detection.boxes if detection is not None else []
        detector_scores = detection.scores if detection is not None else []
        object_scores = assign_proxy_scores(
            pred_boxes,
            detector_boxes=detector_boxes,
            detector_scores=detector_scores,
            image_shape=frame.shape,
        )
        if not pred_boxes:
            score_source = "none"
        elif detector_boxes and detector_scores:
            score_source = "yolo_confidence"
        else:
            score_source = "area_normalized_proxy"
        obj_30 = object_counts_at_threshold(pred_boxes, gt_boxes, 0.3)
        obj_50 = object_counts_at_threshold(pred_boxes, gt_boxes, 0.5)
        obj_75 = object_counts_at_threshold(pred_boxes, gt_boxes, 0.75)
        mog2_used, framediff_used = energy_usage_flags(pipeline_key)
        energy_inputs = {
            "yolo_called": int(gate_open),
            "reused_prediction": reused_prediction,
            "mog2_used": mog2_used,
            "framediff_used": framediff_used,
        }
        energy_value = frame_energy(energy_inputs, energy_cfg)
        object_records.append(
            {
                "frame_id": frame_number(frame_files[idx]) if frames_source is None else idx,
                "pred_boxes": pred_boxes,
                "gt_boxes": gt_boxes,
                "scores": object_scores,
                "score_source": score_source,
            }
        )
        if pipeline_key == "P4_ASMAG_PLUS" and bool(eval_cfg.get("save_p4_diagnostics", False)):
            debug_masks = getattr(gate, "last_debug_masks", {})
            if debug_masks:
                gt_eval = gt[:, :, 0] if gt.ndim == 3 else gt
                p4_diagnostics.append({
                    "frame_id": frame_label,
                    "frame": frame.copy(),
                    "gt": gt_eval.copy(),
                    "masks": {
                        **{k: v.copy() for k, v in debug_masks.items()},
                        "final_pred_mask": pred_mask.copy(),
                    },
                    "fd_area": mask_area(debug_masks.get("fd_mask")),
                    "mog_area": mask_area(debug_masks.get("mog_mask")),
                    "knn_area": mask_area(debug_masks.get("knn_mask")),
                    "gate_area": mask_area(debug_masks.get("gate_mask_before_filter")),
                    "filter_area": mask_area(debug_masks.get("filter_mask_after_component")),
                    "final_area": mask_area(pred_mask),
                    "gt_area": int(np.sum(valid_gt_mask(gt_eval, cdnet_gt_config)[0])),
                    "FP_pixel": px["FP_pixel"],
                    "FN_pixel": px["FN_pixel"],
                    "FMeasure": px["FMeasure"],
                    "gate_score": gate_info.get("gate_score", 0),
                    "component_entropy_mean": gate_info.get("component_entropy_mean", 0),
                    "kept_components": gate_info.get("kept_components", 0),
                    "watchdog_triggered": gate_info.get("watchdog_triggered", 0),
                })

        rows.append({
            "category": seq["category"],
            "video": seq["video"],
            "pipeline": pipeline_name,
            "frame_id": frame_number(frame_files[idx]) if frames_source is None else idx,
            "raw_frame_id": frame_label,
            "evaluated_index": evaluated_index,
            "Is_Active": is_active,
            "gate_open": int(gate_open),
            "yolo_called": int(gate_open),
            "selected_mode": controller_selected_mode,
            "category_policy_mode": category_policy_mode,
            "used_p3_fallback": int(controller_selected_mode == "P3_FALLBACK"),
            "used_acc": int(controller_selected_mode == "ACC"),
            "used_fast": int(controller_selected_mode == "FAST"),
            "activation": int(gate_open),
            "energy_proxy": energy_value,
            "Event_State": e_state,
            "latency_ms": latency_ms,
            "FPS": fps,
            "CPU_Usage": cpu,
            "RAM_Usage": ram,
            "is_warmup": 0,
            "reused_prediction": reused_prediction,
            "reuse_age": reuse_age,
            "reuse_age_eval": reuse_age_eval,
            "reuse_age_raw": reuse_age_raw,
            "reuse_allowed_by_eval_age": reuse_allowed_by_eval_age,
            "reuse_allowed_by_raw_age": reuse_allowed_by_raw_age,
            "reuse_stopped": reuse_stopped,
            "mog2_used": mog2_used,
            "framediff_used": framediff_used,
            "energy_frame": energy_value,
            "energy_unit": energy_cfg.get("unit", "relative_energy_unit"),
            "pred_object_count": len(pred_boxes),
            "gt_object_count": len(gt_boxes),
            "TP_object_iou_0_3": obj_30["TP_object"],
            "FP_object_iou_0_3": obj_30["FP_object"],
            "FN_object_iou_0_3": obj_30["FN_object"],
            "TP_object": obj_50["TP_object"],
            "FP_object": obj_50["FP_object"],
            "FN_object": obj_50["FN_object"],
            "TP_object_iou_0_75": obj_75["TP_object"],
            "FP_object_iou_0_75": obj_75["FP_object"],
            "FN_object_iou_0_75": obj_75["FN_object"],
            "object_score_source": score_source,
            "last_detection_frame_id": last_detection_frame_id if last_detection_frame_id is not None else "",
            "last_detection_eval_index": last_detection_eval_index if last_detection_eval_index is not None else "",
            "last_detection_raw_frame_id": last_detection_raw_frame_id if last_detection_raw_frame_id is not None else "",
            **px,
            **gate_info
        })

        if save_masks:
            cv2.imwrite(str(mask_dir / f"bin{frame_label:06d}.png"), pred_mask)
        if save_qual and processed % 30 == 0:
            qdir = ensure(seq_out / "qualitative")
            draw_qualitative(frame, gt, pred_mask, qdir / f"frame_{frame_label:06d}_overlay.png")

        prev = frame.copy()
        processed += 1

    df = pd.DataFrame(rows)
    df.to_csv(seq_out / "frame_metrics.csv", index=False)
    if pipeline_key == "P4_ASMAG_PLUS" and bool(eval_cfg.get("save_p4_diagnostics", False)):
        write_p4_diagnostics(
            out_root,
            p4_diagnostics,
            always_frames=eval_cfg.get("p4_diagnostic_frames", [470]),
            top_n=int(eval_cfg.get("p4_diagnostic_top_fp", 10)),
        )

    ev = summarize_event(df) if not df.empty else {}
    pxsum = aggregate_pixel(px_rows) if px_rows else {}
    objsum = summarize_object_records(object_records) if object_records else {}

    activation = yolo_calls / processed if processed else 0
    edge_summary = {
        "avg_CPU": float(df["CPU_Usage"].mean()) if not df.empty else 0,
        "median_CPU": float(df["CPU_Usage"].median()) if not df.empty else 0,
        "avg_RAM": float(df["RAM_Usage"].mean()) if not df.empty else 0,
        "avg_FPS": float(df["FPS"].mean()) if not df.empty else 0,
        "median_FPS": float(df["FPS"].median()) if not df.empty else 0,
        "P95_latency_ms": float(df["latency_ms"].quantile(0.95)) if not df.empty else 0,
        "YOLO_activation_rate": activation,
        "processed_frames": processed,
        "temporal_roi_start": temporal_roi_start if temporal_roi_start is not None else "",
        "temporal_roi_end": temporal_roi_end if temporal_roi_end is not None else "",
        "evaluated_frames": processed,
        "skipped_frames_before_roi": skipped_frames_before_roi,
        "warmup_frames": warmup_processed,
        "reused_prediction_count": reused_predictions,
        "reused_prediction_rate": reused_predictions / processed if processed else 0
    }

    common = {"category": seq["category"], "video": seq["video"], "pipeline": pipeline_name}
    result = ({**common, **ev}, {**common, **pxsum}, {**common, **edge_summary}, {**common, **objsum})
    for payload, path in zip(result, resume_paths.values()):
        pd.DataFrame([payload]).to_csv(path, index=False)
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    out_root = ensure(Path(cfg.get("output_root", "outputs")) / cfg["experiment_name"])
    print(f"[RUN] Experiment: {cfg['experiment_name']}")
    print(f"[OUT] {out_root}")

    detector = create_detector(cfg.get("detector_mode", "mock"), cfg.get("model_path", ""), cfg.get("model_name", "mock_detector"))
    print(f"[DETECTOR] {cfg.get('detector_mode')} - {cfg.get('model_name')}")

    if cfg.get("dataset_mode") == "synthetic":
        frames, gts = make_synthetic_sequence(**cfg.get("synthetic", {}))
        sequences = [{"category": "synthetic", "video": "moving_box", "input_dir": "", "gt_dir": ""}]
    else:
        sequences = scan_cdnet(cfg["dataset_root"], cfg["categories"], cfg.get("videos", "auto"))
        frames, gts = None, None

    if not sequences:
        print("[ERROR] No sequences found. Check dataset_root/categories.")
        return

    progress_path = initialize_run_progress(out_root, sequences, cfg["pipelines"], cfg)

    all_ev, all_px, all_edge, all_obj, all_cdnet_frame_rows = [], [], [], [], []
    for seq in sequences:
        print(f"\n[SEQ] {seq['category']}/{seq['video']}")
        for p in cfg["pipelines"]:
            print(f"  - Running {p} ...")
            update_run_progress(progress_path, seq["category"], seq["video"], p, "running")
            try:
                ev, px, ed, obj = unpack_sequence_result(process_sequence(cfg, seq, p, detector, frames, gts))
                update_run_progress(progress_path, seq["category"], seq["video"], p, "completed")
            except Exception as exc:
                update_run_progress(progress_path, seq["category"], seq["video"], p, "failed", repr(exc))
                raise
            all_ev.append(ev); all_px.append(px); all_edge.append(ed)
            all_obj.append(obj)
            frame_metrics_path = out_root / "raw_results" / seq["category"] / seq["video"] / p / "frame_metrics.csv"
            if frame_metrics_path.exists():
                all_cdnet_frame_rows.extend(pd.read_csv(frame_metrics_path).to_dict("records"))
            print(
                f"    EventF1={ev.get('Event_F1',0):.3f} | "
                f"FMeasure={px.get('FMeasure',0):.3f} | "
                f"Activation={ed.get('YOLO_activation_rate',0):.3f} | "
                f"ROI={ed.get('temporal_roi_start','')}-{ed.get('temporal_roi_end','')} | "
                f"EvalFrames={ed.get('evaluated_frames',0)} | "
                f"SkippedBeforeROI={ed.get('skipped_frames_before_roi',0)}"
            )

    pd.DataFrame(all_ev).to_csv(out_root / "summary_event_metrics.csv", index=False)
    pd.DataFrame(all_px).to_csv(out_root / "summary_pixel_metrics.csv", index=False)
    build_cdnet_metrics_summary(all_cdnet_frame_rows).to_csv(
        out_root / "summary_cdnet_metrics.csv", index=False
    )
    summarize_edge_energy(all_cdnet_frame_rows, cfg.get("energy_proxy", {})).to_csv(
        out_root / "summary_edge_energy_metrics.csv", index=False
    )
    pd.DataFrame(all_edge).to_csv(out_root / "summary_edge_metrics.csv", index=False)
    pd.DataFrame(all_obj).to_csv(out_root / "summary_object_metrics.csv", index=False)
    research_summary = build_research_summary(all_ev, all_px, all_edge)
    research_summary.to_csv(out_root / "summary_research_metrics.csv", index=False)
    summary_by_category = build_group_summary(research_summary, ["category", "pipeline"])
    summary_by_category.to_csv(out_root / "summary_by_category.csv", index=False)
    summary_by_video = build_group_summary(research_summary, ["category", "video", "pipeline"])
    summary_by_video.to_csv(out_root / "summary_by_video.csv", index=False)
    pd.DataFrame(build_object_group_summary(all_obj, ["pipeline"])).to_csv(
        out_root / "summary_object_by_pipeline.csv", index=False
    )
    pd.DataFrame(build_object_group_summary(all_obj, ["category", "pipeline"])).to_csv(
        out_root / "summary_object_by_category.csv", index=False
    )
    pd.DataFrame(build_object_group_summary(all_obj, ["category", "video", "pipeline"])).to_csv(
        out_root / "summary_object_by_video.csv", index=False
    )
    final_pipelines = [
        "P1_YOLO_Only",
        "P2_FrameDiff",
        "P3_MOG2",
        "P4_ASMAG_PLUS",
        "ASMAG_TR_ACC",
        "ASMAG_TR_FAST",
        "ASMAG_TR_CONTROLLER",
    ]
    final_comparison = build_pipeline_comparison(research_summary, final_pipelines)
    if not final_comparison.empty:
        final_comparison.to_csv(out_root / "asmag_tr_final_comparison.csv", index=False)
    ablation_table = build_asmag_ablation_table(research_summary)
    ablation_table.to_csv(out_root / "asmag_ablation_table.csv", index=False)
    p4_precision_comparison = build_p4_precision_comparison(all_ev, all_px, all_edge)
    if not p4_precision_comparison.empty:
        p4_precision_comparison.to_csv(out_root / "p4_precision_comparison.csv", index=False)
    p4_balanced_comparison = build_p4_balanced_comparison(all_ev, all_px, all_edge)
    if not p4_balanced_comparison.empty:
        p4_balanced_comparison.to_csv(out_root / "p4_balanced_comparison.csv", index=False)
    p4_efficient_comparison = build_p4_efficient_comparison(all_ev, all_px, all_edge)
    if not p4_efficient_comparison.empty:
        p4_efficient_comparison.to_csv(out_root / "p4_efficient_comparison.csv", index=False)
    p4_reuse_comparison = build_p4_reuse_comparison(all_ev, all_px, all_edge)
    if not p4_reuse_comparison.empty:
        p4_reuse_comparison.to_csv(out_root / "p4_reuse_comparison.csv", index=False)
    pareto_summary = write_pareto_metrics(out_root, cfg.get("pareto", {}))
    create_summary_charts(out_root)

    print("\n[DONE] Summary files:")
    print(f" - {out_root/'summary_event_metrics.csv'}")
    print(f" - {out_root/'summary_pixel_metrics.csv'}")
    print(f" - {out_root/'summary_cdnet_metrics.csv'}")
    print(f" - {out_root/'summary_edge_energy_metrics.csv'}")
    print(f" - {out_root/'summary_object_metrics.csv'}")
    print(f" - {out_root/'summary_edge_metrics.csv'}")
    print(f" - {out_root/'summary_pareto_metrics.csv'}")
    print(f" - {out_root/'summary_research_metrics.csv'}")
    print(f" - {out_root/'asmag_tr_final_comparison.csv'}")
    print(f" - {out_root/'asmag_ablation_table.csv'}")
    print(f" - {out_root/'charts'}")
    if not final_comparison.empty:
        best_accuracy = final_comparison.sort_values(["FMeasure", "Event_F1"], ascending=False).iloc[0]
        best_efficiency = final_comparison.sort_values(["Activation", "Avg_FPS"], ascending=[True, False]).iloc[0]
        best_score = final_comparison.sort_values("Research_Score", ascending=False).iloc[0]
        print("\n[AUTO CONCLUSION]")
        print(f" - Best accuracy: {best_accuracy['Pipeline']} (FMeasure={best_accuracy['FMeasure']:.4f}, Event_F1={best_accuracy['Event_F1']:.4f})")
        print(f" - Best activation saving: {best_efficiency['Pipeline']} (Activation={best_efficiency['Activation']:.4f}, Avg_FPS={best_efficiency['Avg_FPS']:.2f})")
        print(f" - Best Research Score: {best_score['Pipeline']} (Research_Score={best_score['Research_Score']:.4f})")
    print_pipeline_final_table(out_root, pareto_summary)

if __name__ == "__main__":
    main()
