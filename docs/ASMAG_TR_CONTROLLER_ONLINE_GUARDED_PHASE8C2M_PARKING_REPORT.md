# ASMAG-TR Controller Online Guarded Phase 8C-2M Parking Report

Status: failed targeted category dry-run

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

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2m_dryrun/`
- Updated guard code: `src/run_experiment.py`
- Updated compare code: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2M_PARKING_REPORT.md`
- Updated status: `docs/DAILY_STATUS.md`

## Implementation

- Added parking-only no-detector rescue-first event protection:
  - target video: `intermittentObjectMotion/parking`
  - detector requests disabled on the rescue path
  - rescue candidates protected before the parking cap
  - final normal-frame suppressor still applies
- Added parking-only generic non-rescue proposal cap:
  - proposal target/hard cap: 0.40/0.45
  - detector cap: 0.02
  - rescue candidates are not capped
- Added parking diagnostics:
  - `ai_parking_iom_rescue_candidate`
  - `ai_parking_iom_rescue_active`
  - `ai_parking_iom_rescue_reason`
  - `ai_parking_iom_rescue_rejected_reason`
  - `ai_parking_iom_rescue_no_detector`
  - `ai_parking_iom_rescue_frame`
  - `ai_parking_iom_rescue_cap_used`
  - `ai_parking_iom_rescue_first_protected_before_cap`
  - `ai_parking_iom_cap_active`
  - `ai_parking_iom_cap_suppressed_generic_only`
  - `ai_parking_iom_cap_reclaimed_count`
  - `ai_parking_iom_cap_preserved_count`
  - `ai_parking_iom_final_normal_suppressed`
- Added compare output: `ai_intervention_2m_parking_summary.csv`

## Validation Commands

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2m_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2m_dryrun
```

## Aggregate Result

- Jobs: 80/80 completed, 0 failed
- FMeasure: 0.43061
- Event_F1: 0.66513
- Activation: 0.56778
- Avg_FPS: 29.69619
- P95 latency: 223.50977 ms
- Proposed intervention rate: 0.19818
- Detector request rate: 0.01365
- Block-only rate: 0.18453
- Event/foreground block-only rate: 0.15319
- Normal-frame proposed interventions: 0
- Guard alignment: 1.00000

## Parking Result

| Phase | Proposal | Detector | Event FN | Unprotected FN |
| --- | ---: | ---: | ---: | ---: |
| 8C-2L2 | 0.40000 | 0.00000 | n/a | 16 |
| 8C-2M | 0.20000 | 0.00000 | 33 | 31 |

Parking rescue/cap diagnostics:

- Rescue candidates: 57
- Active rescues: 20
- No-detector rescues: 20
- Rescue protected-before-cap frames: 20
- Protected event FN: 2
- Generic cap suppressions: 52
- Rescue candidates suppressed by final normal suppressor: 0

Root cause:

- The parking rescue candidate predicate was too broad: it fired mainly on unsafe/fallback frames with active memory and persistence risk, but only 2 of the 20 active rescues protected event-FN frames.
- The generic cap was too aggressive: because `ai_parking_iom_cap_generic_only` suppressed generic non-rescue event/foreground proposals even before the 0.40 cap pressure mattered, it reclaimed 52 frames and reduced proposal rate from 0.40000 to 0.20000.
- Net effect: the patch removed more useful generic protection than the rescue restored, so unprotected FN worsened from 16 to 31.

Narrowest next patch recommendation:

- Keep the parking path no-detector and target-video-only.
- Restrict rescue activation to likely unprotected FN frames, not broad unsafe/fallback + memory frames.
- Change the parking cap so it only suppresses generic non-rescue proposals after the proposal cap is reached, and never suppresses localized/event-FN-risk proposals.
- Preserve existing generic proposals until the rescue has demonstrated FN coverage.

## Carry-Over Status

| Video | 8C-2M status |
| --- | --- |
| `shadow/cubicle` | recall 0.87879, unprotected FN 0 |
| `nightVideos/bridgeEntry` | event FN 0 |
| `PTZ/continuousPan` | proposal 0.04000, detector 0.01000, unprotected FN 0 |
| `PTZ/intermittentPan` | proposal 0.01000, detector 0.00000, unprotected FN 0 |
| `lowFramerate/tramCrossroad_1fps` | proposal/detector 0.00000/0.00000 |
| `dynamicBackground/fountain01` | proposal/detector 0.00000/0.00000 |
| `dynamicBackground/fountain02` | normal-frame false interventions 0 |
| `shadow/copyMachine` | proposal/detector 0.38000/0.00000, unprotected FN 12 |

## Remaining Risks

- `turbulence/turbulence2`: proposal/detector 0.38000/0.05000, unprotected FN 2.
- `lowFramerate/tunnelExit_0_35fps`: proposal/detector 0.24000/0.00000, unprotected FN 2.

## Gate Table

| Gate | Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.01365 | PASS |
| Aggregate normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.87879, 0 | PASS |
| BridgeEntry event FN = 0 | 0 | PASS |
| ContinuousPan proposal <= 0.05 | 0.04000 | PASS |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.01000, 0 | PASS |
| TramCrossroad_1fps proposal <= 0.05 and detector <= 0.02 | 0.00000/0.00000 | PASS |
| Fountain01 proposal <= 0.05 and detector <= 0.02 | 0.00000/0.00000 | PASS |
| Fountain02 normal-frame false interventions = 0 | 0 | PASS |
| CopyMachine unprotected FN <= 15 acceptable | 12 | PASS |
| CopyMachine detector <= 0.05 | 0.00000 | PASS |
| Parking detector <= 0.02 | 0.00000 | PASS |
| Parking unprotected FN improves materially versus 2L2 | 16 -> 31 | FAIL |
| Parking preferred unprotected FN <= 8 | 31 | FAIL |
| Parking acceptable unprotected FN <= 12 | 31 | FAIL |
| Hard fail if parking unprotected FN >= 16 | 31 | FAIL |
| No forbidden validation launched | none launched | PASS |

## Decision

8C-2M targeted category dry-run fails. Live remains held.
