"""Minimal, fail-closed adapter for Solstice Agent Trace Exchange v1."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .loaders import TraceFormatError
from .models import TraceMessage, TraceSession

EXCHANGE_VERSION = "solstice-agent-trace-exchange/v1"
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_FIELD_BYTES = 2 * 1024 * 1024
SUPPORTED_EVENT_TYPES = {
    "message", "user_message", "assistant_message", "tool_call", "tool_result",
    "tool_use", "tool_output", "approval", "checkpoint", "state_change",
    "decision", "action_summary", "unknown",
}


def _size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str).encode("utf-8"))


def validate_exchange(envelope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise TraceFormatError("DeltaStore exchange must be a JSON object")
    if envelope.get("schema_version") != EXCHANGE_VERSION:
        raise TraceFormatError(f"Unsupported DeltaStore exchange version: {envelope.get('schema_version')!r}")
    required = ("trace_id", "source", "task", "events", "checkpoints", "branches", "outcomes", "findings", "redaction", "provenance")
    missing = [key for key in required if key not in envelope]
    if missing:
        raise TraceFormatError(f"DeltaStore exchange missing fields: {', '.join(missing)}")
    if not isinstance(envelope["events"], list) or not isinstance(envelope["checkpoints"], list) or not isinstance(envelope["branches"], list):
        raise TraceFormatError("DeltaStore events, checkpoints, and branches must be arrays")
    events = envelope["events"]
    event_ids = [event.get("event_id") for event in events if isinstance(event, dict)]
    if len(event_ids) != len(events) or any(not value for value in event_ids):
        raise TraceFormatError("Every DeltaStore event requires event_id")
    if len(set(event_ids)) != len(event_ids):
        raise TraceFormatError("Duplicate DeltaStore event ID")
    sequences = [event.get("sequence") for event in events]
    if any(not isinstance(value, int) or value < 1 for value in sequences) or sequences != sorted(sequences) or len(set(sequences)) != len(sequences):
        raise TraceFormatError("DeltaStore event sequence must be strictly increasing")
    tool_ids: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            raise TraceFormatError("DeltaStore event must be an object")
        if _size(event) > MAX_FIELD_BYTES:
            raise TraceFormatError(f"DeltaStore event exceeds {MAX_FIELD_BYTES} bytes")
        event_type = str(event.get("event_type", ""))
        if event_type not in SUPPORTED_EVENT_TYPES:
            raise TraceFormatError(f"Unsupported DeltaStore event type: {event_type}")
        if event.get("parent_event_id") and event["parent_event_id"] not in event_ids:
            raise TraceFormatError("DeltaStore event references unknown parent_event_id")
        for reference in event.get("evidence_refs", []) or []:
            if reference not in event_ids:
                raise TraceFormatError("DeltaStore event references unknown evidence event")
        tool_id = event.get("tool_call_id")
        if tool_id:
            tool_ids.append(str(tool_id))
    if len(tool_ids) != len(set(tool_ids)):
        raise TraceFormatError("Duplicate DeltaStore tool-call ID")
    checkpoint_ids = {item.get("checkpoint_id") for item in envelope["checkpoints"] if isinstance(item, dict)}
    if len(checkpoint_ids) != len(envelope["checkpoints"]):
        raise TraceFormatError("Duplicate or invalid DeltaStore checkpoint ID")
    for checkpoint in envelope["checkpoints"]:
        if checkpoint.get("event_id") not in event_ids:
            raise TraceFormatError("Checkpoint references unknown event")
    branch_ids = {item.get("branch_id") for item in envelope["branches"] if isinstance(item, dict)}
    if len(branch_ids) != len(envelope["branches"]):
        raise TraceFormatError("Duplicate or invalid DeltaStore branch ID")
    for branch in envelope["branches"]:
        parent = branch.get("parent_checkpoint_id")
        if parent and parent not in checkpoint_ids:
            raise TraceFormatError("Branch references unknown checkpoint")
        for event in branch.get("events", []) or []:
            if event.get("event_id") in event_ids:
                raise TraceFormatError("Branch event duplicates original event ID")
    return envelope


def load_exchange(path: str | Path) -> tuple[TraceSession, dict[str, Any]]:
    path = Path(path)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise TraceFormatError(f"Trace exceeds maximum file size ({MAX_FILE_BYTES} bytes): {path}")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TraceFormatError(f"Invalid DeltaStore exchange JSON: {path}") from exc
    envelope = validate_exchange(envelope)
    messages: list[TraceMessage] = []
    event_map: list[str] = []
    unsupported: list[dict[str, str]] = []
    for event in envelope["events"]:
        event_type = str(event.get("event_type"))
        event_map.append(event["event_id"])
        actor = event.get("actor") if isinstance(event.get("actor"), dict) else {}
        role = str(actor.get("role") or actor.get("type") or ("tool" if event_type in {"tool_result", "tool_output"} else "assistant"))
        content = event.get("output_summary") or event.get("input_summary") or event.get("message") or ""
        raw: dict[str, Any] = {"role": role, "content": content, "source_event_type": event_type, "event_id": event["event_id"], "branch_id": event.get("branch_id"), "checkpoint_id": event.get("checkpoint_id")}
        if event_type in {"tool_call", "tool_use"} or event.get("tool_call_id") and event_type not in {"tool_result", "tool_output"}:
            raw["toolCalls"] = [{"id": str(event.get("tool_call_id") or event["event_id"]), "function": {"name": str(event.get("tool_name") or "unknown_tool"), "arguments": event.get("input_summary") or {}}}]
        if event_type in {"tool_result", "tool_output"}:
            raw["toolCallId"] = str(event.get("tool_call_id") or "")
        if event_type not in SUPPORTED_EVENT_TYPES:
            unsupported.append({"event_id": event["event_id"], "reason": f"unsupported event type {event_type}"})
            continue
        messages.append(TraceMessage.model_validate(raw))
    metadata = {
        "source_format": EXCHANGE_VERSION,
        "source_schema_version": EXCHANGE_VERSION,
        "trace_id": envelope["trace_id"],
        "exchange_event_ids": event_map,
        "exchange_checkpoints": envelope["checkpoints"],
        "exchange_branches": envelope["branches"],
        "exchange_policy": envelope.get("policy"),
        "exchange_provenance": envelope.get("provenance"),
        "exchange_redaction": envelope.get("redaction"),
        "exchange_outcomes": envelope.get("outcomes"),
        "exchange_findings": envelope.get("findings", []),
        "normalization_report": {"source_events": len(envelope["events"]), "normalized_events": len(messages), "dropped_events": unsupported, "unsupported_event_types": [], "inferred_fields": [], "preserved_tool_calls": sum(bool(message.tool_calls) for message in messages), "preserved_tool_results": sum(message.role == "tool" for message in messages)},
    }
    return TraceSession(harness="deltastore-exchange", id=str(envelope["trace_id"]), name=envelope.get("title"), messages=messages, metadata=metadata, source=str(path)), envelope
