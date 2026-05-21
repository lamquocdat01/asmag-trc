# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6B Implementation Plan

This is the proposed next implementation plan after Phase 6A targeted diagnosis. It is not implemented here.

## Smallest High-Impact Bundle

Phase 6B should implement a narrow motion-compensation-informed safety layer while preserving the pipeline ID:

`ASMAG_TR_CONTROLLER_ONLINE_GUARDED`

Recommended bundle:

1. Add risk-gated downscaled phase-correlation shift probe.
2. Add compensated temporal IoU and residual motion diagnostics.
3. Add PTZ/camera-motion detector floor when residual risk is high.
4. Invalidate stale reuse and lightweight masks when compensation fails.
5. Restrict GMQ behavioral changes outside PTZ/camera-jitter-like camera-motion risk.
6. Add low-framerate cadence floor as a separate guarded rule, not PTZ logic.
7. Keep dense flow, ECC, and affine/scale compensation disabled.

## Architecture Diagram

```text
Frame t-1, Frame t
        |
        v
Cheap risk gate
  |-- low risk ---------------------------> Phase 5B fast path
  |
  '-- high camera-motion / event risk
        |
        v
Downscaled phase-correlation probe
        |
        +--> shift confidence, dx/dy, residual ratio
        +--> compensated temporal IoU for P3/ACC/FAST/reuse
        |
        v
Compensated GMQ trust update
        |
        +--> translation-like pan: allow compensated reuse only if safe
        +--> high residual / zoom suspicion: detector floor
        +--> jump/position switch: invalidate reuse and refresh
        |
        v
Existing GMQ + PTZ emergency + final sanitizer
        |
        v
Final action
```

## Proposed Config Flags

Add under `online_controller_guarded` only:

```yaml
motion_comp_probe_enabled: true
motion_comp_behavior_enabled: true
motion_comp_method: "phase_correlation_shift"
motion_comp_resize_width: 160
motion_comp_min_response: 0.20
motion_comp_max_residual_ratio_for_reuse: 0.35
motion_comp_min_compensated_iou_for_reuse: 0.20
motion_comp_max_shift_px_for_fast_path: 12

ptz_detector_floor_enabled: true
ptz_detector_floor_min_activation: 0.70
ptz_detector_floor_interval_frames: 2
ptz_detector_floor_max_extra_refreshes_per_100_frames: 35
ptz_detector_floor_high_residual_interval_frames: 1

zoom_scale_suspect_enabled: true
zoom_scale_residual_threshold: 0.55
zoom_scale_area_change_threshold: 0.20
zoom_scale_force_detector_floor: true

gmq_restrict_non_ptz_behavior_enabled: true
gmq_non_ptz_behavior_requires_camera_motion: true
gmq_dynamic_background_escape_enabled: true

low_framerate_cadence_guard_enabled: true
low_framerate_min_activation_floor: 0.70
low_framerate_max_reuse_age_frames: 1
```

The exact values should be treated as starting points for smoke/targeted validation, not as final thresholds.

## New Diagnostics

Required diagnostics:

- `motion_comp_probe_active`
- `motion_comp_compute_ms`
- `motion_comp_dx`
- `motion_comp_dy`
- `motion_comp_shift_mag`
- `motion_comp_response`
- `motion_comp_residual_ratio`
- `motion_comp_temporal_iou_p3`
- `motion_comp_temporal_iou_acc`
- `motion_comp_temporal_iou_fast`
- `motion_comp_temporal_iou_final`
- `motion_comp_reuse_safe`
- `motion_comp_failure_reason`
- `zoom_scale_suspect`
- `camera_jump_suspect`
- `ptz_detector_floor_active`
- `ptz_detector_floor_reason`
- `reuse_invalidated_by_motion_comp`
- `lightweight_invalidated_by_motion_comp`
- `gmq_non_ptz_behavior_restricted`
- `low_framerate_cadence_guard_active`

## Decision Flow

```text
if low risk:
    use Phase 5B fast path

if camera-motion risk:
    compute phase-correlation shift
    compute residual ratio and compensated temporal IoU

    if shift confidence high and residual low:
        allow compensated reuse/lightweight only if compensated IoU is acceptable

    if residual high or compensated IoU poor:
        block stale reuse
        block lightweight P3/ACC as final action unless candidate quality is clearly high
        enforce PTZ detector floor

    if residual high and area changes are widespread:
        set zoom_scale_suspect
        prefer detector floor/full P3-like branch

if low-framerate risk:
    apply low-framerate cadence guard
    keep detector/event floor separate from PTZ emergency

apply existing Phase 5B final sanitizer
```

## Table 7: Recommended Phase 6B Changes and Expected Metric Impact

| Change | Expected FMeasure impact | Expected Event_F1 impact | Expected FPS/P95 impact | Risk |
|---|---|---|---|---|
| Risk-gated phase correlation probe | Positive on PTZ/cameraJitter | Neutral/positive | Small cost if gated | Low/medium |
| Compensated temporal IoU | Positive by reducing stale reuse | Positive in PTZ/jitter | Minimal | Low |
| PTZ detector floor on high residual | Strong positive on PTZ | Positive | FPS drop in PTZ | Medium |
| Zoom/scale suspect detector floor | Strong positive on zoomInZoomOut | Neutral | Local latency cost | Medium |
| Restrict non-PTZ GMQ behavior | Positive on dynamic/night/low-framerate losses | Neutral/positive | Improves FPS | Low |
| Low-framerate cadence guard | Positive on turnpike/tramCrossroad | Positive | Moderate local cost | Medium |
| Dense flow/ECC/affine now | Unknown | Unknown | High cost | High, postpone |

## Validation Stages

Smoke must be rerun before any targeted validation because Phase 6B changes final action arbitration and reuse behavior.

Recommended stages:

1. Smoke CDnet only.
2. PTZ-targeted subset only.
3. Full targeted CDnet set.
4. Full CDnet only if full targeted passes.
5. Cross-dataset only after full CDnet validates.

## Table 8: Phase 6 Validation Gate

| Stage | Videos | Pass criteria | Stop conditions |
|---|---|---|---|
| Smoke | Existing 8 smoke videos | Aggregate F/Event >= old online, FPS >= 30, P95 <= old + 30 ms, continuousPan closed-empty <= 0.02 | continuousPan collapse, bridgeEntry event FNs return |
| PTZ-targeted | continuousPan, intermittentPan, zoomInZoomOut, twoPositionPTZCam | PTZ category F gap vs old online materially reduced; no PTZ video worse than old by >0.05 unless documented | zoomInZoomOut or continuousPan remains catastrophic |
| Full targeted | Existing targeted config | Aggregate F/Event/FPS/P95 pass old-online gates; no severe unexplained regressions | aggregate F below old, Event below old, GMQ branch everywhere |
| Full CDnet | All CDnet only after targeted pass | Category-balanced improvement and no severe PTZ/night/dynamic regression | PTZ/category collapse or latency collapse |
| Cross-dataset | LASIESTA/SBI/BMC only after full CDnet | Generalization holds without CDnet-specific overfit | any major dataset collapse |

## Acceptance Criteria for Phase 6B Smoke

Hard:

- No crashes.
- All Phase 5B diagnostics remain present.
- New motion-compensation diagnostics present.
- Aggregate smoke FMeasure >= old online.
- Aggregate smoke Event_F1 >= old online.
- Aggregate smoke FPS >= 30, preferably >= 35.
- Aggregate smoke P95 <= old online + 30 ms.
- `continuousPan` FMeasure no worse than old online by more than 0.02.
- `continuousPan` closed-empty <= 0.02.
- `bridgeEntry` final CLOSED_EMPTY event FN count remains 0.

## Acceptance Criteria for PTZ-Targeted Only

Hard:

- `zoomInZoomOut` no longer catastrophic; target FMeasure gap vs old online <= 0.10 for first PTZ-targeted gate.
- `continuousPan` FMeasure no worse than old online by more than 0.02 and closed-empty <= 0.02.
- `intermittentPan` closed-empty event FNs reduced substantially and Event_F1 gap shrinks.
- `twoPositionPTZCam` does not regress vs Phase 5B targeted.
- PTZ detector floor does not become 100% on every PTZ frame unless explicitly justified by residual risk.

## Stop Conditions

Stop before full targeted if:

- Smoke fails.
- Motion compensation diagnostics are missing.
- Motion-comp probe runs on nearly every frame and FPS collapses.
- `continuousPan` regresses again.
- `zoomInZoomOut` remains below old online by more than 0.30 FMeasure after detector floor.
- `intermittentPan` closed-empty/reuse event failures remain high.
- Non-PTZ GMQ overreach worsens in smoke.

Stop before full CDnet if:

- Full targeted aggregate FMeasure remains below old online.
- Full targeted Event_F1 remains below old online.
- Any PTZ video remains a severe unexplained regression.
- Dynamic background or low-framerate losses worsen.

## Exact Command Plan

After implementation, run only:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke
```

If smoke passes, create a PTZ-targeted config/output folder and run only PTZ videos:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_ptz_targeted.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_ptz_targeted
```

Only after PTZ-targeted passes should the existing full targeted set be rerun. Full CDnet remains blocked until full targeted passes.

## Phase 6B Final Direction

Targeted failure cannot be solved safely by cadence/activation alone. Phase 6B should implement downscaled phase correlation first as a gated diagnostic and trust signal, plus a conservative detector floor when compensation fails. Affine/scale compensation should be postponed unless `zoomInZoomOut` remains severe after the residual-based detector floor.
