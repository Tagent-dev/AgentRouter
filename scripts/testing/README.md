# scripts/testing

Test orchestration helpers

Contains `validate_structure.py`, which verifies every path in the target
repository structure exists, that all JSON and YAML parses, and that no
secret-bearing file is tracked by Git.

```bash
python scripts/testing/validate_structure.py
```

Requires PyYAML for the YAML checks; they are skipped if it is unavailable.

## Status

Structure validation implemented. Application test orchestration pending.
