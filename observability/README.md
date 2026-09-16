# Observability

OpenTelemetry-compatible instrumentation across all services, correlated by a
shared request/trace ID through gateway, analyzer, policy, router and provider.

## Platform metrics

```text
request_total
request_success_total
request_failure_total
request_latency
provider_latency
routing_latency
tokens_total
cost_total
fallback_total
escalation_total
policy_block_total
```

## Monitored signals

```text
request rate
error rate
P50 / P95 / P99 latency
provider latency and failures
routing latency
fallback rate
escalation rate
token usage
cost and savings
policy blocks
```

## Layout

```text
otel/        OpenTelemetry collector configuration and pipelines
prometheus/  Scrape configuration and recording rules
grafana/     Grafana provisioning
alerts/      Alert rules and routing
dashboards/  Dashboard definitions
runbooks/    Operational runbooks referenced by alerts
```

Raw prompts are not logged by default. Telemetry stores metadata.

## Status

Scaffold, not implemented.
