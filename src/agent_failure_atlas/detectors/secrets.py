from __future__ import annotations

import json

from ..models import Evidence, Finding, ScanPolicy, Severity, TraceSession
from .base import (
    Detector,
    evidence_for_call,
    excerpt,
    iter_tool_calls,
    regex_any,
    stable_finding_id,
)


class SecretExposureDetector(Detector):
    name = "secret-exposure"

    def scan(self, session: TraceSession, policy: ScanPolicy) -> list[Finding]:
        findings: list[Finding] = []
        for index, message in enumerate(session.messages):
            if regex_any(policy.secret_patterns, message.content):
                severity = Severity.CRITICAL if message.role == "assistant" else Severity.HIGH
                findings.append(
                    Finding(
                        id=stable_finding_id(self.name, session.id, index, {"content": message.content}),
                        detector=self.name,
                        category="secret_exposure",
                        severity=severity,
                        title="Potential credential or secret appears in the trace",
                        description=f"A {message.role} message matched a configured secret pattern.",
                        remediation=(
                            "Redact secrets before persistence or publication, use short-lived credentials, and scan traces "
                            "locally before uploading them to a dataset or bucket."
                        ),
                        confidence=0.93,
                        evidence=[
                            Evidence(
                                message_index=index,
                                role=message.role,
                                excerpt=excerpt(message.content),
                            )
                        ],
                    )
                )

        for index, _message, call in iter_tool_calls(session):
            serialized = json.dumps(call.function.parsed_arguments(), sort_keys=True, default=str)
            if not regex_any(policy.secret_patterns, serialized):
                continue
            findings.append(
                Finding(
                    id=stable_finding_id(self.name, session.id, index, {"tool": call.id, "args": serialized}),
                    detector=self.name,
                    category="secret_exposure",
                    severity=Severity.CRITICAL,
                    title="Potential credential or secret was passed to a tool",
                    description=f"Arguments for '{call.function.name}' matched a configured secret pattern.",
                    remediation=(
                        "Block secrets from tool arguments unless the tool explicitly requires a protected credential "
                        "reference; pass secret handles rather than raw values and redact persisted traces."
                    ),
                    confidence=0.96,
                    evidence=[evidence_for_call(index, call)],
                )
            )
        return findings
