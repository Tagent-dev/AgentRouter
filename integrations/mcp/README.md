# MCP Integration

A thin door into AgentRouter. It holds no routing intelligence: every call
goes through the normal API, authentication, authorization, tenant context,
policy, rate limiting and audit path.

Planned tools (specification section 37):

```text
analyze_task
recommend_model
estimate_cost
get_available_models
check_policy
route_request
```

Resources expose read-only information such as model capabilities, routing
policies and usage. An MCP client must never be able to bypass enterprise policy.

## Layout

```text
server/
  tools/      tool implementations
  resources/  read-only resources
  prompts/    prompt definitions
  auth/       authentication and tenant context
  server/     server wiring and transport
tests/        MCP conformance and integration tests
```

## Status

Scaffold, not implemented.
