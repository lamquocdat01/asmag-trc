# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-1C Runtime Alignment Report

Date: 2026-05-12

Phase 8C-1C is shadow-mode research only. AI intervention remains disabled and no learned model is allowed to alter guarded final actions.

## 1. Phase 8C-1B Recap

Phase 8C-1B completed calibration and smoke-only shadow validation, but Phase 8C-2 remained blocked.

- `ai_shadow_behavior_enabled: false`
- Offline recommended `unsafe_action` threshold: `0.75`
- Offline unsafe flag rate at `0.75`: `0.0393`
- Offline precision / recall / F1: `0.3003 / 0.9171 / 0.4524`
- Offline FPR: `0.0279`
- Smoke replay flag rate at `0.75`: `0.96375`
- Actual smoke rerun unsafe flag rate: `0.97125`
- Detector request / reuse block / lightweight block rates: `0.67875 / 0.27375 / 0.10625`
- Known safety-event warning rate: `0.9655`
- Missing feature count remained `0.0`
- Mean / P95 shadow latency after stride/lightweight rerun: `22.15 / 118.33 ms`

Main blockers carried into 8C-1C were runtime score saturation, offline/runtime score distribution mismatch, high P95 latency, and insufficient confidence for no-drift intervention.

## 2. Class and Probability Mapping

Output: `outputs/phase8c_shadow_calibration/class_probability_mapping.csv`

All exported model class/probability mappings are correct.

| Target | Model | Classes | Positive class | Offline index | Runtime index | Mapping |
| --- | --- | --- | --- | ---: | ---: | --- |
| detector_needed | logistic_regression | 0, 1 | 1 | 1 | 1 | OK |
| unsafe_action | random_forest | 0, 1 | 1 | 1 | 1 | OK |
| reuse_allowed | logistic_regression | 0, 1 | 1 | 1 | 1 | OK |
| lightweight_allowed | random_forest | 0, 1 | 1 | 1 | 1 | OK |
| detector_floor_needed | decision_tree | 0, 1 | 1 | 1 | 1 | OK |
| risk_class | random_forest | low, medium, unsafe | unsafe | 2 | 2 | OK |

`reuse_allowed` and `lightweight_allowed` scores are probabilities of allowed class `1`; runtime block decisions intentionally use `score < threshold`. No label encoding inversion was found.

## 3. Feature Schema Alignment

Output: `outputs/phase8c_shadow_calibration/feature_schema_alignment.csv`

Feature order is aligned for every exported model:

- Model features: `24`
- Runtime features: `24`
- Same order: `true`
- Missing runtime features: none
- Extra runtime features: none
- Mapping OK: `true` for all targets

Important runtime-value caveat: several features are built by the runtime adapter rather than directly logged in `frame_metrics.csv`: `normalized_latency`, `window_detector_count`, `window_reuse_count`, `window_closed_empty_count`, `window_mean_utility`, and `window_action_rate_*`. The adapter sets `window_mean_utility` to `0.0`, so schema order is correct but feature value distribution can still differ from training.

## 4. Runtime Score Distributions

Outputs:

- `outputs/phase8c_shadow_calibration/runtime_score_distribution.csv`
- `outputs/phase8c_shadow_calibration/offline_runtime_score_distribution_comparison.csv`

The mismatch is distributional, not a probability-index bug.

| Target | Offline mean | Runtime mean | Offline P95 | Runtime P95 |
| --- | ---: | ---: | ---: | ---: |
| unsafe_action | 0.0901 | 0.8532 | 0.6878 | 0.9176 |
| detector_needed | 0.0096 | 0.5021 | 0.0001 | 1.0000 |
| reuse_allowed | 0.0785 | 0.9544 | 0.7033 | 1.0000 |
| lightweight_allowed | 0.0711 | 0.9411 | 0.4912 | 0.9866 |
| detector_floor_needed | 0.0116 | 0.5736 | 0.0000 | 0.9981 |
| risk_class unsafe | 0.0139 | 0.0000 | 0.0212 | 0.0000 |

Runtime `risk_class` score is `0.0` because smoke used lightweight runtime mode and skipped the `risk_class` random forest.

## 5. Runtime Threshold Recommendations

Outputs:

- `outputs/phase8c_shadow_calibration/runtime_threshold_sweep.csv`
- `outputs/phase8c_shadow_calibration/runtime_threshold_recommendations.csv`

Recommended shadow-only thresholds:

| Target | Threshold | Runtime flag rate | Known safety recall | Normal-frame flag rate | Recommendation |
| --- | ---: | ---: | ---: | ---: | --- |
| unsafe_action | 0.76 | 0.9475 | 0.9212 | 0.9564 | Research only; still saturated |
| detector_needed | 0.98 | 0.3638 | 0.5961 | 0.2848 | Advisory with cadence only |
| detector_floor_needed | 0.99 | 0.1550 | 0.4384 | 0.0586 | Sparse advisory only |
| reuse_allowed | 0.99 | 0.3150 | 0.5419 | 0.2379 | Conservative advisory block |
| lightweight_allowed | 0.95 | 0.4975 | 0.3448 | 0.5494 | Advisory only; too costly/noisy |
| risk_class | 0.95 | 0.0000 | 0.0000 | 0.0000 | Disabled in lightweight runtime |

Unsafe threshold tradeoff on runtime smoke:

- `0.75`: flag rate `0.96375`, known safety recall `0.9507`
- `0.76`: flag rate `0.94750`, known safety recall `0.9212`
- `0.80`: flag rate `0.83375`, known safety recall `0.5911`
- `0.85`: flag rate `0.59125`, known safety recall `0.3005`
- `0.90`: flag rate `0.21125`, known safety recall `0.0197`

There is no runtime threshold that both reduces unsafe flags substantially below saturation and preserves high safety recall. This is the decisive blocker.

## 6. Latency Breakdown

Output: `outputs/phase8c_shadow_calibration/shadow_latency_breakdown.csv`

Existing smoke logs only contain total `ai_shadow_latency_ms`, so component values are offline replay microbenchmarks from the same smoke telemetry. Observed totals come from the smoke run.

| Scope | Mean total | P95 total | Mean model predict | P95 model predict | Mean feature adapter |
| --- | ---: | ---: | ---: | ---: | ---: |
| All frames | 22.15 ms | 118.33 ms | 10.23 ms | 46.27 ms | 0.61 ms |
| Prediction frames | 63.74 ms | 132.09 ms | 30.64 ms | 55.37 ms | 1.82 ms |

Per-target replay model timing:

- `unsafe_action` random forest: mean `11.77 ms`, P95 `21.59 ms`
- `lightweight_allowed` random forest: mean `11.40 ms`, P95 `20.56 ms`
- `detector_needed` logistic regression: mean `2.47 ms`, P95 `4.63 ms`
- `reuse_allowed` logistic regression: mean `2.55 ms`, P95 `4.94 ms`
- `detector_floor_needed` decision tree: mean `2.45 ms`, P95 `4.80 ms`

Worst observed video-level P95 shadow latency:

- `bridgeEntry`: `135.29 ms`
- `continuousPan`: `132.14 ms`
- `tramCrossroad_1fps`: `123.37 ms`

The bottleneck is prediction-frame sklearn inference, especially the `unsafe_action` and `lightweight_allowed` random forests. Cached frames are near zero, but stride recompute frames are still too slow.

## 7. Lightweight Runtime Model Recommendation

Output: `outputs/phase8c_shadow_calibration/runtime_model_set_recommendation.csv`

Primary recommendation: `offline-only, no runtime intervention yet`.

Secondary future candidate after retraining/replacement:

- `detector_needed`: logistic regression
- `reuse_allowed`: logistic regression
- `unsafe_action`: calibrated logistic regression or shallow sub-risk decision trees, replacing the current random forest
- `lightweight_allowed`: disable the current random forest from frame-critical runtime
- `risk_class`: keep disabled in lightweight runtime
- `detector_floor_needed`: decision tree

## 8. Smoke Rerun

No smoke rerun was performed in Phase 8C-1C.

Reason: class/probability mapping and feature schema order were verified as correct, and no runtime score extraction fix or config change was made. The required 8C-1C outputs were generated from the existing allowed smoke shadow run.

## 9. Phase 8C-2 Decision

Phase 8C-2 limited intervention is still blocked.

Reasons:

1. Runtime unsafe scores remain saturated. The best high-recall runtime threshold found here, `0.76`, still flags `0.9475` of smoke frames.
2. Thresholds that materially reduce unsafe flagging lose hard safety recall immediately.
3. P95 shadow latency remains too high: `118.33 ms` overall and `132.09 ms` on prediction frames.
4. The current frame-critical path still includes random forests for `unsafe_action` and `lightweight_allowed`.
5. No new no-drift A/B smoke comparison was performed in this phase.

## 10. Safety Confirmation

- AI intervention remains disabled.
- `ai_shadow_behavior_enabled` remains `false`.
- AI predictions still do not alter final actions.
- Old `ONLINE_CALIBRATED` was not modified.
- Frozen CDnet2014 v1.6 outputs were not overwritten.
- P1_YOLO_Only, P2_FrameDiff, P3_MOG2, ASMAG_TR_FAST, and ASMAG_TR_CONTROLLER were not modified.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.

## Files Created

- `tools/analyze_phase8c_runtime_alignment.py`
- `outputs/phase8c_shadow_calibration/class_probability_mapping.csv`
- `outputs/phase8c_shadow_calibration/feature_schema_alignment.csv`
- `outputs/phase8c_shadow_calibration/runtime_score_distribution.csv`
- `outputs/phase8c_shadow_calibration/runtime_threshold_sweep.csv`
- `outputs/phase8c_shadow_calibration/runtime_threshold_recommendations.csv`
- `outputs/phase8c_shadow_calibration/shadow_latency_breakdown.csv`
- `outputs/phase8c_shadow_calibration/runtime_model_set_recommendation.csv`
- `outputs/phase8c_shadow_calibration/offline_runtime_score_distribution_comparison.csv`

## Verification

Ran:

```powershell
python -m py_compile tools/analyze_phase8c_runtime_alignment.py tools/calibrate_phase8c_shadow_models.py tools/export_phase8b_shadow_models.py src/run_experiment.py tools/compare_asmag_tr_controller_online_guarded.py
python tools/analyze_phase8c_runtime_alignment.py
```

No forbidden experiment was run.
