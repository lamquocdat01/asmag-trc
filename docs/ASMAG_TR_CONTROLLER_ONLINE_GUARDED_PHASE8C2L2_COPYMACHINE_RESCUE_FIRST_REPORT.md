# ASMAG-TR Controller Online Guarded Phase 8C-2L2 CopyMachine Rescue-First Report

Date: 2026-05-14

Status: PASS for the 8C-2L2 targeted category dry-run gates. Live remains held.

Phase 8C-2L2 adds a narrow rescue-first ordering for `shadow/copyMachine` and an explicit 8C-2K rescue preservation lock for `PTZ/intermittentPan`, on top of 8C-2L. The patch does not target `parking`, `turbulence2`, or `tunnelExit_0_35fps`.

No live, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## Files

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2l2_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2l2_dryrun/`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2L2_COPYMACHINE_RESCUE_FIRST_REPORT.md`
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
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2l2_dryrun.yaml --max-jobs-per-run 8
```

Resumed until all 80 jobs completed.

Compare:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2l2_dryrun
```

Result: PASS. Compare emitted pandas fragmentation warnings only; output CSVs were written.

## Aggregate Metrics

- Jobs: 80/80 completed, 0 failed.
- Video count: 20.
- Category count: 9.
- FMeasure: 0.43259.
- Event_F1: 0.66453.
- Activation: 0.56978.
- Avg_FPS: 26.70032.
- P95 latency: 242.24090 ms.
- Proposed intervention rate: 0.20222.
- Proposed detector request rate: 0.01466.
- Block-only rate: 0.18756.
- Event/foreground block-only rate: 0.15925.
- Normal-frame proposed interventions: 0.
- Guard alignment: 1.00000.

## copyMachine Result

| Metric | 8C-2K | 8C-2L | 8C-2L2 |
|---|---:|---:|---:|
| Proposal rate | 0.40000 | 0.35000 | 0.39000 |
| Detector request rate | 0.01000 | 0.00000 | 0.00000 |
| Event FN | 46 | 58 | 46 |
| Protected event FN | 25 | 33 | 35 |
| Unprotected event FN | 21 | 25 | 11 |
| Guard reclaimed count | n/a | 37 | 24 |
| Guard preserved count | n/a | 35 | 39 |
| FN rescue count | n/a | 6 | 18 |
| FN rescue no-detector count | n/a | 6 | 18 |
| Rescue-first candidates | n/a | n/a | 50 |
| Rescue-first active | n/a | n/a | 18 |
| Generic-only cap suppressions | n/a | n/a | 24 |
| Rescue-first final-normal suppressed | n/a | n/a | 0 |
| Normal-frame proposals | 0 | 0 | 0 |

The rescue-first ordering fixed the 2L regression materially: unprotected event FNs improved from 25 to 11, and also improved versus 8C-2K's 21. Detector requests stayed at 0.00000 and proposal stayed within the acceptable 0.35-0.40 range.

Residual root cause: copyMachine misses the preferred <=10 gate by one frame because the rescue-first extra cap is exhausted. The compare summary shows 50 rescue-first candidates, 18 active rescue-first frames, and `rescue_cap_exhausted` in the rejection distribution. Since proposal and detector gates pass and unprotected FN is below the acceptable <=15 gate, this is an acceptable pass for 2L2.

## PTZ/intermittentPan Result

| Metric | 8C-2K | 8C-2L | 8C-2L2 |
|---|---:|---:|---:|
| Proposal rate | 0.12000 | 0.03000 | 0.01000 |
| Detector request rate | 0.00000 | 0.00000 | 0.00000 |
| Event FN | 11 | 5 | 1 |
| Unprotected event FN | 0 | 2 | 0 |
| Cap reclaimed count | 26 | 23 | 15 |
| Cap preserved count | 12 | 3 | 1 |
| FN rescue count | 3 | 0 | 1 |
| 2K rescue preserved count | n/a | n/a | 1 |
| Normal-frame proposals | 0 | 0 | 0 |

The 8C-2K rescue behavior is preserved for the target video: intermittentPan returns to 0 unprotected event FNs, with no detector requests and a proposal rate well below 0.15.

## Core Carry-Over Status

| Video | Status |
|---|---|
| `shadow/cubicle` | PASS: recall 0.86869, unprotected FN 0, normal-frame proposals 0. |
| `nightVideos/bridgeEntry` | PASS: event FN 0. Detector rate is 0.08000, unchanged as a non-gated carry-over budget detail for this phase. |
| `PTZ/continuousPan` | PASS/no regression: proposal 0.02000, detector 0.00000, unprotected FN 0. The 2K/2J policy was not changed. |
| `lowFramerate/tramCrossroad_1fps` | PASS: proposal 0.00000, detector 0.00000. |
| `dynamicBackground/fountain01` | PASS: proposal 0.00000, detector 0.00000. |
| `dynamicBackground/fountain02` | PASS: normal-frame false interventions 0. |

## Remaining Risks

| Video | 8C-2L2 proposal | 8C-2L2 detector | 8C-2L2 unprotected FN | Note |
|---|---:|---:|---:|---|
| `intermittentObjectMotion/parking` | 0.40000 | 0.00000 | 16 | Monitored only; not fixed in 2L2. |
| `turbulence/turbulence2` | 0.39000 | 0.04000 | 3 | Monitored only; not fixed in 2L2. |
| `lowFramerate/tunnelExit_0_35fps` | 0.25000 | 0.00000 | 2 | Monitored only; not fixed in 2L2. |

## Gate Table

| Gate | Result | Notes |
|---|---|---|
| 80/80 completed, 0 failed | PASS | `run_progress.csv` has 80 completed jobs. |
| Aggregate detector request rate < 0.10 | PASS | 0.01466. |
| Aggregate normal-frame proposals = 0 | PASS | 0. |
| Guard alignment >= 0.95 | PASS | 1.00000. |
| Cubicle recall >= 0.80 and unprotected FN = 0 | PASS | 0.86869 recall, 0 unprotected FN. |
| bridgeEntry event FN = 0 | PASS | 0. |
| continuousPan proposal <= 0.05 | PASS | 0.02000. |
| intermittentPan proposal <= 0.15 | PASS | 0.01000. |
| intermittentPan detector <= 0.02 preferred, hard fail if > 0.05 | PASS | 0.00000. |
| intermittentPan unprotected FN = 0 | PASS | 0. |
| tramCrossroad_1fps proposal <= 0.05 and detector <= 0.02 | PASS | 0.00000 / 0.00000. |
| fountain01 proposal <= 0.05 and detector <= 0.02 | PASS | 0.00000 / 0.00000. |
| fountain02 normal-frame false interventions = 0 | PASS | 0. |
| copyMachine detector <= 0.05 | PASS | 0.00000. |
| copyMachine unprotected FN improves versus 2L and preferably versus 2K | PASS | 25 -> 11 versus 2L, 21 -> 11 versus 2K. |
| copyMachine preferred unprotected FN <= 10 | FAIL preferred | 11. |
| copyMachine acceptable unprotected FN <= 15 | PASS | 11, with proposal 0.39000 and detector 0.00000 passing. |
| Hard fail if copyMachine unprotected FN >= 21 | PASS | 11. |
| No forbidden validation launched | PASS | Dry-run and dry-run compare only. |

## Conclusion

8C-2L2 passes targeted category dry-run after compare review under the acceptable copyMachine gate. The two scoped regressions are fixed: `shadow/copyMachine` event-FN protection improves materially, and `PTZ/intermittentPan` returns to 0 unprotected event FNs while preserving no-detector behavior.

Live remains held. Because `parking`, `turbulence2`, and `tunnelExit_0_35fps` remain documented risks, Step 3B should still be held. The next narrow dry-run patch should target `intermittentObjectMotion/parking` first; it has the largest remaining unprotected FN count.
