import json

import pytest

from agent_failure_atlas.loaders import TraceFormatError, dump_sts, load_trace_file


def test_load_sts(root):
    session = load_trace_file(root / "examples" / "traces" / "safe_trace.jsonl")
    assert session.id == "safe-trace"
    assert len(session.messages) == 4
    assert session.messages[1].tool_calls[0].function.name == "read_file"


def test_round_trip_sts(root, tmp_path):
    session = load_trace_file(root / "examples" / "traces" / "safe_trace.jsonl")
    destination = dump_sts(session, tmp_path / "roundtrip.jsonl")
    loaded = load_trace_file(destination)
    assert loaded.model_dump(exclude={"source"}) == session.model_dump(exclude={"source"})


def test_openai_style_jsonl(tmp_path):
    path = tmp_path / "messages.jsonl"
    path.write_text(
        '\n'.join([json.dumps({"role": "user", "content": "hi"}), json.dumps({"role": "assistant", "content": "hello"})]),
        encoding="utf-8",
    )
    session = load_trace_file(path)
    assert session.harness == "openai-chat-jsonl"
    assert len(session.messages) == 2


def test_invalid_json_raises(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(TraceFormatError):
        load_trace_file(path)
