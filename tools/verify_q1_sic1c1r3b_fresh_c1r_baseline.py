"""Verify Q1-SIC-1C1R3B fresh C1R baseline and same-source observer identity."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml


PIPELINE = "ASMAG_TR_CONTROLLER_ONLINE_GUARDED"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_C1R_CONFIG = PROJECT_ROOT / "configs" / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r_restore_copy_port_subset_dryrun.yaml"
FRESH_C1R_CONFIG = PROJECT_ROOT / "configs" / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3b_fresh_c1r_baseline_subset_dryrun.yaml"
C1R3_CONFIG = PROJECT_ROOT / "configs" / "asmag_tr_controller_online_guarded_cdnet_q1_sic1c1r3_observer_isolation_subset_dryrun.yaml"

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
NUMERIC_COLUMNS = {
    "yolo_called",
    "ai_intervention_detector_requested",
    "ai_intervention_applied",
    "q1_sic_arbitration_active",
    "q1_sic_watch_only",
}


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


def norm(value: object, numeric: bool = False) -> str:
    if value in (None, "NA"):
        return ""
    text = str(value).strip()
    if numeric and text != "":
        return "1" if number(text) > 0 else "0"
    return text


def frame(row: Dict[str, str]) -> int:
    for key in ("raw_frame_id", "frame_id", "frame", "frame_idx"):
        if row.get(key) not in (None, ""):
            return int(float(row[key]))
    return -1


def row_key(row: Dict[str, str]) -> Tuple[str, str, int, str]:
    return (
        row.get("category", ""),
        row.get("video", ""),
        frame(row),
        row.get("pipeline", PIPELINE),
    )


def guarded_path(root: Path, video: Sequence[str]) -> Path:
    return root / "raw_results" / video[0] / video[1] / PIPELINE / "frame_metrics.csv"


def load_video(root: Path, video: Sequence[str]) -> List[Dict[str, str]]:
    return read_csv(guarded_path(root, video))


def by_frame(rows: Iterable[Dict[str, str]]) -> Dict[int, Dict[str, str]]:
    return {frame(row): row for row in rows}


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
    return bool(is_fn(row) and (truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested"))))


def unprotected(row: Dict[str, str]) -> bool:
    if not row:
        return False
    if truthy(row.get("unprotected_fn")) or row.get("q1_sic_post_protection_label") == "unprotected_fn":
        return True
    return bool(is_fn(row) and not protected(row))


def normal_intervention(row: Dict[str, str]) -> bool:
    return bool(is_normal(row) and (truthy(row.get("ai_intervention_applied")) or truthy(row.get("ai_intervention_detector_requested"))))


def max_col(rows: List[Dict[str, str]], column: str) -> float:
    return max([number(row.get(column)) for row in rows] or [0.0])


def count_duplicates(rows: List[Dict[str, str]]) -> Tuple[int, int]:
    counts = Counter(row_key(row) for row in rows)
    duplicate_keys = [count for count in counts.values() if count > 1]
    return len(duplicate_keys), sum(count - 1 for count in duplicate_keys)


def compare_behavior(
    left_rows: List[Dict[str, str]],
    right_rows: List[Dict[str, str]],
    left_label: str,
    right_label: str,
) -> List[Dict[str, object]]:
    left = {row_key(row): row for row in left_rows}
    right = {row_key(row): row for row in right_rows}
    deltas: List[Dict[str, object]] = []
    for key in sorted(set(left) | set(right)):
        lrow = left.get(key, {})
        rrow = right.get(key, {})
        if not lrow or not rrow:
            deltas.append({
                "category": key[0],
                "video": key[1],
                "frame": key[2],
                "pipeline": key[3],
                "field": "row_presence",
                left_label: "present" if lrow else "missing",
                right_label: "present" if rrow else "missing",
            })
            continue
        for column in BEHAVIOR_COLUMNS:
            lval = norm(lrow.get(column, ""), column in NUMERIC_COLUMNS)
            rval = norm(rrow.get(column, ""), column in NUMERIC_COLUMNS)
            if lval != rval:
                deltas.append({
                    "category": key[0],
                    "video": key[1],
                    "frame": key[2],
                    "pipeline": key[3],
                    "field": column,
                    left_label: lrow.get(column, ""),
                    right_label: rrow.get(column, ""),
                })
        derived = [
            ("protected_fn_accounting", int(protected(lrow)), int(protected(rrow))),
            ("unprotected_fn_accounting", int(unprotected(lrow)), int(unprotected(rrow))),
            ("normal_frame_intervention_indicator", int(normal_intervention(lrow)), int(normal_intervention(rrow))),
        ]
        for field, lval, rval in derived:
            if lval != rval:
                deltas.append({
                    "category": key[0],
                    "video": key[1],
                    "frame": key[2],
                    "pipeline": key[3],
                    "field": field,
                    left_label: lval,
                    right_label: rval,
                })
    return deltas


def summarize_deltas(deltas: List[Dict[str, object]], left_rows: List[Dict[str, str]], right_rows: List[Dict[str, str]]) -> Dict[str, object]:
    by_field = Counter(str(row.get("field", "")) for row in deltas)
    left_dup_keys, left_dup_extra = count_duplicates(left_rows)
    right_dup_keys, right_dup_extra = count_duplicates(right_rows)
    left_keys = {row_key(row) for row in left_rows}
    right_keys = {row_key(row) for row in right_rows}
    return {
        "left_guarded_rows": len(left_rows),
        "right_guarded_rows": len(right_rows),
        "row_count_match": int(len(left_rows) == len(right_rows)),
        "overlapping_keys": len(left_keys & right_keys),
        "row_presence_deltas": by_field.get("row_presence", 0),
        "left_duplicate_keys": left_dup_keys,
        "left_duplicate_extra_rows": left_dup_extra,
        "right_duplicate_keys": right_dup_keys,
        "right_duplicate_extra_rows": right_dup_extra,
        "behavior_delta_rows": len(deltas),
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
    }


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


def config_diff(left_path: Path, right_path: Path, left_label: str, right_label: str) -> List[Dict[str, object]]:
    left = flat_config(left_path)
    right = flat_config(right_path)
    rows = []
    for key in sorted(set(left) | set(right)):
        lval = left.get(key, "")
        rval = right.get(key, "")
        if str(lval) == str(rval):
            continue
        if key in {"experiment_name", "edge_profile.name", "output_root"}:
            classification = "intended output-root/name change"
        elif key == "resume_existing_results":
            classification = "progress/output identifier"
        elif key.endswith("q1_sic_observer_isolated_enabled"):
            classification = "observer enable flag"
        elif key.endswith("q1_sic_detector_action_probe_enabled"):
            classification = "detector-action probe semantic difference"
        elif key.endswith("q1_sic_detector_action_probe_stable_snapshot_enabled"):
            classification = "stable snapshot explicit disable"
        elif "q1_sic" in key or "detector" in key or "protection" in key:
            classification = "behavior-sensitive config difference"
        else:
            classification = "unknown"
        rows.append({"key": key, left_label: lval, right_label: rval, "classification": classification})
    return rows


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
        "fresh_c1r_execution_ok": int(len(rows) == 56 and completed == 56 and failed == 0 and compare_completed),
    }


def local_gate_summary(fresh_root: Path, historical_root: Path) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    fresh_all = all_guarded_rows(fresh_root)
    fresh_parking = load_video(fresh_root, PARKING)
    historical_parking = load_video(historical_root, PARKING)
    fresh_parking_summary = video_summary(fresh_root, *PARKING)
    historical_parking_summary = video_summary(historical_root, *PARKING)
    fresh_parking_proposal = number(fresh_parking_summary.get("intervention_rate"), rate(fresh_parking, "ai_intervention_applied"))
    historical_parking_proposal = number(historical_parking_summary.get("intervention_rate"), rate(historical_parking, "ai_intervention_applied"))
    fresh_parking_detector = number(fresh_parking_summary.get("detector_request_rate"), rate(fresh_parking, "ai_intervention_detector_requested"))
    fresh_parking_unprotected = sum(int(unprotected(row)) for row in fresh_parking)
    parking_ok = int(
        fresh_parking_unprotected == 0
        and fresh_parking_detector == 0.0
        and fresh_parking_proposal <= historical_parking_proposal + 0.0001
    )

    row_checks: List[Dict[str, object]] = []
    copy_rows = by_frame(load_video(fresh_root, COPY))
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

    port_rows = by_frame(load_video(fresh_root, PORT))
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
        for row in read_csv(fresh_root / "ai_intervention_video_summary.csv")
    )
    q1_touch_max = max_col(fresh_all, "q1_sic_would_touch_normal_frame")
    gt_decision_max = max_col(fresh_all, "q1_sic_gt_signal_used_for_decision")
    normal_ok = int(normal_frame_interventions == 0 and q1_touch_max == 0 and gt_decision_max == 0)
    q1b_proxy_rows = sum(int(truthy(row.get("q1_sic_event_risk_empty_detect_proxy"))) for row in fresh_all)
    q1b_label_rows = sum(
        int(row.get("q1_sic_arbitration_label") == "FORCE_EVENT_RISK_EMPTY_DETECT_PROTECTION")
        for row in fresh_all
    )
    snow_enforcement_ok = int(q1b_proxy_rows == 0 and q1b_label_rows == 0)
    local_ok = int(all([parking_ok, copy_ok, port_ok, no_port_enforce_ok, normal_ok, snow_enforcement_ok]))
    return {
        "parking_preserved_ok": parking_ok,
        "historical_parking_proposal": f"{historical_parking_proposal:.5f}",
        "fresh_parking_proposal": f"{fresh_parking_proposal:.5f}",
        "fresh_parking_detector": f"{fresh_parking_detector:.5f}",
        "fresh_parking_unprotected_fn": fresh_parking_unprotected,
        "copyMachine_preserved_ok": copy_ok,
        "port_watch_preserved_ok": port_ok,
        "no_port_retighten_enforcement_ok": no_port_enforce_ok,
        "normal_safety_ok": normal_ok,
        "normal_frame_interventions": normal_frame_interventions,
        "q1_sic_would_touch_normal_frame_max": q1_touch_max,
        "q1_sic_gt_signal_used_for_decision_max": gt_decision_max,
        "no_snowfall_enforcement_ok": snow_enforcement_ok,
        "q1_sic1b_proxy_active_rows": q1b_proxy_rows,
        "q1_sic1b_enforcement_label_rows": q1b_label_rows,
        "fresh_c1r_preserves_required_local_gates": local_ok,
    }, row_checks


def classification_rows(
    decision: str,
    fresh_exec_ok: int,
    local_ok: int,
    alignment_ok: int,
    hist_deltas: int,
    same_source_deltas: int,
    gate: Dict[str, object],
) -> List[Dict[str, object]]:
    rows = [
        {"classification": "fresh baseline cannot reproduce local gates", "is_primary": int(decision == "FAIL_FRESH_C1R_BASELINE"), "evidence": f"local_gates_ok={local_ok}"},
        {"classification": "same-source observer identity still fails", "is_primary": int(decision == "FAIL_SAME_SOURCE_OBSERVER_IDENTITY"), "evidence": f"fresh_c1r_vs_c1r3_deltas={same_source_deltas}"},
        {"classification": "historical C1R invalid but fresh baseline ok", "is_primary": int(decision == "PASS_FRESH_BASELINE_HISTORICAL_C1R_INVALID"), "evidence": f"historical_vs_fresh_deltas={hist_deltas}"},
        {"classification": "config mismatch", "is_primary": 0, "evidence": "see config diff CSVs"},
        {"classification": "verifier mismatch", "is_primary": int(decision == "FAIL_VERIFIER_OR_ALIGNMENT"), "evidence": f"alignment_ok={alignment_ok}"},
        {"classification": "normal-frame safety violation", "is_primary": 0, "evidence": f"normal_safety_ok={gate.get('normal_safety_ok', '')}"},
        {"classification": "GT leakage", "is_primary": 0, "evidence": f"q1_sic_gt_signal_used_for_decision_max={gate.get('q1_sic_gt_signal_used_for_decision_max', '')}"},
        {"classification": "parking regression", "is_primary": 0, "evidence": f"parking_preserved_ok={gate.get('parking_preserved_ok', '')}"},
        {"classification": "copyMachine regression", "is_primary": 0, "evidence": f"copyMachine_preserved_ok={gate.get('copyMachine_preserved_ok', '')}"},
        {"classification": "port watch regression", "is_primary": 0, "evidence": f"port_watch_preserved_ok={gate.get('port_watch_preserved_ok', '')}"},
        {"classification": "unintended snowFall enforcement", "is_primary": 0, "evidence": f"no_snowfall_enforcement_ok={gate.get('no_snowfall_enforcement_ok', '')}"},
        {"classification": "unintended port retighten", "is_primary": 0, "evidence": f"no_port_retighten_enforcement_ok={gate.get('no_port_retighten_enforcement_ok', '')}"},
    ]
    if not fresh_exec_ok:
        rows.insert(0, {"classification": "fresh baseline execution incomplete", "is_primary": int(decision == "FAIL_FRESH_C1R_BASELINE"), "evidence": f"fresh_c1r_execution_ok={fresh_exec_ok}"})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1C1R3B fresh C1R baseline.")
    parser.add_argument("--historical-c1r-root", required=True)
    parser.add_argument("--fresh-c1r-root", required=True)
    parser.add_argument("--c1r3-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    historical_root = Path(args.historical_c1r_root)
    fresh_root = Path(args.fresh_c1r_root)
    c1r3_root = Path(args.c1r3_root)
    out = Path(args.out)

    historical_rows = all_guarded_rows(historical_root)
    fresh_rows = all_guarded_rows(fresh_root)
    c1r3_rows = all_guarded_rows(c1r3_root)

    historical_vs_fresh = compare_behavior(historical_rows, fresh_rows, "historical_c1r", "fresh_c1r")
    fresh_vs_c1r3 = compare_behavior(fresh_rows, c1r3_rows, "fresh_c1r", "c1r3")
    write_csv(out / "historical_c1r_vs_fresh_c1r_behavior_delta.csv", historical_vs_fresh)
    write_csv(out / "fresh_c1r_vs_c1r3_behavior_delta.csv", fresh_vs_c1r3)

    hist_summary = summarize_deltas(historical_vs_fresh, historical_rows, fresh_rows)
    same_source_summary = summarize_deltas(fresh_vs_c1r3, fresh_rows, c1r3_rows)
    hist_summary["comparison"] = "historical_c1r_vs_fresh_c1r"
    same_source_summary["comparison"] = "fresh_c1r_vs_c1r3"
    hist_summary["historical_c1r_reproducibility_assessment"] = (
        "reproducible" if hist_summary["behavior_delta_rows"] == 0 else "not_valid_for_current_source_identity"
    )
    same_source_summary["same_source_observer_identity_assessment"] = (
        "passes" if same_source_summary["behavior_delta_rows"] == 0 else "fails"
    )
    write_csv(out / "historical_c1r_vs_fresh_c1r_summary.csv", [hist_summary])
    write_csv(out / "fresh_c1r_vs_c1r3_summary.csv", [same_source_summary])

    write_csv(
        out / "config_diff_historical_c1r_vs_fresh_c1r.csv",
        config_diff(HISTORICAL_C1R_CONFIG, FRESH_C1R_CONFIG, "historical_c1r", "fresh_c1r"),
    )
    write_csv(
        out / "config_diff_fresh_c1r_vs_c1r3.csv",
        config_diff(FRESH_C1R_CONFIG, C1R3_CONFIG, "fresh_c1r", "c1r3"),
    )

    execution = progress_summary(fresh_root)
    gate, row_checks = local_gate_summary(fresh_root, historical_root)
    write_csv(out / "fresh_c1r_baseline_row_checks.csv", row_checks)

    align_ok = int(
        hist_summary["row_count_match"]
        and same_source_summary["row_count_match"]
        and hist_summary["row_presence_deltas"] == 0
        and same_source_summary["row_presence_deltas"] == 0
        and hist_summary["left_duplicate_extra_rows"] == 0
        and hist_summary["right_duplicate_extra_rows"] == 0
        and same_source_summary["right_duplicate_extra_rows"] == 0
    )
    local_ok = int(gate["fresh_c1r_preserves_required_local_gates"])
    execution_ok = int(execution["fresh_c1r_execution_ok"])
    hist_deltas = int(hist_summary["behavior_delta_rows"])
    same_source_deltas = int(same_source_summary["behavior_delta_rows"])

    if not align_ok:
        decision = "FAIL_VERIFIER_OR_ALIGNMENT"
    elif not execution_ok or not local_ok:
        decision = "FAIL_FRESH_C1R_BASELINE"
    elif same_source_deltas == 0 and hist_deltas == 0:
        decision = "PASS_FRESH_BASELINE_AND_OBSERVER_IDENTITY"
    elif same_source_deltas == 0 and hist_deltas > 0:
        decision = "PASS_FRESH_BASELINE_HISTORICAL_C1R_INVALID"
    else:
        decision = "FAIL_SAME_SOURCE_OBSERVER_IDENTITY"

    gate_summary = {
        **execution,
        **gate,
        "verifier_alignment_ok": align_ok,
        "historical_c1r_behavior_delta_rows": hist_deltas,
        "fresh_c1r_vs_c1r3_behavior_delta_rows": same_source_deltas,
        "decision": decision,
    }
    write_csv(out / "fresh_c1r_baseline_gate_summary.csv", [gate_summary])
    write_csv(
        out / "q1_sic1c1r3b_failure_classification.csv",
        classification_rows(decision, execution_ok, local_ok, align_ok, hist_deltas, same_source_deltas, gate),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
