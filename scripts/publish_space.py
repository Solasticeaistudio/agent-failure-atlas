"""Publish the minimal credential-free Gradio Space bundle."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="atlas-space-") as directory:
        stage = Path(directory)
        shutil.copy2(ROOT / "space" / "app.py", stage / "app.py")
        shutil.copy2(ROOT / "space" / "README.md", stage / "README.md")
        shutil.copytree(ROOT / "src", stage / "src")
        shutil.copytree(ROOT / "examples", stage / "examples")
        (stage / "requirements.txt").write_text(
            "pydantic>=2.8,<3\n"
            "typer>=0.12,<1\n"
            "PyYAML>=6.0,<7\n"
            "huggingface-hub>=0.27\n"
            "gradio>=5,<7\n"
            "pandas>=2.0\n",
            encoding="utf-8",
        )
        api = HfApi()
        api.create_repo("solsticestudioai/agent-failure-atlas", repo_type="space",
                        space_sdk="gradio", exist_ok=True)
        api.upload_folder(repo_id="solsticestudioai/agent-failure-atlas", repo_type="space",
                          folder_path=str(stage), commit_message="Launch Agent Failure Atlas Space")
    print("space-uploaded: https://huggingface.co/spaces/solsticestudioai/agent-failure-atlas")


if __name__ == "__main__":
    main()
