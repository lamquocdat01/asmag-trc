import os, sys, time, argparse, pickle, json, math
from pathlib import Path
from datetime import datetime
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

ONLINE_CONTROLLER_PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE"
ONLINE_CONTROLLER_P3TUNED_PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_P3TUNED"
ONLINE_CONTROLLER_CALIBRATED_PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED"
ONLINE_CONTROLLER_PIPELINES = {
    ONLINE_CONTROLLER_PIPELINE,
    ONLINE_CONTROLLER_P3TUNED_PIPELINE,
    ONLINE_CONTROLLER_CALIBRATED_PIPELINE,
}

ONLINE_MODE_FEATURE_COLUMNS = [
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

def normalize01(value, scale):
    if scale <= 0:
        return 0.0
    return max(0.0, min(1.0, float(value) / float(scale)))

def online_mode_from_difficulty(score, fast_threshold=0.30, p3_threshold=0.60):
    if score < fast_threshold:
        return "FAST"
    if score < p3_threshold:
        return "ACC"
    return "P3_FALLBACK"

class OnlineSceneDifficultyEstimator:
    def __init__(self, cfg=None):
        cfg = cfg or {}
        self.window = int(cfg.get("window", 30))
        self.min_stable_frames = int(cfg.get("min_stable_frames", cfg.get("min_mode_duration", 10)))
        self.fast_threshold = float(cfg.get("fast_threshold", 0.30))
        self.p3_threshold = float(cfg.get("p3_threshold", 0.60))
        self.disagreement_high_threshold = float(cfg.get("disagreement_high_threshold", 0.35))
        self.fallback_boost_if_disagreement_high = bool(cfg.get("fallback_boost_if_disagreement_high", False))
        self.force_p3_if_fd_mog_disagreement_high = bool(cfg.get("force_p3_if_fd_mog_disagreement_high", False))
        self.force_p3_if_knn_mog_disagreement_high = bool(cfg.get("force_p3_if_knn_mog_disagreement_high", False))
        self.max_switch_per_100_frames = int(cfg.get("max_switch_per_100_frames", 6))
        self.use_hysteresis = bool(cfg.get("use_hysteresis", True))
        self.current_mode = str(cfg.get("initial_mode", "ACC"))
        self.candidate_mode = self.current_mode
        self.candidate_frames = 0
        self.mode_duration = 0
        self.mode_switch_count = 0
        self.switch_eval_indices = []
        self.history = []
        self.policy_model = None
        self.policy_name = ""
        self.policy_feature_columns = ONLINE_MODE_FEATURE_COLUMNS
        policy_path = str(cfg.get("mode_policy_path", "") or "").strip()
        if policy_path:
            with open(policy_path, "rb") as f:
                artifact = pickle.load(f)
            self.policy_model = artifact.get("model", artifact) if isinstance(artifact, dict) else artifact
            if isinstance(artifact, dict):
                self.policy_name = str(artifact.get("policy_name", "calibrated_policy"))
                self.policy_feature_columns = list(artifact.get("feature_columns", ONLINE_MODE_FEATURE_COLUMNS))
            else:
                self.policy_name = "calibrated_policy"

    def predict_calibrated_mode(self, features):
        if self.policy_model is None:
            return None
        row = pd.DataFrame(
            [[float(features.get(col, 0.0) or 0.0) for col in self.policy_feature_columns]],
            columns=self.policy_feature_columns,
        )
        return str(self.policy_model.predict(row)[0])

    def update(self, gate_info, gate_open, reused_prediction, is_active, evaluated_index):
        frame_record = {
            "motion_density": float(gate_info.get("motion_density", 0.0) or 0.0),
            "component_count": float(gate_info.get("kept_components", 0.0) or 0.0),
            "fd_mog_disagreement": abs(float(gate_info.get("fd_area", 0.0) or 0.0) - float(gate_info.get("mog_area", 0.0) or 0.0))
            / max(1.0, float(gate_info.get("image_area", 0.0) or gate_info.get("frame_area", 0.0) or 1.0)),
            "knn_mog_disagreement": abs(float(gate_info.get("knn_area", 0.0) or 0.0) - float(gate_info.get("mog_area", 0.0) or 0.0))
            / max(1.0, float(gate_info.get("image_area", 0.0) or gate_info.get("frame_area", 0.0) or 1.0)),
            "illumination_diff": float(gate_info.get("illumination_diff", 0.0) or 0.0),
            "reuse_success": int(reused_prediction),
            "is_active": int(is_active),
            "gate_closed": int(not gate_open),
        }
        self.history.append(frame_record)
        if len(self.history) > self.window:
            self.history = self.history[-self.window:]

        h = pd.DataFrame(self.history)
        features = {
            "motion_density_mean": float(h["motion_density"].mean()),
            "motion_density_std": float(h["motion_density"].std(ddof=0)),
            "component_count_mean": float(h["component_count"].mean()),
            "component_count_std": float(h["component_count"].std(ddof=0)),
            "fd_mog_disagreement": float(h["fd_mog_disagreement"].mean()),
            "knn_mog_disagreement": float(h["knn_mog_disagreement"].mean()),
            "illumination_variance": float(h["illumination_diff"].var(ddof=0)),
            "reuse_success_rate": float(h["reuse_success"].mean()),
            "active_frame_rate": float(h["is_active"].mean()),
            "gate_closed_rate": float(h["gate_closed"].mean()),
        }
        features["motion_density_std_norm"] = normalize01(features["motion_density_std"], 0.05)
        features["component_count_std_norm"] = normalize01(features["component_count_std"], 12.0)
        features["fd_mog_disagreement_norm"] = normalize01(features["fd_mog_disagreement"], 0.08)
        features["knn_mog_disagreement_norm"] = normalize01(features["knn_mog_disagreement"], 0.08)
        features["illumination_variance_norm"] = normalize01(features["illumination_variance"], 400.0)
        features["reuse_failure_rate"] = 1.0 - features["reuse_success_rate"]
        features["gate_instability"] = min(features["gate_closed_rate"], 1.0 - features["gate_closed_rate"]) * 2.0
        difficulty = (
            0.20 * features["motion_density_std_norm"]
            + 0.15 * features["component_count_std_norm"]
            + 0.20 * features["fd_mog_disagreement_norm"]
            + 0.15 * features["illumination_variance_norm"]
            + 0.10 * features["reuse_failure_rate"]
            + 0.10 * features["active_frame_rate"]
            + 0.10 * features["gate_instability"]
        )
        fd_high = features["fd_mog_disagreement"] >= self.disagreement_high_threshold
        knn_high = features["knn_mog_disagreement"] >= self.disagreement_high_threshold
        if self.fallback_boost_if_disagreement_high and (fd_high or knn_high):
            difficulty = max(difficulty, self.p3_threshold)
        force_p3 = (
            (self.force_p3_if_fd_mog_disagreement_high and fd_high)
            or (self.force_p3_if_knn_mog_disagreement_high and knn_high)
        )
        calibrated_mode = self.predict_calibrated_mode(features)
        desired_mode = calibrated_mode or (
            "P3_FALLBACK" if force_p3 else online_mode_from_difficulty(
                difficulty,
                self.fast_threshold,
                self.p3_threshold,
            )
        )
        if not self.use_hysteresis:
            if desired_mode != self.current_mode:
                self.mode_switch_count += 1
                self.mode_duration = 0
                self.switch_eval_indices.append(evaluated_index)
            else:
                self.mode_duration += 1
            self.current_mode = desired_mode
            self.candidate_mode = desired_mode
            self.candidate_frames = 0
            features.update({
                "SceneDifficulty": difficulty,
                "selected_mode": self.current_mode,
                "desired_mode": desired_mode,
                "calibrated_policy_mode": calibrated_mode or "",
                "calibrated_policy_name": self.policy_name,
                "emergency_p3_fallback": int(force_p3),
                "fd_mog_disagreement_high": int(fd_high),
                "knn_mog_disagreement_high": int(knn_high),
                "mode_switch_count": self.mode_switch_count,
                "mode_duration": self.mode_duration,
            })
            return features
        if desired_mode == self.current_mode:
            self.candidate_mode = desired_mode
            self.candidate_frames = 0
        elif desired_mode == self.candidate_mode:
            self.candidate_frames += 1
        else:
            self.candidate_mode = desired_mode
            self.candidate_frames = 1

        self.switch_eval_indices = [i for i in self.switch_eval_indices if evaluated_index - i < 100]
        can_switch = len(self.switch_eval_indices) < self.max_switch_per_100_frames
        if self.candidate_frames >= self.min_stable_frames and can_switch:
            self.current_mode = self.candidate_mode
            self.candidate_frames = 0
            self.mode_duration = 0
            self.mode_switch_count += 1
            self.switch_eval_indices.append(evaluated_index)
        else:
            self.mode_duration += 1

        features.update({
            "SceneDifficulty": difficulty,
            "selected_mode": self.current_mode,
            "desired_mode": desired_mode,
            "calibrated_policy_mode": calibrated_mode or "",
            "calibrated_policy_name": self.policy_name,
            "emergency_p3_fallback": int(force_p3),
            "fd_mog_disagreement_high": int(fd_high),
            "knn_mog_disagreement_high": int(knn_high),
            "mode_switch_count": self.mode_switch_count,
            "mode_duration": self.mode_duration,
        })
        return features

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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def parse_optional_int(value):
    if value in (None, "", "null", "None"):
        return None
    return int(value)

def append_csv(path, df):
    path = Path(path)
    if df is None or df.empty:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, mode="a", header=not path.exists(), index=False)

def configure_runtime(cfg):
    runtime = cfg.get("runtime", {})
    edge = cfg.get("edge_profile", {})
    threads = int(runtime.get("opencv_num_threads", runtime.get("max_threads", edge.get("simulated_cores", 4))))
    try:
        cv2.setNumThreads(max(1, threads))
    except Exception:
        pass
    torch_threads = int(runtime.get("torch_num_threads", threads))
    try:
        import torch
        torch.set_num_threads(max(1, torch_threads))
        if not bool(runtime.get("cuda_enabled", False)):
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
    except Exception:
        pass

def gpu_profile():
    return math.nan, math.nan

def sequence_summary_paths(out_root, category, video, pipeline):
    seq_out = Path(out_root) / "raw_results" / category / video / pipeline
    return [
        seq_out / "sequence_event_summary.csv",
        seq_out / "sequence_pixel_summary.csv",
        seq_out / "sequence_edge_summary.csv",
        seq_out / "sequence_object_summary.csv",
    ]

def sequence_result_complete(out_root, category, video, pipeline, expected_frames=None):
    if not all(path.exists() for path in sequence_summary_paths(out_root, category, video, pipeline)):
        return False
    if expected_frames in (None, "", "null", "None"):
        return True
    frame_metrics = Path(out_root) / "raw_results" / category / video / pipeline / "frame_metrics.csv"
    if not frame_metrics.exists():
        return False
    try:
        rows = sum(1 for _ in open(frame_metrics, "r", encoding="utf-8")) - 1
    except Exception:
        return False
    return rows >= int(expected_frames)

def has_external_run_experiment_process(config_path=None):
    current_pid = os.getpid()
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["pid"] == current_pid:
                continue
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if "run_experiment.py" in cmdline and (not config_path or str(config_path) in cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def is_stale_progress_row(row, stale_minutes):
    updated_at = str(row.get("updated_at", "") or "").strip()
    if not updated_at:
        return True
    try:
        age = pd.Timestamp.now() - pd.Timestamp(updated_at)
    except Exception:
        return True
    return age.total_seconds() > stale_minutes * 60

PROGRESS_COLUMNS = [
    "job_id",
    "category",
    "video",
    "pipeline",
    "status",
    "frames_expected",
    "frames_done",
    "started_at",
    "updated_at",
    "completed_at",
    "runtime_seconds",
    "avg_fps",
    "p95_latency_ms",
    "activation",
    "energy_per_frame",
    "simulated_runtime_energy_per_frame",
    "error_message",
    "output_path",
    "message",
]

def progress_summary(progress):
    counts = progress["status"].value_counts().to_dict()
    running = progress[progress["status"] == "running"]
    current_job = ""
    if not running.empty:
        row = running.iloc[0]
        current_job = f"{row['category']}/{row['video']}/{row['pipeline']}"
    return {
        "completed": int(counts.get("completed", 0)),
        "pending": int(counts.get("pending", 0)),
        "running": int(counts.get("running", 0)),
        "failed": int(counts.get("failed", 0)),
        "current_job": current_job,
    }

def print_progress_summary(progress_path, label="PROGRESS"):
    progress_path = Path(progress_path)
    if not progress_path.exists():
        return
    progress = pd.read_csv(progress_path)
    summary = progress_summary(progress)
    print(
        f"[{label}] completed={summary['completed']} | "
        f"pending={summary['pending']} | running={summary['running']} | "
        f"failed={summary['failed']} | current_job={summary['current_job'] or '-'}"
    )

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
    progress_cfg = cfg.get("progress", {})
    auto_recover = bool(progress_cfg.get("auto_recover_stale_jobs", True))
    stale_minutes = float(progress_cfg.get("stale_running_minutes", 10))
    external_runner_active = has_external_run_experiment_process(cfg.get("_config_path"))
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
                    "job_id": f"{seq['category']}/{seq['video']}/{pipeline}",
                    "category": seq["category"],
                    "video": seq["video"],
                    "pipeline": pipeline,
                    "status": "pending",
                    "frames_expected": expected_by_seq[(seq["category"], seq["video"])],
                    "frames_done": 0,
                    "started_at": "",
                    "updated_at": "",
                    "completed_at": "",
                    "runtime_seconds": "",
                    "avg_fps": "",
                    "p95_latency_ms": "",
                    "activation": "",
                    "energy_per_frame": "",
                    "simulated_runtime_energy_per_frame": "",
                    "error_message": "",
                    "output_path": str(Path(out_root) / "raw_results" / seq["category"] / seq["video"] / pipeline),
                    "message": "",
                }
                for seq in sequences
                for pipeline in pipelines
            ]
        )
    for col in PROGRESS_COLUMNS:
        if col not in progress.columns:
            if col == "job_id":
                progress[col] = progress.apply(lambda r: f"{r['category']}/{r['video']}/{r['pipeline']}", axis=1)
            elif col == "frames_expected":
                progress[col] = progress.apply(lambda r: expected_by_seq.get((r["category"], r["video"]), ""), axis=1)
            elif col == "output_path":
                progress[col] = progress.apply(
                    lambda r: str(Path(out_root) / "raw_results" / r["category"] / r["video"] / r["pipeline"]),
                    axis=1,
                )
            else:
                progress[col] = ""
    if "expected_eval_frames" in progress.columns:
        progress["frames_expected"] = progress["frames_expected"].where(
            progress["frames_expected"].astype(str).str.len() > 0,
            progress["expected_eval_frames"],
        )
    existing_jobs = set(zip(progress["category"].astype(str), progress["video"].astype(str), progress["pipeline"].astype(str)))
    new_rows = []
    for seq in sequences:
        for pipeline in pipelines:
            key = (str(seq["category"]), str(seq["video"]), str(pipeline))
            if key in existing_jobs:
                continue
            new_rows.append({
                "job_id": f"{seq['category']}/{seq['video']}/{pipeline}",
                "category": seq["category"],
                "video": seq["video"],
                "pipeline": pipeline,
                "status": "pending",
                "frames_expected": expected_by_seq[(seq["category"], seq["video"])],
                "frames_done": 0,
                "started_at": "",
                "updated_at": "",
                "completed_at": "",
                "runtime_seconds": "",
                "avg_fps": "",
                "p95_latency_ms": "",
                "activation": "",
                "energy_per_frame": "",
                "simulated_runtime_energy_per_frame": "",
                "error_message": "",
                "output_path": str(Path(out_root) / "raw_results" / seq["category"] / seq["video"] / pipeline),
                "message": "",
            })
    if new_rows:
        progress = pd.concat([progress, pd.DataFrame(new_rows)], ignore_index=True)
    recovered = 0
    for idx, row in progress.iterrows():
        expected_frames = expected_by_seq.get((row["category"], row["video"]), row.get("frames_expected", None))
        if sequence_result_complete(out_root, row["category"], row["video"], row["pipeline"], expected_frames):
            progress.loc[idx, "status"] = "completed"
            progress.loc[idx, "message"] = "checkpoint exists"
            progress.loc[idx, "frames_done"] = expected_frames
        elif str(progress.loc[idx, "status"]) == "completed":
            progress.loc[idx, "status"] = "pending"
            progress.loc[idx, "message"] = "checkpoint incomplete for current expected frames"
        elif (
            auto_recover
            and str(progress.loc[idx, "status"]) == "running"
            and ((not external_runner_active) or is_stale_progress_row(row, stale_minutes))
        ):
            progress.loc[idx, "status"] = "pending"
            progress.loc[idx, "updated_at"] = now_iso()
            progress.loc[idx, "message"] = f"auto-recovered stale running state; stale>{stale_minutes:g}min or no external runner"
            recovered += 1
    progress = progress[PROGRESS_COLUMNS]
    progress.to_csv(progress_path, index=False)
    if recovered:
        print(f"[AUTO-RECOVER] reset {recovered} stale running job(s) to pending")
    print_progress_summary(progress_path, "START PROGRESS")
    return progress_path

def update_run_progress(progress_path, category, video, pipeline, status, message="", metrics=None):
    progress_path = Path(progress_path)
    if not progress_path.exists():
        return
    progress = pd.read_csv(progress_path)
    for col in ["status", "started_at", "updated_at", "completed_at", "error_message", "message"]:
        if col in progress.columns:
            progress[col] = progress[col].fillna("").astype(str)
    mask = (
        (progress["category"] == category)
        & (progress["video"] == video)
        & (progress["pipeline"] == pipeline)
    )
    if mask.any():
        progress.loc[mask, "status"] = status
        progress.loc[mask, "updated_at"] = now_iso()
        progress.loc[mask, "message"] = str(message)[:500]
        if status == "running":
            progress.loc[mask & (progress["started_at"].fillna("").astype(str) == ""), "started_at"] = now_iso()
        if status == "completed":
            progress.loc[mask, "completed_at"] = now_iso()
            progress.loc[mask, "error_message"] = ""
        if status == "failed":
            progress.loc[mask, "error_message"] = str(message)[:500]
        if metrics:
            for key, value in metrics.items():
                if key in progress.columns:
                    progress.loc[mask, key] = value
    progress.to_csv(progress_path, index=False)
    if status in {"completed", "failed"}:
        print_progress_summary(progress_path, "JOB PROGRESS")

def write_run_plan(run_plan_path, sequences):
    run_plan_path = Path(run_plan_path)
    if run_plan_path.exists():
        return pd.read_csv(run_plan_path)
    rows = []
    for i, seq in enumerate(sequences, start=1):
        rows.append({
            "day_index": i,
            "priority": i,
            "category": seq["category"],
            "video": seq["video"],
            "max_frames": "",
            "status": "pending",
            "notes": "",
        })
    plan = pd.DataFrame(rows)
    run_plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan.to_csv(run_plan_path, index=False)
    return plan

def apply_run_filters(sequences, cfg, args):
    if args.category:
        sequences = [s for s in sequences if s["category"] == args.category]
    if args.video:
        sequences = [s for s in sequences if s["video"] == args.video]
    if args.pipeline:
        cfg["pipelines"] = [args.pipeline]
    if args.max_frames is not None:
        cfg.setdefault("evaluation", {})["max_frames_per_video"] = int(args.max_frames)
    if args.run_plan:
        plan = write_run_plan(args.run_plan, sequences)
        allowed = {
            (str(row["category"]), str(row["video"]))
            for _, row in plan.iterrows()
            if str(row.get("status", "pending")).lower() != "skip"
        }
        sequences = [s for s in sequences if (s["category"], s["video"]) in allowed]
    return sequences

def limit_sequences_for_run(sequences, progress_path, max_videos_per_run):
    if not max_videos_per_run:
        return sequences
    progress_path = Path(progress_path)
    if not progress_path.exists():
        return sequences[: int(max_videos_per_run)]
    progress = pd.read_csv(progress_path)
    active = progress[progress["status"].isin(["pending", "running", "failed"])].copy()
    wanted = []
    for seq in sequences:
        key = (seq["category"], seq["video"])
        if ((active["category"] == key[0]) & (active["video"] == key[1])).any():
            wanted.append(key)
        if len(wanted) >= int(max_videos_per_run):
            break
    wanted = set(wanted)
    return [s for s in sequences if (s["category"], s["video"]) in wanted]

def update_daily_progress_report(out_root, progress_path, next_resume_command):
    out_root = Path(out_root)
    progress = pd.read_csv(progress_path) if Path(progress_path).exists() else pd.DataFrame()
    summary = progress_summary(progress) if not progress.empty else {"completed": 0, "pending": 0, "running": 0, "failed": 0, "current_job": ""}
    lines = [
        "# Daily Progress Report",
        "",
        f"Updated at `{now_iso()}`.",
        "",
        "## Progress",
        "",
        "```text",
        f"completed={summary['completed']}",
        f"pending={summary['pending']}",
        f"running={summary['running']}",
        f"failed={summary['failed']}",
        f"current_job={summary['current_job'] or '-'}",
        "```",
        "",
        "## Next Resume Command",
        "",
        "```bat",
        next_resume_command,
        "```",
    ]
    if not progress.empty:
        by_video = progress.groupby(["category", "video"])["status"].apply(lambda s: int((s == "completed").sum())).reset_index(name="completed_jobs")
        lines += ["", "## Recent Video Progress", "", by_video.tail(20).to_markdown(index=False)]
    (out_root / "daily_progress_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def write_official_edge_reports(out_root, pipelines):
    out_root = Path(out_root)
    event_path = out_root / "summary_event_metrics.csv"
    pixel_path = out_root / "summary_pixel_metrics.csv"
    edge_path = out_root / "summary_edge_metrics.csv"
    object_path = out_root / "summary_object_metrics.csv"
    if not (event_path.exists() and pixel_path.exists() and edge_path.exists()):
        return
    ev = pd.read_csv(event_path)
    px = pd.read_csv(pixel_path)
    edge = pd.read_csv(edge_path)
    obj = pd.read_csv(object_path) if object_path.exists() else pd.DataFrame()
    keys = ["category", "video", "pipeline"]
    merged = px.merge(ev, on=keys, how="outer").merge(edge, on=keys, how="outer")
    if not obj.empty:
        obj_cols = [c for c in ["category", "video", "pipeline", "mAP_50"] if c in obj.columns]
        if obj_cols:
            merged = merged.merge(obj[obj_cols], on=keys, how="outer")
    merged["mAP_50"] = merged.get("mAP_50", 0)
    merged["Energy/frame"] = merged.get("Energy/frame", merged.get("energy_frame", 0))
    merged["Simulated_runtime_energy/frame"] = merged.get("simulated_runtime_energy/frame", 0)
    merged["Activation"] = merged.get("YOLO_activation_rate", 0)
    merged["Avg_FPS"] = merged.get("avg_FPS", 0)
    merged["P95_latency_ms"] = merged.get("P95_latency_ms", 0)
    merged["Reuse_rate"] = merged.get("reused_prediction_rate", 0)
    merged.to_csv(out_root / "official_like_results.csv", index=False)
    merged.to_csv(out_root / "per_video_summary.csv", index=False)
    edge.to_csv(out_root / "edge_runtime_summary.csv", index=False)
    per_category = merged.groupby(["category", "pipeline"], as_index=False).mean(numeric_only=True)
    per_category.to_csv(out_root / "per_category_summary.csv", index=False)

    final = merged.groupby("pipeline", as_index=False).mean(numeric_only=True)
    final = final.rename(columns={"pipeline": "Pipeline", "FMeasure": "CDnet_FMeasure"})
    for col in ["CDnet_FMeasure", "Event_F1", "mAP_50", "Activation", "Avg_FPS", "P95_latency_ms", "Energy/frame", "Simulated_runtime_energy/frame", "Reuse_rate"]:
        if col not in final.columns:
            final[col] = 0.0
    max_f = max(1e-9, float(final["CDnet_FMeasure"].max()))
    max_event = max(1e-9, float(final["Event_F1"].max()))
    max_fps = max(1e-9, float(final["Avg_FPS"].max()))
    max_energy = max(1e-9, float(final["Energy/frame"].max()))
    final["AE_Score"] = (
        0.35 * (final["CDnet_FMeasure"] / max_f)
        + 0.25 * (final["Event_F1"] / max_event)
        + 0.15 * (1.0 - final["Activation"])
        + 0.15 * (final["Avg_FPS"] / max_fps)
        + 0.10 * (1.0 - final["Energy/frame"] / max_energy)
    )
    final["Pareto"] = True
    final["Pipeline"] = pd.Categorical(final["Pipeline"], categories=pipelines, ordered=True)
    final = final.sort_values("Pipeline")
    final["Pipeline"] = final["Pipeline"].astype(str)
    cols = ["Pipeline", "CDnet_FMeasure", "Event_F1", "mAP_50", "Activation", "Avg_FPS", "P95_latency_ms", "Energy/frame", "Simulated_runtime_energy/frame", "Reuse_rate", "AE_Score", "Pareto"]
    final[cols].to_csv(out_root / "final_main_comparison.csv", index=False)

    metrics = [
        ("Best CDnet_FMeasure", "CDnet_FMeasure", "max"),
        ("Best Event_F1", "Event_F1", "max"),
        ("Best mAP_50", "mAP_50", "max"),
        ("Lowest Activation", "Activation", "min"),
        ("Highest Avg_FPS", "Avg_FPS", "max"),
        ("Lowest P95 latency", "P95_latency_ms", "min"),
        ("Lowest Energy/frame", "Energy/frame", "min"),
        ("Lowest Simulated_runtime_energy/frame", "Simulated_runtime_energy/frame", "min"),
        ("Highest AE_Score", "AE_Score", "max"),
    ]
    best_rows = []
    for label, col, direction in metrics:
        idx = final[col].idxmax() if direction == "max" else final[col].idxmin()
        best_rows.append({"metric": label, "Pipeline": final.loc[idx, "Pipeline"], "value": final.loc[idx, col]})
    pd.DataFrame(best_rows).to_csv(out_root / "best_by_metric.csv", index=False)

    base = final[final["Pipeline"] == "P3_MOG2"]
    comparisons = [
        ("ASMAG_TR_CONTROLLER", "P3_MOG2"),
        ("ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED", "P3_MOG2"),
        ("ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED", "ASMAG_TR_CONTROLLER"),
        ("ASMAG_TR_FAST", "P3_MOG2"),
        ("P2_FrameDiff", "P3_MOG2"),
        ("P1_YOLO_Only", "P3_MOG2"),
    ]
    gain_rows = []
    for left, right in comparisons:
        ldf = final[final["Pipeline"] == left]
        rdf = final[final["Pipeline"] == right]
        if ldf.empty or rdf.empty:
            continue
        lrow, rrow = ldf.iloc[0], rdf.iloc[0]
        gain_rows.append({
            "Comparison": f"{left} vs {right}",
            "FMeasure_gain": lrow["CDnet_FMeasure"] - rrow["CDnet_FMeasure"],
            "Event_F1_gain": lrow["Event_F1"] - rrow["Event_F1"],
            "Activation_saving": rrow["Activation"] - lrow["Activation"],
            "Energy_saving": rrow["Energy/frame"] - lrow["Energy/frame"],
            "Simulated_runtime_energy_saving": rrow["Simulated_runtime_energy/frame"] - lrow["Simulated_runtime_energy/frame"],
            "FPS_gain": lrow["Avg_FPS"] - rrow["Avg_FPS"],
            "P95_latency_gain": rrow["P95_latency_ms"] - lrow["P95_latency_ms"],
            "AE_Score_gain": lrow["AE_Score"] - rrow["AE_Score"],
            "Interpretation": "positive savings mean lower activation/energy/latency than comparison",
        })
    pd.DataFrame(gain_rows).to_csv(out_root / "gain_summary.csv", index=False)

    frame_runtime = out_root / "frame_runtime_log.csv"
    if frame_runtime.exists():
        fr = pd.read_csv(frame_runtime)
        if "selected_mode" in fr.columns:
            mode = fr[fr["selected_mode"].fillna("") != ""].groupby(["pipeline", "selected_mode"], as_index=False).size()
            mode.to_csv(out_root / "mode_usage_summary.csv", index=False)
    if not (out_root / "mode_usage_summary.csv").exists():
        pd.DataFrame(columns=["pipeline", "selected_mode", "size"]).to_csv(out_root / "mode_usage_summary.csv", index=False)

    charts_dir = ensure(out_root / "charts")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        chart_specs = [
            ("fmeasure_by_pipeline.png", "CDnet_FMeasure", "FMeasure"),
            ("event_f1_by_pipeline.png", "Event_F1", "Event F1"),
            ("fps_by_pipeline.png", "Avg_FPS", "Avg FPS"),
            ("latency_p95_by_pipeline.png", "P95_latency_ms", "P95 latency ms"),
            ("cpu_by_pipeline.png", "avg_process_cpu_percent", "CPU %"),
            ("ram_by_pipeline.png", "avg_ram_mb", "RAM MB"),
            ("activation_by_pipeline.png", "Activation", "Activation"),
            ("energy_by_pipeline.png", "Energy/frame", "Energy/frame"),
            ("simulated_energy_by_pipeline.png", "Simulated_runtime_energy/frame", "Sim runtime energy/frame"),
        ]
        chart_source = final.merge(edge.groupby("pipeline", as_index=False).mean(numeric_only=True).rename(columns={"pipeline": "Pipeline"}), on="Pipeline", how="left")
        for filename, col, ylabel in chart_specs:
            if col not in chart_source.columns:
                continue
            plt.figure(figsize=(10, 5))
            plt.bar(chart_source["Pipeline"], chart_source[col].astype(float))
            plt.xticks(rotation=25, ha="right")
            plt.ylabel(ylabel)
            plt.tight_layout()
            plt.savefig(charts_dir / filename, dpi=160)
            plt.close()
        plt.figure(figsize=(7, 5))
        plt.scatter(final["Energy/frame"], final["CDnet_FMeasure"])
        for _, row in final.iterrows():
            plt.annotate(row["Pipeline"], (row["Energy/frame"], row["CDnet_FMeasure"]), fontsize=8)
        plt.xlabel("Energy/frame")
        plt.ylabel("FMeasure")
        plt.tight_layout()
        plt.savefig(charts_dir / "pareto_fmeasure_energy.png", dpi=160)
        plt.close()
        plt.figure(figsize=(7, 5))
        plt.scatter(final["Activation"], final["CDnet_FMeasure"])
        for _, row in final.iterrows():
            plt.annotate(row["Pipeline"], (row["Activation"], row["CDnet_FMeasure"]), fontsize=8)
        plt.xlabel("Activation")
        plt.ylabel("FMeasure")
        plt.tight_layout()
        plt.savefig(charts_dir / "pareto_activation_fmeasure.png", dpi=160)
        plt.close()
        for filename, value_col in [("per_category_fmeasure_heatmap.png", "CDnet_FMeasure"), ("per_category_latency_heatmap.png", "P95_latency_ms")]:
            pivot = per_category.rename(columns={"FMeasure": "CDnet_FMeasure"}).pivot(index="category", columns="pipeline", values=value_col)
            plt.figure(figsize=(12, 6))
            plt.imshow(pivot.values.astype(float), aspect="auto")
            plt.colorbar(label=value_col)
            plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=25, ha="right")
            plt.yticks(range(len(pivot.index)), pivot.index)
            plt.tight_layout()
            plt.savefig(charts_dir / filename, dpi=160)
            plt.close()
    except Exception as exc:
        print(f"[WARN] chart generation skipped: {exc}")

    best_f = final.loc[final["CDnet_FMeasure"].idxmax()]
    best_event = final.loc[final["Event_F1"].idxmax()]
    best_fps = final.loc[final["Avg_FPS"].idxmax()]
    best_latency = final.loc[final["P95_latency_ms"].idxmin()]
    best_energy = final.loc[final["Energy/frame"].idxmin()]
    lines = [
        "# Official-Like Edge Profile Summary",
        "",
        f"Updated at `{now_iso()}`.",
        "",
        f"- Best FMeasure: `{best_f['Pipeline']}` (`{best_f['CDnet_FMeasure']:.4f}`).",
        f"- Best Event_F1: `{best_event['Pipeline']}` (`{best_event['Event_F1']:.4f}`).",
        f"- Best FPS: `{best_fps['Pipeline']}` (`{best_fps['Avg_FPS']:.4f}`).",
        f"- Best latency: `{best_latency['Pipeline']}` (`{best_latency['P95_latency_ms']:.4f}` ms P95).",
        f"- Best activation/energy: `{best_energy['Pipeline']}` (`{best_energy['Energy/frame']:.4f}` energy/frame).",
        "- ASMAG_TR_CONTROLLER remains the category-aware upper-bound comparator when present.",
        "- ONLINE_CALIBRATED is the deployable label-free variant to watch; confirm after full frame_step=1 completes.",
        "- This partial/complete official-like run should be compared against sampled results before final paper claims.",
        "- CPU-only edge profiling reports latency/FPS/CPU/RAM without requiring NVIDIA CUDA.",
        "- Limitation: CPU-only PC profiling is a proxy for true embedded edge hardware.",
    ]
    (out_root / "auto_research_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def collect_completed_sequence_summaries(out_root, pipelines):
    out_root = Path(out_root)
    all_ev, all_px, all_edge, all_obj = [], [], [], []
    for pipeline in pipelines:
        for event_path in (out_root / "raw_results").rglob(f"{pipeline}/sequence_event_summary.csv"):
            seq_dir = event_path.parent
            pixel_path = seq_dir / "sequence_pixel_summary.csv"
            edge_path = seq_dir / "sequence_edge_summary.csv"
            object_path = seq_dir / "sequence_object_summary.csv"
            if not (pixel_path.exists() and edge_path.exists() and object_path.exists()):
                continue
            all_ev.append(pd.read_csv(event_path).iloc[0].to_dict())
            all_px.append(pd.read_csv(pixel_path).iloc[0].to_dict())
            all_edge.append(pd.read_csv(edge_path).iloc[0].to_dict())
            all_obj.append(pd.read_csv(object_path).iloc[0].to_dict())
    return all_ev, all_px, all_edge, all_obj

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

def write_online_controller_diagnostics(out_root, frame_rows):
    if not frame_rows:
        return
    df = pd.DataFrame(frame_rows)
    df = df[df["pipeline"].isin(ONLINE_CONTROLLER_PIPELINES)].copy()
    if df.empty or "SceneDifficulty" not in df.columns:
        return

    def pctl(values, q):
        return float(values.quantile(q)) if len(values) else 0.0

    scene_rows = []
    usage_rows = []
    for (category, video, pipeline), group in df.groupby(["category", "video", "pipeline"], sort=False):
        difficulty = group["SceneDifficulty"].astype(float)
        scene_rows.append({
            "category": category,
            "video": video,
            "pipeline": pipeline,
            "frames": len(group),
            "scene_difficulty_mean": float(difficulty.mean()),
            "scene_difficulty_std": float(difficulty.std(ddof=0)),
            "scene_difficulty_min": float(difficulty.min()),
            "scene_difficulty_p25": pctl(difficulty, 0.25),
            "scene_difficulty_p50": pctl(difficulty, 0.50),
            "scene_difficulty_p75": pctl(difficulty, 0.75),
            "scene_difficulty_p90": pctl(difficulty, 0.90),
            "scene_difficulty_p95": pctl(difficulty, 0.95),
            "scene_difficulty_max": float(difficulty.max()),
        })
        counts = group["selected_mode"].value_counts()
        frames = max(1, len(group))
        usage_rows.append({
            "category": category,
            "video": video,
            "pipeline": pipeline,
            "frames": len(group),
            "FAST_frames": int(counts.get("FAST", 0)),
            "ACC_frames": int(counts.get("ACC", 0)),
            "P3_FALLBACK_frames": int(counts.get("P3_FALLBACK", 0)),
            "FAST_rate": float(counts.get("FAST", 0) / frames),
            "ACC_rate": float(counts.get("ACC", 0) / frames),
            "P3_FALLBACK_rate": float(counts.get("P3_FALLBACK", 0) / frames),
        })

    pd.DataFrame(scene_rows).to_csv(Path(out_root) / "online_scene_difficulty_summary.csv", index=False)
    pd.DataFrame(usage_rows).to_csv(Path(out_root) / "online_mode_usage_by_video.csv", index=False)

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
    is_online_controller = pipeline_name in ONLINE_CONTROLLER_PIPELINES
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
    expected_for_resume = expected_eval_frame_count(seq, cfg)
    if bool(cfg.get("resume_existing_results", False)) and sequence_result_complete(
        out_root,
        seq["category"],
        seq["video"],
        pipeline_name,
        expected_for_resume,
    ):
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
    } or is_online_controller
    if eval_positions and frames_source is None and uses_bg_subtractor:
        loop_positions = range(eval_positions[0], eval_positions[-1] + 1)
    else:
        loop_positions = eval_positions
    if eval_positions and frames_source is None and uses_bg_subtractor and warmup_frames > 0:
        warmup_start = max(0, eval_positions[0] - warmup_frames)
        warmup_positions = range(warmup_start, eval_positions[0])
    else:
        warmup_positions = []

    online_gates = {}
    online_estimator = None
    if is_online_controller:
        online_gates = {
            "P3_FALLBACK": MOG2Gate(min_area_ratio=cfg.get("p4_asmag_plus", {}).get("min_area_ratio", 0.001)),
            "ACC": ASMAGPlusEfficientGate(p4_efficient_cfg_for_pipeline(cfg, "ASMAG_TR_ACC")),
            "FAST": ASMAGPlusEfficientGate(p4_efficient_cfg_for_pipeline(cfg, "ASMAG_TR_FAST")),
        }
        if pipeline_name == ONLINE_CONTROLLER_CALIBRATED_PIPELINE:
            online_cfg_key = "online_controller_calibrated"
        elif pipeline_name == ONLINE_CONTROLLER_P3TUNED_PIPELINE:
            online_cfg_key = "online_controller_p3tuned"
        else:
            online_cfg_key = "online_controller"
        online_estimator = OnlineSceneDifficultyEstimator(cfg.get(online_cfg_key, cfg.get("online_controller", {})))
        gate = None
    elif pipeline_key == "P2_FrameDiff":
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
        if is_online_controller:
            for online_gate in online_gates.values():
                online_gate.process(frame, prev)
        else:
            gate.process(frame, prev)
        prev = frame.copy()
        warmup_processed += 1

    if warmup_processed and is_online_controller:
        for online_gate in online_gates.values():
            if hasattr(online_gate, "reset_runtime_state"):
                online_gate.reset_runtime_state()
    elif warmup_processed and hasattr(gate, "reset_runtime_state"):
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
            if is_online_controller:
                for online_gate in online_gates.values():
                    online_gate.process(frame, prev, {"is_evaluation": False})
            elif pipeline_key != "P1_YOLO_Only":
                gate.process(frame, prev, {"is_evaluation": False})
            prev = frame.copy()
            continue

        frame_start_time = now_iso()
        t0 = time.time()
        frame_label = frame_number(frame_files[idx]) if frames_source is None else idx
        evaluated_index = processed

        gate_open = True
        gate_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        gate_info = {"gate_score": 1.0, "motion_area": 0, "watchdog_triggered": 0}

        if pipeline_key != "P1_YOLO_Only":
            gate_state = {
                "is_evaluation": True,
                "evaluated_index": evaluated_index,
                "raw_frame_id": frame_label,
            }
            if is_online_controller:
                online_outputs = {}
                for mode, online_gate in online_gates.items():
                    online_outputs[mode] = online_gate.process(frame, prev, gate_state)
                telemetry_open, _, telemetry_info = online_outputs["ACC"]
                telemetry_info["image_area"] = frame.shape[0] * frame.shape[1]
                feature_info = online_estimator.update(
                    telemetry_info,
                    telemetry_open,
                    0,
                    0,
                    evaluated_index,
                )
                controller_selected_mode = feature_info["selected_mode"]
                category_policy_mode = "ONLINE"
                gate_open, gate_mask, gate_info = online_outputs[controller_selected_mode]
                gate_info = {**gate_info, **feature_info, "image_area": frame.shape[0] * frame.shape[1]}
            else:
                gate_open, gate_mask, gate_info = gate.process(frame, prev, gate_state)

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
            if pipeline_key == "P4_ASMAG_PLUS_EFFICIENT_REUSE" or (is_online_controller and controller_selected_mode in {"ACC", "FAST"}):
                if is_online_controller:
                    reuse_cfg = p4_efficient_cfg_for_pipeline(cfg, CONTROLLER_MODE_TO_PIPELINE[controller_selected_mode])
                else:
                    reuse_cfg = p4_efficient_cfg_for_pipeline(cfg, execution_pipeline_name)
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

        if is_online_controller and controller_selected_mode in online_gates and hasattr(online_gates[controller_selected_mode], "update_after_detection"):
            online_gates[controller_selected_mode].update_after_detection(bool(gate_open and np.sum(pred_mask > 0) > 0))
        elif pipeline_key in {"P4_ASMAG_PLUS", "P4_ASMAG_PLUS_PRECISION", "P4_ASMAG_PLUS_BALANCED", "P4_ASMAG_PLUS_EFFICIENT", "P4_ASMAG_PLUS_EFFICIENT_REUSE"} and hasattr(gate, "update_after_detection"):
            gate.update_after_detection(bool(gate_open and np.sum(pred_mask > 0) > 0))

        if delay > 0:
            time.sleep(delay)
        latency_ms = (time.time()-t0)*1000
        frame_end_time = now_iso()
        fps = 1000.0/latency_ms if latency_ms > 0 else 0
        cpu, ram = cpu_ram_percent(proc, cores, ram_gb)
        system_cpu = psutil.cpu_percent(interval=None)
        process_ram_mb = proc.memory_info().rss / (1024 * 1024)
        system_ram_percent = psutil.virtual_memory().percent
        gpu_util, gpu_memory = gpu_profile()

        pred_alert = bool(np.sum(pred_mask > 0) > 0)
        e_state, is_active = event_state_from_masks(pred_alert, gt, cdnet_gt_config)
        if is_online_controller and online_estimator.history:
            online_estimator.history[-1]["is_active"] = int(is_active)
            online_estimator.history[-1]["reuse_success"] = int(reused_prediction)
            online_estimator.history[-1]["gate_closed"] = int(not gate_open)
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
        energy_pipeline_key = pipeline_key
        if is_online_controller:
            energy_pipeline_key = canonical_pipeline_name(CONTROLLER_MODE_TO_PIPELINE[controller_selected_mode])
        mog2_used, framediff_used = energy_usage_flags(energy_pipeline_key)
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
            "start_time": frame_start_time,
            "end_time": frame_end_time,
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
            "fps_instant": fps,
            "CPU_Usage": cpu,
            "RAM_Usage": ram,
            "process_cpu_percent": cpu,
            "system_cpu_percent": system_cpu,
            "process_ram_mb": process_ram_mb,
            "system_ram_percent": system_ram_percent,
            "gpu_util_percent": gpu_util,
            "gpu_memory_mb": gpu_memory,
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
            "energy_proxy_frame": energy_value,
            "simulated_runtime_energy_frame": "",
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
    if not df.empty:
        max_latency = max(1e-9, float(df["latency_ms"].max()))
        gpu_norm = df["gpu_util_percent"].fillna(0).astype(float) / 100.0 if "gpu_util_percent" in df.columns else 0.0
        df["simulated_runtime_energy_frame"] = (
            1.0
            + 5.0 * df["yolo_called"].astype(float)
            + 1.0 * (df["process_cpu_percent"].astype(float) / 100.0)
            + 1.0 * (df["latency_ms"].astype(float) / max_latency)
            + 2.0 * gpu_norm
            + 0.1 * df["reused_prediction"].astype(float)
        )
    df.to_csv(seq_out / "frame_metrics.csv", index=False)
    edge_cols = [
        "pipeline",
        "category",
        "video",
        "frame_id",
        "evaluated_index",
        "start_time",
        "end_time",
        "latency_ms",
        "fps_instant",
        "process_cpu_percent",
        "system_cpu_percent",
        "process_ram_mb",
        "system_ram_percent",
        "gpu_util_percent",
        "gpu_memory_mb",
        "yolo_called",
        "reused_prediction",
        "selected_mode",
        "energy_proxy_frame",
        "simulated_runtime_energy_frame",
    ]
    edge_profile_df = df[[c for c in edge_cols if c in df.columns]].copy() if not df.empty else pd.DataFrame(columns=edge_cols)
    edge_profile_df.to_csv(seq_out / "edge_profile.csv", index=False)
    append_csv(out_root / "frame_runtime_log.csv", edge_profile_df)
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
    runtime_seconds = float(df["latency_ms"].sum() / 1000.0) if not df.empty else 0.0
    energy_per_frame = float(df["energy_frame"].mean()) if not df.empty and "energy_frame" in df.columns else 0.0
    simulated_energy_per_frame = float(df["simulated_runtime_energy_frame"].mean()) if not df.empty and "simulated_runtime_energy_frame" in df.columns else 0.0
    edge_summary = {
        "avg_CPU": float(df["CPU_Usage"].mean()) if not df.empty else 0,
        "avg_process_cpu_percent": float(df["process_cpu_percent"].mean()) if not df.empty else 0,
        "max_process_cpu_percent": float(df["process_cpu_percent"].max()) if not df.empty else 0,
        "median_CPU": float(df["CPU_Usage"].median()) if not df.empty else 0,
        "avg_RAM": float(df["RAM_Usage"].mean()) if not df.empty else 0,
        "avg_ram_mb": float(df["process_ram_mb"].mean()) if not df.empty else 0,
        "max_ram_mb": float(df["process_ram_mb"].max()) if not df.empty else 0,
        "avg_FPS": float(df["FPS"].mean()) if not df.empty else 0,
        "median_FPS": float(df["FPS"].median()) if not df.empty else 0,
        "avg_latency_ms": float(df["latency_ms"].mean()) if not df.empty else 0,
        "median_latency_ms": float(df["latency_ms"].median()) if not df.empty else 0,
        "P95_latency_ms": float(df["latency_ms"].quantile(0.95)) if not df.empty else 0,
        "P99_latency_ms": float(df["latency_ms"].quantile(0.99)) if not df.empty else 0,
        "YOLO_activation_rate": activation,
        "processed_frames": processed,
        "temporal_roi_start": temporal_roi_start if temporal_roi_start is not None else "",
        "temporal_roi_end": temporal_roi_end if temporal_roi_end is not None else "",
        "evaluated_frames": processed,
        "skipped_frames_before_roi": skipped_frames_before_roi,
        "warmup_frames": warmup_processed,
        "reused_prediction_count": reused_predictions,
        "reused_prediction_rate": reused_predictions / processed if processed else 0,
        "Energy/frame": energy_per_frame,
        "simulated_runtime_energy/frame": simulated_energy_per_frame,
        "runtime_seconds": runtime_seconds,
    }

    common = {"category": seq["category"], "video": seq["video"], "pipeline": pipeline_name}
    result = ({**common, **ev}, {**common, **pxsum}, {**common, **edge_summary}, {**common, **objsum})
    summary_payload = {
        **common,
        "frames_processed": processed,
        "CDnet_FMeasure": pxsum.get("FMeasure", 0),
        "Event_F1": ev.get("Event_F1", 0),
        "mAP_50": objsum.get("mAP_50", 0),
        "Activation": activation,
        "Reuse_rate": reused_predictions / processed if processed else 0,
        "Avg_FPS": edge_summary["avg_FPS"],
        "avg_latency_ms": edge_summary["avg_latency_ms"],
        "median_latency_ms": edge_summary["median_latency_ms"],
        "p95_latency_ms": edge_summary["P95_latency_ms"],
        "p99_latency_ms": edge_summary["P99_latency_ms"],
        "avg_process_cpu_percent": edge_summary["avg_process_cpu_percent"],
        "max_process_cpu_percent": edge_summary["max_process_cpu_percent"],
        "avg_ram_mb": edge_summary["avg_ram_mb"],
        "max_ram_mb": edge_summary["max_ram_mb"],
        "Energy/frame": edge_summary["Energy/frame"],
        "simulated_runtime_energy/frame": edge_summary["simulated_runtime_energy/frame"],
        "runtime_seconds": edge_summary["runtime_seconds"],
    }
    with open(seq_out / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)
    for payload, path in zip(result, resume_paths.values()):
        pd.DataFrame([payload]).to_csv(path, index=False)
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-plan", default="")
    ap.add_argument("--max-videos-per-run", type=int, default=None)
    ap.add_argument("--progress-only", action="store_true")
    ap.add_argument("--category", default="")
    ap.add_argument("--video", default="")
    ap.add_argument("--pipeline", default="")
    ap.add_argument("--max-frames", type=int, default=None)
    args = ap.parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_config_path"] = args.config
    configure_runtime(cfg)

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
    sequences = apply_run_filters(sequences, cfg, args)

    if not sequences:
        print("[ERROR] No sequences found. Check dataset_root/categories.")
        return

    progress_path = initialize_run_progress(out_root, sequences, cfg["pipelines"], cfg)
    default_resume = f"python src/run_experiment.py --config {args.config}"
    resume_run_plan = args.run_plan or cfg.get("run_plan", "")
    if resume_run_plan:
        default_resume += f" --run-plan {resume_run_plan}"
    if args.max_videos_per_run:
        default_resume += f" --max-videos-per-run {args.max_videos_per_run}"
    elif resume_run_plan:
        default_resume += " --max-videos-per-run 1"
    if args.progress_only:
        print_progress_summary(progress_path, "PROGRESS ONLY")
        update_daily_progress_report(out_root, progress_path, default_resume.replace(" --progress-only", ""))
        return

    sequences = limit_sequences_for_run(sequences, progress_path, args.max_videos_per_run)

    all_ev, all_px, all_edge, all_obj, all_cdnet_frame_rows = [], [], [], [], []
    for seq in sequences:
        print(f"\n[SEQ] {seq['category']}/{seq['video']}")
        for p in cfg["pipelines"]:
            print(f"  - Running {p} ...")
            update_run_progress(progress_path, seq["category"], seq["video"], p, "running")
            try:
                ev, px, ed, obj = unpack_sequence_result(process_sequence(cfg, seq, p, detector, frames, gts))
                update_run_progress(
                    progress_path,
                    seq["category"],
                    seq["video"],
                    p,
                    "completed",
                    metrics={
                        "frames_done": ed.get("evaluated_frames", ed.get("processed_frames", "")),
                        "runtime_seconds": ed.get("runtime_seconds", ""),
                        "avg_fps": ed.get("avg_FPS", ""),
                        "p95_latency_ms": ed.get("P95_latency_ms", ""),
                        "activation": ed.get("YOLO_activation_rate", ""),
                        "energy_per_frame": ed.get("Energy/frame", ""),
                        "simulated_runtime_energy_per_frame": ed.get("simulated_runtime_energy/frame", ""),
                    },
                )
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
        update_daily_progress_report(out_root, progress_path, default_resume)

    all_ev, all_px, all_edge, all_obj = collect_completed_sequence_summaries(out_root, cfg["pipelines"])
    all_cdnet_frame_rows = []
    for frame_metrics_path in (out_root / "raw_results").rglob("frame_metrics.csv"):
        try:
            all_cdnet_frame_rows.extend(pd.read_csv(frame_metrics_path).to_dict("records"))
        except Exception:
            pass

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
        "ASMAG_TR_CONTROLLER_ONLINE",
        "ASMAG_TR_CONTROLLER_ONLINE_P3TUNED",
        "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED",
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
    write_online_controller_diagnostics(out_root, all_cdnet_frame_rows)
    pareto_summary = write_pareto_metrics(out_root, cfg.get("pareto", {}))
    create_summary_charts(out_root)
    write_official_edge_reports(out_root, cfg["pipelines"])
    update_daily_progress_report(out_root, progress_path, default_resume)

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
    print_progress_summary(progress_path, "END PROGRESS")
    print(f"[NEXT_RESUME_COMMAND] {default_resume}")

if __name__ == "__main__":
    main()
