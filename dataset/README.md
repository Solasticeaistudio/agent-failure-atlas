---
license: apache-2.0
task_categories:
- text-classification
language:
- en
tags:
- agent-traces
- ai-agents
- security
- evaluation
- synthetic
pretty_name: Open Agent Failure Atlas - Synthetic Smoke Set
size_categories:
- n<1K
---

# Open Agent Failure Atlas — Synthetic Smoke Set

A deterministic set of 20 sanitized synthetic agent traces designed to exercise the Open Agent Failure Atlas detectors across safe, scope, approval, injection, recovery, efficiency, secret, and traversal cases.

## Important limitation

This dataset is a software smoke test. A perfect score on it is **not** evidence of real-world precision, recall, robustness, or model safety. The examples are deliberately constructed around known detector rules.

## Fields

- `session_id`
- `trace_file`
- `expected_categories`
- `synthetic`
- `notes`

The raw STS trace files live under `examples/traces/` in the source repository.
