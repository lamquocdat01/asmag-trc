# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-1E Sub-Risk Tuning Report

Date: 2026-05-12

## 1. Phase 8C-1D recap

Phase 8C-1D replaced the broad runtime `unsafe_action` shadow model with lightweight sub-risk shadows. The smoke run completed 32/32 with 0 failures, missing features stayed at 0.0, and sub-risk shadow latency improved to 8.15 / 31.73 ms mean/P95 overall and 22.41 / 38.97 ms on prediction frames.

The remaining blockers were recall/selectivity rather than runtime cost:

- Known safety-event sub-risk warning rate: 0.9579.
- Hard-video sub-risk warning rate: 0.8650.
- `shadow/cubicle` hard-video warning rate: 0.64.
- Intervention remained disabled and Phase 8C-2 stayed blocked.

## 2. Threshold tuning outputs

Created `tools/tune_phase8c_subrisk_thresholds.py`.

Generated:

- `outputs/phase8c_subrisk_models/threshold_tuning/subrisk_threshold_sweep.csv`
- `outputs/phase8c_subrisk_models/threshold_tuning/subrisk_threshold_recommendations.csv`
- `outputs/phase8c_subrisk_models/threshold_tuning/cubicle_threshold_analysis.csv`
- `outputs/phase8c_subrisk_models/threshold_tuning/hard_video_threshold_analysis.csv`
- `outputs/phase8c_subrisk_models/threshold_tuning/cubicle_diagnosis.csv`
- `outputs/phase8c_subrisk_models/threshold_tuning/ai_shadow_drift_simulation.csv`
- `outputs/phase8c_subrisk_models/threshold_tuning/ai_shadow_drift_summary.csv`
- `outputs/phase8c_subrisk_models/threshold_tuning/subrisk_runtime_policy_recommendation.csv`

No smoke rerun was required because no runtime logging, model export, or config behavior was changed.

## 3. Threshold tuning results

The action sub-risk thresholds were already selective, but they do not recover cubicle known events. The only threshold lever that recovers cubicle is lowering the `detector_needed` threshold, but that produces detector-heavy behavior.

| target | threshold | flag_rate | known_event_recall | hard_video_recall | cubicle_recall | normal_flag_rate | recommendation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| closed_empty_risk | 0.9999 | 0.0300 | 0.0158 | 0.0343 | 0.0000 | 0.0344 | deterministic_guard_only |
| reuse_risk | 0.9999 | 0.3175 | 0.4632 | 0.3457 | 0.0000 | 0.2721 | shadow_only |
| lightweight_p3_risk | 0.9900 | 0.0300 | 0.0263 | 0.0343 | 0.0000 | 0.0311 | deterministic_guard_only |
| legacy_cadence_risk | 0.9900 | 0.0275 | 0.1158 | 0.0314 | 0.0000 | 0.0000 | deterministic_guard_only |
| detector_needed | 0.8500 | 0.7338 | 0.6789 | 0.7271 | 1.0000 | 0.7508 | shadow_only |
| lightweight_acc_allowed | 0.2100 | 0.0675 | 0.1263 | 0.0729 | 0.0000 | 0.0492 | needs_retrain |

The `detector_needed=0.85` threshold is a shadow A/B recall candidate only. It should not be used for limited intervention because it creates excessive normal-frame detector requests.

## 4. Cubicle diagnosis

Cubicle has 18 known guarded safety-event frames. Missing features remained 0.0, so the miss is not caused by schema or feature extraction.

Cubicle known-event feature context:

- Foreground risk mean: 1.0.
- Active event memory rate: 1.0.
- Global motion proxy mean: 0.867.

Model behavior:

- `closed_empty_risk`: cubicle recall 0.0 at 0.9999; known-event P90 score is 0.9997, just below threshold.
- `reuse_risk`: cubicle recall 0.0 at 0.9999; known-event P50 score is 0.9988 and P90 is 0.9996.
- `lightweight_p3_risk`: cubicle recall 0.0 at 0.99; known-event score is about 0.9705.
- `legacy_cadence_risk`: no useful cubicle signal.
- `detector_needed`: cubicle recall 1.0 at 0.85, but cubicle all-frame flag rate becomes 0.88.

Conclusion: cubicle is better represented as foreground/event risk than camera-motion risk. Threshold-only recovery requires detector-heavy behavior and is not intervention-safe. A deterministic event/foreground guard should dominate cubicle handling until a retrained event/foreground sub-risk model is available.

## 5. Shadow A/B drift simulation

The A/B simulation did not change runtime actions. It only wrote simulated fields:

- `ai_sim_would_block_action`
- `ai_sim_would_request_detector`
- `ai_sim_intervention_type`
- `ai_sim_original_action`
- `ai_sim_recommended_safe_action`
- `ai_sim_intervention_allowed_by_deterministic_guard`

Aggregate simulated intervention result using the recall-candidate thresholds:

| metric | value |
| --- | ---: |
| simulated_intervention_rate | 0.83125 |
| simulated_detector_request_rate | 0.73375 |
| simulated_reuse_block_rate | 0.18625 |
| simulated_lightweight_block_rate | 0.00125 |
| simulated_closed_empty_block_rate | 0.00000 |
| interventions_in_known_hard_video_frames | 586 |
| interventions_in_known_safety_event_frames | 184 |
| interventions_in_normal_frames | 481 |
| deterministic_guard_aligned_intervention_rate | 0.27669 |
| over_intervention_risk_score | 0.60125 |

Hard-video warning with recall-candidate thresholds:

| video | subrisk_any_recall | subrisk_or_detector_recall | normal_frame_warning_rate |
| --- | ---: | ---: | ---: |
| ALL_HARD_VIDEOS | 0.4286 | 0.8871 | 0.8513 |
| bridgeEntry | 0.5200 | 0.9100 | 0.8933 |
| continuousPan | 0.7000 | 1.0000 | 1.0000 |
| cubicle | 0.3000 | 0.9700 | 0.9634 |
| fountain02 | 0.3600 | 0.6400 | 0.6023 |
| tramCrossroad_1fps | 0.4900 | 0.7900 | 0.7561 |
| turbulence2 | 0.3000 | 0.9000 | 0.9000 |
| twoPositionPTZCam | 0.3300 | 1.0000 | 1.0000 |

This does not pass drift control. The recall candidate still misses the hard-video target of 0.90 overall and creates unacceptable over-intervention risk.

## 6. Runtime recommendation

Do not update guarded runtime config for Phase 8C-1E. The existing 8C-1D shadow thresholds are safer for logging, and the improved cubicle recall candidate is too detector-heavy.

Recommended policy state:

- `closed_empty_risk`: deterministic guard only.
- `reuse_risk`: shadow only.
- `lightweight_p3_risk`: deterministic guard only.
- `legacy_cadence_risk`: deterministic guard only.
- `detector_needed`: shadow only; retrain or add cadence/budget constraints before intervention.
- `lightweight_acc_allowed`: needs retrain.

Recommended next model work:

- Add or retrain an event/foreground sub-risk target for cubicle-like scenes.
- Add detector-request budget/cadence constraints to the shadow A/B simulator.
- Calibrate per-video/category thresholds only as diagnostics, not intervention policy.

## 7. Phase 8C-2 decision

Phase 8C-2 limited intervention is still blocked.

Reasons:

- Hard-video warning improves only to 0.8871 under the recall-candidate A/B, below the 0.90 target.
- Cubicle can be recovered only by a detector-heavy threshold with 0.9634 normal-frame warning rate on cubicle.
- Aggregate simulated intervention rate is 0.83125, and 481 simulated interventions occur on normal frames.
- Only 27.67% of simulated interventions align with deterministic guard events.

## 8. Safety confirmation

- AI intervention remains disabled: `ai_shadow_behavior_enabled: false`.
- AI predictions and simulated interventions were not applied to final actions.
- old `ONLINE_CALIBRATED` was not modified.
- P1/P2/P3/FAST/`ASMAG_TR_CONTROLLER` were not modified.
- Frozen CDnet2014 v1.6 outputs were not overwritten.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- No smoke rerun was performed for 8C-1E because only post-hoc analysis outputs were added.

