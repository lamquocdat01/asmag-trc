from __future__ import annotations

from datasets.base_adapter import BaseDatasetAdapter


class SBI2015Adapter(BaseDatasetAdapter):
    dataset_name = "sbi2015"
    default_frame_dir_names = (
        "input",
        "Input",
        "frames",
        "Frames",
        "images",
        "Images",
        "imgs",
        "RGB",
    )
    default_gt_dir_names = (
        "groundtruth",
        "GroundTruth",
        "gt",
        "GT",
        "masks",
        "Masks",
        "foreground",
        "Foreground",
    )
    default_ignore_dir_names = ("ignore", "Ignore", "roi", "ROI", "valid", "valid_roi")
    default_foreground_values = (255,)
    default_background_values = (0,)
    default_ignore_values = ()


SBMI2015Adapter = SBI2015Adapter
