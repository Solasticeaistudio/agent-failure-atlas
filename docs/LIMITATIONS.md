# Limitations

- The included benchmark is synthetic and constructed around the implemented rules.
- Deterministic detectors can miss semantic failures and produce false positives.
- “No findings” does not mean a trace is safe, correct, private, or policy-compliant.
- Prompt-injection detection is pattern based; it does not establish causality.
- Approval detection uses explicit phrases or structured IDs and is not a complete authorization system.
- Filesystem and network scope checks cover common argument shapes, not every tool schema.
- Secret redaction is best effort and cannot guarantee removal of all sensitive data.
- Raw native coding-agent adapters are not yet claimed beyond STS and normalized formats.
- This release does not rank models, call models, or claim frontier-model evaluation.
- The project is research and developer tooling, not a production security control or compliance certification.
