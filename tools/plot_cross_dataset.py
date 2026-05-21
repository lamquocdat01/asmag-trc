from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def create_cross_dataset_charts(output_dir: str | Path) -> Path:
    output_dir = Path(output_dir)
    charts = output_dir / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / "final_summary.csv"
    per_video_path = output_dir / "per_video_summary.csv"
    if not final_path.exists():
        return charts

    final = pd.read_csv(final_path)
    if final.empty:
        return charts

    for filename, metric, label in [
        ("fmeasure_by_pipeline.png", "fmeasure", "F-measure"),
        ("precision_by_pipeline.png", "precision", "Precision"),
        ("recall_by_pipeline.png", "recall", "Recall"),
        ("event_f1_by_pipeline.png", "event_f1", "Event F1"),
        ("activation_by_pipeline.png", "activation_rate", "Activation rate"),
        ("reuse_by_pipeline.png", "reuse_rate", "Reuse rate"),
        ("fps_by_pipeline.png", "avg_fps", "Average FPS"),
        ("latency_p95_by_pipeline.png", "p95_latency_ms", "P95 latency (ms)"),
        ("energy_by_pipeline.png", "estimated_energy_per_frame", "Estimated energy/frame"),
    ]:
        if metric in final.columns:
            _bar(final, "pipeline", metric, label, charts / filename)

    if {"activation_rate", "fmeasure", "pipeline"}.issubset(final.columns):
        _scatter(final, "activation_rate", "fmeasure", "pipeline", "Activation rate", "F-measure", charts / "pareto_activation_fmeasure.png")
    if {"estimated_energy_per_frame", "fmeasure", "pipeline"}.issubset(final.columns):
        _scatter(
            final,
            "estimated_energy_per_frame",
            "fmeasure",
            "pipeline",
            "Estimated energy/frame",
            "F-measure",
            charts / "pareto_energy_fmeasure.png",
        )

    if per_video_path.exists():
        per_video = pd.read_csv(per_video_path)
        if {"category", "pipeline", "fmeasure"}.issubset(per_video.columns) and not per_video.empty:
            pivot = per_video.pivot_table(index="category", columns="pipeline", values="fmeasure", aggfunc="mean")
            _heatmap(pivot, "Category F-measure", charts / "category_fmeasure_heatmap.png")

    return charts


def _bar(df: pd.DataFrame, x: str, y: str, ylabel: str, out_path: Path) -> None:
    plt.figure(figsize=(10, 5))
    plt.bar(df[x].astype(str), pd.to_numeric(df[y], errors="coerce").fillna(0.0))
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def _scatter(df: pd.DataFrame, x: str, y: str, label_col: str, xlabel: str, ylabel: str, out_path: Path) -> None:
    plt.figure(figsize=(7, 5))
    xs = pd.to_numeric(df[x], errors="coerce").fillna(0.0)
    ys = pd.to_numeric(df[y], errors="coerce").fillna(0.0)
    plt.scatter(xs, ys, s=70)
    for idx, row in df.iterrows():
        plt.annotate(str(row[label_col]), (float(xs.loc[idx]), float(ys.loc[idx])), fontsize=8)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def _heatmap(pivot: pd.DataFrame, title: str, out_path: Path) -> None:
    plt.figure(figsize=(12, 6))
    plt.imshow(pivot.fillna(0.0).values.astype(float), aspect="auto", vmin=0.0, vmax=1.0)
    plt.colorbar(label="F-measure")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=25, ha="right")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    print(create_cross_dataset_charts(args.output_dir))


if __name__ == "__main__":
    main()
