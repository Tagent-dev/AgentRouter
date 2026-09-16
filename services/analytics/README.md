# analytics service

**Plane:** Analytics

Consumes events off the critical path and produces usage, cost, routing and quality aggregates for dashboards and reports.

## Layout

```text
cmd/        service entry point
internal/
  ingestion/    Event stream consumption, idempotent by event ID
  aggregation/  Rollups by org, team, user, model, provider, period
  metrics/      Derived product and routing metrics
  reports/      Report generation
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
