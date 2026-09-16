# Requirements Document

## Introduction

This specification drives AgentRouter from its current state (a committed directory
scaffold with zero runnable application code) to the complete platform described in
the Master Engineering Specification (`README.md`, 141 sections).

The Master Engineering Specification is the source of truth. This document does not
restate it; it converts it into independently verifiable requirements ordered to match
the 46-step dependency sequence in README section 132, so that the task sheet derived
from this document doubles as the project's completion tracker.

Scope is the full 46 steps: foundation, the data plane, the control plane, integrations,
clients, enterprise governance, deployment, and production hardening.

### Decisions of record

These two decisions were unresolved in the source documents. They are recorded here as
defaults so requirements can be written concretely, and either can be changed by
amending this section and the affected requirements.

- **D1 — Delivery shape.** Phase 1 delivers the vertical slice of README section 141
  (IDE → client → auth → tenant → analyzer → policy → router → cost → provider →
  streaming response → telemetry) at production quality on a single host. Subsequent
  phases decompose that vertical into the distributed services of `Architecture.md`
  without changing the routing engine's interfaces. Rationale: README section 141
  states this explicitly, and it makes routing quality measurable earliest.
- **D2 — Implementation languages.** Python is the implementation language for the
  Analyzer, Routing_Engine, Policy_Engine, Cost_Engine, Model_Registry, Provider_Gateway,
  and MCP_Server. TypeScript/Node is the implementation language for the VS Code
  extension, the Dashboard, and the Admin_Console. Go is not used in Phase 1. Rationale:
  Python and Node are installed, Go is not; both have first-class provider and MCP SDKs.
  `technology.md` names Go for the Gateway; Requirement 45 governs any later migration,
  which the Provider_Adapter and transport boundaries confine to the gateway layer.
- **D3 — Policy precedence is monotonic narrowing.** A narrower scope in the
  Policy_Hierarchy may further restrict what a broader scope permits, and may never widen
  it. If any scope prohibits a model or provider, the resolved Policy_Decision prohibits
  it. Rationale: it makes Requirement 17's determinism and idempotence properties provable,
  and it matches Master_Specification section 128 ("never select a prohibited model").
  Consequence to accept knowingly: a team cannot be granted an exception to an
  organization-wide block; the organization scope must instead permit the model and
  restrict it at the scopes that should not have it. Changing this to support explicit
  overrides requires amending this decision and Requirement 17.
- **D4 — Cost is per request, not per attempt.** Recorded request cost is the sum across
  every provider attempt made for that request, including fallbacks and escalations.
  Savings are signed: a request that costs more than its Baseline_Model yields negative
  savings, which is reported as a negative value and never floored at zero. Rationale:
  Requirement 2 exists to prevent flattering numbers, and a floor at zero would
  systematically understate the cost of QUALITY_FIRST and escalation.
- **D5 — Routing determinism is scoped to Routing_Input.** Determinism and
  replica-equivalence claims hold for a fixed Routing_Input, which explicitly includes
  provider health, Circuit_Breaker state, and budget consumption. Rationale: those values
  legitimately change between calls and legitimately change the Candidate_Set, so an
  unscoped determinism claim would be untestable.
- **D6 — Migrations are reversible in development, forward-only in production.** Every
  migration ships a tested down-migration; the round-trip property is verified against a
  development database. Production applies migrations forward only. Rationale: reconciles
  Requirement 5 with `database/README.md`, and keeps rolling deployments safe.

## Glossary

- **AgentRouter**: The complete platform defined by the Master Engineering Specification.
- **Master_Specification**: The file `README.md` at the repository root, containing 141 numbered sections.
- **Implementation_Sequence**: The 46 dependency-ordered steps in Master_Specification section 132.
- **Component_DoD**: The 12-item per-component completion checklist in Master_Specification section 134.
- **Production_DoD**: The 29-item platform completion checklist in Master_Specification section 135.
- **Status_Manifest**: The file `docs/implementation-status.yaml`, the machine-readable record mapping each component to its status, implementation location, test location, Verification_Evidence command, and known limitations.
- **Status_Record**: The file `docs/IMPLEMENTATION_STATUS.md`, the human-readable status document generated from the Status_Manifest.
- **Status_Values**: The set {`not started`, `in progress`, `implemented`, `blocked`}.
- **Task_Sheet**: The file `tasks.md` in this specification directory.
- **Canonical_Request**: The single internal request structure of Master_Specification section 11.
- **Analyzer**: The component that produces the requirement description of Master_Specification section 14 without selecting a model.
- **Analysis_Result**: The Analyzer output object: task_type, complexity, reasoning_requirement, context_requirement, coding_requirement, tool_requirement, expected_output, confidence.
- **Task_Type**: A value from the classification set in Master_Specification section 15.
- **Complexity_Level**: One of LOW, MEDIUM, HIGH, CRITICAL (Master_Specification section 16).
- **Model_Registry**: The authoritative catalog of models, capabilities, pricing, and health (Master_Specification sections 12 and 13).
- **Model_Record**: One Model_Registry entry carrying every field listed in Master_Specification section 12.
- **Model_Lifecycle_State**: One of DISCOVERED, BENCHMARKING, APPROVED, ACTIVE, DEPRECATED, RETIRED (Master_Specification section 80).
- **Provider_Adapter**: The per-provider implementation of the interface in Master_Specification section 13.
- **Provider_Gateway**: The component that owns all Provider_Adapter instances and is the only component permitted to call provider APIs.
- **Routing_Engine**: The component that filters candidates and scores them to select a model (Master_Specification sections 17 through 21).
- **Candidate_Set**: The models remaining after every filter in Master_Specification section 20 has been applied.
- **Routing_Mode**: One of BALANCED, QUALITY_FIRST, COST_FIRST, LATENCY_FIRST, RELIABILITY_FIRST, POLICY_FIRST (Master_Specification section 19).
- **Routing_Decision**: The explainable decision object of Master_Specification section 21.
- **Score_Function**: The configurable weighted scoring function of Master_Specification section 18.
- **Weight_Preset**: The named set of Score_Function weights that defines one Routing_Mode.
- **Routing_Input**: The complete input tuple a routing invocation depends upon: the Canonical_Request, the Analysis_Result, the resolved Policy_Decision, the Model_Registry snapshot identifier (including per-model health, availability, and Circuit_Breaker state), the budget-consumption state, and the active Weight_Preset.
- **Context_Tier**: A named band of context-window requirement used to compare requests whose content differs in length.
- **Policy_Engine**: The component that evaluates policy and returns the decision object of Master_Specification section 28.
- **Policy_Decision**: A Policy_Engine result carrying allowed, reason, and restrictions.
- **Policy_Hierarchy**: The six ordered scopes of Master_Specification section 29: platform, organization, department, team, user, request constraints.
- **Cost_Engine**: The component that computes request cost and savings (Master_Specification sections 22 and 23).
- **Baseline_Model**: The configured model against which savings are measured (Master_Specification section 23).
- **Escalation_Engine**: The component implementing the retry-with-stronger-model flow of Master_Specification section 24.
- **Fallback_Engine**: The component implementing provider-failure recovery of Master_Specification section 25.
- **Circuit_Breaker**: The provider health state machine of Master_Specification section 26.
- **Redaction_Library**: The component that removes sensitive values from data before it leaves the process (Master_Specification section 36).
- **Sensitive_Value**: An API key, password, token, private key, credential, or PII item as defined by the Redaction_Library detectors.
- **Tenant**: An isolated customer scope owning users, teams, providers, models, policies, requests, usage, billing, and audit records (Master_Specification section 30).
- **Tenant_Context**: The authenticated tenant identity attached to a request, derived from credentials and never from client-supplied fields (Master_Specification section 85).
- **RBAC_System**: The role and permission system of Master_Specification section 32.
- **API_Gateway**: The public HTTP surface exposing the eleven paths of Master_Specification section 45.
- **MCP_Server**: The Model Context Protocol integration exposing the six tools of Master_Specification section 37.
- **Integration_Adapter**: The per-IDE abstraction with the capability profile of Master_Specification section 39.
- **Capability_Profile**: The declared set of supported capabilities for one Integration_Adapter.
- **Local_Client**: The developer-machine client of Master_Specification section 44.
- **CLI**: The command-line interface of Master_Specification section 48.
- **Dashboard**: The developer and administrator web interface of Master_Specification sections 50 through 52.
- **Admin_Console**: The administrative interface of Master_Specification section 105.
- **Event_Bus**: The asynchronous event distribution mechanism of Master_Specification sections 64 and 65.
- **Domain_Event**: One published message carrying a unique event identifier.
- **Audit_Log**: The append-only administrative event record of Master_Specification section 58.
- **Benchmark_Harness**: The model benchmarking system of Master_Specification section 77.
- **Evaluation_Harness**: The routing-quality regression system of Master_Specification sections 40 and 76.
- **Routing_Dataset**: The labeled regression dataset of Master_Specification section 76.
- **Helm_Chart**: The chart at `deployments/helm/agentrouter`.
- **CI_Pipeline**: The GitHub Actions workflows under `.github/workflows`.
- **Verification_Evidence**: A named, re-runnable automated check whose passing output substantiates a completion claim.

## Requirements

### Requirement 1: Completion Tracking Integrity

**User Story:** As the project owner, I want completion status to reflect only what actually works, so that I can trust the Status_Record and Task_Sheet as a picture of real progress.

#### Acceptance Criteria

1. THE Status_Manifest SHALL record, for every component named in Master_Specification section 6, a status drawn from Status_Values.
2. THE Status_Manifest SHALL record, for every component with status `implemented`, the implementation location, the test location, and the Verification_Evidence command.
3. THE Status_Manifest SHALL validate against a committed schema, and THE CI_Pipeline SHALL fail WHEN the Status_Manifest violates that schema.
4. THE repository SHALL generate the Status_Record from the Status_Manifest, and THE CI_Pipeline SHALL fail WHEN the committed Status_Record differs from the generated output.
5. WHEN a component's status changes, THE Status_Manifest SHALL be updated within the same commit that changes the component.
6. THE CI_Pipeline SHALL fail WHEN a component is recorded as `implemented` in the Status_Manifest and its named Verification_Evidence command is absent or exits non-zero.
7. IF a component satisfies fewer than all twelve items of the Component_DoD, THEN THE Status_Manifest SHALL record that component with a status other than `implemented`.
8. THE Status_Manifest SHALL list every known limitation of every component recorded as `implemented`.
9. THE Task_Sheet SHALL contain one task for each of the 46 steps of the Implementation_Sequence or for a subdivision of one of those steps.
10. WHERE a task in the Task_Sheet is marked complete, THE Task_Sheet SHALL reference the Verification_Evidence that substantiates completion.
11. WHEN a Task_Sheet task reaches completed status, THE repository SHALL update the Status_Manifest entry for that task's component and SHALL regenerate the Status_Record.

### Requirement 2: Anti-Fabrication Controls

**User Story:** As the project owner, I want the system and its documentation to state only claims that are substantiated, so that customer-facing material survives enterprise scrutiny.

#### Acceptance Criteria

1. THE CI_Pipeline SHALL fail WHEN a source file whose component is recorded as `implemented` in the Status_Manifest contains a placeholder marker from the configured marker set.
2. IF a savings figure is reported for a request, THEN THE Cost_Engine SHALL derive that figure from the recorded actual cost and the recorded Baseline_Model cost of the same request.
3. THE Benchmark_Harness SHALL record, for every published quality or latency figure, the dataset identifier, the model identifier, the run timestamp, and the sample count.
4. IF a benchmark figure lacks a recorded run, THEN THE Benchmark_Harness SHALL exclude that figure from generated reports.
5. WHERE documentation describes an IDE integration capability, THE documentation SHALL name the passing automated test that exercises that capability against the host's officially supported mechanism.
6. THE repository SHALL describe compliance frameworks as prepared controls and SHALL attribute certification status only to a named issued audit report.
7. WHEN a provider request fails, THE API_Gateway SHALL return a normalized error from the set in Master_Specification section 47 and SHALL set the request lifecycle state to a failure state from Master_Specification section 10.
8. THE Status_Manifest SHALL describe every non-buildable placeholder artifact in the repository as a placeholder.

### Requirement 3: Repository Foundation and Development Environment

**User Story:** As the sole engineer, I want a reproducible repository and local environment, so that every later phase starts from a known-good state. (Implementation_Sequence steps 01 and 02)

#### Acceptance Criteria

1. THE repository SHALL provide a structure generator that produces the target tree of `Repository Structure.md` and SHALL leave the tree unchanged on a second consecutive run.
2. THE repository SHALL provide a structure validator that verifies the presence of every declared path, the parseability of every tracked JSON and YAML file, and the absence of tracked credential files.
3. WHEN a developer runs the documented environment setup command on a machine with Python 3.13 and Node 20 present, THE development environment SHALL install every dependency required to run the repository's test suites.
4. THE local environment SHALL start PostgreSQL and Redis and SHALL report both as reachable through a documented health command.
5. THE CI_Pipeline SHALL execute the structure validator on every pull request.
6. THE repository SHALL declare a single documented command that runs formatting, linting, type checking, and unit tests.

### Requirement 4: Shared Types and API Contracts

**User Story:** As a developer of any AgentRouter component, I want one authoritative contract definition, so that services and SDKs cannot drift apart. (Implementation_Sequence step 03)

#### Acceptance Criteria

1. THE repository SHALL define the Canonical_Request, the Analysis_Result, the Routing_Decision, the Policy_Decision, and the normalized error set as versioned schemas in `packages/api-contracts`.
2. THE file `docs/api/openapi.yaml` SHALL declare an operation for every path listed in Master_Specification section 45.
3. THE OpenAPI document SHALL validate against the OpenAPI specification version it declares.
4. WHEN a contract schema changes, THE CI_Pipeline SHALL regenerate the derived language types and SHALL fail IF the committed generated types differ from the regenerated types.
5. FOR ALL Canonical_Request values, serializing to the wire format and deserializing SHALL produce a value equal to the original (round-trip property).
6. FOR ALL Analysis_Result, Routing_Decision, and Policy_Decision values, serializing and deserializing SHALL produce a value equal to the original (round-trip property).
7. IF a payload violates its schema, THEN THE validating component SHALL reject the payload and SHALL identify the violating field path.

### Requirement 5: Database Foundation

**User Story:** As a platform operator, I want a migrated, tenant-scoped schema, so that data structure changes are safe and reviewable. (Implementation_Sequence step 04)

#### Acceptance Criteria

1. THE database SHALL define each of the 25 core tables listed in Master_Specification section 61.
2. THE database SHALL apply every schema change through a versioned migration.
3. WHEN the migration suite runs against an empty database, THE database SHALL reach the current schema version and SHALL report zero pending migrations.
4. THE repository SHALL provide a tested down-migration for every migration, and FOR ALL migrations applied against a development database, applying the migration then reverting it SHALL restore the prior schema version (round-trip property, decision D6).
5. THE production migration runner SHALL apply migrations in the forward direction only (decision D6).
6. THE database SHALL constrain every table holding tenant-owned data with a non-null tenant identifier column.
7. THE database SHALL provide a seed dataset sufficient to run the integration test suite.
8. IF two migrations declare the same version identifier, THEN THE migration runner SHALL refuse to run and SHALL name the conflicting migrations.

### Requirement 6: Authentication

**User Story:** As an enterprise administrator, I want standards-based authentication, so that AgentRouter fits our identity infrastructure. (Implementation_Sequence step 05)

#### Acceptance Criteria

1. THE API_Gateway SHALL authenticate requests presenting an API key, an OIDC token, or a service-account credential.
2. THE API_Gateway SHALL store API keys as one-way hashes and SHALL return the key material only in the response that creates the key.
3. WHEN an API key reaches its expiration timestamp, THE API_Gateway SHALL reject requests presenting that key with AUTHENTICATION_ERROR.
4. WHEN an administrator revokes an API key, THE API_Gateway SHALL reject subsequent requests presenting that key with AUTHENTICATION_ERROR.
5. IF a request presents no credential or an unrecognized credential, THEN THE API_Gateway SHALL return AUTHENTICATION_ERROR and SHALL omit the presented credential material from the response and from logs.
6. THE API_Gateway SHALL record an Audit_Log entry for each API key creation, rotation, and revocation.
7. WHERE a Tenant has SAML or OIDC single sign-on configured, THE API_Gateway SHALL authenticate that Tenant's interactive users through the configured identity provider.

### Requirement 7: Multi-Tenancy and Tenant Isolation

**User Story:** As a security administrator, I want tenant boundaries enforced at every data access, so that one customer can never observe another customer's data. (Implementation_Sequence step 06)

#### Acceptance Criteria

1. THE API_Gateway SHALL derive Tenant_Context from the authenticated credential.
2. IF a request body or header supplies a tenant identifier that differs from the Tenant_Context derived from the credential, THEN THE API_Gateway SHALL reject the request with an authorization error.
3. FOR ALL data-access operations on tenant-owned tables, THE data-access layer SHALL apply the Tenant_Context tenant identifier as a query predicate (invariant).
4. FOR ALL pairs of distinct Tenants, a read issued under one Tenant_Context SHALL return zero records owned by the other Tenant (isolation property).
5. WHEN a data-access operation on a tenant-owned table executes without Tenant_Context, THE data-access layer SHALL raise an error and SHALL execute no query.
6. THE Event_Bus SHALL carry the originating tenant identifier on every Domain_Event describing tenant-owned data.

### Requirement 8: Role-Based Access Control

**User Story:** As an organization administrator, I want granular roles, so that developers, auditors, and finance staff see only what their role permits. (Implementation_Sequence step 07)

#### Acceptance Criteria

1. THE RBAC_System SHALL define each role listed in Master_Specification section 32.
2. THE RBAC_System SHALL express every authorization decision as a check of a named permission against the authenticated principal's granted permissions.
3. WHEN a principal lacking the required permission requests a protected operation, THE API_Gateway SHALL return an authorization error and SHALL perform no part of the operation.
4. FOR ALL protected API operations, THE API_Gateway SHALL evaluate authorization on the server irrespective of any client-supplied capability claim.
5. THE API_Gateway SHALL restrict a principal holding only the DEVELOPER role to usage records attributed to that principal.
6. WHEN a principal's role assignment changes, THE RBAC_System SHALL record an Audit_Log entry naming the principal, the prior roles, and the new roles.
7. WHERE an operation modifies policies, providers, models, or credentials, THE RBAC_System SHALL require an administrative permission.

### Requirement 9: Model Registry

**User Story:** As an organization administrator, I want one authoritative model catalog, so that capability and pricing data is never duplicated in service code. (Implementation_Sequence step 08)

#### Acceptance Criteria

1. THE Model_Registry SHALL store every field listed in Master_Specification section 12 for each Model_Record.
2. THE Model_Registry SHALL be the only source of model pricing and model capability values consumed by other components.
3. THE CI_Pipeline SHALL fail WHEN a source file outside the Model_Registry and outside the declared test-fixture and seed-data paths contains a literal model price or context-window value for a registered model.
4. THE Model_Registry SHALL assign each Model_Record exactly one Model_Lifecycle_State.
5. WHEN a Model_Record transitions between Model_Lifecycle_States, THE Model_Registry SHALL permit only the transitions defined in Master_Specification section 80 and SHALL record an Audit_Log entry.
6. WHILE a Model_Record holds the DEPRECATED or RETIRED state, THE Routing_Engine SHALL exclude that model from the Candidate_Set.
7. THE Model_Registry SHALL expose current availability, latency, and error-rate values for each Model_Record.
8. IF a Model_Record omits a required capability or pricing field, THEN THE Model_Registry SHALL reject the record and SHALL name the missing field.

### Requirement 10: Provider Abstraction and Adapters

**User Story:** As a developer, I want every provider behind one interface, so that a provider API change never reaches the routing engine. (Implementation_Sequence steps 09 and 10)

#### Acceptance Criteria

1. THE Provider_Gateway SHALL define the Provider_Adapter interface with the operations listed in Master_Specification section 13.
2. THE Provider_Gateway SHALL implement a Provider_Adapter for OpenAI, for Anthropic, for Google, and for OpenAI-compatible endpoints.
3. THE Routing_Engine SHALL contain no provider-specific identifier or provider-specific branch.
4. WHEN a Provider_Adapter receives a provider error, THE Provider_Adapter SHALL return a normalized error from the set in Master_Specification section 47.
5. FOR ALL Provider_Adapter implementations, THE contract test suite SHALL execute the same set of assertions against each adapter (model-based property).
6. THE Provider_Gateway SHALL read provider credentials from the configured secret source at request time and SHALL omit credential values from logs, errors, and telemetry.
7. WHERE a provider supports streaming, THE Provider_Adapter SHALL forward response chunks without accumulating the complete response before the first chunk is emitted.
8. WHEN a request would exceed a model's context window, THE Provider_Adapter SHALL return CONTEXT_TOO_LARGE before contacting the provider.

### Requirement 11: Canonical Request Normalization

**User Story:** As a developer, I want every entry point to produce one internal request shape, so that adding an integration requires no core change. (Implementation_Sequence step 11)

#### Acceptance Criteria

1. THE normalization layer SHALL convert an input from the API_Gateway, the MCP_Server, the CLI, an SDK, or an Integration_Adapter into a Canonical_Request.
2. THE normalization layer SHALL assign each Canonical_Request a unique request identifier.
3. FOR ALL supported entry points presenting equivalent input, THE normalization layer SHALL produce Canonical_Request values that are equal except for the request identifier and receipt timestamp (confluence property).
4. THE normalization layer SHALL set the Canonical_Request tenant, user, and team fields from Tenant_Context rather than from the input payload.
5. IF an input omits a field required by the Canonical_Request schema, THEN THE normalization layer SHALL return INVALID_REQUEST naming the missing field.
6. THE normalization layer SHALL advance each request through the lifecycle states of Master_Specification section 10 and SHALL record each transition against the request identifier.

### Requirement 12: API Gateway

**User Story:** As an API consumer, I want a documented, versioned HTTP surface, so that I can integrate without reading service internals. (Implementation_Sequence step 12)

#### Acceptance Criteria

1. THE API_Gateway SHALL serve every path listed in Master_Specification section 45 under the `/v1` prefix.
2. THE API_Gateway SHALL serve responses conforming to the schemas declared in `docs/api/openapi.yaml`.
3. WHEN a client sets the streaming flag on a generation request, THE API_Gateway SHALL forward provider response chunks to the client as they are received.
4. THE API_Gateway SHALL enforce rate limits at each scope listed in Master_Specification section 27.
5. WHEN a request exceeds an applicable rate limit, THE API_Gateway SHALL return RATE_LIMIT and SHALL state the scope that was exceeded.
6. THE API_Gateway SHALL attach the request identifier and the trace identifier to every response.
7. IF an unhandled error occurs while serving a request, THEN THE API_Gateway SHALL return UNKNOWN with the request identifier and SHALL exclude internal stack detail from the response body.

### Requirement 13: Request Analyzer

**User Story:** As a developer, I want the analyzer to describe what a task requires, so that routing decisions rest on task requirements rather than prompt size. (Implementation_Sequence step 13)

#### Acceptance Criteria

1. THE Analyzer SHALL produce an Analysis_Result containing every field listed in Master_Specification section 14 for each Canonical_Request.
2. THE Analyzer SHALL assign each Analysis_Result a Task_Type from the set in Master_Specification section 15 and a Complexity_Level from the set in Master_Specification section 16.
3. THE Analyzer SHALL derive Complexity_Level from task type, requested operation count, reasoning requirement, context requirement, tool requirement, expected output, ambiguity, and dependencies.
4. FOR ALL pairs of Canonical_Requests that differ only in the character length of message content AND that fall in the same Context_Tier AND that carry the same task type, requested operation count, tool requirement, and expected output, THE Analyzer SHALL assign the same Complexity_Level (invariant, per `prompt complexity.md`).
5. THE Analyzer SHALL treat message character length as a signal only through Context_Tier and SHALL derive no other Complexity_Level contribution from character length alone.
6. THE Analyzer SHALL emit a confidence value in the closed interval from zero to one.
7. THE Analyzer SHALL produce an Analysis_Result that names no model and no provider (invariant).
8. THE Analyzer SHALL accept a new Task_Type through configuration without modification to Analyzer source code.
9. IF the Analyzer cannot classify a request, THEN THE Analyzer SHALL assign the GENERAL Task_Type and SHALL report a confidence value below the configured confidence floor.

### Requirement 14: Routing Engine

**User Story:** As an organization administrator, I want the least expensive capable model chosen under my constraints, so that spend falls without quality loss. (Implementation_Sequence step 14)

#### Acceptance Criteria

1. THE Routing_Engine SHALL construct the Candidate_Set by applying the capability, context, policy, region, availability, and budget filters of Master_Specification section 20.
2. THE Routing_Engine SHALL score each member of the Candidate_Set with the Score_Function of Master_Specification section 18.
3. THE Routing_Engine SHALL read every Score_Function weight from configuration.
4. THE Routing_Engine SHALL support every Routing_Mode listed in Master_Specification section 19, and SHALL define each Routing_Mode as a named Weight_Preset rather than as an independent selection rule.
5. FOR ALL routing invocations, THE selected model SHALL be a member of the Candidate_Set (invariant).
6. FOR ALL routing invocations, THE selected model SHALL satisfy every capability named as required in the Analysis_Result (invariant).
7. FOR ALL routing invocations, THE selected model SHALL have a context window at least the size of the request's context requirement (invariant).
8. FOR ALL routing invocations under a Policy_Decision that prohibits a model or provider, THE selected model SHALL be neither a prohibited model nor a model of a prohibited provider (invariant).
9. FOR ALL routing invocations, THE selected model SHALL hold the maximum score among the Candidate_Set under the active Weight_Preset, with ties broken by a documented deterministic rule (invariant, single selection rule).
10. THE COST_FIRST Weight_Preset SHALL assign cost the sole non-zero weight, so that selection under COST_FIRST yields the lowest-estimated-cost member of the Candidate_Set.
11. IF the Candidate_Set is empty, THEN THE Routing_Engine SHALL return MODEL_UNAVAILABLE stating the filter that removed the last candidate and SHALL dispatch no provider request.
12. FOR ALL pairs of routing invocations sharing one Routing_Input, THE Routing_Engine SHALL select the same model (determinism property, scoped per decision D5).

### Requirement 15: Explainable Routing Decision

**User Story:** As an administrator investigating routing behavior, I want each decision explained, so that I can audit why a model was chosen. (Master_Specification sections 21, 53, and 110)

#### Acceptance Criteria

1. THE Routing_Engine SHALL emit a Routing_Decision for every routing invocation.
2. THE Routing_Decision SHALL name the selected model, the reasons for selection, the confidence value, the estimated cost, and the considered alternatives.
3. THE Routing_Decision SHALL record every rejected model together with the filter that rejected it.
4. THE Routing_Decision SHALL record the active Routing_Mode, the applied weights, and each Policy_Decision consulted.
5. THE API_Gateway SHALL persist each Routing_Decision against its request identifier.
6. WHERE a Tenant enables developer transparency, THE API_Gateway SHALL return the Routing_Decision fields permitted by that Tenant's configuration.

### Requirement 16: Cost Engine

**User Story:** As a FinOps owner, I want costs and savings computed from registry pricing, so that reported figures reconcile with provider invoices. (Implementation_Sequence step 15)

#### Acceptance Criteria

1. THE Cost_Engine SHALL compute request cost as the sum, across every provider attempt made for that request including fallback and escalation attempts, of the input, output, and cached token costs using the Model_Registry pricing for the model serving each attempt (decision D4).
2. FOR ALL completed requests, THE recorded cost SHALL equal the sum over attempts of the token counts multiplied by the corresponding Model_Registry prices for the model of that attempt (consistency property).
3. THE Cost_Engine SHALL compute savings as the configured Baseline_Model cost of the same request minus the recorded actual cost, and SHALL report the result as a signed value.
4. WHERE the recorded actual cost exceeds the Baseline_Model cost, THE Cost_Engine SHALL report negative savings and SHALL NOT floor the reported value at zero (decision D4).
5. THE Dashboard and every report SHALL present negative savings as a negative value rather than as zero or as absent.
6. WHEN the served model is the Baseline_Model and no additional attempt occurred, THE Cost_Engine SHALL report savings of zero.
7. THE Cost_Engine SHALL support the per-provider pricing structures declared in the Model_Registry.
8. THE Cost_Engine SHALL label every forecast value as an estimate and SHALL record the historical window the forecast was derived from.
9. IF Model_Registry pricing for a served model is absent, THEN THE Cost_Engine SHALL record the request cost as unavailable and SHALL raise a pricing-gap notification.

### Requirement 17: Policy Engine

**User Story:** As a security administrator, I want centralized policy with deterministic precedence, so that governance is predictable and provable. (Implementation_Sequence step 16)

#### Acceptance Criteria

1. THE Policy_Engine SHALL evaluate each policy field listed in Master_Specification section 28.
2. THE Policy_Engine SHALL return a Policy_Decision carrying allowed, reason, and restrictions.
3. THE Policy_Engine SHALL resolve policy across the six scopes of the Policy_Hierarchy by monotonic narrowing, in which the Policy_Hierarchy order defines the sequence in which restrictions accumulate and a narrower scope may restrict but never widen what a broader scope permits (decision D3).
4. FOR ALL policy sets, THE Policy_Engine SHALL resolve a given request to the same Policy_Decision on every evaluation (determinism property).
5. FOR ALL policy sets in which any scope prohibits a model, THE resolved Policy_Decision SHALL prohibit that model (precedence invariant).
6. FOR ALL policy evaluations, applying the resolution to an already-resolved policy set SHALL produce the same Policy_Decision (idempotence property).
7. WHEN a request violates a policy, THE API_Gateway SHALL set the lifecycle state to POLICY_BLOCKED, SHALL return the violated policy in the response, and SHALL dispatch no provider request.
8. WHERE a Tenant restricts data residency by region, THE Routing_Engine SHALL exclude models outside the permitted regions from the Candidate_Set.
9. THE Policy_Engine SHALL record an Audit_Log entry for every policy creation, modification, and deletion.

### Requirement 18: Escalation Engine

**User Story:** As a developer, I want an inadequate cheap-model result retried on a stronger model, so that cost optimization does not degrade outcomes. (Implementation_Sequence step 17)

#### Acceptance Criteria

1. THE Escalation_Engine SHALL evaluate each completed response against the configured escalation criteria of Master_Specification section 24.
2. WHEN an evaluation fails and escalation is enabled, THE Escalation_Engine SHALL re-route the request restricted to models scoring higher on the required capability than the model just used.
3. FOR ALL escalations, THE escalated model SHALL satisfy the same Policy_Decision as the original selection (invariant).
4. THE Escalation_Engine SHALL record every escalation attempt against the originating request identifier, including the evaluation result that triggered it.
5. WHILE escalation is disabled for a Tenant, THE Escalation_Engine SHALL return the original response without re-routing.
6. THE Escalation_Engine SHALL stop escalating at the configured attempt limit and SHALL return the best obtained response together with the escalation history.
7. THE Cost_Engine SHALL include the cost of every escalation attempt in the recorded request cost.

### Requirement 19: Fallback Engine and Circuit Breaker

**User Story:** As a platform operator, I want provider failures absorbed within policy, so that a single provider outage does not fail requests. (Implementation_Sequence step 18)

#### Acceptance Criteria

1. WHEN a provider request fails or times out, THE Fallback_Engine SHALL select an alternative model from the current Candidate_Set.
2. FOR ALL fallback selections, THE alternative model SHALL satisfy the active Policy_Decision, the region constraints, the capability requirements, and the budget constraints (invariant).
3. THE Circuit_Breaker SHALL transition provider health through the closed, open, and half-open states of Master_Specification section 26 using configured thresholds.
4. WHILE a provider's Circuit_Breaker is open, THE Routing_Engine SHALL exclude that provider's models from the Candidate_Set.
5. WHEN a half-open health probe succeeds, THE Circuit_Breaker SHALL close the circuit for that provider.
6. IF no policy-compliant alternative exists, THEN THE API_Gateway SHALL return the normalized provider error and SHALL set the lifecycle state to FAILED.
7. THE Fallback_Engine SHALL record every fallback attempt against the originating request identifier.

### Requirement 20: Security, Privacy, and Redaction

**User Story:** As a security administrator, I want secrets and customer content kept out of logs and storage, so that using AgentRouter introduces no data exposure. (Implementation_Sequence step 19)

#### Acceptance Criteria

1. THE Redaction_Library SHALL detect each Sensitive_Value category listed in Master_Specification section 36.
2. FOR ALL values passed to the logging layer, THE emitted log record SHALL contain no substring matching a Sensitive_Value detector, except for values matching the declared allow-list of non-sensitive structured identifiers such as request identifiers, trace identifiers, tenant identifiers, and model identifiers (redaction property).
3. FOR ALL redaction invocations, redacting an already-redacted value SHALL produce the same value (idempotence property).
4. THE logging layer SHALL omit message content from log records unless the Tenant has explicitly enabled content logging.
5. THE platform SHALL persist request metadata by default and SHALL persist full conversation content only where a Tenant has explicitly enabled conversation retention.
6. THE platform SHALL read provider credentials and platform secrets from the configured secret source and SHALL store no secret value in tracked repository files.
7. THE CI_Pipeline SHALL fail WHEN a tracked file matches a configured secret-detection pattern.
8. WHEN a Tenant's retention period elapses for a stored record, THE platform SHALL delete that record.
9. THE platform SHALL encrypt data in transit using TLS at every network boundary it controls.

### Requirement 21: Observability

**User Story:** As a platform operator, I want metrics, logs, and traces spanning the request path, so that I can diagnose production behavior. (Implementation_Sequence step 20)

#### Acceptance Criteria

1. THE platform SHALL emit every metric listed in Master_Specification section 59.
2. THE platform SHALL emit OpenTelemetry-compatible spans covering the gateway, analyzer, policy, router, and provider stages of each request.
3. THE platform SHALL carry one trace identifier across every span of a single request.
4. THE platform SHALL emit structured log records carrying the request identifier, the tenant identifier, and the lifecycle state.
5. THE platform SHALL expose a health endpoint per service reporting the reachability of that service's dependencies.
6. THE observability configuration SHALL define an alert rule for each condition listed in Master_Specification section 57.

### Requirement 22: Event System

**User Story:** As a platform engineer, I want side effects consumed asynchronously, so that analytics, billing, and audit stay off the request path. (Implementation_Sequence step 21)

#### Acceptance Criteria

1. THE Event_Bus SHALL publish every event listed in Master_Specification section 64.
2. THE Event_Bus SHALL assign each Domain_Event a unique event identifier.
3. FOR ALL Domain_Events, processing the same event identifier more than once SHALL produce the same consumer state as processing it once (idempotence property).
4. THE request path SHALL complete a response without waiting for analytics, billing, notification, or audit consumers.
5. IF a consumer fails to process a Domain_Event, THEN THE Event_Bus SHALL retain the event for retry and SHALL record the failure.
6. FOR ALL Domain_Events, serializing to the bus format and deserializing SHALL produce a value equal to the original (round-trip property).

### Requirement 23: Analytics and FinOps

**User Story:** As a FinOps owner, I want usage and cost broken down across our organization, so that I can attribute and forecast AI spend. (Implementation_Sequence step 22)

#### Acceptance Criteria

1. THE analytics component SHALL aggregate usage and cost by each dimension listed in Master_Specification section 54.
2. THE analytics component SHALL report each figure listed in Master_Specification section 55.
3. FOR ALL aggregation periods, THE sum of the per-dimension cost aggregates SHALL equal the sum of the underlying recorded request costs (consistency property).
4. THE analytics component SHALL report the routing metrics listed in Master_Specification section 78.
5. WHEN a budget crosses a configured threshold from Master_Specification section 56, THE platform SHALL execute that threshold's configured action.
6. WHEN usage or cost deviates from the configured anomaly bounds, THE platform SHALL notify the Tenant's administrators.
7. THE analytics component SHALL restrict each query result to the Tenant_Context of the requesting principal.

### Requirement 24: MCP Server

**User Story:** As an AI agent host, I want AgentRouter exposed over MCP, so that agents can use routing through a standard mechanism. (Implementation_Sequence step 23)

#### Acceptance Criteria

1. THE MCP_Server SHALL expose each of the six tools listed in Master_Specification section 37.
2. THE MCP_Server SHALL conform to the MCP specification version it declares and SHALL state that version in its documentation.
3. THE MCP_Server SHALL authenticate every connection and SHALL attach Tenant_Context before invoking any tool.
4. FOR ALL MCP tool invocations, THE resulting Policy_Decision SHALL be identical to the Policy_Decision for the equivalent API_Gateway request (equivalence property).
5. THE MCP_Server SHALL delegate every routing decision to the Routing_Engine and SHALL contain no scoring or candidate-filtering logic.
6. THE MCP_Server SHALL enforce per-tool permissions, rate limits, and audit logging.
7. IF an MCP client requests a tool the connected principal lacks permission for, THEN THE MCP_Server SHALL return an authorization error and SHALL execute no part of the tool.

### Requirement 25: Local Client

**User Story:** As a developer, I want a local client managing credentials and connectivity, so that my IDE reaches AgentRouter without handling provider keys. (Implementation_Sequence step 24)

#### Acceptance Criteria

1. THE Local_Client SHALL perform login, configuration, connection management, MCP hosting, and diagnostics.
2. THE Local_Client SHALL store credentials in the operating system's secure credential store.
3. THE Local_Client SHALL exclude provider credentials from its configuration files and its log output.
4. WHEN the configured AgentRouter endpoint is unreachable, THE Local_Client SHALL report the failing check and the remediation step.
5. THE Local_Client SHALL report its version and the negotiated API version through a documented status command.

### Requirement 26: CLI

**User Story:** As a developer or operator, I want scriptable command-line access, so that I can automate and troubleshoot. (Implementation_Sequence step 25)

#### Acceptance Criteria

1. THE CLI SHALL implement every command listed in Master_Specification section 48.
2. THE CLI SHALL emit machine-readable output when the machine-readable output flag is set.
3. THE CLI SHALL return a zero exit status on success and a documented non-zero exit status on each failure category.
4. THE diagnose command SHALL check each item listed in Master_Specification section 92 and SHALL report a remediation step for each failing check.
5. FOR ALL CLI commands producing machine-readable output, THE output SHALL validate against that command's declared schema (round-trip property).

### Requirement 27: SDKs

**User Story:** As an application developer, I want SDKs in my language, so that I can call AgentRouter without hand-writing HTTP code. (Implementation_Sequence step 26)

#### Acceptance Criteria

1. THE repository SHALL provide a TypeScript SDK, a Python SDK, and a Go SDK exposing the operations listed in Master_Specification section 49.
2. THE SDKs SHALL derive their request and response types from the contracts in `packages/api-contracts`.
3. FOR ALL SDK implementations, THE shared conformance suite SHALL execute the same set of assertions against each SDK (model-based property).
4. WHEN the API returns a normalized error, THE SDK SHALL raise a typed error corresponding to that normalized error category.
5. WHERE the API supports streaming, THE SDK SHALL expose an incremental streaming interface.

### Requirement 28: IDE Integrations

**User Story:** As a developer, I want AgentRouter in the IDE I already use, through mechanisms the IDE officially supports. (Implementation_Sequence step 27)

#### Acceptance Criteria

1. THE repository SHALL define an Integration_Adapter interface exposing the capability flags listed in Master_Specification section 39.
2. THE repository SHALL declare a Capability_Profile for each of VS Code, Kiro, Cursor, Claude Code, and JetBrains.
3. THE Integration_Adapter implementations SHALL use only the host's officially documented extension, provider, or MCP mechanisms.
4. WHERE a host exposes no mechanism for a capability, THE Capability_Profile SHALL declare that capability unsupported and THE documentation SHALL state the limitation.
5. THE repository SHALL claim an integration capability as supported only where an automated test exercises that capability and passes.
6. THE Routing_Engine SHALL contain no reference to any specific IDE or Integration_Adapter (invariant).

### Requirement 29: Dashboard and Admin Console

**User Story:** As an administrator or developer, I want a web interface for usage, cost, routing, and governance, so that I can operate AgentRouter without the API. (Implementation_Sequence steps 28 and 29)

#### Acceptance Criteria

1. THE Dashboard SHALL present every section listed in Master_Specification section 50.
2. THE Dashboard SHALL present the developer views of Master_Specification section 51 and the administrator views of Master_Specification section 52.
3. THE Admin_Console SHALL manage every area listed in Master_Specification section 105.
4. FOR ALL privileged Dashboard and Admin_Console actions, THE backend SHALL authorize the action irrespective of the interface state (invariant).
5. THE Dashboard SHALL reach data only through the control-plane API.
6. THE Dashboard SHALL present a routing investigation view showing the Routing_Decision fields listed in Master_Specification section 53.
7. THE Dashboard SHALL meet WCAG 2.1 Level AA success criteria that automated accessibility tooling can verify.

### Requirement 30: Billing

**User Story:** As a business operator, I want subscription and usage billing isolated from routing, so that commercial logic never affects request handling. (Implementation_Sequence step 30)

#### Acceptance Criteria

1. THE billing component SHALL manage each item listed in Master_Specification section 90.
2. THE billing component SHALL derive usage charges from recorded usage records rather than from live routing calls.
3. FOR ALL billing periods, THE invoiced usage total SHALL equal the sum of that period's recorded usage records for that Tenant (consistency property).
4. THE Routing_Engine SHALL contain no reference to billing state (invariant).
5. WHEN a usage record arrives more than once with the same identifier, THE billing component SHALL charge it once (idempotence property).

### Requirement 31: Notifications

**User Story:** As an administrator, I want to be notified of budget, policy, and reliability events on the channels we use. (Implementation_Sequence step 31)

#### Acceptance Criteria

1. THE notification component SHALL deliver to each channel listed in Master_Specification section 57.
2. THE notification component SHALL emit a notification for each event listed in Master_Specification section 57.
3. THE notification component SHALL exclude Sensitive_Values and message content from notification payloads.
4. IF a channel delivery fails, THEN THE notification component SHALL retry within the configured retry budget and SHALL record the final delivery outcome.
5. FOR ALL notification events, delivering the same event identifier more than once SHALL produce one delivered notification per channel (idempotence property).

### Requirement 32: Benchmarking

**User Story:** As the product owner, I want model quality measured on real datasets, so that routing weights rest on evidence. (Implementation_Sequence step 32)

#### Acceptance Criteria

1. THE Benchmark_Harness SHALL provide a dataset for each domain listed in Master_Specification section 77.
2. THE Benchmark_Harness SHALL measure quality, success rate, cost, latency, context handling, and tool usage per model.
3. THE Benchmark_Harness SHALL record the dataset version, the model version, and the run timestamp for every result.
4. THE Benchmark_Harness SHALL write measured capability scores to the Model_Registry through the registry's write interface.
5. IF a benchmark run fails partway, THEN THE Benchmark_Harness SHALL mark the run incomplete and SHALL exclude the run from reports.

### Requirement 33: Routing Evaluation

**User Story:** As the product owner, I want routing regression-tested against labeled cases, so that a scoring change cannot silently degrade selection quality. (Implementation_Sequence step 33)

#### Acceptance Criteria

1. THE Routing_Dataset SHALL carry every field listed in Master_Specification section 76 for each case.
2. THE Evaluation_Harness SHALL report routing accuracy, cost delta, and quality delta against the Routing_Dataset.
3. THE CI_Pipeline SHALL run the Evaluation_Harness on every change to analyzer, routing, or scoring source files.
4. WHEN measured routing accuracy falls below the configured threshold, THE CI_Pipeline SHALL fail and SHALL name the regressed cases.
5. THE Evaluation_Harness SHALL report measured figures only and SHALL derive no reported figure from an unexecuted case.
6. THE platform SHALL record developer feedback values from Master_Specification section 79 against the originating request identifier.

### Requirement 34: Kubernetes Deployment

**User Story:** As a platform operator, I want the platform deployable to Kubernetes, so that it runs in our production environment. (Implementation_Sequence step 34)

#### Acceptance Criteria

1. THE repository SHALL provide Kubernetes manifests deploying the workloads listed in Master_Specification section 32 of `Architecture.md`.
2. THE manifests SHALL declare resource requests, resource limits, liveness probes, and readiness probes for every workload.
3. THE manifests SHALL declare network policies restricting traffic to the required paths.
4. WHEN the manifests are applied to a conformant cluster with the required secrets present, THE platform SHALL report every workload ready.
5. THE manifests SHALL read every secret from a Kubernetes secret reference rather than an inline value.
6. THE container images SHALL run as a non-root user and SHALL be built from a minimal base image.

### Requirement 35: Helm Chart

**User Story:** As a self-hosting customer, I want a production Helm chart, so that I can install AgentRouter in my own cluster. (Implementation_Sequence step 35)

#### Acceptance Criteria

1. THE Helm_Chart SHALL template every workload required to serve requests.
2. THE Helm_Chart SHALL expose every configuration surface listed in Master_Specification section 67.
3. THE Helm_Chart SHALL render valid Kubernetes manifests for the development, staging, and production value files.
4. WHEN the Helm_Chart is installed against a conformant cluster, THE platform SHALL serve a routed request end to end.
5. THE CI_Pipeline SHALL lint the Helm_Chart and SHALL validate rendered output against the Kubernetes schema.
6. THE Helm_Chart SHALL contain no provider credential value and no customer-specific value in tracked value files.

### Requirement 36: Terraform Infrastructure

**User Story:** As a platform operator, I want infrastructure defined as code, so that environments are reproducible. (Implementation_Sequence step 36)

#### Acceptance Criteria

1. THE repository SHALL provide a Terraform module for each area listed in Master_Specification section 68.
2. THE repository SHALL provide a Terraform environment configuration for development, staging, and production.
3. THE CI_Pipeline SHALL validate and format-check every Terraform module.
4. THE Terraform configurations SHALL read credentials from the execution environment and SHALL contain no credential value in tracked files.
5. FOR ALL Terraform modules, a plan against unchanged state SHALL report zero changes (idempotence property).

### Requirement 37: CI/CD

**User Story:** As the sole engineer, I want automation to gate every change, so that quality does not depend on my remembering to check. (Implementation_Sequence step 37)

#### Acceptance Criteria

1. THE CI_Pipeline SHALL run linting, formatting, unit tests, integration tests, security scanning, dependency scanning, and build on every pull request.
2. WHEN a change merges to the main branch, THE CI_Pipeline SHALL build container images, scan those images, and deploy to staging.
3. THE CI_Pipeline SHALL run the end-to-end suite against staging before permitting a production deployment.
4. THE CI_Pipeline SHALL require an explicit approval before a production deployment.
5. THE CI_Pipeline SHALL deploy production workloads by immutable image digest.
6. IF any gate in the CI_Pipeline fails, THEN THE CI_Pipeline SHALL block the merge or deployment and SHALL name the failing gate.
7. THE CI_Pipeline SHALL publish a software bill of materials for every released image.

### Requirement 38: High Availability

**User Story:** As a platform operator, I want no single replica to be required for service, so that routine failures stay invisible to developers. (Implementation_Sequence step 38)

#### Acceptance Criteria

1. THE platform SHALL serve requests while any single application replica is unavailable.
2. THE platform SHALL run request-path services as stateless processes holding no request-affecting local state.
3. THE platform SHALL scale request-path workloads on the signals listed in Master_Specification section 71.
4. WHEN a replica fails its readiness probe, THE load balancer SHALL stop routing traffic to that replica.
5. FOR ALL request-path services, two replicas processing one Routing_Input SHALL produce identical routing selections (replica-equivalence property, scoped per decision D5).

### Requirement 39: Disaster Recovery

**User Story:** As a platform operator, I want tested backup and restore, so that recovery is a rehearsed procedure. (Implementation_Sequence step 39)

#### Acceptance Criteria

1. THE repository SHALL document the recovery point objective, the recovery time objective, the backup frequency, and the restore procedure.
2. THE platform SHALL back up PostgreSQL and platform configuration on the documented schedule.
3. THE platform SHALL exclude transient cache contents from backups.
4. WHEN the documented restore procedure runs against a backup in a clean environment, THE platform SHALL start and SHALL pass its data integrity checks.
5. THE repository SHALL record the date and outcome of the most recent restore test.

### Requirement 40: Security Testing

**User Story:** As a security administrator, I want the security controls tested automatically, so that a regression is caught before release. (Implementation_Sequence step 40)

#### Acceptance Criteria

1. THE security test suite SHALL assert that an unauthenticated request to each protected path is rejected.
2. THE security test suite SHALL assert that a principal of one Tenant cannot read or write another Tenant's records.
3. THE security test suite SHALL assert that a principal lacking a required permission cannot perform the corresponding operation.
4. THE security test suite SHALL assert that no Sensitive_Value appears in emitted logs, error responses, or telemetry.
5. THE repository SHALL document a threat model covering the boundaries listed in Master_Specification section 83.
6. THE CI_Pipeline SHALL run the security test suite on every pull request.

### Requirement 41: Load Testing

**User Story:** As a platform operator, I want measured throughput and latency, so that capacity planning uses data rather than estimates. (Implementation_Sequence step 41)

#### Acceptance Criteria

1. THE load test suite SHALL measure request rate, error rate, and the p50, p95, and p99 latencies of the routing path.
2. THE load test suite SHALL isolate routing-path latency from provider latency in its reported results.
3. THE load test suite SHALL record the measured environment specification alongside every published result.
4. WHEN a measured latency exceeds its configured budget, THE load test suite SHALL fail and SHALL name the exceeded budget.

### Requirement 42: End-to-End Testing

**User Story:** As the project owner, I want the whole chain exercised automatically, so that "it works end to end" is a test result rather than a belief. (Implementation_Sequence step 42)

#### Acceptance Criteria

1. THE end-to-end suite SHALL exercise the complete chain of Master_Specification section 141 from integration entry through telemetry arrival.
2. THE end-to-end suite SHALL assert the presence of a persisted Routing_Decision, a persisted usage record, and a persisted cost record for each exercised request.
3. THE end-to-end suite SHALL exercise a streaming request and SHALL assert incremental chunk delivery.
4. THE end-to-end suite SHALL exercise a policy-blocked request, a fallback path, and an escalation path.
5. THE end-to-end suite SHALL substitute provider responses with recorded fixtures by default and SHALL run against live providers only where explicitly configured.

### Requirement 43: Documentation

**User Story:** As any AgentRouter audience, I want documentation with working examples, so that I can use the platform without reading source code. (Implementation_Sequence step 43)

#### Acceptance Criteria

1. THE repository SHALL provide documentation for each audience listed in Master_Specification section 94.
2. THE repository SHALL generate API reference documentation from `docs/api/openapi.yaml`.
3. THE CI_Pipeline SHALL execute every executable example embedded in the documentation and SHALL fail on any example that errors.
4. THE documentation SHALL state the known limitations of each component recorded in the Status_Record.
5. WHEN a public API contract changes, THE CI_Pipeline SHALL fail IF the corresponding documentation is unchanged in the same change set.

### Requirement 44: Customer Onboarding and Support

**User Story:** As a new customer, I want a documented path from signup to a routed request, so that adoption does not require vendor hand-holding. (Implementation_Sequence steps 44, 45, and 46)

#### Acceptance Criteria

1. THE repository SHALL document each step of the onboarding flow in Master_Specification section 91.
2. THE end-to-end suite SHALL exercise the documented onboarding flow from tenant creation to a first routed request.
3. THE platform SHALL make every request traceable through the identifiers listed in Master_Specification section 93 without exposing message content to support personnel.
4. THE repository SHALL provide the incident response procedure of Master_Specification section 119 and the security incident procedures of Master_Specification section 120.
5. THE repository SHALL record, for each item of the Production_DoD, the Verification_Evidence that substantiates it or the reason it remains outstanding.
6. THE repository SHALL declare the platform production-ready only when every Production_DoD item has passing Verification_Evidence.

### Requirement 45: Architectural Boundary Preservation

**User Story:** As the architect, I want the core boundaries enforced mechanically, so that extension does not erode the design. (Master_Specification sections 98 and 128)

#### Acceptance Criteria

1. THE CI_Pipeline SHALL fail WHEN Routing_Engine source files import a provider SDK, an Integration_Adapter, or an MCP module.
2. THE CI_Pipeline SHALL enforce provider-call containment by static import-graph analysis, failing WHEN a module outside the Provider_Gateway imports an HTTP client or provider SDK, and THE integration test suite SHALL additionally assert at runtime that no outbound provider request originates outside the Provider_Gateway.
3. THE platform SHALL admit a new provider by adding a Provider_Adapter and Model_Registry records without modification to Routing_Engine source files.
4. THE platform SHALL admit a new model by adding a Model_Record without modification to any component's source files.
5. THE platform SHALL admit a new IDE integration by adding an Integration_Adapter and a Capability_Profile without modification to Routing_Engine or Provider_Gateway source files.
6. WHERE the Gateway transport layer is reimplemented in another language, THE Routing_Engine, Analyzer, Policy_Engine, and Cost_Engine interfaces SHALL remain unchanged (decision D2 containment).
7. THE platform SHALL gate every new routing algorithm, provider, and integration behind a feature flag.
