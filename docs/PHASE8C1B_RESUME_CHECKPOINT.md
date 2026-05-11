# Phase 8C-1B Resume Checkpoint

Date: 2026-05-11

Phase: `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` Phase 8C-1B, AI Shadow Model Calibration and Latency Optimization.

## Completion Summary

Phase 8C-1B is complete as calibration/shadow research.

Current safety status:

- Intervention remains disabled.
- `ai_shadow_behavior_enabled: false`.
- No production behavior was intentionally changed.
- Old `ONLINE_CALIBRATED` was not modified.
- P1/P2/P3/FAST/`ASMAG_TR_CONTROLLER` were not modified.
- Frozen CDnet2014 v1.6 outputs were not touched.
- No PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, or BMC run was launched.
- Only allowed smoke/shadow validation was run.

Phase 8C-2 limited intervention is not allowed yet.

## Files Created Or Modified

Created:

- `tools/calibrate_phase8c_shadow_models.py`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C1B_LATENCY_OPTIMIZATION_PLAN.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C1B_SHADOW_CALIBRATION_REPORT.md`
- `docs/PHASE8C1B_RESUME_CHECKPOINT.md`
- `outputs/phase8c_shadow_calibration/`

Modified as guarded-only shadow/runtime research support:

- `src/run_experiment.py`
- `configs/asmag_tr_controller_online_guarded_cdnet_smoke.yaml`

Refreshed smoke/shadow outputs:

- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_disagreement_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_safety_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_video_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/asmag_tr_final_comparison.csv`
- Other smoke summary CSVs under `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/`

Model export directory present:

- `outputs/phase8b_policy_training/models/`

Do not commit large generated outputs unless explicitly requested.

## Commands Already Run

Compile checks:

```powershell
python -m py_compile tools\calibrate_phase8c_shadow_models.py tools\export_phase8b_shadow_models.py src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Calibration:

```powershell
python tools\calibrate_phase8c_shadow_models.py
```

Model export:

```powershell
python tools\export_phase8b_shadow_models.py
```

Allowed smoke-only validation:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke.yaml --max-jobs-per-run 8
```

Comparison:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke
```

No forbidden experiment runner or forbidden dataset run was launched.

## Calibration Outputs

Created under `outputs/phase8c_shadow_calibration/`:

- `unsafe_threshold_sweep.csv`
- `detector_threshold_sweep.csv`
- `reuse_threshold_sweep.csv`
- `lightweight_threshold_sweep.csv`
- `detector_floor_threshold_sweep.csv`
- `risk_class_unsafe_threshold_sweep.csv`
- `calibration_recommendations.csv`
- `calibration_report.md`
- `subrisk_model_probe.csv`
- `subrisk_feature_importance.csv`

## Key Calibration Results

Recommended unsafe threshold:

- `unsafe_action`: `0.75`

Offline unsafe metrics at threshold `0.75`:

- Flag rate: `0.0393`
- Precision / recall / F1: `0.3003 / 0.9171 / 0.4524`
- FPR: `0.0279`

Smoke replay at threshold `0.75`:

- Unsafe flag rate: `0.96375`

Actual smoke rerun using the earlier runtime threshold:

- Unsafe flag rate: `0.97125`
- Detector request rate: `0.67875`
- Reuse block rate: `0.27375`
- Lightweight block rate: `0.10625`
- Known safety-event warning rate: `0.9655`
- Missing feature count: `0.0`

Sub-risk diagnostic probes were generated for:

- `closed_empty_unsafe`
- `reuse_unsafe`
- `lightweight_p3_unsafe`
- `legacy_cadence_unsafe`

These are offline diagnostics only and are not deployed.

## Latency Results

Before Phase 8C-1B optimization:

- Mean / P95 shadow latency: `49.37 / 70.65 ms`

After stride/lightweight-mode smoke rerun:

- Mean / P95 shadow latency: `22.15 / 118.33 ms`

Mean latency improved, but P95 remains too high for intervention.

## Current Decision

Phase 8C-2 limited intervention is not allowed yet.

Next phase should be:

`Phase 8C-1C Runtime Score Alignment and Shadow Latency Stabilization`

## Main Blockers

1. Offline calibration and runtime smoke calibration mismatch.
2. Unsafe-action model still over-flags smoke frames.
3. Shadow P95 latency remains too high.
4. Refreshed smoke comparison did not provide enough no-drift confidence.
5. Class probability / label mapping may be wrong.
6. Feature order/schema alignment may be wrong.
7. Runtime score distribution differs from offline calibration.
8. Unsafe threshold is not selective enough in smoke.

## Exact Next Safe Task

Phase 8C-1C should inspect probability mapping, feature schema alignment, runtime score distributions, threshold sweeps, and latency breakdown.

Keep AI behavior disabled. Do not enable intervention.

## Continue Phase 8C-1C From Checkpoint

Ready-to-copy prompt:

```text
You are working on ASMAG-TRC.

PHASE NAME
ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-1C:
Runtime Score Alignment and Shadow Latency Stabilization

IMPORTANT
This is still shadow-mode research only.
Do NOT enable AI intervention.
Do NOT modify old ONLINE_CALIBRATED.
Do NOT modify P1/P2/P3/FAST/ASMAG_TR_CONTROLLER.
Do NOT overwrite frozen CDnet2014 v1.6 outputs.
Do NOT run PTZ-targeted.
Do NOT run targeted CDnet.
Do NOT run full CDnet.
Do NOT run LASIESTA/SBI2015/BMC.
Do NOT deploy any learned model into runtime action selection.
AI behavior must remain disabled.

READ FIRST
Read docs/PHASE8C1B_RESUME_CHECKPOINT.md first.
Then inspect:
- docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C1B_SHADOW_CALIBRATION_REPORT.md
- docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C1B_LATENCY_OPTIMIZATION_PLAN.md
- outputs/phase8c_shadow_calibration/
- outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_summary.csv
- outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_safety_summary.csv
- outputs/asmag_tr_controller_online_guarded_cdnet_smoke/ai_shadow_video_summary.csv
- outputs/phase8b_policy_training/models/manifest.json
- tools/calibrate_phase8c_shadow_models.py
- tools/export_phase8b_shadow_models.py
- src/run_experiment.py guarded-only AI shadow code

CURRENT STATUS
Phase 8C-1B is complete as calibration/shadow research.
Recommended unsafe threshold is 0.75, but smoke replay still flags 0.96375 of frames.
Actual rerun unsafe flag rate was 0.97125.
Mean shadow latency improved from 49.37 ms to 22.15 ms, but P95 worsened to 118.33 ms.
Missing feature count stayed 0.0.
Phase 8C-2 limited intervention is NOT allowed yet.

TASK
Perform Phase 8C-1C runtime alignment and latency stabilization.

Required work:
1. Verify probability/class mapping for all exported shadow models.
2. Verify feature schema alignment and feature order between training/export/runtime.
3. Generate runtime score distributions from existing smoke logs.
4. Compare runtime score distributions to offline calibration distributions.
5. Recompute threshold sweeps using runtime smoke scores where possible.
6. Recommend runtime thresholds that reduce unsafe over-flagging without losing hard-video warning recall.
7. Analyze latency breakdown into feature adapter, each model inference, caching/stride, and logging.
8. Recommend or implement shadow-only latency instrumentation if needed.
9. Keep AI behavior disabled.

Allowed outputs:
- docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C1C_RUNTIME_ALIGNMENT_REPORT.md
- outputs/phase8c_shadow_alignment/

Do not run PTZ-targeted/targeted/full/cross-dataset experiments.
Do not run smoke unless explicitly needed and only after explaining why.
Do not enable intervention.
```

## Stop/Resume Notes

It is safe to stop after this checkpoint.

On resume, start by reading this file and do not assume earlier chat context.
