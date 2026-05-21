# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Logic-Outcome Analysis

Read-only mining study over existing CDnet2014 evidence and ASMAG pipeline outputs. No algorithm code was modified and no CDnet/SBI/LASIESTA/BMC run was launched.

## Evidence

- `outputs/full_cdnet2014_official_edge_profile_pc/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted/`
- Per-video summaries, per-frame metrics, mode/action summaries, GMQ summaries, motion-compensation summaries when available, and the P4/targeted diagnosis docs.

## Dataset Shape

- Video/pipeline rows: 482
- Guarded rows with old-online deltas: 41
- Guarded wins/losses vs ONLINE_CALIBRATED in FMeasure: 12/27
- Action-summary rows: 80

## Strongest Positive FMeasure Correlations

| feature                   |   n |   spearman_rho |   p_value |
|:--------------------------|----:|---------------:|----------:|
| compensated_iou_p95       |  41 |         0.5253 |    0.0004 |
| compensated_iou_mean      |  49 |         0.3662 |    0.0097 |
| FAST_rate                 | 135 |         0.1063 |    0.2197 |
| legacy_safe_rate          |  82 |         0.0789 |    0.4810 |
| motion_comp_behavior_rate |  49 |         0.0717 |    0.6243 |
| reuse_rate                | 135 |         0.0066 |    0.9392 |
| PTZ_emergency_rate        |  82 |        -0.0049 |    0.9653 |
| detector_like_P3_rate     |  82 |        -0.0108 |    0.9234 |
| closed_empty_rate         |  82 |        -0.0108 |    0.9231 |
| P3_FALLBACK_rate          | 135 |        -0.0160 |    0.8535 |

## Strongest Negative FMeasure Correlations

| feature                        |   n |   spearman_rho |   p_value |
|:-------------------------------|----:|---------------:|----------:|
| avg_frames_since_last_detector |  41 |        -0.3964 |    0.0103 |
| candidate_disagreement_mean    |  41 |        -0.3547 |    0.0229 |
| low_framerate_guard_rate       |  16 |        -0.3396 |    0.1982 |
| event_hard_veto_rate           |  41 |        -0.1553 |    0.3324 |
| GMQ_behavior_rate              | 135 |        -0.1502 |    0.0821 |
| ACC_rate                       | 135 |        -0.1148 |    0.1849 |
| final_sanitizer_rate           |  82 |        -0.0974 |    0.3840 |
| lightweight_P3_rate            |  82 |        -0.0924 |    0.4088 |
| motion_comp_probe_rate         |  49 |        -0.0832 |    0.5698 |
| candidate_disagreement_p95     |  41 |        -0.0756 |    0.6387 |

## Delta-F Correlation Signals

| feature                     |   n |   spearman_rho |   p_value |
|:----------------------------|----:|---------------:|----------:|
| candidate_disagreement_p95  |  41 |         0.3674 |    0.0181 |
| FAST_rate                   | 135 |         0.1820 |    0.0347 |
| candidate_disagreement_mean |  41 |         0.1484 |    0.3545 |
| compensated_iou_mean        |  49 |         0.1412 |    0.3333 |
| motion_comp_probe_rate      |  49 |         0.1262 |    0.3875 |
| residual_ratio_mean         |  49 |         0.0759 |    0.6041 |
| residual_ratio_p95          |  49 |         0.0668 |    0.6484 |
| low_framerate_guard_rate    |  16 |         0.0066 |    0.9808 |
| compensated_iou_p95         |  41 |         0.0020 |    0.9900 |
| detector_floor_rate         |  16 |        -0.0313 |    0.9085 |

## PTZ Action Outcomes

| category   | action_label                 |   videos |   frames |   mean_FMeasure |   mean_Recall |   mean_Precision |   mean_latency_ms |   yolo_rate |   reuse_rate |
|:-----------|:-----------------------------|---------:|---------:|----------------:|--------------:|-----------------:|------------------:|------------:|-------------:|
| PTZ        | LIGHTWEIGHT_MASK_ACC         |        3 |       26 |          0.7707 |        0.9717 |           0.6663 |           21.1925 |      0.0000 |       0.0000 |
| PTZ        | DETECT_ACC                   |        4 |       65 |          0.6596 |        0.7322 |           0.6235 |          281.6814 |      1.0000 |       0.0000 |
| PTZ        | FALLBACK_P3_GUARD            |        4 |       17 |          0.6215 |        0.6742 |           0.5916 |          264.7280 |      1.0000 |       0.0000 |
| PTZ        | FALLBACK_P3_POLICY           |        3 |       39 |          0.4118 |        0.4250 |           0.4073 |          263.8724 |      1.0000 |       0.0000 |
| PTZ        | other                        |       23 |     1813 |          0.3475 |        0.4046 |           0.3348 |          287.2123 |      0.9470 |       0.0127 |
| PTZ        | LEGACY_SAFE_P3_GUARD         |        6 |      182 |          0.1718 |        0.2292 |           0.1591 |          333.2034 |      1.0000 |       0.0000 |
| PTZ        | LIGHTWEIGHT_MASK_P3_FALLBACK |        6 |      171 |          0.1278 |        0.2622 |           0.1237 |           45.2792 |      0.0000 |       0.0000 |
| PTZ        | REUSE_ACC                    |        4 |       60 |          0.0408 |        0.0824 |           0.0413 |           29.7326 |      0.0000 |       1.0000 |
| PTZ        | CLOSED_EMPTY_ACC             |        3 |       27 |          0.0000 |        0.0000 |           0.0000 |           18.6910 |      0.0000 |       0.0000 |

## Category-Stratified Correlations

| category     | feature                        |   n |   spearman_rho |   p_value |
|:-------------|:-------------------------------|----:|---------------:|----------:|
| PTZ          | compensated_iou_mean           |   8 |         0.7306 |    0.0396 |
| PTZ          | detector_floor_rate            |   4 |         0.7071 |    0.2929 |
| PTZ          | motion_comp_behavior_rate      |   8 |         0.6635 |    0.0728 |
| PTZ          | motion_comp_probe_rate         |   8 |         0.4854 |    0.2227 |
| PTZ          | residual_ratio_mean            |   8 |         0.4338 |    0.2829 |
| PTZ          | residual_ratio_p95             |   8 |         0.3790 |    0.3545 |
| PTZ          | final_sanitizer_rate           |  12 |         0.3546 |    0.2581 |
| PTZ          | candidate_disagreement_mean    |   6 |         0.2029 |    0.6998 |
| PTZ          | candidate_disagreement_p95     |   6 |         0.2029 |    0.6998 |
| PTZ          | P3_FALLBACK_rate               |  16 |         0.1696 |    0.5300 |
| PTZ          | FAST_rate                      |  16 |         0.1438 |    0.5952 |
| PTZ          | PTZ_emergency_rate             |  12 |        -0.0153 |    0.9623 |
| PTZ          | event_hard_veto_rate           |   6 |        -0.1518 |    0.7741 |
| PTZ          | legacy_safe_rate               |  12 |        -0.4471 |    0.1450 |
| PTZ          | reuse_rate                     |  16 |        -0.4643 |    0.0700 |
| PTZ          | avg_frames_since_last_detector |   6 |        -0.4857 |    0.3287 |
| PTZ          | ACC_rate                       |  16 |        -0.5039 |    0.0466 |
| PTZ          | GMQ_behavior_rate              |  16 |        -0.5068 |    0.0451 |
| PTZ          | closed_empty_rate              |  12 |        -0.5781 |    0.0490 |
| PTZ          | lightweight_P3_rate            |  12 |        -0.6307 |    0.0279 |
| PTZ          | compensated_iou_p95            |   6 |        -0.6571 |    0.1562 |
| PTZ          | low_framerate_guard_rate       |   4 |        -0.7071 |    0.2929 |
| PTZ          | detector_like_P3_rate          |  12 |        -0.8574 |    0.0004 |
| cameraJitter | motion_comp_behavior_rate      |   4 |         0.6325 |    0.3675 |
| cameraJitter | FAST_rate                      |  12 |         0.3932 |    0.2061 |
| cameraJitter | candidate_disagreement_mean    |   4 |         0.2000 |    0.8000 |
| cameraJitter | candidate_disagreement_p95     |   4 |         0.2000 |    0.8000 |
| cameraJitter | PTZ_emergency_rate             |   8 |         0.1485 |    0.7256 |
| cameraJitter | P3_FALLBACK_rate               |  12 |         0.1334 |    0.6794 |
| cameraJitter | compensated_iou_p95            |   4 |         0.0000 |    1.0000 |

## Logistic Regression Odds Ratios

| feature                        |    coef |   odds_ratio |   n |   positive | model_note                                                                           |
|:-------------------------------|--------:|-------------:|----:|-----------:|:-------------------------------------------------------------------------------------|
| candidate_disagreement_p95     |  1.0852 |       2.9599 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| final_sanitizer_rate           |  0.9098 |       2.4839 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| compensated_iou_mean           |  0.3113 |       1.3651 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| motion_comp_behavior_rate      |  0.2058 |       1.2286 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| low_framerate_guard_rate       |  0.1544 |       1.1670 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| detector_floor_rate            |  0.1528 |       1.1651 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| ACC_rate                       | -0.0144 |       0.9857 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| PTZ_emergency_rate             | -0.0386 |       0.9622 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| legacy_safe_rate               | -0.1664 |       0.8467 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| compensated_iou_p95            | -0.1991 |       0.8195 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| event_hard_veto_rate           | -0.2702 |       0.7633 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| residual_ratio_mean            | -0.2974 |       0.7427 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| P3_FALLBACK_rate               | -0.2985 |       0.7419 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| avg_frames_since_last_detector | -0.3202 |       0.7260 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| motion_comp_probe_rate         | -0.3646 |       0.6945 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| residual_ratio_p95             | -0.4131 |       0.6616 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| candidate_disagreement_mean    | -0.4144 |       0.6607 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| detector_like_P3_rate          | -0.4693 |       0.6255 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| FAST_rate                      | -0.5656 |       0.5680 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |
| lightweight_P3_rate            | -0.6976 |       0.4978 |  41 |         12 | standardized logistic regression; target=guarded beats ONLINE_CALIBRATED in FMeasure |

## Decision Tree Rules

```text
Target: 1 means ASMAG_TR_CONTROLLER_ONLINE_GUARDED loses to ONLINE_CALIBRATED in FMeasure.

|--- GMQ_behavior_rate <= 0.0550
|   |--- candidate_disagreement_p95 <= 0.6311
|   |   |--- class: 0
|   |--- candidate_disagreement_p95 >  0.6311
|   |   |--- class: 0
|--- GMQ_behavior_rate >  0.0550
|   |--- detector_like_P3_rate <= 0.0150
|   |   |--- GMQ_behavior_rate <= 0.2400
|   |   |   |--- class: 1
|   |   |--- GMQ_behavior_rate >  0.2400
|   |   |   |--- class: 0
|   |--- detector_like_P3_rate >  0.0150
|   |   |--- compensated_iou_mean <= 0.2211
|   |   |   |--- class: 1
|   |   |--- compensated_iou_mean >  0.2211
|   |   |   |--- class: 0


Top split/importances:
- GMQ_behavior_rate: 0.6651
- detector_like_P3_rate: 0.2063
- compensated_iou_mean: 0.1024
- candidate_disagreement_p95: 0.0263
```

## Top Recommendations

| logic_candidate                                              |   rank_score |   expected_FMeasure_gain_signal |   expected_Event_F1_gain_signal |   FPS_signal |   P95_cost_signal |   robustness_category_coverage | implementation_risk   | recommended_rule                                                                                                                                                                |
|:-------------------------------------------------------------|-------------:|--------------------------------:|--------------------------------:|-------------:|------------------:|-------------------------------:|:----------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PTZ detector-like P3 floor on high GMQ disagreement/residual |       0.6910 |                          0.1676 |                         -0.1296 |       0.3149 |           -0.1736 |                         1.0000 | medium                | In PTZ or confirmed camera motion, require periodic detector-like P3 when candidate disagreement/residual is high; block lightweight P3/reuse until compensated trust recovers. |
| Restrict GMQ behavior outside confirmed camera motion        |       0.5583 |                          0.1337 |                          0.1352 |       0.0290 |            0.0252 |                         1.0000 | low-medium            | Make GMQ logging-only outside confirmed camera motion; allow behavioral changes in non-PTZ only for event-risk or low-framerate-risk.                                           |
| Keep Phase 5B fast path for non-PTZ stable scenes            |       0.2125 |                          0.0274 |                          0.0543 |       0.1537 |           -0.0024 |                         1.0000 | low                   | Preserve FAST/ACC reuse where disagreement, residual, and event-risk are low; add hard exits to detector-like refresh for lowFramerate/night/shadow active events.              |
| Learned teacher-student policy with safety labels            |       0.0351 |                          0.1218 |                          0.1191 |      -0.0877 |            0.0621 |                         1.0000 | medium-high           | Train a small policy on empirical action outcomes, but keep deterministic guards for compensated trust, detector cadence, PTZ, low-framerate, and event continuity.             |
| Low-framerate cadence and event-veto floor                   |      -0.0743 |                         -0.2376 |                          0.0365 |       0.5116 |           -0.1668 |                         1.0000 | low-medium            | In lowFramerate and active-event windows, limit reuse age and closed-empty outputs; refresh detector/P3 before event masks go stale.                                            |

## Implementation Implications

1. Treat compensated IoU as the primary trust signal; it has the strongest positive FMeasure relationship in this mining pass.
2. When compensated trust is low or candidate disagreement is high, block reuse and lightweight P3 behavior.
3. When `frames_since_last_detector` is high under confirmed camera motion or low-framerate risk, enforce a detector-like refresh.
4. Outside confirmed camera motion, make GMQ logging-only unless event-risk or low-framerate-risk is active.
5. Do not treat `LEGACY_SAFE_P3_GUARD` as automatically safe; it is safe only when it preserves detector-like refresh cadence.
6. Prefer the Phase 5B fast path for stable non-PTZ scenes with low disagreement, good compensated trust, and no active event risk.

## Answers

1. Positive FMeasure correlations: compensated_iou_p95 (0.53), compensated_iou_mean (0.37), FAST_rate (0.11), legacy_safe_rate (0.08), motion_comp_behavior_rate (0.07).
2. Negative FMeasure correlations: avg_frames_since_last_detector (-0.40), candidate_disagreement_mean (-0.35), low_framerate_guard_rate (-0.34), event_hard_veto_rate (-0.16), GMQ_behavior_rate (-0.15).
3. High-mean-F PTZ actions: LIGHTWEIGHT_MASK_ACC (0.771), DETECT_ACC (0.660), FALLBACK_P3_GUARD (0.621), FALLBACK_P3_POLICY (0.412).
4. Dangerous PTZ actions: CLOSED_EMPTY_ACC (0.000), REUSE_ACC (0.041), LIGHTWEIGHT_MASK_P3_FALLBACK (0.128), LEGACY_SAFE_P3_GUARD (0.172), other (0.348).
5. Non-PTZ regression predictors: low_framerate_guard_rate (-0.80), final_sanitizer_rate (-0.34), event_hard_veto_rate (-0.33), detector_floor_rate (-0.32), avg_frames_since_last_detector (-0.31).
6. Use the P3-safe detector floor when PTZ/camera motion is confirmed and candidate disagreement, residual ratio, low-framerate cadence risk, or active-event veto risk is high.
7. Keep Phase 5B fast path in stable non-PTZ scenes with low disagreement/residual and no event hard-veto; it is a speed tool, not a PTZ substitute.
8. Yes, restrict GMQ behavior outside confirmed camera motion; outside PTZ/camera-motion it should be logging-only unless event-risk or low-framerate-risk is active.
9. A learned teacher-student policy is justified as a second-layer ranker because action outcomes are separable, but only with deterministic compensated-trust and detector-cadence guards.
10. Top 3 rules: 1) PTZ detector-like P3 floor on high GMQ disagreement/residual; 2) Restrict GMQ behavior outside confirmed camera motion; 3) Keep Phase 5B fast path for non-PTZ stable scenes.

## Interpretation

The statistics reinforce the targeted diagnosis: compensated trust and detector-like refresh cadence are the safe accuracy levers, while lightweight P3, reuse, closed-empty behavior, legacy-safe behavior, and broad GMQ interventions become dangerous when PTZ/global motion or sparse-frame cadence is present.

The next implementation should prioritize a narrow deterministic rule stack before expanding the learned policy: confirm camera motion, trust compensated IoU first, require detector-like refresh when trust or cadence fails, invalidate reuse/lightweight masks after jumps, keep GMQ logging-only outside confirmed motion unless risk is active, and leave Phase 5B fast behavior active in stable non-PTZ scenes.
