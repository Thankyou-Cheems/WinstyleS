"""Run the WinstyleS release readiness checks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_commands(python_version: str, quick: bool) -> list[tuple[str, list[str]]]:
    uv_prefix = ["uv", "run", "--python", python_version, "--extra", "dev"]
    command_checks = [
        ("version", [*uv_prefix, "winstyles", "--version"]),
        ("scan", [*uv_prefix, "winstyles", "scan", "-f", "json"]),
    ]
    if quick:
        return command_checks

    return [
        ("black", [*uv_prefix, "black", "--check", "src", "tests"]),
        ("ruff", [*uv_prefix, "ruff", "check", "src", "tests"]),
        ("mypy", [*uv_prefix, "mypy", "src/winstyles"]),
        (
            "pytest",
            [
                *uv_prefix,
                "pytest",
                "tests",
                "-v",
                "--cov=src/winstyles",
                "--cov-report=term-missing",
                "--capture=no",
            ],
        ),
        *command_checks,
    ]


def run_check(name: str, command: Sequence[str]) -> int:
    print(f"\n== {name} ==", flush=True)
    print(" ".join(command), flush=True)
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print(f"\nFAILED: {name} exited with {result.returncode}", flush=True)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python",
        default="3.12",
        help="Python version passed to uv run (default: 3.12)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Only run winstyles --version and winstyles scan -f json",
    )
    args = parser.parse_args()

    for name, command in build_commands(args.python, args.quick):
        returncode = run_check(name, command)
        if returncode != 0:
            return returncode

    print("\nAll release checks passed.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
