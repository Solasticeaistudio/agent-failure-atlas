"""Explicit adapters for supported public trace formats."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .loaders import TraceFormatError, load_trace_file
from .models import TraceMessage, TraceSession


class TraceAdapter(Protocol):
    format_id: str

    def accepts(self, path: Path) -> bool: ...

    def load(self, path: Path) -> TraceSession: ...


def _first_rows(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for _ in range(2):
            line = handle.readline()
            if not line:
                break
            value = json.loads(line)
            if not isinstance(value, dict):
                return []
            rows.append(value)
    return rows


def _native_session(path: Path, format_id: str, rows: list[dict[str, Any]]) -> TraceSession:
    messages: list[TraceMessage] = []
    for row in rows:
        event_type = str(row.get("type") or row.get("event") or row.get("name") or "")
        if event_type in {"message", "assistant_message", "user_message"}:
            role = str(row.get("role") or row.get("message", {}).get("role") or "assistant")
            content = row.get("content") or row.get("message", {}).get("content") or ""
            messages.append(TraceMessage(role=role, content=content, source_event_type=event_type))
        elif event_type in {"tool_call", "tool_use", "function_call"}:
            function = row.get("function") or row.get("tool") or {}
            name = function.get("name") if isinstance(function, dict) else str(function)
            arguments = function.get("arguments", {}) if isinstance(function, dict) else {}
            messages.append(TraceMessage(role="assistant", content="", source_event_type=event_type,
                                         toolCalls=[{"id": str(row.get("id", "tool")),
                                                     "function": {"name": str(name), "arguments": arguments}}]))
        elif event_type in {"tool_result", "tool_output", "function_result"}:
            messages.append(TraceMessage(role="tool", content=str(row.get("content", "")),
                                         toolCallId=str(row.get("id") or row.get("tool_call_id", "")),
                                         source_event_type=event_type))
    return TraceSession(harness=format_id, id=path.stem, messages=messages,
                        metadata={"source_format": format_id, "source_schema_version": "1"}, source=str(path))


@dataclass(frozen=True)
class HuggingFaceSTSAdapter:
    format_id: str = "huggingface-sts"

    def accepts(self, path: Path) -> bool:
        rows = _first_rows(path)
        return bool(rows and rows[0].get("type") == "session")

    def load(self, path: Path) -> TraceSession:
        if not self.accepts(path):
            raise TraceFormatError(f"Input is not {self.format_id}: {path}")
        return load_trace_file(path)


@dataclass(frozen=True)
class OpenAIChatJSONLAdapter:
    format_id: str = "openai-chat-jsonl"

    def accepts(self, path: Path) -> bool:
        rows = _first_rows(path)
        return bool(rows and all("role" in row for row in rows))

    def load(self, path: Path) -> TraceSession:
        if not self.accepts(path):
            raise TraceFormatError(f"Input is not {self.format_id}: {path}")
        return load_trace_file(path)


@dataclass(frozen=True)
class NativeJSONLAdapter:
    format_id: str
    markers: tuple[str, ...]

    def accepts(self, path: Path) -> bool:
        rows = _first_rows(path)
        return bool(rows and any(str(row.get("type") or row.get("event") or "") in self.markers for row in rows))

    def load(self, path: Path) -> TraceSession:
        if not self.accepts(path):
            raise TraceFormatError(f"Input is not {self.format_id}: {path}")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return _native_session(path, self.format_id, rows)


ClaudeCodeAdapter = NativeJSONLAdapter("claude-code-jsonl", ("tool_use", "tool_result", "assistant_message"))
CodexAdapter = NativeJSONLAdapter("codex-jsonl", ("function_call", "function_result", "assistant_message"))
PiAgentAdapter = NativeJSONLAdapter("pi-agent-jsonl", ("tool_call", "tool_output", "user_message"))
OTLPAdapter = NativeJSONLAdapter("otlp-jsonl", ("span",))


ADAPTERS: tuple[TraceAdapter, ...] = (
    HuggingFaceSTSAdapter(), OpenAIChatJSONLAdapter(), ClaudeCodeAdapter,
    CodexAdapter, PiAgentAdapter, OTLPAdapter,
)


def load_with_adapter(path: str | Path) -> TraceSession:
    path = Path(path)
    matches = [adapter for adapter in ADAPTERS if adapter.accepts(path)]
    if len(matches) == 1:
        return matches[0].load(path)
    if len(matches) > 1:
        raise TraceFormatError("Ambiguous trace format; specify an adapter explicitly: "
                               + ", ".join(adapter.format_id for adapter in matches))
    supported = [adapter.format_id for adapter in ADAPTERS]
    raise TraceFormatError(f"Unsupported trace format; expected one of {supported}")
