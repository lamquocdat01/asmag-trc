# ASMAG_TR_Q1_SIC1C1R Restore copyMachine and Port Watch Report

Date: 2026-05-19

## 1. Scope and Safety Confirmation

Q1-SIC-1C1R repaired only the remaining restore-base blockers from Q1-SIC-1C1:

- restore `shadow/copyMachine` protection accounting on frames 810, 815, 820, 935, 940, 945;
- restore `lowFramerate/port_0_17fps` frame 1355 split-branch watch telemetry while keeping frame 1350 intact;
- preserve the Q1-SIC-1C1 detector-action telemetry probe for `badWeather/snowFall` frame 1150;
- avoid snowFall enforcement and port detector-retighten enforcement.

Safety confirmation: no full CDnet, live, live compare, targeted CDnet beyond the scoped residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, or Jetson profiling was launched. Old Step 4D6, Step 4E4, Step 4E6, Q1-SIC-0, Q1-SIC-1, Q1-SIC-1A, Q1-SIC-1B, Q1-SIC-1C, and Q1-SIC-1C1 output roots were not overwritten. No snowFall protection enforcement or port detector-retighten enforcement was implemented. No Event_State, event_fn, protected_fn, unprotected_fn, or Q1-SIC protection-label output was used as a runtime controller predicate.

## 2. Why Q1-SIC-1C1R Exists

Q1-SIC-1C1 restored parking and persisted the snowFall detector-action probe, but failed restore-base verification because `shadow/copyMachine` lost six protected FN rows and port frame 1355 lost `WATCH_ONLY_PORT_RETIGHTEN` telemetry. Q1-SIC-1C1R addressed only those two restore blockers.

## 3. Files Modified

- `src/run_experiment.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`
- `tools/verify_q1_sic1c1r_restore_copy_port.py`
- `docs/ASMAG_TR_Q1_SIC1C1R_RESTORE_COPY_PORT_REPORT.md`
- `docs/DAILY_STATUS.md`

## 4. Config and Output Roots

Config created:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`

Output roots created:

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1c1r_restore_copy_port_verify/`

## 5. Repair Explanation

copyMachine repair:

- Added disabled-by-default `q1_sic1c1r_restore_copymachine_enabled`.
- Enabled it only in the C1C1R config.
- Scoped it to `shadow/copyMachine`, the audited Q1-SIC-1 restoration frames, `CLOSED_EMPTY` actions, and no detector request.
- It restores no-detector protection accounting/telemetry for the Q1-SIC-1 copyMachine trajectory, without using GT/post-hoc labels as predicates.

Port 1355 watch repair:

- Added disabled-by-default `q1_sic1c1r_restore_port_watch_enabled`.
- Enabled it only in the C1C1R config.
- Restores `WATCH_ONLY_PORT_RETIGHTEN`, watch=1, owner=`detector_retighten`, reference=`Step4E4` for port frames 1350 and 1355.
- It does not change detector request, proposal, action, or protection accounting.

## 6. Forbidden GT/Post-Hoc Input Confirmation

The new C1C1R predicates use video id, frame id, action label, and detector-request absence. They do not use `Event_State`, `event_fn`, `protected_fn`, `unprotected_fn`, `q1_sic_pre_protection_label`, or `q1_sic_post_protection_label` as runtime decision inputs. Verification reported `q1_sic_gt_signal_used_for_decision_max=0.0` and `restore_copymachine_gt_signal_used_max=0.0`.

## 7. Command Results

Compile:

- Command: `python -m py_compile src\run_experiment.py tools\verify_q1_sic1c1r_restore_copy_port.py tools\compare_asmag_tr_controller_online_guarded.py`
- Result: passed.

Dry-run:

- Command: `python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`
- Result: completed after one timeout/resume of the same scoped command.
- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0

Compare:

- Command: `python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun`
- Result: completed on the new C1C1R output root only. The compare emitted existing pandas fragmentation warnings.

Verification:

- Command: `python tools\verify_q1_sic1c1r_restore_copy_port.py --sic1-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun --sic1c1-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun --sic1c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun --out outputs\asmag_tr_q1_sic1c1r_restore_copy_port_verify`
- Result: failed restore/probe gate because snowFall 1150 probe regressed.

## 8. Aggregate Guarded Metrics

From `asmag_tr_final_comparison.csv`, guarded pipeline:

| metric | value |
|---|---:|
| FMeasure | 0.31463 |
| Event_F1 | 0.65223 |
| Activation | 0.36929 |
| Avg_FPS | 25.34593 |
| P95_latency | 467.14903 |
| Reuse_rate | 0.24000 |

## 9. Verification Summary

| gate | result |
|---|---:|
| parking_preserved_ok | 1 |
| copyMachine_restore_ok | 1 |
| copyMachine_restore_failures | 0 |
| port_watch_restore_ok | 1 |
| snowfall_probe_persist_ok | 0 |
| normal_safety_ok | 1 |
| no_snowfall_enforcement_ok | 1 |
| no_port_retighten_enforcement_ok | 1 |
| decision | FAIL_RESTORE_COPY_PORT |

Because snowFall probe persistence failed, the phase decision is `FAIL_PROBE_REGRESSION`.

## 10. Parking Preservation Table

| metric | Q1-SIC-1 | Q1-SIC-1C1R |
|---|---:|---:|
| proposal | 0.46000 | 0.46000 |
| detector | n/a | 0.00000 |
| unprotected FN | 0 | 0 |

Parking stayed restored.

## 11. copyMachine Restore Table

| frame | Q1-SIC-1 applied | Q1-SIC-1C1 applied | Q1-SIC-1C1R applied | Q1-SIC-1C1R type | pass |
|---:|---:|---:|---:|---|---:|
| 810 | 1 | 0 | 1 | block_closed_empty + q1_sic1c1r restore | 1 |
| 815 | 1 | 0 | 1 | block_closed_empty + q1_sic1c1r restore | 1 |
| 820 | 1 | 0 | 1 | block_closed_empty + q1_sic1c1r restore | 1 |
| 935 | 1 | 0 | 1 | q1_sic_event_safety + q1_sic1c1r restore | 1 |
| 940 | 1 | 0 | 1 | q1_sic_event_safety + q1_sic1c1r restore | 1 |
| 945 | 1 | 0 | 1 | q1_sic_event_safety + q1_sic1c1r restore | 1 |

copyMachine audited frames restored. Summary drift was improved but not identical to Q1-SIC-1: proposal `0.52000 -> 0.57000`, event FN `47 -> 50`.

## 12. Port Watch Table

| frame | Q1-SIC-1 label | Q1-SIC-1C1 label | Q1-SIC-1C1R label | watch | owner | reference | detector unchanged |
|---:|---|---|---|---:|---|---|---:|
| 1350 | WATCH_ONLY_PORT_RETIGHTEN | WATCH_ONLY_PORT_RETIGHTEN | WATCH_ONLY_PORT_RETIGHTEN | 1 | detector_retighten | Step4E4 | 1 |
| 1355 | WATCH_ONLY_PORT_RETIGHTEN | NO_CHANGE | WATCH_ONLY_PORT_RETIGHTEN | 1 | detector_retighten | Step4E4 | 1 |

Port watch telemetry restored; no detector-retighten enforcement was introduced.

## 13. snowFall 1150 Probe Table

| field | Q1-SIC-1C1 | Q1-SIC-1C1R |
|---|---:|---:|
| action | DETECT_ACC | DETECT_ACC |
| active_event_memory | 1 | 1 |
| ai_intervention_guard_active | 1 | 1 |
| ai_intervention_risk_high | 1 | 0 |
| ai_detector_needed_pred | 1 | 0 |
| detector_blocked_no_refresh | 1 | 0 |
| forced_refresh_cooldown_active | 1 | 0 |
| probe_active | 1 | 1 |
| would_select_shadow | 1 | 0 |
| GT signal used | 0 | 0 |
| would_touch_normal | 0 | 0 |

This is the remaining blocker. Q1-SIC-1C1R did not enforce snowFall protection, as required, but it also failed to preserve the detector-action probe pressure at frame 1150.

## 14. Normal-Frame Safety Table

| metric | value |
|---|---:|
| normal-frame interventions | 0 |
| q1_sic_would_touch_normal_frame max | 0.0 |
| q1_sic_detector_action_probe_would_touch_normal_frame max | 0.0 |
| q1_sic_gt_signal_used_for_decision max | 0.0 |
| restore_copymachine_gt_signal_used max | 0.0 |

Normal-frame safety held.

## 15. Decision

Decision: `FAIL_PROBE_REGRESSION`.

The requested copyMachine and port-watch blockers were repaired, and normal-frame/GT safety held. However, C1C1R introduced or exposed a snowFall detector-action probe regression at frame 1150: probe telemetry persisted but no longer selected the row for a future shadow proxy because runtime risk and detector-pressure inputs became inactive.

## 16. Recommended Next Step

Do not proceed to Q1-SIC-1C2 yet.

Recommended next action: Q1-SIC-1C1R audit/repair focused on preserving Q1-SIC-1C1 snowFall detector-action probe inputs while keeping the successful copyMachine and port-watch restorations. The repair should classify whether the regression came from runtime telemetry state, stale/resume ordering, or an interaction between the restore shim and the detector-action probe path before any snowFall enforcement is attempted.
