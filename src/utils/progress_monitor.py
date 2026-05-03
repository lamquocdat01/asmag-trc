import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


LIVE_PROGRESS_FIELDS = [
    "timestamp",
    "phase",
    "total_jobs",
    "completed_jobs",
    "pending_jobs",
    "running_jobs",
    "failed_jobs",
    "overall_job_percent",
    "total_videos",
    "completed_videos",
    "current_job_index",
    "completed_video_count",
    "total_video_count",
    "completed_pipelines_for_current_video",
    "total_pipelines_for_current_video",
    "current_video_completed_pipelines",
    "current_video_total_pipelines",
    "current_category",
    "current_video",
    "current_pipeline",
    "current_frame",
    "total_frames",
    "job_frame_percent",
    "evaluated_frames",
    "fps_current",
    "fps_avg",
    "latency_avg_ms",
    "latency_p95_so_far_ms",
    "cpu_process_percent",
    "ram_process_mb",
    "energy_per_frame",
    "simulated_runtime_energy_per_frame",
    "runtime_current_job_seconds",
    "runtime_session_seconds",
    "eta_current_job_seconds",
    "eta_remaining_jobs_seconds",
    "last_completed_job",
    "next_pending_job",
    "fun_status_line",
    "live_file",
    "message",
]


CORE_PIPELINES = [
    "P1_YOLO_Only",
    "P2_FrameDiff",
    "P3_MOG2",
    "ASMAG_TR_FAST",
    "ASMAG_TR_CONTROLLER",
    "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED",
]


FUN_STATUS_LINES = [
    "Đang tăng tốc, cố lên nào!",
    "Pipeline đang làm việc rất chăm chỉ...",
    "Sắp xong thêm một chặng nữa!",
    "Giữ vững phong độ, dữ liệu đang chảy về!",
    "YOLO nghỉ ít thôi, còn nhiều video phía trước 😄",
    "Progress đang đẹp lên từng frame!",
    "Thêm một ít nữa là chạm mốc mới!",
    "Bình tĩnh, video dài nhưng chúng ta bền bỉ!",
    "Một pipeline xong là gần bài báo hơn một bước!",
    "Edge profiling vẫn đang ổn định!",
]


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def safe_float(value, default=0.0):
    try:
        if value in ("", None) or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value in ("", None) or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def format_duration(seconds):
    seconds = int(max(0, safe_float(seconds, 0.0)))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def load_progress(progress_path):
    progress_path = Path(progress_path)
    if not progress_path.exists():
        return pd.DataFrame()
    return pd.read_csv(progress_path)


def summarize_progress(progress):
    if progress is None or progress.empty:
        return {
            "total": 0,
            "completed": 0,
            "pending": 0,
            "running": 0,
            "failed": 0,
            "overall_percent": 0.0,
            "current_job": "",
            "completed_video_count": 0,
            "total_video_count": 0,
            "current_job_index": 0,
            "current_video_completed_pipelines": 0,
            "current_video_total_pipelines": len(CORE_PIPELINES),
            "last_completed": None,
            "next_pending": None,
            "failed_jobs": [],
        }
    counts = progress["status"].fillna("").astype(str).value_counts().to_dict()
    total = int(len(progress))
    completed = int(counts.get("completed", 0))
    running = progress[progress["status"].fillna("").astype(str) == "running"]
    completed_rows = progress[progress["status"].fillna("").astype(str) == "completed"].copy()
    pending_rows = progress[progress["status"].fillna("").astype(str) == "pending"].copy()
    failed_rows = progress[progress["status"].fillna("").astype(str) == "failed"].copy()
    current_job = ""
    if not running.empty:
        row = running.iloc[0]
        current_job = f"{row.get('category', '')}/{row.get('video', '')}/{row.get('pipeline', '')}"
    last_completed = None
    if not completed_rows.empty:
        completed_rows["_completed_at_sort"] = completed_rows.get("completed_at", "").fillna("").astype(str)
        last_completed = completed_rows.sort_values("_completed_at_sort").iloc[-1].to_dict()
    next_pending = pending_rows.iloc[0].to_dict() if not pending_rows.empty else None
    video_groups = progress.groupby(["category", "video"])
    total_video_count = int(len(video_groups))
    completed_video_count = 0
    for _, group in video_groups:
        completed_pipelines = set(group[group["status"].fillna("").astype(str) == "completed"]["pipeline"].astype(str))
        if set(CORE_PIPELINES).issubset(completed_pipelines):
            completed_video_count += 1
    current_video_completed_pipelines = 0
    current_row = None
    if not running.empty:
        current_row = running.iloc[0]
    elif next_pending is not None:
        current_row = next_pending
    if current_row is not None:
        cur_cat = str(current_row.get("category", ""))
        cur_vid = str(current_row.get("video", ""))
        cur_group = progress[(progress["category"].astype(str) == cur_cat) & (progress["video"].astype(str) == cur_vid)]
        current_video_completed_pipelines = int(
            cur_group[
                (cur_group["pipeline"].astype(str).isin(CORE_PIPELINES))
                & (cur_group["status"].fillna("").astype(str) == "completed")
            ].shape[0]
        )
    current_job_index = 0
    index_row = None
    if not running.empty:
        index_row = running.iloc[0]
    elif next_pending is not None:
        index_row = next_pending
    if index_row is not None:
        mask = (
            (progress["category"].astype(str) == str(index_row.get("category", "")))
            & (progress["video"].astype(str) == str(index_row.get("video", "")))
            & (progress["pipeline"].astype(str) == str(index_row.get("pipeline", "")))
        )
        matches = progress.index[mask].tolist()
        if matches:
            current_job_index = int(matches[0]) + 1
    return {
        "total": total,
        "completed": completed,
        "pending": int(counts.get("pending", 0)),
        "running": int(counts.get("running", 0)),
        "failed": int(counts.get("failed", 0)),
        "overall_percent": (completed / total * 100.0) if total else 0.0,
        "current_job": current_job,
        "completed_video_count": completed_video_count,
        "total_video_count": total_video_count,
        "current_job_index": current_job_index,
        "current_video_completed_pipelines": current_video_completed_pipelines,
        "current_video_total_pipelines": len(CORE_PIPELINES),
        "last_completed": last_completed,
        "next_pending": next_pending,
        "failed_jobs": failed_rows.to_dict("records"),
    }


def estimate_remaining_jobs_seconds(progress, eta_current_job_seconds=0.0):
    if progress is None or progress.empty:
        return 0.0
    completed = progress[progress["status"].fillna("").astype(str) == "completed"].copy()
    remaining_jobs = int((progress["status"].fillna("").astype(str).isin(["pending", "running", "failed"])).sum())
    runtimes = [safe_float(v) for v in completed.get("runtime_seconds", [])]
    runtimes = [v for v in runtimes if v > 0]
    if not runtimes:
        return safe_float(eta_current_job_seconds, 0.0)
    return max(0.0, remaining_jobs * (sum(runtimes) / len(runtimes)))


def build_live_payload(
    progress_path,
    phase="idle",
    category="",
    video="",
    pipeline="",
    current_frame=0,
    total_frames=0,
    evaluated_frames=0,
    fps_current=0.0,
    fps_avg=0.0,
    latency_avg_ms=0.0,
    latency_p95_so_far_ms=0.0,
    cpu_process_percent=0.0,
    ram_process_mb=0.0,
    energy_per_frame=0.0,
    simulated_runtime_energy_per_frame=0.0,
    runtime_current_job_seconds=0.0,
    runtime_session_seconds=0.0,
    eta_current_job_seconds=0.0,
    eta_remaining_jobs_seconds=None,
    message="",
    fun_status_line="",
):
    progress = load_progress(progress_path)
    summary = summarize_progress(progress)
    total_frames = safe_int(total_frames)
    current_frame = safe_int(current_frame)
    job_percent = (current_frame / total_frames * 100.0) if total_frames else 0.0
    if eta_remaining_jobs_seconds is None:
        eta_remaining_jobs_seconds = estimate_remaining_jobs_seconds(progress, eta_current_job_seconds)
    fun_status_line = fun_status_line or random.choice(FUN_STATUS_LINES)
    payload = {
        "timestamp": now_iso(),
        "phase": phase,
        "total_jobs": summary["total"],
        "completed_jobs": summary["completed"],
        "pending_jobs": summary["pending"],
        "running_jobs": summary["running"],
        "failed_jobs": summary["failed"],
        "overall_job_percent": round(summary["overall_percent"], 4),
        "total_videos": summary["total_video_count"],
        "completed_videos": summary["completed_video_count"],
        "current_job_index": summary["current_job_index"],
        "completed_video_count": summary["completed_video_count"],
        "total_video_count": summary["total_video_count"],
        "completed_pipelines_for_current_video": summary["current_video_completed_pipelines"],
        "total_pipelines_for_current_video": summary["current_video_total_pipelines"],
        "current_video_completed_pipelines": summary["current_video_completed_pipelines"],
        "current_video_total_pipelines": summary["current_video_total_pipelines"],
        "current_category": category,
        "current_video": video,
        "current_pipeline": pipeline,
        "current_frame": current_frame,
        "total_frames": total_frames,
        "job_frame_percent": round(job_percent, 4),
        "evaluated_frames": safe_int(evaluated_frames),
        "fps_current": round(safe_float(fps_current), 4),
        "fps_avg": round(safe_float(fps_avg), 4),
        "latency_avg_ms": round(safe_float(latency_avg_ms), 4),
        "latency_p95_so_far_ms": round(safe_float(latency_p95_so_far_ms), 4),
        "cpu_process_percent": round(safe_float(cpu_process_percent), 4),
        "ram_process_mb": round(safe_float(ram_process_mb), 4),
        "energy_per_frame": round(safe_float(energy_per_frame), 4),
        "simulated_runtime_energy_per_frame": round(safe_float(simulated_runtime_energy_per_frame), 4),
        "runtime_current_job_seconds": round(safe_float(runtime_current_job_seconds), 4),
        "runtime_session_seconds": round(safe_float(runtime_session_seconds), 4),
        "eta_current_job_seconds": round(safe_float(eta_current_job_seconds), 4),
        "eta_remaining_jobs_seconds": round(safe_float(eta_remaining_jobs_seconds), 4),
        "last_completed_job": format_job(summary["last_completed"]),
        "next_pending_job": format_job(summary["next_pending"]),
        "fun_status_line": fun_status_line,
        "live_file": str(Path(progress_path).parent / "live_progress.md"),
        "message": message,
    }
    return {field: payload.get(field, "") for field in LIVE_PROGRESS_FIELDS}


def progress_bar(percent, width=20):
    pct = max(0.0, min(100.0, safe_float(percent)))
    filled = int(round(width * pct / 100.0))
    return "[" + ("█" * filled) + ("░" * (width - filled)) + f"] {pct:.2f}%"


def format_job(row):
    if not row:
        return "-"
    return f"{row.get('category', '-')}/{row.get('video', '-')}/{row.get('pipeline', '-')}"


def live_progress_paths(out_root):
    out_root = Path(out_root)
    return out_root / "live_progress.json", out_root / "live_progress.md"


def write_live_progress(out_root, payload):
    json_path, md_path = live_progress_paths(out_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_live_markdown(payload), encoding="utf-8")


def render_live_markdown(payload):
    return "\n".join(
        [
            "# G2G3 Live Progress",
            "",
            "## Overall",
            f"- Jobs completed: {payload.get('completed_jobs', 0)} / {payload.get('total_jobs', 0)}",
            f"- Overall percent: {safe_float(payload.get('overall_job_percent')):.2f}%",
            f"- Videos completed: {payload.get('completed_videos', payload.get('completed_video_count', 0))} / {payload.get('total_videos', payload.get('total_video_count', 0))}",
            f"- Current job index: {payload.get('current_job_index', 0)} / {payload.get('total_jobs', 0)}",
            f"- Pending: {payload.get('pending_jobs', 0)}",
            f"- Running: {payload.get('running_jobs', 0)}",
            f"- Failed: {payload.get('failed_jobs', 0)}",
            "",
            "## Current",
            f"- Category: {payload.get('current_category') or '-'}",
            f"- Video: {payload.get('current_video') or '-'}",
            f"- Pipeline: {payload.get('current_pipeline') or '-'}",
            f"- Video pipeline progress: {payload.get('completed_pipelines_for_current_video', payload.get('current_video_completed_pipelines', 0))} / {payload.get('total_pipelines_for_current_video', payload.get('current_video_total_pipelines', 6))}",
            f"- Frame progress: {payload.get('current_frame', 0)} / {payload.get('total_frames', 0)}",
            f"- Job progress: {safe_float(payload.get('job_frame_percent')):.2f}%",
            f"- Job bar: {progress_bar(payload.get('job_frame_percent', 0))}",
            f"- Overall bar: {progress_bar(payload.get('overall_job_percent', 0))}",
            "",
            "## Runtime",
            f"- FPS current: {safe_float(payload.get('fps_current')):.2f}",
            f"- FPS average: {safe_float(payload.get('fps_avg')):.2f}",
            f"- Avg latency: {safe_float(payload.get('latency_avg_ms')):.2f} ms",
            f"- P95 latency: {safe_float(payload.get('latency_p95_so_far_ms')):.2f} ms",
            f"- CPU process: {safe_float(payload.get('cpu_process_percent')):.2f} %",
            f"- RAM process: {safe_float(payload.get('ram_process_mb')):.2f} MB",
            f"- Energy/frame: {safe_float(payload.get('energy_per_frame')):.4f}",
            f"- Simulated energy/frame: {safe_float(payload.get('simulated_runtime_energy_per_frame')):.4f}",
            f"- Runtime current job: {format_duration(payload.get('runtime_current_job_seconds', 0))}",
            f"- Runtime session: {format_duration(payload.get('runtime_session_seconds', 0))}",
            f"- ETA current job: {format_duration(payload.get('eta_current_job_seconds', 0))}",
            f"- ETA remaining: {format_duration(payload.get('eta_remaining_jobs_seconds', 0))}",
            "",
            "## Last / Next",
            f"- Last completed job: {payload.get('last_completed_job') or '-'}",
            f"- Next pending job: {payload.get('next_pending_job') or '-'}",
            f"- Fun status: {payload.get('fun_status_line') or '-'}",
            f"- Last update: {payload.get('timestamp', '')}",
            f"- Message: {payload.get('message', '') or '-'}",
            "",
        ]
    )


def print_progress_block(payload):
    print("=" * 60)
    print("📡 [G2G3 LIVE STATUS]")
    print(
        "🗂 Overall jobs     : "
        f"completed {payload.get('completed_jobs', 0)} / {payload.get('total_jobs', 0)} | "
        f"pending {payload.get('pending_jobs', 0)} | failed {payload.get('failed_jobs', 0)}"
    )
    print(
        "📼 Videos done      : "
        f"{payload.get('completed_videos', payload.get('completed_video_count', 0))} / "
        f"{payload.get('total_videos', payload.get('total_video_count', 0))}"
    )
    print(f"🧮 Current job index: {payload.get('current_job_index', 0)} / {payload.get('total_jobs', 0)}")
    print(
        "🎬 Current video    : "
        f"{payload.get('current_category') or '-'} / {payload.get('current_video') or '-'}"
    )
    print(f"🧪 Current pipeline : {payload.get('current_pipeline') or '-'}")
    print(
        "🧩 Video progress   : "
        f"{payload.get('completed_pipelines_for_current_video', payload.get('current_video_completed_pipelines', 0))} / "
        f"{payload.get('total_pipelines_for_current_video', payload.get('current_video_total_pipelines', 6))} pipelines"
    )
    print(
        "🖼 Frame progress   : "
        f"{payload.get('current_frame', 0)} / {payload.get('total_frames', 0)}"
    )
    print(f"📊 Job progress     : {safe_float(payload.get('job_frame_percent')):.2f}%")
    print("")
    print("Progress bar job:")
    print(progress_bar(payload.get("job_frame_percent", 0)))
    print("")
    print("Progress bar overall:")
    print(progress_bar(payload.get("overall_job_percent", 0)))
    print("")
    print(f"⚡ FPS current      : {safe_float(payload.get('fps_current')):.2f}")
    print(f"⚡ FPS average      : {safe_float(payload.get('fps_avg')):.2f}")
    print(f"⏱ Avg latency      : {safe_float(payload.get('latency_avg_ms')):.2f} ms")
    print(f"⏱ P95 latency      : {safe_float(payload.get('latency_p95_so_far_ms')):.2f} ms")
    print(f"🧠 CPU process      : {safe_float(payload.get('cpu_process_percent')):.2f} %")
    print(f"💾 RAM process      : {safe_float(payload.get('ram_process_mb')):.2f} MB")
    print(f"🔋 Energy/frame     : {safe_float(payload.get('energy_per_frame')):.4f}")
    print(f"🔋 Sim energy/frame : {safe_float(payload.get('simulated_runtime_energy_per_frame')):.4f}")
    print("")
    print(f"⌛ Runtime job      : {format_duration(payload.get('runtime_current_job_seconds', 0))}")
    print(f"⌛ Runtime session  : {format_duration(payload.get('runtime_session_seconds', 0))}")
    print(f"🕒 ETA current job  : {format_duration(payload.get('eta_current_job_seconds', 0))}")
    print(f"🕒 ETA all remain   : {format_duration(payload.get('eta_remaining_jobs_seconds', 0))}")
    print("")
    print(f"✅ Last completed   : {payload.get('last_completed_job') or '-'}")
    print(f"➡️ Next pending     : {payload.get('next_pending_job') or '-'}")
    print("")
    print(f"😄 Fun status line  : {payload.get('fun_status_line') or '-'}")
    print("=" * 60)


class ProgressMonitor:
    def __init__(self, out_root, progress_path, cfg, session_started_at=None):
        self.out_root = Path(out_root)
        self.progress_path = Path(progress_path)
        progress_cfg = cfg.get("progress", {})
        self.print_every_frames = max(1, int(progress_cfg.get("print_progress_every_frames", 25)))
        self.write_every_frames = max(1, int(progress_cfg.get("write_progress_every_frames", 25)))
        self.heartbeat_seconds = max(1, int(progress_cfg.get("progress_heartbeat_seconds", 30)))
        self.show_eta = bool(progress_cfg.get("show_eta", True))
        self.session_started_at = session_started_at or time.time()
        self.last_print_time = 0.0
        self.last_write_time = 0.0

    def should_update(self, evaluated_frames, force=False):
        now = time.time()
        if force:
            return True
        if evaluated_frames <= 1:
            return True
        if evaluated_frames % min(self.print_every_frames, self.write_every_frames) == 0:
            return True
        return (now - self.last_print_time) >= self.heartbeat_seconds

    def update(
        self,
        category,
        video,
        pipeline,
        current_frame,
        total_frames,
        evaluated_frames,
        fps_current,
        fps_avg,
        latency_avg_ms,
        latency_p95_so_far_ms,
        runtime_current_job_seconds,
        cpu_process_percent=0.0,
        ram_process_mb=0.0,
        energy_per_frame=0.0,
        simulated_runtime_energy_per_frame=0.0,
        message="running",
        force=False,
        print_block=True,
    ):
        if not self.should_update(evaluated_frames, force=force):
            return None
        elapsed_session = time.time() - self.session_started_at
        current_frame = safe_int(current_frame)
        total_frames = safe_int(total_frames)
        remaining_frames = max(0, total_frames - current_frame)
        eta_job = remaining_frames / max(1e-9, safe_float(fps_avg)) if self.show_eta and fps_avg else 0.0
        payload = build_live_payload(
            self.progress_path,
            phase="running",
            category=category,
            video=video,
            pipeline=pipeline,
            current_frame=current_frame,
            total_frames=total_frames,
            evaluated_frames=evaluated_frames,
            fps_current=fps_current,
            fps_avg=fps_avg,
            latency_avg_ms=latency_avg_ms,
            latency_p95_so_far_ms=latency_p95_so_far_ms,
            cpu_process_percent=cpu_process_percent,
            ram_process_mb=ram_process_mb,
            energy_per_frame=energy_per_frame,
            simulated_runtime_energy_per_frame=simulated_runtime_energy_per_frame,
            runtime_current_job_seconds=runtime_current_job_seconds,
            runtime_session_seconds=elapsed_session,
            eta_current_job_seconds=eta_job,
            message=message,
        )
        write_live_progress(self.out_root, payload)
        self.last_write_time = time.time()
        if print_block:
            print_progress_block(payload)
            self.last_print_time = time.time()
        return payload


def write_idle_live_progress(out_root, progress_path, message="idle"):
    progress = load_progress(progress_path)
    summary = summarize_progress(progress)
    current = summary.get("current_job") or ""
    category = video = pipeline = ""
    if current:
        parts = current.split("/", 2)
        if len(parts) == 3:
            category, video, pipeline = parts
    elif summary.get("next_pending"):
        row = summary["next_pending"]
        category = str(row.get("category", "") or "")
        video = str(row.get("video", "") or "")
        pipeline = str(row.get("pipeline", "") or "")
    elif summary.get("last_completed"):
        row = summary["last_completed"]
        category = str(row.get("category", "") or "")
        video = str(row.get("video", "") or "")
        pipeline = str(row.get("pipeline", "") or "")
    payload = build_live_payload(
        progress_path,
        phase="idle",
        category=category,
        video=video,
        pipeline=pipeline,
        message=message,
    )
    write_live_progress(out_root, payload)
    return payload


def print_progress_only_report(progress_path, recommended_resume_command):
    progress = load_progress(progress_path)
    summary = summarize_progress(progress)
    print("[G2G3 PROGRESS ONLY]")
    print(f"total jobs: {summary['total']}")
    print(
        f"completed={summary['completed']} | pending={summary['pending']} | "
        f"running={summary['running']} | failed={summary['failed']}"
    )
    print(f"overall percent: {summary['overall_percent']:.2f}%")
    print(f"completed videos: {summary['completed_video_count']} / {summary['total_video_count']}")
    if summary["current_job"]:
        print(f"current running job: {summary['current_job']}")
    else:
        print("current running job: -")
    if summary["next_pending"]:
        row = summary["next_pending"]
        print(f"next pending job: {row.get('category')}/{row.get('video')}/{row.get('pipeline')}")
    else:
        print("next pending job: -")
    if summary["last_completed"]:
        row = summary["last_completed"]
        print(
            "last completed job: "
            f"{row.get('category')}/{row.get('video')}/{row.get('pipeline')} "
            f"at {row.get('completed_at', '')}"
        )
    else:
        print("last completed job: -")
    if summary["failed_jobs"]:
        print("failed jobs:")
        for row in summary["failed_jobs"]:
            print(f" - {row.get('category')}/{row.get('video')}/{row.get('pipeline')}: {row.get('error_message', '')}")
    else:
        print("failed jobs: -")
    print(f"recommended resume command: {recommended_resume_command}")


def show_live_progress(out_root):
    json_path, md_path = live_progress_paths(out_root)
    if md_path.exists():
        print(md_path.read_text(encoding="utf-8"))
        return
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        print_progress_block(payload)
        return
    print(f"[LIVE PROGRESS] no live progress file found in {out_root}")
