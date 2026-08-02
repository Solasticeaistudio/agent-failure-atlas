# Research validation workspace

This directory contains protocols and templates, not evaluation evidence. The
repository intentionally includes no raw real-world traces, human labels, model
credentials, or provider calls.

Private working directories are ignored by Git and excluded from release
archives:

- `research/traces/`
- `research/annotations/`
- `research/results/`

Use `experiment-manifest.template.json` to preregister each controlled
model + harness + tool set + policy + task configuration. Use
`annotations.template.jsonl` only as a field example; replace placeholder
values and obtain at least two genuinely independent reviews.

After local redaction and review:

```bash
python scripts/run_labeled_benchmark.py \
  --traces research/traces \
  --annotations research/annotations/reviews.jsonl \
  --policy examples/policy.yaml \
  --out research/results/consensus-metrics.json
```

The evaluator reports Fleiss-style kappa for binary positive/negative labels,
excludes ambiguous and single-reviewer items, and scores only unanimous labels
with the configured minimum reviewer count. It never turns missing denominators
into perfect metrics.
