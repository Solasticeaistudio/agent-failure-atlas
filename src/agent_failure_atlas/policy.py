from __future__ import annotations

from pathlib import Path

import yaml

from .models import ScanPolicy


def load_policy(path: str | Path | None) -> ScanPolicy:
    if path is None:
        return ScanPolicy()
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Policy must be a YAML object: {path}")
    return ScanPolicy.model_validate(raw)
