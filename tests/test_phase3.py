import json

import pytest

from agent_failure_atlas.adapters import load_with_adapter
from agent_failure_atlas.annotations import load_annotations
from agent_failure_atlas.hub import publish_dataset
from agent_failure_atlas.loaders import TraceFormatError


@pytest.mark.parametrize(
    ("format_id", "filename", "source_events"),
    [
        ("claude-code-jsonl", "claude-code.jsonl", ["tool_use", "tool_result"]),
        ("codex-jsonl", "codex.jsonl", ["function_call", "function_result"]),
        ("pi-agent-jsonl", "pi-agent.jsonl", ["tool_call", "tool_output"]),
        ("otlp-jsonl", "otlp.jsonl", ["span"]),
    ],
)
def test_native_adapter_fixtures(root, format_id, filename, source_events):
    path = root / "tests" / "fixtures" / "adapters" / filename
    session = load_with_adapter(path)

    assert session.harness == format_id
    assert session.metadata["source_format"] == format_id
    assert session.metadata["source_event_types"] == source_events
    assert session.messages[0].tool_calls[0].function.name == "read_file"
    assert session.messages[-1].role == "tool"
    assert load_with_adapter(path, format_id=format_id) == session


def test_explicit_adapter_resolves_ambiguous_input(tmp_path):
    path = tmp_path / "ambiguous.jsonl"
    path.write_text(
        json.dumps({"type": "assistant_message", "content": "done"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(TraceFormatError, match="Ambiguous"):
        load_with_adapter(path)
    assert load_with_adapter(path, format_id="codex-jsonl").messages[0].content == "done"


def test_unknown_and_unsupported_adapters_fail_closed(tmp_path):
    path = tmp_path / "hermes.jsonl"
    path.write_text(
        json.dumps({"type": "hermes_message", "content": "not a stable contract"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(TraceFormatError, match="Unsupported"):
        load_with_adapter(path)
    with pytest.raises(TraceFormatError, match="Unknown adapter"):
        load_with_adapter(path, format_id="hermes-jsonl")


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
    annotation.write_text(
        json.dumps(
            {
                "session_id": "safe-trace",
                "source_type": "synthetic",
                "failure_category": "scope_violation",
                "label": "negative",
                "reviewer_id": "reviewer-a",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    loaded = load_annotations(annotation, trace.parent)
    assert loaded[0].session_id == "safe-trace"
