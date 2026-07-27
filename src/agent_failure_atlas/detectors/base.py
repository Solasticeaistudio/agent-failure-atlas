from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

from ..models import Evidence, Finding, ScanPolicy, TraceSession


class Detector(ABC):
    name: str

    @abstractmethod
    def scan(self, session: TraceSession, policy: ScanPolicy) -> list[Finding]:
        raise NotImplementedError


def stable_finding_id(detector: str, session_id: str, message_index: int, payload: Any) -> str:
    raw = json.dumps(
        {"detector": detector, "session": session_id, "index": message_index, "payload": payload},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def excerpt(text: str, limit: int = 240) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def regex_any(patterns: Iterable[str], value: str) -> bool:
    return any(re.search(pattern, value or "") for pattern in patterns)


def iter_tool_calls(session: TraceSession):
    for index, message in enumerate(session.messages):
        for call in message.tool_calls:
            yield index, message, call


def flatten_strings(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            found.extend(flatten_strings(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(flatten_strings(child, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        found.append((prefix, value))
    return found


def evidence_for_call(index: int, call) -> Evidence:
    return Evidence(
        message_index=index,
        role="assistant",
        excerpt=f"{call.function.name}({excerpt(str(call.function.arguments), 180)})",
        tool_name=call.function.name,
        tool_arguments=call.function.parsed_arguments(),
    )


def looks_like_url(value: str) -> bool:
    return bool(urlparse(value).scheme and urlparse(value).netloc)
