# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Targeted CDnet Report

## Executive Summary

Targeted CDnet validation completed without crashes, but `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` does not pass the targeted gate.

The run completed 132/132 jobs with 0 failed jobs and wrote only to `outputs/asmag_tr_controller_online_guarded_cdnet_targeted/`. The guarded pipeline remains faster and lower-latency than `ONLINE_CALIBRATED`, but it fails targeted acceptance because aggregate FMeasure and Event_F1 are below old online, continuousPan regressed again in FMeasure, twoPositionPTZCam is below the watch-stop threshold, and additional PTZ scenes show severe regressions.

Full CDnet is not allowed.

## Targeted Video List

All requested targeted videos were available and used.

| Category | Videos |
|---|---|
| badWeather | blizzard, skating, wetSnow |
| cameraJitter | traffic, badminton, boulevard, sidewalk |
| dynamicBackground | fountain01, fountain02, boats, fall, canoe |
| lowFramerate | tramCrossroad_1fps, tunnelExit_0_35fps, turnpike_0_5fps, port_0_17fps |
| nightVideos | bridgeEntry, busyBoulvard, tramStation, winterStreet |
| PTZ | intermittentPan, zoomInZoomOut, continuousPan, twoPositionPTZCam |
| shadow | backdoor, cubicle, bungalows, busStation, copyMachine |
| turbulence | turbulence0, turbulence1, turbulence2, turbulence3 |

Missing videos skipped: none.

## Aggregate Comparison

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 ms |
|---|---:|---:|---:|---:|---:|
| P3_MOG2 | 0.5448 | 0.7279 | 0.8511 | 35.12 | 407.49 |
| ASMAG_TR_CONTROLLER | 0.5420 | 0.7232 | 0.8253 | 37.43 | 400.53 |
| ONLINE_CALIBRATED | 0.5021 | 0.7069 | 0.7741 | 11.63 | 429.21 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4533 | 0.6972 | 0.4822 | 26.25 | 330.90 |

Gate interpretation:

| Gate | Result |
|---|---|
| No crashes | Pass |
| Aggregate FMeasure >= old online | Fail, -0.0488 |
| Aggregate Event_F1 >= old online | Fail, -0.0098 |
| Aggregate FPS >= old online | Pass, +14.62 FPS |
| Aggregate P95 <= old online + 30 ms | Pass, 330.90 <= 459.21 ms |
| No new severe per-video regression below -0.05 FMeasure | Fail, 15 videos |
| Full CDnet allowed | No |

## Per-Category Summary

| Category | Guarded F | Old F | Delta F | Guarded Event | Old Event | Delta Event |
|---|---:|---:|---:|---:|---:|---:|
| PTZ | 0.3088 | 0.5815 | -0.2728 | 0.6540 | 0.6782 | -0.0242 |
| badWeather | 0.6712 | 0.6184 | +0.0527 | 0.7703 | 0.7852 | -0.0148 |
| cameraJitter | 0.5761 | 0.6497 | -0.0737 | 0.9323 | 0.9446 | -0.0123 |
| dynamicBackground | 0.5020 | 0.5382 | -0.0362 | 0.4462 | 0.4502 | -0.0040 |
| lowFramerate | 0.3774 | 0.4607 | -0.0833 | 0.5948 | 0.6247 | -0.0299 |
| nightVideos | 0.3212 | 0.3939 | -0.0727 | 0.8765 | 0.8692 | +0.0073 |
| shadow | 0.5019 | 0.5416 | -0.0398 | 0.6134 | 0.6534 | -0.0401 |
| turbulence | 0.3983 | 0.2432 | +0.1552 | 0.7920 | 0.7472 | +0.0449 |

## Top Gains Vs Old Online

| Category | Video | F_guard | Delta F | Event_guard | Delta Event | FPS_guard | Delta FPS |
|---|---|---:|---:|---:|---:|---:|---:|
| turbulence | turbulence2 | 0.6676 | +0.3583 | 0.7677 | +0.2449 | 65.79 | +41.86 |
| badWeather | blizzard | 0.6666 | +0.1976 | 0.8095 | +0.0595 | 31.69 | +14.13 |
| turbulence | turbulence1 | 0.2447 | +0.1593 | 1.0000 | +0.0000 | 4.52 | -0.46 |
| turbulence | turbulence3 | 0.6490 | +0.1112 | 0.8193 | -0.0557 | 14.88 | +10.54 |
| lowFramerate | tunnelExit_0_35fps | 0.1869 | +0.0842 | 0.9045 | +0.0473 | 39.01 | +27.99 |
| dynamicBackground | fountain02 | 0.7110 | +0.0566 | 0.6667 | -0.0199 | 41.92 | +1.58 |
| lowFramerate | port_0_17fps | 0.0134 | +0.0134 | 0.2812 | -0.0706 | 36.99 | +32.59 |
| nightVideos | tramStation | 0.5746 | +0.0020 | 0.8636 | +0.0000 | 19.00 | +12.53 |
| dynamicBackground | fountain01 | 0.0401 | +0.0009 | 0.3051 | +0.0000 | 18.73 | +14.85 |
| badWeather | skating | 0.5700 | +0.0005 | 0.6250 | +0.0043 | 12.25 | +6.34 |

## Top Losses Vs Old Online

| Category | Video | F_guard | Delta F | Event_guard | Delta Event | FPS_guard | Delta FPS |
|---|---|---:|---:|---:|---:|---:|---:|
| PTZ | zoomInZoomOut | 0.2065 | -0.7178 | 0.7730 | +0.0000 | 24.46 | +20.45 |
| lowFramerate | turnpike_0_5fps | 0.6317 | -0.2585 | 0.7625 | -0.0659 | 23.83 | +19.68 |
| PTZ | intermittentPan | 0.1676 | -0.1873 | 0.7600 | -0.0866 | 27.37 | +20.83 |
| lowFramerate | tramCrossroad_1fps | 0.6775 | -0.1724 | 0.4310 | -0.0305 | 26.53 | +20.25 |
| dynamicBackground | canoe | 0.7798 | -0.1675 | 0.7813 | +0.0000 | 7.39 | +3.67 |
| cameraJitter | badminton | 0.5957 | -0.1604 | 0.9635 | -0.0365 | 21.78 | +17.08 |
| nightVideos | winterStreet | 0.3667 | -0.1348 | 0.8889 | +0.0000 | 22.38 | +18.91 |
| PTZ | continuousPan | 0.1215 | -0.1132 | 0.2906 | +0.0000 | 18.75 | +15.74 |
| nightVideos | busyBoulvard | 0.1744 | -0.0873 | 0.7792 | +0.0292 | 33.09 | +28.12 |
| cameraJitter | sidewalk | 0.6341 | -0.0813 | 0.9747 | +0.0131 | 16.55 | +10.14 |

## Severe Regressions

Videos worse than old online by more than 0.05 FMeasure:

PTZ/zoomInZoomOut (-0.7178), lowFramerate/turnpike_0_5fps (-0.2585), PTZ/intermittentPan (-0.1873), lowFramerate/tramCrossroad_1fps (-0.1724), dynamicBackground/canoe (-0.1675), cameraJitter/badminton (-0.1604), nightVideos/winterStreet (-0.1348), PTZ/continuousPan (-0.1132), nightVideos/busyBoulvard (-0.0873), cameraJitter/sidewalk (-0.0813), shadow/busStation (-0.0780), PTZ/twoPositionPTZCam (-0.0727), nightVideos/bridgeEntry (-0.0708), shadow/copyMachine (-0.0627), dynamicBackground/boats (-0.0604).

## continuousPan

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 ms | Closed-empty |
|---|---:|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.2347 | 0.2906 | 1.00 | 3.01 | 527.53 | n/a |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.1215 | 0.2906 | 0.33 | 18.75 | 333.95 | 0.00 |

continuousPan fails the targeted gate. Phase 5B preserved the closed-empty hard kill switch (`closed_empty_rate=0.00`, `ptz_closed_empty_kill_rate=0.10`), but activation fell to 0.33 and FMeasure is 0.1132 below old online. This means the smoke recovery did not generalize to the targeted run frame sample. The remaining problem is not closed-empty leakage; it is insufficient PTZ-safe mask quality or cadence under broader continuousPan evaluation.

## bridgeEntry

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 ms | Final CLOSED_EMPTY event FN |
|---|---:|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.2397 | 0.9744 | 0.85 | 6.66 | 402.71 | n/a |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.1690 | 0.9744 | 0.58 | 22.39 | 392.55 | 0 |

bridgeEntry passes the Event_F1 and final CLOSED_EMPTY event-FN gate, but FMeasure remains 0.0708 below old online. The event-continuity guard is doing its safety job (`event_hard_veto_frames=23`, `final_sanitizer_frames=22`, `event_closed_empty_final_count=0`), while pixel-level mask quality still trails.

## twoPositionPTZCam Watch Analysis

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 ms | Closed-empty |
|---|---:|---:|---:|---:|---:|---:|
| ONLINE_CALIBRATED | 0.8123 | 0.8025 | 0.91 | 5.84 | 385.01 | n/a |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.7396 | 0.7925 | 0.61 | 23.07 | 340.72 | 0.04 |

twoPositionPTZCam is a watch-stop failure. The delta vs old online is -0.0727 FMeasure, worse than the requested -0.03 review threshold. Closed-empty is small but not zero (`0.04`), and the main loss appears to come from reduced activation and conservative reuse/guard choices rather than latency.

## GMQ Branch Usage Summary

GMQ behavior is explainable in the intended scenes, but still too broad and not consistently accuracy-safe.

| Video | Legacy-safe rate | P3 veto rate | PTZ override rate | PTZ closed-empty kill rate |
|---|---:|---:|---:|---:|
| PTZ/continuousPan | 0.29 | 0.94 | 0.03 | 0.10 |
| PTZ/intermittentPan | 0.13 | 0.44 | 0.01 | 0.00 |
| PTZ/twoPositionPTZCam | 0.05 | 0.10 | 0.00 | 0.01 |
| PTZ/zoomInZoomOut | 0.38 | 0.74 | 0.02 | 0.00 |
| nightVideos/bridgeEntry | 0.00 | 0.00 | 0.00 | 0.00 |

Non-PTZ scenes also saw notable GMQ/legacy activity, including cameraJitter/boulevard (`legacy_safe_rate=0.42`), cameraJitter/traffic (`0.28`), dynamicBackground/canoe (`0.31`), and dynamicBackground/fall (`0.24`). This is not a broad P3-always policy, but GMQ is clearly influencing non-PTZ scenes and still creates accuracy losses in several categories.

## Decision

Targeted CDnet fails.

Full CDnet is not allowed. The next step should not be full CDnet or cross-dataset validation. The targeted results show that smoke-passing Phase 5B was overfit to the smoke distribution: it solved continuousPan closed-empty leakage but did not preserve mask quality or activation in the broader targeted PTZ set. The next research/implementation pass should focus on PTZ/camera-motion mask quality and cadence generalization, especially zoomInZoomOut, intermittentPan, continuousPan, and twoPositionPTZCam.
