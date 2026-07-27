# Phase 3: publication and real-trace validation

Atlas 0.2.0 adds publication plumbing and explicit native trace adapters while
keeping uploads opt-in. `agent-atlas publish --dry-run` previews a Dataset
upload; an upload requires `--yes`, a repository ID, and a Hub token. Files
must be explicitly redacted before upload. No command uploads user traces
automatically.

Supported adapter contracts are STS, OpenAI chat JSONL, Claude Code JSONL,
Codex JSONL, Pi Agent JSONL, and a conservative OTLP span JSONL shape. Native
adapters preserve `source_format`, `source_schema_version`, and the original
event type in normalized session metadata. Ambiguous automatic detection is a
hard error; callers should select an adapter explicitly.

Real-trace metrics require reviewer annotations. Use the annotation schema in
`agent_failure_atlas.annotations` and `scripts/run_labeled_benchmark.py`.
Positive, negative, ambiguous, and excluded labels are kept distinct; only
reviewed positive/negative rows enter precision/recall/F1. Unlabeled traces do
not enter accuracy denominators.

Public traces can contain prompts, private code, tool arguments, local paths,
screenshots, credentials, and personal data. Obtain consent, redact locally,
review the output, and publish only sanitized fixtures. The project does not
claim real-world detection quality until an independently reviewed set exists.
