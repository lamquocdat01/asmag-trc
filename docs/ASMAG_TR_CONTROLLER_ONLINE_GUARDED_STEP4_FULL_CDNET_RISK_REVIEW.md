# ASMAG-TRC Step 4 Full CDnet2014 Risk Review

Date: 2026-05-16

## Executive Summary

The Step 4 full CDnet2014 dry-run completed technically:

- Dataset: CDnet2014
- Categories: 11
- Videos: 53
- Pipelines: 4
- Jobs: 212
- Completed: 212/212
- Failed: 0

Aggregate detector, normal-frame, and guard safety remained strong. The controller stayed detector-sparse, produced zero normal-frame proposed interventions, and maintained perfect guard alignment.

This is **not** a clean Step 4 pass. The primary gate hold is `intermittentObjectMotion/parking` proposal 0.51000 against the revised protection-aware cap of 0.50000. Full CDnet live remains held.

## Aggregate Strength Analysis

| Metric | Result | Why it is strong |
|---|---:|---|
| Proposed detector request rate | 0.01211 | Far below the 0.10000 aggregate ceiling; no broad detector-heavy behavior appeared. |
| Normal-frame proposed interventions | 0 | The final normal-frame suppressor and scene guards avoided normal-frame proposal churn across the full dataset. |
| Guard alignment | 1.00000 | Deterministic guard accounting stayed fully aligned in the compare output. |
| Event_F1 | 0.76989 | Event-level behavior remains competitive despite full-dataset expansion beyond the targeted 20-video set. |
| P95 latency | 244.80332 ms | Latency stayed below the earlier targeted-category live P95 range and did not show an edge-profile collapse. |
| Failed jobs | 0 | The full validation completed all 212 planned jobs without execution failures. |

These strengths indicate the Step 4 issue is not systemic detector pressure or unstable execution. The remaining risks are concentrated by category/video.

## Gate Blocker Table

| Blocker | Result | Gate / context | Review decision |
|---|---:|---|---|
| `intermittentObjectMotion/parking` proposal | 0.51000 | Revised protection-aware cap is 0.50000 | Current frozen gate says hold. This is also a protection-aware tolerance candidate because the miss is only 0.01000 and the safety context is favorable. |
| `intermittentObjectMotion/parking` detector | 0.00000 | Gate requires <= 0.02000 | Pass; no detector cost. |
| `intermittentObjectMotion/parking` unprotected FN | 3 | Gate requires <= 12 | Pass; protection remains effective. |
| Parking normal-frame proposals | 0 | Gate requires 0 | Pass; no normal-frame churn. |

Parking should be treated as a governance decision rather than an automatic code-patch target. If the team accepts a narrow protection-aware tolerance from 0.50000 to 0.51000 for full CDnet dry-run only, parking becomes acceptable. If the 0.50000 cap remains strict, parking remains a hard Step 4 blocker.

## Residual Risk Classification

Classification key:

- A: must patch or audit before next full dry-run
- B: watch item for full live
- C: paper discussion / limitation
- D: acceptable under protection-aware gate or tolerance

| Video / risk | Evidence | Class | Rationale |
|---|---|---|---|
| `thermal/lakeSide` | unprotected FN 21, event FN 48, protected FN 27, proposal 0.40000, detector 0.00000 | A | Largest unprotected-FN source; needs frame-level audit and likely thermal-specific FN protection before another full dry-run freeze. |
| `intermittentObjectMotion/sofa` | unprotected FN 10, event FN 22, protected FN 12, detector 0.03000 | A | Full-dataset intermittent-object FN risk similar in shape to earlier parking issues; likely benefits from a narrow IOM audit before patching. |
| `badWeather/snowFall` | unprotected FN 10, event FN 22, protected FN 12, detector 0.03000 | A | Bad-weather FN risk not covered by targeted validation; should be audited for event-memory/foreground-loss rescue opportunities. |
| `lowFramerate/port_0_17fps` | detector 0.07000, proposal 0.37000, unprotected FN 0 | A/B | Detector pressure is under aggregate limit but high locally; audit before full live to decide whether a narrow no-detector retighten is needed. |
| `PTZ/continuousPan` | FMeasure 0.08818, Event_F1 0.29060, proposal 0.04000, detector 0.01000, unprotected FN 0 | B/C | Proposal and FN safety are controlled, but low metrics require full-live watch and paper discussion about mask quality / PTZ limitations. |
| `dynamicBackground/overpass` | FMeasure 0.00000, Event_F1 0.00000, unprotected FN 0 | C | No FN or detector-safety issue; likely metric/mask-quality limitation rather than controller safety failure. |
| `dynamicBackground/fall` | FMeasure 0.10964, Event_F1 0.13084, unprotected FN 0 | C | Low event/pixel metrics without FN risk; discuss as dynamic-background quality limitation. |
| `dynamicBackground/fountain01` | FMeasure 0.03924, Event_F1 0.30508, proposal 0.00000, detector 0.00000, unprotected FN 0 | C/D | Quiet guard worked as designed; low metric is a limitation/watch item, not a detector or FN failure. |
| `shadow/backdoor` | FMeasure 0.00000, Event_F1 0.00000, proposal 0.40000, detector 0.04000, unprotected FN 0 | B/C | No FN issue, but low metrics plus moderate proposal/detector pressure should be watched before full live. |
| `intermittentObjectMotion/parking` | proposal 0.51000, detector 0.00000, unprotected FN 3, normal proposals 0 | D if tolerance accepted; A if strict cap retained | Safety context is favorable and no-detector. It is only a gate blocker because the revised cap is 0.50000. |
| `shadow/copyMachine` | proposal 0.46000, detector 0.00000, event FN 47, protected FN 42, unprotected FN 5 | B/D | Protection carries over with no detector cost; keep on watchlist but do not patch before the larger FN risks. |

## Patch Priority Recommendation

Recommended narrow next-action order:

1. **Step 4A-AUDIT: frame-level audit of `thermal/lakeSide`, `intermittentObjectMotion/sofa`, and `badWeather/snowFall` before patching.**
2. Priority 1 patch candidate after audit: `thermal/lakeSide` FN protection.
3. Priority 2 patch candidate after audit: `intermittentObjectMotion/sofa` FN protection.
4. Priority 3 patch candidate after audit: `badWeather/snowFall` FN protection.
5. Priority 4 patch candidate after audit: `lowFramerate/port_0_17fps` detector-pressure retighten.

Parking should **not** be patched again now unless the team rejects the protection-aware tolerance around 0.51000. Previous parking work showed that trimming protected parking frames can trade away event safety; the full dry-run parking result remains no-detector with unprotected FN 3.

## Scientific Interpretation

The full CDnet dry-run exposed categories and videos that were not covered by the targeted-category validation. That is expected: targeted validation stabilized the known live-sensitive videos, while full CDnet adds thermal, additional bad-weather, broader intermittent-object, and more dynamic-background scenes.

The controller remains detector-sparse and safety-aligned:

- aggregate detector request is only 0.01211
- normal-frame proposed interventions are 0
- guard alignment is 1.00000
- no broad detector-heavy behavior appeared

The remaining errors are category-specific event-FN risks and localized metric weaknesses, not a global policy collapse. Some very low pixel FMeasure videos, especially in dynamic-background and PTZ scenes, may reflect mask-quality limits or dataset-specific foreground definitions more than online policy failure, because they do not coincide with unprotected event-FN pressure.

## Recommended Next Step

Recommended next step: **Step 4A-AUDIT**.

Use the existing full dry-run frame-level outputs to audit:

- `thermal/lakeSide`
- `intermittentObjectMotion/sofa`
- `badWeather/snowFall`
- optionally `lowFramerate/port_0_17fps` for detector-pressure accounting

Prefer the audit before patching because frame-level logs are available under `outputs/asmag_tr_controller_online_guarded_cdnet_full_2q2_dryrun/`. The audit should identify whether each FN cluster is caused by unsafe empty/fallback actions, rescue cap exhaustion, insufficient event memory, foreground-loss thresholding, or scene-specific detector cadence.

## Full Live Decision

Full CDnet live remains **held**.

Cross-dataset validation remains **held**.

Jetson/edge profiling remains **held**.

Do not run full live or cross-dataset validation until a clean Step 4 dry-run freeze is documented.
