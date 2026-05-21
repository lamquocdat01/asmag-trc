# ASMAG_TR_Q1_SIC1C1R3D Live-Probe Purity Report

Date: 2026-05-20

## 1. Scope and Safety Confirmation

Q1-SIC-1C1R3D was limited to a paired same-source residual-risk subset experiment: one live-probe baseline run with observer disabled, and one observer-purity run with the isolated observer enabled. No full CDnet, live run, live compare, targeted CDnet beyond the two scoped residual-risk subset dry-runs, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, Q1-SIC-1C2 snowFall enforcement, or Step 4E7-D2 port detector-retighten implementation was run.

Old Step 4D6, Step 4E4, Step 4E6, Q1-SIC-0, Q1-SIC-1, Q1-SIC-1A, Q1-SIC-1B, Q1-SIC-1C, Q1-SIC-1C1, Q1-SIC-1C1R, Q1-SIC-1C1R2, Q1-SIC-1C1R3, Q1-SIC-1C1R3B, Q1-SIC-1C1R3C, and audit output folders were not overwritten.

## 2. Why Q1-SIC-1C1R3D Exists

R3C_AUDIT concluded that fresh C1R-current and R3C were generated under different source paths, so the R3C identity failure was not a clean observer-flag-only comparison. R3D therefore created a paired same-source baseline and observer run to test whether enabling isolated observer telemetry changes behavior or the live detector-action probe surface.

## 3. Files Modified

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_live_probe_baseline_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_observer_purity_subset_dryrun.yaml`
- `tools/verify_q1_sic1c1r3d_live_probe_purity.py`
- `docs/ASMAG_TR_Q1_SIC1C1R3D_LIVE_PROBE_PURITY_REPORT.md`
- `docs/DAILY_STATUS.md`

`src/run_experiment.py` was inspected but not modified in this phase. The current source already had the R3C hard-isolation source edit: the live-probe helper no longer directly gates on `q1_sic_observer_isolated_enabled`, and observer telemetry is merged after `frame_metrics_row` assembly from copied row snapshots.

## 4. Configs Created

Baseline config:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_live_probe_baseline_subset_dryrun.yaml`

Observer config:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_observer_purity_subset_dryrun.yaml`

Both preserve:

- `q1_sic_detector_action_probe_enabled: true`
- `q1_sic_detector_action_probe_stable_snapshot_enabled: false`
- `q1_sic_event_risk_empty_detect_proxy_enabled: false`
- `q1_sic_observer_pressure_memory_enabled: false`

The intended behavioral toggle is only `q1_sic_observer_isolated_enabled`.

## 5. Output Roots Created

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_live_probe_baseline_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_observer_purity_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1c1r3d_live_probe_purity_verify/`

Verifier outputs:

- `r3d_baseline_vs_observer_behavior_delta.csv`
- `r3d_live_probe_delta.csv`
- `r3d_local_gates.csv`
- `r3d_observer_telemetry_summary.csv`
- `r3d_snowfall_1150_check.csv`
- `r3d_parking_check.csv`
- `r3d_config_diff_baseline_vs_observer.csv`
- `r3d_failure_classification.csv`
- `r3d_baseline_vs_observer_summary.csv`

## 6. Live-Probe Helper Purity Repair Explanation

The live-probe helper path was inspected in the current source. The previous R3C source-gating repair is present: `_apply_q1_sic_detector_action_probe` no longer reads `q1_sic_observer_isolated_enabled` as an early return, and it continues to be controlled by `q1_sic_detector_action_probe_enabled`.

No further source patch was made before validation. After the paired verifier failed, the phase failure rule was applied: no additional controller repair was attempted.

## 7. Observer Isolation Design

The observer remains post-decision only:

- `build_q1_sic_detector_action_observer_row(...)` copies both input snapshots.
- It returns only `q1_sic_observer_*` telemetry fields.
- It does not call `final_safety_arbitration`.
- It does not write `q1_sic_detector_action_probe_*` fields.
- It does not update pressure memory.
- It is merged after final frame metrics row assembly.

Observer telemetry safety passed in the paired run.

## 8. Config Parity Table

| config key | baseline | observer | classification |
|---|---|---|---|
| `base_config` | R3B fresh baseline config | R3D baseline config | intended config ancestry/output identifier |
| `experiment_name` | R3D live-probe baseline | R3D observer purity | intended output identifier |
| `edge_profile.name` | baseline profile | observer profile | intended output identifier |
| `q1_sic_observer_isolated_enabled` | `false` | `true` | intended observer telemetry flag |

No unexpected raw config differences were reported by the verifier.

## 9. Runtime-Safe Input and Forbidden GT/Post-Hoc Confirmation

The observer uses copied final row/runtime snapshot fields only. It did not use `Event_State`, GT-derived `frame_state`, `event_fn`, `protected_fn`, `unprotected_fn`, `q1_sic_pre_protection_label`, or `q1_sic_post_protection_label` as runtime controller/probe predicates.

Verification reported:

| metric | value |
|---|---:|
| observer mutated control state max | 0.0 |
| observer GT signal used max | 0.0 |
| observer would-touch-normal max | 0.0 |
| observer pressure memory enabled max | 0.0 |
| Q1-SIC GT signal used for decision max | 0.0 |

## 10. Compile Result

Command:

```powershell
python -m py_compile src\run_experiment.py tools\verify_q1_sic1c1r3d_live_probe_purity.py tools\compare_asmag_tr_controller_online_guarded.py
```

Result: passed.

## 11. Baseline Dry-Run and Compare Result

Command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_live_probe_baseline_subset_dryrun.yaml
```

Result:

| planned jobs | completed jobs | failed jobs |
|---:|---:|---:|
| 56 | 56 | 0 |

Compare command:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_live_probe_baseline_subset_dryrun
```

Result: completed on the new R3D baseline root. The compare emitted existing pandas fragmentation warnings.

## 12. Observer Dry-Run and Compare Result

Command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_observer_purity_subset_dryrun.yaml
```

Result: the first invocation timed out after one hour while the same scoped run was in progress; the exact same command was resumed using the progress ledger and completed.

| planned jobs | completed jobs | failed jobs |
|---:|---:|---:|
| 56 | 56 | 0 |

Compare command:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_observer_purity_subset_dryrun
```

Result: completed on the new R3D observer root. The compare emitted existing pandas fragmentation warnings.

## 13. Verification Result

Command:

```powershell
python tools\verify_q1_sic1c1r3d_live_probe_purity.py --baseline-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_live_probe_baseline_subset_dryrun --observer-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_observer_purity_subset_dryrun --out outputs\asmag_tr_q1_sic1c1r3d_live_probe_purity_verify
```

Decision: `FAIL_OBSERVER_IDENTITY`.

| gate | result |
|---|---:|
| baseline execution ok | 1 |
| observer execution ok | 1 |
| alignment ok | 1 |
| baseline local gates ok | 1 |
| observer identity ok | 0 |
| live-probe purity ok | 0 |
| observer telemetry ok | 1 |

## 14. Baseline vs Observer Behavior Delta Summary

| metric | value |
|---|---:|
| baseline guarded rows | 1400 |
| observer guarded rows | 1400 |
| row presence deltas | 0 |
| duplicate extra rows | 0 / 0 |
| behavior delta cells | 1250 |
| behavior delta rows | 480 |
| action-label deltas | 393 |
| proposal deltas | 213 |
| detector-request deltas | 21 |
| YOLO-called deltas | 254 |
| selected-mode deltas | 112 |
| Q1-label deltas | 36 |
| protected-accounting deltas | 85 |
| unprotected-accounting deltas | 24 |
| normal-frame intervention indicator deltas | 40 |

Top behavior-delta videos:

| video | behavior delta cells |
|---|---:|
| badWeather/snowFall | 211 |
| shadow/copyMachine | 143 |
| thermal/lakeSide | 134 |
| lowFramerate/tunnelExit_0_35fps | 133 |
| shadow/cubicle | 128 |

Top action transitions:

| baseline action | observer action | rows |
|---|---|---:|
| DETECT_ACC | REUSE_ACC | 65 |
| REUSE_ACC | CLOSED_EMPTY_ACC | 47 |
| REUSE_ACC | DETECT_ACC | 42 |
| DETECT_ACC | CLOSED_EMPTY_ACC | 32 |
| DETECT_ACC | LIGHTWEIGHT_MASK_ACC | 31 |

## 15. Baseline vs Observer Live-Probe Delta Summary

| metric | value |
|---|---:|
| live-probe delta cells | 3204 |
| live-probe delta rows | 598 |
| live-probe delta fields | 16 |

Top live-probe delta fields:

| field | delta cells |
|---|---:|
| `q1_sic_detector_action_probe_reject_reason` | 521 |
| `q1_sic_detector_action_probe_snapshot_detector_pressure` | 327 |
| `q1_sic_detector_action_probe_detector_pressure` | 327 |
| `q1_sic_detector_action_probe_detector_blocked` | 313 |
| `q1_sic_detector_action_probe_snapshot_detector_blocked` | 313 |

Top live-probe delta videos:

| video | live-probe delta cells |
|---|---:|
| badWeather/snowFall | 582 |
| lowFramerate/tunnelExit_0_35fps | 411 |
| turbulence/turbulence2 | 394 |
| shadow/copyMachine | 323 |
| thermal/lakeSide | 314 |

## 16. Local Gates Table

| gate | result |
|---|---:|
| parking preserved | 1 |
| parking proposal | 0.46000 |
| parking detector | 0.00000 |
| parking unprotected FN | 0 |
| copyMachine audited rows protected | 1 |
| port 1350/1355 watch preserved | 1 |
| no port detector-retighten enforcement | 1 |
| normal-frame interventions | 0 |
| `q1_sic_would_touch_normal_frame` max | 0.0 |
| `q1_sic_gt_signal_used_for_decision` max | 0.0 |
| no Q1-SIC-1B empty-detect enforcement | 1 |

## 17. snowFall 1150 Paired Same-Source Check

| field | baseline | observer |
|---|---|---|
| action | `DETECT_ACC` | `CLOSED_EMPTY_ACC` |
| proposal | 0 | 1 |
| detector request | 0 | 0 |
| Q1 label | `NO_CHANGE` | `FORCE_PROTECT_EVENT_MEMORY` |
| live probe would-select | 1 | 0 |
| observer enabled | n/a | 1 |
| observer GT signal used | n/a | 0 |
| observer would-touch-normal | n/a | 0 |

Result: `snowFall_1150_paired_same_source_ok = 0`.

## 18. Parking Paired Same-Source Check

| metric | baseline | observer |
|---|---:|---:|
| proposal | 0.46000 | 0.46000 |
| detector request | 0.00000 | 0.00000 |
| unprotected FN | 0 | 0 |
| parking live-probe delta rows | 0 | 0 |

Result: parking paired same-source check passed.

## 19. Decision Label

Decision: `FAIL_OBSERVER_IDENTITY`.

The paired current-source comparison did not prove observer purity. Even though observer telemetry was safe and baseline local gates passed, enabling the observer flag was associated with broad behavior deltas and broad live-probe surface deltas. Because the phase failed, no further patching was performed.

Primary failure classification:

- `observer changes behavior`

Secondary evidence:

- observer changes live-probe fields;
- snowFall 1150 drift;
- observer telemetry safe;
- baseline local gates preserved;
- parking/copyMachine/port/normal/GT gates preserved;
- row alignment valid.

## 20. Recommended Next Step

Recommended next action: Q1-SIC-1C1R3D audit/repair.

The repair should isolate why the post-decision observer flag still correlates with trajectory drift in a paired same-source run. The immediate audit should focus on whether the observer merge point changes row/state ordering, whether any downstream per-frame metrics or cached state are affected by added observer columns, whether resume/runtime ordering introduced nondeterminism, and whether the live-probe helper still writes behavior-sensitive fields into live control state.

Do not proceed to Q1-SIC-1C2 unless a runtime-safe detector-action proxy is proven without behavior drift. Do not proceed to Step 4E7-D2 until the event-safety observer/diagnostic path is stable.
