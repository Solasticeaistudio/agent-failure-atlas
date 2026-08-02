"""Build and smoke-test the current wheel in an isolated environment."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="atlas-clean-") as temp:
        temporary = Path(temp)
        distribution = temporary / "dist"
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(distribution)],
            cwd=root,
            check=True,
        )
        wheels = list(distribution.glob("agent_failure_atlas-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"Expected one freshly built wheel, found: {wheels}")
        wheel = wheels[0]
        env = temporary / "env"
        subprocess.run([sys.executable, "-m", "venv", str(env)], check=True)
        python = env / ("Scripts" if sys.platform == "win32" else "bin") / (
            "python.exe" if sys.platform == "win32" else "python"
        )
        subprocess.run(
            [str(python), "-m", "pip", "--disable-pip-version-check", "install", str(wheel)],
            check=True,
        )
        subprocess.run(
            [
                str(python),
                "-c",
                (
                    "import agent_failure_atlas; "
                    "import agent_failure_atlas.deltastore_exchange; "
                    "print(agent_failure_atlas.__version__)"
                ),
            ],
            check=True,
        )
        demo = temporary / "demo.json"
        subprocess.run(
            [str(python), "-m", "agent_failure_atlas.cli", "demo", "--out", str(demo)],
            check=True,
        )
        if not demo.is_file():
            raise RuntimeError("Installed-wheel demo did not produce a report")
        print(f"clean-install-ok: {wheel.name}")


if __name__ == "__main__":
    main()
