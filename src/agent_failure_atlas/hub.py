from __future__ import annotations

from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def download_trace_dataset(
    repo_id: str,
    revision: str = "main",
    allow_patterns: list[str] | None = None,
    token: str | None = None,
) -> Path:
    """Download JSON/JSONL files from a Hub dataset without uploading or mutating it."""
    path = snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        revision=revision,
        allow_patterns=allow_patterns or ["*.jsonl", "**/*.jsonl", "*.json", "**/*.json"],
        token=token,
    )
    return Path(path)


def publish_dataset(
    repo_id: str,
    source_dir: str | Path,
    *,
    token: str | None = None,
    commit_message: str = "Publish redacted Agent Failure Atlas benchmark artifacts",
    dry_run: bool = False,
) -> dict[str, str | bool]:
    """Publish a prepared, redacted artifact directory to a Hub dataset.

    The caller must prepare the directory; this function refuses files whose
    names look like raw traces unless they carry the explicit ``.redacted``
    marker. It never uploads automatically and supports a dry-run plan.
    """
    root = Path(source_dir)
    if not root.is_dir():
        raise ValueError(f"Publish source directory does not exist: {root}")
    files = sorted(p for p in root.rglob("*") if p.is_file())
    safe_metadata = {"metrics.json", "findings.json", "labels.json", "results.json", "summary.json"}
    unsafe = [p for p in files if p.suffix.lower() in {".jsonl", ".json"}
              and "redacted" not in p.name.lower()
              and p.name not in safe_metadata
              and "report" not in p.name.lower()]
    if unsafe:
        raise ValueError("Refusing to publish files that are not explicitly redacted: "
                         + ", ".join(str(p.relative_to(root)) for p in unsafe))
    result: dict[str, str | bool] = {"repo_id": repo_id, "source_dir": str(root),
                                     "files": str(len(files)), "dry_run": dry_run}
    if not dry_run:
        api = HfApi(token=token)
        api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)
        api.upload_folder(repo_id=repo_id, repo_type="dataset", folder_path=str(root),
                          commit_message=commit_message)
        result["uploaded"] = True
    return result
