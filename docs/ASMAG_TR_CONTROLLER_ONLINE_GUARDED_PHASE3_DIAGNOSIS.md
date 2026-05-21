# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 3 Diagnosis

Generated after Phase 2 smoke outputs in `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/`.

## Smoke Context

Aggregate Phase 2 smoke result is strong enough globally but blocked by a severe PTZ failure:

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 18.89 | 286.37 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4205 | 0.5953 | 0.4912 | 41.77 | 239.28 |

The guarded controller improved average speed and latency, but `PTZ/continuousPan` collapsed:

| Video | FMeasure | delta vs old online | Event_F1 | Activation | FPS | P95 latency ms |
|---|---:|---:|---:|---:|---:|---:|
| PTZ/continuousPan | 0.0062 | -0.2285 | 0.3421 | 0.09 | 29.23 | 206.58 |
| nightVideos/bridgeEntry | 0.2160 | -0.0237 | 0.9744 | 0.94 | 8.15 | 220.33 |
| PTZ/twoPositionPTZCam | 0.8075 | -0.0032 | 0.8052 | 0.74 | 21.29 | 353.54 |
| dynamicBackground/fountain02 | 0.7007 | +0.0466 | 0.6757 | 0.36 | 51.13 | 221.19 |

## continuousPan Diagnosis

Action distribution for `PTZ/continuousPan`:

| action_label | frames | rate | mean F | mean recall | mean motion disagreement | mean latency ms |
|---|---:|---:|---:|---:|---:|---:|
| REUSE_ACC | 36 | 0.36 | 0.0085 | 0.1756 | 0.168 | 33.81 |
| CLOSED_EMPTY_ACC | 28 | 0.28 | 0.0000 | 0.0000 | 0.155 | 34.67 |
| REUSE_P3_FALLBACK | 14 | 0.14 | 0.0050 | 0.0027 | 0.161 | 32.00 |
| CLOSED_EMPTY_P3_FALLBACK | 13 | 0.13 | 0.0000 | 0.0000 | 0.169 | 33.05 |
| FORCED_REFRESH | 6 | 0.06 | 0.0004 | 0.1667 | 0.163 | 211.70 |
| FALLBACK_P3_POLICY | 2 | 0.02 | 0.0000 | 0.0000 | 0.145 | 214.76 |
| FALLBACK_P3_GUARD | 1 | 0.01 | 0.8658 | 0.9695 | 0.258 | 223.30 |

Key rates and distributions:

| Measure | Value |
|---|---:|
| closed-empty rate | 0.41 |
| reuse rate | 0.50 |
| detector activation rate | 0.09 |
| frames_since_last_detector p50 / p95 / max | 6 / 13 / 14 |
| guard_cooldown_active rate | 0.70 |
| overload_guard_active rate | 0.00 |
| motion_disagreement min / avg / max | 0.104 / 0.163 / 0.273 |
| candidate_P3_gate_open rate | 1.00 |
| motion_density_mean avg / max | 0.286 / 0.424 |
| candidate area avg, FAST / ACC / P3 | 89,020 / 89,020 / 28,615 |

Guard reasons were almost always persistent risk, not transient spikes:

| guard_reason | frames |
|---|---:|
| motion_disagreement+foreground_risk | 91 |
| motion_disagreement+gate_instability+foreground_risk | 6 |
| motion_disagreement | 2 |
| motion_disagreement+gate_instability | 1 |

Interpretation:

- This is primarily a global-motion / PTZ-like detector suppression failure.
- It is also a closed-empty failure: 41% of evaluated frames emitted empty masks while motion disagreement stayed high and the P3 candidate was open on every frame.
- Reuse is not safe in this sequence: 50% reuse produced near-zero FMeasure, consistent with stale masks under camera motion.
- Hard P3 guard is firing too infrequently after Phase 2 cadence control. The one `FALLBACK_P3_GUARD` frame had high FMeasure, which strongly suggests the fallback path itself is useful but over-suppressed.
- Candidate gate features are cached correctly (`cache_hit_gate_features=1.0`), but the cached features indicate widespread motion that Phase 2 currently converts into cooldown/reuse rather than safe refresh.

## bridgeEntry Diagnosis

Action distribution for `nightVideos/bridgeEntry`:

| action_label | frames | rate | mean F | mean latency ms | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| DETECT_ACC | 94 | 0.94 | 0.2380 | 201.55 | 227.14 |
| REUSE_ACC | 6 | 0.06 | 0.2578 | 17.39 | 19.35 |

Other observations:

| Measure | Value |
|---|---:|
| detector activation rate | 0.94 |
| closed-empty frames | 0 |
| reuse confidence min / avg / max | 0.000 / 0.055 / 0.909 |
| motion_disagreement avg / max | 0.0131 / 0.0303 |
| illumination_diff avg / max | 0.0590 / 0.6447 |
| illumination_variance_norm avg / max | 0.0000 / 0.0001 |

Interpretation:

- `bridgeEntry` is not an activation-collapse failure. It is already detector-heavy.
- FMeasure loss is mostly from ACC detection/mask quality in a night scene, not from `CLOSED_EMPTY`.
- Current logs do not include mean illumination/brightness, so low-light must be inferred weakly from category behavior and tiny illumination variance. A Phase 3 low-light proxy should add `illumination_mean`/`illumination_proxy` so this no longer depends on video names.
- A low-risk fix is to permit occasional P3 fallback refresh in low-light risk windows, not to increase activation broadly.

## Comparator Checks

`PTZ/twoPositionPTZCam` already has high activation and acceptable accuracy:

- detector activation rate: 0.74
- closed-empty rate: 0.09
- motion_disagreement avg / max: 0.082 / 0.799
- FMeasure delta vs old online: -0.0032

`dynamicBackground/fountain02` is benefiting from Phase 2 suppression:

- detector activation rate: 0.36
- closed-empty rate: 0.51
- motion_disagreement avg / max: 0.006 / 0.018
- FMeasure delta vs old online: +0.0466

This suggests the Phase 3 escape hatch should require persistent high disagreement and widespread motion. It should not simply reopen the detector for all closed-empty frames.

## Cache / Runtime Diagnosis

Shared gate feature cache appears active:

| Video | cache hit rate | avg gate feature latency ms | max gate feature latency ms |
|---|---:|---:|---:|
| PTZ/continuousPan | 1.00 | 28.97 | 81.31 |
| nightVideos/bridgeEntry | 1.00 | 13.41 | 31.76 |
| PTZ/twoPositionPTZCam | 1.00 | 16.03 | 109.92 |
| dynamicBackground/fountain02 | 1.00 | 10.68 | 27.00 |

The Phase 3 problem is not repeated gate recomputation. The issue is policy/cadence behavior after cached features identify hard motion.

## Phase 3 Root Cause

`PTZ/continuousPan` is a global-motion / PTZ-like failure where Phase 2 latency controls suppress activation too aggressively:

1. Motion disagreement remains high on every frame.
2. P3 candidate gate stays open on every frame.
3. Guard cooldown is active on 70% of frames.
4. Detector activation drops to 9%.
5. Reuse and closed-empty dominate.
6. Reuse is stale under camera motion and closed-empty misses foreground.

`nightVideos/bridgeEntry` is a low-light/night mask-quality issue:

1. Activation is already 94%.
2. No closed-empty run exists.
3. FMeasure remains below old online and far below P3/controller.
4. Occasional P3 fallback under low-light risk is more appropriate than broad activation increases.

## Required Phase 3 Direction

Implement guarded-only escape hatches:

- Add label-free global-motion proxy from motion density, candidate areas, component count, and motion disagreement.
- In global-motion escape mode, prevent long closed-empty runs.
- Enforce a minimum global-motion activation floor using cadence-limited P3 refresh.
- Prefer current lightweight P3 mask over stale reuse during global camera motion.
- Add PTZ-safe P3 fallback cadence rather than per-frame fallback.
- Add low-light telemetry and a cadence-limited night refresh guard.
- Preserve Phase 2 overload and cooldown controls outside these escape conditions.

## Phase 3 Continuation Finding

After the first Phase 3 smoke rerun, the failure mode changed but did not pass acceptance:

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 19.27 | 326.59 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4127 | 0.5880 | 0.4013 | 32.03 | 288.53 |

`PTZ/continuousPan` no longer emits long `CLOSED_EMPTY` runs, but it is still catastrophic:

| action_label | frames | rate | interpretation |
|---|---:|---:|---|
| REUSE_P3_FALLBACK | 60 | 0.60 | stale masks under camera motion |
| LIGHTWEIGHT_MASK_P3_FALLBACK | 15 | 0.15 | non-detector update; low FMeasure |
| FALLBACK_P3_GUARD | 13 | 0.13 | useful but too sparse |
| FALLBACK_P3_POLICY | 6 | 0.06 | useful but too sparse |
| FORCED_REFRESH | 6 | 0.06 | sparse detector refresh |

ContinuousPan metrics in this failed rerun:

| FMeasure | Event_F1 | Activation | FPS | P95 latency ms | closed-empty rate |
|---:|---:|---:|---:|---:|---:|
| 0.0572 | 0.2906 | 0.25 | 14.56 | 302.22 | 0.00 |

The updated diagnosis is that `continuousPan` is now a stale-reuse/global-motion failure rather than a closed-empty failure. `global_motion_proxy` remains 1.0 and motion disagreement stays high while 60% of frames reuse stale P3 masks. The fallback detector works on the earliest global-motion frame, but cadence still suppresses it too often for a continuously panning camera.

`nightVideos/bridgeEntry` also regressed from the Phase 2 state:

| action_label | frames | rate | interpretation |
|---|---:|---:|---|
| DETECT_ACC | 51 | 0.51 | useful detector path |
| CLOSED_EMPTY_ACC | 21 | 0.21 | missed dim foreground |
| REUSE_ACC | 15 | 0.15 | stale/weak masks |
| LIGHTWEIGHT_MASK_ACC | 9 | 0.09 | weak lightweight update |
| FALLBACK_P3_GUARD | 3 | 0.03 | too rare |
| FORCED_REFRESH | 1 | 0.01 | too rare |

BridgeEntry brightness telemetry is now available: mean illumination is about 120, with low motion disagreement and moderate motion density. The configured low-light threshold of 110 is too low, so the low-light guard never activates. The root cause is over-suppression of ACC detector refresh in a dim scene, not global motion.

The next patch should therefore be even narrower:

- Treat persistent high-disagreement, high-density, high-FAST-area motion as a PTZ emergency and allow P3 fallback refresh without normal guard cadence suppression.
- In dim, non-global-motion scenes with moderate motion density, force an ACC detector floor so `bridgeEntry` does not collapse into `CLOSED_EMPTY_ACC` and stale reuse.
- Keep the existing Phase 2 latency controls for all other conditions.

## Phase 3 Final Guarded-Smoke Rerun

The final guarded-only Phase 3 rerun completed without crashes and all requested Phase 3 diagnostic columns were present in the guarded `frame_metrics.csv` files.

Aggregate comparison:

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 18.56 | 405.04 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4476 | 0.5793 | 0.5338 | 37.32 | 262.71 |

Aggregate acceptance is satisfied: FMeasure and Event_F1 are above old online, FPS is above 35, and P95 latency is far below old online plus 30 ms.

`PTZ/continuousPan` remains blocked:

| FMeasure | delta vs old online | Event_F1 | Activation | FPS | P95 latency ms | closed-empty rate | reuse rate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.1226 | -0.1121 | 0.2906 | 0.49 | 12.64 | 346.78 | 0.00 | 0.00 |

Final action distribution for `PTZ/continuousPan`:

| action_label | frames | rate |
|---|---:|---:|
| LIGHTWEIGHT_MASK_P3_FALLBACK | 51 | 0.51 |
| FALLBACK_P3_GUARD | 38 | 0.38 |
| FORCED_REFRESH | 6 | 0.06 |
| FALLBACK_P3_POLICY | 5 | 0.05 |

Final PTZ telemetry:

| Measure | Value |
|---|---:|
| global_motion_proxy mean | 1.000 |
| global_motion_escape_active rate | 0.760 |
| global_motion_refresh_triggered rate | 0.430 |
| ptz_safe_fallback_active rate | 0.760 |
| closed_empty_guard_active rate | 0.000 |

The Phase 3 patch fixed the original `continuousPan` closed-empty and stale-reuse collapse, but it did not recover FMeasure enough. The failure is now a global-motion/PTZ mask-quality and cadence failure: global motion is detected, closed-empty is suppressed, and detector activation rises, but lightweight P3 fallback masks still dominate many frames and the expensive fallback cadence is not accurate enough under continuous camera motion.

`nightVideos/bridgeEntry` improved relative to the earlier failed Phase 3 continuation and now nearly matches old online FMeasure:

| FMeasure | delta vs old online | Event_F1 | Activation | FPS | P95 latency ms | closed-empty rate | reuse rate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.2339 | -0.0058 | 0.9130 | 0.76 | 15.89 | 276.11 | 0.11 | 0.09 |

Final action distribution for `nightVideos/bridgeEntry`:

| action_label | frames | rate |
|---|---:|---:|
| DETECT_ACC | 75 | 0.75 |
| CLOSED_EMPTY_ACC | 11 | 0.11 |
| REUSE_ACC | 9 | 0.09 |
| LIGHTWEIGHT_MASK_ACC | 4 | 0.04 |
| FORCED_REFRESH | 1 | 0.01 |

Final night telemetry:

| Measure | Value |
|---|---:|
| low_light_guard_active rate | 1.000 |
| illumination_proxy mean | 0.0367 |
| night_refresh_triggered rate | 0.210 |
| global_motion_escape_active rate | 0.000 |

The low-light guard is active and the bridgeEntry FMeasure gap shrank to -0.0058 versus old online, but Event_F1 remains below old online by 0.0613.

## Phase 3 Acceptance Decision

Phase 3 does not pass. Aggregate smoke metrics pass, all diagnostics are present, and `bridgeEntry` improved, but `PTZ/continuousPan` remains more than 0.02 below old `ONLINE_CALIBRATED` FMeasure. The guarded pipeline is not safe to advance to targeted CDnet yet.
