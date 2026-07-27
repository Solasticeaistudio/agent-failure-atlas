"""Evaluate only explicitly annotated traces; unlabeled traces are excluded."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_failure_atlas.annotations import load_annotations
from agent_failure_atlas.loaders import load_trace_file
from agent_failure_atlas.policy import load_policy
from agent_failure_atlas.scanner import scan_session


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    annotations = load_annotations(args.annotations, args.traces)
    rows = []
    for annotation in annotations:
        if annotation.label.value in {"ambiguous", "excluded"}:
            continue
        trace = next(p for p in args.traces.glob("*.jsonl") if p.stem == annotation.session_id)
        report = scan_session(load_trace_file(trace), load_policy(args.policy))
        predicted = annotation.failure_category in {f.category for f in report.findings}
        expected = annotation.label.value == "positive"
        rows.append({"session_id": annotation.session_id, "category": annotation.failure_category,
                     "expected": expected, "predicted": predicted,
                     "source_type": annotation.source_type})
    tp = sum(row["expected"] and row["predicted"] for row in rows)
    fp = sum(not row["expected"] and row["predicted"] for row in rows)
    fn = sum(row["expected"] and not row["predicted"] for row in rows)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    result = {"labeled_sessions": len(rows), "ambiguous_or_excluded": len(annotations) - len(rows),
              "true_positives": tp, "false_positives": fp, "false_negatives": fn,
              "precision": precision, "recall": recall,
              "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
              "rows": rows,
              "warning": "Metrics cover only reviewed annotations and do not estimate performance on unlabeled traces."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
