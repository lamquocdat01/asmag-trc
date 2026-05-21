"""Gate verification script for guarded_v2_residual_risk_subset_dryrun."""
import json
import pandas as pd
from pathlib import Path

root = Path("outputs/guarded_v2_residual_risk_subset_dryrun")
pipeline = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
pv = pd.read_csv(root / "per_video_summary.csv")
guarded = pv[pv["pipeline"] == pipeline].set_index("video")

def fm(v):
    return float(guarded.loc[v]["FMeasure"]) if v in guarded.index else None

def fr(v):
    return float(guarded.loc[v]["Recall"]) if v in guarded.index else None

def read_frames(category, video):
    p = root / "raw_results" / category / video / pipeline / "frame_metrics.csv"
    return pd.read_csv(p) if p.exists() else None

gates = []

# --- PARKING GATES ---
df_park = read_frames("intermittentObjectMotion", "parking")
fn_park = df_park[df_park["Event_State"] == "FN"]
unfn_park = fn_park[fn_park["ai_intervention_type"].isna() | (fn_park["ai_intervention_type"] == "")]
trim4d6_rate = float(df_park["ai_parking_post_lock_trim_4d6_final_rate"].iloc[-1])
gates.append(("G01_parking_FMeasure_le_050", fm("parking") <= 0.50, fm("parking")))
gates.append(("G02_parking_unprotected_FN_eq_0", len(unfn_park) == 0, len(unfn_park)))
gates.append(("G03_parking_4d6_trim_rate_eq_050", abs(trim4d6_rate - 0.50) < 0.001, trim4d6_rate))

# --- SNOWFALL GATES ---
df_snow = read_frames("badWeather", "snowFall")
f1150 = df_snow[df_snow["raw_frame_id"] == 1150].iloc[0]
gates.append(("G04_snowFall_FMeasure_gt_0", fm("snowFall") > 0, fm("snowFall")))
gates.append(("G05_snowFall_1150_arb_v2_FORCE", f1150["arb_v2_label"] == "FORCE_PROTECT_EVENT_MEMORY", f1150["arb_v2_label"]))
gates.append(("G06_snowFall_1150_action_DETECT_ACC", f1150["action_label"] == "DETECT_ACC", f1150["action_label"]))
gates.append(("G07_snowFall_1150_pred_obj_eq_0", int(f1150["pred_object_count"]) == 0, int(f1150["pred_object_count"])))
gates.append(("G08_snowFall_1150_active_event_eq_1", int(f1150["active_event_memory"]) == 1, int(f1150["active_event_memory"])))
gates.append(("G09_snowFall_1150_risk_high_eq_1", int(f1150["ai_intervention_risk_high"]) == 1, int(f1150["ai_intervention_risk_high"])))
gates.append(("G10_snowFall_1150_arb_v2_override_eq_1", int(f1150["arb_v2_override"]) == 1, int(f1150["arb_v2_override"])))

# --- PER-VIDEO FMEASURE GATES ---
gates.append(("G11_lakeSide_FMeasure_ge_030", fm("lakeSide") is not None and fm("lakeSide") >= 0.30, fm("lakeSide")))
gates.append(("G12_cubicle_Recall_ge_080", fr("cubicle") is not None and fr("cubicle") >= 0.80, fr("cubicle")))
gates.append(("G13_copyMachine_FMeasure_ge_050", fm("copyMachine") is not None and fm("copyMachine") >= 0.50, fm("copyMachine")))
gates.append(("G14_turbulence2_FMeasure_ge_050", fm("turbulence2") is not None and fm("turbulence2") >= 0.50, fm("turbulence2")))
gates.append(("G15_sofa_FMeasure_gt_0", fm("sofa") is not None and fm("sofa") > 0, fm("sofa")))
gates.append(("G16_port_FMeasure_eq_0", fm("port_0_17fps") == 0.0, fm("port_0_17fps")))
gates.append(("G17_fountain01_FMeasure_gt_0", fm("fountain01") is not None and fm("fountain01") > 0, fm("fountain01")))
gates.append(("G18_fountain02_FMeasure_gt_0", fm("fountain02") is not None and fm("fountain02") > 0, fm("fountain02")))
gates.append(("G19_bridgeEntry_FMeasure_gt_0", fm("bridgeEntry") is not None and fm("bridgeEntry") > 0, fm("bridgeEntry")))

# --- SCHEMA GATES ---
q1_sic_cols = [c for c in df_snow.columns if "q1_sic" in c]
gates.append(("G20_no_q1sic_columns_in_output", len(q1_sic_cols) == 0, q1_sic_cols if q1_sic_cols else "none"))
gates.append(("G21_arb_v2_3cols_present", all(c in df_snow.columns for c in ["arb_v2_label", "arb_v2_reason", "arb_v2_override"]),
              [c for c in df_snow.columns if "arb_v2" in c]))

# --- JOB COMPLETION GATE ---
lp = json.loads((root / "live_progress.json").read_text(encoding="utf-8"))
completed = lp["completed_jobs"]
failed = lp["failed_jobs"]
total = lp["total_jobs"]
gates.append(("G22_56_jobs_completed_0_failed", completed == 56 and failed == 0, f"{completed}/{total} failed={failed}"))

# --- PRINT RESULTS ---
pass_count = sum(1 for _, s, _ in gates if s)
fail_count = sum(1 for _, s, _ in gates if not s)

print("=" * 68)
print("GUARDED V2 GATE VERIFICATION REPORT")
print("=" * 68)
for name, status, value in gates:
    icon = "PASS" if status else "FAIL"
    print(f"  [{icon}] {name}: {value}")
print("=" * 68)
print(f"  TOTAL: {pass_count}/{len(gates)} PASS  |  {fail_count} FAIL")
print("=" * 68)

if fail_count == 0:
    print("  VERDICT: ALL GATES PASS - ready to commit")
else:
    print("  VERDICT: GATES FAILED - do NOT commit, report to user")
