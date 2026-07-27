from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import TraceMessage, TraceSession


class TraceFormatError(ValueError):
    pass


def iter_trace_rows(path: str | Path, *, max_file_bytes: int = 50 * 1024 * 1024, max_line_bytes: int = 2 * 1024 * 1024, max_rows: int = 100_000) -> Iterable[dict[str, Any]]:
    """Stream validated JSON objects without executing trace content."""
    yield from _iter_jsonl(Path(path), max_file_bytes=max_file_bytes, max_line_bytes=max_line_bytes, max_rows=max_rows)


def _iter_jsonl(path: Path, *, max_file_bytes: int = 50 * 1024 * 1024, max_line_bytes: int = 2 * 1024 * 1024, max_rows: int = 100_000) -> Iterable[dict[str, Any]]:
    size = path.stat().st_size
    if size > max_file_bytes:
        raise TraceFormatError(f"Trace exceeds maximum file size ({max_file_bytes} bytes): {path}")
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > max_rows:
                raise TraceFormatError(f"Trace exceeds maximum row count ({max_rows}): {path}")
            if len(line.encode("utf-8")) > max_line_bytes:
                raise TraceFormatError(f"Trace line {line_number} exceeds maximum message size ({max_line_bytes} bytes)")
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise TraceFormatError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
            if not isinstance(value, dict):
                raise TraceFormatError(f"Expected an object on line {line_number} of {path}")
            yield value


def _normalize_tool_calls(message: dict[str, Any]) -> dict[str, Any]:
    if "tool_calls" in message and "toolCalls" not in message:
        message["toolCalls"] = message.pop("tool_calls")
    if "tool_call_id" in message and "toolCallId" not in message:
        message["toolCallId"] = message.pop("tool_call_id")
    if "reasoning_content" in message and "reasoningContent" not in message:
        message["reasoningContent"] = message.pop("reasoning_content")
    return message


def _validate_unique_tool_ids(messages: list[TraceMessage], path: Path) -> None:
    """Reject ambiguous tool-result joins before scanning a trace."""
    seen: set[str] = set()
    for message in messages:
        for call in message.tool_calls:
            if call.id in seen:
                raise TraceFormatError(f"Duplicate tool call id {call.id!r} in {path}")
            seen.add(call.id)


def load_trace_file(path: str | Path, *, max_file_bytes: int = 50 * 1024 * 1024, max_line_bytes: int = 2 * 1024 * 1024, max_rows: int = 100_000) -> TraceSession:
    path = Path(path)
    rows = list(_iter_jsonl(path, max_file_bytes=max_file_bytes, max_line_bytes=max_line_bytes, max_rows=max_rows))
    if not rows:
        raise TraceFormatError(f"Trace file is empty: {path}")

    # Hugging Face Session Trace Simple Format (STS): header, then message envelopes.
    if rows[0].get("type") == "session":
        header = rows[0]
        messages: list[TraceMessage] = []
        for row in rows[1:]:
            if row.get("type") != "message" or not isinstance(row.get("message"), dict):
                continue
            messages.append(TraceMessage.model_validate(_normalize_tool_calls(dict(row["message"]))))
        metadata = {k: v for k, v in header.items() if k not in {"type", "harness", "id", "name"}}
        _validate_unique_tool_ids(messages, path)
        return TraceSession(
            harness=str(header.get("harness", "unknown")),
            id=str(header.get("id", path.stem)),
            name=header.get("name"),
            messages=messages,
            metadata=metadata,
            source=str(path),
        )

    # One-row normalized dataset format: {session_id, harness, messages:[...]}
    if len(rows) == 1 and isinstance(rows[0].get("messages"), list):
        row = rows[0]
        messages = [TraceMessage.model_validate(_normalize_tool_calls(dict(m))) for m in row["messages"]]
        metadata = {
            k: v
            for k, v in row.items()
            if k not in {"messages", "session_id", "id", "harness", "name", "title"}
        }
        _validate_unique_tool_ids(messages, path)
        return TraceSession(
            harness=str(row.get("harness", "normalized-dataset")),
            id=str(row.get("session_id") or row.get("id") or path.stem),
            name=row.get("name") or row.get("title"),
            messages=messages,
            metadata=metadata,
            source=str(path),
        )

    # OpenAI-style JSONL: one message object per line.
    if all("role" in row for row in rows):
        messages = [TraceMessage.model_validate(_normalize_tool_calls(dict(row))) for row in rows]
        _validate_unique_tool_ids(messages, path)
        return TraceSession(
            harness="openai-chat-jsonl",
            id=path.stem,
            name=path.stem,
            messages=messages,
            source=str(path),
        )

    raise TraceFormatError(
        f"Unsupported trace format for {path}. Current MVP supports Hugging Face STS, "
        "one-row normalized datasets, and OpenAI-style message JSONL."
    )


def discover_trace_files(path: str | Path) -> list[Path]:
    path = Path(path)
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(path)
    return sorted(p for p in path.rglob("*.jsonl") if p.is_file())


def dump_sts(session: TraceSession, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "type": "session",
        "harness": session.harness,
        "id": session.id,
        "name": session.name,
        **session.metadata,
    }
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(header, ensure_ascii=False) + "\n")
        for message in session.messages:
            payload = message.model_dump(by_alias=True, exclude_none=True, mode="json")
            handle.write(json.dumps({"type": "message", "message": payload}, ensure_ascii=False) + "\n")
    return path
