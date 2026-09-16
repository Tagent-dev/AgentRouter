# Scripts

Repository automation.

```text
bootstrap/    First-run repository and environment setup
development/  Local development helpers
database/     Migration, seed and backup helpers
testing/      Test orchestration helpers
release/      Versioning and release helpers
deployment/   Deployment helpers
```

## Available now

```bash
python scripts/bootstrap/scaffold_repository.py   # recreate anything missing
python scripts/testing/validate_structure.py      # verify the tree
python scripts/development/check.py               # format, lint, types, tests
python scripts/development/health.py              # PostgreSQL and Redis reachability
```

The scaffold recreates any missing part of the target structure. Existing files
are never overwritten.
