# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-1B Shadow Calibration Report

Phase 8C-1 passed instrumentation but could not proceed to intervention because the AI shadow model over-flagged every smoke frame as unsafe and added too much per-frame latency.

AI intervention remains disabled. No learned model is used to alter final guarded actions.

## Inputs

Read inputs:

- Phase 8C-1 report and smoke shadow summaries.
- Phase 8B model results, best-model summary, feature importance, unsafe analysis, and exported shadow models.
- Phase 8A policy dataset.

## Calibration Outputs

Created:

- `outputs/phase8c_shadow_calibration/unsafe_threshold_sweep.csv`
- `outputs/phase8c_shadow_calibration/detector_threshold_sweep.csv`
- `outputs/phase8c_shadow_calibration/reuse_threshold_sweep.csv`
- `outputs/phase8c_shadow_calibration/lightweight_threshold_sweep.csv`
- `outputs/phase8c_shadow_calibration/detector_floor_threshold_sweep.csv`
- `outputs/phase8c_shadow_calibration/risk_class_unsafe_threshold_sweep.csv`
- `outputs/phase8c_shadow_calibration/calibration_recommendations.csv`
- `outputs/phase8c_shadow_calibration/calibration_report.md`
- `outputs/phase8c_shadow_calibration/subrisk_model_probe.csv`
- `outputs/phase8c_shadow_calibration/subrisk_feature_importance.csv`

## Recommended Thresholds

| Target | Recommended threshold | Offline flag rate | Precision | Recall | F1 | FPR | Smoke flag rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| unsafe_action | 0.75 | 0.0393 | 0.3003 | 0.9171 | 0.4524 | 0.0279 | 0.9638 |
| detector_needed | 0.98 | 0.0093 | 0.9767 | 0.9963 | 0.9864 | 0.0002 | n/a |
| reuse_block | 0.99 | 0.9956 | 0.9969 | 0.9983 | 0.9976 | 0.5344 | n/a |
| lightweight_block | 0.98 | 0.9951 | 0.9957 | 0.9990 | 0.9974 | 0.5243 | n/a |
| detector_floor_needed | 0.98 | 0.0097 | 0.6010 | 0.9734 | 0.7432 | 0.0039 | n/a |
| risk_class unsafe | 0.96 | 0.0076 | 0.8536 | 0.9103 | 0.8810 | 0.0011 | n/a |

The `unsafe_action` threshold of 0.75 is the recommended research threshold because it keeps high offline recall and high hard-video smoke warning recall while reducing the offline flag rate. It does not fully solve smoke over-flagging.

## Smoke Rerun Summary

Smoke-only rerun completed 32/32 jobs with no failed jobs.

Aggregate AI shadow summary:

- Frames with AI logs: 800.
- Shadow enabled rate: 1.000.
- Unsafe flag rate from the actual rerun threshold 0.74: 0.97125.
- Replay flag rate at the final recommended threshold 0.75: 0.96375.
- Detector request rate: 0.67875.
- Reuse block rate: 0.27375.
- Lightweight block rate: 0.10625.
- Mean / P95 missing features: 0.0 / 0.0.
- Mean / P95 shadow latency: 22.15 / 118.33 ms.
- Known safety-event AI warning rate: 0.9655.

Known hard-video warning rates:

- `continuousPan`: unsafe flag rate 0.93, known-event warning rate 0.9405.
- `twoPositionPTZCam`: unsafe flag rate 1.00, known-event warning rate 1.0000.
- `bridgeEntry`: unsafe flag rate 1.00, known-event warning rate 1.0000.
- `cubicle`: unsafe flag rate 0.99, known-event warning rate 0.9444.

## Sub-Risk Diagnostics

Derived labels were feasible for:

- `closed_empty_unsafe`
- `reuse_unsafe`
- `lightweight_p3_unsafe`
- `legacy_cadence_unsafe`

Best observed probe results:

| Sub-risk | Best model | F1 | Recall | Precision |
| --- | --- | ---: | ---: | ---: |
| closed_empty_unsafe | decision tree | 0.9899 | 1.0000 | 0.9799 |
| reuse_unsafe | decision tree | 0.9831 | 1.0000 | 0.9669 |
| lightweight_p3_unsafe | decision tree | 0.8651 | 1.0000 | 0.7622 |
| legacy_cadence_unsafe | random forest | 0.8696 | 1.0000 | 0.7692 |

These sub-risk models are offline diagnostics only. They are not deployed.

## Latency Bottleneck

The runtime model loader is cached per sequence and is not the main bottleneck. The expensive path is sequential sklearn inference, especially random forests, plus per-frame feature-frame construction. A prediction stride of 3 and lightweight runtime mode reduced mean AI latency from 49.37 ms to 22.15 ms, but P95 remains too high.

Recommended lightweight runtime set:

- `detector_needed`: logistic regression.
- `reuse_allowed`: logistic regression advisory.
- `detector_floor_needed`: decision tree.
- Replace monolithic unsafe RF with sub-risk decision trees or deterministic rules before intervention.
- Skip `risk_class` RF in frame-critical runtime mode.
- Keep action rankers excluded.

## Final Behavior Check

AI behavior remained disabled via:

- `ai_shadow_behavior_enabled: false`

The shadow code only logs prediction fields and advisory flags. It does not write into the guarded action selector.

However, the refreshed smoke comparison did not reproduce the prior Phase 8C-1 aggregate guarded accuracy exactly. The current comparison reports:

- `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` FMeasure: 0.3126.
- `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` Event_F1: 0.5800.
- `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` Activation: 0.3438.

Because Phase 8C-2 requires high confidence that shadow instrumentation causes no final-action drift, this rerun should be treated as a blocker until a controlled A/B smoke check reproduces equivalent guarded outputs with AI logging on and off.

## Phase 8C-2 Decision

Phase 8C-2 limited intervention is not allowed yet.

Reasons:

1. Unsafe flag rate is no longer exactly saturated, but it is still very high on smoke: 0.97125 in the actual rerun and 0.96375 in threshold replay.
2. Mean latency improved, but P95 is still too high for intervention.
3. A no-drift behavior comparison should be repeated before any learned policy is allowed near action control.

Recommended next fixes:

1. Export and evaluate sub-risk decision-tree/rule candidates for unsafe diagnostics.
2. Add A/B smoke comparison with identical config except AI shadow logging on/off.
3. Add latency sub-timers for feature building, each model, and logging.
4. Keep intervention disabled until unsafe flag rate, latency, and behavior stability pass together.
