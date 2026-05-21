# ASMAG-TR Controller Online Guarded Step 4C sofa Rescue Report

Date: 2026-05-17

## Scope

Step 4C was a dry-run-only residual-risk subset pass for `intermittentObjectMotion/sofa` intermittent-object no-detector rescue.

- Videos: 14
- Categories: 9
- Pipelines: 4
- Planned jobs: 56
- Completed jobs: 56
- Failed jobs: 0
- Output root: `outputs/asmag_tr_controller_online_guarded_cdnet_step4c_sofa_risk_subset_dryrun/`
- Config: `configs/asmag_tr_controller_online_guarded_cdnet_step4c_sofa_risk_subset_dryrun.yaml`

Subset videos:

1. `thermal/lakeSide`
2. `intermittentObjectMotion/sofa`
3. `badWeather/snowFall`
4. `lowFramerate/port_0_17fps`
5. `intermittentObjectMotion/parking`
6. `shadow/copyMachine`
7. `turbulence/turbulence2`
8. `lowFramerate/tunnelExit_0_35fps`
9. `shadow/cubicle`
10. `PTZ/continuousPan`
11. `PTZ/intermittentPan`
12. `dynamicBackground/fountain01`
13. `dynamicBackground/fountain02`
14. `nightVideos/bridgeEntry`

## Safety Audit

No live validation, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

The default guarded config remains unchanged with `ai_intervention_enabled: false`. No ONLINE_CALIBRATED, P1, P2, P3, FAST, or ASMAG_TR_CONTROLLER configs were modified. Existing prior output roots were not deleted or overwritten.

## Aggregate Step 4C Metrics

| Metric | Value |
|---|---:|
| FMeasure | 0.31803 |
| Event_F1 | 0.65986 |
| Activation | 0.44143 |
| Avg_FPS | 30.22110 |
| P95 latency | 360.79176 ms |
| Proposal rate | 0.32929 |
| Detector request rate | 0.01643 |
| Block-only rate | 0.31286 |
| Event/foreground block-only rate | 0.24786 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## sofa Comparison

| Phase | Proposal | Detector | Event FN | Protected FN | Unprotected FN |
|---|---:|---:|---:|---:|---:|
| Step 4 full 2Q2 | 0.20000 | 0.03000 | 22 | 12 | 10 |
| Step 4C subset | 0.26000 | 0.00000 | 21 | 21 | 0 |

Step 4C removes the `sofa` unprotected-FN residual while keeping proposal pressure below the preferred 0.35000 ceiling and reducing detector request rate to 0.00000.

## sofa Rescue Behavior

The Step 4C rescue applies only to `intermittentObjectMotion/sofa`. It is no-detector, ordered before generic proposal caps, and does not bypass the final normal-frame suppressor.

Observed sofa counters:

| Counter | Value |
|---|---:|
| Rescue candidates | 15 |
| Rescue activations | 12 |
| Rescue no-detector frames | 12 |
| Rescue cap used | 12 |
| Rescue-protected event-FN frames | 12 |
| Rescue-first protected-before-cap frames | 12 |
| Final-normal suppressed rescue frames | 0 |
| Proposal guard active frames | 31 |
| Proposal guard generic suppressions | 0 |
| Proposal guard skipped rescue frames | 12 |
| Proposal guard final rate | 0.26000 |

Rejected candidate reasons were expected and narrow: 61 frames were not unsafe empty/fallback actions, 16 were already protected, and 3 were rejected after the sofa rescue cap was exhausted.

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Normal proposals | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `thermal/lakeSide` | 0.50000 | 0.00000 | 48 | 48 | 0 | 0 | PASS: Step 4B4 gate preserved |
| `badWeather/snowFall` | 0.30000 | 0.03000 | 22 | 12 | 10 | 0 | Residual watch; not patched in Step 4C |
| `lowFramerate/port_0_17fps` | 0.40000 | 0.08000 | 14 | 10 | 4 | 0 | Residual detector watch; not patched in Step 4C |
| `intermittentObjectMotion/parking` | 0.50000 | 0.00000 | 33 | 29 | 4 | 0 | PASS: protection-aware gate preserved |
| `shadow/copyMachine` | 0.46000 | 0.00000 | 47 | 42 | 5 | 0 | PASS: accepted gate preserved |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | 0 | PASS: accepted gate preserved |
| `lowFramerate/tunnelExit_0_35fps` | 0.31000 | 0.00000 | 2 | 1 | 1 | 0 | PASS: accepted gate preserved |
| `shadow/cubicle` | 0.90000 | 0.02000 | 14 | 14 | 0 | 0 | PASS: recall 0.90909 and FN 0 |
| `PTZ/continuousPan` | 0.04000 | 0.01000 | 0 | 0 | 0 | 0 | PASS: controlled |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | 0 | PASS: controlled |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | 0 | PASS: quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.04000 | 1 | 0 | 1 | 0 | PASS: normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.22000 | 0.05000 | 0 | 0 | 0 | 0 | PASS: event FN 0 |

## Gate Results

| Gate | Result | Evidence |
|---|---|---|
| All planned subset jobs completed, 0 failed | PASS | 56/56 completed, 0 failed |
| Aggregate detector request rate < 0.10 | PASS | 0.01643 |
| Normal-frame proposals = 0 | PASS | 0 |
| Guard alignment >= 0.95 | PASS | 1.00000 |
| sofa detector request <= 0.03 | PASS | 0.00000 |
| sofa proposal <= 0.35 preferred, hard fail if > 0.40 | PASS | 0.26000 |
| sofa unprotected FN improves materially versus 10 | PASS | 10 -> 0 |
| preferred sofa unprotected FN <= 4 | PASS | 0 |
| hard fail if sofa unprotected FN >= 10 | PASS | 0 |
| lakeSide proposal <= 0.50 | PASS | 0.50000 |
| lakeSide detector <= 0.02 | PASS | 0.00000 |
| lakeSide unprotected FN <= 8 preferred | PASS | 0 |
| parking remains within protection-aware gate | PASS | proposal 0.50000, unprotected FN 4 |
| copyMachine remains within accepted gate | PASS | proposal 0.46000, detector 0.00000 |
| turbulence2 remains within accepted gate | PASS | unprotected FN 0 |
| tunnelExit remains within accepted gate | PASS | detector 0.00000, unprotected FN 1 |
| cubicle recall >= 0.80 and FN 0 | PASS | recall 0.90909, unprotected FN 0 |
| continuousPan remains controlled | PASS | proposal 0.04000, event FN 0 |
| intermittentPan remains controlled | PASS | proposal 0.01000, unprotected FN 0 |
| fountain01 remains quiet | PASS | proposal 0.00000 |
| fountain02 normal-frame false interventions = 0 | PASS | 0 |
| bridgeEntry event FN = 0 | PASS | 0 |
| No forbidden validation launched | PASS | dry-run subset and compare only |

## Decision

Step 4C residual-risk subset dry-run passes.

Full CDnet rerun remains held. Recommended next work is Step 4D `badWeather/snowFall` weather-aware rescue before a full CDnet rerun, unless the team chooses an interim full CDnet dry-run after lakeSide plus sofa stabilization.
