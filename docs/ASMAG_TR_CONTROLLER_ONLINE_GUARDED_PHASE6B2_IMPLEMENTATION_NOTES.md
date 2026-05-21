# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6B-2 Implementation Notes

Date: 2026-05-10

Phase 6B-2 narrows the Phase 6B motion-compensation behavior using the logic-outcome mining results in `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_LOGIC_OUTCOME_ANALYSIS.md`.

## Mining Constraints Applied

- Treat compensated IoU as the primary trust signal.
- Block reuse and lightweight P3 when compensated trust is low or candidate disagreement is high.
- Enforce detector-like refresh only when camera motion is confirmed and trust/cadence has failed.
- Keep GMQ behavioral changes logging-only outside confirmed camera motion, event risk, or low-framerate risk.
- Do not treat `LEGACY_SAFE_P3_GUARD` as automatically safe.
- Preserve the Phase 5B fast path for stable non-PTZ scenes.

## Code Changes

- Added `motion_comp_min_compensated_iou_for_trust`.
- Added per-frame diagnostics for compensated trust and GMQ behavior gating:
  - `motion_comp_best_iou`
  - `motion_comp_compensated_trust_low`
  - `motion_comp_compensated_trust_good`
  - `gmq_motion_branch_allowed`
  - `gmq_confirmed_camera_motion_allows_behavior`
  - `gmq_event_risk_allows_behavior`
  - `gmq_low_framerate_allows_behavior`
- Changed GMQ motion branches so vetoes, ACC blocking, PTZ emergency, legacy-safe override, and global-motion P3 behavior require `gmq_motion_branch_allowed`.
- Changed `gmq_motion_branch_allowed` to require confirmed camera motion, event risk, or low-framerate cadence risk when non-PTZ restriction is enabled.
- Changed PTZ emergency, PTZ override, and legacy-safe behavior to require confirmed camera-motion behavior allowance.
- Changed detector-floor and invalidation decisions to use `compensated_trust_low`.

## Config Changes

The smoke, targeted, and full guarded CDnet configs now expose `motion_comp_min_compensated_iou_for_trust: 0.25`. Targeted and full configs also include the guarded Phase 6B/6B-2 motion-compensation and GMQ restriction flags so validation stages use the same controller semantics.

## Validation Scope

Only syntax and config parsing were verified for this implementation pass. Full CDnet, LASIESTA, SBI, and BMC were not run.
