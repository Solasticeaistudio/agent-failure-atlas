# Changelog

## 0.1.0 — 2026-07-27

- Added Hugging Face STS and normalized JSONL loading.
- Added deterministic detectors for scope, approval, prompt injection, repetition, tool failure, and secret exposure.
- Added YAML policy support, local redaction, structured reporting, report comparison, and Hub dataset download.
- Added Gradio Space, synthetic smoke set, dataset card, schemas, CI, tests, and a 90-day research roadmap.
## 0.1.0 Phase 2 hardening

- Added bounded streaming JSONL limits and duplicate tool-ID rejection.
- Added explicit Hugging Face STS and OpenAI-compatible adapter entry points.
- Expanded the deterministic sanitized fixture set to 20 sessions.
- Added per-category precision, recall, F1, and confusion metrics.
- Added before/after persistent finding classification and a Space comparison view.
- Added deterministic source archive and SHA-256 generation.

All benchmark results remain synthetic smoke-test evidence only.
## 0.2.0 Phase 3

- Added opt-in, dry-run-first Hugging Face Dataset publication.
- Added annotation validation for reviewed real-trace samples.
- Added conservative Claude Code, Codex, Pi, and OTLP adapter contracts with source metadata.
- Added clean-install wheel smoke verification and expanded comparison metadata.
- No real traces or provider calls are included in this release.
