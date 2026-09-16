# audit service

**Plane:** Governance

Append-only record of administrative and security-relevant events, immutable from normal customer workflows.

## Layout

```text
cmd/        service entry point
internal/
  events/   Audit event definitions
  storage/  Append-only storage
  queries/  Auditor-facing queries
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
