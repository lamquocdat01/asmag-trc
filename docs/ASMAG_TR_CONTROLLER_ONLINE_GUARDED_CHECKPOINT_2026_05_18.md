# ASMAG-TR Controller Online Guarded Checkpoint - 2026-05-18

## Current Highest Validated Milestone

- Step 3B targeted category live is frozen as PASS under the revised protection-aware parking gate.
- 8C-2Q2 is the current full-CDnet dry-run candidate lineage.
- Full CDnet success is not yet achieved.
- Full CDnet live remains held.
- Cross-dataset validation remains held.

## Step 4 Full CDnet Dry-Run Status

The Step 4 full CDnet dry-run completed technically, but it is not a clean Step 4 pass because residual risks remain.

| Item | Value |
|---|---:|
| Categories | 11 |
| Videos | 53 |
| Pipelines | 4 |
| Jobs completed | 212/212 |
| Failed jobs | 0 |
| FMeasure | 0.47863 |
| Event_F1 | 0.76989 |
| Detector request rate | 0.01211 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

## Step 4 Residual-Risk Work Completed

- Step 4A audit completed.
- Step 4B4 lakeSide stabilization passed the residual subset:
  - lakeSide proposal 0.50000
  - detector 0.00000
  - unprotected FN 0
- Step 4C sofa rescue passed:
  - sofa unprotected FN 10 -> 0
  - detector 0.00000
- Step 4D6 parking/snowFall subset state passed before later port work:
  - snowFall 0.36000 / detector 0.00000 / unprotected FN 1
  - parking 0.50000 / detector 0.00000 / unprotected FN 0
- Step 4E4 port detector retighten improved `lowFramerate/port_0_17fps`:
  - port detector 0.05000
  - unprotected FN 0
  - frames 1350 and 1355 protected
- Step 4E5 failed.
- Step 4E6 failed.

## Latest Failed State: Step 4E6

Step 4E6 completed technically but did not enforce the intended behavior locks.

| Item | Value |
|---|---:|
| Jobs completed | 56/56 |
| Failed jobs | 0 |
| FMeasure | 0.29046 |
| Event_F1 | 0.62271 |
| Detector request rate | 0.01500 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

Failed gates:

- `lowFramerate/port_0_17fps` detector 0.08000 > 0.05000.
- port unprotected FN 4.
- port frames 1350 and 1355 remained unprotected FN.
- `intermittentObjectMotion/parking` proposal 0.57000 > 0.50000.
- parking unprotected FN 9.
- snowFall proposal/FN gate failed.
- lakeSide FN gate failed.
- cubicle recall 0.77419 failed.
- intermittentPan unprotected FN 2.

Root cause summary:

- Hard-lock flags were active but did not enforce behavior.
- Port V4 lock did not reach the no-detector protection path for frames 1350 and 1355.
- Parking trim counters were restored, but the Step 4D6 protection trajectory was not restored.
- The failure appears to be a branch-order/action-branch enforcement issue, not a missing-config-only issue.

## Current Recommended Next Step

Proceed with Step 4E6-BRANCH-AUDIT.

- Audit only.
- No experiment.
- Determine why port hard lock was telemetry-active but did not protect frames 1350 and 1355.
- Determine why parking 4D6 trajectory was not restored despite trim counters.
- Classify failures as telemetry-only, branch inactive, action branch not reached, final action frozen, cap/cooldown, or trajectory shift.
- Full CDnet rerun remains held until this audit is complete.

## Current Decision

- Do not continue patching from Step 4E6 blindly.
- Do not run full CDnet.
- Do not run live.
- Do not run cross-dataset.
- Next action is audit, not patch.

## Safety Confirmation

- No experiments were run during this checkpoint update.
- No outputs were deleted.
- No configs were modified.
- No controller code was modified.
- Default guarded config remains unchanged with `ai_intervention_enabled: false`.

## Resume / Next Prompt Hint

Use the Step 4E6-BRANCH-AUDIT prompt next.

After audit, choose one of:

A. Exact row/action-branch patch for port only.
B. Rebase to Step 4E4 output behavior and accept parking residual.
C. Roll back or defer port retighten as a watch item.
D. Split event-safety branch and detector-retighten branch.
