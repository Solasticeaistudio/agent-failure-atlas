from typer.testing import CliRunner

from agent_failure_atlas.cli import app

runner = CliRunner()


def test_cli_scan(root, tmp_path):
    out = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "scan",
            str(root / "examples" / "traces" / "scope_violation.jsonl"),
            "--policy",
            str(root / "examples" / "policy.yaml"),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_cli_redact(root, tmp_path):
    out = tmp_path / "redacted.jsonl"
    result = runner.invoke(
        app,
        [
            "redact",
            str(root / "examples" / "traces" / "secret_exposure.jsonl"),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "REDACTED_SECRET" in out.read_text(encoding="utf-8")


def test_cli_demo(tmp_path):
    out = tmp_path / "demo.json"
    result = runner.invoke(app, ["demo", "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()


def test_cli_scan_with_explicit_adapter(root, tmp_path):
    out = tmp_path / "codex-report.json"
    result = runner.invoke(
        app,
        [
            "scan",
            str(root / "tests" / "fixtures" / "adapters" / "codex.jsonl"),
            "--adapter",
            "codex-jsonl",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
