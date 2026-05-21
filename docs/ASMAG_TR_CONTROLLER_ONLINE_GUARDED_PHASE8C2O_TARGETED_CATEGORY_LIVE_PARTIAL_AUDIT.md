# ASMAG-TRC Phase 8C-2O Targeted Category Live Partial Audit

Date: 2026-05-15

## Scope

This audit covers Step 3B-PARTIAL-AUDIT only.

No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was run during this audit. No partial 8C-2O live artifacts were deleted or overwritten. Accidental 8C-2E live artifacts were not used or modified.

## Observed Partial State

| Item | Observation |
|---|---|
| Live config | `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live.yaml` exists |
| Live config role | Overlay on `asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun.yaml` with `online_controller_guarded.ai_intervention_dry_run: false` |
| Output root | `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live/` |
| `run_progress.csv` | Exists |
| Total jobs | 80 |
| Completed jobs | 68 |
| Running jobs | 1 |
| Pending jobs | 11 |
| Failed jobs | 0 |
| Latest modified files | `live_progress.md`, `live_progress.json`, and `run_progress.csv` at `2026-05-15 15:44:34` |
| Current local audit time | `2026-05-15 19:09:47 +07:00` |
| Active file change check | Static across an 8-second snapshot |

## Running Job

| Field | Value |
|---|---|
| Job ID | `baseline/highway/P3_MOG2` |
| Status | `running` |
| Frames expected | 100 |
| Frames done | 1 |
| Progress | 1.0% |
| Started at | `2026-05-15T15:44:32` |
| Updated at | `2026-05-15T15:44:34` |
| Output path | `outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live\raw_results\baseline\highway\P3_MOG2` |
| Observed contents | `masks/` directory only; no completed sequence summary files yet |

## Pending Jobs

| Job ID |
|---|
| `baseline/highway/ASMAG_TR_CONTROLLER` |
| `baseline/highway/ONLINE_CALIBRATED` |
| `baseline/highway/ASMAG_TR_CONTROLLER_ONLINE_GUARDED` |
| `baseline/office/P3_MOG2` |
| `baseline/office/ASMAG_TR_CONTROLLER` |
| `baseline/office/ONLINE_CALIBRATED` |
| `baseline/office/ASMAG_TR_CONTROLLER_ONLINE_GUARDED` |
| `turbulence/turbulence2/P3_MOG2` |
| `turbulence/turbulence2/ASMAG_TR_CONTROLLER` |
| `turbulence/turbulence2/ONLINE_CALIBRATED` |
| `turbulence/turbulence2/ASMAG_TR_CONTROLLER_ONLINE_GUARDED` |

## Process Audit

| Check | Result |
|---|---|
| `tasklist /FI "IMAGENAME eq python.exe" /V` | Access denied |
| `tasklist /FI "IMAGENAME eq pythonw.exe" /V` | Access denied |
| `Get-Process python -ErrorAction SilentlyContinue` | No visible rows returned |
| `Get-Process pythonw -ErrorAction SilentlyContinue` | No visible rows returned |
| `wmic.exe process where "name='python.exe'" get ProcessId,CommandLine,CreationDate` | Failed with `process - Alias not found.` |
| `wmic.exe process where "name='pythonw.exe'" get ProcessId,CommandLine,CreationDate` | Failed with `process - Alias not found.` |

Decision: the recorded running job is stale by best available evidence. The decisive signals are the old/static output timestamps, unchanged latest files across the snapshot, and no visible Python process from `Get-Process`. This is not an active live validation confirmation because `tasklist` and `wmic` were unavailable or denied, but no evidence of an active runner was found.

## Resume Safety Assessment

| Check | Assessment |
|---|---|
| Runner skips completed jobs | Yes. `src/run_experiment.py` checks `run_progress.csv` and skips rows whose status is `completed`. |
| Runner handles stale running rows | Yes. `initialize_run_progress` auto-recovers stale `running` jobs to `pending` when no external runner is found or the row exceeds the stale threshold. |
| Completed rows have raw result folders | Yes. All 68 completed rows have output directories. |
| Completed rows have required summary files | Yes. All 68 completed rows have `sequence_event_summary.csv`, `sequence_pixel_summary.csv`, `sequence_edge_summary.csv`, and `sequence_object_summary.csv`. |
| Running partial job output | Incomplete but expected for an interrupted job: only `masks/` was observed under `baseline/highway/P3_MOG2`. |
| Lock/temp/pid files | None found under the 2O live output root. |
| Corruption signs | No completed-job corruption found. The only incomplete artifact is the stale running job. |

## Recommended Next Action

Safe resume is recommended after explicit authorization, using the same live command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live.yaml --max-jobs-per-run 8
```

Do not run live compare until all 80 jobs complete with 0 failed. Full CDnet, full CDnet compare, cross-dataset validation, and PTZ-targeted standalone validation remain held.

## Resume Outcome

After explicit authorization, the existing partial live folder was resumed with the same command:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live.yaml --max-jobs-per-run 8
```

Resume outcome:

| Item | Result |
|---|---|
| Output root | `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live/` |
| Stale row recovery | `baseline/highway/P3_MOG2` was auto-recovered from stale `running` to pending and rerun |
| Final live progress | 80 completed, 0 pending, 0 running, 0 failed |
| Completed raw jobs overwritten | No evidence found; completed rows were skipped by the runner and the same partial folder was reused |
| Live compare | Completed and wrote comparison files under the same root |
| Forbidden validation | No full CDnet, full CDnet compare, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched |

The resumed live run completed technically, but the official Step 3B live gates failed:

| Gate | Live Result | Status |
|---|---|---|
| Cubicle recall >= 0.80 and unprotected FN = 0 | recall 0.81818, unprotected FN 1 | Fail |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | proposal 0.05000, unprotected FN 2 | Fail |
| CopyMachine unprotected FN <= 15 | 18 | Fail |
| Parking proposal <= 0.45 and unprotected FN <= 12 | proposal 0.43000, unprotected FN 14 | Fail |

Aggregate safety controls remained intact: detector request rate 0.02477, normal-frame interventions 0, and guard alignment 1.00000. Step 3B targeted category live therefore fails due to localized FN-protection drift, not due to broad detector-heavy behavior.

Recommended next action: hold Step 4 full CDnet dry-run and make a narrow dry-run-only patch for the live-sensitive FN misses in `shadow/cubicle`, `PTZ/intermittentPan`, `shadow/copyMachine`, and `intermittentObjectMotion/parking`.
