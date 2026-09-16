# billing service

**Plane:** Commercial

Plans, seats, metered usage, overages, invoices and payment status. Isolated from routing logic and never in the synchronous request path.

## Layout

```text
cmd/        service entry point
internal/
  subscriptions/  Plans and seats
  usage/          Metered usage rating
  invoices/       Invoice generation
  payments/       Payment status and provider integration
tests/      service tests
```

## Status

Scaffold, not implemented. Track progress in `docs/IMPLEMENTATION_STATUS.md`.
