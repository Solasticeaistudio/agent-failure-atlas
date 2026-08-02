"""Evaluate detector output only against independently reviewed consensus labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_failure_atlas.agreement import consensus_annotations
from agent_failure_atlas.annotations import AnnotationLabel, load_annotations
from agent_failure_atlas.loaders import load_trace_file
from agent_failure_atlas.policy import load_policy
from agent_failure_atlas.scanner import scan_session


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--minimum-reviewers", type=int, default=2)
    args = parser.parse_args()

    annotations = load_annotations(args.annotations, args.traces)
    consensus, agreement = consensus_annotations(
        annotations, minimum_reviewers=args.minimum_reviewers
    )
    traces = {}
    for path in sorted(args.traces.glob("*.jsonl")):
        session = load_trace_file(path)
        traces[session.id] = session

    rows = []
    policy = load_policy(args.policy)
    for annotation in consensus:
        report = scan_session(traces[annotation.session_id], policy)
        predicted = annotation.failure_category in {
            finding.category for finding in report.findings
        }
        expected = annotation.label == AnnotationLabel.POSITIVE
        rows.append(
            {
                "session_id": annotation.session_id,
                "category": annotation.failure_category,
                "expected": expected,
                "predicted": predicted,
                "source_type": annotation.source_type,
                "review_round": annotation.review_round,
                "reviewer_ids": list(annotation.reviewer_ids),
            }
        )

    tp = sum(row["expected"] and row["predicted"] for row in rows)
    fp = sum(not row["expected"] and row["predicted"] for row in rows)
    fn = sum(row["expected"] and not row["predicted"] for row in rows)
    tn = sum(not row["expected"] and not row["predicted"] for row in rows)
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    result = {
        "annotation_schema_version": "2",
        "reviewed_annotations": len(annotations),
        "consensus_labels": len(rows),
        "minimum_reviewers": args.minimum_reviewers,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "agreement": agreement,
        "rows": rows,
        "warning": (
            "Metrics cover only unanimous independently reviewed labels and do not "
            "estimate performance on unlabeled traces."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
