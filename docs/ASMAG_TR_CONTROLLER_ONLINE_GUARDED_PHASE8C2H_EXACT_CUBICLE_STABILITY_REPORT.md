# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2H Exact-Cubicle Stability Report

Date: 2026-05-13

Status: smoke dry-run failed. Targeted mini dry-run was not launched. Live remains held.

## Scope

Phase 8C-2H adds a narrow exact-cubicle no-detector event-FN stabilizer on top of the frozen 8C-2G policy.

No live smoke, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was run.

Default guarded behavior remains unchanged: the default guarded config still keeps `ai_intervention_enabled: false`. The accidental 8C-2E live artifacts were not touched or used.

## Files

Configs:
- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2h_dryrun.yaml`

Output roots:
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2h_dryrun/`

Code updates:
- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun
```

The smoke dry-run command was resumed with the same command until all 32 smoke jobs completed.

The targeted mini dry-run command was not run because the smoke gate failed.

## Smoke Dry-Run Metrics

Sources:
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun/run_progress.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun/ai_intervention_2h_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun/ai_intervention_2h_video_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2h_dryrun/ai_intervention_2h_exact_cubicle_stabilizer_summary.csv`

| Metric | Value |
|---|---:|
| Completed jobs | 32/32 |
| Failed jobs | 0 |
| Proposed intervention rate | 0.30875 |
| Proposed detector request rate | 0.02875 |
| Block-only rate | 0.28000 |
| Event/foreground block-only rate | 0.23875 |
| Normal-frame proposed interventions | 0 |
| Guard alignment | 1.00000 |
| Cubicle proposed known-event recall | 0.81818 |
| Cubicle event FN | 14 |
| Cubicle proposed event FN | 12 |
| Cubicle unprotected event FN | 2 |
| bridgeEntry event FN | 0 |
| bridgeEntry detector budget max | 5 |
| continuousPan proposed intervention rate | 0.05000 |
| lowFramerate/tramCrossroad_1fps proposed intervention rate | 0.02000 |
| LowFramerate trim reclaimed proposals | 7 |
| Exact-cubicle stabilizer active frames | 0 |
| Exact-cubicle stabilizer event-FN covered | 0 |

## Smoke Gate Table

| Gate | Result |
|---|---|
| 32/32 completed, 0 failed | pass |
| Proposed intervention rate < 0.35 | pass: 0.30875 |
| Proposed detector request rate < 0.10 | pass: 0.02875 |
| Normal-frame proposed interventions = 0 | pass |
| Guard alignment >= 0.95 | pass: 1.00000 |
| Cubicle recall >= 0.80 | pass: 0.81818 |
| Cubicle unprotected event FN = 0 | fail: 2 |
| bridgeEntry event FN = 0 | pass |
| bridgeEntry detector budget max <= 8 | pass: 5 |
| continuousPan proposal rate <= 0.05 | pass: 0.05000 |
| lowFramerate trim still active and controlled | pass: 0.02000, 7 trim reclaims |
| No forbidden validation launched | pass |

## Root Cause

8C-2H failed the smoke gate because the exact-cubicle stabilizer did not activate on the two remaining cubicle FN frames:

| Video | Frame | Event state | Action | Foreground risk | Recent-event memory |
|---|---:|---|---|---:|---:|
| `shadow/cubicle` | 1340 | FN | `CLOSED_EMPTY_ACC` | 1.00000 | 9 |
| `shadow/cubicle` | 1345 | FN | `CLOSED_EMPTY_ACC` | 1.00000 | 10 |

The implementation added the stabilizer after the early normal-frame suppressor. These two frames were exact-cubicle, guarded, high foreground-risk, and recent-event-memory frames, but they returned before reaching the stabilizer path. That left cubicle unprotected event FN at 2.

The compare log confirms `ai_exact_cubicle_event_fn_stabilizer_active` stayed at 0 frames in smoke.

## Targeted Mini Status

Targeted mini dry-run was not run.

Reason: smoke dry-run failed the cubicle unprotected-FN gate, and the validation rule requires stopping before targeted mini when smoke fails.

## Comparison Against 8C-2G

| Metric | 8C-2G smoke dry-run | 8C-2H smoke dry-run | Result |
|---|---:|---:|---|
| Proposed intervention rate | 0.31500 | 0.30875 | lower |
| Proposed detector request rate | 0.03000 | 0.02875 | lower |
| Normal-frame proposed interventions | 0 | 0 | preserved |
| Cubicle recall | 0.84848 | 0.81818 | regressed but still above 0.80 |
| Cubicle unprotected event FN | 0 | 2 | regressed; gate fail |
| bridgeEntry event FN | 0 | 0 | preserved |
| bridgeEntry detector budget max | 8 | 5 | improved |
| continuousPan proposal rate | 0.05000 | 0.05000 | preserved |
| tramCrossroad_1fps proposal rate | 0.02000 | 0.02000 | preserved |
| LowFramerate trim reclaimed proposals | 7 | 7 | preserved |

## Next Fix

Do not run live.

The next 8C-2H fix should move or exempt the exact-cubicle stabilizer so exact-cubicle stabilizer pre-signal frames are not returned by the early normal-frame suppressor. The final normal-frame suppressor should still remain in place after all AI proposal paths.

After that code fix, rerun smoke dry-run first. Run targeted mini dry-run only if smoke returns cubicle unprotected event FN to 0 and preserves the rest of the smoke gates.

## Decision

8C-2H does not pass smoke dry-run.

Targeted mini dry-run remains held.

Live remains held.
