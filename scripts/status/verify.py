#!/usr/bin/env python3
"""Run the Verification_Evidence of every component recorded as `implemented`.

Requirement 1.6: the pipeline fails when a component is recorded as `implemented`
and its named evidence command is absent or exits non-zero. This is the
`status-evidence` CI gate.

Scope
-----
Only components at `implemented` are executed. A component at any other status is
claiming nothing, so running its commands would gate the build on work that is
openly declared incomplete. Commands declared by such components are counted and
reported as skipped, never silently ignored.

Nothing in the manifest is `implemented` today, so a normal run executes zero
commands. That is reported as `no evidence to run`, with the reason, rather than
as a pass: a gate that prints "passed" while doing nothing is exactly the kind of
green signal Requirement 2 exists to prevent.

Trust boundary
--------------
This script executes commands read from a YAML file, so it is worth stating
plainly what is trusted and why.

  * `docs/implementation-status.yaml` is a tracked file. Changing it requires a
    commit, and `.github/CODEOWNERS` puts that commit through review. The
    manifest is therefore trusted to the same degree as `Makefile`,
    `.github/workflows/*.yml` and `scripts/development/check.py`, all of which
    already run arbitrary commands in CI. An attacker who can add a command here
    can equally add one to the CI workflow, so this script is not the weak link
    and is not treated as a sandbox.
  * The commands are **not** trusted enough to hand to a shell. Every command is
    split with `shlex.split` and passed to `subprocess.run` as an argument list
    with `shell=False`. A manifest entry cannot chain with `;`, redirect, expand
    a variable, or glob: `pytest tests; rm -rf /` fails to find a program called
    `pytest tests; rm -rf /` instead of running two commands. That keeps the
    reviewable text of a command equal to what actually executes.
  * `--manifest` is offered so a test can point at a synthetic file. Pointing it
    at untrusted input executes that input's commands; it is a developer and CI
    tool, never something to expose to unreviewed data.
  * Each command runs from the repository root with a timeout, so a hung command
    fails the gate rather than the job's wall clock.

Usage:
    python scripts/status/verify.py
    python scripts/status/verify.py --component routing-engine
    python scripts/status/verify.py --all          # every declared command
    python scripts/status/verify.py --dry-run      # list without executing

Exit status:
    0   every executed command exited zero (including the zero-command case)
    1   at least one command failed, was unparseable, or its program was absent
    2   the manifest could not be read
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # direct execution: python scripts/status/verify.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.status.manifest import (
    IMPLEMENTED,
    MANIFEST_PATH,
    ROOT,
    ManifestError,
    component_id,
    load_manifest,
    select,
)

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_UNREADABLE = 2

DEFAULT_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class Command:
    """One evidence command and the component that claims it."""

    component: str
    name: str
    command: str

    @property
    def label(self) -> str:
        return f"{self.component}/{self.name}"


@dataclass(frozen=True)
class Outcome:
    """The result of one command. `argv` is empty when the command was unparseable."""

    command: Command
    returncode: int
    seconds: float
    detail: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def collect(entries: Sequence[dict[str, Any]], *, every_status: bool) -> tuple[list[Command], list[Command]]:
    """Split declared commands into the ones to run and the ones out of scope."""
    to_run: list[Command] = []
    skipped: list[Command] = []
    for entry in entries:
        evidence = entry.get("evidence")
        if not isinstance(evidence, list):
            continue
        in_scope = every_status or entry.get("status") == IMPLEMENTED
        for item in evidence:
            if not isinstance(item, dict):
                continue
            command = Command(
                component=component_id(entry),
                name=str(item.get("name", "<unnamed>")),
                command=str(item.get("command", "")),
            )
            (to_run if in_scope else skipped).append(command)
    return to_run, skipped


def parse(command: Command) -> list[str]:
    """Split a command into an argument list. Never handed to a shell.

    `posix=True` on every platform so a command reads the same way in the manifest
    as it does in CI. Backslashes are therefore escapes, which is why manifest
    paths are POSIX-style and the schema rejects a backslash.
    """
    argv = shlex.split(command.command, posix=True)
    if not argv:
        raise ValueError("command is empty")
    return argv


def run_one(command: Command, *, timeout: int) -> Outcome:
    """Execute one command from the repository root without a shell."""
    try:
        argv = parse(command)
    except ValueError as exc:
        return Outcome(command, returncode=127, seconds=0.0, detail=f"unparseable command: {exc}")

    if shutil.which(argv[0]) is None and not (ROOT / argv[0]).exists():
        return Outcome(
            command,
            returncode=127,
            seconds=0.0,
            detail=(
                f"program {argv[0]!r} not found on PATH; Requirement 1.6 treats absent "
                "evidence as a failure"
            ),
        )

    started = time.monotonic()
    try:
        completed = subprocess.run(  # noqa: S603 - argv list, shell=False; see module docstring
            argv,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return Outcome(
            command,
            returncode=124,
            seconds=time.monotonic() - started,
            detail=f"timed out after {timeout}s; evidence must be non-interactive and bounded",
        )
    except OSError as exc:
        return Outcome(
            command, returncode=127, seconds=time.monotonic() - started, detail=f"could not start: {exc}"
        )

    seconds = time.monotonic() - started
    if completed.returncode == 0:
        return Outcome(command, returncode=0, seconds=seconds, detail="")
    return Outcome(
        command,
        returncode=completed.returncode,
        seconds=seconds,
        detail=tail(completed.stdout, completed.stderr),
    )


def tail(stdout: str, stderr: str, *, lines: int = 20) -> str:
    """The last lines of output, which is where a test runner puts its verdict."""
    combined = "\n".join(part for part in (stdout or "", stderr or "") if part.strip())
    kept = [line for line in combined.splitlines() if line.strip()][-lines:]
    return "\n".join(kept)


def report(
    outcomes: Sequence[Outcome], skipped: Sequence[Command], *, every_status: bool
) -> int:
    """Print the summary and return the process exit status."""
    for outcome in outcomes:
        status = "PASS" if outcome.ok else "FAIL"
        print(f"  [{status}] {outcome.command.label}: {outcome.command.command} ({outcome.seconds:.1f}s)")

    if skipped:
        owners = sorted({command.component for command in skipped})
        print(
            f"\n  {len(skipped)} command(s) declared by {len(owners)} component(s) not recorded "
            "`implemented` were not run. Requirement 1.6 scopes evidence execution to "
            "components that claim completion."
        )

    if not outcomes:
        print(
            "\nstatus-evidence: no evidence to run. "
            + (
                "No component declares an evidence command."
                if not skipped
                else "No component is recorded `implemented`, so no completion claim needs "
                "substantiating yet."
            )
        )
        print(
            "This is not a pass on any component: zero commands ran. Use --all to run every "
            "declared command regardless of status."
        )
        return EXIT_OK

    failed = [outcome for outcome in outcomes if not outcome.ok]
    if failed:
        print(f"\nstatus-evidence: {len(failed)} of {len(outcomes)} command(s) failed:")
        for outcome in failed:
            print(f"\n  {outcome.command.label} (exit {outcome.returncode})")
            print(f"    command: {outcome.command.command}")
            for line in (outcome.detail or "no output").splitlines():
                print(f"    | {line}")
        print(
            "\nEither fix the component or lower its status. Requirement 1.6 does not allow "
            "`implemented` to stand on failing evidence."
        )
        return EXIT_FAILED

    scope = "declared" if every_status else "implemented"
    print(f"\nstatus-evidence: {len(outcomes)} {scope} command(s) passed")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/status/verify.py",
        description="Run the evidence commands of components recorded `implemented`.",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--component", help="restrict to one component id")
    parser.add_argument(
        "--all",
        action="store_true",
        dest="every_status",
        help="run every declared command, not only those of `implemented` components",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="list the commands that would run, and stop"
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    try:
        entries = select(load_manifest(args.manifest), args.component)
    except ManifestError as exc:
        print(f"status-evidence: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE

    to_run, skipped = collect(entries, every_status=bool(args.every_status))

    scope = "every declared" if args.every_status else "`implemented`"
    print(f"status-evidence: {len(to_run)} command(s) in scope ({scope}) from {args.manifest}")

    if args.dry_run:
        for command in to_run:
            print(f"  would run: {command.label}: {command.command}")
        if not to_run:
            print("  nothing in scope")
        return EXIT_OK

    outcomes = [run_one(command, timeout=int(args.timeout)) for command in to_run]
    return report(outcomes, skipped, every_status=bool(args.every_status))


if __name__ == "__main__":
    sys.exit(main())
