# Terraform

Terraform provisions infrastructure; Helm then installs AgentRouter into the
resulting cluster.

## Modules

```text
modules/network/     VPC, subnets, routing and egress control
modules/kubernetes/  Managed Kubernetes cluster and node pools
modules/database/    Managed PostgreSQL, backups and private networking
modules/redis/       Managed Redis
modules/storage/     S3-compatible object storage
modules/monitoring/  Metrics, logs, traces and alerting backends
modules/security/    IAM, KMS and secret manager resources
```

## Environments

```text
environments/development/
environments/staging/
environments/production/
```

## Status

Scaffold, not implemented.
