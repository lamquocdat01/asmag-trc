# TASK BOARD - ASMAG-TRC

| ID | Task | Status | Priority | Input | Output | Command | Estimated time | Notes |
|---|---|---|---|---|---|---|---|---|
| G0 | Commit current state | Completed | High | Current repo changes | Git commit | `git status && git add ... && git commit -m "..."` | Done | G1 committed as `39ba931`; 9D committed as `cb809b5`. |
| G1 | Finish 9C-Fix | Completed | High | `configs/q2_core_extended_online_controller_p3tuned.yaml` | `outputs/q2_core_extended_online_controller_p3tuned` final reports | `python src/run_experiment.py --config configs/q2_core_extended_online_controller_p3tuned.yaml` | Done | Final progress: `128/128` completed; final reports generated. |
| G1b | Calibrate online controller 9D | Completed | High | `outputs/q2_core_extended_online_controller_p3tuned`, `outputs/full_cdnet2014_controller_sampled_metrics` | `outputs/q2_core_extended_online_controller_calibrated` final reports | `python src/controller/train_online_mode_policy.py ...` then `python src/run_experiment.py --config configs/q2_core_extended_online_controller_calibrated.yaml` | Done | `ONLINE_CALIBRATED` FMeasure `0.4196` > p3tuned `0.4111`; activation/energy remain below P3_MOG2. |
| G2G3-Setup | Prepare official-like Edge CPU-only run | Completed | High | Full CDnet2014 dataset, 6 core pipelines | Config, run plan, output structure, progress system | `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only` | Done | Config and 53-video run plan created; progress has 318 jobs. |
| G2G3-Smoke | Smoke test one short job | Completed | High | `baseline/highway/P3_MOG2`, `max_frames=50` | Smoke raw result and edge profile | `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --pipeline P3_MOG2 --max-frames 50` | Done | Frames `50`, FMeasure `0.8727`, Event_F1 `1.0000`, Avg_FPS `4.1100`, P95 latency `313.8325 ms`. |
| G2G3-Test1Video-Safe | Test one video with 6 pipelines at 100 frames | Completed | High | `baseline/highway`, 6 core pipelines, `max_frames=100` | `test1video_summary.csv`, `test1video_summary.md` | `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --max-frames 100` | Done | All 6 pipelines completed; progress `completed=6`, `pending=312`, `running=0`, `failed=0`. |
| G2G3-Test1Video-300 | Increase same one-video test to 300 frames | Completed | High | `baseline/highway`, 6 core pipelines, `max_frames=300` | `test1video_summary_300.csv`, `test1video_summary_300.md`, `test1video_100_vs_300_comparison.csv` | `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --category baseline --video highway --max-frames 300` | Done | All 6 pipelines completed; 300-frame result is stable enough to justify representative run. |
| G2G3-Representative | Representative 6-video run | Completed | High | highway, office, canoe, traffic, library, turbulence2 | Representative reports and charts | Run selected videos with `max_frames=300` | Done | Completed 36/36 representative jobs; P3_MOG2 best quality, P2 fastest/lowest energy, controller near P3 with lower activation. |
| G2G3-ProgressMonitor | Upgrade detailed live progress before resume | Done | High | `run_progress.csv`, G2G3 config | `live_progress.json`, `live_progress.md`, richer terminal progress, `progress_percent` | `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --progress-only` | Done | Adds current category/video/pipeline, frame progress, FPS, latency, runtime, ETA, and `--show-live-progress`; no experiment jobs run during validation. |
| G2G3-MaxJobsResume | Add one-job resume mode | Done | High | G2G3 runner and run progress | `--max-jobs-per-run 1`, single-job start block, visual live progress | `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 1 --progress-only` | Done | Progress-only verified at `completed=6/318`, `pending=312`, `running=0`, `failed=0`; next job remains `badWeather/skating/P1_YOLO_Only`. Live JSON/MD now include job index, CPU/RAM, energy, progress bars, and fun status line. |
| G2G3-FullOfficialLike | Full CDnet2014 official-like frame_step=1 + Edge profiling | In Progress / Paused | High | Full run plan | Full official-like reports and charts | `python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml --run-plan configs/full_cdnet2014_official_edge_video_run_plan.csv --max-jobs-per-run 10` | Multi-day | Run-10 completed on 2026-04-30: progress `completed=97/318` (`30.5031%`), `pending=221`, `running=0`, `failed=0`, completed videos `16/53`. Last completed: `dynamicBackground/fountain02/P1_YOLO_Only`. Next pending: `dynamicBackground/fountain02/P2_FrameDiff`. Safe to resume. |
| G2G3-FinalReport | Final paper/report tables and figures | Pending | High | Completed official-like output | `auto_research_summary.md`, final tables, charts | Generated by runner after completed or partial aggregation | TBD | Use for Journal of Real-Time Image Processing positioning. |
| G4 | Confidence-aware reuse | Pending | Medium | YOLO confidence/object scores | Reuse policy variant | TBD | 1-2 days | Improve reuse decisions using confidence decay and uncertainty. |
| G5 | Tracking-assisted reuse | Pending | Medium | Frame-level detections/masks | Tracking reuse variant | TBD | 1-2 days | Add lightweight tracking to reduce reuse misalignment. |
| G6 | Cross-dataset validation | Pending | Medium | Additional dataset | Cross-dataset report | TBD | TBD | Validate generalization outside CDnet2014. |
| G7 | Qualitative examples | Pending | Medium | Selected videos/frames | Figures and overlays | TBD | 2-4 hrs | Show success/failure cases for paper. |
| G8 | Paper manuscript | Pending | High | Final metrics/figures | Manuscript draft | TBD | Multi-day | Position as adaptive inference-control, not SOTA segmentation. |
| G9 | Journal submission preparation | Pending | Medium | Manuscript + artifacts | Submission package | TBD | Multi-day | Format, cover letter, reproducibility checklist. |
| G9-SubmissionPrep | Manuscript audit and supplementary package prep | Completed | High | `manuscript/ASMAG_2026_submission_draft.docx`, official-like output CSV/charts | `outputs/manuscript_submission_check`, `outputs/submission_package`, `outputs/paper_ready_figures` | `python src/paper/generate_paper_figures.py`; `python src/paper/generate_submission_prep_reports.py` | Done | Backup created; reports/checklist/statements/cover letter/supplementary package created; manuscript readiness `62/100`; `.docx` not overwritten. |
| G9-SubmissionPrep-Pass2 | Clean Markdown master and fix formula/table/reference/figure blockers | Completed | High | `manuscript/ASMAG_2026_submission_draft.md`, pass1 reports, `gain_summary.csv`, paper-ready figures | `manuscript/ASMAG_2026_submission_ready_v1.md`, pass2 reports, references draft/BibTeX | `python src/paper/create_submission_ready_v1.py` | Done | Formulas fixed in Markdown; Table 4 corrected from CSV; references draft has 39 complete entries + 5 TODO entries; Figures 1-6 have Markdown paths/captions; readiness `78/100`. |
| G9-SubmissionPrep-Pass3 | Prepare Word-ready Markdown and conversion/proof reports | Completed | High | `manuscript/ASMAG_2026_submission_ready_v1.md`, references draft/BibTeX, paper-ready figures | `outputs/submission_package/pass3_word_ready` | `python src/paper/prepare_pass3_word_ready.py` | Done | Word-ready Markdown created; DOCX/PDF conversion blocked due missing Pandoc/LibreOffice/python-docx; structure proof passed on Markdown; readiness `80/100`. |
| G9-DOCX-PDF-Proof | Check user-created DOCX and prepare final Word/PDF proof package | Completed / PDF pending | High | `outputs/submission_package/pass3_word_ready/ASMAG_2026_submission_ready_v1.docx` | `FINAL_DOCX_PDF_PROOF_REPORT.md`, `MANUAL_WORD_PROOF_CHECKLIST.md`, updated readiness report | Manual DOCX XML/text proof; no experiment rerun | Done | DOCX exists (`777970` bytes); PDF missing; DOCX structure proof passes; 9 TODO remain; readiness `86/100`; next step is manual PDF export and visual proof. |
| G9-ManuscriptFix | Insert formula/table/reference fixes into manuscript | Pending | High | `outputs/manuscript_submission_check/*`, `references_to_add.bib`, `outputs/paper_ready_figures` | Updated Word or journal-template manuscript | Manual Word edit or future docx-capable tool | TBD | Fix broken equations, Table 4 mismatches, citation placeholders, references, and final figure placement before submission. |
<!-- G2G3_AUTO_STATUS_START -->
## G2G3 Auto Resume Status

- Updated at: `2026-05-24T10:23:01`
- Event: run completed or paused after selected batch
- Completed: `53 / 53`
- Pending: `0`
- Running: `0`
- Failed: `0`
- Overall progress: `100.0000%`
- Completed videos: `0 / 53`
- Jobs completed this session: `12`
- Last completed job: `turbulence/turbulence3/ASMAG_TR_CONTROLLER_ONLINE_GUARDED`
- Next pending job: `-`
- Resume command: `python src/run_experiment.py --config configs/full_cdnet2014_guarded_v2_clean.yaml --max-jobs-per-run 15`

### Failed Jobs

- None
<!-- G2G3_AUTO_STATUS_END -->
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
