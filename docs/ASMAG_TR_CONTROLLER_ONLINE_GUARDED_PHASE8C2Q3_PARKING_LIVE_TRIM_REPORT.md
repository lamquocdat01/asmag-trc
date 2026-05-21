# ASMAG-TR Controller Online Guarded - Phase 8C-2Q3 Parking Live Trim Report

## Scope

Phase 8C-2Q3 is a parking-only retighten after the 8C-2Q2 targeted category live retry completed technically but failed the parking intervention gate.

Forbidden validation remains held: no full CDnet, no full CDnet compare, no cross-dataset validation, no LASIESTA/SBI2015/BMC, and no PTZ-targeted standalone validation.

## Root Cause

8C-2Q2 live retained too many `intermittentObjectMotion/parking` protected/reserve proposals after preservation:

| Run | Parking proposal/intervention | Detector | Event FN | Protected FN | Unprotected FN | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2Q2 dry-run | 0.45000 | 0.00000 | 33 | 28 | 5 | pass |
| 2Q2 live | 0.50000 | 0.00000 | 10 | 6 | 4 | failed proposal gate only |

The 2Q2 live reserve protected FN risk and stayed no-detector, but live post-preservation cap accounting retained 50/100 parking frames. The 2Q3 patch adds a second no-detector, parking-only trim for generic non-risk retained proposals once the parking final count is above the 0.44 soft target / 0.45 hard gate.

## 2Q3 Policy

Config added in `configs/asmag_tr_controller_online_guarded_cdnet_targeted_category_2q3_dryrun.yaml` and inherited by live:

- `ai_parking_live_post_trim_2q3_enabled: true`
- exact target: `intermittentObjectMotion/parking`
- no detector
- generic non-risk only
- do not trim rescue, live reserve, preserved FN-risk, likely unprotected-FN, or deterministic emergency frames
- min/max trim frames: 5/8
- priority: after preserve/rescue, before final parking summary

## Validation

Compile passed:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Targeted category 2Q3 dry-run completed:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2q3_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2q3_dryrun
```

Live was not run because dry-run failed the parking proposal gate.

### Dry-Run

| Metric | 2Q3 dry-run |
| --- | ---: |
| Jobs | 80/80 completed, 0 failed |
| FMeasure | 0.43284 |
| Event_F1 | 0.66513 |
| Activation | 0.57478 |
| Avg_FPS | 27.14769 |
| P95 latency | 238.93533 ms |
| Proposal rate | 0.21385 |
| Detector request rate | 0.01011 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

Dry-run gate result: **FAIL**.

The failure is isolated to `intermittentObjectMotion/parking` proposal pressure:

| Run | Parking proposal/intervention | Detector | Event FN | Protected FN | Unprotected FN | 2Q3 trim count | Accidental protected trim | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2Q2 dry-run | 0.45000 | 0.00000 | 33 | 28 | 5 | n/a | 0 | pass |
| 2Q2 live | 0.50000 | 0.00000 | 10 | 6 | 4 | n/a | 0 | failed proposal gate |
| 2Q3 dry-run | 0.50000 | 0.00000 | 33 | 29 | 4 | 0 | 0 | failed proposal gate |

2Q3 post-trim behavior:

- 2Q3 active frames: 50
- 2Q3 candidate frames: 0
- 2Q3 suppressed generic non-risk frames: 0
- 2Q3 trim count max: 0
- 2Q3 final rate max: 0.50000
- skipped rescue frames: 24
- skipped live reserve frames: 8
- skipped preserved FN-risk frames: 29
- skipped likely unprotected-FN frames: 29
- accidental protected/reserve trim count: 0

Root cause: the 2Q3 candidate predicate was too strict. It required generic non-risk proposals to have no intermittent parking memory/localized FN-risk, but all retained over-gate parking proposals were classified as protected/reserve/FN-risk or otherwise `not_generic_nonrisk`. The patch therefore preserved safety but did not reclaim any of the five required frames.

Narrow next fix: keep the same parking-only/no-detector scope, but introduce a second-tier parking trim candidate for over-hard-gate frames that are not rescue-active, not live-reserve-active, not preserved FN-risk-active, not likely-unprotected-FN, and not deterministic emergency, without requiring the broader `not_generic_nonrisk` rejection. The trim should use explicit protected-frame exclusions as the safety boundary and should only begin when retained parking count is above the hard 0.45 gate.

### Live

Not run. The 2Q3 targeted category live output root remains unused because dry-run failed.

## Core Gate Status

| Gate | 2Q3 dry-run status |
| --- | --- |
| Aggregate detector request < 0.10 | PASS: 0.01011 |
| Normal-frame proposals = 0 | PASS: 0 |
| Guard alignment >= 0.95 | PASS: 1.00000 |
| Parking proposal <= 0.45 | FAIL: 0.50000 |
| Parking detector <= 0.02 | PASS: 0.00000 |
| Parking unprotected FN <= 12 | PASS: 4 |
| Accidental protected/rescue trim count = 0 | PASS: 0 |
| Cubicle recall >= 0.80 and unprotected FN = 0 | PASS: recall 0.90909, unprotected FN 0 |
| PTZ/intermittentPan proposal <= 0.15 and unprotected FN = 0 | PASS: 0.01000, unprotected FN 0 |
| PTZ/continuousPan proposal <= 0.05 | PASS: 0.05000 |
| BridgeEntry event FN = 0 | PASS: 0 |
| TramCrossroad_1fps proposal/detector <= 0.05/0.02 | PASS: 0.00000/0.00000 |
| Fountain01 proposal/detector <= 0.05/0.02 | PASS: 0.00000/0.00000 |
| Fountain02 normal-frame false interventions = 0 | PASS: 0 |
| CopyMachine unprotected FN <= 15 | PASS: 4 |
| Turbulence2 proposal <= 0.35 and unprotected FN <= 2 | PASS: 0.31000, unprotected FN 0 |
| TunnelExit_0_35fps proposal <= 0.35 and unprotected FN <= 1 | PASS: 0.30000, unprotected FN 1 |

## Safety Audit

- Full CDnet was not launched.
- Full CDnet compare was not launched.
- Cross-dataset validation was not launched.
- PTZ-targeted standalone validation was not launched.
- LASIESTA/SBI2015/BMC were not launched.
- Accidental 8C-2E live artifacts were not deleted or used.
- Default guarded config remains unchanged with `ai_intervention_enabled: false`.

## Decision

8C-2Q3 dry-run does **not** pass. Step 3B targeted category live remains held. Step 4 full CDnet dry-run remains held.
