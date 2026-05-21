# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2F Normal Cleanup Report

## Scope

Phase 8C-2F adds a final normal-frame proposal suppressor and a narrow cubicle-only no-detector micro-bump path on top of 8C-2E.

Safety scope was preserved:
- No live smoke was run.
- No live compare was run.
- The accidental 8C-2E live artifacts under `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_live/` were left untouched.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset run was launched.
- Default guarded behavior remains unchanged; the default guarded config still keeps `ai_intervention_enabled: false`.

## Files Changed Or Created

Created:
- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_live.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_live/`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2F_NORMAL_CLEANUP_REPORT.md`

Changed:
- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`

## Implementation Summary

Added final normal-frame suppressor config and logs:
- `ai_final_normal_frame_suppressor_enabled`
- `ai_final_normal_frame_suppressor_active`
- `ai_final_normal_frame_suppressor_reason`
- `ai_final_normal_frame_suppressed_path`
- `ai_final_normal_frame_suppressed_video`
- `ai_final_normal_frame_suppressed_frame`

Added cubicle micro-bump config and logs:
- `ai_cubicle_micro_bump_enabled`
- `ai_cubicle_micro_bump_score_threshold`
- `ai_cubicle_micro_bump_requires_active_memory`
- `ai_cubicle_micro_bump_requires_not_normal_frame`
- `ai_cubicle_micro_bump_allow_detector`
- `ai_cubicle_micro_bump_extra_cap_per_video`
- `ai_cubicle_micro_bump_cooldown`
- `ai_cubicle_micro_bump_active`
- `ai_cubicle_micro_bump_reason`
- `ai_cubicle_micro_bump_no_detector`
- `ai_cubicle_micro_bump_cap_used`
- `ai_cubicle_micro_bump_rejected_reason`

Updated compare outputs:
- `ai_intervention_2f_summary.csv`
- `ai_intervention_2f_video_summary.csv`
- `ai_intervention_2f_event_foreground_summary.csv`
- `ai_intervention_2f_cubicle_like_summary.csv`
- `ai_intervention_2f_budget_reclaim_summary.csv`
- `ai_intervention_2f_normal_frame_suppression_summary.csv`

`ai_intervention_2f_dryrun_vs_live.csv` was not written because no 2F live run exists.

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_dryrun
```

The dry-run was resumed until all jobs completed.

## Prior 8C-2E Normal-Frame Proposal Diagnostic

Source: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_dryrun/ai_intervention_2f_normal_frame_suppression_summary.csv`.

| Phase | Video | Frame | Action | Event state | Proposal type | Reason |
|---|---|---:|---|---|---|---|
| 8C-2E prior | dynamicBackground/fountain02 | 850 | CLOSED_EMPTY_ACC | TN | block_closed_empty | event_foreground_risk+foreground_loss_risk+event_continuity_risk+foreground_risk; budget reclaim already satisfied |
| 8C-2E prior | dynamicBackground/fountain02 | 855 | CLOSED_EMPTY_ACC | TN | block_closed_empty | event_foreground_risk+foreground_loss_risk+event_continuity_risk+foreground_risk; budget reclaim already satisfied |

## Dry-Run Metrics

Source: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2f_dryrun/ai_intervention_2f_summary.csv`.

| Metric | 8C-2E | 8C-2F | Delta |
|---|---:|---:|---:|
| Completed jobs | 32 | 32 | 0 |
| Failed jobs | 0 | 0 | 0 |
| Proposed intervention rate | 0.32625 | 0.35375 | +0.02750 |
| Proposed detector request rate | 0.04000 | 0.04125 | +0.00125 |
| Block-only rate | 0.28625 | 0.31250 | +0.02625 |
| Event/foreground block-only rate | 0.25750 | 0.26625 | +0.00875 |
| Cubicle-like no-detector proposal rate | 0.04625 | 0.05375 | +0.00750 |
| Normal-frame proposed interventions | 2 | 0 | -2 |
| Guard alignment | 1.00000 | 1.00000 | 0 |
| Cubicle proposed known-event recall | 0.75269 | 0.84848 | +0.09580 |
| Cubicle unprotected event FN | 0 | 0 | 0 |
| bridgeEntry event FN | 0 | 0 | 0 |
| bridgeEntry detector budget max | 8 | 7 | -1 |
| continuousPan proposed intervention rate | 0.04000 | 0.05000 | +0.01000 |
| Non-cubicle proposals reclaimed | 30 | 30 | 0 |
| Cubicle micro-bump frames | 0 | 8 | +8 |
| Final normal-frame suppressed frames | 0 | 0 | 0 |

## Gate Table

| Gate | 8C-2F value | Result |
|---|---:|---|
| 32/32 completed, 0 failed | 32/32, 0 failed | pass |
| Proposed intervention rate < 0.35 | 0.35375 | fail |
| Proposed detector request rate < 0.10 | 0.04125 | pass |
| Normal-frame proposed interventions = 0 | 0 | pass |
| Guard alignment >= 0.95 | 1.00000 | pass |
| Cubicle proposed known-event recall >= 0.80 preferred | 0.84848 | pass |
| Cubicle unprotected event FN remains 0 | 0 | pass |
| bridgeEntry event FN remains 0 | 0 | pass |
| bridgeEntry detector budget max <= 8 | 7 | pass |
| continuousPan proposed intervention <= 0.05 | 0.05000 | pass |
| No forbidden validation launched | yes | pass |

## Root Cause

8C-2F fixes both intended local blockers: normal-frame proposed interventions drop from 2 to 0, and cubicle recall rises from 0.75269 to 0.84848. However, the dry-run fails because aggregate proposed intervention rate is 0.35375, four proposed frames above the strict `< 0.35` ceiling for an 800-frame smoke set.

The increase is not detector-driven; detector request rate remains low at 0.04125. The overrun comes from extra block-only proposals. The cubicle micro-bump adds 8 cubicle no-detector frames as intended, while the dry-run also shows broader non-cubicle event/foreground proposal pressure, especially `lowFramerate/tramCrossroad_1fps` increasing from 0.08 in 8C-2E to 0.33 in 8C-2F.

## Recommendation

Live remains held.

Next fix: keep the normal-frame cleanup and cubicle micro-bump, then reclaim at least 4 additional non-cubicle event/foreground block-only proposals. The most direct target is to tighten lowFramerate/tramCrossroad_1fps preservation or raise the non-cubicle reclaim target while preserving bridgeEntry and continuousPan guardrails.
