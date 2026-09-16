#!/usr/bin/env python3
"""Generate docs/IMPLEMENTATION_STATUS.md from the Status_Manifest.

Requirement 1.4: the repository generates the Status_Record from the
Status_Manifest, and the pipeline fails when the committed document differs from
the generated output. `--check` is that gate (`status-render` in CI); the default
write mode is for local use.

Every fact in the output comes from the manifest. There is deliberately no
timestamp, no host name and no git revision: a generated document that changes on
every run cannot be compared with the committed copy, which would make the gate
either noisy or useless.

The manifest stores `not_started`; the document renders `not started`, the display
spelling of the requirements glossary. That translation lives in
`scripts/status/manifest.py` so the four gates agree on it.

Usage:
    python scripts/status/render.py            # write the document
    python scripts/status/render.py --check     # fail if the committed copy is stale
    python scripts/status/render.py --stdout    # print without writing

Exit status:
    0   written, or (with --check) the committed document matches
    1   with --check: the committed document is stale; a unified diff is printed
    2   the manifest could not be read
"""

from __future__ import annotations

import argparse
import difflib
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # direct execution: python scripts/status/render.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.status.manifest import (
    DOCUMENT_PATH,
    MANIFEST_PATH,
    STATUS_ORDER,
    ManifestError,
    component_id,
    components,
    display_status,
    dod_progress,
    load_manifest,
    not_applicable_items,
)

EXIT_OK = 0
EXIT_STALE = 1
EXIT_UNREADABLE = 2

GENERATED_NOTICE = (
    "<!-- Generated from docs/implementation-status.yaml by scripts/status/render.py. "
    "Do not edit: edit the manifest and re-run the generator. -->"
)

# Section order and headings. The manifest's `group` field carries no meaning
# beyond selecting one of these, which is why the schema documents it as
# presentation only.
GROUPS: tuple[tuple[str, str], ...] = (
    ("foundation", "Foundation"),
    ("services", "Services"),
    ("integrations", "Integrations"),
    ("clients", "Clients and interfaces"),
    ("platform", "Platform"),
)

PLACEHOLDER_KINDS: dict[str, str] = {
    "dockerfile": "Dockerfile",
    "helm_template": "Helm template",
    "kubernetes_manifest": "Kubernetes manifest",
    "terraform_module": "Terraform module",
    "api_contract": "API contract",
    "ci_workflow": "CI workflow",
    "make_target": "Make target",
    "directory": "Directory",
    "other": "Other",
}


def cell(value: object) -> str:
    """Render a value into a markdown table cell.

    Manifest prose is folded across lines and may contain a pipe, either of which
    would break the table, so newlines collapse to spaces and pipes are escaped.
    """
    text = " ".join(str(value or "").split())
    return text.replace("|", "\\|") if text else "-"


def code(value: object) -> str:
    text = " ".join(str(value or "").split())
    return f"`{text}`" if text else "-"


def table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> list[str]:
    """Render a markdown table with no column padding.

    Unpadded because the widths would otherwise shift with the longest cell, so an
    unrelated note edit would rewrite every row of the table and bury the real
    change in the diff.
    """
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def sort_key(component: dict[str, Any]) -> tuple[int, str]:
    """Order within a section: Implementation_Sequence step, then id."""
    phase = component.get("phase")
    return (int(phase) if isinstance(phase, int) else 0, component_id(component))


def dod_cell(component: dict[str, Any]) -> str:
    """Component_DoD progress, with the not-applicable count called out.

    Requirement 1.7 forbids `implemented` below twelve of twelve, so partial
    credit belongs here and never in the status column. An item true because the
    specification's "where applicable" qualifier does not apply is counted, and
    the count of such items is shown, so 12/12 cannot be read as twelve completed
    tasks.
    """
    satisfied, total = dod_progress(component)
    if not total:
        return "-"
    exempt = len(not_applicable_items(component))
    suffix = f" ({exempt} n/a)" if exempt else ""
    return f"{satisfied}/{total}{suffix}"


def component_rows(entries: Sequence[dict[str, Any]]) -> list[list[str]]:
    return [
        [
            cell(entry.get("name")),
            cell(entry.get("module")),
            display_status(str(entry.get("status", ""))),
            cell(entry.get("phase")),
            dod_cell(entry),
            code(entry.get("implementation")),
            cell(entry.get("notes")),
        ]
        for entry in sorted(entries, key=sort_key)
    ]


def summary_section(entries: Sequence[dict[str, Any]]) -> list[str]:
    counts = {status: 0 for status in STATUS_ORDER}
    for entry in entries:
        status = str(entry.get("status", ""))
        counts[status] = counts.get(status, 0) + 1

    product = sum(1 for entry in entries if entry.get("category") == "product_module")
    rows = [
        [display_status(status), str(counts.get(status, 0))]
        for status in STATUS_ORDER
        if counts.get(status, 0) or status == "implemented"
    ]

    lines = ["## Summary", ""]
    lines.extend(table(["Status", "Components"], rows))
    lines += [
        "",
        f"{len(entries)} tracked components: {product} of the product modules of "
        f"Master_Specification section 6, and {len(entries) - product} foundation entries "
        "that section 6 does not name.",
        "",
        "A status is a claim about working software. `implemented` additionally requires "
        "all twelve Component_DoD items and at least one passing Verification_Evidence "
        "command, which `scripts/status/verify.py` and `scripts/status/check_dod.py` "
        "enforce in CI. The DoD column records partial credit so it never leaks into the "
        "status column.",
    ]
    return lines


def group_sections(entries: Sequence[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    headers = ["Component", "Module", "Status", "Step", "DoD", "Implementation", "Notes"]
    for key, heading in GROUPS:
        members = [entry for entry in entries if entry.get("group") == key]
        if not members:
            continue
        lines += ["", f"## {heading}", ""]
        lines += table(headers, component_rows(members))
    return lines


def evidence_section(entries: Sequence[dict[str, Any]]) -> list[str]:
    rows: list[list[str]] = []
    for entry in sorted(entries, key=sort_key):
        evidence = entry.get("evidence")
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            if not isinstance(item, dict):
                continue
            rows.append(
                [
                    cell(entry.get("name")),
                    code(item.get("name")),
                    code(item.get("command")),
                ]
            )

    lines = ["", "## Verification evidence", ""]
    if not rows:
        lines.append(
            "No component names a Verification_Evidence command yet, so no completion "
            "claim in this document is substantiated by a re-runnable check."
        )
        return lines

    lines.append(
        "Named, re-runnable commands. `scripts/status/verify.py` runs the commands of every "
        "component recorded as `implemented`; the commands below belonging to components at "
        "another status are declared, not gated."
    )
    lines.append("")
    lines += table(["Component", "Evidence", "Command"], rows)
    return lines


def limitations_section(entries: Sequence[dict[str, Any]]) -> list[str]:
    lines = ["", "## Known limitations", ""]
    listed = [
        entry
        for entry in sorted(entries, key=sort_key)
        if isinstance(entry.get("limitations"), list) and entry["limitations"]
    ]
    if not listed:
        lines.append("No component records a known limitation.")
        return lines

    lines.append(
        "Requirement 1.8. An absent entry below is a positive claim that the component "
        "has no known limitation, not an absence of review."
    )
    for entry in listed:
        lines += ["", f"### {cell(entry.get('name'))}", ""]
        lines += [f"- {cell(limitation)}" for limitation in entry["limitations"]]
    return lines


def placeholders_section(entries: Sequence[dict[str, Any]]) -> list[str]:
    rows: list[list[str]] = []
    for entry in sorted(entries, key=sort_key):
        placeholders = entry.get("placeholders")
        if not isinstance(placeholders, list):
            continue
        for item in sorted(
            (p for p in placeholders if isinstance(p, dict)),
            key=lambda p: str(p.get("path", "")),
        ):
            kind = str(item.get("kind", ""))
            rows.append(
                [
                    code(item.get("path")),
                    PLACEHOLDER_KINDS.get(kind, kind or "-"),
                    cell(entry.get("name")),
                    cell(item.get("reason")),
                ]
            )

    lines = ["", "## Placeholder artifacts", ""]
    if not rows:
        lines.append("No placeholder artifact is recorded.")
        return lines

    lines.append(
        "Requirement 2.8. Each of these exists, parses or lints, and does not build, render "
        "or execute. They are listed so a green check on one of them cannot be mistaken for "
        "working software."
    )
    lines.append("")
    lines += table(["Path", "Kind", "Component", "Why it is a placeholder"], rows)
    return lines


def blocked_section(entries: Sequence[dict[str, Any]]) -> list[str]:
    blocked = [entry for entry in sorted(entries, key=sort_key) if entry.get("status") == "blocked"]
    if not blocked:
        return []
    lines = ["", "## Blocked", ""]
    lines += table(
        ["Component", "What blocks it"],
        [[cell(entry.get("name")), cell(entry.get("blocked_reason"))] for entry in blocked],
    )
    return lines


def render(manifest: dict[str, Any]) -> str:
    """Return the complete generated document."""
    entries = components(manifest)

    lines: list[str] = [
        "# Implementation Status",
        "",
        GENERATED_NOTICE,
        "",
        "Living record of what actually works, generated from "
        "`docs/implementation-status.yaml`. Change a status by editing the manifest and "
        "running `python scripts/status/render.py`; a hand edit here is reverted by the "
        "`status-render` CI gate.",
        "",
        "**Legend:** `not started` | `in progress` | `implemented` | `blocked`",
        "",
    ]
    lines += summary_section(entries)
    lines += group_sections(entries)
    lines += evidence_section(entries)
    lines += limitations_section(entries)
    lines += placeholders_section(entries)
    lines += blocked_section(entries)
    lines += [
        "",
        "## Remaining work",
        "",
        "Work follows the 46-step Implementation_Sequence of Master_Specification section "
        "132; the Step column above gives each component's step. The task sheet is "
        "`.kiro/specs/agentrouter-end-to-end-delivery/tasks.md`.",
    ]
    return "\n".join(lines) + "\n"


def write_document(text: str, path: Path) -> None:
    """Write with explicit LF endings, matching every other generated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def diff(committed: str, generated: str, path: Path) -> str:
    return "".join(
        difflib.unified_diff(
            committed.splitlines(keepends=True),
            generated.splitlines(keepends=True),
            fromfile=f"{path} (committed)",
            tofile=f"{path} (generated)",
            n=2,
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/status/render.py",
        description="Generate docs/IMPLEMENTATION_STATUS.md from the status manifest.",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=DOCUMENT_PATH)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed document differs from the generated output (CI gate)",
    )
    mode.add_argument("--stdout", action="store_true", help="print the document without writing")
    args = parser.parse_args(argv)

    try:
        generated = render(load_manifest(args.manifest))
    except ManifestError as exc:
        print(f"status-render: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE

    if args.stdout:
        sys.stdout.write(generated)
        return EXIT_OK

    if args.check:
        try:
            committed = args.output.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(
                f"status-render: {args.output} does not exist. "
                "Run: python scripts/status/render.py",
                file=sys.stderr,
            )
            return EXIT_STALE
        if committed != generated:
            print(f"status-render: {args.output} is stale.\n")
            print(diff(committed, generated, args.output))
            print(
                "Regenerate and commit the result: python scripts/status/render.py\n"
                "If the content is wrong, the manifest is wrong: fix "
                "docs/implementation-status.yaml, not the document."
            )
            return EXIT_STALE
        print(f"status-render: {args.output} matches the manifest")
        return EXIT_OK

    write_document(generated, args.output)
    print(f"status-render: wrote {args.output} ({len(generated.splitlines())} lines)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
