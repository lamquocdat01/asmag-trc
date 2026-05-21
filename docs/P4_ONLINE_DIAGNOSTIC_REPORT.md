# P4-Online Diagnostic Report

Date: 2026-05-09

Scope: read-only diagnostic of `ONLINE_CALIBRATED` / P4-Online against the frozen ASMAG-TRC v1.6 CDnet2014 evidence. No algorithm code or existing result folders were modified.

## Evidence Inspected

- Implementation: `src/run_experiment.py`, especially `OnlineSceneDifficultyEstimator`, `process_sequence`, `write_official_edge_reports`, and `write_online_controller_diagnostics`.
- Gates: `src/gating/gates.py`, especially `ASMAGPlusGate` and `ASMAGPlusEfficientGate`.
- Policy training: `src/controller/train_online_mode_policy.py`.
- Configs: `configs/full_cdnet2014_official_edge_profile_pc.yaml`, `configs/q2_core_extended_online_controller_calibrated.yaml`, `configs/q2_core_extended_online_controller_p3tuned.yaml`, `configs/q2_core_extended_full_metrics.yaml`.
- Frozen full CDnet2014 evidence: `outputs/full_cdnet2014_official_edge_profile_pc/`.
- Supporting sampled and calibration evidence: `outputs/q2_core_extended_online_controller_calibrated/`, `outputs/q2_core_extended_online_controller_p3tuned/`, `outputs/full_cdnet2014_sampled_full_metrics/`, `outputs/full_cdnet2014_controller_sampled_metrics/`.
- Available result artifacts: `final_main_comparison.csv`, `best_by_metric.csv`, `summary_pareto_metrics.csv`, `per_category_summary.csv`, `per_video_summary.csv`, `summary_by_category.csv`, `summary_by_video.csv`, `summary_edge_metrics.csv`, `summary_edge_energy_metrics.csv`, `frame_runtime_log.csv`, `online_mode_usage_by_video.csv`, `online_scene_difficulty_summary.csv`, per-sequence `frame_metrics.csv`, `edge_profile.csv`, and available ranking/insight files in adjacent runs.

Note: `outputs/full_cdnet2014_official_edge_profile_pc/` does not contain `final_rankings.csv`, `category_wise_insight.csv`, or `video_wise_failure_cases.csv`. Equivalent files exist in adjacent sampled/controller runs, but the official full folder has stronger direct evidence through `per_video_summary.csv`, `per_category_summary.csv`, frame logs, and online mode diagnostics.

## A. Current Global Summary

Source: `outputs/full_cdnet2014_official_edge_profile_pc/final_main_comparison.csv`.

| Pipeline | FMeasure | Event_F1 | mAP50_proxy | Activation | FPS | P95 latency ms | Energy/frame | AE_Score |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| P1_YOLO_Only | 0.5697 | 0.6692 | 0.3085 | 1.0000 | 4.7219 | 291.1175 | 6.2000 | 0.3727 |
| P2_FrameDiff | 0.4934 | 0.5806 | 0.2261 | 0.5987 | 73.9393 | 251.1027 | 4.2936 | 0.4915 |
| P3_MOG2 | 0.5866 | 0.6965 | 0.3145 | 0.8088 | 43.7747 | 291.3274 | 5.7442 | 0.4753 |
| ASMAG_TR_FAST | 0.5363 | 0.6774 | 0.2884 | 0.6636 | 33.0296 | 294.8152 | 5.1449 | 0.4644 |
| ASMAG_TR_CONTROLLER | 0.5939 | 0.7114 | 0.3243 | 0.7710 | 34.2186 | 285.9222 | 5.6021 | 0.4769 |
| ONLINE_CALIBRATED | 0.5718 | 0.7053 | 0.3051 | 0.7502 | 13.3250 | 328.0999 | 5.5126 | 0.4416 |

Global interpretation:

- ONLINE_CALIBRATED is not a competitive replacement for `ASMAG_TR_CONTROLLER` yet. It trails by -0.0221 FMeasure, -0.0061 Event_F1, -0.0192 mAP50_proxy, -20.89 FPS, and +42.18 ms P95 latency.
- It does save activation versus `P3_MOG2` and `ASMAG_TR_CONTROLLER`, but only modestly: -0.0586 vs P3 and -0.0208 vs controller.
- The runtime trade is poor: ONLINE_CALIBRATED is slower than P3 despite slightly lower activation and energy proxy. That points to controller/gate overhead rather than detector calls alone.
- `best_by_metric.csv` confirms the current winners: best accuracy is `ASMAG_TR_CONTROLLER`; fastest, lowest latency, lowest activation, lowest energy, and best AE_Score is `P2_FrameDiff`.

## B. Per-Category Comparison

Source: `outputs/full_cdnet2014_official_edge_profile_pc/per_category_summary.csv`.

`vs_P3`, `vs_FAST`, and `vs_CTRL` are P4-Online FMeasure deltas. Negative means ONLINE_CALIBRATED loses.

| Category | P4 FMeasure | vs P3 | vs FAST | vs Controller | P4 Event_F1 | P4 Activation | P4 P95 ms | P4 FPS |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| turbulence | 0.3274 | -0.1320 | +0.0691 | -0.1320 | 0.5248 | 0.8069 | 340.6525 | 7.5290 |
| lowFramerate | 0.4590 | -0.0306 | +0.0377 | -0.0306 | 0.5011 | 0.8534 | 345.6193 | 5.7099 |
| PTZ | 0.6205 | -0.0288 | +0.0804 | -0.0288 | 0.4551 | 0.8914 | 345.5125 | 6.8642 |
| dynamicBackground | 0.6500 | -0.0201 | +0.0776 | -0.0201 | 0.5285 | 0.8169 | 366.6397 | 10.0410 |
| nightVideos | 0.3875 | -0.0181 | +0.0137 | -0.0181 | 0.5894 | 0.8881 | 323.1651 | 7.1048 |
| shadow | 0.7292 | -0.0119 | +0.0469 | -0.0119 | 0.8617 | 0.5642 | 280.0804 | 26.6524 |
| badWeather | 0.7711 | -0.0133 | +0.0049 | -0.0114 | 0.4842 | 0.6461 | 339.4652 | 8.6091 |
| cameraJitter | 0.6590 | -0.0102 | +0.0493 | -0.0102 | 0.9033 | 0.8982 | 331.5835 | 6.7079 |
| thermal | 0.8272 | +0.0436 | +0.0071 | -0.0064 | 0.9492 | 0.6257 | 312.6140 | 23.8075 |
| intermittentObjectMotion | 0.3292 | +0.0186 | +0.0053 | -0.0008 | 0.9008 | 0.6421 | 342.7710 | 20.2952 |
| baseline | 0.5611 | +0.0117 | +0.0045 | +0.0046 | 0.9693 | 0.6956 | 284.7386 | 15.2373 |

Largest category losses:

- `turbulence` is the clear failure category: -0.1320 FMeasure vs P3/controller.
- `lowFramerate`, `PTZ`, `dynamicBackground`, and `nightVideos` are the next largest losses.
- P4-Online usually beats `ASMAG_TR_FAST`, so the issue is not that the adaptive family is hopeless. The issue is choosing and executing modes in a way that neither preserves P3/controller accuracy nor captures FAST runtime.

## C. Per-Video Failure Analysis

Source: `per_video_summary.csv`, `online_mode_usage_by_video.csv`, `online_scene_difficulty_summary.csv`, and per-video `frame_metrics.csv`.

### Largest FMeasure Drop vs P3_MOG2

| Category | Video | P4 F | Delta vs P3 | Activation | Reuse | FAST | ACC | P3 fallback | Suspected root cause |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|:--|
| turbulence | turbulence2 | 0.2766 | -0.3380 | 0.3777 | 0.2419 | 0.0297 | 0.4154 | 0.5549 | Low activation/missed foreground; hard-scene policy miss |
| dynamicBackground | fountain02 | 0.6942 | -0.1025 | 0.2660 | 0.2160 | 0.1760 | 0.3900 | 0.4340 | Low activation plus mixed modes in dynamic background |
| shadow | backdoor | 0.4261 | -0.0950 | 0.3716 | 0.2005 | 0.3410 | 0.3329 | 0.3260 | Gate closes too often; hard-scene mode split |
| turbulence | turbulence1 | 0.1585 | -0.0822 | 0.9507 | 0.0493 | 0.3638 | 0.0357 | 0.6005 | High activation with poor mask quality; unstable hard scene |
| shadow | cubicle | 0.2093 | -0.0809 | 0.4283 | 0.2557 | 0.2525 | 0.3777 | 0.3698 | Reuse/stale predictions plus weak shadow handling |
| lowFramerate | tramCrossroad_1fps | 0.7692 | -0.0788 | 0.9381 | 0.0619 | 0.0000 | 0.4631 | 0.5369 | High activation without accuracy gain |
| turbulence | turbulence0 | 0.1965 | -0.0781 | 0.9465 | 0.0330 | 0.2954 | 0.0000 | 0.7046 | High activation; hard-scene policy miss |
| nightVideos | bridgeEntry | 0.3048 | -0.0540 | 0.9507 | 0.0473 | 0.2798 | 0.0000 | 0.7202 | High activation; night video mask quality issue |
| PTZ | twoPositionPTZCam | 0.8321 | -0.0512 | 0.8368 | 0.0733 | 0.1472 | 0.1492 | 0.7035 | P3 fallback not dominant enough for PTZ |
| lowFramerate | tunnelExit_0_35fps | 0.1645 | -0.0438 | 0.7381 | 0.1104 | 0.0915 | 0.2289 | 0.6797 | Runtime-heavy fallback, still weak quality |

### Largest FMeasure Drop vs ASMAG_TR_CONTROLLER

The worst list is nearly identical because the frozen controller maps many hard categories to `P3_MOG2`. The largest controller losses are `turbulence2` (-0.3380), `fountain02` (-0.1025), `backdoor` (-0.0950), `turbulence1` (-0.0822), `cubicle` (-0.0809), `tramCrossroad_1fps` (-0.0788), `turbulence0` (-0.0781), `bridgeEntry` (-0.0540), `twoPositionPTZCam` (-0.0512), and `blizzard` (-0.0491).

### Largest P95 Latency Increase

| Category | Video | P4 P95 ms | P95 vs P3 | P95 vs Controller | Activation | Reuse | FAST | P3 fallback | Suspected root cause |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|:--|
| dynamicBackground | fountain02 | 521.9889 | +331.2507 | +249.8452 | 0.2660 | 0.2160 | 0.1760 | 0.4340 | Triple-gate overhead with low activation |
| cameraJitter | traffic | 399.0922 | +141.8592 | -55.8883 | 0.9791 | 0.0104 | 0.0000 | 0.8644 | High detector activity; hard scene |
| dynamicBackground | fall | 399.3089 | +119.7793 | +124.3672 | 0.9873 | 0.0127 | 0.0566 | 0.9237 | P3-heavy but pays online overhead |
| PTZ | continuousPan | 389.5819 | +116.2181 | +108.9003 | 0.9991 | 0.0000 | 0.0000 | 1.0000 | Pure fallback plus controller overhead |
| turbulence | turbulence0 | 378.7439 | +95.3875 | +93.0190 | 0.9465 | 0.0330 | 0.2954 | 0.7046 | Hard scene with high activation |
| intermittentObjectMotion | tramstop | 364.4476 | +94.3942 | +22.7041 | 0.7453 | 0.2344 | 0.6396 | 0.0835 | FAST/ACC switching overhead |
| shadow | bungalows | 302.2444 | +92.6449 | +91.5072 | 0.5646 | 0.1856 | 0.1934 | 0.5617 | Mixed hard-shadow modes |
| PTZ | twoPositionPTZCam | 382.0915 | +83.6737 | +127.1074 | 0.8368 | 0.0733 | 0.1472 | 0.7035 | Fallback-heavy but not cheap |
| badWeather | wetSnow | 340.5960 | +72.4597 | +57.6282 | 0.7264 | 0.1386 | 0.3039 | 0.6101 | Mixed mode overhead |
| PTZ | intermittentPan | 339.4346 | +71.4536 | +78.7835 | 0.8153 | 0.0730 | 0.1469 | 0.7162 | Fallback-heavy PTZ overhead |

### Highest Activation Without Accuracy Gain

| Category | Video | P4 F | Delta vs Controller | Activation | P95 ms | Reuse | Suspected root cause |
|:--|:--|--:|--:|--:|--:|--:|:--|
| nightVideos | winterStreet | 0.5026 | -0.0110 | 0.9955 | 336.4710 | 0.0045 | P3-heavy but with online overhead |
| dynamicBackground | fall | 0.3810 | -0.0006 | 0.9873 | 399.3089 | 0.0127 | P3-heavy but with online overhead |
| cameraJitter | traffic | 0.7220 | -0.0342 | 0.9791 | 399.0922 | 0.0104 | High activation, no accuracy gain |
| dynamicBackground | boats | 0.8954 | -0.0013 | 0.9785 | 304.3912 | 0.0102 | Near-P3 behavior, no runtime benefit |
| dynamicBackground | fountain01 | 0.0522 | -0.0005 | 0.9758 | 340.1314 | 0.0242 | High activation but very poor mask quality |
| badWeather | skating | 0.6655 | -0.0026 | 0.9723 | 356.9622 | 0.0277 | Almost always active |
| turbulence | turbulence3 | 0.6781 | -0.0295 | 0.9529 | 350.4937 | 0.0457 | High activation, turbulence sensitivity |
| turbulence | turbulence1 | 0.1585 | -0.0822 | 0.9507 | 398.2897 | 0.0493 | Hard scene, poor mask quality |
| nightVideos | bridgeEntry | 0.3048 | -0.0540 | 0.9507 | 377.4860 | 0.0473 | Night video mask quality issue |
| nightVideos | tramStation | 0.6043 | -0.0138 | 0.9492 | 285.5814 | 0.0508 | Small accuracy loss, little activation saving |

### Low Activation Causing Missed Foreground

| Category | Video | P4 F | Delta vs P3 | P4 Recall | Recall vs P3 | Activation | Reuse | Suspected root cause |
|:--|:--|--:|--:|--:|--:|--:|--:|:--|
| turbulence | turbulence2 | 0.2766 | -0.3380 | 0.5445 | -0.2108 | 0.3777 | 0.2419 | Gate closes during true foreground |
| badWeather | blizzard | 0.7729 | -0.0425 | 0.7657 | -0.0346 | 0.3611 | 0.2293 | Low activation and weather motion |
| dynamicBackground | fountain02 | 0.6942 | -0.1025 | 0.7253 | -0.0244 | 0.2660 | 0.2160 | Dynamic background gate miss |
| shadow | backdoor | 0.4261 | -0.0950 | 0.9463 | -0.0233 | 0.3716 | 0.2005 | Shadow scene, stale/closed gate |

### High Reuse / Stale Prediction Risk

| Category | Video | P4 F | Delta vs Controller | Activation | Reuse | FAST | P3 fallback | Suspected root cause |
|:--|:--|--:|--:|--:|--:|--:|--:|:--|
| thermal | lakeSide | 0.6390 | -0.0152 | 0.4152 | 0.4908 | 0.4677 | 0.0007 | Very high reuse; moderate quality loss |
| intermittentObjectMotion | winterDriveway | 0.1033 | +0.0226 | 0.4124 | 0.3718 | 0.5436 | 0.1412 | Reuse high but not main loss vs controller |
| baseline | PETS2006 | 0.1103 | -0.0004 | 0.5827 | 0.3607 | 0.7991 | 0.0011 | FAST/reuse dominated baseline |
| intermittentObjectMotion | sofa | 0.2097 | +0.0032 | 0.6015 | 0.3518 | 0.6633 | 0.0062 | Reuse high, not current accuracy bottleneck |
| intermittentObjectMotion | parking | 0.6889 | -0.0353 | 0.4297 | 0.3383 | 0.2305 | 0.4133 | Reuse/stale masks plus runtime overhead |
| thermal | library | 0.9025 | -0.0152 | 0.5864 | 0.2678 | 0.3669 | 0.1586 | High reuse, small quality loss |
| baseline | office | 0.7866 | -0.0004 | 0.6705 | 0.2667 | 0.6962 | 0.1094 | Reuse acceptable here |
| shadow | cubicle | 0.2093 | -0.0809 | 0.4283 | 0.2557 | 0.2525 | 0.3698 | Stale masks in shadow scene |
| turbulence | turbulence2 | 0.2766 | -0.3380 | 0.3777 | 0.2419 | 0.0297 | 0.5549 | Gate/reuse misses foreground |
| thermal | corridor | 0.9123 | -0.0066 | 0.5013 | 0.2418 | 0.2995 | 0.0677 | Reuse high, low risk |

Mode switching is also a failure signal. With calibrated `use_hysteresis: false`, the worst switch rates are `backdoor` 9.31 switches/100 frames, `turbulence2` 8.57, `fountain02` 8.50, and `cubicle` 7.97. These overlap heavily with the largest accuracy-loss videos.

## D. Runtime Overhead Diagnosis

Primary runtime cause: repeated gate computation before mode selection.

- In `process_sequence`, online mode creates three independent gates: `P3_FALLBACK` as `MOG2Gate`, `ACC` as `ASMAGPlusEfficientGate`, and `FAST` as another `ASMAGPlusEfficientGate`.
- For every evaluated online frame, the code runs `for mode, online_gate in online_gates.items()` before choosing `controller_selected_mode`.
- Each efficient gate inherits `ASMAGPlusGate`, which computes FrameDiff, MOG2, KNN, morphology, connected components, motion statistics, and smoothed gate state.
- Therefore one online frame can pay for approximately three MOG2 passes, two KNN passes, two frame-diff passes, two component filtering passes, plus the learned policy, before any detector call.
- `resize_width_for_gating: 320` exists in the official config, but no implementation use was found in `src/run_experiment.py` or `src/gating/gates.py`; gates appear to run at full frame resolution.

Quantitative runtime evidence:

| Pipeline | Avg latency ms | P95 ms | Avg FPS | Activation | Reuse | Energy/frame |
|:--|--:|--:|--:|--:|--:|--:|
| ASMAG_TR_CONTROLLER | 178.7004 | 285.9222 | 34.2186 | 0.7710 | 0.1116 | 5.6021 |
| ONLINE_CALIBRATED | 208.8260 | 328.0999 | 13.3250 | 0.7502 | 0.1339 | 5.5126 |
| ASMAG_TR_FAST | 167.3159 | 294.8152 | 33.0296 | 0.6636 | 0.2710 | 5.1449 |
| P3_MOG2 | 186.6627 | 291.3274 | 43.7747 | 0.8088 | 0.0000 | 5.7442 |

Online frame latency by selected mode:

| Selected mode | Frames | Mean latency ms | P95 latency ms | Detector rate | Reuse rate |
|:--|--:|--:|--:|--:|--:|
| ACC | 29297 | 103.5424 | 291.6507 | 0.3315 | 0.3755 |
| FAST | 34887 | 206.9395 | 342.3893 | 0.7434 | 0.2377 |
| P3_FALLBACK | 55942 | 235.8763 | 358.5841 | 0.8446 | 0.0000 |

Runtime root-cause assessment:

- Rolling feature computation: moderate cost from per-frame pandas-free feature updates, but not likely the dominant cost.
- Repeated MOG2/FrameDiff/KNN extraction: dominant. The online path computes all candidate gates, not just the selected one.
- Controller logic overhead: nontrivial but secondary to repeated gates.
- CSV/logging overhead: large files exist, but per-frame `latency_ms` is measured before end-of-sequence CSV writes. Logging affects wall-clock run time more than reported P95 latency.
- Fallback path overhead: major. P3 fallback still pays online telemetry/gate overhead, so fallback is slower than plain P3.
- Unnecessary detector calls: significant. Online detector activation is 0.7502 globally and 0.8446 inside P3 fallback mode, so detector savings are too small.
- Mode switching instability: significant. The calibrated official config disables hysteresis.
- Missing caching: major. Gate masks/features are not shared across ACC/FAST/P3 candidate gates.
- Per-frame Python loops: present around gate execution, feature assembly, object metrics, and progress update; secondary compared with OpenCV background subtractors.
- High-cost visual/debug operations: disabled in official config, so not a current runtime cause.

## E. Accuracy Failure Diagnosis

The accuracy loss is not uniform. ONLINE_CALIBRATED is near controller on many videos, but fails hard on specific scenes where the controller would use P3 fallback or where reuse/low activation disrupts recall.

Main accuracy causes:

- Too much non-P3 behavior in hard scenes. The controller maps `PTZ`, `cameraJitter`, `dynamicBackground`, `lowFramerate`, `nightVideos`, `shadow`, `turbulence` to `P3_FALLBACK`, but the learned online policy frequently mixes FAST/ACC into these categories. Example: `turbulence2` uses only 55.49 percent P3 fallback and loses -0.3380 FMeasure vs P3/controller.
- Weak calibrated policy target. `train_online_mode_policy.py` trains on pseudo labels from category policy, not on per-video or per-frame outcome. The selected logistic regression policy reaches only 0.687 mode accuracy and 0.552 macro F1 on validation.
- P3 fallback recall is incomplete in the policy. Validation confusion shows true `P3_FALLBACK` frames predicted as `FAST` 465 times and `ACC` 960 times.
- Calibration feature mismatch. Feature importance is dominated by `illumination_variance` at 0.497, far above direct motion disagreement features. That can misclassify hard dynamic or shadow scenes where illumination does not explain segmentation difficulty.
- Motion disagreement is not a hard guard. In the calibrated path, `calibrated_mode` overrides the handcrafted `force_p3` route, so disagreement is a feature, not a safety trigger.
- Gate closing during slow or noisy foreground. `turbulence2`, `blizzard`, `fountain02`, and `backdoor` show low activation plus recall loss.
- Stale reuse risk. `cubicle`, `parking`, and `turbulence2` have enough reuse to plausibly preserve obsolete masks during changing foreground.
- Dynamic background, shadow, night, and turbulence remain weak. These categories are exactly where a simple motion gate can confuse background motion, illumination changes, and true foreground.
- Mode switching instability. Calibrated `use_hysteresis: false` allows frame-level switching; the highest switch-rate videos overlap with largest losses.

## F. Top 10 Proposed Improvements

Full detail is also provided in `docs/P4_ONLINE_TOP10_IMPROVEMENTS.md`.

| Rank | Improvement | Problem addressed | Expected FMeasure | Event_F1 | Activation | Runtime | Risk | Likely files/functions | Rerun required | Validation command |
|--:|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| 1 | Shared gate feature cache | Repeated MOG2/KNN/FrameDiff per frame | Neutral to slight up | Neutral | Neutral | Large FPS/P95 gain | Medium | `process_sequence`, `ASMAGPlusGate` | Yes | `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc_p4_v1_7.yaml` |
| 2 | Hard P3 guards for disagreement and hard categories | Under-escalation in hard scenes | Medium up | Medium up | Up | P95 may rise unless cache lands | Low-medium | `OnlineSceneDifficultyEstimator.update` | Yes | Same new v1.7 config |
| 3 | Restore hysteresis/min stable frames for calibrated mode | Mode switching instability | Medium up | Small/medium up | Neutral/down | P95 smoother | Low | config, `OnlineSceneDifficultyEstimator` | Yes | Same new v1.7 config |
| 4 | Train policy on empirical per-video winners | Pseudo-label mismatch | Medium/high up | Medium up | Depends | Depends | Medium | `train_online_mode_policy.py` | Yes | Train policy, then rerun P4-only |
| 5 | Low-activation foreground safety refresh | Gate closes during true foreground | Medium up on failures | Medium up | Slight up | Slight P95 cost | Low | `ASMAGPlusEfficientGate`, reuse branch | Yes | Same new v1.7 config |
| 6 | Reuse age and decay rules by scene | Stale masks | Small/medium up | Small up | Slight up | Slight cost | Low | reuse branch in `process_sequence` | Yes | Same new v1.7 config |
| 7 | Use resized gate masks then upscale | Full-resolution gate overhead | Neutral/slight down unless tuned | Neutral | Neutral | Large FPS/P95 gain | Medium | `gating/gates.py` | Yes | Same new v1.7 config |
| 8 | Make fallback cheap | P3 fallback slower than P3 | Neutral | Neutral | Neutral | Large P95 gain | Medium | online gate path in `process_sequence` | Yes | Same new v1.7 config |
| 9 | Per-category safety profile | One policy cannot fit all categories | Medium up | Medium up | Depends | Depends | Low | config, estimator thresholds | Yes | Same new v1.7 config |
| 10 | Add latency/action breakdown logs | Attribution gaps | No direct effect | No direct effect | No direct effect | Enables focused optimization | Low | frame rows, edge profile | Smoke only for logging; full after algorithm change | `python src/run_experiment.py --config configs/cdnet_smoke_test.yaml` |

## G. Recommended P4-Online v1.7 Upgrade Plan

Must-have:

- Add a shared per-frame gate feature cache so online mode does not recompute MOG2/KNN/FrameDiff for every candidate mode.
- Add hard safety overrides for high FD/MOG or KNN/MOG disagreement, low activation with rising FN risk proxies, and categories/videos known to need P3 fallback.
- Re-enable calibrated hysteresis with `min_stable_frames` and a switch budget. Do not allow frame-by-frame policy flipping in the official run.
- Run v1.7 into a new output folder. Do not overwrite frozen `full_cdnet2014_official_edge_profile_pc`.

Should-have:

- Train a new policy using empirical winners or cost-sensitive targets: maximize `FMeasure/Event_F1` subject to activation/runtime budgets.
- Add per-category or per-scene policy priors. Dynamic background, turbulence, PTZ, night, and shadow should have stronger fallback bias.
- Implement explicit low-activation forced refresh and reuse decay.

Optional:

- Downscale gate computation to the configured `resize_width_for_gating`, then upscale masks carefully.
- Add compact mode-switch dampening reports and per-mode latency summaries to the output folder.
- Add a P4-only official config so full validation can run without redoing frozen baselines.

Risky / do not implement yet:

- Replacing MOG2/KNN with an entirely new background model before v1.7. That changes too much at once.
- Retuning detector or YOLO weights. Current failures are mostly controller/gate behavior, not detector model selection.
- Aggressive activation cuts before accuracy is recovered. Runtime matters, but the current blocker is competitiveness.

Recommended validation sequence:

1. Smoke: one or two known failure videos (`turbulence2`, `fountain02`, `backdoor`) in a new output folder.
2. Six-category calibrated rerun using the existing q2 extended scope, again into a new experiment name.
3. Full CDnet2014 P4-only v1.7 official run into a new folder.
4. Only after P4 v1.7 clears thresholds should LASIESTA, SBI2015, and BMC be run.

## H. Missing Information Request

The available logs are strong enough to diagnose the main failure modes, but insufficient for precise per-frame causal attribution and micro-optimization. A separate required-logs file is provided at `docs/P4_ONLINE_REQUIRED_EXTRA_LOGS.md`.

Most important missing details:

- Explicit per-frame action label: `DETECT`, `REUSE`, `FALLBACK_P3`, `FORCED_REFRESH`, `CLOSED_EMPTY`.
- Latency breakdown: gate feature extraction, policy prediction, detector inference, morphology/filtering, metrics/logging.
- Candidate mode outputs: gate open, mask area, score, detector decision, and estimated cost for FAST/ACC/P3 before final selection.
- Reuse diagnostics: source frame, age, IoU/change proxy, stopped reason, and whether reuse later caused FP/FN.
- Mode-switch reason: policy, hysteresis, hard guard, emergency fallback, category prior.
- Resize/cache diagnostics: whether masks were computed once, at what resolution, and reused by which modes.

## Bottom Line

P4-Online can be improved with low-risk changes, but the first v1.7 target should be both accuracy and runtime because the current problems are coupled. Runtime is bad primarily because the online path computes too much before choosing a mode; accuracy is bad because the calibrated policy under-escalates or switches in hard scenes. The smallest competitive v1.7 is: shared gate cache, hard fallback guards, restored hysteresis, and empirical policy retraining or per-category safety priors.

Delay LASIESTA/SBI2015/BMC full runs until P4-Online v1.7 is ready. Running them now would propagate a known weak online baseline and likely force a second round of expensive cross-dataset runs.
