from __future__ import annotations

import sys
from pathlib import Path

try:
    import gradio as gr
    import pandas as pd
except ImportError as exc:  # optional Space dependencies are not needed for CLI use
    gr = None
    pd = None
    _SPACE_IMPORT_ERROR = exc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_failure_atlas.compare import compare_reports  # noqa: E402
from agent_failure_atlas.loaders import load_trace_file  # noqa: E402
from agent_failure_atlas.policy import load_policy  # noqa: E402
from agent_failure_atlas.reporting import report_markdown  # noqa: E402
from agent_failure_atlas.scanner import scan_session  # noqa: E402

DEMO = ROOT / "examples" / "traces" / "combined_failures.jsonl"
POLICY = ROOT / "examples" / "policy.yaml"


def analyze(trace_path: str | None, policy_path: str | None):
    trace = Path(trace_path) if trace_path else DEMO
    policy = load_policy(Path(policy_path) if policy_path else POLICY)
    report = scan_session(load_trace_file(trace), policy)
    rows = []
    for finding in report.findings:
        evidence = finding.evidence[0] if finding.evidence else None
        rows.append(
            {
                "severity": finding.severity.value,
                "category": finding.category,
                "title": finding.title,
                "message_index": evidence.message_index if evidence else None,
                "evidence": evidence.excerpt if evidence else "",
                "confidence": finding.confidence,
            }
        )
    summary = {
        "session": report.session.id,
        "harness": report.session.harness,
        **report.metrics.model_dump(),
    }
    return summary, pd.DataFrame(rows), report_markdown(report), report.model_dump(mode="json")


def compare_traces(before_path: str | None, after_path: str | None, policy_path: str | None):
    """Render a bounded before/after finding diff without executing trace content."""
    if not before_path or not after_path:
        return {"error": "Select both before and after traces."}, pd.DataFrame()
    policy = load_policy(Path(policy_path) if policy_path else POLICY)
    comparison = compare_reports(
        scan_session(load_trace_file(Path(before_path)), policy),
        scan_session(load_trace_file(Path(after_path)), policy),
    )
    rows = [{"finding_id": finding_id, "status": status}
            for finding_id, status in comparison["finding_status"].items()]
    return comparison, pd.DataFrame(rows, columns=["finding_id", "status"])


if gr is not None:
    with gr.Blocks(title="Open Agent Failure Atlas") as demo:
        gr.Markdown(
        """
# Open Agent Failure Atlas
Deterministic trace-level checks for agent security, control, and reliability failures.

Upload a Hugging Face **Session Trace Simple Format (STS)** JSONL file, or run the included synthetic demonstration. Findings identify evidence positions; they are not a proof that unflagged traces are safe.
"""
        )
        with gr.Row():
            trace_file = gr.File(label="Agent trace (.jsonl)", file_types=[".jsonl"], type="filepath")
            policy_file = gr.File(label="Optional policy (.yaml)", file_types=[".yaml", ".yml"], type="filepath")
        run = gr.Button("Analyze trace", variant="primary")
        summary = gr.JSON(label="Run summary")
        findings = gr.Dataframe(label="Findings", interactive=False, wrap=True)
        narrative = gr.Markdown()
        raw = gr.JSON(label="Structured report")
        run.click(analyze, inputs=[trace_file, policy_file], outputs=[summary, findings, narrative, raw])
        gr.Examples(examples=[[str(DEMO), str(POLICY)]], inputs=[trace_file, policy_file])

        gr.Markdown("## Compare two traces\nFindings are classified as new, resolved, or persistent.")
        with gr.Row():
            before_file = gr.File(label="Before trace", file_types=[".jsonl"], type="filepath")
            after_file = gr.File(label="After trace", file_types=[".jsonl"], type="filepath")
        compare_button = gr.Button("Compare traces")
        comparison_summary = gr.JSON(label="Comparison")
        comparison_rows = gr.Dataframe(label="Finding changes", interactive=False)
        compare_button.click(compare_traces, inputs=[before_file, after_file, policy_file],
                             outputs=[comparison_summary, comparison_rows])

if __name__ == "__main__":
    if gr is None:
        print(f"Space dependencies unavailable: {_SPACE_IMPORT_ERROR}. Install with pip install -e '.[space]'.")
    else:
        demo.launch()
