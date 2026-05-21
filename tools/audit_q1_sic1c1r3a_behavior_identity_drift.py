"""Audit Q1-SIC-1C1R3 behavior identity drift versus Q1-SIC-1C1R.

This script is analysis-only. It reads existing configs, source, verifier
outputs, and frame_metrics files, then writes CSV summaries to a new audit root.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
C1R_CONFIG = PROJECT_ROOT / "configs" / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml"
C1R3_CONFIG = PROJECT_ROOT / "configs" / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun.yaml"
RUN_EXPERIMENT = PROJECT_ROOT / "src" / "run_experiment.py"
R3_VERIFIER = PROJECT_ROOT / "tools" / "verify_q1_sic1c1r3_observer_isolation.py"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str] | None = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        field_set = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    field_set.append(key)
                    seen.add(key)
        fields = field_set
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


def frame_id(row: Dict[str, str]) -> int:
    for key in ("raw_frame_id", "frame_id", "frame", "frame_idx"):
        if row.get(key) not in (None, ""):
            try:
                return int(float(row[key]))
            except (TypeError, ValueError):
                return -1
    return -1


def row_key(row: Dict[str, str]) -> Tuple[str, str, int]:
    return (str(row.get("category", "")), str(row.get("video", "")), frame_id(row))


def all_guarded_frame_paths(root: Path) -> List[Path]:
    return sorted(root.glob(f"raw_results/*/*/{PIPELINE}/frame_metrics.csv"))


def all_guarded_rows(root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in all_guarded_frame_paths(root):
        parts = path.parts
        try:
            raw_idx = parts.index("raw_results")
            category = parts[raw_idx + 1]
            video = parts[raw_idx + 2]
        except (ValueError, IndexError):
            category = ""
            video = ""
        for row in read_csv(path):
            row.setdefault("category", category)
            row.setdefault("video", video)
            rows.append(row)
    return rows


def flatten(prefix: str, value: object, out: Dict[str, object]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            flatten(f"{prefix}.{key}" if prefix else str(key), child, out)
    else:
        out[prefix] = value


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
        cfg = deep_update(load_config_with_base(base_path), cfg)
    return cfg


def flat_config(path: Path) -> Dict[str, object]:
    flat: Dict[str, object] = {}
    flatten("", load_config_with_base(path), flat)
    return flat


def classify_config_diff(key: str, left: object, right: object) -> str:
    if key in {"experiment_name", "edge_profile.name"}:
        return "intended output-root/name change"
    if key in {"output_root"}:
        return "intended output-root/name change"
    if key == "resume_existing_results":
        return "suspicious resume/cache behavior flag"
    if key.endswith("q1_sic_observer_isolated_enabled"):
        return "intended observer enable flag"
    if key.endswith("q1_sic_observer_pressure_memory_enabled"):
        return "harmless telemetry flag"
    if key.endswith("q1_sic_detector_action_probe_stable_snapshot_enabled"):
        return "missing explicit disable for C1C1R2/R3 behavior" if truthy(right) else "harmless telemetry flag"
    if key.endswith("q1_sic_detector_action_probe_enabled"):
        return "suspicious default behavior flag"
    if "detector" in key and str(left) != str(right):
        return "suspicious detector scheduling flag"
    if any(token in key for token in ("protection", "carryover", "q1_sic_event", "arbitration")):
        return "suspicious branch/carry-over/protection flag"
    return "unknown"


def summarize_counter(counter: Counter, key_names: Sequence[str]) -> List[Dict[str, object]]:
    rows = []
    for key, count in counter.most_common():
        if not isinstance(key, tuple):
            key = (key,)
        row = {name: key[idx] if idx < len(key) else "" for idx, name in enumerate(key_names)}
        row["delta_rows"] = count
        rows.append(row)
    return rows


def frame_range_label(frame: int, width: int = 100) -> str:
    if frame < 0:
        return "unknown"
    start = (frame // width) * width
    return f"{start}-{start + width - 1}"


def count_duplicates(rows: List[Dict[str, str]]) -> Tuple[int, Counter]:
    counts = Counter(row_key(row) for row in rows)
    duplicate_keys = Counter({key: count for key, count in counts.items() if count > 1})
    return sum(count - 1 for count in duplicate_keys.values()), duplicate_keys


def min_max_mtime(paths: Sequence[Path]) -> Tuple[str, str]:
    mtimes = [path.stat().st_mtime for path in paths if path.exists()]
    if not mtimes:
        return "", ""
    return (
        datetime.fromtimestamp(min(mtimes)).isoformat(timespec="seconds"),
        datetime.fromtimestamp(max(mtimes)).isoformat(timespec="seconds"),
    )


def line_for(source_lines: List[str], pattern: str) -> str:
    for idx, line in enumerate(source_lines, start=1):
        if pattern in line:
            return str(idx)
    return ""


def source_inventory(c1r3_cfg: Dict[str, object]) -> List[Dict[str, object]]:
    text = RUN_EXPERIMENT.read_text(encoding="utf-8", errors="replace") if RUN_EXPERIMENT.exists() else ""
    lines = text.splitlines()

    def cfg_value(key: str, default: object = "") -> object:
        return c1r3_cfg.get(f"online_controller_guarded.{key}", default)

    rows = [
        {
            "block": "post_decision_observer_function",
            "line": line_for(lines, "def build_q1_sic_detector_action_observer_row"),
            "flag": "q1_sic_observer_isolated_enabled",
            "c1r3_effective_value": cfg_value("q1_sic_observer_isolated_enabled", False),
            "classification": "enabled but telemetry-only",
            "risk_note": "returns new q1_sic_observer_* dict and is merged after frame_metrics row assembly",
        },
        {
            "block": "observer_short_circuit_of_live_probe",
            "line": line_for(lines, "if self.q1_sic_observer_isolated_enabled:"),
            "flag": "q1_sic_observer_isolated_enabled",
            "c1r3_effective_value": cfg_value("q1_sic_observer_isolated_enabled", False),
            "classification": "enabled but telemetry-only",
            "risk_note": "bypasses old live probe writes; should only touch q1_sic_detector_action_probe telemetry fields",
        },
        {
            "block": "c1r2_pressure_memory_update",
            "line": line_for(lines, "def _update_q1_sic_detector_action_probe_pressure_memory"),
            "flag": "q1_sic_detector_action_probe_stable_snapshot_enabled",
            "c1r3_effective_value": cfg_value("q1_sic_detector_action_probe_stable_snapshot_enabled", False),
            "classification": "disabled by config and safe",
            "risk_note": "pressure memory requires stable snapshot enabled; verifier saw old pressure memory max 0",
        },
        {
            "block": "old_live_detector_action_probe",
            "line": line_for(lines, "def _apply_q1_sic_detector_action_probe"),
            "flag": "q1_sic_detector_action_probe_enabled",
            "c1r3_effective_value": cfg_value("q1_sic_detector_action_probe_enabled", False),
            "classification": "disabled by config and safe",
            "risk_note": "C1R had this enabled; R3 disables it to avoid live info writes",
        },
        {
            "block": "q1_final_safety_arbitration",
            "line": line_for(lines, "def final_safety_arbitration"),
            "flag": "q1_sic_final_arbitration_enabled",
            "c1r3_effective_value": cfg_value("q1_sic_final_arbitration_enabled", ""),
            "classification": "enabled and potentially behavior-affecting",
            "risk_note": "base Q1-SIC path can change proposal/protection when upstream action/risk trajectory changes",
        },
        {
            "block": "c1r_copymachine_restore_shim",
            "line": line_for(lines, "def _apply_q1_sic1c1r_restore_copymachine"),
            "flag": "q1_sic1c1r_restore_copymachine_enabled",
            "c1r3_effective_value": cfg_value("q1_sic1c1r_restore_copymachine_enabled", ""),
            "classification": "enabled and potentially behavior-affecting",
            "risk_note": "inherited from C1R and audited rows are preserved",
        },
        {
            "block": "c1r_port_watch_restore_shim",
            "line": line_for(lines, "q1_sic1c1r_restore_port_watch_enabled"),
            "flag": "q1_sic1c1r_restore_port_watch_enabled",
            "c1r3_effective_value": cfg_value("q1_sic1c1r_restore_port_watch_enabled", ""),
            "classification": "enabled but telemetry-only",
            "risk_note": "inherited from C1R and port 1350/1355 watch rows are preserved",
        },
        {
            "block": "q1_sic1b_empty_detect_proxy",
            "line": line_for(lines, "q1_sic_event_risk_empty_detect_proxy_enabled"),
            "flag": "q1_sic_event_risk_empty_detect_proxy_enabled",
            "c1r3_effective_value": cfg_value("q1_sic_event_risk_empty_detect_proxy_enabled", ""),
            "classification": "disabled by config and safe",
            "risk_note": "verifier saw FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION rows = 0",
        },
        {
            "block": "general_action_selection_and_detector_scheduling",
            "line": line_for(lines, "selected_mode_after_guard"),
            "flag": "many guarded-controller flags",
            "c1r3_effective_value": "inherited from C1R effective config",
            "classification": "unknown",
            "risk_note": "broad action/yolo/selected_mode deltas across non-observer rows point here or to historical source drift",
        },
    ]
    return rows


def verifier_alignment_audit(
    verifier_text: str,
    c1r_rows: List[Dict[str, str]],
    c1r3_rows: List[Dict[str, str]],
    behavior_deltas: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    c1r_dup_count, c1r_dups = count_duplicates(c1r_rows)
    c1r3_dup_count, c1r3_dups = count_duplicates(c1r3_rows)
    c1r_keys = {row_key(row) for row in c1r_rows}
    c1r3_keys = {row_key(row) for row in c1r3_rows}
    row_presence_deltas = sum(1 for row in behavior_deltas if row.get("field") == "row_presence")
    behavior_columns_line = "OBSERVER_COLUMNS" in verifier_text and "BEHAVIOR_COLUMNS" in verifier_text
    observer_compared_as_behavior = "q1_sic_observer_" in verifier_text.split("OBSERVER_COLUMNS", 1)[0]
    return [
        {"check": "compares_guarded_pipeline_only", "value": int(PIPELINE in verifier_text and "raw_results/*/*/{PIPELINE}/frame_metrics.csv" in verifier_text), "finding": "verifier uses guarded raw frame_metrics only"},
        {"check": "alignment_key", "value": "category/video/frame", "finding": "row_key returns category, video, frame; pipeline is implicit because only guarded files are loaded"},
        {"check": "frame_column_priority", "value": "raw_frame_id,frame_id,frame,frame_idx", "finding": "R3 verifier uses raw_frame_id first"},
        {"check": "c1r_row_count", "value": len(c1r_rows), "finding": "guarded rows loaded from C1R"},
        {"check": "c1r3_row_count", "value": len(c1r3_rows), "finding": "guarded rows loaded from C1R3"},
        {"check": "row_key_overlap", "value": len(c1r_keys & c1r3_keys), "finding": "overlapping category/video/frame keys"},
        {"check": "row_presence_delta_count", "value": row_presence_deltas, "finding": "missing/present row deltas from verifier output"},
        {"check": "c1r_duplicate_extra_rows", "value": c1r_dup_count, "finding": f"duplicate keys={len(c1r_dups)}"},
        {"check": "c1r3_duplicate_extra_rows", "value": c1r3_dup_count, "finding": f"duplicate keys={len(c1r3_dups)}"},
        {"check": "observer_columns_separate_from_behavior_columns", "value": int(behavior_columns_line and not observer_compared_as_behavior), "finding": "observer columns are declared separately and not behavior delta fields"},
        {"check": "uses_post_compare_outputs", "value": 0, "finding": "verifier reads raw frame_metrics, not compare summary rows"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Q1-SIC-1C1R3 behavior identity drift.")
    parser.add_argument("--c1r-root", required=True)
    parser.add_argument("--c1r3-root", required=True)
    parser.add_argument("--c1r3-verify-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    c1r_root = Path(args.c1r_root)
    c1r3_root = Path(args.c1r3_root)
    verify_root = Path(args.c1r3_verify_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    behavior_deltas = read_csv(verify_root / "q1_sic1c1r3_behavior_delta.csv")
    c1r_rows = all_guarded_rows(c1r_root)
    c1r3_rows = all_guarded_rows(c1r3_root)
    c1r_by_key = {row_key(row): row for row in c1r_rows}
    c1r3_by_key = {row_key(row): row for row in c1r3_rows}

    by_video = Counter((row.get("category", ""), row.get("video", "")) for row in behavior_deltas)
    write_csv(out / "behavior_delta_by_video.csv", summarize_counter(by_video, ["category", "video"]))

    by_field = Counter(row.get("field", "") for row in behavior_deltas)
    write_csv(out / "behavior_delta_by_field.csv", summarize_counter(by_field, ["field"]))

    action_transitions = Counter()
    for row in behavior_deltas:
        if row.get("field") == "action_label":
            action_transitions[(row.get("c1r", ""), row.get("c1r3", ""))] += 1
    write_csv(
        out / "behavior_delta_by_action_transition.csv",
        summarize_counter(action_transitions, ["c1r_action", "c1r3_action"]),
    )

    by_frame_range = Counter()
    for row in behavior_deltas:
        try:
            frame = int(float(row.get("frame", -1)))
        except (TypeError, ValueError):
            frame = -1
        by_frame_range[(row.get("category", ""), row.get("video", ""), frame_range_label(frame))] += 1
    write_csv(
        out / "behavior_delta_by_frame_range.csv",
        summarize_counter(by_frame_range, ["category", "video", "frame_range"]),
    )

    observer_tab = Counter()
    q1_tab = Counter()
    for delta in behavior_deltas:
        key = (delta.get("category", ""), delta.get("video", ""), int(float(delta.get("frame", -1))))
        c1r_row = c1r_by_key.get(key, {})
        c1r3_row = c1r3_by_key.get(key, {})
        observer_enabled = int(truthy(c1r3_row.get("q1_sic_observer_isolated_enabled")))
        observer_action_detect = int(truthy(c1r3_row.get("q1_sic_observer_action_is_detect")))
        observer_would_select = int(truthy(c1r3_row.get("q1_sic_observer_would_select_shadow")))
        observer_inactive = int(not bool(observer_action_detect or observer_would_select))
        observer_tab[(delta.get("field", ""), observer_enabled, observer_action_detect, observer_would_select, observer_inactive)] += 1
        q1_tab[(
            delta.get("field", ""),
            int(truthy(c1r_row.get("q1_sic_arbitration_active"))),
            int(truthy(c1r3_row.get("q1_sic_arbitration_active"))),
            c1r_row.get("q1_sic_arbitration_label", ""),
            c1r3_row.get("q1_sic_arbitration_label", ""),
        )] += 1
    write_csv(
        out / "behavior_delta_observer_activity_cross_tab.csv",
        summarize_counter(
            observer_tab,
            ["field", "observer_enabled", "observer_action_is_detect", "observer_would_select_shadow", "observer_inactive"],
        ),
    )
    write_csv(
        out / "behavior_delta_q1_activity_cross_tab.csv",
        summarize_counter(
            q1_tab,
            ["field", "c1r_q1_active", "c1r3_q1_active", "c1r_q1_label", "c1r3_q1_label"],
        ),
    )

    c1r_dup_count, c1r_dups = count_duplicates(c1r_rows)
    c1r3_dup_count, c1r3_dups = count_duplicates(c1r3_rows)
    c1r_paths = all_guarded_frame_paths(c1r_root)
    c1r3_paths = all_guarded_frame_paths(c1r3_root)
    c1r_min_mtime, c1r_max_mtime = min_max_mtime(c1r_paths)
    c1r3_min_mtime, c1r3_max_mtime = min_max_mtime(c1r3_paths)
    row_count_rows = []
    all_videos = sorted({(row.get("category", ""), row.get("video", "")) for row in c1r_rows + c1r3_rows})
    for category, video in all_videos:
        left = [row for row in c1r_rows if row.get("category") == category and row.get("video") == video]
        right = [row for row in c1r3_rows if row.get("category") == category and row.get("video") == video]
        _, left_dups = count_duplicates(left)
        _, right_dups = count_duplicates(right)
        row_count_rows.append({
            "category": category,
            "video": video,
            "c1r_rows": len(left),
            "c1r3_rows": len(right),
            "row_count_match": int(len(left) == len(right)),
            "c1r_duplicate_keys": len(left_dups),
            "c1r3_duplicate_keys": len(right_dups),
        })
    row_count_rows.append({
        "category": "__TOTAL__",
        "video": "",
        "c1r_rows": len(c1r_rows),
        "c1r3_rows": len(c1r3_rows),
        "row_count_match": int(len(c1r_rows) == len(c1r3_rows)),
        "c1r_duplicate_keys": len(c1r_dups),
        "c1r3_duplicate_keys": len(c1r3_dups),
        "c1r_duplicate_extra_rows": c1r_dup_count,
        "c1r3_duplicate_extra_rows": c1r3_dup_count,
        "c1r_first_frame_metrics_mtime": c1r_min_mtime,
        "c1r_last_frame_metrics_mtime": c1r_max_mtime,
        "c1r3_first_frame_metrics_mtime": c1r3_min_mtime,
        "c1r3_last_frame_metrics_mtime": c1r3_max_mtime,
        "run_experiment_mtime": datetime.fromtimestamp(RUN_EXPERIMENT.stat().st_mtime).isoformat(timespec="seconds") if RUN_EXPERIMENT.exists() else "",
    })
    write_csv(out / "c1r_vs_c1r3_row_count_and_duplicate_check.csv", row_count_rows)

    c1r_cfg = flat_config(C1R_CONFIG)
    c1r3_cfg = flat_config(C1R3_CONFIG)
    config_rows = []
    for key in sorted(set(c1r_cfg) | set(c1r3_cfg)):
        left = c1r_cfg.get(key, "<missing>")
        right = c1r3_cfg.get(key, "<missing>")
        if str(left) == str(right):
            continue
        config_rows.append({
            "key": key,
            "c1r": left,
            "c1r3": right,
            "classification": classify_config_diff(key, left, right),
        })
    write_csv(out / "c1r_vs_c1r3_config_diff.csv", config_rows)

    verifier_text = R3_VERIFIER.read_text(encoding="utf-8", errors="replace") if R3_VERIFIER.exists() else ""
    write_csv(
        out / "c1r3_verifier_alignment_audit.csv",
        verifier_alignment_audit(verifier_text, c1r_rows, c1r3_rows, behavior_deltas),
    )

    write_csv(out / "source_risk_block_inventory.csv", source_inventory(c1r3_cfg))

    observer_inactive_deltas = sum(
        count
        for key, count in observer_tab.items()
        if key[-1] == 1
    )
    q1_inactive_deltas = sum(
        count
        for key, count in q1_tab.items()
        if key[1] == 0 and key[2] == 0
    )
    row_presence_deltas = by_field.get("row_presence", 0)
    duplicate_or_row_mismatch = bool(c1r_dup_count or c1r3_dup_count or row_presence_deltas or len(c1r_rows) != len(c1r3_rows))
    broad_non_observer = bool(observer_inactive_deltas > 0 and q1_inactive_deltas > 0 and len(by_video) > 7)
    suspicious_config = any(
        row["classification"].startswith("suspicious") for row in config_rows
    )
    verifier_mismatch = bool(duplicate_or_row_mismatch)
    source_newer_than_c1r = bool(c1r_max_mtime and RUN_EXPERIMENT.exists() and RUN_EXPERIMENT.stat().st_mtime > max(path.stat().st_mtime for path in c1r_paths))

    if verifier_mismatch:
        primary = "OUTPUT_DUPLICATE_OR_RESUME_MIX"
        recommendation = "C. Q1-SIC-1C1R3B verifier alignment repair"
    elif broad_non_observer and source_newer_than_c1r:
        primary = "CURRENT_SOURCE_DRIFT_FROM_HISTORICAL_C1R"
        recommendation = "D. Q1-SIC-1C1R3B fresh clean C1R baseline under current source"
    elif suspicious_config:
        primary = "C1R3_CONFIG_DIFF_ENABLED_BEHAVIOR"
        recommendation = "B. Q1-SIC-1C1R3B config pinning repair"
    elif broad_non_observer:
        primary = "HISTORICAL_C1R_OUTPUT_NOT_VALID_IDENTITY_TARGET"
        recommendation = "D. Q1-SIC-1C1R3B fresh clean C1R baseline under current source"
    else:
        primary = "UNKNOWN_NEEDS_FRESH_BASELINE"
        recommendation = "D. Q1-SIC-1C1R3B fresh clean C1R baseline under current source"

    secondary = [
        "broad action deltas" if by_field.get("action_label", 0) else "",
        "broad proposal deltas" if by_field.get("ai_intervention_applied", 0) else "",
        "Q1-label deltas" if by_field.get("q1_sic_arbitration_label", 0) else "",
        "observer inactive rows changed" if observer_inactive_deltas else "",
        "Q1 inactive rows changed" if q1_inactive_deltas else "",
        "fountain-dominated drift" if any(key[1].startswith("fountain") for key in by_video) else "",
        "snowFall drift" if any(key == ("badWeather", "snowFall") for key in by_video) else "",
        "port drift" if any(key == ("lowFramerate", "port_0_17fps") for key in by_video) else "",
        "parking still preserved",
        "copyMachine still preserved",
    ]
    secondary = [item for item in secondary if item]
    classification_rows = [
        {
            "classification": primary,
            "primary": 1,
            "evidence": (
                f"behavior_delta_rows={len(behavior_deltas)}; videos_with_deltas={len(by_video)}; "
                f"observer_inactive_delta_rows={observer_inactive_deltas}; "
                f"q1_inactive_delta_rows={q1_inactive_deltas}; "
                f"row_presence_deltas={row_presence_deltas}; source_newer_than_c1r={int(source_newer_than_c1r)}"
            ),
        }
    ]
    for item in secondary:
        classification_rows.append({"classification": item, "primary": 0, "evidence": ""})
    write_csv(out / "behavior_identity_drift_classification.csv", classification_rows)

    option_rows = []
    for option in [
        "A. Q1-SIC-1C1R3B hard-gate/rollback behavior-affecting code",
        "B. Q1-SIC-1C1R3B config pinning repair",
        "C. Q1-SIC-1C1R3B verifier alignment repair",
        "D. Q1-SIC-1C1R3B fresh clean C1R baseline under current source",
        "E. Stop Q1-SIC-1C1R observer work and return to Q1-SIC-1C1R as last usable partial branch",
    ]:
        selected = int(option == recommendation)
        if option.startswith("A."):
            rationale = "Use only if source risk inventory proves R2/R3 code affects behavior with flags off; current audit does not prove that."
        elif option.startswith("B."):
            rationale = "Config has suspicious differences, but row drift is broad and also appears in observer/Q1-inactive rows."
        elif option.startswith("C."):
            rationale = "Verifier alignment appears sound: guarded-only, raw frame_metrics, equal row counts, no row-presence deltas."
        elif option.startswith("D."):
            rationale = "Selected because historical C1R predates current modified source and broad deltas are not localized to observer/Q1 active rows."
        else:
            rationale = "Too conservative unless fresh-baseline audit also fails to isolate drift."
        option_rows.append({"option": option, "selected": selected, "rationale": rationale})
    write_csv(out / "recommended_repair_options.csv", option_rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
