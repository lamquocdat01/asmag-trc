# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 5 Implementation Notes

Date: 2026-05-09

## Why Phase 4B Failed

Phase 4B detected the right risk signals but still let unsafe actions reach the final output. In `PTZ/continuousPan`, ACC remained the dominant best candidate even while persistent global motion and poor temporal consistency made ACC unreliable. In `nightVideos/bridgeEntry`, event-risk guards fired too weakly and `CLOSED_EMPTY_ACC` still reached final predictions, producing event false negatives.

Phase 4B also kept computing GMQ mask-quality diagnostics on every guarded frame. That preserved observability, but it cost enough runtime to keep aggregate FPS below acceptance.

## GMQ Lazy Evaluation

Phase 5 adds risk-gated GMQ quality computation. Full P3/ACC/FAST quality scoring now runs only when at least one of these cheap pre-checks is true:

- persistent global motion risk is high
- candidate disagreement is high
- low-light active-event risk is high
- recent low-trust action rate is high

Otherwise, the controller uses the Phase 3-style fast path and logs cheap quality defaults. The main logs are `gmq_lazy_eval_active`, `gmq_lazy_eval_reason`, and `gmq_quality_compute_ms`.

## PTZ Emergency Override

The PTZ emergency branch is a conservative label-free override for continuousPan-like signatures. It activates under persistent global motion, high disagreement, ACC instability, and low-trust or low-activation risk. While active it forces `LEGACY_SAFE_P3_GUARD`, blocks ACC selection, blocks lightweight P3, and blocks closed-empty unless the previous latency is beyond the extreme-overload limit.

The branch is capped by burst and cooldown parameters and logs `ptz_emergency_active`, `ptz_emergency_reason`, `ptz_emergency_burst_age`, and `ptz_emergency_forced_action`.

## Final Action Sanitizer

Phase 5 adds a final sanitizer after cadence and GMQ selection but before output is accepted.

For PTZ emergency frames it blocks:

- `CLOSED_EMPTY_*`
- low-confidence `REUSE_*`
- `LIGHTWEIGHT_MASK_P3_FALLBACK`
- ACC final selection

For active low-light event memory it blocks `CLOSED_EMPTY_*` unless empty evidence is confident. It then prefers reuse, cadence-limited `DETECT_ACC`, or acceptable `LIGHTWEIGHT_MASK_ACC`. The sanitizer logs both the planned and rewritten action through `final_action_before_sanitizer`, `final_action_after_sanitizer`, `final_sanitizer_active`, and `final_sanitizer_reason`.

## Rolling Runtime Signature

Phase 5 logs rolling label-free signals:

- `rolling_global_motion_persistence`
- `rolling_acc_dominance_under_global_motion`
- `rolling_low_trust_action_rate`
- `rolling_closed_empty_under_motion_rate`

These are intended to detect continuousPan-like behavior without video names or CDnet category labels.

## Motion Compensation

Motion compensation remains disabled. Dense optical flow, ECC, homography, or feature matching would be Phase 6 work only if Phase 5 still cannot recover PTZ/global-motion scenes while preserving aggregate runtime.

Phase 6 motion compensation should be triggered if smoke shows that:

- PTZ emergency raises activation and removes closed-empty but FMeasure still remains below old online by more than 0.02, or
- P3/ACC/FAST masks remain temporally inconsistent under global motion even with conservative action selection.
