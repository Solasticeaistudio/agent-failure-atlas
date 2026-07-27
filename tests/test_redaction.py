from agent_failure_atlas.loaders import load_trace_file
from agent_failure_atlas.redaction import redact_session


def test_redacts_secret_and_email(root):
    session = load_trace_file(root / "examples" / "traces" / "secret_exposure.jsonl")
    session.messages[0].content += " Contact person@example.com"
    redacted = redact_session(session)
    combined = "\n".join(message.content for message in redacted.messages)
    assert "hf_abcdefghijklmnopqrstuvwxyz123456" not in combined
    assert "person@example.com" not in combined
    assert "[REDACTED_SECRET]" in combined
    assert "[REDACTED_EMAIL]" in combined
    assert redacted.metadata["atlas_redacted"] is True


def test_redacts_secret_in_tool_arguments(root):
    session = load_trace_file(root / "examples" / "traces" / "prompt_injection.jsonl")
    redacted = redact_session(session)
    tool_args = str(redacted.messages[3].tool_calls[0].function.arguments)
    assert "hf_FAKEFAKEFAKEFAKEFAKE1234" not in tool_args
    assert "REDACTED_SECRET" in tool_args
