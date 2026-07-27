from agent_failure_atlas.compare import compare_reports
from agent_failure_atlas.loaders import load_trace_file
from agent_failure_atlas.policy import load_policy
from agent_failure_atlas.scanner import scan_session


def test_compare_reports(root):
    policy = load_policy(root / "examples" / "policy.yaml")
    before = scan_session(load_trace_file(root / "examples" / "traces" / "scope_violation.jsonl"), policy)
    after = scan_session(load_trace_file(root / "examples" / "traces" / "safe_trace.jsonl"), policy)
    comparison = compare_reports(before, after)
    assert comparison["before_total"] == 1
    assert comparison["after_total"] == 0
    assert comparison["net_change"] == -1
