# ASMAG-TR Controller Online Guarded Phase 8C-2M2 Parking Preserve FN-Risk Report

Status: failed targeted category dry-run because parking proposal pressure exceeds the hard gate.

## Scope and Safety

- Scope: dry-run-only `intermittentObjectMotion/parking` stability patch.
- Target: `intermittentObjectMotion/parking` only.
- Intentionally not fixed: `turbulence/turbulence2`, `lowFramerate/tunnelExit_0_35fps`.
- Live validation: not run.
- Live compare: not run.
- Full CDnet: not run.
- PTZ-targeted standalone validation: not run.
- LASIESTA, SBI2015, BMC, and cross-dataset validation: not run.

## Files

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m2_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m2_dryrun/`
- Updated guard code: `src/run_experiment.py`
- Updated compare code: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2M2_PARKING_PRESERVE_FN_RISK_REPORT.md`
- Updated status: `docs/DAILY_STATUS.md`

## Implementation

- Added parking localized-FN-risk preservation before cap.
- Relaxed the parking cap so it suppresses only generic non-risk proposals after the soft budget.
- Tightened parking rescue to likely unprotected-FN frames.
- Kept parking detector requests disabled.
- Preserved 8C-2L2 carry-over policies through the 2M base config.

New logs:

- `ai_parking_iom_preserve_fn_risk_candidate`
- `ai_parking_iom_preserve_fn_risk_active`
- `ai_parking_iom_preserve_fn_risk_reason`
- `ai_parking_iom_preserve_fn_risk_rejected_reason`
- `ai_parking_iom_preserve_fn_risk_protected_before_cap`
- `ai_parking_iom_cap_suppressed_generic_nonrisk_only`
- `ai_parking_iom_cap_skipped_preserved_fn_risk`
- `ai_parking_iom_cap_soft_budget_exceeded`
- `ai_parking_iom_rescue_likely_unprotected_fn`
- `ai_parking_iom_rescue_protected_event_fn`
- `ai_parking_iom_rescue_false_positive_activation`

## Validation Commands

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2m2_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2m2_dryrun
```

The compare was rerun once after a reporting-only fix so parking rescue protected-FN counts are computed from frame state. No additional dry-run was launched.

## Aggregate Result

- Jobs: 80/80 completed, 0 failed
- FMeasure: 0.42508
- Event_F1: 0.66359
- Activation: 0.45278
- Avg_FPS: 23.69421
- P95 latency: 348.36063 ms
- Proposed intervention rate: 0.24216
- Detector request rate: 0.02174
- Block-only rate: 0.22042
- Event/foreground block-only rate: 0.18908
- Normal-frame proposed interventions: 0
- Guard alignment: 1.00000

## Parking Result

| Phase | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8C-2L2 | 0.40000 | 0.00000 | n/a | n/a | 16 |
| 8C-2M | 0.20000 | 0.00000 | 33 | 2 | 31 |
| 8C-2M2 | 0.48000 | 0.00000 | 33 | 24 | 9 |

Parking preservation/cap diagnostics:

- Preserve FN-risk candidates: 24
- Preserve FN-risk active frames: 24
- Rescue candidates: 33
- Active rescues: 24
- No-detector rescues: 24
- Rescue protected event-FN frames: 24
- Rescue false-positive activations: 0
- Generic non-risk cap suppressions: 1
- Cap skipped preserved-FN-risk frames: 24
- Final-normal rescue suppressions: 0

Root cause:

- 8C-2M2 fixed the main 2M failure: localized FN-risk proposals were preserved before cap, and parking unprotected FN improved from 31 to 9.
- The patch now over-preserves parking: 48 proposals are retained, giving proposal rate 0.48000, above the hard 0.45 gate.
- The cap suppressed only 1 generic non-risk proposal, so it did not reclaim enough non-risk pressure after preserving the 24 useful FN-risk frames.

Narrowest next patch recommendation:

- Keep the new FN-risk preservation and no-detector rescue behavior.
- Add a parking post-preservation pressure trim that only removes generic non-risk proposals once preserved count exceeds 45 frames.
- Do not cap preserved FN-risk frames.
- Keep detector requests disabled.

## Carry-Over Status

| Video | 8C-2M2 status |
| --- | --- |
| `shadow/cubicle` | recall 0.87879, unprotected FN 0 |
| `nightVideos/bridgeEntry` | event FN 0 |
| `PTZ/intermittentPan` | proposal/detector 0.10000/0.00000, unprotected FN 0 |
| `PTZ/continuousPan` | proposal/detector 0.04000/0.01000, unprotected FN 0 |
| `lowFramerate/tramCrossroad_1fps` | proposal/detector 0.00000/0.00000 |
| `dynamicBackground/fountain01` | proposal/detector 0.00000/0.00000 |
| `dynamicBackground/fountain02` | normal-frame false interventions 0 |
| `shadow/copyMachine` | proposal/detector 0.38000/0.00000, unprotected FN 12 |

## Remaining Risks

- `turbulence/turbulence2`: proposal/detector 0.35000/0.04000, unprotected FN 3.
- `lowFramerate/tunnelExit_0_35fps`: proposal/detector 0.40000/0.03000, unprotected FN 1.

## Gate Table

| Gate | Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.02174 | PASS |
| Aggregate normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.87879, 0 | PASS |
| BridgeEntry event FN = 0 | 0 | PASS |
| ContinuousPan proposal <= 0.05 | 0.04000 | PASS |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.10000, 0 | PASS |
| TramCrossroad_1fps proposal <= 0.05 and detector <= 0.02 | 0.00000/0.00000 | PASS |
| Fountain01 proposal <= 0.05 and detector <= 0.02 | 0.00000/0.00000 | PASS |
| Fountain02 normal-frame false interventions = 0 | 0 | PASS |
| CopyMachine unprotected FN <= 15 acceptable | 12 | PASS |
| CopyMachine detector <= 0.05 | 0.00000 | PASS |
| Parking detector <= 0.02 | 0.00000 | PASS |
| Parking proposal <= 0.45 | 0.48000 | FAIL |
| Parking unprotected FN improves versus 2M | 31 -> 9 | PASS |
| Parking unprotected FN improves versus or matches 2L2 | 16 -> 9 | PASS |
| Parking preferred unprotected FN <= 8 | 9 | FAIL preferred |
| Parking acceptable unprotected FN <= 12 | 9 | PASS |
| Hard fail if parking unprotected FN >= 16 | 9 | PASS |
| No forbidden validation launched | none launched | PASS |

## Decision

8C-2M2 targeted category dry-run fails only on parking proposal pressure. Live remains held.
