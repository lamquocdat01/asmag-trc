# ASMAG_TR_Q1_SIC1C1R3C Live-Probe / Observer Audit

Date: 2026-05-20

## 1. Scope and Safety Confirmation

Q1-SIC-1C1R3C_AUDIT was analysis-only. It inspected existing docs, source, configs, verifier outputs, and raw guarded `frame_metrics.csv` files to explain why R3C failed same-source identity against the fresh C1R-current baseline.

No experiments, dry-runs, compares, full CDnet, live run, live compare, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, existing-output modifications, Q1-SIC-1C2 work, or Step 4E7-D2 work were performed.

## 2. Q1-SIC-1C1R3C Recap

R3C kept the live detector-action probe enabled and enabled isolated post-decision observer telemetry. The scoped dry-run completed 56/56 jobs with 0 failed, and compare completed only on the R3C output root.

Observer telemetry stayed safe:

| metric | value |
|---|---:|
| observer columns present | 1 |
| observer enabled max | 1 |
| observer post-decision only max | 1 |
| observer used immutable snapshot max | 1 |
| observer mutated control state max | 0 |
| observer GT signal used max | 0 |
| observer would-touch-normal max | 0 |
| observer pressure memory enabled max | 0 |

But R3C failed with `FAIL_SAME_SOURCE_IDENTITY`: 904 behavior delta rows versus fresh C1R-current, 1340 live-probe cell deltas, parking regression, and snowFall frame 1150 drift.

## 3. Files, Configs, and Outputs Inspected

Docs read or used as prior phase evidence:

- `docs/ASMAG_TR_Q1_SIC1C1R3B_FRESH_C1R_BASELINE_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R3C_OBSERVER_GATING_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R3_OBSERVER_ISOLATION_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R3A_BEHAVIOR_IDENTITY_DRIFT_AUDIT.md`
- `docs/ASMAG_TR_Q1_SAFETY_INVARIANT_SPEC.md`
- `docs/DAILY_STATUS.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_VALIDATION_PLAN.md`

Read-only code/config/output inspection was performed by the audit script:

- `src/run_experiment.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun.yaml`
- `tools/verify_q1_sic1c1r3b_fresh_c1r_baseline.py`
- `tools/verify_q1_sic1c1r3c_observer_gating.py`
- fresh C1R and R3C output roots
- R3B and R3C verifier output roots

Created:

- `tools/audit_q1_sic1c1r3c_live_probe_observer.py`
- `outputs/asmag_tr_q1_sic1c1r3c_live_probe_observer_audit/`

Audit outputs:

- `r3c_live_probe_delta_summary.csv`
- `r3c_behavior_delta_by_video.csv`
- `r3c_behavior_delta_by_action_transition.csv`
- `r3c_behavior_delta_live_probe_crosstab.csv`
- `r3c_snowfall_1150_live_probe_audit.csv`
- `r3c_parking_live_probe_audit.csv`
- `r3c_config_diff_semantic_audit.csv`
- `r3c_source_flag_inventory.csv`
- `r3c_failure_classification.csv`
- `r3c_recommended_repair_options.csv`

## 4. Fresh C1R vs R3C Config Semantic Diff

The semantic config diff is limited to output identifiers and R3C observer/probe flags:

| item | audit classification |
|---|---|
| experiment/profile name | intended output-root/name change |
| `q1_sic_detector_action_probe_enabled=true` | live probe preserved |
| `q1_sic_detector_action_probe_stable_snapshot_enabled=false` | missing-vs-false default suspicious |
| `q1_sic_observer_isolated_enabled=true` | intended observer telemetry flag |
| `q1_sic_observer_pressure_memory_enabled=false` | missing-vs-false default suspicious |
| `q1_sic_event_risk_empty_detect_proxy_enabled=false` | missing-vs-false default suspicious |

The explicit false flags are suspicious because fresh C1R has missing/inherited keys, but the source uses `cfg.get(..., False)` for these flags. The audit did not prove explicit false values alone changed behavior.

## 5. Source Flag Inventory

Static source inventory found:

- `q1_sic_detector_action_probe_enabled` is read in controller initialization and applied in `_apply_q1_sic_detector_action_probe`.
- `q1_sic_observer_isolated_enabled` is read for observer setup and post-decision observer telemetry.
- After the R3C edit, `q1_sic_observer_isolated_enabled` no longer appears as an early-return gate inside `_apply_q1_sic_detector_action_probe`.
- `build_q1_sic_detector_action_observer_row` is called from the `frame_metrics_row.update(...)` post-decision assembly path.
- The live-probe helper still writes many `q1_sic_detector_action_probe_*` fields into the live `info` dict and calls pressure-memory helper code, even with stable snapshot disabled.
- Observer columns use the `q1_sic_observer_*` prefix; no direct column-name collision with `q1_sic_detector_action_probe_*` was found.

The audit also classified the comparison as source-path sensitive: current `src/run_experiment.py` is newer than the fresh C1R output, while R3C was generated after the R3C source edit. That means fresh C1R vs R3C is not a pure observer-flag-only comparison under an identical source snapshot.

## 6. Behavior Delta by Video and Action Transition

Top behavior delta videos:

| video | delta rows |
|---|---:|
| badWeather/snowFall | 211 |
| dynamicBackground/fountain01 | 202 |
| dynamicBackground/fountain02 | 177 |
| thermal/lakeSide | 137 |
| intermittentObjectMotion/sofa | 92 |

Top action transitions:

| fresh C1R action | R3C action | delta rows |
|---|---|---:|
| DETECT_ACC | REUSE_ACC | 92 |
| DETECT_ACC | LIGHTWEIGHT_MASK_ACC | 32 |
| REUSE_ACC | CLOSED_EMPTY_ACC | 26 |
| CLOSED_EMPTY_P3_FALLBACK | CLOSED_EMPTY_ACC | 12 |
| REUSE_ACC | DETECT_ACC | 11 |

Behavior delta total: 904 rows.

## 7. Live-Probe Delta Summary

The audit found:

| metric | value |
|---|---:|
| live-probe cell deltas | 1340 |
| rows with any live-probe delta | 399 |
| behavior delta rows | 904 |

The live-probe surface changed broadly, but the source audit did not support a simple “observer flag still gates live probe” explanation after the R3C source edit. The stronger explanation is that the comparison is contaminated by source-path mismatch and live-probe helper sensitivity: fresh C1R was not replayed after the R3C source edit, while R3C was.

## 8. snowFall 1150 Live-Probe Audit

snowFall frame 1150 changed:

| field | fresh C1R | R3C |
|---|---|---|
| action | `CLOSED_EMPTY_ACC` | `DETECT_ACC` |
| proposal | 1 | 0 |
| detector request | 0 | 0 |
| Q1 label | `FORCE_PROTECT_EVENT_MEMORY` | `NO_CHANGE` |
| live probe enabled | 1 | 1 |
| live probe would-select | 0 | 1 |
| observer enabled | blank/0 | 1 |
| observer GT signal used | blank/0 | 0 |
| observer would-touch-normal | blank/0 | 0 |

The audit found 24 changed fields on the snowFall 1150 row. R3C did not introduce new snowFall enforcement; it failed to preserve the fresh C1R same-source behavior at this row.

## 9. Parking Live-Probe Audit

Parking audit summary:

| metric | value |
|---|---:|
| parking rows audited | 22 |
| rows that became unprotected FN | 5 |
| fresh C1R proposal | 0.46000 |
| R3C proposal | 0.53000 |

The parking regression aligns with broad trajectory drift and live-probe surface changes. The audit did not prove a direct observer-column mutation of parking control state; observer GT and normal-touch safety stayed 0.

## 10. Failure Classification

Primary classification:

`FRESH_C1R_VS_R3C_SOURCE_PATH_MISMATCH`

Evidence:

- fresh C1R was generated before the R3C source-gating edit;
- R3C was generated after the source edit;
- the source audit found `q1_sic_observer_isolated_enabled` no longer directly gates the live-probe helper;
- row alignment was clean, but behavior and live-probe telemetry still drifted broadly;
- live-probe delta surface was high: 1340 cell deltas across 399 rows;
- behavior delta rows were high: 904;
- snowFall 1150 and parking both drifted.

Secondary classes:

- snowFall 1150 drift
- parking regression
- live_probe_delta_count high
- observer telemetry safe
- normal safety preserved
- port/copyMachine preserved
- PTZ/fountain drift
- explicit false flag suspicious
- missing-vs-false default suspicious

Not supported as primary:

- `VERIFIER_COUNTS_TELEMETRY_AS_BEHAVIOR`: behavior deltas include action/proposal/Q1/accounting fields, not observer telemetry.
- `OBSERVER_AND_LIVE_PROBE_DICT_COLLISION`: prefixes are distinct.
- `OBSERVER_FLAG_STILL_CHANGES_LIVE_PROBE_PATH`: not supported after the R3C source edit removed the early live-probe return.

## 11. Recommended Q1-SIC-1C1R3D Action

Recommended exactly one:

`C. Q1-SIC-1C1R3D live-probe helper purity audit/repair`

Reason: R3C still cannot prove observer identity because the live-probe surface and runtime trajectory are source-path sensitive. R3D should preserve live-probe behavior exactly, add observer telemetry outside the helper, and establish an identity comparison that is not contaminated by pre-edit fresh C1R output.

Do not proceed to Q1-SIC-1C2. Do not proceed to Step 4E7-D2.

## 12. Explicit Safety Statement

No experiments, dry-runs, compares, full CDnet, live, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, or existing-output modifications were performed.

Commands run:

```powershell
python -m py_compile tools\audit_q1_sic1c1r3c_live_probe_observer.py
python tools\audit_q1_sic1c1r3c_live_probe_observer.py --fresh-c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun --r3c-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun --r3c-verify-root outputs\asmag_tr_q1_sic1c1r3c_observer_gating_verify --out outputs\asmag_tr_q1_sic1c1r3c_live_probe_observer_audit
```
