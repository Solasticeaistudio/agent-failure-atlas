import json

import pytest

from agent_failure_atlas.adapters import load_with_adapter
from agent_failure_atlas.annotations import load_annotations
from agent_failure_atlas.hub import publish_dataset
from agent_failure_atlas.loaders import TraceFormatError


def test_native_adapter_preserves_source_metadata(tmp_path):
    path = tmp_path / "native.jsonl"
    path.write_text(json.dumps({"type": "tool_use", "id": "x", "tool": {"name": "read_file", "arguments": {}}}) + "\n", encoding="utf-8")
    session = load_with_adapter(path)
    assert session.metadata["source_format"] == "claude-code-jsonl"
    assert session.messages[0].tool_calls[0].function.name == "read_file"


def test_ambiguous_adapter_is_rejected(tmp_path):
    path = tmp_path / "ambiguous.jsonl"
    path.write_text(json.dumps({"type": "assistant_message", "event": "span"}) + "\n", encoding="utf-8")
    with pytest.raises(TraceFormatError, match="Ambiguous"):
        load_with_adapter(path)


def test_publish_dry_run_refuses_unredacted_trace(tmp_path):
    (tmp_path / "trace.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="redacted"):
        publish_dataset("org/dataset", tmp_path, dry_run=True)


def test_publish_dry_run_plan(tmp_path):
    (tmp_path / "trace.redacted.jsonl").write_text("{}\n", encoding="utf-8")
    result = publish_dataset("org/dataset", tmp_path, dry_run=True)
    assert result["dry_run"] is True


def test_annotation_validation(root, tmp_path):
    trace = root / "examples" / "traces" / "safe_trace.jsonl"
    annotation = tmp_path / "annotations.jsonl"
    annotation.write_text(json.dumps({"session_id": "safe-trace", "source_type": "synthetic",
                                      "label": "negative", "evidence_start": 0,
                                      "evidence_end": 0}) + "\n", encoding="utf-8")
    loaded = load_annotations(annotation, trace.parent)
    assert loaded[0].session_id == "safe-trace"
