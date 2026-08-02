"""Explicit, fail-closed adapters for supported trace formats."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .deltastore_exchange import EXCHANGE_VERSION, load_exchange
from .loaders import TraceFormatError, iter_trace_rows, load_trace_file
from .models import TraceMessage, TraceSession


class TraceAdapter(Protocol):
    format_id: str

    def accepts(self, path: Path) -> bool: ...

    def load(self, path: Path) -> TraceSession: ...


@dataclass(frozen=True)
class DeltaStoreExchangeAdapter:
    format_id: str = EXCHANGE_VERSION

    def accepts(self, path: Path) -> bool:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return isinstance(value, dict) and value.get("schema_version") == EXCHANGE_VERSION

    def load(self, path: Path) -> TraceSession:
        if not self.accepts(path):
            raise TraceFormatError(f"Input is not {self.format_id}: {path}")
        session, _ = load_exchange(path)
        return session


def _first_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for row in iter_trace_rows(path):
            rows.append(row)
            if len(rows) == 2:
                break
    except (OSError, TraceFormatError):
        return []
    return rows


def _event_type(row: dict[str, Any]) -> str:
    return str(row.get("type") or row.get("event") or row.get("name") or "")


def _native_session(path: Path, format_id: str, rows: list[dict[str, Any]]) -> TraceSession:
    messages: list[TraceMessage] = []
    source_event_types: list[str] = []
    tool_ids: set[str] = set()

    def register_tool_id(tool_id: str) -> None:
        if not tool_id:
            raise TraceFormatError(f"{format_id} tool event requires an ID: {path}")
        if tool_id in tool_ids:
            raise TraceFormatError(f"Duplicate tool call id {tool_id!r} in {path}")
        tool_ids.add(tool_id)

    for row in rows:
        event_type = _event_type(row)
        source_event_types.append(event_type)
        if event_type in {"message", "assistant_message", "user_message"}:
            nested = row.get("message") if isinstance(row.get("message"), dict) else {}
            role = str(row.get("role") or nested.get("role") or "assistant")
            content = row.get("content")
            if content is None:
                content = nested.get("content", "")
            messages.append(
                TraceMessage(role=role, content=content, source_event_type=event_type)
            )
        elif event_type in {"tool_call", "tool_use", "function_call"}:
            function = row.get("function") or row.get("tool") or {}
            name = function.get("name") if isinstance(function, dict) else str(function)
            if not name:
                raise TraceFormatError(f"{format_id} tool call requires a tool name: {path}")
            arguments = function.get("arguments", {}) if isinstance(function, dict) else {}
            tool_id = str(row.get("id") or row.get("tool_call_id") or "")
            register_tool_id(tool_id)
            messages.append(
                TraceMessage(
                    role="assistant",
                    content="",
                    source_event_type=event_type,
                    toolCalls=[
                        {
                            "id": tool_id,
                            "function": {"name": str(name), "arguments": arguments},
                        }
                    ],
                )
            )
        elif event_type in {"tool_result", "tool_output", "function_result"}:
            tool_id = str(row.get("id") or row.get("tool_call_id") or "")
            if not tool_id:
                raise TraceFormatError(f"{format_id} tool result requires a tool-call ID: {path}")
            messages.append(
                TraceMessage(
                    role="tool",
                    content=row.get("content", ""),
                    toolCallId=tool_id,
                    source_event_type=event_type,
                )
            )
        elif event_type == "span":
            attributes = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
            tool_name = attributes.get("gen_ai.tool.name") or attributes.get("tool.name")
            if tool_name:
                tool_id = str(
                    attributes.get("gen_ai.tool.call.id")
                    or attributes.get("tool.call.id")
                    or row.get("span_id")
                    or ""
                )
                register_tool_id(tool_id)
                arguments = (
                    attributes.get("gen_ai.tool.call.arguments")
                    or attributes.get("tool.call.arguments")
                    or {}
                )
                messages.append(
                    TraceMessage(
                        role="assistant",
                        content="",
                        source_event_type=event_type,
                        toolCalls=[
                            {
                                "id": tool_id,
                                "function": {"name": str(tool_name), "arguments": arguments},
                            }
                        ],
                    )
                )
                result = attributes.get("gen_ai.tool.call.result")
                if result is None:
                    result = attributes.get("tool.call.result")
                if result is not None:
                    messages.append(
                        TraceMessage(
                            role="tool",
                            content=result,
                            toolCallId=tool_id,
                            source_event_type=event_type,
                        )
                    )
            else:
                content = (
                    attributes.get("gen_ai.output.messages")
                    or attributes.get("gen_ai.prompt")
                    or attributes.get("gen_ai.completion")
                    or row.get("content")
                )
                if content is not None:
                    messages.append(
                        TraceMessage(
                            role=str(attributes.get("gen_ai.role") or "assistant"),
                            content=content,
                            source_event_type=event_type,
                        )
                    )

    if not messages:
        raise TraceFormatError(f"{format_id} input contained no supported events: {path}")
    return TraceSession(
        harness=format_id,
        id=path.stem,
        messages=messages,
        metadata={
            "source_format": format_id,
            "source_schema_version": "1",
            "source_event_types": source_event_types,
        },
        source=str(path),
    )


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
        return bool(rows and any(_event_type(row) in self.markers for row in rows))

    def load(self, path: Path) -> TraceSession:
        if not self.accepts(path):
            raise TraceFormatError(f"Input is not {self.format_id}: {path}")
        rows = list(iter_trace_rows(path))
        return _native_session(path, self.format_id, rows)


ClaudeCodeAdapter = NativeJSONLAdapter(
    "claude-code-jsonl", ("tool_use", "tool_result", "assistant_message")
)
CodexAdapter = NativeJSONLAdapter(
    "codex-jsonl", ("function_call", "function_result", "assistant_message")
)
PiAgentAdapter = NativeJSONLAdapter(
    "pi-agent-jsonl", ("tool_call", "tool_output", "user_message")
)
OTLPAdapter = NativeJSONLAdapter("otlp-jsonl", ("span",))


ADAPTERS: tuple[TraceAdapter, ...] = (
    DeltaStoreExchangeAdapter(),
    HuggingFaceSTSAdapter(),
    OpenAIChatJSONLAdapter(),
    ClaudeCodeAdapter,
    CodexAdapter,
    PiAgentAdapter,
    OTLPAdapter,
)


def adapter_for(format_id: str) -> TraceAdapter:
    matches = [adapter for adapter in ADAPTERS if adapter.format_id == format_id]
    if not matches:
        supported = ", ".join(adapter.format_id for adapter in ADAPTERS)
        raise TraceFormatError(f"Unknown adapter {format_id!r}; expected one of: {supported}")
    return matches[0]


def load_with_adapter(path: str | Path, *, format_id: str | None = None) -> TraceSession:
    path = Path(path)
    if format_id:
        return adapter_for(format_id).load(path)
    matches = [adapter for adapter in ADAPTERS if adapter.accepts(path)]
    if len(matches) == 1:
        return matches[0].load(path)
    if len(matches) > 1:
        raise TraceFormatError(
            "Ambiguous trace format; specify an adapter explicitly: "
            + ", ".join(adapter.format_id for adapter in matches)
        )
    supported = [adapter.format_id for adapter in ADAPTERS]
    raise TraceFormatError(f"Unsupported trace format; expected one of {supported}")
