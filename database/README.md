# Database

PostgreSQL is the authoritative transactional store. Redis is a cache and
coordination layer, never the source of truth.

## Rules

- Every schema change ships as a migration. Production schema is never edited by hand.
- Migrations run before the application deployment.
- Migrations must be backwards compatible while rolling deployments are in flight.
- Every tenant-scoped table enforces isolation at the data-access boundary.

## Core tables

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

## Layout

```text
migrations/  ordered, forward-only schema migrations
seeds/       non-production seed data
schemas/     reference schema documentation
queries/     reviewed query definitions
views/       database views
```

## Status

Scaffold. No migrations written yet.
