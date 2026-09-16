# Security

Security spans identity, network, application, data, secrets, infrastructure,
tenant isolation and logging.

## Layout

```text
policies/           Internal security policies and standards
threat-model/       Threat models per plane and per trust boundary
compliance/         Control mapping for SOC 2, ISO 27001 and GDPR readiness
security-tests/     Security test definitions and evidence
incident-response/  Incident response procedures and severity definitions
```

## Non-negotiables

- Tenant identity is derived from authenticated identity. A client-supplied
  `tenant_id` is never trusted.
- Secrets never enter source control, images, committed values files or logs.
- Raw prompts and customer source are not persisted by default.
- The frontend is never trusted for authorization.
- Compliance certification is never claimed before it exists.

Vulnerability reporting: see `SECURITY.md` at the repository root.

## Status

Scaffold, not implemented.
