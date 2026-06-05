"""
VIRAT Ground Release 2.0 adapter for ASMAG-TRC cross-dataset evaluation.

VIRAT has no pixel-level foreground GT, so gt_path is always None.
Frames are extracted from MP4 to a local _frames_cache/<video>/ directory
on first access; subsequent runs reuse the cached JPEGs via hard-links.

Only efficiency metrics are meaningful: Activation, FPS, Energy/frame.
"""
from __future__ import annotations

import cv2
from pathlib import Path
from typing import Iterator, List, Optional

from datasets.base_adapter import BaseDatasetAdapter, FrameRecord, VideoRecord, safe_name


class VIRATAdapter(BaseDatasetAdapter):
    """Adapter for VIRAT Ground Release 2.0 MP4 videos."""

    dataset_name = "virat"

    def __init__(self, dataset_root: str | Path, config: Optional[dict] = None):
        super().__init__(dataset_root, config)

    def _discover_videos(self) -> List[VideoRecord]:
        max_frames = self._max_frames()
        videos: List[VideoRecord] = []
        for mp4 in sorted(self.root.glob("*.mp4")):
            vid_name = mp4.stem
            parts = vid_name.split("_")
            scene_raw = parts[2] if len(parts) >= 3 else "unknown"
            category = safe_name(f"scene_{scene_raw}")

            cap = cv2.VideoCapture(str(mp4))
            roi_end = None
            if cap.isOpened():
                fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                roi_end = min(fc, max_frames) if max_frames else fc
                cap.release()

            frames_cache = self.root / "_frames_cache" / vid_name
            videos.append(
                VideoRecord(
                    video_id=f"{category}/{vid_name}",
                    category=category,
                    video=vid_name,
                    frame_dir=frames_cache,
                    gt_dir=None,
                    roi_start=1,
                    roi_end=roi_end,
                )
            )
        return videos

    def iter_frames(self, video_id: str) -> Iterator[FrameRecord]:
        video = self.get_video(video_id)
        mp4 = self.root / f"{video.video}.mp4"
        if not mp4.exists():
            return

        frames_dir: Path = video.frame_dir
        frames_dir.mkdir(parents=True, exist_ok=True)

        max_frames = self._max_frames()
        frame_ext = str(self.config.get("frame_ext", ".jpg"))

        cap = cv2.VideoCapture(str(mp4))
        if not cap.isOpened():
            return
        try:
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                if max_frames and frame_idx > max_frames:
                    break
                frame_path = frames_dir / f"in{frame_idx:06d}{frame_ext}"
                if not frame_path.exists():
                    cv2.imwrite(str(frame_path), frame)
                yield FrameRecord(
                    frame_id=frame_idx,
                    frame_path=frame_path,
                    gt_path=None,
                    ignore_path=None,
                )
        finally:
            cap.release()

    def _max_frames(self) -> int:
        v = self.config.get("max_frames_per_video", 500)
        if v in (None, "", "null", "None"):
            return 0
        return int(v)
