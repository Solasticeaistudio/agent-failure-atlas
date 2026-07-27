"""Validated reviewer annotations for real-trace evaluation."""
from __future__ import annotations

import json
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
    session_id: str
    source_type: str
    failure_category: str | None = None
    label: AnnotationLabel
    evidence_start: int | None = Field(default=None, ge=0)
    evidence_end: int | None = Field(default=None, ge=0)
    reviewer_notes: str = ""
    ambiguous: bool = False
    annotation_schema_version: str = "1"

    @model_validator(mode="after")
    def validate_range(self) -> TraceAnnotation:
        if (self.evidence_start is None) != (self.evidence_end is None):
            raise ValueError("evidence_start and evidence_end must be supplied together")
        if self.evidence_start is not None and self.evidence_end < self.evidence_start:
            raise ValueError("evidence_end must not precede evidence_start")
        return self


def load_annotations(path: str | Path, traces: str | Path) -> list[TraceAnnotation]:
    annotations = [TraceAnnotation.model_validate(json.loads(line))
                   for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    available = {load_trace_file(p).id for p in Path(traces).glob("*.jsonl")}
    for annotation in annotations:
        if annotation.session_id not in available:
            raise ValueError(f"Annotation references unknown trace: {annotation.session_id}")
        if annotation.evidence_end is not None:
            report = load_trace_file(next(p for p in Path(traces).glob("*.jsonl")
                                          if p.stem == annotation.session_id or load_trace_file(p).id == annotation.session_id))
            if annotation.evidence_end >= len(report.messages):
                raise ValueError(f"Evidence range exceeds trace: {annotation.session_id}")
    return annotations
