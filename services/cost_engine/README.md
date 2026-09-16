# cost_engine service

**Plane:** FinOps

Token accounting, cost estimation, actual cost calculation and savings against a configurable baseline. Savings numbers must never be inflated.

## Layout

```text
cmd/        service entry point
internal/
  pricing/      Pricing resolution from the registry
  estimation/   Pre-flight cost estimation
  calculation/  Post-flight actual cost
  savings/      Baseline comparison and savings reporting
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
