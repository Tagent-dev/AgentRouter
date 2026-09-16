# VS Code Integration

Authentication, configuration, connection management, model/provider
configuration, status and diagnostics through officially supported extension
and provider mechanisms only.

Every integration declares a capability profile rather than assuming parity:

| Capability                | Meaning                                        |
| ------------------------- | ---------------------------------------------- |
| supports_mcp              | Host can attach an MCP server                   |
| supports_model_provider   | Host accepts a custom model/provider            |
| supports_model_selection  | Host exposes programmatic model selection       |
| supports_request_proxy    | Host requests can be proxied through AgentRouter|
| supports_extension        | Host has an official extension mechanism        |
| supports_streaming        | Host consumes streamed responses                |
| supports_auth             | Host supports the auth handshake                |

A capability is only marked supported once it is actually implemented and tested.
Undocumented host APIs are out of scope.

## Status

Scaffold, not implemented.
