# Docker Deployments

Local and test stacks.

```text
docker-compose.yml       backing services (PostgreSQL, Redis)
docker-compose.dev.yml   development overlay
docker-compose.test.yml  ephemeral stack for integration tests
```

Credentials come from your local `.env` (see `.env.example`). Compose files
never carry real secrets.

## Status

Backing services usable. Application services pending implementation.
