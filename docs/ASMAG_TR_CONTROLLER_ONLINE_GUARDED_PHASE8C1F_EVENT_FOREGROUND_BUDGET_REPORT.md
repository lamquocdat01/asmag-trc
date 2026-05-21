# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-1F Event/Foreground Budget Report

Date: 2026-05-12

## 1. Phase 8C-1E recap

Phase 8C-1E showed that action sub-risk thresholds alone were not enough:

- Hard-video recall candidate: 0.8871, below the 0.90 target.
- Hard-video normal-frame warning rate: 0.8513, too high.
- Cubicle could be recovered by `detector_needed=0.85`, but cubicle normal-frame warning rose to 0.9634.
- Simulated intervention rate: 0.83125.
- Simulated detector request rate: 0.73375.
- Normal-frame simulated interventions: 481.
- Deterministic-guard-aligned intervention rate: 0.2767.

The main interpretation was correct: cubicle-like cases need event/foreground risk, and detector requests need deterministic guard alignment plus budgets.

## 2. Event/foreground label definitions

Created `tools/train_phase8c_event_foreground_risk.py`.

Labels were derived from existing guarded smoke frame logs. Evaluation metrics such as `Recall` and `FMeasure` were used only for offline label construction, not as model features.

Targets:

- `event_foreground_risk`: deterministic safety guard is active, or active event/continuity plus strong foreground and quality-loss/closed-empty risk.
- `foreground_loss_risk`: foreground risk plus active event and quality loss, known guard, closed-empty block, or sanitizer event.
- `event_continuity_risk`: known guard or active event/continuity with quality loss, stale detector cadence, or stale active prediction.
- `detector_refresh_needed_for_event`: known guard or event/foreground continuity plus stale detector/quality-loss/closed-empty refresh need.

Runtime-observable features included active-event memory, foreground risk, global-motion proxy, event-continuity risk, frames since detector, reuse age/confidence, candidate area/quality/temporal-IoU signals, low-light/final-sanitizer flags, closed-empty/event counters, and trust signals.

## 3. Model results

Only lightweight candidates were trained: logistic regression and shallow decision tree. No random forest was used.

Recommended event/foreground models:

| target | model | threshold | positives | positive_rate |
| --- | --- | ---: | ---: | ---: |
| event_foreground_risk | logistic_regression | 0.950000 | 425 | 0.53125 |
| foreground_loss_risk | shallow_decision_tree | 0.743286 | 434 | 0.54250 |
| event_continuity_risk | logistic_regression | 0.987949 | 681 | 0.85125 |
| detector_refresh_needed_for_event | logistic_regression | 0.986630 | 682 | 0.85250 |

Leave-one-video mean model metrics:

| target | best lightweight model | precision | recall | F1 | balanced_accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| event_foreground_risk | logistic_regression | 0.8013 | 0.8209 | 0.8086 | 0.8567 |
| foreground_loss_risk | shallow_decision_tree | 0.7856 | 0.8750 | 0.8240 | 0.7393 |
| event_continuity_risk | logistic_regression | 0.9420 | 0.8874 | 0.9058 | 0.8442 |
| detector_refresh_needed_for_event | logistic_regression | 0.9430 | 0.8717 | 0.8961 | 0.8394 |

Outputs:

- `outputs/phase8c_event_foreground_risk/event_foreground_model_results.csv`
- `outputs/phase8c_event_foreground_risk/event_foreground_threshold_sweep.csv`
- `outputs/phase8c_event_foreground_risk/event_foreground_feature_importance.csv`
- `outputs/phase8c_event_foreground_risk/event_foreground_runtime_recommendation.csv`
- `outputs/phase8c_event_foreground_risk/event_foreground_frame_scores.csv`

## 4. Cubicle analysis

Cubicle known safety-event frames: 18.

At recommended event/foreground thresholds:

| target | cubicle recall | cubicle normal warning | cubicle all-frame warning |
| --- | ---: | ---: | ---: |
| event_foreground_risk | 1.0000 | 0.3049 | 0.4300 |
| foreground_loss_risk | 1.0000 | 0.4756 | 0.5700 |
| event_continuity_risk | 0.9444 | 0.4024 | 0.5000 |
| detector_refresh_needed_for_event | 0.9444 | 0.4268 | 0.5200 |

The event/foreground model fixes the Phase 8C-1E cubicle gap without using the broad detector-needed threshold that caused 0.9634 cubicle normal-frame warnings. The best cubicle signal is `event_foreground_risk`: 1.0 recall with 0.3049 normal-frame warning before budget gating.

BridgeEntry event recall is 1.0 for all event/foreground targets. ContinuousPan remains broad at standalone warning thresholds, so it must be budgeted and deterministic-guard gated.

## 5. Budgeted drift simulation

Created `tools/simulate_phase8c_budgeted_intervention.py`.

The simulator still does not change runtime actions. It allows a simulated intervention only when:

1. AI sub-risk or event/foreground risk is high.
2. A deterministic guard condition is active.
3. Budget/cadence allows the intervention.

Budgets simulated:

| budget | max_detector_per_100 | min_detector_interval | max_reuse_blocks | max_lightweight_blocks | event_override_budget | ptz_override_budget |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| conservative | 12 | 8 | 8 | 3 | 10 | 12 |
| balanced | 30 | 3 | 25 | 8 | 45 | 45 |
| aggressive | 80 | 1 | 40 | 15 | 100 | 100 |

Aggregate results:

| budget | hard-known recall | cubicle recall | intervention rate | detector request rate | guard alignment | over-intervention risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| conservative | 0.2804 | 0.2222 | 0.0675 | 0.04125 | 1.0000 | 0.0000 |
| balanced | 0.5767 | 0.3889 | 0.1375 | 0.09500 | 1.0000 | 0.0000 |
| aggressive | 0.9788 | 1.0000 | 0.2325 | 0.23250 | 1.0000 | 0.0000 |

Important metric distinction:

- Guard-gated hard-video known-event recall for aggressive budget is 0.9788 and passes the decision target.
- Hard-video all-frame warning recall is only 0.2643 because the simulator intentionally refuses to intervene on normal hard-video frames unless a deterministic guard is active.

The aggressive budget produces 186 interventions on known safety-event frames and 0 interventions on normal frames.

## 6. Recommended budget policy

Recommended next-phase candidate: `aggressive`, but only as deterministic-guard-gated limited-intervention design.

Recommended policy constraints:

- Require deterministic guard active.
- Require event/foreground or sub-risk high.
- Allow detector refresh during deterministic event/foreground risk.
- Keep intervention rate bounded by per-video budget.
- Keep normal-frame interventions at zero.
- Keep AI behavior disabled until Phase 8C-2 implementation explicitly starts.

The conservative and balanced budgets are not preferred because they are safe but under-recall cubicle and hard-video known safety events.

## 7. Phase 8C-2 decision

Phase 8C-2 limited intervention is conditionally allowed as a next-phase design candidate, not enabled in 8C-1F.

The aggressive guard-gated budget meets the requested post-hoc decision criteria:

- Hard-video known safety-event recall: 0.9788, above 0.90.
- Cubicle recall: 1.0000, above 0.80.
- Deterministic-guard alignment: 1.0000, substantially above 0.2767.
- Over-intervention risk: 0.0000, substantially below 0.60125.
- Simulated intervention rate: 0.2325, below 0.50.
- Detector request rate: 0.2325, budgeted and explainable by deterministic guard plus event/foreground risk.

Before enabling any runtime intervention, Phase 8C-2 should implement this as a guarded, budgeted, shadow-first limited intervention with a required smoke validation gate.

## 8. Safety confirmation

- AI intervention remains disabled: `ai_shadow_behavior_enabled: false`.
- AI predictions and simulated interventions were not applied to final actions.
- old `ONLINE_CALIBRATED` was not modified.
- P1/P2/P3/FAST/`ASMAG_TR_CONTROLLER` were not modified.
- Frozen CDnet2014 v1.6 outputs were not overwritten.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- No smoke rerun was performed.

