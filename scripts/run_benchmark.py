"""Run the deterministic synthetic benchmark with per-category metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_failure_atlas.loaders import load_trace_file
from agent_failure_atlas.policy import load_policy
from agent_failure_atlas.scanner import scan_session

ROOT = Path(__file__).resolve().parents[1]


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def run(traces: Path, labels_path: Path, policy_path: Path) -> dict:
    labels = {r["session_id"]: set(r["expected_categories"])
              for r in map(json.loads, labels_path.read_text(encoding="utf-8").splitlines())}
    rows = []
    categories = sorted({c for values in labels.values() for c in values} | {"none"})
    stats = {c: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for c in categories}
    for trace in sorted(traces.glob("*.jsonl")):
        if trace.name == "labels.jsonl":
            continue
        report = scan_session(load_trace_file(trace), load_policy(policy_path))
        expected = labels.get(report.session.id, set())
        predicted = {finding.category for finding in report.findings}
        for category in categories:
            stats[category]["tp"] += int(category in expected and category in predicted)
            stats[category]["fp"] += int(category not in expected and category in predicted)
            stats[category]["fn"] += int(category in expected and category not in predicted)
            stats[category]["tn"] += int(category not in expected and category not in predicted)
        rows.append({"session_id": report.session.id, "expected": sorted(expected),
                     "predicted": sorted(predicted), "pass": expected == predicted})
    metrics = {}
    for category, values in stats.items():
        precision = (values["tp"] / (values["tp"] + values["fp"])
                     if values["tp"] + values["fp"] else 1.0)
        recall = (values["tp"] / (values["tp"] + values["fn"])
                  if values["tp"] + values["fn"] else 1.0)
        metrics[category] = {**values, "precision": round(precision, 4), "recall": round(recall, 4),
                             "f1": round(_f1(precision, recall), 4)}
    totals = {key: sum(values[key] for values in stats.values()) for key in ("tp", "fp", "fn")}
    precision = totals["tp"] / (totals["tp"] + totals["fp"]) if totals["tp"] + totals["fp"] else 1.0
    recall = totals["tp"] / (totals["tp"] + totals["fn"]) if totals["tp"] + totals["fn"] else 1.0
    return {"scope": "synthetic deterministic smoke benchmark", "sessions": rows,
            "true_positives": totals["tp"], "false_positives": totals["fp"],
            "false_negatives": totals["fn"], "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(_f1(precision, recall), 4),
            "per_category": metrics, "confusion": stats,
            "warning": ("Synthetic fixtures validate implemented detector behavior only; "
                        "they are not evidence of real-world accuracy.")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", type=Path, default=ROOT / "benchmark" / "synthetic")
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--policy", type=Path, default=ROOT / "examples" / "policy.yaml")
    parser.add_argument("--out", type=Path, default=ROOT / "benchmark" / "results.json")
    args = parser.parse_args()
    labels = args.labels or args.traces / "labels.jsonl"
    result = run(args.traces, labels, args.policy)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
