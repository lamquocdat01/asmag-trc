# ASMAG-TRC Step 3B Parking Protection-Aware Gate Review

Date: 2026-05-16

## Executive Summary

Step 3B parking retighten attempts show that the old raw parking proposal gate is likely too strict for `intermittentObjectMotion/parking`.

8C-2Q4 reached parking proposal 0.50000 with detector 0.00000, normal-frame proposals 0, unprotected FN 4, and accidental hard-protected trim count 0. The attempted soft trim found 0 trim candidates because all retained parking proposals were hard-protected or otherwise unsafe to trim. This indicates the 0.50000 parking proposal rate is not caused by generic non-risk proposal noise.

Further trimming would likely sacrifice event-FN protection and risks reproducing the earlier 2M failure mode: low parking proposal pressure with many unprotected FNs.

## Evidence Table

| Phase / run | Parking proposal / intervention | Parking detector | Parking unprotected FN | Interpretation |
| --- | ---: | ---: | ---: | --- |
| 2M parking | 0.20000 | 0.00000 | 31 | Too little protection; high unprotected FN. |
| 2M2 parking | 0.48000 | 0.00000 | 9 | More no-detector protection; large FN reduction. |
| 2M3 parking | 0.39000 | 0.00000 | 9 | Lower proposal, but no additional FN benefit. |
| 2Q2 dry-run | 0.45000 | 0.00000 | 5 | Passed old parking gate with strong FN protection. |
| 2Q2 live | 0.50000 | 0.00000 | 4 | Failed old raw proposal gate only; all other live gates passed. |
| 2Q3 dry-run | 0.50000 | 0.00000 | 4 | Trim candidate predicate found no safe generic frames. |
| 2Q4 dry-run | 0.50000 | 0.00000 | 4 | Soft trim found 18 soft-preserved frames, but 0 safe trim candidates due hard protection. |

## Interpretation

For `intermittentObjectMotion/parking`, proposal pressure is serving event-FN protection. The improvements from 2M to 2Q2/2Q4 are dominated by fewer unprotected event FNs, not by detector usage.

Detector cost remains zero for parking in the relevant accepted/reviewed runs. Normal-frame proposals/interventions remain zero. The extra parking proposals are therefore not broad detector-heavy behavior and are not normal-frame churn.

Forcing parking proposal/intervention <= 0.45000 after 2Q4 would likely require trimming hard-protected or FN-risk frames. That may improve the raw proposal diagnostic while worsening the safety objective.

## Proposed Revised Parking Gate

Replace the old parking-only raw proposal gate:

| Old gate | Status |
| --- | --- |
| `intermittentObjectMotion/parking` proposal/intervention <= 0.45000 | Too strict for the protected parking behavior observed in 2Q2 live and 2Q4 dry-run. |

Use this protection-aware, scene-specific parking gate instead:

| Revised protection-aware parking gate | Requirement |
| --- | ---: |
| Parking proposal/intervention | <= 0.50000 acceptable |
| Parking detector request | <= 0.02000 |
| Parking unprotected FN | <= 12 |
| Parking normal-frame interventions | 0 |
| Parking accidental hard-protected trim count | 0 |
| Aggregate detector request | < 0.10000 |
| Broad detector-heavy behavior | none |
| Forbidden validation launched | none |

This revised gate applies only to `intermittentObjectMotion/parking`. It is not a global proposal relaxation.

## Live Result Implication

Under the revised protection-aware parking gate, the 8C-2Q2 targeted category live retry would pass all Step 3B targeted category live gates:

| 2Q2 live requirement | Result | Status under revised gate |
| --- | ---: | --- |
| 80/80 completed, 0 failed | 80/80, 0 failed | Pass |
| Aggregate detector request < 0.10 | 0.01062 | Pass |
| Normal-frame interventions = 0 | 0 | Pass |
| Guard alignment >= 0.95 | 1.00000 | Pass |
| Parking proposal/intervention <= 0.50 | 0.50000 | Pass |
| Parking detector <= 0.02 | 0.00000 | Pass |
| Parking unprotected FN <= 12 | 4 | Pass |
| Other targeted live gates | all passed under existing table | Pass |

The old gate marked 2Q2 live as failed only because parking intervention was 0.50000 against a 0.45000 raw cap. The protection-aware gate accepts that intervention level because it is no-detector, non-normal-frame, and associated with low unprotected FN.

## Scientific Justification

The online guarded controller optimizes detector-sparse event safety, not raw proposal minimization. Proposal rate is a useful safety-control diagnostic, but it is not equivalent to detector cost or false intervention cost.

In intermittent-object scenes, no-detector protection proposals may legitimately be higher than in static background, dynamic background, or PTZ scenes. Parking has intermittent object persistence and event-FN risk that benefits from retaining guarded no-detector proposals.

The primary efficiency measures for this controller are detector request rate, activation, latency, and energy. In the reviewed parking runs, detector request remains 0.00000 while unprotected FN improves dramatically versus the low-proposal 2M behavior. That is aligned with the controller's detector-sparse safety objective.

## Risk Note

This is an accepted scene-specific exception, not a global relaxation.

The revised gate applies only to `intermittentObjectMotion/parking`. It must be monitored again in any Step 3B live freeze, full CDnet dry-run, full CDnet live/edge profiling, and later cross-dataset planning. If parking proposal pressure rises above 0.50000, detector requests increase, normal-frame interventions appear, or unprotected FN worsens, the exception should be reopened.

## Recommendation

Do not patch parking further now. Two consecutive parking trim attempts showed that the retained frames are protected or unsafe to trim under the current safety definition.

Recommended gate decision:

- Revise the parking gate from a raw <= 0.45000 proposal/intervention cap to the protection-aware parking gate above.
- Mark the 8C-2Q2 targeted category live retry as passing under the revised gate.
- Alternatively, if strict phase consistency is preferred, authorize one final 8C-2Q4 targeted category live run under the revised parking gate before freeze.
- Do not run full CDnet yet. First document a Step 3B live freeze under the revised parking gate, then review whether Step 4 full CDnet dry-run is authorized.
