# ASMAG-TR Q1-SIC-1C Integration/Base Audit

Date: 2026-05-19

## Scope and Safety Confirmation

This phase was audit-only. It diagnosed why Q1-SIC-1B passed pre-run verification but failed the runtime dry-run.

No experiments, dry-runs, live runs, live compares, targeted CDnet, full CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling were launched. No controller behavior, `src/run_experiment.py`, compare behavior, configs, existing outputs, or frozen CDnet2014 v1.6 outputs were modified.

New writes were limited to:

- `tools/audit_q1_sic1c_integration_base.py`
- `outputs/asmag_tr_q1_sic1c_integration_base_audit/`
- this report
- `docs/DAILY_STATUS.md`

## Q1-SIC-1B Status Recap

Q1-SIC-1B compiled, passed its pre-run proxy verifier, completed the scoped residual-risk subset dry-run with 56/56 jobs and 0 failed jobs, and compare completed only on the new Q1-SIC-1B output root. Normal-frame safety held: max `q1_sic_would_touch_normal_frame=0` and max `q1_sic_gt_signal_used_for_decision=0`.

The phase still failed because:

- `badWeather/snowFall` frame 1150 remained unprotected.
- Runtime Q1-SIC telemetry stayed `NO_CHANGE`.
- New proxy telemetry stayed default on frame 1150.
- `intermittentObjectMotion/parking` regressed from Q1-SIC-1/Step 4D6 behavior.
- `shadow/copyMachine` produced unexpected unprotected FN rows.
- `lowFramerate/port_0_17fps` frames 1350/1355 lost `WATCH_ONLY_PORT_RETIGHTEN` telemetry.

## Files, Configs, and Outputs Inspected

Docs read included the Q1 safety invariant spec, Q1-SIC-0 replay report, Q1-SIC-1 final arbitration report, Q1-SIC-1A audit, Q1-SIC-1B report, daily status, and guarded validation plan.

Code and configs inspected read-only:

- `src/run_experiment.py`
- `tools/verify_q1_sic1_shadow_arbitration.py`
- `tools/verify_q1_sic1b_runtime_proxy.py`
- `tools/audit_q1_sic1a_snowfall_mismatch.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun.yaml`

Output roots inspected read-only:

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1b_runtime_proxy_verify/`
- `outputs/asmag_tr_q1_sic1a_snowfall_mismatch_audit/`
- `outputs/asmag_tr_q1_sic1_shadow_verify/`
- `outputs/asmag_tr_q1_sic0_invariant_replay/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun/`

Generated audit CSVs:

- `q1_sic1c_snowfall_1150_integration_audit.csv`
- `q1_sic1c_snowfall_context_diff_sic1_vs_sic1b.csv`
- `q1_sic1c_parking_diff_sic1_vs_sic1b.csv`
- `q1_sic1c_copyMachine_diff_sic1_vs_sic1b.csv`
- `q1_sic1c_port_watch_diff_sic1_vs_sic1b.csv`
- `q1_sic1c_step4d6_vs_sic1b_parking_diff.csv`
- `q1_sic1c_config_diff_summary.csv`
- `q1_sic1c_telemetry_persistence_summary.csv`
- `q1_sic1c_missing_columns_summary.csv`
- `q1_sic1c_failure_classification.csv`

The only commands run were:

```powershell
python -m py_compile tools\audit_q1_sic1c_integration_base.py
python tools\audit_q1_sic1c_integration_base.py --sic1-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun --sic1b-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun --sic1b-verify-root outputs\asmag_tr_q1_sic1b_runtime_proxy_verify --sic1a-root outputs\asmag_tr_q1_sic1a_snowfall_mismatch_audit --step4d6-root outputs\asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun --out outputs\asmag_tr_q1_sic1c_integration_base_audit
```

## Config Diff Summary

Raw YAML differences:

| Key | Q1-SIC-1 | Q1-SIC-1B | Classification |
|---|---|---|---|
| `base_config` | Step 4D6 config | Q1-SIC-1 config | raw wrapper base changed |
| `experiment_name` | Q1-SIC-1 name | Q1-SIC-1B name | harmless output-root change |
| `edge_profile.name` | Q1-SIC-1 profile | Q1-SIC-1B profile | harmless output-root change |
| `q1_sic_event_risk_empty_detect_proxy_enabled` | missing | true | intended Q1-SIC-1B addition |
| `q1_sic_forbid_gt_decision_signals` | missing | true | intended Q1-SIC-1B addition |

Source inspection shows `load_config_with_base(...)` resolves `base_config` recursively. The effective recursive config diff did not expose missing dataset, pipeline, parking, copyMachine, carry-over, or event-safety flags; it showed only the expected Q1-SIC-1B proxy additions plus harmless experiment/profile name changes.

Conclusion: this is not proven to be a simple YAML omission. The runtime behavior still failed to preserve the Step 4D6/Q1-SIC-1 trajectory, so the safer classification is trajectory preservation failure rather than a blind config patch target.

## snowFall 1150 Integration Audit

| Check | Q1-SIC-1 | Q1-SIC-1B | Verifier | Classification |
|---|---:|---:|---:|---|
| `q1_sic_final_arbitration_enabled` | 1 | 1 |  | runtime flag enabled |
| `q1_sic_arbitration_label` | `NO_CHANGE` | `NO_CHANGE` |  | runtime remained `NO_CHANGE` |
| `q1_sic_event_risk_empty_detect_proxy` | NA | 0 | 1 | proxy verifier selected; runtime proxy default |
| `q1_sic_runtime_detector_pressure_proxy` | NA | 0 |  | runtime default |
| `q1_sic_runtime_detector_empty_proxy` | NA | 0 |  | runtime default |
| `q1_sic_runtime_proposal_absent_proxy` | NA | 0 |  | runtime default |
| `q1_sic_runtime_proxy_inputs` | NA | blank |  | runtime input trace did not persist |
| `q1_sic_empty_detect_proxy_reject_reason` | NA | blank |  | no reject reason persisted |
| pre-run verifier selected 1150 |  |  | 1 | verifier/runtime mismatch |

The Q1-SIC-1B config text enabled the proxy, and the runtime row recorded `q1_sic_final_arbitration_enabled=1`. However, frame 1150 also had blank `q1_sic_pre_action`, blank `q1_sic_post_action`, blank protection labels, blank proxy inputs, and no reject reason. That pattern looks like the Q1-SIC arbitration block did not execute or did not persist for that detector-action row, not like the proxy predicate rejected the row.

## snowFall Context Q1-SIC-1 vs Q1-SIC-1B

| Frame | State | Q1-SIC-1 action/protection | Q1-SIC-1B action/protection | Q1-SIC-1B label/proxy |
|---:|---|---|---|---|
| 1120 | FN | `CLOSED_EMPTY_ACC` / protected | `CLOSED_EMPTY_ACC` / protected | `FORCE_PROTECT_EVENT_MEMORY`, proxy 0 |
| 1135 | FN | `CLOSED_EMPTY_ACC` / protected | `CLOSED_EMPTY_ACC` / protected | `NO_CHANGE`, proxy 0 |
| 1140 | FN | `CLOSED_EMPTY_ACC` / protected | `CLOSED_EMPTY_ACC` / protected | `NO_CHANGE`, proxy 0 |
| 1150 | FN | `DETECT_ACC` / unprotected | `DETECT_ACC` / unprotected | `NO_CHANGE`, proxy 0 with blank inputs |
| 1160 | TN | `CLOSED_EMPTY_ACC` / blank | `CLOSED_EMPTY_ACC` / not_fn | `NO_CHANGE`, proxy 0 |
| 1165 | TN | `CLOSED_EMPTY_ACC` / blank | `CLOSED_EMPTY_ACC` / not_fn | `NO_CHANGE`, proxy 0 |
| 1170 | TN | `CLOSED_EMPTY_ACC` / blank | `CLOSED_EMPTY_ACC` / not_fn | `NO_CHANGE`, proxy 0 |

Frame 1150 is the critical mismatch: the verifier said the runtime-safe proxy would select it, but the runtime row did not show proxy inputs, proxy rejection, or arbitration activity.

## Parking Q1-SIC-1 vs Q1-SIC-1B

| Frame | Q1-SIC-1 state/action/protection | Q1-SIC-1B state/action/protection | Q1-SIC-1B event/risk/guard |
|---:|---|---|---|
| 1195 | FN / `CLOSED_EMPTY_ACC` / protected | FN / `CLOSED_EMPTY_ACC` / unprotected | 0 / 0 / 0 |
| 1310 | FN / `CLOSED_EMPTY_ACC` / protected | FN / `CLOSED_EMPTY_ACC` / protected | 1 / 1 / 1 |
| 1315 | FN / `CLOSED_EMPTY_ACC` / protected | FN / `CLOSED_EMPTY_ACC` / protected | 1 / 1 / 1 |
| 1320 | FN / `CLOSED_EMPTY_ACC` / protected | FN / `CLOSED_EMPTY_ACC` / protected | 1 / 1 / 1 |
| 1425 | TP / `DETECT_ACC` / not_fn | FN / `CLOSED_EMPTY_ACC` / unprotected | 0 / 1 / 0 |
| 1430 | TP / `REUSE_ACC` / not_fn | FN / `CLOSED_EMPTY_ACC` / unprotected | 0 / 0 / 0 |
| 1435 | FN / `CLOSED_EMPTY_ACC` / protected | FN / `CLOSED_EMPTY_ACC` / unprotected | 0 / 0 / 0 |
| 1440 | FN / `CLOSED_EMPTY_ACC` / protected | FN / `CLOSED_EMPTY_ACC` / unprotected | 0 / 0 / 0 |
| 1445 | FN / `CLOSED_EMPTY_ACC` / protected | FN / `CLOSED_EMPTY_ACC` / unprotected | 0 / 0 / 0 |

Q1-SIC-1B did not preserve the Q1-SIC-1 parking event-safety trajectory. Six inspected parking rows were unprotected in Q1-SIC-1B.

## Step4D6 vs Q1-SIC-1B Parking Trajectory

Step 4D6 protected the same late parking rows via the stable event-safety trajectory. Q1-SIC-1B matched Step 4D6 only on frames 1310, 1315, and 1320. It lost protection at 1195, 1425, 1430, 1435, 1440, and 1445.

This is the strongest evidence that Q1-SIC-1B should not be repaired by only widening the snowFall proxy. The event-safety base trajectory was not preserved.

## copyMachine Drift Table

The copyMachine audit found five Q1-SIC-1B FN rows that lost protection relative to Q1-SIC-1:

| Frame | Q1-SIC-1 | Q1-SIC-1B |
|---:|---|---|
| 925 | TP, no intervention | FN, no intervention |
| 930 | TP, no intervention | FN, no intervention |
| 935 | FN, protected | FN, unprotected |
| 940 | FN, protected | FN, unprotected |
| 945 | FN, protected | FN, unprotected |

This is unexpected non-snowFall event-safety drift.

## Port Watch-Only Telemetry Regression

| Frame | Q1-SIC-1 label/watch/owner | Q1-SIC-1B label/watch/owner |
|---:|---|---|
| 1350 | `WATCH_ONLY_PORT_RETIGHTEN` / 1 / detector_retighten | `NO_CHANGE` / 0 / blank |
| 1355 | `WATCH_ONLY_PORT_RETIGHTEN` / 1 / detector_retighten | `NO_CHANGE` / 0 / blank |

Port detector-retighten was not implemented, but split-branch watch telemetry regressed. This violates the Q1-SIC ownership evidence expected by I7.

## Source Path Audit

`src/run_experiment.py` contains:

- `final_safety_arbitration(...)` near the top of the file.
- `Q1_SIC_EVENT_SAFETY_OWNERS`, which includes `badWeather/snowFall`.
- `Q1_SIC_PORT_WATCH_VIDEO` and frames `{1350, 1355}`.
- Recursive `load_config_with_base(...)`, so nested `base_config` should resolve.
- Runtime proxy input computation immediately before the `final_safety_arbitration(...)` call in the guarded telemetry block.
- The `runtime_proxy_signals` dict is passed into `final_safety_arbitration(...)`.
- Returned Q1-SIC fields are written into `info[...]` immediately after the call.
- If arbitration is active, not shadow-only, final proposal is true, pre-proposal was false, and the row is not watch-only, the code appends `q1_sic_event_safety_no_detector_fallback` to `kinds`.

Important ordering finding: in the source path where the Q1-SIC block is reached, proxy inputs are computed before arbitration and written afterward. The Q1-SIC-1B frame 1150 CSV did not contain `q1_sic_pre_action`, `q1_sic_post_action`, proxy inputs, or a reject reason, so the runtime evidence points to callsite reachability or telemetry persistence failure for that row.

DETECT rows do not appear to have a separate explicit bypass inside `final_safety_arbitration(...)`; the Q1-SIC-1B proxy path checks `_q1_sic_detect_action(...)`. But frame 1150 did not show the proxy path's reject reasons either, so the failure is earlier than a simple DETECT predicate false.

Proposal/protection accounting remains fragile: Q1-SIC can append a no-detector fallback kind after arbitration, but frame 1150 did not show that path. Parking and copyMachine also show that the accepted Step 4D6/Q1-SIC-1 protection trajectory was not preserved.

## Telemetry Persistence Classification

| Video | Q1-SIC-1 active | Q1-SIC-1B active | Q1-SIC-1B proxy active | Q1-SIC-1B unprotected FN | Classification |
|---|---:|---:|---:|---:|---|
| badWeather/snowFall | 0 | 3 | 0 | 1 | proxy integration telemetry absent on detector-action row |
| intermittentObjectMotion/parking | 0 | 0 | 0 | 6 | parking trajectory/protection regression |
| lowFramerate/port_0_17fps | 2 | 0 | 0 | 4 | port watch-only telemetry not preserved |
| shadow/copyMachine | 7 | 7 | 0 | 5 | unexpected unprotected FN drift |

## Failure Classification

Primary class: `STEP4D6_TRAJECTORY_NOT_PRESERVED`

Secondary classes:

- snowFall proxy integration failure
- parking regression
- copyMachine regression
- split-branch watch telemetry regression
- raw wrapper `base_config` changed, but effective recursive config did not show missing inherited event-safety flags

Rejected primary classifications:

- `CONFIG_BASE_INHERITANCE_MISMATCH`: raw YAML base changed, but the source loader is recursive and the effective config diff did not show missing event-safety flags.
- `PROXY_INPUTS_COMPUTED_AFTER_ARBITRATION`: source inspection shows proxy inputs are computed before the arbitration call when the block is reached.
- `DETECT_ACTION_PATH_SKIPS_ARBITRATION`: source inspection shows a DETECT-specific proxy path, but runtime telemetry did not prove that path was reached.
- `COMPARE_REPORTING_MISMATCH`: row-level frame metrics show real trajectory/protection drift, not only compare summary drift.

## Recommended Q1-SIC-1C1 Action

Recommended action: `E. Revert Q1-SIC-1B and return to Q1-SIC-1 as last stable event-safety base`.

Rationale: Q1-SIC-1B is not only a snowFall frame-1150 failure. It also fails to preserve parking, copyMachine, and port watch telemetry. Because the effective config diff does not reveal a simple missing event-safety flag, the next step should first restore the last stable event-safety base and then reintroduce the snowFall runtime proxy through a smaller callsite/telemetry-persistence repair.

Do not proceed to Step 4E7-D2 port retighten until Q1-SIC event-safety is stable again.

## Explicit Safety Statement

No experiments, dry-runs, compares, full CDnet, live runs, live compares, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, controller edits, compare edits, config edits, or existing-output modifications were performed in Q1-SIC-1C.
