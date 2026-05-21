# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-1 Shadow-Mode Report

Date: 2026-05-11

## Scope

Phase 8C-1 added offline-trained AI risk policy shadow logging for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` only. The learned policy is advisory only: `ai_shadow_behavior_enabled` remains false, no AI prediction is used to choose or modify the final guarded action, and no runtime deployment or intervention was enabled.

## Models Loaded

Shadow artifacts were exported under `outputs/phase8b_policy_training/models/`.

| Target | Model | Runtime role |
|---|---:|---|
| detector_needed | logistic_regression | advisory detector request |
| unsafe_action | random_forest | advisory unsafe flag |
| reuse_allowed | logistic_regression | advisory reuse block |
| lightweight_allowed | random_forest | advisory lightweight block |
| risk_class | random_forest | advisory risk severity |
| detector_floor_needed | decision_tree | advisory detector floor |

The Phase 8B action rankers were intentionally not exported as runtime selectors.

## Features

The exported schema contains 24 robust runtime-compatible features: latency, normalized latency, YOLO/reuse indicators, frame indices, reuse state, and rolling action-window counts/rates. Runtime missing features are filled with safe default `0.0` and counted per frame.

Smoke validation reported:

| Metric | Value |
|---|---:|
| Guarded frames with AI logs | 800 |
| AI enabled rate | 1.000 |
| Mean missing feature count | 0.000 |
| P95 missing feature count | 0.000 |
| Mean shadow latency | 49.37 ms |
| P95 shadow latency | 70.65 ms |

Latency improved after loading forest models with single-thread inference, but it is still too high for any intervention phase without further optimization.

## Smoke Aggregate

Smoke command run in four allowed chunks:

`python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke.yaml --max-jobs-per-run 8`

Final smoke progress:

| Jobs completed | Failed | Pending |
|---:|---:|---:|
| 32 | 0 | 0 |

Final guarded comparison:

| Pipeline | FMeasure | Event_F1 | Activation | Avg_FPS | P95_latency | Reuse_rate |
|---|---:|---:|---:|---:|---:|---:|
| ASMAG_TR_CONTROLLER | 0.5063 | 0.6412 | 0.6600 | 86.55 | 224.99 | 0.0000 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4166 | 0.5887 | 0.5800 | 34.40 | 255.03 | 0.1263 |
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 25.97 | 269.07 | 0.0938 |
| P3_MOG2 | 0.5063 | 0.6412 | 0.6600 | 63.00 | 234.72 | 0.0000 |

The final guarded behavior remains controlled by existing guarded logic. AI fields are written only as telemetry.

## Shadow Prediction Summary

Generated comparison files:

- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_disagreement_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_safety_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_video_summary.csv`

Aggregate shadow summary:

| Metric | Value |
|---|---:|
| Disagreement rate | 1.000 |
| Unsafe flag rate | 1.000 |
| Detector request rate | 0.705 |
| Block reuse rate | 0.126 |
| Block lightweight rate | 0.056 |
| Known safety event warning rate | 1.000 |

The AI warning behavior is intentionally shadow-only. The detector request signal is plausible on hard videos, but the unsafe-action model over-flags every smoke frame and is not suitable for intervention.

## Known Failure Analysis

| Video | AI unsafe flags | AI detector requests | AI block reuse | AI block lightweight | Known guarded safety events | Mean shadow latency |
|---|---:|---:|---:|---:|---:|---:|
| continuousPan | 100 | 100 | 2 | 10 | 83 | 56.04 ms |
| twoPositionPTZCam | 100 | 92 | 13 | 1 | 17 | 61.66 ms |
| bridgeEntry | 100 | 84 | 21 | 0 | 8 | 50.90 ms |
| cubicle | 100 | 64 | 11 | 6 | 18 | 44.16 ms |

The AI correctly warns on all known hard-video safety-event frames, but because unsafe flags are saturated, this result is not selective enough to justify runtime blocking.

## Acceptance

Phase 8C-1 shadow logging passes the instrumentation criteria:

- No crashes in smoke validation.
- AI predictions are logged on every guarded smoke frame.
- Missing feature count is zero.
- Hard videos receive AI warnings.
- No AI behavior intervention occurs.

Phase 8C-2 limited intervention is not allowed yet. Required fixes before intervention:

1. Recalibrate or retrain the unsafe-action shadow model so it does not flag every frame.
2. Reduce shadow latency substantially, or move prediction to a batched/asynchronous cadence.
3. Validate selectivity on a held-out smoke-like batch before any action-blocking experiment.
4. Keep intervention behind a separate disabled-by-default flag and rerun smoke only before broader validation.

No production pipeline behavior was changed, old `ONLINE_CALIBRATED` was not modified, frozen CDnet2014 v1.6 outputs were not overwritten, and no PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or experiment runner command was run.
