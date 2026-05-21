import argparse
import csv
from pathlib import Path


PARKING_FRAMES = {"1195", "1310", "1315", "1320", "1425", "1430", "1435", "1440", "1445"}
PORT_WATCH_FRAMES = {"1350", "1355"}
EVENT_SAFETY_LABELS = {
    "FORCE_PROTECT_EVENT_MEMORY",
    "FORCE_RISK_HIGH_RESCUE",
    "FORCE_CARRYOVER_PROTECTION",
}
PORT_LABELS = {
    "WATCH_ONLY_PORT_RETIGHTEN",
}
ALLOWED_LABELS = EVENT_SAFETY_LABELS | PORT_LABELS | {
    "TELEMETRY_ONLY_DO_NOT_COUNT_PASS",
    "NO_CHANGE",
}


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def truthy(value):
    if value in (None, "", "NA"):
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return str(value).lower() in {"true", "yes", "active"}


def check_pass(condition):
    return "1" if condition else "0"


def main():
    parser = argparse.ArgumentParser(description="Verify Q1-SIC-1 shadow arbitration on Q1-SIC-0 replay output.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    out_dir = Path(args.out)
    candidates = read_csv(input_dir / "counterfactual_arbitration_candidates.csv")
    parking_rows = [
        r for r in candidates
        if r.get("analysis_group") == "parking" and r.get("frame_id") in PARKING_FRAMES
    ]
    port_rows = [
        r for r in candidates
        if r.get("analysis_group") == "port" and r.get("frame_id") in PORT_WATCH_FRAMES
    ]
    snow_lake_rows = [
        r for r in candidates
        if (r.get("category"), r.get("video")) in {("badWeather", "snowFall"), ("thermal", "lakeSide")}
    ]

    parking_caught_frames = {
        r.get("frame_id")
        for r in parking_rows
        if r.get("suggested_arbitration") in EVENT_SAFETY_LABELS
    }
    port_watch_frames = {
        r.get("frame_id")
        for r in port_rows
        if r.get("suggested_arbitration") == "WATCH_ONLY_PORT_RETIGHTEN"
    }
    report_only_rows = [
        r for r in snow_lake_rows
        if "report-only" in r.get("classification", "")
        or "telemetry-only flag but no enforcement" in r.get("classification", "")
        or r.get("suggested_arbitration") == "TELEMETRY_ONLY_DO_NOT_COUNT_PASS"
    ]
    report_only_not_counted = bool(report_only_rows) and all(
        r.get("suggested_arbitration") == "TELEMETRY_ONLY_DO_NOT_COUNT_PASS"
        or r.get("suggested_arbitration") in EVENT_SAFETY_LABELS
        for r in report_only_rows
    )
    would_touch_normal_frame = max(
        [int(truthy(r.get("would_touch_normal_frame"))) for r in candidates] or [0]
    )
    no_forbidden_detector_labels = all(
        r.get("suggested_arbitration") not in {
            "FORCE_DETECTOR_CONTEXT_ROW",
            "FORCE_NO_DETECTOR_HOLDOUT_PROTECTION",
        }
        for r in candidates
    )
    labels_allowed = all(r.get("suggested_arbitration", "NO_CHANGE") in ALLOWED_LABELS for r in candidates)
    port_only_watch = all(r.get("suggested_arbitration") in PORT_LABELS or r.get("suggested_arbitration") == "NO_CHANGE" for r in port_rows)
    split_branch_ok = bool(no_forbidden_detector_labels and labels_allowed and port_only_watch)

    parking_failures_caught = parking_caught_frames == PARKING_FRAMES
    port_1350_1355_watch_only = port_watch_frames == PORT_WATCH_FRAMES
    known_step4e6_failures_caught = bool(
        parking_failures_caught
        and port_1350_1355_watch_only
        and report_only_not_counted
        and would_touch_normal_frame == 0
        and split_branch_ok
    )

    verdict_rows = []
    for frame in sorted(PARKING_FRAMES, key=int):
        row = next((r for r in parking_rows if r.get("frame_id") == frame), {})
        verdict_rows.append({
            "check": "parking_known_failure",
            "category": "intermittentObjectMotion",
            "video": "parking",
            "frame_id": frame,
            "observed_label": row.get("suggested_arbitration", "MISSING"),
            "expected_label": "FORCE_PROTECT_EVENT_MEMORY",
            "passed": check_pass(row.get("suggested_arbitration") in EVENT_SAFETY_LABELS),
            "details": row.get("classification", ""),
        })
    for frame in sorted(PORT_WATCH_FRAMES, key=int):
        row = next((r for r in port_rows if r.get("frame_id") == frame), {})
        verdict_rows.append({
            "check": "port_watch_only",
            "category": "lowFramerate",
            "video": "port_0_17fps",
            "frame_id": frame,
            "observed_label": row.get("suggested_arbitration", "MISSING"),
            "expected_label": "WATCH_ONLY_PORT_RETIGHTEN",
            "passed": check_pass(row.get("suggested_arbitration") == "WATCH_ONLY_PORT_RETIGHTEN"),
            "details": row.get("classification", ""),
        })
    for category, video in [("badWeather", "snowFall"), ("thermal", "lakeSide")]:
        rows = [r for r in report_only_rows if r.get("category") == category and r.get("video") == video]
        verdict_rows.append({
            "check": "report_only_not_counted_as_pass",
            "category": category,
            "video": video,
            "frame_id": "",
            "observed_label": "TELEMETRY_ONLY_DO_NOT_COUNT_PASS",
            "expected_label": "TELEMETRY_ONLY_DO_NOT_COUNT_PASS",
            "passed": check_pass(bool(rows)),
            "details": f"report_only_rows={len(rows)}",
        })

    summary = [{
        "known_step4e6_failures_caught": int(known_step4e6_failures_caught),
        "parking_failures_caught": int(parking_failures_caught),
        "parking_frames_caught": len(parking_caught_frames),
        "port_1350_1355_watch_only": int(port_1350_1355_watch_only),
        "report_only_not_counted_as_pass": int(report_only_not_counted),
        "report_only_rows_checked": len(report_only_rows),
        "would_touch_normal_frame": int(would_touch_normal_frame),
        "split_branch_ok": int(split_branch_ok),
        "candidate_rows_checked": len(candidates),
        "decision": "PASS_SHADOW" if known_step4e6_failures_caught else "FAIL_SHADOW",
    }]

    write_csv(
        out_dir / "shadow_arbitration_verdict.csv",
        verdict_rows,
        ["check", "category", "video", "frame_id", "observed_label", "expected_label", "passed", "details"],
    )
    write_csv(
        out_dir / "shadow_arbitration_summary.csv",
        summary,
        [
            "known_step4e6_failures_caught",
            "parking_failures_caught",
            "parking_frames_caught",
            "port_1350_1355_watch_only",
            "report_only_not_counted_as_pass",
            "report_only_rows_checked",
            "would_touch_normal_frame",
            "split_branch_ok",
            "candidate_rows_checked",
            "decision",
        ],
    )


if __name__ == "__main__":
    main()
