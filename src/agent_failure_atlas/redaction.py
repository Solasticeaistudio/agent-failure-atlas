from __future__ import annotations

import re
from copy import deepcopy

from .models import ScanPolicy, TraceSession

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
HOME_PATH_PATTERN = re.compile(r"(?i)(?:/home/[^/\s]+|/Users/[^/\s]+|[A-Z]:\\Users\\[^\\\s]+)")


def redact_text(value: str, policy: ScanPolicy) -> str:
    result = value
    for pattern in policy.secret_patterns:
        result = re.sub(pattern, "[REDACTED_SECRET]", result)
    result = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", result)
    result = HOME_PATH_PATTERN.sub("[REDACTED_HOME]", result)
    return result


def redact_session(session: TraceSession, policy: ScanPolicy | None = None) -> TraceSession:
    policy = policy or ScanPolicy()
    redacted = deepcopy(session)
    for message in redacted.messages:
        message.content = redact_text(message.content, policy)
        if message.reasoning_content:
            message.reasoning_content = redact_text(message.reasoning_content, policy)
        for call in message.tool_calls:
            if isinstance(call.function.arguments, str):
                call.function.arguments = redact_text(call.function.arguments, policy)
            else:
                call.function.arguments = _redact_value(call.function.arguments, policy)
    redacted.metadata = _redact_value(redacted.metadata, policy)
    redacted.metadata["atlas_redacted"] = True
    return redacted


def _redact_value(value, policy: ScanPolicy):
    if isinstance(value, dict):
        return {key: _redact_value(child, policy) for key, child in value.items()}
    if isinstance(value, list):
        return [_redact_value(child, policy) for child in value]
    if isinstance(value, str):
        return redact_text(value, policy)
    return value
