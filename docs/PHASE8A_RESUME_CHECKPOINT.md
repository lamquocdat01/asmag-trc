# Phase 8A Resume Checkpoint

Created: 2026-05-11

## 1. Current Phase 8A Status

Phase 8A was paused safely after building the research dataset and before completing the model probe.

Completed:

- Created `tools/build_phase8a_policy_dataset.py`.
- Created `tools/probe_phase8a_policy_models.py`.
- Built the Phase 8A research dataset under `outputs/phase8a_policy_dataset/`.
- Created `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8A_DATASET_REPORT.md`.
- Created a narrow `.gitignore` for Phase 8A generated parquet/model/cache artifacts.
- Created inventory, action label mapping, frame dataset, window dataset, teacher labels, oracle labels, split files, missing-feature report, and utility sanity CSV.
- Confirmed no active Python process remained after stopping the interrupted probe process.

Incomplete:

- `tools/probe_phase8a_policy_models.py` did not complete.
- These expected probe outputs are not present yet:
  - `outputs/phase8a_policy_dataset/model_probe_results.csv`
  - `outputs/phase8a_policy_dataset/policy_feature_importance.csv`
  - `outputs/phase8a_policy_dataset/policy_rule_candidates.txt`

Interrupted commands:

- The first full model probe run timed out.
- The second model probe run was interrupted by the user. One lingering `python` process was detected afterward and stopped with `Stop-Process -Id 18400`.

Still running:

- None observed after stopping PID `18400`; `Get-Process python -ErrorAction SilentlyContinue` returned no rows.
- A command-line process inspection using `Get-CimInstance Win32_Process` was attempted but failed with access denied, so the process identity could not be confirmed from command line text before stopping it.

## 2. Files Created Or Modified

Phase 8A source files:

- `tools/build_phase8a_policy_dataset.py`
- `tools/probe_phase8a_policy_models.py`

Phase 8A docs:

- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8A_DATASET_REPORT.md`
- `docs/PHASE8A_RESUME_CHECKPOINT.md`

Configs:

- No Phase 8A configs were created or modified.

Small metadata/checkpoint files:

- `.gitignore` with Phase 8A generated artifact exclusions only.

Output folder:

- `outputs/phase8a_policy_dataset/`

Important partial or complete output files:

- `outputs/phase8a_policy_dataset/data_inventory.csv`
- `outputs/phase8a_policy_dataset/action_label_mapping.csv`
- `outputs/phase8a_policy_dataset/frame_state_dataset.parquet`
- `outputs/phase8a_policy_dataset/frame_state_dataset_sample.csv`
- `outputs/phase8a_policy_dataset/window_state_dataset.parquet`
- `outputs/phase8a_policy_dataset/window_state_dataset_sample.csv`
- `outputs/phase8a_policy_dataset/teacher_label_dataset.parquet`
- `outputs/phase8a_policy_dataset/oracle_action_dataset.parquet`
- `outputs/phase8a_policy_dataset/missing_feature_report.csv`
- `outputs/phase8a_policy_dataset/utility_sanity_by_action.csv`
- `outputs/phase8a_policy_dataset/splits/split_leave_one_video.csv`
- `outputs/phase8a_policy_dataset/splits/split_leave_one_category.csv`
- `outputs/phase8a_policy_dataset/splits/split_ptz_holdout.csv`
- `outputs/phase8a_policy_dataset/splits/split_smoke_vs_targeted.csv`

Workspace note:

- `git status --short` shows a broad dirty workspace with many pre-existing modified/untracked project files and outputs from earlier phases. Phase 8A work should be reviewed by file path rather than assuming all dirty files belong to this phase.

## 3. Commands Already Run

Completed lightweight/context commands:

```powershell
Get-Content docs\ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE7C_ABLATION_RESULTS.md
Get-Content docs\ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE7A_ORACLE_POLICY_DIAGNOSIS.md
Get-Content docs\ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE7A_TEACHER_STUDENT_PROPOSAL.md
Get-Content docs\ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE7B_IMPLEMENTATION_PLAN.md
Get-ChildItem outputs\logic_outcome_analysis -Recurse -File | Select-Object -First 40 FullName
Get-ChildItem outputs\policy_diagnosis -Recurse -File | Select-Object -First 60 FullName
Get-ChildItem outputs\asmag_tr_controller_online_guarded_ablation_phase7c -Depth 2 | Select-Object -First 80 FullName
Get-ChildItem outputs\asmag_tr_controller_online_guarded_cdnet_smoke -Depth 2 | Select-Object -First 80 FullName
rg --files outputs\asmag_tr_controller_online_guarded_cdnet_smoke | Select-String -Pattern "frame_metrics.csv$|per_video_summary.csv$|summary_by_video.csv$" | Select-Object -First 40
rg --files outputs\asmag_tr_controller_online_guarded_cdnet_targeted | Select-String -Pattern "frame_metrics.csv$|per_video_summary.csv$|summary_by_video.csv$" | Select-Object -First 40
rg --files outputs\full_cdnet2014_official_edge_profile_pc | Select-String -Pattern "frame_metrics.csv$|per_video_summary.csv$|summary_by_video.csv$" | Select-Object -First 40
Get-Content outputs\asmag_tr_controller_online_guarded_cdnet_smoke\per_video_summary.csv -TotalCount 2
Get-Content outputs\asmag_tr_controller_online_guarded_cdnet_targeted\per_video_summary.csv -TotalCount 2
Get-Content outputs\full_cdnet2014_official_edge_profile_pc\per_video_summary.csv -TotalCount 2
python -c "import importlib.util as u; print('sklearn', bool(u.find_spec('sklearn'))); print('pyarrow', bool(u.find_spec('pyarrow'))); print('fastparquet', bool(u.find_spec('fastparquet')))"
```

Completed verification/build commands:

```powershell
python -m py_compile tools\build_phase8a_policy_dataset.py tools\probe_phase8a_policy_models.py
python tools\build_phase8a_policy_dataset.py
python -m py_compile tools\build_phase8a_policy_dataset.py tools\probe_phase8a_policy_models.py
python tools\build_phase8a_policy_dataset.py
python -m py_compile tools\build_phase8a_policy_dataset.py tools\probe_phase8a_policy_models.py
python tools\build_phase8a_policy_dataset.py
python -m py_compile tools\build_phase8a_policy_dataset.py tools\probe_phase8a_policy_models.py
```

Command outcomes:

- First `python tools\build_phase8a_policy_dataset.py`: failed with a pandas `fillna` TypeError during window dataset construction after loading 543 frame metric files.
- Second `python tools\build_phase8a_policy_dataset.py`: timed out after 1200 seconds; frame/window/teacher artifacts were present, but oracle/splits/report were not complete.
- Third `python tools\build_phase8a_policy_dataset.py`: completed successfully and wrote the full Phase 8A dataset.
- All listed `py_compile` commands completed successfully.

Interrupted or timed-out probe commands:

```powershell
python tools\probe_phase8a_policy_models.py
python tools\probe_phase8a_policy_models.py
```

Probe outcomes:

- First probe command timed out after 1200 seconds.
- Second probe command was interrupted by the user after about 539 seconds.
- No completed probe result files were observed afterward.

Pause/checkpoint inspection commands:

```powershell
git status --short
Get-ChildItem outputs\phase8a_policy_dataset -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime
Get-ChildItem docs -Filter *PHASE8A* -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -match 'phase8a|probe_phase8a|build_phase8a' } | Select-Object ProcessId,Name,CommandLine
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,StartTime
Get-ChildItem outputs\phase8a_policy_dataset\splits -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime
Stop-Process -Id 18400
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,StartTime
```

Inspection outcomes:

- `git status --short` completed.
- Phase 8A output folder listing completed.
- Phase 8A docs listing completed.
- `Get-CimInstance Win32_Process` failed with access denied.
- `Get-Process python` showed one active Python process, PID `18400`, started during the interrupted probe window.
- `Stop-Process -Id 18400` completed.
- A final `Get-Process python` returned no rows.

## 4. Partial Outputs

Output folders:

- `outputs/phase8a_policy_dataset/`
- `outputs/phase8a_policy_dataset/splits/`

Files observed in `outputs/phase8a_policy_dataset/`:

| File | Status | Notes |
|---|---|---|
| `action_label_mapping.csv` | complete | written by completed builder |
| `data_inventory.csv` | complete | written by completed builder |
| `frame_state_dataset.parquet` | complete | 731,526 frame rows observed during inspection |
| `frame_state_dataset_sample.csv` | complete | sample export |
| `window_state_dataset.parquet` | complete | rolling windows for sizes 3, 5, 10 |
| `window_state_dataset_sample.csv` | complete | sample export |
| `teacher_label_dataset.parquet` | complete | per-video teacher labels |
| `oracle_action_dataset.parquet` | complete | vectorized oracle labels from completed builder |
| `missing_feature_report.csv` | complete | generated by report step |
| `utility_sanity_by_action.csv` | complete | generated by report step |
| `splits/split_leave_one_video.csv` | complete | video-grouped split file |
| `splits/split_leave_one_category.csv` | complete | category holdout split file |
| `splits/split_ptz_holdout.csv` | complete | PTZ holdout split file |
| `splits/split_smoke_vs_targeted.csv` | complete | video-safe smoke vs targeted split file |
| `model_probe_results.csv` | missing/incomplete | probe did not complete |
| `policy_feature_importance.csv` | missing/incomplete | probe did not complete |
| `policy_rule_candidates.txt` | missing/incomplete | probe did not complete |

Commit guidance:

- Do not commit the generated parquet datasets.
- Do not commit large generated CSV samples or runtime outputs.
- Regenerate large Phase 8A outputs at home from the committed tools if they are missing, stale, or suspected partial.
- Keep only source scripts, small docs, and narrow ignore metadata in the Git checkpoint.

Observed output sizes at pause:

- `frame_state_dataset.parquet`: 21,011,854 bytes
- `window_state_dataset.parquet`: 19,473,750 bytes
- `oracle_action_dataset.parquet`: 1,203,615 bytes
- `teacher_label_dataset.parquet`: 13,404 bytes

## 5. How To Resume

Do not rerun experiment runners.

Recommended next command:

```powershell
python tools\probe_phase8a_policy_models.py --max-rows 10000
```

Resume strategy:

- Resume from existing `outputs/phase8a_policy_dataset/` artifacts.
- Do not rerun `python tools\build_phase8a_policy_dataset.py` unless the dataset builder source changes or outputs are intentionally refreshed.
- There is no cache/progress file for the model probe.
- The model probe writes outputs only after fitting/evaluation completes, so the interrupted probe left no reliable partial probe results to resume from.

If the 10,000-row probe still runs too long, reduce the sample:

```powershell
python tools\probe_phase8a_policy_models.py --max-rows 5000
```

Expected completed probe outputs:

- `outputs/phase8a_policy_dataset/model_probe_results.csv`
- `outputs/phase8a_policy_dataset/policy_feature_importance.csv`
- `outputs/phase8a_policy_dataset/policy_rule_candidates.txt`

## 6. Safety Notes

- Old `ONLINE_CALIBRATED` production behavior was not modified.
- P1/P2/P3/FAST/`ASMAG_TR_CONTROLLER` production behavior was not modified.
- `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` production behavior was not modified during Phase 8A.
- No configs were created or modified for Phase 8A.
- Frozen CDnet2014 v1.6 outputs were read only; they were not intentionally overwritten by Phase 8A.
- No smoke run was launched.
- No PTZ-targeted run was launched.
- No targeted CDnet run was launched.
- No full CDnet run was launched.
- No cross-dataset validation run was launched.
- No LASIESTA, SBI2015, or BMC run was launched.
- Only offline dataset-building and model-probe scripts were run.

## 7. Continue Phase 8A from checkpoint

```text
You are working on ASMAG-TRC Phase 8A. Resume from docs/PHASE8A_RESUME_CHECKPOINT.md.

Do NOT run experiments. Do NOT modify production behavior. Do NOT rerun smoke, targeted, full CDnet, LASIESTA, SBI2015, or BMC.

The Phase 8A dataset builder completed and outputs exist under outputs/phase8a_policy_dataset/. The model probe was interrupted and produced no final probe outputs.

Please run only:
python -m py_compile tools\probe_phase8a_policy_models.py
python tools\probe_phase8a_policy_models.py --max-rows 10000

If that is still too slow, stop and reduce to --max-rows 5000. Then inspect:
outputs/phase8a_policy_dataset/model_probe_results.csv
outputs/phase8a_policy_dataset/policy_feature_importance.csv
outputs/phase8a_policy_dataset/policy_rule_candidates.txt

Update docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8A_DATASET_REPORT.md with the probe results and give a research-only Phase 8B readiness recommendation. Do not recommend deployment unless data quality is strong and explicitly justified.
```
