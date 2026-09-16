# providers service

**Plane:** Provider gateway

The only component that talks to model providers. Every provider sits behind the same adapter interface so a provider API change stays contained in one adapter.

## Layout

```text
cmd/        service entry point
internal/
  gateway/        Provider-facing execution entry point
  adapters/       ProviderAdapter interface and shared adapter logic
  health/         Latency, error rate, availability and circuit state
  failover/       Provider failover execution
  normalization/  Request/response and error normalization
  openai/         OpenAI adapter
  anthropic/      Anthropic adapter
  google/         Google adapter
  azure/          Azure-hosted model adapter
  aws/            AWS-hosted model adapter
  compatible/     OpenAI-compatible and self-hosted endpoints
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
