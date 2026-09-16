# Contributing

## Source of truth

Target architecture and requirements live in the root planning documents:

```text
README.md                 master engineering specification
Architecture.md           production architecture
Repository Structure.md   target repository structure
technology.md             technology per layer
product.md                capability checklist
prompt complexity.md      analyzer design guidance
MVP.md                    local-first starting point
```

Current reality lives in `docs/IMPLEMENTATION_STATUS.md`. Read it before
starting work.

## Implementation order

Follow the dependency order in the master specification, section 132. Do not
jump between unrelated phases. Each phase passes its acceptance criteria before
the next begins.

## Per-phase process

```text
UNDERSTAND  inspect the repository and existing implementation
DESIGN      smallest correct architecture consistent with the spec
IMPLEMENT   production-quality code
TEST        unit, integration and relevant end-to-end tests
SECURITY    auth, authorization, secrets, tenant isolation, data handling
OBSERVE     logs, metrics, traces
DOCUMENT    update the relevant documentation
VALIDATE    tests, linting, builds, deployment validation
REPORT      what was implemented, what was tested, known limitations
```

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

```text
implementation exists
unit tests exist
integration tests exist where applicable
errors handled
security considered
structured logging implemented
metrics implemented where applicable
documentation exists
API contract exists
configuration exists
deployment exists where applicable
CI validates it
```

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
