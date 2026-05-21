# ASMAG_TR_Q1_SIC1C1R2 Stable Probe Snapshot Report

Date: 2026-05-19

## 1. Scope and Safety Confirmation

Q1-SIC-1C1R2 implemented a narrow, shadow-only detector-action probe snapshot attempt on top of Q1-SIC-1C1R. It was intended to restore stable runtime probe pressure for `badWeather/snowFall` frame 1150 without enforcing snowFall protection and without changing port detector-retighten behavior.

Commands run were limited to the requested compile, scoped residual-risk dry-run, compare on the new Q1-SIC-1C1R2 root, and verifier. No full CDnet, live, live compare, targeted CDnet beyond the scoped residual-risk subset, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, Jetson profiling, old output overwrite, port detector-retighten implementation, or Q1-SIC-1C2 enforcement was launched.

The phase failed verification. No further repair was made after the failure was identified.

## 2. Why Q1-SIC-1C1R2 Exists

Q1-SIC-1C1R restored parking, copyMachine, and port watch telemetry but regressed the snowFall detector-action probe. The C1C1R audit classified the issue as `RUNTIME_PRESSURE_TRAJECTORY_CHANGED`: pressure inputs that were present earlier disappeared by frame 1150, and the row returned through the detector-action helper before later Q1 telemetry.

Q1-SIC-1C1R2 attempted a stable pre-final probe snapshot and short-lived probe-only pressure memory. The intent was to preserve detector-action evidence for future shadow selection only.

## 3. Files Modified

- `src/run_experiment.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun.yaml`
- `tools/verify_q1_sic1c1r2_stable_probe_snapshot.py`
- `docs/ASMAG_TR_Q1_SIC1C1R2_STABLE_PROBE_SNAPSHOT_REPORT.md`
- `docs/DAILY_STATUS.md`

## 4. Config and Output Roots

Config created:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun.yaml`

It inherits from:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml`

New output roots:

- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun/`
- `outputs/asmag_tr_q1_sic1c1r2_stable_probe_snapshot_verify/`

## 5. Stable Snapshot Definition

The implementation added guarded-only config flags:

- `q1_sic_detector_action_probe_stable_snapshot_enabled`
- `q1_sic_detector_action_probe_pressure_memory_max_age`

The probe records stable snapshot telemetry for event-safety-owned rows and maintains a probe-only pressure memory keyed by video. The memory merges current runtime pressure with recent prior pressure so that a later empty detector-action row can still report whether the detector-action probe would have selected it.

It is shadow-only. It does not intentionally change final action, detector request, proposal, or protection accounting.

## 6. Runtime-Safe Inputs

Runtime-safe inputs used by the snapshot/probe path:

- `video_id`, category/video, and frame index
- `action_label`
- `selected_mode_before_guard`
- `selected_mode_after_guard`
- `active_event_memory`
- `ai_intervention_guard_active`
- `ai_intervention_risk_high`
- `ai_detector_needed_pred`
- `ai_detector_request_blocked_no_refresh_model`
- detector-request blocked interval/budget flags
- `forced_refresh_cooldown_active`
- runtime proposal/detector absence
- `pred_object_count`
- candidate ACC/P3/FAST areas
- event-safety owner and port watch owner

Forbidden GT/post-hoc inputs were not used as probe predicates: `Event_State`, GT-derived `frame_state`, `event_fn`, `protected_fn`, `unprotected_fn`, `q1_sic_pre_protection_label`, and `q1_sic_post_protection_label`.

Verification reported:

- `q1_sic_gt_signal_used_for_decision_max = 0`
- `q1_sic_detector_action_probe_gt_signal_used_max = 0`

## 7. Pressure Memory Logic and Guardrails

The pressure memory is active only when:

- stable snapshot is enabled,
- the video is event-safety-owned,
- the row is not the port watch-only video,
- runtime event/guard/detector/empty pressure exists.

At probe evaluation, `would_select_shadow` still requires:

- event-safety owner,
- `DETECT_*` action,
- event-risk pressure,
- detector pressure,
- proposal/detector absence,
- runtime empty proxy,
- not port watch-only,
- no GT signal used.

Guardrails were intended to keep TN context frames 1160, 1165, and 1170 unselected and avoid any snowFall protection enforcement. The context selection guard passed, but the no-enforcement intent failed because the runtime trajectory shifted to existing `FORCE_PROTECT_EVENT_MEMORY` enforcement on snowFall rows.

## 8. Compile Result

Compile passed:

```powershell
python -m py_compile src\run_experiment.py tools\verify_q1_sic1c1r2_stable_probe_snapshot.py tools\compare_asmag_tr_controller_online_guarded.py
```

The same compile command was rerun after tightening verifier reporting for snowFall enforcement labels, and it passed again.

## 9. Dry-Run Result

Scoped residual-risk subset dry-run command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun.yaml
```

Result:

| planned jobs | completed jobs | failed jobs |
|---:|---:|---:|
| 56 | 56 | 0 |

## 10. Compare Result

Compare was run only on the new Q1-SIC-1C1R2 output root:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun
```

The first compare attempt timed out at 120 seconds while writing the large summary set. The same command was rerun with a longer timeout and completed, writing guarded comparison files under the new Q1-SIC-1C1R2 root only.

## 11. Aggregate Guarded Metrics

From the guarded aggregate outputs:

| metric | value |
|---|---:|
| FMeasure | 0.29578 |
| Event_F1 | 0.62784 |
| activation | 0.32286 |
| Avg_FPS | 33.91921 |
| P95 latency ms | 449.59700 |
| intervention rate | 0.38071 |
| detector request rate | 0.01786 |
| normal-frame interventions | 0 |
| guard alignment | 1.00000 |

## 12. Verification Result

Verifier command:

```powershell
python tools\verify_q1_sic1c1r2_stable_probe_snapshot.py --sic1c1r-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun --sic1c1r2-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun --out outputs\asmag_tr_q1_sic1c1r2_stable_probe_snapshot_verify
```

Summary:

| gate | result |
|---|---:|
| snowFall probe restored | 0 |
| snowFall context guard | 1 |
| parking preserved | 0 |
| copyMachine preserved | 1 |
| port watch preserved | 1 |
| normal safety | 1 |
| no enforcement | 0 |
| decision | `FAIL_PROBE_SNAPSHOT` |

## 13. snowFall 1150 C1C1R vs C1C1R2

| field | Q1-SIC-1C1R | Q1-SIC-1C1R2 |
|---|---:|---:|
| action | `DETECT_ACC` | `CLOSED_EMPTY_ACC` |
| Q1 label | `NO_CHANGE` | `FORCE_PROTECT_EVENT_MEMORY` |
| intervention applied | 0 | 1 |
| detector requested | 0 | 0 |
| probe active | 1 | 0 |
| snapshot active | blank | 1 |
| snapshot source | blank | `current+memory` |
| event-risk pressure | 0 | 1 |
| detector pressure | 0 | 1 |
| pressure memory active | blank | 1 |
| would_select_shadow | 0 | 0 |
| reject reason | blank | `action_not_detect+proposal_or_detector_present` |
| GT signal used | 0 | 0 |
| would-touch-normal | 0 | 0 |

The snapshot/memory columns persisted, but frame 1150 no longer reached the intended detector-action probe path. It was already a `CLOSED_EMPTY_ACC` row with an existing `FORCE_PROTECT_EVENT_MEMORY` intervention, so the detector-action probe correctly did not select it.

## 14. snowFall Context 1120-1170

| frame | C1C1R2 action | C1C1R2 label | would_select_shadow | would_touch_normal |
|---:|---|---|---:|---:|
| 1120 | `CLOSED_EMPTY_ACC` | `FORCE_PROTECT_EVENT_MEMORY` | 0 | 0 |
| 1125 | `CLOSED_EMPTY_ACC` | `FORCE_PROTECT_EVENT_MEMORY` | 0 | 0 |
| 1130 | `CLOSED_EMPTY_ACC` | `FORCE_PROTECT_EVENT_MEMORY` | 0 | 0 |
| 1135 | `CLOSED_EMPTY_ACC` | `FORCE_PROTECT_EVENT_MEMORY` | 0 | 0 |
| 1140 | `CLOSED_EMPTY_ACC` | `FORCE_PROTECT_EVENT_MEMORY` | 0 | 0 |
| 1145 | `LIGHTWEIGHT_MASK_ACC` | `NO_CHANGE` | 0 | 0 |
| 1150 | `CLOSED_EMPTY_ACC` | `FORCE_PROTECT_EVENT_MEMORY` | 0 | 0 |
| 1155 | `CLOSED_EMPTY_ACC` | `NO_CHANGE` | 0 | 0 |
| 1160 | `CLOSED_EMPTY_ACC` | `NO_CHANGE` | 0 | 0 |
| 1165 | `CLOSED_EMPTY_ACC` | `NO_CHANGE` | 0 | 0 |
| 1170 | `CLOSED_EMPTY_ACC` | `NO_CHANGE` | 0 | 0 |

The requested TN guard for 1160/1165/1170 held. The failure is earlier trajectory/enforcement drift, not TN over-selection.

## 15. Parking Preservation

| metric | Q1-SIC-1C1R | Q1-SIC-1C1R2 |
|---|---:|---:|
| proposal/intervention rate | 0.46000 | 0.52000 |
| detector request rate | 0.00000 | 0.00000 |
| unprotected FN | 0 | 10 |

Parking did not preserve the Q1-SIC-1C1R baseline. This is a hard failure and confirms C1C1R2 is not acceptable as a stable base.

## 16. copyMachine Preservation

| frame | C1C1R2 action state | restore active | protected |
|---:|---|---:|---:|
| 810 | FN, intervention applied | 1 | yes |
| 815 | FN, intervention applied | 1 | yes |
| 820 | FN, intervention applied | 1 | yes |
| 935 | FN, intervention applied | 1 | yes |
| 940 | FN, intervention applied | 1 | yes |
| 945 | FN, intervention applied | 1 | yes |

copyMachine remained restored on the audited rows.

## 17. Port 1350/1355 Preservation

| frame | label | watch | owner | reference | detector/proposal changed |
|---:|---|---:|---|---|---:|
| 1350 | `WATCH_ONLY_PORT_RETIGHTEN` | 1 | `detector_retighten` | `Step4E4` | no |
| 1355 | `WATCH_ONLY_PORT_RETIGHTEN` | 1 | `detector_retighten` | `Step4E4` | no |

Port watch telemetry remained restored. No port detector-retighten enforcement was introduced.

## 18. Normal-Frame Safety

| metric | value |
|---|---:|
| normal-frame interventions | 0 |
| `q1_sic_would_touch_normal_frame` max | 0 |
| detector-action probe would-touch-normal max | 0 |
| Q1-SIC GT decision signal max | 0 |
| detector-action probe GT signal max | 0 |

Normal-frame safety held and no GT/post-hoc decision leakage was recorded.

## 19. Decision

Decision: `FAIL_PROBE_SNAPSHOT`

Secondary failures:

- `FAIL_PARKING_REGRESSION`: parking proposal drifted to 0.52000 and unprotected FN became 10.
- Unintended snowFall enforcement appeared: seven snowFall rows had `FORCE_*` labels with intervention applied.
- The target row 1150 did not remain a detector-action row, so the detector-action probe could not select it.

## 20. Recommended Next Step

Do not proceed to Q1-SIC-1C2 snowFall protection repair.

Recommended next step: Q1-SIC-1C1R2 audit/repair. The audit should determine why enabling the stable snapshot changes the event-safety trajectory enough to:

- move snowFall frame 1150 from `DETECT_ACC` to `CLOSED_EMPTY_ACC`,
- activate existing `FORCE_PROTECT_EVENT_MEMORY` on snowFall rows,
- regress parking from Q1-SIC-1C1R behavior.

The next repair should restore C1C1R behavior first, then add stable probe telemetry in a way that cannot affect trajectory or protection accounting.
