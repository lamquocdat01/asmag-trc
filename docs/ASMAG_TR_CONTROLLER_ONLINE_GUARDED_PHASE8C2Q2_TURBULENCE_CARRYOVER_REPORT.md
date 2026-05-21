# ASMAG-TRC Phase 8C-2Q2 Turbulence2 Carry-over Reserve Report

Date: 2026-05-16

## Scope And Safety

Phase 8C-2Q2 adds a dry-run-only, no-detector carry-over reserve for `turbulence/turbulence2` on top of the 8C-2Q policy stack. The reserve is exact-scoped to cap-exhausted turbulence2 closed-empty/fallback rescue frames and uses its own small cap instead of increasing the existing turbulence2 rescue cap.

No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched. Accidental 8C-2E live artifacts were not deleted or overwritten. `ONLINE_CALIBRATED`, P1/P2/P3/FAST/ASMAG_TR_CONTROLLER, and the default guarded config were not modified.

## Files

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_dryrun/`
- Updated controller: `src/run_experiment.py`
- Updated compare: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2Q2_TURBULENCE_CARRYOVER_REPORT.md`
- Updated status: `docs/DAILY_STATUS.md`

## Implementation

The 2Q2 config inherits from 2Q and adds only:

```yaml
online_controller_guarded:
  ai_turbulence2_carryover_reserve_enabled: true
  ai_turbulence2_carryover_reserve_target_video: turbulence/turbulence2
  ai_turbulence2_carryover_reserve_allow_detector: false
  ai_turbulence2_carryover_reserve_extra_cap_per_video: 4
  ai_turbulence2_carryover_reserve_cooldown: 1
  ai_turbulence2_carryover_reserve_requires_not_normal_frame: true
  ai_turbulence2_carryover_reserve_requires_cap_exhausted: true
  ai_turbulence2_carryover_reserve_event_score_threshold: 0.65
  ai_turbulence2_carryover_reserve_foreground_loss_threshold: 0.45
  ai_turbulence2_carryover_reserve_actions:
    - CLOSED_EMPTY_ACC
    - CLOSED_EMPTY_P3_FALLBACK
  ai_turbulence2_carryover_reserve_keep_final_normal_suppressor: true
```

The reserve activates only after the existing turbulence2 FN rescue rejects a candidate because the rescue cap is exhausted. It requires exact `turbulence/turbulence2`, an unsafe empty/fallback action, no detector request, not-final-normal context, and event-FN risk from event score, foreground-loss score, localized FN risk, or recent turbulence rescue context. It preserves the final normal-frame suppressor and does not modify copyMachine, parking, detector policy, or non-turbulence videos.

Added frame logs:

- `ai_turbulence2_carryover_reserve_candidate`
- `ai_turbulence2_carryover_reserve_active`
- `ai_turbulence2_carryover_reserve_reason`
- `ai_turbulence2_carryover_reserve_rejected_reason`
- `ai_turbulence2_carryover_reserve_no_detector`
- `ai_turbulence2_carryover_reserve_frame`
- `ai_turbulence2_carryover_reserve_cap_used`
- `ai_turbulence2_carryover_reserve_protected_event_fn`
- `ai_turbulence2_carryover_reserve_final_normal_suppressed`

Compare now writes `ai_intervention_2q2_turbulence_carryover_summary.csv`.

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_dryrun
```

The dry-run was resumed until all 80 jobs completed. The first compare invocation timed out at 120 seconds while emitting pandas performance warnings; the same dry-run compare was rerun with warnings suppressed and completed.

## Aggregate Result

- Jobs: 80/80 completed, 0 failed
- FMeasure: 0.43068
- Event_F1: 0.66657
- Activation: 0.56292
- Avg_FPS: 28.34227
- P95 latency: 227.01209 ms
- Proposal/intervention rate: 0.21335
- Detector request rate: 0.01163
- Block-only rate: 0.20172
- Event/foreground block-only rate: 0.16481
- Normal-frame proposals: 0
- Guard alignment: 1.00000

## Turbulence2 Comparison

| Phase | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8C-2P | 0.30000 | 0.00000 | 3 | 2 | 1 |
| 8C-2Q | 0.30000 | 0.00000 | 5 | 2 | 3 |
| 8C-2Q2 | 0.31000 | 0.00000 | 3 | 3 | 0 |

2Q2 restores turbulence2 beyond the accepted gate: proposal remains <= 0.35, detector requests remain 0, and unprotected event FNs improve to 0.

## Turbulence2 Carry-over Reserve

- Existing turbulence2 rescue candidates: 3
- Existing turbulence2 rescue active frames: 6
- Existing rescue-protected event-FN frames: 2
- Carry-over reserve candidates: 2
- Carry-over reserve active frames: 1
- Carry-over reserve no-detector frames: 1
- Carry-over reserve protected event-FN frames: 1
- Carry-over reserve cap used max: 1 / 4
- Carry-over final-normal suppressions: 0
- Protected rescue frames accidentally suppressed by pressure guard: 0

Frame status:

| Raw frame | 2Q status | 2Q2 status |
| ---: | --- | --- |
| 950 | FN, `CLOSED_EMPTY_ACC`, rescue cap exhausted | TP, `DETECT_ACC`, not an unprotected FN |
| 975 | FN, `CLOSED_EMPTY_ACC`, rescue cap exhausted | TP, `DETECT_ACC`, not an unprotected FN |
| 985 | FN, `CLOSED_EMPTY_ACC`, rescue cap exhausted | FN protected by carry-over reserve, no detector |

## CopyMachine And Parking Carry-over

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Reserve behavior | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `shadow/copyMachine` | 0.46000 | 0.00000 | 46 | 42 | 4 | 8 reserve activations, 8 protected FNs, no detector | Pass, unchanged from 2Q |
| `intermittentObjectMotion/parking` | 0.45000 | 0.00000 | 33 | 28 | 5 | 8 reserve activations, 4 protected FNs, burst bridge 0, no detector | Pass, improved vs 2P; one more residual FN than 2Q but well inside gate |

No copyMachine or parking reserve code/config was changed in 2Q2.

## Core Gate Status

| Gate | Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01163 | Pass |
| Normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.90909, 0 | Pass |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.01000, 0 | Pass |
| ContinuousPan proposal <= 0.05 | 0.04000 | Pass |
| BridgeEntry event FN = 0 | 0 | Pass |
| TramCrossroad_1fps controlled | proposal/detector 0.00000/0.00000 | Pass |
| Fountain01 quiet | proposal/detector 0.00000/0.00000 | Pass |
| Fountain02 normal false interventions = 0 | 0 | Pass |
| CopyMachine unprotected FN <= 15 | 4 | Pass |
| Parking unprotected FN <= 12 | 5 | Pass |
| CopyMachine detector request <= 0.02 | 0.00000 | Pass |
| Parking detector request <= 0.02 | 0.00000 | Pass |
| Turbulence2 proposal <= 0.35 | 0.31000 | Pass |
| Turbulence2 detector request <= 0.02 | 0.00000 | Pass |
| Turbulence2 unprotected FN <= 2, preferred <= 1 | 0 | Pass preferred |
| Frames 950 and 975 protected or no longer unprotected FN | both TP | Pass |
| TunnelExit proposal <= 0.35, unprotected FN <= 1 | 0.31000, 1 | Pass |
| No forbidden validation launched | confirmed | Pass |

## Decision

8C-2Q2 passes the targeted category dry-run gates. Live was not run automatically. After review of this report and the residual accepted parking/tunnelExit misses, a Step 3B targeted category live retry is now reasonable; full CDnet remains held until targeted live passes.
