# Design Document

## Overview

This design converts the 45 requirements into a buildable architecture. It covers the
whole 46-step Implementation_Sequence, but it specifies Phase 1 (decision D1: the
single-host vertical slice) at implementation depth and later phases at interface depth,
because the later phases decompose Phase 1 rather than replacing it.

Three ideas carry most of the design weight:

1. **A pure routing core.** Analyzer, Policy_Engine, Routing_Engine, and Cost_Engine are
   pure functions over explicit inputs. No I/O, no clocks, no provider SDKs, no database
   handles. Everything the core needs arrives as a parameter. This is what makes the
   determinism, isolation, and invariant properties from the requirements testable at all,
   and it is what lets Phase 2 split the core into services without touching its logic.
2. **One canonical pipeline.** Every entry point (HTTP, MCP, CLI, SDK, IDE adapter)
   normalizes to a `CanonicalRequest` and runs the identical pipeline. Requirement 11.3
   (confluence) and Requirement 24.4 (MCP/API policy equivalence) then hold by
   construction rather than by parallel implementations kept in sync by discipline.
3. **A machine-readable completion ledger.** `docs/implementation-status.yaml` is the
   single source of truth for what works; the markdown status document and the spec task
   sheet are both derived from it. This is what makes the auto-update hook reliable.

### Design principles

| Principle | Consequence |
| --- | --- |
| Core is pure | Ports live at the edges; core takes snapshots, not connections |
| One pipeline | New entry points add an adapter, never a second routing path |
| Registry is authoritative | No price or capability literal outside the registry and declared fixtures |
| Derived over duplicated | Status markdown, SDK types, and API docs are generated |
| Evidence over assertion | A completion claim names a command that exits zero |

## Requirements Traceability

Design sections map to requirements as follows. Requirements not listed here are satisfied
by the component whose name matches the requirement title.

| Requirement | Design section |
| --- | --- |
| 1, 2 | Completion Ledger; Anti-Fabrication Enforcement |
| 3 | Repository and Environment |
| 4 | Contracts Package |
| 5 | Persistence Layer |
| 6, 7, 8 | Identity, Tenancy, and Authorization |
| 9 | Model Registry |
| 10 | Provider Gateway |
| 11, 12 | Entry Adapters; API Gateway |
| 13 | Analyzer |
| 14, 15 | Routing Engine |
| 16 | Cost Engine |
| 17 | Policy Engine |
| 18, 19 | Execution Orchestrator |
| 20 | Security, Redaction, and Secrets |
| 21 | Observability |
| 22, 23, 30, 31 | Event Bus and Consumers |
| 24 | MCP Server |
| 25, 26, 27, 28 | Client, CLI, SDKs, Integration Adapters |
| 29 | Web Applications |
| 32, 33 | Benchmark and Evaluation Harnesses |
| 34, 35, 36, 37 | Deployment and Infrastructure |
| 38, 39 | Availability and Recovery |
| 40, 41, 42 | Test Architecture |
| 43, 44 | Documentation and Onboarding |
| 45 | Boundary Enforcement |

## Architecture

### Phase 1 process topology

Phase 1 runs as three processes on one host. The module boundaries inside the API process
are the same boundaries that later become service boundaries, so decomposition is a
deployment change rather than a rewrite.

```text
┌───────────────────────────────────────────────────────────────┐
│ DEVELOPER MACHINE                                             │
│                                                               │
│   IDE ──► Local Client ──► MCP Server (process 2)             │
│                                  │                            │
└──────────────────────────────────┼────────────────────────────┘
                                   │ HTTPS
                                   ▼
┌───────────────────────────────────────────────────────────────┐
│ API PROCESS (process 1)                                       │
│                                                               │
│  Entry Adapters ──► Auth ──► Normalizer                       │
│                                  │                            │
│                                  ▼                            │
│                        ┌──────── PURE CORE ────────┐          │
│                        │  Analyzer                 │          │
│                        │  Policy Engine            │          │
│                        │  Routing Engine           │          │
│                        │  Cost Engine              │          │
│                        └───────────┬───────────────┘          │
│                                    ▼                          │
│                       Execution Orchestrator                  │
│                    (escalation, fallback, breaker)            │
│                                    │                          │
│                                    ▼                          │
│                          Provider Gateway ──────────► providers
│                                    │                          │
│                    ┌───────────────┴────────────┐             │
│                    ▼                            ▼             │
│              Response/stream              Event Bus (outbox)  │
└───────────────────────────────────────────────────────────────┘
                    │                            │
                    ▼                            ▼
              PostgreSQL / Redis        Worker (process 3)
                                   analytics, billing, audit,
                                   notifications, health probes
```

### The request pipeline

One sequence, used by every entry point. Stage numbers correspond to the lifecycle states
of Master_Specification section 10.

```text
RECEIVED       Entry adapter accepts transport-specific input
AUTHENTICATED  Credential verified, Principal resolved
AUTHORIZED     Permission checked, TenantContext derived
               Normalizer builds CanonicalRequest (tenant fields from context)
ANALYZING      Analyzer produces AnalysisResult
               Policy Engine resolves PolicyDecision
ROUTING        Routing Engine builds Candidate_Set, scores, emits RoutingDecision
               Cost Engine estimates cost
EXECUTING      Orchestrator calls Provider Gateway; streams chunks
VALIDATING     Escalation criteria evaluated
COMPLETED      Cost recorded, events enqueued, response finalized
```

Failure states (`REJECTED`, `TIMEOUT`, `FAILED`, `FALLBACK`, `ESCALATED`,
`POLICY_BLOCKED`) are terminal transitions from the corresponding stage. The state machine
is a single table in `packages/shared-types`, so transitions are validated rather than
implied by control flow.

### Repository layout for Phase 1

Python packages install as a workspace so imports are absolute and boundary rules are
enforceable by import analysis.

```text
packages/
  shared_types/       CanonicalRequest, AnalysisResult, RoutingDecision, PolicyDecision,
                      lifecycle table, normalized errors  (no dependencies)
  api_contracts/      JSON Schema + OpenAPI source of truth; codegen entry point
  configuration/      typed settings loader, weight presets, env binding
  redaction/          detectors, allow-list, redact()
  logging/            structured logger with redaction wired in
  telemetry/          OTel setup, metric registry
  errors/             normalized error taxonomy and HTTP/MCP mapping
  tenant/             TenantContext, scoped-session enforcement
  auth/               credential verification, API key hashing
  authorization/      roles, permissions, require()
  events/             event definitions, outbox writer, consumer base
  testing/            fixtures, fakes, property-test strategies

services/
  registry/           model + provider catalog, pricing, lifecycle, health read model
  analyzer/           classifier, complexity, capabilities, context tiers
  policy/             rules, hierarchy resolution, evaluation
  router/             candidates, scoring, strategies, escalation, fallback (pure)
  cost_engine/        estimation, calculation, savings
  providers/          adapter interface, per-provider adapters, breaker, health
  gateway/            HTTP app, entry adapters, orchestrator wiring
```

## Components and Interfaces

### Contracts Package

`packages/api_contracts` holds JSON Schema documents as the single source of truth.
Python types, TypeScript types, and the OpenAPI paths are generated from them.

```text
api_contracts/
  schemas/
    canonical_request.schema.json
    analysis_result.schema.json
    routing_decision.schema.json
    policy_decision.schema.json
    usage_record.schema.json
    errors.schema.json
  openapi/
    openapi.yaml          assembled; operations reference schemas/
  codegen.py              schemas -> python + typescript
```

CI regenerates and diffs (Requirement 4.4). Round-trip properties (4.5, 4.6) are
Hypothesis properties over schema-derived strategies, so new fields are covered
automatically rather than needing new tests.

Schema versioning: each schema carries `x-contract-version`. A breaking change requires a
new version and a documented migration, enforced by Requirement 43.5's docs-changed gate.

### Analyzer

Pure. Signature makes the "no model selection" invariant (13.7) structural — the Analyzer
cannot name a model because it never receives the registry.

```python
def analyze(request: CanonicalRequest, config: AnalyzerConfig) -> AnalysisResult
```

Complexity derivation, satisfying R13.3 while respecting R13.4/13.5:

```text
signals = {
    task_type            from classifier (configurable rules; R13.8)
    operation_count      count of imperative clauses / requested artifacts
    reasoning_required    from task_type profile + dependency depth
    context_tier         SMALL | MEDIUM | LARGE | HUGE  (token estimate -> band)
    tool_required        presence and count of declared tools
    expected_output      code | diagnosis | prose | structured
    ambiguity            unresolved-reference and underspecification count
    dependency_depth     cross-file / cross-service references
}

complexity = weighted_band(signals excluding raw character length)
```

`context_tier` is the only path from content size to complexity (R13.5). The invariant test
for R13.4 generates request pairs differing only in padding within one tier and asserts
equal `Complexity_Level`.

Task types and their signal profiles live in `config/<env>/analyzer.yaml`, satisfying
R13.8 (new task type without source change).

Phase 1 classifier is deterministic and rule-based. This is deliberate: a model-based
classifier would put a network call inside the analyzer and break both determinism and the
latency budget. If classification quality proves insufficient, the escalation path
(Requirement 18) absorbs it, and the evaluation harness measures whether it does.

### Model Registry

Authoritative for capability, pricing, and health (R9.2). The core never queries it
directly during routing; instead the orchestrator takes an immutable snapshot.

```python
@dataclass(frozen=True)
class RegistrySnapshot:
    snapshot_id: str            # part of Routing_Input identity (D5)
    models: tuple[ModelRecord, ...]
    health: Mapping[ModelId, HealthState]
    taken_at: datetime
```

The snapshot is what makes D5 workable: routing is deterministic given a snapshot id, and
health changes produce a new snapshot rather than nondeterminism inside a single decision.

Snapshots are cached in Redis with a short TTL and refreshed by the worker; the snapshot id
is a content hash so identical states reuse an id.

Lifecycle transitions (R9.5) are validated against an explicit allowed-transition set;
`DEPRECATED` and `RETIRED` models are excluded at snapshot construction (R9.6), so no
filter can accidentally admit them.

### Policy Engine

Pure, monotonic narrowing per decision D3.

```python
def resolve(scopes: Sequence[PolicyScope], request: CanonicalRequest) -> PolicyDecision
```

Resolution folds scopes broad-to-narrow, intersecting permissions and unioning
prohibitions:

```text
start:   allowed = platform_defaults
per scope in [platform, organization, department, team, user, request]:
    allowed_models     = allowed_models    ∩ scope.allowed_models
    allowed_providers  = allowed_providers ∩ scope.allowed_providers
    blocked_models     = blocked_models    ∪ scope.blocked_models
    max_cost           = min(max_cost, scope.max_cost)
    allowed_regions    = allowed_regions   ∩ scope.allowed_regions
```

Intersection and union are commutative and idempotent, which is what gives R17.4
(determinism), R17.5 (precedence), and R17.6 (idempotence) directly. Each restriction
records the scope that contributed it, so `PolicyDecision.reason` can name the exact source
— required by R17.7 and by the routing explainability requirements.

### Routing Engine

The core IP, and pure. Its entire input is `RoutingInput` (decision D5).

```python
@dataclass(frozen=True)
class RoutingInput:
    request: CanonicalRequest
    analysis: AnalysisResult
    policy: PolicyDecision
    snapshot: RegistrySnapshot
    budget: BudgetState
    preset: WeightPreset

def route(inp: RoutingInput) -> RoutingDecision
```

Filtering is a pipeline of named predicates. Each rejection is recorded with its filter
name, which is what lets `RoutingDecision` explain itself (R15.3) and lets R14.11 name the
filter that emptied the set.

```text
snapshot.models
  ├─ capability_filter    required capabilities present
  ├─ context_filter       context_window >= required context
  ├─ policy_filter        not prohibited; provider permitted
  ├─ region_filter        model region ∈ policy.allowed_regions
  ├─ availability_filter  health ok; circuit not open; lifecycle ACTIVE
  └─ budget_filter        estimated cost within remaining budget
       └─► Candidate_Set
```

Scoring, with all weights from configuration (R14.3):

```text
score(m) =  w_quality     * quality_match(m, analysis)
          + w_capability  * capability_match(m, analysis)
          + w_context     * context_fit(m, analysis)
          + w_reliability * reliability(m, snapshot.health)
          + w_latency     * latency_score(m)
          - w_cost        * cost_penalty(m, analysis)
```

Each term is normalized to `[0, 1]` before weighting so weights remain comparable and
tuning stays interpretable. `cost_penalty` normalizes against the most expensive candidate
in the current set, making the penalty relative to actual alternatives rather than an
absolute scale.

Routing modes are weight presets only (R14.4, R14.10) — there is exactly one selection
rule:

| Preset | quality | capability | context | reliability | latency | cost |
| --- | --- | --- | --- | --- | --- | --- |
| BALANCED | 0.30 | 0.20 | 0.10 | 0.15 | 0.10 | 0.15 |
| QUALITY_FIRST | 0.50 | 0.25 | 0.10 | 0.10 | 0.05 | 0.00 |
| COST_FIRST | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| LATENCY_FIRST | 0.10 | 0.15 | 0.05 | 0.15 | 0.55 | 0.00 |
| RELIABILITY_FIRST | 0.15 | 0.15 | 0.05 | 0.55 | 0.10 | 0.00 |
| POLICY_FIRST | 0.25 | 0.30 | 0.15 | 0.20 | 0.10 | 0.00 |

These are starting values to be replaced by evaluation-harness measurements, not tuned
constants. COST_FIRST giving cost the sole non-zero weight is what makes R14.10 a
consequence of R14.9 rather than a competing rule.

Selection: maximum score, ties broken by `(lower estimated cost, lower latency_p95,
lexicographic model_id)`. The final lexicographic term guarantees total ordering, so
determinism (R14.12) and replica-equivalence (R38.5) hold with no residual ambiguity.

### Cost Engine

Per-attempt accumulation with signed savings (decision D4).

```python
def cost_of_attempt(attempt: ProviderAttempt, pricing: ModelPricing) -> Money
def cost_of_request(attempts: Sequence[ProviderAttempt], snapshot) -> RequestCost
def savings(actual: Money, baseline: Money) -> SignedMoney   # may be negative
```

`RequestCost` carries a per-attempt breakdown so an escalated request shows where its cost
came from. Money is integer minor units with an explicit currency — never float — because
aggregate consistency (R16.2, R23.3) cannot hold under binary floating point.

Missing pricing yields `cost: unavailable` plus a pricing-gap event (R16.9) rather than a
zero, which would silently understate spend.

### Provider Gateway

The only component permitted outbound provider calls (R45.2).

```python
class ProviderAdapter(Protocol):
    async def authenticate(self) -> None
    async def health_check(self) -> HealthState
    async def list_models(self) -> Sequence[ProviderModel]
    async def generate(self, req: ProviderRequest) -> ProviderResponse
    def stream(self, req: ProviderRequest) -> AsyncIterator[Chunk]
    def estimate_tokens(self, req: ProviderRequest) -> TokenEstimate
    def normalize_error(self, exc: Exception) -> NormalizedError
```

One shared contract-test suite runs against every adapter (R10.5), parameterized over
adapters, so a new provider inherits the full assertion set. Adapters are tested against
recorded fixtures; a separately-marked live suite runs only with explicit configuration
(R42.5).

Streaming forwards chunks without accumulation (R10.7) — the type is `AsyncIterator`, so
buffering would require deliberately materializing it, and a test asserts first-chunk
latency stays well below full-response latency.

Context pre-check (R10.8) happens before any network call, using `estimate_tokens` against
the snapshot's context window.

### Execution Orchestrator

The only impure part of the request path. It owns retries, escalation, fallback, and
breaker state — deliberately kept out of the pure core.

```text
attempts = []
decision = route(routing_input)

loop (bounded by configured attempt limit):
    result = provider_gateway.execute(decision.selected_model, request)
    attempts.append(result)

    if result.failed:
        breaker.record_failure(provider)
        alt = fallback.next_candidate(decision, exclude=attempted)   # same Candidate_Set
        if alt is None: return FAILED with normalized error          # R19.6
        decision = alt; continue                                     # FALLBACK

    if escalation.enabled and not escalation.acceptable(result):
        stronger = escalation.next_candidate(decision, min_capability=current)
        if stronger is None: break
        decision = stronger; continue                                # ESCALATED

    break

cost = cost_of_request(attempts, snapshot)     # every attempt (D4)
```

Fallback and escalation both select from the Candidate_Set the router already produced,
which is how R19.2 and R18.3 (alternatives still satisfy policy) hold structurally — a
prohibited model is not in the set to be chosen.

Circuit breaker state lives in Redis keyed by provider, with closed/open/half-open
transitions on configured thresholds (R19.3–19.5). State is shared across replicas so
breaker behavior is consistent under horizontal scaling.

### Identity, Tenancy, and Authorization

`TenantContext` derives from the verified credential only (R7.1). A client-supplied tenant
identifier that disagrees is rejected (R7.2) rather than ignored, so mismatch is a loud
failure.

Isolation (R7.3–7.5) is enforced at the session layer, not by reviewer vigilance:

```python
class TenantScopedSession:
    """Every query carries a tenant predicate; unscoped access raises."""
    def query(self, model, *, ctx: TenantContext): ...
```

Tenant-owned tables are additionally protected by PostgreSQL row-level security, giving a
second independent enforcement point. The security suite (R40.2) asserts cross-tenant reads
return zero rows for every tenant-owned table, driven by table introspection so new tables
are covered without new tests.

API keys are stored as Argon2id hashes with a lookup prefix, returned once at creation
(R6.2).

### Event Bus and Consumers

Phase 1 uses a transactional outbox in PostgreSQL rather than Kafka. Requirements demand
idempotent, retryable, at-least-once delivery (R22.3, R22.5) — not a specific broker — and
an outbox provides exactly that with one less operational component. The publisher
interface is broker-agnostic, so the Kafka/Redpanda migration named in `technology.md` is a
Phase 2 adapter swap.

```text
request txn ──► write outbox row (same transaction as state change)
                      │
worker poll ──────────┘──► dispatch ──► consumers (analytics, billing, audit, notifications)
                                             │
                                     processed_events (event_id unique)
```

The `processed_events` uniqueness constraint gives consumer idempotence (R22.3, R30.5,
R31.5) as a database guarantee. The request path commits and returns without waiting for
any consumer (R22.4).

### Completion Ledger

This is the mechanism behind the auto-updating task sheet.

```text
docs/implementation-status.yaml     authoritative, schema-validated
        │
        ├──► scripts/status/render.py   ──► docs/IMPLEMENTATION_STATUS.md  (generated)
        ├──► scripts/status/verify.py   ──► runs each evidence command
        └──► scripts/status/sync_tasks.py ──► reconciles with spec tasks.md
```

Manifest shape:

```yaml
version: 1
components:
  - id: routing-engine
    module: "01..30 from Master_Specification section 6"
    status: not_started        # not_started | in_progress | implemented | blocked
    phase: 14                  # Implementation_Sequence step
    implementation: services/router
    tests: services/router/tests
    evidence:
      - name: router-unit
        command: "pytest services/router/tests -q"
      - name: router-properties
        command: "pytest services/router/tests/test_properties.py -q"
    component_dod:              # all 12 must be true for status: implemented
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
      - "Weight presets are unmeasured starting values"
```

Three CI gates make the ledger honest:

| Gate | Enforces |
| --- | --- |
| `status-schema` | manifest validates (R1.3) |
| `status-render` | committed markdown equals generated (R1.4) |
| `status-evidence` | every `implemented` component's evidence exits zero (R1.6) |
| `status-dod` | no `implemented` component has a false DoD item (R1.7) |

The auto-update hook is a `postTaskExecution` hook running
`python scripts/status/on_task_complete.py`, which maps the completed task to its
component, re-runs that component's evidence, promotes status only if evidence passes and
all twelve DoD items are true, regenerates the markdown, and writes the evidence name back
into `tasks.md` (R1.10, R1.11). If evidence fails, it records `blocked` with the failure
output rather than promoting — the hook cannot manufacture green status.

### Anti-Fabrication Enforcement

| Check | Requirement | Mechanism |
| --- | --- | --- |
| Placeholder in implemented component | 2.1 | grep marker set, scoped by manifest |
| Price/context literal outside registry | 9.3 | AST scan, fixture paths exempt |
| Core imports provider SDK / IDE / MCP | 45.1 | import-graph analysis |
| Outbound call outside Provider Gateway | 45.2 | import analysis + runtime assertion |
| Secret in tracked file | 20.7 | secret-detection patterns |
| Unsubstantiated benchmark figure | 2.3, 2.4 | run record required for publication |
| Docs unchanged on contract change | 43.5 | path-pair diff gate |

Boundary enforcement lives in `scripts/architecture/check_boundaries.py` and reads an
allow-list of permitted import edges, so the rule set is data rather than scattered
assertions.

## Data Models

### Core routing types

```python
@dataclass(frozen=True)
class CanonicalRequest:
    request_id: str
    tenant_id: str            # from TenantContext, never from payload (R11.4)
    user_id: str
    team_id: str | None
    session_id: str | None
    source: EntrySource
    agent: str | None
    messages: tuple[Message, ...]
    tools: tuple[ToolSpec, ...]
    context: RequestContext
    stream: bool
    constraints: RequestConstraints
    received_at: datetime

@dataclass(frozen=True)
class AnalysisResult:
    task_type: TaskType
    complexity: ComplexityLevel
    reasoning_requirement: Level
    context_requirement: ContextTier
    coding_requirement: Level
    tool_requirement: Level
    expected_output: ExpectedOutput
    confidence: float                    # [0, 1]
    signals: Mapping[str, float]         # explainability

@dataclass(frozen=True)
class RoutingDecision:
    selected_model: ModelId
    reasons: tuple[str, ...]
    confidence: float
    estimated_cost: Money
    alternatives: tuple[ScoredCandidate, ...]
    rejected: tuple[RejectedCandidate, ...]   # model + filter name (R15.3)
    mode: RoutingMode
    weights: Mapping[str, float]
    policy_decisions: tuple[PolicyDecisionRef, ...]
    routing_input_id: str                     # D5 determinism key
```

### Schema notes

The 25 core tables of Master_Specification section 61 are created across ordered
migrations. Design decisions worth stating:

- Every tenant-owned table carries `tenant_id NOT NULL` plus an RLS policy (R5.6, R7.3).
- `requests`, `routing_decisions`, `provider_requests`, `usage_records`, and `cost_records`
  are append-only and partitioned by month; they are the highest-volume tables and the ones
  analytics reads.
- `audit_events` is append-only with revocation of UPDATE and DELETE from the application
  role, making immutability a database guarantee (R58 / R8.6).
- Money columns are `BIGINT` minor units with a currency column, never floating point.
- `processed_events` holds a unique constraint on `event_id` for consumer idempotence.

## Error Handling

Normalized errors are the only errors that cross a boundary. Every layer maps into the
taxonomy of Master_Specification section 47.

| Normalized error | HTTP | Typical origin |
| --- | --- | --- |
| `AUTHENTICATION_ERROR` | 401 | missing, expired, revoked credential |
| `AUTHORIZATION_ERROR` | 403 | permission, tenant mismatch |
| `INVALID_REQUEST` | 400 | schema violation, missing field |
| `POLICY_BLOCKED` | 403 | policy prohibition |
| `CONTEXT_TOO_LARGE` | 413 | pre-flight context check |
| `RATE_LIMIT` | 429 | scope limit exceeded |
| `MODEL_UNAVAILABLE` | 503 | empty Candidate_Set |
| `PROVIDER_ERROR` | 502 | provider failure after fallback |
| `TIMEOUT` | 504 | deadline exceeded |
| `CONTENT_POLICY` | 422 | provider content refusal |
| `UNKNOWN` | 500 | unhandled |

Every error response carries `request_id` and `trace_id` and excludes stack detail
(R12.7). Errors pass through redaction before serialization, so a provider error echoing a
credential cannot leak it (R20.2).

`MODEL_UNAVAILABLE` names the filter that removed the last candidate (R14.11) — the
difference between "no model available" and "your region policy excluded the only capable
model" is the difference between a support ticket and a self-service fix.

## Correctness Properties

These are the properties the design must uphold. Each is stated as a checkable predicate,
with the structural reason it holds and the requirement it discharges. They are the
specification for the property-test suite below.

### Property 1: Selection soundness

**Statement.** For every routing invocation that returns a decision, the selected model is
a member of the Candidate_Set, satisfies every capability the AnalysisResult marks required,
has a context window at least the required size, and is not prohibited by the resolved
PolicyDecision.

**Holds because** capability, context, and policy filters all precede scoring, and
selection is `max()` over the filtered set. Fallback and escalation re-select from that same
filtered set, so no later stage can reintroduce an unsound model.

**Validates: Requirements 14.5, 14.6, 14.7, 14.8, 18.3, 19.2**

### Property 2: Routing determinism

**Statement.** Two invocations sharing one `RoutingInput` select the same model, including
invocations on different replicas.

**Holds because** the core is pure, the registry snapshot id fixes model and health state,
and the tie-break `(cost, latency_p95, model_id)` is a total order.

**Validates: Requirements 14.12, 38.5**

### Property 3: Policy resolution algebra

**Statement.** Policy resolution is deterministic and idempotent, and if any scope in the
hierarchy prohibits a model or provider then the resolved decision prohibits it.

**Holds because** resolution folds intersection over permissions and union over
prohibitions across an ordered scope list; both operations are idempotent, and union is
monotone, giving monotonic narrowing per decision D3.

**Validates: Requirements 17.4, 17.5, 17.6**

### Property 4: Tenant isolation

**Statement.** A read or write issued under one TenantContext never observes or modifies
records owned by another tenant, and a tenant-owned access attempted with no TenantContext
raises before any query executes.

**Holds because** the scoped session applies a tenant predicate to every query and refuses
unscoped access, with PostgreSQL row-level security as an independent second enforcement
point.

**Validates: Requirements 7.3, 7.4, 7.5, 40.2**

### Property 5: Sensitive-value containment

**Statement.** No log record, error response, notification payload, or telemetry attribute
contains a substring matching a Sensitive_Value detector, except values on the declared
non-sensitive identifier allow-list. Redaction is idempotent.

**Holds because** redaction is inside the logging layer and the error serializer rather
than at call sites, and replacement tokens do not match the detectors that produce them.

**Validates: Requirements 20.2, 20.3, 31.3, 40.4**

### Property 6: Cost and savings faithfulness

**Statement.** Recorded request cost equals the sum, over every provider attempt including
fallbacks and escalations, of token counts multiplied by the registry price for that
attempt's model. Reported savings equal baseline cost minus actual cost as a signed value,
and are never floored at zero.

**Holds because** money is integer minor units with an explicit currency, the per-attempt
breakdown is retained, and the savings function has no clamping branch.

**Validates: Requirements 2.2, 16.2, 16.3, 16.4**

### Property 7: Aggregate consistency

**Statement.** For any period, the sum of per-dimension cost aggregates equals the sum of
the underlying recorded request costs, and the invoiced usage total equals the sum of that
period's recorded usage records.

**Holds because** analytics and billing both read the same append-only records rather than
recomputing from live routing calls.

**Validates: Requirements 23.3, 30.3**

### Property 8: Pipeline confluence

**Statement.** Equivalent input presented at any entry point (HTTP, MCP, CLI, SDK, IDE
adapter) produces CanonicalRequest values equal except for request id and receipt timestamp,
and yields an identical PolicyDecision.

**Holds because** every adapter normalizes into one pipeline, and all entry points call the
same Policy_Engine instance.

**Validates: Requirements 11.3, 24.4**

### Property 9: Complexity stability

**Statement.** Two requests differing only in message character length, falling in the same
Context_Tier and sharing task type, operation count, tool requirement, and expected output,
receive the same Complexity_Level.

**Holds because** character length influences complexity only through the `Context_Tier`
band; no other signal reads raw length.

**Validates: Requirements 13.4, 13.5**

### Property 10: Idempotent event consumption

**Statement.** Processing the same event identifier more than once leaves consumer state
identical to processing it once, produces one charge per usage record, and delivers one
notification per channel.

**Holds because** `processed_events.event_id` carries a unique constraint checked inside the
consumer transaction, making idempotence a database guarantee.

**Validates: Requirements 22.3, 30.5, 31.5**

### Property 11: Round-trip fidelity

**Statement.** Serializing then deserializing any contract value, domain event, or CLI
machine-readable output yields a value equal to the original. Applying then reverting any
development migration restores the prior schema version. A Terraform plan against unchanged
state reports zero changes.

**Holds because** codecs are generated from one schema source, every migration ships a
tested down-migration (decision D6), and module inputs contain no non-deterministic values.

**Validates: Requirements 4.5, 4.6, 5.4, 22.6, 26.5, 36.5**

### Property 12: Boundary containment

**Statement.** No module outside Provider_Gateway performs an outbound provider call, and
Routing_Engine source imports no provider SDK, IDE adapter, MCP module, or billing state.

**Holds because** CI runs import-graph analysis against an allow-list of permitted edges,
and the integration suite asserts the same at runtime.

**Validates: Requirements 28.6, 30.4, 45.1, 45.2**

### Property 13: No-dispatch on block

**Statement.** A request whose PolicyDecision disallows it, or whose Candidate_Set is empty,
reaches a terminal failure state without any provider request being dispatched.

**Holds because** the orchestrator is entered only after an allowing decision and a
non-empty Candidate_Set; both checks precede any adapter call.

**Validates: Requirements 14.11, 17.7**

### Property 14: Audit immutability

**Statement.** An `audit_events` row, once written, is never modified or deleted through
application credentials.

**Holds because** UPDATE and DELETE are revoked from the application role on that table.

**Validates: Requirements 8.6**

### Property 15: Termination and availability

**Statement.** Every accepted request reaches a terminal lifecycle state; escalation and
fallback loops terminate at the configured attempt limit; an open circuit eventually probes
and can close; the platform continues serving while any single replica is unavailable; a
failed event is retained for retry.

**Holds because** the lifecycle table defines terminal states explicitly, loops are bounded
by a configured counter, the breaker has a half-open probe timer, request-path services hold
no request-affecting local state, and undispatched outbox rows persist.

**Validates: Requirements 11.6, 18.6, 19.5, 22.5, 38.1**

### Deliberately not claimed

Stating these prevents false confidence later:

- **No claim** that classification is correct — only that it is deterministic and stable
  within a context tier. Accuracy is measured by the evaluation harness (R33), not asserted.
- **No claim** that routing selects the objectively best model — only that it selects the
  max-scoring candidate under the active preset. Whether the scoring is *good* is an
  empirical question the harness answers.
- **No claim** of exactly-once event delivery — at-least-once with idempotent consumers.
- **No claim** that prompt-injection detection is complete (per Master_Specification 86).
- **No claim** of WCAG conformance beyond what automated tooling verifies (R29.7); full
  conformance needs manual assistive-technology testing and expert review.

## Testing Strategy

The property tables above are the test specification: each row becomes a Hypothesis
property. Tests assert general truths rather than examples, so new models, providers, and
tenants are covered without new test code.

### Property tests (Hypothesis)

| Property | Requirement |
| --- | --- |
| Contract round-trip (D-7) | 4.5, 4.6 |
| Migration up/down round-trip, dev (D-8) | 5.4 |
| Cross-tenant reads return nothing (S5) | 7.4, 40.2 |
| Selected model ∈ Candidate_Set (S1) | 14.5 |
| Selected model satisfies capabilities (S2) | 14.6 |
| Selected model context sufficient (S3) | 14.7 |
| Selected model never prohibited (S4) | 14.8 |
| Selected model is max-scoring | 14.9 |
| Same RoutingInput ⇒ same model (D-1) | 14.12, 38.5 |
| Complexity invariant within context tier (C6) | 13.4 |
| Policy resolution deterministic / idempotent (D-2, D-3) | 17.4, 17.6 |
| Any scope prohibits ⇒ resolved prohibits (D-4) | 17.5 |
| Cost equals tokens × price summed over attempts (C1) | 16.2 |
| Aggregates equal underlying records (C2) | 23.3 |
| Redaction idempotent, no sensitive substring (S6, D-5) | 20.2, 20.3 |
| Event processing idempotent (D-6) | 22.3, 30.5, 31.5 |
| Terraform plan on unchanged state is empty (D-9) | 36.5 |

### Model-based suites

Provider adapters (R10.5) and SDKs (R27.3) each run one shared assertion set parameterized
over implementations, so conformance cannot drift per implementation.

### Test layers

```text
unit          pure core, no I/O, fast
integration   real PostgreSQL + Redis via docker-compose.test.yml
contract      adapters against recorded fixtures
api           requests validated against OpenAPI
security      auth, authorization, tenant isolation, redaction  (R40)
e2e           full chain of Master_Specification 141 with fixture providers  (R42)
load          routing-path latency isolated from provider latency  (R41)
chaos         provider failure, timeout, breaker, fallback
evaluation    routing accuracy against the labeled dataset  (R33)
```

The e2e suite defaults to fixture providers (R42.5) so it runs in CI without spending money
or depending on provider availability.

## Deployment and Infrastructure

Phase 1 targets docker-compose; the Kubernetes and Helm work (Requirements 34, 35) applies
to the same images. Consolidated workloads per `Architecture.md` section 32: gateway,
router, control-api, worker, mcp, dashboard. Images are distroless, non-root, with SBOM and
digest-pinned production deployments (R34.6, R37.5, R37.7).

Secrets resolve through a `SecretSource` port with env, Vault, and cloud implementations
(R20.6) — no secret in any tracked file, verified by CI.

## Open Points

Recorded rather than silently decided:

1. **Weight presets are unmeasured.** The table above is a starting point. The evaluation
   harness (Requirement 33) must produce measured values before any savings claim is made
   externally. This is listed as a limitation in the manifest from day one.
2. **Quality scores need a source.** `quality_match` depends on registry capability scores,
   which depend on the benchmark harness (step 32). Until then Phase 1 uses published
   provider benchmarks, explicitly labeled as third-party rather than measured.
3. **Go gateway migration deferred.** `technology.md` names Go for the gateway; D2 defers
   it. R45.6 keeps core interfaces stable so the migration stays confined to transport.
4. **Kafka deferred to Phase 2.** The outbox satisfies every stated requirement; the
   publisher interface keeps the swap local.
