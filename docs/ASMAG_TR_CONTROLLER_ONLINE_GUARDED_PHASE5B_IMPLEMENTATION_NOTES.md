# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 5B Implementation Notes

Date: 2026-05-09

## Why Phase 5 Almost Passed

Phase 5 restored `PTZ/continuousPan` FMeasure to old-online level and fixed `nightVideos/bridgeEntry` closed-empty event false negatives. Aggregate FMeasure, Event_F1, FPS, and P95 latency all cleared the main smoke thresholds.

The remaining blocker was narrow: `continuousPan` still had a 13% closed-empty leak. Those frames were all `CLOSED_EMPTY_P3_FALLBACK` during global-motion escape, not during explicit `ptz_emergency_active` bursts.

## Source of the Leak

The Phase 5 final sanitizer blocked PTZ closed-empty during `ptz_emergency_active`, but global-motion escape frames outside the emergency burst could still end as `CLOSED_EMPTY_P3_FALLBACK`. The leaked frames had high global-motion risk, high disagreement, `global_motion_escape_active=1`, and `selected_mode_after_guard=P3_FALLBACK`.

Candidate evidence was still available: the P3 candidate quality was generally above the new hard-kill minimum. The issue was final action arbitration, not total mask absence.

## PTZ Closed-Empty Hard Kill Switch

Phase 5B adds a guarded-only last-step sanitizer. If the final action is `CLOSED_EMPTY_*` and the frame has a PTZ/global-motion signature, the final output cannot remain closed-empty.

The kill switch is triggered by label-free runtime signals:

- `ptz_emergency_active`
- persistent global-motion risk
- `global_motion_escape_active` with high motion disagreement
- high rolling ACC dominance under global motion
- active legacy-safe branch
- final P3 fallback under global motion

Replacement priority:

1. Use the best non-empty current candidate mask whose quality clears `ptz_closed_empty_replacement_min_quality`.
2. Reuse the previous accepted mask if reuse confidence is not critically low.
3. Use a capped legacy-safe P3 action when cadence override is allowed.
4. Fall back to the least-risk non-empty candidate or last valid prediction.

New diagnostics:

- `ptz_closed_empty_kill_active`
- `ptz_closed_empty_kill_reason`
- `closed_empty_attempted_under_ptz`
- `closed_empty_blocked_under_ptz`
- `closed_empty_replacement_action`
- `closed_empty_replacement_source`
- `closed_empty_replacement_quality`
- `closed_empty_kill_cadence_override_used`

## BridgeEntry Protection

The Phase 5 event-continuity sanitizer remains unchanged. In active low-light event memory, `CLOSED_EMPTY_*` remains blocked unless confident empty evidence is present. The existing event counters remain logged:

- `event_closed_empty_attempt_count`
- `event_closed_empty_blocked_count`
- `event_closed_empty_final_count`

## Motion Compensation

Motion compensation remains disabled. Phase 5B is an enforcement patch, not a mask-registration pass. Motion compensation should be considered only if closed-empty is eliminated and PTZ/global-motion mask quality still fails against old online.

## Targeted CDnet Gate

Phase 5B is safe to proceed to targeted CDnet only if smoke passes all hard gates, especially:

- continuousPan closed-empty <= 0.02
- continuousPan FMeasure within 0.02 of old online
- bridgeEntry final closed-empty event FN count remains 0
- aggregate FPS remains >= 30
- aggregate P95 remains within old online + 30 ms

## Smoke Validation Result

Phase 5B smoke completed without crashes after the P3-first replacement correction.

Key guarded-smoke outcome:

| Metric | ONLINE_CALIBRATED | ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 5B |
|---|---:|---:|
| FMeasure | 0.4155 | 0.4336 |
| Event_F1 | 0.5636 | 0.5835 |
| Activation | 0.6150 | 0.5088 |
| FPS | 23.32 | 37.22 |
| P95 latency ms | 345.11 | 281.68 |

`PTZ/continuousPan` closed-empty was reduced to 0.00 and FMeasure recovered above old online. `nightVideos/bridgeEntry` final closed-empty event FNs remained 0. `PTZ/twoPositionPTZCam` has a small residual FMeasure gap versus old online, about -0.021, and should be watched in targeted CDnet, but it is not a catastrophic regression.
