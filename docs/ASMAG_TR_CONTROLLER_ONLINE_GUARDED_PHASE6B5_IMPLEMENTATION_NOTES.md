# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6B-5 Implementation Notes

Date: 2026-05-10

## Scope

Phase 6B-5 applies only to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. It does not modify `ONLINE_CALIBRATED`, P1/P2/P3, `ASMAG_TR_FAST`, or `ASMAG_TR_CONTROLLER`.

The phase is a narrow continuous-pan action-selection patch. It does not add affine, scale, ECC, homography, sparse matching, dense optical flow, or new deep models.

## Why Phase 6B-4 Failed

Phase 6B-4 passed the aggregate smoke gates but failed video-level gates:

- continuousPan recovered FPS and P95 but lost FMeasure because relaxed trust allowed too much `REUSE_ACC`.
- twoPositionPTZCam regressed because continuous-pan relaxation and cadence rules still leaked into position-switch-like behavior.
- bridgeEntry preserved final `CLOSED_EMPTY` event safety and remains protected by the event-safe path.

The mining evidence ranked PTZ `REUSE_ACC` as dangerous. Phase 6B-5 therefore treats relaxed continuous-pan trust as sufficient for lightweight ACC only, not reuse.

## Real Trust vs Relaxed Trust

Phase 6B-5 separates continuous-pan trust into three practical bands:

- Real high trust: compensated IoU meets the high threshold and residual is low.
- Relaxed medium trust: continuous-pan signature is active and a detector anchor is recent, but the compensated signal is not truly high.
- Low trust: all other cases.

`REUSE_ACC` is legal only under real high trust. Relaxed medium trust can use `LIGHTWEIGHT_MASK_ACC` when ACC candidate quality is acceptable. Low trust falls back to a detector-like anchor.

## Continuous-Pan Reuse Cap

Continuous-pan `REUSE_ACC` is capped at 0.05 unless real high trust explains it. If a relaxed-trust frame would reuse:

- replace with `LIGHTWEIGHT_MASK_ACC` when ACC quality is acceptable;
- otherwise replace with a detector-like anchor.

The frame logs record reuse blocking, replacement action, reuse rate window, and whether the cap was active.

## Anchor Cadence

The anchor cadence is restored from the Phase 6B-4 aggressive thinning policy:

- detector-like anchor interval: 2 frames;
- target detector-like anchor rate: at least 0.50 and at most 0.60;
- inter-anchor frames prefer `LIGHTWEIGHT_MASK_ACC`;
- `LIGHTWEIGHT_MASK_P3_FALLBACK` remains blocked.

This is intended to land between the Phase 6B-3 detector-heavy behavior and the Phase 6B-4 reuse-heavy behavior.

## Position-Switch Protection

Continuous-pan rules are suppressed when position-switch-like evidence appears:

- position-switch reset is active;
- camera jump is suspected;
- shift instability exceeds the configured threshold.

When suppressed, the Phase 6B-3 position-switch reset logic remains in control with a short detector burst and fast exit path.

## BridgeEntry and Non-PTZ Protection

BridgeEntry event safety is not changed. `CLOSED_EMPTY` remains blocked during active event risk unless the established confident-empty evidence path allows it.

For non-PTZ scenes without confirmed camera motion, continuous-pan rules remain disabled and motion-comp behavior remains suppressed outside event-risk or low-framerate-risk conditions.

## Comparison Outputs

The comparison tool now writes `continuous_pan_policy_summary.csv` with:

- continuous-pan `REUSE_ACC`, `LIGHTWEIGHT_MASK_ACC`, and detector-anchor action rates;
- real high trust and relaxed medium trust rates;
- relaxed-trust reuse blocking rate;
- position-switch suppression rate;
- rolling reuse and detector-anchor windows.

## Deferred Work

Affine and scale-aware compensation remain postponed. If Phase 6B-5 cannot recover continuousPan or twoPositionPTZCam simultaneously, the remaining blocker should be treated as evidence for a later bounded affine/scale phase, not for broadening this patch.
