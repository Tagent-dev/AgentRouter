# Security Policy

## Reporting a vulnerability

Report suspected vulnerabilities privately. Do not open a public issue.

Replace this placeholder with a monitored security contact before any external
release:

```text
security@example.invalid
```

Include what you can: affected component, reproduction steps, impact and any
proof of concept. Expect an acknowledgement while the report is triaged.

## Scope

The repository covers the AgentRouter platform: gateway, router, analyzer,
policy, providers, registry, cost engine, supporting services, integrations,
clients, SDKs, deployment assets and infrastructure code.

## Security commitments in this codebase

- Secrets never enter source control, container images, committed Helm values or
  logs.
- Tenant identity is always derived from authenticated identity. A
  client-supplied `tenant_id` is never trusted.
- Raw prompts and customer source code are not persisted by default.
- Authorization is enforced server side. The frontend is never trusted.
- Provider credentials are held in an external secret manager and are never
  exposed to ordinary developers.
- Administrative operations require stronger authentication and are audited.

## Compliance status

No certification currently exists. SOC 2, ISO 27001 and GDPR readiness work is
tracked under `security/compliance/`. Certification is never claimed before it is
actually held.

## Current state

The repository is at the scaffold stage. There is no deployed service and no
production surface to attack yet. See `docs/IMPLEMENTATION_STATUS.md`.
