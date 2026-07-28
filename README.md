---
title: Open Agent Failure Atlas
emoji: 🧭
colorFrom: yellow
colorTo: indigo
sdk: gradio
sdk_version: 6.5.1
app_file: space/app.py
pinned: false
license: apache-2.0
---

# Open Agent Failure Atlas

> An open, evidence-linked toolkit for detecting security, control, and reliability failures in AI-agent traces.

## Public artifacts

- **GitHub:** [Solasticeaistudio/agent-failure-atlas](https://github.com/Solasticeaistudio/agent-failure-atlas)
- **Hugging Face Dataset:** [Synthetic benchmark](https://huggingface.co/datasets/solsticestudioai/agent-failure-atlas-benchmark)
- **Interactive Space:** [Agent Failure Atlas Static Space](https://huggingface.co/spaces/solsticestudioai/agent-failure-atlas) ([direct browser host](https://solsticestudioai-agent-failure-atlas.static.hf.space/))

The Atlas reads Hugging Face **Session Trace Simple Format (STS)** JSONL, normalized trace records, and `solstice-agent-trace-exchange/v1` envelopes, applies deterministic policy checks, and produces structured findings tied to exact trace positions. It is designed to complement the Hugging Face trace viewer: the viewer shows *what happened*; the Atlas begins answering *what failed, where, and under which policy*.

## Why this exists

Final-answer accuracy hides important agent failures. An agent can reach a plausible result while:

- calling a tool outside its allowed scope,
- acting without required approval,
- following instructions embedded in untrusted tool output,
- repeating the same action without progress,
- claiming success after a tool failure,
- or exposing a credential in the trace.

The first release intentionally uses deterministic, offline checks. It makes no model calls and does not claim general detector accuracy.

## Current MVP

- Native loader for Hugging Face STS JSONL
- Normalized dataset and OpenAI-style JSONL loaders
- Six evidence-linked detectors
- YAML policy configuration
- Local trace redaction
- JSON and Markdown reports
- Before/after report comparison
- Hugging Face dataset download support
- Gradio Space
- Synthetic smoke benchmark and tests
- Deterministic 20-session synthetic benchmark with per-category metrics
- Explicit native adapter interfaces for STS and OpenAI chat JSONL
- Bounded streaming limits and duplicate tool-call validation
- Before/after comparison with new, resolved, and persistent findings
- Opt-in Hugging Face Dataset publication with redaction gates
- Reviewer annotation schema for real-trace validation
- Conservative native adapters for Claude Code, Codex, Pi, and OTLP JSONL

## Detectors

| Category | What the MVP flags |
|---|---|
| Scope violation | Tools, absolute paths, or network hosts outside configured policy |
| Approval bypass | High-impact actions without explicit structured or nearby approval |
| Prompt injection | Instruction-like text in tool output and follow-up agent action |
| Runaway loop | Identical tool calls repeated past a bounded threshold |
| Silent tool failure | Error results followed by unsupported success claims or no recovery |
| Secret exposure | Common credential patterns persisted in assistant or tool messages |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev,space]"

agent-atlas scan examples/traces/combined_failures.jsonl \
  --policy examples/policy.yaml \
  --out artifacts/combined.report.json \
  --markdown artifacts/combined.report.md

agent-atlas redact examples/traces/secret_exposure.jsonl \
  --out artifacts/secret_exposure.redacted.jsonl

agent-atlas publish --dataset Solasticeaistudio/agent-failure-atlas-benchmark \
  --report artifacts/publishable --dry-run

python scripts/run_benchmark.py
pytest
```

The benchmark prints per-category precision, recall, F1, and a confusion
summary. It is deliberately synthetic and does not measure model capability.
Generate a reproducible release archive with:

```bash
python scripts/build_release_archive.py
```

Run the Space locally:

```bash
python space/app.py
```

## Scan a Hugging Face dataset

```bash
export HF_TOKEN=hf_...   # only needed for private or gated datasets
agent-atlas scan-hf trace-commons/agent-traces \
  --out-dir artifacts/trace-commons
```

The Hub already renders raw Claude Code, Codex, Pi, Hermes, and other supported sessions. Atlas currently analyzes STS and normalized records, with explicit STS and OpenAI-compatible adapter contracts that reject incompatible inputs rather than silently approximating them.

## Hugging Face-native output

Redacted sessions are written back to STS JSONL, so they can be uploaded to a Dataset or Storage Bucket and viewed with the Hub trace viewer:

```bash
agent-atlas redact session.jsonl --out session.redacted.jsonl
hf upload <username>/<dataset-name> session.redacted.jsonl . --repo-type dataset
```

Review every trace manually before publishing. Redaction is not a guarantee.

## Synthetic verification result

The included smoke set contains safe and intentionally failing fixtures. Run:

```bash
python scripts/run_benchmark.py
```

A perfect fixture result means the code recognizes the exact patterns it was designed around. It is **not** evidence of real-world precision, recall, or model safety.

Phase 3 real-trace validation is annotation-gated: unlabeled public traces are
never included in precision/recall/F1 denominators. Review and redact traces
locally before any optional Hub upload; see
[docs/PHASE3_REAL_TRACE_VALIDATION.md](docs/PHASE3_REAL_TRACE_VALIDATION.md).

## Project structure

```text
src/agent_failure_atlas/   package, detectors, CLI, Hub loader
examples/traces/           STS synthetic sessions
benchmark/                 labels and generated fixture result
space/                     Gradio Space
dataset/                  dataset card and synthetic index
 docs/                     architecture, security, limitations, roadmap
 tests/                    loader, detector, CLI, redaction, comparison tests
```

## What would make this research-grade

The next version should add independently labeled public traces, native harness adapters, held-out scenarios, human agreement analysis, semantic detectors with calibrated uncertainty, cross-model comparisons, and explicit separation of model, harness, tool, and policy effects. See [docs/ROADMAP.md](docs/ROADMAP.md).

## Safety and privacy

Agent traces can contain private code, personal data, local paths, credentials, and command output. Atlas never uploads a trace automatically. Read [docs/SECURITY.md](docs/SECURITY.md) before using public datasets or publishing results.

## Hugging Face references

- [Agent Traces on the Hub](https://huggingface.co/docs/hub/agent-traces)
- [Session Trace Simple Format](https://huggingface.co/docs/hub/session-traces-format)
- [Inspecting smolagents runs with OpenTelemetry](https://huggingface.co/docs/smolagents/en/tutorials/inspect_runs)
- [Gradio Spaces](https://huggingface.co/docs/hub/spaces-sdks-gradio)

## License

Apache License 2.0. Copyright 2026 Justin Meister, doing business as Solstice Studio.
