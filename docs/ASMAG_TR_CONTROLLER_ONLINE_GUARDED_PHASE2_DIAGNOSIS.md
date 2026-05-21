# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 2 Diagnosis

Date: 2026-05-09

Scope: Phase 1 smoke output under `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/`.

## Baseline Smoke Result

`ASMAG_TR_CONTROLLER_ONLINE_GUARDED` completed the 8-video smoke run without crashing and produced the required Phase 1 diagnostic columns. It improved aggregate FPS over old `ONLINE_CALIBRATED`, but it was not a clean pass:

| Pipeline | FMeasure | Event_F1 | Activation | FPS | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| P3_MOG2 | 0.5063 | 0.6412 | 0.6600 | 52.65 | 222.50 |
| ASMAG_TR_CONTROLLER | 0.5063 | 0.6412 | 0.6600 | 81.95 | 351.76 |
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 23.10 | 263.27 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4089 | 0.5483 | 0.6125 | 41.03 | 528.06 |

## 1. Videos Causing P95 Regression

The P95 regression is dominated by two smoke videos:

| Category | Video | P95 delta vs ONLINE_CALIBRATED | FPS delta vs ONLINE_CALIBRATED | FMeasure delta vs ONLINE_CALIBRATED |
|---|---|---:|---:|---:|
| PTZ | continuousPan | +1113.62 ms | +0.29 | +0.0264 |
| nightVideos | bridgeEntry | +1031.83 ms | +0.50 | -0.0237 |

Minor P95 regressions also appear in `shadow/cubicle`, `lowFramerate/tramCrossroad_1fps`, and `shadow/backdoor`, but those are tens of milliseconds rather than seconds.

## 2. Highest-Latency Action Labels

Action-label latency ranking from guarded frame logs:

| Video | Action label | Frames | Mean latency ms | P95 latency ms | Max latency ms | Detector mean ms |
|---|---|---:|---:|---:|---:|---:|
| PTZ/continuousPan | FALLBACK_P3_GUARD | 77 | 467.12 | 1688.59 | 2377.79 | 420.02 |
| nightVideos/bridgeEntry | DETECT_ACC | 94 | 400.05 | 1332.27 | 1891.28 | 375.41 |
| PTZ/continuousPan | FALLBACK_P3_POLICY | 23 | 307.85 | 393.03 | 393.18 | 256.04 |
| shadow/backdoor | FALLBACK_P3_GUARD | 5 | 259.33 | 310.41 | 310.41 | 233.97 |
| shadow/cubicle | FALLBACK_P3_POLICY | 30 | 227.59 | 301.42 | 302.41 | 210.72 |

Low-latency actions are reuse and closed-empty actions, generally below 25 ms P95.

## 3. Source of Spikes

Spikes come from detector calls, not mask postprocess:

- `continuousPan` worst frame: total 2377.79 ms, detector 2310.07 ms, gate features 47.56 ms, postprocess 2.01 ms.
- `bridgeEntry` worst frame: total 1891.28 ms, detector 1802.28 ms, gate features 62.86 ms, postprocess 1.42 ms.

`FORCED_REFRESH` is not the source. It fired only 2 frames in the full smoke set, with P95 around 199 ms.

## 4. Hard P3 Guard Frequency

Hard P3 guard is too frequent in PTZ/global-motion scenes:

| Video | Frames | Detector calls | FALLBACK_P3_GUARD frames | Guard rate | Reuse rate |
|---|---:|---:|---:|---:|---:|
| PTZ/continuousPan | 100 | 100 | 77 | 0.77 | 0.00 |
| dynamicBackground/fountain02 | 100 | 32 | 14 | 0.14 | 0.11 |
| shadow/cubicle | 100 | 50 | 11 | 0.11 | 0.08 |
| shadow/backdoor | 100 | 21 | 5 | 0.05 | 0.12 |
| turbulence/turbulence2 | 100 | 19 | 1 | 0.01 | 0.17 |
| nightVideos/bridgeEntry | 100 | 94 | 0 | 0.00 | 0.06 |

The guard is useful for preserving accuracy in `continuousPan`, but it is allowed to refresh every frame, which turns a hard-scene safety rule into a latency spike amplifier.

## 5. Forced Refresh Frequency

Forced refresh is not too frequent. It appears only twice in the smoke run:

- `dynamicBackground/fountain02`: 1 frame.
- `shadow/cubicle`: 1 frame.

Phase 2 still needs a forced refresh cooldown because the mechanism can create consecutive detector spikes in other videos, but it is not the Phase 1 root cause.

## 6. Reuse Stopping

Reuse is too conservative in the two worst latency videos:

- `continuousPan`: 0 reuse frames, 100 detector calls, 77 guard calls.
- `bridgeEntry`: 6 reuse frames, 94 detector calls.

In easier videos, reuse is active but often stopped by current confidence/closed-streak rules. This suggests Phase 2 should add a critical reuse threshold for overload/guard-cooldown cases instead of using the normal reuse threshold everywhere.

## 7. Hysteresis and Expensive Modes

Hysteresis prevents rapid mode thrashing, but it can keep expensive behavior active too long:

- `continuousPan` alternates between hard guard P3 fallback and policy P3 fallback; all 100 frames call the detector.
- `bridgeEntry` stays in ACC, but ACC gate remains open on 94 frames and the detector dominates latency.

The issue is not mode switching frequency alone. The missing control is detector refresh cadence inside persistent hard/high-activation states.

## 8. Gate Feature Cache

Candidate gates are not being recomputed in the old inefficient way for the guarded path. The `cache_hit_gate_features` value is 1.0 across inspected guarded smoke logs. Gate feature latency is usually far below detector latency. The Phase 2 runtime target should therefore focus on detector-call suppression, reuse, and cooldown logging rather than another feature-cache rewrite.

## Phase 2 Stabilization Direction

Low-risk Phase 2 changes should be limited to `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`:

1. Add hard-guard cadence so `FALLBACK_P3_GUARD` cannot trigger detector refresh every frame.
2. Add forced-refresh cooldown even though Phase 1 forced refresh was rare.
3. Add max consecutive P3 guard duration and an exit threshold when motion disagreement decreases.
4. Add latency-aware overload cooldown after slow detector frames.
5. Retune guarded reuse with a separate critical threshold for overload/cooldown frames.
6. Log guard, cooldown, overload, and previous-latency state per frame.

No old pipeline behavior should change.
