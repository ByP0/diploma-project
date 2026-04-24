from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def build_uvicorn_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.reload:
        command.extend(["--reload", "--reload-dir", str(PROJECT_ROOT / "app")])
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run backend after tests and migrations.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_step([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
    run_step([sys.executable, "-m", "alembic", "upgrade", "head"])
    run_step(build_uvicorn_command(args))


if __name__ == "__main__":
    main()
