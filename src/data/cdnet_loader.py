import os, glob
from pathlib import Path
import cv2
import numpy as np

def frame_number(path):
    digits = "".join(ch for ch in Path(path).stem if ch.isdigit())
    return int(digits) if digits else None

def read_temporal_roi(video_dir):
    roi_path = Path(video_dir) / "temporalROI.txt"
    if not roi_path.exists():
        return None, None
    parts = roi_path.read_text(encoding="utf-8").strip().split()
    if len(parts) < 2:
        return None, None
    return int(parts[0]), int(parts[1])

def scan_cdnet(dataset_root, categories, videos="auto"):
    sequences = []
    root = Path(dataset_root)
    for cat in categories:
        cat_dir = root / cat
        if not cat_dir.exists():
            print(f"[WARN] Category not found: {cat_dir}")
            continue
        if videos == "auto":
            video_names = [p.name for p in cat_dir.iterdir() if p.is_dir()]
        else:
            video_names = videos.get(cat, [])
        for vid in video_names:
            video_dir = cat_dir / vid
            input_dir = video_dir / "input"
            gt_dir = video_dir / "groundtruth"
            if input_dir.exists():
                roi_start, roi_end = read_temporal_roi(video_dir)
                sequences.append({
                    "category": cat,
                    "video": vid,
                    "input_dir": str(input_dir),
                    "gt_dir": str(gt_dir),
                    "roi_start": roi_start,
                    "roi_end": roi_end
                })
    return sequences

def list_frames(input_dir, gt_dir):
    frames = sorted(glob.glob(os.path.join(input_dir, "*.jpg")))
    if not frames:
        frames = sorted(glob.glob(os.path.join(input_dir, "*.png")))
    gts = sorted(glob.glob(os.path.join(gt_dir, "*.png"))) if os.path.exists(gt_dir) else []
    return frames, gts

def read_frame(path):
    return cv2.imread(path)

def read_gt(gt_files, idx, shape):
    if idx < len(gt_files):
        gt = cv2.imread(gt_files[idx], cv2.IMREAD_GRAYSCALE)
        if gt is not None:
            return gt
    return np.zeros(shape[:2], dtype=np.uint8)

def read_gt_for_frame(gt_by_number, frame_file, shape):
    num = frame_number(frame_file)
    gt_path = gt_by_number.get(num)
    if gt_path:
        gt = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
        if gt is not None:
            return gt
    return np.zeros(shape[:2], dtype=np.uint8)

def make_synthetic_sequence(num_frames=160, width=320, height=180):
    frames, gts = [], []
    for i in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8) + 25
        gt = np.zeros((height, width), dtype=np.uint8)
        # illumination changes
        if 50 <= i < 60:
            frame[:] = 80
        # moving/standing object
        if 20 <= i < 140:
            if i < 70:
                x = 20 + i * 2
            elif i < 105:
                x = 160  # intermittent/stationary
            else:
                x = 160 + (i - 105) * 2
            y = 70
            cv2.rectangle(frame, (x, y), (x+36, y+26), (210, 210, 210), -1)
            cv2.rectangle(gt, (x, y), (x+36, y+26), 255, -1)
        # dynamic background noise
        for k in range(6):
            cx = (i*3 + k*47) % width
            cy = (k*31 + 20) % height
            cv2.circle(frame, (cx, cy), 2, (60,60,60), -1)
        frames.append(frame)
        gts.append(gt)
    return frames, gts
