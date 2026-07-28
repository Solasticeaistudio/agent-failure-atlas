# DeltaStore exchange adapter audit

The existing ingestion path is `adapters.load_with_adapter`, which performs
explicit format detection and then returns the existing `TraceSession` model.
STS and OpenAI JSONL continue through `loaders.load_trace_file`; native JSONL
formats use `NativeJSONLAdapter`.

The DeltaStore envelope is identified only by
`schema_version == "solstice-agent-trace-exchange/v1"`. The focused adapter in
`src/agent_failure_atlas/deltastore_exchange.py` validates required envelope
sections, event IDs, sequences, tool-call IDs, parent/evidence references,
checkpoints, branches, and bounded payload sizes before normalization.

Observable event summaries become existing `TraceMessage` records. Original
event IDs, event types, branch/checkpoint IDs, provenance, policy, redaction,
and normalization details are retained in session metadata. Tool calls and
tool results remain linked by their stable IDs; missing results are not
invented. Unknown fields are not interpreted as reasoning.

Atlas findings add DeltaStore-compatible `trace_id`, taxonomy and rule IDs, and
`evidence_event_ids`. The existing detector taxonomy and stable finding ID
logic are unchanged. The exchange adapter does not claim replayability or
causal reconstruction.

The browser adapter mirrors the same explicit detection and normalization
contract locally. It preserves source metadata and exports findings in the
DeltaStore handoff shape. Files are not uploaded or persisted.
