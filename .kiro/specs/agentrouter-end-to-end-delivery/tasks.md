# Implementation Plan

## Overview

Tasks follow the 46-step Implementation_Sequence of Master_Specification section 132.
Every task is a coding step; each names the requirements it satisfies. Completion updates
`docs/implementation-status.yaml` and regenerates `docs/IMPLEMENTATION_STATUS.md`
automatically via the task-completion hook built in task 2.

Tasks 1 through 3 are deliberately front-loaded infrastructure: the quality gate, the
completion ledger, and the boundary scanners. They exist first because every later task
depends on them to prove it is done, and because the anti-fabrication controls are worthless
if added after the code they are meant to police.

Task 16 is the milestone that matters most. At that point the vertical slice of decision D1
runs end to end and routing quality becomes measurable. Everything after it either hardens
that path or widens access to it.

## Task Dependency Graph

Tasks within a wave have no interdependencies and may proceed in any order or in parallel.
Each wave requires every prior wave to be complete.

```json
{
  "waves": [
    {
      "wave": 1,
      "name": "Foundation and enforcement",
      "tasks": ["1", "1.1", "1.2"],
      "requires": [],
      "rationale": "Nothing can be validated before the quality gate exists."
    },
    {
      "wave": 2,
      "name": "Completion ledger",
      "tasks": ["2", "2.1", "2.2", "2.3", "2.4"],
      "requires": ["1"],
      "rationale": "Every later task proves completion through this ledger and its hook."
    },
    {
      "wave": 3,
      "name": "Anti-fabrication and boundaries",
      "tasks": ["3", "3.1", "3.2"],
      "requires": ["2"],
      "rationale": "Scanners must police code as it is written, not retroactively."
    },
    {
      "wave": 4,
      "name": "Contracts",
      "tasks": ["4", "4.1", "4.2", "4.3", "4.4"],
      "requires": ["3"],
      "rationale": "All components and SDKs derive types from these schemas."
    },
    {
      "wave": 5,
      "name": "Cross-cutting packages",
      "tasks": ["5", "5.1", "5.2", "5.3", "5.4"],
      "requires": ["4"],
      "rationale": "Config, errors, redaction, logging, telemetry are used by every service."
    },
    {
      "wave": 6,
      "name": "Persistence and tenancy",
      "tasks": ["6", "6.1", "6.2", "6.3", "6.4"],
      "requires": ["5"],
      "rationale": "Tenant isolation must exist before any tenant-owned data is written."
    },
    {
      "wave": 7,
      "name": "Identity",
      "tasks": ["7", "7.1", "7.2", "7.3", "7.4"],
      "requires": ["6"],
      "rationale": "TenantContext derives from verified credentials."
    },
    {
      "wave": 8,
      "name": "Registry and providers",
      "tasks": ["8", "8.1", "8.2", "8.3", "13", "13.1", "13.2", "13.3", "13.4"],
      "requires": ["7"],
      "rationale": "Registry snapshots and adapters are independent of each other but both precede routing."
    },
    {
      "wave": 9,
      "name": "Pure core",
      "tasks": ["9", "9.1", "9.2", "9.3", "10", "10.1", "10.2", "10.3", "12", "12.1", "12.2", "12.3"],
      "requires": ["8"],
      "rationale": "Analyzer, policy engine and cost engine are mutually independent pure components."
    },
    {
      "wave": 10,
      "name": "Routing engine",
      "tasks": ["11", "11.1", "11.2", "11.3", "11.4", "11.5"],
      "requires": ["9"],
      "rationale": "Consumes analysis, policy decision, registry snapshot and cost estimation."
    },
    {
      "wave": 11,
      "name": "Request path assembly",
      "tasks": ["14", "14.1", "14.2", "15", "15.1", "15.2", "15.3"],
      "requires": ["10"],
      "rationale": "Normalization and orchestration wire the core to execution."
    },
    {
      "wave": 12,
      "name": "API gateway - vertical slice complete",
      "tasks": ["16", "16.1", "16.2", "16.3"],
      "requires": ["11"],
      "rationale": "Milestone of decision D1: routing quality becomes measurable end to end."
    },
    {
      "wave": 13,
      "name": "Async, integrations, interfaces, deployment",
      "tasks": [
        "17", "17.1", "17.2", "17.3", "17.4", "17.5", "17.6",
        "18", "19", "20", "20.1", "20.2", "24", "24.1", "24.2",
        "25", "26", "26.1", "26.2", "27", "27.1", "27.2"
      ],
      "requires": ["12"],
      "rationale": "Four independent branches off the working vertical slice."
    },
    {
      "wave": 14,
      "name": "Clients and packaging",
      "tasks": ["21", "21.1", "21.2", "22", "23", "28", "29"],
      "requires": ["13"],
      "rationale": "Clients require the MCP server; Helm and Terraform require images."
    },
    {
      "wave": 15,
      "name": "Pipeline and resilience",
      "tasks": ["26.3", "30", "31", "32"],
      "requires": ["14"],
      "rationale": "Measured weights require the harness; HA and DR require deployment."
    },
    {
      "wave": 16,
      "name": "Verification and hardening",
      "tasks": ["33", "33.1", "33.2", "33.3", "34", "34.1", "34.2", "36"],
      "requires": ["15"],
      "rationale": "Full-system suites require the full system."
    },
    {
      "wave": 17,
      "name": "Production readiness",
      "tasks": ["35"],
      "requires": ["16"],
      "rationale": "Declares readiness only when every Production_DoD item has passing evidence."
    }
  ],
  "critical_path": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17"],
  "milestone": {
    "wave": 12,
    "meaning": "End-to-end routed request on a single host per decision D1"
  }
}
```

## Tasks

- [x] 1. Establish the development environment and quality gate
- [x] 1.1 Create the Python workspace and dependency manifests
  - Add a root `pyproject.toml` declaring the workspace, pinned exact dependency versions, and the `packages/*` plus `services/*` members
  - Configure ruff, mypy strict mode, and pytest with coverage in the same file
  - Add `requirements-dev.txt` pinning test tooling including hypothesis
  - _Requirements: 3.3, 3.6_
  - _Evidence: `python -m pytest tests/unit/test_dependency_manifests.py -q` (71 passed); `python -m ruff check .`; `python -m mypy`; `python scripts/testing/validate_structure.py` (320 paths)_

- [x] 1.2 Wire the single quality command and environment health check
  - Implement `scripts/development/check.py` running format, lint, type check, and unit tests as one command, surfaced as `make check`
  - Implement `scripts/development/health.py` verifying PostgreSQL and Redis reachability, surfaced as `make health`
  - Extend the CI structure job to run `make check`
  - _Requirements: 3.3, 3.4, 3.5, 3.6_
  - _Evidence: `python scripts/development/check.py` (4/4 steps pass, 107 tests); `python scripts/development/health.py` (exit 0 with compose services up, exit 1 with remediation when down); `python scripts/bootstrap/scaffold_repository.py` (0 created on re-run); `python scripts/testing/validate_structure.py` (324 paths)_

- [ ] 2. Build the completion ledger and auto-update mechanism
- [x] 2.1 Define the status manifest and its schema
  - Write `docs/status-manifest.schema.json` covering component id, module, status enum, phase, implementation path, tests path, evidence commands, the twelve Component_DoD booleans, and limitations
  - Write `docs/implementation-status.yaml` seeded with every component of Master_Specification section 6 at `not_started`
  - _Requirements: 1.1, 1.2, 1.3_
  - _Evidence: `python -m pytest tests/unit/test_status_manifest.py -q` (271 passed); `python scripts/development/check.py` (4/4 steps pass, 382 tests); `python scripts/testing/validate_structure.py` (326 paths); `python scripts/bootstrap/scaffold_repository.py` (0 created on re-run)_

- [ ] 2.2 Implement manifest validation, rendering, and evidence verification
  - Implement `scripts/status/validate.py` checking the manifest against its schema
  - Implement `scripts/status/render.py` generating `docs/IMPLEMENTATION_STATUS.md` from the manifest
  - Implement `scripts/status/verify.py` executing each evidence command for components marked `implemented` and failing on any non-zero exit
  - Implement `scripts/status/check_dod.py` failing when an `implemented` component has any false Component_DoD item
  - Write unit tests covering a passing manifest, a schema violation, a stale rendering, failing evidence, and an incomplete DoD
  - _Requirements: 1.3, 1.4, 1.6, 1.7, 2.8_

- [ ] 2.3 Implement the task-completion hook
  - Implement `scripts/status/on_task_complete.py` that maps a completed task to its component, re-runs that component's evidence, promotes status to `implemented` only when evidence exits zero and all twelve DoD items are true, records `blocked` with captured failure output otherwise, regenerates the status document, and writes the evidence name into this task sheet
  - Register a `postTaskExecution` hook invoking the script
  - Write tests asserting the hook never promotes a component whose evidence fails
  - _Requirements: 1.5, 1.8, 1.10, 1.11_

- [ ] 2.4 Add the ledger gates to CI
  - Add `status-schema`, `status-render`, `status-evidence`, and `status-dod` jobs to `.github/workflows/ci.yml`
  - _Requirements: 1.3, 1.4, 1.6, 1.7_

- [ ] 3. Implement anti-fabrication and boundary enforcement
- [ ] 3.1 Implement the placeholder and literal scanners
  - Implement `scripts/architecture/check_placeholders.py` failing when a source file belonging to an `implemented` component contains a configured placeholder marker
  - Implement `scripts/architecture/check_literals.py` using AST analysis to fail on model price or context-window literals outside the registry, exempting declared fixture and seed paths
  - Write tests including the fixture-exemption case
  - _Requirements: 2.1, 9.3_

- [ ] 3.2 Implement import-graph boundary enforcement
  - Implement `scripts/architecture/check_boundaries.py` reading an allow-list of permitted import edges and failing when routing core imports a provider SDK, HTTP client, IDE adapter, MCP module, or billing state
  - Add the allow-list data file and tests for each forbidden edge
  - Add all scanners to CI
  - _Requirements: 28.6, 30.4, 45.1, 45.2_

- [ ] 4. Define shared types and API contracts
- [ ] 4.1 Author the contract schemas
  - Write JSON Schema documents in `packages/api_contracts/schemas/` for canonical request, analysis result, routing decision, policy decision, usage record, and the normalized error set, each carrying `x-contract-version`
  - _Requirements: 4.1_

- [ ] 4.2 Implement shared types and the lifecycle state machine
  - Implement frozen dataclasses in `packages/shared_types/` for every contract type
  - Implement the request lifecycle table with validated transitions and terminal states
  - Write round-trip property tests over schema-derived Hypothesis strategies
  - _Requirements: 4.5, 4.6, 4.7, 11.6_

- [ ] 4.3 Implement code generation and the drift gate
  - Implement `packages/api_contracts/codegen.py` emitting Python and TypeScript types from the schemas
  - Add a CI job regenerating types and failing when committed output differs
  - _Requirements: 4.4_

- [ ] 4.4 Author the OpenAPI document
  - Declare an operation for each of the eleven paths of Master_Specification section 45, referencing the contract schemas
  - Add CI validation of the document against its declared OpenAPI version
  - _Requirements: 4.2, 4.3_

- [ ] 5. Implement configuration, errors, redaction, logging, and telemetry
- [ ] 5.1 Implement the typed configuration loader
  - Implement `packages/configuration/` binding environment variables and `config/<env>/*.yaml` into typed settings, including weight presets and the analyzer signal profiles
  - Implement a `SecretSource` port with an environment implementation
  - Write tests for missing required settings and precedence order
  - _Requirements: 20.6, 13.8, 14.3_

- [ ] 5.2 Implement the normalized error taxonomy
  - Implement `packages/errors/` with every error of Master_Specification section 47 and its HTTP and MCP mappings
  - Write tests asserting each error maps to the documented status code
  - _Requirements: 2.7, 12.7_

- [ ] 5.3 Implement redaction
  - Implement detectors for every Sensitive_Value category, plus the non-sensitive identifier allow-list
  - Write property tests for redaction idempotence and the no-sensitive-substring property
  - _Requirements: 20.1, 20.2, 20.3_

- [ ] 5.4 Implement structured logging and telemetry
  - Implement `packages/logging/` with redaction applied inside the emit path and content logging off unless explicitly enabled
  - Implement `packages/telemetry/` with OpenTelemetry tracing, the metric registry of Master_Specification section 59, and shared trace identifiers
  - Write tests asserting a secret passed to the logger never appears in output
  - _Requirements: 20.2, 20.4, 21.1, 21.2, 21.3, 21.4_

- [ ] 6. Implement the persistence layer
- [ ] 6.1 Implement the migration runner
  - Implement forward migration application with version conflict detection and a development-only revert path
  - Write tests for duplicate version rejection and up/down round-trip
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.8_

- [ ] 6.2 Create the core schema migrations
  - Write ordered migrations creating the 25 core tables, with `tenant_id NOT NULL` on tenant-owned tables, integer minor-unit money columns, month partitioning on the high-volume append-only tables, and a unique constraint on `processed_events.event_id`
  - Revoke UPDATE and DELETE on `audit_events` from the application role
  - _Requirements: 5.1, 5.6, 8.6, 22.3_

- [ ] 6.3 Implement tenant-scoped data access
  - Implement `packages/tenant/` with `TenantContext` and a scoped session that applies a tenant predicate to every query and raises on unscoped access
  - Enable PostgreSQL row-level security on every tenant-owned table
  - Write a property test asserting cross-tenant reads return zero rows, driven by table introspection
  - _Requirements: 7.3, 7.4, 7.5_

- [ ] 6.4 Create the seed dataset
  - Write seeds providing tenants, users, teams, providers, models with pricing, and policies sufficient for the integration suite
  - _Requirements: 5.7_

- [ ] 7. Implement authentication and authorization
- [ ] 7.1 Implement credential verification
  - Implement API key issuance with Argon2id hashing and a lookup prefix, returning key material only at creation, plus expiration and revocation checks
  - Implement OIDC token verification and service-account credentials
  - Write tests for expired, revoked, absent, and malformed credentials asserting no credential material reaches responses or logs
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 7.2 Implement tenant context derivation
  - Derive `TenantContext` solely from the verified credential and reject requests whose supplied tenant identifier disagrees
  - Write tests for the mismatch rejection path
  - _Requirements: 7.1, 7.2_

- [ ] 7.3 Implement RBAC
  - Implement every role of Master_Specification section 32, granular named permissions, and a `require()` check evaluated server side
  - Restrict DEVELOPER principals to their own usage records
  - Write tests asserting a permission-less principal performs no part of a protected operation
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.7_

- [ ] 7.4 Implement audit logging for identity events
  - Record append-only audit entries for key creation, rotation, revocation, and role changes
  - _Requirements: 6.6, 8.6_

- [ ] 8. Implement the model registry
- [ ] 8.1 Implement model and provider records
  - Implement storage and validation for every Model_Record field of Master_Specification section 12, rejecting records missing a required capability or pricing field and naming the missing field
  - _Requirements: 9.1, 9.2, 9.8_

- [ ] 8.2 Implement lifecycle management
  - Implement the six Model_Lifecycle_States with an allowed-transition set and audit entries on transition
  - _Requirements: 9.4, 9.5_

- [ ] 8.3 Implement the health read model and registry snapshots
  - Implement per-model availability, latency, and error-rate exposure
  - Implement immutable `RegistrySnapshot` construction with a content-hash snapshot id, excluding DEPRECATED and RETIRED models, cached in Redis with a short TTL
  - Write tests asserting identical state yields an identical snapshot id
  - _Requirements: 9.6, 9.7, 14.12_

- [ ] 9. Implement the request analyzer
- [ ] 9.1 Implement the task classifier and context tiers
  - Implement configurable rule-based classification over the task types of Master_Specification section 15, falling back to GENERAL below the confidence floor
  - Implement `Context_Tier` banding from token estimates
  - _Requirements: 13.2, 13.8, 13.9_

- [ ] 9.2 Implement complexity derivation
  - Derive Complexity_Level from task type, operation count, reasoning requirement, context tier, tool requirement, expected output, ambiguity, and dependency depth, reading raw length only through `Context_Tier`
  - Emit the signal map for explainability and a confidence value in the unit interval
  - Write the property test for complexity stability within a context tier
  - _Requirements: 13.1, 13.3, 13.4, 13.5, 13.6_

- [ ] 9.3 Enforce the analyzer's model-agnostic signature
  - Confirm `analyze()` receives no registry and write a test asserting no AnalysisResult field can name a model or provider
  - _Requirements: 13.7_

- [ ] 10. Implement the policy engine
- [ ] 10.1 Implement policy rules and storage
  - Implement every policy field of Master_Specification section 28 with per-scope persistence
  - _Requirements: 17.1_

- [ ] 10.2 Implement monotonic narrowing resolution
  - Implement the broad-to-narrow fold intersecting permissions and unioning prohibitions across the six scopes, recording the contributing scope for each restriction
  - Return `PolicyDecision` carrying allowed, reason, and restrictions
  - Write property tests for determinism, idempotence, and the prohibition-precedence invariant
  - _Requirements: 17.2, 17.3, 17.4, 17.5, 17.6_

- [ ] 10.3 Implement policy audit and region constraints
  - Record audit entries for policy creation, modification, and deletion
  - Expose permitted regions for consumption by the routing region filter
  - _Requirements: 17.8, 17.9_

- [ ] 11. Implement the routing engine
- [ ] 11.1 Implement candidate filtering
  - Implement the capability, context, policy, region, availability, and budget filters as named predicates over a `RegistrySnapshot`, each recording rejections with its filter name
  - _Requirements: 14.1, 15.3_

- [ ] 11.2 Implement the scoring function and weight presets
  - Implement the six-term score with each term normalized to the unit interval and all weights read from configuration
  - Define the six routing modes as named weight presets, with COST_FIRST assigning cost the sole non-zero weight
  - _Requirements: 14.2, 14.3, 14.4, 14.10_

- [ ] 11.3 Implement selection and the routing decision
  - Select the maximum-scoring candidate with the total tie-break ordering, and return MODEL_UNAVAILABLE naming the last removing filter when the candidate set is empty
  - Emit `RoutingDecision` carrying selected model, reasons, confidence, estimated cost, alternatives, rejections, mode, weights, consulted policy decisions, and the routing input id
  - _Requirements: 14.11, 15.1, 15.2, 15.4_

- [ ] 11.4 Write the routing property suite
  - Implement properties for candidate membership, capability satisfaction, context sufficiency, prohibition avoidance, maximal score, and determinism over a fixed `RoutingInput`
  - _Requirements: 14.5, 14.6, 14.7, 14.8, 14.9, 14.12_

- [ ] 11.5 Persist and expose routing decisions
  - Persist each decision against its request identifier and return tenant-permitted fields when developer transparency is enabled
  - _Requirements: 15.5, 15.6_

- [ ] 12. Implement the cost engine
- [ ] 12.1 Implement cost calculation
  - Implement per-attempt cost from registry pricing in integer minor units and per-request accumulation across all attempts including fallbacks and escalations, retaining the breakdown
  - Support the per-provider pricing structures declared in the registry
  - Write the property test for cost equalling tokens times price summed over attempts
  - _Requirements: 16.1, 16.2, 16.7_

- [ ] 12.2 Implement signed savings and estimation
  - Implement savings as baseline minus actual with no clamping, returning zero only when the baseline served alone
  - Implement pre-flight estimation and forecast labelling with the derivation window
  - Write tests asserting a costlier-than-baseline request reports negative savings
  - _Requirements: 2.2, 16.3, 16.4, 16.5, 16.6, 16.8_

- [ ] 12.3 Handle missing pricing
  - Record cost as unavailable and raise a pricing-gap notification rather than defaulting to zero
  - _Requirements: 16.9_

- [ ] 13. Implement the provider gateway
- [ ] 13.1 Implement the adapter interface and shared behaviour
  - Implement the `ProviderAdapter` protocol with all seven operations, plus shared retry, timeout, and error normalization
  - _Requirements: 10.1, 10.4_

- [ ] 13.2 Implement the OpenAI, Anthropic, Google, and compatible adapters
  - Implement each adapter including streaming that forwards chunks without accumulation and a pre-flight context check returning CONTEXT_TOO_LARGE before any network call
  - Read credentials from the secret source at request time, excluding them from logs, errors, and telemetry
  - _Requirements: 10.2, 10.6, 10.7, 10.8_

- [ ] 13.3 Write the shared adapter contract suite
  - Implement one assertion set parameterized over every adapter, running against recorded fixtures, with a separately-marked live suite
  - Add a first-chunk-latency test proving streaming does not buffer
  - _Requirements: 10.5, 42.5_

- [ ] 13.4 Implement provider health and the circuit breaker
  - Implement latency, error-rate, and availability tracking with closed, open, and half-open transitions on configured thresholds, stored in Redis so state is shared across replicas
  - Write tests for each transition including the half-open probe closing the circuit
  - _Requirements: 19.3, 19.4, 19.5_

- [ ] 14. Implement request normalization and entry adapters
- [ ] 14.1 Implement the normalizer
  - Convert input from every entry point into a `CanonicalRequest`, assigning a unique request identifier and setting tenant, user, and team fields from `TenantContext` rather than the payload
  - Return INVALID_REQUEST naming any missing required field
  - _Requirements: 11.1, 11.2, 11.4, 11.5_

- [ ] 14.2 Implement lifecycle tracking and the confluence property
  - Advance and record lifecycle transitions against the request identifier
  - Write the property test asserting equivalent input at every entry point yields equal canonical requests modulo identifier and timestamp
  - _Requirements: 11.3, 11.6_

- [ ] 15. Implement the execution orchestrator
- [ ] 15.1 Implement the escalation engine
  - Evaluate completed responses against the configured criteria and re-route to a higher-capability candidate from the same candidate set, bounded by the attempt limit, recording every attempt and returning the escalation history
  - Return the original response unchanged when escalation is disabled for the tenant
  - Write tests asserting escalated models satisfy the original policy decision
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_

- [ ] 15.2 Implement the fallback engine
  - Select alternatives from the existing candidate set on provider failure or timeout, recording each attempt, and return the normalized provider error with a FAILED lifecycle state when no compliant alternative exists
  - Write tests asserting fallback never reaches a prohibited provider
  - _Requirements: 19.1, 19.2, 19.6, 19.7_

- [ ] 15.3 Wire the orchestrator and the no-dispatch guarantee
  - Compose route, execute, evaluate, escalate, fall back, and record cost into the bounded loop
  - Write tests asserting a policy-blocked request and an empty candidate set both dispatch zero provider requests
  - _Requirements: 14.11, 17.7_

- [ ] 16. Implement the API gateway
- [ ] 16.1 Implement the HTTP application and routes
  - Serve every path of Master_Specification section 45 under `/v1`, conforming to the OpenAPI schemas, attaching request and trace identifiers to every response
  - Return UNKNOWN with the request identifier and no stack detail on unhandled errors
  - _Requirements: 12.1, 12.2, 12.6, 12.7_

- [ ] 16.2 Implement streaming pass-through
  - Forward provider chunks to the client as received when the streaming flag is set
  - _Requirements: 12.3_

- [ ] 16.3 Implement rate limiting
  - Enforce limits at every scope of Master_Specification section 27 using Redis, returning RATE_LIMIT naming the exceeded scope
  - _Requirements: 12.4, 12.5_

- [ ] 17. Implement the event system and asynchronous consumers
- [ ] 17.1 Implement the transactional outbox
  - Implement event definitions for Master_Specification section 64, unique event identifiers, an outbox writer enlisted in the request transaction, and a broker-agnostic publisher port
  - Write round-trip property tests for event serialization
  - _Requirements: 22.1, 22.2, 22.6_

- [ ] 17.2 Implement the dispatcher and idempotent consumer base
  - Implement worker polling, dispatch, retry with failure recording, and a consumer base enforcing idempotence through `processed_events`
  - Write the property test for repeated event identifiers producing identical consumer state
  - Write a test asserting the request path returns without waiting for consumers
  - _Requirements: 22.3, 22.4, 22.5_

- [ ] 17.3 Implement analytics aggregation and FinOps reporting
  - Aggregate usage and cost by every dimension of Master_Specification section 54, report the figures of section 55 and the routing metrics of section 78, scoped to the requesting principal's tenant
  - Write the property test asserting aggregates equal the underlying records
  - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.7_

- [ ] 17.4 Implement budgets and anomaly detection
  - Execute the configured action at each budget threshold of Master_Specification section 56 and notify administrators on deviation beyond configured bounds
  - _Requirements: 23.5, 23.6_

- [ ] 17.5 Implement notifications
  - Deliver to email, webhook, Slack, and Teams for every event of Master_Specification section 57, excluding sensitive values and message content, retrying within the configured budget and recording final outcome
  - Write the property test for one delivered notification per channel per event identifier
  - _Requirements: 31.1, 31.2, 31.3, 31.4, 31.5_

- [ ] 17.6 Implement the audit service
  - Implement append-only storage and auditor-facing queries for every administrative event of Master_Specification section 58
  - Write a test asserting update and delete attempts fail
  - _Requirements: 8.6_

- [ ] 18. Implement observability endpoints and alerting
  - Implement per-service health endpoints reporting dependency reachability
  - Define alert rules for every condition of Master_Specification section 57 under `observability/alerts/`
  - _Requirements: 21.5, 21.6_

- [ ] 19. Implement data retention and transport security
  - Implement tenant-configurable retention with deletion on elapse, metadata-only persistence by default, and conversation retention only on explicit opt-in
  - Enforce TLS at every controlled network boundary
  - Add the secret-detection gate to CI
  - _Requirements: 20.5, 20.7, 20.8, 20.9_

- [ ] 20. Implement the MCP server
- [ ] 20.1 Implement the six MCP tools
  - Implement `analyze_task`, `recommend_model`, `estimate_cost`, `get_available_models`, `check_policy`, and `route_request`, each delegating to the core and containing no scoring or filtering logic
  - Declare and document the implemented MCP specification version
  - _Requirements: 24.1, 24.2, 24.5_

- [ ] 20.2 Implement MCP authentication, authorization, and limits
  - Authenticate every connection, attach tenant context before any tool invocation, enforce per-tool permissions, rate limits, and audit logging, and reject unpermitted tools without partial execution
  - Write the property test asserting MCP and API produce identical policy decisions for equivalent requests
  - _Requirements: 24.3, 24.4, 24.6, 24.7_

- [ ] 21. Implement the local client and CLI
- [ ] 21.1 Implement the local client
  - Implement login, configuration, connection management, MCP hosting, and diagnostics, storing credentials in the OS secure store and excluding provider credentials from config files and logs
  - Report the failing check and remediation when the endpoint is unreachable, and expose version and negotiated API version
  - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5_

- [ ] 21.2 Implement the CLI
  - Implement every command of Master_Specification section 48 with machine-readable output, documented exit statuses, and a diagnose command checking every item of section 92 with remediation guidance
  - Write the property test asserting machine-readable output validates against each command's declared schema
  - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5_

- [ ] 22. Implement the SDKs
  - Implement TypeScript, Python, and Go SDKs exposing route, generate, stream, getModels, and getUsage, with types derived from the contracts, typed errors per normalized category, and incremental streaming interfaces
  - Implement one shared conformance suite parameterized over all three SDKs
  - _Requirements: 27.1, 27.2, 27.3, 27.4, 27.5_

- [ ] 23. Implement IDE integrations
  - Implement the `IntegrationAdapter` interface with the capability flags of Master_Specification section 39 and declare a capability profile for VS Code, Kiro, Cursor, Claude Code, and JetBrains using only officially documented mechanisms
  - Mark each capability supported only where a passing automated test exercises it, and document every unsupported capability as a limitation
  - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6_

- [ ] 24. Implement the dashboard and admin console
- [ ] 24.1 Implement the dashboard
  - Implement every section of Master_Specification section 50 plus the developer and administrator views of sections 51 and 52, reaching data only through the control-plane API
  - Implement the routing investigation view showing the fields of section 53, presenting negative savings as negative values
  - _Requirements: 16.5, 29.1, 29.2, 29.5, 29.6_

- [ ] 24.2 Implement the admin console and authorization tests
  - Implement management of every area of Master_Specification section 105
  - Write tests asserting the backend authorizes every privileged action irrespective of interface state
  - Add automated accessibility checks for verifiable WCAG 2.1 AA criteria
  - _Requirements: 29.3, 29.4, 29.7_

- [ ] 25. Implement billing
  - Implement plans, seats, metered usage, overages, invoices, and payment status, deriving charges from recorded usage records and charging a repeated usage identifier once
  - Write the property test asserting invoiced totals equal the period's recorded usage, and a test asserting no routing module references billing state
  - _Requirements: 30.1, 30.2, 30.3, 30.4, 30.5_

- [ ] 26. Implement benchmarking and routing evaluation
- [ ] 26.1 Implement the benchmark harness
  - Implement datasets for every domain of Master_Specification section 77, measure quality, success rate, cost, latency, context handling, and tool usage, record dataset version, model version, run timestamp, and sample count, and write measured scores to the registry
  - Exclude incomplete runs from reports and omit figures lacking a recorded run
  - _Requirements: 2.3, 2.4, 32.1, 32.2, 32.3, 32.4, 32.5_

- [ ] 26.2 Implement the evaluation harness and its CI gate
  - Implement the labeled routing dataset with every field of Master_Specification section 76, report routing accuracy, cost delta, and quality delta from executed cases only, and record developer feedback against request identifiers
  - Add a CI job running the harness on analyzer, routing, and scoring changes, failing below the configured accuracy threshold and naming regressed cases
  - _Requirements: 33.1, 33.2, 33.3, 33.4, 33.5, 33.6_

- [ ] 26.3 Replace the provisional weight presets with measured values
  - Tune the weight presets against harness output and update the manifest limitation entry recording that the values are now measured
  - _Requirements: 14.3, 33.2_

- [ ] 27. Implement containerization and Kubernetes deployment
- [ ] 27.1 Build the service images
  - Replace the placeholder Dockerfiles with distroless multi-stage builds running as non-root, and enable the image build workflow
  - _Requirements: 34.6_

- [ ] 27.2 Author the Kubernetes manifests
  - Implement base manifests and environment overlays for the consolidated workloads, declaring resource requests, limits, liveness and readiness probes, network policies, and secret references rather than inline values
  - _Requirements: 34.1, 34.2, 34.3, 34.4, 34.5_

- [ ] 28. Implement the Helm chart
  - Implement templates for every workload and expose every configuration surface of Master_Specification section 67, rendering valid manifests for all three value files with no credential in tracked values
  - Add CI chart linting and rendered-output schema validation
  - _Requirements: 35.1, 35.2, 35.3, 35.4, 35.5, 35.6_

- [ ] 29. Implement Terraform infrastructure
  - Implement a module for every area of Master_Specification section 68 and configurations for development, staging, and production, reading credentials from the execution environment
  - Add CI validate and format checks, and the property test asserting a plan against unchanged state reports zero changes
  - _Requirements: 36.1, 36.2, 36.3, 36.4, 36.5_

- [ ] 30. Complete the CI/CD pipeline
  - Implement lint, format, unit, integration, security scanning, dependency scanning, and build on pull requests; image build, image scan, and staging deployment on merge; end-to-end verification and explicit approval before production; digest-pinned production deployment; SBOM publication per released image
  - Ensure every gate names the failing check when it blocks
  - _Requirements: 37.1, 37.2, 37.3, 37.4, 37.5, 37.6, 37.7_

- [ ] 31. Implement high availability and autoscaling
  - Confirm request-path services hold no request-affecting local state, configure autoscaling on the signals of Master_Specification section 71, and remove unready replicas from load balancing
  - Write the replica-equivalence property test over a fixed routing input and a test asserting service continuity with one replica down
  - _Requirements: 38.1, 38.2, 38.3, 38.4, 38.5_

- [ ] 32. Implement disaster recovery
  - Implement scheduled PostgreSQL and configuration backups excluding transient caches, document RPO, RTO, frequency, and the restore procedure, and implement a restore verification script asserting startup and data integrity
  - Record the date and outcome of the most recent restore test
  - _Requirements: 39.1, 39.2, 39.3, 39.4, 39.5_

- [ ] 33. Implement the security, load, and end-to-end suites
- [ ] 33.1 Implement the security suite
  - Assert unauthenticated rejection on every protected path, cross-tenant read and write denial, permission enforcement, and absence of sensitive values in logs, errors, and telemetry
  - Document the threat model covering every boundary of Master_Specification section 83 and add the suite to CI
  - _Requirements: 40.1, 40.2, 40.3, 40.4, 40.5, 40.6_

- [ ] 33.2 Implement the load suite
  - Measure request rate, error rate, and p50, p95, and p99 routing-path latency isolated from provider latency, record the environment specification with every result, and fail when a latency budget is exceeded
  - _Requirements: 41.1, 41.2, 41.3, 41.4_

- [ ] 33.3 Implement the end-to-end suite
  - Exercise the full chain of Master_Specification section 141 from integration entry through telemetry arrival, asserting persisted routing decision, usage record, and cost record
  - Cover streaming with incremental chunk assertions, plus policy-blocked, fallback, and escalation paths, using fixture providers by default
  - _Requirements: 42.1, 42.2, 42.3, 42.4, 42.5_

- [ ] 34. Complete documentation and onboarding
- [ ] 34.1 Write audience documentation and generate the API reference
  - Write documentation for every audience of Master_Specification section 94, generate the API reference from the OpenAPI document, and state each component's known limitations from the manifest
  - Add CI jobs executing embedded examples and failing when a contract change leaves documentation unchanged
  - _Requirements: 43.1, 43.2, 43.3, 43.4, 43.5_

- [ ] 34.2 Implement onboarding and support traceability
  - Document every step of the onboarding flow of Master_Specification section 91 and cover it in the end-to-end suite from tenant creation to first routed request
  - Implement request traceability through the identifiers of section 93 without exposing message content to support personnel
  - Write the incident response and security incident procedures of sections 119 and 120
  - _Requirements: 44.1, 44.2, 44.3, 44.4_

- [ ] 35. Complete production readiness verification
  - Record Verification_Evidence or an outstanding reason for every item of the Production_DoD in the manifest
  - Implement `scripts/status/check_production_ready.py` declaring production readiness only when every item has passing evidence, and add it to CI
  - _Requirements: 44.5, 44.6_

- [ ] 36. Implement feature flags and extensibility verification
  - Implement feature flagging for new routing algorithms, providers, and integrations
  - Write tests proving a new provider, a new model, and a new IDE integration each require no routing engine source change
  - _Requirements: 45.3, 45.4, 45.5, 45.7_

## Notes

### How completion works

A task is complete only when its component satisfies all twelve Component_DoD items and its
named Verification_Evidence command exits zero. The hook from task 2.3 enforces this: on task
completion it re-runs the evidence, promotes the component to `implemented` only if the
evidence passes and the DoD is fully satisfied, and otherwise records `blocked` with the
captured failure output. The hook cannot manufacture green status, which is the point.

Until task 2 lands, status updates are manual. That is the only window where the ledger can
drift, and it is why task 2 sits second.

### Sequencing rules

- Do not begin a task before its dependencies in the graph above are `implemented`.
- Task 26.3 must complete before any external savings or routing-quality claim is made. Until
  then the weight presets remain provisional and the manifest carries that limitation.
- Task 27.1 replaces the deliberately non-buildable placeholder Dockerfiles. Do not enable the
  image build workflow before it.

### Scope boundaries

These tasks cover implementation only. The following appear in the source documents but are
not coding work and are excluded: legal and commercial documents (Master_Specification 122),
compliance certification audits (121), pricing and packaging decisions, and customer support
staffing. The repository prepares controls for SOC 2, ISO 27001, and GDPR under
`security/compliance/`, but certification is never claimed before an issued audit report
exists.

### Placeholder replacements owed

The scaffold intentionally contains non-functional artifacts. Each is replaced by a specific
task, and `docs/implementation-status.yaml` lists them as placeholders until then:

| Artifact | Replaced by |
| --- | --- |
| Service `Dockerfile`s (`FROM scratch`) | 27.1 |
| Helm templates (render nothing) | 28 |
| `docs/api/openapi.yaml` (`paths: {}`) | 4.4 |
| `make build` / `migrate` stubs (`lint` and `test` wired in 1.2) | 6.1, 27.1 |
| `LICENSE`, `CODEOWNERS`, `SECURITY.md` placeholder contacts | owner action, not a coding task |

### Requirements coverage

All 45 requirements are covered. Requirements 1 through 3 and 45 are satisfied by the
front-loaded infrastructure tasks rather than by a single feature task, because they constrain
every subsequent task rather than describing one component.
