from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "outputs" / "full_cdnet2014_official_edge_profile_pc"
OUT_DIR = ROOT / "outputs" / "paper_ready_figures"


PIPELINE_LABELS = {
    "P1_YOLO_Only": "P1\nYOLO",
    "P2_FrameDiff": "P2\nFrameDiff",
    "P3_MOG2": "P3\nMOG2",
    "ASMAG_TR_FAST": "ASMAG\nFAST",
    "ASMAG_TR_CONTROLLER": "ASMAG\nController",
    "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED": "ASMAG\nOnline",
}


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.dpi": 150,
            "savefig.dpi": 320,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.24,
            "grid.linewidth": 0.6,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"{name}.{ext}", bbox_inches="tight", dpi=320)
    plt.close(fig)


def readable_pipeline(series: pd.Series) -> list[str]:
    return [PIPELINE_LABELS.get(v, "\n".join(textwrap.wrap(str(v), 12))) for v in series]


def bar_chart(df: pd.DataFrame, metric: str, title: str, ylabel: str, name: str) -> None:
    data = df.copy()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    colors = ["#5B8DEF", "#56B870", "#F5A623", "#D96C75", "#7B61FF", "#38A6A5"]
    bars = ax.bar(readable_pipeline(data["Pipeline"]), data[metric], color=colors[: len(data)])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.grid(axis="x", visible=False)
    top = data[metric].max()
    bottom = data[metric].min()
    pad = (top - bottom) * 0.18 if top != bottom else top * 0.12
    ax.set_ylim(max(0, bottom - pad), top + pad)
    for bar, value in zip(bars, data[metric]):
        fmt = "{:.2f}" if abs(value) >= 1 else "{:.3f}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            fmt.format(value),
            ha="center",
            va="bottom",
            fontsize=8,
        )
    fig.tight_layout()
    save(fig, name)


def pareto(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    sizes = 90 + (1.0 - df["Activation"]) * 520
    colors = np.where(df["Pareto"].astype(str).str.lower() == "true", "#2AA876", "#9AA0A6")
    ax.scatter(df["Energy/frame"], df["CDnet_FMeasure"], s=sizes, c=colors, alpha=0.85, edgecolor="white", linewidth=0.9)
    for _, row in df.iterrows():
        ax.annotate(
            PIPELINE_LABELS.get(row["Pipeline"], row["Pipeline"]).replace("\n", " "),
            (row["Energy/frame"], row["CDnet_FMeasure"]),
            textcoords="offset points",
            xytext=(6, 5),
            fontsize=8,
        )
    ax.set_title("Accuracy-Energy Pareto Trade-off")
    ax.set_xlabel("Energy/frame proxy (lower is better)")
    ax.set_ylabel("CDnet FMeasure (higher is better)")
    ax.grid(True, alpha=0.24)
    fig.tight_layout()
    save(fig, "pareto_fmeasure_energy")


def heatmap(df: pd.DataFrame, value_col: str, title: str, name: str, fmt: str = ".3f") -> None:
    pivot = df.pivot_table(index="category", columns="Pipeline", values=value_col, aggfunc="mean")
    ordered_cols = [p for p in PIPELINE_LABELS if p in pivot.columns]
    pivot = pivot[ordered_cols]
    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    im = ax.imshow(pivot.values, aspect="auto", cmap="viridis")
    ax.set_title(title)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([PIPELINE_LABELS.get(c, c).replace("\n", " ") for c in pivot.columns], rotation=35, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.grid(False)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = pivot.values[i, j]
            if pd.isna(value):
                label = ""
            else:
                label = format(value, fmt)
            ax.text(j, i, label, ha="center", va="center", color="white", fontsize=7)
    cbar = fig.colorbar(im, ax=ax, fraction=0.026, pad=0.02)
    cbar.ax.tick_params(labelsize=8)
    fig.tight_layout()
    save(fig, name)


def main() -> None:
    style()
    main_df = pd.read_csv(RESULT_DIR / "final_main_comparison.csv")
    cat_df = pd.read_csv(RESULT_DIR / "per_category_summary.csv")
    ordered = [p for p in PIPELINE_LABELS if p in set(main_df["Pipeline"])]
    main_df = main_df.set_index("Pipeline").loc[ordered].reset_index()

    bar_chart(main_df, "CDnet_FMeasure", "CDnet FMeasure Across Pipelines", "CDnet FMeasure", "fmeasure_by_pipeline")
    bar_chart(main_df, "Event_F1", "Event F1 Across Pipelines", "Event F1", "event_f1_by_pipeline")
    bar_chart(main_df, "Activation", "Detector Activation Rate Across Pipelines", "Activation rate", "activation_by_pipeline")
    bar_chart(main_df, "P95_latency_ms", "P95 Latency Across Pipelines", "P95 latency (ms)", "latency_p95_by_pipeline")
    bar_chart(main_df, "Avg_FPS", "Average FPS Across Pipelines", "FPS", "fps_by_pipeline")
    bar_chart(main_df, "Energy/frame", "Energy Proxy Across Pipelines", "Energy/frame proxy", "energy_by_pipeline")
    bar_chart(
        main_df,
        "Simulated_runtime_energy/frame",
        "Runtime-Aware Simulated Energy Across Pipelines",
        "Simulated energy/frame",
        "simulated_energy_by_pipeline",
    )
    pareto(main_df)
    heatmap(cat_df, "CDnet_FMeasure", "Per-Category CDnet FMeasure", "per_category_fmeasure_heatmap")
    heatmap(cat_df, "Activation", "Per-Category Activation Rate", "per_category_activation_heatmap")
    heatmap(cat_df, "P95_latency_ms", "Per-Category P95 Latency", "per_category_latency_heatmap", ".1f")


if __name__ == "__main__":
    main()
