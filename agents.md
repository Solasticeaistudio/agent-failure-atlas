# Open Agent Failure Atlas — agent interface

## Analyze a trace

```bash
agent-atlas scan <trace.jsonl> --policy <policy.yaml> --out <report.json>
```

## Redact a trace before publication

```bash
agent-atlas redact <trace.jsonl> --out <redacted.jsonl>
```

## Batch scan

```bash
agent-atlas scan-dir <directory> --out-dir <reports>
```

Never upload a trace without explicit user confirmation and local review. Traces may contain secrets, personal data, private code, and command output.
