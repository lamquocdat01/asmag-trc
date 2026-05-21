# ASMAG-TRC Phase 8C-2Q2 Full CDnet2014 Dry-Run Report

Date: 2026-05-16

## Execution Summary

Status: **completed, held for review**.

This Step 4 validation used the frozen 8C-2Q2 policy stack as the full CDnet2014 dry-run candidate. It was dry-run/proposal mode only. Full live, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, and Jetson/edge profiling were not run.

| Item | Value |
|---|---:|
| Config | `configs/asmag_tr_controller_online_guarded_cdnet_full_2q2_dryrun.yaml` |
| Output root | `outputs/asmag_tr_controller_online_guarded_cdnet_full_2q2_dryrun/` |
| Dataset root | `D:/THS Programing/06.6 ASMAG Project/dataset cdnet2014/archive/dataset` |
| Categories planned | 11 |
| Videos planned | 53 |
| Pipelines planned | 4 |
| Jobs planned | 212 |
| Completed jobs | 212 |
| Failed jobs | 0 |
| Pending jobs | 0 |
| Resumed jobs | yes |

Resume/checkpoint behavior worked. After 32 completed jobs, PowerShell stopped on a non-fatal pandas `FutureWarning` from stderr and left `run_progress.csv` as a zero-byte stale progress artifact. The empty artifact was preserved as `run_progress.empty_after_stderr_warning_20260516.csv`; no result outputs were deleted. The runner rebuilt progress from existing checkpoints and completed the remaining jobs.

## Planned Full Video List

| Category | Videos |
|---|---|
| `badWeather` | `blizzard`, `skating`, `snowFall`, `wetSnow` |
| `baseline` | `highway`, `office`, `pedestrians`, `PETS2006` |
| `cameraJitter` | `badminton`, `boulevard`, `sidewalk`, `traffic` |
| `dynamicBackground` | `boats`, `canoe`, `fall`, `fountain01`, `fountain02`, `overpass` |
| `intermittentObjectMotion` | `abandonedBox`, `parking`, `sofa`, `streetLight`, `tramstop`, `winterDriveway` |
| `lowFramerate` | `port_0_17fps`, `tramCrossroad_1fps`, `tunnelExit_0_35fps`, `turnpike_0_5fps` |
| `nightVideos` | `bridgeEntry`, `busyBoulvard`, `fluidHighway`, `streetCornerAtNight`, `tramStation`, `winterStreet` |
| `PTZ` | `continuousPan`, `intermittentPan`, `twoPositionPTZCam`, `zoomInZoomOut` |
| `shadow` | `backdoor`, `bungalows`, `busStation`, `copyMachine`, `cubicle`, `peopleInShade` |
| `thermal` | `corridor`, `diningRoom`, `lakeSide`, `library`, `park` |
| `turbulence` | `turbulence0`, `turbulence1`, `turbulence2`, `turbulence3` |

## Aggregate Metrics

| Metric | Full CDnet 8C-2Q2 dry-run |
|---|---:|
| FMeasure | 0.47863 |
| Event_F1 | 0.76989 |
| Activation / proposed activation | 0.61917 |
| Avg_FPS | 26.11998 |
| P95 latency | 244.80332 ms |
| Proposed intervention rate | 0.17766 |
| Proposed detector request rate | 0.01211 |
| Block-only rate | 0.16555 |
| Event/foreground block-only rate | 0.14632 |
| Normal-frame proposed interventions | 0 |
| Guard alignment | 1.00000 |

## Category-Wise Metrics

| Category | Videos | FMeasure | Event_F1 | Activation | Proposal | Detector | Normal proposals | Event FN | Protected FN | Unprotected FN | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `badWeather` | 4 | 0.73136 | 0.80351 | 0.56000 | 0.28000 | 0.02000 | 0 | 69 | 54 | 15 | Watch `snowFall` unprotected FN 10. |
| `baseline` | 4 | 0.57477 | 0.97285 | 0.62250 | 0.07000 | 0.01000 | 0 | 9 | 4 | 5 | `PETS2006` low FMeasure but event F1 high. |
| `cameraJitter` | 4 | 0.62330 | 0.94608 | 0.68863 | 0.04217 | 0.00250 | 0 | 2 | 2 | 0 | Controlled. |
| `dynamicBackground` | 6 | 0.38952 | 0.37182 | 0.73761 | 0.11000 | 0.00167 | 0 | 0 | 0 | 0 | No FN issue, but very low Event_F1 on `overpass`, `fall`, `fountain01`. |
| `intermittentObjectMotion` | 6 | 0.27002 | 0.88274 | 0.56667 | 0.22500 | 0.02500 | 0 | 70 | 55 | 15 | Parking is over revised cap; `sofa` unprotected FN 10. |
| `lowFramerate` | 4 | 0.42675 | 0.64040 | 0.64750 | 0.17250 | 0.01750 | 0 | 7 | 6 | 1 | Category detector controlled; `port_0_17fps` detector 0.07000 watch. |
| `nightVideos` | 6 | 0.32395 | 0.88529 | 0.66833 | 0.14333 | 0.01833 | 0 | 0 | 0 | 0 | Event-safe; `bridgeEntry` remains protected. |
| `PTZ` | 4 | 0.29671 | 0.67519 | 0.82000 | 0.06000 | 0.00500 | 0 | 1 | 1 | 0 | No unprotected FN, but PTZ pixel FMeasure remains a review item. |
| `shadow` | 6 | 0.59197 | 0.66734 | 0.39833 | 0.44500 | 0.01667 | 0 | 77 | 72 | 5 | `cubicle` and `copyMachine` protected but high proposal. |
| `thermal` | 5 | 0.74492 | 0.91225 | 0.49513 | 0.13135 | 0.00682 | 0 | 49 | 27 | 22 | `lakeSide` is the top unprotected-FN risk. |
| `turbulence` | 4 | 0.39466 | 0.81193 | 0.69000 | 0.15250 | 0.00250 | 0 | 6 | 6 | 0 | `turbulence2` carry-over remains protected. |

## Video-Wise Risk Table

| Video | FMeasure | Event_F1 | Proposal | Detector | Normal proposals | Event FN | Protected FN | Unprotected FN | Detector budget max | Major guard | Label |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `badWeather/blizzard` | 0.65487 | 0.80952 | 0.40000 | 0.01000 | 0 | 32 | 27 | 5 | 1 | general 2Q2 guarded policy | PASS |
| `badWeather/skating` | 0.56361 | 0.62500 | 0.13000 | 0.03000 | 0 | 0 | 0 | 0 | 3 | general 2Q2 guarded policy | PASS |
| `badWeather/snowFall` | 0.87425 | 0.86061 | 0.29000 | 0.03000 | 0 | 22 | 12 | 10 | 3 | general 2Q2 guarded policy | WATCH |
| `badWeather/wetSnow` | 0.83268 | 0.91892 | 0.30000 | 0.01000 | 0 | 15 | 15 | 0 | 1 | general 2Q2 guarded policy | PASS |
| `baseline/highway` | 0.96674 | 0.99497 | 0.02000 | 0.00000 | 0 | 1 | 0 | 1 | 0 | general 2Q2 guarded policy | PASS |
| `baseline/office` | 0.77872 | 0.97409 | 0.04000 | 0.01000 | 0 | 3 | 3 | 0 | 1 | general 2Q2 guarded policy | PASS |
| `baseline/pedestrians` | 0.42316 | 0.94798 | 0.08000 | 0.01000 | 0 | 0 | 0 | 0 | 1 | general 2Q2 guarded policy | PASS |
| `baseline/PETS2006` | 0.13045 | 0.97436 | 0.14000 | 0.02000 | 0 | 5 | 1 | 4 | 2 | general 2Q2 guarded policy | WATCH |
| `cameraJitter/badminton` | 0.77574 | 1.00000 | 0.04225 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `cameraJitter/boulevard` | 0.39734 | 0.95288 | 0.01000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `cameraJitter/sidewalk` | 0.75214 | 0.98750 | 0.08642 | 0.00000 | 0 | 2 | 2 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `cameraJitter/traffic` | 0.56800 | 0.84393 | 0.03000 | 0.01000 | 0 | 0 | 0 | 0 | 1 | general 2Q2 guarded policy | PASS |
| `dynamicBackground/boats` | 0.90844 | 0.34711 | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | WATCH |
| `dynamicBackground/canoe` | 0.56876 | 0.78125 | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `dynamicBackground/fall` | 0.10964 | 0.13084 | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | WATCH |
| `dynamicBackground/fountain01` | 0.03924 | 0.30508 | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | fountain01 quiet guard | WATCH |
| `dynamicBackground/fountain02` | 0.71104 | 0.66667 | 0.40000 | 0.01000 | 0 | 0 | 0 | 0 | 1 | normal-frame suppressor watch | WATCH |
| `dynamicBackground/overpass` | 0.00000 | 0.00000 | 0.26000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | WATCH |
| `intermittentObjectMotion/abandonedBox` | 0.49772 | 0.98477 | 0.13000 | 0.02000 | 0 | 3 | 3 | 0 | 2 | general 2Q2 guarded policy | PASS |
| `intermittentObjectMotion/parking` | 0.47928 | 0.53333 | 0.51000 | 0.00000 | 0 | 32 | 29 | 3 | 0 | parking protection-aware | FAIL/HOLD |
| `intermittentObjectMotion/sofa` | 0.16873 | 0.87640 | 0.20000 | 0.03000 | 0 | 22 | 12 | 10 | 3 | general 2Q2 guarded policy | WATCH |
| `intermittentObjectMotion/streetLight` | 0.07547 | 0.98477 | 0.05000 | 0.01000 | 0 | 2 | 1 | 1 | 1 | general 2Q2 guarded policy | WATCH |
| `intermittentObjectMotion/tramstop` | 0.33355 | 0.95288 | 0.31000 | 0.05000 | 0 | 9 | 9 | 0 | 5 | general 2Q2 guarded policy | WATCH |
| `intermittentObjectMotion/winterDriveway` | 0.06537 | 0.96429 | 0.15000 | 0.04000 | 0 | 2 | 1 | 1 | 4 | general 2Q2 guarded policy | WATCH |
| `lowFramerate/port_0_17fps` | 0.00000 | 0.40580 | 0.37000 | 0.07000 | 0 | 5 | 5 | 0 | 7 | general 2Q2 guarded policy | WATCH |
| `lowFramerate/tramCrossroad_1fps` | 0.79750 | 0.46154 | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | lowFramerate retighten | WATCH |
| `lowFramerate/tunnelExit_0_35fps` | 0.09523 | 0.86585 | 0.31000 | 0.00000 | 0 | 2 | 1 | 1 | 0 | tunnelExit preserve/rescue | WATCH |
| `lowFramerate/turnpike_0_5fps` | 0.81425 | 0.82840 | 0.01000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `nightVideos/bridgeEntry` | 0.15849 | 0.97436 | 0.22000 | 0.05000 | 0 | 0 | 0 | 0 | 5 | bridgeEntry protection | WATCH |
| `nightVideos/busyBoulvard` | 0.30267 | 0.77419 | 0.22000 | 0.01000 | 0 | 0 | 0 | 0 | 1 | general 2Q2 guarded policy | PASS |
| `nightVideos/fluidHighway` | 0.24369 | 0.94737 | 0.10000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `nightVideos/streetCornerAtNight` | 0.23077 | 0.86331 | 0.10000 | 0.01000 | 0 | 0 | 0 | 0 | 1 | general 2Q2 guarded policy | PASS |
| `nightVideos/tramStation` | 0.59810 | 0.86364 | 0.19000 | 0.04000 | 0 | 0 | 0 | 0 | 4 | general 2Q2 guarded policy | PASS |
| `nightVideos/winterStreet` | 0.40994 | 0.88889 | 0.03000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `PTZ/continuousPan` | 0.08818 | 0.29060 | 0.04000 | 0.01000 | 0 | 0 | 0 | 0 | 1 | continuousPan cap | WATCH |
| `PTZ/intermittentPan` | 0.23884 | 0.84472 | 0.01000 | 0.00000 | 0 | 1 | 1 | 0 | 0 | intermittentPan cap/rescue | WATCH |
| `PTZ/twoPositionPTZCam` | 0.70611 | 0.79245 | 0.13000 | 0.01000 | 0 | 0 | 0 | 0 | 1 | general 2Q2 guarded policy | PASS |
| `PTZ/zoomInZoomOut` | 0.15373 | 0.77301 | 0.06000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | WATCH |
| `shadow/backdoor` | 0.00000 | 0.00000 | 0.40000 | 0.04000 | 0 | 0 | 0 | 0 | 4 | general 2Q2 guarded policy | WATCH |
| `shadow/bungalows` | 0.91582 | 0.70103 | 0.37000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `shadow/busStation` | 0.85355 | 0.92473 | 0.29000 | 0.00000 | 0 | 14 | 14 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `shadow/copyMachine` | 0.64981 | 0.69281 | 0.46000 | 0.00000 | 0 | 47 | 42 | 5 | 0 | copyMachine reserve | WATCH |
| `shadow/cubicle` | 0.21338 | 0.75591 | 0.90000 | 0.02000 | 0 | 14 | 14 | 0 | 2 | cubicle reserve/stabilizer | WATCH |
| `shadow/peopleInShade` | 0.91926 | 0.92958 | 0.25000 | 0.04000 | 0 | 2 | 2 | 0 | 4 | general 2Q2 guarded policy | PASS |
| `thermal/corridor` | 0.80410 | 1.00000 | 0.11000 | 0.02000 | 0 | 0 | 0 | 0 | 2 | general 2Q2 guarded policy | PASS |
| `thermal/diningRoom` | 0.78691 | 0.97959 | 0.01000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `thermal/lakeSide` | 0.50681 | 0.63636 | 0.40000 | 0.00000 | 0 | 48 | 27 | 21 | 0 | general 2Q2 guarded policy | WATCH |
| `thermal/library` | 0.81693 | 0.96970 | 0.01000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `thermal/park` | 0.80988 | 0.97561 | 0.12676 | 0.01408 | 0 | 1 | 0 | 1 | 1 | general 2Q2 guarded policy | PASS |
| `turbulence/turbulence0` | 0.03628 | 0.60504 | 0.21000 | 0.01000 | 0 | 3 | 3 | 0 | 1 | general 2Q2 guarded policy | WATCH |
| `turbulence/turbulence1` | 0.20671 | 1.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |
| `turbulence/turbulence2` | 0.66756 | 0.76768 | 0.31000 | 0.00000 | 0 | 3 | 3 | 0 | 0 | turbulence2 carry-over | WATCH |
| `turbulence/turbulence3` | 0.66809 | 0.87500 | 0.09000 | 0.00000 | 0 | 0 | 0 | 0 | 0 | general 2Q2 guarded policy | PASS |

## Carry-Over Watchlist

- `shadow/cubicle`: proposal 0.90000, detector 0.02000, unprotected FN 0. It remains protected but proposal pressure is high in full CDnet.
- `shadow/copyMachine`: proposal 0.46000, detector 0.00000, event FN 47, protected FN 42, unprotected FN 5. Still no-detector and within targeted-category intent, but remains a Step 4 watch item.
- `intermittentObjectMotion/parking`: proposal 0.51000, detector 0.00000, event FN 32, protected FN 29, unprotected FN 3. It exceeds the revised protection-aware parking cap by 0.01000.
- `PTZ/continuousPan`: proposal 0.04000, detector 0.01000, unprotected FN 0. Proposal remains controlled, but FMeasure/Event_F1 are low.
- `PTZ/intermittentPan`: proposal 0.01000, detector 0.00000, event FN 1, protected FN 1, unprotected FN 0. Targeted guard carries over.
- `lowFramerate/tramCrossroad_1fps`: proposal/detector 0.00000/0.00000, unprotected FN 0. Retighten carries over.
- `lowFramerate/tunnelExit_0_35fps`: proposal 0.31000, detector 0.00000, unprotected FN 1. Within the targeted gate but still watchlisted.
- `dynamicBackground/fountain01`: proposal/detector 0.00000/0.00000, unprotected FN 0. Quiet guard carries over, but Event_F1 is low.
- `dynamicBackground/fountain02`: proposal 0.40000, detector 0.01000, normal-frame proposals 0. Normal-frame suppressor holds.
- `turbulence/turbulence2`: proposal 0.31000, detector 0.00000, unprotected FN 0. Carry-over reserve remains effective.
- `nightVideos/bridgeEntry`: event FN 0, detector 0.05000. Event-safe but detector pressure should be monitored.

## Gate Evaluation

| Gate | Result | Status |
|---|---:|---|
| All planned jobs complete, 0 failed | 212/212 completed, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.01211 | PASS |
| Normal-frame proposed interventions = 0 or reviewed | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| No broad detector-heavy behavior | aggregate detector 0.01211 | PASS |
| No category has uncontrolled proposal explosion without event-FN justification | high proposal is mostly protected/FN-risk, but `shadow/cubicle` 0.90000 and parking 0.51000 require review | WATCH |
| PTZ categories do not collapse | no unprotected FN, but PTZ FMeasure 0.29671 and `continuousPan` Event_F1 0.29060 need review | WATCH |
| dynamicBackground normal-frame false-intervention explosion avoided | normal proposals 0 | PASS |
| lowFramerate detector request stays controlled | category detector 0.01750, but `port_0_17fps` detector 0.07000 | WATCH |
| Parking uses protection-aware gate | proposal 0.51000 vs revised cap 0.50000, detector 0.00000, unprotected FN 3 | FAIL |
| No forbidden validation launched | dry-run and dry-run compare only | PASS |

## Residual Risk Analysis

Top videos by unprotected FN:

| Rank | Video | Unprotected FN | Event FN | Protected FN | Proposal | Detector |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `thermal/lakeSide` | 21 | 48 | 27 | 0.40000 | 0.00000 |
| 2 | `badWeather/snowFall` | 10 | 22 | 12 | 0.29000 | 0.03000 |
| 3 | `intermittentObjectMotion/sofa` | 10 | 22 | 12 | 0.20000 | 0.03000 |
| 4 | `shadow/copyMachine` | 5 | 47 | 42 | 0.46000 | 0.00000 |
| 5 | `badWeather/blizzard` | 5 | 32 | 27 | 0.40000 | 0.01000 |
| 6 | `baseline/PETS2006` | 4 | 5 | 1 | 0.14000 | 0.02000 |
| 7 | `intermittentObjectMotion/parking` | 3 | 32 | 29 | 0.51000 | 0.00000 |
| 8 | `intermittentObjectMotion/streetLight` | 1 | 2 | 1 | 0.05000 | 0.01000 |
| 9 | `intermittentObjectMotion/winterDriveway` | 1 | 2 | 1 | 0.15000 | 0.04000 |
| 10 | `lowFramerate/tunnelExit_0_35fps` | 1 | 2 | 1 | 0.31000 | 0.00000 |

Top videos by detector request rate:

| Rank | Video | Detector | Proposal | Unprotected FN |
|---:|---|---:|---:|---:|
| 1 | `lowFramerate/port_0_17fps` | 0.07000 | 0.37000 | 0 |
| 2 | `intermittentObjectMotion/tramstop` | 0.05000 | 0.31000 | 0 |
| 3 | `nightVideos/bridgeEntry` | 0.05000 | 0.22000 | 0 |
| 4 | `shadow/peopleInShade` | 0.04000 | 0.25000 | 0 |
| 5 | `intermittentObjectMotion/winterDriveway` | 0.04000 | 0.15000 | 1 |
| 6 | `nightVideos/tramStation` | 0.04000 | 0.19000 | 0 |
| 7 | `shadow/backdoor` | 0.04000 | 0.40000 | 0 |
| 8 | `badWeather/snowFall` | 0.03000 | 0.29000 | 10 |
| 9 | `badWeather/skating` | 0.03000 | 0.13000 | 0 |
| 10 | `intermittentObjectMotion/sofa` | 0.03000 | 0.20000 | 10 |

Top videos by proposal/intervention rate:

| Rank | Video | Proposal | Detector | Unprotected FN | Note |
|---:|---|---:|---:|---:|---|
| 1 | `shadow/cubicle` | 0.90000 | 0.02000 | 0 | Protected but high proposal pressure. |
| 2 | `intermittentObjectMotion/parking` | 0.51000 | 0.00000 | 3 | Exceeds revised parking cap. |
| 3 | `shadow/copyMachine` | 0.46000 | 0.00000 | 5 | Protected no-detector carry-over. |
| 4 | `thermal/lakeSide` | 0.40000 | 0.00000 | 21 | Top FN risk. |
| 5 | `badWeather/blizzard` | 0.40000 | 0.01000 | 5 | Event-risk pressure. |
| 6 | `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | Normal proposals remain 0. |
| 7 | `shadow/backdoor` | 0.40000 | 0.04000 | 0 | Low FMeasure/Event_F1. |
| 8 | `lowFramerate/port_0_17fps` | 0.37000 | 0.07000 | 0 | Detector watch. |
| 9 | `shadow/bungalows` | 0.37000 | 0.00000 | 0 | Event-safe. |
| 10 | `intermittentObjectMotion/tramstop` | 0.31000 | 0.05000 | 0 | Detector watch. |

Very low FMeasure or Event_F1 watchlist:

- `dynamicBackground/overpass`: FMeasure 0.00000, Event_F1 0.00000.
- `shadow/backdoor`: FMeasure 0.00000, Event_F1 0.00000.
- `lowFramerate/port_0_17fps`: FMeasure 0.00000, Event_F1 0.40580.
- `turbulence/turbulence0`: FMeasure 0.03628, Event_F1 0.60504.
- `dynamicBackground/fountain01`: FMeasure 0.03924, Event_F1 0.30508.
- `intermittentObjectMotion/winterDriveway`: FMeasure 0.06537, Event_F1 0.96429.
- `intermittentObjectMotion/streetLight`: FMeasure 0.07547, Event_F1 0.98477.
- `PTZ/continuousPan`: FMeasure 0.08818, Event_F1 0.29060.
- `lowFramerate/tunnelExit_0_35fps`: FMeasure 0.09523, Event_F1 0.86585.
- `dynamicBackground/fall`: FMeasure 0.10964, Event_F1 0.13084.

## Decision

The full CDnet2014 dry-run is technically complete with 212/212 jobs and 0 failed jobs, but it is **not accepted as a clean Step 4 pass**.

Primary hold reason:

- `intermittentObjectMotion/parking` proposal is 0.51000, exceeding the revised protection-aware parking cap of 0.50000. Detector remains 0.00000 and unprotected FN is only 3, so the failure is narrow and safety/protection-oriented, but it still exceeds the frozen revised gate.

Additional review risks before any full live authorization:

- `thermal/lakeSide` unprotected FN 21.
- `badWeather/snowFall` unprotected FN 10.
- `intermittentObjectMotion/sofa` unprotected FN 10.
- `lowFramerate/port_0_17fps` detector rate 0.07000.
- PTZ and dynamicBackground contain low metric videos even without normal-frame proposal explosion.

Full CDnet live is **held**.

Recommended next step: review the Step 4 residual risks and decide whether to apply a narrow full-dataset parking/thermal/IOM/lowFramerate follow-up before re-running full CDnet dry-run. Do not run full live or cross-dataset validation until a clean Step 4 dry-run freeze is documented.

## Resume Command

The run completed. If re-auditing or resuming the same root is needed:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_full_2q2_dryrun.yaml --max-jobs-per-run 8
```
