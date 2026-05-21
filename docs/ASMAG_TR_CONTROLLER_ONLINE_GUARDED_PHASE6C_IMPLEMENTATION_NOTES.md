# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6C Implementation Notes

Date: 2026-05-10

## Scope

Phase 6C applies only to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. It does not modify `ONLINE_CALIBRATED`, P1/P2/P3, `ASMAG_TR_FAST`, or `ASMAG_TR_CONTROLLER`.

## Why Phase 6B-5 Failed

Phase 6B-5 fixed the immediate continuous-pan reuse failure: `REUSE_ACC` dropped to zero and detector-anchor cadence landed in the target band. The remaining smoke failures were still continuousPan and twoPositionPTZCam, which indicates the remaining blocker is PTZ geometry rather than reuse, closed-empty handling, or anchor rate.

## Why Bounded Affine/Scale Is Justified

The existing translation-only phase-correlation trust cannot represent scale, small rotation, or position-switch geometry. Phase 6C therefore adds a bounded geometry trust probe using ORB features and `estimateAffinePartial2D`. This gives limited translation, rotation, and uniform scale evidence without turning the phase into a full motion-estimation system.

Dense optical flow and deep models are not used. The probe is downscaled, feature-limited, gated by PTZ/camera-motion risk, and disabled as a broad non-PTZ behavior path.

## Geometry Trust

The geometry probe logs:

- ORB match and inlier counts;
- inlier ratio;
- affine translation, scale, and rotation;
- residual ratio after affine warping;
- affine-compensated IoU against P3, ACC, and FAST candidate masks;
- whether affine improves over translation-only compensation.

Trust bands are:

- High: strong affine-compensated IoU and low residual.
- Medium: moderate affine-compensated IoU and bounded residual.
- Low: failed probe, low inliers, low IoU, or high residual.

## Action Selection

Geometry trust affects guarded PTZ action selection:

- High geometry trust can allow `LIGHTWEIGHT_MASK_ACC` and tightly gated `REUSE_ACC`.
- Medium geometry trust can allow `LIGHTWEIGHT_MASK_ACC` but blocks reuse.
- Low geometry trust blocks reuse and lightweight P3, then falls back to detector-like anchors.

The previous Phase 6B diagnostics remain intact.

## ContinuousPan Handling

Continuous-pan rules now consult geometry trust. Relaxed continuous-pan trust alone is no longer enough to justify inter-anchor lightweight behavior when the geometry probe is active. `REUSE_ACC` remains blocked unless geometry trust is high.

Closed-empty remains blocked.

## twoPosition / Jump Handling

Position-switch-like frames can be reinforced by geometry evidence:

- probe failure;
- low inlier ratio;
- low geometry trust;
- scale or rotation instability.

These frames use the existing short detector-burst reset path and exit when trust stabilizes.

## BridgeEntry and Non-PTZ Protection

Geometry behavior is suppressed outside confirmed camera motion. Event-only low-light scenes can log suppression, but geometry behavior does not override the existing Phase 5B event safety path.

Non-PTZ motion-comp behavior remains capped by the existing suppression logic.

## Comparison Outputs

Phase 6C adds:

- `geometry_probe_summary.csv`
- `geometry_trust_summary.csv`
- `geometry_action_summary.csv`

These report probe rate, success rate, compute cost, inlier ratio, scale/rotation, residuals, trust bands, action replacements, and per-video deltas versus old online.
