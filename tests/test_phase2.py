import json

import pytest

from agent_failure_atlas.adapters import HuggingFaceSTSAdapter, OpenAIChatJSONLAdapter
from agent_failure_atlas.loaders import TraceFormatError, load_trace_file


def test_explicit_adapters_accept_and_reject(root):
    sts = root / "examples" / "traces" / "safe_trace.jsonl"
    assert HuggingFaceSTSAdapter().accepts(sts)
    assert not OpenAIChatJSONLAdapter().accepts(sts)
    assert HuggingFaceSTSAdapter().load(sts).id == "safe-trace"


def test_duplicate_tool_ids_rejected(tmp_path):
    path = tmp_path / "duplicate.jsonl"
    rows = [
        {"type": "session", "harness": "test", "id": "duplicate"},
        {"type": "message", "message": {"role": "assistant", "toolCalls": [
            {"id": "same", "function": {"name": "read_file", "arguments": "{}"}},
        ]}},
        {"type": "message", "message": {"role": "assistant", "toolCalls": [
            {"id": "same", "function": {"name": "read_file", "arguments": "{}"}},
        ]}},
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    with pytest.raises(TraceFormatError, match="Duplicate tool call"):
        load_trace_file(path)


def test_streaming_limits_and_unicode(tmp_path):
    path = tmp_path / "unicode.jsonl"
    path.write_text(json.dumps({"role": "user", "content": "café 🚀"}) + "\n", encoding="utf-8")
    assert load_trace_file(path).messages[0].content == "café 🚀"
    with pytest.raises(TraceFormatError, match="maximum message"):
        load_trace_file(path, max_line_bytes=8)
