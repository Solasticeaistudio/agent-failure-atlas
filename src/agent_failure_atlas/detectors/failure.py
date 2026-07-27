from __future__ import annotations

from ..models import Evidence, Finding, ScanPolicy, Severity, TraceSession
from .base import Detector, excerpt, regex_any, stable_finding_id


class SilentFailureDetector(Detector):
    name = "silent-failure"

    def scan(self, session: TraceSession, policy: ScanPolicy) -> list[Finding]:
        findings: list[Finding] = []
        for index, message in enumerate(session.messages):
            if message.role != "tool" or not regex_any(policy.error_patterns, message.content):
                continue
            later = session.messages[index + 1 :]
            success_claim = next(
                (
                    (index + 1 + offset, candidate)
                    for offset, candidate in enumerate(later)
                    if candidate.role == "assistant"
                    and candidate.content
                    and regex_any(policy.success_claim_patterns, candidate.content)
                ),
                None,
            )
            retry = any(
                candidate.role == "assistant" and candidate.tool_calls
                for candidate in later[:4]
            )
            if success_claim:
                claim_index, claim_message = success_claim
                findings.append(
                    Finding(
                        id=stable_finding_id(self.name, session.id, index, message.content),
                        detector=self.name,
                        category="silent_tool_failure",
                        severity=Severity.HIGH,
                        title="Agent claimed success after a tool failure",
                        description=(
                            "A tool returned an error, but a later assistant message asserted success without evidence "
                            "of a successful recovery."
                        ),
                        remediation=(
                            "Make tool success machine-verifiable, propagate errors into agent state, and block final "
                            "success claims until required postconditions pass."
                        ),
                        confidence=0.95 if not retry else 0.85,
                        evidence=[
                            Evidence(
                                message_index=index,
                                role="tool",
                                excerpt=excerpt(message.content),
                            ),
                            Evidence(
                                message_index=claim_index,
                                role="assistant",
                                excerpt=excerpt(claim_message.content),
                            ),
                        ],
                    )
                )
            elif not retry:
                findings.append(
                    Finding(
                        id=stable_finding_id(self.name, session.id, index, {"unhandled": message.content}),
                        detector=self.name,
                        category="unhandled_tool_failure",
                        severity=Severity.MEDIUM,
                        title="Tool failure was not followed by recovery or escalation",
                        description="A tool error appears to have terminated without a retry, fallback, or explicit escalation.",
                        remediation="Define bounded retries, fallbacks, and user-visible escalation for every tool failure mode.",
                        confidence=0.82,
                        evidence=[
                            Evidence(
                                message_index=index,
                                role="tool",
                                excerpt=excerpt(message.content),
                            )
                        ],
                    )
                )
        return findings
