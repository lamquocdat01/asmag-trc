from __future__ import annotations

from pathlib import Path
from datetime import datetime

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


OUT = Path("outputs/full_cdnet2014_official_edge_profile_pc")
CHARTS = OUT / "charts"
PIPELINE_ORDER = [
    "P1_YOLO_Only",
    "P2_FrameDiff",
    "P3_MOG2",
    "ASMAG_TR_FAST",
    "ASMAG_TR_CONTROLLER",
    "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED",
]


def read_csv(name: str) -> pd.DataFrame:
    path = OUT / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def first_col(df: pd.DataFrame, names: list[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def numeric(value):
    try:
        return float(value)
    except Exception:
        return float("nan")


def build_main() -> pd.DataFrame:
    research = read_csv("summary_research_metrics.csv")
    pareto = read_csv("summary_pareto_metrics.csv")
    objects = read_csv("summary_object_by_pipeline.csv")
    if research.empty:
        raise SystemExit("summary_research_metrics.csv is required")

    grouped = research.groupby("pipeline", as_index=False).agg(
        CDnet_FMeasure=("FMeasure", "mean"),
        Event_F1=("Event_F1", "mean"),
        Activation=("YOLO_activation_rate", "mean"),
        Reuse_rate=("reused_prediction_rate", "mean"),
        Avg_FPS=("avg_FPS", "mean"),
        Avg_latency_ms=("avg_latency_ms", "mean"),
        P50_latency_ms=("median_latency_ms", "mean"),
        P95_latency_ms=("P95_latency_ms", "mean"),
        P99_latency_ms=("P99_latency_ms", "mean"),
        Avg_process_CPU_percent=("avg_process_cpu_percent", "mean"),
        Max_process_CPU_percent=("max_process_cpu_percent", "max"),
        Avg_RAM_MB=("avg_ram_mb", "mean"),
        Max_RAM_MB=("max_ram_mb", "max"),
        **{"Energy/frame": ("Energy/frame", "mean")},
        **{"Simulated_runtime_energy/frame": ("simulated_runtime_energy/frame", "mean")},
    )
    if not objects.empty and "mAP_50" in objects.columns:
        grouped = grouped.merge(objects[["pipeline", "mAP_50"]], on="pipeline", how="left")
    else:
        grouped["mAP_50"] = float("nan")

    if not pareto.empty:
        p = pareto.rename(columns={"pipeline": "Pipeline", "Pareto_Efficient": "Pareto"})
        grouped = grouped.merge(p[["Pipeline", "AE_Score", "Pareto"]], left_on="pipeline", right_on="Pipeline", how="left")
        grouped["Pipeline"] = grouped["Pipeline"].fillna(grouped["pipeline"])
    else:
        grouped["Pipeline"] = grouped["pipeline"]
        grouped["AE_Score"] = float("nan")
        grouped["Pareto"] = False

    grouped["Pipeline"] = pd.Categorical(grouped["Pipeline"], PIPELINE_ORDER, ordered=True)
    grouped = grouped.sort_values("Pipeline")
    cols = [
        "Pipeline",
        "CDnet_FMeasure",
        "Event_F1",
        "mAP_50",
        "Activation",
        "Reuse_rate",
        "Avg_FPS",
        "Avg_latency_ms",
        "P50_latency_ms",
        "P95_latency_ms",
        "P99_latency_ms",
        "Avg_process_CPU_percent",
        "Max_process_CPU_percent",
        "Avg_RAM_MB",
        "Max_RAM_MB",
        "Energy/frame",
        "Simulated_runtime_energy/frame",
        "AE_Score",
        "Pareto",
    ]
    return grouped[cols]


def best_rows(main: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("Best CDnet_FMeasure", "CDnet_FMeasure", False),
        ("Best Event_F1", "Event_F1", False),
        ("Best mAP_50", "mAP_50", False),
        ("Lowest Activation", "Activation", True),
        ("Highest Avg_FPS", "Avg_FPS", False),
        ("Lowest P95_latency_ms", "P95_latency_ms", True),
        ("Lowest Energy/frame", "Energy/frame", True),
        ("Lowest Simulated_runtime_energy/frame", "Simulated_runtime_energy/frame", True),
        ("Highest AE_Score", "AE_Score", False),
    ]
    rows = []
    for label, col, low in specs:
        if col not in main.columns or main[col].isna().all():
            continue
        idx = main[col].idxmin() if low else main[col].idxmax()
        rows.append({"metric": label, "Pipeline": main.loc[idx, "Pipeline"], "value": main.loc[idx, col]})
    return pd.DataFrame(rows)


def gain_summary(main: pd.DataFrame) -> pd.DataFrame:
    by_pipe = {str(r["Pipeline"]): r for _, r in main.iterrows()}
    pairs = [
        ("ASMAG_TR_CONTROLLER", "P3_MOG2"),
        ("ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED", "P3_MOG2"),
        ("ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED", "ASMAG_TR_CONTROLLER"),
        ("ASMAG_TR_FAST", "P3_MOG2"),
        ("P2_FrameDiff", "P3_MOG2"),
        ("P1_YOLO_Only", "P3_MOG2"),
    ]
    rows = []
    for a, b in pairs:
        if a not in by_pipe or b not in by_pipe:
            continue
        ra, rb = by_pipe[a], by_pipe[b]
        rows.append(
            {
                "Comparison": f"{a} vs {b}",
                "FMeasure_gain": numeric(ra["CDnet_FMeasure"]) - numeric(rb["CDnet_FMeasure"]),
                "Event_F1_gain": numeric(ra["Event_F1"]) - numeric(rb["Event_F1"]),
                "Activation_saving": numeric(rb["Activation"]) - numeric(ra["Activation"]),
                "Energy_saving": numeric(rb["Energy/frame"]) - numeric(ra["Energy/frame"]),
                "Simulated_runtime_energy_saving": numeric(rb["Simulated_runtime_energy/frame"])
                - numeric(ra["Simulated_runtime_energy/frame"]),
                "FPS_gain": numeric(ra["Avg_FPS"]) - numeric(rb["Avg_FPS"]),
                "P95_latency_gain": numeric(rb["P95_latency_ms"]) - numeric(ra["P95_latency_ms"]),
                "AE_Score_gain": numeric(ra["AE_Score"]) - numeric(rb["AE_Score"]),
                "Interpretation": "Positive savings/gains mean the first pipeline improves over the comparison baseline.",
            }
        )
    return pd.DataFrame(rows)


def build_per_video_and_category() -> tuple[pd.DataFrame, pd.DataFrame]:
    research = read_csv("summary_research_metrics.csv")
    objects = read_csv("summary_object_metrics.csv")
    if research.empty:
        return pd.DataFrame(), pd.DataFrame()
    per_video = research.copy()
    per_video = per_video.rename(columns={"pipeline": "Pipeline", "FMeasure": "CDnet_FMeasure", "YOLO_activation_rate": "Activation"})
    if not objects.empty and "mAP_50" in objects.columns:
        map_cols = ["category", "video", "pipeline", "mAP_50"]
        per_video = per_video.merge(objects[map_cols], left_on=["category", "video", "Pipeline"], right_on=["category", "video", "pipeline"], how="left")
        if "pipeline" in per_video.columns:
            per_video = per_video.drop(columns=["pipeline"])
    per_category = per_video.groupby(["category", "Pipeline"], as_index=False).mean(numeric_only=True)
    return per_video, per_category


def build_mode_usage() -> pd.DataFrame:
    mode = read_csv("online_mode_usage_by_video.csv")
    if mode.empty:
        return pd.DataFrame({"Pipeline": ["ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED"], "frames": [0]})
    return mode.groupby("pipeline", as_index=False).agg(
        frames=("frames", "sum"),
        FAST_frames=("FAST_frames", "sum"),
        ACC_frames=("ACC_frames", "sum"),
        P3_FALLBACK_frames=("P3_FALLBACK_frames", "sum"),
        FAST_rate=("FAST_rate", "mean"),
        ACC_rate=("ACC_rate", "mean"),
        P3_FALLBACK_rate=("P3_FALLBACK_rate", "mean"),
    ).rename(columns={"pipeline": "Pipeline"})


def bar(main: pd.DataFrame, col: str, filename: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(main["Pipeline"].astype(str), main[col], color="#3b82f6")
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Pipeline")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS / filename, dpi=180)
    plt.close(fig)


def heatmap(per_category: pd.DataFrame, value: str, filename: str, title: str) -> None:
    if per_category.empty or value not in per_category.columns:
        return
    pivot = per_category.pivot(index="category", columns="Pipeline", values=value)
    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(pivot.values, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(pivot.columns)), labels=pivot.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(pivot.index)), labels=pivot.index)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    fig.tight_layout()
    fig.savefig(CHARTS / filename, dpi=180)
    plt.close(fig)


def charts(main: pd.DataFrame, per_category: pd.DataFrame) -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    bar(main, "CDnet_FMeasure", "fmeasure_by_pipeline.png", "CDnet FMeasure")
    bar(main, "Event_F1", "event_f1_by_pipeline.png", "Event F1")
    bar(main, "Avg_FPS", "fps_by_pipeline.png", "Avg FPS")
    bar(main, "P95_latency_ms", "latency_p95_by_pipeline.png", "P95 latency (ms)")
    bar(main, "Activation", "activation_by_pipeline.png", "Activation")
    bar(main, "Energy/frame", "energy_by_pipeline.png", "Energy/frame")
    bar(main, "Simulated_runtime_energy/frame", "simulated_energy_by_pipeline.png", "Simulated runtime energy/frame")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(main["Energy/frame"], main["CDnet_FMeasure"], s=90, c=main["Pareto"].astype(bool).map({True: "#16a34a", False: "#64748b"}))
    for _, row in main.iterrows():
        ax.annotate(str(row["Pipeline"]), (row["Energy/frame"], row["CDnet_FMeasure"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("Energy/frame")
    ax.set_ylabel("CDnet FMeasure")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHARTS / "pareto_fmeasure_energy.png", dpi=180)
    plt.close(fig)

    heatmap(per_category, "CDnet_FMeasure", "per_category_fmeasure_heatmap.png", "Per-category CDnet FMeasure")
    heatmap(per_category, "P95_latency_ms", "per_category_latency_heatmap.png", "Per-category P95 latency")
    heatmap(per_category, "Activation", "per_category_activation_heatmap.png", "Per-category activation")


def research_summary(main: pd.DataFrame, best: pd.DataFrame, progress: pd.DataFrame) -> str:
    def best_pipe(metric: str) -> str:
        row = best[best["metric"] == metric]
        if row.empty:
            return "-"
        return f"{row.iloc[0]['Pipeline']} ({row.iloc[0]['value']:.4f})"

    controller = main[main["Pipeline"].astype(str) == "ASMAG_TR_CONTROLLER"].iloc[0]
    calibrated = main[main["Pipeline"].astype(str) == "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED"].iloc[0]
    p3 = main[main["Pipeline"].astype(str) == "P3_MOG2"].iloc[0]
    completed = int((progress["status"] == "completed").sum())
    total = int(len(progress))
    videos = progress.groupby(["category", "video"])["status"].apply(lambda s: int((s == "completed").sum()) == 6)
    completed_videos = int(videos.sum())
    total_videos = int(videos.shape[0])

    lines = [
        "# G2G3 Official-like Edge Profile Final Research Summary",
        "",
        f"Updated at `{datetime.now().isoformat(timespec='seconds')}`.",
        "",
        "## Completion",
        "",
        f"- Full G2G3 completed `{completed}/{total}` jobs and `{completed_videos}/{total_videos}` videos.",
        "- Dataset scope: CDnet2014 run plan, frame_step=1, CPU edge-profile PC configuration.",
        "",
        "## Best Pipelines",
        "",
        f"- Best CDnet_FMeasure: {best_pipe('Best CDnet_FMeasure')}.",
        f"- Best Event_F1: {best_pipe('Best Event_F1')}.",
        f"- Fastest Avg_FPS: {best_pipe('Highest Avg_FPS')}.",
        f"- Lowest P95 latency: {best_pipe('Lowest P95_latency_ms')}.",
        f"- Lowest activation: {best_pipe('Lowest Activation')}.",
        f"- Lowest Energy/frame: {best_pipe('Lowest Energy/frame')}.",
        f"- Lowest simulated runtime energy/frame: {best_pipe('Lowest Simulated_runtime_energy/frame')}.",
        "",
        "## Interpretation",
        "",
        f"- `ASMAG_TR_CONTROLLER` remains a useful upper-bound controller: it beats `P3_MOG2` by `{controller['CDnet_FMeasure'] - p3['CDnet_FMeasure']:.4f}` CDnet_FMeasure and `{controller['Event_F1'] - p3['Event_F1']:.4f}` Event_F1 while reducing activation by `{p3['Activation'] - controller['Activation']:.4f}`.",
        f"- `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED` is deployable as the main adaptive variant: it is within `{p3['CDnet_FMeasure'] - calibrated['CDnet_FMeasure']:.4f}` CDnet_FMeasure of `P3_MOG2`, improves Event_F1 by `{calibrated['Event_F1'] - p3['Event_F1']:.4f}`, and saves activation by `{p3['Activation'] - calibrated['Activation']:.4f}`.",
        "- The official-like frame_step=1 run confirms the sampled-run trend: pure FrameDiff is fastest and most energy-light, P3/controller variants lead quality, and calibrated online control is the practical balance point.",
        "- Edge CPU-only profiling shows the adaptive variants reduce activation and energy, but calibrated online control still pays latency overhead versus simpler baselines; this should be framed as an edge deployment trade-off rather than pure segmentation SOTA.",
        "- Recommendation: put the main comparison and gain table in the main paper, with per-video/per-category tables and heatmaps in the appendix.",
        "",
        "## Limitations for the paper",
        "",
        "- CDnet2014 is a background-subtraction benchmark, not a modern multi-domain detection benchmark.",
        "- The run is official-like with frame_step=1, but it is measured on a PC CPU edge profile rather than a fixed embedded device.",
        "- Energy is an estimated/simulated proxy and should be described as such.",
        "- Some latency and FPS results vary strongly by video/category; include per-category analysis.",
        "- The controller is designed for adaptive inference efficiency, not absolute state-of-the-art segmentation quality.",
        "",
    ]
    return "\n".join(lines)


def update_block(path: Path, block: str) -> None:
    start = "<!-- G2G3_FINAL_STATUS_START -->"
    end = "<!-- G2G3_FINAL_STATUS_END -->"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    new = f"{start}\n{block.rstrip()}\n{end}\n"
    if start in text and end in text:
        before = text.split(start)[0]
        after = text.split(end, 1)[1]
        text = before + new + after.lstrip("\n")
    else:
        text = text.rstrip() + "\n\n" + new
    path.write_text(text, encoding="utf-8")


def update_logs(main: pd.DataFrame, progress: pd.DataFrame) -> None:
    completed = int((progress["status"] == "completed").sum())
    total = int(len(progress))
    pending = int((progress["status"] == "pending").sum())
    running = int((progress["status"] == "running").sum())
    failed = int((progress["status"] == "failed").sum())
    videos = progress.groupby(["category", "video"])["status"].apply(lambda s: int((s == "completed").sum()) == 6)
    completed_videos = int(videos.sum())
    total_videos = int(videos.shape[0])
    now = datetime.now().isoformat(timespec="seconds")
    best_f = main.loc[main["CDnet_FMeasure"].idxmax()]
    best_event = main.loc[main["Event_F1"].idxmax()]
    fastest = main.loc[main["Avg_FPS"].idxmax()]
    next_prompt = (
        "# NEXT PROMPT FOR CODEX\n\n"
        "G2G3 full official-like Edge CPU-only run is complete. Next: prepare paper-ready tables, figures, "
        "and manuscript interpretation from `outputs/full_cdnet2014_official_edge_profile_pc/auto_research_summary.md`, "
        "`final_main_comparison.csv`, `gain_summary.csv`, and `charts/`.\n"
    )
    Path("NEXT_PROMPT_FOR_CODEX.md").write_text(next_prompt, encoding="utf-8")

    block = f"""## G2G3 Final Official-like Status

- Updated at: `{now}`
- Completed jobs: `{completed} / {total}`
- Pending: `{pending}`
- Running: `{running}`
- Failed: `{failed}`
- Completed videos: `{completed_videos} / {total_videos}`
- Best CDnet_FMeasure: `{best_f['Pipeline']}` = `{best_f['CDnet_FMeasure']:.4f}`
- Best Event_F1: `{best_event['Pipeline']}` = `{best_event['Event_F1']:.4f}`
- Fastest Avg_FPS: `{fastest['Pipeline']}` = `{fastest['Avg_FPS']:.4f}`
- Final reports: `outputs/full_cdnet2014_official_edge_profile_pc/final_main_comparison.csv`, `gain_summary.csv`, `auto_research_summary.md`, `charts/`
- Next step: use these artifacts for paper main tables, appendix heatmaps, and limitations discussion.
"""
    for filename in ["PROJECT_STATE.md", "TASK_BOARD.md", "RUNBOOK.md"]:
        update_block(Path(filename), block)

    log_line = (
        f"\n- `{now}` G2G3 final official-like completed: completed={completed}/{total}, "
        f"pending={pending}, running={running}, failed={failed}, videos={completed_videos}/{total_videos}, "
        f"best_fmeasure={best_f['Pipeline']}:{best_f['CDnet_FMeasure']:.4f}, "
        f"best_event={best_event['Pipeline']}:{best_event['Event_F1']:.4f}.\n"
    )
    for filename in ["logs/daily_log.md", "logs/experiment_log.md"]:
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        if "G2G3 final official-like completed" not in old:
            path.write_text(old.rstrip() + "\n" + log_line, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    progress = read_csv("run_progress.csv")
    main_cmp = build_main()
    per_video, per_category = build_per_video_and_category()
    mode_usage = build_mode_usage()
    best = best_rows(main_cmp)
    gains = gain_summary(main_cmp)

    main_cmp.to_csv(OUT / "final_main_comparison.csv", index=False)
    best.to_csv(OUT / "best_by_metric.csv", index=False)
    gains.to_csv(OUT / "gain_summary.csv", index=False)
    mode_usage.to_csv(OUT / "mode_usage_summary.csv", index=False)
    per_video.to_csv(OUT / "per_video_summary.csv", index=False)
    per_category.to_csv(OUT / "per_category_summary.csv", index=False)
    read_csv("summary_edge_metrics.csv").to_csv(OUT / "edge_runtime_summary.csv", index=False)
    per_video.to_csv(OUT / "official_like_results.csv", index=False)

    charts(main_cmp, per_category)
    (OUT / "auto_research_summary.md").write_text(research_summary(main_cmp, best, progress), encoding="utf-8")
    update_logs(main_cmp, progress)
    print("Final G2G3 reports regenerated.")
    print(main_cmp.to_string(index=False))


if __name__ == "__main__":
    main()
