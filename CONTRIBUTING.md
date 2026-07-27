# Contributing

Contributions are welcome, especially:

- public trace fixtures with explicit consent and redaction,
- native harness adapters with conformance tests,
- failure-taxonomy proposals,
- detector evaluations on held-out data,
- privacy and secret-scanning improvements,
- and Hugging Face Space usability work.

Do not submit private traces, secrets, personal information, proprietary source code, or data you do not have permission to share.

## Development

```bash
pip install -e ".[dev,space]"
pytest
ruff check .
```

Every detector change should include a positive fixture, a negative fixture, and a statement of expected false-positive/false-negative behavior.
