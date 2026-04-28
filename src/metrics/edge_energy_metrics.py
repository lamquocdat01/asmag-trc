import pandas as pd


DEFAULT_ENERGY_PROXY_CONFIG = {
    "E_base": 1.0,
    "E_gate": 0.2,
    "E_yolo": 5.0,
    "E_reuse": 0.1,
    "E_mog2": 0.5,
    "E_framediff": 0.1,
    "unit": "relative_energy_unit",
}


def normalize_energy_config(config=None):
    energy = dict(DEFAULT_ENERGY_PROXY_CONFIG)
    if config:
        energy.update(config)
    for key in ["E_base", "E_gate", "E_yolo", "E_reuse", "E_mog2", "E_framediff"]:
        energy[key] = float(energy[key])
    return energy


def energy_usage_flags(pipeline_key):
    framediff_used = pipeline_key in {
        "P2_FrameDiff",
        "P4_ASMAG_PLUS",
        "P4_ASMAG_PLUS_PRECISION",
        "P4_ASMAG_PLUS_BALANCED",
        "P4_ASMAG_PLUS_EFFICIENT",
        "P4_ASMAG_PLUS_EFFICIENT_REUSE",
    }
    mog2_used = pipeline_key in {
        "P3_MOG2",
        "P4_ASMAG_PLUS",
        "P4_ASMAG_PLUS_PRECISION",
        "P4_ASMAG_PLUS_BALANCED",
        "P4_ASMAG_PLUS_EFFICIENT",
        "P4_ASMAG_PLUS_EFFICIENT_REUSE",
    }
    return int(mog2_used), int(framediff_used)


def frame_energy(row, config=None):
    energy = normalize_energy_config(config)
    return (
        energy["E_base"]
        + energy["E_gate"]
        + int(row.get("yolo_called", 0)) * energy["E_yolo"]
        + int(row.get("reused_prediction", 0)) * energy["E_reuse"]
        + int(row.get("mog2_used", 0)) * energy["E_mog2"]
        + int(row.get("framediff_used", 0)) * energy["E_framediff"]
    )


def summarize_edge_energy(frame_rows, config=None):
    if not frame_rows:
        return pd.DataFrame()

    energy = normalize_energy_config(config)
    df = pd.DataFrame(frame_rows).copy()
    if "energy_frame" not in df.columns:
        df["energy_frame"] = df.apply(lambda row: frame_energy(row, energy), axis=1)

    group_keys = ["category", "video", "pipeline"]
    grouped = df.groupby(group_keys, as_index=False).agg(
        Estimated_energy_total=("energy_frame", "sum"),
        processed_frames=("energy_frame", "count"),
        active_event_frames=("Is_Active", "sum"),
        yolo_calls=("yolo_called", "sum"),
        reused_prediction_count=("reused_prediction", "sum"),
        mog2_used_frames=("mog2_used", "sum"),
        framediff_used_frames=("framediff_used", "sum"),
    )
    grouped["Estimated_energy_per_frame"] = (
        grouped["Estimated_energy_total"] / grouped["processed_frames"].clip(lower=1)
    )
    grouped["Estimated_energy_per_event"] = grouped.apply(
        lambda row: row["Estimated_energy_total"] / row["active_event_frames"]
        if row["active_event_frames"] > 0
        else 0.0,
        axis=1,
    )
    grouped["energy_unit"] = str(energy.get("unit", "relative_energy_unit"))

    grouped["Energy_reduction_rate_vs_P1_YOLO_Only"] = 0.0
    grouped["Energy_reduction_rate_vs_P4_ASMAG_PLUS"] = 0.0
    for _, seq_group in grouped.groupby(["category", "video"], sort=False):
        p1 = _baseline_energy(seq_group, "P1_YOLO_Only")
        p4 = _baseline_energy(seq_group, "P4_ASMAG_PLUS")
        for idx in seq_group.index:
            current = float(grouped.loc[idx, "Estimated_energy_per_frame"])
            grouped.loc[idx, "Energy_reduction_rate_vs_P1_YOLO_Only"] = _reduction(p1, current)
            grouped.loc[idx, "Energy_reduction_rate_vs_P4_ASMAG_PLUS"] = _reduction(p4, current)

    unit = str(energy.get("unit", "relative_energy_unit"))
    pipeline_summary = _aggregate_summary(grouped, ["pipeline"], "pipeline", unit)
    category_summary = _aggregate_summary(grouped, ["category", "pipeline"], "category", unit)
    video_summary = grouped.copy()
    video_summary.insert(0, "aggregation_level", "video")
    return pd.concat([video_summary, category_summary, pipeline_summary], ignore_index=True)


def _aggregate_summary(df, keys, level, unit):
    grouped = df.groupby(keys, as_index=False).agg(
        Estimated_energy_total=("Estimated_energy_total", "sum"),
        processed_frames=("processed_frames", "sum"),
        active_event_frames=("active_event_frames", "sum"),
        yolo_calls=("yolo_calls", "sum"),
        reused_prediction_count=("reused_prediction_count", "sum"),
        mog2_used_frames=("mog2_used_frames", "sum"),
        framediff_used_frames=("framediff_used_frames", "sum"),
        Energy_reduction_rate_vs_P1_YOLO_Only=("Energy_reduction_rate_vs_P1_YOLO_Only", "mean"),
        Energy_reduction_rate_vs_P4_ASMAG_PLUS=("Energy_reduction_rate_vs_P4_ASMAG_PLUS", "mean"),
    )
    grouped["Estimated_energy_per_frame"] = (
        grouped["Estimated_energy_total"] / grouped["processed_frames"].clip(lower=1)
    )
    grouped["Estimated_energy_per_event"] = grouped.apply(
        lambda row: row["Estimated_energy_total"] / row["active_event_frames"]
        if row["active_event_frames"] > 0
        else 0.0,
        axis=1,
    )
    grouped["energy_unit"] = unit
    grouped.insert(0, "aggregation_level", level)
    return grouped


def _baseline_energy(group, pipeline):
    row = group[group["pipeline"] == pipeline]
    if row.empty:
        return None
    return float(row["Estimated_energy_per_frame"].iloc[0])


def _reduction(baseline, current):
    if baseline is None or baseline <= 0:
        return 0.0
    return (baseline - current) / baseline
