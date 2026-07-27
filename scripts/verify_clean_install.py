"""Build and smoke-test a wheel in an isolated environment."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(root / "dist")], cwd=root, check=True)
    wheel = sorted((root / "dist").glob("agent_failure_atlas-*.whl"))[-1]
    with tempfile.TemporaryDirectory(prefix="atlas-clean-") as temp:
        env = Path(temp) / "env"
        subprocess.run([sys.executable, "-m", "venv", str(env)], check=True)
        python = env / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")
        subprocess.run([str(python), "-m", "pip", "install", str(wheel)], check=True)
        subprocess.run([str(python), "-c", "import agent_failure_atlas; print(agent_failure_atlas.__version__)"], check=True)
        subprocess.run([str(python), "-m", "agent_failure_atlas.cli", "demo",
                        "--out", str(Path(temp) / "demo.json")], check=True)
    print(f"clean-install-ok: {wheel}")


if __name__ == "__main__":
    main()
