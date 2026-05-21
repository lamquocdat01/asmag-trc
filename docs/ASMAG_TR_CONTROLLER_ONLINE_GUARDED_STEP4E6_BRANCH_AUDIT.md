# ASMAG-TR Controller Online Guarded Step 4E6 Branch Audit

Date: 2026-05-19

## Scope

This is an audit-only report for the failed Step 4E6 residual-risk subset dry-run. It diagnoses why Step 4E6 did not enforce the intended behavior locks. It does not implement Step 4E7 and does not recommend patching Step 4E6 blindly.

Safety confirmation:

- No experiments, dry-runs, live runs, full CDnet runs, targeted CDnet runs, PTZ-targeted validation, cross-dataset validation, LASIESTA, SBI2015, BMC, Jetson/edge profiling, or compare commands were run for this audit.
- `src/run_experiment.py` and `tools/compare_asmag_tr_controller_online_guarded.py` were inspected read-only only.
- No configs, outputs, controller logic, compare logic, experiment outputs, CSVs, logs, or output folders were modified, overwritten, or deleted.
- The only intended writes for this audit are this report and the `docs/DAILY_STATUS.md` note.

## Files Inspected

Required read-first documents:

- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_CHECKPOINT_2026_05_18.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_PORT_PARKING_REBASE_REPORT.md`
- `docs/DAILY_STATUS.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_VALIDATION_PLAN.md`

Additional read-only documents:

- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_PORT_PARKING_REBASE_REPORT.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E4_PORT_HOLDOUT_RETIGHTEN_REPORT.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D6_PARKING_FINAL_TRIM_REPORT.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E5_PORT_PARKING_CARRYOVER_REPORT.md`

Code inspected read-only:

- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`

Output folders inspected read-only:

- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4b4_lakeside_risk_subset_dryrun/`

Primary CSV/log evidence inspected:

- `ai_intervention_4e6_port_parking_rebase_summary.csv`
- `ai_intervention_4e6_port_parking_rebase_rows.csv`
- `ai_intervention_4e4_port_detector_rows.csv`
- guarded `frame_metrics.csv` files for `lowFramerate/port_0_17fps` and `intermittentObjectMotion/parking`
- carry-over summaries for snowFall, lakeSide, cubicle, intermittentPan, and tunnelExit

## Summary Diagnosis

Step 4E6 failed because the new locks did not reproduce the prior working branches:

- Port: the hard-lock flag fired only on early rows and was inactive at the late-FN region. Frames 1350 and 1355 were not selected by the hard-lock or holdout branches, even though their action was in the intended unsafe fallback set.
- Parking: trim counters were restored, but the Step 4D6 protection trajectory was not. The late FN rows lost active event memory and risk-high state, so legacy parking rescue and carry-over branches did not even become candidates.
- snowFall/lakeSide: the new gate locks were status/report locks. They did not force correction. Existing rescue branches did activate, but the trajectory and caps differed from the stable Step 4D6 state.
- cubicle/intermittentPan/tunnelExit: settings/branches were present through the inherited stack, but video trajectories shifted relative to Step 4D6.

## Port Branch Audit

Video: `lowFramerate/port_0_17fps`

Step 4E4 succeeded on port by keeping detector/context rows at 1210, 1230, 1255, 1340, and 1360, then suppressing later detector-refresh rows and activating no-detector holdout on 1405 through 1430. Frames 1350 and 1355 were protected without direct holdout because the nearby pre-FN/context detector state remained stable.

Step 4E6 did not reproduce that trajectory. The hard-lock telemetry fired overall (`hard_lock_active_frames=54` in the Step 4E6 summary), but on the audited late-FN/holdout window it was active only at 1210, 1230, and 1255. It was inactive at 1340, 1350, 1355, 1360, and all later holdout rows.

### Step 4E4 Reference Rows

| Frame | State | Final action | Before guard | Detector | Protected/Unprotected FN | Retighten decision | Holdout | Final normal suppressor |
|---:|---|---|---|---:|---:|---|---|---:|
| 1210 | FN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 1 | 1/0 | kept: actual_fn_detector_protection+explicit_likely_unprotected_fn | rejected: already_protected | 0 |
| 1230 | FP | FORCED_REFRESH | P3_FALLBACK | 1 | 0/0 | kept: within_hard_detector_budget_context_kept | rejected: already_protected | 0 |
| 1255 | FP | FALLBACK_P3_POLICY | P3_FALLBACK | 1 | 0/0 | kept: within_hard_detector_budget_context_kept | rejected: already_protected | 0 |
| 1340 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 1 | 0/0 | kept: pre_fn_context+downstream_holdout_risk | rejected: already_protected | 0 |
| 1350 | FN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 1/0 | no detector row | rejected: already_protected | 0 |
| 1355 | FN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 1/0 | no detector row | rejected: already_protected | 0 |
| 1360 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 1 | 0/0 | kept: pre_fn_context+downstream_holdout_risk | rejected: already_protected | 0 |
| 1405 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | suppressed above max detector rate | active no-detector holdout | 0 |
| 1410 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | suppressed above max detector rate | active no-detector holdout | 0 |
| 1415 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | suppressed above max detector rate | active no-detector holdout | 0 |
| 1420 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | suppressed above max detector rate | active no-detector holdout | 0 |
| 1425 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | suppressed above max detector rate | active no-detector holdout | 0 |
| 1430 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | suppressed above max detector rate | active no-detector holdout | 0 |
| 1435 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | suppressed above max detector rate | rejected: holdout_cap_exhausted | 0 |
| 1440 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | suppressed above max detector rate | rejected: holdout_cap_exhausted | 0 |

### Step 4E6 Rows

| Frame | State | Final action | Before guard | Detector | Protected/Unprotected FN | Hard lock | Retighten decision | Holdout/reject | Final normal suppressor |
|---:|---|---|---|---:|---:|---|---|---|---:|
| 1210 | FN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 1 | 1/0 | active | kept actual-FN detector | rejected: already_protected | 0 |
| 1230 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | active | no detector decision | rejected: already_protected | 0 |
| 1255 | FP | FALLBACK_P3_POLICY | P3_FALLBACK | 0 | 0/0 | active | no detector decision | rejected: action_not_unsafe_empty_fallback | 0 |
| 1340 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1350 | FN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/1 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1355 | FN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/1 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1360 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1405 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1410 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1415 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1420 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1425 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1430 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1435 | TN | CLOSED_EMPTY_P3_FALLBACK | P3_FALLBACK | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |
| 1440 | TN | CLOSED_EMPTY_ACC | ACC | 0 | 0/0 | inactive | no detector decision | inactive, no reject reason | 0 |

For all audited Step 4E6 port rows, `ai_intervention_original_action` matched `ai_intervention_final_action`. The port hard-lock did not change the final action on these rows. It either kept an already-selected detector row at 1210 or logged early-row context without reproducing the Step 4E4 action/detector pattern.

### Why 1350 and 1355 Were Not Protected

Frames 1350 and 1355 were final FN with `CLOSED_EMPTY_P3_FALLBACK`, detector request 0, protected FN 0, and unprotected FN 1.

Audit answers:

- Step 4E6 hard-lock telemetry fired: yes, overall.
- Step 4E6 hard-lock telemetry fired at frames 1350 and 1355: no.
- Selected as candidates: no. `ai_port_lf_v4_hard_lock_active=0`, `ai_port_lf_detector_retighten_v4_active=0`, and `ai_port_lf_post_suppression_holdout_active=0`.
- Holdout rejected them: no explicit reject reason was logged. The holdout branch did not evaluate on those rows in Step 4E6.
- Action not in action set: no. The action was `CLOSED_EMPTY_P3_FALLBACK`, which is one of the unsafe fallback actions used by the holdout design.
- Final normal suppressor suppressed them: no. `ai_final_normal_frame_suppressor_active=0`.
- Fallback/protection flag set but final action remained unsafe: no. No port hard-lock fallback/protection flag was set.
- Branch executed after final action was frozen: the audited rows show no action change and no branch activation. The practical failure is earlier than final-action mutation: branch reachability/candidate selection failed.
- Port V4 hard lock only logged telemetry: yes for the rows where it fired. On the late-FN rows it did not even log active telemetry.
- Cap/cooldown: not the direct cause for frames 1350 and 1355. The missed frames had no detector request and no holdout/fallback activation to cap.
- Trajectory shift: yes. Step 4E6 lost the Step 4E4 context-detector and downstream-holdout trajectory around 1340/1360 and 1405-1430.

Branch classification for port:

- `D. action branch not reached`
- `B. telemetry-only flag` on early hard-lock rows
- `G. trajectory shift` because Step 4E6 lost the Step 4E4 pre-FN/context detector rows at 1340 and 1360

## Parking Branch Audit

Video: `intermittentObjectMotion/parking`

### Summary Comparison

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN | 4D3 trim | 4D5 trim | 4D6 trim | Rescue/carry-over protection |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Step 4D6 | 0.50000 | 0.00000 | 33 | 33 | 0 | 4 | 4 | 1 | rescue active 24, carry-over lock 9 |
| Step 4E6 | 0.57000 | 0.00000 | 46 | 37 | 9 | 4 | 4 | 1 | hard-restore fallback 0 |

Step 4E6 restored the trim counters but not the protection trajectory. The old Step 4D6 rescue and carry-over mechanisms depended on risk state that no longer existed on the Step 4E6 FN rows.

### Step 4E6 Unprotected Parking FN Rows

| Frame | Step 4E6 state/action | Step 4E6 rescue candidate/active | Step 4E6 hard fallback | Step 4D6 comparison |
|---:|---|---|---|---|
| 1195 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: FN, rescue candidate 1, rescue active 1, active_event_memory 1 |
| 1310 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: FN, rescue candidate 1, rescue active 1, active_event_memory 1 |
| 1315 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: FN, rescue candidate 1, rescue active 1, active_event_memory 1 |
| 1320 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: FN, rescue candidate 1, rescue active 1, active_event_memory 1 |
| 1425 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: TP / DETECT_ACC, already protected |
| 1430 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: TP / REUSE_ACC, already protected |
| 1435 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: FN, rescue candidate 1, rescue active 1, active_event_memory 1 |
| 1440 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: FN, rescue candidate 1, rescue active 1, active_event_memory 1 |
| 1445 | FN / CLOSED_EMPTY_ACC | 0 / 0 | 0 | 4D6: FN, rescue candidate 1, rescue active 1, active_event_memory 1 |

On these nine Step 4E6 rows:

- `ai_parking_iom_rescue_candidate=0`
- `ai_parking_iom_rescue_active=0`
- `ai_parking_carryover_lock_active=0`
- `ai_parking_iom_preserve_fn_risk_candidate=0`
- `ai_parking_4d6_hard_restore_active=0`
- `ai_parking_4d6_hard_restore_fn_fallback_active=0`
- `ai_intervention_guard_active=0`
- `active_event_memory=0`
- `ai_parking_iom_rescue_likely_unprotected_fn=0`

The same 1195/1310/1315/1320/1435/1440/1445 rows in Step 4D6 had:

- `active_event_memory=1`
- `ai_intervention_guard_active=1`
- `ai_intervention_risk_high=1`
- parking rescue candidate 1
- parking rescue active 1
- likely-unprotected-FN marker 1

In Step 4E6 those rows had `active_event_memory=0`, guard inactive, and mostly low risk scores. One unprotected row, 1425, still had `ai_intervention_risk_high=1`, but it had no active event memory, no guard activation, and no rescue/fallback candidate. The parking fallback branch did not execute because the pre-signal/candidate predicates were false. This is not a trim-counter issue and not a cap issue; the trim counters were restored and the fallback cap was unused.

Parking branch classification:

- `G. trajectory shift`
- `C. branch inactive/rejected` through false candidate predicates
- `D. action branch not reached`
- Not `F. cap/cooldown exhausted`

## Carry-Over Drift Audit

| Video | Settings present | Branch activity | Failure classification | Evidence |
|---|---|---|---|---|
| `badWeather/snowFall` | Existing inherited snowFall rescue plus new 4E6 gate lock | Actual-FN rescue active 20, proposal guard active 59, cap exhausted 9 | `F. cap/cooldown exhausted` + `G. trajectory shift` + `H. report-only lock` | Step 4D6 had 22 FN, 21 protected, 1 unprotected; Step 4E6 had 35 FN, 28 protected, 7 unprotected. Gate lock reported drift but did not correct. |
| `thermal/lakeSide` | Existing lakeSide rescue/trim plus new 4E6 gate lock | FN rescue active 3 vs 15 in 4D6, early-memory active 4, carry-over/highscore locks active 51 | `G. trajectory shift` + `H. report-only lock` | Step 4D6 had 48/48 protected; Step 4E6 had 61 FN, only 37 protected. Gate-lock status string reported pass during row logging but final compare failed with 24 unprotected FN, so status was not enforcement. |
| `shadow/cubicle` | Inherited exact cubicle stabilizer/rescue settings present | Stabilizer active 2, pre-signal 2, late rescue active 4, live mismatch reserve 3, same counts as Step 4D6 | `G. trajectory shift` | Unprotected FN stayed 0, but recall fell to 0.77419. Branches fired, but final recall changed. |
| `PTZ/intermittentPan` | Inherited PTZ intermittentPan settings present | Cap active 93, FN rescue active 4, preserve-2K rescue active 4 | `G. trajectory shift` | Step 4D6 had event FN 1/protected 1/unprotected 0. Step 4E6 had event FN 9/protected 7/unprotected 2. Branches fired more often but did not preserve trajectory. |
| `lowFramerate/tunnelExit_0_35fps` | Inherited tunnelExit settings present | preserve-FN-risk active 35, rescue active 6, post-trim active 38 | `G. trajectory shift` | Step 4D6 had event FN 2/protected 1/unprotected 1. Step 4E6 had event FN 4/protected 1/unprotected 3. Branches fired, but trajectory worsened. |

## Recommendation

Recommended path: **Step 4E7-D: split validation into two branches: event-safety branch and detector-retighten branch.**

Rationale:

- Port retighten is not isolated anymore. The Step 4E6 attempt to hard-lock port still lost the late-FN protection path and detector cap, while parking/snowFall/lakeSide/cubicle/intermittentPan/tunnelExit drifted at the same time.
- Parking restoration is unstable when grafted onto Step 4E4/4E6 because the protection trajectory, not the trim stack, is the thing that changed.
- The last subset candidate with broad carry-over stability was Step 4D6. The last port-specific success was Step 4E4, but it failed parking. Combining both as generic locks has not worked.

Specific Step 4E7-D plan:

1. **Event-safety branch base:** use `configs/asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun.yaml` as the base.
2. **Preserve:** Step 4D6 parking, snowFall, lakeSide, sofa, copyMachine, turbulence2, tunnelExit, cubicle, PTZ, fountain, and bridgeEntry behavior.
3. **Port retighten scope:** keep port retighten out of the event-safety branch except as telemetry/watch. Accept `lowFramerate/port_0_17fps` detector as a watch item in that branch.
4. **Detector-retighten branch base:** use `configs/asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun.yaml` only for a port-detector branch, and do not attempt to restore parking/snow/lake with generic locks in the same patch.
5. **Parking:** in the event-safety branch, preserve Step 4D6 strictly. In the detector-retighten branch, parking should be accepted only under protection-aware tolerance if the explicit goal is port detector behavior; otherwise it blocks freeze.
6. **Full CDnet:** remains held until one branch is chosen and passes the same residual-risk subset gates.

If one single branch must be chosen next, prefer the event-safety branch first. That means Step 4E7-D/event-safety based on Step 4D6, with port retighten deferred as a watch item rather than forced into the same freeze candidate.
