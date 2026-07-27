from __future__ import annotations

import time
from collections import Counter
from collections.abc import Iterable

from .detectors import DEFAULT_DETECTORS
from .detectors.base import Detector
from .models import SEVERITY_RANK, ScanMetrics, ScanPolicy, ScanReport, TraceSession


def scan_session(
    session: TraceSession,
    policy: ScanPolicy | None = None,
    detectors: Iterable[Detector] | None = None,
) -> ScanReport:
    policy = policy or ScanPolicy()
    detectors = list(detectors or DEFAULT_DETECTORS)
    started = time.perf_counter()

    by_id = {}
    for detector in detectors:
        for finding in detector.scan(session, policy):
            by_id[finding.id] = finding
    findings = sorted(
        by_id.values(),
        key=lambda f: (-SEVERITY_RANK[f.severity], f.evidence[0].message_index if f.evidence else 10**9, f.id),
    )

    severity_counts = Counter(f.severity.value for f in findings)
    category_counts = Counter(f.category for f in findings)
    tool_calls = sum(len(message.tool_calls) for message in session.messages)
    elapsed_ms = (time.perf_counter() - started) * 1000

    metrics = ScanMetrics(
        total_messages=len(session.messages),
        total_tool_calls=tool_calls,
        total_findings=len(findings),
        findings_by_severity=dict(sorted(severity_counts.items())),
        findings_by_category=dict(sorted(category_counts.items())),
        scan_duration_ms=round(elapsed_ms, 3),
    )
    return ScanReport(
        policy_hash=policy.stable_hash(),
        session=session,
        findings=findings,
        metrics=metrics,
    )
