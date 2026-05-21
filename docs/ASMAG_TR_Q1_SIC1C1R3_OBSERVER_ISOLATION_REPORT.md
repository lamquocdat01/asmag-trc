# ASMAG_TR_Q1_SIC1C1R3 Observer Isolation Report

Date: 2026-05-20

## 1. Scope and Safety Confirmation

Q1-SIC-1C1R3 was limited to the requested shadow-only observer isolation repair and the scoped 14-video residual-risk subset. No full CDnet, live run, live compare, targeted CDnet beyond the residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, Q1-SIC-1C2 snowFall enforcement, or Step 4E7-D2 port detector-retighten implementation was run.

Old Step 4D6, Step 4E4, Step 4E6, Q1-SIC-0, Q1-SIC-1, Q1-SIC-1A, Q1-SIC-1B, Q1-SIC-1C, Q1-SIC-1C1, Q1-SIC-1C1R, Q1-SIC-1C1R2, and audit output folders were not overwritten. The existing partial Q1-SIC-1C1R3 root was rerun as the active phase output root after resetting only its progress ledger.

## 2. Why Q1-SIC-1C1R3 Exists

Q1-SIC-1C1R2 was intended to be shadow-only, but the side-effect audit found broad behavior drift versus Q1-SIC-1C1R: 335 action-label deltas, 187 proposal deltas, 18 Q1-label deltas, snowFall frame 1150 drift to `CLOSED_EMPTY_ACC / FORCE_PROTECT_EVENT_MEMORY`, and parking regression to proposal `0.52000` with 10 unprotected FNs.

Q1-SIC-1C1R3 therefore restored Q1-SIC-1C1R as the behavioral base and moved detector-action telemetry to a post-decision observer built from copied row snapshots.

## 3. Files Modified

- `src/run_experiment.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun.yaml`
- `tools/verify_q1_sic1c1r3_observer_isolation.py`
- `docs/ASMAG_TR_Q1_SIC1C1R3_OBSERVER_ISOLATION_REPORT.md`
- `docs/DAILY_STATUS.md`

## 4. Config Created

Config:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun.yaml`

It is based on:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`

It does not inherit from the Q1-SIC-1C1R2 stable snapshot config. The old live detector-action probe and stable snapshot pressure memory are disabled in this phase, while the isolated observer is enabled.

## 5. Output Roots Created

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1c1r3_observer_isolation_verify/`

Verifier outputs:

- `q1_sic1c1r3_observer_isolation_summary.csv`
- `q1_sic1c1r3_observer_isolation_row_checks.csv`
- `q1_sic1c1r3_behavior_delta.csv`
- `q1_sic1c1r3_failure_classification.csv`

## 6. What Was Removed or Disabled from Q1-SIC-1C1R2

- `q1_sic_detector_action_probe_stable_snapshot_enabled` is disabled.
- `q1_sic_detector_action_probe_pressure_memory_active` stays 0 globally.
- `q1_sic_observer_pressure_memory_enabled` is disabled.
- The controller-instance pressure memory is not used for observer telemetry.
- The old live detector-action probe is bypassed when isolated observer mode is enabled.

## 7. Observer Isolation Design

The observer function is:

```text
build_q1_sic_detector_action_observer_row(
    immutable_final_row_snapshot,
    immutable_runtime_signal_snapshot,
    config,
) -> dict
```

It copies the input dictionaries, computes only `q1_sic_observer_*` telemetry, does not call `final_safety_arbitration`, and returns a new telemetry dictionary. The returned observer telemetry is merged into `frame_metrics_row` only after final action, proposal, detector request, Q1 arbitration, and accounting fields are already assembled.

## 8. Runtime-Safe Input List

Observer telemetry uses runtime row fields only:

- `category`, `video`, `raw_frame_id` / `frame_id`
- `action_label` / `ai_intervention_final_action`
- `active_event_memory`
- `ai_intervention_risk_high`
- `ai_intervention_guard_active`
- `ai_detector_needed_pred`
- detector blocked and cooldown flags
- proposal and detector absence
- `pred_object_count`
- candidate ACC/P3/FAST areas
- event-safety ownership and port watch ownership

## 9. Forbidden GT/Post-Hoc Input Confirmation

The observer does not use `Event_State`, GT-derived `frame_state`, `event_fn`, `protected_fn`, `unprotected_fn`, `q1_sic_pre_protection_label`, or `q1_sic_post_protection_label` as runtime controller or observer predicates. Verification reported:

| metric | value |
|---|---:|
| observer GT signal used max | 0.0 |
| Q1-SIC GT signal used for decision max | 0.0 |

## 10. Compile Result

Command:

```powershell
python -m py_compile src\run_experiment.py tools\verify_q1_sic1c1r3_observer_isolation.py tools\compare_asmag_tr_controller_online_guarded.py
```

Result: passed.

## 11. Dry-Run Result

Command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun.yaml
```

Result:

| planned jobs | completed jobs | failed jobs |
|---:|---:|---:|
| 56 | 56 | 0 |

## 12. Compare Result

Command:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun
```

Result: completed on the new Q1-SIC-1C1R3 output root. The compare emitted existing pandas fragmentation warnings.

Guarded aggregate:

| metric | value |
|---|---:|
| FMeasure | 0.34715 |
| Event_F1 | 0.66329 |
| Activation | 0.51000 |
| Avg_FPS | 27.36943 |
| Reuse_rate | 0.15643 |

## 13. Verification Result

Command:

```powershell
python tools\verify_q1_sic1c1r3_observer_isolation.py --c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun --c1r3-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun --out outputs\asmag_tr_q1_sic1c1r3_observer_isolation_verify
```

Result: `FAIL_BEHAVIOR_IDENTITY`.

| gate | result |
|---|---:|
| behavior_identity_ok | 0 |
| parking_preserved_ok | 1 |
| copyMachine_preserved_ok | 1 |
| port_watch_preserved_ok | 1 |
| observer_isolation_ok | 1 |
| snowFall_1150_observer_ok | 1 |
| normal_safety_ok | 1 |

## 14. Behavior Delta vs C1C1R Table

| field | delta rows |
|---|---:|
| action_label | 337 |
| yolo_called | 231 |
| ai_intervention_applied | 124 |
| selected_mode_after_guard | 79 |
| selected_mode_before_guard | 45 |
| selected_mode | 45 |
| protected_fn_accounting | 40 |
| ai_intervention_detector_requested | 31 |
| q1_sic_arbitration_label | 11 |
| q1_sic_arbitration_active | 11 |
| unprotected_fn_accounting | 7 |

Top video-level delta groups:

| video | delta rows |
|---|---:|
| dynamicBackground/fountain01 | 202 |
| badWeather/snowFall | 156 |
| dynamicBackground/fountain02 | 113 |
| PTZ/intermittentPan | 110 |
| intermittentObjectMotion/sofa | 91 |
| shadow/cubicle | 89 |
| lowFramerate/port_0_17fps | 70 |

Row-level audit: `outputs/asmag_tr_q1_sic1c1r3_observer_isolation_verify/q1_sic1c1r3_behavior_delta.csv`.

## 15. Parking Preservation Table

| metric | C1C1R | C1C1R3 |
|---|---:|---:|
| proposal/intervention rate | 0.46000 | 0.46000 |
| detector request rate | 0.00000 | 0.00000 |
| unprotected FN | 0 | 0 |

Parking preservation passed.

## 16. copyMachine Preservation Table

| frame | preserved |
|---:|---:|
| 810 | 1 |
| 815 | 1 |
| 820 | 1 |
| 935 | 1 |
| 940 | 1 |
| 945 | 1 |

All audited rows stayed protected as in C1C1R.

## 17. Port 1350/1355 Preservation Table

| frame | label | watch | owner | reference | detector unchanged |
|---:|---|---:|---|---|---:|
| 1350 | WATCH_ONLY_PORT_RETIGHTEN | 1 | detector_retighten | Step4E4 | 1 |
| 1355 | WATCH_ONLY_PORT_RETIGHTEN | 1 | detector_retighten | Step4E4 | 1 |

No port detector-retighten enforcement was introduced.

## 18. snowFall 1150 Observer Table

| field | C1C1R | C1C1R3 |
|---|---:|---:|
| action | DETECT_ACC | DETECT_ACC |
| Q1 label | NO_CHANGE | NO_CHANGE |
| proposal/intervention | 0 | 0 |
| detector request | 0 | 0 |
| yolo called | 1 | 1 |
| observer isolated enabled | blank | 1 |
| observer event-risk pressure | blank | 1 |
| observer detector pressure | blank | 1 |
| observer proposal absent | blank | 0 |
| observer runtime empty proxy | blank | 1 |
| observer would select shadow | blank | 0 |
| observer reject reason | blank | proposal_or_detector_present |

The observer is present and post-decision only. `would_select_shadow=0` because the post-decision observer treats the final `yolo_called=1` detector action as detector/proposal present, so the proposal-absent predicate is false. No snowFall protection was enforced.

## 19. Normal-Frame Safety Table

| metric | value |
|---|---:|
| normal-frame interventions | 0 |
| q1_sic_would_touch_normal_frame max | 0.0 |
| q1_sic_gt_signal_used_for_decision max | 0.0 |
| observer would-touch-normal max | 0.0 |
| observer mutated control state max | 0.0 |
| observer pressure memory enabled max | 0.0 |

Normal-frame safety passed.

## 20. Decision

`FAIL_BEHAVIOR_IDENTITY`

Primary failure classification: `behavior_identity_failed`.

Secondary note: observer isolation itself passed, pressure memory was disabled, parking/copyMachine/port/snowFall-1150/normal safety gates passed, and GT leakage stayed 0. The phase still fails because action/proposal/detector/Q1/accounting identity versus C1C1R was not preserved.

## 21. Recommended Next Step

Recommended next step: `Q1-SIC-1C1R3 audit/repair`.

Do not proceed to Q1-SIC-1C2 snowFall protection repair and do not proceed to Step 4E7-D2 port detector-retighten. The next R3 audit should determine why rerunning the C1C1R behavioral base under the current source produces broad C1C1R-vs-C1C1R3 trajectory drift despite the isolated observer passing its local safety checks.

## Stop Confirmation

Stopped after creating this report and updating daily status. No Q1-SIC-1C2, Step 4E7-D2, full CDnet, live run, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, or Jetson profiling was launched.
