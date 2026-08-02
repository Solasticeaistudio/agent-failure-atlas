# Native adapter contracts

Atlas adapters are deliberately narrow and fail closed. Auto-detection inspects
at most the first two bounded JSONL rows. Use `--adapter FORMAT_ID` when a
producer uses markers shared by more than one contract.

| Format ID | Required identifying event |
|---|---|
| `huggingface-sts` | First row has `type: session` |
| `openai-chat-jsonl` | Every inspected row has a `role` |
| `claude-code-jsonl` | `tool_use`, `tool_result`, or `assistant_message` |
| `codex-jsonl` | `function_call`, `function_result`, or `assistant_message` |
| `pi-agent-jsonl` | `tool_call`, `tool_output`, or `user_message` |
| `otlp-jsonl` | `event` or `type` is `span`; tool fields use `gen_ai.tool.*` |
| `solstice-agent-trace-exchange/v1` | JSON envelope declares that schema version |

Tool calls require a non-empty ID and tool name. Tool results require a call ID.
Duplicate call IDs and inputs with no normalizable events are rejected. The
sanitized contract fixtures live in `tests/fixtures/adapters/`.

These contracts do not promise compatibility with every producer release.
Hermes is intentionally unsupported until a stable, fixture-backed event
contract is selected. Convert unsupported sources to STS or normalized JSONL
instead of relying on heuristic coercion.
