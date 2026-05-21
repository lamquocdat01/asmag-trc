# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 5B Diagnosis

Date: 2026-05-09

## Scope

This diagnosis inspects the Phase 5 smoke output for the guarded pipeline only. No source behavior was changed before this diagnosis, and no targeted/full/cross-dataset runs were used.

## continuousPan Closed-Empty Leak

`PTZ/continuousPan` has 13 final closed-empty frames in the Phase 5 smoke output. Every leaked frame has the final label:

| action_label | frames |
|---|---:|
| CLOSED_EMPTY_P3_FALLBACK | 13 |

The leak is narrow and consistent:

| Condition on leaked frames | Observation |
|---|---|
| `ptz_emergency_active` | 0 on all 13 frames |
| `global_motion_escape_active` | 1 on all 13 frames |
| `gmq_legacy_safe_branch_active` | 0 on all 13 frames |
| `active_event_memory` | 1 on all 13 frames |
| `final_sanitizer_active` | 0 on all 13 frames |
| `final_action_before_sanitizer` | `CLOSED_EMPTY_P3_FALLBACK` |
| `final_action_after_sanitizer` | `CLOSED_EMPTY_P3_FALLBACK` |
| `gmq_global_motion_risk` | 1.0 on all 13 frames |
| `selected_mode_after_guard` | `P3_FALLBACK` |

The sanitizer allowed these frames because the Phase 5 PTZ post-sanitizer only blocked closed-empty when `ptz_emergency_active=1`. These frames were global-motion escape / P3 fallback frames, but they occurred outside the explicit PTZ emergency burst. The event sanitizer also did not fire because its low-light event-risk condition is intended for bridgeEntry-like scenes, not PTZ/global-motion scenes.

## Candidate Availability

The leaked frames had usable P3 fallback candidate evidence:

- `candidate_P3_quality` ranged from about 0.48 to 0.62.
- `candidate_P3_area_ratio` ranged from about 0.044 to 0.060.
- `motion_disagreement` stayed high, about 0.10 to 0.18.
- `gmq_candidate_disagreement` stayed high, about 0.47 to 0.53.

This indicates the leak was not caused by total candidate absence. It was caused by final action arbitration: a global-motion P3 fallback state was permitted to output closed-empty when lightweight P3 had been vetoed or suppressed.

## Root Cause

Phase 5 recovered `continuousPan` FMeasure by restoring conservative P3-like behavior, but the closed-empty suppression was scoped too tightly to `ptz_emergency_active`. The remaining leak is a final-action enforcement gap:

`global_motion_escape_active=1` + `P3_FALLBACK` + high disagreement can still produce `CLOSED_EMPTY_P3_FALLBACK` after the earlier sanitizer has finished.

## Required Fix

Add a final last-step PTZ closed-empty hard kill switch after all scoring, cadence, reuse, GMQ, PTZ emergency, and event logic. If the final action is `CLOSED_EMPTY_*` in a PTZ/global-motion context, replace it with a non-empty candidate, safe reuse, or capped legacy-safe P3 fallback. This should not retune GMQ broadly and should not change old `ONLINE_CALIBRATED`.
