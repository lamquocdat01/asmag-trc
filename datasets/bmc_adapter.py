from __future__ import annotations

from pathlib import Path
from typing import List

from datasets.base_adapter import BaseDatasetAdapter, VideoRecord, safe_name


class BMCAdapter(BaseDatasetAdapter):
    """BMC2012 adapter.

    Supports synth1/ and synth2/ splits where each video has been extracted
    from mp4 pairs to <split>/<video_id>/frames/ and <split>/<video_id>/gt/.
    Real videos (real/) are skipped — they have no pixel-level GT.
    """

    dataset_name = "bmc"
    default_frame_dir_names = ("frames", "input", "Input", "images", "imgs", "RGB")
    default_gt_dir_names = ("gt", "GT", "groundtruth", "GroundTruth", "masks", "foreground")
    default_ignore_dir_names = ("ignore", "Ignore", "roi", "ROI", "valid", "valid_roi")
    default_foreground_values = (255,)
    default_background_values = (0,)
    default_ignore_values = ()

    def _discover_videos(self) -> List[VideoRecord]:
        videos: List[VideoRecord] = []
        for split in ("synth1", "synth2"):
            split_dir = self.root / split
            if not split_dir.is_dir():
                continue
            for video_dir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
                frames_dir = video_dir / "frames"
                gt_dir = video_dir / "gt"
                if not frames_dir.is_dir() or not gt_dir.is_dir():
                    continue
                if not self._has_image_files(frames_dir, (".jpg", ".jpeg", ".png", ".bmp")):
                    continue
                if not self._has_image_files(gt_dir, (".png", ".bmp", ".jpg")):
                    continue
                video_id = f"{split}/{video_dir.name}"
                videos.append(
                    VideoRecord(
                        video_id=video_id,
                        category=safe_name(split),
                        video=safe_name(video_dir.name),
                        frame_dir=frames_dir,
                        gt_dir=gt_dir,
                    )
                )
        return sorted(videos, key=lambda v: v.video_id)


BMC2012Adapter = BMCAdapter
