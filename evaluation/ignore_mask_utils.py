from __future__ import annotations

from typing import Iterable, Optional

import cv2
import numpy as np

from evaluation.mask_normalization import to_grayscale


def ignore_mask_from_values(mask, ignore_values: Optional[Iterable[int]] = None) -> np.ndarray:
    gray = to_grayscale(mask)
    if not ignore_values:
        return np.zeros(gray.shape, dtype=bool)
    return np.isin(gray, [int(v) for v in ignore_values])


def combine_ignore_masks(*masks) -> np.ndarray:
    available = [np.asarray(mask).astype(bool) for mask in masks if mask is not None]
    if not available:
        return np.zeros((0, 0), dtype=bool)
    out = np.zeros(available[0].shape, dtype=bool)
    for mask in available:
        if mask.shape != out.shape:
            mask = cv2.resize(mask.astype(np.uint8), (out.shape[1], out.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        out |= mask
    return out


def valid_mask_from_ignore(ignore_mask, shape=None) -> np.ndarray:
    if ignore_mask is None:
        if shape is None:
            raise ValueError("shape is required when ignore_mask is None")
        return np.ones(shape, dtype=bool)
    return ~np.asarray(ignore_mask).astype(bool)


def apply_ignore_mask(mask, ignore_mask, fill_value: int = 0) -> np.ndarray:
    out = np.asarray(mask).copy()
    if ignore_mask is not None:
        out[np.asarray(ignore_mask).astype(bool)] = fill_value
    return out
