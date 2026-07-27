# Release process

The source archive is generated deterministically: files are sorted, metadata timestamps are fixed, and caches/build outputs are excluded.

```bash
python scripts/build_release.py
sha256sum -c dist/agent-failure-atlas-v0.1.0.zip.sha256
```

Run the complete release check first:

```bash
pytest
python scripts/run_benchmark.py
python -m compileall -q src space scripts tests
python scripts/build_release.py
```

The release archive includes the package, Space, synthetic traces, dataset card, schemas, docs, tests, and sample reports. It excludes `.git`, caches, editable-install metadata, and the `dist/` directory itself.
