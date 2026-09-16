#!/usr/bin/env python3
"""The single quality command: format, lint, type check, unit tests.

Requirement 3.6 asks for one documented command that runs formatting, linting,
type checking and unit tests. That command is:

    make check          (or: python scripts/development/check.py)

Every step is invoked with no arguments because `pyproject.toml` already supplies
the file selection, the strictness settings and the coverage configuration. Any
argument added here would be a second, undocumented source of configuration.

Steps, in order:

    1. python -m ruff format --check .   formatting is checked, never rewritten
    2. python -m ruff check .            lint
    3. python -m mypy                    strict type check
    4. python -m pytest                  unit tests with coverage

Run-all, not fail-fast
----------------------
Every step runs even after an earlier one fails, and the exit status is non-zero
when any step failed. The reason is that these four steps are independent
verdicts on the same tree: a lint error tells you nothing about whether the type
checker is happy, so stopping at the first failure hides work that the developer
would have to discover one round trip at a time. The four steps together take
seconds on this repository, so there is no meaningful time saved by stopping
early.

`--fail-fast` is available for the case where that trade changes, for example a
CI job that only needs a pass/fail verdict as cheaply as possible.

Exit status:
    0   every step passed
    1   at least one step failed; the summary names each failing step
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Step:
    """One quality gate step and how to fix it."""

    name: str
    description: str
    argv: tuple[str, ...]
    remedy: str


# `sys.executable -m <tool>` rather than a bare `ruff`/`mypy`/`pytest` entry
# point, so the tools that run are the ones installed in the interpreter running
# this script rather than whatever happens to be first on PATH.
STEPS: tuple[Step, ...] = (
    Step(
        name="format",
        description="formatting (ruff format --check)",
        argv=(sys.executable, "-m", "ruff", "format", "--check", "."),
        remedy="python -m ruff format .",
    ),
    Step(
        name="lint",
        description="lint (ruff check)",
        argv=(sys.executable, "-m", "ruff", "check", "."),
        remedy="python -m ruff check --fix .",
    ),
    Step(
        name="typecheck",
        description="type check (mypy, strict)",
        argv=(sys.executable, "-m", "mypy"),
        remedy="fix the reported types; mypy runs in strict mode",
    ),
    Step(
        name="test",
        description="unit tests (pytest with coverage)",
        argv=(sys.executable, "-m", "pytest"),
        remedy="python -m pytest -x -vv",
    ),
)


@dataclass(frozen=True)
class Result:
    """Outcome of one step."""

    step: Step
    returncode: int
    seconds: float

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_step(step: Step) -> Result:
    """Run one step from the repository root and time it."""
    print(f"\n>>> {step.name}: {' '.join(step.argv)}", flush=True)
    started = time.monotonic()
    completed = subprocess.run(step.argv, cwd=ROOT, check=False)
    return Result(step=step, returncode=completed.returncode, seconds=time.monotonic() - started)


def run(steps: Sequence[Step], *, fail_fast: bool) -> list[Result]:
    """Run the steps, stopping at the first failure only when asked to."""
    results: list[Result] = []
    for step in steps:
        result = run_step(step)
        results.append(result)
        if fail_fast and not result.ok:
            print(f"\n--fail-fast: stopping after {step.name}", flush=True)
            break
    return results


def report(results: Sequence[Result], total: Sequence[Step]) -> int:
    """Print the summary and return the process exit status."""
    print("\n" + "=" * 72)
    print("quality gate summary")
    print("=" * 72)

    for result in results:
        status = "PASS" if result.ok else "FAIL"
        step = result.step
        print(f"  {status}  {step.name:<10} {step.description} ({result.seconds:.1f}s)")

    skipped = [step for step in total if step.name not in {r.step.name for r in results}]
    for step in skipped:
        print(f"  SKIP  {step.name:<10} {step.description}")

    failed = [result for result in results if not result.ok]
    if not failed:
        print("\nall checks passed")
        return 0

    print(f"\n{len(failed)} step(s) failed:")
    for result in failed:
        print(f"  - {result.step.name} (exit {result.returncode}): {result.step.remedy}")
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/development/check.py",
        description="Run formatting, lint, type check and unit tests as one command.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="stop at the first failing step instead of running all four",
    )
    args = parser.parse_args(argv)

    print(f"AgentRouter quality gate: {len(STEPS)} steps in {ROOT}")
    results = run(STEPS, fail_fast=bool(args.fail_fast))
    return report(results, STEPS)


if __name__ == "__main__":
    sys.exit(main())
