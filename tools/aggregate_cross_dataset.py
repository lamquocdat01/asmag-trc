from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.binary_mask_metrics import aggregate_binary_mask_metrics, event_f1_from_rows


PIPELINE_ORDER = [
    "P1_YOLO_Only",
    "P2_FrameDiff",
    "P3_MOG2",
    "ASMAG_TR_FAST",
    "ASMAG_TR_ACC",
    "ASMAG_TR_CONTROLLER",
    "ASMAG_TR_CONTROLLER_ONLINE",
]


def aggregate_cross_dataset(
    output_dir: str | Path,
    dataset_name: Optional[str] = None,
    low_fmeasure_threshold: float = 0.25,
) -> dict:
    output_dir = Path(output_dir)
    dataset_name = dataset_name or output_dir.name.replace("_full", "")

    frame_log = build_per_frame_log(output_dir, dataset_name)
    frame_log.to_csv(output_dir / "per_frame_log.csv", index=False)

    per_video = build_per_video_summary(output_dir, dataset_name)
    per_video.to_csv(output_dir / "per_video_summary.csv", index=False)

    final = build_final_summary(per_video, dataset_name)
    final.to_csv(output_dir / "final_summary.csv", index=False)

    failures = build_failure_cases(output_dir, per_video, dataset_name, low_fmeasure_threshold)
    failures.to_csv(output_dir / "failure_cases.csv", index=False)

    return {
        "per_frame_log": output_dir / "per_frame_log.csv",
        "per_video_summary": output_dir / "per_video_summary.csv",
        "final_summary": output_dir / "final_summary.csv",
        "failure_cases": output_dir / "failure_cases.csv",
    }


def build_per_frame_log(output_dir: str | Path, dataset_name: str) -> pd.DataFrame:
    rows = []
    for path in _sequence_paths(output_dir, "frame_metrics.csv"):
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if df.empty:
            continue
        df = df.copy()
        df.insert(0, "dataset", dataset_name)
        for source, target in [
            ("Precision", "precision"),
            ("Recall", "recall"),
            ("FMeasure", "fmeasure"),
            ("PWC", "pwc"),
            ("latency_ms", "latency_ms"),
            ("FPS", "fps"),
            ("reused_prediction", "reused_prediction"),
            ("energy_frame", "estimated_energy_per_frame"),
            ("Event_State", "event_state"),
        ]:
            if source in df.columns and target not in df.columns:
                df[target] = df[source]
        if "activation_rate" not in df.columns:
            df["activation_rate"] = df["yolo_called"] if "yolo_called" in df.columns else df.get("activation", 0)
        keep = [
            "dataset",
            "category",
            "video",
            "pipeline",
            "frame_id",
            "raw_frame_id",
            "evaluated_index",
            "precision",
            "recall",
            "fmeasure",
            "pwc",
            "activation_rate",
            "reused_prediction",
            "latency_ms",
            "fps",
            "estimated_energy_per_frame",
            "event_state",
            "selected_mode",
            "gate_open",
            "TP_pixel",
            "TN_pixel",
            "FP_pixel",
            "FN_pixel",
        ]
        rows.append(df[[c for c in keep if c in df.columns]])
    if not rows:
        return pd.DataFrame(columns=["dataset", "category", "video", "pipeline", "frame_id"])
    out = pd.concat(rows, ignore_index=True)
    return _sort_by_pipeline(out)


def build_per_video_summary(output_dir: str | Path, dataset_name: str) -> pd.DataFrame:
    pixel = _read_sequence_summaries(output_dir, "sequence_pixel_summary.csv")
    event = _read_sequence_summaries(output_dir, "sequence_event_summary.csv")
    edge = _read_sequence_summaries(output_dir, "sequence_edge_summary.csv")
    objects = _read_sequence_summaries(output_dir, "sequence_object_summary.csv")
    keys = ["category", "video", "pipeline"]

    if pixel.empty:
        return pd.DataFrame(columns=["dataset", *keys])

    out = pixel.copy()
    if not event.empty:
        out = out.merge(event, on=keys, how="left", suffixes=("", "_event"))
    if not edge.empty:
        out = out.merge(edge, on=keys, how="left", suffixes=("", "_edge"))
    if not objects.empty:
        object_cols = [c for c in ["category", "video", "pipeline", "mAP_50", "mAP_50_95_proxy"] if c in objects.columns]
        out = out.merge(objects[object_cols], on=keys, how="left")

    out.insert(0, "dataset", dataset_name)
    out["precision"] = _col(out, "Precision")
    out["recall"] = _col(out, "Recall")
    out["fmeasure"] = _col(out, "FMeasure")
    out["event_f1"] = _col(out, "Event_F1")
    out["activation_rate"] = _col(out, "YOLO_activation_rate")
    out["reuse_rate"] = _col(out, "reused_prediction_rate")
    out["avg_fps"] = _col(out, "avg_FPS")
    out["mean_latency_ms"] = _col(out, "avg_latency_ms")
    out["p95_latency_ms"] = _col(out, "P95_latency_ms")
    out["estimated_energy_per_frame"] = _col(out, "Energy/frame", _col(out, "energy_frame"))
    out["processed_frames"] = _col(out, "processed_frames", _col(out, "evaluated_frames"))

    keep = [
        "dataset",
        "category",
        "video",
        "pipeline",
        "processed_frames",
        "TP_pixel",
        "TN_pixel",
        "FP_pixel",
        "FN_pixel",
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
        "mAP_50",
        "mAP_50_95_proxy",
        "Event_TP",
        "Event_TN",
        "Event_FP",
        "Event_FN",
    ]
    out = out[[c for c in keep if c in out.columns]]
    return _sort_by_pipeline(out)


def build_final_summary(per_video: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    if per_video.empty:
        return pd.DataFrame(columns=["dataset", "pipeline"])
    rows = []
    for pipeline, group in per_video.groupby("pipeline", sort=False):
        pixel_metrics = aggregate_binary_mask_metrics(group.to_dict("records"))
        event_metrics = event_f1_from_rows(group.to_dict("records"))
        weights = _weights(group)
        row = {
            "dataset": dataset_name,
            "pipeline": pipeline,
            "videos": int(group[["category", "video"]].drop_duplicates().shape[0]),
            "processed_frames": int(pd.to_numeric(group.get("processed_frames", 0), errors="coerce").fillna(0).sum()),
            "precision": pixel_metrics["precision"],
            "recall": pixel_metrics["recall"],
            "fmeasure": pixel_metrics["fmeasure"],
            "event_f1": event_metrics["event_f1"],
            "activation_rate": _weighted_mean(group, "activation_rate", weights),
            "reuse_rate": _weighted_mean(group, "reuse_rate", weights),
            "avg_fps": _weighted_mean(group, "avg_fps", weights),
            "mean_latency_ms": _weighted_mean(group, "mean_latency_ms", weights),
            "p95_latency_ms": _weighted_mean(group, "p95_latency_ms", weights),
            "estimated_energy_per_frame": _weighted_mean(group, "estimated_energy_per_frame", weights),
            "mAP_50": _weighted_mean(group, "mAP_50", weights),
            "mAP_50_95_proxy": _weighted_mean(group, "mAP_50_95_proxy", weights),
            **pixel_metrics,
            **event_metrics,
        }
        rows.append(row)
    out = pd.DataFrame(rows)
    return _sort_by_pipeline(out)


def build_failure_cases(
    output_dir: str | Path,
    per_video: pd.DataFrame,
    dataset_name: str,
    low_fmeasure_threshold: float,
) -> pd.DataFrame:
    rows = []
    progress_path = Path(output_dir) / "run_progress.csv"
    if progress_path.exists():
        progress = pd.read_csv(progress_path)
        failed = progress[progress["status"].astype(str) == "failed"] if "status" in progress.columns else pd.DataFrame()
        for _, row in failed.iterrows():
            rows.append(
                {
                    "dataset": dataset_name,
                    "category": row.get("category", ""),
                    "video": row.get("video", ""),
                    "pipeline": row.get("pipeline", ""),
                    "case_type": "job_failed",
                    "metric": "",
                    "value": "",
                    "reference_pipeline": "",
                    "reference_value": "",
                    "delta": "",
                    "notes": row.get("error_message", row.get("message", "")),
                }
            )

    if not per_video.empty and "fmeasure" in per_video.columns:
        low = per_video[pd.to_numeric(per_video["fmeasure"], errors="coerce").fillna(0) <= low_fmeasure_threshold]
        if low.empty:
            low = per_video.sort_values("fmeasure", ascending=True).head(min(20, len(per_video)))
        for _, row in low.iterrows():
            rows.append(
                {
                    "dataset": dataset_name,
                    "category": row.get("category", ""),
                    "video": row.get("video", ""),
                    "pipeline": row.get("pipeline", ""),
                    "case_type": "low_fmeasure",
                    "metric": "fmeasure",
                    "value": row.get("fmeasure", ""),
                    "reference_pipeline": "",
                    "reference_value": "",
                    "delta": "",
                    "notes": "lowest video-level binary mask F-measure cases",
                }
            )

        p3 = per_video[per_video["pipeline"] == "P3_MOG2"][["category", "video", "fmeasure"]].rename(
            columns={"fmeasure": "p3_fmeasure"}
        )
        for pipeline in ["ASMAG_TR_FAST", "ASMAG_TR_ACC", "ASMAG_TR_CONTROLLER", "ASMAG_TR_CONTROLLER_ONLINE"]:
            cur = per_video[per_video["pipeline"] == pipeline]
            if cur.empty or p3.empty:
                continue
            joined = cur.merge(p3, on=["category", "video"], how="inner")
            joined["delta_vs_p3"] = pd.to_numeric(joined["fmeasure"], errors="coerce") - pd.to_numeric(joined["p3_fmeasure"], errors="coerce")
            joined = joined.sort_values("delta_vs_p3").head(10)
            for _, row in joined.iterrows():
                rows.append(
                    {
                        "dataset": dataset_name,
                        "category": row.get("category", ""),
                        "video": row.get("video", ""),
                        "pipeline": pipeline,
                        "case_type": "worse_than_p3",
                        "metric": "fmeasure",
                        "value": row.get("fmeasure", ""),
                        "reference_pipeline": "P3_MOG2",
                        "reference_value": row.get("p3_fmeasure", ""),
                        "delta": row.get("delta_vs_p3", ""),
                        "notes": "negative delta means lower F-measure than P3_MOG2 on the same video",
                    }
                )

    return pd.DataFrame(
        rows,
        columns=[
            "dataset",
            "category",
            "video",
            "pipeline",
            "case_type",
            "metric",
            "value",
            "reference_pipeline",
            "reference_value",
            "delta",
            "notes",
        ],
    )


def _sequence_paths(output_dir: str | Path, filename: str) -> Iterable[Path]:
    root = Path(output_dir) / "raw_results"
    if not root.exists():
        return []
    return root.rglob(filename)


def _read_sequence_summaries(output_dir: str | Path, filename: str) -> pd.DataFrame:
    rows = []
    for path in _sequence_paths(output_dir, filename):
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if not df.empty:
            rows.append(df.iloc[0].to_dict())
    return pd.DataFrame(rows)


def _col(df: pd.DataFrame, name: str, default=0.0):
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce").fillna(0.0)
    if isinstance(default, pd.Series):
        return pd.to_numeric(default, errors="coerce").fillna(0.0)
    return default


def _weights(df: pd.DataFrame) -> pd.Series:
    if "processed_frames" in df.columns:
        weights = pd.to_numeric(df["processed_frames"], errors="coerce").fillna(0.0)
        if float(weights.sum()) > 0:
            return weights
    return pd.Series(np.ones(len(df)), index=df.index)


def _weighted_mean(df: pd.DataFrame, col: str, weights: pd.Series) -> float:
    if col not in df.columns:
        return 0.0
    values = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    total = float(weights.sum())
    if total <= 0:
        return float(values.mean()) if len(values) else 0.0
    return float((values * weights).sum() / total)


def _sort_by_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "pipeline" not in df.columns:
        return df
    out = df.copy()
    out["pipeline"] = pd.Categorical(out["pipeline"].astype(str), categories=PIPELINE_ORDER, ordered=True)
    sort_cols = [c for c in ["dataset", "category", "video", "pipeline", "frame_id"] if c in out.columns]
    out = out.sort_values(sort_cols)
    out["pipeline"] = out["pipeline"].astype(str)
    return out.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--dataset_name", default="")
    parser.add_argument("--low_fmeasure_threshold", type=float, default=0.25)
    args = parser.parse_args()
    paths = aggregate_cross_dataset(args.output_dir, args.dataset_name or None, args.low_fmeasure_threshold)
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
