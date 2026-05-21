# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 4B Implementation Notes

Date: 2026-05-09

## Why Phase 4 Failed

Phase 4 added useful GMQ diagnostics, but the behavioral arbitration was too blunt. It treated poor lightweight P3 quality as a reason to suppress most P3-like actions, which pushed `PTZ/continuousPan` toward ACC even though the old P3-like online cadence was safer there. The event-continuity guard was also too soft: `nightVideos/bridgeEntry` still emitted CLOSED_EMPTY actions during active event memory, producing event false negatives.

## Split P3 Veto

Phase 4B separates P3 veto scope:

- `gmq_lightweight_p3_veto_active` blocks only lightweight P3 mask reuse/update when P3 mask quality is poor under persistent global motion.
- `gmq_full_p3_veto_active` is reserved for extreme whole-frame, unstable P3 masks.
- `gmq_p3_veto_active` remains as a compatibility aggregate, with `gmq_p3_veto_scope` and `gmq_p3_veto_reason` explaining the active scope.

This keeps full P3 detector refresh and `LEGACY_SAFE_P3_GUARD` available when global motion makes lightweight masks unreliable.

## PTZ-Safe Override

The PTZ-safe override is label-free and does not use video names or CDnet categories. It activates when persistent global-motion risk, candidate disagreement, low activation, and low-trust recent actions indicate that ACC is being selected from misleading quality scores. When active, it forces a capped `LEGACY_SAFE_P3_GUARD` burst instead of letting ACC dominate solely because lightweight P3 was vetoed.

The branch is capped by burst, cooldown, and maximum legacy-safe branch-rate controls so it cannot become an always-on P3 policy.

## ACC Dominance Block

Under persistent global motion, ACC must pass temporal-consistency and background-reliability checks. If ACC is the best quality candidate but fails those checks, Phase 4B logs `gmq_acc_blocked_under_global_motion` and makes the PTZ-safe legacy branch more likely.

## Hard Event-Continuity Veto

For active event memory in low-light risk, Phase 4B blocks closed-empty actions before final action selection when empty evidence is not confident. The hard veto prefers reuse if the event memory is still fresh enough; otherwise it allows a cadence-limited ACC detector refresh, with a lightweight ACC update as a last non-empty fallback.

The relevant logs are `gmq_event_hard_veto_active`, `gmq_event_hard_veto_reason`, `gmq_confident_empty_evidence`, and `closed_empty_blocked_by_event_guard`.

## Ablation Switches

The smoke config now includes:

- `gmq_behavior_enabled`
- `gmq_quality_behavior_enabled`
- `gmq_ptz_safe_override_enabled`
- `gmq_event_hard_veto_enabled`
- `gmq_logging_only`

When `gmq_logging_only` is true, GMQ diagnostics are still computed, but GMQ behavioral overrides are disabled.

## Motion Compensation

Motion compensation remains disabled in Phase 4B. The config placeholders stay present, and `gmq_motion_compensation_enabled` remains false. Dense flow, ECC, and feature matching are postponed until smoke evidence shows that mask-quality arbitration alone cannot recover PTZ scenes.

## Runtime Note

GMQ quality metrics now compute component count, spatial spread, edge touch, and temporal IoU on a downscaled binary mask while retaining original-frame area ratios. This keeps diagnostic coverage while reducing the Phase 4 overhead that pushed aggregate FPS below acceptance.
