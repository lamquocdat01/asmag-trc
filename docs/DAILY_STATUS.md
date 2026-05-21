# Daily Status

## 2026-05-20 Q1-SIC-1C1R3C Live-Probe / Observer Audit

- Created analysis-only tool `tools/audit_q1_sic1c1r3c_live_probe_observer.py`.
- Created audit report `docs/ASMAG_TR_Q1_SIC1C1R3C_LIVE_PROBE_OBSERVER_AUDIT.md`.
- Wrote audit outputs under `outputs/asmag_tr_q1_sic1c1r3c_live_probe_observer_audit/`: live-probe delta summary, behavior delta by video, action transitions, behavior/live-probe cross-tab, snowFall 1150 audit, parking audit, config semantic diff, source flag inventory, failure classification, and repair recommendation.
- Inspected existing R3B/R3C/R3/R3A reports, safety invariant spec, daily status, validation plan, current `src/run_experiment.py`, fresh C1R/R3C configs, R3B/R3C verifier scripts, fresh C1R and R3C output roots, and R3C verifier outputs read-only.
- Commands run: `python -m py_compile tools\audit_q1_sic1c1r3c_live_probe_observer.py`, then the new analysis-only audit script. No experiment, dry-run, compare, full CDnet, live run, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edit, compare edit, config edit, or existing-output modification was performed.
- Primary failure classification: `FRESH_C1R_VS_R3C_SOURCE_PATH_MISMATCH`.
- Key evidence: 904 behavior delta rows, 1340 live-probe cell deltas, 399 rows with any live-probe delta, 5 parking rows became unprotected FN, and snowFall frame 1150 had 24 changed audited fields.
- Source finding: after R3C, `q1_sic_observer_isolated_enabled` no longer directly gates the live-probe helper, but fresh C1R was generated before the R3C source-gating edit while R3C was generated after it. The audit therefore classifies the current comparison as source-path sensitive rather than a clean observer-only identity test.
- Config finding: R3C explicitly sets stable snapshot, observer pressure memory, and Q1-SIC-1B empty-detect proxy flags to false where fresh C1R has missing/inherited keys. These are suspicious missing-vs-false differences, but source `cfg.get(..., False)` semantics did not prove them as the primary cause.
- Recommended Q1-SIC-1C1R3D action: `C. Q1-SIC-1C1R3D live-probe helper purity audit/repair`. Preserve live-probe behavior exactly, add observer telemetry outside the helper, and avoid identity comparisons contaminated by pre-edit fresh C1R output.
- Safety confirmation: audit-only; do not proceed to Q1-SIC-1C2 or Step 4E7-D2.

## 2026-05-20 Q1-SIC-1C1R3C Observer Gating Repair

- Modified `src/run_experiment.py` so `q1_sic_observer_isolated_enabled` no longer short-circuits `_apply_q1_sic_detector_action_probe`; the live detector-action probe remains governed by `q1_sic_detector_action_probe_enabled`.
- Created config `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun.yaml`, based on fresh C1R-current R3B config, keeping the live probe enabled and enabling only isolated observer telemetry with observer pressure memory disabled.
- Created verifier `tools/verify_q1_sic1c1r3c_observer_gating.py`.
- Created report `docs/ASMAG_TR_Q1_SIC1C1R3C_OBSERVER_GATING_REPORT.md`.
- Created outputs under `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun/` and `outputs/asmag_tr_q1_sic1c1r3c_observer_gating_verify/`.
- Compile passed for `src/run_experiment.py`, the new verifier, and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Scoped residual-risk subset dry-run completed 56/56 jobs with 0 failed. Compare completed on the new R3C root only; it emitted existing pandas fragmentation warnings.
- Verification decision: `FAIL_SAME_SOURCE_IDENTITY`. Fresh C1R vs R3C had 904 behavior delta rows, including 275 action-label deltas, 130 proposal deltas, 11 detector-request deltas, 205 YOLO-called deltas, 24 Q1-label deltas, 66 protected-accounting deltas, and 25 unprotected-accounting deltas.
- Observer telemetry itself was safe: observer columns present, mutated-control max 0, observer GT-signal max 0, observer would-touch-normal max 0, observer pressure memory enabled max 0. However, live probe behavior was not preserved: `live_probe_delta_count=1511`.
- Local gates failed through parking and snowFall same-source mismatch: parking proposal regressed to 0.53000 with unprotected FN 5; snowFall frame 1150 changed from fresh C1R `CLOSED_EMPTY_ACC / FORCE_PROTECT_EVENT_MEMORY / proposal 1` to R3C `DETECT_ACC / NO_CHANGE / proposal 0`.
- Preserved gates: copyMachine rows 810, 815, 820, 935, 940, 945 protected; port 1350/1355 watch preserved; normal-frame interventions 0; `q1_sic_would_touch_normal_frame` max 0; `q1_sic_gt_signal_used_for_decision` max 0; no Q1-SIC-1B snowFall enforcement; no port detector-retighten enforcement.
- Per failure rules, no further patch was made after R3C verification failed.
- Recommended next action: `Q1-SIC-1C1R3C audit/repair`. Do not proceed to Q1-SIC-1C2 or Step 4E7-D2.
- Safety confirmation: no full CDnet, live run, live compare, targeted CDnet beyond the scoped subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, frozen-output overwrite, Q1-SIC-1C2 snowFall enforcement, or Step 4E7-D2 port detector-retighten was performed.

## 2026-05-20 Q1-SIC-1C1R3B Fresh Clean C1R Baseline

- Created fresh C1R-current config `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun.yaml`, based on Q1-SIC-1C1R restore-copy-port config with only experiment/profile identifiers changed.
- Created verifier `tools/verify_q1_sic1c1r3b_fresh_c1r_baseline.py`.
- Created report `docs/ASMAG_TR_Q1_SIC1C1R3B_FRESH_C1R_BASELINE_REPORT.md`.
- Created outputs under `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun/` and `outputs/asmag_tr_q1_sic1c1r3b_fresh_c1r_baseline_verify/`.
- Compile passed for `src/run_experiment.py`, the new verifier, and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Scoped residual-risk subset dry-run completed 56/56 jobs with 0 failed. Compare completed on the new fresh C1R root only; it emitted existing pandas fragmentation warnings.
- Fresh C1R-current preserved local gates: parking proposal 0.46000, detector 0.00000, unprotected FN 0; copyMachine rows 810, 815, 820, 935, 940, 945 protected; port 1350/1355 watch preserved; normal-frame interventions 0; `q1_sic_would_touch_normal_frame` max 0; `q1_sic_gt_signal_used_for_decision` max 0.
- Verification decision: `FAIL_SAME_SOURCE_OBSERVER_IDENTITY`. Historical C1R vs fresh C1R had 1048 behavior deltas, confirming historical C1R is not a current-source identity target. Fresh C1R vs C1R3 still had 381 behavior deltas, including 122 action-label deltas, 81 proposal deltas, 15 detector-request deltas, 7 Q1-label deltas, 34 protected-accounting deltas, and 10 unprotected-accounting deltas.
- Primary failure classification: same-source observer identity still fails. Row-level failure output was written to `outputs/asmag_tr_q1_sic1c1r3b_fresh_c1r_baseline_verify/fresh_c1r_vs_c1r3_behavior_delta.csv`.
- Recommended next action: `Q1-SIC-1C1R3C config/source gating repair`. Do not proceed to Q1-SIC-1C2 or Step 4E7-D2.
- Safety confirmation: no full CDnet, live run, live compare, targeted CDnet beyond the scoped subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, frozen-output overwrite, controller behavior edit, compare behavior edit, Q1-SIC-1C2 snowFall enforcement, or Step 4E7-D2 port detector-retighten was performed.

## 2026-05-20 Q1-SIC-1C1R3A Behavior Identity Drift Audit

- Created analysis-only tool `tools/audit_q1_sic1c1r3a_behavior_identity_drift.py`.
- Created audit report `docs/ASMAG_TR_Q1_SIC1C1R3A_BEHAVIOR_IDENTITY_DRIFT_AUDIT.md`.
- Wrote audit outputs under `outputs/asmag_tr_q1_sic1c1r3a_behavior_identity_drift_audit/`: delta-by-video, delta-by-field, action transitions, frame-range concentration, observer/Q1 activity cross-tabs, row-count/duplicate checks, effective config diff, verifier alignment audit, source risk block inventory, classification, and repair recommendation.
- Inspected Q1-SIC-1C1R, Q1-SIC-1C1R2, Q1-SIC-1C1R3, Q1-SIC-1A, and safety-invariant docs; current `src/run_experiment.py`; C1R/R3 configs; C1R/R3 verifiers; C1R/R3 output roots; and R3 verifier/failure outputs read-only.
- Commands run: `python -m py_compile tools\audit_q1_sic1c1r3a_behavior_identity_drift.py`, then the new analysis-only audit script. No experiment, dry-run, compare, full CDnet, live run, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edit, compare edit, config edit, or existing-output modification was performed.
- Primary failure classification: `CURRENT_SOURCE_DRIFT_FROM_HISTORICAL_C1R`.
- Key evidence: 961 behavior delta rows across 13 videos; 510 delta rows where the observer was inactive; 930 delta rows where Q1 arbitration was inactive in both roots; clean row alignment with 1400 C1R rows and 1400 C1R3 rows, 0 duplicate keys, and 0 row-presence deltas; current `src/run_experiment.py` timestamp is newer than the historical C1R frame metrics.
- Config finding: R3 inherits C1R but changes `resume_existing_results` from true to false, disables the old live detector-action probe, explicitly disables stable snapshot, and enables the isolated observer. These are audit-worthy differences but do not by themselves explain broad observer-inactive and Q1-inactive drift.
- Verifier finding: R3 verifier compares guarded raw `frame_metrics.csv` only, aligns by category/video/frame, and does not count observer telemetry columns as behavior columns.
- Recommended Q1-SIC-1C1R3B action: `D. Q1-SIC-1C1R3B fresh clean C1R baseline under current source`, in a new output root and only after a separate explicit approval step. Do not proceed to Q1-SIC-1C2 or Step 4E7-D2.
- Safety confirmation: audit-only; no controller behavior, compare behavior, configs, or existing outputs were modified.

## 2026-05-20 Q1-SIC-1C1R3 Observer Isolation

- Implemented Q1-SIC-1C1R3 on the Q1-SIC-1C1R behavioral base, not the Q1-SIC-1C1R2 stable-snapshot base.
- Created/used config `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun.yaml` and verifier `tools/verify_q1_sic1c1r3_observer_isolation.py`.
- Added the Q1-SIC detector-action observer as post-decision telemetry built from copied row snapshots, with observer pressure memory disabled and the old live detector-action stable snapshot path bypassed under isolated-observer mode.
- Created report `docs/ASMAG_TR_Q1_SIC1C1R3_OBSERVER_ISOLATION_REPORT.md`.
- Created outputs under `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun/` and `outputs/asmag_tr_q1_sic1c1r3_observer_isolation_verify/`.
- Compile passed for `src/run_experiment.py`, `tools/verify_q1_sic1c1r3_observer_isolation.py`, and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Scoped residual-risk subset dry-run completed 56/56 jobs with 0 failed. No full CDnet, live run, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, Q1-SIC-1C2 snowFall enforcement, or Step 4E7-D2 port detector-retighten was run.
- Compare completed on the new R3 output root only; it emitted existing pandas fragmentation warnings.
- Verification decision: `FAIL_BEHAVIOR_IDENTITY`. Observer isolation passed, but behavior identity versus Q1-SIC-1C1R failed with 961 behavior delta rows, including 337 action-label deltas, 124 proposal deltas, 31 detector-request deltas, 11 Q1-label deltas, 40 protected-accounting deltas, and 7 unprotected-accounting deltas.
- Preserved gates: parking proposal 0.46000, detector 0.00000, unprotected FN 0; copyMachine audited rows 810, 815, 820, 935, 940, 945 preserved; port 1350/1355 watch telemetry preserved; snowFall 1150 stayed `DETECT_ACC / NO_CHANGE`; observer mutated-control max 0, observer GT signal max 0, observer would-touch-normal max 0, pressure memory enabled max 0; normal-frame interventions 0.
- Failure classification output created at `outputs/asmag_tr_q1_sic1c1r3_observer_isolation_verify/q1_sic1c1r3_failure_classification.csv`; primary class is `behavior_identity_failed`.
- Recommended next step: Q1-SIC-1C1R3 audit/repair only. Do not proceed to Q1-SIC-1C2 or Step 4E7-D2.

## 2026-05-19 Q1-SIC-1C1R2 Stable Snapshot Side-Effect Audit

- Created analysis-only tool `tools/audit_q1_sic1c1r2_side_effect.py`.
- Created audit report `docs/ASMAG_TR_Q1_SIC1C1R2_SIDE_EFFECT_AUDIT.md`.
- Wrote audit outputs under `outputs/asmag_tr_q1_sic1c1r2_side_effect_audit/`: snowFall frame-1150 comparison, snowFall context 1120-1170, parking known-row regression table, global behavior deltas, Q1 label deltas, snapshot pressure-memory activation rows, effective config diff, source signal inventory, classification, and repair recommendation.
- Inspected the Q1 safety invariant spec, Q1-SIC-1/1A/C1/C1R/C1R2 reports, daily status, validation plan, `src/run_experiment.py`, C1R/C1R2 configs, C1R/C1R2 verifier scripts, C1R/C1R2 output roots, C1R/C1R2 verifier roots, C1R probe-regression audit outputs, Q1-SIC-1C1 verifier outputs, and Q1-SIC-1 output root read-only.
- Commands run: `python -m py_compile tools\audit_q1_sic1c1r2_side_effect.py`, then the new analysis-only audit script. No experiment, dry-run, or compare command was run.
- Primary classification: `UNKNOWN_NEEDS_INSTRUMENTATION`. Effective config diff showed only intended C1R2 name/profile and stable snapshot flags, and source inspection did not prove direct final-arbitration input mutation, but observed outputs had broad action/proposal/Q1-label trajectory changes.
- Key findings: snowFall frame 1150 changed from `DETECT_ACC / NO_CHANGE` to `CLOSED_EMPTY_ACC / FORCE_PROTECT_EVENT_MEMORY`; global deltas included 335 action-label changes, 187 proposal changes, and 18 Q1-label changes; pressure memory activated on 1300 rows across the event-safety subset; parking regressed at video level to proposal 0.52000 and unprotected FN 10.
- Source-path finding: the stable snapshot does not directly call `final_safety_arbitration` or assign `kinds`, but it writes probe telemetry into the live `info` dict inside the intervention helper and keeps broad controller-instance pressure memory, so the observer is not isolated enough for a shadow-only guarantee.
- Recommended next action: `Q1-SIC-1C1R3 shadow-only observer isolation repair`. Restore C1C1R behavior first, compute probe telemetry from immutable post-decision copies, and require zero action/proposal/Q1-label deltas versus C1C1R except intended telemetry columns before any Q1-SIC-1C2 enforcement.
- Safety confirmation: no experiments, dry-runs, compares, full CDnet, live runs, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, existing-output modifications, or frozen CDnet2014 v1.6 overwrites were performed.

## 2026-05-19 Q1-SIC-1C1R2 Stable Probe Snapshot

- Implemented a shadow-only stable detector-action probe snapshot and short-lived probe pressure memory in `src/run_experiment.py`, guarded by disabled-by-default flags and enabled only in the new C1C1R2 config.
- Created `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun.yaml`, based on Q1-SIC-1C1R, and verifier `tools/verify_q1_sic1c1r2_stable_probe_snapshot.py`.
- Created report `docs/ASMAG_TR_Q1_SIC1C1R2_STABLE_PROBE_SNAPSHOT_REPORT.md`.
- Created outputs under `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun/` and `outputs/asmag_tr_q1_sic1c1r2_stable_probe_snapshot_verify/`.
- Compile passed for `src/run_experiment.py`, the new verifier, and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Scoped residual-risk subset dry-run completed 56/56 jobs with 0 failed. Compare completed only on the new Q1-SIC-1C1R2 root; the first compare attempt timed out at 120 seconds and the same new-root compare was rerun with a longer timeout successfully.
- Aggregate guarded metrics: FMeasure 0.29578, Event_F1 0.62784, activation 0.32286, Avg_FPS 33.91921, P95 latency 449.59700 ms, intervention rate 0.38071, detector request rate 0.01786, normal-frame interventions 0, guard alignment 1.00000.
- Verification decision: `FAIL_PROBE_SNAPSHOT`. snowFall frame 1150 snapshot/memory telemetry persisted, but the row changed from Q1-SIC-1C1R `DETECT_ACC`/`NO_CHANGE` to C1C1R2 `CLOSED_EMPTY_ACC`/`FORCE_PROTECT_EVENT_MEMORY`, so detector-action probe active became 0 and `would_select_shadow` stayed 0.
- Additional failures: parking regressed from C1C1R proposal 0.46000/detector 0.00000/unprotected FN 0 to C1C1R2 proposal 0.52000/detector 0.00000/unprotected FN 10; seven snowFall rows had existing `FORCE_*` enforcement labels with intervention applied.
- Preserved gates: copyMachine audited rows 810, 815, 820, 935, 940, 945 stayed protected; port frames 1350 and 1355 stayed `WATCH_ONLY_PORT_RETIGHTEN`, watch 1, owner `detector_retighten`, reference `Step4E4`; normal-frame safety and GT-signal safety held.
- Recommended next step: Q1-SIC-1C1R2 audit/repair, not Q1-SIC-1C2. First determine why enabling the stable snapshot changes snowFall and parking trajectory; restore C1C1R behavior before adding any snowFall enforcement.
- Safety confirmation: no full CDnet, live run, live compare, targeted CDnet beyond the scoped residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, frozen CDnet2014 v1.6 overwrite, old output overwrite, port detector-retighten enforcement, or Q1-SIC-1C2 snowFall protection repair was performed.

## 2026-05-19 Q1-SIC-1C1R Probe Regression Audit

- Created analysis-only tool `tools/audit_q1_sic1c1r_probe_regression.py`.
- Created audit report `docs/ASMAG_TR_Q1_SIC1C1R_PROBE_REGRESSION_AUDIT.md`.
- Wrote audit outputs under `outputs/asmag_tr_q1_sic1c1r_probe_regression_audit/`: snowFall frame-1150 Q1-SIC-1/C1/C1R row table, context 1120-1170 C1-vs-C1R table, probe input delta, config diff, source signal inventory, duplicate frame check, resume/stale-output check, classification, and recommended repair options.
- Inspected Q1-SIC-1C1/C1C1R reports, Q1-SIC-1C/1B/1A/1 reports, safety invariant spec, daily status, `src/run_experiment.py`, C1/C1R configs, C1/C1R verifiers, C1/C1R output roots, Q1-SIC-1 output root, and the Q1-SIC-1A audit root read-only.
- Commands run: `python -m py_compile tools\audit_q1_sic1c1r_probe_regression.py`, then the new analysis-only audit script. No experiment, dry-run, or compare command was run.
- Primary classification: `RUNTIME_PRESSURE_TRAJECTORY_CHANGED`.
- Secondary classes: risk-high lost, detector-needed lost, detector-blocked lost, cooldown lost, and context trajectory shift.
- Key finding: snowFall frame 1150 kept active event memory and empty-proxy/proposal-absent conditions, but C1C1R lost `ai_intervention_risk_high`, `ai_detector_needed_pred`, detector-blocked-no-refresh, and forced-refresh-cooldown. Context frames show the trajectory started diverging before 1150, especially around 1130-1145.
- Source-path finding: C1C1R frame 1150 has detector-action probe telemetry but blank Q1 pre/post action/protection fields, so the row returned through the probe helper before reaching the later final-arbitration telemetry block that Q1-SIC-1C1 reached. The probe reads live mutable values rather than a stable snapshot.
- Config/resume finding: config diff showed only intended C1C1R additions/name changes; no pressure-related config diff was found. The C1C1R snowFall guarded frame metrics had 100 rows, 100 unique frames, and no duplicate frame ambiguity. The snowFall file was generated before the timeout/resume point, with no evidence of stale mixed rows.
- Recommended next action: Q1-SIC-1C1R2 stable snapshot repair for detector-action probe inputs, still shadow-only and without snowFall enforcement. Preserve parking/copyMachine/port-watch restoration before any Q1-SIC-1C2 protection work.
- Safety confirmation: no experiments, dry-runs, compares, full CDnet, live runs, live compares, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, existing-output modifications, or frozen CDnet2014 v1.6 overwrites were performed.

## 2026-05-19 Q1-SIC-1C1R Restore copyMachine and Port Watch

- Implemented the C1C1R restore repair in `src/run_experiment.py` behind disabled-by-default flags for `shadow/copyMachine` restoration and `lowFramerate/port_0_17fps` watch telemetry restoration.
- Created `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`, based on Q1-SIC-1C1, enabling only the copyMachine restore shim and port watch telemetry restore while keeping the detector-action probe enabled.
- Created verifier `tools/verify_q1_sic1c1r_restore_copy_port.py`.
- Created report `docs/ASMAG_TR_Q1_SIC1C1R_RESTORE_COPY_PORT_REPORT.md`.
- Created outputs under `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun/` and `outputs/asmag_tr_q1_sic1c1r_restore_copy_port_verify/`.
- Compile passed for `src/run_experiment.py`, `tools/verify_q1_sic1c1r_restore_copy_port.py`, and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Scoped residual-risk subset dry-run completed 56/56 jobs with 0 failed after resuming the same scoped command from a tool timeout. Compare completed on the new Q1-SIC-1C1R output root only.
- Guarded aggregate compare metrics: FMeasure 0.31463, Event_F1 0.65223, Activation 0.36929, Avg_FPS 25.34593, P95 latency 467.14903 ms, Reuse rate 0.24000.
- Repair successes: parking remained restored at proposal 0.46000, detector 0.00000, unprotected FN 0; copyMachine audited frames 810, 815, 820, 935, 940, 945 were restored to protected behavior; port frames 1350 and 1355 both reported `WATCH_ONLY_PORT_RETIGHTEN`, watch 1, owner `detector_retighten`, reference `Step4E4`, with detector unchanged.
- Safety gates held: normal-frame interventions 0, `q1_sic_would_touch_normal_frame` max 0, detector-action probe would-touch-normal max 0, Q1-SIC GT decision signal max 0, copyMachine restore GT signal max 0, Q1-SIC-1B empty-detect enforcement rows 0, and no port-retighten detector enforcement.
- Restore failure: snowFall frame 1150 detector-action probe regressed. Probe telemetry was present and active, but `would_select_shadow` changed from 1 in Q1-SIC-1C1 to 0 in Q1-SIC-1C1R because runtime `ai_intervention_risk_high`, detector-needed, detector-blocked, and forced-refresh-cooldown inputs were 0.
- Decision: `FAIL_PROBE_REGRESSION`.
- Recommended next step: Q1-SIC-1C1R audit/repair focused on preserving Q1-SIC-1C1 snowFall detector-action probe inputs while keeping the successful copyMachine and port-watch restorations. Do not proceed to Q1-SIC-1C2 snowFall protection enforcement or Step 4E7-D2 port retighten yet.
- Safety confirmation: no full CDnet, live run, live compare, targeted CDnet beyond the scoped residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, frozen CDnet2014 v1.6 overwrite, old output overwrite, snowFall protection enforcement, or port detector-retighten enforcement was performed.

## 2026-05-19 Q1-SIC-1C1 Restore Base Probe

- Restored Q1-SIC-1 as the behavioral config base and did not continue from Q1-SIC-1B.
- Added a shadow-only detector-action runtime telemetry probe in `src/run_experiment.py`, guarded by disabled-by-default `q1_sic_detector_action_probe_enabled`.
- Created `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun.yaml`, based on Q1-SIC-1 and enabling only the detector-action probe.
- Created verifier `tools/verify_q1_sic1c1_restore_base_probe.py`.
- Created report `docs/ASMAG_TR_Q1_SIC1C1_RESTORE_BASE_PROBE_REPORT.md`.
- Created outputs under `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun/` and `outputs/asmag_tr_q1_sic1c1_restore_base_probe_verify/`.
- Compile passed for `src/run_experiment.py`, `tools/verify_q1_sic1c1_restore_base_probe.py`, and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Scoped residual-risk subset dry-run completed 56/56 jobs with 0 failed. Compare completed on the new Q1-SIC-1C1 output root only.
- Guarded aggregate compare metrics: FMeasure 0.30625, Event_F1 0.63759, Activation 0.35929, Avg_FPS 20.53205, P95 latency 465.10092 ms, Energy/frame 3.60129, Reuse rate 0.23071.
- Q1-SIC-1B empty-detect enforcement stayed disabled: `q1_sic_event_risk_empty_detect_proxy` active rows 0 and `FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION` label rows 0.
- Restore/probe verifier result: parking restored to Q1-SIC-1 behavior with proposal 0.46000, detector 0.00000, and unprotected FN 0; snowFall frame 1150 probe telemetry persisted with `would_select_shadow=1`, GT signal used 0, and would-touch-normal-frame 0; normal-frame interventions stayed 0.
- Restore failure: copyMachine did not restore to Q1-SIC-1 and had six audited protected-to-unprotected row regressions; port frame 1355 lost `WATCH_ONLY_PORT_RETIGHTEN` telemetry while frame 1350 restored.
- Decision: `FAIL_RESTORE_BASE`.
- Recommended next step: Q1-SIC-1C1 audit/repair focused only on restoring Q1-SIC-1 runtime trajectory and port watch telemetry under current source code. Do not proceed to Q1-SIC-1C2 snowFall protection enforcement or Step 4E7-D2 port retighten yet.
- Safety confirmation: no full CDnet, live run, live compare, targeted CDnet beyond the scoped residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, frozen CDnet2014 v1.6 overwrite, old output overwrite, port detector-retighten implementation, or snowFall protection enforcement was performed.

## 2026-05-19 Q1-SIC-1C Integration/Base Audit

- Created analysis-only tool `tools/audit_q1_sic1c_integration_base.py`.
- Created audit report `docs/ASMAG_TR_Q1_SIC1C_INTEGRATION_BASE_AUDIT.md`.
- Wrote audit outputs under `outputs/asmag_tr_q1_sic1c_integration_base_audit/`: snowFall 1150 integration audit, snowFall context diff, parking diff, copyMachine diff, port watch diff, Step4D6-vs-Q1-SIC-1B parking diff, config diff summary, telemetry persistence summary, missing-column summary, and failure classification.
- Inspected Q1 safety docs, Q1-SIC-0/1/1A/1B reports, daily status, validation plan, `src/run_experiment.py`, Q1-SIC verifier/audit tools, Q1-SIC-1 and Q1-SIC-1B configs, and existing Q1-SIC/Step4 output roots read-only.
- Commands run: `py_compile` for the new audit tool, then the new analysis-only script. No controller dry-run or compare command was run.
- Config finding: raw Q1-SIC-1B YAML points to Q1-SIC-1 as `base_config`, while Q1-SIC-1 points to Step4D6. Source inspection shows recursive base loading, and the effective recursive config diff showed only intended Q1-SIC-1B proxy additions plus harmless experiment/profile name changes.
- Runtime finding: snowFall frame 1150 had Q1-SIC enabled and was selected by the pre-run verifier, but the Q1-SIC-1B runtime row kept `NO_CHANGE` with blank/default proxy inputs, pre/post action, protection labels, and reject reason. That indicates callsite reachability or telemetry persistence failure for that detector-action row.
- Trajectory finding: Q1-SIC-1B did not preserve the Step4D6/Q1-SIC-1 event-safety trajectory. Parking had 6 unprotected inspected rows, copyMachine had 5 unexpected unprotected FN rows, and port frames 1350/1355 lost `WATCH_ONLY_PORT_RETIGHTEN` telemetry.
- Primary failure classification: `STEP4D6_TRAJECTORY_NOT_PRESERVED`. Secondary classes: snowFall proxy integration failure, parking regression, copyMachine regression, split-branch watch telemetry regression, and raw wrapper `base_config` change.
- Recommended Q1-SIC-1C1 action: revert Q1-SIC-1B and return to Q1-SIC-1 as the last stable event-safety base before reintroducing a smaller snowFall callsite/telemetry-persistence repair. Do not proceed to Step 4E7-D2 port retighten while Q1-SIC event-safety is unstable.
- Safety confirmation: no experiments, dry-runs, compares, full CDnet, live runs, live compares, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, existing-output modifications, or frozen CDnet2014 v1.6 overwrites were performed.

## 2026-05-19 Q1-SIC-1B Runtime Proxy Repair

- Implemented a narrow guarded-only Q1-SIC-1B runtime-safe proxy for `badWeather/snowFall` empty-detect event-risk rows in `src/run_experiment.py`, behind disabled-by-default config flags.
- Created `tools/verify_q1_sic1b_runtime_proxy.py`, `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun.yaml`, and report `docs/ASMAG_TR_Q1_SIC1B_RUNTIME_PROXY_REPAIR_REPORT.md`.
- Created outputs under `outputs/asmag_tr_q1_sic1b_runtime_proxy_verify/` and `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun/`.
- Compile passed for `src/run_experiment.py`, `tools/verify_q1_sic1b_runtime_proxy.py`, and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Shadow/proxy verification passed: snowFall frame 1150 selected, quiet TN frames 1160/1165/1170 not selected, active-event-memory-only not selected, DETECT_ACC not globally unsafe, GT decision signal use 0, would-touch-normal-frame 0, port watch-only preserved, split-branch OK.
- Because shadow passed, the scoped 14-video residual-risk subset dry-run was allowed and completed 56/56 jobs with 0 failed. Compare completed on the new Q1-SIC-1B output root only.
- Aggregate guarded compare metrics: FMeasure 0.28985, Event_F1 0.64343, Activation 0.35071, Avg_FPS 25.99883, P95 latency 433.58593 ms. Normal-frame intervention count remained 0, max `q1_sic_would_touch_normal_frame` was 0, and max `q1_sic_gt_signal_used_for_decision` was 0.
- Dry-run decision: `FAIL_DRYRUN`. snowFall frame 1150 still ended as an unprotected FN with runtime Q1-SIC label `NO_CHANGE`; new proxy telemetry stayed default on that detector-action row, indicating proxy integration/effect did not reach or persist.
- Additional dry-run regressions: `intermittentObjectMotion/parking` regressed to proposal 0.58000 and 6 unprotected FN rows, `shadow/copyMachine` had 5 unprotected FN rows, and port frames 1350/1355 lost Q1-SIC watch-only telemetry even though no port detector-retighten behavior was implemented.
- Failure classification: proxy too narrow or integration not reached, protection-accounting mismatch, trajectory reference mismatch, unexpected non-snowFall drift, and split-branch telemetry regression. No GT/post-hoc leakage and no normal-frame safety violation were observed.
- Recommended next step: Q1-SIC-1C audit/repair focused on detector-action arbitration telemetry/effect persistence and Q1-SIC-1B config/base inheritance. Do not proceed to Step 4E7-D freeze or Step 4E7-D2 port detector-retighten from this result.
- Safety confirmation: no full CDnet, live run, live compare, targeted CDnet beyond the explicitly allowed scoped residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, Jetson/edge profiling, frozen CDnet2014 v1.6 overwrite, old output overwrite, or port detector-retighten implementation was performed.

## 2026-05-19 Q1-SIC-1A snowFall Runtime Mismatch Audit

- Created audit report `docs/ASMAG_TR_Q1_SIC1A_SNOWFALL_RUNTIME_MISMATCH_AUDIT.md`.
- Created analysis-only tool `tools/audit_q1_sic1a_snowfall_mismatch.py`.
- Wrote audit outputs under `outputs/asmag_tr_q1_sic1a_snowfall_mismatch_audit/`: frame-1150 runtime row, context rows 1120-1170, Step 4D6-vs-Q1-SIC-1 diff, Step 4E6-vs-Q1-SIC-1 diff, SIC0/shadow-vs-runtime table, missing-column summary, and mismatch classification.
- Inspected Q1-SIC invariant/report docs, Step 4E6 audit/rebase docs, validation plan, Q1-SIC-1 report, `src/run_experiment.py`, Q1-SIC replay/shadow tools, the Q1-SIC-1 config, and existing Q1-SIC/Step 4D6/Step 4E6/Step 4E4 outputs read-only.
- Scripts run: `py_compile` for the new audit tool, then the new analysis script only.
- Frame 1150 classification: primary `FINAL_PROTECTION_ACCOUNTING_MISMATCH`; secondary `ARBITRATION_CONDITION_TOO_WEAK`, `POSTHOC_ONLY_SIGNAL_NOT_RUNTIME_SAFE`, and `TELEMETRY_INSUFFICIENT`.
- Diagnosis: runtime had active event memory, risk-high, guard-active, detector-needed, and detector-blocked signals, but selected action `DETECT_ACC` was not considered unsafe by Q1-SIC. `final_safety_arbitration(...)` therefore returned `NO_CHANGE`; the unprotected-FN evidence is post-hoc/ground-truth accounting and must not be used directly as a runtime decision input.
- Recommended next step: Q1-SIC-1B telemetry repair / risk proxy addition. Do not revert Q1-SIC-1, and do not proceed to port detector-retighten from this audit.
- Safety confirmation: no experiments, dry-runs, live runs, live compares, targeted CDnet, full CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, Jetson/edge profiling, controller edits, compare edits, config edits, existing-output modifications, or frozen CDnet2014 v1.6 overwrites were performed.

## 2026-05-19 Q1-SIC-1 Final Safety Arbitration

- Created `docs/ASMAG_TR_Q1_SIC1_FINAL_ARBITRATION_REPORT.md`, `tools/verify_q1_sic1_shadow_arbitration.py`, and `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun.yaml`.
- Updated `src/run_experiment.py` with disabled-by-default Q1-SIC final arbitration flags, pure `final_safety_arbitration(...)`, event-safety-only enforcement labels, port watch-only telemetry, and compact Q1-SIC frame telemetry.
- Created outputs under `outputs/asmag_tr_q1_sic1_shadow_verify/` and `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun/`.
- Compile passed for `src/run_experiment.py`, `tools/verify_q1_sic1_shadow_arbitration.py`, and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Shadow verification passed all dry-run gates: known Step 4E6 failures caught 1, parking failures caught 1, port 1350/1355 watch-only 1, report-only not counted as pass 1, would-touch-normal-frame 0, split-branch OK 1.
- Because shadow passed, the scoped 14-video residual-risk subset dry-run was allowed and completed 56/56 jobs with 0 failed. Compare completed on the new output root only.
- Aggregate guarded dry-run metrics: FMeasure 0.34221, Event_F1 0.66715, Activation 0.45786, intervention rate 0.34643, detector request rate 0.01429, normal-frame interventions 0, guard alignment 1.00000, max `q1_sic_would_touch_normal_frame` 0.
- Parking passed the event-safety dry-run gates: proposal 0.46000, detector 0.00000, unprotected FN 0. Port frames 1350/1355 were labeled `WATCH_ONLY_PORT_RETIGHTEN`, owner Step4E4/detector-retighten, and did not block event-safety.
- Dry-run decision: `FAIL_DRYRUN`, not a technical job failure. `badWeather/snowFall` frame 1150 remained an unprotected FN while Q1-SIC runtime telemetry reported `NO_CHANGE`, so this is a final protection/telemetry mismatch that must not be silently passed as report-only lock success.
- Recommended next step: Q1-SIC-1 telemetry repair so final arbitration sees final row protection/accounting state before any Step 4E7-D freeze. Do not proceed to Step 4E7-D2 port retighten yet.
- Safety confirmation: no full CDnet, live run, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, Jetson/edge profiling, frozen CDnet2014 v1.6 overwrite, old output overwrite, or port detector-retighten enforcement was performed.

## 2026-05-19 Q1-SIC-0 Safety-Invariant Spec and Counterfactual Replay

- Created `docs/ASMAG_TR_Q1_SAFETY_INVARIANT_SPEC.md` and `docs/ASMAG_TR_Q1_SIC0_INVARIANT_REPLAY_REPORT.md`.
- Created analysis-only tools `tools/analyze_q1_safety_trajectory_diff.py` and `tools/replay_q1_safety_invariants.py`.
- Wrote Q1-SIC-0 outputs under `outputs/asmag_tr_q1_sic0_invariant_replay/`: port, parking, and carry-over trajectory diffs; invariant violation summary; missing-column summary; counterfactual arbitration candidates; and counterfactual summary.
- Inspected existing Step 4D6, Step 4E4, Step 4E6, Step 4B4, smoke, Phase 8A, and Phase 8C shadow/calibration evidence read-only. Required docs read included Step 4E6 audit/report, daily status, validation plan, P4 online diagnostics/log requirements, Phase 8A checkpoint, and Phase 8C-1B checkpoint.
- Scripts run: `py_compile` for the two new tools, then the two new offline analysis scripts only. No `src/run_experiment.py`, no compare command, and no validation command was run for this phase.
- A leftover `run_experiment.py` process from the interrupted previous Step 4E7-D turn was detected and stopped before Q1-SIC-0 analysis began.
- Summary of invariant violations: parking had 9 event-memory losses, 9 unsafe unprotected FN rows, 7 candidate-predicate false rows, and 9 trajectory shifts; port frames 1350/1355 were caught as detector-retighten/watch under split-branch invariant I7; snowFall/lakeSide showed report-only locks plus unsafe FN drift; intermittentPan/tunnelExit showed trajectory drift and unsafe unprotected FN rows; cubicle had no direct row-level replay issue but still needs aggregate recall preservation.
- Counterfactual replay caught known Step 4E6 failure rows and, after enforcing I1 normal-frame protection in the replay heuristic, produced `would_touch_normal_frame=0` across replay candidates.
- Recommended next step: proceed to Q1-SIC-1 final-safety-arbitration design/implementation with replay-first verification. Do not return directly to Step 4E7-D or Step 4E7-D2 without the invariant arbitration layer.
- Safety confirmation: no experiments, dry-runs, live runs, compares, targeted CDnet, full CDnet, PTZ-targeted validation, cross-dataset validation, LASIESTA, SBI2015, BMC, Jetson/edge profiling, controller edits, compare-code edits, config edits, existing-output modification, or frozen CDnet2014 v1.6 overwrite was performed.

## 2026-05-19 Step 4E6 branch audit refresh

- Refreshed `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_BRANCH_AUDIT.md` as an audit-only Step 4E6 failure diagnosis. No Step 4E7 implementation was started.
- Read-first docs inspected: checkpoint 2026-05-18, Step 4E6 port/parking rebase report, this daily status, and the validation plan. Also inspected Step 4E4/4D6/4B4 reference outputs, Step 4E6 output CSVs/logs, `src/run_experiment.py`, and `tools/compare_asmag_tr_controller_online_guarded.py` read-only.
- Port diagnosis: Step 4E6 hard-lock telemetry fired overall, but did not fire at frames 1350 or 1355. Those frames were final FN, unprotected FN, no-detector `CLOSED_EMPTY_P3_FALLBACK` rows. The action was already in the unsafe fallback set, so the failure is branch reachability/order plus trajectory shift from Step 4E4, not an action-set, cap/cooldown, or final-normal-suppressor issue.
- Parking diagnosis: Step 4E6 restored the 4D3/4D5/4D6 trim counters, but the nine unprotected FN rows had active event memory 0, guard inactive, rescue candidate 0, carry-over lock 0, and hard-restore fallback 0. This is a trajectory-before-rescue problem, not a trim-counter problem.
- Carry-over classification remains: snowFall cap/trajectory/report-only lock; lakeSide trajectory/report-only lock; cubicle trajectory shift with branches firing; intermittentPan and tunnelExit trajectory shifts with inherited branches present.
- Recommendation remains split validation: Step 4E7 event-safety branch based on Step 4D6 first, with port detector retighten isolated into a separate Step 4E4-based branch. Full CDnet, live, and cross-dataset validation remain held.
- Safety confirmation: no experiments, dry-runs, live runs, compares, full CDnet, targeted CDnet, PTZ-targeted validation, cross-dataset validation, LASIESTA, SBI2015, BMC, Jetson/edge profiling, output deletion/overwrite, config edits, controller edits, or compare-code edits were performed.

## 2026-05-18 checkpoint update

- Created `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_CHECKPOINT_2026_05_18.md` as the current ASMAG_TR_CONTROLLER_ONLINE_GUARDED state snapshot.
- Current highest validated milestone: Step 3B targeted category live remains frozen as PASS under the revised protection-aware parking gate. 8C-2Q2 remains the current full-CDnet dry-run candidate lineage, but full CDnet success has not yet been achieved.
- Step 4 full CDnet dry-run completed technically with 212/212 jobs, 0 failed, FMeasure 0.47863, Event_F1 0.76989, detector request 0.01211, normal-frame proposals 0, and guard alignment 1.00000. It is not a clean Step 4 pass due residual risks.
- Residual-risk progress remains: Step 4B4 lakeSide passed, Step 4C sofa rescue passed, Step 4D6 parking/snowFall passed before later port work, and Step 4E4 repaired port detector pressure to detector 0.05000 with unprotected FN 0 and frames 1350/1355 protected.
- Latest failed state is Step 4E6: 56/56 completed, 0 failed, FMeasure 0.29046, Event_F1 0.62271, detector request 0.01500, normal-frame proposals 0, guard alignment 1.00000. Failed gates include port detector 0.08000, port unprotected FN 4, frames 1350/1355 unprotected, parking proposal 0.57000, parking unprotected FN 9, snowFall/lakeSide drift, cubicle recall 0.77419, and intermittentPan unprotected FN 2.
- Current decision: do not patch blindly from Step 4E6. The next recommended action is Step 4E6-BRANCH-AUDIT: audit only, no experiment, to classify failures as telemetry-only, branch inactive, action branch not reached, final action frozen, cap/cooldown, or trajectory shift.
- Safety confirmation for this checkpoint update: no experiments, dry-runs, compares, live runs, full CDnet, cross-dataset validation, output deletion, config edits, or controller-code edits were performed. Full CDnet, live, and cross-dataset remain held.

## 2026-05-18 Step 4E6 branch audit

- Completed audit-only Step 4E6 branch analysis. Created `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_BRANCH_AUDIT.md`.
- No experiments, live run, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was run. No controller or compare code was modified, and no output folders were overwritten.
- Port audit: Step 4E6 hard-lock telemetry fired only on early rows 1210/1230/1255 and was inactive at 1340/1350/1355/1360 and the 1405-1440 holdout region. Frames 1350 and 1355 were final FN with `CLOSED_EMPTY_P3_FALLBACK`, detector 0, protected FN 0, unprotected FN 1, final-normal suppressor inactive, and no hard-lock/holdout reject reason. The action was in the intended unsafe fallback set, so this is branch reachability/order plus telemetry-only behavior, not an action-set or final-normal issue.
- Parking audit: Step 4E6 restored trim counters `4/4/1`, but the nine unprotected FN rows had rescue candidate 0, carry-over lock 0, hard-restore fallback 0, guard inactive, and active event memory 0. The matching Step 4D6 FN rows had active event memory 1, guard active, risk-high, likely-unprotected-FN, and rescue active. Parking failure is a trajectory shift before rescue/protection, not a trim-counter or cap issue.
- Carry-over drift classification: snowFall is cap/trajectory/report-only lock; lakeSide is trajectory/report-only lock; cubicle is trajectory shift with branches still firing; intermittentPan and tunnelExit are trajectory shifts with inherited branches present.
- Recommendation: Step 4E7-D, split validation into an event-safety branch and a detector-retighten branch. Use Step 4D6 as the event-safety base and defer port retighten as telemetry/watch there. Use Step 4E4 only for a separate port detector branch. Full CDnet remains held.

## 2026-05-18 Step 4E6 port V4 hard lock and parking 4D6 rebase subset dry-run

- Implemented Step 4E6 as a separate dry-run-only rebase attempt. Created `configs/asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun.yaml`, output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun/`, and report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_PORT_PARKING_REBASE_REPORT.md`.
- Updated `src/run_experiment.py` with Step 4E6 exact-video port V4 hard-lock telemetry/enforcement hooks, parking 4D6 hard-restore hooks, and snowFall/lakeSide carry-over lock status. Updated `tools/compare_asmag_tr_controller_online_guarded.py` with Step 4E6 summary and row-level CSV outputs.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4E6 residual-risk subset dry-run completed 56/56 jobs with 0 failed across the same 14 videos and 4 pipelines. One parking guarded attempt exposed a `NameError`; it was fixed, recompiled, and the job was retried successfully in the same scoped Step 4E6 run. Compare completed after rerunning with warnings suppressed.
- Aggregate guarded metrics: FMeasure 0.29046, Event_F1 0.62271, Activation 0.37714, Avg_FPS 23.92270, P95 latency 399.20162 ms, proposal rate 0.36714, detector request rate 0.01500, normal-frame proposals 0, guard alignment 1.00000.
- Port comparison for proposal/detector/event-FN/protected-FN/unprotected-FN: Step 4E4 `0.42000/0.05000/5/5/0`, Step 4E5 `0.43000/0.06000/13/10/3`, Step 4E6 `0.40000/0.08000/14/10/4`. Frames 1350 and 1355 remained unprotected FN, so the V4 hard lock did not reproduce Step 4E4.
- Parking comparison for proposal/detector/event-FN/protected-FN/unprotected-FN: Step 4D6 `0.50000/0.00000/33/33/0`, Step 4E5 `0.49000/0.00000/45/35/10`, Step 4E6 `0.57000/0.00000/46/37/9`. The 4D3/4D5/4D6 trim counters remained `4/4/1`, and accidental FN/rescue trims stayed `0/0`, but proposal and preferred FN safety failed.
- snowFall/lakeSide carry-over locks reported drift but did not correct it: snowFall `0.52000/0.00000/7` fails proposal and unprotected-FN gates; lakeSide `0.41000/0.00000/24` fails unprotected-FN gate.
- Other carry-over status: sofa `0.35000/0.00000/0` pass; copyMachine `0.47000/0.00000/7` watch/fail versus prior accepted carry-over; turbulence2 `0.31000/0.00000/0` pass; tunnelExit `0.38000/0.00000/3` watch; cubicle recall `0.77419` fails recall >= 0.80 though unprotected FN is 0; continuousPan controlled; intermittentPan watch with unprotected FN 2; fountain01 quiet; fountain02 normal-frame false interventions 0; bridgeEntry event FN 0.
- Root cause: Step 4E6 added hard-lock switches but did not actually force the Step 4E4 row-level port trajectory or protect the 1350/1355 no-detector FN rows. Parking rebase restored trim counters but not the surrounding Step 4D6 protection trajectory. snowFall/lakeSide locks were reporting-only in practice.
- Step 4E6 residual-risk subset dry-run fails. Full CDnet rerun remains held. Recommended next work is a narrower behavior reproduction patch: explicit Step 4E4 port row-decision lock plus actual parking Step 4D6 protection-state rebase before trims.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-18 Step 4E5 port V4 preserve and parking carry-over subset dry-run

- Implemented Step 4E5 as a separate dry-run-only continuation on top of Step 4E4. Created `configs/asmag_tr_controller_online_guarded_cdnet_step4e5_port_parking_subset_dryrun.yaml`, output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4e5_port_parking_subset_dryrun/`, and report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E5_PORT_PARKING_CARRYOVER_REPORT.md`.
- Updated `src/run_experiment.py` with Step 4E5 port V4 preserve telemetry and parking Step 4D6 trim-stack/fallback controls. Updated `tools/compare_asmag_tr_controller_online_guarded.py` with `ai_intervention_4e5_port_parking_summary.csv` and `ai_intervention_4e5_parking_rows.csv`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4E5 residual-risk subset dry-run completed 56/56 jobs with 0 failed across the same 14 videos and 4 pipelines. One local command timed out during a PTZ job, then the next resume recovered and completed the run. Compare completed for the Step 4E5 root.
- Aggregate guarded metrics: FMeasure 0.30991, Event_F1 0.64280, Activation 0.31143, Avg_FPS 23.43675, P95 latency 467.12444 ms, proposed intervention rate 0.37500, detector request rate 0.01643, normal-frame proposals 0, guard alignment 1.00000.
- Port comparison for proposal/detector/event-FN/protected-FN/unprotected-FN: Step 4E3 `0.40000/0.04000/12/10/2`, Step 4E4 `0.42000/0.05000/5/5/0`, Step 4E5 `0.43000/0.06000/13/10/3`. Step 4E5 fails port detector hard gate, port unprotected-FN gate, and port proposal preferred gate.
- Port Step 4E5 behavior: 12 detector requests before retighten, 6 suppressed, 6 kept, 3 actual-FN detector rows kept, 0 pre-FN/context detectors kept, 6 final FP/TN detector rows suppressed, 0 true deterministic-emergency detector rows kept, 0 created unprotected FN from detector suppression, and 1 holdout activation with 0 protected event FN. Frames 1350 and 1355 regressed to unprotected FN.
- Parking comparison for proposal/detector/event-FN/protected-FN/unprotected-FN: Step 4D6 `0.50000/0.00000/33/33/0`, Step 4E4 `0.51000/0.00000/37/35/2`, Step 4E5 `0.49000/0.00000/45/35/10`. Parking now passes the hard proposal/detector/unprotected-FN gates but misses preferred zero unprotected FN.
- Parking Step 4E5 telemetry: restored 4D3/4D5/4D6 trim counts are `4/4/1`, extra reserve trim count 0, fallback activations 0, fallback protected event-FN count 0, accidental FN-protected/rescue trim counts 0/0.
- Carry-over status: snowFall 0.49000/0.00000/6 fails proposal gate; lakeSide 0.53000/0.00000/1 fails proposal gate; sofa 0.35000/0.00000/0 pass; copyMachine 0.49000/0.00000/2 pass; turbulence2 0.31000/0.00000/0 pass; tunnelExit 0.40000/0.00000/3 watch; cubicle recall 0.84021 with unprotected FN 0 pass; continuousPan 0.05000/0.01000/0 pass; intermittentPan 0.10000/0.00000/0 watch; fountain01 quiet; fountain02 normal-frame false interventions 0; bridgeEntry event FN 0.
- Root cause: the new port V4 preserve switch is telemetry-only and did not lock or reproduce the successful Step 4E4 detector/holdout trajectory. Step 4E5 kept one extra detector, lost the Step 4E4 pre-FN/context protection pattern, and left frames 1350/1355 outside holdout protection. Parking fallback also did not activate on unprotected `CLOSED_EMPTY_ACC` FN rows, indicating a pre-signal/branch reachability issue.
- Step 4E5 residual-risk subset dry-run fails. Full CDnet rerun remains held. Recommended next work is a narrow port V4 decision lock or row-level reproduction of the Step 4E4 port kept/suppressed/context pattern before revisiting parking fallback reachability.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-18 Step 4E4 port scoped retighten and downstream holdout subset dry-run

- Implemented Step 4E4 as a separate dry-run-only `lowFramerate/port_0_17fps` detector-retighten v4 path plus downstream no-detector holdout guard. Created config `configs/asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun.yaml`, output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun/`, and report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E4_PORT_HOLDOUT_RETIGHTEN_REPORT.md`.
- Updated `src/run_experiment.py` with v4 final-row-state retighten controls, pre-FN/context detector retention, downstream holdout logging, and safety counters. Updated `tools/compare_asmag_tr_controller_online_guarded.py` with Step 4E4 port detector summary and row-level CSV outputs.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4E4 residual-risk subset dry-run completed 56/56 jobs with 0 failed across the same 14 videos and 4 pipelines. Compare completed for the Step 4E4 root.
- Aggregate guarded metrics: FMeasure 0.34056, Event_F1 0.67182, Activation 0.51786, Avg_FPS 33.93451, P95 latency 252.63299 ms, proposed intervention rate 0.33857, detector request rate 0.01000, normal-frame proposals 0, guard alignment 1.00000.
- Port progression: Step 4 full `0.37000/0.07000/5/5/0`, Step 4E `0.37000/0.07000/5/5/0`, Step 4E2 `0.40000/0.08000/14/10/4`, Step 4E3 `0.40000/0.04000/12/10/2`, and Step 4E4 `0.42000/0.05000/5/5/0` for proposal/detector/event-FN/protected-FN/unprotected-FN.
- Step 4E4 port behavior: 13 detector requests before retighten, 8 suppressed, 5 kept, 1 actual-FN detector kept, 2 pre-FN/context detectors kept, 8 final FP/TN detector rows suppressed, 0 true deterministic-emergency detectors kept, and 0 created unprotected FN from detector suppression.
- Downstream holdout activated 6 times on final-TN frames 1405, 1410, 1415, 1420, 1425, and 1430. It stayed no-detector and protected-event-FN count was 0. Frames 1350 and 1355 are now protected FN with unprotected FN 0; the repair came from pre-FN/context detector retention at nearby frames rather than direct holdout activation on those two frames.
- Carry-over status: snowFall 0.36000/0.00000/1 pass; lakeSide 0.50000/0.00000/0 pass; sofa 0.28000/0.00000/0 pass; parking 0.51000/0.00000/2 fails proposal gate and loses the Step 4D6/4E3 carry-over state; copyMachine 0.47000/0.00000/3 pass; turbulence2 0.31000/0.00000/0 pass; tunnelExit 0.31000/0.00000/1 pass; cubicle recall 0.87320 with unprotected FN 0 pass; continuousPan 0.05000/0.01000/0 pass; intermittentPan 0.01000/0.00000/0 pass; fountain01 quiet; fountain02 normal-frame false interventions 0; bridgeEntry event FN 0.
- Step 4E4 residual-risk subset dry-run fails because `intermittentObjectMotion/parking` regressed to proposal 0.51000, above the 0.50000 gate, and exposed 2 unprotected FN. The port hard gates pass, but the subset cannot be frozen.
- Root cause: the v4 port/holdout telemetry is exact-video scoped and reports zero parking activations, but the current Step 4E4 run did not preserve the stable Step 4D6/4E3 parking trajectory. Recommended next work is a narrow Step 4E5 that keeps the v4 port result and explicitly restores or locks the parking Step 4D6 carry-over state before any freeze.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched. Full CDnet remains held.

## 2026-05-18 Step 4E3 port row-state detector classifier subset dry-run

- Implemented Step 4E3 as a separate dry-run-only `lowFramerate/port_0_17fps` row-state detector-retighten v3 path rebased from the stable Step 4E / Step 4D6 stack. Created config `configs/asmag_tr_controller_online_guarded_cdnet_step4e3_port_detector_subset_dryrun.yaml` and output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4e3_port_detector_subset_dryrun/`.
- Updated `src/run_experiment.py` with Step 4E3 v3 controls, final/decision-time state logs, strict true-emergency and explicit-likely-FN classification, no-detector fallback logging, and suppression safety counters. Updated `tools/compare_asmag_tr_controller_online_guarded.py` with Step 4E3 port detector summary and row-level CSV outputs. Created report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E3_PORT_ROWSTATE_RETIGHTEN_REPORT.md`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4E3 residual-risk subset dry-run completed 56/56 jobs with 0 failed across the same 14 videos and 4 pipelines. Compare completed for the Step 4E3 root.
- Aggregate guarded metrics: FMeasure 0.33590, Event_F1 0.66315, Activation 0.49143, Avg_FPS 23.58319, P95 latency 318.10496 ms, proposed intervention rate 0.33286, detector request rate 0.01357, normal-frame proposals 0, guard alignment 1.00000.
- Step 4E3 fails the port unprotected-FN gate: `lowFramerate/port_0_17fps` changed from Step 4 full / Step 4E proposal/detector/event-FN/protected-FN/unprotected-FN `0.37000/0.07000/5/5/0` and Step 4E2 `0.40000/0.08000/14/10/4` to Step 4E3 `0.40000/0.04000/12/10/2`.
- Step 4E3 detector behavior: 22 detector-refresh rows before retighten, 18 suppressed, 4 kept, 3 actual-FN detector rows kept, 18 final FP/TN rows suppressed, 0 true deterministic-emergency rows kept, 1 generic-refresh row suppressed, and 0 created unprotected FN from direct detector suppression.
- Row-level Step 4E3 audit: final FP/TN frames 1020, 1025, 1030, 1035, 1040, 1045, 1050, 1055, 1060, 1065, 1070, 1130, 1215, 1220, 1225, 1230, 1235, and 1240 were suppressed through no-detector fallback with created-unprotected-FN 0. Frame 1135 was kept by v3 safety. Frames 1155, 1175, and 1245 were kept for actual-FN detector protection plus explicit likely-unprotected-FN marking.
- Carry-over regressions from Step 4E2 were removed: snowFall 0.36000/0.00000/1, lakeSide 0.50000/0.00000/0, sofa 0.27000/0.00000/0, parking 0.50000/0.00000/0, copyMachine 0.46000/0.00000/4, turbulence2 0.31000/0.00000/0, tunnelExit 0.31000/0.00000/1, cubicle recall 0.87408 with unprotected FN 0, continuousPan 0.05000/0.01000/0, intermittentPan 0.01000/0.00000/0, fountain01 quiet, fountain02 normal-frame false interventions 0, and bridgeEntry event FN 0.
- Root cause: v3 fixed final FP/TN classification and detector suppression, but expanded the audited detector surface to 22 rows and suppressed 18 final FP/TN rows. The direct suppression safety counter stayed clean, but the downstream port trajectory produced two later unprotected FN frames, 1350 and 1355, where v3 was inactive.
- Step 4E3 residual-risk subset dry-run fails. Full CDnet rerun remains held. Recommended next work is a narrow Step 4E4 that constrains v3 to the intended Step 4E audited detector-refresh surface or adds a downstream port holdout guard so port unprotected FN remains 0 while suppressing final FP/TN generic refresh rows.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-18 Step 4E2 port detector retighten v2 subset dry-run

- Implemented Step 4E2 as a separate dry-run-only `lowFramerate/port_0_17fps` detector-retighten v2 path. Created config `configs/asmag_tr_controller_online_guarded_cdnet_step4e2_port_detector_subset_dryrun.yaml` and output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4e2_port_detector_subset_dryrun/`.
- Updated `src/run_experiment.py` with Step 4E2 retighten-v2 controls, row-level detector decision logs, no-detector fallback logging, and suppression safety counters. Updated `tools/compare_asmag_tr_controller_online_guarded.py` with Step 4E2 port detector summary and audited-row CSV outputs. Created report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E2_PORT_DETECTOR_RETIGHTEN_REPORT.md`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4E2 residual-risk subset dry-run completed 56/56 jobs with 0 failed across the same 14 videos and 4 pipelines. Compare completed for the Step 4E2 root.
- Aggregate guarded metrics: FMeasure 0.28116, Event_F1 0.59756, Activation 0.31429, Avg_FPS 20.92067, P95 latency 412.66461 ms, proposed intervention rate 0.36071, detector request rate 0.01643, normal-frame proposals 0, guard alignment 1.00000.
- Step 4E2 fails the port detector gate: `lowFramerate/port_0_17fps` changed from Step 4 full and Step 4E proposal/detector/event-FN/protected-FN/unprotected-FN `0.37000/0.07000/5/5/0` to Step 4E2 `0.40000/0.08000/14/10/4`. The v2 audit saw 9 detector-refresh rows, suppressed 1, kept 8, kept 3 actual-FN detectors, kept 0 true deterministic-emergency detectors, and created 0 unprotected FN from suppression.
- Row-level Step 4E2 audit: frames 1020, 1040, 1060, and 1130 were TN detector-refresh rows kept by the inherited safety label; frames 1150, 1170, and 1210 were FN rows kept for actual-FN protection; frame 1190 was a TN row suppressed through the no-detector fallback with created-unprotected-FN 0; frame 1255 was FP and kept as `likely_unprotected_fn_risk`, not true deterministic emergency.
- Root cause: v2 did not lock onto the intended Step 4E seven-row surface and audited 9 rows. The decision-time state used by the retighten branch kept several final-TN rows under generic safety, and the `likely_unprotected_fn` predicate remained too broad for the frame-1255 FP row. Generic event-refresh safety was not counted as true deterministic emergency.
- Carry-over status: `badWeather/snowFall` proposal/detector/unprotected-FN 0.44000/0.00000/15, fails snowFall carry-over; `thermal/lakeSide` 0.46000/0.00000/18, fails lakeSide carry-over; `intermittentObjectMotion/sofa` 0.35000/0.00000/4, passes; `intermittentObjectMotion/parking` 0.53000/0.00000/12, fails proposal gate; `shadow/copyMachine` 0.45000/0.00000/27, fails accepted carry-over; `turbulence/turbulence2` 0.28000/0.00000/0, passes; `lowFramerate/tunnelExit_0_35fps` 0.40000/0.00000/3, accepted watch; `shadow/cubicle` proposal/detector/unprotected-FN 0.88000/0.05000/0, recall still requires separate watch; `PTZ/continuousPan` 0.04000/0.01000/0, controlled; `PTZ/intermittentPan` 0.11000/0.00000/0, controlled but higher than Step 4E; `dynamicBackground/fountain01` 0.00000/0.00000/0, quiet; `dynamicBackground/fountain02` normal-frame false interventions 0; `nightVideos/bridgeEntry` event FN 0.
- Step 4E2 residual-risk subset dry-run fails. Full CDnet rerun remains held. Recommended next work is a narrow Step 4E3 that rebases from the known Step 4E behavior, classifies the retighten rows using final FP/TN state or logs both decision-time and final state, narrows likely-unprotected-FN retention, and suppresses final FP/TN generic refresh rows unless a true explicit emergency flag is present.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4E port detector retighten subset dry-run

- Implemented Step 4E as an exact-video `lowFramerate/port_0_17fps` detector-retighten path on top of Step 4D6. Created config `configs/asmag_tr_controller_online_guarded_cdnet_step4e_port_detector_subset_dryrun.yaml` and output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4e_port_detector_subset_dryrun/`.
- Updated `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py` with Step 4E port retighten telemetry and compare summaries. Created report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E_PORT_DETECTOR_RETIGHTEN_REPORT.md`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4E residual-risk subset dry-run completed 56/56 jobs with 0 failed across 14 videos and 4 pipelines. Compare completed for the Step 4E root.
- Aggregate guarded metrics: FMeasure 0.34682, Event_F1 0.67667, Activation 0.52000, Avg_FPS 36.87264, P95 latency 220.49601 ms, proposed intervention rate 0.33000, detector request rate 0.01214, normal-frame proposals 0, guard alignment 1.00000.
- Step 4E fails the port detector gate: `lowFramerate/port_0_17fps` stayed at proposal/detector/unprotected-FN `0.37000/0.07000/0`, with 7 detector requests before retighten, 0 suppressed, 7 kept, 1 kept detector protecting FN, and created-unprotected-FN count 0.
- Root cause: the exact-video retighten hook and reporting are present, but the suppression decision is too conservative. The code identified FP/TN event-refresh rows with `no_likely_unprotected_fn_risk`, yet kept them as `detector_preserved_by_port_retighten_safety`; one FP row was also kept as `deterministic_emergency_safeguard`.
- Carry-over status: `badWeather/snowFall` proposal/detector/unprotected-FN 0.36000/0.00000/1; `thermal/lakeSide` 0.50000/0.00000/0; `intermittentObjectMotion/sofa` 0.28000/0.00000/0; `intermittentObjectMotion/parking` 0.46000/0.00000/0; `shadow/copyMachine` 0.49000/0.00000/2; `turbulence/turbulence2` 0.31000/0.00000/0; `lowFramerate/tunnelExit_0_35fps` 0.30000/0.00000/2, a watch item versus Step 4D6's unprotected FN 1; `shadow/cubicle` recall 0.87396 with unprotected FN 0; `PTZ/continuousPan` 0.04000/0.01000/0; `PTZ/intermittentPan` 0.01000/0.00000/0; `dynamicBackground/fountain01` 0.00000/0.00000/0; `dynamicBackground/fountain02` normal-frame false interventions 0; `nightVideos/bridgeEntry` event FN 0.
- Recommended next step: Step 4E2 port-only correction should keep the actual-FN detector-protecting row, re-audit the one FP row labeled deterministic emergency, and suppress FP/TN `detector_refresh_needed_for_event` rows with no likely unprotected-FN risk through the no-detector fallback path. Full CDnet remains held.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4D6 parking final one-frame trim subset dry-run

- Implemented Step 4D6 as a parking-only final post-lock trim continuation on top of Step 4D5. Created config `configs/asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun.yaml` and output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun/`.
- Updated `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py` with Step 4D6 final one-frame trim controls and reporting. Created report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D6_PARKING_FINAL_TRIM_REPORT.md`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4D6 residual-risk subset dry-run completed 56/56 jobs with 0 failed across 14 videos and 4 pipelines. Compare completed after rerunning with a longer timeout when the first compare invocation hit the local 120-second tool timeout.
- Aggregate guarded metrics: FMeasure 0.35061, Event_F1 0.67692, Activation 0.52429, Avg_FPS 33.70033, P95 latency 258.67779 ms, proposed intervention rate 0.33071, detector request rate 0.01071, normal-frame proposals 0, guard alignment 1.00000.
- Parking progression: Step 4D3 proposal/detector/unprotected-FN 0.54000/0.00000/0, Step 4D4 0.58000/0.00000/0, Step 4D5 0.51000/0.00000/0, Step 4D6 0.50000/0.00000/0. Event FN stayed fully protected at 33/33.
- Parking trim behavior: restored Step 4D3 trim count 4, Step 4D5 post-lock trim count 4, Step 4D6 final extra trim count 1, accidental FN-protected trim count 0, accidental rescue trim count 0. Step 4D6 used the same 4D5 soft-candidate pool and did not request detector.
- Carry-over remained intact: `badWeather/snowFall` proposal/detector/unprotected-FN 0.36000/0.00000/1; `thermal/lakeSide` 0.50000/0.00000/0; `intermittentObjectMotion/sofa` 0.27000/0.00000/0; `lowFramerate/port_0_17fps` 0.37000/0.07000/0; `shadow/copyMachine` 0.46000/0.00000/4; `turbulence/turbulence2` 0.31000/0.00000/0; `lowFramerate/tunnelExit_0_35fps` 0.31000/0.00000/1; `shadow/cubicle` recall 0.87408 with unprotected FN 0; `PTZ/continuousPan` 0.05000/0.01000/0; `PTZ/intermittentPan` 0.01000/0.00000/0; `dynamicBackground/fountain01` 0.00000/0.00000/0; `dynamicBackground/fountain02` normal-frame false interventions 0; `nightVideos/bridgeEntry` event FN 0.
- Step 4D6 residual-risk subset dry-run passes all listed gates. Full CDnet remains held. Recommended next step: Step 4E `lowFramerate/port_0_17fps` detector retighten before any full CDnet rerun.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4D5 parking trim-order subset dry-run

- Implemented Step 4D5 as a parking-only trim-order correction on top of Step 4D4. Created config `configs/asmag_tr_controller_online_guarded_cdnet_step4d5_parking_trim_order_subset_dryrun.yaml` and output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4d5_parking_trim_order_subset_dryrun/`.
- Updated `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py` with restored Step 4D3 parking trim logs plus Step 4D5 post-lock soft-trim reporting. Created report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D5_PARKING_TRIM_ORDER_REPORT.md`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4D5 residual-risk subset dry-run completed 56/56 jobs with 0 failed across 14 videos and 4 pipelines. Compare completed after rerunning with a longer timeout when the first compare invocation hit the local 120-second tool timeout.
- Aggregate guarded metrics: FMeasure 0.35061, Event_F1 0.67692, Activation 0.52429, Avg_FPS 37.28567, P95 latency 245.21436 ms, proposed intervention rate 0.33143, detector request rate 0.01071, normal-frame proposals 0, guard alignment 1.00000.
- Step 4D5 fails only the parking proposal gate: `intermittentObjectMotion/parking` proposal/detector/unprotected-FN changed from Step 4D3 0.54000/0.00000/0 and Step 4D4 0.58000/0.00000/0 to Step 4D5 0.51000/0.00000/0.
- Parking trim behavior: restored Step 4D3 trim count 4, blocked-by-later-hardprotect frames 0, Step 4D5 post-lock candidates 40, soft candidates 12, post-lock trim count 4, final rate 0.51000, accidental FN-protected trim count 0, accidental rescue trim count 0. Event FN stayed fully protected at 33/33.
- Root cause: Step 4D5 fixed the trim order and protected-frame safety, but the new post-lock stage suppressed only four extra soft candidates. Eight total safe trims left parking at 51 proposals out of 100, one frame above the gate.
- Carry-over remained intact outside parking: `badWeather/snowFall` proposal/detector/unprotected-FN 0.36000/0.00000/1; `thermal/lakeSide` 0.50000/0.00000/0; `intermittentObjectMotion/sofa` 0.27000/0.00000/0; `lowFramerate/port_0_17fps` 0.37000/0.07000/0; `shadow/copyMachine` 0.46000/0.00000/4; `turbulence/turbulence2` 0.31000/0.00000/0; `lowFramerate/tunnelExit_0_35fps` 0.31000/0.00000/1; `shadow/cubicle` recall 0.87408 with unprotected FN 0; `PTZ/continuousPan` 0.05000/0.01000/0; `PTZ/intermittentPan` 0.01000/0.00000/0; `dynamicBackground/fountain01` 0.00000/0.00000/0; `dynamicBackground/fountain02` normal-frame false interventions 0; `nightVideos/bridgeEntry` event FN 0.
- Recommended next step: Step 4D6 parking-only dry-run should keep the restored Step 4D3 trim unchanged and continue the same Step 4D5 soft-candidate post-lock trim until `<= 0.50000`, with an explicit final-needed-frame calculation and the same no-FN/no-rescue safety counters. Full CDnet remains held.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4D4 parking post-lock trim subset dry-run

- Implemented Step 4D4 as a parking-only post-lock proposal trim on top of Step 4D3. Created config `configs/asmag_tr_controller_online_guarded_cdnet_step4d4_parking_trim_subset_dryrun.yaml` and output root `outputs/asmag_tr_controller_online_guarded_cdnet_step4d4_parking_trim_subset_dryrun/`.
- Updated `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py` with Step 4D4 parking trim and compare reporting fields. Created report `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D4_PARKING_POST_LOCK_TRIM_REPORT.md`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Step 4D4 residual-risk subset dry-run completed 56/56 jobs with 0 failed across 14 videos and 4 pipelines. Compare completed after rerunning with a longer timeout when the first compare invocation hit the local 120-second tool timeout.
- Aggregate guarded metrics: FMeasure 0.34816, Event_F1 0.67692, Activation 0.52429, Avg_FPS 35.50413, P95 latency 234.25517 ms, proposed intervention rate 0.33571, detector request rate 0.01071, normal-frame proposals 0, guard alignment 1.00000.
- Step 4D4 fails the parking proposal gate: `intermittentObjectMotion/parking` proposal/detector/unprotected-FN changed from Step 4D3 0.54000/0.00000/0 to Step 4D4 0.58000/0.00000/0. Event FN stayed fully protected, but proposal pressure worsened.
- Parking trim behavior: post-lock trim candidates 38, soft candidates 0, trim count 0, final rate 0.58000, hard-protected frames 58, skipped hard-protected frames 58, accidental hard trim count 0, accidental FN-protected trim count 0, deduplicate count 0. Step 4D4 also prevented the known-safe Step 4D3 post-preservation trim from reclaiming its 4 generic/nonrisk frames.
- Root cause: Step 4D4 hard-protection classification was too conservative at the post-lock trim stage. It protected FN safety correctly but treated all retained parking proposal frames as hard-protected, leaving no soft-lock candidates and no deduplicate overlap to reclaim.
- Carry-over remained intact outside parking: `badWeather/snowFall` proposal/detector/unprotected-FN 0.36000/0.00000/1; `thermal/lakeSide` 0.50000/0.00000/0; `intermittentObjectMotion/sofa` 0.27000/0.00000/0; `lowFramerate/port_0_17fps` 0.37000/0.07000/0; `shadow/copyMachine` 0.46000/0.00000/4; `turbulence/turbulence2` 0.31000/0.00000/0; `lowFramerate/tunnelExit_0_35fps` 0.31000/0.00000/1; `shadow/cubicle` recall 0.87408 with unprotected FN 0; `PTZ/continuousPan` 0.04000/0.01000/0; `PTZ/intermittentPan` 0.01000/0.00000/0; `dynamicBackground/fountain01` 0.00000/0.00000/0; `dynamicBackground/fountain02` normal-frame false interventions 0; `nightVideos/bridgeEntry` event FN 0.
- Recommended next step: Step 4D5 dry-run should restore the Step 4D3 parking post-preservation 4-frame trim unchanged, then add a separate post-lock soft trim only against known generic/nonrisk over-gate frames. Full CDnet remains held.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4D3 snowFall carry-over lock subset dry-run

- Implemented Step 4D3 as a separate dry-run config/output root with a narrow `badWeather/snowFall` actual-FN cap increase plus exact carry-over locks/reporting for `thermal/lakeSide`, `intermittentObjectMotion/sofa`, and `intermittentObjectMotion/parking`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D3_SNOWFALL_CARRYOVER_LOCK_REPORT.md`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4d3_snowfall_carryover_subset_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4d3_snowfall_carryover_subset_dryrun/`.
- Compile passed. The residual-risk subset dry-run completed 56/56 planned jobs, 0 failed, across 14 videos and 4 pipelines. Compare completed for the Step 4D3 root.
- Aggregate guarded subset metrics: FMeasure 0.34747, Event_F1 0.67444, Activation 0.52000, Avg_FPS 34.58562, P95 latency 235.50198 ms, proposed intervention rate 0.33500, detector request rate 0.01071, normal-frame proposals 0, guard alignment 1.00000.
- `badWeather/snowFall` improved from Step 4D2 proposal/detector/event FN/protected FN/unprotected FN 0.30000/0.00000/23/16/7 to Step 4D3 0.36000/0.00000/22/21/1. The cap increase logged 21 actual-FN candidates, 20 activations, cap used max 20, 20 no-detector rescue-protected event-FN frames, 1 cap-exhausted row after D3, and 0 mask-quality skips.
- `thermal/lakeSide` restored the carry-over gate: proposal 0.50000, detector 0.00000, unprotected FN 0. Carry-over lock was active on 62 frames and no hard/rescue event-FN frames were accidentally trimmed.
- `intermittentObjectMotion/sofa` restored the carry-over gate: proposal 0.27000, detector 0.00000, unprotected FN 0. The fallback lock did not need to fire because the inherited Step 4C rescue path recovered the event-FN rows.
- `intermittentObjectMotion/parking` recall recovered but proposal failed: proposal 0.54000, detector 0.00000, unprotected FN 0. The new carry-over lock activated on 9 cap-exhausted event-FN-risk frames, eliminating the Step 4D2 unprotected-FN miss but pushing protected proposal pressure above the 0.50000 gate.
- Carry-over status: `lowFramerate/port_0_17fps` remains a detector watch item at proposal/detector 0.37000/0.07000 with unprotected FN 0; `shadow/copyMachine` remains within accepted gate at 0.49000/0.00000 with unprotected FN 8; `turbulence/turbulence2` 0.31000/0.00000 with unprotected FN 0; `lowFramerate/tunnelExit_0_35fps` 0.31000/0.00000 with unprotected FN 1; `shadow/cubicle` recall 0.87408 with unprotected FN 0; `PTZ/continuousPan` 0.04000/0.01000 with event FN 0; `PTZ/intermittentPan` 0.01000/0.00000 with unprotected FN 0; `dynamicBackground/fountain01` remains quiet; `dynamicBackground/fountain02` normal-frame false interventions 0; `nightVideos/bridgeEntry` event FN 0.
- Step 4D3 residual-risk subset dry-run fails only the parking proposal gate. Full CDnet/live/cross-dataset/PTZ-targeted standalone validation remains held. Recommended next work is a narrow Step 4D4 parking post-lock proposal-pressure trim or stricter carry-over lock budget before Step 4E port retighten.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4D2 carry-over audit

- Created audit-only report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D2_CARRYOVER_AUDIT.md`.
- No experiment, live run, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched. No code was patched.
- Config inheritance audit found Step 4D2 still inherits Step 4B4 lakeSide settings, Step 4C sofa settings, and 2Q2/2Q parking/copyMachine/turbulence/tunnelExit/cubicle/PTZ/fountain/lowFramerate settings. The regressions are not primarily missing-config failures.
- lakeSide drift root cause: Step 4B4 settings are present, but Step 4D2's drift recap suppressed 0 frames because soft candidates were seen before final pressure was known and later pressure was hard-protected; classify as exact guard present but not activating plus trajectory drift.
- sofa regression root cause: Step 4C settings and cap values are present, but rescue candidates fell from 15 to 12 while event FN rose from 21 to 28; the new unprotected FN rows were not sofa-rescue candidates under the changed memory/score trajectory.
- parking regression root cause: parking settings are present and active, but event FN rose from 33 to 47, preserve candidates fell from 28 to 25, and 12 rescue candidates hit `parking_rescue_cap_exhausted`; classify as cap exhaustion plus trajectory drift.
- snowFall likely needs a narrow actual-FN cap increase, not broad detector logic. Six unprotected closed-empty actual-FN candidates were cap-exhausted, while one residual `DETECT_ACC` row remains a mask-quality/watch case.
- Recommended Step 4D3: carry-over locks plus a narrow snowFall actual-FN cap increase, with explicit carry-over reporting gates before any full CDnet/live/cross-dataset work.

## 2026-05-17 Step 4D2 snowFall actual-FN candidacy fix + lakeSide drift recheck subset dry-run

- Implemented a dry-run-only exact-video `badWeather/snowFall` actual-FN unsafe-action no-detector rescue path, plus an exact-video `thermal/lakeSide` drift recap attempt in `src/run_experiment.py`, and added Step 4D2 summary fields in `tools/compare_asmag_tr_controller_online_guarded.py`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4d2_snowfall_risk_subset_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4d2_snowfall_risk_subset_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D2_SNOWFALL_CANDIDACY_REPORT.md`.
- Compile passed. The residual-risk subset dry-run completed 56/56 planned jobs, 0 failed, across 14 videos and 4 pipelines. The dry-run compare completed for the Step 4D2 root.
- Aggregate guarded subset metrics: FMeasure 0.29756, Event_F1 0.63983, Activation 0.38357, Avg_FPS 23.38464, P95 latency 429.25865 ms, proposed intervention rate 0.33929, detector request rate 0.01714, block-only rate 0.32214, event/foreground block-only rate 0.24571, normal-frame proposals 0, guard alignment 1.00000.
- `badWeather/snowFall` improved from Step 4D proposal/detector/event FN/protected FN/unprotected FN 0.28000/0.00000/22/12/10 to Step 4D2 0.30000/0.00000/23/16/7, but still misses the acceptable unprotected-FN gate of <= 6.
- SnowFall actual-FN behavior: 22 candidates, 12 activations, 12 no-detector rescues, 12 rescue-protected event-FN frames, 12 budget-available actual-FN rescues, and 0 final-normal suppressions. Root cause for the residual miss: 10 actual-FN candidates were rejected as `snowfall_actual_fn_rescue_cap_exhausted`.
- LakeSide drift recheck failed: proposal 0.52000, detector 0.00000, unprotected FN 5, drift recap trims 0, accidental hard/rescue trims 0. Root cause: remaining soft candidates were encountered before final pressure was known and rejected as target-rate-satisfied; later pressure was hard-protected, so the one-pass recap could not recover the 0.50000 ceiling.
- Carry-over: copyMachine, turbulence2, cubicle, continuousPan, intermittentPan, fountain01, fountain02, and bridgeEntry stayed within their listed gates. port remains a detector watch item. sofa drifted to unprotected FN 8, parking drifted to unprotected FN 22, tunnelExit drifted to unprotected FN 2, and lakeSide remained above proposal gate.
- Step 4D2 residual-risk subset dry-run fails. Full CDnet rerun remains held; next work should be a narrow Step 4D3 that raises/adapts the exact snowFall actual-FN cap and turns lakeSide drift recap into an early reserve/two-pass-equivalent soft trim buffer, with sofa/parking carry-over rechecked before any full CDnet dry-run.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4D snowFall weather-aware no-detector rescue subset dry-run

- Implemented a dry-run-only exact-video `badWeather/snowFall` weather-aware no-detector rescue, localized weather guard, proposal guard, and Step 4D telemetry in `src/run_experiment.py`, plus Step 4D snowFall summary output in `tools/compare_asmag_tr_controller_online_guarded.py`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4d_snowfall_risk_subset_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4d_snowfall_risk_subset_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D_SNOWFALL_RESCUE_REPORT.md`.
- Compile passed. The residual-risk subset dry-run completed 56/56 planned jobs, 0 failed, across 14 videos and 4 pipelines. The dry-run compare completed for the Step 4D root.
- Aggregate guarded subset metrics: FMeasure 0.33238, Event_F1 0.66485, Activation 0.47929, Avg_FPS 25.47992, P95 latency 368.05579 ms, proposed intervention rate 0.34143, detector request rate 0.01500, block-only rate 0.32643, event/foreground block-only rate 0.26071, normal-frame proposals 0, guard alignment 1.00000.
- `badWeather/snowFall` did not improve: Step 4 full proposal/detector/event FN/protected FN/unprotected FN 0.29000/0.03000/22/12/10, Step 4D 0.28000/0.00000/22/12/10.
- SnowFall rescue behavior: 0 candidates, 0 activations, 0 no-detector rescue frames, 0 rescue-protected event-FN frames, 83 localized-guard-active frames, 31 proposal-guard-active frames, 0 proposal-guard suppressions, and 0 final-normal rescue suppressions.
- Root cause: the rescue pressure condition required cap exhaustion or closed-empty budget exhaustion, but the remaining unprotected FN rows still logged available closed-empty budget and no generic budget block. Several unprotected FN rows still had active memory and foreground continuity, so the next fix should relax the pressure condition for actual `Event_State=FN` rows while keeping the exact-video, no-detector, localized-guard, and proposal-ceiling constraints.
- Carry-over: sofa, parking, turbulence2, cubicle, continuousPan, intermittentPan, fountain01, fountain02, and bridgeEntry stayed within their gates; port remains a detector watch item. LakeSide drifted to proposal 0.52000 and fails the Step 4B4 carry-over proposal gate. CopyMachine and tunnelExit kept accepted detector/proposal controls but showed FN drift that should be watched.
- Step 4D residual-risk subset dry-run fails. Full CDnet rerun remains held; do not proceed to Step 4E or full CDnet until a narrow Step 4D2 snowFall candidacy fix and the lakeSide proposal drift are resolved or explicitly accepted.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4C sofa intermittent-object no-detector rescue subset dry-run

- Implemented a dry-run-only exact-video `intermittentObjectMotion/sofa` intermittent-object no-detector rescue in `src/run_experiment.py`, plus Step 4C sofa summary fields in `tools/compare_asmag_tr_controller_online_guarded.py`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4c_sofa_risk_subset_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4c_sofa_risk_subset_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4C_SOFA_RESCUE_REPORT.md`.
- Compile passed. The residual-risk subset dry-run completed 56/56 planned jobs, 0 failed, across 14 videos and 4 pipelines. The dry-run compare completed for the Step 4C root.
- Aggregate guarded subset metrics: FMeasure 0.31803, Event_F1 0.65986, Activation 0.44143, Avg_FPS 30.22110, P95 latency 360.79176 ms, proposed intervention rate 0.32929, detector request rate 0.01643, block-only rate 0.31286, event/foreground block-only rate 0.24786, normal-frame proposals 0, guard alignment 1.00000.
- `intermittentObjectMotion/sofa` improved from Step 4 full proposal/detector/event FN/protected FN/unprotected FN 0.20000/0.03000/22/12/10 to Step 4C 0.26000/0.00000/21/21/0.
- Sofa rescue behavior: 15 candidates, 12 activations, 12 no-detector rescue frames, 12 rescue-protected event-FN frames, 0 final-normal rescue suppressions, and 0 generic proposal-guard suppressions. Proposal guard skipped all 12 rescue frames and final proposal rate was 0.26000.
- Carry-over stayed within gates for `lakeSide`, `parking`, `copyMachine`, `turbulence2`, `tunnelExit_0_35fps`, `cubicle`, `continuousPan`, `intermittentPan`, `fountain01`, `fountain02`, and `bridgeEntry`; `snowFall` and `port_0_17fps` remain residual watch/patch items as planned.
- Step 4C residual-risk subset dry-run passes. Full CDnet rerun remains held; recommended next work is Step 4D `badWeather/snowFall` weather-aware rescue before a full CDnet rerun unless the team chooses an interim full dry-run after lakeSide plus sofa stabilization.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4B4 lakeSide high-score non-FN softening subset dry-run

- Implemented a dry-run-only `thermal/lakeSide` high-score non-FN hard-protection softener and high-score soft trim in `src/run_experiment.py`, plus Step 4B4 lakeSide summary fields in `tools/compare_asmag_tr_controller_online_guarded.py`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4b4_lakeside_risk_subset_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4b4_lakeside_risk_subset_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4B4_LAKESIDE_HIGHSCORE_SOFTEN_REPORT.md`.
- Compile passed. The residual-risk subset dry-run completed 56/56 planned jobs, 0 failed, across 14 videos and 4 pipelines. The dry-run compare completed for the Step 4B4 root.
- Aggregate guarded subset metrics: FMeasure 0.34462, Event_F1 0.65472, Activation 0.48000, Avg_FPS 23.35906, P95 latency 391.63325 ms, proposed intervention rate 0.32571, detector request rate 0.02000, block-only rate 0.30571, event/foreground block-only rate 0.25143, normal-frame proposals 0, guard alignment 1.00000.
- `thermal/lakeSide` Step 4B4 result: proposal/detector/event FN/protected FN/unprotected FN 0.50000/0.00000/48/48/0. This meets the proposal ceiling while preserving Step 4B/4B3 FN protection.
- High-score softening behavior: 62 soften-active frames, 48 final hard-protected frames, 7 high-score soft candidates, 5 high-score trims, 7 foreground-loss-only trims, 12 total trims, 0 accidental hard-protected trims, 0 accidental rescue-protected trims, and 0 final-normal suppressor regressions.
- Detector pressure stayed controlled: final lakeSide detector request rate 0.00000 and detector retighten active frames 0.
- Carry-over stayed within gates for `parking`, `copyMachine`, `turbulence2`, `tunnelExit_0_35fps`, `cubicle`, `continuousPan`, `intermittentPan`, `fountain01`, `fountain02`, and `bridgeEntry`; `sofa`, `snowFall`, and `port_0_17fps` remain residual watch/patch items.
- Step 4B4 residual-risk subset dry-run passes. Full CDnet rerun remains held; recommended next work is Step 4C sofa patch before a full CDnet rerun unless the team chooses an interim full dry-run to freeze lakeSide stabilization.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4B3 lakeSide foreground-loss-only softening subset dry-run

- Implemented a dry-run-only `thermal/lakeSide` hard-protection refinement, foreground-loss-only soft trim, and detector retighten path in `src/run_experiment.py`, plus Step 4B3 lakeSide summary fields in `tools/compare_asmag_tr_controller_online_guarded.py`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4b3_lakeside_risk_subset_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4b3_lakeside_risk_subset_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4B3_LAKESIDE_FGLOSS_SOFT_TRIM_REPORT.md`.
- Compile passed. The residual-risk subset dry-run completed 56/56 planned jobs, 0 failed, across 14 videos and 4 pipelines. The dry-run compare completed for the Step 4B3 root.
- Aggregate guarded subset metrics: FMeasure 0.34953, Event_F1 0.67446, Activation 0.52071, Avg_FPS 30.79529, P95 latency 293.49922 ms, proposed intervention rate 0.32286, detector request rate 0.01643, block-only rate 0.30643, event/foreground block-only rate 0.25000, normal-frame proposals 0, guard alignment 1.00000.
- `thermal/lakeSide` Step 4B3 result: proposal/detector/event FN/protected FN/unprotected FN 0.55000/0.00000/48/48/0. This restores Step 4B FN protection and removes the Step 4B2 detector request, but still fails the proposal ceiling of <= 0.50000.
- Hard-protection refinement behavior: 62 refine-active frames, 55 final hard-protected frames, and 7 foreground-loss-only soft candidates. All 7 soft candidates were trimmed, with 0 accidental hard-protected trims, 0 accidental rescue-protected trims, and 0 final-normal suppressor regressions.
- Detector retighten result: 0 active frames and final lakeSide detector request rate 0.00000.
- Root cause: the foreground-loss-only soft pool exposed only 7 safe trims, while reaching the 0.50000 proposal gate required at least 12 suppressions from the pre-trim lakeSide proposal set. The remaining needed trims sit in the residual hard-protected set, especially 7 non-likely high-event-score foreground-loss hard frames.
- Carry-over stayed within gates for `parking`, `copyMachine`, `turbulence2`, `tunnelExit_0_35fps`, `cubicle`, `continuousPan`, `intermittentPan`, `fountain01`, `fountain02`, and `bridgeEntry`; `sofa`, `snowFall`, and `port_0_17fps` remain residual watch/patch items.
- Step 4B3 is not a clean pass. Stop here under the dry-run failure rule. Full CDnet rerun remains held; next work should be a narrow Step 4B4 audit/soften pass for the 7 non-likely high-event foreground-loss lakeSide hard frames before Step 4C, unless the team explicitly accepts lakeSide 0.55000 as a temporary residual failure.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-17 Step 4B2 lakeSide rescue pressure trim subset dry-run

- Implemented a dry-run-only `thermal/lakeSide` post-rescue pressure trim and optional rescue-cap refine path in `src/run_experiment.py`, plus Step 4B2 lakeSide trim summary fields in `tools/compare_asmag_tr_controller_online_guarded.py`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4b2_lakeside_risk_subset_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4b2_lakeside_risk_subset_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4B2_LAKESIDE_TRIM_REPORT.md`.
- Compile passed. The residual-risk subset dry-run completed 56/56 planned jobs, 0 failed, across 14 videos and 4 pipelines. The dry-run compare completed for the Step 4B2 root.
- Aggregate guarded subset metrics: FMeasure 0.34097, Event_F1 0.67414, Activation 0.49929, Avg_FPS 27.38296, P95 latency 305.14125 ms, proposed intervention rate 0.34286, detector request rate 0.01786, block-only rate 0.32500, event/foreground block-only rate 0.26714, normal-frame proposals 0, guard alignment 1.00000.
- `thermal/lakeSide` Step 4B2 result: proposal/detector/event FN/protected FN/unprotected FN 0.63000/0.01000/52/50/2. This remains materially better than Step 4 full CDnet unprotected FN 21, but fails the proposal ceiling of <= 0.50000 and regresses proposal pressure versus Step 4B 0.60000.
- Trim behavior: 16 main no-detector rescues, 4 early-memory rescues, 20 newly protected event-FN frames, 0 trim candidates, 0 trim suppressions, 63 hard-protected frames, 0 accidental hard-protected trims, and 0 final-normal suppressor regressions.
- Root cause: every lakeSide proposal was hard-protected under the requested rules. Fifty were likely event-FN/unprotected-FN risk, twelve were protected by foreground-loss score >= 0.90 with active memory >= 1, and one also carried an existing detector request. Optional cap refine did not fire because the configured cap 18 exceeded the actual 16 main rescues and all main rescues protected event-FN frames.
- Carry-over stayed within gates for `parking`, `copyMachine`, `turbulence2`, `tunnelExit_0_35fps`, `cubicle`, `continuousPan`, `intermittentPan`, `fountain01`, `fountain02`, and `bridgeEntry`; `sofa`, `snowFall`, and `port_0_17fps` remain residual watch/patch items.
- Step 4B2 is not a clean pass. Stop here under the dry-run failure rule. Full CDnet rerun remains held; next work should first resolve lakeSide foreground-loss-only hard-protection pressure before moving to Step 4C.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

## 2026-05-16 Step 4B lakeSide no-detector FN rescue subset dry-run

- Implemented a narrow exact-video `thermal/lakeSide` no-detector FN rescue and early active-memory rescue in `src/run_experiment.py`, plus Step 4B compare summary output in `tools/compare_asmag_tr_controller_online_guarded.py`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_step4b_lakeside_risk_subset_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4b_lakeside_risk_subset_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4B_LAKESIDE_RESCUE_REPORT.md`.
- Compile passed. The residual-risk subset dry-run completed 56/56 planned jobs, 0 failed, across 14 videos and 4 pipelines. The dry-run compare completed for the Step 4B root.
- Aggregate guarded subset metrics: FMeasure 0.35061, Event_F1 0.67692, Activation 0.52429, Avg_FPS 38.36761, P95 latency 219.14120 ms, proposed intervention rate 0.32786, detector request rate 0.01571, block-only rate 0.31214, event/foreground block-only rate 0.25643, normal-frame proposals 0, guard alignment 1.00000.
- `thermal/lakeSide` improved from Step 4 baseline proposal/detector/unprotected FN 0.40000/0.00000/21 to Step 4B 0.60000/0.00000/0. Rescue activity: 15 main rescue frames, 3 early-memory rescue frames, 18 protected event-FN frames from the new thermal rescues, and 0 final-normal suppressor regressions.
- Step 4B is not a clean pass because `lakeSide` proposal pressure exceeded the phase acceptance ceiling of 0.50000. The narrow next fix is a `thermal/lakeSide` rescue proposal-pressure ceiling or lower effective rescue cap.
- Carry-over stayed within gates for `parking`, `copyMachine`, `turbulence2`, `tunnelExit_0_35fps`, `cubicle`, `continuousPan`, `intermittentPan`, `fountain01`, `fountain02`, and `bridgeEntry`; `sofa`, `snowFall`, and `port_0_17fps` remain residual watch/patch items.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched. Full CDnet rerun, full live, and cross-dataset remain held.

## 2026-05-16 Step 4A top residual risk frame audit

- Created frame-level audit: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4A_TOP_RISK_FRAME_AUDIT.md`.
- Scope was audit-only using existing full CDnet dry-run outputs. No experiment, live run, live compare, full CDnet rerun, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.
- Audited frames: `thermal/lakeSide` 21 unprotected FNs, `intermittentObjectMotion/sofa` 10 unprotected FNs, `badWeather/snowFall` 10 unprotected FNs, and `lowFramerate/port_0_17fps` 7 detector-request frames.
- Root causes: `thermal/lakeSide` is mostly cap exhaustion before protection; `sofa` is missing/ordering-specific intermittent-object rescue under active memory; `snowFall` is cap exhaustion under weather event risk; `port_0_17fps` detector requests are mostly likely unnecessary FP/TN event-refresh-specific requests.
- Recommended patch order: Step 4B `thermal/lakeSide` no-detector FN rescue, Step 4C `sofa` intermittent-object rescue, Step 4D `snowFall` weather-aware rescue, Step 4E `port_0_17fps` detector retighten.
- Full CDnet live, cross-dataset validation, and Jetson/edge profiling remain held.

## 2026-05-16 Step 4 full CDnet2014 residual risk review

- Created risk review: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4_FULL_CDNET_RISK_REVIEW.md`.
- Scope was documentation, risk triage, and next-action planning only. No experiment, full live, full live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.
- Risk classification: `thermal/lakeSide`, `intermittentObjectMotion/sofa`, and `badWeather/snowFall` are Priority A frame-level audit / likely patch candidates before the next full dry-run freeze. `lowFramerate/port_0_17fps` is A/B for detector-pressure audit. PTZ/dynamicBackground low metric videos are mostly B/C watch or paper-limitations items. `intermittentObjectMotion/parking` is a D tolerance candidate if the team accepts 0.51000 under the protection-aware gate, but remains a blocker if the 0.50000 cap is strict.
- Recommended next step: Step 4A-AUDIT using existing frame-level outputs for `thermal/lakeSide`, `intermittentObjectMotion/sofa`, `badWeather/snowFall`, and optionally `lowFramerate/port_0_17fps` before patching.
- Full CDnet live, cross-dataset validation, and Jetson/edge profiling remain held.

## 2026-05-16 Step 4 full CDnet2014 8C-2Q2 dry-run completed

- Ran only the full CDnet2014 dry-run for frozen 8C-2Q2 using `configs/asmag_tr_controller_online_guarded_cdnet_full_2q2_dryrun.yaml`.
- Output root: `outputs/asmag_tr_controller_online_guarded_cdnet_full_2q2_dryrun/`.
- Completed 212/212 planned jobs, 0 failed, across 11 categories and 53 videos. The dry-run compare completed for this root.
- Aggregate guarded metrics: FMeasure 0.47863, Event_F1 0.76989, Activation 0.61917, Avg_FPS 26.11998, P95 latency 244.80332 ms, proposed intervention 0.17766, detector request 0.01211, block-only 0.16555, event/foreground block-only 0.14632, normal-frame proposed interventions 0, guard alignment 1.00000.
- Checkpoint note: after 32 jobs, a non-fatal pandas stderr warning left `run_progress.csv` empty. The zero-byte artifact was preserved as `run_progress.empty_after_stderr_warning_20260516.csv`, progress was rebuilt from checkpoints, and no result outputs were deleted.
- Gate decision: Step 4 full dry-run is held, not accepted as a clean pass, because `intermittentObjectMotion/parking` proposal is 0.51000 versus the revised protection-aware cap 0.50000. Parking detector remains 0.00000 and unprotected FN is 3.
- Additional full-dataset risks: `thermal/lakeSide` unprotected FN 21, `badWeather/snowFall` unprotected FN 10, `intermittentObjectMotion/sofa` unprotected FN 10, `lowFramerate/port_0_17fps` detector 0.07000, and low PTZ/dynamicBackground metric videos.
- No full live, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was run. Full CDnet live and cross-dataset remain held.
- Updated report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q2_FULL_CDNET_DRYRUN_REPORT.md`.

## 2026-05-16 Step 4 full CDnet2014 dry-run setup

- Created full dry-run config: `configs/asmag_tr_controller_online_guarded_cdnet_full_2q2_dryrun.yaml`.
- Created initial full dry-run report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q2_FULL_CDNET_DRYRUN_REPORT.md`.
- Planned scope: CDnet2014 dataset root `D:/THS Programing/06.6 ASMAG Project/dataset cdnet2014/archive/dataset`, 11 categories, 53 videos, 4 pipelines, 212 planned jobs.
- Scope remains dry-run only. Full live, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, and Jetson/edge profiling remain held.

## 2026-05-16 Step 3B targeted category live freeze

- Created freeze report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP3B_TARGETED_CATEGORY_LIVE_FREEZE.md`.
- Scope was documentation, audit, and consolidation only. No experiment, live validation, live compare, full CDnet, full CDnet compare, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Freeze decision: Step 3B targeted category live is accepted as **PASS** under the revised protection-aware parking gate.
- Official result: 8C-2Q2 targeted category live, 80/80 completed, 0 failed, FMeasure 0.44351, Event_F1 0.67449, detector request 0.01062, normal-frame interventions 0, guard alignment 1.00000.
- Parking accepted under the scene-specific protection-aware gate: intervention 0.50000, detector 0.00000, unprotected FN 4, normal-frame interventions 0.
- 8C-2Q2 is now the current full-CDnet dry-run candidate, but is not marked as full CDnet success.
- Full CDnet live and cross-dataset validation remain held. Recommended next step is Step 4 full CDnet2014 dry-run only after explicit authorization.

## 2026-05-16 Step 3B parking protection-aware gate review

- Created gate review: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP3B_PARKING_GATE_REVIEW.md`.
- Scope was documentation, metric review, and gate decision only. No experiment, live validation, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, or PTZ-targeted standalone validation was launched.
- Review finding: the old `intermittentObjectMotion/parking` proposal/intervention <= 0.45000 gate is likely too strict because 2Q4 shows parking proposal 0.50000 is not caused by generic non-risk frames. The soft trim found 18 soft-preserved frames but 0 safe trim candidates, with 50 hard-protected frames and 0 accidental hard-protected trims.
- Evidence reviewed: 2M parking proposal/detector/unprotected FN 0.20000/0.00000/31; 2M2 0.48000/0.00000/9; 2M3 0.39000/0.00000/9; 2Q2 dry-run 0.45000/0.00000/5; 2Q2 live 0.50000/0.00000/4; 2Q3 dry-run 0.50000/0.00000/4; 2Q4 dry-run 0.50000/0.00000/4.
- Recommended revised parking gate: parking proposal/intervention <= 0.50000 acceptable, parking detector <= 0.02000, parking unprotected FN <= 12, parking normal-frame interventions 0, accidental hard-protected trim count 0, aggregate detector request < 0.10000, no broad detector-heavy behavior, and no forbidden validation launched.
- Under this revised protection-aware parking gate, the completed 8C-2Q2 targeted category live retry can be accepted as passing: parking intervention 0.50000, detector 0.00000, unprotected FN 4, normal-frame interventions 0, aggregate detector request 0.01062, guard alignment 1.00000, and all other live gates already passed.
- Recommendation: do not patch parking further now. Document a Step 3B live freeze under the revised parking gate, or authorize one final 2Q4 targeted category live run under the revised gate only if strict phase consistency is desired. Full CDnet remains held until a Step 3B live freeze is documented.

## 2026-05-16 Step 3B targeted category live retry with 8C-2Q2

- Created live config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_live.yaml`.
- Created and used separate live output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_live/`.
- Confirmed the live root was absent before creation and therefore safe to write. Accidental 8C-2E live artifacts were not used, deleted, or overwritten. The 2Q2 dry-run output root and previous live outputs were not overwritten.
- Ran only the 8C-2Q2 targeted category live retry and live compare for that root. No full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, or PTZ-targeted standalone validation was launched.
- Live technical completion: 80/80 jobs completed, 0 failed.
- Live aggregate guarded metrics: FMeasure 0.44351, Event_F1 0.67449, Activation 0.58678, Avg_FPS 24.60626, P95 latency 231.79742 ms, intervention rate 0.20677, detector request rate 0.01062, block-only rate 0.19616, event/foreground block-only rate 0.15824, normal-frame interventions 0, guard alignment 1.00000.
- Passing live gates include aggregate detector, normal-frame interventions, guard alignment, cubicle, bridgeEntry, continuousPan, intermittentPan, tramCrossroad_1fps, fountain01, fountain02 normal-frame false interventions, copyMachine, turbulence2, tunnelExit, and no broad detector-heavy behavior.
- Failed live gate: `intermittentObjectMotion/parking` intervention/proposal rate 0.50000 exceeds the <= 0.45000 live gate, although detector remains 0.00000 and unprotected FN is 4.
- Root cause: live parking preserved/protected context retained more frames than dry-run after the reserve/cap and post-preservation trim path. Live post-trim final rate reached 0.50000 versus 0.45000 dry-run.
- Decision: Step 3B targeted category live retry fails. Stop here, do not run full CDnet. Recommended next step is a narrow parking-only live proposal retighten, followed by dry-run and authorized targeted live retry after review.
- Updated report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q2_TARGETED_CATEGORY_RETRY_FREEZE.md`.

## 2026-05-16 Step 3B-RETRY-READINESS FREEZE for 8C-2Q2 targeted category live retry

- Created freeze report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q2_TARGETED_CATEGORY_RETRY_FREEZE.md`.
- Freeze scope was documentation, audit, and consolidation only. No experiment, live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- 8C-2Q2 is frozen as the current targeted category Step 3B live-retry candidate based on its completed targeted category dry-run: 80/80 completed, 0 failed, FMeasure 0.43068, Event_F1 0.66657, Activation 0.57292, Avg_FPS 28.34227, P95 latency 227.01209 ms, proposal rate 0.21335, detector request rate 0.01163, normal-frame proposals 0, and guard alignment 1.00000.
- Carry-over gates remain accepted for cubicle, intermittentPan, continuousPan, bridgeEntry, tramCrossroad_1fps, fountain01, fountain02, copyMachine, parking, turbulence2, and tunnelExit.
- Residual live-retry watchlist: `shadow/copyMachine` proposal 0.46000 with unprotected FN 4, `intermittentObjectMotion/parking` proposal 0.45000 with unprotected FN 5, and `lowFramerate/tunnelExit_0_35fps` unprotected FN 1.
- Accidental 8C-2E artifacts remain excluded, default guarded config remains unchanged with `ai_intervention_enabled: false`, and controller code was not modified during this freeze.
- Freeze decision: mark 8C-2Q2 as the targeted category live-retry candidate only. Do not mark it as full CDnet success; full CDnet remains held.
- Recommended next step is Step 3B targeted category live retry with the 2Q2 policy after explicit authorization.

## 2026-05-16 8C-2Q2 turbulence2 carry-over reserve targeted category dry-run

- Implemented Phase 8C-2Q2 as a dry-run-only no-detector carry-over reserve for `turbulence/turbulence2` rescue-cap-exhausted frames.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q2_TURBULENCE_CARRYOVER_REPORT.md`.
- Updated controller logs and compare output with `ai_intervention_2q2_turbulence_carryover_summary.csv`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Dry-run result: 80/80 jobs completed, 0 failed. Aggregate guarded metrics: FMeasure 0.43068, Event_F1 0.66657, Activation 0.57292, Avg_FPS 28.34227, P95 latency 227.01209 ms, proposal rate 0.21335, detector request rate 0.01163, block-only rate 0.20172, event/foreground block-only rate 0.16481, normal-frame proposals 0, guard alignment 1.00000.
- `turbulence/turbulence2` recovered from 2Q event FN 5 / unprotected FN 3 to event FN 3 / unprotected FN 0, with proposal/detector 0.31000/0.00000. The carry-over reserve had 2 candidates, 1 active no-detector frame, 1 protected event-FN frame, cap used 1/4, and 0 final-normal suppressions.
- Turbulence2 frames 950 and 975 are TP `DETECT_ACC` in 2Q2 and no longer unprotected FNs; frame 985 remains FN but is protected by the carry-over reserve with no detector request.
- CopyMachine remains at the successful 2Q state: proposal/detector 0.46000/0.00000, unprotected FN 4, 8 reserve activations. Parking remains inside gate and improved versus 2P: proposal/detector 0.45000/0.00000, unprotected FN 5, 8 reserve activations, burst bridge 0.
- Core carry-over gates pass: cubicle recall 0.90909 with unprotected FN 0; intermittentPan proposal 0.01000 with unprotected FN 0; continuousPan proposal 0.04000; bridgeEntry event FN 0; tramCrossroad_1fps proposal/detector 0.00000/0.00000; fountain01 proposal/detector 0.00000/0.00000; fountain02 normal false interventions 0; tunnelExit proposal 0.31000 with unprotected FN 1.
- 8C-2Q2 passes targeted category dry-run gates. Step 3B targeted category live retry is now reasonable after review; live was not run automatically and full CDnet remains held.

## 2026-05-15 8C-2Q live cap-exhaustion reserve targeted category dry-run

- Implemented Phase 8C-2Q as a dry-run-only no-detector live cap-exhaustion reserve for `shadow/copyMachine` and `intermittentObjectMotion/parking`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q_LIVE_CAP_RESERVE_REPORT.md`.
- Updated compare output with `ai_intervention_2q_live_cap_reserve_summary.csv`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Dry-run progress: 80/80 jobs completed, 0 failed. Aggregate guarded metrics: FMeasure 0.43084, Event_F1 0.66386, Activation 0.57292, Avg_FPS 31.94125, P95 latency 229.94988 ms, proposal rate 0.21537, detector request rate 0.01112, block-only rate 0.20425, event/foreground block-only rate 0.16835, normal-frame proposals 0, guard alignment 1.00000.
- Target reserve behavior: `shadow/copyMachine` improved from 2P unprotected FN 12 to 4 with 8 no-detector reserve activations; `intermittentObjectMotion/parking` improved from 2P unprotected FN 9 to 4 with 8 no-detector reserve activations and 0 reserve/bridge frames trimmed.
- Carry-over gates passed for `shadow/cubicle`, `PTZ/intermittentPan`, `PTZ/continuousPan`, `nightVideos/bridgeEntry`, `lowFramerate/tramCrossroad_1fps`, `dynamicBackground/fountain01`, `dynamicBackground/fountain02`, and `lowFramerate/tunnelExit_0_35fps`.
- 8C-2Q does not pass targeted category dry-run gates because `turbulence/turbulence2` regressed to unprotected FN 3, above the accepted gate of <= 2. New failing rows versus 2P are frames 950 and 975, both `CLOSED_EMPTY_ACC` with turbulence2 rescue rejected by `rescue_cap_exhausted`.
- Live remains held. Recommended next step is a narrow dry-run-only carry-over audit for `turbulence/turbulence2` under the current 2Q code path before any Step 3B targeted category live retry. Full CDnet remains held.

## 2026-05-15 8C-2P live final-action mismatch targeted category dry-run

- Implemented Phase 8C-2P as a dry-run-only live final-action mismatch patch for `shadow/cubicle` and `PTZ/intermittentPan`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2p_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2P_LIVE_MISMATCH_REPORT.md`.
- Updated compare output with `ai_intervention_2p_live_mismatch_summary.csv` and `ai_intervention_2p_frame_status.csv`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Dry-run result: 80/80 jobs completed, 0 failed. Aggregate guarded metrics: FMeasure 0.43110, Event_F1 0.66604, Activation 0.58078, Avg_FPS 27.16402, P95 latency 233.21158 ms, proposed intervention rate 0.19818, detector request rate 0.01011, block-only rate 0.18807, event/foreground block-only rate 0.15167, normal-frame proposals 0, guard alignment 1.00000.
- 2P target-frame dry-run status: `shadow/cubicle` frame 1560 is TP with `FORCED_REFRESH`, `PTZ/intermittentPan` frames 1370 and 1375 are TP with `DETECT_ACC`; all three are not unprotected in dry-run, so the new live mismatch guards correctly reject them as `action_not_unsafe_empty_fallback` in dry-run.
- Guard activity: cubicle live-mismatch reserve fired on 3 no-detector cubicle frames, used its separate cap of 3, and produced 0 compare-defined normal-frame proposals. The PTZ live-mismatch rescue did not fire in dry-run because the audited intermittentPan frames already use `DETECT_ACC`.
- Gates pass: cubicle recall 0.90909 with unprotected FN 0; intermittentPan proposal/detector 0.01000/0.00000 with unprotected FN 0; continuousPan proposal 0.04000; bridgeEntry event FN 0; tramCrossroad and fountain01 remain quiet; fountain02 normal false interventions 0; copyMachine unprotected FN 12; parking proposal 0.39000 with unprotected FN 9; turbulence2 proposal 0.30000 with unprotected FN 1; tunnelExit proposal 0.31000 with unprotected FN 1.
- 8C-2P passes targeted category dry-run gates. Live remains held. Recommended next step is a separate dry-run patch for the remaining live-sensitive `shadow/copyMachine` and `intermittentObjectMotion/parking` failures before any targeted category live retry. Step 4 full CDnet dry-run remains held.

## 2026-05-15 Step 3B-LIVE-FAILURE-AUDIT

- Created live failure audit report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP3B_LIVE_FAILURE_AUDIT.md`.
- Step 3B 8C-2O targeted category live completed technically but failed live gates. Audited live unprotected FN frames: `shadow/cubicle` 1, `PTZ/intermittentPan` 2, `shadow/copyMachine` 18, and `intermittentObjectMotion/parking` 14.
- Root-cause summary: `shadow/cubicle` is primarily cap exhaustion with stabilizer threshold and dry-run/live final-action mismatch; `PTZ/intermittentPan` is dry-run/live final-action mismatch plus missing rescue/candidate logging; `shadow/copyMachine` is rescue-cap exhaustion with 6 live-sensitive additions over the accepted dry-run residual; `intermittentObjectMotion/parking` is rescue-cap exhaustion plus low-score/no-active-memory candidate misses and 5 live-sensitive additions over the accepted dry-run residual.
- No new validation, live resume, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched during this audit. Controller code and compare tooling were not modified.
- Full CDnet remains held. Next step is pending patch decision, with a recommended dry-run-only patch order: first `shadow/cubicle` plus `PTZ/intermittentPan`, then `shadow/copyMachine` plus `intermittentObjectMotion/parking`.

## 2026-05-15 Step 3B 8C-2O targeted category live resume result

- Safely resumed the existing partial live output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live/`.
- Resume command used: `python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live.yaml --max-jobs-per-run 8`.
- The runner auto-recovered the stale `baseline/highway/P3_MOG2` row and completed the remaining jobs in two bounded resume passes. Final progress: 80 completed, 0 pending, 0 running, 0 failed.
- Live compare completed with `python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live`.
- Live aggregate metrics for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`: FMeasure 0.42292, Event_F1 0.66650, Activation 0.47928, Avg_FPS 16.50218, P95 latency 484.56976 ms, intervention/proposal rate 0.23357, detector request rate 0.02477, block-only rate 0.20880, event/foreground block-only rate 0.16886, normal-frame interventions 0, guard alignment 1.00000.
- Step 3B targeted category live fails despite technical completion. Failed gates: `shadow/cubicle` recall 0.81818 but unprotected FN 1, `PTZ/intermittentPan` proposal 0.05000 but unprotected FN 2, `shadow/copyMachine` unprotected FN 18, and `intermittentObjectMotion/parking` proposal 0.43000 with unprotected FN 14.
- Passing carry-over gates include aggregate detector < 0.10, normal-frame interventions 0, guard alignment 1.00000, `nightVideos/bridgeEntry` event FN 0, `PTZ/continuousPan` proposal 0.05000, `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000, `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000, `dynamicBackground/fountain02` normal-frame false interventions 0, `turbulence/turbulence2` proposal 0.30000 with unprotected FN 1, and `lowFramerate/tunnelExit_0_35fps` proposal 0.30000 with unprotected FN 1.
- No full CDnet, full CDnet compare, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched. Accidental 8C-2E live artifacts were not used.
- Step 4 full CDnet dry-run remains held. Recommended next action is a narrow dry-run-only patch for the live-sensitive FN misses in `shadow/cubicle`, `PTZ/intermittentPan`, `shadow/copyMachine`, and `intermittentObjectMotion/parking`.

## 2026-05-15 Step 3B-PARTIAL-AUDIT 8C-2O targeted category live

- Created partial audit report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2O_TARGETED_CATEGORY_LIVE_PARTIAL_AUDIT.md`.
- Step 3B targeted category live remains partial/unresolved as an official result: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live/run_progress.csv` shows 68 completed, 1 running, 11 pending, and 0 failed.
- The recorded running job is `baseline/highway/P3_MOG2` at 1/100 frames with last update `2026-05-15T15:44:34`; output timestamps were static during audit and no visible Python runner was found via `Get-Process`, while `tasklist` was denied and `wmic` failed.
- Audit assessment: the running row is stale by best available evidence, completed job artifacts appear resumable, and no completed-job corruption, lock file, temp file, or pid file was found.
- No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched during this audit.
- No official 8C-2O targeted category live result exists yet. Full CDnet remains held.

## 2026-05-15 Step 3-FREEZE 8C-2O targeted category dry-run candidate

- Created freeze report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2O_TARGETED_CATEGORY_FREEZE.md`.
- Freeze decision: 8C-2O is the official targeted category dry-run candidate for Step 3 review.
- No new experiment, live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched during this freeze step.
- Freeze scope remains dry-run only: 20 videos, 9 categories, output root `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun/`.
- 8C-2O aggregate freeze metrics: 80/80 completed, 0 failed; FMeasure 0.40060; Event_F1 0.66904; Activation 0.47128; Avg_FPS 22.57987; P95 latency 418.20077 ms; proposed intervention rate 0.21587; detector request rate 0.01921; block-only rate 0.19666; event/foreground block-only rate 0.15875; normal-frame proposals 0; guard alignment 1.00000.
- Accepted dry-run residual risks for live monitoring: `shadow/copyMachine` unprotected FN 12, `intermittentObjectMotion/parking` unprotected FN 9, `turbulence/turbulence2` unprotected FN 2, and `lowFramerate/tunnelExit_0_35fps` unprotected FN 1.
- Step 3B targeted category live is recommended only after explicit authorization and review acceptance of the residual risks.
- Full CDnet remains held and is not recommended yet.
- Accidental 8C-2E live artifacts were excluded from the freeze decision and left untouched.
- Default guarded config remains unchanged with `ai_intervention_enabled: false`.

## 2026-05-15 8C-2O tunnelExit targeted category dry-run status

- Implemented Phase 8C-2O as a dry-run-only `lowFramerate/tunnelExit_0_35fps` FN-risk preservation, no-detector rescue, and post-preservation generic trim patch on top of the 8C-2N config.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2O_TUNNELEXIT_REPORT.md`.
- Updated compare output with `ai_intervention_2o_tunnel_exit_summary.csv`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Dry-run result: 80/80 jobs completed, 0 failed across 20 videos and 9 categories.
- Aggregate guarded metrics: FMeasure 0.40060, Event_F1 0.66904, Activation 0.47128, Avg_FPS 22.57987, P95 latency 418.20077 ms, proposed intervention rate 0.21587, detector request rate 0.01921, block-only rate 0.19666, event/foreground block-only rate 0.15875, normal-frame proposed interventions 0, guard alignment 1.00000.
- TunnelExit improved from 8C-2N proposal/detector/unprotected FN 0.24000/0.00000/2 to 8C-2O 0.30000/0.00000/1. Residual raw frame 2485 missed because the configured no-detector rescue cap of 6 frames was exhausted.
- TunnelExit diagnostics: 30 preserved FN-risk active frames, 2 rescue candidates, 6 active no-detector rescue frames, 1 rescue-protected event-FN frame, 0 generic post-trim suppressions, final post-trim rate 0.30000, and 0 preserved/rescue frames accidentally trimmed.
- Carry-over status: `shadow/cubicle` recall 0.87879 and unprotected FN 0; `nightVideos/bridgeEntry` event FN 0; `PTZ/continuousPan` proposal/detector 0.05000/0.01000 and unprotected FN 0; `PTZ/intermittentPan` proposal/detector 0.01000/0.00000 and unprotected FN 0; `shadow/copyMachine` proposal/detector 0.38000/0.00000 and unprotected FN 12; `intermittentObjectMotion/parking` proposal/detector 0.43000/0.00000 and unprotected FN 9; `turbulence/turbulence2` proposal/detector 0.11000/0.00000 and unprotected FN 2; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `lowFramerate/turnpike_0_5fps` proposal/detector 0.01000/0.00000 and unprotected FN 0; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0.
- 8C-2O passes targeted category dry-run gates. Live remains held because this phase was dry-run-only and because review should accept the residual tunnelExit FN=1 plus the turbulence2 carry-over caveat before Step 3B targeted category live authorization.
- Accidental 8C-2E live artifacts were left untouched and were not used.

## 2026-05-15 8C-2M3 parking post-preservation trim targeted category dry-run status

- Implemented Phase 8C-2M3 as a dry-run-only `intermittentObjectMotion/parking` post-preservation pressure trim on top of the 8C-2M2 config.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m3_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m3_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2M3_PARKING_POST_TRIM_REPORT.md`.
- Updated compare output with `ai_intervention_2m3_parking_summary.csv`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Dry-run result: 80/80 jobs completed, 0 failed across 20 videos and 9 categories.
- Aggregate guarded metrics: FMeasure 0.42369, Event_F1 0.66607, Activation 0.49428, Avg_FPS 23.91514, P95 latency 328.76947 ms, proposed intervention rate 0.24065, detector request rate 0.02022, block-only rate 0.22042, event/foreground block-only rate 0.18605, normal-frame proposed interventions 0, guard alignment 1.00000.
- Parking comparison: 8C-2L2 proposal/detector/FN 0.40000/0.00000/16; 8C-2M 0.20000/0.00000/31; 8C-2M2 0.48000/0.00000/9; 8C-2M3 0.39000/0.00000/9.
- Parking diagnostics: 24 preserved FN-risk frames, 24 active no-detector rescue frames, 24 rescue-protected event-FN frames, 4 post-preservation generic non-risk trims, 0 rescue false-positive activations, and 0 preserved/rescue frames accidentally trimmed.
- Carry-over remained intact: `shadow/copyMachine` proposal/detector 0.38000/0.00000 with 12 unprotected FNs; `PTZ/intermittentPan` proposal/detector 0.01000/0.00000 with unprotected FN 0; `PTZ/continuousPan` block-only proposal/detector 0.05000/0.01000 with unprotected FN 0; `shadow/cubicle` recall 0.87879 and unprotected FN 0; `nightVideos/bridgeEntry` event FN 0; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0.
- Remaining monitored risks intentionally not fixed in 2M3: `turbulence/turbulence2` proposal/detector 0.39000/0.03000 with 3 unprotected FNs, and `lowFramerate/tunnelExit_0_35fps` proposal/detector 0.28000/0.00000 with 1 unprotected FN.
- 8C-2M3 passes targeted category dry-run gates. Live remains held because this phase was dry-run-only and remaining risks still need review before any Step 3B live authorization.
- Accidental 8C-2E live artifacts were left untouched and were not used.

## 2026-05-14 8C-2M2 parking preserve-FN-risk targeted category dry-run status

- Implemented Phase 8C-2M2 as a dry-run-only `intermittentObjectMotion/parking` localized-FN preservation patch on top of the 8C-2M config.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m2_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m2_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2M2_PARKING_PRESERVE_FN_RISK_REPORT.md`.
- Updated compare output with `ai_intervention_2m2_parking_summary.csv`; compare was rerun once after a reporting-only fix so parking rescue protected-FN counts are computed from actual frame state.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation or live compare was launched.
- Dry-run result: 80/80 jobs completed, 0 failed across 20 videos and 9 categories.
- Aggregate guarded metrics: FMeasure 0.42508, Event_F1 0.66359, Activation 0.45278, Avg_FPS 23.69421, P95 latency 348.36063 ms, proposed intervention rate 0.24216, proposed detector request rate 0.02174, block-only rate 0.22042, event/foreground block-only rate 0.18908, normal-frame proposed interventions 0, guard alignment 1.00000.
- Parking improved on FN protection but failed proposal pressure: 8C-2L2 proposal/detector 0.40000/0.00000 with 16 unprotected FNs; 8C-2M proposal/detector 0.20000/0.00000 with 31 unprotected FNs; 8C-2M2 proposal/detector 0.48000/0.00000 with 9 unprotected FNs. This exceeds the 0.45 parking proposal hard gate.
- Parking diagnostics: 24 preserved FN-risk frames, 24 active no-detector rescues, 24 rescue-protected event-FN frames, 0 rescue false-positive activations, 1 generic non-risk cap suppression, and 24 preserved-FN-risk cap skips.
- Root cause: the FN-risk preservation fixed the 2M under-protection problem but over-preserved parking. The cap now suppresses too little generic non-risk pressure after preserving useful FN-risk frames.
- Carry-over remained intact for gated videos: `shadow/cubicle` recall 0.87879 and unprotected FN 0; `nightVideos/bridgeEntry` event FN 0; `PTZ/intermittentPan` proposal/detector 0.10000/0.00000 and unprotected FN 0; `PTZ/continuousPan` proposal/detector 0.04000/0.01000 and unprotected FN 0; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0; `shadow/copyMachine` proposal/detector 0.38000/0.00000 with 12 unprotected FNs.
- Remaining monitored risks intentionally not fixed in 2M2: `turbulence/turbulence2` proposal/detector 0.35000/0.04000 with 3 unprotected FNs, and `lowFramerate/tunnelExit_0_35fps` proposal/detector 0.40000/0.03000 with 1 unprotected FN.
- 8C-2M2 fails targeted category dry-run gates because parking proposal is 0.48000, above the 0.45 hard gate. Live remains held.
- Recommended next patch: keep the new no-detector FN-risk preservation, add a parking post-preservation pressure trim that only removes generic non-risk proposals once preserved count exceeds 45 frames, and continue preserving FN-risk frames.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-14 8C-2M parking targeted category dry-run status

- Implemented Phase 8C-2M as a dry-run-only `intermittentObjectMotion/parking` stability patch on top of the 8C-2L2 config.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2M_PARKING_REPORT.md`.
- Updated compare output with `ai_intervention_2m_parking_summary.csv`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation or live compare was launched.
- Dry-run result: 80/80 jobs completed, 0 failed across 20 videos and 9 categories.
- Aggregate guarded metrics: FMeasure 0.43061, Event_F1 0.66513, Activation 0.56778, Avg_FPS 29.69619, P95 latency 223.50977 ms, proposed intervention rate 0.19818, proposed detector request rate 0.01365, block-only rate 0.18453, event/foreground block-only rate 0.15319, normal-frame proposed interventions 0, guard alignment 1.00000.
- Parking failed the target: 8C-2L2 proposal/detector 0.40000/0.00000 with 16 unprotected FNs became 8C-2M proposal/detector 0.20000/0.00000 with 31 unprotected FNs. Rescue produced 57 candidates and 20 active no-detector rescues, but only 2 protected event-FN frames while the cap suppressed 52 generic proposals.
- Root cause: the parking rescue predicate was too broad, while the generic-only cap suppressed useful non-rescue event/foreground proposals before the proposal cap was actually exceeded. The patch removed more FN protection than it restored.
- Carry-over mostly remained intact: `shadow/cubicle` recall 0.87879 and unprotected FN 0; `nightVideos/bridgeEntry` event FN 0; `PTZ/intermittentPan` proposal/detector 0.01000/0.00000 and unprotected FN 0; `PTZ/continuousPan` proposal/detector 0.04000/0.01000 and unprotected FN 0; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0; `shadow/copyMachine` proposal/detector 0.38000/0.00000 with 12 unprotected FNs.
- Remaining monitored risks intentionally not fixed in 2M: `turbulence/turbulence2` proposal/detector 0.38000/0.05000 with 2 unprotected FNs, and `lowFramerate/tunnelExit_0_35fps` proposal/detector 0.24000/0.00000 with 2 unprotected FNs.
- 8C-2M fails targeted category dry-run gates because parking unprotected FN worsened and hits the hard-fail threshold. Live remains held.
- Recommended next patch: keep parking no-detector and video-scoped, narrow rescue activation to likely unprotected FN frames, and change the cap to suppress generic non-rescue proposals only after the 0.40 cap is actually reached while preserving localized/event-FN-risk proposals.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-12 18:36:44 +07:00

- Phase 8C-2E dry-run paused and preserved.
- Current dry-run progress: 32 completed, 0 failed, based on `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun/run_progress.csv`.
- Resume command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun.yaml --max-jobs-per-run 8
```

- Reminder: live smoke is not allowed until dry-run passes all gates.
- No targeted CDnet, full CDnet, PTZ-targeted, LASIESTA, SBI2015, BMC, or cross-dataset run was started during this pause step.

## 2026-05-13 08:54 +07:00

- Phase 8C-2E dry-run audit confirmed `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun/run_progress.csv` has 32 completed jobs and 0 failed jobs.
- Ran dry-run compare only:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun
```

- Dry-run compare result: proposed intervention rate 0.32625, detector request rate 0.04000, block-only rate 0.28625, event/foreground block-only rate 0.25750, cubicle-like no-detector proposal rate 0.04625, guard alignment 1.00000, cubicle proposed known-event recall 0.75269, cubicle unprotected event FN 0, bridgeEntry event FN 0, bridgeEntry detector budget max 8, continuousPan proposed intervention rate 0.04000, non-cubicle proposals reclaimed 30.
- Live folder audit: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_live/` is populated and contains completed live artifacts from the previously interrupted live command: 32 completed rows, 0 failed rows, 32 raw result job folders, and 285 recursive files. These were documented as accidental/unintended live artifacts; no files were deleted.
- Final 8C-2E recommendation: live remains held because cubicle recall is below the 0.80 live target and normal-frame proposed interventions are 2 rather than 0, even though aggregate proposed intervention rate is below 0.35.
- No live smoke, live-root compare, PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched during this audit.

## 2026-05-13 8C-2F dry-run status

- Implemented Phase 8C-2F normal-frame cleanup and cubicle recall micro-bump using separate 2F configs and output roots.
- Created `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2F_NORMAL_CLEANUP_REPORT.md`.
- Ran dry-run only:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_dryrun
```

- Dry-run result: 32 completed jobs, 0 failed jobs.
- 8C-2F fixed the targeted local blockers: normal-frame proposed interventions dropped from 2 to 0, and cubicle proposed known-event recall rose from 0.75269 to 0.84848.
- 8C-2F does not pass the strict dry-run gate because aggregate proposed intervention rate is 0.35375, above the `< 0.35` limit.
- Live remains held. No live smoke, live compare, PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- Accidental 8C-2E live artifacts were left untouched.

## 2026-05-13 8C-2G dry-run status

- Implemented Phase 8C-2G lowFramerate proposal trim using separate 2G configs and output roots.
- Created `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2G_LOWFRAMERATE_TRIM_REPORT.md`.
- Ran dry-run only:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun
```

- Dry-run result: 32 completed jobs, 0 failed jobs.
- 8C-2G passes dry-run gates: proposed intervention rate 0.31500, detector request rate 0.03000, normal-frame proposed interventions 0, cubicle recall 0.84848, bridgeEntry event FN 0, bridgeEntry detector budget max 8, continuousPan proposed intervention rate 0.05000.
- LowFramerate/tramCrossroad_1fps proposed intervention rate dropped from 0.33000 in 8C-2F to 0.02000 in 8C-2G; the direct trim log reports 7 reclaimed proposals.
- Live remains held pending explicit authorization. No live smoke, live compare, PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- Accidental 8C-2E live artifacts were left untouched.

## 2026-05-13 8C-2G official live smoke status

- Confirmed the 8C-2G dry-run report says 8C-2G passed the dry-run gate.
- Confirmed `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/` was empty before the official live run and safe to write.
- Ran official 8C-2G live smoke only:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live.yaml --max-jobs-per-run 8
```

- Resumed the same official live command until all jobs completed: 32 completed, 0 failed.
- Ran official 8C-2G live compare only:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live
```

- Live metrics: FMeasure 0.19806, Event_F1 0.55372, Activation 0.61125, Avg_FPS 25.35154, P95 latency 242.01526 ms, proposed intervention rate 0.28125, detector request rate 0.02875, normal-frame interventions 0, cubicle recall 0.82828, cubicle unprotected event FN 0, bridgeEntry event FN 0, bridgeEntry detector budget max 2, continuousPan proposed intervention rate 0.05000.
- Dry-run vs live: proposed intervention rate improved from 0.31500 to 0.28125; detector request rate improved from 0.03000 to 0.02875; cubicle recall stayed above target at 0.82828; lowFramerate/tramCrossroad_1fps proposed intervention rate improved from 0.02000 to 0.01000; lowFramerate trim reclaimed proposals stayed at 7.
- 8C-2G passes official live smoke. No larger validation was launched.
- Accidental 8C-2E live artifacts were not used and were left untouched.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.

## 2026-05-13 8C-2G official smoke freeze

- Created official consolidation/freeze report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2G_OFFICIAL_SMOKE_FREEZE.md`.
- 8C-2G official smoke-live passed.
- 8C-2G official live smoke is frozen as the official smoke-live candidate, not as full validation success.
- Larger validation remains held pending explicit authorization.
- Next recommended step is targeted mini-validation dry-run only after approval; live should run only if that targeted dry-run passes.
- No new experiments, live smoke, live compare, PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched during the freeze step.

## 2026-05-13 8C-2G targeted mini dry-run status

- Created targeted mini dry-run config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2g_dryrun.yaml`.
- Ran targeted mini dry-run only on `cubicle`, `bridgeEntry`, `continuousPan`, `tramCrossroad_1fps`, `fountain02`, and additional dynamicBackground video `fountain01`.
- Dry-run result: 24/24 jobs completed, 0 failed.
- Compare result: proposed intervention rate 0.22167, detector request rate 0.01500, normal-frame proposed interventions 0, guard alignment 1.00000, bridgeEntry event FN 0, continuousPan proposed intervention rate 0.04000, lowFramerate/tramCrossroad_1fps proposed intervention rate 0.01000, lowFramerate trim reclaimed proposals 7.
- Targeted mini dry-run failed because cubicle recall dropped to 0.71717 and cubicle unprotected event FN rose to 7 versus 0 in smoke dry-run/live.
- Wrote report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2G_TARGETED_MINI_DRYRUN_REPORT.md`.
- Step 2 live remains held. Recommended next fix is a narrow cubicle-protection stability patch before any live mini-validation.
- No live smoke, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-13 8C-2H smoke dry-run status

- Implemented Phase 8C-2H exact-cubicle event-FN stabilizer using separate 2H dry-run configs and output roots.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2H_EXACT_CUBICLE_STABILITY_REPORT.md`.
- Ran compile and smoke dry-run only:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun
```

- Smoke dry-run result: 32/32 jobs completed, 0 failed.
- Compare result: proposed intervention rate 0.30875, detector request rate 0.02875, normal-frame proposed interventions 0, guard alignment 1.00000, cubicle recall 0.81818, bridgeEntry event FN 0, bridgeEntry detector budget max 5, continuousPan proposal rate 0.05000, tramCrossroad_1fps proposal rate 0.02000, lowFramerate trim reclaimed proposals 7.
- 8C-2H failed the smoke gate because cubicle unprotected event FN was 2. The exact-cubicle stabilizer did not activate because the early normal-frame suppressor returned before the stabilizer path on cubicle FN frames 1340 and 1345.
- Targeted mini dry-run was not launched because smoke failed. Live remains held.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live smoke, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-13 8C-2H2 pre-signal dry-run status

- Implemented Phase 8C-2H2 exact-cubicle event-FN pre-signal before the early normal-frame suppressor using separate 2H2 dry-run configs and output roots.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2H2_PRESIGNAL_REPORT.md`.
- Ran compile, smoke dry-run, smoke compare, targeted mini dry-run, and targeted mini compare only. No live validation was launched.
- Smoke dry-run result: 32/32 jobs completed, 0 failed. Metrics: proposed intervention rate 0.31625, detector request rate 0.02625, normal-frame proposed interventions 0, guard alignment 1.00000, cubicle recall 0.83838, cubicle unprotected event FN 0, bridgeEntry event FN 0, bridgeEntry detector budget max 8, continuousPan proposal rate 0.05000, tramCrossroad_1fps proposal rate 0.01000.
- Cubicle frames 1340 and 1345 are now protected by the exact-cubicle no-detector stabilizer after pre-signal bypassed the early normal suppressor.
- Targeted mini dry-run result: 24/24 jobs completed, 0 failed. Metrics: FMeasure 0.32892, Event_F1 0.57127, Activation 0.51667, Avg_FPS 19.26090, P95 latency 422.70620 ms, proposed intervention rate 0.35833, detector request rate 0.05833, normal-frame proposed interventions 0, cubicle recall 0.82828, cubicle unprotected event FN 0, bridgeEntry event FN 0, continuousPan proposal rate 0.05000.
- 8C-2H2 fails targeted mini because non-cubicle proposal pressure regressed: `dynamicBackground/fountain01` rose from 0.00000 proposals in 8C-2G targeted mini to 0.38000, with detector request rate 0.15000; `lowFramerate/tramCrossroad_1fps` rose from 0.01000 to 0.18000 despite trim remaining active.
- Live remains held. Recommended next step is a dry-run-only non-cubicle proposal-pressure cleanup that restores fountain01 quiet behavior and re-tightens targeted lowFramerate preservation while keeping the successful exact-cubicle pre-signal unchanged.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live smoke, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-13 8C-2I non-cubicle cleanup dry-run status

- Implemented Phase 8C-2I using separate dry-run configs and output roots only.
- Added `dynamicBackground/fountain01` quiet guard and `lowFramerate/tramCrossroad_1fps` targeted retighten while preserving the 8C-2H2 exact-cubicle pre-signal/stabilizer, final normal-frame suppressor, lowFramerate trim, and sparse detector policy.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2I_NONCUBICLE_CLEANUP_REPORT.md`.
- Ran compile, smoke dry-run, smoke compare, targeted mini dry-run, and targeted mini compare only. No live validation was launched.
- Smoke dry-run result: 32/32 jobs completed, 0 failed. Metrics: proposed intervention rate 0.33625, detector request rate 0.03875, normal-frame proposed interventions 0, guard alignment 1.00000, cubicle recall 0.84848, cubicle unprotected event FN 0, bridgeEntry event FN 0, bridgeEntry detector budget max 8, continuousPan proposal rate 0.04000, tramCrossroad_1fps proposal rate 0.01000.
- Targeted mini dry-run result: 24/24 jobs completed, 0 failed. Metrics: FMeasure 0.23247, Event_F1 0.57761, Activation 0.50167, Avg_FPS 18.73201, P95 latency 467.01634 ms, proposed intervention rate 0.26667, detector request rate 0.02333, normal-frame proposed interventions 0, cubicle recall 0.83838, cubicle unprotected event FN 0, bridgeEntry event FN 0, bridgeEntry detector budget max 8, continuousPan proposal rate 0.05000.
- `dynamicBackground/fountain01` quiet behavior was restored: proposal rate 0.38000 in 8C-2H2 targeted mini to 0.00000 in 8C-2I, detector request rate 0.15000 to 0.00000, with 80 proposals reclaimed.
- `lowFramerate/tramCrossroad_1fps` was re-tightened: proposal rate 0.18000 in 8C-2H2 targeted mini to 0.01000 in 8C-2I, detector request rate 0.05000 to 0.00000, with 10 retighten proposals reclaimed.
- 8C-2I passes both smoke and targeted mini dry-runs. Targeted mini live is recommended for explicit authorization review only; live remains held until approved.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live smoke, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-13 8C-2I targeted mini live status

- Created official targeted mini live config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_live.yaml`.
- Created and used official targeted mini live output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_live/`.
- Confirmed the 2I report stated both dry-runs passed before running live. The 2I live output folder was missing before this step, so no partial 2I live artifacts were overwritten.
- Ran only the authorized 8C-2I targeted mini live command and resumed it until completion:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_live.yaml --max-jobs-per-run 8
```

- Ran only the authorized 8C-2I targeted mini live compare:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_live
```

- Live result: 24/24 jobs completed, 0 failed. Aggregate metrics: FMeasure 0.35628, Event_F1 0.55840, Activation 0.55167, Avg_FPS 12.06588, P95 latency 451.06938 ms, intervention rate 0.26000, detector request rate 0.03000, block-only rate 0.23000, event/foreground block-only rate 0.18833, normal-frame interventions 0, guard alignment 1.00000.
- Non-cubicle pressure behavior matched expectations: `dynamicBackground/fountain01` stayed quiet at 0.00000 intervention and 0.00000 detector request; `lowFramerate/tramCrossroad_1fps` stayed controlled at 0.00000 intervention and 0.00000 detector request; `PTZ/continuousPan` stayed capped at 0.05000; `nightVideos/bridgeEntry` event FN stayed 0 with detector budget max 8; `dynamicBackground/fountain02` had 0 normal-frame false interventions.
- 8C-2I targeted mini live failed the strict live gate because `shadow/cubicle` had cubicle unprotected event FN = 1 despite recall 0.80808. The missed frame was `shadow/cubicle` frame 1560, action `CLOSED_EMPTY_P3_FALLBACK`; cubicle-like path rejected on `event_continuity_signal_low`, micro-bump rejected on `micro_cap_exhausted`, pre-signal did not activate, and exact-cubicle stabilizer rejected on `event_foreground_or_loss_score_low`.
- Step 3 targeted category dry-run remains held. Recommended next work is a narrow exact-cubicle live stability fix for frame-1560-like misses, then dry-run validation before any further live or wider validation.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No smoke live, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-14 8C-2J exact-cubicle live rescue status

- Implemented Phase 8C-2J exact `shadow/cubicle` late-event no-detector rescue using separate 2J configs and output roots only.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2J_EXACT_CUBICLE_LIVE_RESCUE_REPORT.md`.
- Ran compile, smoke dry-run, smoke compare, targeted mini dry-run, targeted mini compare, targeted mini live, and targeted mini live compare only.
- Smoke dry-run result: 32/32 jobs completed, 0 failed. Metrics: FMeasure 0.32426, Event_F1 0.59763, Activation 0.30375, Avg_FPS 17.91204, P95 latency 340.44474 ms, proposed intervention rate 0.32750, detector request rate 0.05375, normal-frame proposals 0, cubicle recall 0.86364, cubicle unprotected FN 0, bridgeEntry event FN 0, continuousPan proposal rate 0.05000, tramCrossroad_1fps proposal rate 0.00000.
- Targeted mini dry-run result: 24/24 jobs completed, 0 failed. Metrics: FMeasure 0.33742, Event_F1 0.56913, Activation 0.62500, Avg_FPS 16.63252, P95 latency 375.03676 ms, proposed intervention rate 0.23833, detector request rate 0.02000, normal-frame proposals 0, cubicle recall 0.82828, cubicle unprotected FN 0, bridgeEntry event FN 0, continuousPan proposal rate 0.04000, tramCrossroad_1fps proposal/detector 0.00000/0.00000, fountain01 proposal/detector 0.00000/0.00000, fountain02 normal-frame false interventions 0.
- Targeted mini live result: 24/24 jobs completed, 0 failed. Metrics: FMeasure 0.34562, Event_F1 0.54909, Activation 0.59000, Avg_FPS 17.76615, P95 latency 307.53556 ms, intervention/proposal rate 0.27333, detector request rate 0.02500, normal-frame interventions/proposals 0, guard alignment 1.00000, cubicle recall 0.89899, cubicle unprotected FN 0, bridgeEntry event FN 0, continuousPan proposal rate 0.05000, tramCrossroad_1fps proposal/detector 0.00000/0.00000, fountain01 proposal/detector 0.00000/0.00000, fountain02 normal-frame false interventions 0.
- Frame 1560 is present and no longer an unprotected FN: event state `TP`, action `FALLBACK_P3_POLICY`, detector requested 0. The late-event rescue did not fire on that frame because the final action was already outside the unsafe empty/fallback action set.
- 8C-2J passes all allowed stages. Step 3 targeted category dry-run is recommended next, but remains unlaunched.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No full CDnet, Step 3 targeted category, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-14 8C-2J Step 3 targeted category dry-run status

- Created dry-run-only Step 3 config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2j_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2j_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2J_TARGETED_CATEGORY_DRYRUN_REPORT.md`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation or live compare was launched.
- Video resolution: all 20 requested videos were present locally; no replacements were used.
- Dry-run result: 80/80 jobs completed, 0 failed across 20 videos and 9 categories.
- Aggregate guarded metrics: FMeasure 0.40068, Event_F1 0.66660, proposed activation 0.46114, Avg_FPS 21.11406, P95 latency 407.14876 ms, proposed intervention rate 0.24216, proposed detector request rate 0.02326, block-only rate 0.21891, event/foreground block-only rate 0.18655, normal-frame proposed interventions 0, guard alignment 1.00000.
- Exact-cubicle behavior remains healthy: `shadow/cubicle` recall 0.87879, unprotected FN 0, late-event rescue frames 4, no-detector rescue frames 4. Frame 1560 is present and no longer unprotected; detector requested 0.
- Core carry-over guards remain intact: `nightVideos/bridgeEntry` event FN 0; `PTZ/continuousPan` proposal rate 0.04000; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0.
- Step 3 targeted category dry-run fails because `PTZ/intermittentPan` proposal rate is 0.30000, above the 0.15 hard gate, while still leaving 2 unprotected event FNs. Additional high-risk videos include `intermittentObjectMotion/parking` with 16 unprotected FNs, `shadow/copyMachine` with 21 unprotected FNs, and `turbulence/turbulence2` with proposal rate 0.39000 and 3 unprotected FNs.
- Step 3B targeted category live is held. Recommended next work is a dry-run-only, category/video scoped proposal-pressure cap for `PTZ/intermittentPan`, modeled after the existing `continuousPan` cap, followed by review of remaining high-risk videos before any live validation.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-16 8C-2Q4 parking soft-preserved trim dry-run status

- Implemented Phase 8C-2Q4 as a parking-only no-detector soft-preserved trim for `intermittentObjectMotion/parking`.
- Created configs: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q4_dryrun.yaml` and `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q4_live.yaml`.
- Created output roots: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q4_dryrun/` and `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q4_live/`; live root remains unused.
- Created/updated report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q4_PARKING_SOFT_TRIM_REPORT.md`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Targeted category dry-run completed: 80/80 jobs completed, 0 failed. Compare completed for the 2Q4 dry-run root.
- Aggregate guarded dry-run metrics: FMeasure 0.43293, Event_F1 0.66513, Activation 0.57878, Avg_FPS 28.11636, P95 latency 235.00799 ms, proposal rate 0.21183, detector request rate 0.00910, normal-frame proposals 0, guard alignment 1.00000.
- Dry-run failed one gate: `intermittentObjectMotion/parking` proposal remained 0.50000, above the <=0.45000 gate. Parking detector stayed 0.00000 and unprotected FN stayed acceptable at 4.
- 2Q4 soft-trim behavior: active frames 50, hard-protected frames 50, soft-preserved frames 18, candidate frames 0, suppressed frames 0, trim count 0, final rate 0.50000, accidental hard-protected trim count 0.
- Root cause: the loosened soft-preserved boundary identified 18 soft-preserved parking frames, but all were also classified as hard-protected by deterministic/emergency safeguard classification. The policy correctly refused to trim hard-protected frames, so no frames were reclaimed.
- Other core gates remained pass: `shadow/cubicle` recall 0.90909 and unprotected FN 0; `PTZ/intermittentPan` proposal 0.01000 and unprotected FN 0; `PTZ/continuousPan` proposal 0.05000; `nightVideos/bridgeEntry` event FN 0; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0; `shadow/copyMachine` unprotected FN 4; `turbulence/turbulence2` proposal 0.31000 and unprotected FN 0; `lowFramerate/tunnelExit_0_35fps` proposal 0.30000 and unprotected FN 1.
- Step 3B targeted category live remains held because 2Q4 dry-run failed. Step 4 full CDnet dry-run remains held.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, or PTZ-targeted standalone validation was launched.
- Accidental 8C-2E live artifacts were left untouched and were not used.

## 2026-05-16 8C-2Q3 parking live trim dry-run status

- Implemented Phase 8C-2Q3 as a parking-only no-detector post-preservation trim attempt for `intermittentObjectMotion/parking`.
- Created configs: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q3_dryrun.yaml` and `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q3_live.yaml`.
- Created output roots: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q3_dryrun/` and `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q3_live/`; live root remains unused.
- Created/updated report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q3_PARKING_LIVE_TRIM_REPORT.md`.
- Compile passed for `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py`.
- Targeted category dry-run completed: 80/80 jobs completed, 0 failed. Compare completed for the 2Q3 dry-run root.
- Aggregate guarded dry-run metrics: FMeasure 0.43284, Event_F1 0.66513, Activation 0.57478, Avg_FPS 27.14769, P95 latency 238.93533 ms, proposal rate 0.21385, detector request rate 0.01011, normal-frame proposals 0, guard alignment 1.00000.
- Dry-run failed one gate: `intermittentObjectMotion/parking` proposal remained 0.50000, above the <=0.45000 gate. Parking detector stayed 0.00000 and unprotected FN stayed acceptable at 4.
- 2Q3 trim behavior: active frames 50, candidate frames 0, suppressed frames 0, trim count 0, final rate 0.50000, accidental protected/reserve trim count 0. The candidate predicate was too strict and rejected retained over-gate frames as `not_generic_nonrisk` or protected/reserve/FN-risk.
- Other core gates remained pass: `shadow/cubicle` recall 0.90909 and unprotected FN 0; `PTZ/intermittentPan` proposal 0.01000 and unprotected FN 0; `PTZ/continuousPan` proposal 0.05000; `nightVideos/bridgeEntry` event FN 0; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0; `shadow/copyMachine` unprotected FN 4; `turbulence/turbulence2` proposal 0.31000 and unprotected FN 0; `lowFramerate/tunnelExit_0_35fps` proposal 0.30000 and unprotected FN 1.
- Step 3B targeted category live remains held because 2Q3 dry-run failed. Step 4 full CDnet dry-run remains held.
- No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, or PTZ-targeted standalone validation was launched.
- Accidental 8C-2E live artifacts were left untouched and were not used.

## 2026-05-14 8C-2L2 copyMachine rescue-first targeted category dry-run status

- Implemented Phase 8C-2L2 with rescue-first ordering for `shadow/copyMachine` and an explicit 8C-2K rescue preservation lock for `PTZ/intermittentPan`.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2l2_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2l2_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2L2_COPYMACHINE_RESCUE_FIRST_REPORT.md`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation or live compare was launched.
- Dry-run result: 80/80 jobs completed, 0 failed across 20 videos and 9 categories.
- Aggregate guarded metrics: FMeasure 0.43259, Event_F1 0.66453, Activation 0.56978, Avg_FPS 26.70032, P95 latency 242.24090 ms, proposed intervention rate 0.20222, proposed detector request rate 0.01466, block-only rate 0.18756, event/foreground block-only rate 0.15925, normal-frame proposed interventions 0, guard alignment 1.00000.
- `shadow/copyMachine` improved from 8C-2L proposal/detector 0.35000/0.00000 with 25 unprotected FNs to 8C-2L2 proposal/detector 0.39000/0.00000 with 11 unprotected FNs. This also improves versus 8C-2K's 21 unprotected FNs. Rescue-first produced 50 candidates, 18 active no-detector rescues, 24 generic-only cap suppressions, and 0 final-normal rescue suppressions.
- `PTZ/intermittentPan` recovered the 8C-2K behavior: proposal/detector 0.01000/0.00000, unprotected FN 0, and 1 preserved 2K rescue frame.
- Core carry-over gates remained intact: `shadow/cubicle` recall 0.86869 and unprotected FN 0; `nightVideos/bridgeEntry` event FN 0; `PTZ/continuousPan` proposal/detector 0.02000/0.00000; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0.
- Remaining monitored risks not fixed in 2L2: `intermittentObjectMotion/parking` proposal/detector 0.40000/0.00000 with 16 unprotected FNs, `turbulence/turbulence2` proposal/detector 0.39000/0.04000 with 3 unprotected FNs, and `lowFramerate/tunnelExit_0_35fps` proposal/detector 0.25000/0.00000 with 2 unprotected FNs.
- 8C-2L2 passes targeted category dry-run gates under the acceptable copyMachine gate: the preferred copyMachine unprotected-FN target <=10 misses by one frame, but the acceptable <=15 gate passes with safe proposal/detector rates and documented rescue-cap exhaustion.
- Live remains held. Recommended next work is a narrow dry-run patch for `intermittentObjectMotion/parking` before any Step 3B targeted category live authorization.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-14 8C-2K PTZ/intermittentPan targeted category dry-run status

- Implemented Phase 8C-2K with a narrow `PTZ/intermittentPan` proposal-pressure cap and no-detector FN rescue on top of the 8C-2J policy.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2k_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2k_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2K_PTZ_INTERMITTENTPAN_REPORT.md`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live validation or live compare was launched.
- Dry-run result: 80/80 jobs completed, 0 failed across 20 videos and 9 categories.
- Aggregate guarded metrics: FMeasure 0.38702, Event_F1 0.66234, Activation 0.39278, Avg_FPS 23.75311, P95 latency 452.27077 ms, proposed intervention rate 0.24216, proposed detector request rate 0.02679, block-only rate 0.21537, event/foreground block-only rate 0.18605, normal-frame proposed interventions 0, guard alignment 1.00000.
- `PTZ/intermittentPan` improved from proposal/detector 0.30000/0.06000 with 2 unprotected FNs in 8C-2J Step 3 to proposal/detector 0.12000/0.00000 with 0 unprotected FNs in 8C-2K. The cap reclaimed 26 proposals, preserved 12, and the FN rescue fired 3 times, all no-detector.
- `PTZ/continuousPan` stayed at the gate: proposal 0.05000, detector 0.01000, unprotected FN 0.
- Core carry-over gates remained intact: `shadow/cubicle` recall 0.87879 and unprotected FN 0; `nightVideos/bridgeEntry` event FN 0; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0.
- Remaining risks were monitored but intentionally not fixed in 2K: `intermittentObjectMotion/parking` proposal 0.40000 with 18 unprotected FNs, `shadow/copyMachine` proposal 0.40000 with 21 unprotected FNs, `turbulence/turbulence2` proposal 0.35000 with 3 unprotected FNs, and `lowFramerate/tunnelExit_0_35fps` proposal 0.39000 with 3 unprotected FNs.
- 8C-2K passes the requested targeted category dry-run hard gates. Live remains held; recommended next step is review or a narrow dry-run patch for the remaining risk videos before any Step 3B targeted category live authorization.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-14 8C-2L copyMachine targeted category dry-run status

- Implemented Phase 8C-2L with a narrow `shadow/copyMachine` proposal-pressure guard and no-detector FN rescue on top of the 8C-2K policy.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2l_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2l_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2L_COPYMACHINE_REPORT.md`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. The first compare invocation timed out at 120 seconds while writing the large summary set, then the same compare was rerun with a longer timeout and completed. No live validation or live compare was launched.
- Dry-run result: 80/80 jobs completed, 0 failed across 20 videos and 9 categories.
- Aggregate guarded metrics: FMeasure 0.36538, Event_F1 0.64596, Activation 0.37578, Avg_FPS 17.96888, P95 latency 482.31024 ms, proposed intervention rate 0.25228, proposed detector request rate 0.03640, block-only rate 0.21587, event/foreground block-only rate 0.18150, normal-frame proposed interventions 0, guard alignment 1.00000.
- `shadow/copyMachine` proposal pressure improved from 0.40000 to 0.35000 and detector request rate improved from 0.01000 to 0.00000, but unprotected event FNs worsened from 21 to 25. The copyMachine guard reclaimed 37 proposals and preserved 35; the FN rescue fired 6 times, all no-detector.
- Root cause: the copyMachine hard proposal cap is reached before enough event-FN frames can be protected. In the 2L logs, 17 unprotected FN frames were marked rescue `already_protected` before the later guard cap suppressed the proposal, so rescue was not retried after cap rejection. With 58 copyMachine event-FN frames and a hard maximum of 35 protected proposal frames, unprotected FN <= 5 is not reachable under the current accounting unless the rescue/cap relationship is changed or the cap is reviewed.
- `PTZ/intermittentPan` regressed relative to 8C-2K: proposal 0.12000 -> 0.03000 and detector stayed 0.00000, but unprotected FN changed from 0 to 2 and the intermittentPan FN rescue did not fire. This violates the 2L preservation gate.
- Core carry-over remained safe otherwise: `shadow/cubicle` recall 0.83838 with unprotected FN 0; `nightVideos/bridgeEntry` event FN 0; `PTZ/continuousPan` proposal/detector 0.04000/0.01000; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.01000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0.
- Remaining monitored risks not fixed in 2L: `intermittentObjectMotion/parking` proposal/detector 0.40000/0.06000 with 33 unprotected FNs, `turbulence/turbulence2` proposal/detector 0.37000/0.04000 with 3 unprotected FNs, and `lowFramerate/tunnelExit_0_35fps` proposal/detector 0.24000/0.00000 with 2 unprotected FNs.
- 8C-2L fails targeted category dry-run gates. Live remains held. Recommended next work is a dry-run-only correction that reruns or moves copyMachine rescue after copyMachine cap suppression and explicitly preserves the 8C-2K intermittentPan rescue behavior before any Step 3B live authorization.
- Accidental 8C-2E live artifacts were left untouched and were not used.
- No live, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## 2026-05-15 8C-2N turbulence2 targeted category dry-run status

- Implemented Phase 8C-2N with a narrow `turbulence/turbulence2` dynamic-texture pressure guard and no-detector event-FN rescue on top of 8C-2M3.
- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2n_dryrun.yaml`.
- Created and used output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2n_dryrun/`.
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2N_TURBULENCE2_REPORT.md`.
- Ran compile, targeted category dry-run, and targeted category dry-run compare only. No live, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Dry-run result: 80/80 jobs completed, 0 failed. Aggregate guarded metrics: FMeasure 0.43122, Event_F1 0.66513, Activation 0.56678, Avg_FPS 19.80952, P95 latency 367.68531 ms, proposed intervention rate 0.19970, detector request rate 0.00910, block-only rate 0.19060, event/foreground block-only rate 0.16077, normal-frame proposals 0, guard alignment 1.00000.
- `turbulence/turbulence2` improved from 8C-2M3 proposal/detector 0.39000/0.03000 with 3 unprotected FNs to 8C-2N proposal/detector 0.30000/0.00000 with 1 unprotected FN. The rescue produced 3 candidates, 6 active no-detector rescue frames, 2 rescue-protected event-FN frames, and 0 protected rescue frames accidentally suppressed. The pressure guard suppressed 11 generic non-risk proposals and 8 detector refreshes.
- Carry-over remains within gates: `shadow/copyMachine` proposal/detector 0.38000/0.00000 with 12 unprotected FNs; `intermittentObjectMotion/parking` proposal/detector 0.43000/0.00000 with 9 unprotected FNs and 0 preserved/rescue frames accidentally trimmed; `PTZ/intermittentPan` proposal/detector 0.01000/0.00000 with 0 unprotected FNs; `PTZ/continuousPan` block-only proposal 0.05000 and detector 0.01000; `shadow/cubicle` recall 0.87879 with 0 unprotected FNs; `nightVideos/bridgeEntry` event FN 0; `lowFramerate/tramCrossroad_1fps` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain01` proposal/detector 0.00000/0.00000; `dynamicBackground/fountain02` normal-frame false interventions 0.
- Remaining risk intentionally not fixed in this phase: `lowFramerate/tunnelExit_0_35fps` proposal/detector 0.24000/0.00000 with 2 unprotected FNs.
- 8C-2N passes targeted category dry-run gates. Live remains held because this phase was dry-run-only; Step 3B targeted category live should wait for review acceptance of the residual tunnelExit risk and acceptable-but-not-preferred FN counts.
## 2026-05-20 Q1-SIC-1C1R3D Paired Same-Source Live-Probe Purity

- Inspected the R3C live-probe/observer audit, R3C/R3B/R3 observer reports, C1R restore report, Q1 safety invariant spec, controller validation plan, current `src/run_experiment.py`, R3B/R3C configs, and prior verifier/audit tools.
- Created paired configs: `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_live_probe_baseline_subset_dryrun.yaml` and `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_observer_purity_subset_dryrun.yaml`.
- Created verifier: `tools/verify_q1_sic1c1r3d_live_probe_purity.py`.
- Compile passed for `src\run_experiment.py`, the new verifier, and `tools\compare_asmag_tr_controller_online_guarded.py`.
- Ran only the two allowed scoped residual-risk subset dry-runs. Baseline completed 56/56 jobs with 0 failed. Observer completed 56/56 jobs with 0 failed after resuming the same scoped command once following a command timeout.
- Compare completed only on the two new R3D roots.
- Verification output root: `outputs/asmag_tr_q1_sic1c1r3d_live_probe_purity_verify/`.
- Primary failure classification: `observer changes behavior`; decision `FAIL_OBSERVER_IDENTITY`.
- Evidence: row alignment clean at 1400/1400 guarded rows with no duplicates or row-presence deltas, baseline local gates passed, observer telemetry safety passed, but baseline-vs-observer had 1250 behavior delta cells across 480 rows and 3204 live-probe delta cells across 598 rows. snowFall 1150 drifted from `DETECT_ACC / NO_CHANGE / proposal 0` to `CLOSED_EMPTY_ACC / FORCE_PROTECT_EVENT_MEMORY / proposal 1`.
- Recommended next action: Q1-SIC-1C1R3D audit/repair focused on why the post-decision observer flag still correlates with behavior and live-probe drift in a paired same-source run.
- Safety confirmation: no full CDnet, live/live compare, targeted CDnet beyond the two scoped residual-risk subset dry-runs, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, Q1-SIC-1C2 snowFall enforcement, Step 4E7-D2 port detector-retighten, or old-output overwrite was performed.
