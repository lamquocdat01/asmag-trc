from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_BASELINE = "P3_MOG2"
METRICS = [
    "precision",
    "recall",
    "fmeasure",
    "event_f1",
    "activation_rate",
    "reuse_rate",
    "avg_fps",
    "mean_latency_ms",
    "p95_latency_ms",
    "estimated_energy_per_frame",
]


def write_cross_dataset_stats(output_dir: str | Path, baseline: str = DEFAULT_BASELINE) -> Path:
    output_dir = Path(output_dir)
    per_video_path = output_dir / "per_video_summary.csv"
    if not per_video_path.exists():
        raise FileNotFoundError(per_video_path)
    per_video = pd.read_csv(per_video_path)
    rows = []
    for metric in [m for m in METRICS if m in per_video.columns]:
        wide = per_video.pivot_table(index=["category", "video"], columns="pipeline", values=metric, aggfunc="mean")
        if baseline not in wide.columns:
            continue
        for pipeline in wide.columns:
            values = pd.to_numeric(wide[pipeline], errors="coerce")
            base = pd.to_numeric(wide[baseline], errors="coerce")
            paired = pd.DataFrame({"pipeline": values, "baseline": base}).dropna()
            if paired.empty:
                continue
            delta = paired["pipeline"] - paired["baseline"]
            rows.append(
                {
                    "metric": metric,
                    "pipeline": pipeline,
                    "baseline": baseline,
                    "n_paired_videos": int(len(paired)),
                    "mean": float(paired["pipeline"].mean()),
                    "baseline_mean": float(paired["baseline"].mean()),
                    "mean_delta_vs_baseline": float(delta.mean()),
                    "median_delta_vs_baseline": float(delta.median()),
                    "std_delta_vs_baseline": float(delta.std(ddof=0)),
                    "win_rate_vs_baseline": float((delta > 0).mean()),
                    "loss_rate_vs_baseline": float((delta < 0).mean()),
                    "bootstrap_ci95_low": _bootstrap_mean_ci(delta.values, 0.025),
                    "bootstrap_ci95_high": _bootstrap_mean_ci(delta.values, 0.975),
                }
            )
    out = pd.DataFrame(rows)
    path = output_dir / "stat_summary.csv"
    out.to_csv(path, index=False)
    return path


def _bootstrap_mean_ci(values, quantile: float, rounds: int = 1000) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return 0.0
    rng = np.random.default_rng(20260508)
    means = []
    for _ in range(rounds):
        sample = rng.choice(values, size=len(values), replace=True)
        means.append(float(np.mean(sample)))
    return float(np.quantile(means, quantile))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    args = parser.parse_args()
    print(write_cross_dataset_stats(args.output_dir, args.baseline))


if __name__ == "__main__":
    main()
