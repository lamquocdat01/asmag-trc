# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 6A Targeted Diagnosis

Research-only diagnosis for the targeted CDnet failure of `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.

No source code, configs, thresholds, or frozen outputs were modified for this diagnosis.

## Executive Summary

Phase 5B passed smoke but failed targeted CDnet because the smoke fix was too narrow. The closed-empty leak was solved for `PTZ/continuousPan`, but targeted PTZ videos expose a broader global-motion generalization failure: the guarded controller is still deciding between detector refresh, P3 fallback, ACC, lightweight masks, and reuse using risk signals that do not measure camera-motion compensation or true candidate trust.

The dominant failure is not simply under-activation. Under-activation contributes, especially in `continuousPan`, `intermittentPan`, low-framerate videos, and night videos, but `zoomInZoomOut` shows the deeper issue: closed-empty is zero and event F1 is unchanged, yet FMeasure collapses from old online 0.9243 to guarded 0.2065. Lightweight P3 and reuse are not safe substitutes for detector-like P3 behavior under zoom/scale motion.

The next phase should not retune the existing GMQ thresholds. Phase 6B should add a small motion-compensation probe and a compensated trust estimator, then restrict GMQ behavioral changes outside scenes where the compensation/risk signals justify them. Dense optical flow remains too heavy; a downscaled phase-correlation probe is the lowest-risk first step, with a zoom/scale residual flag for `zoomInZoomOut`-like scenes.

## Table 1: Targeted Aggregate Comparison

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 ms |
|---|---:|---:|---:|---:|---:|
| P3_MOG2 | 0.5448 | 0.7279 | 0.8511 | 35.12 | 407.49 |
| ASMAG_TR_CONTROLLER | 0.5420 | 0.7232 | 0.8253 | 37.43 | 400.53 |
| ONLINE_CALIBRATED | 0.5021 | 0.7069 | 0.7741 | 11.63 | 429.21 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4533 | 0.6972 | 0.4822 | 26.25 | 330.90 |

Targeted failed because guarded FMeasure is 0.0488 below old online, guarded Event_F1 is 0.0098 below old online, and PTZ category FMeasure drops from old online 0.5815 to guarded 0.3088.

## Targeted Failure Root Cause

Phase 5B solved the smoke-specific symptom but not the underlying PTZ/global-motion problem.

Primary root causes:

1. The current GMQ quality score often ranks ACC above P3 in PTZ scenes even when ACC/lightweight behavior is not the most accurate final policy.
2. P3 lightweight quality is treated as evidence against P3-like behavior, but targeted PTZ often needs full detector/P3 cadence, not lightweight P3 masks.
3. Activation is too low for PTZ and low-framerate scenes that need frequent refreshes.
4. Lightweight masks and reuse have very low mean frame F under sustained camera motion.
5. The controller lacks a label-free measurement of whether previous masks can be aligned to the current frame.
6. The same global-motion GMQ behavior spills into camera jitter, dynamic background, night, and low-framerate videos, causing non-PTZ regressions.

## Table 2: PTZ Per-Video Comparison

| PTZ video | Old F | Guard F | Delta F | Old Event | Guard Event | Guard Act | Guard FPS | P95 ms | Closed-empty |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| zoomInZoomOut | 0.924 | 0.206 | -0.718 | 0.773 | 0.773 | 0.510 | 24.46 | 364.2 | 0.000 |
| intermittentPan | 0.355 | 0.168 | -0.187 | 0.847 | 0.760 | 0.320 | 27.37 | 324.4 | 0.170 |
| continuousPan | 0.235 | 0.121 | -0.113 | 0.291 | 0.291 | 0.330 | 18.75 | 334.0 | 0.000 |
| twoPositionPTZCam | 0.812 | 0.740 | -0.073 | 0.803 | 0.792 | 0.610 | 23.07 | 340.7 | 0.040 |

## PTZ Per-Video Diagnosis

### zoomInZoomOut

Main cause: zoom/scale camera motion plus wrong lightweight/detector arbitration.

Evidence:

- Guarded FMeasure is 0.2065 vs old online 0.9243.
- Event_F1 is unchanged at 0.7730, so the failure is mask quality, not event detection.
- Closed-empty is 0.00, so the Phase 5B kill switch is not the limiting factor.
- Old online is effectively P3 fallback on 97% of frames.
- Guarded chooses `LIGHTWEIGHT_MASK_P3_FALLBACK` on 47% of frames with mean F 0.353 and `LEGACY_SAFE_P3_GUARD` on 38% with mean F 0.393.
- Full detector-like actions are rare but high quality: `FALLBACK_P3_GUARD` mean F 0.939, `DETECT_ACC` mean F 0.959, `FALLBACK_P3_POLICY` mean F 0.976.
- GMQ best candidate is ACC on 95% of frames even though the controller needs detector-like behavior.

Interpretation: phase-correlation translation may not be enough. Zoom/scale needs at least a scale/affine residual cue, or a conservative detector floor when shift-only compensation is unreliable.

### intermittentPan

Main cause: intermittent camera jumps, too little PTZ emergency behavior, closed-empty/reuse leaks, and sparse detector cadence.

Evidence:

- Guarded FMeasure is 0.1676 vs old online 0.3548.
- Event_F1 drops from old online 0.8466 to 0.7600.
- Activation is 0.32 vs old online 0.84.
- Closed-empty is 0.17 and `CLOSED_EMPTY_ACC` has mean F 0.0.
- `LIGHTWEIGHT_MASK_P3_FALLBACK` is 35% of frames with mean F 0.082.
- `REUSE_ACC` is 10% of frames with mean F 0.005.
- `DETECT_ACC`, `LIGHTWEIGHT_MASK_ACC`, and `FALLBACK_P3_GUARD` are much better when selected.
- PTZ emergency fires only on 9% of frames, and the PTZ closed-empty kill switch does not fire.

Interpretation: this is not a continuous-pan signature; it is a jump/intermittent-pan signature. Hysteresis around detected camera jumps and a detector floor are more important than broad lightweight fallback.

### continuousPan

Main cause: persistent pan with under-activation and unsafe lightweight P3 substitution.

Evidence:

- Guarded FMeasure is 0.1215 vs old online 0.2347.
- Closed-empty is 0.00, so the smoke leak remains fixed.
- Activation is only 0.33 vs old online 1.00.
- `LIGHTWEIGHT_MASK_P3_FALLBACK` is 67% of frames with mean F 0.021.
- `LEGACY_SAFE_P3_GUARD` is 29% of frames with mean F 0.078.
- `FALLBACK_P3_GUARD` is only 3% of frames but has mean F 0.485.
- GMQ vetoes P3 on 94% of frames and ranks ACC as best candidate on 96% of frames.

Interpretation: Phase 5B fixed closed-empty but reintroduced sparse detector cadence. Continuous pan likely needs shift-compensated temporal consistency plus a detector/P3 floor, not more lightweight P3 masks.

### twoPositionPTZCam

Main cause: position-switch cadence and stale reuse, not broad GMQ emergency failure.

Evidence:

- Guarded FMeasure is 0.7396 vs old online 0.8123.
- Activation is 0.61 vs old online 0.91.
- Closed-empty is 0.04.
- `REUSE_ACC` is 20% of frames with mean F 0.021.
- `DETECT_ACC` is 26% of frames with mean F 0.655 and `LIGHTWEIGHT_MASK_ACC` is 12% with mean F 0.741.
- Old online uses P3 fallback on 79% of frames.
- PTZ emergency never fires.

Interpretation: this scene should not receive a heavy continuous-pan emergency policy everywhere. It needs position-switch detection, reuse invalidation after a jump, and a modest activation floor.

## Table 3: PTZ Action Distribution and Mean F by Action

| Video | Action | Rate | Mean F | Yolo rate | Reuse rate |
|---|---|---:|---:|---:|---:|
| zoomInZoomOut | LIGHTWEIGHT_MASK_P3_FALLBACK | 0.47 | 0.353 | 0.00 | 0.00 |
| zoomInZoomOut | LEGACY_SAFE_P3_GUARD | 0.38 | 0.393 | 1.00 | 0.00 |
| zoomInZoomOut | FALLBACK_P3_GUARD | 0.06 | 0.939 | 1.00 | 0.00 |
| zoomInZoomOut | DETECT_ACC | 0.03 | 0.959 | 1.00 | 0.00 |
| zoomInZoomOut | FALLBACK_P3_POLICY | 0.03 | 0.976 | 1.00 | 0.00 |
| intermittentPan | LIGHTWEIGHT_MASK_P3_FALLBACK | 0.35 | 0.082 | 0.00 | 0.00 |
| intermittentPan | CLOSED_EMPTY_ACC | 0.17 | 0.000 | 0.00 | 0.00 |
| intermittentPan | DETECT_ACC | 0.14 | 0.747 | 1.00 | 0.00 |
| intermittentPan | LEGACY_SAFE_P3_GUARD | 0.13 | 0.211 | 1.00 | 0.00 |
| intermittentPan | REUSE_ACC | 0.10 | 0.005 | 0.00 | 1.00 |
| intermittentPan | LIGHTWEIGHT_MASK_ACC | 0.06 | 0.902 | 0.00 | 0.00 |
| continuousPan | LIGHTWEIGHT_MASK_P3_FALLBACK | 0.67 | 0.021 | 0.00 | 0.00 |
| continuousPan | LEGACY_SAFE_P3_GUARD | 0.29 | 0.078 | 1.00 | 0.00 |
| continuousPan | FALLBACK_P3_GUARD | 0.03 | 0.485 | 1.00 | 0.00 |
| continuousPan | FORCED_REFRESH | 0.01 | 0.000 | 1.00 | 0.00 |
| twoPositionPTZCam | DETECT_ACC | 0.26 | 0.655 | 1.00 | 0.00 |
| twoPositionPTZCam | FALLBACK_P3_POLICY | 0.22 | 0.427 | 1.00 | 0.00 |
| twoPositionPTZCam | REUSE_ACC | 0.20 | 0.021 | 0.00 | 1.00 |
| twoPositionPTZCam | LIGHTWEIGHT_MASK_ACC | 0.12 | 0.741 | 0.00 | 0.00 |
| twoPositionPTZCam | FALLBACK_P3_GUARD | 0.06 | 0.291 | 1.00 | 0.00 |

Old online action distributions where logged:

| Video | Old online dominant actions |
|---|---|
| zoomInZoomOut | P3_FALLBACK 0.97, ACC 0.03 |
| intermittentPan | ACC 0.52, P3_FALLBACK 0.46, FAST 0.02 |
| continuousPan | P3_FALLBACK 1.00 |
| twoPositionPTZCam | P3_FALLBACK 0.79, ACC 0.21 |

## Table 4: GMQ Score Summary by PTZ Video

| Video | P3 q mean/p50/p95 | ACC q mean/p50/p95 | Disagree mean/p95 | BG rel mean/p95 | Temporal mean/p95 | Legacy | P3 veto | PTZ emerg | Kill | FSLD p50/p95/max | Best mode |
|---|---|---|---|---|---|---:|---:|---:|---:|---|---|
| zoomInZoomOut | 0.505/0.465/0.698 | 0.602/0.596/0.718 | 0.376/0.456 | 0.512/0.780 | 0.062/0.390 | 0.380 | 0.740 | 0.280 | 0.000 | 1/18/22 | ACC 0.95 |
| intermittentPan | 0.540/0.514/0.798 | 0.553/0.549/0.783 | 0.287/0.657 | 0.614/0.974 | 0.149/0.500 | 0.130 | 0.440 | 0.090 | 0.000 | 8/22/27 | ACC 0.55 |
| continuousPan | 0.503/0.488/0.595 | 0.594/0.589/0.651 | 0.463/0.519 | 0.452/0.468 | 0.073/0.157 | 0.290 | 0.940 | 0.220 | 0.100 | 6/21/22 | ACC 0.96 |
| twoPositionPTZCam | 0.665/0.703/0.814 | 0.677/0.737/0.824 | 0.232/0.625 | 0.720/0.907 | 0.081/0.335 | 0.050 | 0.100 | 0.000 | 0.010 | 1/17/22 | ACC 0.78 |

Key GMQ finding: the current quality score is not calibrated for PTZ. ACC is selected as best candidate in 95-96% of `zoomInZoomOut` and `continuousPan`, despite severe FMeasure collapse. Temporal consistency is extremely low in the same videos, which should override raw candidate quality.

## Motion-Compensation Need Assessment

| Video | Runtime motion class | Shift compensation likely help | Scale/affine likely needed | Diagnosis |
|---|---|---:|---:|---|
| continuousPan | translation-like continuous pan | High | Low/medium | Phase correlation can estimate global shift and improve temporal IoU/reuse validity. |
| intermittentPan | intermittent pan/jump | Medium | Medium | Need jump detection and hysteresis; shift helps during stable segments but not abrupt changes. |
| zoomInZoomOut | zoom/scale | Low/medium | High | Shift-only cannot explain radial expansion; need residual/scale cue and detector floor. |
| twoPositionPTZCam | position switch | Medium | Medium | Need reuse invalidation after switch and cautious activation floor. |

Motion compensation should be used as a probe and trust feature first. It should not be a mandatory warp in all frames.

## Table 5: Severe Non-PTZ Regression Diagnosis

| Video | Delta F vs old | Event delta | Guard act | Reuse | Closed-empty | GMQ pattern | Diagnosis |
|---|---:|---:|---:|---:|---:|---|---|
| lowFramerate/turnpike_0_5fps | -0.258 | -0.066 | 0.510 | 0.130 | 0.100 | P3 fallback top, lazy GMQ 0.94 | Low-framerate cadence floor too low; sparse frames make reuse/lightweight unsafe. |
| lowFramerate/tramCrossroad_1fps | -0.172 | -0.031 | 0.560 | 0.190 | 0.140 | DETECT/REUSE/CLOSED_EMPTY mix | Low-framerate event continuity and closed-empty policy too weak. |
| dynamicBackground/canoe | -0.167 | 0.000 | 0.564 | 0.077 | 0.000 | Legacy 0.308, P3 veto 0.397 | Dynamic background over-classified as global-motion risk; lightweight P3 degrades pixel F. |
| cameraJitter/badminton | -0.160 | -0.036 | 0.394 | 0.324 | 0.070 | Reuse-heavy, GMQ active broadly | Camera-jitter motion needs compensation/reuse invalidation, not PTZ emergency. |
| nightVideos/winterStreet | -0.135 | 0.000 | 0.480 | 0.400 | 0.000 | Reuse-heavy, some emergency | Low-light pixel mask quality and reuse staleness. |
| nightVideos/busyBoulvard | -0.087 | +0.029 | 0.420 | 0.440 | 0.060 | Reuse-heavy | Event okay, pixel mask quality/activation low. |
| cameraJitter/sidewalk | -0.081 | +0.013 | 0.543 | 0.222 | 0.049 | P3 veto 0.247, PTZ emergency 0.049 | Camera-jitter compensation needed; PTZ logic should be narrower. |
| shadow/busStation | -0.078 | +0.030 | 0.400 | 0.330 | 0.150 | Closed-empty/reuse | Shadow scene needs active-event/closed-empty guard, not global-motion branch. |
| nightVideos/bridgeEntry | -0.071 | 0.000 | 0.580 | 0.350 | 0.000 | Event guard held | Event fixed, pixel F still low from activation/reuse cadence. |

## General Hard-Scene Diagnosis

PTZ:
The controller lacks a reliable distinction between raw frame motion and alignable camera motion. It also lacks a detector floor for zoom/scale and jump-like PTZ signatures.

Camera jitter:
These scenes resemble PTZ in raw global-motion signals but need jitter compensation and reuse invalidation, not full PTZ emergency behavior.

Dynamic background:
GMQ can treat widespread water/tree motion as global-motion risk. This creates P3 veto and legacy-safe behavior where the old dynamic background strengths should be preserved.

Low frame rate:
Sparse sampling makes stale reuse and closed-empty especially risky. The controller needs a frame-rate-aware cadence floor rather than PTZ logic.

Night:
Event continuity works after Phase 5/5B, but pixel-level masks still degrade when reuse dominates. The night guard should protect refresh cadence for active events and low-contrast masks.

Shadow:
Some shadow videos lose pixel F through low activation, reuse, and closed-empty, even when Event_F1 improves. Shadow-specific over-suppression must be watched before full CDnet.

## Why Cadence/Activation Alone Is Not Enough

Cadence alone could improve `continuousPan` and `intermittentPan`, where activation is plainly too low. It cannot explain `zoomInZoomOut`, where the few detector-like actions are excellent but lightweight and legacy-safe selections dominate the frame budget with poor mask quality. A blind activation increase would also threaten FPS and P95.

The missing mechanism is compensated candidate trust:

- If previous and current frames can be aligned with a simple global shift, reuse and temporal IoU become meaningful.
- If residual motion remains high after shift, lightweight/reuse should be distrusted.
- If scale/affine residual is high, zoom-like scenes should use a detector floor and avoid shift-only confidence.
- If camera-motion signals are absent, GMQ behavior should stay narrow and Phase 3 fast path should dominate.

## Final Recommendation

Implement Phase 6B as a narrow, motion-compensation-informed trust layer:

1. Add downscaled phase-correlation global shift probe.
2. Log shift magnitude, shift confidence, compensated residual motion ratio, and compensated temporal IoU.
3. Use compensated trust to invalidate stale reuse and low-quality lightweight masks.
4. Add a PTZ detector floor for persistent camera-motion risk, especially when compensation residual is high.
5. Add a zoom/scale suspicion flag from poor shift residual plus radial/widespread area changes; do not attempt heavy affine in the first bundle.
6. Restrict GMQ behavioral changes outside PTZ/camera-jitter-like risk; keep diagnostics but avoid broad legacy/P3 behavior in dynamic background and low-framerate scenes.

Full CDnet remains blocked. The next validation should be smoke first, then PTZ-targeted only, then the full targeted set if PTZ passes.

## Phase 6 Direction Answers

1. Can targeted failure be fixed by cadence/activation only?
   No. Cadence and activation are necessary for `continuousPan`, `intermittentPan`, low-framerate, and night regressions, but `zoomInZoomOut` shows that detector-like actions are high quality while lightweight/reuse actions dominate and fail. The controller needs compensated trust, not only more activation.

2. Is motion compensation now required?
   Yes, as a lightweight diagnostic and trust mechanism. It should start as risk-gated phase correlation, not dense flow.

3. Should Phase 6 implement downscaled phase correlation first?
   Yes. It is the lowest-cost way to distinguish alignable translation-like camera motion from high-residual zoom/jump/dynamic-background motion.

4. Does `zoomInZoomOut` require affine/scale compensation?
   Probably eventually, but not in the first Phase 6B bundle. First use shift residual plus widespread area-change signals to detect zoom/scale suspicion and force a detector floor.

5. Should the PTZ branch use a detector floor instead of candidate lightweight masks?
   Yes under persistent camera-motion risk, high residual, or poor compensated temporal IoU. Lightweight masks remain useful only when compensated trust is high.

6. Should non-PTZ GMQ be restricted?
   Yes. Dynamic background, low-framerate, night, and shadow losses show that broad GMQ behavior can overreach. Behavioral GMQ should require strong camera-motion or event-risk evidence; otherwise diagnostics can be logged while Phase 5B fast path remains active.

7. Which changes are low-risk?
   Risk-gated phase-correlation diagnostics, compensated temporal IoU logging, reuse invalidation when compensation confidence is low, non-PTZ GMQ restriction, and explicit PTZ-targeted validation.

8. Which changes are high-risk?
   Dense optical flow, always-on ECC, affine/scale warping, making P3 full cadence universal, or increasing detector activation globally across all targeted videos.

9. What is the smallest Phase 6B implementation bundle?
   Implement risk-gated phase correlation, compensated temporal IoU/residual diagnostics, a PTZ detector floor when residual risk is high, stale-reuse/lightweight invalidation, non-PTZ GMQ restriction, and a separate low-framerate cadence guard. Then validate smoke, PTZ-targeted only, and only afterwards the full targeted set.
