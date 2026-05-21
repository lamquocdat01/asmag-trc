from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import cv2
import numpy as np


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".pgm", ".ppm")
MASK_EXTENSIONS = (".png", ".bmp", ".jpg", ".jpeg", ".tif", ".tiff", ".pgm", ".ppm")


@dataclass(frozen=True)
class FrameRecord:
    frame_id: int
    frame_path: Path
    gt_path: Optional[Path]
    ignore_path: Optional[Path] = None


@dataclass(frozen=True)
class VideoRecord:
    video_id: str
    category: str
    video: str
    frame_dir: Path
    gt_dir: Optional[Path]
    ignore_dir: Optional[Path] = None
    roi_start: Optional[int] = None
    roi_end: Optional[int] = None


def frame_number(path: Path | str) -> Optional[int]:
    digits = "".join(ch for ch in Path(path).stem if ch.isdigit())
    return int(digits) if digits else None


def safe_name(value: str) -> str:
    value = str(value).strip().replace("\\", "/")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("_") or "unnamed"


def _as_path_list(paths: Iterable[Path]) -> List[Path]:
    return sorted(paths, key=lambda p: (frame_number(p) is None, frame_number(p) or 0, p.name.lower()))


def _as_int_values(values, default=None) -> Optional[List[int]]:
    if values is None:
        return default
    if isinstance(values, str):
        if not values.strip():
            return default
        values = [part.strip() for part in values.split(",")]
    return [int(v) for v in values]


class BaseDatasetAdapter:
    """Base adapter for video foreground segmentation datasets.

    Adapters intentionally expose a small common protocol used by
    run_cross_dataset.py:

    - list_videos()
    - iter_frames(video_id)
    - load_frame(frame_path)
    - load_gt_mask(gt_path)
    - normalize_gt_mask(mask)
    - get_ignore_mask(mask)
    """

    dataset_name = "generic"
    default_frame_dir_names = (
        "input",
        "inputs",
        "frames",
        "frame",
        "images",
        "image",
        "imgs",
        "img",
        "rgb",
        "RGB",
        "JPEGImages",
    )
    default_gt_dir_names = (
        "groundtruth",
        "groundTruth",
        "GroundTruth",
        "gt",
        "GT",
        "masks",
        "Masks",
        "mask",
        "foreground",
        "Foreground",
        "fg",
        "FG",
        "binary",
        "Binary",
    )
    default_ignore_dir_names = (
        "ignore",
        "Ignore",
        "void",
        "Void",
        "roi",
        "ROI",
        "valid",
        "valid_roi",
    )
    default_foreground_values: Optional[Sequence[int]] = (255,)
    default_background_values: Optional[Sequence[int]] = (0,)
    default_ignore_values: Sequence[int] = ()
    default_foreground_threshold = 127

    def __init__(self, dataset_root: str | Path, config: Optional[dict] = None):
        self.root = Path(dataset_root)
        self.config = config or {}
        self.frame_dir_names = tuple(self.config.get("frame_dir_names", self.default_frame_dir_names))
        self.gt_dir_names = tuple(self.config.get("gt_dir_names", self.default_gt_dir_names))
        self.ignore_dir_names = tuple(self.config.get("ignore_dir_names", self.default_ignore_dir_names))
        self.foreground_values = _as_int_values(
            self.config.get("foreground_values", self.default_foreground_values),
            list(self.default_foreground_values) if self.default_foreground_values is not None else None,
        )
        self.background_values = _as_int_values(
            self.config.get("background_values", self.default_background_values),
            list(self.default_background_values) if self.default_background_values is not None else None,
        )
        self.ignore_values = _as_int_values(
            self.config.get("ignore_values", self.default_ignore_values),
            list(self.default_ignore_values),
        )
        self.foreground_threshold = int(self.config.get("foreground_threshold", self.default_foreground_threshold))
        self._videos: Dict[str, VideoRecord] = {}

    def list_videos(self) -> List[str]:
        self._ensure_discovered()
        return sorted(self._videos)

    def get_video(self, video_id: str) -> VideoRecord:
        self._ensure_discovered()
        if video_id not in self._videos:
            raise KeyError(f"Unknown {self.dataset_name} video_id: {video_id}")
        return self._videos[video_id]

    def iter_frames(self, video_id: str) -> Iterator[FrameRecord]:
        video = self.get_video(video_id)
        frame_files = self._list_files(video.frame_dir, IMAGE_EXTENSIONS)
        gt_files = self._list_files(video.gt_dir, MASK_EXTENSIONS) if video.gt_dir else []
        ignore_files = self._list_files(video.ignore_dir, MASK_EXTENSIONS) if video.ignore_dir else []
        gt_by_number = self._files_by_number(gt_files)
        ignore_by_number = self._files_by_number(ignore_files)

        for index, frame_path in enumerate(frame_files):
            num = frame_number(frame_path)
            frame_id = num if num is not None else index + 1
            gt_path = gt_by_number.get(num) if num is not None else None
            if gt_path is None and index < len(gt_files):
                gt_path = gt_files[index]
            ignore_path = ignore_by_number.get(num) if num is not None else None
            if ignore_path is None and index < len(ignore_files):
                ignore_path = ignore_files[index]
            yield FrameRecord(frame_id=frame_id, frame_path=frame_path, gt_path=gt_path, ignore_path=ignore_path)

    def load_frame(self, frame_path: str | Path):
        frame = cv2.imread(str(frame_path), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError(f"Could not read frame: {frame_path}")
        return frame

    def load_gt_mask(self, gt_path: str | Path):
        mask = cv2.imread(str(gt_path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise ValueError(f"Could not read ground-truth mask: {gt_path}")
        return mask

    def normalize_gt_mask(self, mask) -> np.ndarray:
        gray = self._to_gray(mask)
        if self.foreground_values is not None:
            fg = np.isin(gray, self.foreground_values)
        else:
            fg = gray > self.foreground_threshold
        out = np.zeros(gray.shape, dtype=np.uint8)
        out[fg] = 255
        return out

    def get_ignore_mask(self, mask) -> np.ndarray:
        gray = self._to_gray(mask)
        if not self.ignore_values:
            return np.zeros(gray.shape, dtype=bool)
        return np.isin(gray, self.ignore_values)

    def category_for_video(self, video_id: str) -> str:
        return self.get_video(video_id).category

    def name_for_video(self, video_id: str) -> str:
        return self.get_video(video_id).video

    def _ensure_discovered(self) -> None:
        if self._videos:
            return
        if not self.root.exists():
            raise FileNotFoundError(f"{self.dataset_name} dataset root not found: {self.root}")
        self._videos = {video.video_id: video for video in self._discover_videos()}

    def _discover_videos(self) -> List[VideoRecord]:
        videos: List[VideoRecord] = []
        candidates = [self.root, *[p for p in self.root.rglob("*") if p.is_dir()]]
        seen_dirs = set()
        for seq_dir in candidates:
            resolved = self._resolve_sequence_dirs(seq_dir)
            if resolved is None:
                continue
            frame_dir, gt_dir, ignore_dir = resolved
            key = (frame_dir.resolve(), gt_dir.resolve() if gt_dir else None)
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            rel_parts = self._relative_parts(seq_dir)
            if len(rel_parts) >= 2:
                category, video_name = rel_parts[-2], rel_parts[-1]
            elif len(rel_parts) == 1:
                category, video_name = self.dataset_name, rel_parts[0]
            else:
                category, video_name = self.dataset_name, self.root.name
            video_id = f"{category}/{video_name}"
            videos.append(
                VideoRecord(
                    video_id=video_id,
                    category=safe_name(category),
                    video=safe_name(video_name),
                    frame_dir=frame_dir,
                    gt_dir=gt_dir,
                    ignore_dir=ignore_dir,
                )
            )
        return sorted(videos, key=lambda v: v.video_id)

    def _resolve_sequence_dirs(self, seq_dir: Path) -> Optional[Tuple[Path, Optional[Path], Optional[Path]]]:
        frame_dir = self._first_existing_child(seq_dir, self.frame_dir_names)
        gt_dir = self._first_existing_child(seq_dir, self.gt_dir_names)
        ignore_dir = self._first_existing_child(seq_dir, self.ignore_dir_names)

        if frame_dir is None and self._has_image_files(seq_dir, IMAGE_EXTENSIONS):
            frame_dir = seq_dir
        if gt_dir is None:
            return None
        if frame_dir is None:
            return None
        if not self._has_image_files(frame_dir, IMAGE_EXTENSIONS):
            return None
        if not self._has_image_files(gt_dir, MASK_EXTENSIONS):
            return None
        return frame_dir, gt_dir, ignore_dir

    def _first_existing_child(self, parent: Path, names: Sequence[str]) -> Optional[Path]:
        for name in names:
            candidate = parent / name
            if candidate.is_dir():
                return candidate
        lower = {p.name.lower(): p for p in parent.iterdir() if p.is_dir()}
        for name in names:
            candidate = lower.get(str(name).lower())
            if candidate is not None:
                return candidate
        return None

    def _relative_parts(self, path: Path) -> Tuple[str, ...]:
        try:
            rel = path.relative_to(self.root)
        except ValueError:
            return (path.name,)
        return tuple(part for part in rel.parts if part not in ("", "."))

    @staticmethod
    def _has_image_files(path: Path, extensions: Sequence[str]) -> bool:
        return path is not None and path.is_dir() and any(
            p.is_file() and p.suffix.lower() in extensions for p in path.iterdir()
        )

    @staticmethod
    def _list_files(path: Optional[Path], extensions: Sequence[str]) -> List[Path]:
        if path is None or not path.exists():
            return []
        return _as_path_list(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in extensions)

    @staticmethod
    def _files_by_number(paths: Sequence[Path]) -> Dict[int, Path]:
        out: Dict[int, Path] = {}
        for path in paths:
            num = frame_number(path)
            if num is not None and num not in out:
                out[num] = path
        return out

    @staticmethod
    def _to_gray(mask) -> np.ndarray:
        arr = np.asarray(mask)
        if arr.ndim == 3:
            return arr[:, :, 0]
        return arr


class CDNet2014Adapter(BaseDatasetAdapter):
    dataset_name = "cdnet2014"
    default_frame_dir_names = ("input",)
    default_gt_dir_names = ("groundtruth",)
    default_ignore_dir_names = ()
    default_foreground_values = (255,)
    default_background_values = (0,)
    default_ignore_values = (50, 85, 170)

    def _discover_videos(self) -> List[VideoRecord]:
        videos: List[VideoRecord] = []
        for category_dir in sorted(p for p in self.root.iterdir() if p.is_dir()):
            for video_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
                input_dir = video_dir / "input"
                gt_dir = video_dir / "groundtruth"
                if not input_dir.exists() or not gt_dir.exists():
                    continue
                roi_start, roi_end = self._read_temporal_roi(video_dir / "temporalROI.txt")
                videos.append(
                    VideoRecord(
                        video_id=f"{category_dir.name}/{video_dir.name}",
                        category=safe_name(category_dir.name),
                        video=safe_name(video_dir.name),
                        frame_dir=input_dir,
                        gt_dir=gt_dir,
                        roi_start=roi_start,
                        roi_end=roi_end,
                    )
                )
        return videos

    @staticmethod
    def _read_temporal_roi(path: Path) -> Tuple[Optional[int], Optional[int]]:
        if not path.exists():
            return None, None
        parts = path.read_text(encoding="utf-8").strip().split()
        if len(parts) < 2:
            return None, None
        return int(parts[0]), int(parts[1])
