# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2G Targeted Mini Dry-Run Report

Date: 2026-05-13

Status: targeted mini dry-run failed. Step 2 live remains held.

## Scope

This step evaluates the frozen 8C-2G smoke-live candidate on a small critical-video CDnet2014 set before any larger validation.

No live smoke, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was run.

Config:
- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2g_dryrun.yaml`

Output root:
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2g_dryrun/`

Compare root:
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2g_dryrun/`

## Commands

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2g_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2g_dryrun
```

The dry-run was resumed with the same dry-run command until all targeted jobs completed.

## Targeted Video List And Resolved Paths

The additional non-PTZ dynamicBackground video was resolved as `dynamicBackground/fountain01`.

| Category | Video | Resolved dataset path |
|---|---|---|
| `shadow` | `cubicle` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\shadow\cubicle` |
| `nightVideos` | `bridgeEntry` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\nightVideos\bridgeEntry` |
| `PTZ` | `continuousPan` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\PTZ\continuousPan` |
| `lowFramerate` | `tramCrossroad_1fps` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\lowFramerate\tramCrossroad_1fps` |
| `dynamicBackground` | `fountain02` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\dynamicBackground\fountain02` |
| `dynamicBackground` | `fountain01` | `D:\THS Programing\06.6 ASMAG Project\dataset cdnet2014\archive\dataset\dynamicBackground\fountain01` |

## Aggregate Dry-Run Metrics

Sources:
- `run_progress.csv`
- `summary_cdnet_metrics.csv`
- `summary_research_metrics.csv`
- `ai_intervention_2g_summary.csv`

| Metric | Value |
|---|---:|
| Completed jobs | 24/24 |
| Failed jobs | 0 |
| FMeasure | 0.14941 |
| Event_F1 | 0.56895 |
| Activation/proposed activation | 0.72000 |
| Avg_FPS | 21.37793 |
| P95 latency ms | 265.74483 |
| Proposed intervention rate | 0.22167 |
| Proposed detector request rate | 0.01500 |
| Block-only rate | 0.20667 |
| Event/foreground block-only rate | 0.17500 |
| Normal-frame proposed interventions | 0 |
| Guard alignment | 1.00000 |
| Cubicle proposed known-event recall | 0.71717 |
| Cubicle event FN | 18 |
| Cubicle proposed event FN | 11 |
| Cubicle unprotected event FN | 7 |
| bridgeEntry event FN | 0 |
| bridgeEntry detector budget max | 4 |
| continuousPan proposed intervention rate | 0.04000 |
| lowFramerate/tramCrossroad_1fps proposed intervention rate | 0.01000 |
| LowFramerate trim reclaimed proposals | 7 |

## Per-Video Metrics

| Video | Proposed intervention | Detector request | Normal-frame proposals | Known-event recall/protection | Event FN / unprotected FN | Detector budget max | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| `cubicle` | 0.71000 | 0.03000 | 0 | 0.71717 | 18 / 7 | 3 | Fails cubicle recall/protection gate; micro-bump frames remained 8 but only 1 event-FN frame was covered by micro-bump. |
| `bridgeEntry` | 0.17000 | 0.04000 | 0 | 0.17000 | 0 / 0 | 4 | bridgeEntry event FN stayed 0; detector budget stayed under smoke max. |
| `continuousPan` | 0.04000 | 0.01000 | 0 | 0.04000 | 0 / 0 | 1 | ContinuousPan stayed controlled below the preferred 0.05 cap. |
| `tramCrossroad_1fps` | 0.01000 | 0.00000 | 0 | 0.01010 | 0 / 0 | 0 | LowFramerate trim active; 7 proposals reclaimed, 1 preserved, 0 detector requests. |
| `fountain02` | 0.40000 | 0.01000 | 0 | 0.47059 | 0 / 0 | 1 | No normal-frame false interventions; normal-frame suppressor did not need final suppression here. |
| `fountain01` | 0.00000 | 0.00000 | 0 | 0.00000 | 0 / 0 | 0 | Additional dynamicBackground video stayed quiet, with no proposed interventions. |

## LowFramerate Trim Status

Source: `ai_intervention_2g_lowframerate_trim_summary.csv`.

| Metric | Value |
|---|---:|
| Target video | `lowFramerate/tramCrossroad_1fps` |
| Proposed intervention rate after trim | 0.01000 |
| Would-have-proposed frames before trim | 8 |
| Trim reclaimed proposals | 7 |
| Trim preserved count max | 1 |
| Event/foreground block-only frames after trim | 1 |
| Detector requests after trim | 0 |
| Normal-frame proposed interventions | 0 |

## Smoke Comparison

| Metric | 8C-2G smoke dry-run | 8C-2G smoke live | Targeted mini dry-run | Interpretation |
|---|---:|---:|---:|---|
| Proposed intervention rate | 0.31500 | 0.28125 | 0.22167 | Lower than both smoke references. |
| Proposed detector request rate | 0.03000 | 0.02875 | 0.01500 | Lower than both smoke references. |
| Normal-frame proposed interventions | 0 | 0 | 0 | Preserved. |
| Cubicle proposed known-event recall | 0.84848 | 0.82828 | 0.71717 | Regression below 0.80 gate. |
| Cubicle unprotected event FN | 0 | 0 | 7 | Material regression. |
| bridgeEntry event FN | 0 | 0 | 0 | Preserved. |
| bridgeEntry detector budget max | 8 | 2 | 4 | Under dry-run smoke max and within safety bound. |
| continuousPan proposed intervention rate | 0.05000 | 0.05000 | 0.04000 | Controlled. |
| lowFramerate/tramCrossroad_1fps proposed intervention rate | 0.02000 | 0.01000 | 0.01000 | Controlled. |
| LowFramerate trim reclaimed proposals | 7 | 7 | 7 | Preserved. |

## Gate Table

| Gate | Result |
|---|---|
| All targeted jobs complete with 0 failed | pass: 24/24 completed, 0 failed |
| Proposed detector request rate < 0.10 | pass: 0.01500 |
| Normal-frame proposed interventions = 0 or safely explained | pass: 0 |
| Cubicle recall/protection remains acceptable, preferred >= 0.80 | fail: 0.71717 |
| Cubicle unprotected event FN remains 0 or does not materially regress | fail: 7 versus 0 in smoke dry-run/live |
| bridgeEntry event FN remains 0 | pass: 0 |
| continuousPan proposed intervention remains controlled | pass: 0.04000 |
| tramCrossroad_1fps remains controlled by lowFramerate trim | pass: 0.01000, 7 trim reclaims |
| fountain02 does not recreate normal-frame false interventions | pass: 0 normal-frame proposals |
| No broad detector-heavy behavior | pass: detector request rate 0.01500 |
| No forbidden validation launched | pass |

## Root Cause And Risk Areas

The targeted mini dry-run fails because cubicle protection is not robust enough outside the smoke freeze replay:

- Cubicle known-event proposal recall dropped from 0.84848 in smoke dry-run and 0.82828 in smoke live to 0.71717.
- Cubicle unprotected event FN regressed from 0 in smoke dry-run/live to 7.
- The cubicle micro-bump remained active for 8 frames, but covered only 1 event-FN frame in this targeted run.
- Cubicle-like no-detector continuity remained active, but total cubicle proposed intervention rate fell from 0.84 in smoke dry-run to 0.71 here.

Primary risk: the exact cubicle protection path is too sensitive to event-continuity/micro-bump gating at targeted scope. Global pressure controls are healthy, but the cubicle safety path needs a narrow robustness bump before live mini-validation.

## Decision

8C-2G targeted mini dry-run does not pass.

Step 2 live is not recommended and remains held.

No larger validation should be launched from this result.

## Proposed Next Fix

Recommended next fix is a narrow 8C-2H cubicle-protection stability patch:

- Target only `cubicle` or exact cubicle-like context.
- Stay dry-run first.
- Preserve final normal-frame suppressor.
- Preserve lowFramerate trim.
- Do not increase detector request.
- Add a cubicle event-FN protection stabilizer that boosts no-detector proposals only when an exact cubicle event-memory/foreground-loss risk is present and the frame is not normal.
- Consider increasing exact-cubicle micro-bump protection from 8 to a slightly larger bounded cap or adding a second exact-cubicle event-FN rescue pass with cooldown.

Validation after the fix should rerun smoke dry-run and targeted mini dry-run before any live authorization.
