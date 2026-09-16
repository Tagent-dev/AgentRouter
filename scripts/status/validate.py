#!/usr/bin/env python3
"""Validate the Status_Manifest against its schema and the rules JSON Schema cannot state.

Requirement 1.3: the manifest validates against a committed schema and the
pipeline fails when it does not. This is the `status-schema` CI gate.

Two checks live here rather than in the schema because JSON Schema cannot express
them:

  * **Component id uniqueness.** `uniqueItems` compares whole objects, so two
    entries sharing an id but differing anywhere else both pass. The completion
    hook (spec task 2.3) resolves a component by id, so a duplicate would make it
    update an arbitrary one of the two.
  * **Coverage of Master_Specification section 6.** Requirement 1.1 demands an
    entry for every product module. The schema can check the shape of a module
    identifier but cannot know which identifiers must be present. The expected
    list is read out of the specification, so adding a module to section 6 fails
    this gate until the manifest catches up.

Three cheaper consistency rules are checked alongside them, all of the same kind:
statements the data can contradict without violating the schema.

Usage:
    python scripts/status/validate.py
    python scripts/status/validate.py --manifest path --schema path

Exit status:
    0   the manifest is valid
    1   at least one violation; every violation found is listed
    2   the manifest or schema could not be read at all
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # direct execution: python scripts/status/validate.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.status.manifest import (
    MANIFEST_PATH,
    SCHEMA_PATH,
    ManifestError,
    component_id,
    components,
    load_manifest,
    load_schema,
    not_applicable_items,
    schema_findings,
    spec_modules,
    unmet_dod_items,
)

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_UNREADABLE = 2


def duplicate_id_findings(entries: Sequence[dict[str, Any]]) -> list[str]:
    """Component ids must be unique. Not expressible in JSON Schema."""
    counts = Counter(component_id(entry) for entry in entries)
    return [
        f"duplicate component id {name!r} appears {count} times; "
        "the completion hook resolves a component by id, so a duplicate is ambiguous"
        for name, count in sorted(counts.items())
        if count > 1
    ]


def module_coverage_findings(entries: Sequence[dict[str, Any]], expected: Sequence[str]) -> list[str]:
    """Requirement 1.1: every product module of Master_Specification section 6 has an entry."""
    findings: list[str] = []
    declared = [
        str(entry["module"])
        for entry in entries
        if entry.get("category") == "product_module" and isinstance(entry.get("module"), str)
    ]

    for missing in sorted(set(expected) - set(declared)):
        findings.append(
            f"Master_Specification section 6 module {missing!r} has no manifest entry "
            "(Requirement 1.1)"
        )
    for unknown in sorted(set(declared) - set(expected)):
        findings.append(
            f"manifest declares product module {unknown!r}, which is not in "
            "Master_Specification section 6"
        )

    repeated = sorted({name for name, count in Counter(declared).items() if count > 1})
    findings.extend(f"module {name!r} is claimed by more than one entry" for name in repeated)
    return findings


def consistency_findings(entries: Sequence[dict[str, Any]]) -> list[str]:
    """Statements the data can contradict while still matching the schema."""
    findings: list[str] = []
    for entry in entries:
        name = component_id(entry)

        evidence = entry.get("evidence")
        if isinstance(evidence, list):
            names = [
                str(item["name"])
                for item in evidence
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            ]
            repeated = sorted({value for value, count in Counter(names).items() if count > 1})
            findings.extend(
                f"{name}: evidence name {value!r} is used twice; the completion hook "
                "writes an evidence name into the task sheet, so it must identify one command"
                for value in repeated
            )

        # A named exemption that is also recorded false says two different things.
        dod = entry.get("component_dod")
        if isinstance(dod, dict):
            for item in not_applicable_items(entry):
                if dod.get(item) is not True:
                    findings.append(
                        f"{name}: {item!r} is listed in dod_not_applicable but recorded "
                        "false; an item that does not apply is true by definition"
                    )

        # Requirement 1.7 repeated over the data. The schema enforces it with a
        # conditional subschema; this restates it so a schema regression that
        # weakened that conditional still fails the gate.
        if entry.get("status") == "implemented":
            unmet = unmet_dod_items(entry)
            if unmet:
                findings.append(
                    f"{name}: claims implemented with unmet Component_DoD items: "
                    f"{', '.join(unmet)} (Requirement 1.7)"
                )
    return findings


def validate(manifest: dict[str, Any], schema: dict[str, Any], spec: Sequence[str]) -> list[str]:
    """Return every finding: schema violations first, then the rules above."""
    findings = schema_findings(manifest, schema)
    entries = components(manifest)
    findings.extend(duplicate_id_findings(entries))
    findings.extend(module_coverage_findings(entries, spec))
    findings.extend(consistency_findings(entries))
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/status/validate.py",
        description="Validate docs/implementation-status.yaml (CI gate: status-schema).",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument(
        "--skip-module-coverage",
        action="store_true",
        help="skip the section 6 coverage check, for validating a synthetic manifest",
    )
    args = parser.parse_args(argv)

    try:
        manifest = load_manifest(args.manifest)
        schema = load_schema(args.schema)
        spec = [] if args.skip_module_coverage else spec_modules()
    except ManifestError as exc:
        print(f"status-schema: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE

    try:
        findings = validate(manifest, schema, spec)
        entry_count = len(components(manifest))
    except ManifestError as exc:
        print(f"status-schema: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE

    if findings:
        print(f"status-schema: {len(findings)} problem(s) in {args.manifest}:")
        for finding in findings:
            print(f"  - {finding}")
        print(
            "\nFix the manifest, not the schema, unless the rule itself is wrong. "
            "The schema is docs/status-manifest.schema.json."
        )
        return EXIT_INVALID

    checked = "schema" if args.skip_module_coverage else "schema, ids, section 6 coverage"
    print(f"status-schema: {entry_count} component(s) valid ({checked})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
