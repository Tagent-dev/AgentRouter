# Configuration

Environment-driven configuration.

```text
development/
staging/
production/
```

Rules:

- Never embed API keys, passwords, production URLs or tenant IDs.
- Every environment uses separate credentials.
- Secrets resolve from environment variables or an external secret manager.
