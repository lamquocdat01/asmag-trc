# ASMAG-TR Q1 Safety-Invariant Specification

Date: 2026-05-19

## Purpose

Q1-SIC-0 converts the Step 4E6 failure pattern into an invariant-first safety specification. The goal is to stop branch-first patching and require every future guarded-controller branch to pass offline trajectory and counterfactual arbitration checks before any new experiment or dry-run.

The intended architecture is:

```text
motion / policy / reuse branches
-> trajectory state reconstruction
-> safety invariant checks
-> final arbitration recommendation
-> offline replay
-> staged validation only after replay passes
```

This specification does not modify controller behavior. It defines the safety contract that a later final arbitration layer must satisfy.

## Invariants

| ID | Name | Requirement | Failure prevented |
|---|---|---|---|
| I0 | Experiment safety invariant | No full CDnet, live, live compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling until staged validation passes. | Expensive or unsafe validation before local evidence is stable. |
| I1 | Normal-frame safety invariant | Normal-frame proposals must remain 0 for accepted guarded branches. No final arbitration may convert quiet normal frames into false intervention rows. | A safety branch that protects events by creating normal-frame false interventions. |
| I2 | Event-memory preservation invariant | If a row belongs to an active event/risk window and the reference stable trajectory had `active_event_memory=1` or `ai_intervention_guard_active=1`, a later branch must not silently drop to `active_event_memory=0` without a logged reason and protection alternative. | Step 4E6 parking lost active event memory and therefore missed rescue/carry-over candidate predicates. |
| I3 | Risk-high unprotected-FN invariant | A row that is risk-high, likely-unprotected-FN, or inside a known event-risk window must not end as unprotected FN under `CLOSED_EMPTY_*`, unsafe reuse, or fallback actions unless explicitly waived by a named watch-only rule. | Step 4E6 parking and port rows ended as unprotected FN under unsafe empty/fallback actions. |
| I4 | Enforcement-vs-telemetry invariant | Every lock, rescue, and guard column must be classified as telemetry-only, candidate-only, final-action-enforcing, protection-accounting-enforcing, or detector-schedule-enforcing. Report-only status cannot be counted as a pass condition. | Step 4E6 snowFall/lakeSide gate locks reported status but did not enforce final protection accounting. |
| I5 | Branch reachability invariant | If a known critical frame is not selected as a candidate, the report must classify whether the miss came from branch inactive, candidate predicate false, action set mismatch, cap/cooldown, final action frozen, trajectory shift, or telemetry-only behavior. | Step 4E6 port hard-lock telemetry fired elsewhere but did not reach frames 1350/1355. |
| I6 | Trajectory preservation invariant | For known residual-risk videos, accepted behavior must be compared by trajectory state, not only final aggregate counts. Required fields are frame, ground-truth/frame state, final action, selected modes before/after guard, detector request, proposal flag, active event memory, risk-high, guard active, rescue candidate, rescue active, carry-over lock active, protected FN, unprotected FN, and branch reject reason. | Step 4E6 restored parking counters but not the Step 4D6 trajectory state that made rescue possible. |
| I7 | Split-branch invariant | Event-safety and detector-retighten must not be optimized in the same branch until both pass separately. Step 4D6 is the event-safety reference. Step 4E4 is the port detector-retighten reference. Port detector pressure is watch-only in an event-safety branch unless it causes a new event-safety regression. | Step 4E6 mixed port retighten and event-safety restoration, destabilizing both. |
| I8 | Full-validation invariant | Full CDnet remains held until the residual-risk subset and targeted CDnet pass under the staged validation plan. | Promotion from local branch evidence to broad validation without staged gates. |

## Trajectory Fields

Q1 replay reports must reconstruct these fields wherever available:

- `frame_id`
- `Event_State`
- `action_label` or final action
- `selected_mode_before_guard`
- `selected_mode_after_guard`
- detector request
- proposal/intervention flag
- `active_event_memory`
- `ai_intervention_risk_high`
- `ai_intervention_guard_active`
- rescue candidate flags
- rescue active flags
- carry-over lock active flags
- protected FN
- unprotected FN
- branch reject or status reason

Missing columns must be reported as `NA` and summarized. Older outputs are allowed to lack newer telemetry, but missing data cannot be treated as proof of safety.

## Enforcement Classes

Every branch-status column used in a pass/fail decision must be classified before acceptance:

| Enforcement class | Meaning | Pass-condition use |
|---|---|---|
| telemetry-only | Reports a status string or branch intent only. | Cannot count as pass evidence. |
| candidate-only | Marks that a row was eligible but does not change final action or protection accounting. | Can explain reachability but cannot count as protection. |
| final-action-enforcing | Mutates or freezes final action/detector request. | Can count if final row outcome is safe. |
| protection-accounting-enforcing | Produces protected-FN accounting without a detector. | Can count if normal-frame invariant remains clean. |
| detector-schedule-enforcing | Keeps, suppresses, or retimes detector requests. | Must be checked against downstream event safety. |

## Branch Ownership

Event-safety branch:

- Reference: Step 4D6.
- Owns parking, snowFall, lakeSide, sofa, copyMachine, turbulence2, tunnelExit, cubicle, PTZ safety, fountain quiet behavior, and bridgeEntry event-FN safety.
- Does not own port detector retighten, except as telemetry/watch.

Detector-retighten branch:

- Reference: Step 4E4 for `lowFramerate/port_0_17fps`.
- Owns detector pressure and context-detector/holdout behavior for port frames such as 1350 and 1355.
- Must not be combined with event-safety freeze until both branches are independently stable.

## Offline Replay Gate

Before a new controller patch is tested, an offline replay must answer:

1. Which invariant would catch each known failure row?
2. Which final arbitration label would be recommended?
3. Would the recommended arbitration touch any quiet normal-frame row?
4. Is the row event-safety-owned, detector-retighten-owned, or watch-only?
5. Is the required telemetry present, or must telemetry be improved first?

Only if replay catches the known Step 4E6 failures without touching quiet normal-frame rows should Q1-SIC-1 proceed to controller implementation.
