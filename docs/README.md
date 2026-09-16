# Documentation

```text
architecture/  system and component architecture
api/           OpenAPI contract and examples
integrations/  per-host integration guides
deployment/    cloud, Kubernetes, Helm, self-hosted, private
security/      security, privacy, auth and threat model
operations/    monitoring, incident response, DR, troubleshooting
customer/      onboarding and role-based guides
product/       vision, roadmap, requirements
implementation-status.yaml    the status manifest: authoritative
status-manifest.schema.json   schema the manifest is validated against
IMPLEMENTATION_STATUS.md      what actually works today (generated)
```

Planning documents at the repository root remain the source of truth for the
target architecture: `README.md` (master specification), `Architecture.md`,
`Repository Structure.md`, `technology.md`, `product.md`, `prompt complexity.md`
and `MVP.md`.

Start with `IMPLEMENTATION_STATUS.md` to see where the build actually stands.
Change status by editing `implementation-status.yaml`, never the generated
document.
