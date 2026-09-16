# scripts/development

Local development helpers

## check.py - the quality gate

```bash
make check                            # or: python scripts/development/check.py
```

Runs four steps in order, each with no arguments because `pyproject.toml` holds
every setting:

| Step        | Command                            |
| ----------- | ---------------------------------- |
| `format`    | `python -m ruff format --check .`  |
| `lint`      | `python -m ruff check .`           |
| `typecheck` | `python -m mypy`                   |
| `test`      | `python -m pytest`                 |

All four run even when an earlier one fails, and the summary names every failing
step with the command that fixes it. Exit status is non-zero when any step
failed. Pass `--fail-fast` to stop at the first failure.

This is the single documented command of requirement 3.6. `make lint` and
`make test` exist only for narrowing a failure; CI runs `make check`.

Formatting is checked, never rewritten. To rewrite in place: `make format`.

## health.py - backing service reachability

```bash
make health                           # or: python scripts/development/health.py
```

Reports whether PostgreSQL and Redis are reachable, reading `POSTGRES_HOST`,
`POSTGRES_PORT`, `REDIS_HOST`, `REDIS_PORT` and `REDIS_PASSWORD` from the
environment, then from `.env` for anything not already exported. Exit status is
non-zero when either is unreachable, and each failure prints remediation.

Both probes use raw sockets from the standard library. No database driver is
installed yet, and adding one for a health probe would put a runtime dependency
in the tree ahead of the code that needs it.

- PostgreSQL: TCP connect plus the protocol SSLRequest handshake. This proves a
  PostgreSQL server is listening. It does **not** verify credentials, the
  database name, or migration state.
- Redis: TCP connect plus a real `PING` over RESP, with `AUTH` first when
  `REDIS_PASSWORD` is set. A wrong password is reported rather than passed over.

Start the services with `make up`.

## Status

Implemented.
