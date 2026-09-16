"""Guards on the single quality command created by spec task 1.2.

Requirement 3.6 asks for one documented command that runs formatting, linting,
type checking and unit tests. These tests assert the properties of that command
that a reviewer cannot check by eye and that would silently rot:

  * the four steps are exactly the documented four, in the documented order, and
    each is invoked with no tool arguments so `pyproject.toml` stays the only
    source of configuration
  * a failing step is named in the summary and produces a non-zero exit status
  * every step still runs after an earlier failure (the run-all decision), while
    `--fail-fast` stops at the first one
  * `make check` and the Taskfile `check` task both invoke this script, so the
    documented entry point cannot drift from the implementation

The steps are never actually executed here: `run_step` is replaced, so these
tests stay fast and cannot recurse into pytest.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.development import check as quality

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_ORDER = ("format", "lint", "typecheck", "test")

EXPECTED_ARGV = {
    "format": ("-m", "ruff", "format", "--check", "."),
    "lint": ("-m", "ruff", "check", "."),
    "typecheck": ("-m", "mypy"),
    "test": ("-m", "pytest"),
}


def _fake_runner(failing: set[str]) -> tuple[list[str], object]:
    """Return a call log and a stand-in for run_step that fails named steps."""
    calls: list[str] = []

    def run_step(step: quality.Step) -> quality.Result:
        calls.append(step.name)
        return quality.Result(
            step=step,
            returncode=1 if step.name in failing else 0,
            seconds=0.0,
        )

    return calls, run_step


@pytest.fixture
def no_subprocess(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Fail loudly if a test reaches the real subprocess call."""

    def explode(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("a unit test must not spawn the real quality steps")

    monkeypatch.setattr(subprocess, "run", explode)
    yield


@pytest.mark.unit
def test_steps_are_the_documented_four_in_order() -> None:
    assert tuple(step.name for step in quality.STEPS) == EXPECTED_ORDER


@pytest.mark.unit
@pytest.mark.parametrize("step", quality.STEPS, ids=[s.name for s in quality.STEPS])
def test_each_step_runs_the_current_interpreter_with_no_tool_arguments(
    step: quality.Step,
) -> None:
    assert step.argv[0] == sys.executable, (
        "steps must run through the interpreter executing check.py, not a PATH entry point"
    )
    assert step.argv[1:] == EXPECTED_ARGV[step.name], (
        f"{step.name} must pass no extra arguments: pyproject.toml is the only "
        "source of file selection, strictness and coverage settings"
    )


@pytest.mark.unit
@pytest.mark.parametrize("step", quality.STEPS, ids=[s.name for s in quality.STEPS])
def test_each_step_offers_a_remedy(step: quality.Step) -> None:
    assert step.remedy.strip()


@pytest.mark.unit
def test_all_passing_returns_zero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    no_subprocess: None,
) -> None:
    calls, runner = _fake_runner(failing=set())
    monkeypatch.setattr(quality, "run_step", runner)

    assert quality.main([]) == 0
    assert calls == list(EXPECTED_ORDER)
    assert "all checks passed" in capsys.readouterr().out


@pytest.mark.unit
@pytest.mark.parametrize("failing", EXPECTED_ORDER)
def test_a_failing_step_is_named_and_exits_non_zero(
    failing: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    no_subprocess: None,
) -> None:
    calls, runner = _fake_runner(failing={failing})
    monkeypatch.setattr(quality, "run_step", runner)

    assert quality.main([]) == 1

    out = capsys.readouterr().out
    assert f"FAIL  {failing}" in out
    assert f"- {failing} (exit 1)" in out
    # Run-all: an early failure must not hide the later verdicts.
    assert calls == list(EXPECTED_ORDER)


@pytest.mark.unit
def test_fail_fast_stops_at_the_first_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    no_subprocess: None,
) -> None:
    calls, runner = _fake_runner(failing={"lint"})
    monkeypatch.setattr(quality, "run_step", runner)

    assert quality.main(["--fail-fast"]) == 1
    assert calls == ["format", "lint"]

    out = capsys.readouterr().out
    assert "SKIP  typecheck" in out
    assert "SKIP  test" in out


@pytest.mark.unit
def test_makefile_check_target_invokes_this_script() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "python scripts/development/check.py" in makefile
    assert "\ncheck:" in makefile


@pytest.mark.unit
def test_taskfile_check_task_invokes_this_script() -> None:
    taskfile = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    assert "python scripts/development/check.py" in taskfile


@pytest.mark.unit
@pytest.mark.parametrize(
    ("constant", "relative_path"),
    [
        ("CHECK_SCRIPT", "scripts/development/check.py"),
        ("HEALTH_SCRIPT", "scripts/development/health.py"),
    ],
)
def test_scaffold_reproduces_the_development_scripts_byte_for_byte(
    constant: str, relative_path: str
) -> None:
    """A fresh clone must get these files from the generator, unchanged.

    The generator holds each script as a text constant so `scaffold_repository.py`
    alone can rebuild the tree. That copy is the thing most likely to drift, so it
    is compared here rather than trusted.
    """
    scaffold_path = ROOT / "scripts" / "bootstrap" / "scaffold_repository.py"
    spec = importlib.util.spec_from_file_location("_scaffold", scaffold_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    embedded = getattr(module, constant)
    on_disk = (ROOT / relative_path).read_text(encoding="utf-8")
    assert embedded == on_disk, (
        f"{constant} in scaffold_repository.py no longer matches {relative_path}; "
        "update the constant so a scaffolded clone reproduces the file"
    )


@pytest.mark.unit
def test_ci_runs_the_single_quality_command() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "make check" in workflow, (
        "requirement 3.6 names one command; CI must run that command, not a copy of its steps"
    )
    assert "requirements-dev.txt" in workflow
