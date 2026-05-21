# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6B Implementation Notes

Date: 2026-05-09

## Why Targeted Phase 5B Failed

Phase 5B passed smoke by eliminating the `continuousPan` closed-empty leak and preserving the `bridgeEntry` event-continuity fix. Targeted CDnet showed that the remaining failure is broader: PTZ/global-motion mask quality and cadence do not generalize. `zoomInZoomOut`, `intermittentPan`, `continuousPan`, and `twoPositionPTZCam` all need better label-free action trust under camera motion.

The old online path often succeeds in PTZ because it behaves closer to detector/P3 cadence. The guarded path was too willing to substitute lightweight P3, ACC, or reuse when raw motion/global-motion signals were unreliable.

## Implemented Motion-Compensation Probe

Phase 6B adds a guarded-only, risk-gated global translation probe:

- Converts previous and current frames to grayscale.
- Resizes to `motion_comp_resize_width`, default 160 px.
- Applies a light blur and Hanning window.
- Uses OpenCV phase correlation to estimate global `dx`/`dy`.
- Logs response, shift magnitude, residual ratio, and compute time.

The probe is only run when risk evidence is present: persistent camera/global-motion risk, candidate disagreement, recent low-trust actions, low-framerate cadence risk, or likely reuse/lightweight action under motion.

## What Was Not Implemented

Dense optical flow, ECC, homography, affine warp, and scale compensation remain disabled. Phase 6B uses phase correlation only as a lightweight translation probe and trust signal. Zoom/scale is detected through residual risk rather than compensated directly.

## Compensated Temporal IoU and Residual Ratio

When the probe runs, the previous accepted mask is translated by the estimated shift. The controller logs compensated IoU between that warped mask and P3, ACC, FAST, and final selected masks.

Residual ratio is computed by warping the previous grayscale frame and measuring thresholded absolute difference against the current grayscale frame. Low residual plus good response means translation-like motion may be alignable. High residual or low response means reuse/lightweight actions are unsafe and detector cadence should be preferred.

## PTZ Detector Floor

A new PTZ detector floor activates when camera-motion risk is high and motion compensation is unreliable:

- Low phase-correlation response.
- High residual after shift.
- Poor compensated temporal IoU.
- `zoom_scale_suspect`.
- `camera_jump_suspect`.

When cadence allows, the floor forces detector-like P3 behavior through the existing guarded infrastructure and caps extra refreshes per 100 frames.

## Zoom/Scale Suspicion

`zoom_scale_suspect` is label-free. It triggers when camera-motion risk is high, shift residual/response is poor, area changes or disagreement are widespread, and compensated IoU is poor. It is meant to catch `zoomInZoomOut`-like failure without implementing affine or scale compensation.

## Camera Jump Suspicion

`camera_jump_suspect` catches large shifts, low-response/high-residual frames, poor compensated IoU with candidate disagreement, or sudden area/spread changes. It invalidates stale reuse and can temporarily raise detector-floor pressure.

## Non-PTZ GMQ Restriction

Phase 6A showed broad GMQ behavior in non-PTZ videos. Phase 6B adds a label-free restriction signal: GMQ motion branches require camera-motion evidence or event-risk evidence. If that evidence is missing, diagnostics remain available but broad motion-branch behavior is restricted.

## Low-Framerate Cadence Guard

Low-framerate scenes get a separate guard rather than being routed through PTZ logic. If detector gaps grow while activation is below the floor and motion/event evidence is present, reuse is blocked and a cadence-limited ACC detector floor is used.

## New Diagnostics

New per-frame diagnostics include:

- `motion_comp_probe_active`
- `motion_comp_compute_ms`
- `motion_comp_dx`
- `motion_comp_dy`
- `motion_comp_shift_mag`
- `motion_comp_response`
- `motion_comp_failure_reason`
- `motion_comp_temporal_iou_p3`
- `motion_comp_temporal_iou_acc`
- `motion_comp_temporal_iou_fast`
- `motion_comp_temporal_iou_final`
- `motion_comp_reuse_safe`
- `motion_comp_residual_ratio`
- `motion_comp_residual_reason`
- `zoom_scale_suspect`
- `zoom_scale_reason`
- `camera_jump_suspect`
- `camera_jump_reason`
- `reuse_invalidated_by_camera_jump`
- `reuse_invalidated_by_motion_comp`
- `lightweight_invalidated_by_motion_comp`
- `invalidation_reason`
- `ptz_detector_floor_active`
- `ptz_detector_floor_reason`
- `ptz_detector_floor_cadence_allowed`
- `ptz_detector_floor_extra_refresh_count`
- `gmq_non_ptz_behavior_restricted`
- `gmq_non_ptz_restriction_reason`
- `low_framerate_cadence_guard_active`
- `low_framerate_cadence_guard_reason`
- `low_framerate_reuse_blocked`
- `low_framerate_detector_floor_active`

## Validation Run

Validation completed:

1. `python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py` passed.
2. Smoke was run with `configs\asmag_tr_controller_online_guarded_cdnet_smoke.yaml`.
3. Comparison was run with `tools\compare_asmag_tr_controller_online_guarded.py`.
4. PTZ-targeted was not run because smoke failed the Phase 6B gate.
5. Full targeted, full CDnet, LASIESTA, SBI2015, and BMC were not run.

Smoke outcome:

- Guarded aggregate FMeasure fell below old online: `0.4053` vs `0.4155`.
- Guarded aggregate Event_F1 fell below old online: `0.5510` vs `0.5636`.
- Guarded aggregate FPS fell below the smoke floor: `16.95`.
- `PTZ/continuousPan` FMeasure recovered to old-online level and closed-empty stayed at `0.00`, but P95 rose to `546.91 ms`.
- The motion-comp probe and detector-floor logic activated too broadly, including non-PTZ smoke videos, which indicates Phase 6B behavior needs tighter risk gating before PTZ-targeted validation.
