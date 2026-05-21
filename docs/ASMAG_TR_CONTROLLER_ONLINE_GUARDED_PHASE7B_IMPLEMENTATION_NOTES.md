# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 7B Implementation Notes

Date: 2026-05-11

## Scope

Phase 7B applies only to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.

Old `ONLINE_CALIBRATED`, `P1_YOLO_Only`, `P2_FrameDiff`, `P3_MOG2`, `ASMAG_TR_FAST`, and `ASMAG_TR_CONTROLLER` are unchanged. Frozen CDnet2014 v1.6 outputs are not used as write targets.

## Why Phase 7A Justified a Ranker

Phase 7A showed that the remaining `continuousPan` issue is primarily wrong action ranking rather than missing closed-empty protection. Closed-empty is already blocked and Phase 6C geometry diagnostics exist, but the guarded stack can still prefer weak actions when PTZ/global-motion trust is low.

The useful teacher signal is deterministic: low-trust PTZ frames need detector-like anchors, while medium/high trust can use quality-gated lightweight ACC behavior. The safest observed replacement for low-utility continuous-pan actions is `FALLBACK_P3_GUARD`.

## Why No Learned Classifier Is Deployed

The shallow policy prototype is diagnostic evidence, not a deployment artifact. The current teacher data is observational and small, and a learned classifier would be harder to rollback, inspect, and constrain in event/non-PTZ edge cases. Phase 7B therefore distills the teacher behavior into explicit rules and logs every ranker decision for future labels.

## Safety Guards

The teacher layer runs only inside PTZ/camera-motion scope:

- confirmed camera motion;
- PTZ/global-motion signature;
- continuous-pan signature;
- position-switch or camera-jump guard.

Before ranking, it blocks unsafe actions:

- no `CLOSED_EMPTY_*` during active event/global motion;
- no `REUSE_ACC` unless trust is real high and reuse age is short;
- no `LIGHTWEIGHT_MASK_P3_FALLBACK` in PTZ low/medium trust;
- no weak `LEGACY_SAFE_P3_GUARD` unless it is actually a detector-like P3 refresh;
- low-trust frames with a stale detector anchor are forced back to detector-like anchors.

## Ranked Action Policy

Low geometry trust ranks:

1. `FALLBACK_P3_GUARD`
2. `DETECT_ACC`
3. `LIGHTWEIGHT_MASK_ACC` only with good ACC quality and a recent anchor
4. detector-like `LEGACY_SAFE_P3_GUARD` only as a last safe option

Medium geometry trust ranks:

1. quality-gated `LIGHTWEIGHT_MASK_ACC`
2. `FALLBACK_P3_GUARD` when an anchor is due
3. `DETECT_ACC` when refresh is due

High geometry trust ranks:

1. quality-gated `LIGHTWEIGHT_MASK_ACC`
2. short-age `REUSE_ACC` only under real high trust
3. `FALLBACK_P3_GUARD` / `DETECT_ACC` when cadence or foreground risk requires an anchor

## continuousPan Handling

For continuous-pan-like frames, low trust is treated as an anchor state. The ranker chooses `FALLBACK_P3_GUARD` or `DETECT_ACC`, blocks `REUSE_ACC`, blocks `LIGHTWEIGHT_MASK_P3_FALLBACK`, and records whether an anchor or inter-anchor action was selected. Medium trust can use `LIGHTWEIGHT_MASK_ACC` only when ACC quality is acceptable and the anchor is recent.

## twoPosition Protection

Phase 6C position-switch handling remains first. If `position_switch_reset_active`, `camera_jump_suspect`, geometry position-switch evidence, or low inlier-ratio geometry is active, continuous-pan teacher behavior is suppressed and a short detector burst is selected. Reuse is invalidated until geometry stabilizes.

## bridgeEntry and Non-PTZ Protection

Event-only low-light scenes such as `bridgeEntry` do not receive the PTZ teacher ranker unless confirmed camera-motion scope is present. The Phase 5B/6C event sanitizer remains responsible for preserving final closed-empty event FN safety.

Stable non-PTZ scenes with no confirmed camera motion log `teacher_non_ptz_suppressed` and do not apply teacher behavior. Existing GMQ/motion-comp non-PTZ suppression remains in force.

## Diagnostics

Phase 7B adds per-frame teacher fields and comparison summaries:

- `teacher_ranker_summary.csv`
- `teacher_action_summary.csv`
- `teacher_safety_guard_summary.csv`
- `teacher_continuous_pan_summary.csv`

These report ranker active and behavior-applied rates, trust distribution, blocked action distribution, selected action before/after distribution, detector-like anchor rate, key action rates, and per-video deltas against old online.

## Validation

Validation sequence for this phase is:

1. `python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py`
2. `python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke.yaml --max-jobs-per-run 8`
3. `python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke`

PTZ-targeted validation remains blocked unless smoke passes.
