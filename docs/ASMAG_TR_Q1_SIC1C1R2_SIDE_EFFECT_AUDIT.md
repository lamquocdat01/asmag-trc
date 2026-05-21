# ASMAG_TR_Q1_SIC1C1R2 Side-Effect Audit

Date: 2026-05-19

## 1. Scope and Safety Confirmation

This phase was audit-only. It diagnosed why Q1-SIC-1C1R2, intended as a shadow-only stable detector-action snapshot, changed runtime behavior relative to Q1-SIC-1C1R.

New writes were limited to:

- `tools/audit_q1_sic1c1r2_side_effect.py`
- `outputs/asmag_tr_q1_sic1c1r2_side_effect_audit/`
- this report
- `docs/DAILY_STATUS.md`

No experiments, dry-runs, compares, full CDnet, live runs, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, existing-output modifications, or frozen CDnet2014 v1.6 overwrites were performed.

## 2. Q1-SIC-1C1R2 Recap

Q1-SIC-1C1R2 compile, scoped dry-run, compare, and verifier had already completed in the previous phase. It failed because:

- snowFall frame 1150 changed from C1C1R `DETECT_ACC / NO_CHANGE` to C1C1R2 `CLOSED_EMPTY_ACC / FORCE_PROTECT_EVENT_MEMORY`;
- detector-action probe active became 0 and `would_select_shadow` stayed 0;
- parking regressed from proposal 0.46000 and unprotected FN 0 to proposal 0.52000 and unprotected FN 10;
- copyMachine audited rows and port 1350/1355 watch telemetry stayed restored;
- normal-frame safety and GT-signal safety held.

## 3. Files, Configs, and Outputs Inspected

Docs inspected:

- `docs/ASMAG_TR_Q1_SAFETY_INVARIANT_SPEC.md`
- `docs/ASMAG_TR_Q1_SIC1_FINAL_ARBITRATION_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1A_SNOWFALL_RUNTIME_MISMATCH_AUDIT.md`
- `docs/ASMAG_TR_Q1_SIC1C1_RESTORE_BASE_PROBE_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R_RESTORE_COPY_PORT_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R_PROBE_REGRESSION_AUDIT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R2_STABLE_PROBE_SNAPSHOT_REPORT.md`
- `docs/DAILY_STATUS.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_VALIDATION_PLAN.md`

Read-only code/config/output inspection:

- `src/run_experiment.py`
- C1C1R and C1C1R2 configs
- C1C1R and C1C1R2 verifier scripts
- C1C1R and C1C1R2 output roots
- C1C1R and C1C1R2 verifier output roots
- C1C1R probe regression audit outputs
- Q1-SIC-1C1 restore-base verifier outputs
- Q1-SIC-1 event-safety output root

## 4. Generated Audit Outputs

The analysis-only script wrote:

- `snowfall_1150_c1r_vs_c1r2_side_effect.csv`
- `snowfall_context_1120_1170_c1r_vs_c1r2.csv`
- `parking_c1r_vs_c1r2_regression.csv`
- `global_behavior_delta_c1r_vs_c1r2.csv`
- `q1_sic_label_delta_c1r_vs_c1r2.csv`
- `snapshot_pressure_memory_activation_rows.csv`
- `config_diff_c1r_vs_c1r2.csv`
- `source_signal_inventory_snapshot_vs_control.csv`
- `side_effect_classification.csv`
- `recommended_repair_options.csv`

Commands run:

```powershell
python -m py_compile tools\audit_q1_sic1c1r2_side_effect.py
python tools\audit_q1_sic1c1r2_side_effect.py --c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun --c1r2-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun --c1r-verify-root outputs\asmag_tr_q1_sic1c1r_restore_copy_port_verify --c1r2-verify-root outputs\asmag_tr_q1_sic1c1r2_stable_probe_snapshot_verify --out outputs\asmag_tr_q1_sic1c1r2_side_effect_audit
```

## 5. C1C1R vs C1C1R2 Config Diff

The audit compares effective configs after resolving `base_config`, not just wrapper YAML.

| key | C1C1R | C1C1R2 | classification |
|---|---|---|---|
| `experiment_name` | C1C1R restore copy/port dry-run | C1C1R2 stable probe snapshot dry-run | intended output/name change |
| `edge_profile.name` | C1C1R restore copy/port profile | C1C1R2 stable probe snapshot profile | intended output/name change |
| `online_controller_guarded.q1_sic_detector_action_probe_stable_snapshot_enabled` | missing/default false | true | intended stable snapshot enable flag |
| `online_controller_guarded.q1_sic_detector_action_probe_pressure_memory_max_age` | missing/default | 8 | intended pressure memory parameter |

No suspicious final-arbitration, event-safety, protection-accounting, parking, copyMachine, or port restore config difference was found after resolving inheritance.

## 6. snowFall 1150 Mutation Table

| field | C1C1R | C1C1R2 |
|---|---:|---:|
| action | `DETECT_ACC` | `CLOSED_EMPTY_ACC` |
| selected before/after | `ACC / ACC` | `ACC / ACC` |
| yolo called | 1 | 0 |
| proposal/intervention | 0 | 1 |
| detector request | 0 | 0 |
| active_event_memory | 1 | 1 |
| guard active | 1 | 1 |
| risk high | 0 | 1 |
| detector needed | 0 | 0 |
| detector blocked no refresh | 0 | 0 |
| forced refresh cooldown | 0 | 0 |
| Q1 active | 0 | 1 |
| Q1 label | `NO_CHANGE` | `FORCE_PROTECT_EVENT_MEMORY` |
| Q1 reason | blank | `I2_I3_event_memory_or_guard_trajectory_protects_unprotected_fn` |
| Q1 owner/reference | blank | `event_safety / Step4D6` |
| Q1 pre/post action | blank / blank | `CLOSED_EMPTY_ACC / CLOSED_EMPTY_ACC` |
| probe active | 1 | 0 |
| snapshot active | NA | 1 |
| pressure memory active | NA | 1 |
| probe reject reason | event/risk and detector pressure inactive | action not detect + proposal/detector present |

The action changed before the detector-action probe could select the row. Q1-SIC label changed because C1C1R2 reached the final arbitration path with an unsafe `CLOSED_EMPTY_ACC` FN row and event/guard/risk pressure, which matches the existing `FORCE_PROTECT_EVENT_MEMORY` condition. The stable snapshot path did not itself call `final_safety_arbitration`, but enabling it coincided with a broader trajectory mutation.

## 7. snowFall Context Table

| frame | C1C1R action | C1C1R2 action | C1C1R proposal | C1C1R2 proposal | C1C1R label | C1C1R2 label |
|---:|---|---|---:|---:|---|---|
| 1120 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `FORCE_PROTECT_EVENT_MEMORY` | `FORCE_PROTECT_EVENT_MEMORY` |
| 1125 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 0 | 1 | `NO_CHANGE` | `FORCE_PROTECT_EVENT_MEMORY` |
| 1130 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 0 | 1 | `NO_CHANGE` | `FORCE_PROTECT_EVENT_MEMORY` |
| 1135 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 0 | 1 | `NO_CHANGE` | `FORCE_PROTECT_EVENT_MEMORY` |
| 1140 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 0 | 1 | `NO_CHANGE` | `FORCE_PROTECT_EVENT_MEMORY` |
| 1145 | `LIGHTWEIGHT_MASK_ACC` | `LIGHTWEIGHT_MASK_ACC` | 0 | 0 | `NO_CHANGE` | `NO_CHANGE` |
| 1150 | `DETECT_ACC` | `CLOSED_EMPTY_ACC` | 0 | 1 | `NO_CHANGE` | `FORCE_PROTECT_EVENT_MEMORY` |
| 1155 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 0 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1160 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1165 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1170 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |

The mutation is not isolated to frame 1150. Several earlier snowFall rows moved from `NO_CHANGE` and no proposal to `FORCE_PROTECT_EVENT_MEMORY` with proposal 1.

## 8. Parking Regression Table

Known parking rows:

| frame | C1C1R action | C1C1R2 action | C1C1R proposal | C1C1R2 proposal | C1C1R label | C1C1R2 label |
|---:|---|---|---:|---:|---|---|
| 1195 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1310 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1315 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1320 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1425 | `DETECT_ACC` | `REUSE_ACC` | 0 | 0 | `NO_CHANGE` | `NO_CHANGE` |
| 1430 | `REUSE_ACC` | `REUSE_ACC` | 0 | 0 | `NO_CHANGE` | `NO_CHANGE` |
| 1435 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1440 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |
| 1445 | `CLOSED_EMPTY_ACC` | `CLOSED_EMPTY_ACC` | 1 | 1 | `NO_CHANGE` | `NO_CHANGE` |

The nine known parking rows did not explain the full parking regression by themselves, but the verifier summary found the video-level regression:

| metric | C1C1R | C1C1R2 |
|---|---:|---:|
| proposal | 0.46000 | 0.52000 |
| detector | 0.00000 | 0.00000 |
| unprotected FN | 0 | 10 |

The global delta scan shows parking had action/proposal trajectory changes outside the nine known rows. Stable snapshot pressure memory activated on parking rows, but the source path did not prove that memory was directly read by the parking protection logic.

## 9. Global Behavior Delta Summary

Across the 14-video subset:

| field | changed rows |
|---|---:|
| `q1_sic_detector_action_probe_pressure_memory_active` | 1400 |
| `action_label` | 335 |
| `yolo_called` | 211 |
| `ai_intervention_applied` | 187 |
| `q1_sic_detector_action_probe_active` | 173 |
| `selected_mode_after_guard` | 56 |
| `ai_intervention_detector_requested` | 37 |
| `selected_mode_before_guard` | 25 |
| `q1_sic_arbitration_active` | 18 |
| `q1_sic_arbitration_label` | 18 |

Q1 label transitions:

| transition | rows |
|---|---:|
| snowFall `NO_CHANGE -> FORCE_PROTECT_EVENT_MEMORY` | 5 |
| copyMachine `FORCE_PROTECT_EVENT_MEMORY -> NO_CHANGE` | 4 |
| snowFall `FORCE_PROTECT_EVENT_MEMORY -> NO_CHANGE` | 3 |
| copyMachine `NO_CHANGE -> FORCE_PROTECT_EVENT_MEMORY` | 3 |
| lakeSide `FORCE_PROTECT_EVENT_MEMORY -> NO_CHANGE` | 2 |
| tunnelExit `FORCE_PROTECT_EVENT_MEMORY -> NO_CHANGE` | 1 |

This is not a verifier-only mismatch. C1C1R2 changed action/proposal/Q1-label trajectories broadly.

## 10. Snapshot Pressure-Memory Activation

Pressure memory activated across all 14 videos, with 100 rows per video in the snapshot table. That means the stable snapshot was not narrowly limited to the detector-action focus row; it became a global per-video stateful observer.

Representative snowFall rows:

| frame | action | label | proposal | snapshot source | event pressure | detector pressure | memory active |
|---:|---|---|---:|---|---:|---:|---:|
| 800 | `FALLBACK_P3_GUARD` | `NO_CHANGE` | 0 | `current` | 0 | 1 | 1 |
| 805 | `LIGHTWEIGHT_MASK_ACC` | `NO_CHANGE` | 0 | `current+memory` | 1 | 1 | 1 |
| 840 | `REUSE_ACC` | `NO_CHANGE` | 1 | `current+memory` | 1 | 1 | 1 |
| 1125 | `CLOSED_EMPTY_ACC` | `FORCE_PROTECT_EVENT_MEMORY` | 1 | `current+memory` | 1 | 1 | 1 |
| 1150 | `CLOSED_EMPTY_ACC` | `FORCE_PROTECT_EVENT_MEMORY` | 1 | `current+memory` | 1 | 1 | 1 |

Memory being active on 1300 event-safety rows is too broad for a phase intended to probe a single detector-action failure pattern.

## 11. Source Path Audit

Answers to the requested source questions:

- `q1_sic_detector_action_probe_stable_snapshot_enabled` gates snapshot and pressure-memory telemetry, but it is evaluated inside the live intervention helper, before final action has fully settled for early-return rows.
- Pressure memory updates `self.q1_sic_detector_action_probe_pressure_memory`, a controller-instance dictionary keyed by video. The audit found no direct read of this dictionary by `final_safety_arbitration`.
- Pressure memory does not directly assign `active_event_memory`, `risk_high`, `guard_active`, `kinds`, `action_label`, proposal, or protection accounting in the inspected source.
- Snapshot logic does not call `final_safety_arbitration`; the final arbitration call remains in the later Q1-SIC block.
- Snapshot logic does not itself emit `FORCE_PROTECT_EVENT_MEMORY`. That label is produced by `final_safety_arbitration`.
- The probe helper writes into the live `info` dict, and that same dict is also used for runtime intervention telemetry and final output. This means the observer is not isolated, even though no direct control-state mutation was proven.
- copyMachine/port restore shims are scoped by video/frame/action and remained successful in C1C1R2. No direct evidence showed that those shims caused the snowFall/parking mutation.
- No exact variable-name collision with final arbitration state was proven. The risk is broader mutable-state coupling: source instrumentation and control telemetry share the same `info` object during branch exits.

## 12. Failure Classification

Primary classification: `UNKNOWN_NEEDS_INSTRUMENTATION`

Rationale:

- The observed output mutation is real: 335 action-label deltas, 187 proposal deltas, 18 Q1-label deltas, and a parking video regression.
- Effective config diff does not show unintended arbitration or protection flags.
- Source inspection does not prove that pressure memory directly feeds final arbitration inputs or proposal accounting.
- The observer is still not isolated: it writes into the live `info` dict inside the intervention helper and maintains broad per-video memory across all event-safety rows.

Secondary classes:

- snowFall action changed
- snowFall Q1 label changed
- parking proposal regression
- parking unprotected-FN regression
- snapshot not shadow-only in observed output
- pressure memory active
- copyMachine preserved
- port watch preserved
- normal safety preserved

## 13. Recommended Q1-SIC-1C1R3 Action

Recommended action: `A. Q1-SIC-1C1R3 shadow-only observer isolation repair`

Do not proceed to Q1-SIC-1C2 or Step 4E7-D2.

The next repair should:

- restore Q1-SIC-1C1R behavior first;
- compute detector-action probe telemetry from immutable local copies after the final action/proposal/protection state is decided;
- avoid writing probe telemetry into the live `info` dict until all control decisions are complete;
- either disable pressure memory or keep it in an isolated observer object that cannot affect branch predicates, budgets, `kinds`, Q1 labels, or proposal accounting;
- rerun only the scoped residual-risk subset after compile, with gates requiring zero action/proposal/label deltas versus C1C1R except the intended telemetry columns.

## 14. Explicit Safety Statement

No experiments, dry-runs, compares, full CDnet, live runs, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, or existing-output modifications were performed in this audit phase.
