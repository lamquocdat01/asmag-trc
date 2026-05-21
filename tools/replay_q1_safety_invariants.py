import argparse
import csv
from pathlib import Path


INPUT_FILES = [
    "port_trajectory_diff.csv",
    "parking_trajectory_diff.csv",
    "carryover_trajectory_diff.csv",
]


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
    except ValueError:
        return str(value).lower() in {"true", "yes", "active"}


def unsafe_action(action):
    text = str(action or "")
    return text.startswith("CLOSED_EMPTY") or "REUSE" in text or "FALLBACK" in text


def classify(row):
    labels = []
    arbitration = "NO_CHANGE"
    invariant = "A"
    owner = row.get("reference_owner", "")

    if row.get("step") != "step4e6":
        return "A. No issue", "NO_CHANGE", "reference_or_context_row"

    is_event_fn = row.get("event_state") == "FN"
    is_normal_like = row.get("event_state") in {"FP", "TN"} or (
        row.get("event_state") not in {"FN", "TP"} and not truthy(row.get("unprotected_fn"))
    )

    if row.get("analysis_group") == "port":
        if truthy(row.get("unprotected_fn")) and unsafe_action(row.get("action_label")):
            labels.extend(["E. final action unsafe", "M. needs detector-retighten arbitration", "N. watch-only"])
            arbitration = "WATCH_ONLY_PORT_RETIGHTEN"
            invariant = "I7"
        elif truthy(row.get("watch_only")):
            labels.append("N. watch-only")
            invariant = "I7"

    if truthy(row.get("report_only_lock")):
        labels.extend(["I. report-only lock", "B. telemetry-only flag but no enforcement"])
        arbitration = "TELEMETRY_ONLY_DO_NOT_COUNT_PASS"
        invariant = "I4"

    if is_normal_like and not is_event_fn:
        if not labels:
            labels.append("A. No issue")
        if arbitration not in {"TELEMETRY_ONLY_DO_NOT_COUNT_PASS", "WATCH_ONLY_PORT_RETIGHTEN"}:
            arbitration = "NO_CHANGE"
        return "; ".join(dict.fromkeys(labels)), arbitration, invariant

    if truthy(row.get("candidate_predicate_false")):
        labels.append("C. candidate predicate false")
        if arbitration == "NO_CHANGE":
            arbitration = "FORCE_RISK_HIGH_RESCUE"
        invariant = "I5"

    if truthy(row.get("active_event_memory_lost")):
        labels.append("F. active_event_memory lost versus reference")
        arbitration = "FORCE_PROTECT_EVENT_MEMORY"
        invariant = "I2"

    if truthy(row.get("risk_high_lost")):
        labels.append("G. risk_high lost versus reference")
        if arbitration == "NO_CHANGE":
            arbitration = "FORCE_RISK_HIGH_RESCUE"
        invariant = "I3"

    if truthy(row.get("guard_active_lost")):
        labels.append("H. guard_active lost versus reference")
        if arbitration == "NO_CHANGE":
            arbitration = "FORCE_PROTECT_EVENT_MEMORY"
        invariant = "I2"

    if truthy(row.get("rescue_active_lost")):
        labels.append("D. action branch not reached")
        if arbitration == "NO_CHANGE":
            arbitration = "FORCE_RISK_HIGH_RESCUE"
        invariant = "I5"

    if truthy(row.get("carryover_lock_lost")):
        labels.append("D. action branch not reached")
        arbitration = "FORCE_CARRYOVER_PROTECTION"
        invariant = "I5"

    if truthy(row.get("unsafe_final_action")) and row.get("analysis_group") != "port":
        labels.extend(["E. final action unsafe", "L. needs event-safety arbitration"])
        if arbitration == "NO_CHANGE":
            arbitration = "FORCE_RISK_HIGH_RESCUE"
        invariant = "I3"

    if truthy(row.get("trajectory_shift")) and not labels:
        labels.append("D. action branch not reached")
        arbitration = "FORCE_RISK_HIGH_RESCUE" if owner == "event_safety" else "FORCE_DETECTOR_CONTEXT_ROW"
        invariant = "I6"

    if row.get("analysis_group") == "port" and truthy(row.get("unprotected_fn")):
        if row.get("frame_id") in {"1350", "1355"}:
            arbitration = "WATCH_ONLY_PORT_RETIGHTEN"
            labels.append("K. split-branch conflict")
            invariant = "I7"
        elif arbitration == "NO_CHANGE":
            arbitration = "FORCE_NO_DETECTOR_HOLDOUT_PROTECTION"

    if not labels:
        labels.append("A. No issue")

    reason = "; ".join(dict.fromkeys(labels))
    return reason, arbitration, invariant


def main():
    parser = argparse.ArgumentParser(description="Replay Q1 safety invariants over trajectory diff CSVs.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    out_dir = Path(args.out)
    candidates = []
    for name in INPUT_FILES:
        for row in read_csv(input_dir / name):
            classification, arbitration, invariant = classify(row)
            if row.get("step") != "step4e6" and classification == "A. No issue":
                continue
            out = dict(row)
            out["source_file"] = name
            out["classification"] = classification
            out["suggested_arbitration"] = arbitration
            out["catching_invariant"] = invariant
            out["would_touch_normal_frame"] = "1" if row.get("event_state") not in {"FN", "TP"} and arbitration not in {"NO_CHANGE", "TELEMETRY_ONLY_DO_NOT_COUNT_PASS", "WATCH_ONLY_PORT_RETIGHTEN"} else "0"
            candidates.append(out)

    summary_counts = {}
    for row in candidates:
        key = (
            row.get("analysis_group", ""),
            row.get("category", ""),
            row.get("video", ""),
            row.get("classification", ""),
            row.get("suggested_arbitration", ""),
            row.get("catching_invariant", ""),
        )
        summary_counts[key] = summary_counts.get(key, 0) + 1
    summary = [
        {
            "analysis_group": k[0],
            "category": k[1],
            "video": k[2],
            "classification": k[3],
            "suggested_arbitration": k[4],
            "catching_invariant": k[5],
            "count": v,
        }
        for k, v in sorted(summary_counts.items())
    ]

    fields = sorted({key for row in candidates for key in row.keys()})
    write_csv(out_dir / "counterfactual_arbitration_candidates.csv", candidates, fields)
    write_csv(
        out_dir / "counterfactual_summary.csv",
        summary,
        ["analysis_group", "category", "video", "classification", "suggested_arbitration", "catching_invariant", "count"],
    )


if __name__ == "__main__":
    main()
