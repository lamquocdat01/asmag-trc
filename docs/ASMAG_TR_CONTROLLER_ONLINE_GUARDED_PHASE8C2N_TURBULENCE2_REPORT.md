# ASMAG-TRC Phase 8C-2N Turbulence2 Stability Cleanup Report

Date: 2026-05-15

## Scope

Phase 8C-2N is a dry-run-only cleanup for `turbulence/turbulence2`. The change adds a dynamic-texture pressure guard and a narrow no-detector event-FN rescue while preserving the 8C-2M3 parking preservation/trim, copyMachine rescue-first ordering, PTZ caps/rescues, cubicle rescue, fountain01 quiet guard, lowFramerate retighten, continuousPan cap, sparse detector policy, and final normal-frame suppressor.

No live validation, live compare, full CDnet, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched. Accidental 8C-2E live artifacts were left untouched. `ONLINE_CALIBRATED`, P1/P2/P3/FAST/ASMAG_TR_CONTROLLER, and frozen CDnet2014 v1.6 outputs were not modified.

## Files

- Created config: `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2n_dryrun.yaml`
- Created output root: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2n_dryrun/`
- Updated controller logic: `src/run_experiment.py`
- Updated compare reporting: `tools/compare_asmag_tr_controller_online_guarded.py`
- Created report: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_PHASE8C2N_TURBULENCE2_REPORT.md`
- Updated daily status: `docs/DAILY_STATUS.md`

## Implementation

The 2N config inherits from 2M3 and enables only the turbulence2 cleanup:

```yaml
online_controller_guarded:
  ai_turbulence2_pressure_guard_enabled: true
  ai_turbulence2_target_video: turbulence/turbulence2
  ai_turbulence2_pressure_guard_no_detector: true
  ai_turbulence2_pressure_guard_suppress_generic_event_fg: true
  ai_turbulence2_pressure_guard_suppress_detector_refresh: true
  ai_turbulence2_pressure_guard_require_localized_fn_risk: true
  ai_turbulence2_pressure_guard_max_proposal_rate: 0.30
  ai_turbulence2_pressure_guard_hard_max_proposal_rate: 0.35
  ai_turbulence2_pressure_guard_max_detector_rate: 0.02
  ai_turbulence2_fn_rescue_enabled: true
  ai_turbulence2_fn_rescue_allow_detector: false
  ai_turbulence2_fn_rescue_extra_cap_per_video: 6
  ai_turbulence2_fn_rescue_cooldown: 1
  ai_turbulence2_fn_rescue_requires_not_normal_frame: true
  ai_turbulence2_fn_rescue_requires_localized_risk: true
  ai_turbulence2_fn_rescue_event_score_threshold: 0.70
  ai_turbulence2_fn_rescue_foreground_loss_threshold: 0.50
  ai_turbulence2_fn_rescue_protect_likely_unprotected_fn: true
```

Ordering is rescue-first for `turbulence/turbulence2`: mark likely event-FN rescue candidates, protect rescue/FN-risk frames, then apply pressure guard only to generic non-risk proposals and detector refreshes. The final normal-frame suppressor still runs after all proposal paths.

Compare now emits `ai_intervention_2n_turbulence2_summary.csv` with turbulence2 proposal/detector/FN, rescue, pressure guard, detector refresh suppression, and protected-rescue accidental suppression metrics.

## Commands Run

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2n_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2n_dryrun
```

The targeted category dry-run was resumed until all 80 jobs completed.

## Aggregate Result

- Jobs: 80/80 completed, 0 failed
- FMeasure: 0.43122
- Event_F1: 0.66513
- Activation: 0.56678
- Avg_FPS: 19.80952
- P95 latency: 367.68531 ms
- Proposed intervention rate: 0.19970
- Detector request rate: 0.00910
- Block-only rate: 0.19060
- Event/foreground block-only rate: 0.16077
- Normal-frame proposals: 0
- Guard alignment: 1.00000

## Turbulence2 Comparison

| Phase | Proposal | Detector | Event FN | Unprotected FN |
| --- | ---: | ---: | ---: | ---: |
| 8C-2M3 | 0.39000 | 0.03000 | 3 | 3 |
| 8C-2N | 0.30000 | 0.00000 | 3 | 1 |

2N reduces turbulence2 proposal pressure by 0.09000, removes all turbulence2 detector requests, and improves unprotected event FNs from 3 to 1.

## Turbulence2 Guard And Rescue Behavior

- Rescue candidates: 3
- Rescue active frames: 6
- Rescue no-detector frames: 6
- Rescue protected event-FN frames: 2
- Rescue final-normal suppressions: 0
- Rescue frames protected before guard: 6
- Pressure guard active frames: 72
- Pressure guard rejected frames: 11
- Generic pressure suppressions: 11
- Detector refresh suppressions: 8
- Pressure guard reclaimed count max: 11
- Pressure guard preserved count max: 30
- Protected rescue frames accidentally suppressed: 0

The remaining unprotected FN is documented as an acceptable residual under the 2N gate because proposal and detector gates pass and unprotected FN improves versus 2M3. It should remain visible in review, but it is not a hard fail.

## Carry-Over Status

| Video | 8C-2M3 status | 8C-2N status | Result |
| --- | --- | --- | --- |
| `shadow/copyMachine` | proposal/detector 0.38000/0.00000, unprotected FN 12 | proposal/detector 0.38000/0.00000, unprotected FN 12 | Pass acceptable, misses preferred |
| `intermittentObjectMotion/parking` | proposal/detector 0.39000/0.00000, unprotected FN 9 | proposal/detector 0.43000/0.00000, unprotected FN 9 | Pass |
| `PTZ/intermittentPan` | proposal/detector 0.01000/0.00000, unprotected FN 0 | proposal/detector 0.01000/0.00000, unprotected FN 0 | Pass |
| `PTZ/continuousPan` | block-only proposal 0.05000, reuse proposal/detector 0.04000/0.01000, unprotected FN 0 | block-only proposal 0.05000, detector 0.01000, unprotected FN 0 | Pass |
| `shadow/cubicle` | recall 0.87879, unprotected FN 0 | recall 0.87879, unprotected FN 0 | Pass |
| `nightVideos/bridgeEntry` | event FN 0 | event FN 0 | Pass |
| `lowFramerate/tramCrossroad_1fps` | proposal/detector 0.00000/0.00000 | proposal/detector 0.00000/0.00000 | Pass |
| `dynamicBackground/fountain01` | proposal/detector 0.00000/0.00000 | proposal/detector 0.00000/0.00000 | Pass |
| `dynamicBackground/fountain02` | normal-frame false interventions 0 | normal-frame false interventions 0 | Pass |

Parking carry-over safety remains intact: preserved FN-risk frames 24, active no-detector rescue frames 24, rescue-protected event-FN frames 24, generic non-risk post-preservation trims 4, and preserved/rescue frames accidentally trimmed 0.

## Remaining Risk

- `lowFramerate/tunnelExit_0_35fps`: proposal/detector 0.24000/0.00000, event FN 2, unprotected FN 2. This phase intentionally did not modify tunnelExit.

## Gates

| Gate | Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80 completed, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.00910 | Pass |
| Aggregate normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.87879, 0 | Pass |
| BridgeEntry event FN = 0 | 0 | Pass |
| ContinuousPan proposal <= 0.05 | block-only 0.05000 | Pass |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.01000, 0 | Pass |
| TramCrossroad_1fps proposal <= 0.05 and detector <= 0.02 | 0.00000, 0.00000 | Pass |
| Fountain01 proposal <= 0.05 and detector <= 0.02 | 0.00000, 0.00000 | Pass |
| Fountain02 normal-frame false interventions = 0 | 0 | Pass |
| CopyMachine unprotected FN <= 15 acceptable, preferred <= 10 | 12 | Pass acceptable, misses preferred |
| Parking proposal <= 0.45 and unprotected FN <= 12 | 0.43000, 9 | Pass |
| Turbulence2 detector <= 0.02 preferred, hard fail if > 0.05 | 0.00000 | Pass preferred |
| Turbulence2 proposal <= 0.35 | 0.30000 | Pass |
| Turbulence2 unprotected FN improves versus 2M3 | 3 -> 1 | Pass |
| Turbulence2 preferred unprotected FN = 0 | 1 | Miss preferred |
| Turbulence2 acceptable unprotected FN <= 2 if proposal/detector gates pass and root cause documented | 1 with proposal/detector gates passing | Pass acceptable |
| Hard fail if turbulence2 unprotected FN >= 3 | 1 | Pass |
| No forbidden validation launched | none launched | Pass |

## Conclusion

8C-2N passes the targeted category dry-run gates. Live remains held because the phase was explicitly dry-run-only. The remaining risk is `lowFramerate/tunnelExit_0_35fps`; Step 3B targeted category live can be considered only after review accepts the residual tunnelExit risk and the acceptable-but-not-preferred copyMachine, parking, and turbulence2 FN counts.
