# ASMAG_TR_Q1_SIC1C1R3C Observer Gating Report

Date: 2026-05-20

## 1. Scope and Safety Confirmation

Q1-SIC-1C1R3C repaired the config/source gating found in R3B by keeping the live detector-action probe path enabled while adding isolated post-decision observer telemetry. Validation was limited to the scoped 14-video residual-risk subset.

No full CDnet, live run, live compare, targeted CDnet beyond the scoped subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, frozen-output overwrite, Q1-SIC-1C2 snowFall enforcement, or Step 4E7-D2 port detector-retighten was performed.

## 2. Why Q1-SIC-1C1R3C Exists

Q1-SIC-1C1R3B showed that historical C1R is not a current-source identity target, but fresh C1R-current still differed from R3 because R3 disabled the live detector-action probe while enabling the isolated observer. R3C therefore attempted to preserve fresh C1R behavior by leaving `q1_sic_detector_action_probe_enabled=true` and adding only `q1_sic_observer_*` telemetry.

## 3. Files Modified

- `src/run_experiment.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun.yaml`
- `tools/verify_q1_sic1c1r3c_observer_gating.py`
- `docs/ASMAG_TR_Q1_SIC1C1R3C_OBSERVER_GATING_REPORT.md`
- `docs/DAILY_STATUS.md`

Source repair: removed the `q1_sic_observer_isolated_enabled` early return inside `_apply_q1_sic_detector_action_probe`, so the observer flag no longer disables the live probe path.

## 4. Config Created

Created:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun.yaml`

It is based on:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun.yaml`

The config keeps `q1_sic_detector_action_probe_enabled: true`, enables `q1_sic_observer_isolated_enabled: true`, disables observer pressure memory, disables stable snapshot, and explicitly keeps Q1-SIC-1B empty-detect proxy enforcement off.

## 5. Output Roots Created

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1c1r3c_observer_gating_verify/`

## 6. Config Diff: Fresh C1R vs R3C

| key | fresh C1R | R3C | classification |
|---|---|---|---|
| `experiment_name` | R3B fresh C1R | R3C observer gated | intended output-root/name change |
| `edge_profile.name` | R3B fresh C1R profile | R3C profile | intended output-root/name change |
| `online_controller_guarded.q1_sic_detector_action_probe_enabled` | inherited `true` | `true` | live probe preserved |
| `online_controller_guarded.q1_sic_detector_action_probe_stable_snapshot_enabled` | blank/inherited missing | `false` | explicit safe disable |
| `online_controller_guarded.q1_sic_observer_isolated_enabled` | blank/inherited missing | `true` | intended observer telemetry flag |
| `online_controller_guarded.q1_sic_observer_pressure_memory_enabled` | blank/inherited missing | `false` | explicit observer memory disable |
| `online_controller_guarded.q1_sic_event_risk_empty_detect_proxy_enabled` | blank/inherited missing | `false` | explicit Q1-SIC-1B enforcement disable |

## 7. Compile Result

Passed:

```powershell
python -m py_compile src\run_experiment.py tools\verify_q1_sic1c1r3c_observer_gating.py tools\compare_asmag_tr_controller_online_guarded.py
```

## 8. Dry-Run Result

The scoped residual-risk subset completed:

| metric | value |
|---|---:|
| jobs total | 56 |
| jobs completed | 56 |
| jobs failed | 0 |

## 9. Compare Result

Compare completed on the new R3C root only:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun
```

The compare emitted existing pandas fragmentation warnings and wrote the guarded comparison files.

## 10. Verification Result

Verifier command:

```powershell
python tools\verify_q1_sic1c1r3c_observer_gating.py --fresh-c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun --r3c-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun --out outputs\asmag_tr_q1_sic1c1r3c_observer_gating_verify
```

Result: `FAIL_SAME_SOURCE_IDENTITY`.

## 11. Fresh C1R vs R3C Behavior Delta Summary

| metric | value |
|---|---:|
| fresh C1R guarded rows | 1400 |
| R3C guarded rows | 1400 |
| row-presence deltas | 0 |
| duplicate extra rows | 0 |
| behavior delta rows | 904 |
| action-label deltas | 275 |
| proposal deltas | 130 |
| detector-request deltas | 11 |
| YOLO-called deltas | 205 |
| selected-mode deltas | 99 |
| Q1-label deltas | 24 |
| protected-accounting deltas | 66 |
| unprotected-accounting deltas | 25 |
| normal-frame intervention indicator deltas | 21 |

Dominant video groups:

| video | delta rows |
|---|---:|
| badWeather/snowFall | 211 |
| dynamicBackground/fountain01 | 202 |
| dynamicBackground/fountain02 | 177 |
| thermal/lakeSide | 137 |
| intermittentObjectMotion/sofa | 92 |
| intermittentObjectMotion/parking | 62 |
| PTZ/continuousPan | 20 |
| PTZ/intermittentPan | 3 |

Row-level deltas are in:

- `outputs/asmag_tr_q1_sic1c1r3c_observer_gating_verify/fresh_c1r_vs_r3c_behavior_delta.csv`

## 12. Observer Telemetry Summary

| metric | value |
|---|---:|
| observer columns present | 1 |
| observer enabled max | 1.0 |
| observer post-decision only max | 1.0 |
| observer used immutable snapshot max | 1.0 |
| observer mutated control state max | 0.0 |
| observer GT signal used max | 0.0 |
| observer would-touch-normal max | 0.0 |
| observer pressure memory enabled max | 0.0 |
| observer pressure memory used max | 0.0 |
| live probe delta count vs fresh C1R | 1511 |
| live probe behavior preserved | 0 |

Observer telemetry itself stayed isolated, but the live-probe behavior surface was not preserved.

## 13. Local Gates Table

| gate | value |
|---|---:|
| execution ok | 1 |
| parking preserved ok | 0 |
| fresh C1R parking proposal | 0.46000 |
| R3C parking proposal | 0.53000 |
| R3C parking detector | 0.00000 |
| R3C parking unprotected FN | 5 |
| copyMachine preserved ok | 1 |
| port watch preserved ok | 1 |
| no port detector-retighten enforcement ok | 1 |
| normal safety ok | 1 |
| normal-frame interventions | 0 |
| `q1_sic_would_touch_normal_frame` max | 0.0 |
| `q1_sic_gt_signal_used_for_decision` max | 0.0 |
| no new Q1-SIC-1B snowFall enforcement | 1 |
| local gates ok | 0 |

copyMachine rows 810, 815, 820, 935, 940, and 945 remained protected. Port frames 1350 and 1355 remained `WATCH_ONLY_PORT_RETIGHTEN`, watch 1, owner `detector_retighten`, reference `Step4E4`, with detector unchanged.

## 14. snowFall 1150 Same-Source Check

| field | fresh C1R | R3C |
|---|---|---|
| action | `CLOSED_EMPTY_ACC` | `DETECT_ACC` |
| proposal | 1 | 0 |
| detector request | 0 | 0 |
| Q1 label | `FORCE_PROTECT_EVENT_MEMORY` | `NO_CHANGE` |
| live probe enabled | n/a | 1 |
| observer enabled | n/a | 1 |
| observer GT signal used | n/a | 0 |
| observer would-touch-normal | n/a | 0 |
| observer reject reason | n/a | `proposal_or_detector_present` |

Result: `snowFall_1150_same_source_ok=0`.

This is not a new snowFall enforcement; it is a failure to preserve the fresh C1R same-source behavior at the audited row.

## 15. Decision Label

`FAIL_SAME_SOURCE_IDENTITY`

Failure classifications:

- live probe behavior not preserved: `live_probe_delta_count=1511`;
- observer still changes behavior / same-source identity failed: `behavior_delta_rows=904`;
- parking regression: proposal `0.53000`, unprotected FN `5`;
- snowFall 1150 same-source mismatch;
- no verifier alignment failure: row counts and keys matched;
- no observer GT leakage or observer normal-frame touch;
- copyMachine and port-watch rows remained preserved.

Per the failure rule, no further patch was made after verification failed.

## 16. Recommended Next Step

Recommended next step: `Q1-SIC-1C1R3C audit/repair`.

The next audit should isolate why enabling observer telemetry while preserving the live probe still changes the live-probe telemetry surface and runtime trajectory. In particular, it should compare R3C against a freshly replayed no-observer C1R baseline generated after the source-gating edit, and separately test whether explicit R3C config disables are interacting with inherited event-safety behavior.

Do not proceed to Q1-SIC-1C2 until a runtime-safe detector-action proxy is proven without behavior drift. Do not proceed to Step 4E7-D2 until the event-safety observer/diagnostic path is stable.
