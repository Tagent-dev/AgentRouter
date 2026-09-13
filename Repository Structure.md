
# AgentRouter — Final Repository Structure

```text
agentrouter/
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── security.yml
│   │   ├── build-images.yml
│   │   ├── deploy-staging.yml
│   │   └── deploy-production.yml
│   │
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── dependabot.yml
│
├── apps/
│   │
│   ├── dashboard/
│   │   ├── src/
│   │   ├── public/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── admin-console/
│   │   ├── src/
│   │   ├── public/
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── api/
│   │   ├── src/
│   │   ├── tests/
│   │   └── README.md
│   │
│   └── docs/
│       ├── content/
│       ├── public/
│       └── README.md
│
├── services/
│   │
│   ├── gateway/
│   │   ├── cmd/
│   │   ├── internal/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── router/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── engine/
│   │   │   ├── scoring/
│   │   │   ├── candidates/
│   │   │   ├── strategies/
│   │   │   ├── escalation/
│   │   │   └── fallback/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── analyzer/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── classifier/
│   │   │   ├── complexity/
│   │   │   ├── capabilities/
│   │   │   ├── context/
│   │   │   └── prompt-analysis/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── policy/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── engine/
│   │   │   ├── rules/
│   │   │   ├── evaluation/
│   │   │   └── inheritance/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── providers/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── gateway/
│   │   │   ├── adapters/
│   │   │   ├── health/
│   │   │   ├── failover/
│   │   │   └── normalization/
│   │   │
│   │   │   ├── openai/
│   │   │   ├── anthropic/
│   │   │   ├── google/
│   │   │   ├── azure/
│   │   │   ├── aws/
│   │   │   └── compatible/
│   │   │
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── registry/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── models/
│   │   │   ├── providers/
│   │   │   ├── capabilities/
│   │   │   ├── pricing/
│   │   │   └── lifecycle/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── cost-engine/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── pricing/
│   │   │   ├── estimation/
│   │   │   ├── calculation/
│   │   │   └── savings/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── analytics/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── ingestion/
│   │   │   ├── aggregation/
│   │   │   ├── metrics/
│   │   │   └── reports/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── billing/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── subscriptions/
│   │   │   ├── usage/
│   │   │   ├── invoices/
│   │   │   └── payments/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── notifications/
│   │   ├── cmd/
│   │   ├── internal/
│   │   │   ├── email/
│   │   │   ├── webhook/
│   │   │   ├── slack/
│   │   │   └── teams/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   └── audit/
│       ├── cmd/
│       ├── internal/
│       │   ├── events/
│       │   ├── storage/
│       │   └── queries/
│       ├── tests/
│       ├── Dockerfile
│       └── README.md
│
├── integrations/
│   │
│   ├── mcp/
│   │   ├── server/
│   │   │   ├── tools/
│   │   │   ├── resources/
│   │   │   ├── prompts/
│   │   │   ├── auth/
│   │   │   └── server/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── vscode/
│   │   ├── src/
│   │   ├── resources/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── kiro/
│   │   ├── src/
│   │   ├── config/
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── cursor/
│   │   ├── src/
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── claude-code/
│   │   ├── src/
│   │   ├── tests/
│   │   └── README.md
│   │
│   └── jetbrains/
│       ├── src/
│       ├── tests/
│       └── README.md
│
├── clients/
│   │
│   ├── desktop/
│   │   ├── src/
│   │   ├── tests/
│   │   └── README.md
│   │
│   └── local-agent/
│       ├── src/
│       ├── config/
│       ├── tests/
│       └── README.md
│
├── cli/
│   ├── cmd/
│   │   ├── login/
│   │   ├── logout/
│   │   ├── configure/
│   │   ├── status/
│   │   ├── models/
│   │   ├── providers/
│   │   ├── route/
│   │   ├── usage/
│   │   ├── diagnose/
│   │   └── policy/
│   │
│   ├── internal/
│   ├── tests/
│   ├── Dockerfile
│   └── README.md
│
├── sdk/
│   │
│   ├── typescript/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── python/
│   │   ├── agentrouter/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── go/
│       ├── agentrouter/
│       ├── tests/
│       ├── go.mod
│       └── README.md
│
├── packages/
│   │
│   ├── api-contracts/
│   ├── shared-types/
│   ├── auth/
│   ├── authorization/
│   ├── tenant/
│   ├── logging/
│   ├── telemetry/
│   ├── errors/
│   ├── security/
│   ├── redaction/
│   ├── configuration/
│   ├── events/
│   ├── validation/
│   └── testing/
│
├── database/
│   │
│   ├── migrations/
│   ├── seeds/
│   ├── schemas/
│   ├── queries/
│   ├── views/
│   └── README.md
│
├── benchmark/
│   │
│   ├── datasets/
│   │   ├── coding/
│   │   ├── debugging/
│   │   ├── refactoring/
│   │   ├── kubernetes/
│   │   ├── terraform/
│   │   ├── sql/
│   │   ├── architecture/
│   │   └── security/
│   │
│   ├── runners/
│   ├── evaluators/
│   ├── reports/
│   └── README.md
│
├── evaluation/
│   │
│   ├── routing/
│   ├── quality/
│   ├── cost/
│   ├── latency/
│   ├── reliability/
│   └── README.md
│
├── tests/
│   │
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── api/
│   ├── mcp/
│   ├── security/
│   ├── load/
│   ├── chaos/
│   └── fixtures/
│
├── deployments/
│   │
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.dev.yml
│   │   └── docker-compose.test.yml
│   │
│   ├── kubernetes/
│   │   ├── base/
│   │   └── overlays/
│   │       ├── development/
│   │       ├── staging/
│   │       └── production/
│   │
│   └── helm/
│       └── agentrouter/
│           ├── Chart.yaml
│           ├── values.yaml
│           ├── values-development.yaml
│           ├── values-staging.yaml
│           ├── values-production.yaml
│           ├── templates/
│           └── README.md
│
├── infrastructure/
│   │
│   └── terraform/
│       ├── modules/
│       │   ├── network/
│       │   ├── kubernetes/
│       │   ├── database/
│       │   ├── redis/
│       │   ├── storage/
│       │   ├── monitoring/
│       │   └── security/
│       │
│       └── environments/
│           ├── development/
│           ├── staging/
│           └── production/
│
├── observability/
│   │
│   ├── otel/
│   ├── prometheus/
│   ├── grafana/
│   ├── alerts/
│   ├── dashboards/
│   └── runbooks/
│
├── security/
│   │
│   ├── policies/
│   ├── threat-model/
│   ├── compliance/
│   ├── security-tests/
│   ├── incident-response/
│   └── README.md
│
├── scripts/
│   ├── bootstrap/
│   ├── development/
│   ├── database/
│   ├── testing/
│   ├── release/
│   └── deployment/
│
├── docs/
│   │
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── system-architecture.md
│   │   ├── data-plane.md
│   │   ├── control-plane.md
│   │   ├── routing-engine.md
│   │   ├── provider-gateway.md
│   │   └── security-architecture.md
│   │
│   ├── api/
│   │   ├── openapi.yaml
│   │   └── examples/
│   │
│   ├── integrations/
│   │   ├── mcp.md
│   │   ├── vscode.md
│   │   ├── kiro.md
│   │   ├── cursor.md
│   │   └── jetbrains.md
│   │
│   ├── deployment/
│   │   ├── cloud.md
│   │   ├── kubernetes.md
│   │   ├── helm.md
│   │   ├── self-hosted.md
│   │   └── private-cloud.md
│   │
│   ├── security/
│   │   ├── security.md
│   │   ├── data-privacy.md
│   │   ├── authentication.md
│   │   ├── authorization.md
│   │   └── threat-model.md
│   │
│   ├── operations/
│   │   ├── monitoring.md
│   │   ├── incident-response.md
│   │   ├── disaster-recovery.md
│   │   └── troubleshooting.md
│   │
│   ├── customer/
│   │   ├── onboarding.md
│   │   ├── administrator-guide.md
│   │   ├── developer-guide.md
│   │   └── finops-guide.md
│   │
│   ├── product/
│   │   ├── vision.md
│   │   ├── roadmap.md
│   │   └── requirements.md
│   │
│   └── IMPLEMENTATION_STATUS.md
│
├── config/
│   ├── development/
│   ├── staging/
│   └── production/
│
├── .env.example
├── .gitignore
├── .dockerignore
├── Makefile
├── Taskfile.yml
├── README.md
├── SECURITY.md
├── CONTRIBUTING.md
├── LICENSE
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
└── VERSION
```

## One change I strongly recommend

Although the structure above is the **target/final repository structure**, don't immediately create 100+ services and directories and then ask Kiro to fill everything.

Start with the architectural skeleton:

```text
agentrouter/
├── apps/
│   ├── api/
│   ├── dashboard/
│   └── docs/
│
├── services/
│   ├── gateway/
│   ├── router/
│   ├── analyzer/
│   ├── policy/
│   ├── providers/
│   ├── registry/
│   └── cost-engine/
│
├── integrations/
│   └── mcp/
│
├── packages/
│   ├── api-contracts/
│   ├── shared-types/
│   ├── auth/
│   ├── security/
│   ├── logging/
│   └── telemetry/
│
├── database/
├── tests/
├── deployments/
├── infrastructure/
├── benchmark/
├── evaluation/
├── docs/
└── scripts/
```

Then let Kiro create the deeper directories **when each component is actually implemented**.

That gives you a clean repository instead of a giant empty skeleton.

### Most important directories

| Directory                  | Purpose                                    |
| -------------------------- | ------------------------------------------ |
| `services/router`          | 🧠 Core model-selection intelligence       |
| `services/analyzer`        | Understands the incoming task              |
| `services/providers`       | Connects to AI providers/models            |
| `services/policy`          | Enterprise governance                      |
| `services/registry`        | Model/provider/capability/pricing catalog  |
| `services/cost-engine`     | Cost and savings calculations              |
| `integrations/mcp`         | MCP interface                              |
| `integrations/vscode`      | VS Code integration                        |
| `integrations/kiro`        | Kiro integration                           |
| `clients/local-agent`      | Developer-side AgentRouter client          |
| `apps/dashboard`           | Customer dashboard                         |
| `database`                 | Persistent data                            |
| `benchmark`                | Model benchmarking                         |
| `evaluation`               | Router-quality evaluation                  |
| `deployments/helm`         | Enterprise Kubernetes installation         |
| `infrastructure/terraform` | Cloud infrastructure                       |
| `observability`            | Production monitoring                      |
| `security`                 | Security/compliance                        |
| `docs`                     | Product/engineering/customer documentation |

### The most important architectural boundary

Keep this separation very strict:

```text
                    integrations/
                         │
                         ▼
                  ┌─────────────┐
                  │   Gateway   │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   Analyzer  │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   Policy    │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   Router    │  ← CORE IP
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │Cost Engine  │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  Providers  │
                  └──────┬──────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
         Model A      Model B      Model C
```

