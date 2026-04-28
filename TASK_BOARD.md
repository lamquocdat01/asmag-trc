# TASK BOARD - ASMAG-TRC

| ID | Task | Status | Priority | Input | Output | Command | Estimated time | Notes |
|---|---|---|---|---|---|---|---|---|
| G0 | Commit current state | Pending | High | Current repo changes | Git commit | `git status && git add ... && git commit -m "..."` | 5-10 min | Commit after 9C-Fix docs/state are stable. |
| G1 | Finish 9C-Fix | Completed | High | `configs/q2_core_extended_online_controller_p3tuned.yaml` | `outputs/q2_core_extended_online_controller_p3tuned` final reports | `python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml` | Done | Final progress: `128/128` completed; final reports generated. |
| G2 | Edge profiling on PC | Pending | Medium | Selected final pipelines | Edge profiling summary | TBD | 1-2 hrs | Measure latency/FPS/CPU/RAM in controlled PC edge profile. |
| G3 | Full CDnet2014 official-like frame_step=1 | Pending | High | Full CDnet2014 config | Official-like metrics | TBD | Long | Run only after 9C decision; likely needs checkpoint resume. |
| G4 | Confidence-aware reuse | Pending | Medium | YOLO confidence/object scores | Reuse policy variant | TBD | 1-2 days | Improve reuse decisions using confidence decay and uncertainty. |
| G5 | Tracking-assisted reuse | Pending | Medium | Frame-level detections/masks | Tracking reuse variant | TBD | 1-2 days | Add lightweight tracking to reduce reuse misalignment. |
| G6 | Cross-dataset validation | Pending | Medium | Additional dataset | Cross-dataset report | TBD | TBD | Validate generalization outside CDnet2014. |
| G7 | Qualitative examples | Pending | Medium | Selected videos/frames | Figures and overlays | TBD | 2-4 hrs | Show success/failure cases for paper. |
| G8 | Paper manuscript | Pending | High | Final metrics/figures | Manuscript draft | TBD | Multi-day | Position as adaptive inference-control, not SOTA segmentation. |
| G9 | Journal submission preparation | Pending | Medium | Manuscript + artifacts | Submission package | TBD | Multi-day | Format, cover letter, reproducibility checklist. |
