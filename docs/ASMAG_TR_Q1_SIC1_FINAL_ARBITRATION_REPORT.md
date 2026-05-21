# ASMAG-TR Q1-SIC-1 Final Safety Arbitration Report

Date: 2026-05-19

## Scope and Safety Confirmation

Q1-SIC-1 implemented a shadow-first, invariant-first final safety arbitration layer for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`. The phase used Q1-SIC-0 replay evidence as the source of truth and did not combine event-safety with port detector-retighten. `lowFramerate/port_0_17fps` remained watch-only for detector-retighten ownership.

No full CDnet, live run, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched. Frozen CDnet2014 v1.6 outputs and old Step 4D6, Step 4E4, Step 4E6, smoke, targeted, and full output folders were not overwritten.

## Files Modified

- `src/run_experiment.py`
  - Added pure `final_safety_arbitration(...)`.
  - Added guarded-only Q1-SIC config flags, all disabled by default except safe defaults.
  - Added compact Q1-SIC telemetry columns to guarded `frame_metrics.csv`.
  - Integrated event-safety enforcement after legacy branch predicates and before final proposal accounting.
- `tools/verify_q1_sic1_shadow_arbitration.py`
  - New analysis-only shadow verifier over Q1-SIC-0 replay output.
- `configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun.yaml`
  - New scoped residual-risk subset config, based on Step 4D6.

## Output Roots Created

- `outputs/asmag_tr_q1_sic1_shadow_verify/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun/`

## Invariants Implemented

| Invariant | Implementation status |
|---|---|
| I1 normal-frame safety | Enforced as `NO_CHANGE` for quiet normal frames; dry-run max `q1_sic_would_touch_normal_frame=0`. |
| I2 event-memory preservation | Implemented for event-safety-owned unsafe unprotected FN rows using `FORCE_PROTECT_EVENT_MEMORY`. |
| I3 risk-high unprotected-FN | Implemented for event/risk FN rows using `FORCE_RISK_HIGH_RESCUE` fallback when memory/guard evidence is absent. |
| I4 enforcement-vs-telemetry | Implemented in replay/shadow; runtime dry-run exposed a telemetry gap on `snowFall` frame 1150. |
| I5 branch reachability | Shadow verifier preserves Step 4E6 failure classifications from Q1-SIC-0. |
| I6 trajectory preservation | Runtime telemetry records pre/post action, detector, and protection labels. |
| I7 split-branch | Port 1350/1355 labeled `WATCH_ONLY_PORT_RETIGHTEN`, owner `detector_retighten`, reference `Step4E4`. |
| I8 full-validation hold | Full CDnet remains held. |

## Telemetry Columns Added

`q1_sic_final_arbitration_enabled`, `q1_sic_shadow_only`, `q1_sic_arbitration_active`, `q1_sic_arbitration_label`, `q1_sic_arbitration_reason`, `q1_sic_owner`, `q1_sic_reference_step`, `q1_sic_enforcement_class`, `q1_sic_would_touch_normal_frame`, `q1_sic_watch_only`, `q1_sic_invariants_triggered`, `q1_sic_pre_action`, `q1_sic_post_action`, `q1_sic_pre_detector_request`, `q1_sic_post_detector_request`, `q1_sic_pre_protection_label`, and `q1_sic_post_protection_label`.

## Compile Result

Passed:

```text
python -m py_compile src\run_experiment.py tools\verify_q1_sic1_shadow_arbitration.py tools\compare_asmag_tr_controller_online_guarded.py
```

## Shadow Verification Result

Command:

```text
python tools\verify_q1_sic1_shadow_arbitration.py --input-dir outputs\asmag_tr_q1_sic0_invariant_replay --out outputs\asmag_tr_q1_sic1_shadow_verify
```

| Gate | Result |
|---|---:|
| known_step4e6_failures_caught | 1 |
| parking_failures_caught | 1 |
| parking_frames_caught | 9 |
| port_1350_1355_watch_only | 1 |
| report_only_not_counted_as_pass | 1 |
| would_touch_normal_frame | 0 |
| split_branch_ok | 1 |
| candidate_rows_checked | 509 |

Shadow verification passed, so the scoped dry-run was allowed.

## Dry-Run and Compare

Dry-run command:

```text
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun.yaml
```

Compare command:

```text
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun
```

Run result: 56 planned jobs, 56 completed, 0 failed. Compare completed on the new output root. The compare script emitted pandas fragmentation warnings only; it wrote the expected comparison CSVs.

## Aggregate Guarded Metrics

| Metric | Value |
|---|---:|
| CDnet FMeasure | 0.34221 |
| Event_F1 | 0.66715 |
| Activation | 0.45786 |
| Avg FPS | 26.14548 |
| P95 latency ms | 376.46185 |
| intervention rate | 0.34643 |
| detector request rate | 0.01429 |
| normal-frame intervention count | 0 |
| guard alignment | 1.00000 |
| q1_sic_would_touch_normal_frame max | 0 |
| q1_sic active rows | 9 |

Q1-SIC runtime labels across guarded rows: `FORCE_PROTECT_EVENT_MEMORY=7`, `WATCH_ONLY_PORT_RETIGHTEN=2`, `NO_CHANGE=1391`.

## Per-Video Gate Table

| Video | proposal | detector | event FN | protected FN | unprotected FN | normal proposals | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| thermal/lakeSide | 0.50 | 0.00 | 48 | 48 | 0 | 0 | pass |
| intermittentObjectMotion/sofa | 0.30 | 0.00 | 23 | 23 | 0 | 0 | pass |
| badWeather/snowFall | 0.36 | 0.00 | 22 | 21 | 1 | 0 | fail: residual unprotected FN |
| lowFramerate/port_0_17fps | 0.40 | 0.08 | 13 | 11 | 2 | 0 | watch-only port retighten |
| intermittentObjectMotion/parking | 0.46 | 0.00 | 31 | 31 | 0 | 0 | pass |
| shadow/copyMachine | 0.52 | 0.00 | 47 | 47 | 0 | 0 | watch: Q1 added 7 protections |
| turbulence/turbulence2 | 0.29 | 0.00 | 3 | 3 | 0 | 0 | pass |
| lowFramerate/tunnelExit_0_35fps | 0.35 | 0.00 | 1 | 1 | 0 | 0 | pass versus Step 4D6 watch |
| shadow/cubicle | 0.91 | 0.02 | 14 | 14 | 0 | 0 | pass FN safety; recall watch remains |
| PTZ/continuousPan | 0.03 | 0.01 | 0 | 0 | 0 | 0 | pass |
| PTZ/intermittentPan | 0.01 | 0.00 | 1 | 1 | 0 | 0 | pass |
| dynamicBackground/fountain01 | 0.00 | 0.00 | 0 | 0 | 0 | 0 | pass |
| dynamicBackground/fountain02 | 0.40 | 0.01 | 0 | 0 | 0 | 0 | pass; normal false interventions 0 |
| nightVideos/bridgeEntry | 0.32 | 0.08 | 0 | 0 | 0 | 0 | pass; event FN 0 |

## Parking Arbitration Table

The nine Step 4E6 parking failure rows were caught in shadow replay. In the Step 4D6-based dry-run trajectory they were already protected, so runtime Q1-SIC correctly returned `NO_CHANGE`.

| Frame | Final state | Action | Proposal | Detector | Q1 label | Protection |
|---:|---|---|---:|---:|---|---|
| 1195 | FN | CLOSED_EMPTY_ACC | 1 | 0 | NO_CHANGE | protected_event_fn |
| 1310 | FN | CLOSED_EMPTY_ACC | 1 | 0 | NO_CHANGE | protected_event_fn |
| 1315 | FN | CLOSED_EMPTY_ACC | 1 | 0 | NO_CHANGE | protected_event_fn |
| 1320 | FN | CLOSED_EMPTY_ACC | 1 | 0 | NO_CHANGE | protected_event_fn |
| 1425 | TP | DETECT_ACC | 0 | 0 | NO_CHANGE | not_fn |
| 1430 | TP | REUSE_ACC | 0 | 0 | NO_CHANGE | not_fn |
| 1435 | FN | CLOSED_EMPTY_ACC | 1 | 0 | NO_CHANGE | protected_event_fn |
| 1440 | FN | CLOSED_EMPTY_ACC | 1 | 0 | NO_CHANGE | protected_event_fn |
| 1445 | FN | CLOSED_EMPTY_ACC | 1 | 0 | NO_CHANGE | protected_event_fn |

Parking meets the dry-run gates: proposal 0.46000, detector 0.00000, unprotected FN 0, no accidental FN-protected trim, and no accidental rescue trim.

## snowFall/lakeSide Enforcement-vs-Telemetry

| Video | Result |
|---|---|
| badWeather/snowFall | Dry-run left frame 1150 as final `FN`, action `DETECT_ACC`, proposal 0, detector telemetry 0, Q1 label `NO_CHANGE`. This is a row-level Q1-SIC-1 failure audit item: telemetry/final-protection mismatch. It is inherited from the Step 4D6 safety/watch state but cannot be silently passed as report-only lock success. |
| thermal/lakeSide | All 48 final FN rows were protected; unprotected FN 0. Q1-SIC did not need to activate. |

## cubicle/intermittentPan/tunnelExit Drift

| Video | Step 4D6 reference | Q1-SIC-1 result | Classification |
|---|---|---|---|
| shadow/cubicle | unprotected FN 0 | unprotected FN 0 | FN safety preserved; recall remains a watch item. |
| PTZ/intermittentPan | unprotected FN 0 | unprotected FN 0 | Step 4D6 safety state preserved. |
| lowFramerate/tunnelExit_0_35fps | unprotected FN 1 watch | unprotected FN 0 | improved versus Step 4D6 watch tolerance. |

## Port Watch-Only Table

| Frame | Final state | Action | Proposal | Detector | Q1 label | Owner | Reference | Watch |
|---:|---|---|---:|---:|---|---|---|---:|
| 1350 | FN | CLOSED_EMPTY_P3_FALLBACK | 0 | 0 | WATCH_ONLY_PORT_RETIGHTEN | detector_retighten | Step4E4 | 1 |
| 1355 | FN | CLOSED_EMPTY_P3_FALLBACK | 0 | 0 | WATCH_ONLY_PORT_RETIGHTEN | detector_retighten | Step4E4 | 1 |

Port 1350/1355 did not block event-safety. They remain owned by a future Step 4E7-D2 port detector-retighten branch.

## Decision

`FAIL_DRYRUN`

The dry-run completed technically and preserved the key event-safety base behavior for parking, lakeSide, cubicle, intermittentPan, and tunnelExit, with normal-frame touch held at zero. However, Q1-SIC-1 cannot be frozen because `badWeather/snowFall` frame 1150 remains an unprotected FN while runtime Q1-SIC reports `NO_CHANGE`. That is exactly the kind of final-action/protection mismatch the invariant layer is supposed to expose, not silently pass.

## Recommended Next Step

Proceed to `Q1-SIC-1 telemetry repair`, not Step 4E7-D freeze and not Step 4E7-D2 port retighten yet.

The repair should make runtime arbitration see the final row protection state used by the compare/accounting layer, so rows like `snowFall` frame 1150 can be classified as telemetry-insufficient or enforced deliberately. Do not patch the event-safety branch blindly; keep port retighten split out.
