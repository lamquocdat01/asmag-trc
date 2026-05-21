# RUNBOOK - ASMAG-TRC

## G2G3 Official-like Edge CPU-only Profiling

Current G2G3 output:

- Config: `configs/full_cdnet2014_official_edge_profile_pc.yaml`
- Run plan: `configs/full_cdnet2014_official_edge_video_run_plan.csv`
- Output: `outputs/full_cdnet2014_official_edge_profile_pc`
- Pipelines: `P1_YOLO_Only`, `P2_FrameDiff`, `P3_MOG2`, `ASMAG_TR_FAST`, `ASMAG_TR_CONTROLLER`, `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`
- Full plan size: 53 videos x 6 pipelines = 318 jobs

Do not delete old checkpoints or outputs. Do not touch/delete:

- `outputs/full_cdnet2014_sampled_full_metrics`
- `outputs/full_cdnet2014_controller_sampled_metrics`
- `outputs/q2_core_extended_online_controller_p3tuned`
- `outputs/q2_core_extended_online_controller_calibrated`

### G2G3 Progress-only

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only
```

### How to run one pipeline of one video

Use this mode for multi-day or overnight work when you want one controlled checkpoint per run. It runs exactly one pending job: one category, one video, one pipeline. It does not delete completed checkpoints or outputs.

Progress-only check:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only
```

Show current live progress without running an experiment:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --show-live-progress
```

Resume exactly one job:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 1
```

Resume one full video, all remaining core pipelines for that video:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 1
```

Single-job live progress writes:

- `outputs/full_cdnet2014_official_edge_profile_pc/live_progress.json`
- `outputs/full_cdnet2014_official_edge_profile_pc/live_progress.md`
- `outputs/full_cdnet2014_official_edge_profile_pc/daily_progress_report.md`
- `outputs/full_cdnet2014_official_edge_profile_pc/experiment_log.md`

### How to check progress

Use these commands before resuming G2G3. They only inspect progress and do not run experiment jobs.

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only
```

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --show-live-progress
```

Open the live markdown file:

```text
outputs/full_cdnet2014_official_edge_profile_pc/live_progress.md
```

Live progress files:

- `outputs/full_cdnet2014_official_edge_profile_pc/live_progress.json`
- `outputs/full_cdnet2014_official_edge_profile_pc/live_progress.md`

### G2G3 Smoke Test

Already completed for `baseline/highway/P3_MOG2` with `max_frames=50`.

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --pipeline P3_MOG2 --max-frames 50
```

Latest smoke result:

- Frames processed: `50`
- CDnet_FMeasure: `0.8727`
- Event_F1: `1.0000`
- Activation: `1.0000`
- Avg_FPS: `4.1100`
- P95 latency: `313.8325 ms`
- Avg CPU: `145.0540`
- Avg RAM: `550.8272 MB`
- Energy/frame: `6.7000`
- Simulated_runtime_energy/frame: `7.9084`

### G2G3 Test One Video

Run only after user confirmation.

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --max-frames 300
```

### G2G3 Representative Run

Run only after user confirmation. Target videos:

- `baseline/highway`
- `baseline/office`
- `dynamicBackground/canoe`
- `cameraJitter/traffic`
- `thermal/library`
- `turbulence/turbulence2`

Recommended approach: run the selected videos one by one with `--max-frames 300`, or temporarily mark other run-plan rows as not pending before using `--max-videos-per-run 6`.

### G2G3 Full Official-like Resume

Safe default, one video per run:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 1
```

Overnight mode:

```bat
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-videos-per-run 10
```

Runner behavior:

- Completed jobs are skipped only when output is complete and `frames_done >= frames_expected`.
- Stale `running` jobs older than 10 minutes are recovered to `pending`.
- `run_progress.csv` is updated during jobs and after every completed or failed job.
- `live_progress.json` and `live_progress.md` show current category/video/pipeline, frame progress, FPS, latency, runtime, and ETA.
- `daily_progress_report.md` is updated after runs.

## Resume 9C-Fix

```bat
python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml
```

The config enables stale job recovery:

```yaml
progress:
  auto_recover_stale_jobs: true
  stale_running_minutes: 10
```

## Manuscript Submission Preparation

Use this workflow for manuscript/package preparation only. It must not rerun full CDnet2014, delete outputs, or overwrite the original Word manuscript without a backup.

Primary manuscript:

```text
manuscript/ASMAG_2026_submission_draft.docx
```

Backup created:

```text
manuscript/backup/ASMAG_2026_submission_draft_backup_20260506_162624.docx
```

Regenerate paper-ready figures from final CSV values:

```bat
python src/paper/generate_paper_figures.py
```

Regenerate submission-prep reports after extraction/package files exist:

```bat
python src/paper/generate_submission_prep_reports.py
```

Key outputs:

- `outputs/manuscript_submission_check/task0_file_check.md`
- `outputs/manuscript_submission_check/manuscript_audit_report.md`
- `outputs/manuscript_submission_check/formula_fixes.md`
- `outputs/manuscript_submission_check/ASMAG_formula_corrected_sections.md`
- `outputs/manuscript_submission_check/table_figure_validation.md`
- `outputs/manuscript_submission_check/reference_gap_report.md`
- `outputs/manuscript_submission_check/references_to_add.bib`
- `outputs/submission_package/Supplementary_Data`
- `outputs/submission_package/FINAL_SUBMISSION_PREP_REPORT.md`

Current manual manuscript blockers:

- Insert corrected formulas from `ASMAG_formula_corrected_sections.md`.
- Correct Table 4 simulated runtime energy values from `gain_summary.csv`.
- Replace `(arXiv)` and `(Microsoft)` placeholders and fill the empty reference section.
- Replace embedded charts with `outputs/paper_ready_figures`.
- Apply target journal template and proof final PDF.

### Pass 2 Markdown Master

Pass 2 creates a clean submission-oriented Markdown master while keeping the original Word document unchanged.

```bat
python src/paper/create_submission_ready_v1.py
```

Main output:

```text
manuscript/ASMAG_2026_submission_ready_v1.md
```

Pass 2 reports:

- `outputs/submission_package/pass2_change_log.md`
- `outputs/submission_package/pass2_formula_check.md`
- `outputs/submission_package/pass2_table4_validation.md`
- `outputs/submission_package/pass2_reference_action_report.md`
- `outputs/submission_package/pass2_figure_insertion_report.md`
- `outputs/submission_package/references_section_draft.md`
- `outputs/submission_package/references_ready.bib`
- `outputs/submission_package/FINAL_SUBMISSION_PREP_PASS2_REPORT.md`

Current pass 2 status:

- Formula placeholders are fixed in Markdown.
- Table 4 is corrected from `gain_summary.csv`.
- Figure paths/captions are inserted for Figures 1-6.
- Threats to Validity and submission declarations are inserted.
- Readiness score is `78/100`.
- Next step is Word conversion or target-journal template migration, followed by `.docx`/PDF proofing.

### Pass 3 Word-Ready Package

Pass 3 prepares a conversion-ready Markdown package and reports conversion blockers.

```bat
python src/paper/prepare_pass3_word_ready.py
```

Main output:

```text
outputs/submission_package/pass3_word_ready/ASMAG_2026_word_ready.md
```

Pass 3 reports:

- `outputs/submission_package/pass3_word_ready/tool_check_report.md`
- `outputs/submission_package/pass3_word_ready/todo_reference_report.md`
- `outputs/submission_package/pass3_word_ready/CONVERSION_BLOCKED.md`
- `outputs/submission_package/pass3_word_ready/PDF_EXPORT_BLOCKED.md`
- `outputs/submission_package/pass3_word_ready/word_pdf_proof_report.md`
- `outputs/submission_package/pass3_word_ready/journal_decision_note.md`
- `outputs/submission_package/pass3_word_ready/USER_DECISIONS_REQUIRED.md`
- `outputs/submission_package/pass3_word_ready/FINAL_PASS3_WORD_READY_REPORT.md`

Current pass 3 status:

- Word-ready Markdown created.
- Automatic DOCX/PDF conversion is blocked in this environment because `pandoc`, `soffice/libreoffice`, `python-docx`, and markdown-to-docx CLIs are unavailable.
- Markdown structure proof passes for title, abstract, keywords, Sections 1-8, references, declarations, appendix, Figures 1-6, Tables 1-4, equations, and captions.
- Readiness score is `80/100`.

Manual conversion route on a machine with Pandoc:

```bat
cd outputs\submission_package\pass3_word_ready
pandoc ASMAG_2026_word_ready.md --resource-path=.;..\.. -o ASMAG_2026_submission_ready_v1.docx
```

Then export the generated DOCX to PDF and visually proof equations, figures, captions, tables, references, declarations, and appendix separation.

### Pass 3 DOCX/PDF Proof Update

User-created DOCX now exists:

```text
outputs/submission_package/pass3_word_ready/ASMAG_2026_submission_ready_v1.docx
```

DOCX file check:

- Exists: `True`
- Size: `777970 bytes` (`759.74 KiB`)
- Modified: `2026-05-06 17:32:55 +07:00`

PDF target:

```text
outputs/submission_package/pass3_word_ready/ASMAG_2026_submission_ready_v1.pdf
```

Current PDF status:

- Exists: `False`
- Manual export is required from Word or LibreOffice.

Manual export steps:

1. Open `ASMAG_2026_submission_ready_v1.docx`.
2. Export/save as PDF.
3. Save as `ASMAG_2026_submission_ready_v1.pdf` in the same folder.
4. Complete `outputs/submission_package/pass3_word_ready/MANUAL_WORD_PROOF_CHECKLIST.md`.

Proof outputs:

- `outputs/submission_package/pass3_word_ready/FINAL_DOCX_PDF_PROOF_REPORT.md`
- `outputs/submission_package/pass3_word_ready/MANUAL_WORD_PROOF_CHECKLIST.md`

Current proof status:

- DOCX structural proof passes for title, abstract, keywords, Sections 1-8, references, declarations, appendix/supplementary, Tables 1-4, and Figures 1-6.
- DOCX contains `6` Word drawing objects, `6` Word table objects, and `19` Office Math objects.
- Raw Markdown image syntax count in DOCX text: `0`.
- Raw LaTeX equation signal count in DOCX text: `0`.
- Remaining TODO count in DOCX text: `9`.
- Readiness score after DOCX proof: `86/100`.

## Check Progress

```bat
python - <<PY
import pandas as pd
df = pd.read_csv("outputs/q2_core_extended_online_controller_p3tuned/run_progress.csv")
print(df.status.value_counts())
print(df[df.status == "running"])
print(df[df.status == "pending"].head(1))
PY
```

PowerShell-friendly alternative:

```powershell
Import-Csv outputs/q2_core_extended_online_controller_p3tuned/run_progress.csv |
  Group-Object status | Select-Object Name,Count
```

## Generate Final Report

Run after progress reaches `completed=128`, `pending=0`, `running=0`, `failed=0`.

Expected outputs:

- `outputs/q2_core_extended_online_controller_p3tuned/final_main_comparison.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/best_by_metric.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/gain_summary.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/mode_usage_summary.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/scene_difficulty_distribution.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/category_wise_mode_usage.csv`
- `outputs/q2_core_extended_online_controller_p3tuned/auto_research_summary.md`

## Run Edge Profiling

```bat
python src/run_experiment.py --config configs/<edge_profile_config>.yaml
```

Use selected final pipelines only to reduce runtime.

## Run Official-like CDnet One-video Mode

Use a temporary config with:

```yaml
evaluation:
  use_temporal_roi: true
  warmup_frames: 50
  frame_step: 1
  max_frames_per_video: null
videos:
  <category>: [<video>]
```

Then run:

```bat
python src/run_experiment.py --config configs/<official_like_one_video>.yaml
```

## Commit Results

```bat
git status
git add PROJECT_STATE.md TASK_BOARD.md RUNBOOK.md NEXT_PROMPT_FOR_CODEX.md logs outputs/q2_core_extended_online_controller_p3tuned
git commit -m "Update ASMAG-TRC 9C-Fix state and results"
```

<!-- G2G3_FINAL_STATUS_START -->
## G2G3 Final Official-like Status

- Updated at: `2026-05-03T17:33:21`
- Completed jobs: `318 / 318`
- Pending: `0`
- Running: `0`
- Failed: `0`
- Completed videos: `53 / 53`
- Best CDnet_FMeasure: `ASMAG_TR_CONTROLLER` = `0.5939`
- Best Event_F1: `ASMAG_TR_CONTROLLER` = `0.7114`
- Fastest Avg_FPS: `P2_FrameDiff` = `73.9393`
- Final reports: `outputs/full_cdnet2014_official_edge_profile_pc/final_main_comparison.csv`, `gain_summary.csv`, `auto_research_summary.md`, `charts/`
- Next step: use these artifacts for paper main tables, appendix heatmaps, and limitations discussion.
<!-- G2G3_FINAL_STATUS_END -->
