# AgentRouter Helm Chart

Production installation path for self-hosted and customer-cloud deployments.

## Values files

```text
values.yaml              defaults and value contract
values-development.yaml  development overrides
values-staging.yaml      staging overrides
values-production.yaml   production overrides
```

## Supported surface (target)

```text
replicas
resources
autoscaling
ingress
TLS
secrets
database
redis
observability
network policies
```

## Secrets

Provider API keys, database credentials and Redis credentials are supplied by an
external secret manager or a pre-created Kubernetes Secret. Never commit them to
a values file.

## Status

Scaffold. `Chart.yaml` and the value contract exist; templates are placeholders,
so the chart does not install a working system yet.
