from __future__ import annotations

import fnmatch
import os
import posixpath
import re
from urllib.parse import urlparse

from ..models import Finding, ScanPolicy, Severity, TraceSession
from .base import (
    Detector,
    evidence_for_call,
    flatten_strings,
    iter_tool_calls,
    looks_like_url,
    stable_finding_id,
)


class ScopeViolationDetector(Detector):
    name = "scope-violation"

    def scan(self, session: TraceSession, policy: ScanPolicy) -> list[Finding]:
        findings: list[Finding] = []
        for index, _message, call in iter_tool_calls(session):
            tool = call.function.name
            args = call.function.parsed_arguments()

            if policy.allowed_tools and not any(fnmatch.fnmatch(tool, pattern) for pattern in policy.allowed_tools):
                findings.append(
                    Finding(
                        id=stable_finding_id(self.name, session.id, index, {"tool": tool}),
                        detector=self.name,
                        category="unauthorized_tool",
                        severity=Severity.HIGH,
                        title="Tool outside the configured allowlist",
                        description=f"The agent called '{tool}', which is not allowed by the active policy.",
                        remediation="Use an explicit tool allowlist and reject unregistered tools before execution.",
                        confidence=0.99,
                        evidence=[evidence_for_call(index, call)],
                    )
                )

            for key, value in flatten_strings(args):
                lowered_key = key.lower()
                if any(token in lowered_key for token in ("path", "file", "directory", "cwd")):
                    # Trace paths are protocol data, not host paths. Use
                    # POSIX canonicalization so Windows execution cannot turn
                    # ``../../`` into backslashes and evade traversal checks.
                    normalized = posixpath.normpath(value.replace("\\", "/"))
                    windows_absolute = bool(re.match(r"^[A-Za-z]:/", normalized))
                    absolute = os.path.isabs(normalized) or windows_absolute
                    traversal = normalized == ".." or normalized.startswith("../")
                    allowed_absolute = any(
                        normalized == prefix.rstrip("/") or normalized.startswith(prefix.rstrip("/") + "/")
                        for prefix in (p.replace("\\", "/") for p in policy.allowed_path_prefixes)
                        if prefix.startswith("/") or re.match(r"^[A-Za-z]:/", prefix)
                    )
                    if traversal or (absolute and not allowed_absolute):
                        findings.append(
                            Finding(
                                id=stable_finding_id(self.name, session.id, index, {"path": value}),
                                detector=self.name,
                                category="scope_violation",
                                severity=Severity.HIGH,
                                title="Filesystem path outside the allowed scope",
                                description=f"Tool '{tool}' referenced path '{value}' outside configured prefixes.",
                                remediation=(
                                    "Canonicalize paths against an allowed root and reject traversal before the tool executes."
                                ),
                                confidence=0.98,
                                evidence=[evidence_for_call(index, call)],
                            )
                        )

                if any(token in lowered_key for token in ("url", "endpoint", "target", "host")) and looks_like_url(value):
                    host = (urlparse(value).hostname or "").lower()
                    if policy.allowed_hosts and host not in {h.lower() for h in policy.allowed_hosts}:
                        findings.append(
                            Finding(
                                id=stable_finding_id(self.name, session.id, index, {"host": host}),
                                detector=self.name,
                                category="scope_violation",
                                severity=Severity.HIGH,
                                title="Network target outside the allowed scope",
                                description=f"Tool '{tool}' targeted host '{host}', which is not approved.",
                                remediation=(
                                    "Resolve and revalidate every network destination against an explicit host policy."
                                ),
                                confidence=0.98,
                                evidence=[evidence_for_call(index, call)],
                            )
                        )
        return findings
