import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import yaml


PIPELINES = {
    "YOLO": "P1_YOLO_Only",
    "P2 mask": "P2_FrameDiff",
    "P3 mask": "P3_MOG2",
    "P4 mask": "P4_ASMAG_PLUS",
}


def read_gray(path, shape):
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return np.zeros(shape[:2], dtype=np.uint8)
    return img


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 24), (0, 0, 0), -1)
    cv2.putText(out, text, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return out


def gt_visual(gt):
    if gt.ndim == 3:
        gt = gt[:, :, 0]
    out = np.zeros((gt.shape[0], gt.shape[1], 3), dtype=np.uint8)
    out[gt == 0] = (20, 20, 20)
    out[(gt == 50) | (gt == 85)] = (120, 120, 120)
    out[gt == 170] = (0, 180, 180)
    out[gt == 255] = (0, 220, 0)
    return out


def mask_visual(mask):
    out = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    out[mask > 0] = (255, 255, 255)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/debug_yolo_50frames.yaml")
    parser.add_argument("--experiment", default=None)
    parser.add_argument("--category", default="baseline")
    parser.add_argument("--video", default="highway")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    experiment = args.experiment or cfg["experiment_name"]
    dataset_root = Path(cfg["dataset_root"])
    seq_dir = dataset_root / args.category / args.video
    raw_root = Path(cfg.get("output_root", "outputs")) / experiment / "raw_results" / args.category / args.video
    out_dir = Path(cfg.get("output_root", "outputs")) / experiment / "compare_grid"
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = raw_root / "P1_YOLO_Only" / "frame_metrics.csv"
    frame_ids = pd.read_csv(metrics_path)["frame_id"].astype(int).tolist()

    for frame_id in frame_ids[:10]:
        frame = cv2.imread(str(seq_dir / "input" / f"in{frame_id:06d}.jpg"))
        if frame is None:
            frame = cv2.imread(str(seq_dir / "input" / f"in{frame_id:06d}.png"))
        if frame is None:
            continue

        gt = read_gray(seq_dir / "groundtruth" / f"gt{frame_id:06d}.png", frame.shape)
        panels = [
            label(frame, f"Original {frame_id:06d}"),
            label(gt_visual(gt), "Ground truth"),
        ]

        for title, pipeline in [("P2 mask", "P2_FrameDiff"), ("P3 mask", "P3_MOG2"), ("P4 mask", "P4_ASMAG_PLUS"), ("YOLO prediction", "P1_YOLO_Only")]:
            mask = read_gray(raw_root / pipeline / "masks" / f"bin{frame_id:06d}.png", frame.shape)
            panels.append(label(mask_visual(mask), title))

        grid = np.hstack(panels)
        cv2.imwrite(str(out_dir / f"compare_{frame_id:06d}.png"), grid)

    print(f"[OUT] {out_dir}")
    print(f"[FRAMES] {min(10, len(frame_ids))}")


if __name__ == "__main__":
    main()
