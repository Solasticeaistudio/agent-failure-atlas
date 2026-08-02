import hashlib
import zipfile

from scripts.build_release_archive import ARCHIVE_TIMESTAMP, build, project_version


def test_release_archive_is_deterministic_and_clean(tmp_path):
    first, sidecar, first_digest = build(tmp_path / "first.zip")
    second, _, second_digest = build(tmp_path / "second.zip")

    assert first.read_bytes() == second.read_bytes()
    assert first_digest == second_digest == hashlib.sha256(first.read_bytes()).hexdigest()
    assert sidecar.read_text(encoding="ascii") == f"{first_digest}  {first.name}\n"

    prefix = f"agent-failure-atlas-v{project_version()}/"
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert all(info.date_time == ARCHIVE_TIMESTAMP for info in archive.infolist())

    assert f"{prefix}src/agent_failure_atlas/deltastore_exchange.py" in names
    assert f"{prefix}tests/test_deltastore_exchange.py" in names
    assert f"{prefix}scripts/build_release.py" not in names
    assert not any(
        forbidden in name
        for name in names
        for forbidden in (
            "/.ruff_cache/",
            "/build/",
            "/dist/",
            "/artifacts/",
            "/research/annotations/",
            "/research/results/",
            "/research/traces/",
            ".egg-info/",
            "CODEX_NEXT_PROMPT.md",
        )
    )
