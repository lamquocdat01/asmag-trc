# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6A Motion Compensation Proposal

This document explains why motion compensation is now considered for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` and proposes a staged, lightweight design for Phase 6B.

No implementation is included in this document.

## Why Motion Compensation Is Now Considered

Phase 5B proved that closed-empty enforcement can fix smoke-specific PTZ failure, but targeted CDnet shows that the remaining failure is global-motion generalization. The controller cannot tell whether a candidate mask is bad because foreground is absent, because the background model is unreliable, or because the camera moved and the previous foreground mask is no longer aligned.

The clearest evidence is PTZ:

- `continuousPan`: closed-empty is 0.00, but FMeasure is still 0.1215 vs old online 0.2347.
- `zoomInZoomOut`: closed-empty is 0.00 and Event_F1 is unchanged, but FMeasure collapses from old online 0.9243 to guarded 0.2065.
- `intermittentPan`: activation is 0.32 and closed-empty is 0.17, indicating jump/cadence risk.
- `twoPositionPTZCam`: reuse has mean F 0.021, suggesting stale mask reuse after camera position changes.

Motion compensation should initially be used to estimate trust and residual risk, not to replace the segmentation pipeline.

## Candidate Options

## Table 6: Motion Compensation Option Comparison

| Option | Core idea | Cost | Helps | Weakness | Phase 6B recommendation |
|---|---|---:|---|---|---|
| Downscaled phase correlation shift | Estimate global x/y translation on small grayscale frames. | Low | continuousPan, jitter, stable pan segments | Fails on zoom/scale and large scene changes | Implement first as diagnostic plus trust gate. |
| Sparse feature matching | Track ORB/FAST-like points, estimate shift or affine. | Medium | intermittent pan, two-position switches | Feature-poor/night scenes, more tuning | Defer unless phase correlation is insufficient. |
| ECC alignment | Optimize image warp for translation/affine. | Medium/high | smooth camera motion | Can be slow/unstable under foreground dominance | Defer; consider only after PTZ-targeted evidence. |
| Affine/scale estimate | Estimate translation, rotation, scale. | Medium/high | zoomInZoomOut | More failure modes and latency risk | Add only as a Phase 6C option if zoom remains severe. |
| Dense optical flow | Estimate per-pixel motion. | High | complex motion | Too heavy for edge objective | Avoid for this pipeline. |

## Phase Correlation Shift Option

Proposed first implementation:

1. Convert current and previous frames to grayscale.
2. Resize to a small width, e.g. 160 px.
3. Apply optional blur/windowing to reduce noise.
4. Use phase correlation to estimate global `(dx, dy)` and response confidence.
5. Warp previous accepted mask by `(dx, dy)` at mask resolution.
6. Compute compensated temporal IoU between warped previous mask and candidate masks.
7. Compute residual motion ratio after alignment.

This is label-free and does not use CDnet category names.

Suggested diagnostics:

- `motion_comp_enabled`
- `motion_comp_method`
- `motion_comp_dx`
- `motion_comp_dy`
- `motion_comp_shift_mag`
- `motion_comp_response`
- `motion_comp_residual_ratio`
- `motion_comp_temporal_iou_p3`
- `motion_comp_temporal_iou_acc`
- `motion_comp_temporal_iou_fast`
- `motion_comp_reuse_safe`
- `motion_comp_failure_reason`

## Compensated Temporal IoU

Current temporal consistency is unwarped. In PTZ frames, unwarped IoU can be low even when a candidate mask is stable relative to the moving camera. Conversely, reuse can look plausible by area but be spatially stale.

Compensated temporal IoU should compare:

- warped previous accepted mask vs current P3 candidate
- warped previous accepted mask vs current ACC candidate
- warped previous accepted mask vs current FAST candidate
- warped previous accepted mask vs final selected mask

Use the compensated IoU as a trust feature:

- If compensated IoU improves strongly and residual is low, reuse/lightweight update can be safer.
- If compensated IoU remains low and residual is high, detector refresh should be preferred.
- If shift confidence is low, do not trust reuse based on compensation.

## Residual Motion Ratio

Residual motion ratio should estimate how much frame-difference/motion remains after global shift alignment.

Interpretation:

- Low residual after shift: motion is largely global translation; compensated reuse or lightweight update may be reasonable.
- High residual after shift: scene contains zoom/scale, jump, foreground-dominant motion, turbulence, dynamic background, or poor alignment; detector floor should dominate.
- High residual plus high global-motion risk: do not let ACC or lightweight P3 win solely by raw candidate score.

## Warp Previous Accepted Mask for Reuse

Warping the previous accepted mask can help only when the shift estimate is reliable. Proposed safe policy:

1. Compute shift and residual.
2. If shift confidence is high and residual is low, allow warped reuse candidate.
3. If residual is high, block stale reuse and prefer detector refresh.
4. Never use warped reuse as a broad replacement for detection in active PTZ risk.

Suggested action labels for later implementation:

- `REUSE_COMPENSATED_ACC`
- `REUSE_COMPENSATED_P3`
- `LIGHTWEIGHT_MASK_COMPENSATED`

These labels are optional for Phase 6B; logging the compensation outcome is more important than adding many new actions.

## Zoom/Scale Option

`zoomInZoomOut` is the strongest sign that shift-only compensation may not be sufficient. A downscaled phase-correlation shift can still be useful because its failure residual becomes a zoom/scale risk signal.

Recommended Phase 6B behavior:

- Do not implement full affine/scale compensation yet.
- Add `zoom_scale_suspect` when global-motion risk is high, phase-correlation residual remains high, candidate area changes are coherent/widespread, and compensated temporal IoU is poor.
- Under `zoom_scale_suspect`, avoid lightweight P3/reuse and use a detector floor or full P3/legacy-safe cadence.

Possible Phase 6C if needed:

- Estimate scale using sparse feature matching or log-polar phase correlation.
- Use affine only as a gated diagnostic first.

## Runtime Risks

Risks:

- Phase correlation can be unreliable in low light, foreground-dominant frames, turbulence, and dynamic backgrounds.
- A poor shift estimate can make reuse worse.
- Even downscaled alignment adds CPU cost if computed on every frame.
- Zoom and intermittent jumps may create false confidence if residual is not checked.

Mitigations:

- Compute only under risk-gated conditions.
- Log compute time.
- Require response confidence and residual thresholds before using compensation behaviorally.
- Fall back to detector floor when compensation is uncertain.
- Keep dense optical flow out of scope.

## Expected PTZ Impact

| Video | Expected effect from shift probe | Remaining risk |
|---|---|---|
| continuousPan | Better global-motion recognition, safer reuse invalidation, higher detector/P3 floor; F should recover toward old online. | FPS may drop if detector floor too high. |
| intermittentPan | Detect jumps/resets, invalidate stale reuse, prevent closed-empty after camera changes. | Shift helps only between jumps. |
| zoomInZoomOut | Shift residual should identify zoom/scale as non-translation, forcing detector floor. | Full recovery may need affine/scale later. |
| twoPositionPTZCam | Position switches can be detected through low shift confidence/high residual; reuse can be blocked after switch. | Avoid over-triggering emergency during stable position. |

## Why Dense Optical Flow Should Still Be Avoided

Dense flow conflicts with the deployment goal of `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`:

- It is computationally expensive.
- It adds dependency and tuning risk.
- It may be unstable in night, turbulence, and low-texture frames.
- The current failure only requires global camera-motion trust, not per-pixel flow.

The right next step is a lightweight global compensation probe plus detector-floor arbitration, not a heavy motion model.
