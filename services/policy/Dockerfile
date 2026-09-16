# Scaffold Dockerfile for the AgentRouter policy service.
#
# This is intentionally NOT buildable yet: the service has no source. Replace
# the placeholder stage once policy is implemented, then enable the service in
# .github/workflows/build-images.yml.
#
# Reference shape for a Go service (see technology.md):
#
#   FROM golang:1.23-alpine AS build
#   WORKDIR /src
#   COPY . .
#   RUN CGO_ENABLED=0 go build -trimpath -o /out/policy ./cmd/policy
#
#   FROM gcr.io/distroless/static-debian12:nonroot
#   USER nonroot:nonroot
#   COPY --from=build /out/policy /policy
#   ENTRYPOINT ["/policy"]
#
# Image requirements from the specification (section 74): minimal base image,
# non-root user, dependency scanning, SBOM, signing where appropriate.

FROM scratch
LABEL org.opencontainers.image.title="agentrouter-policy"
LABEL org.opencontainers.image.description="Scaffold only. Not implemented."
