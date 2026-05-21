# ASMAG-TRC Step 3B Live Failure Audit

Date: 2026-05-15

## Executive Summary

Step 3B 8C-2O targeted category live completed technically with 80/80 jobs completed and 0 failed, and live compare outputs already existed. This audit did not run validation, did not resume live, did not rerun compare, did not modify controller code, and did not delete or overwrite outputs.

Step 3B live fails because four video-specific FN-protection gates failed. The aggregate safety controls stayed healthy: detector request rate 0.02477, normal-frame interventions 0, and guard alignment 1.00000. The failure is localized to live-sensitive FN protection in `shadow/cubicle`, `PTZ/intermittentPan`, `shadow/copyMachine`, and `intermittentObjectMotion/parking`.

Full CDnet remains held.

## Live Aggregate Status

| Metric | Live Result |
| --- | ---: |
| Jobs completed / failed | 80 / 0 |
| FMeasure | 0.42292 |
| Event_F1 | 0.66650 |
| Activation | 0.47928 |
| Avg_FPS | 16.50218 |
| P95 latency | 484.56976 ms |
| Intervention/proposal rate | 0.23357 |
| Detector request rate | 0.02477 |
| Block-only rate | 0.20880 |
| Event/foreground block-only rate | 0.16886 |
| Normal-frame interventions | 0 |
| Guard alignment | 1.00000 |

## Failing Gate Table

| Gate | Live Result | Dry-Run Result | Status |
| --- | --- | --- | --- |
| `shadow/cubicle` recall >= 0.80 and unprotected FN = 0 | recall 0.81818, unprotected FN 1 | recall 0.87879, unprotected FN 0 | Fail |
| `PTZ/intermittentPan` proposal <= 0.15 and unprotected FN = 0 | proposal 0.05000, unprotected FN 2 | proposal 0.01000, unprotected FN 0 | Fail |
| `shadow/copyMachine` unprotected FN <= 15 | unprotected FN 18 | unprotected FN 12 | Fail |
| `intermittentObjectMotion/parking` proposal <= 0.45 and unprotected FN <= 12 | proposal 0.43000, unprotected FN 14 | proposal 0.43000, unprotected FN 9 | Fail |

## Audited Frame Counts

| Video | Live event FNs | Live unprotected FNs audited | Dry-run residual among those frames | Newly live-sensitive among those frames |
| --- | ---: | ---: | ---: | ---: |
| `shadow/cubicle` | 1 | 1 | 0 | 1 |
| `PTZ/intermittentPan` | 2 | 2 | 0 | 2 |
| `shadow/copyMachine` | 22 | 18 | 12 | 6 |
| `intermittentObjectMotion/parking` | 20 | 14 | 9 | 5 |

Unprotected FN here means `Event_State == FN` and `ai_intervention_applied != 1` in the live guarded frame log.

## Frame-Level Unprotected FN Table

Abbreviations:
- `prop`: live `ai_intervention_applied`
- `block`: live `ai_block_only_no_detector`
- `before`: live `selected_mode_before_guard`
- `score/loss/risk`: live event/foreground score, foreground-loss score, and foreground risk
- `mem/reuse`: live active event memory and reuse age
- `dry`: dry-run state, final action, and whether dry-run had an applied/proposed intervention

| Video | Raw frame | Event | Live final | Det | Prop | Block | Before | Score/loss/risk | Mem/reuse | Cap/reject summary | Expected guard | Dry same frame | Root cause |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| `shadow/cubicle` | 1560 | FN | `CLOSED_EMPTY_P3_FALLBACK` | 0 | 0 | 0 | `P3_FALLBACK` | 0.855 / 0.684 / 0.100 | 1 / 11 | late rescue cap 4 exhausted; stabilizer rejected `event_foreground_or_loss_score_low`; micro cap 8 exhausted; cubicle-like continuity low; final suppressor 0 | cubicle late rescue / stabilizer / micro bump | TP, `FORCED_REFRESH`, prop 0 | A + B + D |
| `PTZ/intermittentPan` | 1370 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.919 / 0.222 / 1.000 | 1 / 8 | no pan rescue/cap candidate logged; cap used 0, reclaimed 6, preserved 0; final suppressor 0 | intermittentPan rescue / 2K preserve lock | TP, `DETECT_ACC`, prop 0 | D + E |
| `PTZ/intermittentPan` | 1375 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.919 / 0.222 / 1.000 | 1 / 9 | no pan rescue/cap candidate logged; cap used 0, reclaimed 6, preserved 0; final suppressor 0 | intermittentPan rescue / 2K preserve lock | TP, `DETECT_ACC`, prop 0 | D + E |
| `shadow/copyMachine` | 645 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.374 / 0.684 / 0.231 | 1 / 4 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 8, preserved 18 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 670 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.056 / 0.684 / 0.236 | 1 / 2 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 9, preserved 18 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 870 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.981 / 1.000 / 0.215 | 1 / 9 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 38 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 1 | A + D |
| `shadow/copyMachine` | 875 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.991 / 1.000 / 0.215 | 1 / 10 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 38 | copyMachine rescue-first | TP, `DETECT_ACC`, prop 0 | A + D |
| `shadow/copyMachine` | 885 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.991 / 1.000 / 0.212 | 1 / 12 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 1 | A + D |
| `shadow/copyMachine` | 890 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.999 / 1.000 / 0.211 | 1 / 13 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 895 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.999 / 1.000 / 0.211 | 1 / 14 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 900 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.999 / 1.000 / 0.211 | 1 / 15 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | TP, `DETECT_ACC`, prop 0 | A + D |
| `shadow/copyMachine` | 905 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.999 / 1.000 / 0.208 | 1 / 16 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | TP, `REUSE_ACC`, prop 0 | A + D |
| `shadow/copyMachine` | 910 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.999 / 1.000 / 0.208 | 1 / 17 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 915 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.999 / 1.000 / 0.208 | 1 / 18 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 920 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.989 / 1.000 / 0.208 | 1 / 19 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 930 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.989 / 1.000 / 0.205 | 1 / 21 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | TP, `REUSE_ACC`, prop 0 | A + D |
| `shadow/copyMachine` | 935 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 1.000 / 1.000 / 0.205 | 1 / 22 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 940 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 1.000 / 1.000 / 0.205 | 1 / 23 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 945 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 1.000 / 1.000 / 0.205 | 1 / 24 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 22, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 960 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 1.000 / 1.000 / 0.205 | 1 / 2 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 24, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `shadow/copyMachine` | 965 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.936 / 1.000 / 0.205 | 1 / 3 | rescue-first and FN rescue rejected `rescue_cap_exhausted`; copy cap suppressed 24, preserved 39 | copyMachine rescue-first | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `intermittentObjectMotion/parking` | 1480 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.980 / 1.000 / 0.224 | 1 / 11 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | TP, `REUSE_ACC`, prop 0 | A + D |
| `intermittentObjectMotion/parking` | 1485 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.980 / 1.000 / 0.223 | 1 / 12 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 1 | A + D |
| `intermittentObjectMotion/parking` | 1490 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.989 / 1.000 / 0.222 | 1 / 13 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `intermittentObjectMotion/parking` | 1495 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.989 / 1.000 / 0.219 | 1 / 14 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `intermittentObjectMotion/parking` | 1500 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.989 / 1.000 / 0.219 | 0 / 15 | no rescue or preserve candidate; active memory 0; final suppressor 0 | parking rescue/preserve | TP, `DETECT_ACC`, prop 0 | D + E |
| `intermittentObjectMotion/parking` | 1505 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.007 / 0.012 / 0.214 | 0 / 16 | no rescue or preserve candidate; low score and active memory 0; final suppressor 0 | parking rescue/preserve | TP, `REUSE_ACC`, prop 0 | B + D + E |
| `intermittentObjectMotion/parking` | 1510 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.007 / 0.012 / 0.215 | 0 / 17 | no rescue or preserve candidate; low score and active memory 0; final suppressor 0 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | B + E |
| `intermittentObjectMotion/parking` | 1515 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.007 / 0.012 / 0.215 | 0 / 18 | no rescue or preserve candidate; low score and active memory 0; final suppressor 0 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | B + E |
| `intermittentObjectMotion/parking` | 1520 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.007 / 0.012 / 0.215 | 0 / 19 | no rescue or preserve candidate; low score and active memory 0; final suppressor 0 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | B + E |
| `intermittentObjectMotion/parking` | 1530 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.007 / 0.012 / 0.210 | 1 / 21 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | TP, `REUSE_ACC`, prop 0 | A + D |
| `intermittentObjectMotion/parking` | 1570 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 1.000 / 1.000 / 0.240 | 1 / 4 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `intermittentObjectMotion/parking` | 1585 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 1.000 / 1.000 / 0.238 | 1 / 7 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `intermittentObjectMotion/parking` | 1590 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 1.000 / 1.000 / 0.236 | 1 / 8 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |
| `intermittentObjectMotion/parking` | 1595 | FN | `CLOSED_EMPTY_ACC` | 0 | 0 | 0 | `ACC` | 0.948 / 1.000 / 0.233 | 1 / 9 | rescue rejected `parking_rescue_cap_exhausted`; rescue cap 24, preserve count 24, cap preserved 43 | parking rescue/preserve | FN, `CLOSED_EMPTY_ACC`, prop 0 | A |

## Dry-Run vs Live Comparison

| Video | Same-frame dry-run comparison |
| --- | --- |
| `shadow/cubicle` | The single live miss at raw frame 1560 was TP in dry-run with final action `FORCED_REFRESH`, but live produced `CLOSED_EMPTY_P3_FALLBACK`. Live event score rose to 0.855, foreground-loss stayed 0.684, active memory stayed 1, and reuse age became 11. The live rescue path was blocked by exhausted late-rescue and micro-bump caps plus stabilizer/continuity rejection. |
| `PTZ/intermittentPan` | Raw frames 1370 and 1375 were TP in dry-run with final action `DETECT_ACC`, but live produced `CLOSED_EMPTY_ACC`. No detector request occurred in either run; this is a final-action/live-trajectory mismatch, and the intermittentPan rescue/cap diagnostics did not mark these rows as candidates. |
| `shadow/copyMachine` | Of 18 live unprotected FNs, 12 were already dry-run FN/unprotected residuals, 2 were dry-run FN with applied intervention, and 4 were dry-run TP. All live rows show rescue-first and FN rescue rejection by `rescue_cap_exhausted`. Live reuse ages on the central burst reached 9-24, while several dry-run counterpart rows had shorter reuse age or TP final actions. |
| `intermittentObjectMotion/parking` | Of 14 live unprotected FNs, 9 were already dry-run FN/unprotected residuals, 1 was dry-run FN with applied intervention, and 4 were dry-run TP. Nine live rows were blocked by `parking_rescue_cap_exhausted`; five live rows had no rescue/preserve candidate because active memory was 0 and, for four of them, event/foreground and foreground-loss scores collapsed to near zero. |

No audited frame shows a final normal-frame suppressor activation. The failure is not a final normal suppressor issue.

## Root-Cause Classification

| Video | Primary root cause | Secondary contributors | Notes |
| --- | --- | --- | --- |
| `shadow/cubicle` | A. cap exhausted before protection | B. stabilizer threshold too high; D. dry-run/live final action mismatch | Frame 1560 was TP in dry-run via `FORCED_REFRESH`; live reached `CLOSED_EMPTY_P3_FALLBACK` after late-rescue and micro-bump caps were exhausted. |
| `PTZ/intermittentPan` | D. dry-run/live final action mismatch | E. localized/candidate risk missing or not logged | Frames 1370/1375 were dry-run TP via `DETECT_ACC`; live closed empty. Rescue/cap rows did not log candidate or rejection despite high event score and active memory. |
| `shadow/copyMachine` | A. cap exhausted before protection | D. dry-run/live final action mismatch on 6 frames | The accepted dry-run residual of 12 stayed visible, but live added 6 new unprotected frames; all live unprotected rows report rescue-cap exhaustion. |
| `intermittentObjectMotion/parking` | A. cap exhausted before protection | B. thresholds too high on low-score frames; D. dry-run/live final action mismatch; E. active memory/localized candidate missing | The accepted dry-run residual of 9 rose to 14. Nine rows hit rescue-cap exhaustion; five did not become rescue/preserve candidates, mostly because active memory was 0 and scores were too low. |

Classification groups observed: A, B, D, and E. Groups C, F, and G were not supported by the audited frame logs. In particular, `CLOSED_EMPTY_ACC` and `CLOSED_EMPTY_P3_FALLBACK` are recognized in the live diagnostics, final normal suppressor was inactive on all audited frames, and no evidence showed suppressor-before-rescue ordering as the proximate failure.

## Recommended Narrow Next Patch

Do not change aggregate detector policy, final normal-frame suppression, fountain01 quiet guard, lowFramerate retighten, turbulence2, or tunnelExit. Those gates passed.

Recommended patch order:

1. Patch `shadow/cubicle` and `PTZ/intermittentPan` first as a small grouped "live final-action mismatch" patch. Both failures were dry-run TP but live closed-empty, and both need only 1-2 frames of added protection.
2. Patch `shadow/copyMachine` and `intermittentObjectMotion/parking` second as a grouped "cap-exhaustion residual" patch. Both are acceptable dry-run residual videos that exceeded live thresholds due to extra live misses after rescue caps were exhausted.
3. Keep every patch dry-run-only first. Re-run targeted category dry-run, then targeted category live only after the dry-run gates pass. Do not run full CDnet until Step 3B targeted category live passes.

Patch constraints:

- Prefer no-detector or detector-sparse protection.
- Increase or reserve rescue capacity only for localized event-FN risk frames.
- Preserve normal-frame intervention count at 0.
- Preserve aggregate detector request rate under 0.10.
- Do not broaden behavior outside the four failing videos.

Full CDnet remains held.
