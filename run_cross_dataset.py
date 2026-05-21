from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional

import cv2
import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datasets.base_adapter import CDNet2014Adapter, BaseDatasetAdapter, safe_name
from datasets.bmc_adapter import BMCAdapter
from datasets.lasiesta_adapter import LASIESTAAdapter
from datasets.sbi2015_adapter import SBI2015Adapter
from evaluation.ignore_mask_utils import combine_ignore_masks
from evaluation.mask_normalization import encode_cdnet_style_gt, normalize_prediction_mask
from tools.aggregate_cross_dataset import aggregate_cross_dataset
from tools.plot_cross_dataset import create_cross_dataset_charts
from tools.stat_cross_dataset import write_cross_dataset_stats

sys.path.insert(0, str(SRC_DIR))
importlib.invalidate_caches()

from detectors.detectors import create_detector
from run_experiment import (
    PROGRESS_COLUMNS,
    configure_runtime,
    expected_eval_frame_count,
    process_sequence,
    sequence_result_complete,
    update_run_progress,
)


PIPELINES = [
    "P1_YOLO_Only",
    "P2_FrameDiff",
    "P3_MOG2",
    "ASMAG_TR_FAST",
    "ASMAG_TR_ACC",
    "ASMAG_TR_CONTROLLER",
    "ASMAG_TR_CONTROLLER_ONLINE",
]

ADAPTERS = {
    "cdnet": CDNet2014Adapter,
    "cdnet2014": CDNet2014Adapter,
    "lasiesta": LASIESTAAdapter,
    "sbi": SBI2015Adapter,
    "sbi2015": SBI2015Adapter,
    "sbmi": SBI2015Adapter,
    "sbmi2015": SBI2015Adapter,
    "bmc": BMCAdapter,
    "bmc2012": BMCAdapter,
}


def main():
    parser = argparse.ArgumentParser(description="Unified ASMAG-TRC cross-dataset evaluator.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset_root", default="")
    parser.add_argument("--pipelines", nargs="*", default=None)
    parser.add_argument("--videos", nargs="*", default=None)
    parser.add_argument("--max_frames", type=int, default=None)
    parser.add_argument("--resume", default=None, help="true/false; default comes from config")
    parser.add_argument("--output_dir", default="")
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    dataset_name = str(_cfg_get(cfg, "dataset.name", cfg.get("dataset_name", "")) or "").strip()
    adapter_name = str(_cfg_get(cfg, "dataset.adapter", cfg.get("adapter", dataset_name)) or dataset_name).lower()
    if not dataset_name:
        dataset_name = adapter_name
    adapter = build_adapter(adapter_name, args.dataset_root or cfg.get("dataset_root") or _cfg_get(cfg, "dataset.root", ""), cfg)

    pipelines = parse_list(args.pipelines) or list(cfg.get("pipelines", PIPELINES))
    videos = select_videos(adapter, parse_list(args.videos) or cfg.get("videos", None))
    if not videos:
        raise RuntimeError(f"No videos found for adapter={adapter_name} root={adapter.root}")

    output_dir = resolve_output_dir(cfg, args.output_dir, dataset_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "charts").mkdir(parents=True, exist_ok=True)

    resume = parse_bool(args.resume, bool(cfg.get("resume", cfg.get("resume_existing_results", True))))
    runtime_cfg = prepare_runtime_config(cfg, output_dir, dataset_name, pipelines, resume, args.max_frames)
    runtime_cfg["_config_path"] = str(config_path)
    configure_runtime(runtime_cfg)

    sequences = materialize_adapter_cache(
        adapter,
        videos,
        output_dir,
        refresh=bool(_cfg_get(cfg, "adapter_cache.refresh", False)),
        cache_frame_ext=str(_cfg_get(cfg, "adapter_cache.frame_ext", ".jpg")),
        eval_cfg=runtime_cfg.get("evaluation", {}),
    )
    write_resolved_config(output_dir, runtime_cfg, adapter, videos, config_path)

    progress_path = initialize_cross_progress(output_dir, sequences, pipelines, runtime_cfg, resume)
    detector = create_detector(
        runtime_cfg.get("detector_mode", "mock"),
        runtime_cfg.get("model_path", ""),
        runtime_cfg.get("model_name", "mock_detector"),
    )
    print(f"[RUN] dataset={dataset_name} videos={len(sequences)} pipelines={len(pipelines)}")
    print(f"[OUT] {output_dir}")
    print(f"[DETECTOR] {runtime_cfg.get('detector_mode')} - {runtime_cfg.get('model_name')}")

    session_started_at = time.time()
    for seq in sequences:
        print(f"\n[SEQ] {seq['category']}/{seq['video']}")
        for pipeline in pipelines:
            status = get_progress_status(progress_path, seq["category"], seq["video"], pipeline)
            if resume and status == "completed":
                print(f"  - Skipping completed {pipeline}")
                continue
            print(f"  - Running {pipeline}")
            update_run_progress(progress_path, seq["category"], seq["video"], pipeline, "running")
            try:
                ev, px, edge, _obj = process_sequence(
                    runtime_cfg,
                    seq,
                    pipeline,
                    detector,
                    frames_source=None,
                    gts_source=None,
                    progress_path=progress_path,
                    session_started_at=session_started_at,
                )
                metrics = {
                    "frames_done": edge.get("evaluated_frames", edge.get("processed_frames", "")),
                    "progress_percent": 100.0,
                    "runtime_seconds": edge.get("runtime_seconds", ""),
                    "avg_fps": edge.get("avg_FPS", ""),
                    "p95_latency_ms": edge.get("P95_latency_ms", ""),
                    "activation": edge.get("YOLO_activation_rate", ""),
                    "energy_per_frame": edge.get("Energy/frame", ""),
                    "simulated_runtime_energy_per_frame": edge.get("simulated_runtime_energy/frame", ""),
                }
                update_run_progress(progress_path, seq["category"], seq["video"], pipeline, "completed", metrics=metrics)
                print(
                    f"    F={px.get('FMeasure', 0):.4f} "
                    f"EventF1={ev.get('Event_F1', 0):.4f} "
                    f"Act={edge.get('YOLO_activation_rate', 0):.4f} "
                    f"FPS={edge.get('avg_FPS', 0):.2f}"
                )
            except Exception as exc:
                update_run_progress(progress_path, seq["category"], seq["video"], pipeline, "failed", repr(exc))
                print(f"    [FAILED] {repr(exc)}")

    aggregate_cross_dataset(output_dir, dataset_name, float(_cfg_get(cfg, "failure_cases.low_fmeasure_threshold", 0.25)))
    create_cross_dataset_charts(output_dir)
    try:
        write_cross_dataset_stats(output_dir)
    except Exception as exc:
        print(f"[WARN] stat summary skipped: {exc}")

    print("\n[DONE] Cross-dataset outputs:")
    for name in ["config.yaml", "run_progress.csv", "per_frame_log.csv", "per_video_summary.csv", "final_summary.csv", "failure_cases.csv"]:
        print(f" - {output_dir / name}")
    print(f" - {output_dir / 'charts'}")


def build_adapter(adapter_name: str, dataset_root: str | Path, cfg: dict) -> BaseDatasetAdapter:
    adapter_cls = ADAPTERS.get(adapter_name.lower())
    if adapter_cls is None:
        raise ValueError(f"Unsupported adapter '{adapter_name}'. Available: {', '.join(sorted(ADAPTERS))}")
    adapter_cfg = dict(cfg.get("adapter_config", {}))
    adapter_cfg.update(_cfg_get(cfg, "dataset.adapter_config", {}) or {})
    return adapter_cls(dataset_root, adapter_cfg)


def select_videos(adapter: BaseDatasetAdapter, requested) -> List[str]:
    all_videos = adapter.list_videos()
    tokens = parse_list(requested)
    if not tokens or tokens == ["auto"]:
        return all_videos
    wanted = {str(token).strip() for token in tokens if str(token).strip()}
    selected = []
    for video_id in all_videos:
        video = adapter.get_video(video_id)
        aliases = {
            video_id,
            video_id.replace("\\", "/"),
            video.video,
            f"{video.category}/{video.video}",
            safe_name(video_id),
            safe_name(video.video),
        }
        if aliases & wanted:
            selected.append(video_id)
    missing = sorted(wanted - {alias for vid in selected for alias in _video_aliases(adapter, vid)})
    if missing:
        print(f"[WARN] Requested videos not found: {', '.join(missing)}")
    return selected


def _video_aliases(adapter: BaseDatasetAdapter, video_id: str) -> set:
    video = adapter.get_video(video_id)
    return {video_id, video.video, f"{video.category}/{video.video}", safe_name(video_id), safe_name(video.video)}


def materialize_adapter_cache(
    adapter: BaseDatasetAdapter,
    video_ids: Iterable[str],
    output_dir: Path,
    refresh: bool = False,
    cache_frame_ext: str = ".jpg",
    eval_cfg: Optional[dict] = None,
) -> List[dict]:
    cache_root = output_dir / "_adapter_cache"
    manifest_rows = []
    sequences = []
    for video_id in video_ids:
        video = adapter.get_video(video_id)
        category = safe_name(video.category)
        name = safe_name(video.video)
        seq_root = cache_root / category / name
        input_dir = seq_root / "input"
        gt_dir = seq_root / "groundtruth"
        input_dir.mkdir(parents=True, exist_ok=True)
        gt_dir.mkdir(parents=True, exist_ok=True)

        frame_count = 0
        missing_gt = 0
        frame_window = cache_frame_window(video, eval_cfg or {})
        cache_limit = cache_limit_for_materialization(eval_cfg or {}) if frame_window is None else None
        for record in adapter.iter_frames(video_id):
            if frame_window is not None:
                start_frame, end_frame = frame_window
                if record.frame_id < start_frame:
                    continue
                if record.frame_id > end_frame:
                    break
            if cache_limit is not None and frame_count >= cache_limit:
                break
            frame_count += 1
            frame_id = int(record.frame_id)
            frame_target = input_dir / f"in{frame_id:06d}{cache_frame_ext}"
            gt_target = gt_dir / f"gt{frame_id:06d}.png"

            _link_or_copy(record.frame_path, frame_target, refresh=refresh)

            if record.gt_path is None:
                frame = adapter.load_frame(record.frame_path)
                raw_gt = np.zeros(frame.shape[:2], dtype=np.uint8)
                ignore_mask = np.zeros(frame.shape[:2], dtype=bool)
                missing_gt += 1
            else:
                raw_gt = adapter.load_gt_mask(record.gt_path)
                normalized = adapter.normalize_gt_mask(raw_gt)
                ignore_masks = [adapter.get_ignore_mask(raw_gt)]
                if record.ignore_path is not None:
                    raw_ignore = adapter.load_gt_mask(record.ignore_path)
                    separate = normalize_prediction_mask(raw_ignore) > 0
                    if not bool(adapter.config.get("ignore_dir_positive_is_ignore", True)):
                        separate = ~separate
                    ignore_masks.append(separate)
                ignore_mask = combine_ignore_masks(*ignore_masks)
                raw_gt = normalized
            encoded = encode_cdnet_style_gt(raw_gt, ignore_mask=ignore_mask, ignore_value=85)
            if refresh or not gt_target.exists():
                cv2.imwrite(str(gt_target), encoded)

            manifest_rows.append(
                {
                    "video_id": video_id,
                    "category": category,
                    "video": name,
                    "frame_id": frame_id,
                    "frame_path": str(record.frame_path),
                    "gt_path": str(record.gt_path or ""),
                    "ignore_path": str(record.ignore_path or ""),
                    "cache_frame_path": str(frame_target),
                    "cache_gt_path": str(gt_target),
                    "missing_gt": int(record.gt_path is None),
                }
            )

        if video.roi_start is not None and video.roi_end is not None:
            (seq_root / "temporalROI.txt").write_text(f"{video.roi_start} {video.roi_end}\n", encoding="utf-8")

        sequences.append(
            {
                "category": category,
                "video": name,
                "input_dir": str(input_dir),
                "gt_dir": str(gt_dir),
                "roi_start": video.roi_start,
                "roi_end": video.roi_end,
                "source_video_id": video_id,
            }
        )
        print(f"[CACHE] {video_id} -> {category}/{name} frames={frame_count} missing_gt={missing_gt}")

    pd.DataFrame(manifest_rows).to_csv(output_dir / "adapter_cache_manifest.csv", index=False)
    return sequences


def cache_frame_window(video, eval_cfg: dict) -> Optional[tuple[int, int]]:
    if not bool(eval_cfg.get("use_temporal_roi", False)):
        return None
    if video.roi_start is None or video.roi_end is None:
        return None
    warmup = int(eval_cfg.get("warmup_frames", eval_cfg.get("warmup_frames_before_roi", 0)) or 0)
    start_frame = max(0, int(video.roi_start) - warmup)
    end_frame = int(video.roi_end)
    max_frames = eval_cfg.get("max_frames_per_video", None)
    if max_frames not in (None, "", "null", "None"):
        end_frame = min(end_frame, int(video.roi_start) + int(max_frames) - 1)
    return start_frame, end_frame


def cache_limit_for_materialization(eval_cfg: dict) -> Optional[int]:
    if bool(eval_cfg.get("use_temporal_roi", False)):
        return None
    max_frames = eval_cfg.get("max_frames_per_video", None)
    if max_frames in (None, "", "null", "None"):
        return None
    return int(max_frames)


def _link_or_copy(source: Path, target: Path, refresh: bool = False) -> None:
    if target.exists():
        if not refresh:
            return
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except Exception:
        try:
            target.symlink_to(source)
        except Exception:
            shutil.copy2(source, target)


def prepare_runtime_config(
    cfg: dict,
    output_dir: Path,
    dataset_name: str,
    pipelines: List[str],
    resume: bool,
    max_frames: Optional[int],
) -> dict:
    runtime_cfg = dict(cfg)
    runtime_cfg["dataset_mode"] = "cross_dataset"
    runtime_cfg["dataset_name"] = dataset_name
    runtime_cfg["output_root"] = str(output_dir.parent)
    runtime_cfg["experiment_name"] = output_dir.name
    runtime_cfg["pipelines"] = pipelines
    runtime_cfg["resume_existing_results"] = bool(resume)
    runtime_cfg["cdnet_gt"] = {"enabled": True, "foreground_values": [255], "background_values": [0], "ignore_values": [85]}
    runtime_cfg.setdefault("evaluation", {})
    if max_frames is not None:
        runtime_cfg["evaluation"]["max_frames_per_video"] = int(max_frames)
    runtime_cfg.setdefault("energy_proxy", {})
    runtime_cfg["energy_proxy"].setdefault("enabled", True)
    return runtime_cfg


def initialize_cross_progress(output_dir: Path, sequences: List[dict], pipelines: List[str], cfg: dict, resume: bool) -> Path:
    progress_path = output_dir / "run_progress.csv"
    previous = pd.read_csv(progress_path) if resume and progress_path.exists() else pd.DataFrame()
    previous_by_job = {}
    if not previous.empty and {"category", "video", "pipeline"}.issubset(previous.columns):
        for _, row in previous.iterrows():
            previous_by_job[(str(row["category"]), str(row["video"]), str(row["pipeline"]))] = row.to_dict()

    rows = []
    for seq in sequences:
        expected = expected_eval_frame_count(seq, cfg)
        for pipeline in pipelines:
            key = (str(seq["category"]), str(seq["video"]), str(pipeline))
            old = previous_by_job.get(key, {})
            completed = resume and sequence_result_complete(output_dir, seq["category"], seq["video"], pipeline, expected)
            row = {col: old.get(col, "") for col in PROGRESS_COLUMNS}
            row.update(
                {
                    "job_id": f"{seq['category']}/{seq['video']}/{pipeline}",
                    "category": seq["category"],
                    "video": seq["video"],
                    "pipeline": pipeline,
                    "status": "completed" if completed else "pending",
                    "frames_expected": expected,
                    "frames_done": expected if completed else 0,
                    "progress_percent": 100.0 if completed else 0.0,
                    "error_message": "" if completed else "",
                    "output_path": str(output_dir / "raw_results" / seq["category"] / seq["video"] / pipeline),
                    "message": "checkpoint exists" if completed else "",
                }
            )
            rows.append(row)
    progress = pd.DataFrame(rows, columns=PROGRESS_COLUMNS)
    progress.to_csv(progress_path, index=False)
    return progress_path


def get_progress_status(progress_path: Path, category: str, video: str, pipeline: str) -> str:
    if not progress_path.exists():
        return ""
    progress = pd.read_csv(progress_path)
    mask = (
        (progress["category"].astype(str) == str(category))
        & (progress["video"].astype(str) == str(video))
        & (progress["pipeline"].astype(str) == str(pipeline))
    )
    if not mask.any():
        return ""
    return str(progress.loc[mask, "status"].iloc[0])


def write_resolved_config(
    output_dir: Path,
    runtime_cfg: dict,
    adapter: BaseDatasetAdapter,
    videos: List[str],
    source_config_path: Path,
) -> None:
    payload = dict(runtime_cfg)
    payload["source_config"] = str(source_config_path)
    payload["dataset_root"] = str(adapter.root)
    payload["selected_videos"] = videos
    with open(output_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)


def resolve_output_dir(cfg: dict, override: str, dataset_name: str) -> Path:
    if override:
        return Path(override)
    configured = cfg.get("output_dir") or _cfg_get(cfg, "dataset.output_dir", "")
    if configured:
        return Path(configured)
    suffix = "full" if not str(dataset_name).endswith("_full") else ""
    name = f"{dataset_name}_{suffix}".strip("_")
    return Path("outputs") / "cross_dataset_full_v1_6" / name


def parse_list(value) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
        value = [value]
    out: List[str] = []
    for item in value:
        if item is None:
            continue
        out.extend(part.strip() for part in str(item).split(",") if part.strip())
    return out or None


def parse_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _cfg_get(cfg: dict, dotted_key: str, default=None):
    cur = cfg
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


if __name__ == "__main__":
    main()
