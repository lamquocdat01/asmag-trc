# Experiment Log

## q2_core_full_metrics

- Purpose: Core Q2 baseline/full metrics run.
- Output: `outputs/q2_core_full_metrics`
- Status: completed earlier.

## q2_core_extended_full_metrics

- Purpose: Extended category run used for ASMAG-TR analysis and online controller simulation.
- Output: `outputs/q2_core_extended_full_metrics`
- Status: completed.

## full_cdnet2014_sampled_full_metrics

- Purpose: Full sampled CDnet2014 metrics for P1/P2/P3/ASMAG_TR_ACC/ASMAG_TR_FAST.
- Output: `outputs/full_cdnet2014_sampled_full_metrics`
- Status: completed.
- Key artifacts: `asmag_vs_p3_gap_analysis.csv`, `asmag_vs_p3_gap_summary.md`.

## full_cdnet2014_controller_sampled_metrics

- Purpose: Category-aware `ASMAG_TR_CONTROLLER` evaluation.
- Output: `outputs/full_cdnet2014_controller_sampled_metrics`
- Status: completed.
- Key artifacts: `controller_mode_usage.csv`, `final_main_comparison.csv`, `controller_gain_summary.csv`, `asmag_trc_report_summary.md`.

## q2_core_extended_online_controller_p3tuned

- Purpose: 9C-Fix real run for `ASMAG_TR_CONTROLLER_ONLINE_P3TUNED`.
- Config: `configs/q2_core_extended_online_controller_p3tuned.yaml`
- Output: `outputs/q2_core_extended_online_controller_p3tuned`
- Status: completed.
- Final progress: `completed=128`, `pending=0`, `running=0`, `failed=0`.
- Resume command: `python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml`.

## q2_core_extended_online_controller_calibrated

- Purpose: 9D calibrated online controller using pseudo-labels from category-aware policy.
- Config: `configs/q2_core_extended_online_controller_calibrated.yaml`
- Output: `outputs/q2_core_extended_online_controller_calibrated`
- Status: completed.
- Final progress: `completed=128`, `pending=0`, `running=0`, `failed=0`.
- Key result: `ONLINE_CALIBRATED` FMeasure `0.4196`, Event_F1 `0.7445`, Activation `0.7163`, Energy/frame `5.2610`.

## full_cdnet2014_official_edge_profile_pc

- Purpose: G2G3 official-like CDnet2014 `frame_step=1` plus Edge CPU-only profiling on PC.
- Config: `configs/full_cdnet2014_official_edge_profile_pc.yaml`
- Run plan: `configs/full_cdnet2014_official_edge_video_run_plan.csv`
- Output: `outputs/full_cdnet2014_official_edge_profile_pc`
- Status: setup + smoke completed; waiting for user confirmation before one-video 6-pipeline test.
- Pipelines: `P1_YOLO_Only`, `P2_FrameDiff`, `P3_MOG2`, `ASMAG_TR_FAST`, `ASMAG_TR_CONTROLLER`, `ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`.
- Full plan: 53 videos x 6 pipelines = 318 jobs.
- Current progress after smoke: `completed=1`, `pending=317`, `running=0`, `failed=0`.
- Smoke command: `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --pipeline P3_MOG2 --max-frames 50`.
- Smoke result: frames `50`, FMeasure `0.8727`, Event_F1 `1.0000`, Activation `1.0000`, Avg_FPS `4.1100`, P95 latency `313.8325 ms`, Energy/frame `6.7000`, Simulated_runtime_energy/frame `7.9084`.

## 2026-04-29 G2G3 SingleJob Runner

- Status: setup completed; no experiment job run during validation.
- Added/verified `--max-jobs-per-run 1` so one invocation runs exactly one pending category/video/pipeline job.
- Live progress now includes visual terminal block, progress bars, current job index, completed video count, CPU/RAM process, energy metrics, ETA, and fun status line.
- Current progress: `completed=6/318`, `pending=312`, `running=0`, `failed=0`, completed videos `1/53`.
- Last completed job: `badWeather/blizzard/ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED`.
- Next pending job: `badWeather/skating/P1_YOLO_Only`.
- Resume one job command: `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 1`.

- `2026-05-03T17:33:21` G2G3 final official-like completed: completed=318/318, pending=0, running=0, failed=0, videos=53/53, best_fmeasure=ASMAG_TR_CONTROLLER:0.5939, best_event=ASMAG_TR_CONTROLLER:0.7114.

## 2026-05-06 Manuscript Submission Prep

- Purpose: Prepare ASMAG-TRC manuscript and supplementary package for Q1/Q2 journal submission.
- Main manuscript: `manuscript/ASMAG_2026_submission_draft.docx`.
- Backup created before processing: `manuscript/backup/ASMAG_2026_submission_draft_backup_20260506_162624.docx`.
- Extraction outputs: `manuscript/ASMAG_2026_submission_draft_extracted.txt`, `manuscript/ASMAG_2026_submission_draft.md`.
- Audit outputs: `outputs/manuscript_submission_check`.
- Submission package: `outputs/submission_package`.
- Supplementary data package: `outputs/submission_package/Supplementary_Data`.
- Paper-ready figures: `outputs/paper_ready_figures` generated from official-like CSV outputs using `src/paper/generate_paper_figures.py`.
- Final report: `outputs/submission_package/FINAL_SUBMISSION_PREP_REPORT.md`.
- Key findings: formulas/notation are broken in the `.docx`; visible reference section is empty; `(arXiv)` and `(Microsoft)` placeholders remain; Table 4 simulated runtime energy saving has mismatches against `gain_summary.csv`; original charts are about 180 dpi and paper-ready replacements are about 320 dpi.
- Status: package/audit prep completed; manuscript is not ready to submit yet. No full CDnet2014 rerun, no data fabrication, no commit, no push.

## 2026-05-06 Manuscript Submission Prep Pass 2

- Purpose: Create a clean Markdown master and resolve pass 1 manuscript blockers without touching the original `.docx`.
- Input Markdown: `manuscript/ASMAG_2026_submission_draft.md`.
- Output Markdown: `manuscript/ASMAG_2026_submission_ready_v1.md`.
- Script: `src/paper/create_submission_ready_v1.py`.
- Reports: `outputs/submission_package/pass2_change_log.md`, `pass2_formula_check.md`, `pass2_table4_validation.md`, `pass2_reference_action_report.md`, `pass2_figure_insertion_report.md`, `FINAL_SUBMISSION_PREP_PASS2_REPORT.md`.
- Reference outputs: `outputs/submission_package/references_section_draft.md`, `outputs/submission_package/references_ready.bib`.
- Figure output added: `outputs/paper_ready_figures/asmag_trc_architecture.png` and `.pdf`.
- Key results: required formulas found; broken placeholder counts are zero; Table 4 simulated runtime energy saving corrected from CSV; 39 complete reference entries plus 5 TODO reference entries drafted; Figures 1-6 have Markdown paths and captions; Threats to Validity and Declarations inserted.
- Status: Markdown master ready for Word conversion/proofing; readiness `78/100`. No CDnet2014 rerun, no data fabrication, no commit, no push.

## 2026-05-06 Manuscript Submission Prep Pass 3

- Purpose: Prepare a Word-ready package and determine whether DOCX/PDF conversion is possible in the current environment.
- Input Markdown: `manuscript/ASMAG_2026_submission_ready_v1.md`.
- Output folder: `outputs/submission_package/pass3_word_ready`.
- Main output: `outputs/submission_package/pass3_word_ready/ASMAG_2026_word_ready.md`.
- Script: `src/paper/prepare_pass3_word_ready.py`.
- Tool status: `pandoc`, `soffice/libreoffice`, `winword`, `python-docx`, `pypandoc`, `md-to-docx`, `markdown-to-docx`, `md2docx`, and `docx2pdf` unavailable; Python `markdown` available but insufficient for reliable DOCX conversion.
- Conversion outputs: DOCX/PDF not created; `CONVERSION_BLOCKED.md` and `PDF_EXPORT_BLOCKED.md` created with manual instructions.
- Proof output: `word_pdf_proof_report.md` confirms Markdown structure has title, abstract, keywords, Sections 1-8, references, declarations, appendix, Figures 1-6, Tables 1-4, equations, captions, adjusted figure paths, and zero broken placeholders.
- TODO status: `todo_reference_report.md` finds 19 TODO occurrences across manuscript/reference drafts, mostly vendor/hardware/power-profile references and declaration decisions.
- Status: Word-ready Markdown prepared; readiness `80/100`. No CDnet2014 rerun, no data fabrication, no commit, no push.

## 2026-05-06 Manuscript Submission Prep Pass 3 DOCX/PDF Proof

- Purpose: Check the user-created DOCX, check whether the matching PDF exists, produce final proof reports, and update readiness without rerunning experiments.
- DOCX: `outputs/submission_package/pass3_word_ready/ASMAG_2026_submission_ready_v1.docx`.
- DOCX status: exists; size `777970 bytes` (`759.74 KiB`); modified `2026-05-06 17:32:55 +07:00`.
- PDF target: `outputs/submission_package/pass3_word_ready/ASMAG_2026_submission_ready_v1.pdf`.
- PDF status: not found; manual export from Word/LibreOffice is required.
- Proof reports: `outputs/submission_package/pass3_word_ready/FINAL_DOCX_PDF_PROOF_REPORT.md`, `outputs/submission_package/pass3_word_ready/MANUAL_WORD_PROOF_CHECKLIST.md`.
- DOCX proof result: title, abstract, keywords, Sections 1-8, references, declarations, appendix/supplementary, Tables 1-4, and Figures 1-6 are present.
- Object/placeholder result: `6` Word drawing objects, `6` Word table objects, and `19` Office Math objects detected; requested broken placeholders are absent; raw Markdown image syntax count is `0`; raw LaTeX equation signal count is `0`.
- Remaining TODO in DOCX text: `9`.
- Status: DOCX structurally proofed, PDF export/visual proof pending, readiness `86/100`. No CDnet2014 rerun, no output deletion, no original manuscript overwrite, no commit, no push.
