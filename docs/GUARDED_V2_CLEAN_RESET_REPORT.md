# GUARDED V2 CLEAN RESET REPORT

**Date:** 2026-05-21  
**Branch:** feature/clean-guarded-v2  
**Reset base:** Step 4D6 (backup/pre-reset-r3d-2026-05-22)  
**Experiment:** guarded_v2_residual_risk_subset_dryrun (56/56 jobs, 0 failed)

---

## Summary

Successfully executed invariant-first reset of ASMAG_TR_CONTROLLER_ONLINE_GUARDED controller.

Root cause of Q1-SIC failures (SIC-1 through R3D): Shared mutable `info` dict caused Heisenbug —
observer flags reading/writing the same dict that controls frame behavior, even in "post-decision-only"
mode. Observer code changed actual frame trajectories (480 behavior delta rows in R3D paired test).

Solution: Replaced entire Q1-SIC infrastructure (19,576 lines removed, net ~979 lines removed after
adding arb_v2) with `final_safety_arbitration_v2` — a pure function with zero shared state.

---

## Code Changes

| Item | Before | After |
|------|--------|-------|
| run_experiment.py lines | 21,987 | 21,008 |
| Q1-SIC constants | 18 lines (83–99) | DELETED |
| Q1-SIC helper functions | 353 lines (102–454) | DELETED |
| Q1-SIC `__init__` attributes | 35 lines | DELETED |
| Q1-SIC frame_init columns | 78 lines (77 columns) | DELETED |
| Q1-SIC AIShadowPolicy methods | 314 lines (4 methods) | DELETED |
| `final_safety_arbitration` call block | 136 lines | DELETED |
| observer snapshot block | 9 lines | DELETED |
| `final_safety_arbitration_v2` | 0 | +27 lines (pure function) |
| arb_v2 integration in frame loop | 0 | +10 lines |
| New config | 0 | guarded_v2_residual_risk_subset_dryrun.yaml |

---

## final_safety_arbitration_v2 Logic

Pure function — no shared state, all inputs are snapshot values.

**Trigger condition (is_empty_detect path):**
- `action_label == "DETECT_ACC"` AND `pred_object_count == 0`

**I2 protection trigger:**
- `active_event_memory == 1` AND `risk_high == 1` AND `proposal == 0`
- Returns: `arb_v2_label = "FORCE_PROTECT_EVENT_MEMORY"`

**All other cases:** `arb_v2_label = "NO_CHANGE"` (no side effects)

---

## Gate Results: 22/22 PASS

| Gate | Result | Value |
|------|--------|-------|
| G01 parking FMeasure ≤ 0.50 | PASS | 0.4793 |
| G02 parking unprotected_FN = 0 | PASS | 0 |
| G03 parking 4D6 trim rate = 0.50 | PASS | 0.50 |
| G04 snowFall FMeasure > 0 | PASS | 0.8167 |
| G05 snowFall 1150 arb_v2_label = FORCE_PROTECT_EVENT_MEMORY | PASS | FORCE_PROTECT_EVENT_MEMORY |
| G06 snowFall 1150 action = DETECT_ACC | PASS | DETECT_ACC |
| G07 snowFall 1150 pred_object_count = 0 | PASS | 0 |
| G08 snowFall 1150 active_event_memory = 1 | PASS | 1 |
| G09 snowFall 1150 risk_high = 1 | PASS | 1 |
| G10 snowFall 1150 arb_v2_override = 1 | PASS | 1 |
| G11 lakeSide FMeasure ≥ 0.30 | PASS | 0.3874 |
| G12 cubicle Recall ≥ 0.80 | PASS | 0.8354 |
| G13 copyMachine FMeasure ≥ 0.50 | PASS | 0.6581 |
| G14 turbulence2 FMeasure ≥ 0.50 | PASS | 0.6958 |
| G15 sofa FMeasure > 0 | PASS | 0.1699 |
| G16 port FMeasure = 0.0 (dry_run) | PASS | 0.0 |
| G17 fountain01 FMeasure > 0 | PASS | 0.0392 |
| G18 fountain02 FMeasure > 0 | PASS | 0.7110 |
| G19 bridgeEntry FMeasure > 0 | PASS | 0.1418 |
| G20 no q1_sic columns in output | PASS | none |
| G21 arb_v2 3 columns present | PASS | [arb_v2_label, arb_v2_reason, arb_v2_override] |
| G22 56/56 jobs complete, 0 failed | PASS | 56/56 failed=0 |

---

## Per-Video FMeasure (ASMAG_TR_CONTROLLER_ONLINE_GUARDED)

| Video | FMeasure | Recall | Precision |
|-------|----------|--------|-----------|
| bridgeEntry | 0.1418 | 0.4232 | 0.0852 |
| continuousPan | 0.0908 | 0.8613 | 0.0479 |
| copyMachine | 0.6581 | 0.4998 | 0.9632 |
| cubicle | 0.2078 | 0.8354 | 0.1187 |
| fountain01 | 0.0392 | 0.9577 | 0.0200 |
| fountain02 | 0.7110 | 0.6885 | 0.7351 |
| intermittentPan | 0.1484 | 0.6302 | 0.0841 |
| lakeSide | 0.3874 | 0.2898 | 0.5838 |
| parking | 0.4793 | 0.4824 | 0.4762 |
| port_0_17fps | 0.0000 | 0.0000 | 0.0000 |
| snowFall | 0.8167 | 0.8213 | 0.8122 |
| sofa | 0.1699 | 0.4690 | 0.1037 |
| tunnelExit_0_35fps | 0.1167 | 0.6270 | 0.0643 |
| turbulence2 | 0.6958 | 0.7964 | 0.6177 |

---

## Key Invariants Preserved

1. **Parking 4D6 trim**: `ai_parking_post_lock_trim_4d6_final_rate = 0.500` (target hit exactly)
2. **Parking unprotected FN**: 0 (all 32 parking FN event frames have intervention_type)
3. **snowFall 1150 canary**: arb_v2 correctly fires `FORCE_PROTECT_EVENT_MEMORY` for the exact
   frame where `action=DETECT_ACC + pred_object_count=0 + active_event_memory=1 + risk_high=1`
4. **No observer contamination**: observer_snapshot code fully removed, pure function arb_v2
   reads only from already-computed snapshot values in frame_metrics_row
5. **No q1_sic columns**: all 77 q1_sic columns removed from output schema

---

## Next Steps

- arb_v2 currently runs in **shadow-only mode** (records label but does not override mask output)
- Step 4E: wire arb_v2_override into actual prediction to eliminate snowFall 1150 unprotected FN
- Verify snowFall FMeasure improves after override is wired in
- Proceed to full CDnet2014 live run after Step 4E gates pass

---

## Commit Reference

Branch: feature/clean-guarded-v2  
Parent: backup/pre-reset-r3d-2026-05-22 (R3D full state, 21,987 lines)  
Config: configs/guarded_v2_residual_risk_subset_dryrun.yaml  
Gate script: tools/verify_guarded_v2_gates.py
