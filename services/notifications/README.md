# notifications service

**Plane:** Platform

Delivers budget, reliability, policy and security notifications over email, webhook, Slack and Microsoft Teams.

## Layout

```text
cmd/        service entry point
internal/
  email/    Email delivery
  webhook/  Outbound webhooks
  slack/    Slack delivery
  teams/    Microsoft Teams delivery
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
