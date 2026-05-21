# ASMAG_TR_Q1_SIC1C1R Probe Regression Audit

Date: 2026-05-19

## 1. Scope and Safety Confirmation

This phase was audit-only. It diagnosed why Q1-SIC-1C1R restored parking, copyMachine, and port watch telemetry but regressed the `badWeather/snowFall` frame-1150 detector-action probe.

New writes were limited to:

- `tools/audit_q1_sic1c1r_probe_regression.py`
- `outputs/asmag_tr_q1_sic1c1r_probe_regression_audit/`
- this report
- `docs/DAILY_STATUS.md`

No experiments, dry-runs, compares, full CDnet, live runs, live compares, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, existing-output modifications, or frozen CDnet2014 v1.6 overwrites were performed.

## 2. Q1-SIC-1C1R Recap

Q1-SIC-1C1R completed compile, scoped residual-risk dry-run, compare on the new output root only, and verification. It preserved parking, restored the audited copyMachine rows, restored port watch telemetry for frames 1350 and 1355, held normal-frame safety, and introduced no GT decision leakage.

Decision was still `FAIL_PROBE_REGRESSION` because snowFall frame 1150 probe stayed active but `would_select_shadow` changed from 1 in Q1-SIC-1C1 to 0 in Q1-SIC-1C1R.

## 3. Files, Configs, and Outputs Inspected

Docs inspected:

- `docs/ASMAG_TR_Q1_SIC1C1_RESTORE_BASE_PROBE_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C1R_RESTORE_COPY_PORT_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1C_INTEGRATION_BASE_AUDIT.md`
- `docs/ASMAG_TR_Q1_SIC1B_RUNTIME_PROXY_REPAIR_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1A_SNOWFALL_RUNTIME_MISMATCH_AUDIT.md`
- `docs/ASMAG_TR_Q1_SIC1_FINAL_ARBITRATION_REPORT.md`
- `docs/ASMAG_TR_Q1_SAFETY_INVARIANT_SPEC.md`
- `docs/DAILY_STATUS.md`

Read-only code/config inspection:

- `src/run_experiment.py`
- `tools/verify_q1_sic1c1_restore_base_probe.py`
- `tools/verify_q1_sic1c1r_restore_copy_port.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`

Outputs inspected read-only:

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1c1_restore_base_probe_verify/`
- `outputs/asmag_tr_q1_sic1c1r_restore_copy_port_verify/`
- `outputs/asmag_tr_q1_sic1a_snowfall_mismatch_audit/`

## 4. Generated Audit Outputs

- `snowfall_1150_sic1_vs_c1_vs_c1r.csv`
- `snowfall_context_1120_1170_c1_vs_c1r.csv`
- `snowfall_probe_input_delta.csv`
- `config_diff_c1_vs_c1r.csv`
- `source_signal_name_inventory.csv`
- `duplicate_frame_metrics_check.csv`
- `resume_stale_output_check.csv`
- `probe_regression_classification.csv`
- `recommended_repair_options.csv`

Commands run:

```powershell
python -m py_compile tools\audit_q1_sic1c1r_probe_regression.py
python tools\audit_q1_sic1c1r_probe_regression.py --sic1-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun --sic1c1-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun --sic1c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun --sic1a-root outputs\asmag_tr_q1_sic1a_snowfall_mismatch_audit --sic1c1-verify-root outputs\asmag_tr_q1_sic1c1_restore_base_probe_verify --sic1c1r-verify-root outputs\asmag_tr_q1_sic1c1r_restore_copy_port_verify --out outputs\asmag_tr_q1_sic1c1r_probe_regression_audit
```

## 5. snowFall 1150 Row Table

| field | Q1-SIC-1 | Q1-SIC-1C1 | Q1-SIC-1C1R |
|---|---:|---:|---:|
| action | DETECT_ACC | DETECT_ACC | DETECT_ACC |
| selected before/after | ACC / ACC | ACC / ACC | ACC / ACC |
| yolo_called | 1 | 1 | 1 |
| intervention applied | 0 | 0 | 0 |
| active_event_memory | 1 | 1 | 1 |
| ai_intervention_guard_active | 1 | 1 | 1 |
| ai_intervention_risk_high | 1 | 1 | 0 |
| ai_detector_needed_pred | 1 | 1 | 0 |
| detector_blocked_no_refresh | 1 | 1 | 0 |
| forced_refresh_cooldown_active | 1 | 1 | 0 |
| pred_object_count | 0 | 0 | 0 |
| candidate ACC/P3/FAST area | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| probe active | NA | 1 | 1 |
| event/risk pressure | NA | 1 | 0 |
| detector pressure | NA | 1 | 0 |
| proposal absent | NA | 1 | 1 |
| runtime empty proxy | NA | 1 | 1 |
| would_select_shadow | NA | 1 | 0 |
| GT signal used | NA | 0 | 0 |
| would_touch_normal | NA | 0 | 0 |
| Q1 label | NO_CHANGE | NO_CHANGE | NO_CHANGE |
| Q1 pre/post action | DETECT_ACC / DETECT_ACC | DETECT_ACC / DETECT_ACC | blank / blank |
| audit-only pre/post protection | unprotected_fn / unprotected_fn | unprotected_fn / unprotected_fn | blank / blank |

Key clue: Q1-SIC-1C1R has detector-action probe telemetry, but the later Q1 final-arbitration telemetry (`q1_sic_pre_action`, `q1_sic_post_action`, protection labels) is blank. That means the C1C1R row returned through the probe helper before reaching the later final-arbitration telemetry block that Q1-SIC-1C1 reached.

## 6. Context Frames 1120-1170

| frame | C1 action | C1R action | C1 risk | C1R risk | C1 detector needed | C1R detector needed | C1 blocked | C1R blocked | C1 cooldown | C1R cooldown | class |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1120 | CLOSED_EMPTY_ACC | CLOSED_EMPTY_ACC | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | unchanged |
| 1125 | DETECT_ACC | CLOSED_EMPTY_ACC | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | unchanged/nonprobe |
| 1130 | REUSE_ACC | CLOSED_EMPTY_ACC | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | context pressure changed |
| 1135 | CLOSED_EMPTY_ACC | CLOSED_EMPTY_ACC | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | context pressure changed |
| 1140 | CLOSED_EMPTY_ACC | CLOSED_EMPTY_ACC | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | context pressure changed |
| 1145 | FORCED_REFRESH | LIGHTWEIGHT_MASK_ACC | 1 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | context pressure changed |
| 1150 | DETECT_ACC | DETECT_ACC | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | focus-frame regression |
| 1155 | REUSE_ACC | CLOSED_EMPTY_ACC | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | context pressure changed |
| 1160 | CLOSED_EMPTY_ACC | CLOSED_EMPTY_ACC | 0 | 1 | 0 | 0 | 0 | 1 | 1 | 0 | context pressure changed |
| 1165 | CLOSED_EMPTY_ACC | CLOSED_EMPTY_ACC | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | context pressure changed |
| 1170 | CLOSED_EMPTY_ACC | CLOSED_EMPTY_ACC | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | context pressure changed |

The pressure loss is not isolated to frame 1150. The trajectory starts diverging before 1150, most visibly by frame 1130 and through the 1145/1150 transition.

## 7. Probe Input Delta

| signal | Q1-SIC-1C1 | Q1-SIC-1C1R | classification |
|---|---:|---:|---|
| active_event_memory | 1 | 1 | unchanged |
| ai_intervention_risk_high | 1 | 0 | pressure_lost |
| ai_intervention_guard_active | 1 | 1 | unchanged |
| ai_detector_needed_pred | 1 | 0 | pressure_lost |
| detector_blocked_no_refresh | 1 | 0 | pressure_lost |
| forced_refresh_cooldown_active | 1 | 0 | pressure_lost |
| pred_object_count | 0 | 0 | unchanged |
| candidate areas | 0 / 0 / 0 | 0 / 0 / 0 | unchanged |
| probe event/risk pressure | 1 | 0 | pressure_lost |
| probe detector pressure | 1 | 0 | pressure_lost |
| proposal absent | 1 | 1 | unchanged |
| runtime empty proxy | 1 | 1 | unchanged |
| would_select_shadow | 1 | 0 | pressure_lost |
| reject reason | blank | event_risk_pressure_inactive + detector_pressure_inactive | changed |

## 8. Config Diff Summary

The raw C1 vs C1R config diff contained only:

- expected base wrapper change from Q1-SIC-1 to Q1-SIC-1C1;
- experiment/profile name changes;
- intended C1C1R additions:
  - `q1_sic1c1r_restore_copymachine_enabled`
  - `q1_sic1c1r_restore_copymachine_frames`
  - `q1_sic1c1r_restore_port_watch_enabled`

No suspicious snowFall, detector-pressure, cooldown, event-risk, resume, cache, max-frame, or job-option config difference was found by the audit script.

## 9. Source Path Audit

Source inventory findings from `src/run_experiment.py`:

- C1C1R flags are loaded near lines 1026-1034.
- C1C1R telemetry defaults are added near lines 4128-4135.
- `_apply_q1_sic1c1r_restore_copy_port(...)` starts near line 4937.
- `_apply_q1_sic_detector_action_probe(...)` starts near line 5014 and calls the C1C1R restore helper first.
- The detector-action probe reads live mutable `info[...]`, `telemetry[...]`, and `ai_info[...]` values, including `ai_intervention_risk_high`, detector blocked flags, and cooldown state.
- `ai_intervention_risk_high` is assigned from the computed `high` value near line 6262, before early returns.
- The later Q1 final-arbitration block computes runtime proxy inputs and writes `q1_sic_pre_action`/`q1_sic_post_action` later in the file.

Answers to the source-path questions:

- `ai_intervention_risk_high` is computed from the runtime `high` boolean before the early return gate.
- `ai_detector_needed_pred` comes from the AI/shadow prediction info copied into runtime telemetry; the detector-action probe reads it from `ai_info`.
- `ai_detector_request_blocked_no_refresh_model` is an intervention-info flag written by detector request/blocking paths; the probe reads it live from `info`.
- `forced_refresh_cooldown_active` is computed in the guarded controller telemetry path and copied into intervention info/telemetry.
- The copyMachine/port restore helper does not share a global Q1-SIC dictionary and is scoped by video/frame/action checks. For snowFall frame 1150 it should only set C1C1R enabled flags/default telemetry, not copyMachine or port active fields.
- The probe reads live mutable values, not a stable snapshot.
- The C1C1R restore helper could overwrite Q1 fields for port and copyMachine rows, but no evidence shows it clearing snowFall probe fields. On frame 1150 the probe fields are populated.
- C1C1R frame 1150 did not reach the later final-arbitration telemetry write path, unlike Q1-SIC-1C1. This supports an early-return/trajectory change rather than a final telemetry overwrite.

## 10. Resume and Stale-Output Audit

C1C1R finished after resuming the same scoped command from a tool timeout. The audit checked progress/stale indicators:

| artifact | status |
|---|---|
| `run_progress.csv` | exists, 56 rows, modified 2026-05-19T18:04:33 |
| `live_progress.json` | exists, modified 2026-05-19T18:04:51 |
| snowFall guarded `frame_metrics.csv` | exists, 100 rows, modified 2026-05-19T17:25:09 |
| `ai_intervention_video_summary.csv` | exists, 14 rows, modified 2026-05-19T18:05:34 |
| `asmag_tr_final_comparison.csv` | exists, 4 rows, modified 2026-05-19T18:04:44 |

The snowFall guarded output was generated before the timeout/resume point. That is consistent with the run sequence: the timeout occurred later, around lowFramerate/tunnelExit. The audit did not find evidence of a mixed duplicate snowFall output.

## 11. Duplicate Row Audit

For C1C1R `badWeather/snowFall/ASMAG_TR_CONTROLLER_ONLINE_GUARDED/frame_metrics.csv`:

- rows: 100
- unique frames: 100
- duplicate frame count: 0

Across guarded frame metrics checked by the script, the snowFall guarded file had no duplicate frame ambiguity. The verifier row selection is therefore not the likely cause.

## 12. Failure Classification

Primary classification: `RUNTIME_PRESSURE_TRAJECTORY_CHANGED`

Secondary classes:

- risk-high lost
- detector-needed lost
- detector-blocked lost
- cooldown lost
- context trajectory shift

Rejected classifications:

- `CONFIG_FLAG_DIFF_CHANGED_PRESSURE`: config diff showed only intended C1C1R additions and name/base wrapper changes.
- `RESUME_STALE_OUTPUT_MIX`: snowFall file had 100 unique rows and no duplicate frame ambiguity.
- `VERIFIER_ROW_SELECTION_AMBIGUITY`: no duplicate frame 1150 row.
- `TELEMETRY_COLUMN_OVERWRITE`: probe fields persisted; the loss is in source inputs read by the probe.
- `RESTORE_SHIM_SIDE_EFFECT`: no direct evidence that copyMachine/port restore branches ran on snowFall. However, a future repair should keep the restore shim isolated and verify this again.

## 13. Recommended Q1-SIC-1C1R2 Action

Recommended option: `A. Q1-SIC-1C1R2 stable snapshot repair`.

Rationale:

- Q1-SIC-1C1 had the correct frame-1150 probe pressure.
- Q1-SIC-1C1R reads live mutable values and returned before the later final-arbitration telemetry block.
- The next phase should add shadow-only stable snapshots of the detector-action probe inputs before early returns and before final arbitration, then use those snapshots for probe telemetry consistency.

Important guardrail: Q1-SIC-1C1R2 should still not enforce snowFall protection. It should first restore probe pressure at frame 1150 while preserving parking, copyMachine, and port watch restoration. If the stable snapshot also shows pressure genuinely zero, switch to an instrumentation-only phase rather than adding enforcement.

Do not proceed to Q1-SIC-1C2 snowFall protection enforcement or Step 4E7-D2 port retighten from this audit.

## 14. Explicit Safety Statement

No experiments, dry-runs, compares, full CDnet, live, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, or existing-output modifications were performed in this audit phase.
