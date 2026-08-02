# Phase 3: publication and real-trace validation

Atlas 0.2.0 adds publication plumbing and explicit native trace adapters while
keeping uploads opt-in. `agent-atlas publish --dry-run` previews a Dataset
upload; an upload requires `--yes`, a repository ID, and a Hub token. Files
must be explicitly redacted before upload. No command uploads user traces
automatically.

Supported adapter contracts are STS, normalized datasets, OpenAI chat JSONL,
DeltaStore exchange v1, Claude Code JSONL, Codex JSONL, Pi Agent JSONL, and a
conservative OTLP span JSONL shape. Native adapters preserve source format and
original event types. Ambiguous automatic detection is a hard error; use
`--adapter` with the format IDs documented in `docs/ADAPTER_CONTRACTS.md`.

Real-trace metrics require version 2 reviewer annotations. Real-trace rows are
bound to the reviewed file by SHA-256. Positive labels require evidence ranges,
and duplicate reviewer labels are rejected. At least two independent reviewers
are required by default.

`scripts/run_labeled_benchmark.py` reports pre-adjudication agreement,
conflicts, and unanimous-consensus metrics. Ambiguous, excluded,
single-reviewer, and conflicting items remain visible but do not enter
precision, recall, or F1. Missing denominators produce `null`, never a
synthetic perfect score.

The executable workflow, experiment manifest, held-out protocol, and templates
live in `research/`. Private traces, annotations, and results are ignored by
Git and excluded from release archives.

Public traces can contain prompts, private code, tool arguments, local paths,
screenshots, credentials, and personal data. Obtain consent, redact locally,
review the output, and publish only sanitized fixtures. The project does not
claim real-world detection quality until independently reviewed traces and
controlled external runs actually exist.
