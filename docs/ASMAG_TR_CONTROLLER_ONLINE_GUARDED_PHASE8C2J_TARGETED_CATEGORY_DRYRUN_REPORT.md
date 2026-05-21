# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2J Targeted Category Dry-Run Report

Date: 2026-05-14

Status: FAIL - dry-run completed, but targeted category gates do not clear.

This report covers Step 3 targeted category validation for Phase 8C-2J. This step was dry-run only and used a separate config and output root:

- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2j_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2j_dryrun/`

No live, live compare, full CDnet, PTZ-targeted standalone, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2j_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2j_dryrun
```

The dry-run command was resumed until all jobs completed.

## Video Resolution

All requested videos were present locally. No replacements were used.

Dataset root: `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset`

| Video | Resolved path |
|---|---|
| `shadow/cubicle` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\shadow\cubicle` |
| `nightVideos/bridgeEntry` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\nightVideos\bridgeEntry` |
| `PTZ/continuousPan` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\PTZ\continuousPan` |
| `lowFramerate/tramCrossroad_1fps` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\lowFramerate\tramCrossroad_1fps` |
| `dynamicBackground/fountain01` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\dynamicBackground\fountain01` |
| `dynamicBackground/fountain02` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\dynamicBackground\fountain02` |
| `shadow/backdoor` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\shadow\backdoor` |
| `shadow/copyMachine` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\shadow\copyMachine` |
| `dynamicBackground/overpass` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\dynamicBackground\overpass` |
| `dynamicBackground/canoe` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\dynamicBackground\canoe` |
| `lowFramerate/tunnelExit_0_35fps` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\lowFramerate\tunnelExit_0_35fps` |
| `lowFramerate/turnpike_0_5fps` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\lowFramerate\turnpike_0_5fps` |
| `nightVideos/tramStation` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\nightVideos\tramStation` |
| `nightVideos/streetCornerAtNight` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\nightVideos\streetCornerAtNight` |
| `PTZ/intermittentPan` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\PTZ\intermittentPan` |
| `cameraJitter/traffic` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\cameraJitter\traffic` |
| `intermittentObjectMotion/parking` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\intermittentObjectMotion\parking` |
| `baseline/highway` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\baseline\highway` |
| `baseline/office` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\baseline\office` |
| `turbulence/turbulence2` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\turbulence\turbulence2` |

## Aggregate Metrics

| Metric | Value |
|---|---:|
| Jobs | 80/80 completed, 0 failed |
| Videos / categories | 20 videos / 9 categories |
| FMeasure | 0.40068 |
| Event_F1 | 0.66660 |
| Proposed activation | 0.46114 |
| Avg_FPS | 21.11406 |
| P95 latency ms | 407.14876 |
| Proposed intervention rate | 0.24216 |
| Proposed detector request rate | 0.02326 |
| Block-only rate | 0.21891 |
| Event/foreground block-only rate | 0.18655 |
| Normal-frame proposed interventions | 0 |
| Guard alignment | 1.00000 |
| Late-event rescue count | 4 |
| No-detector rescue count | 4 |

Frame 1560 status: present, not an unprotected FN, detector requested 0. It is not marked protected in this dry-run compare because the final action was already outside the unsafe empty/fallback rescue action set.

## Category Summary

| Category | Videos | Proposal rate | Detector rate | Normal proposals | Event_F1 | FMeasure | Risk note |
|---|---:|---:|---:|---:|---:|---:|---|
| `baseline` | 2 | 0.03000 | 0.00500 | 0 | 0.98453 | 0.87273 | Low proposal pressure; `highway` has 1 unprotected event FN. |
| `cameraJitter` | 1 | 0.01000 | 0.01000 | 0 | 0.84393 | 0.56498 | Clean. |
| `dynamicBackground` | 4 | 0.17196 | 0.01587 | 0 | 0.45340 | 0.22439 | `fountain01` remains quiet; `fountain02` and `overpass` have high proposal pressure. |
| `intermittentObjectMotion` | 1 | 0.40000 | 0.00000 | 0 | 0.51923 | 0.46711 | `parking` has high proposal pressure and 16 unprotected event FNs. |
| `lowFramerate` | 3 | 0.14667 | 0.00667 | 0 | 0.72930 | 0.56421 | `tramCrossroad_1fps` clean; `tunnelExit_0_35fps` has high proposal pressure and 2 unprotected event FNs. |
| `nightVideos` | 3 | 0.27667 | 0.06000 | 0 | 0.90043 | 0.29628 | `bridgeEntry` event FN stays 0; nightVideos proposal pressure is high. |
| `PTZ` | 2 | 0.17000 | 0.03500 | 0 | 0.53603 | 0.11253 | `continuousPan` capped; `intermittentPan` hard-fails proposal gate. |
| `shadow` | 3 | 0.55667 | 0.02333 | 0 | 0.48573 | 0.29050 | `cubicle` passes; `copyMachine` has high unprotected event FNs. |
| `turbulence` | 1 | 0.39000 | 0.04000 | 0 | 0.76768 | 0.66050 | `turbulence2` has high proposal pressure and 3 unprotected event FNs. |

## Per-Video Risk Summary

| Video | Proposal | Detector | Normal props | Event FN | Unprotected FN | Budget max | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `baseline/highway` | 0.020 | 0.000 | 0 | 1 | 1 | 0 | Watch: low pressure but one unprotected event FN. |
| `baseline/office` | 0.040 | 0.010 | 0 | 3 | 0 | 1 | Pass. |
| `cameraJitter/traffic` | 0.010 | 0.010 | 0 | 0 | 0 | 1 | Pass. |
| `dynamicBackground/canoe` | 0.013 | 0.000 | 0 | 0 | 0 | 0 | Pass. |
| `dynamicBackground/fountain01` | 0.000 | 0.000 | 0 | 0 | 0 | 0 | Pass; quiet guard active on 100 frames. |
| `dynamicBackground/fountain02` | 0.400 | 0.060 | 0 | 1 | 1 | 6 | Watch: no normal-frame false interventions, but high proposal pressure. |
| `dynamicBackground/overpass` | 0.240 | 0.000 | 0 | 0 | 0 | 0 | Watch: no detector-heavy behavior, but high proposal pressure. |
| `intermittentObjectMotion/parking` | 0.400 | 0.000 | 0 | 33 | 16 | 0 | Fail-risk: high proposal pressure and many unprotected event FNs. |
| `lowFramerate/tramCrossroad_1fps` | 0.000 | 0.000 | 0 | 0 | 0 | 0 | Pass; retighten/trim preserved. |
| `lowFramerate/tunnelExit_0_35fps` | 0.370 | 0.010 | 0 | 3 | 2 | 1 | Watch/fail-risk: detector budget OK, proposal pressure high. |
| `lowFramerate/turnpike_0_5fps` | 0.070 | 0.010 | 0 | 0 | 0 | 1 | Pass. |
| `nightVideos/bridgeEntry` | 0.310 | 0.080 | 0 | 0 | 0 | 8 | Pass on event FN gate; high but budgeted proposal pressure. |
| `nightVideos/streetCornerAtNight` | 0.200 | 0.020 | 0 | 0 | 0 | 2 | Watch: elevated proposal pressure. |
| `nightVideos/tramStation` | 0.320 | 0.080 | 0 | 0 | 0 | 8 | Watch: elevated proposal pressure. |
| `PTZ/continuousPan` | 0.040 | 0.010 | 0 | 0 | 0 | 1 | Pass; continuousPan cap holds. |
| `PTZ/intermittentPan` | 0.300 | 0.060 | 0 | 10 | 2 | 6 | FAIL: proposal rate exceeds 0.15 hard gate and still leaves unprotected FNs. |
| `shadow/backdoor` | 0.400 | 0.040 | 0 | 0 | 0 | 4 | Watch: no normal-frame spike, but high proposal pressure. |
| `shadow/copyMachine` | 0.400 | 0.010 | 0 | 46 | 21 | 1 | Fail-risk: high unprotected event FNs. |
| `shadow/cubicle` | 0.870 | 0.020 | 0 | 14 | 0 | 2 | Pass: recall 0.87879, unprotected FN 0; stabilizer 2, late rescue 4, all no-detector. |
| `turbulence/turbulence2` | 0.390 | 0.040 | 0 | 3 | 3 | 4 | Fail-risk: high proposal pressure and unprotected FNs. |

## Gate Review

| Gate | Result | Evidence |
|---|---|---|
| All jobs complete, 0 failed | PASS | 80/80 completed, 0 failed. |
| Aggregate detector request rate < 0.10 | PASS | 0.02326. |
| Aggregate normal-frame proposals = 0 or safe/reviewed | PASS | 0 normal-frame proposed interventions. |
| Guard alignment >= 0.95 | PASS | 1.00000. |
| No broad detector-heavy behavior | PASS | Aggregate detector 0.02326; worst listed detector rates stay below 0.10. |
| `shadow/cubicle` recall >= 0.80 and unprotected FN = 0 | PASS | Recall 0.87879, unprotected FN 0. |
| `nightVideos/bridgeEntry` event FN = 0 | PASS | Event FN 0. |
| `PTZ/continuousPan` proposal <= 0.05 | PASS | 0.04000. |
| `lowFramerate/tramCrossroad_1fps` proposal/detector controlled | PASS | 0.00000 / 0.00000. |
| `dynamicBackground/fountain01` proposal/detector controlled | PASS | 0.00000 / 0.00000. |
| `dynamicBackground/fountain02` normal-frame false interventions = 0 | PASS | 0. |
| `PTZ/intermittentPan` no intervention explosion | FAIL | Proposal rate 0.30000, above hard gate 0.15; still has 2 unprotected FNs. |
| LowFramerate detector request control | PASS | `tunnelExit_0_35fps` 0.01000, `turnpike_0_5fps` 0.01000. |
| DynamicBackground no detector-heavy behavior | PASS | `overpass` 0.00000, `canoe` 0.00000. |
| Shadow no normal-frame false-intervention spike | PASS/WATCH | Normal-frame proposals 0, but `copyMachine` has 21 unprotected event FNs. |
| Baseline proposal pressure remains low | PASS/WATCH | `highway` 0.02000, `office` 0.04000; `highway` has 1 unprotected FN. |
| Turbulence no false-pressure explosion | FAIL-RISK | `turbulence2` proposal 0.39000 and 3 unprotected FNs. |
| No forbidden validation launched | PASS | Dry-run and dry-run compare only. |

## Root Cause

The exact-cubicle 8C-2J repair generalizes cleanly to `shadow/cubicle`, and the non-cubicle protections from 8C-2I remain intact on the core carry-over videos. The wider targeted category subset exposes pressure and coverage gaps on videos outside the 2J tuning envelope:

- `PTZ/intermittentPan` is the decisive hard gate failure: proposal rate 0.30000 exceeds the 0.15 hard limit and still leaves 2 unprotected event FNs.
- `intermittentObjectMotion/parking`, `shadow/copyMachine`, and `turbulence/turbulence2` show high proposal pressure with remaining unprotected FNs.
- `dynamicBackground/fountain02`, `dynamicBackground/overpass`, `lowFramerate/tunnelExit_0_35fps`, and nightVideos beyond bridgeEntry need pressure review before live.

## Recommendation

Targeted category dry-run does not pass. Step 3B targeted category live is held.

Narrowest next patch: add a dry-run-only category/video scoped proposal-pressure cap for `PTZ/intermittentPan`, modeled after the existing `continuousPan` cap and preserving event-FN protection. Then review the remaining high-risk dry-run videos for no-detector, non-generic guards before any live validation.
