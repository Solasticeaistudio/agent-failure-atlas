from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


SEVERITY_RANK = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


class ToolFunction(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    arguments: str | dict[str, Any] = "{}"

    def parsed_arguments(self) -> dict[str, Any]:
        if isinstance(self.arguments, dict):
            return self.arguments
        try:
            parsed = json.loads(self.arguments)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except (json.JSONDecodeError, TypeError):
            return {"raw": self.arguments}


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    function: ToolFunction


class TraceMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    role: str
    content: str = ""
    reasoning_content: str | None = Field(default=None, alias="reasoningContent")
    tool_calls: list[ToolCall] = Field(default_factory=list, alias="toolCalls")
    tool_call_id: str | None = Field(default=None, alias="toolCallId")
    timestamp: int | float | str | None = None
    model: str | None = None

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts: list[str] = []
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text") or item.get("content")
                    parts.append(str(text if text is not None else item))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(value)


class TraceSession(BaseModel):
    model_config = ConfigDict(extra="allow")

    harness: str
    id: str
    name: str | None = None
    messages: list[TraceMessage] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None


class Evidence(BaseModel):
    message_index: int
    role: str
    excerpt: str
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None


class Finding(BaseModel):
    id: str
    detector: str
    category: str
    severity: Severity
    title: str
    description: str
    remediation: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class ScanPolicy(BaseModel):
    allowed_tools: list[str] = Field(default_factory=list)
    approval_required_tools: list[str] = Field(
        default_factory=lambda: [
            r"(?i)(delete|remove|destroy|drop|deploy|publish|send|email|transfer|execute|shell|write|modify)"
        ]
    )
    approval_phrases: list[str] = Field(
        default_factory=lambda: [
            "approval granted",
            "approved to proceed",
            "yes, proceed",
            "confirmed, proceed",
        ]
    )
    approval_window_messages: int = 6
    allowed_path_prefixes: list[str] = Field(default_factory=lambda: ["/workspace", "./", "src/"])
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    repeated_action_threshold: int = 3
    injection_followup_window: int = 4
    secret_patterns: list[str] = Field(
        default_factory=lambda: [
            r"hf_[A-Za-z0-9]{20,}",
            r"sk-[A-Za-z0-9_-]{20,}",
            r"AKIA[0-9A-Z]{16}",
            r"(?i)bearer\s+[A-Za-z0-9._-]{20,}",
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        ]
    )
    error_patterns: list[str] = Field(
        default_factory=lambda: [
            r"(?i)\b(error|exception|failed|failure|denied|forbidden|timed out|timeout)\b",
            r"(?i)exit\s+code\s+[1-9]\d*",
            r"(?i)status\s*[:=]\s*(4\d\d|5\d\d)",
        ]
    )
    success_claim_patterns: list[str] = Field(
        default_factory=lambda: [
            r"(?i)\b(done|completed|successful|successfully|fixed|deployed|published|sent)\b"
        ]
    )
    injection_patterns: list[str] = Field(
        default_factory=lambda: [
            r"(?i)ignore (all |any )?(previous|prior) instructions",
            r"(?i)system message",
            r"(?i)developer message",
            r"(?i)do not tell (the )?user",
            r"(?i)(exfiltrate|send|upload).{0,40}(secret|token|credential|key)",
        ]
    )

    def stable_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ScanMetrics(BaseModel):
    total_messages: int
    total_tool_calls: int
    total_findings: int
    findings_by_severity: dict[str, int]
    findings_by_category: dict[str, int]
    scan_duration_ms: float


class ScanReport(BaseModel):
    schema_version: str = "0.1"
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    policy_hash: str
    session: TraceSession
    findings: list[Finding]
    metrics: ScanMetrics
