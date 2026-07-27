from agent_failure_atlas.loaders import load_trace_file
from agent_failure_atlas.policy import load_policy
from agent_failure_atlas.scanner import scan_session


def categories(root, name):
    report = scan_session(
        load_trace_file(root / "examples" / "traces" / name),
        load_policy(root / "examples" / "policy.yaml"),
    )
    return {finding.category for finding in report.findings}


def test_safe_trace_has_no_findings(root):
    assert categories(root, "safe_trace.jsonl") == set()


def test_scope_violation(root):
    assert categories(root, "scope_violation.jsonl") == {"scope_violation"}


def test_path_traversal(root):
    assert categories(root, "path_traversal.jsonl") == {"scope_violation"}


def test_approval_bypass(root):
    assert categories(root, "approval_bypass.jsonl") == {"approval_bypass"}


def test_prompt_injection(root):
    found = categories(root, "prompt_injection.jsonl")
    assert {"prompt_injection", "scope_violation", "secret_exposure"} <= found


def test_repeated_action(root):
    assert categories(root, "repeated_action.jsonl") == {"runaway_loop"}


def test_silent_failure(root):
    assert categories(root, "silent_failure.jsonl") == {"silent_tool_failure"}


def test_secret_exposure(root):
    assert categories(root, "secret_exposure.jsonl") == {"secret_exposure"}


def test_metrics(root):
    report = scan_session(
        load_trace_file(root / "examples" / "traces" / "combined_failures.jsonl"),
        load_policy(root / "examples" / "policy.yaml"),
    )
    assert report.metrics.total_tool_calls == 5
    assert report.metrics.total_findings >= 6
    assert report.metrics.findings_by_severity["critical"] >= 1
