# ASMAG-TR Controller Online Guarded Phase 8C-2L CopyMachine Report

Date: 2026-05-14

Status: FAIL for the 8C-2L targeted category dry-run gates. Live remains held.

Phase 8C-2L adds a narrow `shadow/copyMachine` stabilization path on top of 8C-2K:

- cap generic shadow/copyMachine proposal pressure;
- add a no-detector copyMachine event-FN rescue;
- preserve the already successful 8C-2K policies.

No live, live compare, full CDnet, PTZ-targeted standalone, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## Files

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2l_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2l_dryrun/`
- Created/updated report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2L_COPYMACHINE_REPORT.md`
- Updated status: `docs/DAILY_STATUS.md`
- Changed controller: `src/run_experiment.py`
- Changed compare reporting: `tools/compare_asmag_tr_controller_online_guarded.py`

## Validation

Compile:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Result: PASS.

Targeted category dry-run:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2l_dryrun.yaml --max-jobs-per-run 8
```

Resumed until all 80 jobs completed.

Compare:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2l_dryrun
```

The first compare invocation timed out at 120 seconds while writing the large summary set. It was rerun with a longer timeout against the same dry-run root and completed successfully. The timeout did not launch any additional validation scope.

## Aggregate Metrics

- Jobs: 80/80 completed, 0 failed.
- Video count: 20.
- Category count: 9.
- FMeasure: 0.36538.
- Event_F1: 0.64596.
- Activation: 0.37578.
- Avg_FPS: 17.96888.
- P95 latency: 482.31024 ms.
- Proposed intervention rate: 0.25228.
- Proposed detector request rate: 0.03640.
- Block-only rate: 0.21587.
- Event/foreground block-only rate: 0.18150.
- Normal-frame proposed interventions: 0.
- Guard alignment: 1.00000.
- Exact-cubicle late-event rescue count: 4.
- Exact-cubicle no-detector rescue count: 4.

## copyMachine Result

| Metric | 8C-2K | 8C-2L |
|---|---:|---:|
| Proposal rate | 0.40000 | 0.35000 |
| Detector request rate | 0.01000 | 0.00000 |
| Event FN | 46 | 58 |
| Protected event FN | 25 | 33 |
| Unprotected event FN | 21 | 25 |
| Guard reclaimed count | n/a | 37 |
| Guard preserved count | n/a | 35 |
| FN rescue count | n/a | 6 |
| FN rescue no-detector count | n/a | 6 |
| Normal-frame proposals | 0 | 0 |

The 2L guard reduced copyMachine proposal pressure to the hard cap and removed detector requests, but it failed the event-FN gate. Unprotected event FNs worsened from 21 to 25. The rescue fired 6 times, all no-detector, but 25 event-FN frames remained unprotected.

Root cause: the copyMachine guard reaches the hard 0.35 cap before enough event-FN frames can be protected. In the 2L logs, 17 unprotected FN frames had rescue rejection `already_protected` before the later guard cap suppressed the proposal, so rescue was not retried after cap rejection. Also, with 58 copyMachine event-FN frames and a hard maximum of 35 protected proposal frames, the current gate combination cannot reach unprotected FN <= 5 unless the rescue is counted differently from generic proposal pressure or the cap is reviewed.

## Core Carry-Over Status

| Video | Status |
|---|---|
| `shadow/cubicle` | PASS: recall 0.83838, unprotected FN 0, normal-frame proposals 0. |
| `nightVideos/bridgeEntry` | PASS: event FN 0, normal-frame proposals 0. |
| `PTZ/continuousPan` | PASS: proposal 0.04000, detector 0.01000, unprotected FN 0. |
| `lowFramerate/tramCrossroad_1fps` | PASS: proposal 0.01000, detector 0.00000. |
| `dynamicBackground/fountain01` | PASS: proposal 0.00000, detector 0.00000. |
| `dynamicBackground/fountain02` | PASS: normal-frame false interventions 0. |

## PTZ/intermittentPan Regression

| Metric | 8C-2K | 8C-2L |
|---|---:|---:|
| Proposal rate | 0.12000 | 0.03000 |
| Detector request rate | 0.00000 | 0.00000 |
| Event FN | 11 | 5 |
| Unprotected event FN | 0 | 2 |
| Cap reclaimed count | 26 | 23 |
| FN rescue count | 3 | 0 |
| Normal-frame proposals | 0 | 0 |

The proposal and detector gates pass, but the 2K no-detector rescue did not fire in 2L and `PTZ/intermittentPan` regressed to 2 unprotected event FNs. This violates the 2L preservation gate requiring intermittentPan unprotected FN = 0.

## Remaining Risks

| Video | 8C-2L proposal | 8C-2L detector | 8C-2L unprotected FN | Note |
|---|---:|---:|---:|---|
| `intermittentObjectMotion/parking` | 0.40000 | 0.06000 | 33 | Monitored only; not fixed in 2L. |
| `turbulence/turbulence2` | 0.37000 | 0.04000 | 3 | Monitored only; not fixed in 2L. |
| `lowFramerate/tunnelExit_0_35fps` | 0.24000 | 0.00000 | 2 | Monitored only; not fixed in 2L. |

## Gate Table

| Gate | Result | Notes |
|---|---|---|
| 80/80 completed, 0 failed | PASS | `run_progress.csv` has 80 completed jobs. |
| Aggregate detector request rate < 0.10 | PASS | 0.03640. |
| Aggregate normal-frame proposals = 0 | PASS | 0. |
| Guard alignment >= 0.95 | PASS | 1.00000. |
| Cubicle recall >= 0.80 and unprotected FN = 0 | PASS | 0.83838 recall, 0 unprotected FN. |
| bridgeEntry event FN = 0 | PASS | 0. |
| continuousPan proposal <= 0.05 | PASS | 0.04000. |
| intermittentPan proposal <= 0.15 and unprotected FN = 0 | FAIL | Proposal 0.03000, unprotected FN 2. |
| tramCrossroad_1fps proposal <= 0.05 and detector <= 0.02 | PASS | 0.01000 / 0.00000. |
| fountain01 proposal <= 0.05 and detector <= 0.02 | PASS | 0.00000 / 0.00000. |
| fountain02 normal-frame false interventions = 0 | PASS | 0. |
| copyMachine proposal <= 0.35 preferred <= 0.25 | PASS hard, FAIL preferred | 0.35000. |
| copyMachine detector <= 0.05 | PASS | 0.00000. |
| copyMachine unprotected FN materially improves, preferred 0, acceptable <= 5 | FAIL | 21 -> 25 unprotected FN. |
| No forbidden validation launched | PASS | Dry-run and compare only. |

## Conclusion

8C-2L does not pass targeted category dry-run after compare review.

Live remains held. The narrowest next patch should stay dry-run-only and address two scoped issues before any live authorization:

- Move or repeat the copyMachine FN rescue after copyMachine guard suppression so cap-rejected localized FN frames can be rescued deliberately.
- Review the incompatible copyMachine gate/cap arithmetic: with 58 event-FN frames, a hard cap of 35 proposal frames cannot produce unprotected FN <= 5 if protection is counted only as proposed intervention.
- Preserve 8C-2K `PTZ/intermittentPan` rescue behavior explicitly, because 2L regressed it from 0 to 2 unprotected FNs.
