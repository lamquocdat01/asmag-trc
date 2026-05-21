# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 7C Ablation Plan

Phase 7C is a causal PTZ action-schedule ablation for `ASMAG_TR_CONTROLLER_ONLINE_GUARDED` only. It is diagnostic smoke validation, not a production behavior change.

## Guardrails

- Do not run PTZ-targeted, targeted CDnet, full CDnet, LASIESTA, SBI2015, or BMC.
- Do not overwrite frozen CDnet2014 v1.6 outputs.
- Do not modify old `ONLINE_CALIBRATED` or baseline pipelines.
- Default guarded behavior remains unchanged when `online_controller_guarded.ablation_mode_enabled: false`.

## Config Switch

```yaml
online_controller_guarded:
  ablation_mode_enabled: false
  ablation_policy_name: null
```

When enabled, `ablation_policy_name` must be one of the Phase 7C policy names.

## Smoke Scope

The Phase 7C configs inherit the guarded smoke config, run only `ASMAG_TR_CONTROLLER_ONLINE_GUARDED`, and narrow videos to:

- `PTZ/continuousPan`
- `PTZ/twoPositionPTZCam`
- `nightVideos/bridgeEntry`
- `shadow/cubicle`
- `dynamicBackground/fountain02`
- `turbulence/turbulence2`

Each policy writes to:

```text
outputs/asmag_tr_controller_online_guarded_ablation_phase7c/<policy_name>/
```

## Policies

- `CP_ANCHOR_EVERY_1`: detector-like P3 anchor every continuous-pan frame.
- `CP_ANCHOR_EVERY_2`: detector-like P3 anchor every 2 continuous-pan frames; no ACC reuse or lightweight P3 fallback.
- `CP_ANCHOR_EVERY_3_ACC_INTER`: detector-like P3 anchor every 3 continuous-pan frames; quality-gated `LIGHTWEIGHT_MASK_ACC` between anchors; no ACC reuse.
- `CP_DETECT_ACC_EVERY_2`: `DETECT_ACC` every 2 continuous-pan frames; quality-gated `LIGHTWEIGHT_MASK_ACC` between anchors.
- `CP_FALLBACK_P3_EVERY_2`: `FALLBACK_P3_GUARD` every 2 continuous-pan frames; quality-gated `LIGHTWEIGHT_MASK_ACC` between anchors.
- `TP_BURST_2_THEN_FAST`: disable teacher ranker; use 2 detector-burst frames after position switch/jump, then Phase 6C fast path.
- `TP_BURST_3_THEN_FAST`: disable teacher ranker; use 3 detector-burst frames after position switch/jump, then Phase 6C fast path.
- `TP_PHASE6C_ONLY`: disable teacher ranker and keep Phase 6C position-switch handling.
- `NONPTZ_TEACHER_OFF`: keep teacher inactive outside confirmed camera motion on non-PTZ videos.

## Validation

```powershell
python -m py_compile src\run_experiment.py tools\compare_phase7c_ablations.py
python src\run_experiment.py --config configs\ablation_phase7c_cp_anchor_every_1.yaml
python src\run_experiment.py --config configs\ablation_phase7c_cp_anchor_every_2.yaml
python src\run_experiment.py --config configs\ablation_phase7c_cp_anchor_every_3_acc_inter.yaml
python src\run_experiment.py --config configs\ablation_phase7c_detect_acc_every_2.yaml
python src\run_experiment.py --config configs\ablation_phase7c_fallback_p3_every_2.yaml
python src\run_experiment.py --config configs\ablation_phase7c_tp_burst_2_then_fast.yaml
python src\run_experiment.py --config configs\ablation_phase7c_tp_burst_3_then_fast.yaml
python src\run_experiment.py --config configs\ablation_phase7c_tp_phase6c_only.yaml
python src\run_experiment.py --config configs\ablation_phase7c_nonptz_teacher_off.yaml
python tools\compare_phase7c_ablations.py --root outputs\asmag_tr_controller_online_guarded_ablation_phase7c
```

## Decision Criteria

Recommend Phase 7D only if one ablation shows:

- `continuousPan` FMeasure >= old online - 0.02
- `continuousPan` closed-empty <= 0.02
- `twoPositionPTZCam` FMeasure >= 0.78
- `bridgeEntry` final closed-empty event FN = 0
- `cubicle` and non-PTZ behavior safe
- aggregate FPS >= 30, or the schedule is plausibly optimizable to >= 30

