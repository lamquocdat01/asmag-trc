# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6B-4 Implementation Notes

Date: 2026-05-10

Phase 6B-4 is a narrow continuous-pan cadence and trust-calibration patch for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.

## Why Phase 6B-3 Failed Narrowly

Phase 6B-3 passed the aggregate smoke gates, but continuousPan stayed more than 0.02 below old `ONLINE_CALIBRATED`. The main blocker was not closed-empty safety. It was cadence: compensated trust stayed low on most frames, so PTZ thinning rarely activated and `LEGACY_SAFE_P3_GUARD` remained dominant. That preserved safety but kept FPS low and pushed P95 latency high.

## Continuous-Pan Signature

Phase 6B-4 adds a label-free runtime signature for stable continuous camera motion. It requires persistent confirmed camera motion, a stable rolling translation direction and magnitude, no active position-switch reset, no zoom/scale detector-floor suspicion, unsafe closed-empty context, and no confident empty evidence.

The signature logs:

- `continuous_pan_signature_active`
- `continuous_pan_signature_reason`
- `continuous_pan_shift_stability`
- `continuous_pan_blocked_by_position_switch`
- `continuous_pan_blocked_by_zoom_scale`

## Trust Relaxation

The normal trust-band logic is still the default. For continuous-pan frames only, a recent detector-like anchor plus stable shift trend can relax low trust into medium trust even when absolute compensated IoU is below the normal medium threshold. This is allowed only when the previous accepted mask exists, residual is bounded, response is acceptable, closed-empty is not trusted, and no position-switch or zoom/scale block is active.

This lets the existing medium/high-trust thinning path operate on stable pan segments without loosening trust globally.

## Anchor Cadence

Phase 6B-4 replaces legacy-safe every-frame behavior with detector-like anchors every configured interval. Detector-like actions are still kept as anchors, but inter-anchor frames can be thinned when the continuous-pan signature and relaxed trust are active.

The anchor cadence logs:

- `continuous_pan_anchor_cadence_active`
- `continuous_pan_anchor_due`
- `continuous_pan_anchor_action`
- `continuous_pan_inter_anchor_action`
- `continuous_pan_legacy_safe_rate_window`
- `continuous_pan_legacy_safe_thinned`

## Inter-Anchor LIGHTWEIGHT_MASK_ACC

Between anchors, the preferred replacement is `LIGHTWEIGHT_MASK_ACC` when the ACC candidate has enough quality and non-empty mask evidence. `LIGHTWEIGHT_MASK_P3_FALLBACK` is explicitly blocked for continuous-pan inter-anchor frames. `REUSE_ACC` is allowed only for a short window after a detector anchor and only when reuse confidence is acceptable.

## twoPositionPTZCam Protection

Continuous-pan relaxation and anchor cadence are suppressed whenever `position_switch_reset_active` is true or the motion looks like a strong jump rather than stable pan. This preserves the Phase 6B-3 detector-burst reset behavior that recovered twoPositionPTZCam-like scenes.

## Non-PTZ Protection

Continuous-pan rules require confirmed camera motion and PTZ-style context. If camera motion is not confirmed, the rules stay off and the Phase 6B-3 non-PTZ motion-comp suppression remains in charge.

## Why Affine/Scale Remains Postponed

Phase 6B-4 intentionally avoids affine, scale, ECC, homography, sparse matching, dense optical flow, and new deep models. The patch tests whether stable translation evidence plus anchor cadence can recover the continuous-pan smoke blocker before adding heavier motion models.
