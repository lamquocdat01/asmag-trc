# ASMAG-TR Q1-SIC-0 Invariant Replay Report

Date: 2026-05-19

## Scope and Safety

Q1-SIC-0 is analysis-only. It converts Step 4E6 branch failures into a safety-invariant specification, trajectory-diff CSVs, and a counterfactual replay report.

Safety confirmation:

- No experiments were launched for Q1-SIC-0.
- No dry-runs, live runs, live compares, targeted CDnet, full CDnet, PTZ-targeted validation, cross-dataset validation, LASIESTA, SBI2015, BMC, or Jetson/edge profiling were launched.
- `src/run_experiment.py` was not modified.
- `tools/compare_asmag_tr_controller_online_guarded.py` was not modified or run.
- No configs were modified in this phase.
- Existing outputs were read-only sources only.
- New writes were limited to `tools/analyze_q1_safety_trajectory_diff.py`, `tools/replay_q1_safety_invariants.py`, `docs/ASMAG_TR_Q1_SAFETY_INVARIANT_SPEC.md`, this report, `docs/DAILY_STATUS.md`, and `outputs/asmag_tr_q1_sic0_invariant_replay/`.
- A leftover `run_experiment.py` process from the interrupted previous Step 4E7-D turn was detected and stopped before Q1-SIC-0 analysis began.

## Why This Phase Exists

More than 40 guarded-controller runs and attempts have shown that branch patching is unstable when each patch optimizes a local symptom. Step 4E6 made the failure mode explicit:

- Lock flags can fire without final protection.
- Some locks are report-only.
- Candidate predicates can become false after trajectory state shifts.
- Restored counters are insufficient when `active_event_memory`, `risk_high`, and `guard_active` are lost.
- Rows can remain unsafe even when they belong to a known risk window.

The project therefore needs invariant-first arbitration: reconstruct trajectory state, check safety invariants, and replay counterfactual arbitration offline before any new controller dry-run.

## Inputs Inspected

Documents:

- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_BRANCH_AUDIT.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4E6_PORT_PARKING_REBASE_REPORT.md`
- `docs/DAILY_STATUS.md`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_VALIDATION_PLAN.md`
- `docs/P4_ONLINE_DIAGNOSTIC_REPORT.md`
- `docs/P4_ONLINE_REQUIRED_EXTRA_LOGS.md`
- `docs/PHASE8A_RESUME_CHECKPOINT.md`
- `docs/PHASE8C1B_RESUME_CHECKPOINT.md`

Existing output folders, read-only:

- `outputs/asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4b4_lakeside_risk_subset_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke/`
- `outputs/phase8a_policy_dataset/`
- `outputs/phase8c_shadow_calibration/`

New Q1-SIC-0 outputs:

- `outputs/asmag_tr_q1_sic0_invariant_replay/port_trajectory_diff.csv`
- `outputs/asmag_tr_q1_sic0_invariant_replay/parking_trajectory_diff.csv`
- `outputs/asmag_tr_q1_sic0_invariant_replay/carryover_trajectory_diff.csv`
- `outputs/asmag_tr_q1_sic0_invariant_replay/invariant_violation_summary.csv`
- `outputs/asmag_tr_q1_sic0_invariant_replay/missing_columns_summary.csv`
- `outputs/asmag_tr_q1_sic0_invariant_replay/counterfactual_arbitration_candidates.csv`
- `outputs/asmag_tr_q1_sic0_invariant_replay/counterfactual_summary.csv`

Commands run:

```powershell
python -m py_compile tools\analyze_q1_safety_trajectory_diff.py tools\replay_q1_safety_invariants.py
python tools\analyze_q1_safety_trajectory_diff.py --step4d6-root outputs\asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun --step4e4-root outputs\asmag_tr_controller_online_guarded_cdnet_step4e4_port_detector_subset_dryrun --step4e6-root outputs\asmag_tr_controller_online_guarded_cdnet_step4e6_port_parking_rebase_subset_dryrun --out outputs\asmag_tr_q1_sic0_invariant_replay
python tools\replay_q1_safety_invariants.py --input-dir outputs\asmag_tr_q1_sic0_invariant_replay --out outputs\asmag_tr_q1_sic0_invariant_replay
```

Compile and both analysis-only scripts completed successfully.

## Safety Invariants Table

| Invariant | Name | Failure it prevents | Step 4E6 evidence | Proposed enforcement layer | Telemetry needed |
|---|---|---|---|---|---|
| I0 | Experiment safety | Premature full/live/cross validation | Step 4 work repeatedly needed residual-risk gating before broader runs | Workflow gate outside controller | Run manifest and daily status |
| I1 | Normal-frame safety | Protection patch creates normal-frame false interventions | Replay refined to avoid normal-frame arbitration; `would_touch_normal_frame=0` | Final arbitration must refuse quiet normal rows | `Event_State`, proposal flag, normal-frame suppressor |
| I2 | Event-memory preservation | Rescue predicates become false after trajectory drift | Parking lost `active_event_memory` on all 9 Step 4E6 missed FN rows | Final arbitration checks reference event-memory window | `active_event_memory`, guard state, reference trajectory |
| I3 | Risk-high unprotected-FN | Unsafe closed-empty/reuse/fallback FN remains unprotected | Parking 9, snowFall 7, lakeSide 24, intermittentPan 2, tunnelExit 3 unsafe unprotected FN rows | Event-safety arbitration | final action, risk-high, likely-FN, protected/unprotected FN |
| I4 | Enforcement-vs-telemetry | Report-only locks counted as pass | snowFall 99 and lakeSide 88 report-only lock rows in replay | Lock classification registry | branch class, status strings, final protection accounting |
| I5 | Branch reachability | Critical rows never become candidates | Parking 7 candidate-predicate false rows versus Step 4D6 | Candidate reachability audit before final decision | candidate, active, reject reason, cap/cooldown |
| I6 | Trajectory preservation | Aggregates pass while trajectory state shifts | Parking 9, snowFall 23, lakeSide 22, intermittentPan 11, tunnelExit 8 trajectory shifts | Reference trajectory comparison | required trajectory fields from spec |
| I7 | Split-branch ownership | Port retighten destabilizes event safety | Port 1350/1355 are unsafe but detector-retighten/watch in event-safety branch | Branch ownership policy | branch owner, watch policy, reference step |
| I8 | Full-validation hold | Full CDnet before residual stability | Step 4E6 failed residual-risk subset despite technical completion | Validation planner gate | staged pass/fail evidence |

## Replay Summary

Invariant violations from Step 4E6:

| Video | Key replay findings |
|---|---|
| `lowFramerate/port_0_17fps` | 2 unsafe unprotected FN rows, both classified as detector-retighten/watch under I7. |
| `intermittentObjectMotion/parking` | 9 event-memory losses, 9 unsafe unprotected FN rows, 7 candidate-predicate false rows, 9 trajectory shifts. |
| `badWeather/snowFall` | 99 report-only lock rows, 7 unsafe unprotected FN rows, 4 event-memory losses, 23 trajectory shifts. |
| `thermal/lakeSide` | 88 report-only lock rows, 24 unsafe unprotected FN rows, 5 event-memory losses, 22 trajectory shifts. |
| `shadow/cubicle` | Replay found no direct row-level invariant issue; aggregate recall drift remains a trajectory metric to preserve. |
| `PTZ/intermittentPan` | 2 unsafe unprotected FN rows, 1 event-memory loss, 11 trajectory shifts. |
| `lowFramerate/tunnelExit_0_35fps` | 3 unsafe unprotected FN rows, 2 risk-high losses, 8 trajectory shifts. |

Counterfactual replay produced `would_touch_normal_frame=0` for all 509 replay candidate rows after I1 normal-frame protection was applied.

## Port Replay

Would invariant replay catch frames 1350 and 1355?

Yes. Both rows are Step 4E6 final FN under `CLOSED_EMPTY_P3_FALLBACK`, and replay labels them:

- `E. final action unsafe`
- `M. needs detector-retighten arbitration`
- `N. watch-only`
- `K. split-branch conflict`

Are they event-safety or detector-retighten?

They are detector-retighten/watch rows in this branch. Their reference owner is Step 4E4, not Step 4D6 event safety.

Should they block Step 4E7-D event-safety?

No. Under I7 they should not block an event-safety branch unless they introduce a new event-safety regression. They should be tracked as watch-only for Step 4E7-D.

Which future branch owns them?

Step 4E7-D2 port detector-retighten, using Step 4E4 as the reference trajectory.

## Parking Replay

Which invariant catches the nine Step 4E6 unprotected FN rows?

The rows are caught by I2, I3, I5, and I6:

- I2 catches lost `active_event_memory` and `guard_active`.
- I3 catches unsafe unprotected FN under `CLOSED_EMPTY_ACC`.
- I5 catches missing rescue candidate/active behavior where Step 4D6 had it.
- I6 catches the full trajectory shift versus Step 4D6.

Was the issue counters or trajectory state?

Trajectory state. Step 4E6 restored trim counters, but all nine missed FN rows lost Step 4D6 event-memory/guard trajectory. Seven of the nine also lost rescue candidate and rescue active state.

Fields that must be preserved from Step 4D6:

- `active_event_memory`
- `ai_intervention_guard_active`
- `ai_intervention_risk_high`
- likely-unprotected-FN marker
- parking rescue candidate
- parking rescue active
- carry-over protection where applicable
- final protection accounting

Suggested arbitration: `FORCE_PROTECT_EVENT_MEMORY` before relying on trim counters.

## Carry-Over Replay

| Video | Replay classification |
|---|---|
| `badWeather/snowFall` | Report-only lock plus trajectory shift and cap/cooldown-like exhaustion. Existing lock status cannot count as enforcement because unsafe FN rows remain. |
| `thermal/lakeSide` | Report-only lock plus trajectory shift. LakeSide rows show lock/status activity without final protection preservation. |
| `shadow/cubicle` | Branches appear row-stable in the inspected replay rows; aggregate recall drift still needs trajectory-metric protection. |
| `PTZ/intermittentPan` | Trajectory shift: branch activity exists, but final outcome is not preserved, leaving 2 unsafe unprotected FN rows. |
| `lowFramerate/tunnelExit_0_35fps` | Trajectory shift with branch activity present but not preserving final outcome; 3 unsafe unprotected FN rows. |

## Proposed Final Arbitration API

Do not implement this in the controller yet. Q1-SIC-0 proposes the conceptual API:

```python
final_safety_arbitration(
    video_id,
    frame_idx,
    state_before_guard,
    selected_action,
    selected_mode,
    detector_request,
    proposal,
    active_event_memory,
    risk_high,
    guard_active,
    branch_flags,
    reference_watch_policy,
    caps,
    cooldowns,
) -> {
    "final_action": str,
    "final_detector_request": int,
    "final_protection_label": str,
    "arbitration_reason": str,
    "enforcement_class": str,
}
```

Minimum arbitration labels from replay:

- `FORCE_PROTECT_EVENT_MEMORY`
- `FORCE_RISK_HIGH_RESCUE`
- `FORCE_CARRYOVER_PROTECTION`
- `FORCE_DETECTOR_CONTEXT_ROW`
- `FORCE_NO_DETECTOR_HOLDOUT_PROTECTION`
- `TELEMETRY_ONLY_DO_NOT_COUNT_PASS`
- `WATCH_ONLY_PORT_RETIGHTEN`
- `NO_CHANGE`

The arbitration layer must enforce I1 first: no quiet normal-frame row may be converted into a proposal.

## Recommendation

Proceed to Q1-SIC-1 design/implementation of `final_safety_arbitration`, but only as a narrow implementation phase with replay-first verification. Q1-SIC-0 replay caught the known Step 4E6 port and parking failure rows and, after normal-frame protection was added to replay, produced `would_touch_normal_frame=0`.

Do not return directly to Step 4E7-D event-safety without arbitration. The replay shows that branch-level telemetry and counters are not enough. Also do not proceed to Step 4E7-D2 port retighten yet; port ownership is documented, but the invariant arbitration layer should land first.
