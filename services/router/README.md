# router service

**Plane:** Data plane - core IP

Selects the model. Consumes request analysis, registry candidates, policy decisions, cost, latency and health, then produces an explainable routing decision. Contains no provider-specific and no IDE-specific logic.

## Layout

```text
cmd/        service entry point
internal/
  engine/      Routing orchestration and decision assembly
  scoring/     Configurable scoring function and weights
  candidates/  Candidate generation and filtering
  strategies/  Routing modes (balanced, quality/cost/latency/reliability/policy first)
  escalation/  Quality-driven escalation to a stronger model
  fallback/    Provider/model failure fallback, policy aware
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
