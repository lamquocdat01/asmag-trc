from __future__ import annotations

from typing import Iterable, Optional

import cv2
import numpy as np


def to_grayscale(mask) -> np.ndarray:
    arr = np.asarray(mask)
    if arr.ndim == 3:
        return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY) if arr.shape[2] >= 3 else arr[:, :, 0]
    return arr


def normalize_prediction_mask(mask, threshold: int = 127) -> np.ndarray:
    gray = to_grayscale(mask)
    out = np.zeros(gray.shape, dtype=np.uint8)
    out[gray > threshold] = 255
    return out


def normalize_gt_mask(
    mask,
    foreground_values: Optional[Iterable[int]] = (255,),
    foreground_threshold: int = 127,
    ignore_mask=None,
) -> np.ndarray:
    gray = to_grayscale(mask)
    if foreground_values is None:
        foreground = gray > int(foreground_threshold)
    else:
        foreground = np.isin(gray, [int(v) for v in foreground_values])
    out = np.zeros(gray.shape, dtype=np.uint8)
    out[foreground] = 255
    if ignore_mask is not None:
        out[np.asarray(ignore_mask).astype(bool)] = 0
    return out


def encode_cdnet_style_gt(binary_mask, ignore_mask=None, ignore_value: int = 85) -> np.ndarray:
    gt = normalize_prediction_mask(binary_mask)
    if ignore_mask is not None:
        gt[np.asarray(ignore_mask).astype(bool)] = int(ignore_value)
    return gt.astype(np.uint8)
