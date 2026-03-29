from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
NPM_COMMAND = "npm.cmd" if os.name == "nt" else "npm"
PROJECT_PYTHON = next(
    (
        candidate
        for candidate in (
            ROOT_DIR / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"),
            ROOT_DIR / "venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"),
        )
        if candidate.exists()
    ),
    Path(sys.executable),
)


def main() -> int:
    steps = [
        ("Running backend tests...", [str(PROJECT_PYTHON), "-m", "pytest", "-q"], BACKEND_DIR),
        ("Running frontend typecheck...", [NPM_COMMAND, "run", "typecheck"], FRONTEND_DIR),
        ("Running frontend build...", [NPM_COMMAND, "run", "build"], FRONTEND_DIR),
        ("Running browser smoke tests...", [NPM_COMMAND, "run", "smoke"], FRONTEND_DIR),
    ]

    for label, command, cwd in steps:
        run_step(label, command, cwd)

    print("\nAll checks passed.", flush=True)
    return 0


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f"\n{label}", flush=True)
    started_at = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, env=os.environ.copy(), check=False)
    elapsed = time.perf_counter() - started_at

    if completed.returncode != 0:
        print(f"{label} failed after {elapsed:.1f}s.", flush=True)
        raise SystemExit(completed.returncode)

    print(f"{label} done in {elapsed:.1f}s.", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
