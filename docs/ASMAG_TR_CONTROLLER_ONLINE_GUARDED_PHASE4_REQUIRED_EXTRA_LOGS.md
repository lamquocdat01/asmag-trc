# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4 Required Extra Logs

Date: 2026-05-09

This optional document is created because the current Phase 3 logs are strong enough to identify the remaining failure class, but not sufficient to implement or validate GMQ-Guard with high confidence.

## Why More Logs Are Needed

Phase 3 logs include action labels, candidate areas, global motion proxy, low-light guard state, closed-empty count, and refresh counters. They do not yet expose the main Phase 4 quantity: candidate trust. For `PTZ/continuousPan`, area and global motion alone cannot explain why some fallback frames are useful and many are not. For `bridgeEntry`, current logs identify `CLOSED_EMPTY_ACC` event false negatives, but not whether the controller had enough candidate evidence to block those closed-empty frames label-free.

## Required GMQ Columns

| Column | Type | Reason |
|---|---|---|
| `gmq_guard_active` | int | Shows whether Phase 4 arbitration altered behavior. |
| `gmq_action_score` | float | Final multi-objective risk score for chosen action. |
| `gmq_action_reason` | string | Compact reason for action choice. |
| `gmq_global_motion_risk` | float | Replaces saturated binary global-motion behavior with a ranked risk. |
| `gmq_background_reliability` | float | Indicates whether P3/ACC/FAST background candidates are trustworthy. |
| `gmq_p3_quality` | float | Candidate P3 mask trust. |
| `gmq_acc_quality` | float | Candidate ACC mask trust. |
| `gmq_fast_quality` | float | Candidate FAST mask trust. |
| `gmq_best_candidate_mode` | string | Which candidate looked safest before cost/risk scheduling. |
| `gmq_candidate_disagreement` | float | Pairwise disagreement among P3/ACC/FAST masks. |
| `gmq_temporal_consistency` | float | Current best candidate versus previous accepted mask. |
| `gmq_compensated_temporal_consistency` | float | Same after optional global motion compensation. |
| `gmq_spatial_spread` | float | Coarse-grid spread of candidate foreground. |
| `gmq_component_plausibility` | float | Object-like connected-component score. |
| `gmq_whole_frame_motion_penalty` | float | Penalty for background-dominated masks. |
| `gmq_edge_touch_penalty` | float | Penalty for pan/tilt border artifacts. |
| `gmq_event_continuity_risk` | float | Risk that an action breaks an active event. |
| `gmq_reuse_staleness_risk` | float | Risk that reuse preserves stale foreground. |
| `gmq_latency_risk` | float | Risk from recent detector latency or overload. |
| `gmq_p3_veto_active` | int | Whether P3/lightweight P3 was blocked. |
| `gmq_closed_empty_veto_active` | int | Whether closed-empty was blocked. |
| `gmq_legacy_safe_branch_active` | int | Whether guarded approximated old online. |
| `gmq_legacy_safe_reason` | string | Reason for branch entry/exit. |
| `gmq_motion_compensation_enabled` | int | Whether optional compensation was used. |
| `gmq_global_dx` | float | Estimated global x shift if enabled. |
| `gmq_global_dy` | float | Estimated global y shift if enabled. |
| `gmq_motion_residual_ratio` | float | Residual motion after optional compensation. |

## Candidate Mask Quality Diagnostics

Log these for P3, ACC, and FAST if practical:

| Column pattern | Meaning |
|---|---|
| `candidate_{mode}_area_ratio` | Candidate foreground area normalized by image area. |
| `candidate_{mode}_component_count` | Connected components after filtering. |
| `candidate_{mode}_largest_component_ratio` | Largest component share of mask area. |
| `candidate_{mode}_coarse_grid_occupancy` | Fraction of coarse grid cells touched. |
| `candidate_{mode}_edge_touch_ratio` | Fraction of mask touching borders. |
| `candidate_{mode}_temporal_iou` | IoU with previous accepted mask. |
| `candidate_{mode}_quality` | Final per-candidate quality score. |

These values are label-free and can be computed from masks already available in the guarded path.

## Event-Continuity Diagnostics

Add:

- `active_event_memory`
- `frames_since_active_prediction`
- `frames_since_positive_candidate`
- `closed_empty_blocked_by_event_guard`
- `confident_empty_evidence`
- `event_guard_reason`

These columns directly target `bridgeEntry`, where all 11 event false negatives came from `CLOSED_EMPTY_ACC`.

## Motion Compensation Diagnostics

If optional motion compensation is added:

- `motion_compensation_method`
- `motion_compensation_resolution`
- `motion_compensation_success`
- `global_shift_magnitude`
- `global_affine_scale`
- `global_affine_rotation`
- `pre_comp_motion_area_ratio`
- `post_comp_motion_area_ratio`
- `motion_residual_ratio`
- `compensated_prev_mask_iou`

The first implementation should allow these to be disabled so smoke can isolate GMQ arbitration from compensation cost.

## Summary Reports to Add

Per-video summary should include:

- mean/p50/p95 `gmq_global_motion_risk`
- mean/p50/p95 candidate quality by mode
- GMQ action distribution
- P3 veto count and rate
- closed-empty veto count and rate
- legacy-safe branch count and rate
- event-continuity blocked frames
- average GMQ score by action
- average FMeasure by GMQ action
- latency by GMQ action

## Logging Acceptance

Before any full CDnet run:

- Every guarded frame must have non-empty `gmq_action_reason`.
- Candidate quality columns must be finite for available candidate masks.
- P3 veto and legacy-safe branch reasons must be explainable from logged scores.
- Event-continuity guard must show whether `CLOSED_EMPTY_*` was allowed or blocked.
- Timing overhead from GMQ computation must be logged separately if it can affect P95.
