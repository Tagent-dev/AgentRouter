# AgentRouter developer entry points.
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
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: scaffold
scaffold: ## Recreate any missing part of the repository structure
	python scripts/bootstrap/scaffold_repository.py

.PHONY: verify-structure
verify-structure: ## Fail if the structure drifts from the scaffold definition
	python scripts/bootstrap/scaffold_repository.py
	git diff --exit-code
	python scripts/testing/validate_structure.py

.PHONY: check
check: ## THE quality gate: format, lint, type check, unit tests
	python scripts/development/check.py

.PHONY: format
format: ## Rewrite formatting in place (check only reports)
	python -m ruff format .
	python -m ruff check --fix .

.PHONY: health
health: ## Report whether PostgreSQL and Redis are reachable
	python scripts/development/health.py

.PHONY: up
up: ## Start local backing services (PostgreSQL, Redis)
	$(COMPOSE_DEV) up -d

.PHONY: down
down: ## Stop local backing services
	$(COMPOSE_DEV) down

.PHONY: logs
logs: ## Tail local backing service logs
	$(COMPOSE_DEV) logs -f

.PHONY: test-env-up
test-env-up: ## Start the ephemeral integration test stack
	$(COMPOSE_TEST) up -d --wait

.PHONY: test-env-down
test-env-down: ## Tear down the integration test stack
	$(COMPOSE_TEST) down -v

.PHONY: helm-lint
helm-lint: ## Lint the Helm chart
	helm lint deployments/helm/agentrouter

.PHONY: status
status: ## Show implementation status
	@echo "See docs/IMPLEMENTATION_STATUS.md"

# `lint` and `test` are single steps of `check`, kept for muscle memory and for
# narrowing a failure. `check` is the documented command (requirement 3.6): CI
# and the contributing guide name it and nothing else.
.PHONY: lint
lint: ## One step of check: ruff format --check and ruff check
	python -m ruff format --check .
	python -m ruff check .

.PHONY: test
test: ## One step of check: pytest with coverage
	python -m pytest

.PHONY: build
build: ## Build all services (not implemented)
	@echo "No buildable source yet. Wire this up in the phase that adds code."; exit 1

.PHONY: migrate
migrate: ## Apply database migrations (not implemented)
	@echo "No migrations yet. See database/README.md."; exit 1
