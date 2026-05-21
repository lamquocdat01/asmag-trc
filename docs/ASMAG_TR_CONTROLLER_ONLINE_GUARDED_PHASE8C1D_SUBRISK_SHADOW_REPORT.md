# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-1D Sub-Risk Shadow Report

Date: 2026-05-12

## 1. Why broad unsafe_action was replaced

Phase 8C-1C verified that class/probability mapping and feature schema/order were aligned, but the broad `unsafe_action` runtime shadow model remained distributionally mismatched on smoke replay. The best practical 8C-1C threshold still saturated runtime smoke: threshold 0.76 produced unsafe flag rate 0.9475 with known safety recall 0.9212, while threshold 0.80 reduced flagging to 0.83375 but dropped recall to 0.5911. Shadow latency was also dominated by sklearn random forest inference, especially `unsafe_action` and `lightweight_allowed`.

Phase 8C-1D therefore removes broad `unsafe_action` from the runtime candidate path and replaces it with narrow, lightweight sub-risk shadows. The new runtime set is diagnostic only and remains forbidden from changing final actions.

## 2. Sub-risk label definitions

Labels were derived offline from the Phase 8A policy dataset:

- `closed_empty_risk`: `CLOSED_EMPTY` under active event/global motion/PTZ closed-empty block context.
- `reuse_risk`: `REUSE_ACC` under low compensated/geometric trust, stale reuse, camera jump, or active event/motion context.
- `lightweight_p3_risk`: `LIGHTWEIGHT_MASK_P3_FALLBACK` under PTZ/global-motion or low P3 trust.
- `legacy_cadence_risk`: `LEGACY_SAFE_P3_GUARD` when detector-like cadence/floor preservation is not safe.
- `detector_needed`: existing detector-needed label.
- `lightweight_acc_allowed`: `LIGHTWEIGHT_MASK_ACC` is the best safe action or current safe lightweight action under sufficient trust.

The broad `unsafe_action` target was not exported for runtime.

## 3. Sub-risk model results

Training used video-grouped split plus category-holdout and PTZ-holdout where feasible. Runtime candidates were limited to majority baseline, logistic regression, and shallow decision tree. No random forest was used in the runtime set.

Label distribution:

| target | positives | positive_rate |
| --- | ---: | ---: |
| closed_empty_risk | 1933 | 0.002642 |
| reuse_risk | 2404 | 0.003286 |
| lightweight_p3_risk | 1191 | 0.001628 |
| legacy_cadence_risk | 391 | 0.000534 |
| detector_needed | 4353 | 0.005951 |
| lightweight_acc_allowed | 2168 | 0.002964 |

Recommended offline models:

| target | model | offline threshold | video-grouped precision | video-grouped recall | video-grouped F1 | flag_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| closed_empty_risk | logistic_regression | 0.99 | 0.9565 | 0.9910 | 0.9735 | 0.0263 |
| reuse_risk | logistic_regression | 0.08 | 0.8000 | 1.0000 | 0.8889 | 0.0218 |
| lightweight_p3_risk | shallow_decision_tree | 0.99 | 0.9365 | 1.0000 | 0.9672 | 0.0145 |
| legacy_cadence_risk | logistic_regression | 0.17 | 1.0000 | 1.0000 | 1.0000 | 0.0023 |
| detector_needed | shallow_decision_tree | 0.99 | 0.9592 | 1.0000 | 0.9792 | 0.0225 |
| lightweight_acc_allowed | logistic_regression | 0.21 | 0.5772 | 0.8668 | 0.6929 | 0.7883 |

Runtime export applied stricter smoke-safe threshold floors where offline thresholds over-flagged runtime smoke:

| target | runtime threshold |
| --- | ---: |
| closed_empty_risk | 0.9999 |
| reuse_risk | 0.9999 |
| lightweight_p3_risk | 0.99 |
| legacy_cadence_risk | 0.99 |
| detector_needed | 0.99 |
| lightweight_acc_allowed | 0.21 |

## 4. Runtime model set

Runtime model set: `subrisk_lightweight`.

Export directory: `outputs/phase8c_subrisk_models/runtime_models`.

Runtime models:

- `closed_empty_risk`: logistic regression
- `reuse_risk`: logistic regression
- `lightweight_p3_risk`: shallow decision tree
- `legacy_cadence_risk`: logistic regression
- `detector_needed`: shallow decision tree
- `lightweight_acc_allowed`: logistic regression

The guarded smoke config was updated only for shadow logging/model loading:

- `ai_shadow_behavior_enabled: false`
- `ai_shadow_runtime_model_set: "subrisk_lightweight"`
- `ai_shadow_model_dir: "outputs/phase8c_subrisk_models/runtime_models"`
- `ai_shadow_log_subrisk: true`
- `ai_shadow_prediction_stride: 3`

## 5. Smoke sub-risk shadow summary

Smoke rerun: performed, guarded CDnet smoke only. Final progress was 32/32 completed, 0 failed.

Final smoke sub-risk summary:

| metric | value |
| --- | ---: |
| frames | 800 |
| closed_empty_risk_flag_rate | 0.0300 |
| reuse_risk_flag_rate | 0.3175 |
| lightweight_p3_risk_flag_rate | 0.0300 |
| legacy_cadence_risk_flag_rate | 0.0275 |
| detector_needed_flag_rate | 0.40125 |
| lightweight_acc_not_allowed_rate | 0.0750 |
| subrisk_any_flag_rate | 0.3900 |
| subrisk_or_detector_warning_rate | 0.7000 |
| normal_frame_subrisk_any_flag_rate | 0.32295 |
| known_safety_event_subrisk_warning_rate | 0.95789 |
| hard_video_subrisk_warning_rate | 0.8650 |
| mean_missing_features | 0.0 |
| p95_missing_features | 0.0 |

Per-video sub-risk any flag rates:

| video | subrisk_any_flag_rate | hard_video_warning_rate |
| --- | ---: | ---: |
| PTZ/continuousPan | 0.70 | 1.00 |
| PTZ/twoPositionPTZCam | 0.33 | 0.91 |
| nightVideos/bridgeEntry | 0.52 | 0.91 |
| shadow/cubicle | 0.30 | 0.64 |
| dynamicBackground/fountain02 | 0.36 | 0.00 |
| lowFramerate/tramCrossroad_1fps | 0.49 | 0.00 |
| shadow/backdoor | 0.12 | 0.00 |
| turbulence/turbulence2 | 0.30 | 0.00 |

Compared with the previous broad unsafe path, runtime flagging is no longer saturated: `subrisk_any_flag_rate` is 0.3900 instead of approximately 0.95 to 0.97.

## 6. Latency before/after

Phase 8C-1C RF shadow latency:

- Overall mean/P95: 22.15 / 118.33 ms
- Prediction-frame P95: 132.09 ms

Phase 8C-1D sub-risk lightweight latency:

- Overall mean/P95: 8.15 / 31.73 ms
- Prediction-frame mean/P95: 22.41 / 38.97 ms
- Max observed sub-risk latency: 66.26 ms

Highest video-level P95 was `lowFramerate/tramCrossroad_1fps` at 43.42 ms. The major 8C-1C RF inference bottleneck is resolved for the shadow path, although low-framerate and PTZ scenes still show runtime pipeline spikes outside pure sub-risk model inference.

## 7. Phase 8C-2 decision

Phase 8C-2 limited intervention is still blocked.

Reasons:

- Hard-video sub-risk warning is 0.865, below the desired high-recall intervention bar.
- `shadow/cubicle` hard-video warning is only 0.64.
- Normal-frame sub-risk flagging remains 0.32295, so selectivity is improved but not yet intervention-safe.
- Final behavior drift/control has not been validated under any AI intervention path.

The recommended next step is additional sub-risk calibration focused on hard-video recall and normal-frame selectivity before any Phase 8C-2 intervention proposal.

## 8. Safety confirmation

- AI intervention remains disabled: `ai_shadow_behavior_enabled: false`.
- AI predictions are logged only and do not alter final actions.
- old `ONLINE_CALIBRATED` was not modified.
- Frozen CDnet2014 v1.6 outputs were not overwritten.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- Only guarded CDnet smoke shadow validation was rerun.

