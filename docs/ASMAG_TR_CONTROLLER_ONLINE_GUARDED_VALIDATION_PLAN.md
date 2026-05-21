# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Validation Plan

Date: 2026-05-09

## Objective

Validate `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` on CDnet2014 before any LASIESTA, SBI2015, or BMC runs. The new pipeline is an upgraded guarded version of P4-Online / `ONLINE_CALIBRATED`; the old calibrated online behavior remains preserved for side-by-side comparison.

## Stage 1: Smoke Test on Failure Videos

Run only:

```bash
python src/run_experiment.py --config configs/asmag_tr_controller_online_guarded_cdnet_smoke.yaml
python tools/compare_asmag_tr_controller_online_guarded.py --root outputs/asmag_tr_controller_online_guarded_cdnet_smoke
```

Smoke videos:

- `turbulence/turbulence2`
- `dynamicBackground/fountain02`
- `shadow/backdoor`
- `shadow/cubicle`
- `nightVideos/bridgeEntry`
- `PTZ/twoPositionPTZCam`
- `PTZ/continuousPan`
- `lowFramerate/tramCrossroad_1fps`

Smoke acceptance criteria:

- `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` does not crash.
- All required diagnostic columns are present.
- FPS or P95 latency improves compared with old `ONLINE_CALIBRATED`.
- FMeasure is not lower than old `ONLINE_CALIBRATED` on most smoke videos.
- The gap against `P3_MOG2` is reduced on known failure videos if possible.
- All outputs are written to `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/`.
- No frozen CDnet2014 v1.6 output folder is overwritten.

## Stage 2: Review Smoke Outputs

Review:

- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/comparison_summary.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/gain_vs_old_online.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/gain_vs_p3.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/gain_vs_controller.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/per_video_failure_delta.csv`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/mode_action_summary.csv`

Also inspect guarded per-video `frame_metrics.csv` for:

- non-empty `action_label`
- hard guard frequency
- forced refresh frequency
- reuse confidence behavior
- mode switch stability
- latency breakdown sanity

## Stage 3: Targeted CDnet Test

Only if smoke passes, run a targeted CDnet test in a new output folder. It should include all smoke videos plus nearby hard-scene videos from:

- `turbulence`
- `dynamicBackground`
- `PTZ`
- `shadow`
- `nightVideos`
- `lowFramerate`

Do not overwrite the smoke folder or frozen v1.6 folders.

## Stage 4: Full CDnet Test

Only after the targeted CDnet test passes, run:

```bash
python src/run_experiment.py --config configs/asmag_tr_controller_online_guarded_cdnet_full.yaml
python tools/compare_asmag_tr_controller_online_guarded.py --root outputs/asmag_tr_controller_online_guarded_cdnet_full
```

Full CDnet target criteria:

- FMeasure >= `P3_MOG2 - 0.005`
- Event_F1 >= `P3_MOG2`
- Activation < `P3_MOG2`
- FPS substantially higher than old `ONLINE_CALIBRATED`
- P95 latency substantially lower than old `ONLINE_CALIBRATED`
- Energy/frame <= `P3_MOG2`
- no dependency on CDnet category labels inside `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`

## Stage 5: Cross-Dataset Runs

Run LASIESTA, SBI2015, and BMC only after `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` is validated on CDnet. If smoke or targeted CDnet fails, stop and fix the guarded controller first.
