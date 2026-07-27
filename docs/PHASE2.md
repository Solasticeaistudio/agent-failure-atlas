# Phase 2 hardening

This release keeps the Atlas offline and deterministic while making its input
boundary and evidence more explicit. JSONL parsing is bounded by file, row,
and line/message limits; duplicate tool-call identifiers are rejected because
they make tool-result attribution ambiguous. Trace adapters identify supported
STS and OpenAI-compatible JSONL inputs and reject incompatible formats.

The sanitized synthetic set contains 20 sessions spanning scope, approval,
prompt-injection, recovery, efficiency, secret, traversal, and safe cases.
`python scripts/run_benchmark.py` reports aggregate and per-category
precision/recall/F1 plus TP/FP/FN/TN confusion counts. These are fixture
conformance measurements, not real-world detector or model capability claims.

The Space includes a bounded before/after view that labels findings as new,
resolved, or persistent. A deterministic archive can be built with
`python scripts/build_release_archive.py`, producing a ZIP and SHA-256 sidecar.

The Space remains optional: if Gradio is not installed, `python space/app.py`
exits with an actionable installation message and never requires credentials.
