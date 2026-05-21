"""Verify Q1-SIC-1C1R3D paired live-probe / observer purity."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_CONFIG = (
    PROJECT_ROOT
    / "configs"
    / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_live_probe_baseline_subset_dryrun.yaml"
)
OBSERVER_CONFIG = (
    PROJECT_ROOT
    / "configs"
    / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3d_observer_purity_subset_dryrun.yaml"
)

PARKING = ("intermittentObjectMotion", "parking")
COPY = ("shadow", "copyMachine")
PORT = ("lowFramerate", "port_0_17fps")
SNOW = ("badWeather", "snowFall")
COPY_FRAMES = [810, 815, 820, 935, 940, 945]
PORT_FRAMES = [1350, 1355]

BEHAVIOR_COLUMNS = [
    "action_label",
    "selected_mode",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "yolo_called",
    "ai_intervention_detector_requested",
    "ai_intervention_applied",
    "q1_sic_arbitration_active",
    "q1_sic_arbitration_label",
    "q1_sic_owner",
    "q1_sic_watch_only",
]
NUMERIC_BEHAVIOR_COLUMNS = {
    "yolo_called",
    "ai_intervention_detector_requested",
    "ai_intervention_applied",
    "q1_sic_arbitration_active",
    "q1_sic_watch_only",
}
OBSERVER_COLUMNS = [
    "q1_sic_observer_isolated_enabled",
    "q1_sic_observer_post_decision_only",
    "q1_sic_observer_used_immutable_snapshot",
    "q1_sic_observer_mutated_control_state",
    "q1_sic_observer_gt_signal_used",
    "q1_sic_observer_would_touch_normal_frame",
    "q1_sic_observer_action_is_detect",
    "q1_sic_observer_event_risk_pressure",
    "q1_sic_observer_detector_pressure",
    "q1_sic_observer_proposal_absent",
    "q1_sic_observer_runtime_empty_proxy",
    "q1_sic_observer_would_select_shadow",
    "q1_sic_observer_reject_reason",
    "q1_sic_observer_pressure_memory_enabled",
    "q1_sic_observer_pressure_memory_used",
]
LIVE_PROBE_PREFIX = "q1_sic_detector_action_probe_"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str] | None = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fields.append(key)
                    seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_yaml(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    return loaded if isinstance(loaded, dict) else {}


def flatten(value: object, prefix: str = "") -> Dict[str, object]:
    if isinstance(value, dict):
        out: Dict[str, object] = {}
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten(child, child_prefix))
        return out
    return {prefix: value}


def config_diff() -> List[Dict[str, object]]:
    left = flatten(read_yaml(BASELINE_CONFIG))
    right = flatten(read_yaml(OBSERVER_CONFIG))
    rows: List[Dict[str, object]] = []
    for key in sorted(set(left) | set(right)):
        lval = left.get(key, "")
        rval = right.get(key, "")
        if lval == rval:
            continue
        if key in {
            "experiment_name",
            "edge_profile.name",
            "base_config",
        }:
            classification = "intended output/profile identifier"
        elif key == "online_controller_guarded.q1_sic_observer_isolated_enabled":
            classification = "intended observer telemetry flag"
        else:
            classification = "unexpected config difference"
        rows.append({
            "config_key": key,
            "baseline_value": lval,
            "observer_value": rval,
            "classification": classification,
        })
    return rows


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


def normalize(value: object, numeric_hint: bool = False) -> str:
    if value in (None, "NA"):
        return ""
    text = str(value).strip()
    if text == "":
        return ""
    if numeric_hint:
        try:
            numeric = float(text)
        except (TypeError, ValueError):
            return text
        if numeric == int(numeric):
            return str(int(numeric))
        return f"{numeric:.12g}"
    try:
        numeric = float(text)
    except (TypeError, ValueError):
        return text
    if numeric == int(numeric):
        return str(int(numeric))
    return f"{numeric:.12g}"


def frame(row: Dict[str, str]) -> int:
    for key in ("raw_frame_id", "frame_id", "frame", "frame_idx"):
        if row.get(key) not in (None, ""):
            try:
                return int(float(row[key]))
            except (TypeError, ValueError):
                return -1
    return -1


def row_key(row: Dict[str, str]) -> Tuple[str, str, int, str]:
    return (
        row.get("category", ""),
        row.get("video", ""),
        frame(row),
        row.get("pipeline", PIPELINE),
    )


def all_guarded_rows(root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(root.glob(f"raw_results/*/*/{PIPELINE}/frame_metrics.csv")):
        try:
            raw_idx = path.parts.index("raw_results")
            category = path.parts[raw_idx + 1]
            video = path.parts[raw_idx + 2]
        except (ValueError, IndexError):
            category = ""
            video = ""
        for row in read_csv(path):
            row.setdefault("category", category)
            row.setdefault("video", video)
            row.setdefault("pipeline", PIPELINE)
            rows.append(row)
    return rows


def load_video(root: Path, video: Sequence[str]) -> List[Dict[str, str]]:
    return read_csv(root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv")


def by_frame(rows: Iterable[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    return {frame(row): row for row in rows}


def video_summary(root: Path, category: str, video: str) -> Dict[str, str]:
    for row in read_csv(root / "ai_intervention_video_summary.csv"):
        if row.get("category") == category and row.get("video") == video:
            return row
    return {}


def rate(rows: List[Dict[str, str]], column: str) -> float:
    if not rows:
        return 0.0
    return sum(int(truthy(row.get(column))) for row in rows) / float(len(rows))


def is_fn(row: Dict[str, str]) -> bool:
    return str(row.get("Event_State") or row.get("frame_state") or "") == "FN"


def is_normal(row: Dict[str, str]) -> bool:
    state = str(row.get("Event_State") or row.get("frame_state") or "").strip().lower()
    return state in {"tn", "normal", "background"}


def protected(row: Dict[str, str]) -> bool:
    if truthy(row.get("protected_fn")) or row.get("q1_sic_post_protection_label") == "protected_event_fn":
        return True
    return bool(
        is_fn(row)
        and (truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested")))
    )


def unprotected(row: Dict[str, str]) -> bool:
    if not row:
        return False
    if truthy(row.get("unprotected_fn")) or row.get("q1_sic_post_protection_label") == "unprotected_fn":
        return True
    return bool(is_fn(row) and not protected(row))


def normal_intervention(row: Dict[str, str]) -> bool:
    return bool(
        is_normal(row)
        and (truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested")))
    )


def max_col(rows: List[Dict[str, str]], column: str) -> float:
    return max([number(row.get(column)) for row in rows] or [0.0])


def count_duplicates(rows: List[Dict[str, str]]) -> Tuple[int, int]:
    counts = Counter(row_key(row) for row in rows)
    duplicate_counts = [count for count in counts.values() if count > 1]
    return len(duplicate_counts), sum(count - 1 for count in duplicate_counts)


def live_probe_columns(rows_a: List[Dict[str, str]], rows_b: List[Dict[str, str]]) -> List[str]:
    columns = set()
    for row in rows_a + rows_b:
        columns.update(key for key in row if key.startswith(LIVE_PROBE_PREFIX))
    return sorted(columns)


def keyed(rows: List[Dict[str, str]]) -> Dict[Tuple[str, str, int, str], Dict[str, str]]:
    return {row_key(row): row for row in rows}


def compare_behavior(
    baseline_rows: List[Dict[str, str]],
    observer_rows: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    baseline = keyed(baseline_rows)
    observer = keyed(observer_rows)
    deltas: List[Dict[str, object]] = []
    for key in sorted(set(baseline) | set(observer)):
        brow = baseline.get(key, {})
        orow = observer.get(key, {})
        if not brow or not orow:
            deltas.append({
                "category": key[0],
                "video": key[1],
                "frame": key[2],
                "pipeline": key[3],
                "field": "row_presence",
                "baseline": "present" if brow else "missing",
                "observer": "present" if orow else "missing",
            })
            continue
        for column in BEHAVIOR_COLUMNS:
            bval = normalize(brow.get(column, ""), column in NUMERIC_BEHAVIOR_COLUMNS)
            oval = normalize(orow.get(column, ""), column in NUMERIC_BEHAVIOR_COLUMNS)
            if bval != oval:
                deltas.append({
                    "category": key[0],
                    "video": key[1],
                    "frame": key[2],
                    "pipeline": key[3],
                    "field": column,
                    "baseline": brow.get(column, ""),
                    "observer": orow.get(column, ""),
                })
        for field, bval, oval in [
            ("protected_fn_accounting", int(protected(brow)), int(protected(orow))),
            ("unprotected_fn_accounting", int(unprotected(brow)), int(unprotected(orow))),
            ("normal_frame_intervention_indicator", int(normal_intervention(brow)), int(normal_intervention(orow))),
        ]:
            if bval != oval:
                deltas.append({
                    "category": key[0],
                    "video": key[1],
                    "frame": key[2],
                    "pipeline": key[3],
                    "field": field,
                    "baseline": bval,
                    "observer": oval,
                })
    return deltas


def compare_live_probe(
    baseline_rows: List[Dict[str, str]],
    observer_rows: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    baseline = keyed(baseline_rows)
    observer = keyed(observer_rows)
    columns = live_probe_columns(baseline_rows, observer_rows)
    deltas: List[Dict[str, object]] = []
    for key in sorted(set(baseline) | set(observer)):
        brow = baseline.get(key, {})
        orow = observer.get(key, {})
        if not brow or not orow:
            continue
        for column in columns:
            bval = normalize(brow.get(column, ""))
            oval = normalize(orow.get(column, ""))
            if bval != oval:
                deltas.append({
                    "category": key[0],
                    "video": key[1],
                    "frame": key[2],
                    "pipeline": key[3],
                    "field": column,
                    "baseline": brow.get(column, ""),
                    "observer": orow.get(column, ""),
                })
    return deltas


def progress_summary(root: Path) -> Dict[str, object]:
    rows = read_csv(root / "run_progress.csv")
    completed = sum(1 for row in rows if row.get("status") == "completed")
    failed = sum(1 for row in rows if row.get("status") == "failed")
    compare_completed = int((root / "asmag_tr_final_comparison.csv").exists() and (root / "comparison_summary.csv").exists())
    return {
        "jobs_total": len(rows),
        "jobs_completed": completed,
        "jobs_failed": failed,
        "compare_completed": compare_completed,
        "execution_ok": int(len(rows) == 56 and completed == 56 and failed == 0 and compare_completed),
    }


def summarize_deltas(
    behavior_deltas: List[Dict[str, object]],
    live_probe_deltas: List[Dict[str, object]],
    baseline_rows: List[Dict[str, str]],
    observer_rows: List[Dict[str, str]],
) -> Dict[str, object]:
    by_field = Counter(str(row.get("field", "")) for row in behavior_deltas)
    live_by_field = Counter(str(row.get("field", "")) for row in live_probe_deltas)
    baseline_dup_keys, baseline_dup_extra = count_duplicates(baseline_rows)
    observer_dup_keys, observer_dup_extra = count_duplicates(observer_rows)
    baseline_keys = {row_key(row) for row in baseline_rows}
    observer_keys = {row_key(row) for row in observer_rows}
    return {
        "baseline_guarded_rows": len(baseline_rows),
        "observer_guarded_rows": len(observer_rows),
        "row_count_match": int(len(baseline_rows) == len(observer_rows)),
        "overlapping_keys": len(baseline_keys & observer_keys),
        "row_presence_deltas": by_field.get("row_presence", 0),
        "baseline_duplicate_keys": baseline_dup_keys,
        "baseline_duplicate_extra_rows": baseline_dup_extra,
        "observer_duplicate_keys": observer_dup_keys,
        "observer_duplicate_extra_rows": observer_dup_extra,
        "behavior_delta_cells": len(behavior_deltas),
        "behavior_delta_rows": len({(r.get("category"), r.get("video"), r.get("frame"), r.get("pipeline")) for r in behavior_deltas}),
        "action_label_deltas": by_field.get("action_label", 0),
        "proposal_deltas": by_field.get("ai_intervention_applied", 0),
        "detector_request_deltas": by_field.get("ai_intervention_detector_requested", 0),
        "yolo_called_deltas": by_field.get("yolo_called", 0),
        "selected_mode_deltas": by_field.get("selected_mode", 0)
        + by_field.get("selected_mode_before_guard", 0)
        + by_field.get("selected_mode_after_guard", 0),
        "q1_label_deltas": by_field.get("q1_sic_arbitration_label", 0),
        "q1_active_deltas": by_field.get("q1_sic_arbitration_active", 0),
        "q1_owner_deltas": by_field.get("q1_sic_owner", 0),
        "q1_watch_only_deltas": by_field.get("q1_sic_watch_only", 0),
        "protected_accounting_deltas": by_field.get("protected_fn_accounting", 0),
        "unprotected_accounting_deltas": by_field.get("unprotected_fn_accounting", 0),
        "normal_frame_intervention_indicator_deltas": by_field.get("normal_frame_intervention_indicator", 0),
        "live_probe_delta_cells": len(live_probe_deltas),
        "live_probe_delta_rows": len({(r.get("category"), r.get("video"), r.get("frame"), r.get("pipeline")) for r in live_probe_deltas}),
        "live_probe_delta_fields": len(live_by_field),
    }


def local_gates(root: Path) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    rows = all_guarded_rows(root)
    parking = load_video(root, PARKING)
    parking_summary = video_summary(root, *PARKING)
    parking_proposal = number(parking_summary.get("intervention_rate"), rate(parking, "ai_intervention_applied"))
    parking_detector = number(parking_summary.get("detector_request_rate"), rate(parking, "ai_intervention_detector_requested"))
    parking_unprotected = sum(int(unprotected(row)) for row in parking)
    parking_ok = int(parking_unprotected == 0 and parking_detector == 0.0 and parking_proposal <= 0.46001)

    row_checks: List[Dict[str, object]] = []
    copy_rows = by_frame(load_video(root, COPY))
    copy_ok = 1
    for frame_id in COPY_FRAMES:
        row = copy_rows.get(frame_id, {})
        ok = int(protected(row) and not unprotected(row))
        copy_ok = int(copy_ok and ok)
        row_checks.append({
            "check": "copyMachine_protected",
            "category": COPY[0],
            "video": COPY[1],
            "frame": frame_id,
            "action_label": row.get("action_label", ""),
            "q1_sic_arbitration_label": row.get("q1_sic_arbitration_label", ""),
            "ai_intervention_applied": row.get("ai_intervention_applied", ""),
            "protected": int(protected(row)),
            "unprotected": int(unprotected(row)),
            "passed": ok,
        })

    port_rows = by_frame(load_video(root, PORT))
    port_ok = 1
    no_port_enforce_ok = 1
    for frame_id in PORT_FRAMES:
        row = port_rows.get(frame_id, {})
        watch_ok = int(
            row.get("q1_sic_arbitration_label") == "WATCH_ONLY_PORT_RETIGHTEN"
            and truthy(row.get("q1_sic_watch_only"))
            and row.get("q1_sic_owner") == "detector_retighten"
            and row.get("q1_sic_reference_step") == "Step4E4"
        )
        no_enforce = int(
            number(row.get("q1_sic_pre_detector_request")) == number(row.get("q1_sic_post_detector_request"))
            and number(row.get("ai_intervention_detector_requested")) == 0
        )
        port_ok = int(port_ok and watch_ok)
        no_port_enforce_ok = int(no_port_enforce_ok and no_enforce)
        row_checks.append({
            "check": "port_watch_preserved",
            "category": PORT[0],
            "video": PORT[1],
            "frame": frame_id,
            "q1_sic_arbitration_label": row.get("q1_sic_arbitration_label", ""),
            "q1_sic_watch_only": row.get("q1_sic_watch_only", ""),
            "q1_sic_owner": row.get("q1_sic_owner", ""),
            "q1_sic_reference_step": row.get("q1_sic_reference_step", ""),
            "detector_unchanged": no_enforce,
            "passed": int(watch_ok and no_enforce),
        })

    normal_frame_interventions = sum(
        int(number(row.get("normal_frame_intervention_count")) > 0)
        for row in read_csv(root / "ai_intervention_video_summary.csv")
    )
    q1_touch_max = max_col(rows, "q1_sic_would_touch_normal_frame")
    gt_decision_max = max_col(rows, "q1_sic_gt_signal_used_for_decision")
    normal_ok = int(normal_frame_interventions == 0 and q1_touch_max == 0 and gt_decision_max == 0)

    q1b_proxy_rows = sum(int(truthy(row.get("q1_sic_event_risk_empty_detect_proxy"))) for row in rows)
    q1b_label_rows = sum(
        int(row.get("q1_sic_arbitration_label") == "FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION")
        for row in rows
    )
    snow_ok = int(q1b_proxy_rows == 0 and q1b_label_rows == 0)
    local_ok = int(all([parking_ok, copy_ok, port_ok, no_port_enforce_ok, normal_ok, snow_ok]))
    return {
        "parking_preserved_ok": parking_ok,
        "baseline_parking_proposal": f"{parking_proposal:.5f}",
        "baseline_parking_detector": f"{parking_detector:.5f}",
        "baseline_parking_unprotected_fn": parking_unprotected,
        "copyMachine_preserved_ok": copy_ok,
        "port_watch_preserved_ok": port_ok,
        "no_port_retighten_enforcement_ok": no_port_enforce_ok,
        "normal_safety_ok": normal_ok,
        "normal_frame_interventions": normal_frame_interventions,
        "q1_sic_would_touch_normal_frame_max": q1_touch_max,
        "q1_sic_gt_signal_used_for_decision_max": gt_decision_max,
        "no_new_snowfall_enforcement_ok": snow_ok,
        "q1_sic1b_proxy_active_rows": q1b_proxy_rows,
        "q1_sic1b_enforcement_label_rows": q1b_label_rows,
        "baseline_local_gates_ok": local_ok,
    }, row_checks


def observer_summary(baseline_rows: List[Dict[str, str]], observer_rows: List[Dict[str, str]]) -> Dict[str, object]:
    observer_columns = set()
    baseline_columns = set()
    for row in observer_rows:
        observer_columns.update(row.keys())
    for row in baseline_rows:
        baseline_columns.update(row.keys())
    observer_present = int(all(column in observer_columns for column in OBSERVER_COLUMNS))
    baseline_disabled = int(max_col(baseline_rows, "q1_sic_observer_isolated_enabled") == 0)
    return {
        "observer_columns_present": observer_present,
        "baseline_observer_columns_present": int(any(column in baseline_columns for column in OBSERVER_COLUMNS)),
        "baseline_observer_disabled_max": max_col(baseline_rows, "q1_sic_observer_isolated_enabled"),
        "baseline_observer_disabled_ok": baseline_disabled,
        "observer_enabled_max": max_col(observer_rows, "q1_sic_observer_isolated_enabled"),
        "observer_post_decision_only_max": max_col(observer_rows, "q1_sic_observer_post_decision_only"),
        "observer_used_immutable_snapshot_max": max_col(observer_rows, "q1_sic_observer_used_immutable_snapshot"),
        "observer_mutated_control_state_max": max_col(observer_rows, "q1_sic_observer_mutated_control_state"),
        "observer_gt_signal_used_max": max_col(observer_rows, "q1_sic_observer_gt_signal_used"),
        "observer_would_touch_normal_frame_max": max_col(observer_rows, "q1_sic_observer_would_touch_normal_frame"),
        "observer_pressure_memory_enabled_max": max_col(observer_rows, "q1_sic_observer_pressure_memory_enabled"),
        "observer_pressure_memory_used_max": max_col(observer_rows, "q1_sic_observer_pressure_memory_used"),
    }


def snowfall_1150_check(baseline_root: Path, observer_root: Path) -> Dict[str, object]:
    baseline = by_frame(load_video(baseline_root, SNOW)).get(1150, {})
    observer = by_frame(load_video(observer_root, SNOW)).get(1150, {})
    key_fields = [
        "action_label",
        "ai_intervention_applied",
        "ai_intervention_detector_requested",
        "yolo_called",
        "selected_mode",
        "selected_mode_before_guard",
        "selected_mode_after_guard",
        "q1_sic_arbitration_label",
    ]
    live_columns = sorted(
        key for key in set(baseline) | set(observer) if key.startswith(LIVE_PROBE_PREFIX)
    )
    key_match = int(
        bool(baseline and observer)
        and all(
            normalize(baseline.get(field, ""), field in NUMERIC_BEHAVIOR_COLUMNS)
            == normalize(observer.get(field, ""), field in NUMERIC_BEHAVIOR_COLUMNS)
            for field in key_fields
        )
    )
    live_match = int(
        bool(baseline and observer)
        and all(normalize(baseline.get(field, "")) == normalize(observer.get(field, "")) for field in live_columns)
    )
    observer_ok = int(
        bool(observer)
        and truthy(observer.get("q1_sic_observer_isolated_enabled"))
        and truthy(observer.get("q1_sic_observer_post_decision_only"))
        and truthy(observer.get("q1_sic_observer_used_immutable_snapshot"))
        and not truthy(observer.get("q1_sic_observer_gt_signal_used"))
        and not truthy(observer.get("q1_sic_observer_would_touch_normal_frame"))
        and not truthy(observer.get("q1_sic_observer_mutated_control_state"))
    )
    return {
        "frame": 1150,
        "baseline_action": baseline.get("action_label", ""),
        "observer_action": observer.get("action_label", ""),
        "baseline_proposal": baseline.get("ai_intervention_applied", ""),
        "observer_proposal": observer.get("ai_intervention_applied", ""),
        "baseline_detector_request": baseline.get("ai_intervention_detector_requested", ""),
        "observer_detector_request": observer.get("ai_intervention_detector_requested", ""),
        "baseline_q1_label": baseline.get("q1_sic_arbitration_label", ""),
        "observer_q1_label": observer.get("q1_sic_arbitration_label", ""),
        "baseline_live_probe_would_select": baseline.get("q1_sic_detector_action_probe_would_select_shadow", ""),
        "observer_live_probe_would_select": observer.get("q1_sic_detector_action_probe_would_select_shadow", ""),
        "observer_enabled": observer.get("q1_sic_observer_isolated_enabled", ""),
        "observer_gt_signal_used": observer.get("q1_sic_observer_gt_signal_used", ""),
        "observer_would_touch_normal_frame": observer.get("q1_sic_observer_would_touch_normal_frame", ""),
        "observer_reject_reason": observer.get("q1_sic_observer_reject_reason", ""),
        "behavior_fields_match": key_match,
        "live_probe_fields_match": live_match,
        "observer_safe": observer_ok,
        "snowFall_1150_paired_same_source_ok": int(key_match and live_match and observer_ok),
    }


def parking_check(baseline_root: Path, observer_root: Path) -> Dict[str, object]:
    baseline = load_video(baseline_root, PARKING)
    observer = load_video(observer_root, PARKING)
    baseline_by_key = keyed(baseline)
    observer_by_key = keyed(observer)
    live_columns = live_probe_columns(baseline, observer)
    live_delta_rows = 0
    for key in sorted(set(baseline_by_key) & set(observer_by_key)):
        brow = baseline_by_key[key]
        orow = observer_by_key[key]
        if any(normalize(brow.get(column, "")) != normalize(orow.get(column, "")) for column in live_columns):
            live_delta_rows += 1
    baseline_summary = video_summary(baseline_root, *PARKING)
    observer_summary_row = video_summary(observer_root, *PARKING)
    baseline_proposal = number(baseline_summary.get("intervention_rate"), rate(baseline, "ai_intervention_applied"))
    observer_proposal = number(observer_summary_row.get("intervention_rate"), rate(observer, "ai_intervention_applied"))
    baseline_detector = number(baseline_summary.get("detector_request_rate"), rate(baseline, "ai_intervention_detector_requested"))
    observer_detector = number(observer_summary_row.get("detector_request_rate"), rate(observer, "ai_intervention_detector_requested"))
    baseline_unprotected = sum(int(unprotected(row)) for row in baseline)
    observer_unprotected = sum(int(unprotected(row)) for row in observer)
    behavior_match = int(
        abs(baseline_proposal - observer_proposal) <= 0.00001
        and abs(baseline_detector - observer_detector) <= 0.00001
        and baseline_unprotected == observer_unprotected
    )
    return {
        "baseline_parking_proposal": f"{baseline_proposal:.5f}",
        "observer_parking_proposal": f"{observer_proposal:.5f}",
        "baseline_parking_detector": f"{baseline_detector:.5f}",
        "observer_parking_detector": f"{observer_detector:.5f}",
        "baseline_parking_unprotected_fn": baseline_unprotected,
        "observer_parking_unprotected_fn": observer_unprotected,
        "parking_live_probe_delta_rows": live_delta_rows,
        "parking_behavior_match": behavior_match,
        "parking_live_probe_match": int(live_delta_rows == 0),
        "parking_paired_same_source_ok": int(behavior_match and live_delta_rows == 0),
    }


def failure_rows(
    decision: str,
    summary: Dict[str, object],
    baseline_exec: Dict[str, object],
    observer_exec: Dict[str, object],
    local: Dict[str, object],
    observer: Dict[str, object],
) -> List[Dict[str, object]]:
    return [
        {
            "classification": "baseline local gate failure",
            "is_primary": int(decision == "FAIL_BASELINE_LOCAL_GATES"),
            "evidence": f"baseline_local_gates_ok={local.get('baseline_local_gates_ok')}",
        },
        {
            "classification": "observer changes behavior",
            "is_primary": int(decision == "FAIL_OBSERVER_IDENTITY"),
            "evidence": f"behavior_delta_cells={summary.get('behavior_delta_cells')};behavior_delta_rows={summary.get('behavior_delta_rows')}",
        },
        {
            "classification": "observer changes live-probe fields",
            "is_primary": int(decision == "FAIL_LIVE_PROBE_PURITY"),
            "evidence": f"live_probe_delta_cells={summary.get('live_probe_delta_cells')};live_probe_delta_rows={summary.get('live_probe_delta_rows')}",
        },
        {
            "classification": "observer telemetry missing",
            "is_primary": int(decision == "FAIL_OBSERVER_TELEMETRY"),
            "evidence": f"observer_columns_present={observer.get('observer_columns_present')};observer_enabled_max={observer.get('observer_enabled_max')}",
        },
        {
            "classification": "observer telemetry unsafe",
            "is_primary": 0,
            "evidence": (
                f"mutated={observer.get('observer_mutated_control_state_max')};"
                f"gt={observer.get('observer_gt_signal_used_max')};"
                f"touch={observer.get('observer_would_touch_normal_frame_max')};"
                f"pressure={observer.get('observer_pressure_memory_enabled_max')}"
            ),
        },
        {
            "classification": "config mismatch",
            "is_primary": 0,
            "evidence": "config diff written to r3d_config_diff_baseline_vs_observer.csv",
        },
        {
            "classification": "verifier mismatch",
            "is_primary": int(decision == "FAIL_ALIGNMENT"),
            "evidence": (
                f"row_presence_deltas={summary.get('row_presence_deltas')};"
                f"duplicate_extra={summary.get('baseline_duplicate_extra_rows')}/{summary.get('observer_duplicate_extra_rows')}"
            ),
        },
        {
            "classification": "normal-frame safety violation",
            "is_primary": 0,
            "evidence": f"normal_safety_ok={local.get('normal_safety_ok')}",
        },
        {
            "classification": "GT leakage",
            "is_primary": 0,
            "evidence": (
                f"q1_sic_gt_signal_used_for_decision_max={local.get('q1_sic_gt_signal_used_for_decision_max')};"
                f"observer_gt={observer.get('observer_gt_signal_used_max')}"
            ),
        },
        {
            "classification": "parking regression",
            "is_primary": 0,
            "evidence": f"parking_preserved_ok={local.get('parking_preserved_ok')}",
        },
        {
            "classification": "copyMachine regression",
            "is_primary": 0,
            "evidence": f"copyMachine_preserved_ok={local.get('copyMachine_preserved_ok')}",
        },
        {
            "classification": "port watch regression",
            "is_primary": 0,
            "evidence": f"port_watch_preserved_ok={local.get('port_watch_preserved_ok')}",
        },
        {
            "classification": "unintended snowFall enforcement",
            "is_primary": 0,
            "evidence": f"no_new_snowfall_enforcement_ok={local.get('no_new_snowfall_enforcement_ok')}",
        },
        {
            "classification": "unintended port retighten",
            "is_primary": 0,
            "evidence": f"no_port_retighten_enforcement_ok={local.get('no_port_retighten_enforcement_ok')}",
        },
        {
            "classification": "baseline execution failure",
            "is_primary": 0,
            "evidence": f"baseline_execution_ok={baseline_exec.get('execution_ok')}",
        },
        {
            "classification": "observer execution failure",
            "is_primary": 0,
            "evidence": f"observer_execution_ok={observer_exec.get('execution_ok')}",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1C1R3D paired live-probe purity.")
    parser.add_argument("--baseline-root", required=True)
    parser.add_argument("--observer-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    baseline_root = Path(args.baseline_root)
    observer_root = Path(args.observer_root)
    out = Path(args.out)

    baseline_rows = all_guarded_rows(baseline_root)
    observer_rows = all_guarded_rows(observer_root)
    behavior_deltas = compare_behavior(baseline_rows, observer_rows)
    live_probe_deltas = compare_live_probe(baseline_rows, observer_rows)
    summary = summarize_deltas(behavior_deltas, live_probe_deltas, baseline_rows, observer_rows)
    baseline_exec = progress_summary(baseline_root)
    observer_exec = progress_summary(observer_root)
    local, row_checks = local_gates(baseline_root)
    observer = observer_summary(baseline_rows, observer_rows)
    snow = snowfall_1150_check(baseline_root, observer_root)
    parking = parking_check(baseline_root, observer_root)
    config_rows = config_diff()

    alignment_ok = int(
        summary["row_count_match"]
        and summary["row_presence_deltas"] == 0
        and summary["baseline_duplicate_extra_rows"] == 0
        and summary["observer_duplicate_extra_rows"] == 0
    )
    baseline_execution_ok = int(baseline_exec["execution_ok"])
    observer_execution_ok = int(observer_exec["execution_ok"])
    baseline_local_gates_ok = int(local["baseline_local_gates_ok"])
    observer_identity_ok = int(summary["behavior_delta_cells"] == 0)
    live_probe_purity_ok = int(summary["live_probe_delta_cells"] == 0 and snow["live_probe_fields_match"] == 1 and parking["parking_live_probe_match"] == 1)
    observer_telemetry_ok = int(
        observer["observer_columns_present"]
        and observer["baseline_observer_disabled_ok"]
        and observer["observer_enabled_max"] == 1
        and observer["observer_post_decision_only_max"] == 1
        and observer["observer_used_immutable_snapshot_max"] == 1
        and observer["observer_mutated_control_state_max"] == 0
        and observer["observer_gt_signal_used_max"] == 0
        and observer["observer_would_touch_normal_frame_max"] == 0
        and observer["observer_pressure_memory_enabled_max"] == 0
        and observer["observer_pressure_memory_used_max"] == 0
    )

    if not alignment_ok:
        decision = "FAIL_ALIGNMENT"
    elif not baseline_execution_ok or not observer_execution_ok or not baseline_local_gates_ok:
        decision = "FAIL_BASELINE_LOCAL_GATES"
    elif not observer_identity_ok:
        decision = "FAIL_OBSERVER_IDENTITY"
    elif not live_probe_purity_ok:
        decision = "FAIL_LIVE_PROBE_PURITY"
    elif not observer_telemetry_ok:
        decision = "FAIL_OBSERVER_TELEMETRY"
    else:
        decision = "PASS_LIVE_PROBE_PURITY"

    summary.update({
        "baseline_execution_ok": baseline_execution_ok,
        "observer_execution_ok": observer_execution_ok,
        "baseline_local_gates_ok": baseline_local_gates_ok,
        "observer_identity_ok": observer_identity_ok,
        "live_probe_purity_ok": live_probe_purity_ok,
        "observer_telemetry_ok": observer_telemetry_ok,
        "alignment_ok": alignment_ok,
        "decision": decision,
    })
    local_summary = {
        **baseline_exec,
        **local,
        "observer_execution_ok": observer_execution_ok,
        "snowFall_1150_paired_same_source_ok": snow["snowFall_1150_paired_same_source_ok"],
        "parking_paired_same_source_ok": parking["parking_paired_same_source_ok"],
        "decision": decision,
    }

    write_csv(out / "r3d_baseline_vs_observer_behavior_delta.csv", behavior_deltas)
    write_csv(out / "r3d_live_probe_delta.csv", live_probe_deltas)
    write_csv(out / "r3d_local_gates.csv", [local_summary])
    write_csv(out / "r3d_local_gate_row_checks.csv", row_checks)
    write_csv(out / "r3d_observer_telemetry_summary.csv", [observer])
    write_csv(out / "r3d_snowfall_1150_check.csv", [snow])
    write_csv(out / "r3d_parking_check.csv", [parking])
    write_csv(out / "r3d_config_diff_baseline_vs_observer.csv", config_rows)
    write_csv(out / "r3d_failure_classification.csv", failure_rows(decision, summary, baseline_exec, observer_exec, local, observer))
    write_csv(out / "r3d_baseline_vs_observer_summary.csv", [summary])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
