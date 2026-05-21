# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6B-3 Implementation Notes

Date: 2026-05-10

Phase 6B-3 is a guarded-only detector-cadence thinning and trust-band action-selection patch for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.

## Why Phase 6B-2 Failed

Phase 6B-2 recovered the main safety failures but remained too detector-heavy. Aggregate guarded FMeasure, Event_F1, and P95 beat `ONLINE_CALIBRATED`, but aggregate FPS stayed below the smoke gate.

The two main cadence failures were:

- `continuousPan`: FMeasure recovered and closed-empty was fixed, but `LEGACY_SAFE_P3_GUARD` occupied most frames.
- `bridgeEntry`: final closed-empty event FNs stayed at zero, but `DETECT_ACC` ran on nearly every frame.

`twoPositionPTZCam` also regressed, indicating that short position-switch-like jumps need a reset burst and quick exit rather than long legacy-safe behavior.

## Trust Bands

Phase 6B-3 adds `motion_comp_trust_band` and `motion_comp_trust_band_reason`.

- `high`: compensated IoU is high, residual is low, response is acceptable, and disagreement is not extreme.
- `medium`: compensated IoU is moderate, residual is not extreme, response is acceptable, and disagreement is not extreme.
- `low`: compensated IoU is low, residual is high, response is low, or candidate disagreement is high.
- `unknown`: no usable motion-compensation probe was active.

Medium and high trust allow cadence thinning; low trust keeps the conservative detector-like path.

## Continuous-Pan Cadence Thinning

When confirmed camera motion is active, trust is medium or high, a previous accepted mask exists, and no position-switch reset is active, repeated `LEGACY_SAFE_P3_GUARD` is thinned.

The replacement preference is:

1. `LIGHTWEIGHT_MASK_ACC` when the ACC candidate is non-empty and compensated IoU clears the lightweight threshold.
2. `REUSE_ACC` when reuse is allowed and compensated IoU clears the reuse threshold.

Detector-like refresh is still retained at a controlled interval, so the branch is thinned rather than removed.

## BridgeEntry Event-Safe Cadence

During active low-light event memory, Phase 6B-3 thins repeated `DETECT_ACC` only when event safety remains protected.

The event-safe path can use `REUSE_ACC` or `LIGHTWEIGHT_MASK_ACC` for short gaps between detector refreshes. `CLOSED_EMPTY` remains blocked during active event risk unless confident empty evidence exists.

## Position-Switch Reset

Phase 6B-3 detects position-switch-like behavior from camera-jump suspicion, low compensated IoU, elevated residuals, and non-continuous global-motion history. It does not hard-code video names.

When active, the reset:

- invalidates old reuse for a short window;
- permits a short detector burst using `DETECT_ACC` or `FALLBACK_P3_GUARD`;
- exits quickly when compensated IoU and residual recover;
- allows fast/lightweight behavior again after reset.

## Non-PTZ Overreach Block

Non-PTZ motion-comp behavior is forced off unless confirmed motion, active event risk, or low-framerate cadence risk justifies it. A rate cap prevents cubicle-like scenes from accumulating broad PTZ-style motion-comp behavior.

## Why Affine/Scale Remains Postponed

This phase intentionally avoids affine, scale, ECC, homography, sparse matching, and dense optical flow. The goal is to recover smoke FPS and reduce unsafe action selection using existing translation-probe evidence and deterministic cadence rules before adding heavier motion models.
