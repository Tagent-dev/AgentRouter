# scripts/status

Completion ledger: validate, render, verify evidence, check the DoD

The completion ledger. `docs/implementation-status.yaml` is the
authoritative record; everything here reads it, and only `render.py` writes.

| Script         | Gate              | Enforces |
| -------------- | ----------------- | -------- |
| `validate.py`  | `status-schema`   | the manifest matches its schema, ids are unique, all 30 section 6 modules are covered (R1.3, R1.1) |
| `render.py`    | `status-render`   | the committed `docs/IMPLEMENTATION_STATUS.md` equals the generated output (R1.4) |
| `verify.py`    | `status-evidence` | every evidence command of an `implemented` component exits zero (R1.6) |
| `check_dod.py` | `status-dod`      | no `implemented` component has a false Component_DoD item (R1.7) |

```bash
python scripts/status/validate.py
python scripts/status/render.py            # write the document
python scripts/status/render.py --check    # fail when the committed copy is stale
python scripts/status/verify.py
python scripts/status/check_dod.py --show-progress
```

Each script is independently runnable, exits 0 on success and non-zero with an
actionable message otherwise, because each becomes a separate CI job. Shared
loading and formatting live in `manifest.py` so the four gates cannot disagree
about what the manifest means.

`verify.py` executes commands read from the manifest. It never uses a shell:
every command is split with `shlex` and passed as an argument list, so a manifest
entry cannot chain, redirect or glob. The trust boundary is written out in that
file's module docstring.

## Status

Validation, rendering, evidence verification and the DoD check are implemented.
The `postTaskExecution` completion hook (`on_task_complete.py`) is spec task 2.3
and does not exist yet, so status changes are still made by editing the manifest.
