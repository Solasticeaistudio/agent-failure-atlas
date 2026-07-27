# Codex prompt: Phase 2 hardening and Hugging Face launch

Work inside this repository. Preserve the narrow claim boundaries in `docs/LIMITATIONS.md`. Do not add model calls, external uploads, or unsupported native-format claims without explicit fixtures and tests.

## Objectives

1. Make the Space deploy cleanly from the repository root on Hugging Face.
2. Add streaming parsing and configurable maximum file/message sizes.
3. Add explicit native adapters for at least two public trace formats using sanitized fixtures.
4. Expand the synthetic set from 7 to 20 sessions across scope, injection, approval, recovery, and efficiency.
5. Add a benchmark command that reports per-category precision, recall, F1, and confusion data.
6. Add a trace comparison UI showing two runs side by side with new, resolved, and persistent findings.
7. Add tests for malformed tool arguments, Unicode, large messages, duplicate IDs, and path canonicalization.
8. Produce a deterministic release archive and SHA-256 checksum.

## Required constraints

- No silent heuristic parsing of unsupported harnesses.
- Every adapter must identify its format, reject incompatible input, and have positive and negative fixtures.
- Never execute trace content or tool arguments.
- Never upload traces automatically.
- Redaction must remain clearly labeled best effort.
- Keep the synthetic benchmark disclaimer visible in CLI, Space, and dataset card.
- Update schemas, docs, tests, and changelog with every behavior change.

## Acceptance criteria

- `pytest` passes.
- `python scripts/run_benchmark.py` passes and emits machine-readable results.
- `python space/app.py` starts without network credentials.
- `agent-atlas scan`, `scan-dir`, `scan-hf`, `redact`, `compare`, and `demo` have CLI tests.
- The root README provides a 10-second explanation, 2-minute quick start, architecture, limitations, and launch links.
- A `dist/` release archive is reproducible from a documented command.
