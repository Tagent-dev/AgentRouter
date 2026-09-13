# AgentRouter

* what the product is
* what must be built
* architecture
* repositories
* services
* APIs
* database
* routing algorithm
* MCP
* IDE integrations
* security
* enterprise requirements
* Kubernetes
* SaaS
* self-hosting
* testing
* observability
* deployment
* documentation
* acceptance criteria
* and the exact order in which Kiro should implement everything.

One important correction to your expectation: **the technical plan can be comprehensive, but no document can guarantee that customers will immediately buy the product.** Enterprise sales, security reviews, procurement, integrations, and customer validation still take time. So we'll design this to be genuinely production-ready rather than assuming the market response.

Below is the master specification I recommend giving to your Kiro agent.

---

# AGENTROUTER

## Enterprise AI Model Routing, Optimization & Governance Platform

**Document type:** Master Engineering Specification
**Status:** Final Target Architecture
**Primary implementation environment:** Kiro
**Development model:** Solo founder / AI-assisted engineering
**Deployment target:** SaaS + customer-managed/private deployment
**Primary integration:** AI coding agents, IDEs, MCP, API, CLI, SDK
**Primary objective:** Intelligent model selection and enterprise AI governance

---

# TABLE OF CONTENTS

1. Product Vision
2. Problem Statement
3. Product Scope
4. Core Principles
5. Target Customers
6. User Personas
7. Product Capabilities
8. System Architecture
9. Data Plane
10. Control Plane
11. Integration Plane
12. Request Lifecycle
13. Model Registry
14. Provider Gateway
15. Request Normalization
16. Request Analyzer
17. Routing Engine
18. Routing Algorithms
19. Cost Optimization
20. Quality Optimization
21. Latency Optimization
22. Dynamic Escalation
23. Fallback
24. Policy Engine
25. Security
26. Privacy
27. Authentication
28. Authorization
29. Multi-Tenancy
30. MCP Server
31. IDE Integration
32. AgentRouter Client
33. API Gateway
34. CLI
35. SDK
36. Dashboard
37. Analytics
38. FinOps
39. Benchmarking
40. Evaluation
41. Feedback
42. Billing
43. Notifications
44. Audit
45. Observability
46. Database
47. Caching
48. Messaging
49. Kubernetes
50. Helm
51. Terraform
52. Cloud Deployment
53. Private Deployment
54. CI/CD
55. Testing
56. Performance
57. Disaster Recovery
58. Compliance
59. Documentation
60. Customer Onboarding
61. Support
62. Repository Structure
63. Development Environment
64. Engineering Standards
65. Implementation Sequence
66. Definition of Done
67. Production Readiness
68. Final Architecture
69. Kiro Operating Instructions

---

# 1. PRODUCT VISION

AgentRouter is an enterprise AI gateway that determines the most appropriate AI model for each developer-agent request.

Instead of every task being sent to an expensive model:

```text
Developer
    ↓
AI Agent
    ↓
AgentRouter
    ↓
Analyze request
    ↓
Determine requirements
    ↓
Evaluate available models
    ↓
Apply organization policies
    ↓
Optimize quality/cost/latency
    ↓
Select model
    ↓
Execute
    ↓
Return response
```

The system must support multiple providers and multiple models.

The developer should not need to understand model pricing, capability differences, context limits, provider availability, or enterprise policy.

AgentRouter handles these decisions automatically.

---

# 2. IMPORTANT ARCHITECTURAL PRINCIPLE

MCP is **not the core product**.

MCP is an integration mechanism.

The core product is:

```text
AgentRouter Core
```

with multiple interfaces:

```text
                    AgentRouter Core
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
      MCP              API              Client
       │                 │                  │
       ▼                 ▼                  ▼
    AI Agents       Applications          IDEs
```

The architecture must never depend exclusively on MCP.

Some hosts may not expose APIs allowing an external MCP server to change their native model selector.

Therefore the product must support:

* MCP
* API-based routing
* gateway/provider integration
* IDE extensions where supported
* local client
* CLI
* SDK

---

# 3. PRODUCT OBJECTIVES

AgentRouter must optimize five primary dimensions:

```text
1. Quality
2. Cost
3. Latency
4. Reliability
5. Policy compliance
```

The objective is:

> Select the least expensive model that is capable of successfully completing the request while satisfying required quality, latency, context, security, and organizational constraints.

---

# 4. TARGET CUSTOMERS

## Individual developers

Developers using AI coding tools.

## Startups

Teams wanting to control AI spending.

## Mid-size engineering organizations

Teams using multiple AI providers.

## Enterprise / MNC

Organizations requiring:

* SSO
* RBAC
* governance
* security
* audit
* cost control
* private deployment
* centralized model management
* usage analytics

---

# 5. USER PERSONAS

## Developer

Uses AI agents.

Needs:

* minimal configuration
* automatic routing
* fast responses
* transparency

## Team Admin

Needs:

* team policies
* usage
* budgets

## Organization Admin

Needs:

* models
* providers
* policies
* SSO
* users
* teams

## Security Admin

Needs:

* audit
* data policies
* access controls
* security events

## FinOps

Needs:

* cost
* spending
* savings
* forecasts

## CTO/CIO

Needs:

* organizational AI adoption
* ROI
* model usage
* risk
* governance

---

# 6. PRODUCT MODULES

The final platform consists of:

```text
01 Gateway
02 Authentication
03 Tenant Management
04 User Management
05 Team Management
06 Provider Management
07 Model Registry
08 Request Analyzer
09 Routing Engine
10 Cost Engine
11 Policy Engine
12 Escalation Engine
13 Fallback Engine
14 Security Engine
15 MCP Server
16 IDE Integrations
17 Client
18 API
19 CLI
20 SDK
21 Dashboard
22 Analytics
23 Benchmarking
24 Evaluation
25 Audit
26 Billing
27 Notifications
28 Observability
29 Deployment
30 Administration
```

---

# 7. HIGH-LEVEL ARCHITECTURE

```text
                           USERS
                             │
                             ▼
             ┌─────────────────────────────┐
             │ IDE / AI CODING AGENT       │
             │                             │
             │ VS Code                     │
             │ Cursor                      │
             │ Kiro                        │
             │ Claude Code                 │
             │ Codex                       │
             │ JetBrains                   │
             └──────────────┬──────────────┘
                            │
                 MCP / API / Extension
                            │
                            ▼
             ┌─────────────────────────────┐
             │       AGENTROUTER           │
             │                             │
             │ API Gateway                 │
             │ Authentication              │
             │ Request Normalization       │
             │ Security                    │
             │ Request Analyzer             │
             │ Policy Engine               │
             │ Routing Engine              │
             │ Cost Engine                 │
             │ Model Registry              │
             │ Provider Gateway             │
             │ Escalation                  │
             │ Fallback                    │
             └──────────────┬──────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           Provider A    Provider B    Provider C
              │             │             │
              ▼             ▼             ▼
           Models         Models        Models
                            │
                            ▼
                         RESPONSE
                            │
                            ▼
                           IDE
```

---

# 8. CONTROL PLANE

The control plane manages everything except high-volume model traffic.

```text
Control Plane

Organization
Users
Teams
Roles
Policies
Models
Providers
Budgets
Integrations
Billing
Audit
Analytics
```

The control plane should have its own APIs.

---

# 9. DATA PLANE

The data plane processes AI requests.

It must be:

* stateless where possible
* horizontally scalable
* low latency
* fault tolerant

Request:

```text
POST /v1/route
```

Flow:

```text
Authentication
      ↓
Tenant identification
      ↓
Policy check
      ↓
Request analysis
      ↓
Candidate selection
      ↓
Model scoring
      ↓
Model execution
      ↓
Response validation
      ↓
Fallback/escalation
      ↓
Response
```

---

# 10. REQUEST LIFECYCLE

Every request must receive a unique request ID.

Example:

```text
req_01K...
```

Track:

```text
request_id
tenant_id
user_id
team_id
session_id
agent
integration
provider
model
routing_decision
cost
latency
status
```

The request lifecycle:

```text
RECEIVED
   ↓
AUTHENTICATED
   ↓
AUTHORIZED
   ↓
ANALYZING
   ↓
ROUTING
   ↓
EXECUTING
   ↓
VALIDATING
   ↓
COMPLETED
```

Possible failure states:

```text
REJECTED
TIMEOUT
FAILED
FALLBACK
ESCALATED
POLICY_BLOCKED
```

---

# 11. CANONICAL REQUEST

All integrations must be normalized into one internal request structure.

Conceptually:

```json
{
  "request_id": "...",
  "tenant_id": "...",
  "user_id": "...",
  "team_id": "...",
  "session_id": "...",
  "source": "vscode",
  "agent": "agent-name",
  "messages": [],
  "tools": [],
  "context": {},
  "stream": true,
  "constraints": {}
}
```

Every provider adapter converts this into provider-specific format.

---

# 12. MODEL REGISTRY

Create a central model database.

Each model must have:

```text
model_id
provider_id
display_name
version
status
context_window
input_price
output_price
cached_input_price
coding_score
reasoning_score
debugging_score
architecture_score
tool_calling
vision
structured_output
latency_p50
latency_p95
reliability
regions
data_policy
```

Never hardcode these values across services.

---

# 13. PROVIDER GATEWAY

Create a provider abstraction.

Interface:

```text
ProviderAdapter

authenticate()
healthCheck()
listModels()
generate()
stream()
estimateTokens()
normalizeError()
```

Providers can include:

```text
OpenAI
Anthropic
Google
Azure-hosted models
AWS-hosted models
OpenAI-compatible endpoints
Self-hosted inference
Customer internal models
```

Provider adapters must be independently testable.

---

# 14. REQUEST ANALYZER

The analyzer determines the request requirements.

Output:

```json
{
  "task_type": "debugging",
  "complexity": "high",
  "reasoning_requirement": "high",
  "context_requirement": "large",
  "coding_requirement": "high",
  "tool_requirement": "medium",
  "expected_output": "code",
  "confidence": 0.93
}
```

Do not use prompt length alone to determine complexity.

Consider:

* task type
* number of requested operations
* reasoning requirement
* context
* tools
* expected output
* ambiguity
* dependencies
* requested accuracy

---

# 15. TASK CLASSIFICATION

Initial categories:

```text
CODE_GENERATION
CODE_COMPLETION
CODE_REVIEW
DEBUGGING
REFACTORING
TEST_GENERATION
DOCUMENTATION
EXPLANATION
ARCHITECTURE
SECURITY
KUBERNETES
TERRAFORM
CI_CD
DATABASE
SQL
DATA_ANALYSIS
MULTI_STEP_AGENT
RESEARCH
GENERAL
```

The system must allow new categories later.

---

# 16. COMPLEXITY CLASSIFICATION

Use:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Example:

### LOW

```text
Explain this function.
Rename this variable.
Generate a simple test.
```

### MEDIUM

```text
Refactor this service.
Add authentication middleware.
```

### HIGH

```text
Debug a multi-service failure.
Design a production architecture.
```

### CRITICAL

```text
Analyze a complex production failure
across a large distributed system.
```

These are examples, not hardcoded routing rules.

---

# 17. ROUTING ENGINE

The routing engine receives:

```text
Request Analysis
+
Available Models
+
Policies
+
Cost
+
Latency
+
Reliability
+
Context
```

Then creates candidate models.

```text
All Models
    ↓
Capability filter
    ↓
Context filter
    ↓
Policy filter
    ↓
Region filter
    ↓
Availability filter
    ↓
Cost filter
    ↓
Candidate Models
```

Then score candidates.

---

# 18. ROUTING SCORE

Define a configurable scoring function.

Conceptually:

```text
score(model, request) =
    quality_match * quality_weight
  + capability_match * capability_weight
  + context_match * context_weight
  + reliability * reliability_weight
  + latency_score * latency_weight
  - cost_penalty * cost_weight
```

Weights must be configurable.

Never hardcode a single universal preference.

---

# 19. ROUTING MODES

Support:

```text
BALANCED
QUALITY_FIRST
COST_FIRST
LATENCY_FIRST
RELIABILITY_FIRST
POLICY_FIRST
```

Organization administrators can choose the default.

---

# 20. MODEL CANDIDATE FILTERING

A model should be removed before scoring if:

```text
context insufficient
required capability unavailable
organization disallows provider
organization disallows model
region not allowed
provider unhealthy
budget exceeded
model unavailable
```

This avoids selecting impossible candidates.

---

# 21. ROUTING DECISION

Every routing decision must produce an explainable object.

Example:

```json
{
  "selected_model": "provider/model",
  "reason": [
    "High reasoning requirement",
    "Large context required",
    "Organization policy permits model",
    "Provider healthy",
    "Best quality/cost balance"
  ],
  "confidence": 0.92,
  "estimated_cost": 0.14,
  "alternatives": []
}
```

---

# 22. COST ENGINE

Calculate:

```text
input tokens
output tokens
cached tokens
model pricing
provider pricing
request cost
```

Formula:

```text
input_cost =
input_tokens × input_price

output_cost =
output_tokens × output_price

total =
input_cost + output_cost
```

Support provider-specific pricing structures.

---

# 23. COST SAVINGS

Calculate:

```text
actual_cost
baseline_cost
savings
savings_percentage
```

Baseline must be configurable.

For example:

```text
baseline =
organization default model
```

or:

```text
baseline =
highest-cost approved model
```

Never present a misleading savings number.

---

# 24. DYNAMIC ESCALATION

Implement optional escalation.

```text
Cheap model
     ↓
Evaluate
     ↓
Success?
 ┌───┴───┐
YES      NO
 │        │
Return   Escalate
          ↓
       Stronger model
```

Evaluation criteria can include:

* model refusal
* malformed response
* tool failure
* explicit confidence signal
* validation failure
* developer feedback
* automated evaluator

Enterprise administrators must be able to disable escalation.

---

# 25. FALLBACK

Provider failure:

```text
Provider A
    ↓
Timeout
    ↓
Health check
    ↓
Provider B
```

Fallback must respect:

* policy
* region
* security
* model capability
* budget

Never fallback blindly to a prohibited provider.

---

# 26. CIRCUIT BREAKER

For unreliable providers:

```text
Healthy
 ↓
Failures increase
 ↓
Open circuit
 ↓
Stop sending traffic
 ↓
Periodic health check
 ↓
Half-open
 ↓
Healthy
 ↓
Close
```

Configure thresholds.

---

# 27. RATE LIMITING

Implement:

```text
Global
Organization
Team
User
API Key
Provider
Model
```

Use token-aware rate limiting where appropriate.

---

# 28. POLICY ENGINE

Policy decisions must be centralized.

Examples:

```text
allowed_models
blocked_models
allowed_providers
blocked_providers
maximum_cost
maximum_context
allowed_regions
data_classification
escalation_allowed
fallback_allowed
retention_policy
```

Policy evaluation should return:

```json
{
  "allowed": true,
  "reason": "...",
  "restrictions": []
}
```

---

# 29. POLICY HIERARCHY

```text
Platform policy
      ↓
Organization policy
      ↓
Department policy
      ↓
Team policy
      ↓
User policy
      ↓
Request constraints
```

The system must resolve conflicts deterministically.

---

# 30. MULTI-TENANCY

Every enterprise customer is a tenant.

Data model:

```text
Tenant
 ├── Users
 ├── Teams
 ├── Providers
 ├── Models
 ├── Policies
 ├── Requests
 ├── Usage
 ├── Billing
 └── Audit
```

Tenant isolation must exist at every data-access boundary.

---

# 31. AUTHENTICATION

Support:

```text
Email/password where appropriate
OIDC
OAuth
SAML SSO
API keys
Service accounts
Machine credentials
```

Prefer enterprise identity providers for enterprise accounts.

---

# 32. RBAC

Roles:

```text
PLATFORM_ADMIN
ORG_ADMIN
TEAM_ADMIN
DEVELOPER
SECURITY_ADMIN
AUDITOR
BILLING_ADMIN
```

Permissions must be granular.

Example:

```text
models:read
models:write
policies:read
policies:write
billing:read
audit:read
users:write
```

---

# 33. API KEY MANAGEMENT

API keys must:

* be hashed where possible
* never be stored plaintext
* support expiration
* support rotation
* support revocation
* have scopes
* have audit records

Display secrets only at creation time when appropriate.

---

# 34. SECRETS MANAGEMENT

Provider credentials must never be stored in Git.

Use:

```text
Cloud KMS
Secrets Manager
Vault
Kubernetes Secrets
```

depending on deployment.

Support customer-managed credentials.

---

# 35. DATA PRIVACY

Default design:

```text
Do not persist source code unnecessarily.
Do not persist secrets.
Do not persist full conversations unless explicitly enabled.
```

Telemetry should primarily store metadata.

Allow organization-level retention policies.

---

# 36. SENSITIVE DATA

Build detection for:

```text
API keys
Passwords
Tokens
Private keys
Credentials
PII
Secrets
```

Do not accidentally log them.

Logging middleware must redact sensitive fields.

---

# 37. MCP SERVER

MCP server exposes AgentRouter capabilities.

Tools:

```text
analyze_task
recommend_model
estimate_cost
get_available_models
check_policy
route_request
```

Resources can expose appropriate read-only information such as:

```text
model capabilities
routing policies
usage information
```

MCP implementation must follow the current MCP specification and be independently tested.

---

# 38. MCP SECURITY

MCP connections must have:

```text
Authentication
Authorization
Tenant context
Tool permissions
Audit logging
Rate limiting
```

Never allow an MCP client to bypass normal enterprise policies.

---

# 39. IDE INTEGRATION STRATEGY

Build an abstraction:

```text
IntegrationAdapter
```

Capabilities:

```text
supports_mcp
supports_model_provider
supports_model_selection
supports_request_proxy
supports_extension
supports_streaming
supports_auth
```

Each IDE gets a capability profile.

Do not assume all IDEs have identical capabilities.

---

# 40. VS CODE

Build a dedicated integration where supported.

Responsibilities:

```text
Authentication
Configuration
AgentRouter connection
Model/provider configuration
Status
Diagnostics
```

The integration must use officially supported extension/provider mechanisms.

---

# 41. KIRO

Because your own development is happening in Kiro, create a Kiro-specific integration based on the interfaces Kiro actually exposes.

Do not make assumptions about undocumented internal APIs.

Where Kiro supports MCP, provide the AgentRouter MCP configuration.

Where it provides model/provider integration, use that supported mechanism.

---

# 42. CURSOR

Create a separate adapter.

Support only officially exposed mechanisms.

Do not depend on reverse-engineering internal APIs.

---

# 43. CLAUDE CODE / CODEX / OTHER AGENTS

Create adapters only where supported.

The core routing engine must remain completely independent from these integrations.

---

# 44. AGENTROUTER LOCAL CLIENT

Build a local client for developer machines.

Responsibilities:

```text
login
configuration
authentication
secure credential storage
connection management
MCP
diagnostics
updates
telemetry
```

Architecture:

```text
IDE
 ↓
Local Client
 ↓
AgentRouter Cloud/Private Deployment
```

---

# 45. API GATEWAY

Public APIs:

```text
/v1/auth
/v1/models
/v1/providers
/v1/route
/v1/generate
/v1/usage
/v1/policies
/v1/organizations
/v1/teams
/v1/users
/v1/audit
```

Use OpenAPI.

Generate API documentation from the schema.

---

# 46. STREAMING

AI coding agents often require streaming.

Support:

```text
stream=true
```

Gateway must forward streaming efficiently.

Don't buffer an entire response unnecessarily.

---

# 47. ERROR NORMALIZATION

Providers return different errors.

Normalize internally:

```text
AUTHENTICATION_ERROR
RATE_LIMIT
MODEL_UNAVAILABLE
CONTEXT_TOO_LARGE
PROVIDER_ERROR
TIMEOUT
INVALID_REQUEST
CONTENT_POLICY
UNKNOWN
```

Then map to appropriate API responses.

---

# 48. CLI

Command structure:

```bash
agentrouter login
agentrouter logout
agentrouter configure
agentrouter status
agentrouter models
agentrouter providers
agentrouter route
agentrouter test
agentrouter usage
agentrouter diagnose
agentrouter policy
```

CLI must support machine-readable output.

---

# 49. SDK

Provide:

```text
TypeScript
Python
Go
```

Core API:

```text
route()
generate()
stream()
getModels()
getUsage()
```

SDKs must use the same canonical API contracts.

---

# 50. DASHBOARD

Dashboard sections:

```text
Overview
AI Usage
Cost
Savings
Models
Providers
Routing
Teams
Users
Policies
Security
Audit
Billing
Settings
```

---

# 51. DEVELOPER DASHBOARD

Show:

```text
Requests
Tokens
Cost
Savings
Models used
Latency
Failures
```

Developers should see only authorized data.

---

# 52. ADMIN DASHBOARD

Show:

```text
Organization requests
Organization cost
Organization savings
Users
Teams
Models
Providers
Policy violations
Security events
```

---

# 53. ROUTING ANALYTICS

Every request should have:

```text
selected model
candidate models
rejected models
rejection reasons
routing score
routing mode
policy decisions
```

Admins can investigate routing behavior.

---

# 54. COST ANALYTICS

Break down by:

```text
organization
team
user
model
provider
day
month
task type
project
```

---

# 55. FINOPS

Provide:

```text
Current spend
Forecast
Budget
Actual vs budget
Cost per developer
Cost per team
Cost per model
Savings
```

---

# 56. BUDGET MANAGEMENT

Budgets:

```text
Organization
Team
User
Project
```

Thresholds:

```text
50%
75%
90%
100%
```

Actions:

```text
Notify
Restrict expensive models
Block requests
```

---

# 57. NOTIFICATIONS

Support:

```text
Email
Webhook
Slack
Microsoft Teams
```

Events:

```text
budget threshold
provider failure
policy violation
unusual usage
high latency
service outage
```

---

# 58. AUDIT LOG

Record administrative events:

```text
user created
user deleted
role changed
provider added
model added
policy changed
API key created
API key revoked
budget changed
integration configured
```

Audit records must be immutable from normal customer workflows.

---

# 59. OBSERVABILITY

Use OpenTelemetry-compatible instrumentation.

Metrics:

```text
request_total
request_success_total
request_failure_total
request_latency
provider_latency
routing_latency
tokens_total
cost_total
fallback_total
escalation_total
policy_block_total
```

---

# 60. DISTRIBUTED TRACING

Trace:

```text
Gateway
 ↓
Analyzer
 ↓
Policy
 ↓
Router
 ↓
Provider
```

Use a common request/trace ID.

---

# 61. DATABASE

Use PostgreSQL for transactional data.

Core tables:

```text
organizations
users
teams
memberships
roles
permissions
providers
models
model_capabilities
model_pricing
policies
policy_rules
requests
routing_decisions
provider_requests
usage_records
cost_records
budgets
audit_events
api_keys
service_accounts
integrations
subscriptions
invoices
notifications
```

Use migrations.

Never manually modify production schema.

---

# 62. ANALYTICS DATABASE

At scale, separate transactional workloads from analytical workloads.

Potential architecture:

```text
PostgreSQL
    ↓
Event stream
    ↓
Analytics store
```

Use an analytical database such as ClickHouse when the workload justifies it.

---

# 63. REDIS

Use Redis for:

```text
short-lived cache
rate limiting
distributed locks where necessary
provider health state
session data where appropriate
```

Never treat Redis as the authoritative database.

---

# 64. EVENT SYSTEM

Publish events such as:

```text
request.completed
request.failed
routing.selected
routing.escalated
provider.failed
policy.blocked
budget.threshold
user.created
```

Consumers:

```text
analytics
notifications
billing
audit
```

This decouples the system.

---

# 65. EVENT IDEMPOTENCY

Every event must have an ID.

Consumers must handle duplicates safely.

Never assume exactly-once delivery unless the infrastructure truly guarantees it.

---

# 66. KUBERNETES

Production deployment must be Kubernetes-ready.

Components:

```text
gateway
auth
router
analyzer
policy
provider
analytics-worker
billing
notification
dashboard
```

Not every component must be a separate deployment if unnecessary.

---

# 67. HELM

Create a production Helm chart:

```text
charts/
└── agentrouter/
    ├── Chart.yaml
    ├── values.yaml
    ├── values-production.yaml
    ├── templates/
    └── README.md
```

Support:

```text
replicas
resources
autoscaling
ingress
TLS
secrets
database
redis
observability
network policies
```

---

# 68. TERRAFORM

Create infrastructure modules for supported cloud environments.

Example:

```text
terraform/
├── modules/
│   ├── network
│   ├── kubernetes
│   ├── database
│   ├── redis
│   ├── object-storage
│   └── monitoring
└── environments/
```

---

# 69. DEPLOYMENT MODES

Support:

## SaaS

```text
Customer
 ↓
AgentRouter Cloud
```

## Dedicated

```text
Customer
 ↓
Dedicated AgentRouter environment
```

## Customer cloud

```text
Customer AWS/Azure/GCP
 ↓
AgentRouter
```

## Self-hosted Kubernetes

```text
Customer Kubernetes
 ↓
Helm
 ↓
AgentRouter
```

---

# 70. HIGH AVAILABILITY

Use:

```text
multiple replicas
multiple zones
health checks
load balancing
database backups
provider failover
```

No single application replica should be required for service availability.

---

# 71. AUTOSCALING

Scale gateway and routing workloads based on:

```text
CPU
memory
request rate
latency
queue depth
```

Do not blindly scale every service identically.

---

# 72. DISASTER RECOVERY

Document:

```text
RPO
RTO
backup frequency
restore procedures
database recovery
configuration recovery
regional failure
```

Perform restoration tests.

---

# 73. CI/CD

Every pull request:

```text
lint
format
unit tests
integration tests
security scan
dependency scan
build
```

Main branch:

```text
build images
scan images
deploy staging
E2E
approval
production
```

---

# 74. CONTAINER SECURITY

Every image:

```text
minimal base image
non-root user
dependency scanning
SBOM
image signing where appropriate
vulnerability scanning
```

---

# 75. TESTING STRATEGY

Implement:

```text
unit tests
integration tests
API tests
MCP tests
provider contract tests
E2E tests
security tests
load tests
failure tests
routing evaluation tests
```

---

# 76. ROUTING TEST DATASET

Create a benchmark dataset:

```text
prompt
task_type
complexity
required_capabilities
candidate_models
expected_best_model
actual_selected_model
cost
quality
latency
```

Use it for regression testing.

---

# 77. MODEL BENCHMARKING

Benchmark models against:

```text
coding
debugging
refactoring
testing
Kubernetes
Terraform
architecture
SQL
security
agentic workflows
```

Measure:

```text
quality
success rate
cost
latency
context handling
tool usage
```

---

# 78. ROUTER QUALITY METRICS

Track:

```text
routing accuracy
successful completion rate
cost savings
quality loss
latency
fallback rate
escalation rate
```

Important metric:

```text
Cost reduction without unacceptable quality degradation.
```

---

# 79. HUMAN FEEDBACK

Allow feedback:

```text
good
bad
too slow
wrong model
incorrect answer
```

Use it for analysis and future routing improvements.

---

# 80. MODEL REGISTRY LIFECYCLE

Model states:

```text
DISCOVERED
BENCHMARKING
APPROVED
ACTIVE
DEPRECATED
RETIRED
```

New model:

```text
Discover
 ↓
Register
 ↓
Benchmark
 ↓
Policy review
 ↓
Approve
 ↓
Activate
```

---

# 81. MODEL HEALTH

Continuously track:

```text
availability
latency
error rate
rate-limit frequency
provider status
```

A model's routing score should account for current health.

---

# 82. MODEL DEPRECATION

When a model is deprecated:

```text
Stop new routing
 ↓
Notify administrators
 ↓
Recommend replacement
 ↓
Migrate policies
```

---

# 83. SECURITY ARCHITECTURE

Security must exist across:

```text
Identity
Network
Application
Data
Secrets
Infrastructure
Tenant isolation
Logging
```

---

# 84. NETWORK SECURITY

Use:

```text
TLS
private networking where possible
network policies
firewalls
restricted outbound access
```

For private deployments, support customer network architecture.

---

# 85. TENANT SECURITY

Every service must verify tenant context.

Never trust:

```text
tenant_id
```

from a client request without validating it against authenticated identity.

---

# 86. PROMPT INJECTION

AgentRouter should detect suspicious prompt patterns where feasible, but must not pretend that detection is perfect.

Security controls should include:

```text
tool restrictions
provider policies
data boundaries
least privilege
audit
```

---

# 87. TOOL SECURITY

Tools requested by agents must have explicit authorization.

Don't allow an agent to bypass:

```text
organization policies
user permissions
network restrictions
```

through tool execution.

---

# 88. ADMIN SECURITY

Require stronger authentication for administrative operations.

Support:

```text
MFA through identity provider
short-lived sessions
session revocation
audit
```

---

# 89. DASHBOARD SECURITY

Frontend must never be trusted for authorization.

Every privileged action must be authorized by the backend.

---

# 90. BILLING

SaaS billing must support:

```text
plan
seats
usage
tokens
overages
invoices
payment status
```

Billing must be isolated from routing logic.

---

# 91. CUSTOMER ONBOARDING

Target flow:

```text
Create account
 ↓
Create organization
 ↓
Configure SSO
 ↓
Connect providers
 ↓
Select models
 ↓
Create policies
 ↓
Install client
 ↓
Connect IDE
 ↓
Test request
 ↓
Enable routing
```

---

# 92. DIAGNOSTICS

Create:

```bash
agentrouter diagnose
```

It should check:

```text
authentication
network
endpoint
provider connectivity
model availability
MCP
configuration
permissions
```

Return actionable output.

---

# 93. SUPPORTABILITY

Every request should be traceable through:

```text
request ID
trace ID
routing decision
provider request
provider response status
```

Support engineers must be able to diagnose failures without automatically viewing sensitive customer content.

---

# 94. DOCUMENTATION

Create documentation for:

```text
Developer
Admin
Security
FinOps
Platform Engineer
API Developer
Self-hosting
Kubernetes
MCP
IDE integrations
Troubleshooting
```

Documentation should contain working examples.

---

# 95. API DOCUMENTATION

Use OpenAPI.

Generate:

```text
API reference
authentication documentation
request examples
response examples
errors
rate limits
SDK examples
```

---

# 96. DEVELOPER EXPERIENCE

Installation target:

```text
Install
 ↓
Login
 ↓
Select organization
 ↓
Connect IDE
 ↓
Start coding
```

The developer shouldn't need to understand the internal routing architecture.

---

# 97. PROJECT STRUCTURE

Recommended monorepo:

```text
agentrouter/
│
├── apps/
│   ├── dashboard/
│   ├── api/
│   └── docs/
│
├── services/
│   ├── gateway/
│   ├── router/
│   ├── analyzer/
│   ├── policy/
│   ├── providers/
│   ├── registry/
│   ├── analytics/
│   ├── billing/
│   └── notifications/
│
├── integrations/
│   ├── mcp/
│   ├── vscode/
│   ├── kiro/
│   ├── cursor/
│   ├── claude-code/
│   └── jetbrains/
│
├── packages/
│   ├── api-contracts/
│   ├── shared-types/
│   ├── auth/
│   ├── logging/
│   ├── telemetry/
│   └── security/
│
├── cli/
├── sdk/
│   ├── typescript/
│   ├── python/
│   └── go/
│
├── benchmark/
├── database/
├── deployments/
│   ├── docker/
│   ├── kubernetes/
│   └── helm/
│
├── infrastructure/
│   └── terraform/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── security/
│   ├── load/
│   └── routing/
│
├── docs/
└── .github/
```

---

# 98. ENGINEERING PRINCIPLES

Kiro must follow these rules:

### Rule 1

Do not hardcode provider-specific behavior into the routing engine.

### Rule 2

Do not hardcode model pricing.

### Rule 3

Do not couple the core engine to one IDE.

### Rule 4

Do not couple the product to MCP.

### Rule 5

Do not store secrets in source control.

### Rule 6

Do not log raw prompts by default.

### Rule 7

Do not bypass authorization.

### Rule 8

Do not use undocumented IDE APIs when an official integration mechanism exists.

### Rule 9

Every service must have tests.

### Rule 10

Every production API must have documentation.

---

# 99. CODE QUALITY

Require:

```text
formatting
linting
static analysis
type safety
error handling
structured logging
tests
documentation
```

No TODO-driven production functionality.

If functionality is not implemented, mark it explicitly rather than pretending it works.

---

# 100. CONFIGURATION

Configuration must be environment-driven.

Never embed:

```text
API keys
passwords
production URLs
tenant IDs
```

Use:

```text
environment variables
configuration files
secret managers
```

---

# 101. ENVIRONMENTS

Maintain:

```text
local
development
staging
production
```

Each environment must have separate credentials.

---

# 102. DATABASE MIGRATION

All schema changes must use migrations.

Deployment:

```text
Migration
 ↓
Application deployment
```

Migration must be backwards-compatible where rolling deployments require it.

---

# 103. API VERSIONING

Use:

```text
/v1/
```

for public APIs.

Do not make breaking changes without a migration strategy.

---

# 104. FEATURE FLAGS

Use feature flags for:

```text
new routing algorithm
new provider
new integration
new dashboard feature
```

This allows controlled rollout.

---

# 105. ADMIN CONFIGURATION

The administrator must be able to manage:

```text
providers
models
routing
policies
budgets
users
teams
integrations
security
retention
```

through UI and API.

---

# 106. ROUTING CONFIGURATION EXAMPLE

Conceptually:

```yaml
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
```

Do not treat this exact weighting as universally optimal. Make it configurable and benchmark it.

---

# 107. PROJECT / APPLICATION CONTEXT

Eventually allow organizations to associate usage with:

```text
project
repository
application
environment
```

For example:

```text
Company
 ↓
Team
 ↓
Project
 ↓
Repository
 ↓
AI requests
```

This enables project-level FinOps.

---

# 108. COST FORECASTING

Based on historical usage:

```text
Current usage
+
Growth
+
Model pricing
```

estimate:

```text
month-end spend
```

Clearly label forecasts as estimates.

---

# 109. ANOMALY DETECTION

Detect:

```text
sudden token spike
sudden cost spike
unusual model usage
unusual request volume
```

Notify administrators.

---

# 110. MODEL RECOMMENDATION EXPLANATION

Every recommendation must answer:

```text
What was requested?
What capabilities were required?
Which models were considered?
Which were rejected?
Why was this model selected?
What was estimated cost?
```

This creates trust.

---

# 111. ENTERPRISE DATA RESIDENCY

Model/provider selection may depend on region.

Example:

```text
EU data
 ↓
EU-approved provider only
```

Routing must consider this before selecting a model.

---

# 112. CUSTOMER-MANAGED KEYS

Support:

```text
AgentRouter-managed provider credentials
```

and:

```text
Customer-managed provider credentials
```

Never expose customer credentials to ordinary developers.

---

# 113. PRIVATE DEPLOYMENT

Private deployment should allow:

```text
No public internet access
Private model endpoints
Private databases
Private object storage
Customer identity provider
Customer monitoring
```

where architecture permits.

---

# 114. SELF-HOSTED INSTALLATION

Target:

```bash
helm repo add agentrouter ...
helm install agentrouter ...
```

The exact installation command should be finalized only after the Helm repository is established.

The chart must support production configuration.

---

# 115. CLOUD ARCHITECTURE

SaaS:

```text
DNS
 ↓
CDN/WAF where appropriate
 ↓
Load Balancer
 ↓
API Gateway
 ↓
Kubernetes
 ↓
Services
 ↓
Database / Redis / Analytics
```

---

# 116. WAF

For public SaaS endpoints use appropriate:

```text
WAF
DDoS protection
TLS
rate limiting
bot protection
```

depending on infrastructure.

---

# 117. BACKUPS

Back up:

```text
PostgreSQL
configuration
critical metadata
customer-defined configuration
```

Do not blindly back up transient caches.

---

# 118. RESTORE TEST

Regularly test:

```text
backup
 ↓
restore
 ↓
validate
 ↓
application startup
 ↓
data integrity
```

---

# 119. INCIDENT RESPONSE

Create:

```text
incident-response.md
```

Include:

```text
severity
detection
communication
containment
recovery
postmortem
```

---

# 120. SECURITY INCIDENT

Define procedures for:

```text
credential exposure
tenant isolation failure
unauthorized access
provider compromise
data leakage
service compromise
```

---

# 121. COMPLIANCE

Prepare controls for future:

```text
SOC 2
ISO 27001
GDPR
```

Do not claim certification before certification actually exists.

---

# 122. LEGAL / COMMERCIAL

Before customer deployment, establish:

```text
Terms of Service
Privacy Policy
Data Processing Agreement
Acceptable Use Policy
Security documentation
Subprocessor documentation
SLA
Support policy
```

Have qualified legal counsel review these.

---

# 123. CUSTOMER SECURITY QUESTIONNAIRE

Prepare standard answers for:

```text
data storage
encryption
authentication
SSO
RBAC
logging
retention
subprocessors
incident response
backup
DR
data residency
```

This can significantly reduce enterprise sales friction.

---

# 124. PRODUCT ANALYTICS

Track product-level metrics:

```text
active organizations
active developers
requests
routing decisions
cost savings
retention
provider usage
```

Avoid collecting unnecessary personal data.

---

# 125. BUSINESS METRICS

Monitor:

```text
customer acquisition
activation
active users
requests per customer
AI spend
savings
retention
conversion
```

---

# 126. FINAL CUSTOMER EXPERIENCE

The ideal customer experience:

```text
Company signs up
       ↓
Admin configures organization
       ↓
Connect identity
       ↓
Connect models
       ↓
Define policies
       ↓
Install AgentRouter
       ↓
Connect IDE
       ↓
Developer starts working
       ↓
AgentRouter automatically routes requests
       ↓
Dashboard measures everything
       ↓
Company sees cost + quality + governance
```

---

# 127. THE CRITICAL PRODUCT DIFFERENTIATOR

The platform should eventually learn:

```text
Task type
      ↓
Candidate models
      ↓
Historical success
      ↓
Quality
      ↓
Cost
      ↓
Latency
      ↓
Best model
```

Over time:

```text
More requests
      ↓
More evaluation data
      ↓
Better routing
      ↓
Better savings
      ↓
Better product
```

This creates a defensible routing intelligence layer.

---

# 128. WHAT THE ROUTER MUST NEVER DO

Never:

```text
select a prohibited model
ignore tenant policy
leak tenant data
expose provider credentials
log secrets
bypass authorization
claim unsupported IDE control
pretend a failed request succeeded
calculate fake savings
```

---

# 129. DEVELOPER TRANSPARENCY

Provide an optional routing indicator:

```text
AgentRouter
─────────────
Task: Debugging
Complexity: High
Model: Model X
Reason: High reasoning requirement
```

The organization can configure how much information developers see.

---

# 130. FINAL DEPLOYMENT ARCHITECTURE

```text
                         INTERNET
                            │
                            ▼
                     DNS / WAF / TLS
                            │
                            ▼
                     LOAD BALANCER
                            │
                            ▼
                  ┌──────────────────┐
                  │  API GATEWAY      │
                  └────────┬─────────┘
                           │
             ┌─────────────┼──────────────┐
             │             │              │
             ▼             ▼              ▼
        Authentication   Routing       Dashboard
                           │
                ┌──────────┼───────────┐
                │          │           │
                ▼          ▼           ▼
             Analyzer    Policy      Registry
                │          │           │
                └──────────┼───────────┘
                           │
                       Cost Engine
                           │
                     Provider Gateway
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Provider A    Provider B    Provider C
             │             │             │
             ▼             ▼             ▼
           Models        Models        Models


                 CONTROL PLANE
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       PostgreSQL     Redis      Analytics
                                    │
                                    ▼
                               Dashboards


                 PLATFORM
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Kubernetes      Helm       Terraform
          │
          ▼
       Monitoring
          │
          ▼
    OpenTelemetry
```

---

# 131. FINAL REPOSITORY

Your final GitHub repository should contain:

```text
agentrouter/
├── apps/
├── services/
├── integrations/
├── clients/
├── sdk/
├── cli/
├── dashboard/
├── benchmark/
├── database/
├── deployments/
├── infrastructure/
├── tests/
├── docs/
├── SECURITY.md
├── LICENSE
├── CONTRIBUTING.md
└── README.md
```

GitHub is the **source/distribution location**.

Production runs in:

```text
Kubernetes
Cloud
Customer infrastructure
or local developer machine
```

depending on deployment model.

---

# 132. IMPLEMENTATION ORDER FOR KIRO

This is the most important section for you.

Give Kiro the master document first.

Then instruct Kiro to implement in this dependency order:

```text
01. Repository foundation
02. Development environment
03. Shared types/contracts
04. Database schema
05. Authentication
06. Multi-tenancy
07. RBAC
08. Model registry
09. Provider abstraction
10. Provider adapters
11. Canonical request model
12. API gateway
13. Request analyzer
14. Routing engine
15. Cost engine
16. Policy engine
17. Escalation engine
18. Fallback engine
19. Security/redaction
20. Observability
21. Event system
22. Analytics
23. MCP server
24. AgentRouter local client
25. CLI
26. SDKs
27. IDE integrations
28. Dashboard
29. Admin console
30. Billing
31. Notifications
32. Benchmarking
33. Routing evaluation
34. Kubernetes
35. Helm
36. Terraform
37. CI/CD
38. HA
39. DR
40. Security testing
41. Load testing
42. E2E testing
43. Documentation
44. Customer onboarding
45. Production hardening
46. Enterprise deployment validation
```

Kiro should **not jump randomly between these areas**.

Each stage must pass its acceptance criteria before moving forward.

---

# 133. KIRO'S IMPLEMENTATION RULE

Use this pattern for every phase:

```text
UNDERSTAND
    ↓
DESIGN
    ↓
IMPLEMENT
    ↓
UNIT TEST
    ↓
INTEGRATION TEST
    ↓
SECURITY CHECK
    ↓
DOCUMENT
    ↓
VALIDATE
    ↓
COMMIT
```

Do not let Kiro simply generate thousands of lines of code without validation.

---

# 134. DEFINITION OF DONE

A component is not complete because the code compiles.

A component is complete only when:

```text
✓ implementation exists
✓ unit tests exist
✓ integration tests exist where applicable
✓ errors handled
✓ security considered
✓ logging implemented
✓ metrics implemented where applicable
✓ documentation exists
✓ API contract exists
✓ configuration exists
✓ deployment exists where applicable
✓ CI validates it
```

---

# 135. PRODUCTION DEFINITION OF DONE

The entire platform is production-ready only when:

```text
✓ SaaS deployment works
✓ private deployment works
✓ Kubernetes deployment works
✓ Helm installation works
✓ authentication works
✓ SSO works
✓ RBAC works
✓ multi-tenancy works
✓ provider routing works
✓ model routing works
✓ cost calculation works
✓ policies work
✓ escalation works
✓ fallback works
✓ MCP works
✓ supported IDE integrations work
✓ dashboard works
✓ analytics works
✓ audit works
✓ billing works
✓ monitoring works
✓ alerts work
✓ backup works
✓ restore tested
✓ security tests pass
✓ load tests pass
✓ E2E tests pass
✓ documentation complete
✓ customer onboarding works
```

---

# 136. THE FIRST THING YOU SHOULD GIVE KIRO

Do **not** immediately tell Kiro:

> "Build AgentRouter."

Instead give Kiro a system-level instruction like this:

You are the principal architect and senior engineering agent responsible for implementing AgentRouter, an enterprise-grade AI Model Routing, Optimization and Governance Platform.

The attached/preceding AgentRouter Master Engineering Specification is the source of truth for the target architecture, product capabilities, security requirements, deployment model, integrations, APIs, infrastructure, testing requirements, and production-readiness requirements.

Your responsibility is to implement the complete system end-to-end.

Important engineering principles:

1. Do not treat MCP as the product. MCP is one integration layer.
2. Keep the core routing engine independent from any specific IDE, MCP implementation, or model provider.
3. Use provider adapters rather than provider-specific logic throughout the application.
4. Use a canonical internal request format.
5. Implement strong multi-tenant isolation.
6. Never store secrets in source code.
7. Never log secrets or sensitive customer content by default.
8. Do not rely on undocumented IDE APIs.
9. Do not claim an integration capability unless it is actually supported and tested.
10. Every production capability must have tests.
11. Every major service must have structured logging, error handling and appropriate telemetry.
12. All public APIs must be documented.
13. All database changes must use migrations.
14. All production configuration must be environment/configuration driven.
15. Prefer simple, maintainable architecture over unnecessary microservice complexity.
16. Do not create placeholder implementations and mark them as complete.
17. When an external provider or IDE has a capability limitation, implement the correct supported integration mechanism and document the limitation.
18. Never weaken security or tenant isolation to make a feature easier to implement.
19. Do not fabricate routing-quality, cost-savings, compatibility, or benchmark results.
20. Keep the architecture extensible so new models, providers and IDE integrations can be added without changing the core routing engine.

Implementation process for every phase:

UNDERSTAND
→ inspect the current repository and existing implementation

DESIGN
→ determine the smallest correct architecture consistent with the master specification

IMPLEMENT
→ write production-quality code

TEST
→ add unit, integration and relevant end-to-end tests

SECURITY
→ review authentication, authorization, secrets, tenant isolation and data handling

OBSERVABILITY
→ add appropriate logs, metrics and traces

DOCUMENT
→ update the relevant documentation

VALIDATE
→ run tests, linting, builds and relevant deployment validation

REPORT
→ summarize what was implemented, what was tested, files changed, and any genuine external limitation

Do not move to a later architectural phase until the current phase is functional and validated.

Maintain a living implementation status document:

docs/IMPLEMENTATION_STATUS.md

For every major component record:

* status
* implementation location
* tests
* configuration
* deployment status
* known limitations
* remaining work

Maintain architecture documentation as implementation evolves, but do not change the target product requirements without explicitly identifying the architectural reason for the change.

The final system must support:

* intelligent model routing
* model registry
* multiple model providers
* task analysis
* complexity analysis
* capability matching
* cost optimization
* latency optimization
* reliability-aware routing
* policy-based routing
* dynamic escalation
* provider fallback
* enterprise authentication
* SSO
* RBAC
* multi-tenancy
* security controls
* privacy controls
* MCP
* supported IDE integrations
* local developer client
* API
* CLI
* SDKs
* dashboard
* analytics
* FinOps
* audit
* billing
* benchmarking
* routing evaluation
* Kubernetes
* Helm
* Terraform
* CI/CD
* high availability
* disaster recovery
* production observability
* enterprise deployment

Start by inspecting the repository.

Do not implement the entire system in one uncontrolled generation.

First establish the repository architecture, engineering standards, shared contracts, configuration system, database foundation, testing foundation and implementation tracking.

Then implement the system according to the dependency order defined in the Master Engineering Specification.

The goal is not to produce a prototype that merely demonstrates the idea.

The goal is to produce a production-grade enterprise platform that can be deployed, operated, secured, monitored, tested and maintained by real organizations.

---

# 137. THEN YOUR KIRO PROMPTS

After that master instruction, don't give Kiro huge random prompts.

Use phase prompts.

For example:

Start the next implementation phase defined by the AgentRouter Master Engineering Specification.

First inspect the current repository and docs/IMPLEMENTATION_STATUS.md.

Determine exactly which phase and components are currently ready to implement.

Before changing code:

1. Explain the intended implementation.
2. Identify dependencies.
3. Identify files/modules that will be created or modified.
4. Identify database/API changes.
5. Identify security considerations.
6. Identify tests required.

Then implement the phase completely.

After implementation:

1. Run unit tests.
2. Run integration tests where applicable.
3. Run linting/type checks/builds.
4. Validate configuration.
5. Validate security-sensitive paths.
6. Update documentation.
7. Update docs/IMPLEMENTATION_STATUS.md.
8. Report exactly what works and what remains.

Do not skip tests.
Do not create fake implementations.
Do not mark unsupported external integrations as complete.
Do not move to unrelated phases.

Then repeat that approach phase by phase.

---

# 138. YOUR DEVELOPMENT MACHINE

Because you're doing this solo, your development environment should eventually have:

```text
Git
Docker
Kubernetes
Helm
Terraform
Go
Python
Node.js
PostgreSQL
Redis
```

For local Kubernetes, use an appropriate local cluster such as:

```text
kind
or
minikube
```

depending on your workflow.

---

# 139. HOW YOU SHOULD WORK WITH KIRO

Your role shouldn't be:

> "Kiro, write the entire company."

Your role should be:

```text
You = Product owner + architect + reviewer

Kiro = implementation agent
```

Your loop:

```text
You define requirement
       ↓
Kiro designs
       ↓
Kiro implements
       ↓
Kiro tests
       ↓
You review
       ↓
Kiro fixes
       ↓
Commit
```

This will dramatically reduce the chance of accumulating a huge amount of technically inconsistent generated code.

---

# 140. VERY IMPORTANT: DON'T MEASURE THE PROJECT BY HOURS

You said you're prepared to work 18 hours a day and don't care how many days it takes.

I understand the commitment, but I wouldn't use **18-hour days as the engineering strategy**. With a system this security-sensitive and infrastructure-heavy, exhaustion creates exactly the bugs that are most dangerous in an enterprise product—authentication mistakes, tenant-isolation bugs, bad migrations, credential leaks, and incorrect routing.

Measure progress by:

```text
completed capability
+
passing tests
+
security validation
+
deployment validation
```

not by hours spent.

---

# 141. THE FINAL PRODUCT YOU ARE TRYING TO REACH

When everything is complete, your product should essentially be:

```text
                 AGENTROUTER
                      │
       ┌──────────────┼───────────────┐
       │              │               │
    Developer      Enterprise       Platform
       │              │               │
       ▼              ▼               ▼
      IDE          Governance       Analytics
       │              │               │
       └──────────────┼───────────────┘
                      │
                Intelligent
                Model Router
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     Quality         Cost          Latency
       │              │              │
       └──────────────┼──────────────┘
                      ▼
              Optimal Model
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Provider A  Provider B  Provider C
```

The customer buys **the routing and governance platform**, not an MCP server.

MCP, IDE integrations, API, CLI and SDK are the ways they access it.

---

## One final recommendation before you start

Because you're planning to take this to **real MNC customers**, I would make one thing non-negotiable:

**Build the first customer-grade vertical all the way through before building every possible integration.**

That means the complete chain should actually work:

```text
Kiro/Supported IDE
       ↓
AgentRouter Client
       ↓
Authentication
       ↓
Tenant
       ↓
Request Analyzer
       ↓
Policy Engine
       ↓
Routing Engine
       ↓
Cost Engine
       ↓
Provider Gateway
       ↓
Model Provider
       ↓
Streaming Response
       ↓
IDE
       ↓
Telemetry
       ↓
Dashboard
```
