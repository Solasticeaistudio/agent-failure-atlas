from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Annotated

import typer

from .adapters import load_with_adapter
from .compare import compare_reports
from .hub import download_trace_dataset, publish_dataset
from .loaders import discover_trace_files, dump_sts, load_trace_file
from .policy import load_policy
from .redaction import redact_session
from .reporting import delta_findings_payload, load_json_report, report_markdown, write_json_report
from .scanner import scan_session

app = typer.Typer(
    name="agent-atlas",
    help="Trace-level security and reliability analysis for AI agents.",
    no_args_is_help=True,
)


@app.command()
def scan(
    trace: Annotated[Path, typer.Argument(help="Supported trace or exchange file")],
    policy: Annotated[Path | None, typer.Option("--policy", "-p")] = None,
    adapter: Annotated[str | None, typer.Option("--adapter")] = None,
    out: Annotated[Path | None, typer.Option("--out", "-o")] = None,
    markdown: Annotated[Path | None, typer.Option("--markdown")] = None,
    delta_findings: Annotated[Path | None, typer.Option("--delta-findings", help="Write DeltaStore-compatible findings JSON")] = None,
) -> None:
    session = load_with_adapter(trace, format_id=adapter)
    report = scan_session(session, load_policy(policy))
    if out:
        write_json_report(report, out)
    if markdown:
        markdown.parent.mkdir(parents=True, exist_ok=True)
        markdown.write_text(report_markdown(report), encoding="utf-8")
    if delta_findings:
        delta_findings.parent.mkdir(parents=True, exist_ok=True)
        delta_findings.write_text(json.dumps(delta_findings_payload(report), indent=2), encoding="utf-8")
    typer.echo(report.model_dump_json(indent=2) if not out else str(out))


@app.command("scan-dir")
def scan_dir(
    directory: Annotated[Path, typer.Argument(help="Directory containing JSONL traces")],
    policy: Annotated[Path | None, typer.Option("--policy", "-p")] = None,
    adapter: Annotated[str | None, typer.Option("--adapter")] = None,
    out_dir: Annotated[Path, typer.Option("--out-dir", "-o")] = Path("atlas-reports"),
) -> None:
    active_policy = load_policy(policy)
    files = discover_trace_files(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for path in files:
        try:
            report = scan_session(load_with_adapter(path, format_id=adapter), active_policy)
        except Exception as exc:  # keep batch scans moving and report failures explicitly
            summaries.append({"path": str(path), "error": str(exc)})
            continue
        destination = out_dir / f"{report.session.id}.report.json"
        write_json_report(report, destination)
        summaries.append(
            {
                "path": str(path),
                "report": str(destination),
                "findings": report.metrics.total_findings,
            }
        )
    typer.echo(json.dumps(summaries, indent=2))


@app.command("scan-hf")
def scan_hf(
    repo_id: Annotated[str, typer.Argument(help="Hugging Face dataset repo, e.g. org/name")],
    policy: Annotated[Path | None, typer.Option("--policy", "-p")] = None,
    revision: Annotated[str, typer.Option("--revision")] = "main",
    out_dir: Annotated[Path, typer.Option("--out-dir", "-o")] = Path("atlas-hf-reports"),
    token: Annotated[str | None, typer.Option("--token", envvar="HF_TOKEN")] = None,
) -> None:
    local = download_trace_dataset(repo_id, revision=revision, token=token)
    typer.echo(f"Downloaded {repo_id} to {local}")
    scan_dir(local, policy=policy, out_dir=out_dir)


@app.command()
def publish(
    dataset: Annotated[str, typer.Option("--dataset", help="Hub dataset repository ID")],
    report: Annotated[Path, typer.Option("--report", help="Prepared redacted artifact directory")],
    token: Annotated[str | None, typer.Option("--token", envvar="HF_TOKEN")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Confirm upload")] = False,
) -> None:
    """Publish explicitly prepared redacted benchmark artifacts to the Hub."""
    if not dry_run and not yes:
        raise typer.BadParameter("Pass --yes for an upload, or use --dry-run")
    try:
        typer.echo(json.dumps(publish_dataset(dataset, report, token=token, dry_run=dry_run), indent=2))
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command()
def compare(
    before: Annotated[Path, typer.Argument()],
    after: Annotated[Path, typer.Argument()],
    out: Annotated[Path | None, typer.Option("--out", "-o")] = None,
) -> None:
    result = compare_reports(load_json_report(before), load_json_report(after))
    payload = json.dumps(result, indent=2)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
        typer.echo(str(out))
    else:
        typer.echo(payload)


@app.command()
def redact(
    trace: Annotated[Path, typer.Argument()],
    out: Annotated[Path, typer.Option("--out", "-o")],
    policy: Annotated[Path | None, typer.Option("--policy", "-p")] = None,
    adapter: Annotated[str | None, typer.Option("--adapter")] = None,
) -> None:
    session = load_with_adapter(trace, format_id=adapter)
    redacted = redact_session(session, load_policy(policy))
    dump_sts(redacted, out)
    typer.echo(str(out))


@app.command()
def demo(
    out: Annotated[Path, typer.Option("--out", "-o")] = Path("demo-report.json"),
) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    trace = repository_root / "examples" / "traces" / "combined_failures.jsonl"
    policy_path = repository_root / "examples" / "policy.yaml"
    if not trace.exists():
        # Installed wheel: materialize a compact built-in trace.
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "demo.jsonl"
            trace.write_text(_BUILTIN_DEMO, encoding="utf-8")
            report = scan_session(load_trace_file(trace), load_policy(None))
    else:
        report = scan_session(load_trace_file(trace), load_policy(policy_path))
    write_json_report(report, out)
    typer.echo(f"Wrote {report.metrics.total_findings} findings to {out}")


_BUILTIN_DEMO = """{\"type\":\"session\",\"harness\":\"agent-failure-atlas\",\"id\":\"demo\",\"name\":\"Built-in demo\"}\n{\"type\":\"message\",\"message\":{\"role\":\"user\",\"content\":\"Inspect the workspace only.\"}}\n{\"type\":\"message\",\"message\":{\"role\":\"assistant\",\"content\":\"\",\"toolCalls\":[{\"id\":\"t1\",\"function\":{\"name\":\"delete_file\",\"arguments\":\"{\\\"path\\\":\\\"/etc/passwd\\\"}\"}}]}}\n{\"type\":\"message\",\"message\":{\"role\":\"tool\",\"toolCallId\":\"t1\",\"content\":\"ERROR: permission denied\"}}\n{\"type\":\"message\",\"message\":{\"role\":\"assistant\",\"content\":\"Done successfully.\"}}\n"""


if __name__ == "__main__":
    app()
