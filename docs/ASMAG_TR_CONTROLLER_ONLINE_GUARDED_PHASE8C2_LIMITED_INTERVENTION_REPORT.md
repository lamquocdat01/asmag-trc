# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2 Limited Intervention Report

Date: 2026-05-12

## 1. Phase 8C-1F rationale

Phase 8C-1F found that event/foreground risk closed the cubicle gap in post-hoc analysis:

- Cubicle recall: 1.0000.
- Cubicle normal warning rate: 0.3049.
- BridgeEntry event recall: 1.0000.
- Aggressive guard-gated budget simulation:
  - hard-video known safety-event recall: 0.9788.
  - cubicle recall: 1.0000.
  - simulated intervention rate: 0.2325.
  - simulated detector request rate: 0.2325.
  - deterministic guard alignment: 1.0000.
  - over-intervention risk: 0.0000.
  - normal-frame interventions: 0.

This made Phase 8C-2 conditionally allowed as a narrow design candidate, but only with deterministic guard gating, explicit budgets, no broad AI action selection, and intervention disabled by default.

## 2. Intervention implemented

Implemented Phase 8C-2 only for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`.

The runtime path uses lightweight sub-risk and event/foreground signals:

- `event_foreground_risk`
- `foreground_loss_risk`
- `event_continuity_risk`
- `detector_refresh_needed_for_event`
- `closed_empty_risk`
- `reuse_risk`
- `lightweight_p3_risk`
- `legacy_cadence_risk`
- `detector_needed`

The broad `unsafe_action` model is not used in the runtime intervention path. PTZ action ranking and direct AI action selection remain disabled.

Permitted runtime interventions are limited to:

- blocking `CLOSED_EMPTY_*` into a detector refresh when guarded and budgeted.
- blocking `REUSE_*` into a detector refresh when guarded and budgeted.
- blocking `LIGHTWEIGHT_MASK_P3_FALLBACK` into `FALLBACK_P3_GUARD` or detector refresh when guarded and budgeted.
- requesting detector refresh when event/foreground or detector-needed risk is high, deterministic guard is active, and budget allows.

## 3. Safety guard design

Intervention is controlled by explicit config flags:

- `ai_intervention_enabled`
- `ai_intervention_mode: guard_gated_budgeted`
- `ai_intervention_budget_profile: aggressive_guard_gated`
- `ai_intervention_require_deterministic_guard: true`
- `ai_intervention_allow_direct_action_selection: false`
- `ai_intervention_allow_ptz_action_ranking: false`

Default guarded smoke config keeps `ai_intervention_enabled: false`.

The new intervention smoke config is separate:

- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention.yaml`
- output folder: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention/`

The original non-intervention smoke output folder was not overwritten.

## 4. Budget design

The implemented aggressive guard-gated budget profile matches the Phase 8C-1F candidate:

| budget field | value |
| --- | ---: |
| max detector requests per 100 frames | 80 |
| min detector interval frames | 1 |
| max reuse blocks per 100 frames | 40 |
| max lightweight blocks per 100 frames | 15 |
| event override budget | 100 |
| ptz override budget | 100 |

Runtime logs include guard state, guard reason, no-guard blocks, budget remaining, budget blocks, cadence blocks, original action, final action, detector requests, and intervention type.

## 5. Smoke intervention results

Validation commands run:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention
```

The smoke intervention run completed 32/32 jobs with 0 failed jobs.

Aggregate comparison from `asmag_tr_final_comparison.csv`:

| pipeline | FMeasure | Event_F1 | Activation | Avg_FPS | P95 latency ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| P3_MOG2 | 0.5063 | 0.6412 | 0.6600 | 81.5018 | 550.3541 |
| ASMAG_TR_CONTROLLER | 0.5063 | 0.6412 | 0.6600 | 75.9921 | 597.0975 |
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 12.5777 | 667.7749 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4449 | 0.5774 | 1.1113 | 9.4917 | 896.7722 |

The intervention run improves aggregate FMeasure and Event_F1 over `ONLINE_CALIBRATED` in this smoke folder, but fails runtime cost gates badly.

AI intervention summary:

| metric | value |
| --- | ---: |
| frames | 800 |
| intervention rate | 0.71625 |
| detector request rate | 0.70000 |
| reuse block rate | 0.11125 |
| lightweight block rate | 0.05750 |
| closed-empty block rate | 0.14500 |
| action change rate | 0.50000 |
| deterministic guard alignment | 1.00000 |
| normal-frame intervention count | 467 |
| known-event intervention count | 106 |
| budget blocked rate | 0.09625 |
| cadence blocked rate | 0.00000 |

Budget usage by video shows detector budget saturation on multiple videos:

| video | detector requests | reuse blocks | lightweight blocks | budget blocked frames |
| --- | ---: | ---: | ---: | ---: |
| continuousPan | 80 | 0 | 0 | 20 |
| twoPositionPTZCam | 80 | 27 | 12 | 7 |
| bridgeEntry | 80 | 1 | 0 | 20 |
| tramCrossroad_1fps | 76 | 40 | 0 | 24 |
| turbulence2 | 69 | 2 | 15 | 6 |
| backdoor | 65 | 0 | 8 | 0 |
| cubicle | 57 | 8 | 11 | 0 |
| fountain02 | 53 | 11 | 0 | 0 |

## 6. Focus videos

BridgeEntry:

- Intervention rate: 0.81.
- Detector request rate: 0.80.
- Event FN count: 0.
- Closed-empty final count: 0.
- FMeasure: 0.2200.
- Event_F1: 0.9744.
- P95 latency delta vs `ONLINE_CALIBRATED`: +158.90 ms.

Cubicle:

- Intervention rate: 0.58.
- Detector request rate: 0.57.
- Known-event recall in intervention logs: 0.7895.
- Event FN count: 3.
- Closed-empty final count: 0.
- FMeasure: 0.1945, down 0.0290 vs `ONLINE_CALIBRATED`.
- Event_F1: 0.8613, up 0.0908 vs `ONLINE_CALIBRATED`.
- P95 latency delta vs `ONLINE_CALIBRATED`: +227.40 ms.

ContinuousPan:

- Intervention rate: 0.80.
- Detector request rate: 0.80.
- Known-event recall in intervention logs: 0.7826.
- Event FN count: 0.
- Closed-empty final count: 0.
- FMeasure: 0.1341, down 0.1007 vs `ONLINE_CALIBRATED`.
- Event_F1: 0.2906, unchanged vs `ONLINE_CALIBRATED`.
- P95 latency delta vs `ONLINE_CALIBRATED`: +563.95 ms.

## 7. Comparison with non-intervention guarded smoke

The previous non-intervention guarded smoke folder reported:

| pipeline | FMeasure | Event_F1 | Activation | Avg_FPS | P95 latency ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED, non-intervention | 0.2991 | 0.5808 | 0.3963 | 25.6726 | 415.1758 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED, intervention | 0.4449 | 0.5774 | 1.1113 | 9.4917 | 896.7722 |

The intervention path improves aggregate FMeasure relative to the prior guarded non-intervention smoke, but loses a little Event_F1 and causes a large activation, FPS, and latency regression. This is not acceptable for Phase 8C-2.

## 8. Pass/fail decision

Phase 8C-2 smoke fails.

Acceptance criteria:

| criterion | result | pass |
| --- | --- | --- |
| no crashes | 32/32 completed, 0 failed | yes |
| intervention logs present | summary/video/budget/action/safety files written | yes |
| deterministic guard alignment >= 0.95 | 1.0000 | yes |
| normal-frame interventions zero or near zero | 467 | no |
| runtime intervention rate < 0.50 | 0.71625 | no |
| aggregate FMeasure >= `ONLINE_CALIBRATED` | 0.4449 >= 0.4155 | yes |
| aggregate Event_F1 >= `ONLINE_CALIBRATED` | 0.5774 >= 0.5636 | yes |
| FPS >= 25 target | 9.4917 | no |
| P95 <= `ONLINE_CALIBRATED` + 30 ms | 896.77 > 697.77 | no |
| bridgeEntry final CLOSED_EMPTY event FN remains 0 | event FN 0 | yes |
| cubicle does not regress materially | FMeasure down and event FN 3 | no |
| continuousPan does not collapse | large FMeasure and latency regression | no |
| non-intervention guarded smoke folder untouched | separate output folder used | yes |

## 9. Root cause

The post-hoc budget simulation was too optimistic for live runtime intervention. In the live implementation, the aggressive profile allows up to 80 detector requests per 100 frames and the event/foreground detector path fires on many deterministic-guard frames. That keeps guard alignment perfect, but it does not keep interventions selective.

The main runtime failure mode is detector-heavy over-intervention:

- detector request rate is 0.7000.
- activation rises to 1.1113.
- normal-frame interventions reach 467 frames.
- P95 latency reaches 896.77 ms.
- continuousPan and cubicle suffer material cost/quality regressions.

The deterministic guard gate is necessary but not sufficient. The detector request decision must be much narrower than "risk high while guard active".

## 10. Next fix

Keep Phase 8C-2 blocked. Recommended next patch:

- Split detector requests from action blocks.
- Require `detector_refresh_needed_for_event` specifically for detector refresh, not generic `event_foreground_risk`.
- Reduce detector budget from 80 per 100 frames to a small cadence budget, likely 10-20 per 100 frames with a minimum interval.
- Add a normal-frame suppressor using known event/foreground continuity features.
- Test a dry-run intervention log mode before applying live detector refresh.
- Re-run guarded smoke only after the detector gate and budget are tightened.

## 11. Safety confirmation

- AI intervention remains disabled by default in the guarded smoke config.
- The only enabled intervention config is the new explicit smoke config.
- No old `ONLINE_CALIBRATED` code path was modified.
- No P1/P2/P3/FAST/`ASMAG_TR_CONTROLLER` implementation was modified.
- No frozen CDnet2014 v1.6 outputs were overwritten.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- PTZ-targeted is not allowed after this failed Phase 8C-2 smoke.
