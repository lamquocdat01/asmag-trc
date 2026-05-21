# Phase 8A Resume Checkpoint

Updated: 2026-05-11

## Status

Phase 8A status: completed.

This checkpoint was resumed from the previous saved Phase 8A checkpoint. The checkpoint file was read successfully, existing outputs were inspected, the offline dataset builder was rerun, and the research-only model probe was completed.

## Safety Confirmation

- No production pipeline behavior was modified.
- Old `ONLINE_CALIBRATED` was not modified.
- `P1_YOLO_Only`, `P2_FrameDiff`, `P3_MOG2`, `ASMAG_TR_FAST`, and `ASMAG_TR_CONTROLLER` were not modified.
- Frozen CDnet2014 v1.6 outputs were read as existing sources only and were not overwritten.
- No smoke, PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, or BMC experiment was launched.
- No experiment runner was launched.
- Phase 8A remained dataset-building and research-only.

## Source And Output Files

Updated Phase 8A source files:

- `tools/build_phase8a_policy_dataset.py`
- `tools/probe_phase8a_policy_models.py`

Updated Phase 8A docs:

- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8A_DATASET_REPORT.md`
- `docs/PHASE8A_RESUME_CHECKPOINT.md`

Verified output folder:

- `outputs/phase8a_policy_dataset/`

Required outputs present:

- `data_inventory.csv`
- `action_label_mapping.csv`
- `frame_state_dataset.parquet`
- `frame_state_dataset_sample.csv`
- `window_state_dataset.parquet`
- `window_state_dataset_sample.csv`
- `teacher_label_dataset.parquet`
- `oracle_action_dataset.parquet`
- `splits/split_leave_one_video.csv`
- `splits/split_leave_one_category.csv`
- `splits/split_ptz_holdout.csv`
- `splits/split_smoke_vs_targeted.csv`
- `model_probe_results.csv`
- `policy_feature_importance.csv`
- `policy_rule_candidates.txt`

Additional generated QA outputs:

- `missing_feature_report.csv`
- `utility_sanity_by_action.csv`

## Verification Commands Run

```powershell
python -m py_compile tools\build_phase8a_policy_dataset.py tools\probe_phase8a_policy_models.py
python tools\build_phase8a_policy_dataset.py
python tools\probe_phase8a_policy_models.py
```

Outcomes:

- `py_compile` completed successfully.
- Dataset builder completed successfully with `sources=12` and `frame_metric_files=543`.
- Model probe completed successfully and wrote the three required probe outputs.

Implementation note:

- `tools/probe_phase8a_policy_models.py` now defaults to a target-aware 10,000-row research sample. This keeps the required no-argument verification command practical while preserving rare target classes for the probe. It does not affect production behavior.
- Logistic regression now uses a multiclass-capable solver so the required multiclass probe targets are evaluated instead of reported as solver errors.

## Dataset Summary

- frame-level rows: 731,526
- window-level rows: 2,194,578
- teacher-label rows: 100
- oracle-label rows: 122,856
- inventory rows: 543
- videos: 53
- categories: 11
- pipelines: 15

Action bucket distribution:

- `OTHER`: 722,332
- `DETECT_ACC`: 2,940
- `REUSE_ACC`: 1,496
- `CLOSED_EMPTY`: 1,397
- `LIGHTWEIGHT_MASK_P3_FALLBACK`: 1,020
- `FALLBACK_P3_GUARD`: 1,015
- `LIGHTWEIGHT_MASK_ACC`: 928
- `LEGACY_SAFE_P3_GUARD`: 398

Risk class distribution:

- `medium`: 609,827
- `low`: 119,063
- `unsafe`: 2,636

Unsafe action distribution:

- no unsafe reason: 728,890
- `closed_empty_during_event_or_motion`: 1,268
- `reuse_under_low_trust`: 917
- `lightweight_p3_under_ptz`: 429
- `legacy_safe_without_detector_cadence`: 22

## Split Summary

- `split_leave_one_video.csv`: 5,300 rows, 53 folds, video-disjoint leakage check passed.
- `split_leave_one_category.csv`: 1,100 rows, 11 folds.
- `split_ptz_holdout.csv`: 100 rows, 88 train / 12 test.
- `split_smoke_vs_targeted.csv`: 100 rows, 20 train / 80 test.

## Phase 8B Readiness

The dataset is good enough for Phase 8B offline research probes and policy-learning experiments. It is not good enough for deployment by itself. The learned-policy target remains imbalanced and derived from observational/oracle labels, so Phase 8B should keep deterministic safety guards as the authority and treat learned models as research candidates until separately validated.
