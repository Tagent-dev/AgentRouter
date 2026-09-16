# analyzer service

**Plane:** Data plane

Describes what the request requires - task type, complexity, reasoning, context, tool and coding requirements, expected output, confidence. It never selects a model, and it never uses prompt length alone as a proxy for complexity.

## Layout

```text
cmd/        service entry point
internal/
  classifier/       Task type classification
  complexity/       Complexity estimation (low/medium/high/critical)
  capabilities/     Required capability derivation
  context/          Context size and shape requirements
  prompt_analysis/  Structural prompt analysis signals
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
