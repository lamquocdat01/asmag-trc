# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2B Sparse Intervention Report

Date: 2026-05-12

## 1. Phase 8C-2 failure recap

Phase 8C-2 implemented guard-gated budgeted limited intervention and completed smoke validation, but failed acceptance:

- Smoke completed 32/32, 0 failed.
- Guard alignment: 1.0000.
- Aggregate FMeasure/Event_F1 beat `ONLINE_CALIBRATED`.
- Intervention rate: 0.71625, too high.
- Detector request rate: 0.70000, too high.
- Normal-frame interventions: 467, too high.
- Activation: 1.1113, too high.
- Avg_FPS: 9.49, too low.
- P95 latency: 896.77 ms, too high.
- Cubicle regressed and continuousPan collapsed.

Root cause: generic event/foreground risk was allowed to trigger detector refresh, so the live path became detector-heavy even though deterministic guard alignment was perfect.

## 2. Detector/action-block split

Phase 8C-2B changes the intervention policy to action-block-first:

1. Block `CLOSED_EMPTY_*` only under deterministic guard plus closed-empty/event context.
2. Block `REUSE_*` only under deterministic guard plus `reuse_risk` and event context.
3. Block `LIGHTWEIGHT_MASK_P3_FALLBACK` only under deterministic guard plus `lightweight_p3_risk` and event context.
4. Request detector only when the detector-specific signal is high:
   - `detector_refresh_needed_for_event`, or
   - `detector_needed` under event/foreground context.

`event_foreground_risk` alone no longer requests detector refresh.

New logs include:

- `ai_detector_request_source`
- `ai_detector_request_blocked_no_refresh_model`
- `ai_detector_request_blocked_interval`
- `ai_detector_request_blocked_budget`
- `ai_action_block_first_active`
- `ai_block_only_no_detector`
- `ai_safe_replacement_source`
- `ai_detector_last_resort_used`
- `ai_intervention_dry_run`

Dry-run mode logs proposed interventions through the intervention fields but does not alter final actions.

## 3. Sparse budget design

Added budget profile `sparse_detector_guarded`:

| budget field | value |
| --- | ---: |
| max detector requests per 100 frames | 15 |
| min detector interval frames | 4 |
| max reuse blocks per 100 frames | 30 |
| max lightweight blocks per 100 frames | 12 |
| max closed-empty blocks per 100 frames | 30 |
| event override budget | 40 |
| ptz override budget | 30 |

The old `aggressive_guard_gated` 80-per-100 detector profile was not used for 8C-2B.

A normal-frame suppressor was also added. If deterministic guard is active but there is no active event, no foreground-loss risk, no detector-refresh risk, no closed-empty risk, and no explicit safety event, detector request is suppressed and only logged.

## 4. Validation run

Validation commands run:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2b_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2b_dryrun
```

Dry-run smoke completed 32/32 jobs with 0 failed jobs.

Live smoke was not run.

## 5. Dry-run result

Aggregate dry-run proposal summary:

| metric | value |
| --- | ---: |
| frames | 800 |
| dry-run rate | 1.0000 |
| proposed intervention rate | 0.2000 |
| proposed detector request rate | 0.0450 |
| block-only rate | 0.1550 |
| detector last-resort rate | 0.02125 |
| normal-frame proposed interventions | 0 |
| known-event proposed interventions | 160 |
| guard alignment | 1.0000 |
| detector budget block rate | 0.0000 |
| detector interval block rate | 0.4875 |
| detector no-refresh-model block rate | 0.23375 |
| sparse detector budget active rate | 1.0000 |

The aggregate selectivity gates pass: proposed intervention and detector rates are both below targets, normal-frame proposed interventions are zero, guard alignment is perfect, and block-only intervention is used before detector.

Per-video proposed rates:

| video | proposed intervention | proposed detector | block-only | normal proposed | detector budget used |
| --- | ---: | ---: | ---: | ---: | ---: |
| continuousPan | 0.05 | 0.01 | 0.04 | 0 | 1 |
| twoPositionPTZCam | 0.10 | 0.03 | 0.07 | 0 | 3 |
| fountain02 | 0.20 | 0.05 | 0.15 | 0 | 5 |
| tramCrossroad_1fps | 0.07 | 0.00 | 0.07 | 0 | 0 |
| bridgeEntry | 0.33 | 0.10 | 0.23 | 0 | 10 |
| backdoor | 0.37 | 0.09 | 0.28 | 0 | 9 |
| cubicle | 0.20 | 0.03 | 0.17 | 0 | 3 |
| turbulence2 | 0.28 | 0.05 | 0.23 | 0 | 5 |

Dry-run aggregate performance stayed cost-safe because no proposed intervention was applied:

| pipeline | FMeasure | Event_F1 | Activation | Avg_FPS | P95 latency ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 20.0482 | 356.4973 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.4172 | 0.5886 | 0.5550 | 30.8182 | 314.5554 |

## 6. Live-run gate

Live smoke was not allowed.

Reasons:

- Cubicle proposed known-event recall is only 0.2020.
- Cubicle detector proposal rate is sparse at 0.03, but the dry-run proposal does not demonstrate the requested cubicle protection improvement.
- Backdoor proposed intervention rate is 0.37, slightly above the 0.35 dry-run selectivity target at the per-video level.

The sparse policy fixed the Phase 8C-2 over-intervention failure, but became too conservative for cubicle. This means live action changes are not yet justified.

## 7. Pass/fail decision

Phase 8C-2B does not pass as a live intervention candidate.

Dry-run criteria:

| criterion | result | pass |
| --- | --- | --- |
| no crashes | 32/32 completed, 0 failed | yes |
| guard alignment >= 0.95 | 1.0000 | yes |
| proposed intervention rate < 0.35 | 0.2000 | yes |
| proposed detector request rate < 0.25 | 0.0450 | yes |
| normal-frame proposed interventions near 0 | 0 | yes |
| block-only used before detector request | block-only rate 0.1550 | yes |
| detector budget not saturated everywhere | max per video 10/15 | yes |
| cubicle known-event protection improves | proposed recall 0.2020 | no |

Because the dry-run live gate failed for cubicle, live smoke was not run.

## 8. Next fix

Recommended next patch:

- Add a cubicle/event-continuity override that can raise cubicle known-event proposal coverage without using broad detector requests.
- Keep detector refresh sparse; prefer block-only or deterministic fallback first.
- Consider a separate `cubicle_event_foreground_block` threshold using `event_foreground_risk` plus foreground-loss/active-event continuity rather than detector refresh.
- Re-run dry-run smoke only after cubicle coverage is improved while preserving zero normal-frame proposals.

## 9. Safety confirmation

- Default guarded behavior remains intervention-disabled: `ai_intervention_enabled: false`.
- Dry-run computed and logged proposed interventions but did not alter final actions.
- Live intervention smoke was not run.
- The previous Phase 8C-2 intervention output folder was not overwritten.
- The non-intervention guarded smoke folder was not overwritten.
- old `ONLINE_CALIBRATED` was not modified.
- P1/P2/P3/FAST/`ASMAG_TR_CONTROLLER` were not modified.
- Frozen CDnet2014 v1.6 outputs were not overwritten.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- PTZ-targeted remains not allowed.
