# Security Baseline

## Current Controls
- Non-root pods and restricted container capabilities in Kubernetes deployments.
- Readiness/liveness probes for API.
- Dependency vulnerability scan in CI (`pip-audit`).
- Error envelope includes trace ID for incident correlation.
- Optional API key middleware (`X-API-Key`) when `VISIONFLOW_API_KEY` is configured.
- Optional admin API key middleware (`X-Admin-Key`) for model-management endpoints.
- Redis-backed request rate limiting across pods.

## Required Secrets
- `VISIONFLOW_API_KEY` (enables API key auth).
- `VISIONFLOW_ADMIN_API_KEY` (enables admin-only control-plane actions).

## Data Handling
- Job records use TTL (`JOB_TTL_SECONDS`).
- Raw request payload bytes are never returned from status API.

## Next Security Work
1. Rotate secrets and move to managed secret store.
2. Add image vulnerability scan and policy enforcement in CI.
3. Add RBAC scopes beyond one admin key for control-plane endpoints.
4. Add audit persistence for admin actions.
