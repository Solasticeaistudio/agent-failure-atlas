import json
from pathlib import Path

import pytest

from agent_failure_atlas.adapters import load_with_adapter
from agent_failure_atlas.deltastore_exchange import EXCHANGE_VERSION
from agent_failure_atlas.loaders import TraceFormatError
from agent_failure_atlas.reporting import delta_findings_payload
from agent_failure_atlas.scanner import scan_session

ROOT = Path(__file__).parent / "fixtures" / "deltastore" / "exchange-v1.json"


def test_exchange_fixture_normalizes_and_preserves_lineage():
    session = load_with_adapter(ROOT)
    assert session.id == "trace-01-tool-output-injection"
    assert session.metadata["source_schema_version"] == EXCHANGE_VERSION
    assert session.metadata["exchange_event_ids"] == [
        "trace-01-tool-output-injection-e1",
        "trace-01-tool-output-injection-e2",
        "trace-01-tool-output-injection-e3",
    ]
    assert session.messages[1].tool_calls[0].id.endswith("call-1")


def test_exchange_findings_export_points_to_source_event():
    report = scan_session(load_with_adapter(ROOT))
    payload = delta_findings_payload(report)
    assert payload["trace_id"] == "trace-01-tool-output-injection"
    assert payload["findings"]
    assert payload["findings"][0]["evidence_event_ids"] == ["trace-01-tool-output-injection-e2"]


def test_unsupported_exchange_version_is_rejected(tmp_path):
    value = json.loads(ROOT.read_text(encoding="utf-8"))
    value["schema_version"] = "solstice-agent-trace-exchange/v2"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(TraceFormatError, match="Unsupported"):
        load_with_adapter(path)


@pytest.mark.parametrize("field", ["event_id", "sequence"])
def test_invalid_event_lineage_is_rejected(tmp_path, field):
    value = json.loads(ROOT.read_text(encoding="utf-8"))
    value["events"][1][field] = value["events"][0][field]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(TraceFormatError):
        load_with_adapter(path)
