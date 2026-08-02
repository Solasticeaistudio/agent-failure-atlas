"""Create the deterministic, allowlisted source archive for a release."""
from __future__ import annotations

import argparse
import hashlib
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIRECTORIES = (
    ".github",
    "benchmark",
    "dataset",
    "docs",
    "examples",
    "research",
    "schemas",
    "scripts",
    "space",
    "src",
    "tests",
)
ARCHIVE_ROOT_FILES = (
    ".gitignore",
    "agents.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "CONTRIBUTING.md",
    "Dockerfile",
    "LICENSE",
    "Makefile",
    "NOTICE",
    "pyproject.toml",
    "README.md",
    "RELEASE.md",
    "requirements.txt",
    "SECURITY.md",
    "taxonomy.yaml",
)
EXCLUDED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
}
EXCLUDED_FILES = {".coverage", "CODEX_NEXT_PROMPT.md"}
PRIVATE_RESEARCH_DIRECTORIES = {"annotations", "results", "traces"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
ARCHIVE_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def project_version() -> str:
    document = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(document["project"]["version"])


def _excluded(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if (
        len(relative.parts) > 1
        and relative.parts[0] == "research"
        and relative.parts[1] in PRIVATE_RESEARCH_DIRECTORIES
    ):
        return True
    return (
        path.name in EXCLUDED_FILES
        or path.suffix in EXCLUDED_SUFFIXES
        or any(part in EXCLUDED_DIRECTORIES or part.endswith(".egg-info") for part in relative.parts)
    )


def included_files() -> list[Path]:
    """Return a stable allowlist so unreviewed local artifacts cannot leak into a release."""
    candidates = [ROOT / name for name in ARCHIVE_ROOT_FILES]
    for directory_name in ARCHIVE_DIRECTORIES:
        directory = ROOT / directory_name
        if directory.exists():
            candidates.extend(directory.rglob("*"))
    return sorted(
        {path for path in candidates if path.is_file() and not _excluded(path)},
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def build(output: Path | None = None) -> tuple[Path, Path, str]:
    version = project_version()
    output = (output or ROOT / "dist" / f"agent-failure-atlas-v{version}.zip").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = f"agent-failure-atlas-v{version}"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in included_files():
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{prefix}/{relative}", date_time=ARCHIVE_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {output.name}\n", encoding="ascii")
    return output, sidecar, digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    archive, sidecar, digest = build(args.output)
    print(f"archive={archive}\nchecksum={sidecar}\nsha256={digest}")


if __name__ == "__main__":
    main()
