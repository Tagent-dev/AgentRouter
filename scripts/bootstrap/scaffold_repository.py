#!/usr/bin/env python3
"""Scaffold the AgentRouter target repository structure.

Source of truth: "Repository Structure.md" (final target repository structure).

Properties:
  * Idempotent - an existing file is never overwritten, only reported as skipped.
  * Directory-only nodes get a .gitkeep so Git tracks them.
  * Placeholder files state plainly that they are scaffolds. Nothing here
    pretends to be a working implementation.

Usage:
    python scripts/bootstrap/scaffold_repository.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

created_dirs: list[str] = []
created_files: list[str] = []
skipped_files: list[str] = []

SCAFFOLD_NOTE = (
    "> Scaffold. This document is a placeholder created with the repository "
    "structure and has not been written yet."
)

# Files this generator materializes but does not author. Each is produced by
# another tool from a source that lives elsewhere in the tree, so holding its text
# as a constant here would create a second, competing definition.
GENERATED_ELSEWHERE = {
    "docs/IMPLEMENTATION_STATUS.md": (
        "generated from docs/implementation-status.yaml by scripts/status/render.py"
    ),
}


def mkdir(rel: str) -> Path:
    path = ROOT / rel
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(rel)
    return path


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        skipped_files.append(rel)
        return
    text = content if content == "" or content.endswith("\n") else content + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    created_files.append(rel)


def keep(*rels: str) -> None:
    """Create directories that hold no scaffold files yet."""
    for rel in rels:
        mkdir(rel)
        write(f"{rel}/.gitkeep", "")


def doc(rel: str, title: str, purpose: str) -> None:
    write(rel, f"# {title}\n\n{purpose}\n\n{SCAFFOLD_NOTE}\n")


def readme(rel: str, title: str, body: str) -> None:
    write(rel, f"# {title}\n\n{body}\n")


def tree(paths: list[str]) -> str:
    return "```text\n" + "\n".join(paths) + "\n```"


def render_status_document() -> None:
    """Produce docs/IMPLEMENTATION_STATUS.md by running the renderer, not from a constant.

    The document used to be a text constant here. It is now generated from
    docs/implementation-status.yaml by scripts/status/render.py, and two writers
    for one file means the last one to run wins, which is a drift bug waiting for
    a status change. So this generator delegates instead of competing: it owns the
    manifest, and the renderer owns the document.

    The generator's never-overwrite contract still holds. An existing document is
    left alone and reported as skipped; `status-render` in CI is what catches a
    stale one, because that is a manifest-versus-document question the scaffold
    cannot answer.

    The renderer needs PyYAML, which the scaffold otherwise does not. On a machine
    without it the file is reported as pending rather than written, so the
    bootstrap step still runs on a bare checkout.
    """
    rel = "docs/IMPLEMENTATION_STATUS.md"
    provenance = GENERATED_ELSEWHERE[rel]
    if (ROOT / rel).exists():
        skipped_files.append(rel)
        return

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from scripts.status.manifest import load_manifest
        from scripts.status.render import render
    except ImportError as exc:
        print(
            f"note: {rel} not written ({exc}). It is {provenance}; "
            "install the dev dependencies and run: python scripts/status/render.py"
        )
        return

    text = render(load_manifest(ROOT / "docs" / "implementation-status.yaml"))
    (ROOT / rel).write_text(text, encoding="utf-8", newline="\n")
    created_files.append(rel)


# ---------------------------------------------------------------------------
# .github
# ---------------------------------------------------------------------------

WORKFLOW_HEADER = (
    "# Scaffold workflow. Steps are intentionally minimal until the\n"
    "# corresponding services exist. Extend per implementation phase.\n"
)


def section_github() -> None:
    write(
        ".github/workflows/ci.yml",
        WORKFLOW_HEADER
        + """
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  structure:
    name: Repository structure
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install development dependencies
        run: pip install --disable-pip-version-check -r requirements-dev.txt

      - name: Verify scaffold is idempotent
        run: |
          python scripts/bootstrap/scaffold_repository.py
          git diff --exit-code

      - name: Validate structure, JSON and YAML
        run: python scripts/testing/validate_structure.py

      # Requirement 3.6: one documented command runs formatting, linting, type
      # checking and unit tests. CI runs that command rather than repeating its
      # steps, so the gate cannot differ between a developer machine and CI.
      - name: Quality gate
        run: make check

  helm:
    name: Helm chart
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v4
      - name: Lint chart
        run: helm lint deployments/helm/agentrouter

  # TODO(phase): add integration test and build jobs as each service under
  # services/ and app under apps/ is implemented.
""",
    )

    write(
        ".github/workflows/security.yml",
        WORKFLOW_HEADER
        + """
name: Security

on:
  pull_request:
  schedule:
    - cron: "0 3 * * 1"

permissions:
  contents: read

jobs:
  secret-scan:
    name: Secret scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Fail on committed .env files
        run: |
          if git ls-files | grep -E '(^|/)\\.env$'; then
            echo "A .env file is tracked in Git. Remove it and rotate any secret."
            exit 1
          fi

  # TODO(phase): add dependency scanning, SAST and container image scanning
  # once dependencies and Dockerfiles are functional.
""",
    )

    write(
        ".github/workflows/build-images.yml",
        WORKFLOW_HEADER
        + """
name: Build Images

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    name: Build container images
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Not yet enabled
        run: |
          echo "Service Dockerfiles are scaffolds. Enable per service once its"
          echo "source and build are implemented."
          exit 0
""",
    )

    for env_name in ("staging", "production"):
        write(
            f".github/workflows/deploy-{env_name}.yml",
            WORKFLOW_HEADER
            + f"""
name: Deploy {env_name.title()}

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  deploy:
    name: Deploy to {env_name}
    runs-on: ubuntu-latest
    environment: {env_name}
    steps:
      - uses: actions/checkout@v4
      - name: Not yet enabled
        run: |
          echo "Deployment is not wired up. Requires the Helm chart under"
          echo "deployments/helm/agentrouter plus cluster credentials."
          exit 0
""",
        )

    keep(".github/ISSUE_TEMPLATE")

    write(
        ".github/PULL_REQUEST_TEMPLATE.md",
        """## Summary

<!-- What changes and why. Reference the implementation phase. -->

## Implementation phase

<!-- Phase from the Master Engineering Specification, section 132. -->

## Definition of done

- [ ] Implementation exists (no placeholder marked as complete)
- [ ] Unit tests
- [ ] Integration tests where applicable
- [ ] Errors handled
- [ ] Security reviewed (auth, authorization, secrets, tenant isolation)
- [ ] Structured logging
- [ ] Metrics/traces where applicable
- [ ] Documentation updated
- [ ] API contract updated
- [ ] Configuration documented
- [ ] docs/IMPLEMENTATION_STATUS.md updated
- [ ] CI passing

## Security notes

<!-- Tenant isolation, secret handling, data retention impact. -->
""",
    )

    write(
        ".github/CODEOWNERS",
        """# Ownership map. Replace the placeholder owner before enabling reviews.
# Syntax: <path> <owner>

* @agentrouter-owner

/services/router/ @agentrouter-owner
/services/policy/ @agentrouter-owner
/packages/auth/ @agentrouter-owner
/packages/security/ @agentrouter-owner
/security/ @agentrouter-owner
/infrastructure/ @agentrouter-owner
""",
    )

    write(
        ".github/dependabot.yml",
        """version: 2

updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly

# TODO(phase): add npm, gomod and pip ecosystems as manifests gain real
# dependencies (apps/, integrations/, sdk/, services/).
""",
    )


# ---------------------------------------------------------------------------
# apps
# ---------------------------------------------------------------------------


def node_package(name: str, description: str, private: bool = True) -> str:
    private_line = '  "private": true,\n' if private else ""
    return (
        "{\n"
        f'  "name": "{name}",\n'
        '  "version": "0.0.0",\n'
        f"{private_line}"
        f'  "description": "{description}",\n'
        '  "license": "SEE LICENSE IN LICENSE",\n'
        '  "scripts": {\n'
        '    "build": "echo \\"not implemented\\" && exit 1",\n'
        '    "test": "echo \\"not implemented\\" && exit 1"\n'
        "  }\n"
        "}\n"
    )


def section_apps() -> None:
    keep(
        "apps/dashboard/src",
        "apps/dashboard/public",
        "apps/dashboard/tests",
        "apps/admin-console/src",
        "apps/admin-console/public",
        "apps/admin-console/tests",
        "apps/api/src",
        "apps/api/tests",
        "apps/docs/content",
        "apps/docs/public",
    )

    write(
        "apps/dashboard/package.json", node_package("@agentrouter/dashboard", "Customer dashboard")
    )
    readme(
        "apps/dashboard/README.md",
        "Dashboard",
        """Customer-facing control plane application (React/Next.js per `technology.md`).

Sections defined by the specification: Overview, AI Usage, Cost, Savings, Models,
Providers, Routing, Teams, Users, Policies, Security, Audit, Billing, Settings.

The browser talks only to the control plane API. It never reaches PostgreSQL
directly, and the frontend is never trusted for authorization.

Status: scaffold, not implemented.

"""
        + tree(["src/     application code", "public/  static assets", "tests/   dashboard tests"]),
    )

    write(
        "apps/admin-console/package.json",
        node_package("@agentrouter/admin-console", "Platform administration console"),
    )
    readme(
        "apps/admin-console/README.md",
        "Admin Console",
        """Platform-operator surface, separate from the customer dashboard: tenants,
platform policy, model lifecycle and provider onboarding.

Administrative operations require stronger authentication (MFA through the
identity provider, short-lived sessions, full audit).

Status: scaffold, not implemented.

"""
        + tree(["src/     application code", "public/  static assets", "tests/   console tests"]),
    )

    write("apps/api/package.json", node_package("@agentrouter/api", "Public API application"))
    readme(
        "apps/api/README.md",
        "API",
        """Public API surface described in the specification (section 45):

"""
        + tree(
            [
                "/v1/auth",
                "/v1/models",
                "/v1/providers",
                "/v1/route",
                "/v1/generate",
                "/v1/usage",
                "/v1/policies",
                "/v1/organizations",
                "/v1/teams",
                "/v1/users",
                "/v1/audit",
            ]
        )
        + """

The contract lives in `docs/api/openapi.yaml` and `packages/api_contracts`.
Documentation is generated from the schema, not written by hand.

Status: scaffold, not implemented.""",
    )

    readme(
        "apps/docs/README.md",
        "Docs Site",
        """Published documentation site. Content sources from `docs/`.

Status: scaffold, not implemented.

"""
        + tree(["content/  documentation content", "public/   static assets"]),
    )


# ---------------------------------------------------------------------------
# services
# ---------------------------------------------------------------------------

SERVICES: list[tuple[str, str, str, list[str], dict[str, str]]] = [
    (
        "gateway",
        "Data plane",
        "Entry point for AI requests. Terminates the public contract, attaches "
        "authenticated tenant context, normalizes the request into the canonical "
        "internal format and forwards it through the analyzer, policy and router "
        "chain. Streaming must pass through without buffering whole responses.",
        [],
        {},
    ),
    (
        "router",
        "Data plane - core IP",
        "Selects the model. Consumes request analysis, registry candidates, policy "
        "decisions, cost, latency and health, then produces an explainable routing "
        "decision. Contains no provider-specific and no IDE-specific logic.",
        ["engine", "scoring", "candidates", "strategies", "escalation", "fallback"],
        {
            "engine": "Routing orchestration and decision assembly",
            "scoring": "Configurable scoring function and weights",
            "candidates": "Candidate generation and filtering",
            "strategies": "Routing modes (balanced, quality/cost/latency/reliability/policy first)",
            "escalation": "Quality-driven escalation to a stronger model",
            "fallback": "Provider/model failure fallback, policy aware",
        },
    ),
    (
        "analyzer",
        "Data plane",
        "Describes what the request requires - task type, complexity, reasoning, "
        "context, tool and coding requirements, expected output, confidence. It "
        "never selects a model, and it never uses prompt length alone as a proxy "
        "for complexity.",
        ["classifier", "complexity", "capabilities", "context", "prompt_analysis"],
        {
            "classifier": "Task type classification",
            "complexity": "Complexity estimation (low/medium/high/critical)",
            "capabilities": "Required capability derivation",
            "context": "Context size and shape requirements",
            "prompt_analysis": "Structural prompt analysis signals",
        },
    ),
    (
        "policy",
        "Governance",
        "Centralized policy decisions with deterministic conflict resolution across "
        "the platform, organization, department, team, user and per-request layers.",
        ["engine", "rules", "evaluation", "inheritance"],
        {
            "engine": "Policy decision entry point",
            "rules": "Rule definitions and storage model",
            "evaluation": "Rule evaluation and decision output",
            "inheritance": "Policy hierarchy resolution",
        },
    ),
    (
        "providers",
        "Provider gateway",
        "The only component that talks to model providers. Every provider sits "
        "behind the same adapter interface so a provider API change stays contained "
        "in one adapter.",
        [
            "gateway",
            "adapters",
            "health",
            "failover",
            "normalization",
            "openai",
            "anthropic",
            "google",
            "azure",
            "aws",
            "compatible",
        ],
        {
            "gateway": "Provider-facing execution entry point",
            "adapters": "ProviderAdapter interface and shared adapter logic",
            "health": "Latency, error rate, availability and circuit state",
            "failover": "Provider failover execution",
            "normalization": "Request/response and error normalization",
            "openai": "OpenAI adapter",
            "anthropic": "Anthropic adapter",
            "google": "Google adapter",
            "azure": "Azure-hosted model adapter",
            "aws": "AWS-hosted model adapter",
            "compatible": "OpenAI-compatible and self-hosted endpoints",
        },
    ),
    (
        "registry",
        "Model control",
        "Source of truth for providers, models, capabilities and pricing. No other "
        "service hardcodes model capabilities or prices.",
        ["models", "providers", "capabilities", "pricing", "lifecycle"],
        {
            "models": "Model records and queries",
            "providers": "Provider records",
            "capabilities": "Capability and benchmark-derived attributes",
            "pricing": "Data-driven pricing records",
            "lifecycle": "Discovered -> benchmarking -> approved -> active -> deprecated -> retired",
        },
    ),
    (
        "cost_engine",
        "FinOps",
        "Token accounting, cost estimation, actual cost calculation and savings "
        "against a configurable baseline. Savings numbers must never be inflated.",
        ["pricing", "estimation", "calculation", "savings"],
        {
            "pricing": "Pricing resolution from the registry",
            "estimation": "Pre-flight cost estimation",
            "calculation": "Post-flight actual cost",
            "savings": "Baseline comparison and savings reporting",
        },
    ),
    (
        "analytics",
        "Analytics",
        "Consumes events off the critical path and produces usage, cost, routing and "
        "quality aggregates for dashboards and reports.",
        ["ingestion", "aggregation", "metrics", "reports"],
        {
            "ingestion": "Event stream consumption, idempotent by event ID",
            "aggregation": "Rollups by org, team, user, model, provider, period",
            "metrics": "Derived product and routing metrics",
            "reports": "Report generation",
        },
    ),
    (
        "billing",
        "Commercial",
        "Plans, seats, metered usage, overages, invoices and payment status. Isolated "
        "from routing logic and never in the synchronous request path.",
        ["subscriptions", "usage", "invoices", "payments"],
        {
            "subscriptions": "Plans and seats",
            "usage": "Metered usage rating",
            "invoices": "Invoice generation",
            "payments": "Payment status and provider integration",
        },
    ),
    (
        "notifications",
        "Platform",
        "Delivers budget, reliability, policy and security notifications over email, "
        "webhook, Slack and Microsoft Teams.",
        ["email", "webhook", "slack", "teams"],
        {
            "email": "Email delivery",
            "webhook": "Outbound webhooks",
            "slack": "Slack delivery",
            "teams": "Microsoft Teams delivery",
        },
    ),
    (
        "audit",
        "Governance",
        "Append-only record of administrative and security-relevant events, "
        "immutable from normal customer workflows.",
        ["events", "storage", "queries"],
        {
            "events": "Audit event definitions",
            "storage": "Append-only storage",
            "queries": "Auditor-facing queries",
        },
    ),
]

SERVICE_DOCKERFILE = """# Scaffold Dockerfile for the AgentRouter {name} service.
#
# This is intentionally NOT buildable yet: the service has no source. Replace
# the placeholder stage once {name} is implemented, then enable the service in
# .github/workflows/build-images.yml.
#
# Reference shape for a Go service (see technology.md):
#
#   FROM golang:1.23-alpine AS build
#   WORKDIR /src
#   COPY . .
#   RUN CGO_ENABLED=0 go build -trimpath -o /out/{name} ./cmd/{name}
#
#   FROM gcr.io/distroless/static-debian12:nonroot
#   USER nonroot:nonroot
#   COPY --from=build /out/{name} /{name}
#   ENTRYPOINT ["/{name}"]
#
# Image requirements from the specification (section 74): minimal base image,
# non-root user, dependency scanning, SBOM, signing where appropriate.

FROM scratch
LABEL org.opencontainers.image.title="agentrouter-{name}"
LABEL org.opencontainers.image.description="Scaffold only. Not implemented."
"""


def section_services() -> None:
    for name, plane, purpose, subdirs, subdesc in SERVICES:
        keep(f"services/{name}/cmd", f"services/{name}/tests")
        if subdirs:
            keep(*[f"services/{name}/internal/{sub}" for sub in subdirs])
        else:
            keep(f"services/{name}/internal")

        write(f"services/{name}/Dockerfile", SERVICE_DOCKERFILE.format(name=name))

        layout = ["cmd/        service entry point", "internal/   service-private packages"]
        if subdirs:
            width = max(len(sub) for sub in subdirs) + 2
            layout = ["cmd/        service entry point", "internal/"]
            layout += [f"  {sub + '/':<{width}} {subdesc[sub]}" for sub in subdirs]
        layout.append("tests/      service tests")

        readme(
            f"services/{name}/README.md",
            f"{name} service",
            f"""**Plane:** {plane}

{purpose}

## Layout

{tree(layout)}

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.""",
        )


# ---------------------------------------------------------------------------
# integrations
# ---------------------------------------------------------------------------

INTEGRATION_CAPABILITY_TABLE = """Every integration declares a capability profile rather than assuming parity:

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
Undocumented host APIs are out of scope."""


def section_integrations() -> None:
    keep(
        "integrations/mcp/server/tools",
        "integrations/mcp/server/resources",
        "integrations/mcp/server/prompts",
        "integrations/mcp/server/auth",
        "integrations/mcp/server/server",
        "integrations/mcp/tests",
    )
    write(
        "integrations/mcp/package.json",
        node_package("@agentrouter/mcp-server", "AgentRouter MCP server"),
    )
    readme(
        "integrations/mcp/README.md",
        "MCP Integration",
        """A thin door into AgentRouter. It holds no routing intelligence: every call
goes through the normal API, authentication, authorization, tenant context,
policy, rate limiting and audit path.

Planned tools (specification section 37):

"""
        + tree(
            [
                "analyze_task",
                "recommend_model",
                "estimate_cost",
                "get_available_models",
                "check_policy",
                "route_request",
            ]
        )
        + """

Resources expose read-only information such as model capabilities, routing
policies and usage. An MCP client must never be able to bypass enterprise policy.

## Layout

"""
        + tree(
            [
                "server/",
                "  tools/      tool implementations",
                "  resources/  read-only resources",
                "  prompts/    prompt definitions",
                "  auth/       authentication and tenant context",
                "  server/     server wiring and transport",
                "tests/        MCP conformance and integration tests",
            ]
        )
        + """

## Status

Scaffold, not implemented.""",
    )

    keep(
        "integrations/vscode/src",
        "integrations/vscode/resources",
        "integrations/vscode/tests",
    )
    write(
        "integrations/vscode/package.json",
        node_package("@agentrouter/vscode", "AgentRouter VS Code integration"),
    )
    readme(
        "integrations/vscode/README.md",
        "VS Code Integration",
        f"""Authentication, configuration, connection management, model/provider
configuration, status and diagnostics through officially supported extension
and provider mechanisms only.

{INTEGRATION_CAPABILITY_TABLE}

## Status

Scaffold, not implemented.""",
    )

    for name, title, body in [
        (
            "kiro",
            "Kiro Integration",
            "Uses the interfaces Kiro actually exposes. Where Kiro supports MCP, ship the\n"
            "AgentRouter MCP configuration; where it exposes a model/provider mechanism,\n"
            "use that. No assumptions about undocumented internal APIs.",
        ),
        (
            "cursor",
            "Cursor Integration",
            "Separate adapter built strictly on officially exposed mechanisms. No\n"
            "reverse-engineering of internal APIs.",
        ),
        (
            "claude-code",
            "Claude Code Integration",
            "Adapter for Claude Code, implemented only where officially supported. The\n"
            "routing engine stays independent of this integration.",
        ),
        (
            "jetbrains",
            "JetBrains Integration",
            "Adapter for JetBrains IDEs through the official plugin mechanism.",
        ),
    ]:
        keep(f"integrations/{name}/src", f"integrations/{name}/tests")
        if name == "kiro":
            keep("integrations/kiro/config")
        readme(
            f"integrations/{name}/README.md",
            title,
            f"{body}\n\nCapability profile is declared per host and only marked supported once\ntested.\n\n## Status\n\nScaffold, not implemented.",
        )


# ---------------------------------------------------------------------------
# clients
# ---------------------------------------------------------------------------


def section_clients() -> None:
    keep("clients/desktop/src", "clients/desktop/tests")
    readme(
        "clients/desktop/README.md",
        "Desktop Client",
        """Optional desktop surface for login, organization selection, status and
diagnostics.

## Status

Scaffold, not implemented.""",
    )

    keep("clients/local-agent/src", "clients/local-agent/config", "clients/local-agent/tests")
    readme(
        "clients/local-agent/README.md",
        "Local Agent",
        """Developer-machine client that sits between the IDE and an AgentRouter
deployment.

"""
        + tree(
            [
                "IDE",
                " |",
                " v",
                "Local Agent  (auth, local config, secure credential storage, MCP, diagnostics)",
                " |",
                " v  HTTPS",
                "AgentRouter cloud or private deployment",
            ]
        )
        + """

Credentials are stored using the OS secure store, never in plaintext config.

## Layout

"""
        + tree(
            [
                "src/     client implementation",
                "config/  default configuration",
                "tests/   client tests",
            ]
        )
        + """

## Status

Scaffold, not implemented.""",
    )


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

CLI_COMMANDS = {
    "login": "Authenticate and store credentials securely",
    "logout": "Revoke the local session",
    "configure": "Set endpoint, organization and defaults",
    "status": "Show connection, org and routing status",
    "models": "List models visible under current policy",
    "providers": "List providers and health",
    "route": "Route a request and show the decision",
    "usage": "Show usage and cost",
    "diagnose": "Check auth, network, endpoint, providers, MCP, config, permissions",
    "policy": "Inspect effective policy",
}


def section_cli() -> None:
    keep(*[f"cli/cmd/{name}" for name in CLI_COMMANDS])
    keep("cli/internal", "cli/tests")

    write(
        "cli/Dockerfile",
        SERVICE_DOCKERFILE.format(name="cli").replace("AgentRouter cli service", "AgentRouter CLI"),
    )

    width = max(len(name) for name in CLI_COMMANDS) + 2
    readme(
        "cli/README.md",
        "CLI",
        """`agentrouter` command line interface. All commands support machine-readable
output.

## Commands

"""
        + tree([f"{name + '/':<{width}} {desc}" for name, desc in CLI_COMMANDS.items()])
        + """

`agentrouter diagnose` must return actionable output, not a bare failure.

## Status

Scaffold, not implemented.""",
    )


# ---------------------------------------------------------------------------
# sdk
# ---------------------------------------------------------------------------

SDK_CORE_API = tree(["route()", "generate()", "stream()", "getModels()", "getUsage()"])


def section_sdk() -> None:
    keep("sdk/typescript/src", "sdk/typescript/tests")
    write(
        "sdk/typescript/package.json",
        node_package("@agentrouter/sdk", "AgentRouter TypeScript SDK", private=False),
    )
    readme(
        "sdk/typescript/README.md",
        "TypeScript SDK",
        f"""Core API:

{SDK_CORE_API}

Generated against the same canonical contracts as every other client
(`packages/api_contracts`, `docs/api/openapi.yaml`).

## Status

Scaffold, not implemented.""",
    )

    keep("sdk/python/agentrouter", "sdk/python/tests")
    write(
        "sdk/python/pyproject.toml",
        """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agentrouter"
version = "0.0.0"
description = "AgentRouter Python SDK"
readme = "README.md"
requires-python = ">=3.11"
license = { file = "../../LICENSE" }
dependencies = []

[tool.hatch.build.targets.wheel]
packages = ["agentrouter"]
""",
    )
    readme(
        "sdk/python/README.md",
        "Python SDK",
        f"""Core API:

{SDK_CORE_API}

## Status

Scaffold, not implemented.""",
    )

    keep("sdk/go/agentrouter", "sdk/go/tests")
    write(
        "sdk/go/go.mod",
        """module github.com/agentrouter/agentrouter/sdk/go

go 1.23
""",
    )
    readme(
        "sdk/go/README.md",
        "Go SDK",
        f"""Core API:

{SDK_CORE_API}

## Status

Scaffold, not implemented.""",
    )


# ---------------------------------------------------------------------------
# packages
# ---------------------------------------------------------------------------

# Directory names are snake_case: every one of these is imported as a Python
# module (see pyproject.toml), and a Python module name cannot contain a hyphen.
PACKAGES = {
    "api_contracts": "Canonical API contracts shared by services, SDKs, CLI and apps. Single source for request/response shapes.",
    "shared_types": "Shared domain types: canonical request, routing decision, analysis result, policy decision, usage record.",
    "auth": "Authentication primitives: OIDC/OAuth, SAML SSO, API keys, service accounts, token verification.",
    "authorization": "RBAC roles, granular permissions and resource-level authorization checks.",
    "tenant": "Tenant context propagation and isolation helpers. Tenant identity is always derived from authenticated identity, never from client input.",
    "logging": "Structured logging with redaction wired in by default.",
    "telemetry": "OpenTelemetry setup: traces, metrics and a shared request/trace ID.",
    "errors": "Normalized error taxonomy and mapping to API responses.",
    "security": "Shared security controls: crypto helpers, hashing, sensitive-data detection.",
    "redaction": "Redaction of API keys, passwords, tokens, private keys, credentials and PII before anything is logged or stored.",
    "configuration": "Environment-driven configuration loading and validation. No embedded secrets or production URLs.",
    "events": "Event definitions and publishing. Every event carries an ID; consumers handle duplicates safely.",
    "validation": "Shared input validation.",
    "testing": "Shared test helpers, fixtures and fakes.",
}


def section_packages() -> None:
    for name, purpose in PACKAGES.items():
        keep(f"packages/{name}")
        readme(
            f"packages/{name}/README.md",
            f"packages/{name}",
            f"{purpose}\n\n## Status\n\nScaffold, not implemented.",
        )


# ---------------------------------------------------------------------------
# database
# ---------------------------------------------------------------------------

CORE_TABLES = [
    "organizations",
    "users",
    "teams",
    "memberships",
    "roles",
    "permissions",
    "providers",
    "models",
    "model_capabilities",
    "model_pricing",
    "policies",
    "policy_rules",
    "requests",
    "routing_decisions",
    "provider_requests",
    "usage_records",
    "cost_records",
    "budgets",
    "audit_events",
    "api_keys",
    "service_accounts",
    "integrations",
    "subscriptions",
    "invoices",
    "notifications",
]


def section_database() -> None:
    keep(
        "database/migrations",
        "database/seeds",
        "database/schemas",
        "database/queries",
        "database/views",
    )
    readme(
        "database/README.md",
        "Database",
        """PostgreSQL is the authoritative transactional store. Redis is a cache and
coordination layer, never the source of truth.

## Rules

- Every schema change ships as a migration. Production schema is never edited by hand.
- Migrations run before the application deployment.
- Migrations must be backwards compatible while rolling deployments are in flight.
- Every tenant-scoped table enforces isolation at the data-access boundary.

## Core tables

"""
        + tree(CORE_TABLES)
        + """

## Layout

"""
        + tree(
            [
                "migrations/  ordered, forward-only schema migrations",
                "seeds/       non-production seed data",
                "schemas/     reference schema documentation",
                "queries/     reviewed query definitions",
                "views/       database views",
            ]
        )
        + """

## Status

Scaffold. No migrations written yet.""",
    )


# ---------------------------------------------------------------------------
# benchmark and evaluation
# ---------------------------------------------------------------------------

BENCHMARK_DOMAINS = {
    "coding": "Code generation and completion tasks",
    "debugging": "Fault localization and root-cause tasks",
    "refactoring": "Structural change tasks",
    "kubernetes": "Cluster, manifest and incident tasks",
    "terraform": "Infrastructure-as-code tasks",
    "sql": "Query and schema tasks",
    "architecture": "System design tasks",
    "security": "Security review and hardening tasks",
}


def section_benchmark() -> None:
    keep(*[f"benchmark/datasets/{d}" for d in BENCHMARK_DOMAINS])
    keep("benchmark/runners", "benchmark/evaluators", "benchmark/reports")

    width = max(len(d) for d in BENCHMARK_DOMAINS) + 2
    readme(
        "benchmark/README.md",
        "Benchmark",
        """Model benchmarking feeds capability scores into the model registry. Scores
are measured, never invented.

## Domains

"""
        + tree([f"datasets/{d + '/':<{width}} {desc}" for d, desc in BENCHMARK_DOMAINS.items()])
        + """

## Measured per model and domain

"""
        + tree(["quality", "success rate", "cost", "latency", "context handling", "tool usage"])
        + """

## Layout

"""
        + tree(
            [
                "datasets/    task datasets per domain",
                "runners/     benchmark execution",
                "evaluators/  scoring of model output",
                "reports/     generated benchmark reports",
            ]
        )
        + """

## Status

Scaffold. No datasets or runners yet.""",
    )

    keep(
        "evaluation/routing",
        "evaluation/quality",
        "evaluation/cost",
        "evaluation/latency",
        "evaluation/reliability",
    )
    readme(
        "evaluation/README.md",
        "Evaluation",
        """Measures whether the router is making good decisions, which is a different
question from how good a given model is.

## Tracked metrics

"""
        + tree(
            [
                "routing accuracy",
                "successful completion rate",
                "cost savings",
                "quality loss",
                "latency",
                "fallback rate",
                "escalation rate",
            ]
        )
        + """

The headline objective: cost reduction without unacceptable quality degradation.

## Regression dataset shape

"""
        + tree(
            [
                "prompt",
                "task_type",
                "complexity",
                "required_capabilities",
                "candidate_models",
                "expected_best_model",
                "actual_selected_model",
                "cost",
                "quality",
                "latency",
            ]
        )
        + """

## Layout

"""
        + tree(
            [
                "routing/      routing decision evaluation",
                "quality/      output quality evaluation",
                "cost/         cost outcome evaluation",
                "latency/      latency outcome evaluation",
                "reliability/  fallback and failure behaviour evaluation",
            ]
        )
        + """

## Status

Scaffold, not implemented.""",
    )


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

TEST_SUITES = {
    "unit": "Fast isolated tests owned alongside each module",
    "integration": "Cross-component tests with real dependencies where practical",
    "e2e": "Full chain: integration -> gateway -> analyzer -> policy -> router -> provider -> response",
    "api": "Public API contract tests against the OpenAPI schema",
    "mcp": "MCP server conformance and authorization tests",
    "security": "Auth, authorization, tenant isolation, redaction and secret-handling tests",
    "load": "Throughput and latency under load",
    "chaos": "Provider failure, timeout, circuit breaker and fallback behaviour",
    "fixtures": "Shared fixtures and test data",
}


def section_tests() -> None:
    for name, desc in TEST_SUITES.items():
        keep(f"tests/{name}")
        readme(
            f"tests/{name}/README.md",
            f"tests/{name}",
            f"{desc}\n\n## Status\n\nScaffold. No tests written yet.",
        )

    width = max(len(n) for n in TEST_SUITES) + 2
    readme(
        "tests/README.md",
        "Cross-cutting Tests",
        """Repository-level test suites. Service-local tests live in each
`services/<name>/tests` directory.

"""
        + tree([f"{n + '/':<{width}} {d}" for n, d in TEST_SUITES.items()])
        + """

A component is not done because it compiles. Tests are part of the definition
of done, and unsupported external integrations are never marked complete.""",
    )


# ---------------------------------------------------------------------------
# deployments
# ---------------------------------------------------------------------------

COMPOSE_HEADER = (
    "# Scaffold compose file. Only backing services that are useful before any\n"
    "# application code exists are defined. Application services are added as\n"
    "# each one becomes runnable.\n"
)


def section_deployments() -> None:
    write(
        "deployments/docker/docker-compose.yml",
        COMPOSE_HEADER
        + """
name: agentrouter

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-agentrouter}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in your local .env}
      POSTGRES_DB: ${POSTGRES_DB:-agentrouter}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-agentrouter}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
  redis-data:
""",
    )

    write(
        "deployments/docker/docker-compose.dev.yml",
        COMPOSE_HEADER
        + """
# Overlay for local development. Use with:
#   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

name: agentrouter

services:
  postgres:
    ports:
      - "${POSTGRES_PORT:-5432}:5432"

  redis:
    ports:
      - "${REDIS_PORT:-6379}:6379"

# TODO(phase): add application services with source mounts and hot reload once
# services/ contain runnable code.
""",
    )

    write(
        "deployments/docker/docker-compose.test.yml",
        COMPOSE_HEADER
        + """
# Ephemeral stack for integration tests. Uses throwaway credentials and
# tmpfs storage so no state survives the run.

name: agentrouter-test

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: agentrouter_test
      POSTGRES_PASSWORD: agentrouter_test
      POSTGRES_DB: agentrouter_test
    tmpfs:
      - /var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentrouter_test"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    tmpfs:
      - /data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10
""",
    )

    readme(
        "deployments/docker/README.md",
        "Docker Deployments",
        """Local and test stacks.

"""
        + tree(
            [
                "docker-compose.yml       backing services (PostgreSQL, Redis)",
                "docker-compose.dev.yml   development overlay",
                "docker-compose.test.yml  ephemeral stack for integration tests",
            ]
        )
        + """

Credentials come from your local `.env` (see `.env.example`). Compose files
never carry real secrets.

## Status

Backing services usable. Application services pending implementation.""",
    )

    keep("deployments/kubernetes/base")
    for env_name in ("development", "staging", "production"):
        keep(f"deployments/kubernetes/overlays/{env_name}")
    readme(
        "deployments/kubernetes/README.md",
        "Kubernetes Manifests",
        """Base manifests plus per-environment overlays.

"""
        + tree(
            [
                "base/                    shared manifests",
                "overlays/development/    development patches",
                "overlays/staging/        staging patches",
                "overlays/production/     production patches",
            ]
        )
        + """

Deployment consolidates services rather than shipping one deployment per
directory in `services/`. Initial production workloads:

"""
        + tree(
            [
                "agentrouter-gateway",
                "agentrouter-router",
                "agentrouter-control-api",
                "agentrouter-worker",
                "agentrouter-mcp",
                "agentrouter-dashboard",
            ]
        )
        + """

Split further only when independent scaling justifies it.

## Status

Scaffold. No manifests written yet.""",
    )

    chart_templates = [
        "gateway.yaml",
        "router.yaml",
        "control-api.yaml",
        "worker.yaml",
        "mcp.yaml",
        "dashboard.yaml",
        "ingress.yaml",
        "configmap.yaml",
        "secrets.yaml",
        "serviceaccount.yaml",
        "networkpolicy.yaml",
        "hpa.yaml",
    ]
    mkdir("deployments/helm/agentrouter/templates")

    write(
        "deployments/helm/agentrouter/Chart.yaml",
        """apiVersion: v2
name: agentrouter
description: Enterprise AI model routing, optimization and governance platform
type: application
version: 0.0.0
appVersion: "0.0.0"
kubeVersion: ">=1.28.0-0"
home: https://github.com/agentrouter/agentrouter
sources:
  - https://github.com/agentrouter/agentrouter
maintainers:
  - name: AgentRouter
annotations:
  agentrouter.io/status: scaffold
""",
    )

    write(
        "deployments/helm/agentrouter/values.yaml",
        """# Default values for the AgentRouter chart.
#
# Scaffold: templates are not written yet, so installing this chart does
# nothing. The value shape below is the contract the templates will implement.
#
# Never commit real secrets to any values file. Reference an external secret
# manager or a pre-created Kubernetes Secret instead.

global:
  imageRegistry: ""
  imagePullSecrets: []
  # Deployment mode: saas | dedicated | self-hosted
  deploymentMode: self-hosted

image:
  repository: ghcr.io/agentrouter
  tag: ""
  pullPolicy: IfNotPresent

# Workloads follow the consolidated production topology.
workloads:
  gateway:
    enabled: true
    replicaCount: 2
    resources: {}
    autoscaling:
      enabled: false
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilizationPercentage: 70
  router:
    enabled: true
    replicaCount: 2
    resources: {}
    autoscaling:
      enabled: false
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilizationPercentage: 70
  controlApi:
    enabled: true
    replicaCount: 2
    resources: {}
  worker:
    enabled: true
    replicaCount: 1
    resources: {}
  mcp:
    enabled: true
    replicaCount: 1
    resources: {}
  dashboard:
    enabled: true
    replicaCount: 2
    resources: {}

serviceAccount:
  create: true
  name: ""
  annotations: {}

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 10001
  fsGroup: 10001
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]

ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts: []
  tls: []

networkPolicy:
  enabled: true
  # Restrict egress to approved model providers and platform dependencies.
  allowedEgress: []

# Bring your own PostgreSQL. The chart does not ship a production database.
postgresql:
  enabled: false
  host: ""
  port: 5432
  database: agentrouter
  sslMode: require
  existingSecret: ""

redis:
  enabled: false
  host: ""
  port: 6379
  existingSecret: ""

# Provider credentials always come from an external secret manager.
secrets:
  provider: external   # external | kubernetes
  externalSecretName: ""

observability:
  otel:
    enabled: true
    endpoint: ""
  prometheus:
    serviceMonitor:
      enabled: false

routing:
  mode: balanced
  weights:
    quality: 0.40
    cost: 0.25
    latency: 0.15
    reliability: 0.20
  escalation:
    enabled: true
  fallback:
    enabled: true
""",
    )

    for env_name, notes in [
        (
            "development",
            """# Development overrides: single replicas, no autoscaling, relaxed ingress.

workloads:
  gateway:
    replicaCount: 1
  router:
    replicaCount: 1
  controlApi:
    replicaCount: 1
  dashboard:
    replicaCount: 1

ingress:
  enabled: false

networkPolicy:
  enabled: false

observability:
  otel:
    enabled: false
""",
        ),
        (
            "staging",
            """# Staging overrides: production-shaped, smaller footprint.

workloads:
  gateway:
    replicaCount: 2
    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 4
  router:
    replicaCount: 2
    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 4

ingress:
  enabled: true

networkPolicy:
  enabled: true

observability:
  otel:
    enabled: true
""",
        ),
        (
            "production",
            """# Production overrides.
#
# Pin images by digest. Supply database, Redis and provider credentials through
# an external secret manager, never through this file.

image:
  tag: ""   # set to an immutable tag or digest at release time

workloads:
  gateway:
    replicaCount: 3
    autoscaling:
      enabled: true
      minReplicas: 3
      maxReplicas: 20
  router:
    replicaCount: 3
    autoscaling:
      enabled: true
      minReplicas: 3
      maxReplicas: 20
  controlApi:
    replicaCount: 3
  worker:
    replicaCount: 2
  mcp:
    replicaCount: 2
  dashboard:
    replicaCount: 3

ingress:
  enabled: true

networkPolicy:
  enabled: true

postgresql:
  enabled: false
  sslMode: require

secrets:
  provider: external

observability:
  otel:
    enabled: true
  prometheus:
    serviceMonitor:
      enabled: true
""",
        ),
    ]:
        write(f"deployments/helm/agentrouter/values-{env_name}.yaml", notes)

    for template in chart_templates:
        write(
            f"deployments/helm/agentrouter/templates/{template}",
            f"""{{{{/*
  Scaffold template: {template}

  Not implemented. Rendering this chart currently produces no resources for
  this file. Implement alongside the corresponding workload.
*/}}}}
""",
        )

    readme(
        "deployments/helm/agentrouter/README.md",
        "AgentRouter Helm Chart",
        """Production installation path for self-hosted and customer-cloud deployments.

## Values files

"""
        + tree(
            [
                "values.yaml              defaults and value contract",
                "values-development.yaml  development overrides",
                "values-staging.yaml      staging overrides",
                "values-production.yaml   production overrides",
            ]
        )
        + """

## Supported surface (target)

"""
        + tree(
            [
                "replicas",
                "resources",
                "autoscaling",
                "ingress",
                "TLS",
                "secrets",
                "database",
                "redis",
                "observability",
                "network policies",
            ]
        )
        + """

## Secrets

Provider API keys, database credentials and Redis credentials are supplied by an
external secret manager or a pre-created Kubernetes Secret. Never commit them to
a values file.

## Status

Scaffold. `Chart.yaml` and the value contract exist; templates are placeholders,
so the chart does not install a working system yet.""",
    )


# ---------------------------------------------------------------------------
# infrastructure
# ---------------------------------------------------------------------------

TF_MODULES = {
    "network": "VPC, subnets, routing and egress control",
    "kubernetes": "Managed Kubernetes cluster and node pools",
    "database": "Managed PostgreSQL, backups and private networking",
    "redis": "Managed Redis",
    "storage": "S3-compatible object storage",
    "monitoring": "Metrics, logs, traces and alerting backends",
    "security": "IAM, KMS and secret manager resources",
}


def section_infrastructure() -> None:
    for name, purpose in TF_MODULES.items():
        keep(f"infrastructure/terraform/modules/{name}")
        readme(
            f"infrastructure/terraform/modules/{name}/README.md",
            f"terraform module: {name}",
            f"{purpose}\n\n## Status\n\nScaffold. No Terraform written yet.",
        )

    for env_name in ("development", "staging", "production"):
        keep(f"infrastructure/terraform/environments/{env_name}")
        readme(
            f"infrastructure/terraform/environments/{env_name}/README.md",
            f"terraform environment: {env_name}",
            f"""Composition of the shared modules for the {env_name} environment.

Each environment uses separate credentials and separate remote state. State is
never stored locally for shared environments.

## Status

Scaffold. No Terraform written yet.""",
        )

    width = max(len(n) for n in TF_MODULES) + 2
    readme(
        "infrastructure/terraform/README.md",
        "Terraform",
        """Terraform provisions infrastructure; Helm then installs AgentRouter into the
resulting cluster.

## Modules

"""
        + tree([f"modules/{n + '/':<{width}} {p}" for n, p in TF_MODULES.items()])
        + """

## Environments

"""
        + tree(
            [
                "environments/development/",
                "environments/staging/",
                "environments/production/",
            ]
        )
        + """

## Status

Scaffold, not implemented.""",
    )


# ---------------------------------------------------------------------------
# observability
# ---------------------------------------------------------------------------

OBSERVABILITY_DIRS = {
    "otel": "OpenTelemetry collector configuration and pipelines",
    "prometheus": "Scrape configuration and recording rules",
    "grafana": "Grafana provisioning",
    "alerts": "Alert rules and routing",
    "dashboards": "Dashboard definitions",
    "runbooks": "Operational runbooks referenced by alerts",
}

PLATFORM_METRICS = [
    "request_total",
    "request_success_total",
    "request_failure_total",
    "request_latency",
    "provider_latency",
    "routing_latency",
    "tokens_total",
    "cost_total",
    "fallback_total",
    "escalation_total",
    "policy_block_total",
]


def section_observability() -> None:
    for name, purpose in OBSERVABILITY_DIRS.items():
        keep(f"observability/{name}")
        readme(
            f"observability/{name}/README.md",
            f"observability/{name}",
            f"{purpose}\n\n## Status\n\nScaffold, not implemented.",
        )

    width = max(len(n) for n in OBSERVABILITY_DIRS) + 2
    readme(
        "observability/README.md",
        "Observability",
        """OpenTelemetry-compatible instrumentation across all services, correlated by a
shared request/trace ID through gateway, analyzer, policy, router and provider.

## Platform metrics

"""
        + tree(PLATFORM_METRICS)
        + """

## Monitored signals

"""
        + tree(
            [
                "request rate",
                "error rate",
                "P50 / P95 / P99 latency",
                "provider latency and failures",
                "routing latency",
                "fallback rate",
                "escalation rate",
                "token usage",
                "cost and savings",
                "policy blocks",
            ]
        )
        + """

## Layout

"""
        + tree([f"{n + '/':<{width}} {p}" for n, p in OBSERVABILITY_DIRS.items()])
        + """

Raw prompts are not logged by default. Telemetry stores metadata.

## Status

Scaffold, not implemented.""",
    )


# ---------------------------------------------------------------------------
# security
# ---------------------------------------------------------------------------

SECURITY_DIRS = {
    "policies": "Internal security policies and standards",
    "threat-model": "Threat models per plane and per trust boundary",
    "compliance": "Control mapping for SOC 2, ISO 27001 and GDPR readiness",
    "security-tests": "Security test definitions and evidence",
    "incident-response": "Incident response procedures and severity definitions",
}


def section_security() -> None:
    for name, purpose in SECURITY_DIRS.items():
        keep(f"security/{name}")
        readme(
            f"security/{name}/README.md",
            f"security/{name}",
            f"{purpose}\n\n## Status\n\nScaffold, not implemented.",
        )

    write(
        "security/incident-response/incident-response.md",
        """# Incident Response

"""
        + SCAFFOLD_NOTE
        + """

## Required content

"""
        + tree(
            [
                "severity definitions",
                "detection",
                "communication",
                "containment",
                "recovery",
                "postmortem",
            ]
        )
        + """

## Security incident scenarios to cover

"""
        + tree(
            [
                "credential exposure",
                "tenant isolation failure",
                "unauthorized access",
                "provider compromise",
                "data leakage",
                "service compromise",
            ]
        )
        + "\n",
    )

    width = max(len(n) for n in SECURITY_DIRS) + 2
    readme(
        "security/README.md",
        "Security",
        """Security spans identity, network, application, data, secrets, infrastructure,
tenant isolation and logging.

## Layout

"""
        + tree([f"{n + '/':<{width}} {p}" for n, p in SECURITY_DIRS.items()])
        + """

## Non-negotiables

- Tenant identity is derived from authenticated identity. A client-supplied
  `tenant_id` is never trusted.
- Secrets never enter source control, images, committed values files or logs.
- Raw prompts and customer source are not persisted by default.
- The frontend is never trusted for authorization.
- Compliance certification is never claimed before it exists.

Vulnerability reporting: see `SECURITY.md` at the repository root.

## Status

Scaffold, not implemented.""",
    )


# ---------------------------------------------------------------------------
# scripts
# ---------------------------------------------------------------------------

SCRIPT_DIRS = {
    "bootstrap": "First-run repository and environment setup",
    "development": "Local development helpers",
    "status": "Completion ledger: validate, render, verify evidence, check the DoD",
    "database": "Migration, seed and backup helpers",
    "testing": "Test orchestration helpers",
    "release": "Versioning and release helpers",
    "deployment": "Deployment helpers",
}

STATUS_SCRIPTS_README = """The completion ledger. `docs/implementation-status.yaml` is the
authoritative record; everything here reads it, and only `render.py` writes.

| Script         | Gate              | Enforces |
| -------------- | ----------------- | -------- |
| `validate.py`  | `status-schema`   | the manifest matches its schema, ids are unique, all 30 section 6 modules are covered (R1.3, R1.1) |
| `render.py`    | `status-render`   | the committed `docs/IMPLEMENTATION_STATUS.md` equals the generated output (R1.4) |
| `verify.py`    | `status-evidence` | every evidence command of an `implemented` component exits zero (R1.6) |
| `check_dod.py` | `status-dod`      | no `implemented` component has a false Component_DoD item (R1.7) |

```bash
python scripts/status/validate.py
python scripts/status/render.py            # write the document
python scripts/status/render.py --check    # fail when the committed copy is stale
python scripts/status/verify.py
python scripts/status/check_dod.py --show-progress
```

Each script is independently runnable, exits 0 on success and non-zero with an
actionable message otherwise, because each becomes a separate CI job. Shared
loading and formatting live in `manifest.py` so the four gates cannot disagree
about what the manifest means.

`verify.py` executes commands read from the manifest. It never uses a shell:
every command is split with `shlex` and passed as an argument list, so a manifest
entry cannot chain, redirect or glob. The trust boundary is written out in that
file's module docstring.

## Status

Validation, rendering, evidence verification and the DoD check are implemented.
The `postTaskExecution` completion hook (`on_task_complete.py`) is spec task 2.3
and does not exist yet, so status changes are still made by editing the manifest."""


# Directories holding real scripts document them. The rest get the scaffold note.
SCRIPT_README_BODIES = {
    "bootstrap": """Contains `scaffold_repository.py`, which materializes the target
repository structure and is safe to re-run.

## Status

Implemented.""",
    "development": """## check.py - the quality gate

```bash
make check                            # or: python scripts/development/check.py
```

Runs four steps in order, each with no arguments because `pyproject.toml` holds
every setting:

| Step        | Command                            |
| ----------- | ---------------------------------- |
| `format`    | `python -m ruff format --check .`  |
| `lint`      | `python -m ruff check .`           |
| `typecheck` | `python -m mypy`                   |
| `test`      | `python -m pytest`                 |

All four run even when an earlier one fails, and the summary names every failing
step with the command that fixes it. Exit status is non-zero when any step
failed. Pass `--fail-fast` to stop at the first failure.

This is the single documented command of requirement 3.6. `make lint` and
`make test` exist only for narrowing a failure; CI runs `make check`.

Formatting is checked, never rewritten. To rewrite in place: `make format`.

## health.py - backing service reachability

```bash
make health                           # or: python scripts/development/health.py
```

Reports whether PostgreSQL and Redis are reachable, reading `POSTGRES_HOST`,
`POSTGRES_PORT`, `REDIS_HOST`, `REDIS_PORT` and `REDIS_PASSWORD` from the
environment, then from `.env` for anything not already exported. Exit status is
non-zero when either is unreachable, and each failure prints remediation.

Both probes use raw sockets from the standard library. No database driver is
installed yet, and adding one for a health probe would put a runtime dependency
in the tree ahead of the code that needs it.

- PostgreSQL: TCP connect plus the protocol SSLRequest handshake. This proves a
  PostgreSQL server is listening. It does **not** verify credentials, the
  database name, or migration state.
- Redis: TCP connect plus a real `PING` over RESP, with `AUTH` first when
  `REDIS_PASSWORD` is set. A wrong password is reported rather than passed over.

Start the services with `make up`.

## Status

Implemented.""",
    "testing": """Contains `validate_structure.py`, which verifies every path in the target
repository structure exists, that all JSON and YAML parses, and that no
secret-bearing file is tracked by Git.

```bash
python scripts/testing/validate_structure.py
```

Requires PyYAML for the YAML checks; they are skipped if it is unavailable.

## Status

Structure validation implemented. Application test orchestration pending.""",
    "status": STATUS_SCRIPTS_README,
}


# The two development commands are held here as text so that a tree built by
# this generator alone is complete. `tests/unit/test_quality_command.py` asserts
# these copies match the files on disk, so the duplication cannot drift.

CHECK_SCRIPT = r'''#!/usr/bin/env python3
"""The single quality command: format, lint, type check, unit tests.

Requirement 3.6 asks for one documented command that runs formatting, linting,
type checking and unit tests. That command is:

    make check          (or: python scripts/development/check.py)

Every step is invoked with no arguments because `pyproject.toml` already supplies
the file selection, the strictness settings and the coverage configuration. Any
argument added here would be a second, undocumented source of configuration.

Steps, in order:

    1. python -m ruff format --check .   formatting is checked, never rewritten
    2. python -m ruff check .            lint
    3. python -m mypy                    strict type check
    4. python -m pytest                  unit tests with coverage

Run-all, not fail-fast
----------------------
Every step runs even after an earlier one fails, and the exit status is non-zero
when any step failed. The reason is that these four steps are independent
verdicts on the same tree: a lint error tells you nothing about whether the type
checker is happy, so stopping at the first failure hides work that the developer
would have to discover one round trip at a time. The four steps together take
seconds on this repository, so there is no meaningful time saved by stopping
early.

`--fail-fast` is available for the case where that trade changes, for example a
CI job that only needs a pass/fail verdict as cheaply as possible.

Exit status:
    0   every step passed
    1   at least one step failed; the summary names each failing step
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Step:
    """One quality gate step and how to fix it."""

    name: str
    description: str
    argv: tuple[str, ...]
    remedy: str


# `sys.executable -m <tool>` rather than a bare `ruff`/`mypy`/`pytest` entry
# point, so the tools that run are the ones installed in the interpreter running
# this script rather than whatever happens to be first on PATH.
STEPS: tuple[Step, ...] = (
    Step(
        name="format",
        description="formatting (ruff format --check)",
        argv=(sys.executable, "-m", "ruff", "format", "--check", "."),
        remedy="python -m ruff format .",
    ),
    Step(
        name="lint",
        description="lint (ruff check)",
        argv=(sys.executable, "-m", "ruff", "check", "."),
        remedy="python -m ruff check --fix .",
    ),
    Step(
        name="typecheck",
        description="type check (mypy, strict)",
        argv=(sys.executable, "-m", "mypy"),
        remedy="fix the reported types; mypy runs in strict mode",
    ),
    Step(
        name="test",
        description="unit tests (pytest with coverage)",
        argv=(sys.executable, "-m", "pytest"),
        remedy="python -m pytest -x -vv",
    ),
)


@dataclass(frozen=True)
class Result:
    """Outcome of one step."""

    step: Step
    returncode: int
    seconds: float

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_step(step: Step) -> Result:
    """Run one step from the repository root and time it."""
    print(f"\n>>> {step.name}: {' '.join(step.argv)}", flush=True)
    started = time.monotonic()
    completed = subprocess.run(step.argv, cwd=ROOT, check=False)
    return Result(step=step, returncode=completed.returncode, seconds=time.monotonic() - started)


def run(steps: Sequence[Step], *, fail_fast: bool) -> list[Result]:
    """Run the steps, stopping at the first failure only when asked to."""
    results: list[Result] = []
    for step in steps:
        result = run_step(step)
        results.append(result)
        if fail_fast and not result.ok:
            print(f"\n--fail-fast: stopping after {step.name}", flush=True)
            break
    return results


def report(results: Sequence[Result], total: Sequence[Step]) -> int:
    """Print the summary and return the process exit status."""
    print("\n" + "=" * 72)
    print("quality gate summary")
    print("=" * 72)

    for result in results:
        status = "PASS" if result.ok else "FAIL"
        step = result.step
        print(f"  {status}  {step.name:<10} {step.description} ({result.seconds:.1f}s)")

    skipped = [step for step in total if step.name not in {r.step.name for r in results}]
    for step in skipped:
        print(f"  SKIP  {step.name:<10} {step.description}")

    failed = [result for result in results if not result.ok]
    if not failed:
        print("\nall checks passed")
        return 0

    print(f"\n{len(failed)} step(s) failed:")
    for result in failed:
        print(f"  - {result.step.name} (exit {result.returncode}): {result.step.remedy}")
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/development/check.py",
        description="Run formatting, lint, type check and unit tests as one command.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="stop at the first failing step instead of running all four",
    )
    args = parser.parse_args(argv)

    print(f"AgentRouter quality gate: {len(STEPS)} steps in {ROOT}")
    results = run(STEPS, fail_fast=bool(args.fail_fast))
    return report(results, STEPS)


if __name__ == "__main__":
    sys.exit(main())
'''

HEALTH_SCRIPT = r'''#!/usr/bin/env python3
"""Report whether the local PostgreSQL and Redis are reachable.

Requirement 3.4 asks for a documented health command that reports both backing
services as reachable. That command is:

    make health         (or: python scripts/development/health.py)

Connection settings come from the environment, using the variable names declared
in `.env.example` (POSTGRES_HOST, POSTGRES_PORT, REDIS_HOST, REDIS_PORT,
REDIS_PASSWORD). A `.env` file at the repository root is read when present, and
never overrides a value already exported in the environment.

What is verified, and what is not
---------------------------------
No database driver is used. There is no runtime dependency group in this
repository yet and adding `psycopg` or `redis` to satisfy a health probe would
put a production dependency in the tree ahead of the code that needs it. Both
checks therefore run over a raw TCP socket from the standard library:

  * PostgreSQL: a TCP connect plus the protocol-level SSLRequest handshake. The
    server answers a single byte, 'S' or 'N', only if it speaks the PostgreSQL
    frontend/backend protocol. This proves a PostgreSQL server is listening.
    It does NOT verify credentials, the database name, or that the schema is
    migrated: authenticating requires the full startup and SASL exchange, which
    is a driver's job.

  * Redis: a TCP connect plus a real PING command over RESP. A `+PONG` reply
    proves a Redis server is listening and answering commands. When
    REDIS_PASSWORD is set, AUTH is sent before PING, so a wrong password is
    reported rather than passed over. The password is never printed.

Exit status:
    0   every dependency reachable
    1   at least one dependency unreachable; remediation is printed for each
"""

from __future__ import annotations

import os
import socket
import struct
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"

CONNECT_TIMEOUT_SECONDS = 3.0

# PostgreSQL SSLRequest: int32 length (8) followed by the request code
# 1234 << 16 | 5679. Documented in the PostgreSQL frontend/backend protocol as
# the message a client may send before the StartupMessage.
POSTGRES_SSL_REQUEST = struct.pack("!ii", 8, 80877103)

COMPOSE_UP = (
    "docker compose -f deployments/docker/docker-compose.yml "
    "-f deployments/docker/docker-compose.dev.yml up -d"
)


@dataclass(frozen=True)
class Check:
    """Outcome of one dependency check."""

    name: str
    target: str
    ok: bool
    detail: str
    remedy: tuple[str, ...] = ()
    caveat: str = ""


def load_env_file(path: Path = ENV_FILE) -> None:
    """Read KEY=VALUE lines from `.env` without overriding the real environment.

    Deliberately minimal: no interpolation, no export keyword, no multi-line
    values. Anything more belongs in packages/configuration (task 5.1), which
    owns real configuration loading.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def setting(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def port_setting(name: str, default: int) -> int:
    raw = setting(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def open_socket(host: str, port: int) -> socket.socket:
    """TCP connect with a bounded timeout. Raises OSError on failure."""
    sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT_SECONDS)
    sock.settimeout(CONNECT_TIMEOUT_SECONDS)
    return sock


def unreachable(name: str, target: str, exc: OSError, remedy: tuple[str, ...]) -> Check:
    reason = exc.strerror or str(exc) or exc.__class__.__name__
    return Check(
        name=name,
        target=target,
        ok=False,
        detail=f"cannot connect: {reason}",
        remedy=remedy,
    )


def check_postgres() -> Check:
    """TCP reachability plus the PostgreSQL SSLRequest handshake. No auth check."""
    host = setting("POSTGRES_HOST", "localhost")
    port = port_setting("POSTGRES_PORT", 5432)
    target = f"{host}:{port}"
    database = setting("POSTGRES_DB", "agentrouter")
    remedy = (
        f"start it: {COMPOSE_UP}",
        "confirm POSTGRES_HOST and POSTGRES_PORT in .env match the published port",
        "check the container: docker compose -f deployments/docker/docker-compose.yml ps",
    )

    try:
        with open_socket(host, port) as sock:
            sock.sendall(POSTGRES_SSL_REQUEST)
            reply = sock.recv(1)
    except OSError as exc:
        return unreachable("PostgreSQL", target, exc, remedy)

    caveat = (
        f"protocol handshake only; credentials, database {database!r} and "
        "migration state are not verified (no driver installed yet)"
    )
    if reply in (b"S", b"N"):
        tls = "available" if reply == b"S" else "not offered"
        return Check(
            name="PostgreSQL",
            target=target,
            ok=True,
            detail=f"reachable, speaks the PostgreSQL protocol (TLS {tls})",
            caveat=caveat,
        )
    if reply == b"E":
        # An ErrorResponse still proves a PostgreSQL server answered.
        return Check(
            name="PostgreSQL",
            target=target,
            ok=True,
            detail="reachable, PostgreSQL answered the handshake with an error response",
            caveat=caveat,
        )
    return Check(
        name="PostgreSQL",
        target=target,
        ok=False,
        detail=(
            f"port accepts connections but answered {reply!r} to the SSLRequest handshake, "
            "so the listener is not PostgreSQL"
        ),
        remedy=(
            f"another process is bound to {target}; stop it or set POSTGRES_PORT to a free port",
            f"then: {COMPOSE_UP}",
        ),
    )


def resp_command(*parts: str) -> bytes:
    """Encode a Redis command as a RESP array of bulk strings."""
    out = [f"*{len(parts)}\r\n".encode()]
    for part in parts:
        encoded = part.encode()
        out.append(f"${len(encoded)}\r\n".encode() + encoded + b"\r\n")
    return b"".join(out)


def check_redis() -> Check:
    """TCP reachability plus a real PING over RESP, with AUTH when configured."""
    host = setting("REDIS_HOST", "localhost")
    port = port_setting("REDIS_PORT", 6379)
    password = os.environ.get("REDIS_PASSWORD", "")
    target = f"{host}:{port}"
    remedy = (
        f"start it: {COMPOSE_UP}",
        "confirm REDIS_HOST and REDIS_PORT in .env match the published port",
        "check the container: docker compose -f deployments/docker/docker-compose.yml ps",
    )

    try:
        with open_socket(host, port) as sock:
            if password:
                sock.sendall(resp_command("AUTH", password))
                auth_reply = sock.recv(256)
                # A server with no password set rejects AUTH; PING still decides.
                if auth_reply.startswith(b"-") and b"without any password" not in auth_reply:
                    return Check(
                        name="Redis",
                        target=target,
                        ok=False,
                        detail="reachable but AUTH was refused",
                        remedy=(
                            "REDIS_PASSWORD does not match the running server",
                            "clear REDIS_PASSWORD in .env when the local Redis has no password",
                        ),
                    )
            sock.sendall(resp_command("PING"))
            reply = sock.recv(256)
    except OSError as exc:
        return unreachable("Redis", target, exc, remedy)

    if reply.startswith(b"+PONG"):
        scope = "authenticated" if password else "no password configured"
        return Check(
            name="Redis",
            target=target,
            ok=True,
            detail=f"reachable, PING answered PONG ({scope})",
        )
    if reply.startswith(b"-NOAUTH"):
        return Check(
            name="Redis",
            target=target,
            ok=False,
            detail="reachable, but the server requires authentication",
            remedy=("set REDIS_PASSWORD in .env to the password the running Redis expects",),
        )
    return Check(
        name="Redis",
        target=target,
        ok=False,
        detail=(
            f"port accepts connections but answered {reply[:40]!r} to PING, "
            "so the listener is not Redis"
        ),
        remedy=(
            f"another process is bound to {target}; stop it or set REDIS_PORT to a free port",
            f"then: {COMPOSE_UP}",
        ),
    )


def report(checks: Sequence[Check]) -> int:
    """Print each result with remediation and return the process exit status."""
    print("AgentRouter local environment health")
    print("=" * 72)
    for check in checks:
        status = "OK  " if check.ok else "DOWN"
        print(f"  [{status}] {check.name:<11} {check.target:<22} {check.detail}")
        if check.caveat:
            print(f"           note: {check.caveat}")

    failed = [check for check in checks if not check.ok]
    if not failed:
        print("\nall dependencies reachable")
        return 0

    print(f"\n{len(failed)} dependency(ies) unreachable:")
    for check in failed:
        print(f"\n  {check.name} at {check.target}: {check.detail}")
        for line in check.remedy:
            print(f"    - {line}")
    print(
        "\nA local .env is required by the compose file: cp .env.example .env and set "
        "POSTGRES_PASSWORD."
    )
    return 1


def main() -> int:
    load_env_file()
    return report([check_postgres(), check_redis()])


if __name__ == "__main__":
    sys.exit(main())
'''


def section_scripts() -> None:
    for name, purpose in SCRIPT_DIRS.items():
        mkdir(f"scripts/{name}")
        if name not in {"bootstrap", "development", "status"}:
            write(f"scripts/{name}/.gitkeep", "")
        body = SCRIPT_README_BODIES.get(name, "## Status\n\nScaffold, not implemented.")
        readme(f"scripts/{name}/README.md", f"scripts/{name}", f"{purpose}\n\n{body}")

    write("scripts/development/check.py", CHECK_SCRIPT)
    write("scripts/development/health.py", HEALTH_SCRIPT)

    width = max(len(n) for n in SCRIPT_DIRS) + 2
    readme(
        "scripts/README.md",
        "Scripts",
        """Repository automation.

"""
        + tree([f"{n + '/':<{width}} {p}" for n, p in SCRIPT_DIRS.items()])
        + """

## Available now

```bash
python scripts/bootstrap/scaffold_repository.py   # recreate anything missing
python scripts/testing/validate_structure.py      # verify the tree
python scripts/development/check.py               # format, lint, types, tests
python scripts/development/health.py              # PostgreSQL and Redis reachability
python scripts/status/validate.py                 # manifest matches its schema
python scripts/status/render.py --check           # status document is not stale
python scripts/status/verify.py                   # evidence of implemented components
python scripts/status/check_dod.py                # no implemented component is incomplete
```

The scaffold recreates any missing part of the target structure. Existing files
are never overwritten. `docs/IMPLEMENTATION_STATUS.md` is the one file it does not
author: it delegates to `scripts/status/render.py`, so the manifest stays the only
source of that document.""",
    )


# ---------------------------------------------------------------------------
# docs
# ---------------------------------------------------------------------------

DOCS: dict[str, list[tuple[str, str, str]]] = {
    "architecture": [
        (
            "overview.md",
            "Architecture Overview",
            "Entry point into the architecture documentation set.",
        ),
        (
            "system-architecture.md",
            "System Architecture",
            "The three planes and how they interact: data, control and integration.",
        ),
        ("data-plane.md", "Data Plane", "Live AI request path and its latency budget."),
        (
            "control-plane.md",
            "Control Plane",
            "Organization, identity, policy, registry, billing, analytics and audit management.",
        ),
        (
            "routing-engine.md",
            "Routing Engine",
            "Candidate generation, filtering, scoring, modes, escalation and fallback. The core IP.",
        ),
        (
            "provider-gateway.md",
            "Provider Gateway",
            "Adapter interface, health tracking, failover and error normalization.",
        ),
        (
            "security-architecture.md",
            "Security Architecture",
            "Trust boundaries, tenant isolation, secrets and network posture.",
        ),
    ],
    "integrations": [
        (
            "mcp.md",
            "MCP Integration",
            "Tools, resources, authentication and the limits of what MCP can control.",
        ),
        ("vscode.md", "VS Code Integration", "Supported mechanisms, setup and capability profile."),
        ("kiro.md", "Kiro Integration", "Supported mechanisms, setup and capability profile."),
        ("cursor.md", "Cursor Integration", "Supported mechanisms, setup and capability profile."),
        (
            "jetbrains.md",
            "JetBrains Integration",
            "Supported mechanisms, setup and capability profile.",
        ),
    ],
    "deployment": [
        (
            "cloud.md",
            "Cloud Deployment",
            "SaaS topology: DNS, WAF, load balancer, gateway, Kubernetes, data stores.",
        ),
        (
            "kubernetes.md",
            "Kubernetes Deployment",
            "Namespaces, workloads, scaling and network policy.",
        ),
        (
            "helm.md",
            "Helm Installation",
            "Chart values, upgrade path and production configuration.",
        ),
        ("self-hosted.md", "Self-Hosted Deployment", "Customer-managed Kubernetes installation."),
        (
            "private-cloud.md",
            "Private Deployment",
            "No public internet access, private endpoints, customer identity and monitoring.",
        ),
    ],
    "security": [
        (
            "security.md",
            "Security",
            "Security model across identity, network, application, data and infrastructure.",
        ),
        (
            "data-privacy.md",
            "Data Privacy",
            "What is stored, what is not, and configurable retention.",
        ),
        (
            "authentication.md",
            "Authentication",
            "OIDC, OAuth, SAML SSO, API keys and service accounts.",
        ),
        (
            "authorization.md",
            "Authorization",
            "RBAC roles, granular permissions and resource-level checks.",
        ),
        (
            "threat-model.md",
            "Threat Model",
            "Assets, adversaries, trust boundaries and mitigations.",
        ),
    ],
    "operations": [
        ("monitoring.md", "Monitoring", "Metrics, dashboards, alerts and what each alert means."),
        (
            "incident-response.md",
            "Incident Response",
            "Operational incident handling. See also security/incident-response/.",
        ),
        (
            "disaster-recovery.md",
            "Disaster Recovery",
            "RPO, RTO, backup frequency, restore procedure and restore testing.",
        ),
        (
            "troubleshooting.md",
            "Troubleshooting",
            "Tracing a request by request ID and diagnosing common failures.",
        ),
    ],
    "customer": [
        (
            "onboarding.md",
            "Customer Onboarding",
            "Account, organization, SSO, providers, models, policies, client, IDE, first request.",
        ),
        (
            "administrator-guide.md",
            "Administrator Guide",
            "Managing providers, models, routing, policies, budgets, users, teams and retention.",
        ),
        (
            "developer-guide.md",
            "Developer Guide",
            "Install, login, connect the IDE, start working.",
        ),
        (
            "finops-guide.md",
            "FinOps Guide",
            "Spend, forecast, budgets, cost per team and savings interpretation.",
        ),
    ],
    "product": [
        ("vision.md", "Product Vision", "What AgentRouter is and the problem it solves."),
        ("roadmap.md", "Roadmap", "Phase sequence derived from the master specification."),
        ("requirements.md", "Requirements", "Functional and non-functional requirements."),
    ],
}


# ---------------------------------------------------------------------------
# completion ledger (spec task 2.1)
# ---------------------------------------------------------------------------
#
# The status manifest and its schema are held here as text so that a tree built
# by this generator alone is complete. `tests/unit/test_status_manifest.py`
# asserts these copies match the files on disk, so the duplication cannot drift.
#
# The manifest is data, not documentation: `docs/IMPLEMENTATION_STATUS.md` is
# generated from it. Seeding it here means a fresh clone starts from an honest
# ledger rather than an empty one.

STATUS_SCHEMA = r"""{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agentrouter.dev/schemas/status-manifest.schema.json",
  "title": "AgentRouter status manifest",
  "description": "Schema for docs/implementation-status.yaml, the Status_Manifest. The manifest is the single machine-readable source of truth for what actually works; docs/IMPLEMENTATION_STATUS.md is generated from it. Requirement 1.3 requires this schema to be committed and the pipeline to fail when the manifest violates it. Every object here sets additionalProperties to false, so a mistyped key is a validation error rather than silently ignored data.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "version",
    "components"
  ],
  "properties": {
    "version": {
      "description": "Manifest format version. Bumped only by a change that readers must handle.",
      "const": 1
    },
    "components": {
      "description": "One entry per tracked component. Requirement 1.1 requires an entry for each of the 30 product modules of Master_Specification section 6; entries with category 'foundation' cover work that section 6 does not name.",
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/component"
      }
    }
  },
  "$defs": {
    "component": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "id",
        "name",
        "category",
        "group",
        "status",
        "phase",
        "implementation",
        "tests",
        "evidence",
        "component_dod",
        "limitations"
      ],
      "properties": {
        "id": {
          "description": "Stable slug. scripts/status/on_task_complete.py maps a completed task to its component through this value, so renaming one is a breaking change. Uniqueness across components is not expressible in JSON Schema; it is asserted by tests/unit/test_status_manifest.py and by scripts/status/validate.py.",
          "type": "string",
          "pattern": "^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
          "minLength": 2,
          "maxLength": 60
        },
        "name": {
          "description": "Human-readable component name used in the generated status document.",
          "type": "string",
          "minLength": 1,
          "maxLength": 80
        },
        "category": {
          "description": "Provenance of the entry. 'product_module' means the component is one of the 30 modules of Master_Specification section 6 and must carry a 'module' field. 'foundation' means repository, environment, database, test-harness or pipeline work that section 6 does not name; such an entry must not carry a 'module' field.",
          "enum": [
            "product_module",
            "foundation"
          ]
        },
        "module": {
          "description": "The Master_Specification section 6 entry verbatim: two-digit number and name, for example '09 Routing Engine'. Required for, and permitted only on, category 'product_module'.",
          "type": "string",
          "pattern": "^(0[1-9]|[12][0-9]|30) [A-Z][A-Za-z0-9 /-]*$"
        },
        "group": {
          "description": "Presentation grouping for the generated status document. Carries no semantics beyond ordering sections.",
          "enum": [
            "foundation",
            "services",
            "integrations",
            "clients",
            "platform"
          ]
        },
        "status": {
          "$ref": "#/$defs/status"
        },
        "phase": {
          "description": "Step number in the 46-step Implementation_Sequence of Master_Specification section 132 that delivers this component.",
          "type": "integer",
          "minimum": 1,
          "maximum": 46
        },
        "implementation": {
          "description": "Repository-relative location of the implementation. Requirement 1.2 makes it a substantiated claim once status is 'implemented'; at any other status it is the declared target location and need not exist yet.",
          "$ref": "#/$defs/path"
        },
        "tests": {
          "description": "Repository-relative location of the tests. Requirement 1.2 makes it a substantiated claim once status is 'implemented'; otherwise it is the declared target location.",
          "$ref": "#/$defs/path"
        },
        "evidence": {
          "description": "Named, re-runnable Verification_Evidence commands. Requirement 1.6: for a component recorded as 'implemented', every command must exist and exit zero. An empty list is valid only while the component is not 'implemented', because a component with no code has no command that could substantiate a claim.",
          "type": "array",
          "items": {
            "$ref": "#/$defs/evidence"
          }
        },
        "component_dod": {
          "$ref": "#/$defs/component_dod"
        },
        "dod_not_applicable": {
          "description": "Component_DoD items recorded true because the specification's 'where applicable' qualifier does not apply here, rather than because work was done. Master_Specification section 134 attaches that qualifier to exactly three items, so only those three may appear. Naming them stops a true boolean being read as a completed task; the justification belongs in 'notes'.",
          "type": "array",
          "uniqueItems": true,
          "items": {
            "enum": [
              "integration_tests",
              "metrics",
              "deployment"
            ]
          }
        },
        "limitations": {
          "description": "Every known limitation of the component, in prose. Requirement 1.8 requires this for components recorded as 'implemented'; an empty list is a positive claim that none is known.",
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "placeholders": {
          "description": "Non-buildable placeholder artifacts owned by this component. Requirement 2.8 requires the manifest to describe every such artifact in the repository as a placeholder, so an artifact that does not build, render or execute is recorded here rather than left looking finished.",
          "type": "array",
          "items": {
            "$ref": "#/$defs/placeholder"
          }
        },
        "blocked_reason": {
          "description": "What blocks the component, including the captured failure output when scripts/status/on_task_complete.py records 'blocked' instead of promoting. Required for, and permitted only on, status 'blocked'.",
          "type": "string",
          "minLength": 1
        },
        "notes": {
          "description": "Context for the generated status document: which part is real, which part is scaffold, why a 'where applicable' item does not apply.",
          "type": "string",
          "minLength": 1
        }
      },
      "allOf": [
        {
          "$comment": "A product module carries its section 6 identifier and a foundation entry must not, so the 30 modules can be counted from the data.",
          "if": {
            "properties": {
              "category": {
                "const": "product_module"
              }
            },
            "required": [
              "category"
            ]
          },
          "then": {
            "required": [
              "module"
            ]
          },
          "else": {
            "not": {
              "required": [
                "module"
              ]
            }
          }
        },
        {
          "$comment": "Requirement 1.2: implementation location, test location and evidence command become mandatory content once a component claims 'implemented'. Requirement 1.7: fewer than all twelve Component_DoD items forbids that claim. Both are enforced here; scripts/status/check_dod.py repeats the DoD rule to name the offending items in its failure output.",
          "if": {
            "properties": {
              "status": {
                "const": "implemented"
              }
            },
            "required": [
              "status"
            ]
          },
          "then": {
            "properties": {
              "evidence": {
                "minItems": 1
              },
              "component_dod": {
                "$ref": "#/$defs/component_dod_all_true"
              }
            },
            "required": [
              "implementation",
              "tests",
              "evidence",
              "component_dod",
              "limitations"
            ]
          }
        },
        {
          "$comment": "A blocked component states what blocks it, so 'blocked' cannot become a silent parking space.",
          "if": {
            "properties": {
              "status": {
                "const": "blocked"
              }
            },
            "required": [
              "status"
            ]
          },
          "then": {
            "required": [
              "blocked_reason"
            ]
          },
          "else": {
            "not": {
              "required": [
                "blocked_reason"
              ]
            }
          }
        }
      ]
    },
    "status": {
      "description": "Status_Values from the requirements glossary. The underscore spelling is canonical in the manifest; the generated document renders the display form.",
      "enum": [
        "not_started",
        "in_progress",
        "implemented",
        "blocked"
      ]
    },
    "path": {
      "description": "Repository-relative POSIX path. Leading slashes, backslashes, drive letters and parent-directory segments are rejected, so a manifest path cannot address anything outside the repository. A '*' segment stands for a set of sibling paths, for example 'services/*/Dockerfile'.",
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "pattern": "^(?!.*\\.\\.)[A-Za-z0-9._*][A-Za-z0-9._*-]*(/[A-Za-z0-9._*][A-Za-z0-9._*-]*)*$"
    },
    "evidence": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "name",
        "command"
      ],
      "properties": {
        "name": {
          "description": "Short identifier that the completion hook writes back into the spec task sheet, per Requirement 1.10.",
          "type": "string",
          "pattern": "^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
          "minLength": 2,
          "maxLength": 60
        },
        "command": {
          "description": "The exact command to run from the repository root. It must be re-runnable and non-interactive: scripts/status/verify.py executes it and fails on a non-zero exit.",
          "type": "string",
          "minLength": 1,
          "maxLength": 300
        }
      }
    },
    "placeholder": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "path",
        "kind",
        "reason"
      ],
      "properties": {
        "path": {
          "description": "Repository-relative path of the placeholder artifact.",
          "$ref": "#/$defs/path"
        },
        "kind": {
          "description": "Artifact sort, so the generated document can group placeholders.",
          "enum": [
            "dockerfile",
            "helm_template",
            "kubernetes_manifest",
            "terraform_module",
            "api_contract",
            "ci_workflow",
            "make_target",
            "directory",
            "other"
          ]
        },
        "reason": {
          "description": "Why it does not build, render or execute, stated plainly.",
          "type": "string",
          "minLength": 1
        }
      }
    },
    "component_dod": {
      "description": "The twelve-item Component_DoD of Master_Specification section 134. True means the item is satisfied. Three items carry the specification's 'where applicable' qualifier; when one of those is true because it does not apply, it is named in 'dod_not_applicable' and explained in 'notes'.",
      "type": "object",
      "additionalProperties": false,
      "required": [
        "implementation",
        "unit_tests",
        "integration_tests",
        "error_handling",
        "security_reviewed",
        "logging",
        "metrics",
        "documentation",
        "api_contract",
        "configuration",
        "deployment",
        "ci_validated"
      ],
      "properties": {
        "implementation": {
          "description": "Implementation exists.",
          "type": "boolean"
        },
        "unit_tests": {
          "description": "Unit tests exist.",
          "type": "boolean"
        },
        "integration_tests": {
          "description": "Integration tests exist where applicable.",
          "type": "boolean"
        },
        "error_handling": {
          "description": "Errors are handled.",
          "type": "boolean"
        },
        "security_reviewed": {
          "description": "Security is considered.",
          "type": "boolean"
        },
        "logging": {
          "description": "Logging is implemented.",
          "type": "boolean"
        },
        "metrics": {
          "description": "Metrics are implemented where applicable.",
          "type": "boolean"
        },
        "documentation": {
          "description": "Documentation exists.",
          "type": "boolean"
        },
        "api_contract": {
          "description": "An API contract exists.",
          "type": "boolean"
        },
        "configuration": {
          "description": "Configuration exists.",
          "type": "boolean"
        },
        "deployment": {
          "description": "Deployment exists where applicable.",
          "type": "boolean"
        },
        "ci_validated": {
          "description": "CI validates it.",
          "type": "boolean"
        }
      }
    },
    "component_dod_all_true": {
      "$comment": "Applied only under status 'implemented', on top of #/$defs/component_dod, which is where the twelve keys and their descriptions are declared once.",
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "implementation": {
          "const": true
        },
        "unit_tests": {
          "const": true
        },
        "integration_tests": {
          "const": true
        },
        "error_handling": {
          "const": true
        },
        "security_reviewed": {
          "const": true
        },
        "logging": {
          "const": true
        },
        "metrics": {
          "const": true
        },
        "documentation": {
          "const": true
        },
        "api_contract": {
          "const": true
        },
        "configuration": {
          "const": true
        },
        "deployment": {
          "const": true
        },
        "ci_validated": {
          "const": true
        }
      }
    }
  }
}
"""

STATUS_MANIFEST = """# AgentRouter status manifest (Status_Manifest).
#
# This file is the single machine-readable record of what actually works.
# `docs/IMPLEMENTATION_STATUS.md` is generated from it by
# `python scripts/status/render.py`; edit this file, never the generated document.
#
# Schema: docs/status-manifest.schema.json (validated by scripts/status/validate.py,
# gated in CI as `status-schema` per Requirement 1.3).
#
# After changing anything here, run all four gates:
#
#   python scripts/status/validate.py
#   python scripts/status/render.py          # then commit the regenerated document
#   python scripts/status/verify.py
#   python scripts/status/check_dod.py
#
# A component's own evidence list never names `scripts/status/verify.py`: that is
# the script running the list, so listing it would make the gate recurse into
# itself.
#
# Rules this file exists to enforce
# ---------------------------------
#   * Requirement 1.1 - every one of the 30 product modules of Master_Specification
#     section 6 has an entry, with a status from {not_started, in_progress,
#     implemented, blocked}.
#   * Requirement 1.2 - an entry may only claim `implemented` while naming its
#     implementation location, its test location and at least one Verification_Evidence
#     command. The schema makes those conditional on the status: a component at
#     `not_started` has no command that could substantiate a claim, so requiring one
#     everywhere would force invented evidence, which is the failure mode Requirement 2
#     exists to prevent. `implementation` and `tests` are always present because they
#     also serve as the declared target location; under `implemented` they become a
#     claim about something that exists.
#   * Requirement 1.7 - `implemented` requires all twelve Component_DoD items true.
#     The schema enforces this directly with a conditional subschema, so a manifest
#     that claims completion on an incomplete checklist fails `status-schema` as well
#     as `status-dod`.
#   * Requirement 1.8 - `limitations` lists every known limitation. An empty list is
#     a positive claim that none is known.
#   * Requirement 2.8 - `placeholders` records every artifact that looks finished but
#     does not build, render or execute.
#
# Status honesty
# --------------
# Nothing here is `implemented`. Three components are `in_progress` because real,
# tested code exists for them; the rest are `not_started`. The scaffold is extensive,
# but a materialized directory tree is not an implementation, and Requirement 1.7
# means partial credit is recorded in `component_dod`, never in `status`.
#
# Where a Component_DoD item is true because Master_Specification section 134's
# "where applicable" qualifier does not apply, the item is named in
# `dod_not_applicable` so a reader cannot mistake it for completed work. Section 134
# attaches that qualifier to exactly three items: integration tests, metrics and
# deployment.
#
# Non-section-6 entries
# --------------------
# Section 6 names 30 product modules. It does not name the repository foundation, the
# development environment, this completion ledger, the shared contracts, the database,
# the event system, the verification suites or the documentation set, yet each is a
# distinct step of the 46-step Implementation_Sequence (or, for the ledger, a control
# required by Requirement 1) with its own artifacts and its own Component_DoD. Eight
# entries carry `category: foundation` for that reason, and are excluded from the
# 30-module count asserted in tests/unit/test_status_manifest.py. Steps 44 to 46 of the
# sequence (customer onboarding, production hardening, enterprise deployment
# validation) get no entry: they are platform-level readiness activities measured by
# the 29-item Production_DoD, not components.

version: 1

components:
  # -------------------------------------------------------------------------
  # Foundation (not named in Master_Specification section 6)
  # -------------------------------------------------------------------------

  - id: repository-foundation
    name: Repository foundation
    category: foundation
    group: foundation
    status: in_progress
    phase: 1
    implementation: scripts/bootstrap/scaffold_repository.py
    tests: tests/unit
    evidence:
      - name: scaffold-idempotent
        command: python scripts/bootstrap/scaffold_repository.py
      - name: structure-valid
        command: python scripts/testing/validate_structure.py
    component_dod:
      implementation: true
      unit_tests: false
      integration_tests: false
      error_handling: true
      security_reviewed: true
      logging: false
      metrics: true
      documentation: true
      api_contract: false
      configuration: false
      deployment: true
      ci_validated: true
    dod_not_applicable:
      - metrics
      - deployment
    limitations:
      - "The target structure is embedded in the generator as code, not read from a data file, so the structure definition and its validator list are maintained in two places."
      - "The generator and the structure validator have no dedicated unit suite; only the byte-for-byte constant guards in tests/unit/test_quality_command.py and tests/unit/test_status_manifest.py protect them from drift."
      - "`docs/IMPLEMENTATION_STATUS.md` is the one file the generator does not author: it delegates to scripts/status/render.py. On a checkout without PyYAML the generator reports that file as pending instead of writing it."
    placeholders:
      - path: Makefile
        kind: make_target
        reason: "The `build` and `migrate` targets print a message and exit 1. They fail loudly rather than pretending to succeed, but neither builds nor migrates anything."
    notes: >-
      Repository tooling is not deployed and emits no metrics, so those two
      Component_DoD items are recorded as not applicable rather than done.
      Structured logging and a declared contract for the generator's output are
      genuinely absent.

  - id: development-environment
    name: Development environment and quality gate
    category: foundation
    group: foundation
    status: in_progress
    phase: 2
    implementation: scripts/development
    tests: tests/unit
    evidence:
      - name: quality-gate
        command: python scripts/development/check.py
      - name: dependency-manifests
        command: python -m pytest tests/unit/test_dependency_manifests.py -q
    component_dod:
      implementation: true
      unit_tests: true
      integration_tests: false
      error_handling: true
      security_reviewed: true
      logging: false
      metrics: true
      documentation: true
      api_contract: false
      configuration: true
      deployment: true
      ci_validated: true
    dod_not_applicable:
      - metrics
      - deployment
    limitations:
      - "`scripts/development/health.py` is exercised only against stubbed sockets; no automated test starts the Compose stack, so the reachability path is unverified end to end."
      - "The Compose stack starts PostgreSQL and Redis only. No application service is buildable, so `make up` produces backing services and nothing else."
      - "Coverage `fail_under` is 0 because there is no source to measure yet."
    notes: >-
      `health.py` is deliberately excluded from the evidence list: it requires a
      running Docker daemon, so as evidence it would fail in CI for an
      environmental reason rather than a real one.

  - id: completion-ledger
    name: Completion ledger
    category: foundation
    group: foundation
    status: in_progress
    phase: 2
    implementation: scripts/status
    tests: tests/unit/test_status_manifest.py
    evidence:
      - name: status-manifest
        command: python -m pytest tests/unit/test_status_manifest.py -q
      - name: status-scripts
        command: python -m pytest tests/unit/test_status_scripts.py -q
      - name: status-schema
        command: python scripts/status/validate.py
      - name: status-render
        command: python scripts/status/render.py --check
      - name: status-dod
        command: python scripts/status/check_dod.py
    component_dod:
      implementation: true
      unit_tests: true
      integration_tests: false
      error_handling: true
      security_reviewed: true
      logging: false
      metrics: true
      documentation: true
      api_contract: true
      configuration: false
      deployment: true
      ci_validated: false
    dod_not_applicable:
      - metrics
      - deployment
    limitations:
      - "The `postTaskExecution` completion hook is spec task 2.3 and does not exist, so a status change is still made by editing this file."
      - "The four gates run locally but are not wired into `.github/workflows/ci.yml`; those jobs are spec task 2.4, so nothing yet fails a pull request on a stale document or failing evidence."
      - "`verify.py` executes commands from this file. The trust boundary is that the manifest is a tracked, reviewed file; the script never uses a shell, but it is not a sandbox and must not be pointed at unreviewed input."
      - "Uniqueness of component ids and coverage of all 30 section-6 modules are not expressible in JSON Schema; `scripts/status/validate.py` and tests/unit/test_status_manifest.py assert them instead."
      - "Nothing is recorded `implemented`, so `verify.py` currently executes zero commands. Its failure path is covered only by synthetic manifests in tests, not by a real component."
      - "The renderer has no structured logging and reads no configuration: the document layout is fixed in code."
    notes: >-
      `api_contract` is true because the committed JSON Schema is this component's
      contract. `ci_validated` is false because the four gates are not yet CI jobs,
      which is why the status is `in_progress` rather than `implemented` even though
      the scripts work.

  - id: shared-contracts
    name: Shared types and API contracts
    category: foundation
    group: foundation
    status: not_started
    phase: 3
    implementation: packages/api_contracts
    tests: packages/api_contracts/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    placeholders:
      - path: docs/api/openapi.yaml
        kind: api_contract
        reason: "`paths` is an empty object. The document parses and declares its version, tags and security schemes, but describes no operation, so nothing can be generated or validated from it."
      - path: packages/api_contracts
        kind: directory
        reason: "Holds a README only. No schema, no generated type and no codegen entry point."
    notes: >-
      Covers Implementation_Sequence steps 03 and 11: the versioned contract
      schemas, the derived language types, the canonical request model and
      docs/api/openapi.yaml.

  - id: database-foundation
    name: Database foundation
    category: foundation
    group: foundation
    status: not_started
    phase: 4
    implementation: database
    tests: tests/integration
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    placeholders:
      - path: database/migrations
        kind: directory
        reason: "Empty. None of the 25 core tables of Master_Specification section 61 exists, so no migration runner, no seed and no row-level security policy can run."
    notes: >-
      Decision D6 applies: every migration ships a tested down-migration and
      production applies migrations forward only.

  - id: event-system
    name: Event system
    category: foundation
    group: platform
    status: not_started
    phase: 21
    implementation: packages/events
    tests: packages/events/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Transactional outbox, dispatcher and idempotent consumer base. Analytics,
      Billing, Notifications and Audit all depend on it.

  - id: verification-suites
    name: Verification suites
    category: foundation
    group: foundation
    status: not_started
    phase: 42
    implementation: tests
    tests: tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations:
      - "Only tests/unit holds tests. The api, mcp, integration, e2e, security, load and chaos suites are empty directories."
    notes: >-
      Covers Implementation_Sequence steps 40 to 42: security testing, load
      testing and end-to-end testing.

  - id: documentation
    name: Documentation set
    category: foundation
    group: foundation
    status: not_started
    phase: 43
    implementation: docs
    tests: tests/unit
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations:
      - "Every page under docs/ states its purpose and scope; none carries the content it promises."
      - "No executable example is embedded anywhere, so Requirement 43.3 has nothing to run."
    placeholders:
      - path: apps/docs
        kind: directory
        reason: "Documentation site scaffold. Holds a README and empty content and public directories; no generator, no build."

  # -------------------------------------------------------------------------
  # Master_Specification section 6 product modules
  # -------------------------------------------------------------------------

  - id: gateway
    name: Gateway
    category: product_module
    module: 01 Gateway
    group: services
    status: not_started
    phase: 12
    implementation: services/gateway
    tests: services/gateway/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Serves the eleven paths of Master_Specification section 45 under /v1,
      including streaming pass-through and the rate-limit scopes of section 27.

  - id: authentication
    name: Authentication
    category: product_module
    module: 02 Authentication
    group: platform
    status: not_started
    phase: 5
    implementation: packages/auth
    tests: packages/auth/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []

  - id: tenant-management
    name: Tenant management
    category: product_module
    module: 03 Tenant Management
    group: platform
    status: not_started
    phase: 6
    implementation: packages/tenant
    tests: packages/tenant/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Owns TenantContext and the tenant-scoped session. Tenant isolation must
      exist before any tenant-owned row is written.

  - id: user-management
    name: User management
    category: product_module
    module: 04 User Management
    group: platform
    status: not_started
    phase: 7
    implementation: packages/authorization
    tests: packages/authorization/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Users, their roles and the granular permissions of Master_Specification
      section 32. The administrative surface is served by the gateway; the
      repository has no dedicated control-api service yet, and
      deployments/helm/agentrouter/templates/control-api.yaml is a placeholder for
      one.

  - id: team-management
    name: Team management
    category: product_module
    module: 05 Team Management
    group: platform
    status: not_started
    phase: 7
    implementation: packages/tenant
    tests: packages/tenant/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Teams share the organization model in packages/tenant with tenants, and are
      a policy scope in the six-level Policy_Hierarchy.

  - id: provider-management
    name: Provider management
    category: product_module
    module: 06 Provider Management
    group: services
    status: not_started
    phase: 9
    implementation: services/providers
    tests: services/providers/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      The Provider_Gateway and its adapters. This is the only component permitted
      to call a provider API, which the boundary scanner of spec task 3.2
      enforces.

  - id: model-registry
    name: Model registry
    category: product_module
    module: 07 Model Registry
    group: services
    status: not_started
    phase: 8
    implementation: services/registry
    tests: services/registry/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      The only place a model price or context-window figure may be stated. The
      literal scanner of spec task 3.1 fails the build on such a literal
      elsewhere.

  - id: request-analyzer
    name: Request analyzer
    category: product_module
    module: 08 Request Analyzer
    group: services
    status: not_started
    phase: 13
    implementation: services/analyzer
    tests: services/analyzer/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Model-agnostic by construction: analyze() receives no registry and no
      AnalysisResult field may name a model or a provider.

  - id: routing-engine
    name: Routing engine
    category: product_module
    module: 09 Routing Engine
    group: services
    status: not_started
    phase: 14
    implementation: services/router
    tests: services/router/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      The core IP: candidate filtering, the six-term score, the six Routing_Mode
      weight presets and the explainable RoutingDecision. Determinism claims are
      scoped to a fixed Routing_Input per decision D5.

  - id: cost-engine
    name: Cost engine
    category: product_module
    module: 10 Cost Engine
    group: services
    status: not_started
    phase: 15
    implementation: services/cost_engine
    tests: services/cost_engine/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Cost is per request, summed across every attempt including fallbacks and
      escalations, and savings are signed and never floored at zero (decision D4).

  - id: policy-engine
    name: Policy engine
    category: product_module
    module: 11 Policy Engine
    group: services
    status: not_started
    phase: 16
    implementation: services/policy
    tests: services/policy/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Resolution is monotonic narrowing across the six scopes of the
      Policy_Hierarchy: a narrower scope may restrict further and may never widen
      (decision D3).

  - id: escalation-engine
    name: Escalation engine
    category: product_module
    module: 12 Escalation Engine
    group: services
    status: not_started
    phase: 17
    implementation: services/router/internal/escalation
    tests: services/router/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Re-routes to a higher-capability candidate from the same candidate set, so
      an escalated model still satisfies the original policy decision.

  - id: fallback-engine
    name: Fallback engine
    category: product_module
    module: 13 Fallback Engine
    group: services
    status: not_started
    phase: 18
    implementation: services/router/internal/fallback
    tests: services/router/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Selects alternatives from the existing candidate set only, so fallback can
      never reach a prohibited provider. Owns the Circuit_Breaker states.

  - id: security-engine
    name: Security engine
    category: product_module
    module: 14 Security Engine
    group: platform
    status: not_started
    phase: 19
    implementation: packages/security
    tests: packages/security/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Redaction, retention and transport security. Redaction is applied inside the
      logging emit path so a Sensitive_Value cannot leave the process through a
      log line.

  - id: mcp-server
    name: MCP server
    category: product_module
    module: 15 MCP Server
    group: integrations
    status: not_started
    phase: 23
    implementation: integrations/mcp
    tests: integrations/mcp/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    placeholders:
      - path: integrations/mcp/package.json
        kind: other
        reason: 'The `build` and `test` scripts echo "not implemented" and exit 1. The package declares no dependency and no entry point.'
    notes: >-
      The six tools of Master_Specification section 37, each delegating to the
      core. No scoring or filtering logic may live here.

  - id: ide-integrations
    name: IDE integrations
    category: product_module
    module: 16 IDE Integrations
    group: integrations
    status: not_started
    phase: 27
    implementation: integrations
    tests: integrations/*/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations:
      - "No integration capability is claimed as supported for any host. Requirement 2.5 requires each documented capability to name the passing automated test that exercises it against the host's officially supported mechanism, and no such test exists."
    placeholders:
      - path: integrations/vscode/package.json
        kind: other
        reason: "Extension manifest scaffold. The `build` and `test` scripts exit 1; no activation event, contribution or command is declared."
    notes: >-
      Covers the VS Code, Kiro, Cursor, Claude Code and JetBrains adapters and the
      Capability_Profile of Master_Specification section 39.

  - id: client
    name: Client
    category: product_module
    module: 17 Client
    group: clients
    status: not_started
    phase: 24
    implementation: clients/local-agent
    tests: clients/local-agent/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      The developer-machine Local_Client of Master_Specification section 44:
      login, configuration, MCP hosting and diagnostics, with credentials in the
      OS secure store. clients/desktop is a later shell over the same client.

  - id: api
    name: API
    category: product_module
    module: 18 API
    group: clients
    status: not_started
    phase: 12
    implementation: apps/api
    tests: tests/api
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    placeholders:
      - path: apps/api/package.json
        kind: other
        reason: 'The `build` and `test` scripts echo "not implemented" and exit 1.'
    notes: >-
      The public API product: the surface served by the gateway, its generated
      reference documentation and its conformance suite. The contract itself
      belongs to the shared-contracts entry.

  - id: cli
    name: CLI
    category: product_module
    module: 19 CLI
    group: clients
    status: not_started
    phase: 25
    implementation: cli
    tests: cli/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Every command of Master_Specification section 48 with machine-readable
      output and documented exit statuses. The command tree exists as empty
      directories only.

  - id: sdk
    name: SDK
    category: product_module
    module: 20 SDK
    group: clients
    status: not_started
    phase: 26
    implementation: sdk
    tests: sdk/*/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations:
      - "Decision D2 excludes Go from phase 1, so sdk/go stays a scaffold while the TypeScript and Python SDKs are built."
    placeholders:
      - path: sdk/typescript/package.json
        kind: other
        reason: 'The `build` and `test` scripts echo "not implemented" and exit 1.'
      - path: sdk/go/go.mod
        kind: other
        reason: "Declares a module path and a Go version over a directory with no Go source, so `go build ./...` compiles nothing."
    notes: >-
      One shared conformance suite is parameterized over all three SDKs so they
      cannot diverge.

  - id: dashboard
    name: Dashboard
    category: product_module
    module: 21 Dashboard
    group: clients
    status: not_started
    phase: 28
    implementation: apps/dashboard
    tests: apps/dashboard/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    placeholders:
      - path: apps/dashboard/package.json
        kind: other
        reason: 'The `build` and `test` scripts echo "not implemented" and exit 1. No framework, dependency or source file is present.'

  - id: analytics
    name: Analytics
    category: product_module
    module: 22 Analytics
    group: services
    status: not_started
    phase: 22
    implementation: services/analytics
    tests: services/analytics/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Aggregation by every dimension of Master_Specification section 54, the
      FinOps figures of section 55 and the routing metrics of section 78, always
      scoped to the requesting principal's tenant.

  - id: benchmarking
    name: Benchmarking
    category: product_module
    module: 23 Benchmarking
    group: platform
    status: not_started
    phase: 32
    implementation: benchmark
    tests: benchmark/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations:
      - "No dataset exists in any of the eight domain directories, so every routing weight in config/ is an unmeasured starting value rather than a benchmarked one."
    notes: >-
      Requirements 2.3 and 2.4: a published quality or latency figure must carry
      its dataset id, model id, run timestamp and sample count, and a figure
      without a recorded run is excluded from reports.

  - id: evaluation
    name: Evaluation
    category: product_module
    module: 24 Evaluation
    group: platform
    status: not_started
    phase: 33
    implementation: evaluation
    tests: evaluation/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations:
      - "The labeled Routing_Dataset of Master_Specification section 76 does not exist, so routing quality is currently unmeasurable."

  - id: audit
    name: Audit
    category: product_module
    module: 25 Audit
    group: services
    status: not_started
    phase: 21
    implementation: services/audit
    tests: services/audit/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Append-only storage with UPDATE and DELETE revoked from the application
      role. Identity and policy events start being recorded at sequence steps 05
      to 07, before this service exists.

  - id: billing
    name: Billing
    category: product_module
    module: 26 Billing
    group: services
    status: not_started
    phase: 30
    implementation: services/billing
    tests: services/billing/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Money is held in integer minor units. Billing state is outside the routing
      core's import boundary.

  - id: notifications
    name: Notifications
    category: product_module
    module: 27 Notifications
    group: services
    status: not_started
    phase: 31
    implementation: services/notifications
    tests: services/notifications/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    notes: >-
      Email, webhook, Slack and Teams delivery for every event of
      Master_Specification section 57, excluding sensitive values and message
      content.

  - id: observability
    name: Observability
    category: product_module
    module: 28 Observability
    group: platform
    status: not_started
    phase: 20
    implementation: packages/telemetry
    tests: packages/telemetry/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations:
      - "observability/ documents the metric catalog of Master_Specification section 59 in prose only. No collector configuration, dashboard, alert rule or runbook exists."
    notes: >-
      Structured logging, OpenTelemetry tracing, the metric registry and the alert
      rules under observability/alerts/.

  - id: deployment
    name: Deployment
    category: product_module
    module: 29 Deployment
    group: platform
    status: not_started
    phase: 34
    implementation: deployments
    tests: tests/e2e
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations:
      - "Nothing in the repository is deployable. The only working deployment artifact is the local Compose stack, and it starts PostgreSQL and Redis only."
      - "The Helm chart passes `helm lint` and installs cleanly while deploying no workload at all, which makes a successful install a misleading signal until the templates are written."
    placeholders:
      - path: services/*/Dockerfile
        kind: dockerfile
        reason: "Each is `FROM scratch` plus labels, with the intended build stages in comments. Deliberately not buildable: the services have no source. Named per service in .github/workflows/build-images.yml, which is itself disabled."
      - path: cli/Dockerfile
        kind: dockerfile
        reason: "Same shape as the service Dockerfiles: `FROM scratch` plus labels, no build stage, no source to build."
      - path: deployments/helm/agentrouter/templates/*.yaml
        kind: helm_template
        reason: "Every one of the twelve templates contains a Go template comment and nothing else, so `helm template` renders zero Kubernetes resources."
      - path: deployments/kubernetes/base
        kind: kubernetes_manifest
        reason: "Empty, as are the development, staging and production overlays. There is no kustomization and no manifest."
      - path: infrastructure/terraform/modules
        kind: terraform_module
        reason: "Seven module directories and three environment directories hold a README and a .gitkeep each. No .tf file exists, so `terraform init` has nothing to initialize."
      - path: .github/workflows/build-images.yml
        kind: ci_workflow
        reason: "Prints that service Dockerfiles are scaffolds and exits 0. It builds no image, so a green run means nothing was built."
      - path: .github/workflows/deploy-staging.yml
        kind: ci_workflow
        reason: "Manual dispatch only; prints that deployment is not wired up and exits 0."
      - path: .github/workflows/deploy-production.yml
        kind: ci_workflow
        reason: "Manual dispatch only; prints that deployment is not wired up and exits 0."
    notes: >-
      Covers Implementation_Sequence steps 34 to 37 (Kubernetes, Helm, Terraform,
      CI/CD) and the HA and DR posture of steps 38 and 39.

  - id: administration
    name: Administration
    category: product_module
    module: 30 Administration
    group: clients
    status: not_started
    phase: 29
    implementation: apps/admin-console
    tests: apps/admin-console/tests
    evidence: []
    component_dod:
      implementation: false
      unit_tests: false
      integration_tests: false
      error_handling: false
      security_reviewed: false
      logging: false
      metrics: false
      documentation: false
      api_contract: false
      configuration: false
      deployment: false
      ci_validated: false
    limitations: []
    placeholders:
      - path: apps/admin-console/package.json
        kind: other
        reason: 'The `build` and `test` scripts echo "not implemented" and exit 1.'
    notes: >-
      The Admin_Console of Master_Specification section 105. Authorization is
      evaluated server side; the console is never trusted for it.
"""


def section_docs() -> None:
    for area, entries in DOCS.items():
        mkdir(f"docs/{area}")
        for filename, title, purpose in entries:
            doc(f"docs/{area}/{filename}", title, purpose)

    keep("docs/api/examples")
    write(
        "docs/api/openapi.yaml",
        """# AgentRouter public API contract.
#
# Scaffold: paths are declared as the API surface from the master specification
# (section 45) but no operations are defined yet. API reference documentation is
# generated from this file, so it stays the single source of truth.

openapi: 3.1.0

info:
  title: AgentRouter API
  version: 0.0.0
  description: >-
    Enterprise AI model routing, optimization and governance platform.
    This contract is a scaffold and does not yet describe a running service.
  license:
    name: SEE LICENSE IN LICENSE

servers:
  - url: https://api.example.invalid/v1
    description: Placeholder. Configure per environment.

security:
  - bearerAuth: []

tags:
  - name: auth
  - name: models
  - name: providers
  - name: routing
  - name: usage
  - name: policies
  - name: organizations
  - name: teams
  - name: users
  - name: audit

paths: {}
# Planned surface:
#   /auth
#   /models
#   /providers
#   /route
#   /generate
#   /usage
#   /policies
#   /organizations
#   /teams
#   /users
#   /audit

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
  schemas: {}
""",
    )
    readme(
        "docs/api/README.md",
        "API Documentation",
        """`openapi.yaml` is the contract. Reference documentation, SDK types and API
tests are generated from or validated against it.

"""
        + tree(["openapi.yaml  API contract", "examples/     request and response examples"])
        + """

## Status

Scaffold. Surface declared, operations not defined.""",
    )

    write("docs/status-manifest.schema.json", STATUS_SCHEMA)
    write("docs/implementation-status.yaml", STATUS_MANIFEST)
    render_status_document()

    readme(
        "docs/README.md",
        "Documentation",
        """"""
        + tree(
            [
                "architecture/  system and component architecture",
                "api/           OpenAPI contract and examples",
                "integrations/  per-host integration guides",
                "deployment/    cloud, Kubernetes, Helm, self-hosted, private",
                "security/      security, privacy, auth and threat model",
                "operations/    monitoring, incident response, DR, troubleshooting",
                "customer/      onboarding and role-based guides",
                "product/       vision, roadmap, requirements",
                "implementation-status.yaml    the status manifest: authoritative",
                "status-manifest.schema.json   schema the manifest is validated against",
                "IMPLEMENTATION_STATUS.md      what actually works today (generated)",
            ]
        )
        + """

Planning documents at the repository root remain the source of truth for the
target architecture: `README.md` (master specification), `Architecture.md`,
`Repository Structure.md`, `technology.md`, `product.md`, `prompt complexity.md`
and `MVP.md`.

Start with `IMPLEMENTATION_STATUS.md` to see where the build actually stands.
Change status by editing `implementation-status.yaml`, never the generated
document.""",
    )


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------


def section_config() -> None:
    for env_name, note in [
        ("development", "Local and shared development configuration."),
        ("staging", "Staging configuration. Separate credentials from every other environment."),
        ("production", "Production configuration. Secrets come from a secret manager only."),
    ]:
        mkdir(f"config/{env_name}")
        write(
            f"config/{env_name}/routing.yaml",
            f"""# Routing configuration for the {env_name} environment.
#
# Weights are configuration, not universal truths. Benchmark before changing
# them and record the result in evaluation/.

routing:
  mode: balanced   # balanced | quality_first | cost_first | latency_first | reliability_first | policy_first

weights:
  quality: 0.40
  cost: 0.25
  latency: 0.15
  reliability: 0.20

escalation:
  enabled: true

fallback:
  enabled: true
""",
        )
        readme(
            f"config/{env_name}/README.md",
            f"config/{env_name}",
            f"""{note}

Non-secret configuration only. API keys, passwords, production URLs and tenant
IDs are supplied through environment variables or a secret manager.

"""
            + tree(["routing.yaml  routing mode, weights, escalation and fallback"]),
        )

    readme(
        "config/README.md",
        "Configuration",
        """Environment-driven configuration.

"""
        + tree(["development/", "staging/", "production/"])
        + """

Rules:

- Never embed API keys, passwords, production URLs or tenant IDs.
- Every environment uses separate credentials.
- Secrets resolve from environment variables or an external secret manager.""",
    )


# ---------------------------------------------------------------------------
# root files
# ---------------------------------------------------------------------------


def section_root() -> None:
    write(
        ".env.example",
        """# AgentRouter environment template.
#
# Copy to .env and fill in local values:
#     cp .env.example .env
#
# .env is git-ignored. Never commit real credentials, and never put provider
# API keys in a committed file, container image or Helm values file.

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
AGENTROUTER_ENV=development
AGENTROUTER_LOG_LEVEL=info
# saas | dedicated | self-hosted
AGENTROUTER_DEPLOYMENT_MODE=self-hosted

# ---------------------------------------------------------------------------
# PostgreSQL (authoritative store)
# ---------------------------------------------------------------------------
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=agentrouter
POSTGRES_PASSWORD=change-me-locally
POSTGRES_DB=agentrouter
POSTGRES_SSL_MODE=disable

# ---------------------------------------------------------------------------
# Redis (cache, rate limits, provider health)
# ---------------------------------------------------------------------------
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
OIDC_ISSUER_URL=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
SESSION_SIGNING_KEY=

# ---------------------------------------------------------------------------
# Secret manager
# Provider credentials resolve through this, not through this file.
# vault | aws-secrets-manager | azure-key-vault | gcp-secret-manager | env
# ---------------------------------------------------------------------------
SECRETS_BACKEND=env

# ---------------------------------------------------------------------------
# Model providers
# Local development only. Leave blank in every shared environment.
# ---------------------------------------------------------------------------
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_SERVICE_NAME=agentrouter

# ---------------------------------------------------------------------------
# Routing defaults (overridden by config/<env>/routing.yaml)
# ---------------------------------------------------------------------------
ROUTING_MODE=balanced
ROUTING_ESCALATION_ENABLED=true
ROUTING_FALLBACK_ENABLED=true

# ---------------------------------------------------------------------------
# Privacy
# Raw prompts are not persisted unless an organization explicitly opts in.
# ---------------------------------------------------------------------------
PERSIST_PROMPTS=false
""",
    )

    write(
        ".gitignore",
        """# Secrets and local environment
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.pfx
secrets/
credentials.json

# Node
node_modules/
dist/
build/
.next/
out/
*.tsbuildinfo
npm-debug.log*
yarn-error.log*
pnpm-debug.log*

# Python
__pycache__/
*.py[cod]
.venv/
venv/
.mypy_cache/
.pytest_cache/
.ruff_cache/
*.egg-info/

# Go
bin/
vendor/
*.test
*.out

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
!*.tfvars.example
.terraform.lock.hcl

# Helm
charts/*.tgz

# Tooling and IDE
.idea/
.vscode/*
!.vscode/extensions.json
*.swp
.DS_Store
Thumbs.db

# Test and build output
coverage/
.coverage
htmlcov/
benchmark/reports/*
!benchmark/reports/.gitkeep
""",
    )

    write(
        ".dockerignore",
        """.git
.github
.gitignore
.env
.env.*
!.env.example

node_modules
dist
build
.next
out

__pycache__
*.py[cod]
.venv
venv
.mypy_cache
.pytest_cache
.ruff_cache

bin
vendor

.terraform
*.tfstate
*.tfstate.*

coverage
.coverage
htmlcov

docs
tests
benchmark/reports
*.md
!README.md
""",
    )

    write(
        "Makefile",
        """# AgentRouter developer entry points.
#
# Targets that depend on unimplemented services fail loudly rather than
# pretending to succeed.

SHELL := /bin/sh
COMPOSE := docker compose -f deployments/docker/docker-compose.yml
COMPOSE_DEV := $(COMPOSE) -f deployments/docker/docker-compose.dev.yml
COMPOSE_TEST := docker compose -f deployments/docker/docker-compose.test.yml

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available targets
\t@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \\
\t\tawk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

.PHONY: scaffold
scaffold: ## Recreate any missing part of the repository structure
\tpython scripts/bootstrap/scaffold_repository.py

.PHONY: verify-structure
verify-structure: ## Fail if the structure drifts from the scaffold definition
\tpython scripts/bootstrap/scaffold_repository.py
\tgit diff --exit-code
\tpython scripts/testing/validate_structure.py

.PHONY: check
check: ## THE quality gate: format, lint, type check, unit tests
\tpython scripts/development/check.py

.PHONY: format
format: ## Rewrite formatting in place (check only reports)
\tpython -m ruff format .
\tpython -m ruff check --fix .

.PHONY: health
health: ## Report whether PostgreSQL and Redis are reachable
\tpython scripts/development/health.py

.PHONY: up
up: ## Start local backing services (PostgreSQL, Redis)
\t$(COMPOSE_DEV) up -d

.PHONY: down
down: ## Stop local backing services
\t$(COMPOSE_DEV) down

.PHONY: logs
logs: ## Tail local backing service logs
\t$(COMPOSE_DEV) logs -f

.PHONY: test-env-up
test-env-up: ## Start the ephemeral integration test stack
\t$(COMPOSE_TEST) up -d --wait

.PHONY: test-env-down
test-env-down: ## Tear down the integration test stack
\t$(COMPOSE_TEST) down -v

.PHONY: helm-lint
helm-lint: ## Lint the Helm chart
\thelm lint deployments/helm/agentrouter

.PHONY: status
status: ## Show implementation status
\t@echo "See docs/IMPLEMENTATION_STATUS.md"

# `lint` and `test` are single steps of `check`, kept for muscle memory and for
# narrowing a failure. `check` is the documented command (requirement 3.6): CI
# and the contributing guide name it and nothing else.
.PHONY: lint
lint: ## One step of check: ruff format --check and ruff check
\tpython -m ruff format --check .
\tpython -m ruff check .

.PHONY: test
test: ## One step of check: pytest with coverage
\tpython -m pytest

.PHONY: build
build: ## Build all services (not implemented)
\t@echo "No buildable source yet. Wire this up in the phase that adds code."; exit 1

.PHONY: migrate
migrate: ## Apply database migrations (not implemented)
\t@echo "No migrations yet. See database/README.md."; exit 1
""",
    )

    write(
        "Taskfile.yml",
        """# Task runner alternative to the Makefile (https://taskfile.dev).
# Kept in sync with Makefile targets.

version: "3"

vars:
  COMPOSE: docker compose -f deployments/docker/docker-compose.yml -f deployments/docker/docker-compose.dev.yml
  COMPOSE_TEST: docker compose -f deployments/docker/docker-compose.test.yml

tasks:
  default:
    desc: List available tasks
    cmds:
      - task --list
    silent: true

  scaffold:
    desc: Recreate any missing part of the repository structure
    cmds:
      - python scripts/bootstrap/scaffold_repository.py

  verify-structure:
    desc: Fail if the structure drifts from the scaffold definition
    cmds:
      - python scripts/bootstrap/scaffold_repository.py
      - git diff --exit-code
      - python scripts/testing/validate_structure.py

  check:
    desc: "THE quality gate: format, lint, type check, unit tests"
    cmds:
      - python scripts/development/check.py

  format:
    desc: Rewrite formatting in place (check only reports)
    cmds:
      - python -m ruff format .
      - python -m ruff check --fix .

  health:
    desc: Report whether PostgreSQL and Redis are reachable
    cmds:
      - python scripts/development/health.py

  up:
    desc: Start local backing services
    cmds:
      - "{{.COMPOSE}} up -d"

  down:
    desc: Stop local backing services
    cmds:
      - "{{.COMPOSE}} down"

  logs:
    desc: Tail local backing service logs
    cmds:
      - "{{.COMPOSE}} logs -f"

  test-env-up:
    desc: Start the ephemeral integration test stack
    cmds:
      - "{{.COMPOSE_TEST}} up -d --wait"

  test-env-down:
    desc: Tear down the integration test stack
    cmds:
      - "{{.COMPOSE_TEST}} down -v"

  helm-lint:
    desc: Lint the Helm chart
    cmds:
      - helm lint deployments/helm/agentrouter

  status:
    desc: Show implementation status
    cmds:
      - echo "See docs/IMPLEMENTATION_STATUS.md"

  # lint and test are single steps of check, kept for narrowing a failure.
  # check is the documented command (requirement 3.6).
  lint:
    desc: "One step of check: ruff format --check and ruff check"
    cmds:
      - python -m ruff format --check .
      - python -m ruff check .

  test:
    desc: "One step of check: pytest with coverage"
    cmds:
      - python -m pytest

  build:
    desc: Build all services (not implemented)
    cmds:
      - cmd: echo "No buildable source yet."
      - cmd: exit 1
""",
    )

    write(
        "VERSION",
        "0.0.0\n",
    )

    write(
        "SECURITY.md",
        """# Security Policy

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
""",
    )

    write(
        "CONTRIBUTING.md",
        """# Contributing

## Source of truth

Target architecture and requirements live in the root planning documents:

"""
        + tree(
            [
                "README.md                 master engineering specification",
                "Architecture.md           production architecture",
                "Repository Structure.md   target repository structure",
                "technology.md             technology per layer",
                "product.md                capability checklist",
                "prompt complexity.md      analyzer design guidance",
                "MVP.md                    local-first starting point",
            ]
        )
        + """

Current reality lives in `docs/IMPLEMENTATION_STATUS.md`. Read it before
starting work.

## Implementation order

Follow the dependency order in the master specification, section 132. Do not
jump between unrelated phases. Each phase passes its acceptance criteria before
the next begins.

## Per-phase process

"""
        + tree(
            [
                "UNDERSTAND  inspect the repository and existing implementation",
                "DESIGN      smallest correct architecture consistent with the spec",
                "IMPLEMENT   production-quality code",
                "TEST        unit, integration and relevant end-to-end tests",
                "SECURITY    auth, authorization, secrets, tenant isolation, data handling",
                "OBSERVE     logs, metrics, traces",
                "DOCUMENT    update the relevant documentation",
                "VALIDATE    tests, linting, builds, deployment validation",
                "REPORT      what was implemented, what was tested, known limitations",
            ]
        )
        + """

## Engineering rules

1. No provider-specific behaviour inside the routing engine.
2. No hardcoded model pricing. Pricing comes from the registry.
3. The core engine is not coupled to any IDE.
4. The product is not coupled to MCP. MCP is one integration.
5. No secrets in source control.
6. Raw prompts are not logged by default.
7. Authorization is never bypassed.
8. No undocumented IDE APIs when an official mechanism exists.
9. Every service has tests.
10. Every production API is documented.
11. No placeholder marked as complete.
12. No fabricated routing quality, cost savings or benchmark numbers.
13. Security and tenant isolation are never weakened for convenience.
14. New models, providers and integrations must not require core engine changes.

## Definition of done

A component is complete only when all of the following hold:

"""
        + tree(
            [
                "implementation exists",
                "unit tests exist",
                "integration tests exist where applicable",
                "errors handled",
                "security considered",
                "structured logging implemented",
                "metrics implemented where applicable",
                "documentation exists",
                "API contract exists",
                "configuration exists",
                "deployment exists where applicable",
                "CI validates it",
            ]
        )
        + """

## Development environment

Python 3.13 and Node 20. Install the pinned tooling once:

```bash
python -m pip install -r requirements-dev.txt
```

Start the backing services and confirm they answer:

```bash
cp .env.example .env    # fill in POSTGRES_PASSWORD; compose requires it
make up                 # PostgreSQL and Redis
make health             # reports both as reachable, or how to fix them
```

## The quality gate

One command runs formatting, linting, type checking and unit tests:

```bash
make check              # or: python scripts/development/check.py
```

It runs all four steps even when one fails, then names every failing step and
the command that fixes it. `make format` rewrites formatting in place. `make
lint` and `make test` run single steps when you are narrowing a failure. CI runs
`make check`, so a green local run means a green gate.

Where `make` is unavailable, such as a stock Windows shell, run the script
directly or use [Task](https://taskfile.dev): `task check`, `task health`.

## Repository structure

The structure is generated and verified:

```bash
python scripts/bootstrap/scaffold_repository.py   # recreate anything missing
make verify-structure                             # fail on drift
```

The script never overwrites an existing file. When you add a directory or a
script to the target structure, add it to the generator and to
`scripts/testing/validate_structure.py` too, so the structure stays
reproducible.

## Commits and branches

Work on a branch and open a pull request. The pull request template carries the
definition-of-done checklist. Never commit a `.env` file or any credential.
""",
    )

    write(
        "CODE_OF_CONDUCT.md",
        """# Code of Conduct

## Our standard

This project is a professional engineering environment. Participants are
expected to be respectful, constructive and direct. Technical disagreement is
welcome; personal attacks, harassment and discriminatory behaviour are not.

Expected behaviour:

- Give and accept technical feedback on the substance of the work.
- Assume competence and good intent.
- Respect the security and privacy commitments of the project.

Unacceptable behaviour:

- Harassment, intimidation or discrimination of any kind.
- Publishing others' private information.
- Deliberately introducing insecure or malicious code.

## Reporting

Report concerns to the maintainers. Replace this placeholder with a monitored
contact before accepting outside contributions:

```text
conduct@example.invalid
```

Reports are handled confidentially. Maintainers may warn, restrict or remove
participants who violate this standard.

## Attribution

This document is adapted in spirit from widely used open source codes of
conduct, notably the [Contributor Covenant](https://www.contributor-covenant.org/).
""",
    )

    write(
        "CHANGELOG.md",
        """# Changelog

Notable changes to AgentRouter. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Target repository structure from `Repository Structure.md`, generated by
  `scripts/bootstrap/scaffold_repository.py`.
- Engineering standards, contribution process and definition of done
  (`CONTRIBUTING.md`, pull request template).
- Security policy, code of conduct and license.
- CI scaffold verifying structure idempotency and secret hygiene.
- Local backing services via Docker Compose (PostgreSQL, Redis) plus an
  ephemeral integration test stack.
- Helm chart metadata and value contract for the consolidated production
  workload topology.
- OpenAPI contract scaffold declaring the public API surface.
- Documentation skeleton and `docs/IMPLEMENTATION_STATUS.md`.

### Notes

No runnable application code exists yet. See `docs/IMPLEMENTATION_STATUS.md`
for exactly what does and does not work.
""",
    )

    write(
        "LICENSE",
        """Copyright (c) 2026 AgentRouter

All rights reserved.

This software and its source code are proprietary and confidential. No license,
express or implied, is granted to any person to use, copy, modify, merge,
publish, distribute, sublicense or sell copies of this software, in whole or in
part, without prior written permission from the copyright holder.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT
HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

NOTE: Replace this notice if a different distribution model is chosen. If the
project is ever published under an open source license, update this file, the
`license` fields in every package manifest, and SECURITY.md accordingly.
""",
    )


# ---------------------------------------------------------------------------
# python workspace
# ---------------------------------------------------------------------------
#
# The root pyproject.toml is the single place that declares the workspace
# members, the exact pinned tool versions, and the ruff, mypy and pytest
# configuration. requirements-dev.txt carries the same pins for pip versions
# without PEP 735 dependency-group support.
#
# Member directory names are snake_case throughout: each is imported as a
# Python module and a module name cannot contain a hyphen.

PYPROJECT_TOML = """# AgentRouter Python workspace.
#
# Decision D2 of the design makes Python the implementation language for the
# analyzer, router, policy engine, cost engine, registry, provider adapters,
# gateway and MCP server. This file is the single place that declares:
#
#   1. the workspace members (packages/* and services/*)
#   2. the exact, pinned tool and test dependencies
#   3. the ruff, mypy and pytest/coverage configuration
#
# Every dependency is pinned with `==`. Ranges are not permitted: a range makes
# a build non-reproducible and lets an upstream release change behaviour without
# a reviewed commit.
#
# Import convention
# -----------------
# The repository root is the only import root (`pythonpath = ["."]`). Workspace
# members are therefore imported by their path, for example
# `packages.shared_types` and `services.router`. Putting `packages/` itself on
# sys.path was rejected because `packages/logging/` would then shadow the
# standard library `logging` module.
#
# Member directories use snake_case because a hyphen cannot appear in a Python
# module name.

# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------
# Declared here rather than inferred from a glob so that a new directory under
# packages/ or services/ is a reviewed change. The boundary scanner (task 3.2)
# and the quality command (task 1.2) read this list.

[tool.agentrouter.workspace]
root-import-path = "."
packages = [
    "packages/shared_types",
    "packages/api_contracts",
    "packages/configuration",
    "packages/redaction",
    "packages/logging",
    "packages/telemetry",
    "packages/errors",
    "packages/tenant",
    "packages/auth",
    "packages/authorization",
    "packages/events",
    "packages/testing",
    "packages/security",
    "packages/validation",
]
services = [
    "services/registry",
    "services/analyzer",
    "services/policy",
    "services/router",
    "services/cost_engine",
    "services/providers",
    "services/gateway",
    "services/analytics",
    "services/billing",
    "services/notifications",
    "services/audit",
]

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
# PEP 735 dependency group. Install with:
#
#   python -m pip install --group dev
#
# `requirements-dev.txt` carries the same pins for pip versions without PEP 735
# support. The two are kept in step by tests/unit/test_dependency_manifests.py.
#
# There is no runtime dependency group yet. No service exists, so any runtime
# dependency added now would be a guess.

[dependency-groups]
dev = [
    "ruff==0.16.7",
    "mypy==2.3.1",
    "pytest==9.1.1",
    "pytest-cov==7.1.0",
    "coverage[toml]==7.16.1",
    "hypothesis==6.168.0",
    "pyyaml==6.0.3",
    "types-pyyaml==6.0.12.20260906",
    "jsonschema==4.25.1",
    "types-jsonschema==4.25.1.20250822",
]

# ---------------------------------------------------------------------------
# Formatting and linting (ruff)
# ---------------------------------------------------------------------------

[tool.ruff]
line-length = 100
target-version = "py311"
src = ["."]
# Only Python is in scope. Recent ruff versions also format fenced code blocks in
# Markdown, which would rewrite the spec and planning documents. Those are the
# source of truth for the build and must not be edited by a formatter.
include = ["*.py", "*.pyi"]
extend-exclude = [
    ".venv",
    "node_modules",
    "sdk/go",
    "sdk/typescript",
]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # import sorting
    "N",    # pep8 naming
    "UP",   # pyupgrade
    "B",    # bugbear
    "C4",   # comprehensions
    "SIM",  # simplify
    "PTH",  # prefer pathlib
    "RUF",  # ruff-specific
    "S",    # flake8-bandit: security
]

[tool.ruff.lint.per-file-ignores]
# Assertions are the point of a test, and test fixtures may use predictable
# values that bandit reads as weak randomness or hardcoded credentials.
"tests/**" = ["S101", "S105", "S106", "S311"]
"packages/testing/**" = ["S101", "S105", "S106", "S311"]
# Repository tooling shells out to git and to the interpreter with fixed,
# non-user-supplied argument lists.
"scripts/**" = ["S404", "S603", "S607"]
# The scaffold generator holds long literal document text and long path tables.
# The formatter wraps what it can; the remainder is single string literals that
# cannot be split without changing generated output.
"scripts/bootstrap/scaffold_repository.py" = ["S404", "S603", "S607", "E501"]

[tool.ruff.format]
# Left off deliberately. Docstrings in this repository quote contract shapes and
# spec excerpts verbatim; reformatting them would silently edit quoted material.
docstring-code-format = false

# ---------------------------------------------------------------------------
# Static type checking, strict mode (mypy)
# ---------------------------------------------------------------------------
# The header above avoids the words that mypy parses as an inline config comment
# when this file's text is embedded in a Python source file by the scaffold
# generator.
# ---------------------------------------------------------------------------

[tool.mypy]
# The floor is 3.11 even though 3.13 is the development interpreter, so that
# type checking rejects syntax the floor cannot run.
python_version = "3.11"
strict = true
mypy_path = ["."]
namespace_packages = true
explicit_package_bases = true
warn_unreachable = true
warn_no_return = true
extra_checks = true
enable_error_code = [
    "redundant-expr",
    "possibly-undefined",
    "truthy-bool",
    "ignore-without-code",
]
# mypy fails when a listed directory holds no Python file. `packages/` and
# `services/` hold none yet; each is added to this list by the task that
# introduces its first module.
files = ["scripts", "tests"]

[[tool.mypy.overrides]]
module = ["tests.*"]
# Test bodies are checked as strictly as source, but pytest fixtures and
# parametrize decorators are untyped upstream in some plugins.
disallow_untyped_decorators = false

# ---------------------------------------------------------------------------
# pytest and coverage
# ---------------------------------------------------------------------------

[tool.pytest.ini_options]
minversion = "9.0"
pythonpath = ["."]
testpaths = ["tests", "packages", "services"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov",
    "--cov-report=term-missing",
]
filterwarnings = [
    "error",
    # `packages/` and `services/` hold no Python module yet, so coverage measures
    # nothing and pytest-cov warns that it cannot write a report. Remove this
    # entry with the task that adds the first module: after that, an empty
    # coverage report is a real problem worth failing on.
    "default::pytest_cov.plugin.CovReportWarning",
]
markers = [
    "unit: fast, isolated, no external process",
    "integration: needs PostgreSQL, Redis or another local dependency",
    "e2e: exercises the assembled system",
    "property: Hypothesis property test",
    "live: calls a real provider API; excluded from the default run",
]
xfail_strict = true

[tool.coverage.run]
branch = true
source = ["packages", "services"]
relative_files = true

[tool.coverage.report]
show_missing = true
skip_covered = true
exclude_also = [
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@overload",
]
# Raised as source lands. It cannot be enforced before there is source to
# measure, and a threshold over an empty tree would be a false signal.
fail_under = 0
"""

REQUIREMENTS_DEV = """# AgentRouter development and test tooling.
#
# Install:
#     python -m pip install -r requirements-dev.txt
#
# Equivalent on pip 25.1 or newer, which reads the PEP 735 group directly:
#     python -m pip install --group dev
#
# Every version is pinned exactly. A range would let an upstream release change
# lint, type-check or test behaviour without a reviewed commit, so `>=` and `~=`
# are not permitted in this file.
#
# This file and the `dev` group in pyproject.toml must agree. That is asserted by
# tests/unit/test_dependency_manifests.py, so edit both together.

# Formatting and linting
ruff==0.16.7

# Static type checking (strict mode; configured in pyproject.toml)
mypy==2.3.1

# Unit test runner and coverage
pytest==9.1.1
pytest-cov==7.1.0
coverage[toml]==7.16.1

# Property-based testing. The design's property tables are implemented as
# Hypothesis properties, so this is required tooling rather than optional.
hypothesis==6.168.0

# Used by scripts/testing/validate_structure.py to parse tracked YAML
pyyaml==6.0.3
types-pyyaml==6.0.12.20260906

# Validates docs/implementation-status.yaml against
# docs/status-manifest.schema.json (requirement 1.3). Draft 2020-12 support is
# required: the manifest schema uses if/then/else subschemas to make
# implementation, tests and evidence mandatory only for `implemented`
# components. The stub package is separate from the runtime package, so both are
# pinned, and their versions track each other.
jsonschema==4.25.1
types-jsonschema==4.25.1.20250822
"""


def section_python_workspace() -> None:
    write("pyproject.toml", PYPROJECT_TOML)
    write("requirements-dev.txt", REQUIREMENTS_DEV)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    section_github()
    section_apps()
    section_services()
    section_integrations()
    section_clients()
    section_cli()
    section_sdk()
    section_packages()
    section_database()
    section_benchmark()
    section_tests()
    section_deployments()
    section_infrastructure()
    section_observability()
    section_security()
    section_scripts()
    section_docs()
    section_config()
    section_python_workspace()
    section_root()

    print(f"AgentRouter scaffold complete at {ROOT}")
    print(f"  directories created: {len(created_dirs)}")
    print(f"  files created:       {len(created_files)}")
    print(f"  files skipped:       {len(skipped_files)} (already present)")

    if created_dirs:
        print("\nnew directories:")
        for rel in created_dirs:
            print(f"  + {rel}")
    if created_files:
        print("\nnew files:")
        for rel in created_files:
            print(f"  + {rel}")
    if skipped_files:
        print("\nleft untouched:")
        for rel in skipped_files:
            print(f"  = {rel}")


if __name__ == "__main__":
    main()
