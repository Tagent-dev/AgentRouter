# gateway service

**Plane:** Data plane

Entry point for AI requests. Terminates the public contract, attaches authenticated tenant context, normalizes the request into the canonical internal format and forwards it through the analyzer, policy and router chain. Streaming must pass through without buffering whole responses.

## Layout

```text
cmd/        service entry point
internal/   service-private packages
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
