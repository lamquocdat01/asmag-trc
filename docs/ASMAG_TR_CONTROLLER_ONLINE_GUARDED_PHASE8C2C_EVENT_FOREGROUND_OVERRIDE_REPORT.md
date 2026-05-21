# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2C Event-Foreground Override Report

Date: 2026-05-12

## 1. 8C-2 and 8C-2B recap

Phase 8C-2 proved that guarded intervention can improve aggregate accuracy, but it failed the live acceptance gate because it became detector-heavy:

- Intervention rate: 0.71625.
- Detector request rate: 0.70000.
- Normal-frame interventions: 467.
- Activation: 1.1113.
- Avg_FPS: 9.4917.
- P95 latency: 896.7722 ms.
- Cubicle regressed and continuousPan collapsed.

Phase 8C-2B fixed the detector-heavy behavior with sparse detector budgeting, action-block-first behavior, and a normal-frame suppressor:

- Proposed intervention rate: 0.2000.
- Proposed detector request rate: 0.0450.
- Block-only rate: 0.1550.
- Normal-frame proposed interventions: 0.
- Guard alignment: 1.0000.
- Detector budget usage: max 10/15 per video.

8C-2B did not proceed to live because cubicle proposed known-event recall was only 0.2020.

## 2. Event/foreground block-only override

Phase 8C-2C adds a guarded event/foreground block-only override on top of the 8C-2B sparse policy. The override is enabled only in the new 2C dry-run/live configs:

```yaml
online_controller_guarded:
  ai_event_foreground_block_only_override_enabled: true
  ai_event_foreground_block_only_threshold: 0.95
  ai_event_foreground_requires_active_memory: true
  ai_event_foreground_allow_detector_direct: false
  ai_event_foreground_detector_requires_refresh_model: true
```

The override requires deterministic guard alignment, a high event/foreground score, and active-event memory or foreground risk. It can block `CLOSED_EMPTY`, `REUSE_ACC`, and `LIGHTWEIGHT_MASK_P3_FALLBACK` into existing deterministic sanitizer/fallback paths. It does not request a detector from generic event/foreground risk. Detector requests remain specific to `detector_refresh_needed_for_event`, budget, and interval constraints.

New logs:

- `ai_event_foreground_block_only_active`
- `ai_event_foreground_block_only_reason`
- `ai_event_foreground_block_only_no_detector`
- `ai_event_foreground_safe_replacement_source`
- `ai_detector_request_event_refresh_specific`
- `ai_detector_request_rejected_event_foreground_only`

## 3. Dry-run validation

Commands run:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2c_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2c_dryrun
```

Because `--max-jobs-per-run 8` limits each invocation to eight jobs, the dry-run command was resumed until all 32 smoke jobs completed.

Dry-run completed 32/32 jobs with 0 failed jobs.

Aggregate 2C dry-run proposal summary:

| metric | value |
| --- | ---: |
| proposed intervention rate | 0.3325 |
| proposed detector request rate | 0.0500 |
| block-only rate | 0.2825 |
| event/foreground block-only rate | 0.2750 |
| normal-frame proposed interventions | 0 |
| guard alignment | 1.0000 |
| cubicle proposed known-event recall | 0.3535 |
| cubicle normal-frame proposed interventions | 0 |
| bridgeEntry event FN | 0 |
| continuousPan proposed intervention rate | 0.0400 |
| detector budget block rate | 0.0000 |

Focus videos:

| video | proposed intervention | detector request | block-only | event/foreground block-only | known-event recall | event FN | detector budget used max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| continuousPan | 0.0400 | 0.0100 | 0.0300 | 0.0300 | 0.0400 | 0 | 1 |
| bridgeEntry | 0.3800 | 0.1500 | 0.2300 | 0.2300 | 0.3800 | 0 | 15 |
| cubicle | 0.3500 | 0.0500 | 0.3000 | 0.3000 | 0.3535 | 17 | 5 |

Aggregate dry-run guarded metrics:

| pipeline | FMeasure | Event_F1 | Activation | Avg_FPS | P95 latency ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| ONLINE_CALIBRATED | 0.4155 | 0.5636 | 0.6150 | 14.8397 | 489.4497 |
| ASMAG_TR_CONTROLLER_ONLINE_GUARDED | 0.3605 | 0.5811 | 0.4450 | 24.2342 | 417.2129 |

## 4. Live validation

Live smoke was not run.

The dry-run failed the live gate because cubicle proposed known-event recall was 0.3535, below the required 0.80. Several videos also reached proposed intervention rates of 0.38-0.40, so the override is broader than desired even though aggregate intervention rate remains below 0.35 and detector request rate remains low.

## 5. Pass/fail

Phase 8C-2C does not pass as a live intervention candidate.

| criterion | result | pass |
| --- | --- | --- |
| no crashes | 32/32 completed, 0 failed | yes |
| guard alignment >= 0.95 | 1.0000 | yes |
| proposed intervention rate < 0.35 | 0.3325 | yes |
| proposed detector request rate < 0.15 | 0.0500 | yes |
| normal-frame proposed interventions near 0 | 0 | yes |
| cubicle proposed known-event recall >= 0.80 | 0.3535 | no |
| bridgeEntry event FN protected | event FN 0 | yes |
| continuousPan proposed intervention does not explode | 0.0400 | yes |
| detector budget not saturated everywhere | bridgeEntry reached 15/15; not saturated everywhere | mixed |

## 6. Root cause and next fix

The event/foreground block-only override is correctly detector-sparse, but the current block-only action surface is too narrow for cubicle. Cubicle known-event frames often already sit on detector-like or fallback actions rather than `CLOSED_EMPTY`, `REUSE_ACC`, or `LIGHTWEIGHT_MASK_P3_FALLBACK`, so the override cannot lift cubicle proposal recall to 0.80 without either:

- counting safe detector-like/fallback actions as protected proposals, or
- adding a more specific cubicle/event-continuity replacement path that can convert detector-like event frames into no-detector safe fallback proposals without increasing broad intervention elsewhere.

The next fix should add a tighter cubicle-like event continuity gate, probably using high event/foreground score plus active-event memory plus non-PTZ/no-camera-motion context, and a separate cap for event/foreground fallback proposals. It should avoid applying the generic event/foreground override broadly to bridgeEntry, fountain02, backdoor, turbulence2, or lowFramerate.

## 7. Safety confirmation

- Default guarded smoke config remains intervention-disabled: `configs/asmag_tr_controller_online_guarded_cdnet_smoke.yaml` has `ai_intervention_enabled: false`.
- New 8C-2C configs write to separate output folders.
- 8C-2B outputs were not overwritten.
- Dry-run computed proposed interventions but did not intentionally apply live action changes.
- Live 8C-2C smoke was not run.
- old `ONLINE_CALIBRATED` was not modified.
- P1/P2/P3/FAST/`ASMAG_TR_CONTROLLER` were not modified.
- Frozen CDnet2014 v1.6 outputs were not overwritten.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- PTZ-targeted remains not allowed.
