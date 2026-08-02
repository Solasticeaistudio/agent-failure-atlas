import hashlib
import json

import pytest
from pydantic import ValidationError

from agent_failure_atlas.agreement import agreement_summary, consensus_annotations
from agent_failure_atlas.annotations import AnnotationLabel, TraceAnnotation, load_annotations


def _annotation(session_id, category, reviewer, label):
    evidence = {"evidence_start": 0, "evidence_end": 0} if label == "positive" else {}
    return TraceAnnotation(
        session_id=session_id,
        source_type="synthetic",
        failure_category=category,
        reviewer_id=reviewer,
        label=label,
        **evidence,
    )


def test_positive_annotation_requires_evidence():
    with pytest.raises(ValidationError, match="evidence range"):
        TraceAnnotation(
            session_id="trace-1",
            source_type="synthetic",
            failure_category="scope_violation",
            reviewer_id="reviewer-a",
            label="positive",
        )


def test_agreement_and_unanimous_consensus():
    annotations = [
        _annotation("trace-1", "scope_violation", "reviewer-a", "positive"),
        _annotation("trace-1", "scope_violation", "reviewer-b", "positive"),
        _annotation("trace-2", "scope_violation", "reviewer-a", "positive"),
        _annotation("trace-2", "scope_violation", "reviewer-b", "negative"),
    ]
    summary = agreement_summary(annotations)
    consensus, consensus_summary = consensus_annotations(annotations)

    assert summary["reviewed_items"] == 2
    assert summary["observed_agreement"] == 0.5
    assert summary["fleiss_kappa"] == pytest.approx(-0.3333)
    assert len(summary["conflicts"]) == 1
    assert consensus_summary == summary
    assert [(item.session_id, item.label) for item in consensus] == [
        ("trace-1", AnnotationLabel.POSITIVE)
    ]


def test_real_trace_annotations_require_matching_digest(root, tmp_path):
    trace = root / "examples" / "traces" / "safe_trace.jsonl"
    digest = hashlib.sha256(trace.read_bytes()).hexdigest()
    annotation_path = tmp_path / "annotations.jsonl"
    annotation_path.write_text(
        json.dumps(
            {
                "session_id": "safe-trace",
                "source_type": "real",
                "failure_category": "scope_violation",
                "label": "negative",
                "reviewer_id": "reviewer-a",
                "trace_sha256": digest,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert load_annotations(annotation_path, trace.parent)[0].trace_sha256 == digest

    annotation_path.write_text(
        annotation_path.read_text(encoding="utf-8").replace(digest, "0" * 64),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="digest mismatch"):
        load_annotations(annotation_path, trace.parent)


def test_duplicate_reviewer_annotation_is_rejected(root, tmp_path):
    row = {
        "session_id": "safe-trace",
        "source_type": "synthetic",
        "failure_category": "scope_violation",
        "label": "negative",
        "reviewer_id": "reviewer-a",
    }
    annotation_path = tmp_path / "annotations.jsonl"
    annotation_path.write_text(
        json.dumps(row) + "\n" + json.dumps(row) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate reviewer"):
        load_annotations(annotation_path, root / "examples" / "traces")
