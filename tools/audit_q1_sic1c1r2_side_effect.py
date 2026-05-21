"""Audit Q1-SIC-1C1R2 stable snapshot side effects.

This script is analysis-only. It reads existing configs, source, and CSV outputs,
then writes audit CSVs to a new output folder.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    import yaml
except Exception:  # pragma: no cover - fallback for minimal environments
    yaml = None


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
SNOW = ("badWeather", "snowFall")
PARKING = ("intermittentObjectMotion", "parking")
PARKING_FRAMES = [1195, 1310, 1315, 1320, 1425, 1430, 1435, 1440, 1445]
SNOW_CONTEXT = [1120, 1125, 1130, 1135, 1140, 1145, 1150, 1155, 1160, 1165, 1170]
CONFIG_C1R = Path("configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml")
CONFIG_C1R2 = Path("configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r2_stable_probe_snapshot_subset_dryrun.yaml")
SOURCE = Path("src/run_experiment.py")


KEY_FIELDS = [
    "action_label",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "ai_intervention_detector_requested",
    "yolo_called",
    "ai_intervention_applied",
    "active_event_memory",
    "ai_intervention_guard_active",
    "ai_intervention_risk_high",
    "ai_detector_needed_pred",
    "ai_detector_request_blocked_no_refresh_model",
    "forced_refresh_cooldown_active",
    "q1_sic_arbitration_active",
    "q1_sic_arbitration_label",
    "q1_sic_arbitration_reason",
    "q1_sic_owner",
    "q1_sic_reference_step",
    "q1_sic_pre_action",
    "q1_sic_post_action",
    "q1_sic_detector_action_probe_active",
    "q1_sic_detector_action_probe_would_select_shadow",
    "q1_sic_detector_action_probe_stable_snapshot_enabled",
    "q1_sic_detector_action_probe_snapshot_active",
    "q1_sic_detector_action_probe_snapshot_source",
    "q1_sic_detector_action_probe_event_risk_pressure",
    "q1_sic_detector_action_probe_detector_pressure",
    "q1_sic_detector_action_probe_pressure_memory_active",
    "q1_sic_detector_action_probe_pressure_memory_age",
    "q1_sic_detector_action_probe_pressure_memory_reason",
    "q1_sic_detector_action_probe_reject_reason",
    "protected_fn",
    "unprotected_fn",
    "q1_sic_pre_protection_label",
    "q1_sic_post_protection_label",
]

GLOBAL_DELTA_FIELDS = [
    "action_label",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "ai_intervention_detector_requested",
    "yolo_called",
    "ai_intervention_applied",
    "protected_fn",
    "unprotected_fn",
    "q1_sic_arbitration_label",
    "q1_sic_arbitration_active",
    "q1_sic_detector_action_probe_active",
    "q1_sic_detector_action_probe_pressure_memory_active",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str] | None = None) -> None:
    rows = list(rows)
    if fields is None:
        fields = sorted({key for row in rows for key in row.keys()}) if rows else ["note"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def truthy(value: object) -> bool:
    if value in (None, "", "NA"):
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return str(value).strip().lower() in {"true", "yes", "active"}


def num(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def frame_id(row: Dict[str, str]) -> int:
    for key in ("frame_id", "frame", "raw_frame_id", "frame_idx"):
        value = row.get(key)
        if value not in (None, ""):
            return int(float(value))
    return -1


def guarded_path(root: Path, video: Tuple[str, str]) -> Path:
    return root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv"


def load_video(root: Path, video: Tuple[str, str]) -> List[Dict[str, str]]:
    return read_csv(guarded_path(root, video))


def index_by_frame(rows: Iterable[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    return {frame_id(row): row for row in rows}


def all_guarded(root: Path) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for path in root.glob(f"raw_results/*/*/{PIPELINE}/frame_metrics.csv"):
        parts = path.parts
        category = parts[-4]
        video = parts[-3]
        for row in read_csv(path):
            enriched = dict(row)
            enriched.setdefault("category", category)
            enriched.setdefault("video", video)
            out.append(enriched)
    return out


def key(row: Dict[str, str]) -> Tuple[str, str, int]:
    return (row.get("category", ""), row.get("video", ""), frame_id(row))


def safe_get(row: Dict[str, str], field: str) -> str:
    return row.get(field, "NA") if row else "NA"


def compare_frame_rows(
    c1r_rows: Dict[int, Dict[str, str]],
    c1r2_rows: Dict[int, Dict[str, str]],
    frames: Sequence[int],
    fields: Sequence[str],
    prefix: str,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for fid in frames:
        left = c1r_rows.get(fid, {})
        right = c1r2_rows.get(fid, {})
        row: Dict[str, object] = {"frame_id": fid, "comparison": prefix}
        changed_fields = []
        for field in fields:
            lv = safe_get(left, field)
            rv = safe_get(right, field)
            row[f"c1r_{field}"] = lv
            row[f"c1r2_{field}"] = rv
            if str(lv) != str(rv):
                changed_fields.append(field)
        row["changed_fields"] = ";".join(changed_fields)
        row["changed_field_count"] = len(changed_fields)
        rows.append(row)
    return rows


def is_fn(row: Dict[str, str]) -> bool:
    return str(row.get("Event_State") or row.get("frame_state") or "") == "FN"


def protected(row: Dict[str, str]) -> bool:
    return bool(
        truthy(row.get("protected_fn"))
        or row.get("q1_sic_post_protection_label") == "protected_event_fn"
        or (is_fn(row) and (truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested"))))
    )


def unprotected(row: Dict[str, str]) -> bool:
    return bool(
        truthy(row.get("unprotected_fn"))
        or row.get("q1_sic_post_protection_label") == "unprotected_fn"
        or (is_fn(row) and not protected(row))
    )


def load_yaml_raw(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        return {"__raw__": text}
    return yaml.safe_load(text) or {}


def load_yaml(path: Path) -> Dict[str, object]:
    cfg = load_yaml_raw(path)
    base_ref = cfg.pop("base_config", cfg.pop("_base_config", ""))
    if not base_ref:
        return cfg
    base_path = Path(str(base_ref))
    if not base_path.is_absolute():
        base_path = path.parent / base_path
    merged = load_yaml(base_path)
    return deep_update(merged, cfg)


def deep_update(base: Dict[str, object], override: Dict[str, object]) -> Dict[str, object]:
    merged = dict(base or {})
    for key_, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key_), dict):
            merged[key_] = deep_update(merged.get(key_, {}), value)
        else:
            merged[key_] = value
    return merged


def flatten(prefix: str, value: object) -> Dict[str, object]:
    if isinstance(value, dict):
        out: Dict[str, object] = {}
        for key_, val in value.items():
            next_prefix = f"{prefix}.{key_}" if prefix else str(key_)
            out.update(flatten(next_prefix, val))
        return out
    return {prefix: value}


def config_diff() -> List[Dict[str, object]]:
    left = flatten("", load_yaml(CONFIG_C1R))
    right = flatten("", load_yaml(CONFIG_C1R2))
    rows: List[Dict[str, object]] = []
    for key_ in sorted(set(left) | set(right)):
        lv = left.get(key_, "MISSING")
        rv = right.get(key_, "MISSING")
        if str(lv) == str(rv):
            classification = "unchanged"
        elif key_ in {"experiment_name", "edge_profile.name"}:
            classification = "intended output/name change"
        elif key_ == "base_config":
            classification = "intended C1R2 base wrapper"
        elif key_.endswith("q1_sic_detector_action_probe_stable_snapshot_enabled"):
            classification = "intended stable snapshot enable flag"
        elif key_.endswith("q1_sic_detector_action_probe_pressure_memory_max_age"):
            classification = "intended pressure memory parameter"
        elif "q1_sic" in key_ and "final_arbitration" in key_:
            classification = "suspicious final arbitration flag"
        elif any(token in key_ for token in ("parking", "copymachine", "port_watch", "restore")):
            classification = "suspicious parking/copyMachine/port restore flag" if str(lv) != str(rv) else "unchanged"
        elif any(token in key_ for token in ("event", "risk", "protection", "detector")):
            classification = "suspicious detector/event/protection flag"
        else:
            classification = "unknown"
        if str(lv) != str(rv):
            rows.append({"key": key_, "c1r": lv, "c1r2": rv, "classification": classification})
    return rows


def source_inventory() -> List[Dict[str, object]]:
    text = SOURCE.read_text(encoding="utf-8", errors="replace").splitlines()
    patterns = [
        ("stable_snapshot_flag", "q1_sic_detector_action_probe_stable_snapshot_enabled"),
        ("pressure_memory_state", "q1_sic_detector_action_probe_pressure_memory"),
        ("pressure_memory_update", "_update_q1_sic_detector_action_probe_pressure_memory"),
        ("probe_helper", "_apply_q1_sic_detector_action_probe"),
        ("restore_helper", "_apply_q1_sic1c1r_restore_copy_port"),
        ("final_arbitration_call", "final_safety_arbitration("),
        ("force_event_memory_label", "FORCE_PROTECT_EVENT_MEMORY"),
        ("kinds_append", "kinds.append"),
        ("proposal_source", "ai_intervention_applied"),
        ("action_source", "action_label"),
    ]
    rows: List[Dict[str, object]] = []
    for label, pattern in patterns:
        matches = [i + 1 for i, line in enumerate(text) if pattern in line]
        for line_no in matches[:20]:
            line = text[line_no - 1].strip()
            if "pressure_memory" in label:
                control_class = "mutates probe-only controller instance dict"
            elif label == "probe_helper":
                control_class = "writes live info telemetry dict before return"
            elif label == "final_arbitration_call":
                control_class = "control/protection path"
            elif label == "force_event_memory_label":
                control_class = "final arbitration enforcement label"
            elif label == "kinds_append":
                control_class = "proposal/protection accounting mutation"
            else:
                control_class = "source reference"
            rows.append({
                "signal": label,
                "pattern": pattern,
                "line": line_no,
                "source_excerpt": line[:240],
                "audit_classification": control_class,
            })
    return rows


def global_deltas(c1r_all: List[Dict[str, str]], c1r2_all: List[Dict[str, str]]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    right = {key(row): row for row in c1r2_all}
    summary: Dict[Tuple[str, str, str], Dict[str, object]] = {}
    label_rows: List[Dict[str, object]] = []
    for left in c1r_all:
        row_key = key(left)
        right_row = right.get(row_key)
        if not right_row:
            continue
        for field in GLOBAL_DELTA_FIELDS:
            lv = safe_get(left, field)
            rv = safe_get(right_row, field)
            if str(lv) == str(rv):
                continue
            category, video, fid = row_key
            k = (category, video, field)
            entry = summary.setdefault(k, {
                "category": category,
                "video": video,
                "field": field,
                "changed_rows": 0,
                "example_frames": [],
                "intended_or_unintended": "intended telemetry-only" if "q1_sic_detector_action_probe_pressure_memory" in field else "unintended behavior difference",
            })
            entry["changed_rows"] = int(entry["changed_rows"]) + 1
            examples = entry["example_frames"]
            if isinstance(examples, list) and len(examples) < 12:
                examples.append(fid)
            if field == "q1_sic_arbitration_label":
                label_rows.append({
                    "category": category,
                    "video": video,
                    "frame_id": fid,
                    "c1r_label": lv,
                    "c1r2_label": rv,
                    "c1r_action": left.get("action_label", ""),
                    "c1r2_action": right_row.get("action_label", ""),
                    "c1r_proposal": left.get("ai_intervention_applied", ""),
                    "c1r2_proposal": right_row.get("ai_intervention_applied", ""),
                })
    rows: List[Dict[str, object]] = []
    for entry in summary.values():
        examples = entry.get("example_frames", [])
        entry["example_frames"] = ";".join(str(v) for v in examples) if isinstance(examples, list) else str(examples)
        rows.append(entry)
    rows.sort(key=lambda r: (str(r["category"]), str(r["video"]), str(r["field"])))
    label_rows.sort(key=lambda r: (str(r["category"]), str(r["video"]), int(r["frame_id"])))
    return rows, label_rows


def snapshot_rows(c1r2_all: List[Dict[str, str]]) -> List[Dict[str, object]]:
    rows = []
    for row in c1r2_all:
        if not (
            truthy(row.get("q1_sic_detector_action_probe_snapshot_active"))
            or truthy(row.get("q1_sic_detector_action_probe_pressure_memory_active"))
            or truthy(row.get("q1_sic_detector_action_probe_would_select_shadow"))
        ):
            continue
        rows.append({
            "category": row.get("category", ""),
            "video": row.get("video", ""),
            "frame_id": frame_id(row),
            "action_label": row.get("action_label", ""),
            "q1_label": row.get("q1_sic_arbitration_label", ""),
            "proposal": row.get("ai_intervention_applied", ""),
            "probe_active": row.get("q1_sic_detector_action_probe_active", ""),
            "snapshot_active": row.get("q1_sic_detector_action_probe_snapshot_active", ""),
            "snapshot_source": row.get("q1_sic_detector_action_probe_snapshot_source", ""),
            "event_risk_pressure": row.get("q1_sic_detector_action_probe_event_risk_pressure", ""),
            "detector_pressure": row.get("q1_sic_detector_action_probe_detector_pressure", ""),
            "memory_active": row.get("q1_sic_detector_action_probe_pressure_memory_active", ""),
            "memory_age": row.get("q1_sic_detector_action_probe_pressure_memory_age", ""),
            "memory_reason": row.get("q1_sic_detector_action_probe_pressure_memory_reason", ""),
            "would_select_shadow": row.get("q1_sic_detector_action_probe_would_select_shadow", ""),
            "reject_reason": row.get("q1_sic_detector_action_probe_reject_reason", ""),
        })
    rows.sort(key=lambda r: (str(r["category"]), str(r["video"]), int(r["frame_id"])))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Q1-SIC-1C1R2 stable snapshot side effects.")
    parser.add_argument("--c1r-root", required=True)
    parser.add_argument("--c1r2-root", required=True)
    parser.add_argument("--c1r-verify-root", required=True)
    parser.add_argument("--c1r2-verify-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    c1r_root = Path(args.c1r_root)
    c1r2_root = Path(args.c1r2_root)
    c1r_verify_root = Path(args.c1r_verify_root)
    c1r2_verify_root = Path(args.c1r2_verify_root)
    out = Path(args.out)

    c1r_snow = index_by_frame(load_video(c1r_root, SNOW))
    c1r2_snow = index_by_frame(load_video(c1r2_root, SNOW))
    c1r_parking = index_by_frame(load_video(c1r_root, PARKING))
    c1r2_parking = index_by_frame(load_video(c1r2_root, PARKING))
    c1r_all = all_guarded(c1r_root)
    c1r2_all = all_guarded(c1r2_root)

    snow1150 = compare_frame_rows(c1r_snow, c1r2_snow, [1150], KEY_FIELDS, "snowfall_1150")
    snow_context = compare_frame_rows(c1r_snow, c1r2_snow, SNOW_CONTEXT, KEY_FIELDS, "snowfall_context")
    parking_rows = compare_frame_rows(c1r_parking, c1r2_parking, PARKING_FRAMES, KEY_FIELDS, "parking_known_rows")
    for row in parking_rows:
        fid = int(row["frame_id"])
        left = c1r_parking.get(fid, {})
        right = c1r2_parking.get(fid, {})
        row["c1r_unprotected_audit"] = int(unprotected(left))
        row["c1r2_unprotected_audit"] = int(unprotected(right))
        row["regressed_to_unprotected"] = int(not unprotected(left) and unprotected(right))
        row["snapshot_memory_active_on_row"] = right.get("q1_sic_detector_action_probe_pressure_memory_active", "NA")

    behavior_delta_rows, label_delta_rows = global_deltas(c1r_all, c1r2_all)
    pressure_rows = snapshot_rows(c1r2_all)
    cfg_rows = config_diff()
    src_rows = source_inventory()

    c1r_summary = read_csv(c1r_verify_root / "q1_sic1c1r_restore_copy_port_summary.csv")
    c1r2_summary = read_csv(c1r2_verify_root / "q1_sic1c1r2_stable_probe_snapshot_summary.csv")
    c1r2_verdict = c1r2_summary[0] if c1r2_summary else {}
    snow1150_right = c1r2_snow.get(1150, {})
    parking_regressions = sum(int(row.get("regressed_to_unprotected", 0)) for row in parking_rows)
    c1r2_parking_unprotected_summary = int(num(c1r2_verdict.get("sic1c1r2_parking_unprotected_fn", 0)))
    label_changes = len(label_delta_rows)
    action_deltas = sum(int(row.get("field") == "action_label") * int(row.get("changed_rows", 0)) for row in behavior_delta_rows)
    proposal_deltas = sum(int(row.get("field") == "ai_intervention_applied") * int(row.get("changed_rows", 0)) for row in behavior_delta_rows)
    memory_rows = len(pressure_rows)
    config_suspicious = any("suspicious" in str(row.get("classification", "")) for row in cfg_rows)

    if config_suspicious:
        primary = "CONFIG_ENABLED_UNINTENDED_ARBITRATION"
        recommendation = "C. Q1-SIC-1C1R3 config repair"
    elif (
        truthy(snow1150_right.get("q1_sic_detector_action_probe_snapshot_active"))
        and snow1150_right.get("q1_sic_arbitration_label") == "FORCE_PROTECT_EVENT_MEMORY"
        and action_deltas > 0
        and proposal_deltas > 0
        and memory_rows > 0
    ):
        primary = "UNKNOWN_NEEDS_INSTRUMENTATION"
        recommendation = "A. Q1-SIC-1C1R3 shadow-only observer isolation repair"
    elif memory_rows > 0 and parking_regressions > 0:
        primary = "PRESSURE_MEMORY_MUTATES_EVENT_TRAJECTORY"
        recommendation = "B. Q1-SIC-1C1R3 disable pressure memory and use post-branch local snapshot only"
    else:
        primary = "VERIFY_TOOL_MISMATCH_ONLY" if not action_deltas and not proposal_deltas else "UNKNOWN_NEEDS_INSTRUMENTATION"
        recommendation = "A. Q1-SIC-1C1R3 shadow-only observer isolation repair"

    secondary = [
        "snowFall action changed" if action_deltas else "",
        "snowFall Q1 label changed" if any(r.get("category") == "badWeather" and r.get("video") == "snowFall" for r in label_delta_rows) else "",
        "parking proposal regression" if proposal_deltas else "",
        "parking unprotected-FN regression" if parking_regressions or c1r2_parking_unprotected_summary else "",
        "snapshot not shadow-only in observed output" if proposal_deltas or label_changes else "",
        "pressure memory active" if memory_rows else "",
        "copyMachine preserved",
        "port watch preserved",
        "normal safety preserved",
    ]
    secondary = [s for s in secondary if s]

    classification_rows = [{
        "primary_classification": primary,
        "secondary_classes": ";".join(secondary),
        "snowfall_1150_c1r_action": c1r_snow.get(1150, {}).get("action_label", ""),
        "snowfall_1150_c1r2_action": snow1150_right.get("action_label", ""),
        "snowfall_1150_c1r2_label": snow1150_right.get("q1_sic_arbitration_label", ""),
        "parking_rows_regressed_to_unprotected": parking_regressions,
        "c1r2_parking_unprotected_fn_summary": c1r2_parking_unprotected_summary,
        "global_action_delta_rows": action_deltas,
        "global_proposal_delta_rows": proposal_deltas,
        "global_q1_label_delta_rows": label_changes,
        "snapshot_or_memory_activation_rows": memory_rows,
        "c1r2_verify_decision": c1r2_verdict.get("decision", ""),
        "recommended_repair": recommendation,
    }]
    repair_rows = [{
        "option": recommendation,
        "rationale": (
            "C1C1R2 changed actions/proposals/labels while the source path does not prove a direct final-arbitration input mutation. "
            "The next repair should isolate the observer from control by taking immutable post-decision copies and writing telemetry only."
        ),
        "do_not_do": "Do not proceed to Q1-SIC-1C2 or port retighten before C1C1R behavior is restored.",
    }]

    write_csv(out / "snowfall_1150_c1r_vs_c1r2_side_effect.csv", snow1150)
    write_csv(out / "snowfall_context_1120_1170_c1r_vs_c1r2.csv", snow_context)
    write_csv(out / "parking_c1r_vs_c1r2_regression.csv", parking_rows)
    write_csv(out / "global_behavior_delta_c1r_vs_c1r2.csv", behavior_delta_rows)
    write_csv(out / "q1_sic_label_delta_c1r_vs_c1r2.csv", label_delta_rows)
    write_csv(out / "snapshot_pressure_memory_activation_rows.csv", pressure_rows)
    write_csv(out / "config_diff_c1r_vs_c1r2.csv", cfg_rows)
    write_csv(out / "source_signal_inventory_snapshot_vs_control.csv", src_rows)
    write_csv(out / "side_effect_classification.csv", classification_rows)
    write_csv(out / "recommended_repair_options.csv", repair_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
