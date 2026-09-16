# CLI

`agentrouter` command line interface. All commands support machine-readable
output.

## Commands

```text
login/      Authenticate and store credentials securely
logout/     Revoke the local session
configure/  Set endpoint, organization and defaults
status/     Show connection, org and routing status
models/     List models visible under current policy
providers/  List providers and health
route/      Route a request and show the decision
usage/      Show usage and cost
diagnose/   Check auth, network, endpoint, providers, MCP, config, permissions
policy/     Inspect effective policy
```

`agentrouter diagnose` must return actionable output, not a bare failure.

## Status

Scaffold, not implemented.
