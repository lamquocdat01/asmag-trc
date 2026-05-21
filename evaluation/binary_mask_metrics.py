from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

import numpy as np

from evaluation.mask_normalization import normalize_prediction_mask


@dataclass(frozen=True)
class BinaryMaskCounts:
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0

    def as_dict(self) -> dict:
        return {"tp": self.tp, "tn": self.tn, "fp": self.fp, "fn": self.fn}


def counts_to_metrics(tp: int, tn: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    fmeasure = 2.0 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    total = tp + tn + fp + fn
    pwc = 100.0 * (fp + fn) / total if total else 0.0
    return {
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "fpr": fpr,
        "fnr": fnr,
        "pwc": pwc,
        "fmeasure": fmeasure,
    }


def compute_binary_mask_metrics(pred_mask, gt_mask, ignore_mask: Optional[np.ndarray] = None) -> dict:
    pred = normalize_prediction_mask(pred_mask) > 0
    gt = normalize_prediction_mask(gt_mask) > 0
    if ignore_mask is None:
        valid = np.ones(gt.shape, dtype=bool)
    else:
        valid = ~np.asarray(ignore_mask).astype(bool)
    tp = int(np.sum(pred & gt & valid))
    tn = int(np.sum((~pred) & (~gt) & valid))
    fp = int(np.sum(pred & (~gt) & valid))
    fn = int(np.sum((~pred) & gt & valid))
    return counts_to_metrics(tp, tn, fp, fn)


def aggregate_binary_mask_metrics(rows: Iterable[Mapping]) -> dict:
    rows = list(rows)
    tp = sum(int(row.get("tp", row.get("TP_pixel", 0)) or 0) for row in rows)
    tn = sum(int(row.get("tn", row.get("TN_pixel", 0)) or 0) for row in rows)
    fp = sum(int(row.get("fp", row.get("FP_pixel", 0)) or 0) for row in rows)
    fn = sum(int(row.get("fn", row.get("FN_pixel", 0)) or 0) for row in rows)
    return counts_to_metrics(tp, tn, fp, fn)


def event_f1_from_rows(rows: Iterable[Mapping]) -> dict:
    rows = list(rows)
    tp = sum(int(row.get("Event_TP", row.get("event_tp", 0)) or 0) for row in rows)
    tn = sum(int(row.get("Event_TN", row.get("event_tn", 0)) or 0) for row in rows)
    fp = sum(int(row.get("Event_FP", row.get("event_fp", 0)) or 0) for row in rows)
    fn = sum(int(row.get("Event_FN", row.get("event_fn", 0)) or 0) for row in rows)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    return {
        "event_tp": int(tp),
        "event_tn": int(tn),
        "event_fp": int(fp),
        "event_fn": int(fn),
        "event_precision": precision,
        "event_recall": recall,
        "event_accuracy": accuracy,
        "event_f1": f1,
    }
