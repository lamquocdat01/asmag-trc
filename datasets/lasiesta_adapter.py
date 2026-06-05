from __future__ import annotations

from pathlib import Path
from typing import List

from datasets.base_adapter import BaseDatasetAdapter, VideoRecord, safe_name, IMAGE_EXTENSIONS, MASK_EXTENSIONS


class LASIESTAAdapter(BaseDatasetAdapter):
    """Adapter for LASIESTA dataset.

    Structure at root level (flat, no category sub-folders):
        <SEQ>/        — frames directly inside (e.g. I_BS_01-1.bmp)
        <SEQ>-GT/     — sibling folder with ground-truth masks

    Category is derived from the sequence name prefix: I_BS_01 -> I_BS.
    """

    dataset_name = "lasiesta"
    default_frame_dir_names = ()
    default_gt_dir_names = ()
    default_ignore_dir_names = ()
    default_foreground_values = (255,)
    default_background_values = (0,)
    default_ignore_values = ()

    def _discover_videos(self) -> List[VideoRecord]:
        videos: List[VideoRecord] = []
        for seq_dir in sorted(p for p in self.root.iterdir() if p.is_dir()):
            name = seq_dir.name
            # Skip GT sibling dirs
            if name.endswith("-GT"):
                continue
            gt_dir = self.root / (name + "-GT")
            if not gt_dir.is_dir():
                continue
            if not self._has_image_files(seq_dir, IMAGE_EXTENSIONS):
                continue
            if not self._has_image_files(gt_dir, MASK_EXTENSIONS):
                continue
            # Derive category: I_BS_01 -> I_BS, O_SM_03 -> O_SM
            parts = name.split("_")
            category = "_".join(parts[:2]) if len(parts) >= 3 else name
            videos.append(
                VideoRecord(
                    video_id=f"{category}/{name}",
                    category=safe_name(category),
                    video=safe_name(name),
                    frame_dir=seq_dir,
                    gt_dir=gt_dir,
                )
            )
        return videos
