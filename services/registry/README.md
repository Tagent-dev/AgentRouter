# registry service

**Plane:** Model control

Source of truth for providers, models, capabilities and pricing. No other service hardcodes model capabilities or prices.

## Layout

```text
cmd/        service entry point
internal/
  models/        Model records and queries
  providers/     Provider records
  capabilities/  Capability and benchmark-derived attributes
  pricing/       Data-driven pricing records
  lifecycle/     Discovered -> benchmarking -> approved -> active -> deprecated -> retired
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
