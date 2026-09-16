# Cross-cutting Tests

Repository-level test suites. Service-local tests live in each
`services/<name>/tests` directory.

```text
unit/         Fast isolated tests owned alongside each module
integration/  Cross-component tests with real dependencies where practical
e2e/          Full chain: integration -> gateway -> analyzer -> policy -> router -> provider -> response
api/          Public API contract tests against the OpenAPI schema
mcp/          MCP server conformance and authorization tests
security/     Auth, authorization, tenant isolation, redaction and secret-handling tests
load/         Throughput and latency under load
chaos/        Provider failure, timeout, circuit breaker and fallback behaviour
fixtures/     Shared fixtures and test data
```

A component is not done because it compiles. Tests are part of the definition
of done, and unsupported external integrations are never marked complete.
