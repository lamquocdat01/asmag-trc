# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2D Report

## Phase Recap

Phase 8C-2 fixed the earlier over-intervention problem only partially: detector use and event/foreground handling were still too broad for a guarded online smoke path.

Phase 8C-2B restored sparse detector behavior. Its dry-run completed 32/32 with no failed jobs, proposed intervention rate 0.2000, proposed detector request rate 0.0450, normal-frame proposed interventions 0, guard alignment 1.0000, and block-only rate 0.1550. It did not run live because cubicle proposed known-event recall was only 0.2020.

Phase 8C-2C added an event/foreground block-only override. Its dry-run completed 32/32 with no failed jobs, proposed intervention rate 0.3325, proposed detector request rate 0.0500, block-only rate 0.2825, event/foreground block-only rate 0.2750, normal-frame proposed interventions 0, guard alignment 1.0000, bridgeEntry event FN 0, bridgeEntry detector budget 15/15, continuousPan proposed intervention rate 0.0400, and cubicle proposed known-event recall 0.3535. It did not run live because cubicle coverage was still below gate.

## 8C-2D Change

8C-2D adds a narrow cubicle-like event-continuity no-detector fallback proposal path on top of 8C-2C.

The path is enabled only by the 8C-2D configs and requires:
- deterministic guarded evaluation to be active;
- exact cubicle-like video context;
- active event memory;
- non-PTZ context and configured PTZ exclusions;
- high event/foreground or foreground-loss risk, or continuing-event risk with foreground risk;
- detector-like or fallback current action;
- per-video cubicle-like proposal cap and cooldown.

When active, the path logs `ai_cubicle_like_event_continuity_active`, `ai_cubicle_like_event_continuity_reason`, `ai_cubicle_like_no_detector`, `ai_cubicle_like_safe_replacement_source`, `ai_cubicle_like_rejected_reason`, `ai_cubicle_like_cap_used`, `ai_cubicle_like_is_non_ptz_context`, and `ai_cubicle_like_camera_motion_score`.

The path does not request detector. Detector requests remain limited to the existing event-refresh-specific sparse policy.

## Dry-Run Validation

Commands run:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2d_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2d_dryrun
```

The dry-run completed 32/32 jobs with 0 failed jobs.

Summary:
- Proposed intervention rate: 0.37125
- Proposed detector request rate: 0.04375
- Block-only rate: 0.32750
- Event/foreground block-only rate: 0.30625
- Cubicle-like no-detector proposal rate: 0.05375
- Normal-frame proposed interventions: 0
- Guard alignment: 1.00000
- Cubicle proposed known-event recall: 0.76768
- Cubicle event FN count: 17
- Cubicle proposed event FN count: 17
- Cubicle unprotected event FN count: 0
- BridgeEntry event FN count: 0
- BridgeEntry detector budget max: 8, improved from 8C-2C's 15
- continuousPan proposed intervention rate: 0.04000, matching the 8C-2C guardrail

The cubicle recall improved from 0.3535 in 8C-2C to 0.7677 in 8C-2D. This passes the phase minimum of 0.70 but misses the aspirational 0.80 target.

## Live Validation

Live smoke was not run.

Reason: the dry-run proposed intervention rate was 0.37125. This is below the hard stop of 0.40 but above the preferred/live selectivity line of 0.35, so live was intentionally held back.

## Pass/Fail

8C-2D is a partial technical success but does not pass for live promotion.

Pass:
- 32/32 completed, 0 failed
- Guard alignment 1.0000
- Proposed detector request rate 0.04375, below 0.10
- Normal-frame proposed interventions 0
- Cubicle proposed known-event recall 0.7677, above the 0.70 phase minimum
- Cubicle unprotected proposed event FN reduced to 0
- BridgeEntry event FN remains 0
- BridgeEntry detector budget improved versus 8C-2C
- continuousPan proposed intervention remains 0.04
- No PTZ-targeted, targeted CDnet, full CDnet, or cross-dataset run was executed

Fail / hold:
- Proposed intervention rate 0.37125 remains above the preferred 0.35 live gate.
- Cubicle recall remains below the target 0.80.

## Root Cause And Next Fix

The no-detector cubicle continuity path works, but the 8C-2C event/foreground block-only baseline is already near the intervention ceiling. Adding enough cubicle continuity coverage to pass the 0.70 recall minimum pushes aggregate proposed interventions above the preferred 0.35 threshold.

The next fix should keep the cubicle no-detector path, then reclaim proposal budget from non-cubicle event/foreground block-only frames with per-scene caps or narrower event-continuity criteria. The likely goal is to preserve cubicle recall around 0.70-0.80 while reducing non-cubicle block-only proposals by at least 18 frames across the 800-frame smoke set.

## Safety Confirmation

Default guarded behavior remains unchanged: the default guarded config still has `ai_intervention_enabled: false`.

PTZ-targeted remains not allowed.

No ONLINE_CALIBRATED, P1, P2, P3, FAST, or base ASMAG_TR_CONTROLLER behavior was intentionally modified for this phase. The 8C-2D behavior is isolated behind the new 8C-2D guarded config keys.
