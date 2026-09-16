# Local Agent

Developer-machine client that sits between the IDE and an AgentRouter
deployment.

```text
IDE
 |
 v
Local Agent  (auth, local config, secure credential storage, MCP, diagnostics)
 |
 v  HTTPS
AgentRouter cloud or private deployment
```

Credentials are stored using the OS secure store, never in plaintext config.

## Layout

```text
src/     client implementation
config/  default configuration
tests/   client tests
```

## Status

Scaffold, not implemented.
