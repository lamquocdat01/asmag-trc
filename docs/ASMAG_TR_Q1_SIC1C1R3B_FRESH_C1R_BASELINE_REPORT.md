# ASMAG_TR_Q1_SIC1C1R3B Fresh C1R Baseline Report

Date: 2026-05-20

## 1. Scope and Safety Confirmation

Q1-SIC-1C1R3B created a fresh clean Q1-SIC-1C1R-style baseline under the current source, then compared:

- historical Q1-SIC-1C1R vs fresh current-source C1R;
- fresh current-source C1R vs Q1-SIC-1C1R3 observer isolation.

Only the scoped 14-video residual-risk subset was run. No full CDnet, live run, live compare, targeted CDnet beyond the scoped subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller behavior edit, compare behavior edit, Q1-SIC-1C2 snowFall enforcement, or Step 4E7-D2 port detector-retighten was performed.

## 2. Why Q1-SIC-1C1R3B Exists

Q1-SIC-1C1R3A found that the previous C1R-vs-R3 identity failure could be measuring source drift from a historical C1R output instead of observer-only drift. R3B therefore replayed the C1R config semantics under the current source in a new root before rechecking observer identity against R3.

## 3. Files Modified

- Created `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun.yaml`.
- Created `tools/verify_q1_sic1c1r3b_fresh_c1r_baseline.py`.
- Created this report.
- Updated `docs/DAILY_STATUS.md`.

`src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py` were compiled but not modified.

## 4. Config Created

The R3B config is based on `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`.

Only the experiment/profile identifiers were changed for the new output root. The config did not inherit from Q1-SIC-1C1R2 or Q1-SIC-1C1R3, did not enable observer isolation, did not enable stable snapshot, and preserved the C1R detector-action probe, copyMachine restore, and port-watch restore semantics.

## 5. Output Roots Created

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1c1r3b_fresh_c1r_baseline_verify/`

## 6. Config Diff: Historical C1R vs Fresh C1R

| key | historical C1R | fresh C1R | classification |
|---|---|---|---|
| `experiment_name` | `asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun` | `asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun` | intended output-root/name change |
| `edge_profile.name` | `guarded_q1_sic1c1r_restore_copy_port_subset_dryrun_cpu_edge` | `guarded_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun_cpu_edge` | intended output-root/name change |

## 7. Config Diff: Fresh C1R vs C1R3

| key | fresh C1R | C1R3 | classification |
|---|---|---|---|
| `experiment_name` | R3B fresh C1R | R3 observer isolation | intended output-root/name change |
| `edge_profile.name` | R3B fresh C1R profile | R3 observer isolation profile | intended output-root/name change |
| `resume_existing_results` | `true` | `false` | progress/output identifier |
| `online_controller_guarded.q1_sic_detector_action_probe_enabled` | `true` | `false` | detector-action probe semantic difference |
| `online_controller_guarded.q1_sic_detector_action_probe_stable_snapshot_enabled` | blank/inherited missing | `false` | stable snapshot explicit disable |
| `online_controller_guarded.q1_sic_observer_isolated_enabled` | blank/inherited missing | `true` | observer enable flag |
| `online_controller_guarded.q1_sic_observer_pressure_memory_enabled` | blank/inherited missing | `false` | behavior-sensitive config difference |

## 8. Compile Result

Passed:

```powershell
python -m py_compile src\run_experiment.py tools\verify_q1_sic1c1r3b_fresh_c1r_baseline.py tools\compare_asmag_tr_controller_online_guarded.py
```

## 9. Dry-Run Result

The scoped residual-risk subset completed successfully:

| metric | value |
|---|---:|
| jobs total | 56 |
| jobs completed | 56 |
| jobs failed | 0 |

## 10. Compare Result

Compare completed on the new fresh C1R root only:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun
```

The compare emitted existing pandas fragmentation warnings but wrote the guarded comparison files.

## 11. Verification Result

Verification completed:

```powershell
python tools\verify_q1_sic1c1r3b_fresh_c1r_baseline.py --historical-c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun --fresh-c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun --c1r3-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun --out outputs\asmag_tr_q1_sic1c1r3b_fresh_c1r_baseline_verify
```

Decision: `FAIL_SAME_SOURCE_OBSERVER_IDENTITY`.

## 12. Historical C1R vs Fresh C1R Behavior Delta Summary

| metric | value |
|---|---:|
| guarded rows, historical | 1400 |
| guarded rows, fresh | 1400 |
| row-presence deltas | 0 |
| duplicate extra rows | 0 |
| behavior delta rows | 1048 |
| action-label deltas | 337 |
| proposal deltas | 131 |
| detector-request deltas | 30 |
| YOLO-called deltas | 239 |
| selected-mode deltas | 164 |
| Q1-label deltas | 14 |
| protected-accounting deltas | 54 |
| unprotected-accounting deltas | 15 |

Assessment: historical C1R is not a valid current-source identity target.

## 13. Fresh C1R vs C1R3 Behavior Delta Summary

| metric | value |
|---|---:|
| guarded rows, fresh C1R | 1400 |
| guarded rows, C1R3 | 1400 |
| row-presence deltas | 0 |
| duplicate extra rows | 0 |
| behavior delta rows | 381 |
| action-label deltas | 122 |
| proposal deltas | 81 |
| detector-request deltas | 15 |
| YOLO-called deltas | 66 |
| selected-mode deltas | 11 |
| Q1-label deltas | 7 |
| protected-accounting deltas | 34 |
| unprotected-accounting deltas | 10 |
| normal-frame intervention indicator deltas | 21 |

Top video groups:

| video | delta rows |
|---|---:|
| badWeather/snowFall | 211 |
| lowFramerate/port_0_17fps | 118 |
| PTZ/continuousPan | 49 |
| PTZ/intermittentPan | 3 |

Top action transitions:

| fresh C1R action | C1R3 action | rows |
|---|---|---:|
| FALLBACK_P3_GUARD | DETECT_ACC | 23 |
| CLOSED_EMPTY_ACC | DETECT_ACC | 11 |
| FALLBACK_P3_POLICY | CLOSED_EMPTY_P3_FALLBACK | 10 |
| REUSE_ACC | DETECT_ACC | 10 |
| CLOSED_EMPTY_ACC | REUSE_ACC | 9 |
| LIGHTWEIGHT_MASK_ACC | DETECT_ACC | 9 |

Row-level failure output:

- `outputs/asmag_tr_q1_sic1c1r3b_fresh_c1r_baseline_verify/fresh_c1r_vs_c1r3_behavior_delta.csv`

## 14. Local Gates Table

| gate | value |
|---|---:|
| fresh C1R execution ok | 1 |
| parking preserved ok | 1 |
| historical parking proposal | 0.46000 |
| fresh parking proposal | 0.46000 |
| fresh parking detector | 0.00000 |
| fresh parking unprotected FN | 0 |
| copyMachine preserved ok | 1 |
| port watch preserved ok | 1 |
| no port detector-retighten enforcement ok | 1 |
| normal safety ok | 1 |
| normal-frame interventions | 0 |
| `q1_sic_would_touch_normal_frame` max | 0.0 |
| `q1_sic_gt_signal_used_for_decision` max | 0.0 |
| no Q1-SIC-1B empty-detect snowFall enforcement | 1 |

Audited copyMachine rows 810, 815, 820, 935, 940, and 945 were protected. Port frames 1350 and 1355 remained `WATCH_ONLY_PORT_RETIGHTEN`, watch 1, owner `detector_retighten`, reference `Step4E4`, with detector unchanged.

Notable same-source row-level drift remains at badWeather/snowFall frame 1150:

| root | action | proposal | detector request | Q1 label | probe/observer |
|---|---|---:|---:|---|---|
| fresh C1R | `CLOSED_EMPTY_ACC` | 1 | 0 | `FORCE_PROTECT_EVENT_MEMORY` | live probe enabled, would-select 0 |
| C1R3 | `DETECT_ACC` | 0 | 0 | `NO_CHANGE` | isolated observer enabled, would-select 0, reject `proposal_or_detector_present` |

## 15. Decision Label

`FAIL_SAME_SOURCE_OBSERVER_IDENTITY`

Fresh C1R-current passed execution, alignment, parking, copyMachine, port-watch, normal-safety, and GT-leakage gates. However, fresh C1R-current vs C1R3 still had broad behavior deltas, so observer/config identity under the same source is not proven.

Primary failure classification:

`same-source observer identity still fails`

Secondary findings:

- historical C1R is not reproducible under current source;
- fresh C1R baseline is locally usable but not identical to R3;
- drift is concentrated in snowFall, port, and PTZ rows;
- row alignment is clean, so this is not a verifier row-presence failure;
- no parking, copyMachine, port-watch, normal-safety, or GT-leakage regression was detected in the fresh baseline.

## 16. Recommended Next Step

Recommended next step: `Q1-SIC-1C1R3C config/source gating repair`.

R3B shows that a fresh same-source C1R baseline does not match R3. The next repair should audit and hard-gate the semantic difference between the C1R live detector-action probe path and the R3 isolated-observer path without changing copyMachine, port-watch, parking, or normal-safety gates.

Do not proceed to Q1-SIC-1C2 unless a runtime-safe detector-action proxy is proven without behavior drift. Do not proceed to Step 4E7-D2.
