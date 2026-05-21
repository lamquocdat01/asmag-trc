"""Audit Q1-SIC-1B runtime integration and config/base inheritance.

Analysis-only. Reads existing Q1-SIC-1/Q1-SIC-1B/Step4D6 artifacts and writes
CSV diagnostics under the requested Q1-SIC-1C audit output directory.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import yaml


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
SNOW_VIDEO = ("badWeather", "snowFall")
PARKING_VIDEO = ("intermittentObjectMotion", "parking")
COPY_VIDEO = ("shadow", "copyMachine")
PORT_VIDEO = ("lowFramerate", "port_0_17fps")

SNOW_FRAMES = [1120, 1125, 1130, 1135, 1140, 1145, 1150, 1155, 1160, 1165, 1170]
PARKING_FRAMES = [1195, 1310, 1315, 1320, 1425, 1430, 1435, 1440, 1445]
PORT_FRAMES = [1350, 1355]

BASE_COLUMNS = [
    "frame_id",
    "raw_frame_id",
    "Event_State",
    "frame_state",
    "action_label",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "ai_intervention_applied",
    "ai_intervention_detector_requested",
    "active_event_memory",
    "ai_intervention_risk_high",
    "ai_intervention_guard_active",
    "ai_detector_needed_pred",
    "ai_detector_request_blocked_no_refresh_model",
    "forced_refresh_cooldown_active",
    "frames_since_active_prediction",
    "pred_object_count",
    "candidate_ACC_area",
    "candidate_P3_area",
    "candidate_FAST_area",
    "event_fn",
    "protected_fn",
    "unprotected_fn",
    "q1_sic_final_arbitration_enabled",
    "q1_sic_shadow_only",
    "q1_sic_arbitration_active",
    "q1_sic_arbitration_label",
    "q1_sic_arbitration_reason",
    "q1_sic_owner",
    "q1_sic_reference_step",
    "q1_sic_enforcement_class",
    "q1_sic_would_touch_normal_frame",
    "q1_sic_watch_only",
    "q1_sic_invariants_triggered",
    "q1_sic_pre_action",
    "q1_sic_post_action",
    "q1_sic_pre_detector_request",
    "q1_sic_post_detector_request",
    "q1_sic_pre_protection_label",
    "q1_sic_post_protection_label",
    "q1_sic_event_risk_empty_detect_proxy",
    "q1_sic_runtime_detector_empty_proxy",
    "q1_sic_runtime_proposal_absent_proxy",
    "q1_sic_runtime_detector_pressure_proxy",
    "q1_sic_runtime_proxy_inputs",
    "q1_sic_proxy_runtime_safe",
    "q1_sic_gt_signal_used_for_decision",
    "q1_sic_empty_detect_proxy_reject_reason",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
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


def number(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def frame_id(row: Dict[str, str]) -> int:
    for key in ("frame_id", "frame", "raw_frame_id", "frame_idx"):
        if row.get(key) not in (None, ""):
            return int(float(row[key]))
    return -1


def guarded_path(root: Path, video: Sequence[str]) -> Path:
    return root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv"


def load_video(root: Path, video: Sequence[str]) -> List[Dict[str, str]]:
    return read_csv(guarded_path(root, video))


def by_frame(rows: Iterable[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    return {frame_id(row): row for row in rows}


def value(row: Dict[str, str], col: str) -> str:
    return row.get(col, "NA") if row else "NA"


def diff_rows(
    label_a: str,
    rows_a: List[Dict[str, str]],
    label_b: str,
    rows_b: List[Dict[str, str]],
    frames: Sequence[int],
    category: str,
    video: str,
    columns: Sequence[str] = BASE_COLUMNS,
) -> List[Dict[str, object]]:
    a = by_frame(rows_a)
    b = by_frame(rows_b)
    out: List[Dict[str, object]] = []
    for frame in frames:
        row_a = a.get(frame, {})
        row_b = b.get(frame, {})
        item: Dict[str, object] = {"category": category, "video": video, "frame_id": frame}
        for col in columns:
            item[f"{label_a}_{col}"] = value(row_a, col)
            item[f"{label_b}_{col}"] = value(row_b, col)
        changed = [
            col for col in columns
            if value(row_a, col) != value(row_b, col)
        ]
        item["changed_columns"] = ";".join(changed)
        item["changed_column_count"] = len(changed)
        out.append(item)
    return out


def interesting_copy_rows(rows_a: List[Dict[str, str]], rows_b: List[Dict[str, str]]) -> List[int]:
    frames = set()
    for row in list(rows_a) + list(rows_b):
        state = str(row.get("Event_State") or row.get("frame_state") or "")
        if state == "FN":
            frames.add(frame_id(row))
        if truthy(row.get("event_fn")) or truthy(row.get("protected_fn")) or truthy(row.get("unprotected_fn")):
            frames.add(frame_id(row))
        if truthy(row.get("q1_sic_arbitration_active")):
            frames.add(frame_id(row))
        if str(row.get("q1_sic_arbitration_label", "")) not in {"", "NO_CHANGE", "NA"}:
            frames.add(frame_id(row))
        if str(row.get("q1_sic_pre_protection_label", "")) in {"protected_event_fn", "unprotected_fn"}:
            frames.add(frame_id(row))
        if str(row.get("q1_sic_post_protection_label", "")) in {"protected_event_fn", "unprotected_fn"}:
            frames.add(frame_id(row))
    return sorted(frame for frame in frames if frame >= 0)


def flatten(prefix: str, obj: object, out: Dict[str, object]) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            flatten(next_prefix, val, out)
    else:
        out[prefix] = obj


def deep_update(base: Dict[str, object], override: Dict[str, object]) -> Dict[str, object]:
    merged = dict(base)
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_update(merged[key], val)  # type: ignore[arg-type]
        else:
            merged[key] = val
    return merged


def load_yaml(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_yaml_with_base(path: Path) -> Dict[str, object]:
    cfg = load_yaml(path)
    base_ref = cfg.pop("base_config", cfg.pop("_base_config", ""))
    if base_ref:
        base_path = Path(str(base_ref))
        if not base_path.is_absolute():
            base_path = path.parent / base_path
        cfg = deep_update(load_yaml_with_base(base_path), cfg)
    return cfg


def classify_config_diff(key: str, val_a: object, val_b: object) -> str:
    if key == "experiment_name" or key == "edge_profile.name":
        return "harmless output-root change"
    if key == "base_config":
        return "suspicious changed branch/base behavior"
    if key.startswith("online_controller_guarded.q1_sic_event_risk_empty_detect_proxy_enabled"):
        return "intended Q1-SIC-1B addition"
    if key.startswith("online_controller_guarded.q1_sic_forbid_gt_decision_signals"):
        return "intended Q1-SIC-1B addition"
    if "parking" in key.lower() or "copymachine" in key.lower() or "carry" in key.lower() or "rescue" in key.lower():
        return "suspicious changed parking/copyMachine/carry-over flag"
    if key.startswith("online_controller_guarded.q1_sic") or "event" in key.lower() or "guard" in key.lower():
        return "suspicious missing inherited event-safety flag"
    if val_a == val_b:
        return "unchanged"
    return "unknown"


def config_diff() -> List[Dict[str, object]]:
    sic1_path = Path("configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1_event_safety_subset_dryrun.yaml")
    sic1b_path = Path("configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1b_event_safety_subset_dryrun.yaml")
    rows = []
    for scope, loader in [("raw_yaml", load_yaml), ("effective_recursive", load_yaml_with_base)]:
        left: Dict[str, object] = {}
        right: Dict[str, object] = {}
        flatten("", loader(sic1_path), left)
        flatten("", loader(sic1b_path), right)
        for key in sorted(set(left) | set(right)):
            val_a = left.get(key, "MISSING")
            val_b = right.get(key, "MISSING")
            if val_a != val_b:
                rows.append({
                    "comparison_scope": scope,
                    "config_key": key,
                    "sic1_value": val_a,
                    "sic1b_value": val_b,
                    "classification": classify_config_diff(key, val_a, val_b),
                })
    return rows


def collect_missing(root_name: str, path: Path, rows: List[Dict[str, str]], required: Sequence[str]) -> List[Dict[str, object]]:
    present = set(rows[0].keys()) if rows else set()
    return [
        {
            "root": root_name,
            "path": str(path),
            "missing_column": col,
            "row_count": len(rows),
        }
        for col in required
        if col not in present
    ]


def protection(row: Dict[str, str]) -> str:
    if truthy(row.get("unprotected_fn")) or row.get("q1_sic_post_protection_label") == "unprotected_fn":
        return "unprotected"
    if truthy(row.get("protected_fn")) or row.get("q1_sic_post_protection_label") == "protected_event_fn":
        return "protected"
    if str(row.get("Event_State") or row.get("frame_state") or "") == "FN":
        if truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested")):
            return "protected"
        return "unprotected"
    return ""


def snow_1150_audit(sic1_row: Dict[str, str], sic1b_row: Dict[str, str], verifier_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    verifier_summary = verifier_rows[0] if verifier_rows else {}
    q1_fields = [
        "q1_sic_final_arbitration_enabled",
        "q1_sic_shadow_only",
        "q1_sic_arbitration_active",
        "q1_sic_arbitration_label",
        "q1_sic_arbitration_reason",
        "q1_sic_owner",
        "q1_sic_reference_step",
        "q1_sic_watch_only",
        "q1_sic_event_risk_empty_detect_proxy",
        "q1_sic_runtime_detector_empty_proxy",
        "q1_sic_runtime_proposal_absent_proxy",
        "q1_sic_runtime_detector_pressure_proxy",
        "q1_sic_runtime_proxy_inputs",
        "q1_sic_proxy_runtime_safe",
        "q1_sic_empty_detect_proxy_reject_reason",
    ]
    rows = []
    for field in q1_fields:
        rows.append({
            "check": field,
            "sic1_value": value(sic1_row, field),
            "sic1b_value": value(sic1b_row, field),
            "verifier_value": value(verifier_summary, "snowfall_1150_selected") if field == "q1_sic_event_risk_empty_detect_proxy" else "",
            "classification": classify_snow_field(field, sic1b_row),
        })
    rows.extend([
        {
            "check": "config_proxy_enabled_text",
            "sic1_value": "absent/default",
            "sic1b_value": "true in config file",
            "verifier_value": "",
            "classification": "config enabled by text",
        },
        {
            "check": "runtime_selected_by_shadow_verifier",
            "sic1_value": "",
            "sic1b_value": "",
            "verifier_value": value(verifier_summary, "snowfall_1150_selected"),
            "classification": "pre-run verifier selected frame 1150" if value(verifier_summary, "snowfall_1150_selected") == "1" else "pre-run verifier did not select",
        },
    ])
    return rows


def classify_snow_field(field: str, row: Dict[str, str]) -> str:
    if field == "q1_sic_final_arbitration_enabled":
        return "runtime flag enabled" if truthy(row.get(field)) else "runtime flag disabled or missing"
    if field == "q1_sic_arbitration_label":
        return "runtime remained NO_CHANGE" if row.get(field) == "NO_CHANGE" else "runtime arbitration changed"
    if field.startswith("q1_sic_runtime_") or field == "q1_sic_event_risk_empty_detect_proxy":
        return "proxy telemetry default/empty" if not truthy(row.get(field)) else "proxy telemetry active"
    if field == "q1_sic_empty_detect_proxy_reject_reason":
        return "reject reason missing/blank" if row.get(field, "") == "" else "reject reason persisted"
    return "observed"


def telemetry_persistence_summary(
    sic1_rows: Dict[str, List[Dict[str, str]]],
    sic1b_rows: Dict[str, List[Dict[str, str]]],
) -> List[Dict[str, object]]:
    rows = []
    for video_key in sorted(sic1b_rows):
        current = sic1b_rows[video_key]
        previous = sic1_rows.get(video_key, [])
        rows.append({
            "video": video_key,
            "sic1_rows": len(previous),
            "sic1b_rows": len(current),
            "sic1_q1_active": sum(int(truthy(r.get("q1_sic_arbitration_active"))) for r in previous),
            "sic1b_q1_active": sum(int(truthy(r.get("q1_sic_arbitration_active"))) for r in current),
            "sic1b_proxy_active": sum(int(truthy(r.get("q1_sic_event_risk_empty_detect_proxy"))) for r in current),
            "sic1b_proxy_inputs_nonblank": sum(int(bool(str(r.get("q1_sic_runtime_proxy_inputs", "")).strip())) for r in current),
            "sic1b_proxy_reject_nonblank": sum(int(bool(str(r.get("q1_sic_empty_detect_proxy_reject_reason", "")).strip())) for r in current),
            "sic1b_gt_signal_max": max([number(r.get("q1_sic_gt_signal_used_for_decision")) for r in current] or [0]),
            "sic1b_normal_touch_max": max([number(r.get("q1_sic_would_touch_normal_frame")) for r in current] or [0]),
            "sic1b_unprotected_fn": sum(int(protection(r) == "unprotected") for r in current),
            "sic1b_protected_fn": sum(int(protection(r) == "protected") for r in current),
            "classification": classify_telemetry(video_key, current),
        })
    return rows


def classify_telemetry(video_key: str, rows: List[Dict[str, str]]) -> str:
    if video_key == "badWeather/snowFall":
        row = by_frame(rows).get(1150, {})
        if row.get("q1_sic_arbitration_label") == "NO_CHANGE" and not truthy(row.get("q1_sic_runtime_detector_pressure_proxy")):
            return "snowFall proxy integration telemetry absent on detector-action row"
    if video_key == "lowFramerate/port_0_17fps":
        port = by_frame(rows)
        if any(port.get(f, {}).get("q1_sic_arbitration_label") != "WATCH_ONLY_PORT_RETIGHTEN" for f in PORT_FRAMES):
            return "port watch-only telemetry not preserved"
    if video_key == "intermittentObjectMotion/parking":
        if sum(int(protection(r) == "unprotected") for r in rows) > 0:
            return "parking trajectory/protection regression"
    if video_key == "shadow/copyMachine":
        if sum(int(protection(r) == "unprotected") for r in rows) > 0:
            return "copyMachine unexpected unprotected FN drift"
    return "no telemetry persistence issue detected in audit scope"


def failure_classification(
    config_rows: List[Dict[str, object]],
    snow_row: Dict[str, str],
    parking_rows: List[Dict[str, str]],
    copy_rows: List[Dict[str, str]],
    port_rows: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    raw_base_changed = any(
        row.get("comparison_scope") == "raw_yaml" and row["config_key"] == "base_config"
        for row in config_rows
    )
    effective_base_changed = any(
        row.get("comparison_scope") == "effective_recursive" and row["classification"] == "suspicious changed branch/base behavior"
        for row in config_rows
    )
    snow_default = (
        snow_row.get("q1_sic_arbitration_label") == "NO_CHANGE"
        and not truthy(snow_row.get("q1_sic_runtime_detector_pressure_proxy"))
        and not truthy(snow_row.get("q1_sic_event_risk_empty_detect_proxy"))
    )
    parking_unprotected = sum(int(protection(row) == "unprotected") for row in parking_rows)
    copy_unprotected = sum(int(protection(row) == "unprotected") for row in copy_rows)
    port_map = by_frame(port_rows)
    port_watch_bad = any(
        port_map.get(frame, {}).get("q1_sic_arbitration_label") != "WATCH_ONLY_PORT_RETIGHTEN"
        or not truthy(port_map.get(frame, {}).get("q1_sic_watch_only"))
        for frame in PORT_FRAMES
    )
    if effective_base_changed and (parking_unprotected or copy_unprotected or port_watch_bad):
        primary = "CONFIG_BASE_INHERITANCE_MISMATCH"
        recommendation = "Q1-SIC-1C1 config/base repair only or revert to Q1-SIC-1 as last stable event-safety base before touching snowFall logic"
    elif parking_unprotected or copy_unprotected or port_watch_bad:
        primary = "STEP4D6_TRAJECTORY_NOT_PRESERVED"
        recommendation = "Revert Q1-SIC-1B and return to Q1-SIC-1 as last stable event-safety base before touching snowFall logic"
    elif snow_default:
        primary = "ARBITRATION_CALLSITE_NOT_REACHED"
        recommendation = "Q1-SIC-1C1 callsite/telemetry persistence repair"
    else:
        primary = "UNKNOWN_NEEDS_CODE_INSTRUMENTATION"
        recommendation = "Add read-only instrumentation or telemetry audit before another dry-run"
    secondary = []
    if snow_default:
        secondary.append("snowFall proxy integration failure")
    if parking_unprotected:
        secondary.append("parking regression")
    if copy_unprotected:
        secondary.append("copyMachine regression")
    if port_watch_bad:
        secondary.append("split-branch watch telemetry regression")
    if raw_base_changed:
        secondary.append("raw wrapper base_config changed")
    if effective_base_changed:
        secondary.append("effective branch/base behavior changed")
    return [{
        "primary_class": primary,
        "secondary_classes": ";".join(secondary),
        "snowfall_1150_proxy_default": int(snow_default),
        "parking_unprotected_rows": parking_unprotected,
        "copyMachine_unprotected_rows": copy_unprotected,
        "port_watch_telemetry_bad": int(port_watch_bad),
        "raw_base_config_changed": int(raw_base_changed),
        "effective_base_config_changed": int(effective_base_changed),
        "recommended_action": recommendation,
    }]


def output_fields(rows: List[Dict[str, object]]) -> List[str]:
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    return fields or ["empty"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Q1-SIC-1C integration/base mismatch.")
    parser.add_argument("--sic1-root", required=True)
    parser.add_argument("--sic1b-root", required=True)
    parser.add_argument("--sic1b-verify-root", required=True)
    parser.add_argument("--sic1a-root", required=True)
    parser.add_argument("--step4d6-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sic1_root = Path(args.sic1_root)
    sic1b_root = Path(args.sic1b_root)
    verify_root = Path(args.sic1b_verify_root)
    step4d6_root = Path(args.step4d6_root)
    out = Path(args.out)

    sic1_snow = load_video(sic1_root, SNOW_VIDEO)
    sic1b_snow = load_video(sic1b_root, SNOW_VIDEO)
    sic1_parking = load_video(sic1_root, PARKING_VIDEO)
    sic1b_parking = load_video(sic1b_root, PARKING_VIDEO)
    step4d6_parking = load_video(step4d6_root, PARKING_VIDEO)
    sic1_copy = load_video(sic1_root, COPY_VIDEO)
    sic1b_copy = load_video(sic1b_root, COPY_VIDEO)
    sic1_port = load_video(sic1_root, PORT_VIDEO)
    sic1b_port = load_video(sic1b_root, PORT_VIDEO)
    verifier_summary = read_csv(verify_root / "q1_sic1b_proxy_summary.csv")

    config_rows = config_diff()
    snow1150 = snow_1150_audit(
        by_frame(sic1_snow).get(1150, {}),
        by_frame(sic1b_snow).get(1150, {}),
        verifier_summary,
    )
    snow_diff = diff_rows("sic1", sic1_snow, "sic1b", sic1b_snow, SNOW_FRAMES, *SNOW_VIDEO)
    parking_diff = diff_rows("sic1", sic1_parking, "sic1b", sic1b_parking, PARKING_FRAMES, *PARKING_VIDEO)
    step4d6_parking_diff = diff_rows("step4d6", step4d6_parking, "sic1b", sic1b_parking, PARKING_FRAMES, *PARKING_VIDEO)
    copy_frames = interesting_copy_rows(sic1_copy, sic1b_copy)
    copy_diff = diff_rows("sic1", sic1_copy, "sic1b", sic1b_copy, copy_frames, *COPY_VIDEO)
    port_diff = diff_rows("sic1", sic1_port, "sic1b", sic1b_port, PORT_FRAMES, *PORT_VIDEO)
    telemetry = telemetry_persistence_summary(
        {
            "badWeather/snowFall": sic1_snow,
            "intermittentObjectMotion/parking": sic1_parking,
            "shadow/copyMachine": sic1_copy,
            "lowFramerate/port_0_17fps": sic1_port,
        },
        {
            "badWeather/snowFall": sic1b_snow,
            "intermittentObjectMotion/parking": sic1b_parking,
            "shadow/copyMachine": sic1b_copy,
            "lowFramerate/port_0_17fps": sic1b_port,
        },
    )
    missing: List[Dict[str, object]] = []
    for name, root, video, rows in [
        ("sic1_snow", sic1_root, SNOW_VIDEO, sic1_snow),
        ("sic1b_snow", sic1b_root, SNOW_VIDEO, sic1b_snow),
        ("sic1_parking", sic1_root, PARKING_VIDEO, sic1_parking),
        ("sic1b_parking", sic1b_root, PARKING_VIDEO, sic1b_parking),
        ("step4d6_parking", step4d6_root, PARKING_VIDEO, step4d6_parking),
        ("sic1_copyMachine", sic1_root, COPY_VIDEO, sic1_copy),
        ("sic1b_copyMachine", sic1b_root, COPY_VIDEO, sic1b_copy),
        ("sic1_port", sic1_root, PORT_VIDEO, sic1_port),
        ("sic1b_port", sic1b_root, PORT_VIDEO, sic1b_port),
    ]:
        missing.extend(collect_missing(name, guarded_path(root, video), rows, BASE_COLUMNS))

    classification = failure_classification(
        config_rows,
        by_frame(sic1b_snow).get(1150, {}),
        sic1b_parking,
        sic1b_copy,
        sic1b_port,
    )

    write_csv(out / "q1_sic1c_snowfall_1150_integration_audit.csv", snow1150, output_fields(snow1150))
    write_csv(out / "q1_sic1c_snowfall_context_diff_sic1_vs_sic1b.csv", snow_diff, output_fields(snow_diff))
    write_csv(out / "q1_sic1c_parking_diff_sic1_vs_sic1b.csv", parking_diff, output_fields(parking_diff))
    write_csv(out / "q1_sic1c_copyMachine_diff_sic1_vs_sic1b.csv", copy_diff, output_fields(copy_diff))
    write_csv(out / "q1_sic1c_port_watch_diff_sic1_vs_sic1b.csv", port_diff, output_fields(port_diff))
    write_csv(out / "q1_sic1c_step4d6_vs_sic1b_parking_diff.csv", step4d6_parking_diff, output_fields(step4d6_parking_diff))
    write_csv(out / "q1_sic1c_config_diff_summary.csv", config_rows, output_fields(config_rows))
    write_csv(out / "q1_sic1c_telemetry_persistence_summary.csv", telemetry, output_fields(telemetry))
    write_csv(out / "q1_sic1c_missing_columns_summary.csv", missing, output_fields(missing))
    write_csv(out / "q1_sic1c_failure_classification.csv", classification, output_fields(classification))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
