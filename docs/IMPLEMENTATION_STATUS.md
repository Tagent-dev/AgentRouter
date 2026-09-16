# Implementation Status

<!-- Generated from docs/implementation-status.yaml by scripts/status/render.py. Do not edit: edit the manifest and re-run the generator. -->

Living record of what actually works, generated from `docs/implementation-status.yaml`. Change a status by editing the manifest and running `python scripts/status/render.py`; a hand edit here is reverted by the `status-render` CI gate.

**Legend:** `not started` | `in progress` | `implemented` | `blocked`

## Summary

| Status | Components |
| --- | --- |
| implemented | 0 |
| in progress | 3 |
| not started | 35 |

38 tracked components: 30 of the product modules of Master_Specification section 6, and 8 foundation entries that section 6 does not name.

A status is a claim about working software. `implemented` additionally requires all twelve Component_DoD items and at least one passing Verification_Evidence command, which `scripts/status/verify.py` and `scripts/status/check_dod.py` enforce in CI. The DoD column records partial credit so it never leaks into the status column.

## Foundation

| Component | Module | Status | Step | DoD | Implementation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Repository foundation | - | in progress | 1 | 7/12 (2 n/a) | `scripts/bootstrap/scaffold_repository.py` | Repository tooling is not deployed and emits no metrics, so those two Component_DoD items are recorded as not applicable rather than done. Structured logging and a declared contract for the generator's output are genuinely absent. |
| Completion ledger | - | in progress | 2 | 4/12 (2 n/a) | `docs/implementation-status.yaml` | `api_contract` is true because the committed JSON Schema is this component's contract. `implementation` is false because the scripts that read the manifest are not written yet, which is exactly why the status is not `implemented`. |
| Development environment and quality gate | - | in progress | 2 | 9/12 (2 n/a) | `scripts/development` | `health.py` is deliberately excluded from the evidence list: it requires a running Docker daemon, so as evidence it would fail in CI for an environmental reason rather than a real one. |
| Shared types and API contracts | - | not started | 3 | 0/12 | `packages/api_contracts` | Covers Implementation_Sequence steps 03 and 11: the versioned contract schemas, the derived language types, the canonical request model and docs/api/openapi.yaml. |
| Database foundation | - | not started | 4 | 0/12 | `database` | Decision D6 applies: every migration ships a tested down-migration and production applies migrations forward only. |
| Verification suites | - | not started | 42 | 0/12 | `tests` | Covers Implementation_Sequence steps 40 to 42: security testing, load testing and end-to-end testing. |
| Documentation set | - | not started | 43 | 0/12 | `docs` | - |

## Services

| Component | Module | Status | Step | DoD | Implementation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Model registry | 07 Model Registry | not started | 8 | 0/12 | `services/registry` | The only place a model price or context-window figure may be stated. The literal scanner of spec task 3.1 fails the build on such a literal elsewhere. |
| Provider management | 06 Provider Management | not started | 9 | 0/12 | `services/providers` | The Provider_Gateway and its adapters. This is the only component permitted to call a provider API, which the boundary scanner of spec task 3.2 enforces. |
| Gateway | 01 Gateway | not started | 12 | 0/12 | `services/gateway` | Serves the eleven paths of Master_Specification section 45 under /v1, including streaming pass-through and the rate-limit scopes of section 27. |
| Request analyzer | 08 Request Analyzer | not started | 13 | 0/12 | `services/analyzer` | Model-agnostic by construction: analyze() receives no registry and no AnalysisResult field may name a model or a provider. |
| Routing engine | 09 Routing Engine | not started | 14 | 0/12 | `services/router` | The core IP: candidate filtering, the six-term score, the six Routing_Mode weight presets and the explainable RoutingDecision. Determinism claims are scoped to a fixed Routing_Input per decision D5. |
| Cost engine | 10 Cost Engine | not started | 15 | 0/12 | `services/cost_engine` | Cost is per request, summed across every attempt including fallbacks and escalations, and savings are signed and never floored at zero (decision D4). |
| Policy engine | 11 Policy Engine | not started | 16 | 0/12 | `services/policy` | Resolution is monotonic narrowing across the six scopes of the Policy_Hierarchy: a narrower scope may restrict further and may never widen (decision D3). |
| Escalation engine | 12 Escalation Engine | not started | 17 | 0/12 | `services/router/internal/escalation` | Re-routes to a higher-capability candidate from the same candidate set, so an escalated model still satisfies the original policy decision. |
| Fallback engine | 13 Fallback Engine | not started | 18 | 0/12 | `services/router/internal/fallback` | Selects alternatives from the existing candidate set only, so fallback can never reach a prohibited provider. Owns the Circuit_Breaker states. |
| Audit | 25 Audit | not started | 21 | 0/12 | `services/audit` | Append-only storage with UPDATE and DELETE revoked from the application role. Identity and policy events start being recorded at sequence steps 05 to 07, before this service exists. |
| Analytics | 22 Analytics | not started | 22 | 0/12 | `services/analytics` | Aggregation by every dimension of Master_Specification section 54, the FinOps figures of section 55 and the routing metrics of section 78, always scoped to the requesting principal's tenant. |
| Billing | 26 Billing | not started | 30 | 0/12 | `services/billing` | Money is held in integer minor units. Billing state is outside the routing core's import boundary. |
| Notifications | 27 Notifications | not started | 31 | 0/12 | `services/notifications` | Email, webhook, Slack and Teams delivery for every event of Master_Specification section 57, excluding sensitive values and message content. |

## Integrations

| Component | Module | Status | Step | DoD | Implementation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| MCP server | 15 MCP Server | not started | 23 | 0/12 | `integrations/mcp` | The six tools of Master_Specification section 37, each delegating to the core. No scoring or filtering logic may live here. |
| IDE integrations | 16 IDE Integrations | not started | 27 | 0/12 | `integrations` | Covers the VS Code, Kiro, Cursor, Claude Code and JetBrains adapters and the Capability_Profile of Master_Specification section 39. |

## Clients and interfaces

| Component | Module | Status | Step | DoD | Implementation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| API | 18 API | not started | 12 | 0/12 | `apps/api` | The public API product: the surface served by the gateway, its generated reference documentation and its conformance suite. The contract itself belongs to the shared-contracts entry. |
| Client | 17 Client | not started | 24 | 0/12 | `clients/local-agent` | The developer-machine Local_Client of Master_Specification section 44: login, configuration, MCP hosting and diagnostics, with credentials in the OS secure store. clients/desktop is a later shell over the same client. |
| CLI | 19 CLI | not started | 25 | 0/12 | `cli` | Every command of Master_Specification section 48 with machine-readable output and documented exit statuses. The command tree exists as empty directories only. |
| SDK | 20 SDK | not started | 26 | 0/12 | `sdk` | One shared conformance suite is parameterized over all three SDKs so they cannot diverge. |
| Dashboard | 21 Dashboard | not started | 28 | 0/12 | `apps/dashboard` | - |
| Administration | 30 Administration | not started | 29 | 0/12 | `apps/admin-console` | The Admin_Console of Master_Specification section 105. Authorization is evaluated server side; the console is never trusted for it. |

## Platform

| Component | Module | Status | Step | DoD | Implementation | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Authentication | 02 Authentication | not started | 5 | 0/12 | `packages/auth` | - |
| Tenant management | 03 Tenant Management | not started | 6 | 0/12 | `packages/tenant` | Owns TenantContext and the tenant-scoped session. Tenant isolation must exist before any tenant-owned row is written. |
| Team management | 05 Team Management | not started | 7 | 0/12 | `packages/tenant` | Teams share the organization model in packages/tenant with tenants, and are a policy scope in the six-level Policy_Hierarchy. |
| User management | 04 User Management | not started | 7 | 0/12 | `packages/authorization` | Users, their roles and the granular permissions of Master_Specification section 32. The administrative surface is served by the gateway; the repository has no dedicated control-api service yet, and deployments/helm/agentrouter/templates/control-api.yaml is a placeholder for one. |
| Security engine | 14 Security Engine | not started | 19 | 0/12 | `packages/security` | Redaction, retention and transport security. Redaction is applied inside the logging emit path so a Sensitive_Value cannot leave the process through a log line. |
| Observability | 28 Observability | not started | 20 | 0/12 | `packages/telemetry` | Structured logging, OpenTelemetry tracing, the metric registry and the alert rules under observability/alerts/. |
| Event system | - | not started | 21 | 0/12 | `packages/events` | Transactional outbox, dispatcher and idempotent consumer base. Analytics, Billing, Notifications and Audit all depend on it. |
| Benchmarking | 23 Benchmarking | not started | 32 | 0/12 | `benchmark` | Requirements 2.3 and 2.4: a published quality or latency figure must carry its dataset id, model id, run timestamp and sample count, and a figure without a recorded run is excluded from reports. |
| Evaluation | 24 Evaluation | not started | 33 | 0/12 | `evaluation` | - |
| Deployment | 29 Deployment | not started | 34 | 0/12 | `deployments` | Covers Implementation_Sequence steps 34 to 37 (Kubernetes, Helm, Terraform, CI/CD) and the HA and DR posture of steps 38 and 39. |

## Verification evidence

Named, re-runnable commands. `scripts/status/verify.py` runs the commands of every component recorded as `implemented`; the commands below belonging to components at another status are declared, not gated.

| Component | Evidence | Command |
| --- | --- | --- |
| Repository foundation | `scaffold-idempotent` | `python scripts/bootstrap/scaffold_repository.py` |
| Repository foundation | `structure-valid` | `python scripts/testing/validate_structure.py` |
| Completion ledger | `status-manifest` | `python -m pytest tests/unit/test_status_manifest.py -q` |
| Development environment and quality gate | `quality-gate` | `python scripts/development/check.py` |
| Development environment and quality gate | `dependency-manifests` | `python -m pytest tests/unit/test_dependency_manifests.py -q` |

## Known limitations

Requirement 1.8. An absent entry below is a positive claim that the component has no known limitation, not an absence of review.

### Repository foundation

- The target structure is embedded in the generator as code, not read from a data file, so the structure definition and its validator list are maintained in two places.
- The generator and the structure validator have no dedicated unit suite; only the byte-for-byte constant guard in tests/unit/test_quality_command.py protects them from drift.

### Completion ledger

- Only the schema and the seeded manifest exist. `scripts/status/validate.py`, `render.py`, `verify.py` and `check_dod.py` are spec task 2.2 and are absent.
- `docs/IMPLEMENTATION_STATUS.md` is still hand-written and is not yet generated from this manifest, so the two can disagree until task 2.2 lands.
- The `postTaskExecution` completion hook is spec task 2.3 and does not exist, so status changes are manual.
- The `status-schema`, `status-render`, `status-evidence` and `status-dod` CI jobs are spec task 2.4 and do not exist.
- Uniqueness of component ids and coverage of all 30 section-6 modules are not expressible in JSON Schema; they are asserted in tests/unit/test_status_manifest.py.

### Development environment and quality gate

- `scripts/development/health.py` is exercised only against stubbed sockets; no automated test starts the Compose stack, so the reachability path is unverified end to end.
- The Compose stack starts PostgreSQL and Redis only. No application service is buildable, so `make up` produces backing services and nothing else.
- Coverage `fail_under` is 0 because there is no source to measure yet.

### Observability

- observability/ documents the metric catalog of Master_Specification section 59 in prose only. No collector configuration, dashboard, alert rule or runbook exists.

### SDK

- Decision D2 excludes Go from phase 1, so sdk/go stays a scaffold while the TypeScript and Python SDKs are built.

### IDE integrations

- No integration capability is claimed as supported for any host. Requirement 2.5 requires each documented capability to name the passing automated test that exercises it against the host's officially supported mechanism, and no such test exists.

### Benchmarking

- No dataset exists in any of the eight domain directories, so every routing weight in config/ is an unmeasured starting value rather than a benchmarked one.

### Evaluation

- The labeled Routing_Dataset of Master_Specification section 76 does not exist, so routing quality is currently unmeasurable.

### Deployment

- Nothing in the repository is deployable. The only working deployment artifact is the local Compose stack, and it starts PostgreSQL and Redis only.
- The Helm chart passes `helm lint` and installs cleanly while deploying no workload at all, which makes a successful install a misleading signal until the templates are written.

### Verification suites

- Only tests/unit holds tests. The api, mcp, integration, e2e, security, load and chaos suites are empty directories.

### Documentation set

- Every page under docs/ states its purpose and scope; none carries the content it promises.
- No executable example is embedded anywhere, so Requirement 43.3 has nothing to run.

## Placeholder artifacts

Requirement 2.8. Each of these exists, parses or lints, and does not build, render or execute. They are listed so a green check on one of them cannot be mistaken for working software.

| Path | Kind | Component | Why it is a placeholder |
| --- | --- | --- | --- |
| `Makefile` | Make target | Repository foundation | The `build` and `migrate` targets print a message and exit 1. They fail loudly rather than pretending to succeed, but neither builds nor migrates anything. |
| `docs/api/openapi.yaml` | API contract | Shared types and API contracts | `paths` is an empty object. The document parses and declares its version, tags and security schemes, but describes no operation, so nothing can be generated or validated from it. |
| `packages/api_contracts` | Directory | Shared types and API contracts | Holds a README only. No schema, no generated type and no codegen entry point. |
| `database/migrations` | Directory | Database foundation | Empty. None of the 25 core tables of Master_Specification section 61 exists, so no migration runner, no seed and no row-level security policy can run. |
| `apps/api/package.json` | Other | API | The `build` and `test` scripts echo "not implemented" and exit 1. |
| `integrations/mcp/package.json` | Other | MCP server | The `build` and `test` scripts echo "not implemented" and exit 1. The package declares no dependency and no entry point. |
| `sdk/go/go.mod` | Other | SDK | Declares a module path and a Go version over a directory with no Go source, so `go build ./...` compiles nothing. |
| `sdk/typescript/package.json` | Other | SDK | The `build` and `test` scripts echo "not implemented" and exit 1. |
| `integrations/vscode/package.json` | Other | IDE integrations | Extension manifest scaffold. The `build` and `test` scripts exit 1; no activation event, contribution or command is declared. |
| `apps/dashboard/package.json` | Other | Dashboard | The `build` and `test` scripts echo "not implemented" and exit 1. No framework, dependency or source file is present. |
| `apps/admin-console/package.json` | Other | Administration | The `build` and `test` scripts echo "not implemented" and exit 1. |
| `.github/workflows/build-images.yml` | CI workflow | Deployment | Prints that service Dockerfiles are scaffolds and exits 0. It builds no image, so a green run means nothing was built. |
| `.github/workflows/deploy-production.yml` | CI workflow | Deployment | Manual dispatch only; prints that deployment is not wired up and exits 0. |
| `.github/workflows/deploy-staging.yml` | CI workflow | Deployment | Manual dispatch only; prints that deployment is not wired up and exits 0. |
| `cli/Dockerfile` | Dockerfile | Deployment | Same shape as the service Dockerfiles: `FROM scratch` plus labels, no build stage, no source to build. |
| `deployments/helm/agentrouter/templates/*.yaml` | Helm template | Deployment | Every one of the twelve templates contains a Go template comment and nothing else, so `helm template` renders zero Kubernetes resources. |
| `deployments/kubernetes/base` | Kubernetes manifest | Deployment | Empty, as are the development, staging and production overlays. There is no kustomization and no manifest. |
| `infrastructure/terraform/modules` | Terraform module | Deployment | Seven module directories and three environment directories hold a README and a .gitkeep each. No .tf file exists, so `terraform init` has nothing to initialize. |
| `services/*/Dockerfile` | Dockerfile | Deployment | Each is `FROM scratch` plus labels, with the intended build stages in comments. Deliberately not buildable: the services have no source. Named per service in .github/workflows/build-images.yml, which is itself disabled. |
| `apps/docs` | Directory | Documentation set | Documentation site scaffold. Holds a README and empty content and public directories; no generator, no build. |

## Remaining work

Work follows the 46-step Implementation_Sequence of Master_Specification section 132; the Step column above gives each component's step. The task sheet is `.kiro/specs/agentrouter-end-to-end-delivery/tasks.md`.
