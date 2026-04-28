import argparse
import csv
from pathlib import Path

import cv2
import numpy as np
import yaml


def frame_number(path):
    digits = "".join(ch for ch in Path(path).stem if ch.isdigit())
    return int(digits) if digits else None


def read_temporal_roi(video_dir):
    roi_path = video_dir / "temporalROI.txt"
    if not roi_path.exists():
        return None, None
    parts = roi_path.read_text(encoding="utf-8").strip().split()
    if len(parts) < 2:
        return None, None
    return int(parts[0]), int(parts[1])


def list_frames(folder, patterns):
    if not folder.exists():
        return []
    frames = []
    for pattern in patterns:
        frames.extend(folder.glob(pattern))
    return sorted(frames)


def unique_values(path):
    gt = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if gt is None:
        return ""
    vals, counts = np.unique(gt, return_counts=True)
    return ";".join(f"{int(v)}:{int(c)}" for v, c in zip(vals, counts))


def sample_gt_frames(gt_files, roi_start, roi_end):
    by_number = {frame_number(p): p for p in gt_files if frame_number(p) is not None}
    if not by_number:
        return []

    if roi_start is not None and roi_end is not None:
        candidates = [n for n in sorted(by_number) if roi_start <= n <= roi_end]
    else:
        candidates = sorted(by_number)

    if not candidates:
        return []
    if len(candidates) <= 3:
        sample_numbers = candidates
    else:
        sample_numbers = [
            candidates[0],
            candidates[len(candidates) // 2],
            candidates[-1],
        ]
    return [(n, by_number[n], unique_values(by_number[n])) for n in sample_numbers]


def audit_dataset(dataset_root):
    rows = []
    root = Path(dataset_root)
    for category_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for video_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            input_dir = video_dir / "input"
            gt_dir = video_dir / "groundtruth"
            input_files = list_frames(input_dir, ["*.jpg", "*.png"])
            gt_files = list_frames(gt_dir, ["*.png"])
            roi_start, roi_end = read_temporal_roi(video_dir)
            samples = sample_gt_frames(gt_files, roi_start, roi_end)

            row = {
                "category": category_dir.name,
                "video": video_dir.name,
                "has_input_folder": input_dir.exists(),
                "has_groundtruth_folder": gt_dir.exists(),
                "input_frame_count": len(input_files),
                "groundtruth_frame_count": len(gt_files),
                "has_temporalROI": (video_dir / "temporalROI.txt").exists(),
                "temporal_roi_start": roi_start if roi_start is not None else "",
                "temporal_roi_end": roi_end if roi_end is not None else "",
            }
            for i in range(3):
                if i < len(samples):
                    frame_no, gt_path, values = samples[i]
                    row[f"gt_sample_{i+1}_frame"] = frame_no
                    row[f"gt_sample_{i+1}_file"] = gt_path.name
                    row[f"gt_sample_{i+1}_unique_values"] = values
                else:
                    row[f"gt_sample_{i+1}_frame"] = ""
                    row[f"gt_sample_{i+1}_file"] = ""
                    row[f"gt_sample_{i+1}_unique_values"] = ""
            rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/q2_core.yaml")
    parser.add_argument("--output", default="outputs/dataset_audit.csv")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    dataset_root = cfg["dataset_root"]
    rows = audit_dataset(dataset_root)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "category",
        "video",
        "has_input_folder",
        "has_groundtruth_folder",
        "input_frame_count",
        "groundtruth_frame_count",
        "has_temporalROI",
        "temporal_roi_start",
        "temporal_roi_end",
        "gt_sample_1_frame",
        "gt_sample_1_file",
        "gt_sample_1_unique_values",
        "gt_sample_2_frame",
        "gt_sample_2_file",
        "gt_sample_2_unique_values",
        "gt_sample_3_frame",
        "gt_sample_3_file",
        "gt_sample_3_unique_values",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DATASET] {dataset_root}")
    print(f"[VIDEOS] {len(rows)}")
    print(f"[OUT] {out_path}")


if __name__ == "__main__":
    main()
