from __future__ import annotations

import hashlib
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
DIST = ROOT / "dist"
ARCHIVE = DIST / f"agent-failure-atlas-v{VERSION}.zip"
CHECKSUM = DIST / f"agent-failure-atlas-v{VERSION}.zip.sha256"
PREFIX = f"agent-failure-atlas-v{VERSION}"
EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", "dist", "build"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def included_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in rel.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def build() -> tuple[Path, str]:
    DIST.mkdir(parents=True, exist_ok=True)
    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in included_files():
            rel = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{PREFIX}/{rel}")
            info.date_time = (2026, 7, 27, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if os.access(path, os.X_OK) else 0o644) << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    CHECKSUM.write_text(f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    return ARCHIVE, digest


if __name__ == "__main__":
    archive, digest = build()
    print(archive)
    print(digest)
