#!/usr/bin/env python3
"""Loading, lookup and formatting helpers shared by the four ledger scripts.

The Status_Manifest (`docs/implementation-status.yaml`) is the only
machine-readable record of what actually works. Four scripts read it, and each is
a separate CI gate:

    scripts/status/validate.py    schema plus the rules the schema cannot express
    scripts/status/render.py      generates docs/IMPLEMENTATION_STATUS.md
    scripts/status/verify.py      runs the evidence of every `implemented` entry
    scripts/status/check_dod.py   refuses `implemented` on an unmet DoD item

They share this module rather than four copies of the same loader, because four
copies would eventually disagree about what the manifest means, and the gates
would then contradict each other while all passing.

Nothing here executes anything or writes anything. Reading is separated from
acting so that a failure in one gate cannot be caused by another gate's side
effect.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]

MANIFEST_PATH = ROOT / "docs" / "implementation-status.yaml"
SCHEMA_PATH = ROOT / "docs" / "status-manifest.schema.json"
DOCUMENT_PATH = ROOT / "docs" / "IMPLEMENTATION_STATUS.md"
MASTER_SPEC_PATH = ROOT / "README.md"

IMPLEMENTED = "implemented"

# The manifest stores the underscore spelling; the generated document and every
# human-facing message use the display spelling of the requirements glossary.
STATUS_DISPLAY: dict[str, str] = {
    "not_started": "not started",
    "in_progress": "in progress",
    "implemented": "implemented",
    "blocked": "blocked",
}

# Fixed order for summaries: strongest claim first, so a reader sees what is
# claimed before what is not.
STATUS_ORDER: tuple[str, ...] = ("implemented", "in_progress", "not_started", "blocked")


class ManifestError(Exception):
    """A manifest could not be read, or is not the shape every gate assumes.

    Raised only for problems that stop a gate from running at all (unreadable
    file, invalid YAML, missing `components` list). Rule violations are returned
    as findings instead, so one run reports every one of them.
    """


def display_status(status: str) -> str:
    """Return the display spelling of a manifest status value."""
    return STATUS_DISPLAY.get(status, status)


def load_yaml_mapping(path: Path, *, what: str) -> dict[str, Any]:
    """Read a YAML mapping, turning every failure into an actionable message."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ManifestError(f"{what} not found: {path}") from exc
    except OSError as exc:
        raise ManifestError(f"{what} could not be read: {path}: {exc}") from exc

    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ManifestError(f"{what} is not valid YAML: {path}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise ManifestError(f"{what} must be a mapping at the top level: {path}")
    return loaded


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    """Load the Status_Manifest."""
    return load_yaml_mapping(path, what="status manifest")


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    """Load the committed manifest schema."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest schema not found: {path}") from exc

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest schema is not valid JSON: {path}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise ManifestError(f"manifest schema must be a JSON object: {path}")
    return loaded


def components(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the component entries, rejecting anything that is not a list of maps."""
    entries = manifest.get("components")
    if not isinstance(entries, list):
        raise ManifestError("manifest has no `components` list")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ManifestError(f"components[{index}] is not a mapping")
    return [dict(entry) for entry in entries]


def component_id(component: dict[str, Any]) -> str:
    """Return an entry's id, or a positional stand-in when it has none.

    A missing id is a schema violation reported by `validate.py`; the other gates
    still need something to name the entry in their own output.
    """
    value = component.get("id")
    return str(value) if isinstance(value, str) and value else "<entry with no id>"


def implemented_components(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Every entry claiming `implemented`.

    Requirements 1.6 and 1.7 are scoped to this set: an entry that claims nothing
    has nothing to substantiate.
    """
    return [c for c in components(manifest) if c.get("status") == IMPLEMENTED]


def select(manifest: dict[str, Any], component: str | None) -> list[dict[str, Any]]:
    """Return every entry, or just the one named, raising when the name is unknown."""
    entries = components(manifest)
    if component is None:
        return entries
    matches = [entry for entry in entries if entry.get("id") == component]
    if not matches:
        known = ", ".join(sorted(component_id(entry) for entry in entries))
        raise ManifestError(f"no component with id {component!r}. Known ids: {known}")
    return matches


def schema_findings(manifest: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Return every schema violation, ordered by position in the document.

    `iter_errors` yields in an unspecified order, so it is sorted by
    `absolute_path`; otherwise the same broken manifest would produce differently
    ordered output on different runs and a reviewer could not diff two failures.
    """
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(map(str, error.absolute_path)))
    return [f"{_pointer(error.absolute_path)}: {error.message}" for error in errors]


def _pointer(path: Any) -> str:
    parts = [str(part) for part in path]
    return "/".join(parts) if parts else "<root>"


def dod_items(component: dict[str, Any]) -> dict[str, bool]:
    """Return the twelve Component_DoD booleans of one entry."""
    raw = component.get("component_dod")
    if not isinstance(raw, dict):
        return {}
    return {str(key): bool(value) for key, value in raw.items()}


def not_applicable_items(component: dict[str, Any]) -> list[str]:
    """The DoD items recorded true because the 'where applicable' qualifier does not apply.

    Requirement 1.7 counts them as met, because they are met by definition. They
    are still reported separately: a true boolean that means "does not apply" and
    a true boolean that means "done" are different claims.
    """
    raw = component.get("dod_not_applicable")
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw]


def unmet_dod_items(component: dict[str, Any]) -> list[str]:
    """The DoD items recorded false, which Requirement 1.7 forbids under `implemented`."""
    return sorted(key for key, value in dod_items(component).items() if value is not True)


def dod_progress(component: dict[str, Any]) -> tuple[int, int]:
    """Return (satisfied, total) over the Component_DoD booleans."""
    items = dod_items(component)
    return sum(1 for value in items.values() if value), len(items)


def resolve_path(pattern: str, root: Path = ROOT) -> list[Path]:
    """Resolve a manifest path, expanding a '*' segment.

    `implementation`, `tests` and `placeholders[].path` all permit a '*' segment
    (`services/*/Dockerfile`, `sdk/*/tests`), so a caller that passed one to
    `Path()` would look for a literal asterisk and wrongly report it missing.
    """
    if "*" in pattern:
        return sorted(root.glob(pattern))
    candidate = root / pattern
    return [candidate] if candidate.exists() else []


def spec_modules(path: Path = MASTER_SPEC_PATH) -> list[str]:
    """The product modules of Master_Specification section 6, read from the source.

    Read rather than copied: a module added to section 6 must fail the coverage
    check in `validate.py`, which it cannot do if the expected list lives in the
    checker.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(f"Master_Specification could not be read: {path}: {exc}") from exc

    match = re.search(r"^#+ 6\. PRODUCT MODULES\s*$", text, re.MULTILINE)
    if match is None:
        raise ManifestError(f"section '6. PRODUCT MODULES' not found in {path}")

    fence = text.find("```", match.end())
    if fence == -1:
        raise ManifestError(f"section 6 of {path} has no fenced module list")
    body_start = text.index("\n", fence) + 1
    body_end = text.index("```", body_start)
    return [line.strip() for line in text[body_start:body_end].splitlines() if line.strip()]
