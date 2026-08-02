# Release process

The source archive is generated deterministically from an explicit allowlist:
files are sorted, metadata timestamps are fixed, and local or generated outputs
are excluded.

```bash
python scripts/build_release_archive.py
sha256sum -c dist/agent-failure-atlas-v0.2.0.zip.sha256
```

Run the complete release check first:

```bash
ruff check .
pytest
python scripts/run_benchmark.py
python -m compileall -q src space scripts tests
python scripts/build_release_archive.py
python scripts/verify_clean_install.py
```

The release archive includes the package, Space, synthetic traces, dataset card,
schemas, docs, tests, and research templates. It excludes `.git`, caches,
build outputs, editable-install metadata, `dist/`, and local `artifacts/`.
Excluding `artifacts/` prevents private scan output from being swept into a
release accidentally.
