"""Audit Q1-SIC-1C1R snowFall detector-action probe input regression.

Analysis-only: reads existing docs/code/configs/outputs and writes only to the
requested audit output directory.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
SNOW = ("badWeather", "snowFall")
CONTEXT_FRAMES = [1120, 1125, 1130, 1135, 1140, 1145, 1150, 1155, 1160, 1165, 1170]
FOCUS_FRAME = 1150

ROW_COLUMNS = [
    "category",
    "video",
    "pipeline",
    "frame_id",
    "raw_frame_id",
    "evaluated_index",
    "Event_State",
    "action_label",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "yolo_called",
    "ai_intervention_detector_requested",
    "ai_intervention_applied",
    "active_event_memory",
    "ai_intervention_risk_high",
    "ai_intervention_guard_active",
    "ai_detector_needed_pred",
    "ai_detector_request_blocked_no_refresh_model",
    "forced_refresh_cooldown_active",
    "pred_object_count",
    "candidate_ACC_area",
    "candidate_P3_area",
    "candidate_FAST_area",
    "q1_sic_detector_action_probe_active",
    "q1_sic_detector_action_probe_event_risk_pressure",
    "q1_sic_detector_action_probe_detector_pressure",
    "q1_sic_detector_action_probe_detector_blocked",
    "q1_sic_detector_action_probe_cooldown_active",
    "q1_sic_detector_action_probe_proposal_absent",
    "q1_sic_detector_action_probe_runtime_empty_proxy",
    "q1_sic_detector_action_probe_would_select_shadow",
    "q1_sic_detector_action_probe_gt_signal_used",
    "q1_sic_detector_action_probe_would_touch_normal_frame",
    "q1_sic_detector_action_probe_reject_reason",
    "q1_sic_arbitration_label",
    "q1_sic_pre_action",
    "q1_sic_post_action",
    "q1_sic_pre_protection_label",
    "q1_sic_post_protection_label",
]

PROBE_INPUTS = [
    "active_event_memory",
    "ai_intervention_risk_high",
    "ai_intervention_guard_active",
    "ai_detector_needed_pred",
    "ai_detector_request_blocked_no_refresh_model",
    "forced_refresh_cooldown_active",
    "pred_object_count",
    "candidate_ACC_area",
    "candidate_P3_area",
    "candidate_FAST_area",
    "q1_sic_detector_action_probe_event_risk_pressure",
    "q1_sic_detector_action_probe_detector_pressure",
    "q1_sic_detector_action_probe_detector_blocked",
    "q1_sic_detector_action_probe_cooldown_active",
    "q1_sic_detector_action_probe_proposal_absent",
    "q1_sic_detector_action_probe_runtime_empty_proxy",
    "q1_sic_detector_action_probe_would_select_shadow",
    "q1_sic_detector_action_probe_reject_reason",
]

SOURCE_SIGNALS = [
    "ai_intervention_risk_high",
    "ai_detector_needed_pred",
    "ai_detector_request_blocked_no_refresh_model",
    "forced_refresh_cooldown_active",
    "q1_sic_detector_action_probe",
    "q1_sic1c1r_restore_copymachine",
    "q1_sic1c1r_restore_port_watch",
    "_apply_q1_sic_detector_action_probe",
    "_apply_q1_sic1c1r_restore_copy_port",
    "final_safety_arbitration",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fields:
        keys = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fields = keys
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def frame_value(row: Dict[str, str]) -> int:
    for key in ("frame_id", "frame", "raw_frame_id", "frame_idx"):
        value = row.get(key)
        if value not in (None, ""):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                pass
    return -1


def guarded_path(root: Path, video: Sequence[str]) -> Path:
    return root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv"


def load_snow(root: Path) -> List[Dict[str, str]]:
    return read_csv(guarded_path(root, SNOW))


def by_frame(rows: Iterable[Dict[str, str]]) -> Dict[int, List[Dict[str, str]]]:
    out: Dict[int, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[frame_value(row)].append(row)
    return out


def first_frame(rows_by_frame: Dict[int, List[Dict[str, str]]], frame_id: int) -> Dict[str, str]:
    rows = rows_by_frame.get(frame_id, [])
    return rows[-1] if rows else {}


def slim_row(label: str, row: Dict[str, str]) -> Dict[str, object]:
    out: Dict[str, object] = {"run": label}
    for col in ROW_COLUMNS:
        out[col] = row.get(col, "NA")
    return out


def numish(value: object) -> str:
    if value in (None, ""):
        return ""
    text = str(value)
    try:
        return str(float(text))
    except (TypeError, ValueError):
        return text


def changed(a: object, b: object) -> bool:
    return numish(a) != numish(b)


def flatten_yaml_like(path: Path) -> Dict[str, str]:
    try:
        import yaml
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception:
        data = {}
    flat: Dict[str, str] = {}

    def walk(prefix: str, value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(f"{prefix}.{key}" if prefix else str(key), child)
        elif isinstance(value, list):
            flat[prefix] = ",".join(str(item) for item in value)
        else:
            flat[prefix] = "" if value is None else str(value)

    walk("", data)
    return flat


def classify_config_key(key: str, c1: str, c1r: str) -> str:
    intended = {
        "experiment_name",
        "edge_profile.name",
        "online_controller_guarded.q1_sic1c1r_restore_copymachine_enabled",
        "online_controller_guarded.q1_sic1c1r_restore_copymachine_frames",
        "online_controller_guarded.q1_sic1c1r_restore_port_watch_enabled",
    }
    if key in intended:
        return "intended_c1c1r_addition_or_name_change"
    if key == "base_config":
        return "expected_c1c1_base"
    suspicious_tokens = [
        "snow",
        "carry",
        "risk",
        "detector",
        "cooldown",
        "probe",
        "event",
        "resume",
        "checkpoint",
        "max_frame",
        "frame",
    ]
    if any(token in key.lower() for token in suspicious_tokens):
        return "suspicious_pressure_related_change"
    return "unknown_or_harmless"


def config_diff(c1_path: Path, c1r_path: Path) -> List[Dict[str, object]]:
    c1 = flatten_yaml_like(c1_path)
    c1r = flatten_yaml_like(c1r_path)
    rows = []
    for key in sorted(set(c1) | set(c1r)):
        left = c1.get(key, "<MISSING>")
        right = c1r.get(key, "<MISSING>")
        if left == right:
            continue
        rows.append({
            "key": key,
            "q1_sic1c1": left,
            "q1_sic1c1r": right,
            "classification": classify_config_key(key, left, right),
        })
    return rows


def source_inventory(source_path: Path) -> List[Dict[str, object]]:
    lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    for line_no, line in enumerate(lines, start=1):
        for signal in SOURCE_SIGNALS:
            if signal in line:
                rows.append({
                    "signal": signal,
                    "line": line_no,
                    "source_excerpt": line.strip()[:240],
                })
    return rows


def duplicate_check(root: Path) -> List[Dict[str, object]]:
    rows = []
    for path in sorted(root.glob(f"raw_results/*/*/{PIPELINE}/frame_metrics.csv")):
        data = read_csv(path)
        frames = [frame_value(row) for row in data]
        counts = Counter(frames)
        duplicates = {frame: count for frame, count in counts.items() if frame >= 0 and count > 1}
        rows.append({
            "root": str(root),
            "relative_path": str(path.relative_to(root)),
            "rows": len(data),
            "unique_frames": len(counts),
            "duplicate_frame_count": len(duplicates),
            "duplicate_frames": ";".join(f"{frame}:{count}" for frame, count in sorted(duplicates.items())[:20]),
            "snowfall_guarded": int(path == guarded_path(root, SNOW)),
        })
    return rows


def mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        return ""


def resume_stale_check(root: Path) -> List[Dict[str, object]]:
    patterns = [
        "run_progress.csv",
        "progress.csv",
        "*progress*.csv",
        "*progress*.json",
        "*.lock",
        "*.tmp",
        "raw_results/badWeather/snowFall/ASMAG_TR_CONTROLLER_ONLINE_GUARDED/frame_metrics.csv",
        "ai_intervention_video_summary.csv",
        "asmag_tr_final_comparison.csv",
    ]
    seen = set()
    rows = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if path in seen:
                continue
            seen.add(path)
            rows.append({
                "relative_path": str(path.relative_to(root)),
                "exists": int(path.exists()),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "modified_time": mtime_iso(path),
                "row_count": len(read_csv(path)) if path.suffix.lower() == ".csv" else "",
            })
    progress_paths = sorted(root.glob("**/*progress*.csv"))
    for path in progress_paths:
        if path in seen:
            continue
        seen.add(path)
        rows.append({
            "relative_path": str(path.relative_to(root)),
            "exists": int(path.exists()),
            "size_bytes": path.stat().st_size,
            "modified_time": mtime_iso(path),
            "row_count": len(read_csv(path)),
        })
    return rows


def context_rows(c1_by: Dict[int, List[Dict[str, str]]], c1r_by: Dict[int, List[Dict[str, str]]]) -> List[Dict[str, object]]:
    rows = []
    for frame_id in CONTEXT_FRAMES:
        c1 = first_frame(c1_by, frame_id)
        c1r = first_frame(c1r_by, frame_id)
        pressure_changed = any(changed(c1.get(col), c1r.get(col)) for col in [
            "ai_intervention_risk_high",
            "ai_detector_needed_pred",
            "ai_detector_request_blocked_no_refresh_model",
            "forced_refresh_cooldown_active",
            "q1_sic_detector_action_probe_would_select_shadow",
        ])
        rows.append({
            "frame_id": frame_id,
            "c1_action": c1.get("action_label", "NA"),
            "c1r_action": c1r.get("action_label", "NA"),
            "c1_active_event_memory": c1.get("active_event_memory", "NA"),
            "c1r_active_event_memory": c1r.get("active_event_memory", "NA"),
            "c1_risk_high": c1.get("ai_intervention_risk_high", "NA"),
            "c1r_risk_high": c1r.get("ai_intervention_risk_high", "NA"),
            "c1_detector_needed": c1.get("ai_detector_needed_pred", "NA"),
            "c1r_detector_needed": c1r.get("ai_detector_needed_pred", "NA"),
            "c1_detector_blocked_no_refresh": c1.get("ai_detector_request_blocked_no_refresh_model", "NA"),
            "c1r_detector_blocked_no_refresh": c1r.get("ai_detector_request_blocked_no_refresh_model", "NA"),
            "c1_cooldown": c1.get("forced_refresh_cooldown_active", "NA"),
            "c1r_cooldown": c1r.get("forced_refresh_cooldown_active", "NA"),
            "c1_probe_would_select": c1.get("q1_sic_detector_action_probe_would_select_shadow", "NA"),
            "c1r_probe_would_select": c1r.get("q1_sic_detector_action_probe_would_select_shadow", "NA"),
            "c1_reject": c1.get("q1_sic_detector_action_probe_reject_reason", "NA"),
            "c1r_reject": c1r.get("q1_sic_detector_action_probe_reject_reason", "NA"),
            "pressure_changed": int(pressure_changed),
            "classification": "focus_frame_regression" if frame_id == FOCUS_FRAME and pressure_changed else (
                "context_pressure_changed" if pressure_changed else "unchanged_or_nonprobe_context"
            ),
        })
    return rows


def build_delta(c1: Dict[str, str], c1r: Dict[str, str]) -> List[Dict[str, object]]:
    rows = []
    for signal in PROBE_INPUTS:
        c1_value = c1.get(signal, "NA")
        c1r_value = c1r.get(signal, "NA")
        is_changed = changed(c1_value, c1r_value)
        if signal in {
            "ai_intervention_risk_high",
            "ai_detector_needed_pred",
            "ai_detector_request_blocked_no_refresh_model",
            "forced_refresh_cooldown_active",
            "q1_sic_detector_action_probe_detector_pressure",
            "q1_sic_detector_action_probe_event_risk_pressure",
            "q1_sic_detector_action_probe_would_select_shadow",
        } and is_changed:
            classification = "pressure_lost"
        elif is_changed:
            classification = "changed"
        else:
            classification = "unchanged"
        rows.append({
            "signal": signal,
            "q1_sic1c1": c1_value,
            "q1_sic1c1r": c1r_value,
            "changed": int(is_changed),
            "classification": classification,
        })
    return rows


def classify(c1: Dict[str, str], c1r: Dict[str, str], context: List[Dict[str, object]], config_rows: List[Dict[str, object]], dup_rows: List[Dict[str, object]]) -> Dict[str, object]:
    pressure_lost = any(
        changed(c1.get(col), c1r.get(col))
        and str(c1.get(col, "")) not in {"", "0", "0.0", "NA"}
        and str(c1r.get(col, "")) in {"", "0", "0.0", "NA"}
        for col in [
            "ai_intervention_risk_high",
            "ai_detector_needed_pred",
            "ai_detector_request_blocked_no_refresh_model",
            "forced_refresh_cooldown_active",
        ]
    )
    suspicious_config = any(row["classification"] == "suspicious_pressure_related_change" for row in config_rows)
    duplicate_snow = any(
        row.get("snowfall_guarded") == 1 and int(row.get("duplicate_frame_count") or 0) > 0
        for row in dup_rows
    )
    context_changed_frames = [
        int(row["frame_id"]) for row in context
        if int(row.get("pressure_changed", 0)) and int(row["frame_id"]) != FOCUS_FRAME
    ]
    if duplicate_snow:
        primary = "VERIFIER_ROW_SELECTION_AMBIGUITY"
    elif suspicious_config:
        primary = "CONFIG_FLAG_DIFF_CHANGED_PRESSURE"
    elif pressure_lost:
        primary = "RUNTIME_PRESSURE_TRAJECTORY_CHANGED"
    else:
        primary = "SOURCE_PATH_UNKNOWN_NEEDS_INSTRUMENTATION"
    secondary = []
    for label, col in [
        ("risk-high lost", "ai_intervention_risk_high"),
        ("detector-needed lost", "ai_detector_needed_pred"),
        ("detector-blocked lost", "ai_detector_request_blocked_no_refresh_model"),
        ("cooldown lost", "forced_refresh_cooldown_active"),
    ]:
        if changed(c1.get(col), c1r.get(col)):
            secondary.append(label)
    if context_changed_frames:
        secondary.append("context trajectory shift")
    if duplicate_snow:
        secondary.append("duplicate row ambiguity")
    return {
        "primary_classification": primary,
        "secondary_classes": "; ".join(secondary),
        "focus_frame_pressure_lost": int(pressure_lost),
        "context_changed_frames": ";".join(str(frame) for frame in context_changed_frames),
        "suspicious_config_change": int(suspicious_config),
        "duplicate_snowfall_guarded_rows": int(duplicate_snow),
    }


def repair_options(primary: str) -> List[Dict[str, object]]:
    options = [
        ("A", "Q1-SIC-1C1R2 stable snapshot repair", "Use if C1C1 has correct pressure but C1C1R reads late/reset values."),
        ("B", "Q1-SIC-1C1R2 restore-shim isolation repair", "Use if copyMachine/port restore shims mutate shared Q1-SIC/probe state."),
        ("C", "Q1-SIC-1C1R2 config repair", "Use if config diff changed pressure-related flags."),
        ("D", "Q1-SIC-1C1R rerun clean output only", "Use if timeout/resume or stale mixed output is likely."),
        ("E", "Instrumentation-only phase", "Use if source path cannot locate before/after pressure loss."),
    ]
    recommended = {
        "RUNTIME_PRESSURE_TRAJECTORY_CHANGED": "A",
        "PROBE_READS_LATE_RESET_VALUES": "A",
        "RESTORE_SHIM_SIDE_EFFECT": "B",
        "CONFIG_FLAG_DIFF_CHANGED_PRESSURE": "C",
        "RESUME_STALE_OUTPUT_MIX": "D",
        "VERIFIER_ROW_SELECTION_AMBIGUITY": "D",
        "TELEMETRY_COLUMN_OVERWRITE": "A",
        "SOURCE_PATH_UNKNOWN_NEEDS_INSTRUMENTATION": "E",
    }.get(primary, "E")
    return [
        {
            "option": code,
            "name": name,
            "description": description,
            "recommended": int(code == recommended),
        }
        for code, name, description in options
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Q1-SIC-1C1R snowFall probe input regression.")
    parser.add_argument("--sic1-root", required=True)
    parser.add_argument("--sic1c1-root", required=True)
    parser.add_argument("--sic1c1r-root", required=True)
    parser.add_argument("--sic1a-root", required=True)
    parser.add_argument("--sic1c1-verify-root", required=True)
    parser.add_argument("--sic1c1r-verify-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sic1_root = Path(args.sic1_root)
    c1_root = Path(args.sic1c1_root)
    c1r_root = Path(args.sic1c1r_root)
    out = Path(args.out)

    sic1_by = by_frame(load_snow(sic1_root))
    c1_by = by_frame(load_snow(c1_root))
    c1r_by = by_frame(load_snow(c1r_root))
    sic1_1150 = first_frame(sic1_by, FOCUS_FRAME)
    c1_1150 = first_frame(c1_by, FOCUS_FRAME)
    c1r_1150 = first_frame(c1r_by, FOCUS_FRAME)

    row_table = [slim_row("Q1-SIC-1", sic1_1150), slim_row("Q1-SIC-1C1", c1_1150), slim_row("Q1-SIC-1C1R", c1r_1150)]
    write_csv(out / "snowfall_1150_sic1_vs_c1_vs_c1r.csv", row_table, list(row_table[0].keys()))

    context = context_rows(c1_by, c1r_by)
    write_csv(out / "snowfall_context_1120_1170_c1_vs_c1r.csv", context, list(context[0].keys()))

    delta = build_delta(c1_1150, c1r_1150)
    write_csv(out / "snowfall_probe_input_delta.csv", delta, list(delta[0].keys()))

    config_rows = config_diff(
        Path("configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1_restore_base_probe_subset_dryrun.yaml"),
        Path("configs/asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml"),
    )
    write_csv(out / "config_diff_c1_vs_c1r.csv", config_rows, ["key", "q1_sic1c1", "q1_sic1c1r", "classification"])

    source_rows = source_inventory(Path("src/run_experiment.py"))
    write_csv(out / "source_signal_name_inventory.csv", source_rows, ["signal", "line", "source_excerpt"])

    dup_rows = duplicate_check(c1r_root)
    write_csv(out / "duplicate_frame_metrics_check.csv", dup_rows, [
        "root", "relative_path", "rows", "unique_frames", "duplicate_frame_count", "duplicate_frames", "snowfall_guarded"
    ])

    stale_rows = resume_stale_check(c1r_root)
    write_csv(out / "resume_stale_output_check.csv", stale_rows, [
        "relative_path", "exists", "size_bytes", "modified_time", "row_count"
    ])

    classification = classify(c1_1150, c1r_1150, context, config_rows, dup_rows)
    write_csv(out / "probe_regression_classification.csv", [classification], list(classification.keys()))

    options = repair_options(str(classification["primary_classification"]))
    write_csv(out / "recommended_repair_options.csv", options, ["option", "name", "description", "recommended"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
