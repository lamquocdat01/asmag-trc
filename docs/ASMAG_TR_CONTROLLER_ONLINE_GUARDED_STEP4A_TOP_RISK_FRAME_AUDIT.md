# ASMAG-TRC Step 4A Top Residual Risk Frame Audit

Date: 2026-05-16

## Executive Summary

This is an audit-only review of existing Step 4 full CDnet2014 dry-run outputs. No experiment, live run, full CDnet rerun, cross-dataset validation, PTZ-targeted standalone validation, LASIESTA, SBI2015, BMC, or Jetson/edge profiling was launched.

Step 4 completed technically with 212/212 jobs and 0 failed jobs. Aggregate safety remained strong: detector request rate 0.01211, normal-frame proposed interventions 0, guard alignment 1.00000, and Event_F1 0.76989.

The audit focused on:

- `thermal/lakeSide`
- `intermittentObjectMotion/sofa`
- `badWeather/snowFall`
- `lowFramerate/port_0_17fps`

Audited frames:

| Target | Audit type | Frames audited |
|---|---|---:|
| `thermal/lakeSide` | all unprotected FN frames | 21 |
| `intermittentObjectMotion/sofa` | all unprotected FN frames | 10 |
| `badWeather/snowFall` | all unprotected FN frames | 10 |
| `lowFramerate/port_0_17fps` | all detector-request frames | 7 |

## Located Logs

All target videos have the expected guarded per-video output structure under:

`outputs/asmag_tr_controller_online_guarded_cdnet_full_2q2_dryrun/raw_results/<category>/<video>/ASMAG_TR_CONTROLLER_ONLINE_GUARDED/`

For each target, the audit used:

- `frame_metrics.csv`: primary frame-level audit log with event state, action, AI scores, detector/proposal flags, budgets, cap use, memory, and guard fields.
- `edge_profile.csv`: runtime/action profile mirror for latency and action context.
- `sequence_event_summary.csv`: per-video event TP/TN/FP/FN summary.
- `sequence_pixel_summary.csv`: per-video pixel metrics.
- `summary.json`: per-video aggregate metric summary.

The compare-level summaries used for cross-checking were:

- `ai_intervention_2j_video_summary.csv`
- `ai_intervention_summary.csv`
- `summary_by_video.csv`

## Per-Video Summary

| Video | Event FN | Protected FN | Unprotected FN | Detector rate | Proposal rate | Normal proposals | Main finding | Patch recommended |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `thermal/lakeSide` | 48 | 27 | 21 | 0.00000 | 0.40000 | 0 | Most unprotected FNs appear after generic event/foreground cap exhaustion; early FNs also show weak localized risk despite active memory. | Yes, after audit: thermal no-detector FN rescue. |
| `intermittentObjectMotion/sofa` | 22 | 12 | 10 | 0.03000 | 0.20000 | 0 | FNs have active memory and foreground-loss signal but no sofa-specific rescue path; mostly ordering/missing rescue rather than detector issue. | Yes: sofa intermittent-object rescue. |
| `badWeather/snowFall` | 22 | 12 | 10 | 0.03000 | 0.29000 | 0 | FNs occur under high event/foreground scores after cap reaches 45; includes one FN on `DETECT_ACC`, suggesting some mask-quality exposure. | Yes: snowFall weather-aware no-detector rescue. |
| `lowFramerate/port_0_17fps` | 5 | 5 | 0 | 0.07000 | 0.37000 | 0 | Detector requests are event-refresh-specific; only 1/7 coincides with FN, while 6/7 are FP/TN and likely no-detector fallback candidates. | Yes: detector retighten audit patch after FN patches. |

## Root-Cause Classification Key

- A: cap exhausted before protection
- B: threshold too high
- C: unsafe action not in rescue action set
- D: dry-run/live trajectory mismatch, not applicable here
- E: localized risk missing or not logged
- F: final normal suppressor issue
- G: ordering issue, cap/suppressor before rescue, or missing specific rescue
- H: detector request likely unnecessary
- I: detector request justified by event-FN protection
- J: metric/pixel-mask quality issue rather than controller issue
- K: other

## thermal/lakeSide Frame Audit

Summary:

- Audited 21/21 unprotected FN frames.
- Root causes: A cap exhausted before protection = 18; E localized risk missing or not logged = 3.
- All audited FNs use `ACC` before guard and mostly `CLOSED_EMPTY_ACC`.
- Detector requested: 0/21.
- Final normal suppressor issue: 0/21.

| Frame | State | Final action | Mode before | Detector | Proposed | Block-only | Event score | FG-loss | FG risk | Active memory | Recent age | Reuse age | Cap used | Closed-empty budget | Candidate / rejection | Final normal | Root cause |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1060 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.056 | 0.092 | 0.231 | 1 | 1 | 2 | 0 | 30 | no rescue candidate; active_event+event_continuity only | 0 | E |
| 1065 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.056 | 0.092 | 0.214 | 1 | 2 | 3 | 0 | 30 | no rescue candidate; active_event+event_continuity only | 0 | E |
| 1070 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.056 | 0.092 | 0.200 | 1 | 3 | 4 | 0 | 30 | no rescue candidate; active_event+event_continuity only | 0 | E |
| 1340 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.987 | 1.000 | 0.234 | 1 | 2 | 3 | 45 | 3 | cap exhausted; high event/foreground-loss | 0 | A |
| 1345 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.422 | 1.000 | 0.234 | 1 | 3 | 4 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |
| 1360 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.136 | 1.000 | 0.221 | 1 | 1 | 2 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |
| 1365 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.136 | 1.000 | 0.224 | 1 | 2 | 3 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |
| 1370 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.136 | 1.000 | 0.221 | 1 | 3 | 4 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |
| 1385 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.029 | 0.684 | 0.221 | 1 | 1 | 2 | 45 | 3 | cap exhausted; foreground-loss moderate | 0 | A |
| 1390 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.189 | 1.000 | 0.221 | 1 | 2 | 3 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |
| 1395 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.189 | 1.000 | 0.221 | 1 | 3 | 4 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |
| 1410 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.990 | 1.000 | 0.221 | 1 | 1 | 2 | 45 | 3 | cap exhausted; high event/foreground-loss | 0 | A |
| 1415 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.990 | 1.000 | 0.221 | 1 | 2 | 3 | 45 | 3 | cap exhausted; high event/foreground-loss | 0 | A |
| 1420 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.224 | 1.000 | 0.221 | 1 | 3 | 4 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |
| 1435 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.774 | 1.000 | 0.221 | 1 | 1 | 2 | 45 | 3 | cap exhausted; high event/foreground-loss | 0 | A |
| 1440 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.774 | 1.000 | 0.221 | 1 | 2 | 3 | 45 | 3 | cap exhausted; high event/foreground-loss | 0 | A |
| 1445 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.774 | 1.000 | 0.221 | 1 | 3 | 4 | 45 | 3 | cap exhausted; high event/foreground-loss | 0 | A |
| 1460 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.109 | 1.000 | 0.221 | 1 | 1 | 2 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |
| 1485 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.994 | 1.000 | 0.220 | 1 | 1 | 2 | 45 | 3 | cap exhausted; high event/foreground-loss | 0 | A |
| 1490 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.994 | 1.000 | 0.220 | 1 | 2 | 3 | 45 | 3 | cap exhausted; high event/foreground-loss | 0 | A |
| 1495 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.305 | 1.000 | 0.220 | 1 | 3 | 4 | 45 | 3 | cap exhausted; foreground-loss high | 0 | A |

Thermal/lakeSide root cause: the dominant failure is generic event/foreground cap exhaustion before remaining event FNs can be protected. A small early cluster has active event memory but weak logged localized risk, suggesting thermal-specific foreground/risk calibration is also needed.

## intermittentObjectMotion/sofa Frame Audit

Summary:

- Audited 10/10 unprotected FN frames.
- Root causes: G ordering/missing specific rescue = 9; B threshold too high = 1.
- All audited FNs are `CLOSED_EMPTY_ACC` with active memory.
- Detector requested: 0/10.
- Final normal suppressor issue: 0/10.

| Frame | State | Final action | Mode before | Detector | Proposed | Block-only | Event score | FG-loss | FG risk | Active memory | Recent age | Reuse age | Cap used | Closed-empty budget | Candidate / rejection | Final normal | Root cause |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 510 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.006 | 0.012 | 0.333 | 1 | 1 | 2 | 0 | 30 | no sofa-specific rescue; weak score | 0 | B |
| 515 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.483 | 0.684 | 0.250 | 1 | 2 | 3 | 0 | 30 | active memory + foreground-loss, no rescue | 0 | G |
| 520 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.483 | 0.684 | 0.200 | 1 | 3 | 4 | 0 | 30 | active memory + foreground-loss, no rescue | 0 | G |
| 545 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.516 | 0.684 | 0.210 | 1 | 3 | 4 | 3 | 28 | active memory + foreground-loss, no rescue | 0 | G |
| 560 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.417 | 0.684 | 0.231 | 1 | 1 | 2 | 3 | 28 | active memory + foreground-loss, no rescue | 0 | G |
| 565 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.417 | 0.684 | 0.214 | 1 | 2 | 3 | 3 | 28 | active memory + foreground-loss, no rescue | 0 | G |
| 570 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.417 | 0.684 | 0.214 | 1 | 3 | 4 | 3 | 28 | active memory + foreground-loss, no rescue | 0 | G |
| 585 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.597 | 0.684 | 0.222 | 1 | 1 | 2 | 3 | 28 | active memory + foreground-loss, no rescue | 0 | G |
| 590 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.460 | 0.684 | 0.216 | 1 | 2 | 3 | 3 | 28 | active memory + foreground-loss, no rescue | 0 | G |
| 595 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.460 | 0.684 | 0.215 | 1 | 3 | 4 | 3 | 28 | active memory + foreground-loss, no rescue | 0 | G |

Sofa root cause: the pattern resembles parking before scene-specific protection, but no sofa-specific intermittent-object reserve exists. Scores are often below very high rescue thresholds but have active memory and foreground-loss continuity. This supports a narrow sofa intermittent-object no-detector rescue rather than broader detector policy.

## badWeather/snowFall Frame Audit

Summary:

- Audited 10/10 unprotected FN frames.
- Root causes: A cap exhausted before protection = 10.
- Detector requested: 0/10.
- One FN used `DETECT_ACC` but still remained FN, suggesting a possible mask-quality component for that row.
- Final normal suppressor issue: 0/10.

| Frame | State | Final action | Mode before | Detector | Proposed | Block-only | Event score | FG-loss | FG risk | Active memory | Recent age | Reuse age | Cap used | Closed-empty budget | Candidate / rejection | Final normal | Root cause |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1070 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.703 | 0.684 | 0.467 | 1 | 3 | 4 | 45 | 21 | cap exhausted; weather event risk | 0 | A |
| 1075 | FN | CLOSED_EMPTY_P3_FALLBACK | ACC | 0 | 0 | 0 | 0.703 | 0.684 | 0.467 | 1 | 4 | n/a | 45 | 21 | cap exhausted; fallback action in risk band | 0 | A |
| 1085 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.890 | 0.684 | 0.367 | 1 | 1 | 7 | 45 | 21 | cap exhausted; high event score | 0 | A |
| 1090 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.890 | 0.684 | 0.333 | 1 | 2 | 8 | 45 | 21 | cap exhausted; high event score | 0 | A |
| 1095 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.890 | 0.684 | 0.300 | 1 | 3 | 9 | 45 | 21 | cap exhausted; high event score | 0 | A |
| 1110 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.784 | 0.684 | 0.267 | 1 | 1 | 2 | 45 | 21 | cap exhausted; event risk persists | 0 | A |
| 1115 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.521 | 0.684 | 0.267 | 1 | 2 | 3 | 45 | 21 | cap exhausted; foreground-loss persists | 0 | A |
| 1120 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.521 | 0.684 | 0.267 | 1 | 3 | 4 | 45 | 21 | cap exhausted; foreground-loss persists | 0 | A |
| 1150 | FN | DETECT_ACC | ACC | 0 | 0 | 0 | 0.262 | 0.222 | 0.236 | 1 | 1 | n/a | 45 | 19 | cap exhausted; detector action still FN, possible mask-quality component | 0 | A/J |
| 1195 | FN | CLOSED_EMPTY_ACC | ACC | 0 | 0 | 0 | 0.477 | 0.222 | 0.204 | 1 | 1 | 10 | 45 | 19 | cap exhausted; lower score tail | 0 | A |

SnowFall root cause: the unprotected FNs are concentrated after event/foreground cap reaches 45. The scene has noisy weather motion but logged event scores are often high, so a narrow weather-aware no-detector rescue should prioritize localized event risk and avoid broad detector increases.

## lowFramerate/port_0_17fps Detector Audit

Summary:

- Audited 7/7 detector-request frames.
- Event FN frames: 1/7.
- FP/TN detector frames: 6/7.
- Root causes: I justified detector = 1; H likely unnecessary detector = 6.
- All detector requests were `detector_refresh_needed_for_event` and event-refresh-specific.

| Frame | State | Final action | Mode before | Detector source | Event-specific | Event score | FG-loss | FG risk | Active memory | Recent age | Block-only reason | Guard reason | Detector budget used | Detector budget remaining | Budget blocked | Root cause |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|
| 1210 | FN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | detector_refresh_needed_for_event | 1 | 0.989 | 1.000 | 1.000 | 1 | 4 | event/foreground + active memory + foreground risk | active_event+event_continuity+foreground_risk | 1 | 14 | 0 | I |
| 1230 | FP | FORCED_REFRESH | P3_FALLBACK | detector_refresh_needed_for_event | 1 | 0.999 | 1.000 | 0.973 | 1 | 8 | event/foreground + active memory + foreground risk | active_event+event_continuity+foreground_risk | 2 | 13 | 0 | H |
| 1255 | FP | FALLBACK_P3_POLICY | P3_FALLBACK | detector_refresh_needed_for_event | 1 | 1.000 | 1.000 | 1.000 | 1 | 5 | event/foreground + active memory + foreground risk | active_event+event_continuity+foreground_risk+low_framerate_cadence+explicit_safety_event | 3 | 12 | 0 | H |
| 1340 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | detector_refresh_needed_for_event | 1 | 0.991 | 1.000 | 0.550 | 1 | 3 | event/foreground + active memory | active_event+event_continuity | 4 | 11 | 0 | H |
| 1360 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | detector_refresh_needed_for_event | 1 | 0.991 | 1.000 | 0.524 | 1 | 7 | event/foreground + active memory | active_event+event_continuity | 5 | 10 | 0 | H |
| 1405 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | detector_refresh_needed_for_event | 1 | 0.999 | 1.000 | 0.506 | 1 | 1 | event/foreground + active memory | active_event+event_continuity | 6 | 9 | 1 | H |
| 1425 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | detector_refresh_needed_for_event | 1 | 0.997 | 1.000 | 0.511 | 1 | 5 | event/foreground + active memory | active_event+event_continuity | 7 | 8 | 1 | H |

Port root cause: detector pressure is caused by event-refresh-specific requests under high event/foreground scores. Only the first detector frame coincides with FN protection; later FP/TN detector requests look like no-detector fallback candidates. This supports a lowFramerate port-specific detector retighten after the FN patches.

## Patch Recommendation

Recommended next patch order:

1. **Step 4B: `thermal/lakeSide` no-detector FN rescue.** The dominant pattern is cap exhaustion before protection, with repeated high foreground-loss/event-risk FNs after cap use reaches 45.
2. **Step 4C: `intermittentObjectMotion/sofa` intermittent-object rescue.** Sofa has active memory and foreground-loss continuity but no sofa-specific reserve comparable to parking.
3. **Step 4D: `badWeather/snowFall` weather-aware no-detector rescue.** SnowFall has high event/foreground scores but needs weather-noise-aware localization and cap handling.
4. **Step 4E: `lowFramerate/port_0_17fps` detector suppression/retighten.** Most detector requests are FP/TN and likely can be converted to no-detector protected fallback after FN safety is preserved.

Do not patch parking again unless the team rejects the 0.51000 protection-aware tolerance. Parking remains no-detector with unprotected FN 3, while earlier parking trimming attempts risked event-safety regression.

## Full Live Decision

Full CDnet live remains **held**.

Cross-dataset validation remains **held**.

Jetson/edge profiling remains **held**.

No full live or cross-dataset validation should run until the top residual risks are patched or explicitly accepted and a clean Step 4 dry-run freeze is documented.
