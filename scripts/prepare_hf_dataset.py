"""Prepare the sanitized synthetic benchmark for Hub publication."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "hf-dataset"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data" / "traces").mkdir(parents=True)
    shutil.copy2(ROOT / "dataset" / "README.md", OUT / "README.md")
    shutil.copy2(ROOT / "benchmark" / "results.json", OUT / "data" / "synthetic_metrics.json")
    shutil.copy2(ROOT / "benchmark" / "synthetic" / "labels.jsonl", OUT / "data" / "synthetic_labels.jsonl")
    for trace in (ROOT / "benchmark" / "synthetic").glob("synthetic-*.jsonl"):
        shutil.copy2(trace, OUT / "data" / "traces" / trace.name)
    print(f"prepared {len(list((OUT / 'data' / 'traces').glob('*.jsonl')))} sanitized traces at {OUT}")


if __name__ == "__main__":
    main()
