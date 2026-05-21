# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2K PTZ/intermittentPan Report

Date: 2026-05-14

Status: PASS for the 8C-2K targeted category dry-run gates. Live remains held.

Phase 8C-2K adds a narrow `PTZ/intermittentPan` stabilization path on top of 8C-2J:

- cap generic PTZ proposal pressure on exactly `PTZ/intermittentPan`;
- add a no-detector rescue for localized intermittentPan event-FN risk;
- preserve all 8C-2J policy settings and core carry-over guards.

No live, live compare, full CDnet, PTZ-targeted standalone, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## Files

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2k_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2k_dryrun/`
- Created/updated report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2K_PTZ_INTERMITTENTPAN_REPORT.md`
- Updated status: `docs/DAILY_STATUS.md`
- Changed controller: `src/run_experiment.py`
- Changed compare reporting: `tools/compare_asmag_tr_controller_online_guarded.py`

## Video Resolution

All requested videos were present locally. No replacements were used.

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

## Validation

Compile:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Result: PASS.

Targeted category dry-run:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2k_dryrun.yaml --max-jobs-per-run 8
```

Resumed until all 80 jobs completed.

Compare:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2k_dryrun
```

Result files were written under `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2k_dryrun/`.

## Aggregate Metrics

- Jobs: 80/80 completed, 0 failed.
- Video count: 20.
- Category count: 9.
- FMeasure: 0.38702.
- Event_F1: 0.66234.
- Activation: 0.39278.
- Avg_FPS: 23.75311.
- P95 latency: 452.27077 ms.
- Proposed intervention rate: 0.24216.
- Proposed detector request rate: 0.02679.
- Block-only rate: 0.21537.
- Event/foreground block-only rate: 0.18605.
- Normal-frame proposed interventions: 0.
- Guard alignment: 1.00000.
- Exact-cubicle late-event rescue count: 4.
- Exact-cubicle no-detector rescue count: 4.

## PTZ/intermittentPan Result

| Metric | 8C-2J Step 3 | 8C-2K |
|---|---:|---:|
| Proposal rate | 0.30000 | 0.12000 |
| Detector request rate | 0.06000 | 0.00000 |
| Event FN | 10 | 11 |
| Unprotected event FN | 2 | 0 |
| Cap reclaimed count | n/a | 26 |
| Cap preserved count | n/a | 12 |
| FN rescue count | n/a | 3 |
| FN rescue no-detector count | n/a | 3 |
| Normal-frame proposals | 0 | 0 |

The 2K cap reduced `PTZ/intermittentPan` proposal pressure below the 0.15 hard gate and removed detector requests from the target video. The no-detector rescue covered the remaining unprotected-FN gap: 11/11 event-FN frames were protected, with 0 unprotected FNs.

One rescue frame was categorized by the reason logs as `localized_event_fn_risk` plus active memory and localized foreground/event risk under global motion rather than an unsafe empty/fallback action. It remained no-detector and inside the cap.

## Category Summary

| Category | Videos | Proposal rate | Detector rate | Normal proposals | Event FN | Unprotected FN | FMeasure | Event_F1 | Risk notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| PTZ | 2 | 0.08500 | 0.00500 | 0 | 11 | 0 | 0.11305 | 0.53197 | `intermittentPan` now capped; `continuousPan` unchanged at gate. |
| baseline | 2 | 0.18500 | 0.05500 | 0 | 3 | 1 | 0.82580 | 0.98718 | `office` proposal 0.32000 and detector 0.10000 need review before live. |
| cameraJitter | 1 | 0.02000 | 0.00000 | 0 | 0 | 0 | 0.55114 | 0.84393 | No spike. |
| dynamicBackground | 4 | 0.21164 | 0.04497 | 0 | 1 | 0 | 0.26979 | 0.44060 | `fountain01` quiet; `overpass`/`fountain02` remain proposal-pressure monitors. |
| intermittentObjectMotion | 1 | 0.40000 | 0.00000 | 0 | 33 | 18 | 0.46711 | 0.51923 | `parking` remains a next-risk video. |
| lowFramerate | 3 | 0.15333 | 0.01000 | 0 | 11 | 9 | 0.42420 | 0.71895 | `tunnelExit_0_35fps` remains high proposal/FN risk; `tramCrossroad_1fps` remains controlled for proposal/detector. |
| nightVideos | 3 | 0.18333 | 0.03333 | 0 | 0 | 0 | 0.31710 | 0.90043 | `bridgeEntry` event FN remains 0. |
| shadow | 3 | 0.55667 | 0.02333 | 0 | 60 | 21 | 0.29050 | 0.48573 | `cubicle` protected; `copyMachine` remains a next-risk video. |
| turbulence | 1 | 0.35000 | 0.04000 | 0 | 3 | 3 | 0.66986 | 0.76768 | `turbulence2` remains a next-risk video. |

## Per-Video Risk Summary

| Video | Proposal | Detector | Normal proposals | Event FN | Unprotected FN | Detector budget max | Special guard activations | Status |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 | 0 | 1 | continuousPan cap preserved | PASS |
| `PTZ/intermittentPan` | 0.12000 | 0.00000 | 0 | 11 | 0 | 0 | cap rejected 26; rescue 3, all no-detector | PASS |
| `shadow/cubicle` | 0.87000 | 0.02000 | 0 | 14 | 0 | 2 | micro-bump 8; stabilizer 2; late rescue 4 | PASS |
| `nightVideos/bridgeEntry` | 0.24000 | 0.05000 | 0 | 0 | 0 | 5 | bridgeEntry event protection retained | PASS |
| `lowFramerate/tramCrossroad_1fps` | 0.00000 | 0.00000 | 0 | 6 | 6 | 0 | retighten reclaimed 40; trim reclaimed 25 | PASS for 2K gate; event FN risk remains observational |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | quiet guard reclaimed 91 | PASS |
| `dynamicBackground/fountain02` | 0.40000 | 0.08000 | 0 | 1 | 0 | 8 | normal-frame false interventions 0 | PASS for carry-over gate; proposal pressure monitor |
| `shadow/backdoor` | 0.40000 | 0.04000 | 0 | 0 | 0 | 4 | no target 2K guard | PASS for normal-frame gate; pressure monitor |
| `shadow/copyMachine` | 0.40000 | 0.01000 | 0 | 46 | 21 | 1 | no target 2K guard | REMAINING RISK |
| `dynamicBackground/overpass` | 0.40000 | 0.09000 | 0 | 0 | 0 | 9 | no target 2K guard | pressure monitor |
| `dynamicBackground/canoe` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | no target 2K guard | PASS |
| `lowFramerate/tunnelExit_0_35fps` | 0.39000 | 0.02000 | 0 | 5 | 3 | 2 | no target retighten for this video | REMAINING RISK |
| `lowFramerate/turnpike_0_5fps` | 0.07000 | 0.01000 | 0 | 0 | 0 | 1 | no target 2K guard | PASS |
| `nightVideos/tramStation` | 0.22000 | 0.04000 | 0 | 0 | 0 | 4 | no target 2K guard | PASS |
| `nightVideos/streetCornerAtNight` | 0.09000 | 0.01000 | 0 | 0 | 0 | 1 | no target 2K guard | PASS |
| `cameraJitter/traffic` | 0.02000 | 0.00000 | 0 | 0 | 0 | 0 | no target 2K guard | PASS |
| `intermittentObjectMotion/parking` | 0.40000 | 0.00000 | 0 | 33 | 18 | 0 | no target 2K guard | REMAINING RISK |
| `baseline/highway` | 0.05000 | 0.01000 | 0 | 1 | 1 | 1 | no target 2K guard | monitor |
| `baseline/office` | 0.32000 | 0.10000 | 0 | 2 | 0 | 10 | no target 2K guard | detector/proposal monitor |
| `turbulence/turbulence2` | 0.35000 | 0.04000 | 0 | 3 | 3 | 4 | no target 2K guard | REMAINING RISK |

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| Jobs complete | 80/80, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.02679 | PASS |
| Aggregate normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| `shadow/cubicle` recall >= 0.80 and unprotected FN = 0 | 0.87879, 0 | PASS |
| `nightVideos/bridgeEntry` event FN = 0 | 0 | PASS |
| `PTZ/continuousPan` proposal <= 0.05 | 0.05000 | PASS |
| `lowFramerate/tramCrossroad_1fps` proposal <= 0.05 and detector <= 0.02 | 0.00000, 0.00000 | PASS |
| `dynamicBackground/fountain01` proposal <= 0.05 and detector <= 0.02 | 0.00000, 0.00000 | PASS |
| `dynamicBackground/fountain02` normal-frame false interventions = 0 | 0 | PASS |
| `PTZ/intermittentPan` proposal <= 0.15 | 0.12000 | PASS |
| `PTZ/intermittentPan` detector <= 0.02 preferred, hard fail if > 0.05 | 0.00000 | PASS |
| `PTZ/intermittentPan` unprotected FN improves, preferred 0 | 0 | PASS |
| No forbidden validation launched | dry-run and dry-run compare only | PASS |

## Conclusion

8C-2K passes the requested targeted category dry-run gates. The targeted PTZ issue is fixed: `PTZ/intermittentPan` proposal rate dropped from 0.30000 to 0.12000, detector request rate dropped from 0.06000 to 0.00000, and unprotected event FNs dropped from 2 to 0.

Live remains held. Because `intermittentObjectMotion/parking`, `shadow/copyMachine`, `turbulence/turbulence2`, and `lowFramerate/tunnelExit_0_35fps` remain documented risk videos, the recommended next step is another narrow dry-run patch or review pass for those remaining risks before any Step 3B targeted category live authorization.
