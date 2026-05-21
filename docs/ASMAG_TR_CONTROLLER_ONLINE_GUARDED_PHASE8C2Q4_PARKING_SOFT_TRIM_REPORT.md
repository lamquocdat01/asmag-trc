# ASMAG-TR Controller Online Guarded - Phase 8C-2Q4 Parking Soft Trim Report

## Scope

Phase 8C-2Q4 is a parking-only soft-preserved trim after 8C-2Q3 failed because its candidate predicate was too strict.

The policy applies only to `intermittentObjectMotion/parking`, remains no-detector, and preserves the existing 2Q2/2Q3 parking rescue, preserve, live cap reserve, burst bridge, final-normal suppressor, and detector-safety controls.

Forbidden validation remains held unless explicitly noted in the validation section: no full CDnet, no full CDnet compare, no cross-dataset validation, no LASIESTA/SBI2015/BMC, and no PTZ-targeted standalone validation.

## Policy

2Q4 adds a soft-preserved trim after parking preserve/rescue/live-reserve logic:

- hard-protected frames are never intended to be trimmed
- hard-protected includes rescue, live reserve/bridge, likely unprotected-FN, deterministic emergency, strong event score, strong foreground-loss score in event/FN-risk context, and active-memory/reuse-age hard context
- soft-preserved frames may be trimmed only if no detector is requested, the frame is not final-normal/runtime-normal, not rescue, not live reserve, not likely unprotected-FN, and not deterministic emergency
- trim stops after the parking final rate is brought back to the 0.45 hard gate, with a small 5-8 frame trim budget

## Validation

Compile passed:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Targeted category 2Q4 dry-run completed:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2q4_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_category_2q4_dryrun
```

Live was not run because dry-run failed the parking proposal gate.

### Dry-Run

| Metric | 2Q4 dry-run |
| --- | ---: |
| Jobs | 80/80 completed, 0 failed |
| FMeasure | 0.43293 |
| Event_F1 | 0.66513 |
| Activation | 0.57878 |
| Avg_FPS | 28.11636 |
| P95 latency | 235.00799 ms |
| Proposal rate | 0.21183 |
| Detector request rate | 0.00910 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |

Dry-run gate result: **FAIL**.

The failure remains isolated to `intermittentObjectMotion/parking` proposal pressure:

| Run | Parking proposal/intervention | Detector | Event FN | Protected FN | Unprotected FN | Soft trim count | Accidental hard-protected trim | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2Q2 dry-run | 0.45000 | 0.00000 | 33 | 28 | 5 | n/a | 0 | pass |
| 2Q2 live | 0.50000 | 0.00000 | 10 | 6 | 4 | n/a | 0 | failed proposal gate |
| 2Q3 dry-run | 0.50000 | 0.00000 | 33 | 29 | 4 | 0 | 0 | failed proposal gate |
| 2Q4 dry-run | 0.50000 | 0.00000 | 33 | 29 | 4 | 0 | 0 | failed proposal gate |

2Q4 soft-trim behavior:

- active frames: 50
- hard-protected frames: 50
- soft-preserved frames: 18
- soft-preserved candidate frames: 0
- suppressed frames: 0
- trim count max: 0
- final rate max: 0.50000
- skipped hard-protected frames: 50
- skipped rescue frames: 24
- skipped live reserve frames: 8
- skipped likely unprotected-FN frames: 29
- accidental hard-protected trim count: 0

Root cause: the soft-preserved boundary was loosened enough to identify 18 soft-preserved parking frames, but each of those frames was also classified as hard-protected by the deterministic/emergency safeguard path. Since 2Q4 correctly honored `never_trim_hard_protected`, no frames were reclaimed and parking stayed at 0.50000.

Narrow next fix: separate deterministic emergency safeguards from deterministic empty-output pressure in parking. The next patch should keep true hard emergency frames untrimmable, but define a parking-only "soft deterministic retained proposal" class for low-event-score, no-detector, non-rescue, non-live-reserve, non-likely-FN frames. That would allow reclaiming the five early low-risk retained frames without touching live reserve/protected FN frames.

### Live

Not run. The 2Q4 targeted category live output root remains unused because dry-run failed.

## Core Gate Status

| Gate | 2Q4 dry-run status |
| --- | --- |
| 80/80 completed, 0 failed | PASS: 80/80, 0 failed |
| Aggregate detector request < 0.10 | PASS: 0.00910 |
| Normal-frame proposals = 0 | PASS: 0 |
| Guard alignment >= 0.95 | PASS: 1.00000 |
| Parking proposal <= 0.45 | FAIL: 0.50000 |
| Parking detector <= 0.02 | PASS: 0.00000 |
| Parking unprotected FN <= 12 | PASS: 4 |
| Parking accidental hard-protected trim count = 0 | PASS: 0 |
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

8C-2Q4 dry-run does **not** pass. Step 3B targeted category live remains held. Step 4 full CDnet dry-run remains held.
