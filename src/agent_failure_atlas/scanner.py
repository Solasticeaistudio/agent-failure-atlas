from __future__ import annotations

import time
from collections import Counter
from collections.abc import Iterable

from .detectors import DEFAULT_DETECTORS
from .detectors.base import Detector
from .models import (
    SEVERITY_RANK,
    Evidence,
    Finding,
    ScanMetrics,
    ScanPolicy,
    ScanReport,
    Severity,
    TraceSession,
)


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
    if session.metadata.get("source_format") == "solstice-agent-trace-exchange/v1":
        event_ids = session.metadata.get("exchange_event_ids", [])
        taxonomy = session.metadata.get("exchange_policy", {}) or {}
        taxonomy_version = str(taxonomy.get("taxonomy_version") or "agent-failure-atlas/v1")
        for finding in findings:
            indexes = [item.message_index for item in finding.evidence]
            finding.trace_id = str(session.metadata.get("trace_id") or session.id)
            finding.taxonomy_version = taxonomy_version
            finding.rule_id = finding.detector
            finding.evidence_event_ids = [event_ids[index] for index in indexes if index < len(event_ids)]
            finding.detector_metadata = {"source_format": "solstice-agent-trace-exchange/v1"}
        # DeltaStore may carry an independently produced, evidence-linked
        # evaluator finding. Preserve it as an annotation; do not treat it as
        # a new detector or infer findings from model prose.
        for item in session.metadata.get("exchange_findings", []) or []:
            refs = item.get("evidence_event_ids") or item.get("evidence_lineage") or []
            evidence = []
            for ref in refs:
                if ref in event_ids:
                    index = event_ids.index(ref)
                    evidence.append(Evidence(message_index=index, role="evaluator", excerpt=f"DeltaStore evidence: {item.get('category', 'finding')}"))
            findings.append(Finding(
                id=str(item.get("finding_id") or item.get("id") or f"deltastore-{item.get('category', 'finding')}"),
                detector="deltastore-evaluator",
                category=str(item.get("category", "unknown")),
                severity=Severity(str(item.get("severity", "medium"))),
                title=str(item.get("category", "DeltaStore evaluator finding")),
                description=str(item.get("message") or item.get("description") or "Evidence-linked DeltaStore finding."),
                remediation="Review the linked DeltaStore evidence and policy outcome.",
                confidence=1.0,
                evidence=evidence,
                trace_id=str(session.metadata.get("trace_id") or session.id),
                taxonomy_version=taxonomy_version,
                rule_id=str(item.get("rule_id") or "deltastore-evaluator"),
                affected_policy=item.get("policy") or item.get("affected_policy"),
                affected_resource=item.get("affected_resource"),
                evidence_event_ids=list(refs),
                branch_id=item.get("branch_id"),
                checkpoint_id=item.get("checkpoint_id"),
                detector_metadata={"source": "deltastore_exchange_findings", "authoritative": False},
            ))

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
