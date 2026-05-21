# ASMAG-TR Q1-SIC-1A snowFall Runtime Mismatch Audit

Date: 2026-05-19

## Scope and Safety Confirmation

This phase was audit-only. No experiments, dry-runs, live runs, live compares, targeted CDnet, full CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling were launched.

No controller behavior, `src/run_experiment.py`, compare behavior, configs, existing outputs, or frozen CDnet2014 v1.6 outputs were modified. The only executable run was the new analysis-only script after `py_compile`.

## Q1-SIC-1 Status Recap

Q1-SIC-1 succeeded on compile, shadow verification, scoped residual-risk dry-run execution, normal-frame safety, parking, and port ownership separation:

- Compile passed.
- Shadow verification passed.
- Scoped residual-risk subset completed 56/56 jobs with 0 failed.
- `q1_sic_would_touch_normal_frame` stayed 0.
- Parking passed with proposal `0.46000`, detector `0.00000`, and unprotected FN `0`.
- Port frames 1350/1355 remained `WATCH_ONLY_PORT_RETIGHTEN`.

The phase decision remained `FAIL_DRYRUN` because `badWeather/snowFall` frame 1150 ended as unprotected FN while Q1-SIC runtime telemetry returned `NO_CHANGE`.

## Files and Outputs Inspected

- `docs/ASMAG_TR_Q1_SAFETY_INVARIANT_SPEC.md`
- `docs/ASMAG_TR_Q1_SIC0_INVARIANT_REPLAY_REPORT.md`
- `docs/ASMAG_TR_Q1_SIC1_FINAL_ARBITRATION_REPORT.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_BRANCH_AUDIT.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_PORT_PARKING_REBASE_REPORT.md`
- `docs/DAILY_STATUS.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_VALIDATION_PLAN.md`
- `src/run_experiment.py` read-only
- `tools/verify_q1_sic1_shadow_arbitration.py` read-only
- `tools/replay_q1_safety_invariants.py` read-only
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun.yaml` read-only
- Existing Q1-SIC-1, Q1-SIC-0, Step 4D6, Step 4E6, and Step 4E4 output folders read-only

Created analysis-only:

- `tools/audit_q1_sic1a_snowfall_mismatch.py`
- `outputs/asmag_tr_q1_sic1a_snowfall_mismatch_audit/`

## Generated Audit Outputs

- `snowfall_1150_runtime_row.csv`
- `snowfall_context_1120_1170.csv`
- `snowfall_step4d6_vs_q1sic1_diff.csv`
- `snowfall_step4e6_vs_q1sic1_diff.csv`
- `snowfall_sic0_shadow_vs_runtime.csv`
- `snowfall_missing_columns_summary.csv`
- `snowfall_mismatch_classification.csv`

`py_compile` passed for the new script, and the script completed successfully.

## Frame 1150 Runtime Row

| Field | Q1-SIC-1 value |
|---|---:|
| Video | `badWeather/snowFall` |
| Frame | 1150 |
| `Event_State` | `FN` |
| `Is_Active` | 1 |
| Action | `DETECT_ACC` |
| Selected mode before/after guard | `ACC` / `ACC` |
| `yolo_called` | 1 |
| `ai_intervention_detector_requested` | 0 |
| `ai_intervention_applied` / proposal | 0 |
| `active_event_memory` | 1 |
| `ai_intervention_risk_high` | 1 |
| `ai_intervention_guard_active` | 1 |
| `ai_detector_needed_pred` | 1 |
| `ai_detector_request_blocked_no_refresh_model` | 1 |
| `forced_refresh_cooldown_active` | 1 |
| `q1_sic_arbitration_label` | `NO_CHANGE` |
| `q1_sic_pre_protection_label` | `unprotected_fn` |
| `q1_sic_post_protection_label` | `unprotected_fn` |
| SnowFall rescue reject reason | `action_not_unsafe_empty_fallback` |

Runtime had event/risk/guard pressure, but Q1-SIC did not classify `DETECT_ACC` as an unsafe final action.

## Context Frames 1120-1170

| Frame | State | Action | Proposal | Event memory | Risk high | Guard | Detector-needed | Q1-SIC label | Protection label |
|---:|---|---|---:|---:|---:|---:|---:|---|---|
| 1120 | FN | `CLOSED_EMPTY_ACC` | 1 | 1 | 1 | 1 | 0 | `NO_CHANGE` | protected |
| 1125 | TP | `DETECT_ACC` | 0 | 1 | 0 | 1 | 0 | `NO_CHANGE` | not FN |
| 1130 | TP | `REUSE_ACC` | 1 | 1 | 1 | 1 | 0 | `NO_CHANGE` | not FN |
| 1135 | FN | `CLOSED_EMPTY_ACC` | 1 | 1 | 1 | 1 | 0 | `NO_CHANGE` | protected |
| 1140 | FN | `CLOSED_EMPTY_ACC` | 1 | 1 | 1 | 1 | 0 | `NO_CHANGE` | protected |
| 1145 | TP | `FORCED_REFRESH` | 0 | 1 | 1 | 1 | 1 | `NO_CHANGE` | not FN |
| 1150 | FN | `DETECT_ACC` | 0 | 1 | 1 | 1 | 1 | `NO_CHANGE` | unprotected |
| 1155 | FP | `REUSE_ACC` | 0 | 1 | 1 | 1 | 1 | `NO_CHANGE` | not FN |
| 1160 | TN | `CLOSED_EMPTY_ACC` | 0 | 1 | 0 | 1 | 0 | `NO_CHANGE` | not FN |
| 1165 | TN | `CLOSED_EMPTY_ACC` | 0 | 1 | 0 | 1 | 0 | `NO_CHANGE` | not FN |
| 1170 | TN | `CLOSED_EMPTY_ACC` | 0 | 1 | 0 | 1 | 0 | `NO_CHANGE` | not FN |

The context shows why a blind guard-only repair would be risky: normal/TN rows after 1155 still have event memory and guard active. A repair must require a runtime-safe risk proxy, not merely `active_event_memory=1`.

## Step 4D6 vs Q1-SIC-1

At frame 1150, Step 4D6 and Q1-SIC-1 match the unprotected-FN trajectory:

| Frame | Step 4D6 state/action/proposal | Q1-SIC-1 state/action/proposal | Step 4D6 unprotected FN | Q1-SIC-1 unprotected FN |
|---:|---|---|---:|---:|
| 1150 | `FN` / `DETECT_ACC` / 0 | `FN` / `DETECT_ACC` / 0 | 1 | 1 |

This is not a lost-Step-4D6 trajectory at the row level. Step 4D6 is not a protecting reference for this specific frame.

## Step 4E6 vs Q1-SIC-1

Step 4E6 differed at frame 1150:

| Frame | Step 4E6 state/action/proposal | Q1-SIC-1 state/action/proposal | Step 4E6 unprotected FN | Q1-SIC-1 unprotected FN |
|---:|---|---|---:|---:|
| 1150 | `TP` / `REUSE_ACC` / 0 | `FN` / `DETECT_ACC` / 0 | 0 | 1 |

The Step 4E6 row was not the accepted event-safety reference, and Q1-SIC-1 intentionally did not use Step 4E6 as behavioral base.

## SIC0/Shadow vs Runtime

Q1-SIC-0 replay classified snowFall/lakeSide report-only locks as not pass-worthy. Q1-SIC-1 shadow verification also passed `report_only_not_counted_as_pass=1` over 187 report-only rows.

Runtime frame 1150 was different: no report-only snowFall carry-over lock status reached `final_safety_arbitration`, and the row did not satisfy the runtime unsafe-action predicate. Therefore runtime returned `NO_CHANGE`, not `TELEMETRY_ONLY_DO_NOT_COUNT_PASS` and not an enforcing label.

## Runtime-Available vs Post-Hoc Signals

| Signal | Value at 1150 | Availability class | Runtime-safe as decision input? |
|---|---:|---|---|
| `active_event_memory` | 1 | Runtime before final action | Yes |
| `ai_intervention_risk_high` | 1 | Runtime before final action | Yes |
| `ai_intervention_guard_active` | 1 | Runtime before final action | Yes |
| `ai_detector_needed_pred` | 1 | Runtime before final action | Yes |
| `action_label=DETECT_ACC` | present | After branch decision, before metrics | Yes |
| `ai_detector_request_blocked_no_refresh_model` | 1 | After branch decision, before metrics | Yes |
| `forced_refresh_cooldown_active` | 1 | After branch decision, before metrics | Yes |
| `q1_sic_pre_protection_label=unprotected_fn` | present | Post-hoc/audit metric | No |
| `q1_sic_post_protection_label=unprotected_fn` | present | Post-hoc/audit metric | No |
| `Event_State=FN` | present | Ground-truth-only/reporting | No |
| Derived `event_fn/protected_fn/unprotected_fn` | `1/0/1` | Ground-truth-only/reporting | No |
| `snowfall_weather_likely_unprotected_fn` | not exported as a row column | Missing/present only as local runtime predicate if available | Needs telemetry repair |

Do not repair this by using `Event_State`, `event_fn`, `protected_fn`, or `unprotected_fn` as runtime decision inputs. Those are audit/reporting signals only.

## final_safety_arbitration Condition Path

`final_safety_arbitration(...)` is defined in `src/run_experiment.py` around lines 130-255. The relevant path for frame 1150 is:

1. `q1_sic_final_arbitration_enabled` was true.
2. `q1_sic_event_safety_enabled` was true in the Q1-SIC-1 config.
3. `badWeather/snowFall` is event-safety-owned.
4. The row was not quiet normal because it had FN/event/risk/guard context.
5. It was not port watch-only.
6. It did not enter the report-only-lock path because no snowFall carry-over lock status was passed as an active `report_only_lock`.
7. Ownership/reference checks passed.
8. The enforcing branch required `unsafe_unprotected_fn`, defined as `frame_state == FN`, no proposal, and `_q1_sic_unsafe_action(selected_action)`.
9. `_q1_sic_unsafe_action(...)` only treats `CLOSED_EMPTY*`, `REUSE*`, and `*FALLBACK*` as unsafe. `DETECT_ACC` is not unsafe by that predicate.
10. Therefore `unsafe_unprotected_fn` was false, no enforcement label was selected, and the function returned `NO_CHANGE`.

It did not fail because of split-branch ownership, port retighten, or normal-frame protection. It did not trigger internally and then fail to wire accounting; it never triggered.

## Failure Classification

Primary class: `FINAL_PROTECTION_ACCOUNTING_MISMATCH`

Secondary classes:

- `ARBITRATION_CONDITION_TOO_WEAK`
- `POSTHOC_ONLY_SIGNAL_NOT_RUNTIME_SAFE`
- `TELEMETRY_INSUFFICIENT`

Rationale: runtime had enough event/risk/guard pressure to show this was a dangerous row, but Q1-SIC-1 treated `DETECT_ACC` as safe and did not have a runtime-safe detector-output/empty-mask protection proxy wired into final arbitration. The unprotected-FN evidence itself is post-hoc/ground-truth-derived and must not be used directly for runtime action selection.

Ownership:

- Event-safety branch: yes.
- Port detector-retighten branch: no.
- Normal-frame risk: low only if the repair is gated to runtime event/risk/proxy signals. A naive event-memory or guard-only rule could touch later TN rows and should be avoided.

## Recommended Q1-SIC-1B Action

Recommendation: `Q1-SIC-1B telemetry repair / risk proxy addition`.

Do not revert Q1-SIC-1. Parking and normal-frame safety succeeded, and port ownership stayed clean. The smallest safe next step is to add or wire a runtime-safe risk/protection proxy for snowFall-style event rows where:

- event memory/risk/guard is active,
- detector-needed or detector-output-empty pressure is present,
- no final proposal/protection alternative exists,
- the action is `DETECT_*` but still yields an event-risk empty outcome,
- and quiet normal-frame protection remains hard-gated.

Do not implement this in Q1-SIC-1A, and do not use ground-truth-only FN labels as controller inputs.

## Explicit Stop Confirmation

This audit stopped after creating the analysis script, writing the Q1-SIC-1A audit outputs, creating this report, and updating daily status. No Q1-SIC-1B patch was implemented.
