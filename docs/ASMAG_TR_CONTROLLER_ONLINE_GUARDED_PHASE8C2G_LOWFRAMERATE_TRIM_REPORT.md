# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2G LowFramerate Trim Report

## Scope

Phase 8C-2G adds a narrow non-cubicle lowFramerate trim layer on top of 8C-2F. It targets only `lowFramerate/tramCrossroad_1fps` and preserves the 8C-2F final normal-frame suppressor and cubicle micro-bump.

Safety scope was preserved:
- No live smoke was run.
- No live compare was run.
- The accidental 8C-2E live artifacts were left untouched.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- Default guarded behavior remains unchanged; the default guarded config still keeps `ai_intervention_enabled: false`.

## Files Changed Or Created

Created:
- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2G_LOWFRAMERATE_TRIM_REPORT.md`

Changed:
- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`
- `docs/DAILY_STATUS.md`

## Implementation Summary

Added 2G config and logs:
- `ai_lowframerate_trim_enabled`
- `ai_lowframerate_trim_target_videos`
- `ai_lowframerate_trim_max_proposal_rate`
- `ai_lowframerate_trim_require_event_memory`
- `ai_lowframerate_trim_require_not_normal_frame`
- `ai_lowframerate_trim_require_unprotected_fn_risk`
- `ai_lowframerate_trim_min_score`
- `ai_lowframerate_trim_no_detector`
- `ai_lowframerate_trim_preserve_existing_deterministic_emergency`
- `ai_lowframerate_trim_active`
- `ai_lowframerate_trim_rejected`
- `ai_lowframerate_trim_reason`
- `ai_lowframerate_trim_video`
- `ai_lowframerate_trim_frame`
- `ai_lowframerate_trim_would_have_proposed_before_trim`
- `ai_lowframerate_trim_reclaimed_count`
- `ai_lowframerate_trim_preserved_count`

Updated compare outputs:
- `ai_intervention_2g_summary.csv`
- `ai_intervention_2g_video_summary.csv`
- `ai_intervention_2g_event_foreground_summary.csv`
- `ai_intervention_2g_cubicle_like_summary.csv`
- `ai_intervention_2g_budget_reclaim_summary.csv`
- `ai_intervention_2g_normal_frame_suppression_summary.csv`
- `ai_intervention_2g_lowframerate_trim_summary.csv`

`ai_intervention_2g_dryrun_vs_live.csv` was not written because no 2G live run exists.

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun
```

The dry-run was resumed until all 32 jobs completed.

## Dry-Run Metrics

Source: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun/ai_intervention_2g_summary.csv`.

| Metric | 8C-2F | 8C-2G | Delta |
|---|---:|---:|---:|
| Completed jobs | 32 | 32 | 0 |
| Failed jobs | 0 | 0 | 0 |
| Proposed intervention rate | 0.35375 | 0.31500 | -0.03875 |
| Proposed detector request rate | 0.04125 | 0.03000 | -0.01125 |
| Block-only rate | 0.31250 | 0.28500 | -0.02750 |
| Event/foreground block-only rate | 0.26625 | 0.23875 | -0.02750 |
| Cubicle-like no-detector proposal rate | 0.05375 | 0.05375 | 0 |
| Normal-frame proposed interventions | 0 | 0 | 0 |
| Guard alignment | 1.00000 | 1.00000 | 0 |
| Cubicle proposed known-event recall | 0.84848 | 0.84848 | 0 |
| Cubicle unprotected event FN | 0 | 0 | 0 |
| bridgeEntry event FN | 0 | 0 | 0 |
| bridgeEntry detector budget max | 7 | 8 | +1 |
| continuousPan proposed intervention rate | 0.05000 | 0.05000 | 0 |
| Non-cubicle proposals reclaimed | 30 | 30 | 0 |
| Cubicle micro-bump frames | 8 | 8 | 0 |
| LowFramerate trim reclaimed proposals | 0 | 7 | +7 |
| LowFramerate/tramCrossroad_1fps proposed intervention rate | 0.33000 | 0.02000 | -0.31000 |

## LowFramerate Trim Detail

Source: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_dryrun/ai_intervention_2g_lowframerate_trim_summary.csv`.

| Metric | Value |
|---|---:|
| Target video | `lowFramerate/tramCrossroad_1fps` |
| Proposed intervention rate after trim | 0.02000 |
| Would-have-proposed frames entering trim scope | 9 |
| Direct trim reclaimed proposals | 7 |
| Trim preserved count max | 2 |
| Event/foreground block-only frames after trim | 1 |
| Detector requests after trim | 0 |
| Normal-frame proposed interventions | 0 |

The direct trim log shows 7 reclaimed generic lowFramerate proposals. Net against 8C-2F, the target video's proposed interventions dropped from 33 frames to 2 frames.

## Gate Table

| Gate | 8C-2G value | Result |
|---|---:|---|
| 32/32 completed, 0 failed | 32/32, 0 failed | pass |
| Proposed intervention rate < 0.35 | 0.31500 | pass |
| Proposed detector request rate < 0.10 | 0.03000 | pass |
| Normal-frame proposed interventions = 0 | 0 | pass |
| Guard alignment >= 0.95 | 1.00000 | pass |
| Cubicle proposed known-event recall >= 0.80 | 0.84848 | pass |
| Cubicle unprotected event FN remains 0 | 0 | pass |
| bridgeEntry event FN remains 0 | 0 | pass |
| bridgeEntry detector budget max <= 8 | 8 | pass |
| continuousPan proposed intervention <= 0.05 | 0.05000 | pass |
| lowFramerate/tramCrossroad_1fps proposed intervention rate <= 0.15 | 0.02000 | pass |
| At least 4 non-cubicle proposals reclaimed vs 8C-2F | 7 direct trim reclaims | pass |
| No forbidden validation launched | yes | pass |

## Recommendation

8C-2G passes the dry-run gate. Live remains held in this phase until explicitly authorized; no live command was launched here.

## Official Live Smoke - 2026-05-13

Pre-run checks:
- The 8C-2G dry-run report stated that 8C-2G passed the dry-run gate.
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live/` was empty before the official live smoke and was safe to write.
- Accidental 8C-2E live artifacts in `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_live/` were not used and were left untouched.

Official live command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live.yaml --max-jobs-per-run 8
```

Official live compare command:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2g_live
```

The live smoke was resumed with the same official live command until all 32 jobs completed.

## Official Live Metrics

| Metric | Live value |
|---|---:|
| Completed jobs | 32 |
| Failed jobs | 0 |
| FMeasure | 0.19806 |
| Event_F1 | 0.55372 |
| Activation | 0.61125 |
| Avg_FPS | 25.35154 |
| P95 latency ms | 242.01526 |
| Detector request rate | 0.02875 |
| Proposed intervention rate | 0.28125 |
| Block-only rate | 0.25250 |
| Event/foreground block-only rate | 0.20500 |
| Normal-frame interventions | 0 |
| Guard alignment | 1.00000 |
| Cubicle proposed known-event recall | 0.82828 |
| Cubicle unprotected event FN | 0 |
| bridgeEntry event FN | 0 |
| bridgeEntry detector budget max | 2 |
| continuousPan proposed intervention rate | 0.05000 |
| LowFramerate/tramCrossroad_1fps proposed intervention rate | 0.01000 |
| LowFramerate trim reclaimed proposals | 7 |

## Dry-Run Vs Live

| Metric | Dry-run | Live | Delta |
|---|---:|---:|---:|
| FMeasure | 0.18742 | 0.19806 | +0.01064 |
| Event_F1 | 0.59213 | 0.55372 | -0.03841 |
| Activation | 0.54625 | 0.61125 | +0.06500 |
| Avg_FPS | 16.22514 | 25.35154 | +9.12640 |
| P95 latency ms | 426.21586 | 242.01526 | -184.20060 |
| Proposed intervention rate | 0.31500 | 0.28125 | -0.03375 |
| Proposed detector request rate | 0.03000 | 0.02875 | -0.00125 |
| Block-only rate | 0.28500 | 0.25250 | -0.03250 |
| Event/foreground block-only rate | 0.23875 | 0.20500 | -0.03375 |
| Cubicle-like proposal rate | 0.05375 | 0.06125 | +0.00750 |
| Normal-frame proposed interventions | 0 | 0 | 0 |
| Cubicle proposed known-event recall | 0.84848 | 0.82828 | -0.02020 |
| Cubicle unprotected event FN | 0 | 0 | 0 |
| bridgeEntry detector budget max | 8 | 2 | -6 |
| continuousPan proposed intervention rate | 0.05000 | 0.05000 | 0 |
| Non-cubicle reclaimed proposals | 30 | 30 | 0 |
| Cubicle micro-bump frames | 8 | 8 | 0 |
| LowFramerate trim reclaimed proposals | 7 | 7 | 0 |
| LowFramerate/tramCrossroad_1fps proposed intervention rate | 0.02000 | 0.01000 | -0.01000 |
| Guard alignment | 1.00000 | 1.00000 | 0 |

## Live Assessment

The official 8C-2G live smoke matches the dry-run proposal expectations on the guarded safety gates: intervention pressure is lower than dry-run, detector request rate does not increase, normal-frame interventions remain 0, cubicle recall stays above 0.80, cubicle unprotected event FN remains 0, bridgeEntry event FN remains 0, and continuousPan stays at the 0.05 intervention cap.

8C-2G passes official live smoke. No larger validation was launched.

Safety confirmation:
- Accidental 8C-2E live artifacts were not used and were left untouched.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
