#!/usr/bin/env python3
"""Validate the AgentRouter repository scaffold.

Checks:
  1. Every path in the target structure from "Repository Structure.md" exists.
  2. Every JSON file parses.
  3. Every YAML file parses (Helm templates are skipped - they are Go templates).
  4. No secret-bearing file is tracked by Git.

Usage:
    python scripts/testing/validate_structure.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Paths from the final target repository structure. Directories end with "/".
REQUIRED = """
.github/workflows/ci.yml
.github/workflows/security.yml
.github/workflows/build-images.yml
.github/workflows/deploy-staging.yml
.github/workflows/deploy-production.yml
.github/ISSUE_TEMPLATE/
.github/PULL_REQUEST_TEMPLATE.md
.github/CODEOWNERS
.github/dependabot.yml
apps/dashboard/src/
apps/dashboard/public/
apps/dashboard/tests/
apps/dashboard/package.json
apps/dashboard/README.md
apps/admin-console/src/
apps/admin-console/public/
apps/admin-console/tests/
apps/admin-console/README.md
apps/api/src/
apps/api/tests/
apps/api/README.md
apps/docs/content/
apps/docs/public/
apps/docs/README.md
services/gateway/cmd/
services/gateway/internal/
services/gateway/tests/
services/gateway/Dockerfile
services/gateway/README.md
services/router/cmd/
services/router/internal/engine/
services/router/internal/scoring/
services/router/internal/candidates/
services/router/internal/strategies/
services/router/internal/escalation/
services/router/internal/fallback/
services/router/tests/
services/router/Dockerfile
services/router/README.md
services/analyzer/cmd/
services/analyzer/internal/classifier/
services/analyzer/internal/complexity/
services/analyzer/internal/capabilities/
services/analyzer/internal/context/
services/analyzer/internal/prompt_analysis/
services/analyzer/tests/
services/analyzer/Dockerfile
services/analyzer/README.md
services/policy/cmd/
services/policy/internal/engine/
services/policy/internal/rules/
services/policy/internal/evaluation/
services/policy/internal/inheritance/
services/policy/tests/
services/policy/Dockerfile
services/policy/README.md
services/providers/cmd/
services/providers/internal/gateway/
services/providers/internal/adapters/
services/providers/internal/health/
services/providers/internal/failover/
services/providers/internal/normalization/
services/providers/internal/openai/
services/providers/internal/anthropic/
services/providers/internal/google/
services/providers/internal/azure/
services/providers/internal/aws/
services/providers/internal/compatible/
services/providers/tests/
services/providers/Dockerfile
services/providers/README.md
services/registry/cmd/
services/registry/internal/models/
services/registry/internal/providers/
services/registry/internal/capabilities/
services/registry/internal/pricing/
services/registry/internal/lifecycle/
services/registry/tests/
services/registry/Dockerfile
services/registry/README.md
services/cost_engine/cmd/
services/cost_engine/internal/pricing/
services/cost_engine/internal/estimation/
services/cost_engine/internal/calculation/
services/cost_engine/internal/savings/
services/cost_engine/tests/
services/cost_engine/Dockerfile
services/cost_engine/README.md
services/analytics/cmd/
services/analytics/internal/ingestion/
services/analytics/internal/aggregation/
services/analytics/internal/metrics/
services/analytics/internal/reports/
services/analytics/tests/
services/analytics/Dockerfile
services/analytics/README.md
services/billing/cmd/
services/billing/internal/subscriptions/
services/billing/internal/usage/
services/billing/internal/invoices/
services/billing/internal/payments/
services/billing/tests/
services/billing/Dockerfile
services/billing/README.md
services/notifications/cmd/
services/notifications/internal/email/
services/notifications/internal/webhook/
services/notifications/internal/slack/
services/notifications/internal/teams/
services/notifications/tests/
services/notifications/Dockerfile
services/notifications/README.md
services/audit/cmd/
services/audit/internal/events/
services/audit/internal/storage/
services/audit/internal/queries/
services/audit/tests/
services/audit/Dockerfile
services/audit/README.md
integrations/mcp/server/tools/
integrations/mcp/server/resources/
integrations/mcp/server/prompts/
integrations/mcp/server/auth/
integrations/mcp/server/server/
integrations/mcp/tests/
integrations/mcp/package.json
integrations/mcp/README.md
integrations/vscode/src/
integrations/vscode/resources/
integrations/vscode/tests/
integrations/vscode/package.json
integrations/vscode/README.md
integrations/kiro/src/
integrations/kiro/config/
integrations/kiro/tests/
integrations/kiro/README.md
integrations/cursor/src/
integrations/cursor/tests/
integrations/cursor/README.md
integrations/claude-code/src/
integrations/claude-code/tests/
integrations/claude-code/README.md
integrations/jetbrains/src/
integrations/jetbrains/tests/
integrations/jetbrains/README.md
clients/desktop/src/
clients/desktop/tests/
clients/desktop/README.md
clients/local-agent/src/
clients/local-agent/config/
clients/local-agent/tests/
clients/local-agent/README.md
cli/cmd/login/
cli/cmd/logout/
cli/cmd/configure/
cli/cmd/status/
cli/cmd/models/
cli/cmd/providers/
cli/cmd/route/
cli/cmd/usage/
cli/cmd/diagnose/
cli/cmd/policy/
cli/internal/
cli/tests/
cli/Dockerfile
cli/README.md
sdk/typescript/src/
sdk/typescript/tests/
sdk/typescript/package.json
sdk/typescript/README.md
sdk/python/agentrouter/
sdk/python/tests/
sdk/python/pyproject.toml
sdk/python/README.md
sdk/go/agentrouter/
sdk/go/tests/
sdk/go/go.mod
sdk/go/README.md
packages/api_contracts/
packages/shared_types/
packages/auth/
packages/authorization/
packages/tenant/
packages/logging/
packages/telemetry/
packages/errors/
packages/security/
packages/redaction/
packages/configuration/
packages/events/
packages/validation/
packages/testing/
database/migrations/
database/seeds/
database/schemas/
database/queries/
database/views/
database/README.md
benchmark/datasets/coding/
benchmark/datasets/debugging/
benchmark/datasets/refactoring/
benchmark/datasets/kubernetes/
benchmark/datasets/terraform/
benchmark/datasets/sql/
benchmark/datasets/architecture/
benchmark/datasets/security/
benchmark/runners/
benchmark/evaluators/
benchmark/reports/
benchmark/README.md
evaluation/routing/
evaluation/quality/
evaluation/cost/
evaluation/latency/
evaluation/reliability/
evaluation/README.md
tests/unit/
tests/integration/
tests/e2e/
tests/api/
tests/mcp/
tests/security/
tests/load/
tests/chaos/
tests/fixtures/
deployments/docker/docker-compose.yml
deployments/docker/docker-compose.dev.yml
deployments/docker/docker-compose.test.yml
deployments/kubernetes/base/
deployments/kubernetes/overlays/development/
deployments/kubernetes/overlays/staging/
deployments/kubernetes/overlays/production/
deployments/helm/agentrouter/Chart.yaml
deployments/helm/agentrouter/values.yaml
deployments/helm/agentrouter/values-development.yaml
deployments/helm/agentrouter/values-staging.yaml
deployments/helm/agentrouter/values-production.yaml
deployments/helm/agentrouter/templates/
deployments/helm/agentrouter/README.md
infrastructure/terraform/modules/network/
infrastructure/terraform/modules/kubernetes/
infrastructure/terraform/modules/database/
infrastructure/terraform/modules/redis/
infrastructure/terraform/modules/storage/
infrastructure/terraform/modules/monitoring/
infrastructure/terraform/modules/security/
infrastructure/terraform/environments/development/
infrastructure/terraform/environments/staging/
infrastructure/terraform/environments/production/
observability/otel/
observability/prometheus/
observability/grafana/
observability/alerts/
observability/dashboards/
observability/runbooks/
security/policies/
security/threat-model/
security/compliance/
security/security-tests/
security/incident-response/
security/README.md
scripts/bootstrap/
scripts/bootstrap/scaffold_repository.py
scripts/development/
scripts/development/check.py
scripts/development/health.py
scripts/status/
scripts/status/manifest.py
scripts/status/validate.py
scripts/status/render.py
scripts/status/verify.py
scripts/status/check_dod.py
scripts/status/README.md
scripts/testing/validate_structure.py
scripts/database/
scripts/testing/
scripts/release/
scripts/deployment/
docs/architecture/overview.md
docs/architecture/system-architecture.md
docs/architecture/data-plane.md
docs/architecture/control-plane.md
docs/architecture/routing-engine.md
docs/architecture/provider-gateway.md
docs/architecture/security-architecture.md
docs/api/openapi.yaml
docs/api/examples/
docs/integrations/mcp.md
docs/integrations/vscode.md
docs/integrations/kiro.md
docs/integrations/cursor.md
docs/integrations/jetbrains.md
docs/deployment/cloud.md
docs/deployment/kubernetes.md
docs/deployment/helm.md
docs/deployment/self-hosted.md
docs/deployment/private-cloud.md
docs/security/security.md
docs/security/data-privacy.md
docs/security/authentication.md
docs/security/authorization.md
docs/security/threat-model.md
docs/operations/monitoring.md
docs/operations/incident-response.md
docs/operations/disaster-recovery.md
docs/operations/troubleshooting.md
docs/customer/onboarding.md
docs/customer/administrator-guide.md
docs/customer/developer-guide.md
docs/customer/finops-guide.md
docs/product/vision.md
docs/product/roadmap.md
docs/product/requirements.md
docs/IMPLEMENTATION_STATUS.md
docs/implementation-status.yaml
docs/status-manifest.schema.json
config/development/
config/staging/
config/production/
.env.example
.gitignore
.dockerignore
Makefile
Taskfile.yml
pyproject.toml
requirements-dev.txt
README.md
SECURITY.md
CONTRIBUTING.md
LICENSE
CHANGELOG.md
CODE_OF_CONDUCT.md
VERSION
""".strip().splitlines()

SECRET_PATTERNS = (".env", ".pem", ".key", ".p12", ".pfx", "credentials.json")

failures: list[str] = []
checked = {"paths": 0, "json": 0, "yaml": 0}


def check_required() -> None:
    for entry in REQUIRED:
        entry = entry.strip()
        if not entry:
            continue
        path = ROOT / entry.rstrip("/")
        checked["paths"] += 1
        if entry.endswith("/"):
            if not path.is_dir():
                failures.append(f"missing directory: {entry}")
        elif not path.is_file():
            failures.append(f"missing file: {entry}")


def check_json() -> None:
    for path in ROOT.rglob("*.json"):
        if any(part in {"node_modules", ".git"} for part in path.parts):
            continue
        checked["json"] += 1
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"invalid JSON: {path.relative_to(ROOT)}: {exc}")


def check_yaml() -> None:
    try:
        # Stubs come from types-pyyaml, pinned in requirements-dev.txt.
        import yaml
    except ImportError:
        print("note: PyYAML not installed, skipping YAML parse checks")
        return

    helm_templates = ROOT / "deployments" / "helm" / "agentrouter" / "templates"
    for pattern in ("*.yml", "*.yaml"):
        for path in ROOT.rglob(pattern):
            if any(part in {"node_modules", ".git"} for part in path.parts):
                continue
            # Helm templates are Go templates, not plain YAML.
            if helm_templates in path.parents:
                continue
            checked["yaml"] += 1
            try:
                list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
            except yaml.YAMLError as exc:
                failures.append(f"invalid YAML: {path.relative_to(ROOT)}: {exc}")


def check_no_tracked_secrets() -> None:
    try:
        tracked = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("note: git unavailable, skipping tracked-secret check")
        return

    for entry in tracked:
        name = entry.rsplit("/", 1)[-1]
        if name == ".env.example":
            continue
        if name == ".env" or any(name.endswith(p) for p in SECRET_PATTERNS if p != ".env"):
            failures.append(f"secret-bearing file tracked in Git: {entry}")


def main() -> int:
    check_required()
    check_json()
    check_yaml()
    check_no_tracked_secrets()

    print(
        f"checked {checked['paths']} structure paths, "
        f"{checked['json']} JSON files, {checked['yaml']} YAML files"
    )

    if failures:
        print(f"\n{len(failures)} problem(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("structure validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
