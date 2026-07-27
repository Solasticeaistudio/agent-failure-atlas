from __future__ import annotations

import json
from collections import defaultdict

from ..models import Finding, ScanPolicy, Severity, TraceSession
from .base import Detector, evidence_for_call, iter_tool_calls, stable_finding_id


class RepeatedActionDetector(Detector):
    name = "repeated-action"

    def scan(self, session: TraceSession, policy: ScanPolicy) -> list[Finding]:
        seen: dict[str, list[tuple[int, object]]] = defaultdict(list)
        for index, _message, call in iter_tool_calls(session):
            signature = json.dumps(
                {"tool": call.function.name, "args": call.function.parsed_arguments()},
                sort_keys=True,
                default=str,
            )
            seen[signature].append((index, call))

        findings: list[Finding] = []
        for signature, occurrences in seen.items():
            if len(occurrences) < policy.repeated_action_threshold:
                continue
            first_index, first_call = occurrences[0]
            findings.append(
                Finding(
                    id=stable_finding_id(self.name, session.id, first_index, signature),
                    detector=self.name,
                    category="runaway_loop",
                    severity=Severity.MEDIUM,
                    title="Identical tool action repeated without progress",
                    description=(
                        f"The same '{first_call.function.name}' call occurred {len(occurrences)} times, meeting the "
                        f"configured threshold of {policy.repeated_action_threshold}."
                    ),
                    remediation=(
                        "Track action signatures, require evidence of state change, and stop or escalate when repeated "
                        "calls exceed a bounded retry budget."
                    ),
                    confidence=0.97,
                    evidence=[evidence_for_call(index, call) for index, call in occurrences[:3]],
                )
            )
        return findings
