from pathlib import Path

import pandas as pd


PARETO_COLUMNS = [
    "FMeasure",
    "Event_F1",
    "mAP_50",
    "Activation",
    "Avg_FPS",
    "P95_latency_ms",
    "Estimated_energy_per_frame",
]


DEFAULT_AE_WEIGHTS = {
    "FMeasure_weight": 0.25,
    "Event_F1_weight": 0.25,
    "mAP_50_weight": 0.20,
    "Activation_saving_weight": 0.15,
    "FPS_norm_weight": 0.10,
    "Energy_saving_weight": 0.05,
}


def build_pareto_metrics(out_dir, config=None):
    out_dir = Path(out_dir)
    cdnet = _read_pipeline_metrics(out_dir / "summary_cdnet_metrics.csv", ["FMeasure"])
    objects = _read_pipeline_metrics(out_dir / "summary_object_metrics.csv", ["mAP_50"])
    events = _read_pipeline_metrics(out_dir / "summary_event_metrics.csv", ["Event_F1"])
    edge = _read_pipeline_metrics(
        out_dir / "summary_edge_metrics.csv",
        ["YOLO_activation_rate", "avg_FPS", "P95_latency_ms"],
    )
    energy = _read_pipeline_metrics(
        out_dir / "summary_edge_energy_metrics.csv",
        ["Estimated_energy_per_frame"],
    )

    merged = _merge_pipeline_frames([cdnet, objects, events, edge, energy])
    if merged.empty:
        return pd.DataFrame(columns=["pipeline", *PARETO_COLUMNS, "AE_Score", "Pareto_Efficient"])

    merged = merged.rename(
        columns={
            "YOLO_activation_rate": "Activation",
            "avg_FPS": "Avg_FPS",
        }
    )
    for col in PARETO_COLUMNS:
        if col not in merged.columns:
            merged[col] = 0.0
        merged[col] = merged[col].fillna(0.0).astype(float)

    merged["FPS_norm"] = _norm_by_max(merged["Avg_FPS"])
    merged["Energy_norm"] = _norm_by_max(merged["Estimated_energy_per_frame"])
    merged["Latency_norm"] = _norm_by_max(merged["P95_latency_ms"])
    weights = _ae_weights(config)
    merged["AE_Score"] = (
        weights["FMeasure_weight"] * merged["FMeasure"]
        + weights["Event_F1_weight"] * merged["Event_F1"]
        + weights["mAP_50_weight"] * merged["mAP_50"]
        + weights["Activation_saving_weight"] * (1.0 - merged["Activation"])
        + weights["FPS_norm_weight"] * merged["FPS_norm"]
        + weights["Energy_saving_weight"] * (1.0 - merged["Energy_norm"])
    )
    merged["Pareto_Efficient"] = _pareto_flags(merged)
    return merged.sort_values(["Pareto_Efficient", "AE_Score"], ascending=[False, False])


def write_pareto_metrics(out_dir, config=None):
    out_dir = Path(out_dir)
    df = build_pareto_metrics(out_dir, config)
    df.to_csv(out_dir / "summary_pareto_metrics.csv", index=False)
    return df


def _ae_weights(config=None):
    weights = dict(DEFAULT_AE_WEIGHTS)
    if config:
        weights.update(config.get("ae_score_formula", {}))
    return {key: float(value) for key, value in weights.items()}


def _read_pipeline_metrics(path, value_cols):
    if not path.exists():
        return pd.DataFrame(columns=["pipeline", *value_cols])

    df = pd.read_csv(path)
    if df.empty or "pipeline" not in df.columns:
        return pd.DataFrame(columns=["pipeline", *value_cols])

    if "aggregation_level" in df.columns:
        pipeline_df = df[df["aggregation_level"] == "pipeline"].copy()
        if pipeline_df.empty:
            pipeline_df = df.copy()
    else:
        pipeline_df = df.copy()

    available = [col for col in value_cols if col in pipeline_df.columns]
    if not available:
        return pd.DataFrame(columns=["pipeline", *value_cols])

    out = pipeline_df.groupby("pipeline", as_index=False)[available].mean(numeric_only=True)
    for col in value_cols:
        if col not in out.columns:
            out[col] = 0.0
    return out[["pipeline", *value_cols]]


def _merge_pipeline_frames(frames):
    usable = [df for df in frames if not df.empty]
    if not usable:
        return pd.DataFrame()
    merged = usable[0]
    for df in usable[1:]:
        merged = merged.merge(df, on="pipeline", how="outer")
    return merged


def _norm_by_max(series):
    max_value = float(series.max()) if len(series) else 0.0
    if max_value <= 0:
        return pd.Series([0.0] * len(series), index=series.index)
    return series.astype(float) / max_value


def _pareto_flags(df):
    flags = []
    higher_better = ["FMeasure", "Event_F1", "mAP_50", "Avg_FPS"]
    lower_better = ["Activation", "Estimated_energy_per_frame"]

    for idx, row in df.iterrows():
        dominated = False
        for other_idx, other in df.iterrows():
            if idx == other_idx:
                continue
            no_worse = all(other[col] >= row[col] for col in higher_better) and all(
                other[col] <= row[col] for col in lower_better
            )
            strictly_better = any(other[col] > row[col] for col in higher_better) or any(
                other[col] < row[col] for col in lower_better
            )
            if no_worse and strictly_better:
                dominated = True
                break
        flags.append(not dominated)
    return flags
