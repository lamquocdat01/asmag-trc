# ASMAG-TR Controller Online Guarded Step 4D2 Carry-Over Audit

Date: 2026-05-17

## Scope

This is an audit-only review of existing Step 4D2 residual-risk subset dry-run artifacts. No experiment, live run, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

Read inputs:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4d2_snowfall_risk_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_step4c_sofa_risk_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_step4b4_lakeside_risk_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_step4b3_lakeside_risk_subset_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q2_dryrun.yaml`
- prior reports and existing output roots for Step 4D2, Step 4C, Step 4B4, and 2Q2/2Q4 parking behavior

## Executive Summary

Step 4D2 did not lose the main config inheritance stack. Its declared chain is:

`Step 4D2 -> Step 4D -> Step 4C -> Step 4B4 -> full_2Q2 -> targeted_2Q2 -> targeted_2Q -> targeted_2P -> targeted_2O -> targeted_2N -> targeted_2M3 -> targeted_2M2 -> targeted_2M -> targeted_2L2 -> targeted_2L -> targeted_2K -> targeted_2J -> mini_2J -> mini_2I -> mini_2H2 -> mini_2H -> mini_2G -> smoke_2G -> smoke_2F -> smoke_2E -> smoke_2D -> smoke_2C/2B base stack`

The Step 4B4 lakeSide settings, Step 4C sofa settings, and 2Q/2Q2 parking/copyMachine/turbulence/tunnelExit/cubicle/PTZ/fountain/lowFramerate settings remain present by inheritance. Step 4D2 adds snowFall actual-FN rescue and lakeSide drift recap settings, but it does not override the earlier carry-over blocks.

The observed regressions are therefore not primarily config-loss failures. They are mostly present-but-insufficient activation, cap exhaustion, and trajectory drift in the residual-risk subset.

Recommendation: **Option B**. Create Step 4D3 as carry-over locks plus snowFall cap increase. The carry-over locks should explicitly restate the fragile inherited settings in the Step 4D3 config, then use a narrow snowFall actual-FN cap increase. Do not change core logic broadly.

## Config Inheritance Audit

| Carry-over item | Source step/config | Step 4D2 status | Audit result |
|---|---|---|---|
| lakeSide rescue and high-score soft trim | Step 4B4 | Preserved through Step 4C and Step 4D base chain | Present; not missing or changed |
| sofa intermittent-object rescue | Step 4C | Preserved through Step 4D base chain | Present; not missing or changed |
| parking protection-aware gate and reserves | 2M/2M2/2M3 plus 2Q live reserve | Preserved through full_2Q2 base chain | Present; activation/cap trajectory regressed |
| copyMachine reserve settings | 2L/2L2 plus 2Q live reserve | Preserved through full_2Q2 base chain | Present; Step 4D2 copyMachine remains within accepted gate |
| turbulence2 carry-over reserve | 2N plus 2Q2 | Preserved through full_2Q2 base chain | Present; remains passing |
| tunnelExit preserve/rescue/trim | 2O | Preserved through full_2Q2 base chain | Present; small FN drift remains |
| final normal-frame suppressor | smoke 2F and later exact keep flags | Preserved | Present; remained inactive on audited special rescues |
| sparse detector policy | smoke 2B/2C budget profile | Preserved | Present; port detector pressure is trajectory-specific |
| exact-cubicle rescue/stabilizer | mini 2H/2H2/2J and 2P reserve | Preserved | Present; cubicle remains passing |
| PTZ intermittentPan/continuousPan guards | 2K/2L2/2P plus base PTZ guards | Preserved | Present; PTZ carry-over remains passing |
| fountain01 quiet guard | mini 2I | Preserved | Present; fountain01 remains quiet |
| lowFramerate retighten | mini 2I | Preserved for `tramCrossroad_1fps` | Present, but does not target `port_0_17fps` |

Important nuance: Step 4D2 inherits lowFramerate retighten, but the configured target list is `lowFramerate/tramCrossroad_1fps`. It does not cover `lowFramerate/port_0_17fps`, so the port detector watch item is expected to remain unhandled by that carry-over guard.

## Per-Video Carry-Over Audit

| Video | Comparison | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Special guard/rescue | Columns exist/nonzero | Cap/candidates | Final normal suppressor |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| `thermal/lakeSide` | Step 4D2 | 0.52000 | 0.00000 | 53 | 48 | 5 | lakeSide rescue, early memory, hard-protect refine, fg-loss trim, high-score soften/trim, drift recap | Yes; rescue 15, early 3, high-score soften 64, high-score trim 5, drift recap active 64 but suppressed 0 | Candidate drift: rescue candidates 16 same as B4; early candidates 44 vs 48; post trim candidates 16 vs 14; high-score trim candidates 9 vs 7 | 0 |
| `thermal/lakeSide` | Step 4B4 | 0.50000 | 0.00000 | 48 | 48 | 0 | same except no drift recap | Yes; rescue 15, early 3, high-score soften 62, high-score trim 5 | cap values unchanged; final rate 0.50000 | 0 |
| `intermittentObjectMotion/sofa` | Step 4D2 | 0.35000 | 0.00000 | 28 | 20 | 8 | sofa rescue plus proposal guard | Yes; rescue active 12, proposal guard active 44 | rescue candidates 12 vs 15; cap max 12 unchanged; no cap-exhausted rejection in D2 summary | 0 |
| `intermittentObjectMotion/sofa` | Step 4C | 0.26000 | 0.00000 | 21 | 21 | 0 | same | Yes; rescue active 12, proposal guard active 31 | rescue candidates 15; cap max 12; 3 cap-exhausted rejections but no unprotected FN | 0 |
| `intermittentObjectMotion/parking` | Step 4D2 | 0.44000 | 0.00000 | 47 | 25 | 22 | parking rescue, preserve-FN-risk, post-preservation trim, live cap reserve | Yes; rescue 24, preserve 25, live reserve 8 | rescue cap max 24 unchanged; 12 rescue cap-exhausted; preserve candidates 25 vs 28 in 2Q2 | 0 |
| `intermittentObjectMotion/parking` | 2Q2 dry-run | 0.45000 | 0.00000 | 33 | 28 | 5 | same through 2Q2 live reserve | Yes; rescue 24, preserve 28, live reserve 8 | rescue cap max 24; 9 rescue cap-exhausted | 0 |
| `intermittentObjectMotion/parking` | 2Q4 dry-run reference | 0.50000 | 0.00000 | 33 | 29 | 4 | adds failed soft-preserved trim | Yes; soft trim active but 0 suppressed | soft trim found 18 soft-preserved but all were also hard-protected | 0 |
| `lowFramerate/tunnelExit_0_35fps` | Step 4D2 | 0.30000 | 0.00000 | 3 | 1 | 2 | tunnelExit preserve/rescue/post-trim | Yes; preserve 30, rescue 6, post trim active 30 | rescue cap 6 unchanged; 4 cap-exhausted | 0 |
| `lowFramerate/tunnelExit_0_35fps` | 2Q2/Step 4B4/Step 4C | 0.31000 | 0.00000 | 2 | 1 | 1 | same | Yes; preserve 31, rescue 6, post trim active 31 | rescue cap 6 unchanged; 3 cap-exhausted | 0 |
| `lowFramerate/port_0_17fps` | Step 4D2 | 0.40000 | 0.09000 | 14 | 10 | 4 | generic sparse detector policy; no port-specific retighten | Detector columns exist; port-specific retighten active 0 | detector requests 9 vs 7 in Step 4A; event-FN frames 14 vs 5 | inactive/blank |
| `lowFramerate/port_0_17fps` | Step 4A baseline | 0.37000 | 0.07000 | 5 | 5 | 0 | generic sparse detector policy; no port-specific retighten | Detector columns exist; retighten active 0 | detector requests 7 | 0 |

## Root-Cause Classification

Classification key:

- A: config setting missing
- B: config value changed
- C: compare/reporting mismatch
- D: exact guard present but not activating
- E: cap/cooldown exhausted
- F: score/memory trajectory changed
- G: other

| Regression | Classification | Root cause |
|---|---|---|
| lakeSide proposal 0.52000 and unprotected FN 5 | D + F | Step 4B4 settings are present. Step 4D2 added drift recap, but it suppressed 0 frames because soft candidates were encountered before final pressure was known and later pressure was hard-protected. The frame trajectory changed enough to add 5 unprotected FNs and two extra high-score soft candidates. |
| sofa unprotected FN 8 | F, with D for candidate predicate | Step 4C settings are present and cap values unchanged. Rescue activations stayed at 12, but rescue candidates fell from 15 to 12 and the 8 unprotected FN rows were not sofa-rescue candidates. Three early rows still had active memory and high event/foreground scores; five later rows had inactive memory and weak scores. |
| parking unprotected FN 22 | E + F | Parking settings are present. Rescue and preserve paths activate, but preserve candidates fell from 28 to 25, event FN rose from 33 to 47, and 12 rescue candidates hit `parking_rescue_cap_exhausted`. Eleven additional unprotected FN rows were not rescue/preserve candidates, many with inactive memory or weak scores. |
| port_0_17fps detector 0.09000 | F + G | Sparse detector policy is present; no port-specific retighten exists. Detector requests rose from 7 to 9 and are all `detector_refresh_needed_for_event`, mostly TN/FP. This is an unresolved Step 4A watch item, not a lost carry-over setting. |
| tunnelExit unprotected FN 2 | E + F | tunnelExit settings are present. Metrics drifted slightly from 2Q2/4B4/4C unprotected FN 1 to 2; rescue cap remains 6 and cap-exhausted rejections rose from 3 to 4. |

## SnowFall Candidacy Audit

Step 4D2 snowFall summary:

- proposal rate: 0.30000
- detector request rate: 0.00000
- event FN: 23
- protected FN: 16
- unprotected FN: 7
- actual-FN rescue candidates: 22
- actual-FN rescue activations: 12
- actual-FN no-detector rescues: 12
- actual-FN rescue-protected event-FN frames: 12
- actual-FN final-normal suppressions: 0
- actual-FN cap-exhausted rejections: 10

The 10 cap-exhausted rejected candidates were all actual FN rows with unsafe closed-empty actions (`CLOSED_EMPTY_ACC`), active event memory, and weather/event continuity signal. None were normal-frame rows, detector-request rows, or final-normal suppressor rows. Four of those 10 were already protected by another intervention path, so they do not need extra cap to improve the unprotected-FN count.

Increasing the exact actual-FN rescue cap alone would likely reduce snowFall below the acceptable gate. The current miss is 7 unprotected FN; six are cap-exhausted closed-empty actual-FN candidates and one is a `DETECT_ACC` mask-quality/watch row. Rescuing only one additional safe cap-exhausted closed-empty row should reach the acceptable <= 6 gate. Rescuing the full remaining closed-empty cluster would likely leave only the `DETECT_ACC` row, but preferred <= 4 should still be verified carefully in a later allowed dry-run.

No broad detector logic is indicated by the existing logs. Detector stayed 0.00000, proposal stayed below the 0.45 hard ceiling, and the rejected cap-exhausted rows are consistent with the exact no-detector rescue intent.

## Recommendation

Choose **Option B: settings are present but not activating or not sufficient under the changed trajectory**.

Step 4D3 should be a narrow carry-over lock plus snowFall cap increase:

1. Explicitly restate fragile inherited carry-over locks in the Step 4D3 config: lakeSide Step 4B4 rescue/soft-trim settings, sofa Step 4C rescue settings, parking 2M/2M2/2M3 plus 2Q live reserve settings, copyMachine reserves, turbulence2 carry-over reserve, tunnelExit preserve/rescue/trim, final normal suppressor, exact cubicle guards, PTZ guards, fountain01 quiet guard, and lowFramerate retighten.
2. Increase or adapt only the exact `badWeather/snowFall` actual-FN rescue cap for unsafe closed-empty actual-FN rows, preserving no-detector and final-normal constraints.
3. Add carry-over assertion/reporting gates in the Step 4D3 comparison report so lakeSide, sofa, parking, tunnelExit, and port cannot silently drift.
4. Do not change core logic broadly. Do not run full CDnet/live/cross-dataset until the residual subset dry-run passes and the carry-over rows are explicitly frozen.

Parking should not be patched together with snowFall unless Step 4D3 carry-over locks still show the same parking FN trajectory. The parking regression is larger than snowFall and may require a one-video follow-up, but the audit does not show missing config.

## Hold Status

Full CDnet, full CDnet compare, live, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, and Jetson/edge profiling remain held.
