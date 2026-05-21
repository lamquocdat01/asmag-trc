# ASMAG_TR_Q1_SIC1C1R3A Behavior Identity Drift Audit

Date: 2026-05-20

## 1. Scope and Safety Confirmation

Q1-SIC-1C1R3A was audit-only. It inspected existing docs, code, configs, verifier scripts, and output CSVs to determine why Q1-SIC-1C1R3 failed behavior identity versus Q1-SIC-1C1R even though observer isolation passed.

No experiments, dry-runs, compares, full CDnet, live runs, live compares, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, existing-output modifications, Q1-SIC-1C2 work, or Step 4E7-D2 work were performed.

## 2. Q1-SIC-1C1R3 Recap

Q1-SIC-1C1R3 passed compile, completed the scoped residual-risk dry-run with 56/56 jobs and 0 failed, completed compare on the new R3 root, and passed the local observer isolation gates.

The verifier failed behavior identity:

| metric | value |
|---|---:|
| behavior_identity_ok | 0 |
| behavior_delta_rows | 961 |
| action_label_deltas | 337 |
| yolo_called_deltas | 231 |
| proposal/intervention_deltas | 124 |
| detector_request_deltas | 31 |
| q1_label_deltas | 11 |
| protected_fn_accounting_deltas | 40 |
| unprotected_fn_accounting_deltas | 7 |

Preserved gates remained good: parking, copyMachine audited rows, port 1350/1355 watch telemetry, snowFall frame 1150 action/Q1 label, observer isolation, normal safety, and GT leakage.

## 3. Files, Configs, and Outputs Inspected

Docs inspected:

- `docs/ASMAG_TR_Q1_SIC1C1R_RESTORE_COPY_PORT_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R2_STABLE_PROBE_SNAPSHOT_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R2_SIDE_EFFECT_AUDIT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R3_OBSERVER_ISOLATION_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1A_SNOWFALL_RUNTIME_MISMATCH_AUDIT.md`
- `docs/ASMAG_TR_Q1_SAFETY_INVARIANT_SPEC.md`
- `docs/DAILY_STATUS.md`

Read-only code/config/verifier inspection:

- `src/run_experiment.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun.yaml`
- `tools/verify_q1_sic1c1r_restore_copy_port.py`
- `tools/verify_q1_sic1c1r3_observer_isolation.py`

Read-only output inspection:

- Q1-SIC-1C1R output root
- Q1-SIC-1C1R3 output root
- Q1-SIC-1C1R verifier root
- Q1-SIC-1C1R3 verifier root

Created analysis-only:

- `tools/audit_q1_sic1c1r3a_behavior_identity_drift.py`
- `outputs/asmag_tr_q1_sic1c1r3a_behavior_identity_drift_audit/`

## 4. Behavior Delta by Field

| field | delta rows |
|---|---:|
| action_label | 337 |
| yolo_called | 231 |
| ai_intervention_applied | 124 |
| selected_mode_after_guard | 79 |
| selected_mode | 45 |
| selected_mode_before_guard | 45 |
| protected_fn_accounting | 40 |
| ai_intervention_detector_requested | 31 |
| q1_sic_arbitration_active | 11 |
| q1_sic_arbitration_label | 11 |
| unprotected_fn_accounting | 7 |

This is broad runtime trajectory drift, not a telemetry-column-only mismatch.

## 5. Behavior Delta by Video

| video | delta rows |
|---|---:|
| dynamicBackground/fountain01 | 202 |
| badWeather/snowFall | 156 |
| dynamicBackground/fountain02 | 113 |
| PTZ/intermittentPan | 110 |
| intermittentObjectMotion/sofa | 91 |
| shadow/cubicle | 89 |
| lowFramerate/port_0_17fps | 70 |
| nightVideos/bridgeEntry | 44 |
| PTZ/continuousPan | 37 |
| shadow/copyMachine | 35 |
| turbulence/turbulence2 | 6 |
| lowFramerate/tunnelExit_0_35fps | 4 |
| thermal/lakeSide | 4 |

Thirteen of the fourteen residual-risk videos have deltas. This includes videos unrelated to copyMachine, port, or snowFall.

## 6. Action Transition Analysis

Top action transitions:

| C1R action | C1R3 action | delta rows |
|---|---|---:|
| REUSE_ACC | DETECT_ACC | 114 |
| LIGHTWEIGHT_MASK_ACC | DETECT_ACC | 31 |
| FALLBACK_P3_GUARD | DETECT_ACC | 16 |
| CLOSED_EMPTY_ACC | DETECT_ACC | 16 |
| DETECT_ACC | FALLBACK_P3_GUARD | 14 |
| CLOSED_EMPTY_ACC | CLOSED_EMPTY_P3_FALLBACK | 14 |
| CLOSED_EMPTY_ACC | REUSE_ACC | 12 |

The dominant pattern is not one Q1 label or one observer predicate. It is action-selection and detector-cadence drift across multiple videos.

Frame-range concentration exists by video, for example:

| video/range | delta rows |
|---|---:|
| dynamicBackground/fountain02 900-999 | 60 |
| dynamicBackground/fountain01 600-699 | 58 |
| badWeather/snowFall 900-999 | 51 |
| PTZ/intermittentPan 1200-1299 | 46 |
| dynamicBackground/fountain01 700-799 | 46 |
| badWeather/snowFall 1100-1199 | 42 |

The deltas are clustered in trajectory-sensitive intervals, but not isolated to the observer target row.

## 7. Observer/Q1 Activity Cross-Tab

Observer activity:

| condition | delta rows |
|---|---:|
| observer enabled, action-detect rows | 451 |
| observer enabled, observer inactive rows | 510 |
| observer would_select_shadow rows | 0 |

Q1 activity:

| condition | delta rows |
|---|---:|
| C1R Q1 inactive and C1R3 Q1 inactive | 930 |
| Q1 active in one root but not the other | 31 |

Key implication: most identity drift is present where Q1 arbitration is inactive, and more than half of all delta rows are observer-inactive. That argues against `OBSERVER_CODE_STILL_AFFECTS_BEHAVIOR` as the primary classification.

## 8. Config Diff Summary

Effective config differences:

| key | C1R | C1R3 | classification |
|---|---|---|---|
| experiment_name | C1R root | C1R3 root | intended output-root/name change |
| edge_profile.name | C1R profile | C1R3 profile | intended output-root/name change |
| q1_sic_detector_action_probe_enabled | true | false | suspicious default behavior flag |
| q1_sic_detector_action_probe_stable_snapshot_enabled | missing | false | harmless telemetry flag |
| q1_sic_observer_isolated_enabled | missing | true | intended observer enable flag |
| q1_sic_observer_pressure_memory_enabled | missing | false | harmless telemetry flag |
| resume_existing_results | true | false | suspicious resume/cache behavior flag |

The config diff contains two audit-worthy differences: R3 disables the old live probe and reruns from scratch while C1R was a historical resumed root. However, the drift is broader than the observer/probe surface and appears in Q1-inactive rows.

## 9. Verifier Alignment Audit

Verifier checks:

| check | value |
|---|---:|
| compares guarded pipeline only | 1 |
| C1R guarded rows | 1400 |
| C1R3 guarded rows | 1400 |
| overlapping row keys | 1400 |
| row-presence deltas | 0 |
| C1R duplicate extra rows | 0 |
| C1R3 duplicate extra rows | 0 |
| observer columns separate from behavior columns | 1 |
| uses post-compare outputs | 0 |

The verifier compares raw guarded `frame_metrics.csv` only, aligned by category/video/frame. It does not compare observer telemetry columns as behavior. The audit does not support `VERIFIER_ALIGNMENT_MISMATCH`.

## 10. Source Risk Block Inventory

| block | classification | note |
|---|---|---|
| post-decision observer function | enabled but telemetry-only | returns new `q1_sic_observer_*` dict after row assembly |
| observer short-circuit of live probe | enabled but telemetry-only | bypasses old live probe writes in isolated mode |
| C1R2 pressure memory update | disabled by config and safe | verifier saw old pressure memory max 0 |
| old live detector-action probe | disabled by config and safe | C1R had it enabled; R3 disables it |
| Q1 final safety arbitration | enabled and potentially behavior-affecting | inherited base path; can change proposals if upstream trajectory changes |
| C1R copyMachine restore shim | enabled and potentially behavior-affecting | inherited from C1R; audited rows preserved |
| C1R port watch restore shim | enabled but telemetry-only | inherited from C1R; port watch preserved |
| Q1-SIC-1B empty-detect proxy | disabled by config and safe | no `FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION` rows |
| general action selection and detector scheduling | unknown | broad action/yolo/selected-mode deltas point here or to historical source drift |

The inventory does not prove R2 pressure memory or R3 observer code affects behavior with flags off. The remaining high-risk area is broader current-source guarded-controller trajectory behavior.

## 11. Historical Reproducibility Assessment

Output timing and alignment:

| item | value |
|---|---|
| C1R guarded rows | 1400 |
| C1R3 guarded rows | 1400 |
| C1R frame_metrics mtime range | 2026-05-19T17:25:09 to 2026-05-19T18:04:33 |
| C1R3 frame_metrics mtime range | 2026-05-20T09:35:39 to 2026-05-20T10:05:51 |
| current `src/run_experiment.py` mtime | 2026-05-20T09:32:10 |
| row count mismatch | 0 |
| duplicate key evidence | 0 |
| row-presence delta evidence | 0 |

C1R3 was a fresh rerun under current source after the R3 code edits. C1R is a historical output generated under an older source state and was not rerun. The identity failure therefore may be measuring source drift rather than observer-only drift.

## 12. Is Historical C1R a Valid Identity Target?

Historical C1R remains valid as a documented phase artifact, but it is not a sufficient identity target for isolating R3 observer behavior under current source. The audit found:

- current source is newer than all C1R guarded frame metrics;
- row alignment is clean, so the mismatch is not missing rows;
- most deltas occur with Q1 inactive;
- many deltas occur with the observer inactive;
- deltas span 13 videos, including fountain and PTZ videos unrelated to the R3 observer target.

A fresh clean C1R replay baseline under the same current source is needed before the observer identity gate can answer the intended question. This audit did not run that replay.

## 13. Failure Classification

Primary classification:

`CURRENT_SOURCE_DRIFT_FROM_HISTORICAL_C1R`

Evidence:

- `behavior_delta_rows=961`
- `videos_with_deltas=13`
- `observer_inactive_delta_rows=510`
- `q1_inactive_delta_rows=930`
- `row_presence_deltas=0`
- `source_newer_than_c1r=1`

Secondary classes:

- broad action deltas
- broad proposal deltas
- Q1-label deltas
- observer inactive rows changed
- Q1 inactive rows changed
- fountain-dominated drift
- snowFall drift
- port drift
- parking still preserved
- copyMachine still preserved

## 14. Recommended Q1-SIC-1C1R3B Action

Recommended exactly one:

`D. Q1-SIC-1C1R3B fresh clean C1R baseline under current source`

This should create a new C1R replay output root and rerun only the scoped residual-risk subset after a separate explicit approval step. Do not run it from this audit. The purpose would be to establish whether R3 differs from a same-source C1R baseline, instead of comparing current-source R3 against historical C1R.

Not recommended now:

- `A` hard-gate/rollback behavior-affecting code: not proven by this audit.
- `B` config pinning repair: config differences are suspicious but do not explain broad Q1-inactive and observer-inactive drift alone.
- `C` verifier alignment repair: verifier alignment looks sound.
- `E` stop observer work: too conservative before a same-source baseline test.

## 15. Explicit Safety Statement

No experiments, dry-runs, compares, full CDnet, live, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, or existing-output modifications were performed.

Commands run:

```powershell
python -m py_compile tools\audit_q1_sic1c1r3a_behavior_identity_drift.py
python tools\audit_q1_sic1c1r3a_behavior_identity_drift.py --c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun --c1r3-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun --c1r3-verify-root outputs\asmag_tr_q1_sic1c1r3_observer_isolation_verify --out outputs\asmag_tr_q1_sic1c1r3a_behavior_identity_drift_audit
```
