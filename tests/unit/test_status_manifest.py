"""Guards on the status manifest and its schema, created by spec task 2.1.

The manifest (`docs/implementation-status.yaml`) is the only machine-readable
record of what actually works, and every later task proves completion through it.
So these tests assert the properties that make it trustworthy and that a reviewer
cannot check by eye:

  * the manifest validates against its committed schema (R1.3)
  * every one of the 30 product modules of Master_Specification section 6 has an
    entry, with the module list read out of the specification rather than copied
    here, so adding a module to section 6 fails this suite (R1.1)
  * `component_dod` carries exactly twelve items, matching the count of
    Master_Specification section 134, and the three that the specification
    qualifies with "where applicable" are the three the schema allows to be
    declared not applicable
  * the status enum is exactly the four Status_Values of the requirements
    glossary, in the underscore spelling the manifest uses
  * the schema *rejects* the mistakes that matter: an unknown key, the spaced
    spelling of a status, `implemented` with a false DoD item (R1.7),
    `implemented` with no evidence command (R1.2), and a foundation entry
    carrying a section 6 module number
  * a scaffolded clone reproduces both files byte for byte

Nothing here executes an evidence command. Running evidence is `scripts/status/verify.py`
in spec task 2.2; a unit suite that shelled out to pytest would recurse.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs" / "status-manifest.schema.json"
MANIFEST_PATH = ROOT / "docs" / "implementation-status.yaml"
MASTER_SPEC = ROOT / "README.md"

STATUS_VALUES = ("not_started", "in_progress", "implemented", "blocked")

# Master_Specification section 134 qualifies exactly these three items with
# "where applicable". They are the only items the schema lets an entry declare
# not applicable.
QUALIFIED_DOD_ITEMS = ("integration_tests", "metrics", "deployment")


def _schema() -> dict[str, Any]:
    loaded = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _manifest() -> dict[str, Any]:
    loaded = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _components() -> list[dict[str, Any]]:
    components = _manifest()["components"]
    assert isinstance(components, list)
    return [dict(component) for component in components]


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_schema())


def _errors(instance: object) -> list[str]:
    return [error.message for error in _validator().iter_errors(instance)]


def _fenced_block(heading: str) -> list[str]:
    """Return the lines of the first fenced block under a Master_Specification heading."""
    text = MASTER_SPEC.read_text(encoding="utf-8")
    start = text.index(f"# {heading}")
    opening = text.index("```", start)
    body_start = text.index("\n", opening) + 1
    body_end = text.index("```", body_start)
    return [line.strip() for line in text[body_start:body_end].splitlines() if line.strip()]


def _spec_modules() -> list[str]:
    """The 30 product modules of Master_Specification section 6, read from the source."""
    modules = _fenced_block("6. PRODUCT MODULES")
    assert len(modules) == 30, f"section 6 lists {len(modules)} modules, expected 30"
    return modules


def _spec_dod_items() -> list[str]:
    """The 12 Component_DoD items of Master_Specification section 134."""
    return [line.lstrip("\u2713 ").strip() for line in _fenced_block("134. DEFINITION OF DONE")]


def _product_modules() -> list[dict[str, Any]]:
    return [c for c in _components() if c["category"] == "product_module"]


def _minimal_component(**overrides: Any) -> dict[str, Any]:
    """A schema-valid `not_started` entry, for mutation by the rejection tests."""
    component: dict[str, Any] = {
        "id": "example-component",
        "name": "Example component",
        "category": "foundation",
        "group": "foundation",
        "status": "not_started",
        "phase": 1,
        "implementation": "services/example",
        "tests": "services/example/tests",
        "evidence": [],
        "component_dod": dict.fromkeys(_dod_keys(), False),
        "limitations": [],
    }
    component.update(overrides)
    return component


def _dod_keys() -> list[str]:
    required = _schema()["$defs"]["component_dod"]["required"]
    assert isinstance(required, list)
    return [str(key) for key in required]


def _wrap(component: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, "components": [component]}


# ---------------------------------------------------------------------------
# The schema itself
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_schema_is_a_valid_2020_12_schema() -> None:
    Draft202012Validator.check_schema(_schema())


@pytest.mark.unit
def test_schema_declares_exactly_the_four_status_values() -> None:
    assert tuple(_schema()["$defs"]["status"]["enum"]) == STATUS_VALUES, (
        "the status enum must be the four Status_Values of the requirements glossary, "
        "in the underscore spelling the design's manifest example uses"
    )


@pytest.mark.unit
def test_component_dod_declares_the_twelve_items_of_section_134() -> None:
    spec_items = _spec_dod_items()
    assert len(spec_items) == 12, f"section 134 lists {len(spec_items)} items, expected 12"
    assert len(_dod_keys()) == 12
    assert set(_schema()["$defs"]["component_dod"]["properties"]) == set(_dod_keys())


@pytest.mark.unit
def test_only_the_where_applicable_items_may_be_declared_not_applicable() -> None:
    qualified = [item for item in _spec_dod_items() if "where applicable" in item]
    assert len(qualified) == 3, (
        "section 134 qualifies three items with 'where applicable'; the schema's "
        "dod_not_applicable enum is derived from that count"
    )
    allowed = _schema()["$defs"]["component"]["properties"]["dod_not_applicable"]["items"]["enum"]
    assert tuple(allowed) == QUALIFIED_DOD_ITEMS


@pytest.mark.unit
def test_every_object_in_the_schema_forbids_unknown_keys() -> None:
    """A typo in a manifest key must be an error, not silently ignored data."""
    offenders: list[str] = []

    def walk(node: object, pointer: str) -> None:
        if isinstance(node, dict):
            declares_object_shape = node.get("type") == "object" and "properties" in node
            if declares_object_shape and node.get("additionalProperties") is not False:
                offenders.append(pointer or "#")
            for key, value in node.items():
                walk(value, f"{pointer}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{pointer}/{index}")

    walk(_schema(), "")
    assert offenders == [], f"objects missing additionalProperties: false at {offenders}"


# ---------------------------------------------------------------------------
# The manifest
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_manifest_validates_against_the_schema() -> None:
    errors = sorted(_validator().iter_errors(_manifest()), key=lambda e: list(e.absolute_path))
    rendered = "\n".join(
        f"  {'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    )
    assert errors == [], f"docs/implementation-status.yaml violates its schema:\n{rendered}"


@pytest.mark.unit
def test_component_ids_are_unique() -> None:
    """Not expressible in JSON Schema; the completion hook resolves components by id."""
    ids = [component["id"] for component in _components()]
    duplicates = sorted({name for name in ids if ids.count(name) > 1})
    assert duplicates == [], f"duplicate component ids: {duplicates}"


@pytest.mark.unit
def test_every_product_module_of_section_6_has_an_entry() -> None:
    """Requirement 1.1, with the expected list read out of the specification."""
    assert sorted(c["module"] for c in _product_modules()) == sorted(_spec_modules())


@pytest.mark.unit
def test_exactly_thirty_entries_are_product_modules() -> None:
    assert len(_product_modules()) == 30


@pytest.mark.unit
@pytest.mark.parametrize("component", _components(), ids=lambda c: str(c["id"]))
def test_status_is_a_status_value(component: dict[str, Any]) -> None:
    assert component["status"] in STATUS_VALUES


@pytest.mark.unit
@pytest.mark.parametrize("component", _components(), ids=lambda c: str(c["id"]))
def test_implemented_entries_name_evidence_and_locations(component: dict[str, Any]) -> None:
    """Requirement 1.2 restated over the data, independently of the schema."""
    if component["status"] != "implemented":
        return
    assert component["implementation"]
    assert component["tests"]
    assert component["evidence"], "an implemented component must name at least one evidence command"


@pytest.mark.unit
@pytest.mark.parametrize("component", _components(), ids=lambda c: str(c["id"]))
def test_implemented_entries_satisfy_every_dod_item(component: dict[str, Any]) -> None:
    """Requirement 1.7 restated over the data."""
    if component["status"] != "implemented":
        return
    unmet = sorted(key for key, value in component["component_dod"].items() if value is not True)
    assert unmet == [], f"{component['id']} claims implemented with unmet DoD items: {unmet}"


@pytest.mark.unit
@pytest.mark.parametrize("component", _components(), ids=lambda c: str(c["id"]))
def test_not_applicable_dod_items_are_recorded_true(component: dict[str, Any]) -> None:
    """A named exemption that is also false would say two different things."""
    for key in component.get("dod_not_applicable", []):
        assert component["component_dod"][key] is True, (
            f"{component['id']} lists {key} as not applicable but records it false"
        )


@pytest.mark.unit
@pytest.mark.parametrize("component", _components(), ids=lambda c: str(c["id"]))
def test_evidence_names_are_unique_within_a_component(component: dict[str, Any]) -> None:
    names = [entry["name"] for entry in component["evidence"]]
    assert len(names) == len(set(names)), f"{component['id']} repeats an evidence name"


@pytest.mark.unit
@pytest.mark.parametrize("component", _components(), ids=lambda c: str(c["id"]))
def test_declared_paths_are_repository_relative(component: dict[str, Any]) -> None:
    for field in ("implementation", "tests"):
        value = str(component[field])
        assert not value.startswith("/")
        assert "\\" not in value
        assert ".." not in value


@pytest.mark.unit
def test_no_component_claims_implemented_yet() -> None:
    """Rule 16: a scaffold is not an implementation.

    This will be deleted by the first task that genuinely completes a component.
    Until then it is the assertion that keeps the ledger honest while the ledger's
    own enforcement scripts (spec task 2.2) do not exist.
    """
    claimed = [c["id"] for c in _components() if c["status"] == "implemented"]
    assert claimed == [], (
        f"{claimed} claim implemented, but no evidence runner exists yet (spec task 2.2). "
        "Delete this test in the task that lands the first genuinely complete component."
    )


@pytest.mark.unit
def test_placeholder_artifacts_that_are_recorded_exist_on_disk() -> None:
    """Requirement 2.8: a recorded placeholder must be a real artifact.

    A '*' segment stands for a set of siblings, so it is expanded with glob.
    """
    missing: list[str] = []
    for component in _components():
        for placeholder in component.get("placeholders", []):
            pattern = str(placeholder["path"])
            if "*" in pattern:
                if not list(ROOT.glob(pattern)):
                    missing.append(pattern)
            elif not (ROOT / pattern).exists():
                missing.append(pattern)
    assert missing == [], f"recorded placeholders that do not exist: {missing}"


@pytest.mark.unit
def test_the_known_non_buildable_artifacts_are_all_recorded() -> None:
    """The specific placeholders Requirement 2.8 was written for."""
    recorded = {
        str(placeholder["path"])
        for component in _components()
        for placeholder in component.get("placeholders", [])
    }
    for expected in (
        "services/*/Dockerfile",
        "deployments/helm/agentrouter/templates/*.yaml",
        "deployments/kubernetes/base",
        "infrastructure/terraform/modules",
        "docs/api/openapi.yaml",
        "Makefile",
    ):
        assert expected in recorded, f"{expected} is a non-buildable placeholder and is unrecorded"


# ---------------------------------------------------------------------------
# The schema must reject the mistakes that matter
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_an_unknown_key_is_rejected() -> None:
    assert _errors(_wrap(_minimal_component(statuss="not_started")))


@pytest.mark.unit
@pytest.mark.parametrize("spelling", ["not started", "in progress", "NOT_STARTED", "done"])
def test_a_non_status_value_is_rejected(spelling: str) -> None:
    assert _errors(_wrap(_minimal_component(status=spelling)))


@pytest.mark.unit
def test_implemented_with_a_false_dod_item_is_rejected() -> None:
    """Requirement 1.7, expressed as a conditional subschema."""
    dod = dict.fromkeys(_dod_keys(), True)
    dod["unit_tests"] = False
    instance = _wrap(
        _minimal_component(
            status="implemented",
            component_dod=dod,
            evidence=[{"name": "example", "command": "python -m pytest -q"}],
        )
    )
    assert _errors(instance)


@pytest.mark.unit
def test_implemented_without_evidence_is_rejected() -> None:
    """Requirement 1.2: no command means no substantiated claim."""
    instance = _wrap(
        _minimal_component(
            status="implemented",
            component_dod=dict.fromkeys(_dod_keys(), True),
            evidence=[],
        )
    )
    assert _errors(instance)


@pytest.mark.unit
def test_implemented_with_full_dod_and_evidence_is_accepted() -> None:
    """The conditional must not be vacuously strict."""
    instance = _wrap(
        _minimal_component(
            status="implemented",
            component_dod=dict.fromkeys(_dod_keys(), True),
            evidence=[{"name": "example", "command": "python -m pytest -q"}],
        )
    )
    assert _errors(instance) == []


@pytest.mark.unit
def test_a_missing_dod_item_is_rejected() -> None:
    dod = dict.fromkeys(_dod_keys(), False)
    del dod["metrics"]
    assert _errors(_wrap(_minimal_component(component_dod=dod)))


@pytest.mark.unit
def test_a_foundation_entry_may_not_carry_a_section_6_module() -> None:
    assert _errors(_wrap(_minimal_component(module="09 Routing Engine")))


@pytest.mark.unit
def test_a_product_module_entry_must_carry_a_section_6_module() -> None:
    assert _errors(_wrap(_minimal_component(category="product_module")))


@pytest.mark.unit
@pytest.mark.parametrize("module", ["31 Something", "9 Routing Engine", "routing engine"])
def test_a_malformed_module_identifier_is_rejected(module: str) -> None:
    assert _errors(_wrap(_minimal_component(category="product_module", module=module)))


@pytest.mark.unit
def test_blocked_requires_a_reason() -> None:
    assert _errors(_wrap(_minimal_component(status="blocked")))
    assert (
        _errors(_wrap(_minimal_component(status="blocked", blocked_reason="evidence failed"))) == []
    )


@pytest.mark.unit
def test_a_blocked_reason_on_an_unblocked_component_is_rejected() -> None:
    assert _errors(_wrap(_minimal_component(blocked_reason="stale")))


@pytest.mark.unit
@pytest.mark.parametrize("phase", [0, 47, -1])
def test_a_phase_outside_the_46_step_sequence_is_rejected(phase: int) -> None:
    assert _errors(_wrap(_minimal_component(phase=phase)))


@pytest.mark.unit
@pytest.mark.parametrize("path", ["/etc/passwd", "../secrets", "services\\router", ""])
def test_a_path_escaping_the_repository_is_rejected(path: str) -> None:
    assert _errors(_wrap(_minimal_component(implementation=path)))


@pytest.mark.unit
def test_an_unpinned_version_is_rejected() -> None:
    manifest = copy.deepcopy(_manifest())
    manifest["version"] = 2
    assert _errors(manifest)


@pytest.mark.unit
def test_an_unqualified_dod_item_may_not_be_declared_not_applicable() -> None:
    assert _errors(_wrap(_minimal_component(dod_not_applicable=["unit_tests"])))


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("constant", "relative_path"),
    [
        ("STATUS_SCHEMA", "docs/status-manifest.schema.json"),
        ("STATUS_MANIFEST", "docs/implementation-status.yaml"),
    ],
)
def test_scaffold_reproduces_the_ledger_files_byte_for_byte(
    constant: str, relative_path: str
) -> None:
    scaffold_path = ROOT / "scripts" / "bootstrap" / "scaffold_repository.py"
    spec = importlib.util.spec_from_file_location("_scaffold_ledger", scaffold_path)
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
@pytest.mark.parametrize(
    "relative_path", ["docs/status-manifest.schema.json", "docs/implementation-status.yaml"]
)
def test_ledger_files_use_lf_line_endings(relative_path: str) -> None:
    """The scaffold writes LF; a CRLF copy would break the byte-for-byte guard."""
    assert b"\r\n" not in (ROOT / relative_path).read_bytes()


@pytest.mark.unit
@pytest.mark.parametrize(
    "relative_path", ["docs/status-manifest.schema.json", "docs/implementation-status.yaml"]
)
def test_structure_validator_requires_the_ledger_files(relative_path: str) -> None:
    source = (ROOT / "scripts" / "testing" / "validate_structure.py").read_text(encoding="utf-8")
    assert re.search(rf"^{re.escape(relative_path)}$", source, re.MULTILINE), (
        f"{relative_path} is not in the required-path list, so its deletion would go unnoticed"
    )
