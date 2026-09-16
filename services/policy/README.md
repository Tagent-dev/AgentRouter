# policy service

**Plane:** Governance

Centralized policy decisions with deterministic conflict resolution across the platform, organization, department, team, user and per-request layers.

## Layout

```text
cmd/        service entry point
internal/
  engine/       Policy decision entry point
  rules/        Rule definitions and storage model
  evaluation/   Rule evaluation and decision output
  inheritance/  Policy hierarchy resolution
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
