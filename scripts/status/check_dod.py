#!/usr/bin/env python3
"""Fail when a component recorded `implemented` has a false Component_DoD item.

Requirement 1.7: a component satisfying fewer than all twelve items of the
Component_DoD is recorded with a status other than `implemented`. This is the
`status-dod` CI gate.

Why this exists when the schema already enforces it
---------------------------------------------------
`docs/status-manifest.schema.json` expresses the same rule as a conditional
subschema, so `status-schema` already rejects the violation. This gate exists for
two reasons. It names the offending items ("unit_tests, metrics are false"), where
the schema reports a failed conditional against a sub-object. And it does not
depend on the schema, so a change that weakened that conditional would still be
caught here rather than silently opening the door the requirement closes.

Not-applicable items
--------------------
Master_Specification section 134 qualifies exactly three items with "where
applicable": integration tests, metrics and deployment. An entry may record one of
them true and name it in `dod_not_applicable`. Such an item is met by definition,
so this gate does not treat it as unmet. It is reported separately anyway: 12/12
where three items do not apply is a different claim from 12/12 where twelve pieces
of work were done, and collapsing the two would let the checklist flatter itself.

Usage:
    python scripts/status/check_dod.py
    python scripts/status/check_dod.py --component routing-engine
    python scripts/status/check_dod.py --show-progress   # every component's tally

Exit status:
    0   no `implemented` component has a false item
    1   at least one does; each is named with its false items
    2   the manifest could not be read
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # direct execution: python scripts/status/check_dod.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.status.manifest import (
    IMPLEMENTED,
    MANIFEST_PATH,
    ManifestError,
    component_id,
    display_status,
    dod_progress,
    load_manifest,
    not_applicable_items,
    select,
    unmet_dod_items,
)

EXIT_OK = 0
EXIT_INCOMPLETE = 1
EXIT_UNREADABLE = 2

DOD_ITEM_COUNT = 12


def findings(entries: Sequence[dict[str, Any]]) -> list[str]:
    """Requirement 1.7 over the entries claiming `implemented`."""
    problems: list[str] = []
    for entry in entries:
        if entry.get("status") != IMPLEMENTED:
            continue
        name = component_id(entry)
        satisfied, total = dod_progress(entry)

        if total != DOD_ITEM_COUNT:
            problems.append(
                f"{name}: component_dod carries {total} item(s); Master_Specification "
                f"section 134 defines {DOD_ITEM_COUNT}"
            )

        unmet = unmet_dod_items(entry)
        if unmet:
            problems.append(
                f"{name}: claims `implemented` with {len(unmet)} unmet Component_DoD "
                f"item(s): {', '.join(unmet)}. Requirement 1.7 requires a status other than "
                "`implemented` until every item is satisfied."
            )
    return problems


def progress_lines(entries: Sequence[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        satisfied, total = dod_progress(entry)
        exempt = not_applicable_items(entry)
        suffix = f"  [n/a: {', '.join(sorted(exempt))}]" if exempt else ""
        lines.append(
            f"  {component_id(entry):<26} {display_status(str(entry.get('status', ''))):<12} "
            f"{satisfied}/{total}{suffix}"
        )
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/status/check_dod.py",
        description="Fail when an `implemented` component has a false Component_DoD item.",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--component", help="restrict to one component id")
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="print every component's Component_DoD tally, not only the failures",
    )
    args = parser.parse_args(argv)

    try:
        entries = select(load_manifest(args.manifest), args.component)
    except ManifestError as exc:
        print(f"status-dod: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE

    if args.show_progress:
        print("status-dod: Component_DoD progress")
        for line in progress_lines(entries):
            print(line)
        print()

    problems = findings(entries)
    if problems:
        print(f"status-dod: {len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return EXIT_INCOMPLETE

    claimed = [entry for entry in entries if entry.get("status") == IMPLEMENTED]
    exempt_total = sum(len(not_applicable_items(entry)) for entry in claimed)

    if not claimed:
        print(
            f"status-dod: no component of {len(entries)} is recorded `implemented`, so "
            "Requirement 1.7 has nothing to enforce. Partial Component_DoD credit is "
            "recorded per component; run with --show-progress to see it."
        )
        return EXIT_OK

    print(
        f"status-dod: {len(claimed)} component(s) recorded `implemented`, each with all "
        f"{DOD_ITEM_COUNT} Component_DoD items satisfied"
        + (
            f" ({exempt_total} item(s) across them true because the specification's "
            "'where applicable' qualifier does not apply)"
            if exempt_total
            else ""
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
