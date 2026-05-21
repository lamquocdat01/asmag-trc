# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2J Exact-Cubicle Live Rescue Report

Date: 2026-05-14

Status: passes all allowed 8C-2J stages.

Phase 8C-2J adds a narrow exact `shadow/cubicle` late-event no-detector rescue for frame-1560-like unsafe empty/fallback misses after the existing pre-signal, stabilizer, non-cubicle guards, lowFramerate retighten, sparse detector policy, and final normal-frame suppressor remain in place.

## Implementation

- Added an exact `shadow/cubicle` late-event rescue path guarded by deterministic mode, active event memory, unsafe empty/fallback action, event/foreground score thresholds, PTZ/global-motion rejection, per-video cap, and cooldown.
- The rescue proposes only a no-detector protected fallback. It does not request detector and is blocked from detector routing when `ai_exact_cubicle_late_event_rescue_allow_detector: false`.
- Existing exact-cubicle pre-signal and stabilizer paths remain in place. The final normal-frame suppressor still runs after proposal checks and can suppress the late rescue.
- Non-cubicle guards, including fountain01 quiet guard, lowFramerate retighten, sparse detector policy, bridgeEntry behavior, continuousPan cap, and tramCrossroad_1fps behavior, were not broadened.

## Configs and outputs

- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2j_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2j_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2j_live.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2j_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2j_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2j_live/`

## Validation

Compile:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Result: pass.

Smoke dry-run:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2j_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2j_dryrun
```

Result: pass. Jobs completed 32/32, failed 0. Metrics: FMeasure 0.32426, Event_F1 0.59763, Activation 0.30375, Avg_FPS 17.91204, P95 latency 340.44474 ms, proposed intervention rate 0.32750, detector request rate 0.05375, normal-frame proposals 0, cubicle recall 0.86364, cubicle unprotected FN 0, bridgeEntry event FN 0, continuousPan proposal rate 0.05000, tramCrossroad_1fps proposal rate 0.00000. Late-event rescue frames 4, all no-detector.

Targeted mini dry-run:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2j_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2j_dryrun
```

Result: pass. Jobs completed 24/24, failed 0. Metrics: FMeasure 0.33742, Event_F1 0.56913, Activation 0.62500, Avg_FPS 16.63252, P95 latency 375.03676 ms, proposed intervention rate 0.23833, detector request rate 0.02000, normal-frame proposals 0, cubicle recall 0.82828, cubicle unprotected FN 0, bridgeEntry event FN 0, continuousPan proposal rate 0.04000, tramCrossroad_1fps proposal rate 0.00000, tramCrossroad_1fps detector request 0.00000, fountain01 proposal 0.00000, fountain01 detector request 0.00000, fountain02 normal-frame false interventions 0. Late-event rescue frames 4, all no-detector.

Targeted mini live:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2j_live.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2j_live
```

Result: pass. Jobs completed 24/24, failed 0. Metrics: FMeasure 0.34562, Event_F1 0.54909, Activation 0.59000, Avg_FPS 17.76615, P95 latency 307.53556 ms, intervention/proposal rate 0.27333, detector request rate 0.02500, normal-frame interventions/proposals 0, guard alignment 1.00000, cubicle recall 0.89899, cubicle unprotected FN 0, bridgeEntry event FN 0, continuousPan proposal rate 0.05000, tramCrossroad_1fps proposal rate 0.00000, tramCrossroad_1fps detector request 0.00000, fountain01 proposal 0.00000, fountain01 detector request 0.00000, fountain02 normal-frame false interventions 0. Late-event rescue frames 4, all no-detector.

Frame 1560 status in targeted mini live: present, event state `TP`, action `FALLBACK_P3_POLICY`, detector requested 0, active memory 1, event score 0.88681, foreground-loss score 0.68408. It is no longer an unprotected FN. The late-event rescue did not fire on frame 1560 because the final action was already outside the unsafe empty/fallback action set (`action_not_unsafe_empty_fallback`).

## Comparison to 8C-2I targeted mini live

- Cubicle recall improved from 0.80808 to 0.89899.
- Cubicle unprotected FN improved from 1 to 0.
- Detector request rate decreased from 0.03000 to 0.02500.
- Normal-frame interventions remained 0.
- continuousPan remained capped at 0.05000.
- tramCrossroad_1fps remained controlled at 0.00000 proposal and 0.00000 detector request.
- fountain01 remained quiet at 0.00000 proposal and 0.00000 detector request.
- fountain02 normal-frame false interventions remained 0.
- bridgeEntry event FN remained 0.

No full CDnet, Step 3 targeted category, PTZ-targeted standalone, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched for this phase. Step 3 targeted category dry-run is recommended next, but it was not run automatically.
