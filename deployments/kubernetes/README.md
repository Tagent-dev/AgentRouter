# Kubernetes Manifests

Base manifests plus per-environment overlays.

```text
base/                    shared manifests
overlays/development/    development patches
overlays/staging/        staging patches
overlays/production/     production patches
```

Deployment consolidates services rather than shipping one deployment per
directory in `services/`. Initial production workloads:

```text
agentrouter-gateway
agentrouter-router
agentrouter-control-api
agentrouter-worker
agentrouter-mcp
agentrouter-dashboard
```

Split further only when independent scaling justifies it.

## Status

Scaffold. No manifests written yet.
