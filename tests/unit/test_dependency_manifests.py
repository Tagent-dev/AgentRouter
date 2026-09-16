"""Guards on the dependency manifests created by spec task 1.1.

These assert the two properties the spec asks for and that a human reviewer
cannot check reliably by eye:

  * every declared dependency is pinned exactly (`==`), never a range, because a
    range lets an upstream release change behaviour without a reviewed commit
  * `requirements-dev.txt` and the `dev` dependency group in `pyproject.toml`
    declare the same set of pins, so pip with and without PEP 735 support
    installs the same versions

They also assert that every workspace member named in `pyproject.toml` exists on
disk and is a legal Python module name, which is what makes the hyphen-to-
underscore rename enforced rather than merely done once.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
REQUIREMENTS_DEV = ROOT / "requirements-dev.txt"

# name, optional [extras], ==, version
PIN = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)(?P<extras>\[[^\]]+\])?==(?P<version>[^\s;]+)$")

MODULE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def _config() -> dict[str, object]:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _requirement_lines() -> list[str]:
    lines = []
    for raw in REQUIREMENTS_DEV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def _dev_group() -> list[str]:
    groups = _config()["dependency-groups"]
    assert isinstance(groups, dict)
    dev = groups["dev"]
    assert isinstance(dev, list)
    return [str(item) for item in dev]


def _normalize(name: str) -> str:
    """PEP 503 normalization, so PyYAML and pyyaml compare equal."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _pins(specifiers: list[str]) -> dict[str, str]:
    pins = {}
    for spec in specifiers:
        match = PIN.match(spec)
        assert match is not None, f"not an exact pin: {spec!r}"
        pins[_normalize(match.group("name"))] = match.group("version")
    return pins


@pytest.mark.unit
def test_pyproject_parses() -> None:
    assert _config()


@pytest.mark.unit
@pytest.mark.parametrize("specifier", _dev_group())
def test_dev_group_is_pinned_exactly(specifier: str) -> None:
    assert PIN.match(specifier) is not None, (
        f"{specifier!r} is not an exact `==` pin. Ranges are not permitted: "
        "they make the build non-reproducible."
    )


@pytest.mark.unit
@pytest.mark.parametrize("line", _requirement_lines())
def test_requirements_dev_is_pinned_exactly(line: str) -> None:
    assert PIN.match(line) is not None, (
        f"{line!r} in requirements-dev.txt is not an exact `==` pin."
    )


@pytest.mark.unit
def test_manifests_agree() -> None:
    assert _pins(_dev_group()) == _pins(_requirement_lines()), (
        "requirements-dev.txt and the [dependency-groups] dev group disagree. Edit both together."
    )


@pytest.mark.unit
def test_required_tooling_is_declared() -> None:
    declared = _pins(_dev_group())
    for tool in ("ruff", "mypy", "pytest", "pytest-cov", "coverage", "hypothesis"):
        assert _normalize(tool) in declared, f"{tool} is not declared"


@pytest.mark.unit
def test_mypy_is_strict() -> None:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    mypy = tool["mypy"]
    assert isinstance(mypy, dict)
    assert mypy["strict"] is True


@pytest.mark.unit
def test_coverage_is_enabled_in_the_default_pytest_run() -> None:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    pytest_config = tool["pytest"]
    assert isinstance(pytest_config, dict)
    ini = pytest_config["ini_options"]
    assert isinstance(ini, dict)
    addopts = ini["addopts"]
    assert isinstance(addopts, list)
    assert "--cov" in addopts


def _members() -> list[str]:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    agentrouter = tool["agentrouter"]
    assert isinstance(agentrouter, dict)
    workspace = agentrouter["workspace"]
    assert isinstance(workspace, dict)
    members: list[str] = []
    for key in ("packages", "services"):
        entries = workspace[key]
        assert isinstance(entries, list)
        members.extend(str(entry) for entry in entries)
    return members


@pytest.mark.unit
@pytest.mark.parametrize("member", _members())
def test_workspace_member_exists(member: str) -> None:
    assert (ROOT / member).is_dir(), f"declared workspace member is missing: {member}"


@pytest.mark.unit
@pytest.mark.parametrize("member", _members())
def test_workspace_member_is_importable_as_a_module(member: str) -> None:
    for part in Path(member).parts:
        assert MODULE_NAME.match(part) is not None, (
            f"{member!r} contains {part!r}, which is not a legal Python module "
            "name. Workspace directories are imported, so they must be snake_case."
        )
