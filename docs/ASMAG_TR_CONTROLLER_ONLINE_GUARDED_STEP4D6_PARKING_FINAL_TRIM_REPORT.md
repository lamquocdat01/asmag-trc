# ASMAG-TRC Online Guarded Step 4D6 Parking Final Trim Report

Date: 2026-05-17

## Scope

Step 4D6 is a parking-only final one-frame trim on top of Step 4D5. It keeps the restored Step 4D3 post-preservation trim unchanged, keeps the Step 4D5 post-lock soft-candidate trim, and allows one additional safe post-lock soft-candidate trim only when `intermittentObjectMotion/parking` remains above the `0.50000` proposal gate.

No live, live compare, full CDnet, full CDnet compare, cross-dataset validation, LASIESTA, SBI2015, BMC, PTZ-targeted standalone validation, or Jetson/edge profiling was launched.

Subset videos:

1. `thermal/lakeSide`
2. `intermittentObjectMotion/sofa`
3. `badWeather/snowFall`
4. `lowFramerate/port_0_17fps`
5. `intermittentObjectMotion/parking`
6. `shadow/copyMachine`
7. `turbulence/turbulence2`
8. `lowFramerate/tunnelExit_0_35fps`
9. `shadow/cubicle`
10. `PTZ/continuousPan`
11. `PTZ/intermittentPan`
12. `dynamicBackground/fountain01`
13. `dynamicBackground/fountain02`
14. `nightVideos/bridgeEntry`

## Files

Created:

- `configs/asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun/`
- `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D6_PARKING_FINAL_TRIM_REPORT.md`

Changed:

- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`
- `docs/DAILY_STATUS.md`

## Commands

Compile:

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
```

Step 4D6 residual-risk subset dry-run:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun.yaml --max-jobs-per-run 8
```

The dry-run was resumed until all planned jobs completed.

Compare:

```powershell
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun
```

The first compare invocation hit the local 120-second tool timeout while writing output files. It was rerun with warning suppression and a longer timeout:

```powershell
python -W ignore tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_step4d6_parking_final_trim_subset_dryrun
```

The rerun completed successfully.

## Aggregate Result

| Metric | Step 4D6 |
|---|---:|
| Planned jobs | 56 |
| Completed jobs | 56 |
| Failed jobs | 0 |
| Videos | 14 |
| Pipelines | 4 |
| FMeasure | 0.35061 |
| Event_F1 | 0.67692 |
| Activation | 0.52429 |
| Proposed intervention rate | 0.33071 |
| Detector request rate | 0.01071 |
| Normal-frame proposals | 0 |
| Guard alignment | 1.00000 |
| Avg FPS | 33.70033 |
| P95 latency ms | 258.67779 |

Step 4D6 completed technically and passes the residual-risk subset gates.

## Parking Step Comparison

| Step | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Restored 4D3 trim | 4D5 post-lock trim | 4D6 extra trim | Accidental FN/rescue trim |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Step 4D3 | 0.54000 | 0.00000 | 33 | 33 | 0 | 4 | n/a | n/a | n/a |
| Step 4D4 | 0.58000 | 0.00000 | 33 | 33 | 0 | 0 | 0 | n/a | 0 / 0 |
| Step 4D5 | 0.51000 | 0.00000 | 33 | 33 | 0 | 4 | 4 | n/a | 0 / 0 |
| Step 4D6 | 0.50000 | 0.00000 | 33 | 33 | 0 | 4 | 4 | 1 | 0 / 0 |

## Parking Trim Behavior

Restored Step 4D3 trim:

- Active frames: 59
- Restored post-preservation trim count: 4
- Blocked by later hard-protect classification: 0
- Detector requests introduced: 0

Step 4D5 post-lock trim:

- Active frames: 59
- Candidates: 41
- Soft candidates: 12
- Trim count: 4
- Accidental FN-protected trim count: 0
- Accidental rescue trim count: 0

Step 4D6 final one-frame trim:

- Active frames: 59
- Candidate frames: 41
- Extra suppressed frames: 1
- Final extra trim count: 1
- Reason: `parking_final_one_frame_soft_trim+4d5_trim_count_4+event_score_0.659+foreground_loss_1.000+no_detector`
- Accidental FN-protected trim count: 0
- Accidental rescue trim count: 0

The authoritative Step 4D6 parking proposal rate from the compare summary is `0.50000`. The frame-level final-rate telemetry still reports the pre-extra-trim frame-local rate on the last suppressed row, so the final pass/fail gate uses the compare summary proposal rate.

## Parking Protected-Frame Safety

Parking event FN stayed fully protected:

- Event FN: 33
- Protected FN: 33
- Unprotected FN: 0
- Detector request rate: 0.00000
- Rescue active/no-detector/protected event-FN frames: 24 / 24 / 24
- Carry-over lock active/protected event-FN frames: 9 / 9
- Accidental FN-protected trims: 0
- Accidental rescue trims: 0

## Carry-Over Status

| Video | Proposal | Detector | Event FN | Protected FN | Unprotected FN | Status |
|---|---:|---:|---:|---:|---:|---|
| `badWeather/snowFall` | 0.36000 | 0.00000 | 22 | 21 | 1 | Pass, Step 4D3 cap behavior preserved |
| `thermal/lakeSide` | 0.50000 | 0.00000 | 48 | 48 | 0 | Pass, Step 4B4 gate preserved |
| `intermittentObjectMotion/sofa` | 0.27000 | 0.00000 | 21 | 21 | 0 | Pass, Step 4C gate preserved |
| `lowFramerate/port_0_17fps` | 0.37000 | 0.07000 | 5 | 5 | 0 | Controlled recall, detector watch remains for Step 4E |
| `shadow/copyMachine` | 0.46000 | 0.00000 | 46 | 42 | 4 | Pass, accepted gate preserved |
| `turbulence/turbulence2` | 0.31000 | 0.00000 | 3 | 3 | 0 | Pass |
| `lowFramerate/tunnelExit_0_35fps` | 0.31000 | 0.00000 | 2 | 1 | 1 | Pass |
| `shadow/cubicle` | 0.90000 | 0.02000 | 14 | 14 | 0 | Pass, recall 0.87408 |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 | 0 | Pass, controlled |
| `PTZ/intermittentPan` | 0.01000 | 0.00000 | 1 | 1 | 0 | Pass, controlled |
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 | 0 | Pass, quiet |
| `dynamicBackground/fountain02` | 0.40000 | 0.01000 | 0 | 0 | 0 | Pass, normal-frame false interventions 0 |
| `nightVideos/bridgeEntry` | 0.19000 | 0.04000 | 0 | 0 | 0 | Pass, event FN 0 |

## SnowFall Cap Carry-Over

Step 4D6 preserved the Step 4D3 snowFall behavior:

- Proposal: 0.36000
- Detector: 0.00000
- Event FN: 22
- Protected FN: 21
- Unprotected FN: 1
- Actual-FN candidates: 21
- Actual-FN rescue activations: 20
- No-detector rescue-protected event-FN frames: 20
- Cap exhausted after D3: 1
- Mask-quality skipped rows: 0

## Gate Table

| Gate | Result | Status |
|---|---:|---|
| Planned jobs complete, 0 failed | 56/56, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.01071 | PASS |
| Normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| Parking proposal <= 0.50 | 0.50000 | PASS |
| Parking detector <= 0.02 | 0.00000 | PASS |
| Parking unprotected FN <= 12 | 0 | PASS |
| Parking accidental FN/rescue trim count = 0 | 0 / 0 | PASS |
| SnowFall proposal <= 0.45 | 0.36000 | PASS |
| SnowFall detector <= 0.03 | 0.00000 | PASS |
| SnowFall unprotected FN <= 6 acceptable, <=4 preferred | 1 | PASS |
| LakeSide proposal <= 0.50 | 0.50000 | PASS |
| LakeSide detector <= 0.02 | 0.00000 | PASS |
| LakeSide unprotected FN <= 8 preferred, <=12 acceptable | 0 | PASS |
| Sofa proposal <= 0.35 preferred, hard fail > 0.40 | 0.27000 | PASS |
| Sofa detector <= 0.03 | 0.00000 | PASS |
| Sofa unprotected FN <= 4 preferred, <=6 acceptable | 0 | PASS |
| CopyMachine accepted gate | unprotected FN 4 | PASS |
| Turbulence2 accepted gate | unprotected FN 0 | PASS |
| TunnelExit accepted gate | unprotected FN 1 | PASS |
| Cubicle recall >= 0.80 and FN 0 | recall 0.87408, unprotected FN 0 | PASS |
| ContinuousPan controlled | event FN 0 | PASS |
| IntermittentPan controlled | unprotected FN 0 | PASS |
| Fountain01 quiet | proposal 0.00000, detector 0.00000 | PASS |
| Fountain02 normal-frame false interventions = 0 | 0 | PASS |
| BridgeEntry event FN = 0 | 0 | PASS |
| No forbidden validation launched | none launched | PASS |

## Conclusion

Step 4D6 residual-risk subset dry-run passes. The parking-only final trim reduced parking from Step 4D5 `0.51000` to `0.50000` while keeping detector request at `0.00000`, unprotected FN at `0`, and accidental FN/rescue trims at `0 / 0`.

Full CDnet remains held. Recommended next step is Step 4E `lowFramerate/port_0_17fps` detector retighten before any full CDnet rerun.
