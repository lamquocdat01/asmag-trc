# ASMAG-TR Controller Online Guarded Step 4D2 SnowFall Candidacy Report

Date: 2026-05-17

## Scope

Step 4D2 used the same residual-risk subset as Step 4B through Step 4D: 14 videos, 9 categories, 4 pipelines, 56 planned jobs.

The run was dry-run only. No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

Output root:

`outputs/asmag_tr_controller_online_guarded_cdnet_step4d2_snowfall_risk_subset_dryrun/`

Config:

`configs/asmag_tr_controller_online_guarded_cdnet_step4d2_snowfall_risk_subset_dryrun.yaml`

## Implementation

Step 4D2 added an exact-video `badWeather/snowFall` actual-FN unsafe-action no-detector rescue path. For dry-run/frame-log actual FN rows, unsafe `CLOSED_EMPTY_ACC` / `CLOSED_EMPTY_P3_FALLBACK` actions can now trigger rescue without requiring cap or closed-empty budget exhaustion, while retaining active-memory, localized weather guard, score, final-normal, and no-detector constraints.

Step 4D2 also added an exact-video `thermal/lakeSide` drift recap path intended to trim only already-softened non-FN/non-rescue lakeSide frames when the final proposal rate drifts above 0.50000.

## Execution

Compile passed:

`python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py`

The residual-risk subset completed:

| Item | Result |
|---|---:|
| Planned jobs | 56 |
| Completed jobs | 56 |
| Failed jobs | 0 |

Compare completed for the Step 4D2 output root.

## Aggregate Metrics

| Metric | Step 4D2 |
|---|---:|
| FMeasure | 0.29756 |
| Event_F1 | 0.63983 |
| Activation | 0.38357 |
| Avg_FPS | 23.38464 |
| P95 latency ms | 429.25865 |
| Proposal rate | 0.33929 |
| Detector request rate | 0.01714 |
| Block-only rate | 0.32214 |
| Event/foreground block-only rate | 0.24571 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## SnowFall Comparison

| Run | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
|---|---:|---:|---:|---:|---:|
| Step 4 full 2Q2 | 0.29000 | 0.03000 | 22 | 12 | 10 |
| Step 4D subset | 0.28000 | 0.00000 | 22 | 12 | 10 |
| Step 4D2 subset | 0.30000 | 0.00000 | 23 | 16 | 7 |

Step 4D2 improved snowFall unprotected FN from 10 to 7, but this misses the acceptable gate of <= 6.

## SnowFall Rescue Behavior

| Behavior | Count |
|---|---:|
| Actual-FN rescue candidates | 22 |
| Actual-FN rescue activations | 12 |
| No-detector actual-FN rescues | 12 |
| Actual-FN rescue-protected event-FN frames | 12 |
| Budget-available actual-FN rescues | 12 |
| Final-normal rescue suppressions | 0 |
| Possible mask-quality rows | 0 |

The new candidacy path worked: actual FN plus unsafe closed-empty action was accepted even when closed-empty budget was available. The remaining miss is cap pressure: 10 actual-FN candidates were rejected as `snowfall_actual_fn_rescue_cap_exhausted`. The remaining unprotected FN rows were six closed-empty actual-FN rows after the actual-FN cap was exhausted, plus one `DETECT_ACC` row that remains a mask-quality/watch exposure rather than a detector-heavy path.

## SnowFall Proposal And Detector Behavior

SnowFall proposal stayed controlled at 0.30000, below the preferred 0.40000 and accepted 0.45000 ceilings. Detector request stayed at 0.00000, so the no-detector constraint held.

## LakeSide Drift Recheck

| Metric | Step 4D2 |
|---|---:|
| Proposal | 0.52000 |
| Detector | 0.00000 |
| Event FN | 53 |
| Protected FN | 48 |
| Unprotected FN | 5 |
| Foreground-loss soft trims | 7 |
| High-score soft trims | 5 |
| Drift recap trims | 0 |
| Total trims | 12 |
| Accidental hard trims | 0 |
| Accidental rescue trims | 0 |

LakeSide still fails the 0.50000 proposal gate. Frame-level review shows the remaining four soft candidate frames were encountered before the one-pass final proposal pressure was known and were rejected as `target_rate_satisfied`; later pressure was hard-protected. The drift recap therefore needs a two-pass or early-reserve design that can retain a small trim buffer for already-soft non-FN/non-rescue frames without trimming hard-protected or rescue-protected event-FN frames.

## Carry-Over Status

| Video | Step 4D2 Status |
|---|---|
| thermal/lakeSide | Fail: proposal 0.52000 > 0.50000; detector 0.00000; unprotected FN 5 |
| intermittentObjectMotion/sofa | Fail: proposal 0.35000, detector 0.00000, unprotected FN 8; exceeds acceptable carry-over FN <= 6 |
| badWeather/snowFall | Fail: proposal 0.30000, detector 0.00000, unprotected FN 7; improved but above acceptable <= 6 |
| lowFramerate/port_0_17fps | Watch: detector 0.09000, unprotected FN 4 |
| intermittentObjectMotion/parking | Fail/watch: proposal 0.44000, detector 0.00000, unprotected FN 22; protection-aware carry-over regressed |
| shadow/copyMachine | Pass by proposal/detector gate: proposal 0.49000, detector 0.00000, unprotected FN 2 |
| turbulence/turbulence2 | Pass: proposal 0.29000, detector 0.00000, unprotected FN 0 |
| lowFramerate/tunnelExit_0_35fps | Watch: detector 0.00000, unprotected FN 2 |
| shadow/cubicle | Pass: recall 0.91919, detector 0.02000, unprotected FN 0 |
| PTZ/continuousPan | Pass: proposal 0.04000, detector 0.01000, event FN 0 |
| PTZ/intermittentPan | Pass: proposal 0.01000, detector 0.00000, unprotected FN 0 |
| dynamicBackground/fountain01 | Pass: proposal 0.00000 |
| dynamicBackground/fountain02 | Pass: normal-frame false interventions 0 |
| nightVideos/bridgeEntry | Pass: event FN 0 |

## Gate Table

| Gate | Result |
|---|---|
| 56 planned jobs completed, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | Pass |
| Normal-frame proposals = 0 | Pass |
| Guard alignment >= 0.95 | Pass |
| snowFall detector request <= 0.03 | Pass |
| snowFall proposal <= 0.45 | Pass |
| snowFall unprotected FN improves materially versus 10 | Pass |
| snowFall unprotected FN <= 4 preferred | Fail |
| snowFall unprotected FN <= 6 acceptable | Fail |
| Hard fail if snowFall unprotected FN >= 10 | Pass |
| No final normal suppressor regression | Pass |
| lakeSide proposal <= 0.50 | Fail |
| lakeSide detector <= 0.02 | Pass |
| lakeSide unprotected FN <= 8 preferred | Pass |
| sofa proposal <= 0.35 preferred | Pass |
| sofa detector <= 0.03 | Pass |
| sofa unprotected FN <= 6 acceptable | Fail |
| parking remains within protection-aware gate | Fail |
| copyMachine remains within accepted gate | Pass |
| turbulence2 remains within accepted gate | Pass |
| tunnelExit remains within accepted detector gate | Pass |
| cubicle recall >= 0.80 and FN 0 | Pass |
| continuousPan remains controlled | Pass |
| intermittentPan remains controlled | Pass |
| fountain01 remains quiet | Pass |
| fountain02 normal-frame false interventions = 0 | Pass |
| bridgeEntry event FN = 0 | Pass |
| No forbidden validation launched | Pass |

## Conclusion

Step 4D2 residual-risk subset dry-run fails.

The narrow snowFall candidacy fix moved in the right direction but was capped too tightly for the actual-FN burst. The lakeSide drift recap did not restore the 0.50000 proposal ceiling because the one-pass trim ordering saw remaining soft candidates too early, then later preserved hard-protected pressure.

Recommended next narrow fix:

1. Step 4D3 snowFall: raise or adapt the exact actual-FN rescue cap for cap-exhausted actual-FN unsafe rows while keeping proposal <= 0.45 and detector <= 0.03.
2. Step 4D3 lakeSide: convert drift recap into a small early reserve/two-pass-equivalent trim buffer for already-soft non-FN/non-rescue frames, with accidental hard/rescue trim count required to remain 0.
3. Recheck sofa and parking carry-over in the same residual subset before any full CDnet dry-run.

Full CDnet rerun remains held.
