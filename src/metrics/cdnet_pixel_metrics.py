import numpy as np
import pandas as pd


DEFAULT_CDNET_GT_CONFIG = {
    "foreground_values": [255],
    "background_values": [0],
    "ignore_values": [50, 85, 170],
}

COUNT_COLUMNS = ["TP_pixel", "TN_pixel", "FP_pixel", "FN_pixel"]
METRIC_COLUMNS = [
    "TP_pixel",
    "TN_pixel",
    "FP_pixel",
    "FN_pixel",
    "Precision",
    "Recall",
    "Specificity",
    "FPR",
    "FNR",
    "PWC",
    "FMeasure",
]


def normalize_cdnet_gt_config(config=None):
    cdnet_gt = dict(DEFAULT_CDNET_GT_CONFIG)
    if config:
        cdnet_gt.update(config)
    return {
        "foreground_values": _as_int_set(cdnet_gt.get("foreground_values", [255])),
        "background_values": _as_int_set(cdnet_gt.get("background_values", [0])),
        "ignore_values": _as_int_set(cdnet_gt.get("ignore_values", [50, 85, 170])),
    }


def valid_gt_mask(gt, config=None):
    if gt.ndim == 3:
        gt = gt[:, :, 0]
    cdnet_gt = normalize_cdnet_gt_config(config)
    fg = np.isin(gt, list(cdnet_gt["foreground_values"]))
    bg = np.isin(gt, list(cdnet_gt["background_values"]))
    ignore = np.isin(gt, list(cdnet_gt["ignore_values"]))

    valid = fg | bg
    fg = fg & valid
    bg = bg & valid
    ignore = ignore | (~valid)
    return fg, bg, ignore


def pixel_metrics(pred_mask, gt, config=None):
    fg, bg, ignore = valid_gt_mask(gt, config)
    pred = pred_mask > 0
    valid = ~ignore
    TP = int(np.sum(pred & fg & valid))
    TN = int(np.sum((~pred) & bg & valid))
    FP = int(np.sum(pred & bg & valid))
    FN = int(np.sum((~pred) & fg & valid))
    return counts_to_metrics(TP, TN, FP, FN)


def aggregate_pixel(rows):
    if not rows:
        return {}
    counts = {key: int(sum(row.get(key, 0) for row in rows)) for key in COUNT_COLUMNS}
    return counts_to_metrics(
        counts["TP_pixel"],
        counts["TN_pixel"],
        counts["FP_pixel"],
        counts["FN_pixel"],
    )


def build_cdnet_metrics_summary(frame_rows):
    """Return frame, video, category, and pipeline CDnet metric summaries."""
    if not frame_rows:
        return pd.DataFrame(columns=["aggregation_level", *METRIC_COLUMNS])

    df = pd.DataFrame(frame_rows)
    summaries = []
    frame_keys = ["category", "video", "pipeline", "frame_id"]
    summaries.append(_frame_summary(df, frame_keys))
    for level, keys in [
        ("video", ["category", "video", "pipeline"]),
        ("category", ["category", "pipeline"]),
        ("pipeline", ["pipeline"]),
    ]:
        summaries.append(_group_summary(df, keys, level))
    return pd.concat(summaries, ignore_index=True)


def counts_to_metrics(TP, TN, FP, FN):
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    specificity = TN / (TN + FP) if (TN + FP) > 0 else 0
    fpr = FP / (FP + TN) if (FP + TN) > 0 else 0
    fnr = FN / (FN + TP) if (FN + TP) > 0 else 0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    fmeasure = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    total = TP + TN + FP + FN
    pwc = 100 * (FN + FP) / total if total > 0 else 0
    return {
        "TP_pixel": int(TP),
        "TN_pixel": int(TN),
        "FP_pixel": int(FP),
        "FN_pixel": int(FN),
        "Recall": recall,
        "Specificity": specificity,
        "FPR": fpr,
        "FNR": fnr,
        "Precision": precision,
        "FMeasure": fmeasure,
        "PWC": pwc,
    }


def _frame_summary(df, keys):
    cols = [col for col in keys + METRIC_COLUMNS if col in df.columns]
    out = df[cols].copy()
    out.insert(0, "aggregation_level", "frame")
    return out


def _group_summary(df, keys, level):
    grouped = df.groupby(keys, as_index=False)[COUNT_COLUMNS].sum()
    metric_rows = []
    for _, row in grouped.iterrows():
        metrics = counts_to_metrics(
            int(row["TP_pixel"]),
            int(row["TN_pixel"]),
            int(row["FP_pixel"]),
            int(row["FN_pixel"]),
        )
        metric_rows.append({**{key: row[key] for key in keys}, **metrics})
    out = pd.DataFrame(metric_rows)
    out.insert(0, "aggregation_level", level)
    return out


def _as_int_set(values):
    if values is None:
        return set()
    return {int(value) for value in values}
