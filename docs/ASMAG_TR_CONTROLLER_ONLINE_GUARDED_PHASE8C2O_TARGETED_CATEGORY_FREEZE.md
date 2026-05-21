# ASMAG-TRC Phase 8C-2O Targeted Category Dry-Run Freeze

Date: 2026-05-15

## Executive Summary

Phase 8C-2O is frozen as the official targeted category dry-run candidate for ASMAG-TRC Step 3 review.

8C-2O passes the configured targeted category dry-run gates with 80/80 jobs completed and 0 failed. This freeze does not mark targeted category live success, and it does not mark full CDnet success. Larger validation remains staged and requires explicit authorization.

## Validation Scope

| Item | Scope |
| --- | --- |
| Videos | 20 |
| Categories | 9 |
| Mode | Dry-run only |
| Output root | `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun/` |
| Live validation | Not launched |
| Live compare | Not launched |
| Full CDnet | Not launched |
| PTZ-targeted standalone | Not launched |
| LASIESTA/SBI2015/BMC/cross-dataset | Not launched |

## Aggregate Metrics

| Metric | 8C-2O Result |
| --- | ---: |
| Jobs completed | 80/80 |
| Failed jobs | 0 |
| FMeasure | 0.40060 |
| Event_F1 | 0.66904 |
| Activation | 0.47128 |
| Avg_FPS | 22.57987 |
| P95 latency | 418.20077 ms |
| Proposed intervention rate | 0.21587 |
| Detector request rate | 0.01921 |
| Block-only rate | 0.19666 |
| Event/foreground block-only rate | 0.15875 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## Category And Video Risk Summary

| Category/Video | 8C-2O Status | Freeze Assessment |
| --- | --- | --- |
| `shadow/cubicle` | recall 0.87879, unprotected FN 0 | Pass |
| `nightVideos/bridgeEntry` | event FN 0 | Pass |
| `PTZ/continuousPan` | proposal/detector 0.05000/0.01000, unprotected FN 0 | Pass |
| `PTZ/intermittentPan` | proposal/detector 0.01000/0.00000, unprotected FN 0 | Pass |
| `shadow/copyMachine` | proposal/detector 0.38000/0.00000, unprotected FN 12 | Accepted residual |
| `intermittentObjectMotion/parking` | proposal/detector 0.43000/0.00000, unprotected FN 9 | Accepted residual |
| `turbulence/turbulence2` | proposal/detector 0.11000/0.00000, unprotected FN 2 | Accepted residual |
| `lowFramerate/tunnelExit_0_35fps` | proposal/detector 0.30000/0.00000, unprotected FN 1 | Accepted residual |
| `lowFramerate/tramCrossroad_1fps` | proposal/detector 0.00000/0.00000 | Pass |
| `lowFramerate/turnpike_0_5fps` | proposal/detector 0.01000/0.00000, unprotected FN 0 | Pass |
| `dynamicBackground/fountain01` | proposal/detector 0.00000/0.00000 | Pass |
| `dynamicBackground/fountain02` | normal-frame false interventions 0 | Pass |

## Step 3 Phase Lineage

| Phase | Result |
| --- | --- |
| 8C-2K | Fixed `PTZ/intermittentPan` and established the PTZ intermittentPan cap/rescue behavior. |
| 8C-2L | Failed `shadow/copyMachine` because the copyMachine cap over-constrained useful protection. |
| 8C-2L2 | Fixed copyMachine rescue-first ordering and restored intermittentPan carry-over. |
| 8C-2M | Failed parking because the parking cap was too aggressive and worsened unprotected FNs. |
| 8C-2M2 | Fixed parking FN protection, but over-preserved proposals above the hard parking proposal gate. |
| 8C-2M3 | Trimmed parking safely after preservation, with 0 preserved/rescue frames accidentally trimmed. |
| 8C-2N | Reduced turbulence2 detector pressure and FN risk using a dynamic-texture pressure guard and no-detector rescue. |
| 8C-2O | Reduced tunnelExit FN risk, preserved detector-sparse behavior, and passed the targeted category dry-run gates. |

## Residual Acceptable Risks

These residuals are accepted for the targeted category dry-run freeze, but they must remain visible in targeted category live review and later full-dataset validation:

| Video | Residual | Reason Accepted For Dry-Run Freeze |
| --- | --- | --- |
| `shadow/copyMachine` | unprotected FN 12 | Within acceptable gate of FN <= 15; detector remains 0.00000. |
| `intermittentObjectMotion/parking` | unprotected FN 9 | Within acceptable gate of FN <= 12; proposal 0.43000 remains under 0.45. |
| `turbulence/turbulence2` | unprotected FN 2 | Within acceptable 2O gate of FN <= 2; detector remains 0.00000 and proposal is 0.11000. |
| `lowFramerate/tunnelExit_0_35fps` | unprotected FN 1 | Improved from 2N FN 2 to 2O FN 1; detector remains 0.00000 and proposal is 0.30000. |

The residuals should be monitored carefully in live because dry-run safety does not prove live success. They should also be revisited before any full CDnet validation claim.

## Gate Table

| Gate | 8C-2O Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.01921 | Pass |
| Aggregate normal-frame proposals = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | 0.87879, 0 | Pass |
| BridgeEntry event FN = 0 | 0 | Pass |
| ContinuousPan proposal <= 0.05 | 0.05000 | Pass |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | 0.01000, 0 | Pass |
| TramCrossroad_1fps controlled | proposal/detector 0.00000/0.00000 | Pass |
| Fountain01 quiet | proposal/detector 0.00000/0.00000 | Pass |
| Fountain02 normal-frame false interventions = 0 | 0 | Pass |
| CopyMachine FN <= 15 acceptable | 12 | Pass |
| Parking FN <= 12 acceptable | 9 | Pass |
| Turbulence2 FN <= 2 acceptable | 2 | Pass |
| TunnelExit FN <= 1 acceptable | 1 | Pass |
| No forbidden validation launched | none launched | Pass |

8C-2O passes the targeted category dry-run gate set.

## Safety Audit

- No live validation was launched in this freeze step.
- No live compare was launched in this freeze step.
- No new experiment was launched in this freeze step.
- No full CDnet, PTZ-targeted standalone, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.
- Accidental 8C-2E live artifacts were excluded from the freeze decision and were not deleted.
- Default guarded config remains unchanged with `ai_intervention_enabled: false`.
- 8C-2O output is dry-run only: `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_dryrun/`.
- `ONLINE_CALIBRATED`, P1/P2/P3/FAST/ASMAG_TR_CONTROLLER, and prior outputs were not modified for this freeze.

## Freeze Decision

8C-2O is frozen as the official targeted category dry-run candidate.

Larger validation remains staged. Step 3B targeted category live can be considered only after explicit authorization and review acceptance of the residual copyMachine, parking, turbulence2, and tunnelExit risks. Full CDnet is not recommended yet and remains held.

## Step 3B Live Readiness Checklist

Before targeted category live is authorized, confirm these live gates are accepted:

| Live Readiness Gate | Required Status |
| --- | --- |
| 80/80 completed, 0 failed | Required |
| Aggregate detector request < 0.10 | Required |
| Normal-frame interventions = 0 | Required |
| Guard alignment >= 0.95 | Required |
| Cubicle recall >= 0.80 and unprotected FN 0 | Required |
| BridgeEntry event FN 0 | Required |
| ContinuousPan <= 0.05 | Required |
| IntermittentPan <= 0.15 and FN 0 | Required |
| TramCrossroad controlled | Required |
| Fountain01 quiet | Required |
| Fountain02 no normal-frame false interventions | Required |
| CopyMachine FN <= 15 acceptable | Required |
| Parking FN <= 12 acceptable | Required |
| Turbulence2 FN <= 2 acceptable | Required |
| TunnelExit FN <= 1 acceptable | Required |
| No forbidden validation launched | Required |

## Step 3B Targeted Category Live Result

Step 3B targeted category live was safely resumed in the existing partial live folder after the partial audit. The runner auto-recovered the stale `baseline/highway/P3_MOG2` row, skipped completed jobs, and completed the remaining jobs in the same output root:

`outputs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2o_live/`

The live run completed technically, and live compare completed, but Step 3B does not pass because four critical FN-protection gates failed.

| Metric | 8C-2O Dry-Run | 8C-2O Live |
| --- | ---: | ---: |
| Jobs completed / failed | 80 / 0 | 80 / 0 |
| FMeasure | 0.40060 | 0.42292 |
| Event_F1 | 0.66904 | 0.66650 |
| Activation | 0.47128 | 0.47928 |
| Avg_FPS | 22.57987 | 16.50218 |
| P95 latency ms | 418.20077 | 484.56976 |
| Intervention/proposal rate | 0.21587 | 0.23357 |
| Detector request rate | 0.01921 | 0.02477 |
| Block-only rate | 0.19666 | 0.20880 |
| Event/foreground block-only rate | 0.15875 | 0.16886 |
| Normal-frame interventions | 0 | 0 |
| Guard alignment | 1.00000 | 1.00000 |

### Live Per-Video Status

| Video | Proposal | Detector | Normal interventions | Event FN / unprotected FN | Detector budget max | Special guard notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `PTZ/continuousPan` | 0.05 | 0.01 | 0 | 0 / 0 | 1 | - |
| `PTZ/intermittentPan` | 0.05 | 0.00 | 0 | 2 / 2 | 0 | pan cap rejected 19, rescue 4 |
| `baseline/highway` | 0.03 | 0.00 | 0 | 0 / 0 | 0 | stale row was safely rerun |
| `baseline/office` | 0.04 | 0.01 | 0 | 0 / 0 | 1 | - |
| `cameraJitter/traffic` | 0.02 | 0.00 | 0 | 0 / 0 | 0 | - |
| `dynamicBackground/canoe` | 0.00 | 0.00 | 0 | 0 / 0 | 0 | - |
| `dynamicBackground/fountain01` | 0.00 | 0.00 | 0 | 0 / 0 | 0 | quiet guard active 100 |
| `dynamicBackground/fountain02` | 0.40 | 0.01 | 0 | 0 / 0 | 1 | normal-frame false interventions 0 |
| `dynamicBackground/overpass` | 0.39 | 0.09 | 0 | 0 / 0 | 9 | detector remains under aggregate gate |
| `intermittentObjectMotion/parking` | 0.43 | 0.00 | 0 | 20 / 14 | 0 | parking rescue 24, post-preservation trim 4 |
| `lowFramerate/tramCrossroad_1fps` | 0.00 | 0.00 | 0 | 0 / 0 | 0 | lowFramerate trim 87, retighten 87 |
| `lowFramerate/tunnelExit_0_35fps` | 0.30 | 0.00 | 0 | 2 / 1 | 0 | tunnel preserve 30 |
| `lowFramerate/turnpike_0_5fps` | 0.01 | 0.00 | 0 | 0 / 0 | 0 | - |
| `nightVideos/bridgeEntry` | 0.32 | 0.08 | 0 | 0 / 0 | 8 | bridgeEntry protection intact |
| `nightVideos/streetCornerAtNight` | 0.34 | 0.02 | 0 | 0 / 0 | 2 | - |
| `nightVideos/tramStation` | 0.34 | 0.10 | 0 | 0 / 0 | 10 | - |
| `shadow/backdoor` | 0.40 | 0.08 | 0 | 0 / 0 | 8 | - |
| `shadow/copyMachine` | 0.39 | 0.00 | 0 | 22 / 18 | 0 | copy cap suppressed 26, rescue 18 |
| `shadow/cubicle` | 0.81 | 0.09 | 0 | 1 / 1 | 9 | cubicle bump 8, late rescue 4 |
| `turbulence/turbulence2` | 0.30 | 0.00 | 0 | 3 / 1 | 0 | turbulence reclaim 9 |

### Live Gate Table

| Gate | Live Result | Status |
| --- | --- | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | 0.02477 | Pass |
| Normal-frame interventions = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Cubicle recall >= 0.80 and unprotected FN = 0 | recall 0.81818, unprotected FN 1 | Fail |
| BridgeEntry event FN = 0 | 0 | Pass |
| ContinuousPan proposal <= 0.05 | 0.05000 | Pass |
| IntermittentPan proposal <= 0.15 and unprotected FN = 0 | proposal 0.05000, unprotected FN 2 | Fail |
| TramCrossroad_1fps proposal <= 0.05 and detector <= 0.02 | proposal/detector 0.00000/0.00000 | Pass |
| Fountain01 proposal <= 0.05 and detector <= 0.02 | proposal/detector 0.00000/0.00000 | Pass |
| Fountain02 normal-frame false interventions = 0 | 0 | Pass |
| CopyMachine unprotected FN <= 15 acceptable | 18 | Fail |
| Parking proposal <= 0.45 and unprotected FN <= 12 | proposal 0.43000, unprotected FN 14 | Fail |
| Turbulence2 proposal <= 0.35 and unprotected FN <= 2 | proposal 0.30000, unprotected FN 1 | Pass |
| TunnelExit_0_35fps proposal <= 0.35 and unprotected FN <= 1 | proposal 0.30000, unprotected FN 1 | Pass |
| No broad detector-heavy behavior | aggregate detector 0.02477, normal interventions 0 | Pass |
| No forbidden validation launched | none launched | Pass |

### Live Failure Root Cause

The live failure is not broad detector-heavy behavior. Aggregate detector pressure, normal-frame suppression, and guard alignment remain safe. The failure is localized to FN protection drift in four videos:

- `shadow/cubicle`: recall remains above 0.80, but one live event FN remains unprotected despite cubicle bump and late rescue.
- `PTZ/intermittentPan`: proposal pressure is controlled at 0.05, but both event FNs remain unprotected under the cap/rescue mix.
- `shadow/copyMachine`: no-detector behavior remains intact, but the rescue-first and cap balance leaves 18 unprotected FNs, above the acceptable live gate of 15.
- `intermittentObjectMotion/parking`: proposal remains under 0.45, but unprotected FNs rise to 14, above the acceptable live gate of 12.

Recommended next patch: keep the 8C-2O aggregate controls unchanged and make the narrowest dry-run-only correction to live-sensitive FN protection for `cubicle`, `intermittentPan`, `copyMachine`, and `parking`. Do not run full CDnet until a new targeted category dry-run and targeted category live pass these gates.

Step 3B targeted category live fails. Step 4 full CDnet dry-run remains held.
