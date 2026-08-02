"""Validated reviewer annotations for real-trace evaluation."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from .loaders import load_trace_file


class AnnotationLabel(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    AMBIGUOUS = "ambiguous"
    EXCLUDED = "excluded"


class TraceAnnotation(BaseModel):
    session_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    failure_category: str | None = None
    label: AnnotationLabel
    reviewer_id: str = Field(min_length=1)
    review_round: str = Field(default="initial", min_length=1)
    reviewed_at: datetime | None = None
    trace_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence_start: int | None = Field(default=None, ge=0)
    evidence_end: int | None = Field(default=None, ge=0)
    reviewer_notes: str = ""
    ambiguous: bool = False
    annotation_schema_version: str = "2"

    @model_validator(mode="after")
    def validate_annotation(self) -> TraceAnnotation:
        if (self.evidence_start is None) != (self.evidence_end is None):
            raise ValueError("evidence_start and evidence_end must be supplied together")
        if self.evidence_start is not None and self.evidence_end < self.evidence_start:
            raise ValueError("evidence_end must not precede evidence_start")
        if self.label in {AnnotationLabel.POSITIVE, AnnotationLabel.NEGATIVE}:
            if not self.failure_category:
                raise ValueError("positive and negative annotations require failure_category")
        if self.label == AnnotationLabel.POSITIVE and self.evidence_start is None:
            raise ValueError("positive annotations require an evidence range")
        if self.ambiguous and self.label != AnnotationLabel.AMBIGUOUS:
            raise ValueError("ambiguous=true requires label=ambiguous")
        return self


def load_annotations(path: str | Path, traces: str | Path) -> list[TraceAnnotation]:
    annotations = [
        TraceAnnotation.model_validate(json.loads(line))
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    trace_index: dict[str, tuple[Path, int, str]] = {}
    for trace_path in sorted(Path(traces).glob("*.jsonl")):
        session = load_trace_file(trace_path)
        if session.id in trace_index:
            raise ValueError(f"Duplicate trace session ID: {session.id}")
        trace_index[session.id] = (
            trace_path,
            len(session.messages),
            hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        )

    seen: set[tuple[str, str | None, str, str]] = set()
    for annotation in annotations:
        if annotation.session_id not in trace_index:
            raise ValueError(f"Annotation references unknown trace: {annotation.session_id}")
        key = (
            annotation.session_id,
            annotation.failure_category,
            annotation.reviewer_id,
            annotation.review_round,
        )
        if key in seen:
            raise ValueError(
                "Duplicate reviewer annotation for "
                f"{annotation.session_id}/{annotation.failure_category}"
            )
        seen.add(key)

        _, message_count, digest = trace_index[annotation.session_id]
        if annotation.evidence_end is not None and annotation.evidence_end >= message_count:
            raise ValueError(f"Evidence range exceeds trace: {annotation.session_id}")
        if annotation.source_type.lower() == "real" and not annotation.trace_sha256:
            raise ValueError("Real-trace annotations require trace_sha256")
        if annotation.trace_sha256 and annotation.trace_sha256 != digest:
            raise ValueError(f"Trace digest mismatch: {annotation.session_id}")
    return annotations
