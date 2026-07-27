from __future__ import annotations

from ..models import Evidence, Finding, ScanPolicy, Severity, TraceSession
from .base import Detector, excerpt, regex_any, stable_finding_id


class PromptInjectionDetector(Detector):
    name = "prompt-injection"

    def scan(self, session: TraceSession, policy: ScanPolicy) -> list[Finding]:
        findings: list[Finding] = []
        for index, message in enumerate(session.messages):
            if message.role != "tool" or not regex_any(policy.injection_patterns, message.content):
                continue
            end = min(len(session.messages), index + 1 + policy.injection_followup_window)
            followup_calls = []
            for followup_index in range(index + 1, end):
                followup = session.messages[followup_index]
                for call in followup.tool_calls:
                    followup_calls.append((followup_index, call))

            severity = Severity.HIGH if followup_calls else Severity.MEDIUM
            evidence = [
                Evidence(
                    message_index=index,
                    role=message.role,
                    excerpt=excerpt(message.content),
                    tool_name=None,
                    tool_arguments=None,
                )
            ]
            if followup_calls:
                call_index, call = followup_calls[0]
                evidence.append(
                    Evidence(
                        message_index=call_index,
                        role="assistant",
                        excerpt=f"Follow-up tool call: {call.function.name}",
                        tool_name=call.function.name,
                        tool_arguments=call.function.parsed_arguments(),
                    )
                )
            findings.append(
                Finding(
                    id=stable_finding_id(self.name, session.id, index, message.content),
                    detector=self.name,
                    category="prompt_injection",
                    severity=severity,
                    title=(
                        "Agent acted after untrusted prompt-injection content"
                        if followup_calls
                        else "Untrusted tool output contains prompt-injection content"
                    ),
                    description=(
                        "A tool result attempted to override instructions. A subsequent tool action increases the risk "
                        "that untrusted content influenced agent behavior."
                    ),
                    remediation=(
                        "Treat retrieved and tool-produced text as untrusted data, isolate instructions from content, "
                        "and require policy checks before any follow-up action."
                    ),
                    confidence=0.90 if followup_calls else 0.82,
                    evidence=evidence,
                )
            )
        return findings
