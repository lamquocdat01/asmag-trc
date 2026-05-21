# ASMAG-TR Q1-SIC-1B Runtime Proxy Repair Report

Date: 2026-05-19

## Scope and Safety Confirmation

Q1-SIC-1B implemented a narrow, runtime-safe snowFall empty-detect risk proxy behind disabled-by-default guarded config flags. The phase did not implement port detector-retighten and did not change port ownership.

No full CDnet, live run, live compare, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched. Frozen CDnet2014 v1.6 outputs and old Step 4D6, Step 4E4, Step 4E6, Q1-SIC-0, Q1-SIC-1, and Q1-SIC-1A output folders were not overwritten.

## Files Modified

- `src/run_experiment.py`
  - Added disabled-by-default Q1-SIC-1B proxy config flags.
  - Added runtime-safe proxy telemetry fields.
  - Added `FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION` arbitration label.
- `tools/verify_q1_sic1b_runtime_proxy.py`
  - New analysis-only pre-run verifier over existing Q1-SIC-1 and Q1-SIC-1A outputs.
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun.yaml`
  - New scoped residual-risk subset config.

## Config and Output Roots

Config:

- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun.yaml`

Output roots:

- `outputs/asmag_tr_q1_sic1b_runtime_proxy_verify/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun/`

## Proxy Definition

The Q1-SIC-1B proxy is scoped to `badWeather/snowFall` event-safety repair and is enabled only by:

- `q1_sic_final_arbitration_enabled: true`
- `q1_sic_event_safety_enabled: true`
- `q1_sic_event_risk_empty_detect_proxy_enabled: true`
- `q1_sic_forbid_gt_decision_signals: true`

Runtime-safe proxy inputs:

| Input | Runtime source |
|---|---|
| active event memory | `active_event_memory` |
| risk-high pressure | `ai_intervention_risk_high` |
| guard pressure | `ai_intervention_guard_active` |
| detector pressure | `ai_detector_needed_pred`, `ai_detector_request_blocked_no_refresh_model`, or `forced_refresh_cooldown_active` |
| recent active event | `frames_since_active_prediction <= 1` |
| detect action | `action_label.startswith("DETECT_")` |
| proposal absent | no current intervention kind and no detector request |
| empty detector/proposal proxy | `pred_object_count == 0` and candidate areas are zero |

Forbidden GT/post-hoc inputs, not used for the new proxy:

- `Event_State`
- `event_fn`
- `protected_fn`
- `unprotected_fn`
- `q1_sic_pre_protection_label`
- `q1_sic_post_protection_label`

Telemetry added:

- `q1_sic_event_risk_empty_detect_proxy`
- `q1_sic_runtime_detector_empty_proxy`
- `q1_sic_runtime_proposal_absent_proxy`
- `q1_sic_runtime_detector_pressure_proxy`
- `q1_sic_runtime_proxy_inputs`
- `q1_sic_proxy_runtime_safe`
- `q1_sic_gt_signal_used_for_decision`
- `q1_sic_empty_detect_proxy_reject_reason`

## Compile Result

Passed:

```text
python -m py_compile src\run_experiment.py tools\verify_q1_sic1b_runtime_proxy.py tools\compare_asmag_tr_controller_online_guarded.py
```

## Shadow / Proxy Verification

Command:

```text
python tools\verify_q1_sic1b_runtime_proxy.py --sic1-root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun --sic1a-root outputs\asmag_tr_q1_sic1a_snowfall_mismatch_audit --out outputs\asmag_tr_q1_sic1b_runtime_proxy_verify
```

Final shadow/proxy verification passed:

| Gate | Result |
|---|---:|
| snowFall 1150 selected | 1 |
| quiet TN 1160/1165/1170 selected | 0 |
| active-event-memory-only selected | 0 |
| all `DETECT_ACC` rows classified unsafe | 0 |
| GT signal used for decision | 0 |
| would touch normal frame | 0 |
| port watch-only preserved | 1 |
| split branch OK | 1 |
| `DETECT_ACC` rows checked / selected | 33 / 1 |

Because the verifier passed, the scoped residual-risk dry-run was allowed.

## Dry-Run and Compare

Dry-run command:

```text
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun.yaml
```

Run result:

- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0

Compare command:

```text
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun
```

Compare completed on the new output root. It emitted pandas fragmentation warnings only.

## Aggregate Guarded Metrics

| Metric | Value |
|---|---:|
| CDnet FMeasure | 0.28985 |
| Event_F1 | 0.64343 |
| Activation | 0.35071 |
| Avg FPS | 25.99883 |
| P95 latency ms | 433.58593 |
| Energy/frame | 3.56079 |
| Reuse rate | 0.24857 |
| normal-frame interventions | 0 |
| guard alignment min | 1.00000 for active guarded videos |
| max `q1_sic_would_touch_normal_frame` | 0 |
| max `q1_sic_gt_signal_used_for_decision` | 0 |

## Per-Video Gate Table

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Q1 active | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| thermal/lakeSide | 0.50 | 0.00 | 48 | 48 | 0 | 0 | pass FN safety |
| intermittentObjectMotion/sofa | 0.35 | 0.00 | 24 | 24 | 0 | 0 | pass |
| badWeather/snowFall | 0.49 | 0.00 | 27 | 26 | 1 | 3 | fail: frame 1150 remains unprotected |
| lowFramerate/port_0_17fps | 0.40 | 0.09 | 14 | 10 | 4 | 0 | fail/watch: port watch telemetry not preserved |
| intermittentObjectMotion/parking | 0.58 | 0.00 | 43 | 37 | 6 | 0 | fail: parking trajectory regressed |
| shadow/copyMachine | 0.52 | 0.00 | 52 | 47 | 5 | 7 | fail: unexpected event-safety drift |
| turbulence/turbulence2 | 0.31 | 0.00 | 3 | 3 | 0 | 0 | pass |
| lowFramerate/tunnelExit_0_35fps | 0.38 | 0.00 | 1 | 1 | 0 | 0 | pass |
| shadow/cubicle | 0.91 | 0.02 | 14 | 14 | 0 | 0 | pass FN safety, recall watch |
| PTZ/continuousPan | 0.05 | 0.01 | 0 | 0 | 0 | 0 | pass |
| PTZ/intermittentPan | 0.01 | 0.00 | 1 | 1 | 0 | 0 | pass |
| dynamicBackground/fountain01 | 0.00 | 0.00 | 0 | 0 | 0 | 0 | pass |
| dynamicBackground/fountain02 | 0.40 | 0.05 | 1 | 1 | 0 | 0 | pass; normal false interventions 0 |
| nightVideos/bridgeEntry | 0.32 | 0.08 | 0 | 0 | 0 | 0 | pass; event FN 0 |

## snowFall Frame 1150 Before / After

| Phase | State | Action | Proposal | Detector request | Event memory | Risk high | Guard | Detector pressure | Empty proxy | Q1 label | Q1 proxy | Protection |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| Q1-SIC-1 | FN | `DETECT_ACC` | 0 | 0 | 1 | 1 | 1 | 1 | n/a | `NO_CHANGE` | n/a | unprotected |
| Q1-SIC-1B | FN | `DETECT_ACC` | 0 | 0 | 1 | 1 | 1 | 1 | row has empty runtime inputs | `NO_CHANGE` | 0 | unprotected |

The dry-run did not activate the new proxy on frame 1150. The row-level telemetry remained default for the new proxy fields:

- `q1_sic_runtime_detector_pressure_proxy=0`
- `q1_sic_runtime_detector_empty_proxy=0`
- `q1_sic_runtime_proposal_absent_proxy=0`
- `q1_sic_runtime_proxy_inputs=""`
- `q1_sic_empty_detect_proxy_reject_reason=""`

That means the dry-run failure is not that the proxy predicate rejected frame 1150; it is that the runtime proxy instrumentation/enforcement did not reach or persist on this detector-action row.

## Context Frames 1120-1170

| Frame | State | Action | Proposal | Detector pressure | Recent active | Empty detector | Q1 label | Q1 proxy |
|---:|---|---|---:|---:|---:|---:|---|---:|
| 1120 | FN | `CLOSED_EMPTY_ACC` | 1 | 0 | 0 | 1 | `FORCE_PROTECT_EVENT_MEMORY` | 0 |
| 1125 | TP | `DETECT_ACC` | 0 | 0 | 0 | 0 | `NO_CHANGE` | 0 |
| 1130 | TP | `REUSE_ACC` | 0 | 0 | 1 | 0 | `NO_CHANGE` | 0 |
| 1135 | FN | `CLOSED_EMPTY_ACC` | 1 | 0 | 1 | 1 | `NO_CHANGE` | 0 |
| 1140 | FN | `CLOSED_EMPTY_ACC` | 1 | 0 | 0 | 0 | `NO_CHANGE` | 0 |
| 1145 | TP | `FORCED_REFRESH` | 0 | 1 | 0 | 0 | `NO_CHANGE` | 0 |
| 1150 | FN | `DETECT_ACC` | 0 | 1 | 1 | expected empty | `NO_CHANGE` | 0 |
| 1155 | FP | `REUSE_ACC` | 0 | 1 | 0 | 0 | `NO_CHANGE` | 0 |
| 1160 | TN | `CLOSED_EMPTY_ACC` | 1 | 1 | 1 | 0 | `NO_CHANGE` | 0 |
| 1165 | TN | `CLOSED_EMPTY_ACC` | 1 | 1 | 0 | 0 | `NO_CHANGE` | 0 |
| 1170 | TN | `CLOSED_EMPTY_ACC` | 1 | 1 | 0 | 1 | `NO_CHANGE` | 0 |

The compare-level normal-frame intervention count remained 0, and `q1_sic_would_touch_normal_frame` stayed 0. The table uses `Event_State` only for audit interpretation.

## Normal-Frame Safety

| Gate | Result |
|---|---:|
| compare normal-frame intervention count | 0 |
| max `q1_sic_would_touch_normal_frame` | 0 |
| max `q1_sic_gt_signal_used_for_decision` | 0 |
| pre-run verifier normal touch | 0 |

Normal-frame protection held, but the dry-run still failed event-safety gates.

## Parking Carry-Over Table

Known parking rows regressed relative to Q1-SIC-1:

| Frame | State | Action | Proposal | Event memory | Risk high | Guard | Q1 label | Protection |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1195 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | 0 | `NO_CHANGE` | unprotected |
| 1310 | FN | `CLOSED_EMPTY_ACC` | 1 | 1 | 1 | 1 | `NO_CHANGE` | protected |
| 1315 | FN | `CLOSED_EMPTY_ACC` | 1 | 1 | 1 | 1 | `NO_CHANGE` | protected |
| 1320 | FN | `CLOSED_EMPTY_ACC` | 1 | 1 | 1 | 1 | `NO_CHANGE` | protected |
| 1425 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 1 | 0 | `NO_CHANGE` | unprotected |
| 1430 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | 0 | `NO_CHANGE` | unprotected |
| 1435 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | 0 | `NO_CHANGE` | unprotected |
| 1440 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | 0 | `NO_CHANGE` | unprotected |
| 1445 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | 0 | `NO_CHANGE` | unprotected |

Parking dry-run gates failed: proposal `0.58`, detector `0.00`, unprotected FN `6`. This is an unexpected trajectory-reference regression and must not be patched blindly inside the snowFall proxy.

## Port Watch-Only Table

| Frame | State | Action | Proposal | Detector | Q1 label | Watch |
|---:|---|---|---:|---:|---|---:|
| 1350 | FN | `CLOSED_EMPTY_P3_FALLBACK` | 0 | 0 | `NO_CHANGE` | 0 |
| 1355 | FN | `CLOSED_EMPTY_P3_FALLBACK` | 0 | 0 | `NO_CHANGE` | 0 |

The pre-run verifier confirmed existing Q1-SIC-1 port watch-only behavior, but the Q1-SIC-1B dry-run did not preserve the runtime watch telemetry. Port detector-retighten was not implemented, but split-branch watch telemetry regressed in the new dry-run.

## Failure Audit and Classification

Primary dry-run failure class: `FAIL_DRYRUN`

Failure classes observed:

- `proxy too narrow / integration not reached`: frame 1150 matched the pre-run runtime proxy, but runtime dry-run proxy telemetry stayed default and the row remained `NO_CHANGE`.
- `protection accounting mismatch`: frame 1150 still ended as unprotected FN.
- `trajectory reference mismatch`: parking regressed from Q1-SIC-1/Step 4D6 safety behavior, with 6 unprotected FN rows.
- `unexpected non-snowFall drift`: copyMachine produced 5 unprotected FN rows.
- `split-branch telemetry regression`: port 1350/1355 lost `WATCH_ONLY_PORT_RETIGHTEN` telemetry.

No GT/post-hoc leakage was observed:

- `q1_sic_gt_signal_used_for_decision` global max was 0.
- `q1_sic_would_touch_normal_frame` global max was 0.

## Decision

`FAIL_DRYRUN`

The Q1-SIC-1B pre-run verifier passed, and the scoped dry-run completed technically, but the event-safety branch cannot be accepted. The intended snowFall frame-1150 repair did not activate in runtime output, and parking/copyMachine/port-watch behavior regressed.

## Recommended Next Step

Proceed to `Q1-SIC-1C audit/repair`, not Step 4E7-D freeze and not Step 4E7-D2 port detector-retighten.

Q1-SIC-1C should audit two things before another dry-run:

1. Why Q1-SIC runtime arbitration telemetry/effect did not persist on detector-action rows like snowFall frame 1150 and port frames 1350/1355.
2. Whether the Q1-SIC-1B config/base inheritance reproduced the Step 4D6 event-safety trajectory; the parking regression suggests the event-safety base was not preserved.

Do not patch further from Q1-SIC-1B without that row-level integration and config-base audit.

## Stop Confirmation

Stopped after creating this report and updating daily status. No Q1-SIC-1C implementation, Step 4E7-D2 port branch, full CDnet, live run, targeted CDnet, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ standalone validation, or Jetson profiling was launched.
