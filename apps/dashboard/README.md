# Dashboard

Customer-facing control plane application (React/Next.js per `technology.md`).

Sections defined by the specification: Overview, AI Usage, Cost, Savings, Models,
Providers, Routing, Teams, Users, Policies, Security, Audit, Billing, Settings.

The browser talks only to the control plane API. It never reaches PostgreSQL
directly, and the frontend is never trusted for authorization.

Status: scaffold, not implemented.

```text
src/     application code
public/  static assets
tests/   dashboard tests
```
