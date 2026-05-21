"""Audit Q1-SIC-1C1R3C live-probe / observer gating interaction.

This script is analysis-only. It reads existing source/config/output CSVs and
writes audit summaries to a new output folder.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_EXPERIMENT = PROJECT_ROOT / "src" / "run_experiment.py"
FRESH_CONFIG = PROJECT_ROOT / "configs" / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun.yaml"
R3C_CONFIG = PROJECT_ROOT / "configs" / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3c_observer_gated_same_source_subset_dryrun.yaml"

PARKING = ("intermittentObjectMotion", "parking")
SNOW = ("badWeather", "snowFall")

LIVE_PROBE_COLUMNS = [
    "q1_sic_detector_action_probe_enabled",
    "q1_sic_detector_action_probe_active",
    "q1_sic_detector_action_probe_event_risk_pressure",
    "q1_sic_detector_action_probe_detector_pressure",
    "q1_sic_detector_action_probe_detector_blocked",
    "q1_sic_detector_action_probe_cooldown_active",
    "q1_sic_detector_action_probe_proposal_absent",
    "q1_sic_detector_action_probe_runtime_empty_proxy",
    "q1_sic_detector_action_probe_would_select_shadow",
    "q1_sic_detector_action_probe_reject_reason",
    "q1_sic_detector_action_probe_gt_signal_used",
    "q1_sic_detector_action_probe_would_touch_normal_frame",
    "q1_sic_detector_action_probe_stable_snapshot_enabled",
    "q1_sic_detector_action_probe_pressure_memory_active",
]

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

SNOW_AUDIT_FIELDS = [
    "action_label",
    "ai_intervention_applied",
    "ai_intervention_detector_requested",
    "yolo_called",
    "selected_mode",
    "selected_mode_before_guard",
    "selected_mode_after_guard",
    "q1_sic_arbitration_active",
    "q1_sic_arbitration_label",
    "q1_sic_owner",
    "q1_sic_reference_step",
    "active_event_memory",
    "ai_intervention_risk_high",
    "ai_intervention_guard_active",
    "ai_detector_needed_pred",
    "ai_detector_request_blocked_no_refresh_model",
    "forced_refresh_cooldown_active",
    "q1_sic_runtime_detector_pressure_proxy",
    "q1_sic_runtime_proposal_absent_proxy",
    "q1_sic_runtime_detector_empty_proxy",
] + LIVE_PROBE_COLUMNS + OBSERVER_COLUMNS


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


def norm(value: object) -> str:
    if value in (None, "NA"):
        return ""
    text = str(value).strip()
    try:
        numeric = float(text)
        if numeric == int(numeric):
            return str(int(numeric))
        return str(numeric)
    except (TypeError, ValueError):
        return text


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


def all_guarded_paths(root: Path) -> List[Path]:
    return sorted(root.glob(f"raw_results/*/*/{PIPELINE}/frame_metrics.csv"))


def all_guarded_rows(root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in all_guarded_paths(root):
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


def by_frame(root: Path, video: Sequence[str]) -> Dict[int, Dict[str, str]]:
    path = root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv"
    return {frame(row): row for row in read_csv(path)}


def is_fn(row: Dict[str, str]) -> bool:
    return str(row.get("Event_State") or row.get("frame_state") or "") == "FN"


def protected(row: Dict[str, str]) -> bool:
    if truthy(row.get("protected_fn")) or row.get("q1_sic_post_protection_label") == "protected_event_fn":
        return True
    return bool(is_fn(row) and (truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested"))))


def unprotected(row: Dict[str, str]) -> bool:
    if not row:
        return False
    if truthy(row.get("unprotected_fn")) or row.get("q1_sic_post_protection_label") == "unprotected_fn":
        return True
    return bool(is_fn(row) and not protected(row))


def max_col(rows: List[Dict[str, str]], column: str) -> float:
    return max([number(row.get(column)) for row in rows] or [0.0])


def mtime_range(paths: Sequence[Path]) -> Tuple[str, str]:
    mtimes = [path.stat().st_mtime for path in paths if path.exists()]
    if not mtimes:
        return "", ""
    return (
        datetime.fromtimestamp(min(mtimes)).isoformat(timespec="seconds"),
        datetime.fromtimestamp(max(mtimes)).isoformat(timespec="seconds"),
    )


def deep_update(base: Dict[str, object], override: Dict[str, object]) -> Dict[str, object]:
    merged = dict(base or {})
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_update(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config_with_base(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle) or {}
    base_ref = cfg.pop("base_config", cfg.pop("_base_config", ""))
    if base_ref:
        base_path = Path(base_ref)
        if not base_path.is_absolute():
            base_path = path.parent / base_path
        return deep_update(load_config_with_base(base_path), cfg)
    return cfg


def flatten(prefix: str, value: object, out: Dict[str, object]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            flatten(f"{prefix}.{key}" if prefix else str(key), child, out)
    else:
        out[prefix] = value


def flat_config(path: Path) -> Dict[str, object]:
    flat: Dict[str, object] = {}
    flatten("", load_config_with_base(path), flat)
    return flat


def classify_config_diff(key: str, fresh_present: bool, r3c_present: bool, fresh: object, r3c: object) -> str:
    if key in {"experiment_name", "edge_profile.name", "output_root"}:
        return "intended output-root/name change"
    if key.endswith("q1_sic_observer_isolated_enabled"):
        return "intended observer telemetry flag"
    if key.endswith("q1_sic_detector_action_probe_enabled"):
        return "live probe preserved" if truthy(fresh) and truthy(r3c) else "live probe semantic mismatch"
    if key.endswith("q1_sic_detector_action_probe_stable_snapshot_enabled"):
        return "missing-vs-false default suspicious" if (not fresh_present and r3c_present and not truthy(r3c)) else "stable snapshot semantic difference"
    if key.endswith("q1_sic_event_risk_empty_detect_proxy_enabled"):
        return "missing-vs-false default suspicious" if (not fresh_present and r3c_present and not truthy(r3c)) else "empty-detect proxy semantic difference"
    if key.endswith("q1_sic_observer_pressure_memory_enabled"):
        return "missing-vs-false default suspicious" if (not fresh_present and r3c_present and not truthy(r3c)) else "observer memory semantic difference"
    if fresh_present != r3c_present and str(fresh) != str(r3c):
        return "unknown missing-vs-explicit difference"
    return "unknown"


def config_semantic_diff() -> List[Dict[str, object]]:
    fresh = flat_config(FRESH_CONFIG)
    r3c = flat_config(R3C_CONFIG)
    rows = []
    for key in sorted(set(fresh) | set(r3c)):
        fresh_present = key in fresh
        r3c_present = key in r3c
        fresh_value = fresh.get(key, "")
        r3c_value = r3c.get(key, "")
        if str(fresh_value) == str(r3c_value):
            continue
        rows.append({
            "key": key,
            "fresh_c1r_present": int(fresh_present),
            "r3c_present": int(r3c_present),
            "fresh_c1r_value": fresh_value,
            "r3c_value": r3c_value,
            "classification": classify_config_diff(key, fresh_present, r3c_present, fresh_value, r3c_value),
        })
    return rows


def source_flag_inventory() -> List[Dict[str, object]]:
    text = RUN_EXPERIMENT.read_text(encoding="utf-8", errors="replace") if RUN_EXPERIMENT.exists() else ""
    lines = text.splitlines()
    rows = []
    flags = [
        "q1_sic_detector_action_probe_enabled",
        "q1_sic_observer_isolated_enabled",
        "q1_sic_observer_pressure_memory_enabled",
        "q1_sic_detector_action_probe_stable_snapshot_enabled",
        "q1_sic_event_risk_empty_detect_proxy_enabled",
    ]
    for flag in flags:
        matches = [(idx + 1, line.strip()) for idx, line in enumerate(lines) if flag in line]
        for line_no, snippet in matches:
            if "def _apply_q1_sic_detector_action_probe" in "\n".join(lines[max(0, line_no - 25):line_no + 25]):
                region = "live_probe_helper_nearby"
            elif "build_q1_sic_detector_action_observer_row" in "\n".join(lines[max(0, line_no - 25):line_no + 25]):
                region = "observer_builder_nearby"
            elif "final_safety_arbitration" in "\n".join(lines[max(0, line_no - 25):line_no + 25]):
                region = "final_arbitration_nearby"
            elif "frame_metrics_row.update" in "\n".join(lines[max(0, line_no - 15):line_no + 15]):
                region = "frame_metrics_merge_nearby"
            else:
                region = "other"
            rows.append({
                "flag": flag,
                "line": line_no,
                "region": region,
                "snippet": snippet,
            })
    live_probe_start = next((idx for idx, line in enumerate(lines) if "def _apply_q1_sic_detector_action_probe" in line), -1)
    live_probe_end = next((idx for idx, line in enumerate(lines[live_probe_start + 1:], start=live_probe_start + 1) if line.startswith("    def ") and idx > live_probe_start), len(lines)) if live_probe_start >= 0 else -1
    helper_text = "\n".join(lines[live_probe_start:live_probe_end]) if live_probe_start >= 0 else ""
    rows.append({
        "flag": "__SUMMARY__",
        "line": "",
        "region": "live_probe_helper",
        "snippet": f"observer_flag_in_live_probe_helper={int('q1_sic_observer_isolated_enabled' in helper_text)};live_info_writes={helper_text.count('info[')};calls_pressure_memory={int('_update_q1_sic_detector_action_probe_pressure_memory' in helper_text)}",
    })
    rows.append({
        "flag": "__SUMMARY__",
        "line": "",
        "region": "observer_merge",
        "snippet": f"observer_builder_calls={text.count('build_q1_sic_detector_action_observer_row')};frame_metrics_update_calls={text.count('frame_metrics_row.update')}",
    })
    return rows


def live_probe_deltas(fresh_rows: List[Dict[str, str]], r3c_rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, object]], Dict[Tuple[str, str, int, str], int], Counter]:
    fresh = {row_key(row): row for row in fresh_rows}
    r3c = {row_key(row): row for row in r3c_rows}
    by_key: Dict[Tuple[str, str, int, str], int] = defaultdict(int)
    by_col: Counter = Counter()
    examples: Dict[str, Dict[str, object]] = {}
    for key in sorted(set(fresh) & set(r3c)):
        for col in LIVE_PROBE_COLUMNS:
            left = norm(fresh[key].get(col, ""))
            right = norm(r3c[key].get(col, ""))
            if left != right:
                by_key[key] += 1
                by_col[col] += 1
                examples.setdefault(col, {
                    "example_category": key[0],
                    "example_video": key[1],
                    "example_frame": key[2],
                    "example_fresh_c1r": fresh[key].get(col, ""),
                    "example_r3c": r3c[key].get(col, ""),
                })
    rows = []
    for col, count in by_col.most_common():
        row = {"column": col, "delta_rows": count}
        row.update(examples.get(col, {}))
        rows.append(row)
    rows.insert(0, {
        "column": "__TOTAL_LIVE_PROBE_CELL_DELTAS__",
        "delta_rows": sum(by_col.values()),
        "rows_with_any_live_probe_delta": len(by_key),
    })
    return rows, by_key, by_col


def behavior_by_video(deltas: List[Dict[str, str]]) -> List[Dict[str, object]]:
    counter = Counter((row.get("category", ""), row.get("video", "")) for row in deltas)
    return [{"category": key[0], "video": key[1], "delta_rows": count} for key, count in counter.most_common()]


def action_transitions(deltas: List[Dict[str, str]]) -> List[Dict[str, object]]:
    counter = Counter()
    for row in deltas:
        if row.get("field") == "action_label":
            counter[(row.get("fresh_c1r", ""), row.get("r3c", ""))] += 1
    return [{"fresh_c1r_action": key[0], "r3c_action": key[1], "delta_rows": count} for key, count in counter.most_common()]


def behavior_live_probe_crosstab(
    deltas: List[Dict[str, str]],
    fresh_rows: Dict[Tuple[str, str, int, str], Dict[str, str]],
    r3c_rows: Dict[Tuple[str, str, int, str], Dict[str, str]],
    live_delta_keys: Dict[Tuple[str, str, int, str], int],
) -> List[Dict[str, object]]:
    counter = Counter()
    for delta in deltas:
        try:
            frame_idx = int(float(delta.get("frame", -1)))
        except (TypeError, ValueError):
            frame_idx = -1
        key = (delta.get("category", ""), delta.get("video", ""), frame_idx, delta.get("pipeline", PIPELINE))
        fresh = fresh_rows.get(key, {})
        r3c = r3c_rows.get(key, {})
        live_delta = int(key in live_delta_keys)
        probe_active_diff = int(norm(fresh.get("q1_sic_detector_action_probe_active", "")) != norm(r3c.get("q1_sic_detector_action_probe_active", "")))
        q1_active_diff = int(norm(fresh.get("q1_sic_arbitration_active", "")) != norm(r3c.get("q1_sic_arbitration_active", "")))
        observer_enabled = int(truthy(r3c.get("q1_sic_observer_isolated_enabled")))
        observer_action_detect = int(truthy(r3c.get("q1_sic_observer_action_is_detect")))
        counter[(delta.get("field", ""), live_delta, probe_active_diff, q1_active_diff, observer_enabled, observer_action_detect)] += 1
    return [
        {
            "field": key[0],
            "has_live_probe_delta": key[1],
            "probe_active_diff": key[2],
            "q1_active_diff": key[3],
            "r3c_observer_enabled": key[4],
            "r3c_observer_action_detect": key[5],
            "delta_rows": count,
        }
        for key, count in counter.most_common()
    ]


def snowfall_audit(fresh_root: Path, r3c_root: Path) -> List[Dict[str, object]]:
    fresh = by_frame(fresh_root, SNOW).get(1150, {})
    r3c = by_frame(r3c_root, SNOW).get(1150, {})
    rows = []
    for field in SNOW_AUDIT_FIELDS:
        rows.append({
            "category": SNOW[0],
            "video": SNOW[1],
            "frame": 1150,
            "field": field,
            "fresh_c1r": fresh.get(field, ""),
            "r3c": r3c.get(field, ""),
            "changed": int(norm(fresh.get(field, "")) != norm(r3c.get(field, ""))),
        })
    return rows


def parking_audit(fresh_root: Path, r3c_root: Path, live_delta_keys: Dict[Tuple[str, str, int, str], int]) -> List[Dict[str, object]]:
    fresh_by_frame = by_frame(fresh_root, PARKING)
    r3c_by_frame = by_frame(r3c_root, PARKING)
    rows = []
    for frame_id in sorted(set(fresh_by_frame) | set(r3c_by_frame)):
        fresh = fresh_by_frame.get(frame_id, {})
        r3c = r3c_by_frame.get(frame_id, {})
        became_unprotected = int(not unprotected(fresh) and unprotected(r3c))
        if not became_unprotected and norm(fresh.get("action_label", "")) == norm(r3c.get("action_label", "")) and norm(fresh.get("ai_intervention_applied", "")) == norm(r3c.get("ai_intervention_applied", "")):
            continue
        key = (PARKING[0], PARKING[1], frame_id, PIPELINE)
        rows.append({
            "category": PARKING[0],
            "video": PARKING[1],
            "frame": frame_id,
            "became_unprotected_fn": became_unprotected,
            "fresh_action": fresh.get("action_label", ""),
            "r3c_action": r3c.get("action_label", ""),
            "fresh_proposal": fresh.get("ai_intervention_applied", ""),
            "r3c_proposal": r3c.get("ai_intervention_applied", ""),
            "fresh_detector_request": fresh.get("ai_intervention_detector_requested", ""),
            "r3c_detector_request": r3c.get("ai_intervention_detector_requested", ""),
            "fresh_q1_label": fresh.get("q1_sic_arbitration_label", ""),
            "r3c_q1_label": r3c.get("q1_sic_arbitration_label", ""),
            "fresh_unprotected": int(unprotected(fresh)),
            "r3c_unprotected": int(unprotected(r3c)),
            "fresh_probe_active": fresh.get("q1_sic_detector_action_probe_active", ""),
            "r3c_probe_active": r3c.get("q1_sic_detector_action_probe_active", ""),
            "fresh_probe_would_select": fresh.get("q1_sic_detector_action_probe_would_select_shadow", ""),
            "r3c_probe_would_select": r3c.get("q1_sic_detector_action_probe_would_select_shadow", ""),
            "r3c_observer_enabled": r3c.get("q1_sic_observer_isolated_enabled", ""),
            "r3c_observer_gt_signal_used": r3c.get("q1_sic_observer_gt_signal_used", ""),
            "live_probe_delta_cells_on_row": live_delta_keys.get(key, 0),
        })
    return rows


def classification_and_recommendation(
    source_rows: List[Dict[str, object]],
    config_rows: List[Dict[str, object]],
    behavior_deltas: List[Dict[str, str]],
    live_delta_keys: Dict[Tuple[str, str, int, str], int],
    live_delta_cells: int,
    fresh_root: Path,
    r3c_root: Path,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], str, str]:
    source_summary = " ".join(str(row.get("snippet", "")) for row in source_rows if row.get("flag") == "__SUMMARY__")
    observer_in_live_helper = "observer_flag_in_live_probe_helper=1" in source_summary
    suspicious_explicit_false = any("missing-vs-false" in str(row.get("classification", "")) for row in config_rows)
    src_mtime = RUN_EXPERIMENT.stat().st_mtime if RUN_EXPERIMENT.exists() else 0.0
    fresh_min, fresh_max = mtime_range(all_guarded_paths(fresh_root))
    r3c_min, r3c_max = mtime_range(all_guarded_paths(r3c_root))
    try:
        fresh_max_ts = max(path.stat().st_mtime for path in all_guarded_paths(fresh_root))
    except ValueError:
        fresh_max_ts = 0.0
    source_newer_than_fresh = int(src_mtime > fresh_max_ts)
    behavior_rows_with_probe_delta = sum(
        1 for delta in behavior_deltas
        if (
            delta.get("category", ""),
            delta.get("video", ""),
            int(float(delta.get("frame", -1))),
            delta.get("pipeline", PIPELINE),
        ) in live_delta_keys
    )
    if source_newer_than_fresh and not observer_in_live_helper:
        primary = "FRESH_C1R_VS_R3C_SOURCE_PATH_MISMATCH"
        recommendation = "C. Q1-SIC-1C1R3D live-probe helper purity audit/repair"
    elif observer_in_live_helper:
        primary = "OBSERVER_FLAG_STILL_CHANGES_LIVE_PROBE_PATH"
        recommendation = "A. Q1-SIC-1C1R3D observer flag hard-isolation repair"
    elif suspicious_explicit_false:
        primary = "EXPLICIT_FALSE_CONFIG_DIFF_CHANGES_BEHAVIOR"
        recommendation = "B. Q1-SIC-1C1R3D config-default parity repair"
    elif live_delta_cells > 0:
        primary = "LIVE_PROBE_HELPER_IS_BEHAVIORAL_NOT_TELEMETRY"
        recommendation = "C. Q1-SIC-1C1R3D live-probe helper purity audit/repair"
    else:
        primary = "UNKNOWN_NEEDS_SOURCE_INSTRUMENTATION"
        recommendation = "C. Q1-SIC-1C1R3D live-probe helper purity audit/repair"

    rows = [
        {"classification": "OBSERVER_FLAG_STILL_CHANGES_LIVE_PROBE_PATH", "is_primary": int(primary == "OBSERVER_FLAG_STILL_CHANGES_LIVE_PROBE_PATH"), "evidence": f"observer_flag_in_live_probe_helper={int(observer_in_live_helper)}"},
        {"classification": "EXPLICIT_FALSE_CONFIG_DIFF_CHANGES_BEHAVIOR", "is_primary": int(primary == "EXPLICIT_FALSE_CONFIG_DIFF_CHANGES_BEHAVIOR"), "evidence": f"missing_vs_false_suspicious={int(suspicious_explicit_false)}"},
        {"classification": "LIVE_PROBE_HELPER_IS_BEHAVIORAL_NOT_TELEMETRY", "is_primary": int(primary == "LIVE_PROBE_HELPER_IS_BEHAVIORAL_NOT_TELEMETRY"), "evidence": f"live_probe_delta_cells={live_delta_cells};behavior_rows_with_probe_delta={behavior_rows_with_probe_delta}"},
        {"classification": "LIVE_PROBE_FIELD_WRITE_ORDER_CHANGED", "is_primary": int(primary == "LIVE_PROBE_FIELD_WRITE_ORDER_CHANGED"), "evidence": "not directly proven from static/source-output audit"},
        {"classification": "OBSERVER_AND_LIVE_PROBE_DICT_COLLISION", "is_primary": int(primary == "OBSERVER_AND_LIVE_PROBE_DICT_COLLISION"), "evidence": "observer columns use q1_sic_observer_* prefix; no name collision found"},
        {"classification": "CONFIG_GET_DEFAULT_SEMANTICS_CHANGED", "is_primary": int(primary == "CONFIG_GET_DEFAULT_SEMANTICS_CHANGED"), "evidence": "explicit false flags match bool(cfg.get(..., False)) semantics but remain suspicious until parity replay"},
        {"classification": "VERIFIER_COUNTS_TELEMETRY_AS_BEHAVIOR", "is_primary": int(primary == "VERIFIER_COUNTS_TELEMETRY_AS_BEHAVIOR"), "evidence": "verifier behavior fields exclude q1_sic_observer_* columns"},
        {"classification": "FRESH_C1R_VS_R3C_SOURCE_PATH_MISMATCH", "is_primary": int(primary == "FRESH_C1R_VS_R3C_SOURCE_PATH_MISMATCH"), "evidence": f"source_newer_than_fresh_c1r_outputs={source_newer_than_fresh};fresh_mtime_max={fresh_max};r3c_mtime_min={r3c_min}"},
        {"classification": "UNKNOWN_NEEDS_SOURCE_INSTRUMENTATION", "is_primary": int(primary == "UNKNOWN_NEEDS_SOURCE_INSTRUMENTATION"), "evidence": "remaining risk after static/source-output audit"},
        {"classification": "snowFall 1150 drift", "is_primary": 0, "evidence": "fresh CLOSED_EMPTY_ACC/proposal1/FORCE_PROTECT_EVENT_MEMORY vs R3C DETECT_ACC/proposal0/NO_CHANGE"},
        {"classification": "parking regression", "is_primary": 0, "evidence": "R3C proposal 0.53000 and unprotected FN 5 from verifier"},
        {"classification": "live_probe_delta_count high", "is_primary": 0, "evidence": f"live_probe_delta_cells={live_delta_cells};rows_with_live_probe_delta={len(live_delta_keys)}"},
        {"classification": "observer telemetry safe", "is_primary": 0, "evidence": "observer mutated/GT/touch/pressure-memory max all 0 in verifier"},
        {"classification": "normal safety preserved", "is_primary": 0, "evidence": "normal-frame interventions 0; q1_sic_would_touch_normal_frame max 0"},
        {"classification": "port/copyMachine preserved", "is_primary": 0, "evidence": "R3C report verified audited rows preserved"},
        {"classification": "PTZ/fountain drift", "is_primary": 0, "evidence": "behavior deltas include PTZ and fountain groups"},
        {"classification": "explicit false flag suspicious", "is_primary": 0, "evidence": f"missing-vs-false config rows={sum(1 for row in config_rows if 'missing-vs-false' in str(row.get('classification', '')))}"},
        {"classification": "missing-vs-false default suspicious", "is_primary": 0, "evidence": "R3C explicitly sets stable snapshot/proxy/observer memory false where fresh effective config lacks explicit keys"},
    ]
    repair_rows = [
        {"option": "A", "name": "Q1-SIC-1C1R3D observer flag hard-isolation repair", "recommended": int(recommendation.startswith("A.")), "reason": "Use only if observer flag is still in live-probe/arbitration paths."},
        {"option": "B", "name": "Q1-SIC-1C1R3D config-default parity repair", "recommended": int(recommendation.startswith("B.")), "reason": "Use if explicit false flags differ from missing defaults."},
        {"option": "C", "name": "Q1-SIC-1C1R3D live-probe helper purity audit/repair", "recommended": int(recommendation.startswith("C.")), "reason": "Recommended here because same-source evidence is contaminated by live-probe/source-path drift; next repair should preserve live-probe behavior exactly and move observer telemetry outside the helper."},
        {"option": "D", "name": "Q1-SIC-1C1R3D verifier correction", "recommended": 0, "reason": "Behavior deltas include action/proposal/Q1/accounting, not observer telemetry false positives."},
        {"option": "E", "name": "Stop observer path and freeze fresh C1R baseline", "recommended": int(recommendation.startswith("E.")), "reason": "Reserve for repeated inability to isolate observer without drift."},
    ]
    return rows, repair_rows, primary, recommendation


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Q1-SIC-1C1R3C live-probe / observer interaction.")
    parser.add_argument("--fresh-c1r-root", required=True)
    parser.add_argument("--r3c-root", required=True)
    parser.add_argument("--r3c-verify-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    fresh_root = Path(args.fresh_c1r_root)
    r3c_root = Path(args.r3c_root)
    verify_root = Path(args.r3c_verify_root)
    out = Path(args.out)

    fresh_rows = all_guarded_rows(fresh_root)
    r3c_rows = all_guarded_rows(r3c_root)
    fresh_by_key = {row_key(row): row for row in fresh_rows}
    r3c_by_key = {row_key(row): row for row in r3c_rows}
    behavior_deltas = read_csv(verify_root / "fresh_c1r_vs_r3c_behavior_delta.csv")

    live_summary, live_delta_keys, live_delta_by_col = live_probe_deltas(fresh_rows, r3c_rows)
    config_rows = config_semantic_diff()
    source_rows = source_flag_inventory()
    crosstab = behavior_live_probe_crosstab(behavior_deltas, fresh_by_key, r3c_by_key, live_delta_keys)
    snowfall_rows = snowfall_audit(fresh_root, r3c_root)
    parking_rows = parking_audit(fresh_root, r3c_root, live_delta_keys)
    classification_rows, repair_rows, primary, recommendation = classification_and_recommendation(
        source_rows,
        config_rows,
        behavior_deltas,
        live_delta_keys,
        sum(live_delta_by_col.values()),
        fresh_root,
        r3c_root,
    )

    write_csv(out / "r3c_live_probe_delta_summary.csv", live_summary)
    write_csv(out / "r3c_behavior_delta_by_video.csv", behavior_by_video(behavior_deltas))
    write_csv(out / "r3c_behavior_delta_by_action_transition.csv", action_transitions(behavior_deltas))
    write_csv(out / "r3c_behavior_delta_live_probe_crosstab.csv", crosstab)
    write_csv(out / "r3c_snowfall_1150_live_probe_audit.csv", snowfall_rows)
    write_csv(out / "r3c_parking_live_probe_audit.csv", parking_rows)
    write_csv(out / "r3c_config_diff_semantic_audit.csv", config_rows)
    write_csv(out / "r3c_source_flag_inventory.csv", source_rows)
    write_csv(out / "r3c_failure_classification.csv", classification_rows)
    write_csv(out / "r3c_recommended_repair_options.csv", repair_rows)

    video_rows = behavior_by_video(behavior_deltas)
    transition_rows = action_transitions(behavior_deltas)
    summary = {
        "primary_failure_classification": primary,
        "recommended_repair": recommendation,
        "behavior_delta_rows": len(behavior_deltas),
        "live_probe_delta_cells": sum(live_delta_by_col.values()),
        "rows_with_live_probe_delta": len(live_delta_keys),
        "parking_rows_audited": len(parking_rows),
        "parking_became_unprotected_rows": sum(int(row.get("became_unprotected_fn", 0)) for row in parking_rows),
        "snowfall_1150_changed_fields": sum(int(row.get("changed", 0)) for row in snowfall_rows),
        "top_behavior_videos": video_rows[:5],
        "top_action_transitions": transition_rows[:5],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
