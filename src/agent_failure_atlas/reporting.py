from __future__ import annotations

from pathlib import Path

from .models import ScanReport


def delta_findings_payload(report: ScanReport) -> dict:
    """Return the stable, evidence-linked subset consumed by DeltaStore."""
    return {
        "trace_id": report.session.metadata.get("trace_id", report.session.id),
        "taxonomy_version": "agent-failure-atlas/v1",
        "findings": [
            {
                "finding_id": finding.id,
                "trace_id": finding.trace_id or report.session.id,
                "taxonomy_version": finding.taxonomy_version or "agent-failure-atlas/v1",
                "rule_id": finding.rule_id or finding.detector,
                "category": finding.category,
                "severity": finding.severity.value,
                "affected_policy": finding.affected_policy,
                "affected_resource": finding.affected_resource,
                "evidence_event_ids": finding.evidence_event_ids,
                "evidence_refs": finding.evidence_event_ids,
                "branch_id": finding.branch_id,
                "checkpoint_id": finding.checkpoint_id,
                "message": finding.description,
                "detector_metadata": finding.detector_metadata,
            }
            for finding in report.findings
        ],
    }


def write_json_report(report: ScanReport, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_json_report(path: str | Path) -> ScanReport:
    return ScanReport.model_validate_json(Path(path).read_text(encoding="utf-8"))


def report_markdown(report: ScanReport) -> str:
    lines = [
        f"# Agent Failure Atlas report: {report.session.name or report.session.id}",
        "",
        f"- Session: `{report.session.id}`",
        f"- Harness: `{report.session.harness}`",
        f"- Messages: {report.metrics.total_messages}",
        f"- Tool calls: {report.metrics.total_tool_calls}",
        f"- Findings: {report.metrics.total_findings}",
        "",
    ]
    if not report.findings:
        lines.append("No configured deterministic detector fired. This is not proof that the trace is safe.")
        return "\n".join(lines)
    for finding in report.findings:
        lines.extend(
            [
                f"## [{finding.severity.value.upper()}] {finding.title}",
                "",
                finding.description,
                "",
                f"**Category:** `{finding.category}`  ",
                f"**Detector:** `{finding.detector}`  ",
                f"**Confidence:** {finding.confidence:.2f}",
                "",
                f"**Suggested control:** {finding.remediation}",
                "",
            ]
        )
    return "\n".join(lines)
