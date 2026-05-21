# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2E Budget Reclaim Report

## Pause / Resume Note - 2026-05-12 18:36:44 +07:00

Phase 8C-2E was paused after a lightweight filesystem and process check.

- Dry-run output folder: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun/`
- Dry-run progress file: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun/run_progress.csv`
- Dry-run current progress: 32 completed, 0 failed.
- Partial dry-run jobs needing rerun: none indicated by `run_progress.csv`.
- 2E dry-run config confirmed: `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun.yaml`
- 2E dry-run compare summary exists: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun/ai_intervention_2e_summary.csv`
- Process status: no 8C-2E experiment process remains running after pause handling.
- Note: a previously interrupted 2E live process was detected and stopped; no live compare was run during this pause step.

Resume command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun.yaml --max-jobs-per-run 8
```

Compare command, to run only after all 32 dry-run jobs complete:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun
```

Safety reminder: do not run live smoke unless the dry-run passes all gates. PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, and cross-dataset runs remain disallowed.

## Dry-Run Audit And Compare - 2026-05-13

This audit inspected the completed 8C-2E dry-run only and did not launch live smoke, PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, BMC, or cross-dataset validation.

### Live Folder Audit

Inspected:

```powershell
outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_live\
```

Result: the folder is not empty and is not merely a sparse placeholder. It contains completed live artifacts from the previously interrupted live command:

| Item | Result |
|---|---:|
| Top-level/live output status | populated |
| Recursive file count | 285 |
| Raw result job folders | 32 |
| `run_progress.csv` completed rows | 32 |
| `run_progress.csv` failed rows | 0 |

The folder includes `raw_results/`, `charts/`, `run_progress.csv`, `frame_runtime_log.csv`, `summary_*` files, and comparison CSVs. These artifacts are documented as accidental/unintended live artifacts. No files were deleted.

### Dry-Run Completion

Inspected:

```powershell
outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun\run_progress.csv
```

Result: 32/32 jobs completed, 0 failed jobs.

### Dry-Run Compare Command

Command run:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun
```

Result: completed successfully and wrote guarded comparison files under the 8C-2E dry-run root.

### Dry-Run Metrics

Source: `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2e_dryrun/ai_intervention_2e_summary.csv`.

| Metric | Value |
|---|---:|
| Completed jobs | 32 |
| Failed jobs | 0 |
| Proposed intervention rate | 0.32625 |
| Proposed detector request rate | 0.04000 |
| Block-only rate | 0.28625 |
| Event/foreground block-only rate | 0.25750 |
| Cubicle-like no-detector proposal rate | 0.04625 |
| Normal-frame proposed interventions | 2 |
| Guard alignment | 1.00000 |
| Cubicle proposed known-event recall | 0.75269 |
| Cubicle unprotected event FN | 0 |
| bridgeEntry event FN | 0 |
| bridgeEntry detector budget max | 8 |
| continuousPan proposed intervention rate | 0.04000 |
| Non-cubicle proposals reclaimed | 30 |
| Aggregate proposed intervention rate below 0.35 | yes |

### Pass/Fail Gates

| Gate | Value | Result |
|---|---:|---|
| Dry-run completion is 32/32 with 0 failed | 32/32, 0 failed | pass |
| Aggregate proposed intervention rate < 0.35 | 0.32625 | pass |
| Proposed detector request rate <= 0.10 | 0.04000 | pass |
| Guard alignment is 1.00000 | 1.00000 | pass |
| Cubicle proposed known-event recall >= 0.70 phase minimum | 0.75269 | pass |
| Cubicle proposed known-event recall >= 0.80 live target | 0.75269 | fail |
| Cubicle unprotected event FN is 0 | 0 | pass |
| bridgeEntry event FN is 0 | 0 | pass |
| bridgeEntry detector budget max <= 8 | 8 | pass |
| continuousPan proposed intervention rate <= 0.05 | 0.04000 | pass |
| Non-cubicle proposals reclaimed >= 18 | 30 | pass |
| Normal-frame proposed interventions remain 0 | 2 | fail |

All dry-run gates do not pass under the existing live target/normal-frame safety standard. The budget reclaim objective worked: aggregate proposed intervention rate dropped below 0.35 and 30 non-cubicle proposals were reclaimed. The remaining blockers are cubicle recall below the 0.80 live target and 2 normal-frame proposed interventions.

### Live Status And Recommendation

Live smoke was not intentionally run in this audit, and no live-root compare command was launched. The existing live output folder is populated with completed artifacts from the previously interrupted live command and should be treated as accidental/unintended live output for audit purposes.

Final recommendation: live remains held. Do not run live smoke next until cubicle recall reaches the live target and normal-frame proposed interventions are restored to zero or the gate is explicitly relaxed.
