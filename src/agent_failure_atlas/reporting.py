from __future__ import annotations

from pathlib import Path

from .models import ScanReport


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
