# ASMAG-TR Q1-SIC-1C1 Restore Base Probe Report

Date: 2026-05-19

## Scope and Safety Confirmation

Q1-SIC-1C1 restored Q1-SIC-1 as the behavioral config base and added a shadow-only detector-action runtime telemetry probe for event-safety-owned `DETECT_*` rows. The phase did not enforce a snowFall protection fix.

No full CDnet, live run, live compare, targeted CDnet beyond the scoped residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched. Frozen CDnet2014 v1.6 outputs and old Step 4D6, Step 4E4, Step 4E6, Q1-SIC-0, Q1-SIC-1, Q1-SIC-1A, Q1-SIC-1B, and Q1-SIC-1C output folders were not overwritten.

## Why Q1-SIC-1B Was Disabled

Q1-SIC-1C found that Q1-SIC-1B failed with primary class `STEP4D6_TRAJECTORY_NOT_PRESERVED`. It did not preserve Q1-SIC-1/Step 4D6 event-safety behavior: snowFall frame 1150 stayed `NO_CHANGE`, parking regressed, copyMachine regressed, and port frames 1350/1355 lost watch-only telemetry.

Q1-SIC-1C1 therefore did not continue from Q1-SIC-1B. The new config inherits Q1-SIC-1, does not inherit Q1-SIC-1B, and does not enable Q1-SIC-1B empty-detect enforcement.

## Files Modified

- `src/run_experiment.py`
  - Added disabled-by-default `q1_sic_detector_action_probe_enabled`.
  - Added shadow-only detector-action probe telemetry fields.
  - Added a runtime-safe probe helper that writes telemetry only and does not alter `kinds`, final action, detector request, proposal, protection accounting, Q1-SIC arbitration label, or port watch ownership.
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun.yaml`
  - New config based on Q1-SIC-1.
- `tools/verify_q1_sic1c1_restore_base_probe.py`
  - New verification tool comparing Q1-SIC-1 vs Q1-SIC-1C1.

## Config and Output Roots

Config:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun.yaml`

Output roots:

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1c1_restore_base_probe_verify/`

## Detector-Action Probe Definition

The probe is enabled only by `q1_sic_detector_action_probe_enabled: true`.

Runtime-safe inputs:

| Signal | Runtime source |
|---|---|
| event-safety ownership | category/video key |
| action is detect | `action_label.startswith("DETECT_")` |
| active event memory | `active_event_memory` |
| risk-high pressure | `ai_intervention_risk_high` |
| guard pressure | `ai_intervention_guard_active` |
| detector pressure | `ai_detector_needed_pred`, detector blocked flags, or forced-refresh cooldown |
| proposal absent | no intervention and no detector request at probe time |
| runtime empty proxy | `pred_object_count == 0` and candidate areas are zero |

Probe telemetry columns:

- `q1_sic_detector_action_probe_enabled`
- `q1_sic_detector_action_probe_active`
- `q1_sic_detector_action_probe_video_owner`
- `q1_sic_detector_action_probe_action_is_detect`
- `q1_sic_detector_action_probe_event_risk_pressure`
- `q1_sic_detector_action_probe_detector_pressure`
- `q1_sic_detector_action_probe_detector_blocked`
- `q1_sic_detector_action_probe_cooldown_active`
- `q1_sic_detector_action_probe_proposal_absent`
- `q1_sic_detector_action_probe_runtime_empty_proxy`
- `q1_sic_detector_action_probe_would_select_shadow`
- `q1_sic_detector_action_probe_reject_reason`
- `q1_sic_detector_action_probe_gt_signal_used`
- `q1_sic_detector_action_probe_would_touch_normal_frame`

Forbidden GT/post-hoc inputs were not used as probe decision predicates:

- `Event_State`
- GT-derived `frame_state`
- `event_fn`
- `protected_fn`
- `unprotected_fn`
- `q1_sic_pre_protection_label`
- `q1_sic_post_protection_label`

## Compile Result

Passed:

```text
python -m py_compile src\run_experiment.py tools\verify_q1_sic1c1_restore_base_probe.py tools\compare_asmag_tr_controller_online_guarded.py
```

## Dry-Run Result

Command:

```text
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun.yaml
```

Result:

- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0

## Compare Result

Command:

```text
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun
```

Compare completed on the new Q1-SIC-1C1 output root. It emitted pandas fragmentation warnings only.

Guarded aggregate from `final_main_comparison.csv`:

| Metric | Value |
|---|---:|
| CDnet FMeasure | 0.30625 |
| Event_F1 | 0.63759 |
| Activation | 0.35929 |
| Avg FPS | 20.53205 |
| P95 latency ms | 465.10092 |
| Energy/frame | 3.60129 |
| Reuse rate | 0.23071 |

## Restore-Base Verification Result

Verifier command:

```text
python tools\verify_q1_sic1c1_restore_base_probe.py --sic1-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun --sic1c1-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun --out outputs\asmag_tr_q1_sic1c1_restore_base_probe_verify
```

Verifier summary:

| Gate | Result |
|---|---:|
| parking_restore_ok | 1 |
| port_watch_restore_ok | 0 |
| copyMachine_restore_ok | 0 |
| snowFall_probe_persist_ok | 1 |
| normal_safety_ok | 1 |
| no_q1_sic1b_enforcement_ok | 1 |
| Q1-SIC-1B proxy active rows | 0 |
| Q1-SIC-1B enforcement label rows | 0 |

Decision from verifier: `FAIL_RESTORE_BASE_OR_PROBE`. Since the probe persisted and normal safety held, this report classifies the phase as `FAIL_RESTORE_BASE`.

## Parking Q1-SIC-1 vs Q1-SIC-1C1

| Metric | Q1-SIC-1 | Q1-SIC-1C1 |
|---|---:|---:|
| proposal/intervention rate | 0.46000 | 0.46000 |
| detector request rate | 0.00000 | 0.00000 |
| unprotected FN | 0 | 0 |

Audited parking rows restored:

| Frame | State | Action | Proposal | Q1 label | Protection |
|---:|---|---|---:|---|---|
| 1195 | FN | `CLOSED_EMPTY_ACC` | 1 | `NO_CHANGE` | protected |
| 1310 | FN | `CLOSED_EMPTY_ACC` | 1 | `NO_CHANGE` | protected |
| 1315 | FN | `CLOSED_EMPTY_ACC` | 1 | `NO_CHANGE` | protected |
| 1320 | FN | `CLOSED_EMPTY_ACC` | 1 | `NO_CHANGE` | protected |
| 1425 | TP | `DETECT_ACC` | 0 | `NO_CHANGE` | not_fn |
| 1430 | TP | `REUSE_ACC` | 0 | `NO_CHANGE` | not_fn |
| 1435 | FN | `CLOSED_EMPTY_ACC` | 1 | `NO_CHANGE` | protected |
| 1440 | FN | `CLOSED_EMPTY_ACC` | 1 | `NO_CHANGE` | protected |
| 1445 | FN | `CLOSED_EMPTY_ACC` | 1 | `NO_CHANGE` | protected |

## copyMachine Q1-SIC-1 vs Q1-SIC-1C1

copyMachine did not restore. Six audited frames that were protected in Q1-SIC-1 were unprotected in Q1-SIC-1C1:

| Frame | Q1-SIC-1 | Q1-SIC-1C1 |
|---:|---|---|
| 810 | FN protected | FN unprotected |
| 815 | FN protected | FN unprotected |
| 820 | FN protected | FN unprotected |
| 935 | FN protected | FN unprotected |
| 940 | FN protected | FN unprotected |
| 945 | FN protected | FN unprotected |

Video summary also drifted: Q1-SIC-1 copyMachine proposal/event-FN was `0.52000 / 47`; Q1-SIC-1C1 was `0.58000 / 61`.

## Port Watch Restoration

| Frame | Q1-SIC-1 | Q1-SIC-1C1 |
|---:|---|---|
| 1350 | `WATCH_ONLY_PORT_RETIGHTEN`, watch 1, owner `detector_retighten` | restored |
| 1355 | `WATCH_ONLY_PORT_RETIGHTEN`, watch 1, owner `detector_retighten` | `NO_CHANGE`, watch 0, owner blank |

Port 1355 did not restore the split-branch watch telemetry. No port detector-retighten behavior was implemented.

## snowFall 1150 Detector-Action Probe

snowFall frame 1150 still remained `NO_CHANGE`, which was allowed in this phase. The detector-action probe did persist:

| Field | Value |
|---|---:|
| `Event_State` audit-only | FN |
| action | `DETECT_ACC` |
| Q1-SIC label | `NO_CHANGE` |
| probe enabled | 1 |
| probe active | 1 |
| video owner | `event_safety` |
| event/risk pressure | 1 |
| detector pressure | 1 |
| detector blocked | 1 |
| cooldown active | 1 |
| proposal absent | 1 |
| runtime empty proxy | 1 |
| would select shadow | 1 |
| GT signal used | 0 |
| would touch normal frame | 0 |

This proves the callsite/telemetry persistence problem from Q1-SIC-1B was repaired for the probe, without enforcing protection.

## Normal-Frame Safety

| Gate | Result |
|---|---:|
| normal-frame intervention count | 0 |
| max `q1_sic_would_touch_normal_frame` | 0 |
| max `q1_sic_detector_action_probe_would_touch_normal_frame` | 0 |
| max `q1_sic_gt_signal_used_for_decision` | 0 |
| max probe GT signal used | 0 |

## Decision

`FAIL_RESTORE_BASE`

Q1-SIC-1C1 restored parking and proved snowFall detector-action probe persistence, but it did not restore the full Q1-SIC-1 event-safety base. copyMachine regressed and port frame 1355 lost `WATCH_ONLY_PORT_RETIGHTEN` telemetry.

## Recommended Next Step

Proceed to `Q1-SIC-1C1 audit/repair`, not Q1-SIC-1C2 and not Step 4E7-D2.

The next repair should be limited to restoring Q1-SIC-1 runtime trajectory and port watch telemetry under the current source code. Do not introduce the snowFall protection enforcement until copyMachine and port watch restoration pass.

## Stop Confirmation

Stopped after creating this report and updating daily status. No Q1-SIC-1C2 implementation, Step 4E7-D2 port branch, full CDnet, live run, targeted CDnet beyond the scoped residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, or Jetson profiling was launched.
