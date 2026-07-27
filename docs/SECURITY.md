# Security and privacy boundaries

Agent traces may contain prompts, tool inputs, command output, local paths, screenshots, secrets, private code, and personal information. Treat every trace as sensitive until reviewed.

## Safe defaults

- Scanning is local.
- No trace is uploaded automatically.
- `agent-atlas redact` replaces common credential, email, and home-directory patterns while preserving STS structure.
- Redaction is defense in depth, not a guarantee. Review outputs before publication.
- Hub access tokens are read only from an explicit argument or `HF_TOKEN`.

## Threat model

The MVP assumes trace files themselves are untrusted input. It does not execute tool calls, import code from traces, or evaluate embedded expressions. JSON size and resource-bounding controls are still future hardening work.

Report vulnerabilities privately to `justin@solsticestudio.ai` before public disclosure.
