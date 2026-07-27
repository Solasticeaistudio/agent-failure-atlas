from __future__ import annotations

import re

from ..models import Finding, ScanPolicy, Severity, TraceSession
from .base import Detector, evidence_for_call, iter_tool_calls, stable_finding_id


class ApprovalBypassDetector(Detector):
    name = "approval-bypass"

    def scan(self, session: TraceSession, policy: ScanPolicy) -> list[Finding]:
        findings: list[Finding] = []
        for index, _message, call in iter_tool_calls(session):
            tool = call.function.name
            if not any(re.search(pattern, tool) for pattern in policy.approval_required_tools):
                continue
            start = max(0, index - policy.approval_window_messages)
            context = session.messages[start:index]
            approved = any(
                message.role in {"user", "system"}
                and any(phrase.lower() in message.content.lower() for phrase in policy.approval_phrases)
                for message in context
            )
            explicit_ids = session.metadata.get("approved_tool_call_ids", [])
            approved = approved or call.id in explicit_ids
            if not approved:
                findings.append(
                    Finding(
                        id=stable_finding_id(self.name, session.id, index, {"tool_call": call.id}),
                        detector=self.name,
                        category="approval_bypass",
                        severity=Severity.HIGH,
                        title="High-impact tool call lacks explicit approval",
                        description=(
                            f"The agent invoked '{tool}' without a nearby approval phrase or an approved tool-call ID."
                        ),
                        remediation=(
                            "Represent approval as structured state bound to the exact action, arguments, actor, and expiry; "
                            "do not infer approval from conversational tone."
                        ),
                        confidence=0.96,
                        evidence=[evidence_for_call(index, call)],
                    )
                )
        return findings
