# Security Baseline

## Current Controls
- Non-root pods and restricted container capabilities in Kubernetes deployments.
- Readiness/liveness probes for API.
- Dependency vulnerability scan in CI (`pip-audit`).
- Error envelope includes trace ID for incident correlation.
- Optional API key middleware (`X-API-Key`) when `VISIONFLOW_API_KEY` is configured.
- In-process request rate limiting.

## Required Secrets
- `VISIONFLOW_API_KEY` (enables API key auth).

## Data Handling
- Job records use TTL (`JOB_TTL_SECONDS`).
- Raw request payload bytes are never returned from status API.

## Next Security Work
1. Persist/distribute rate limit state (Redis-backed) for multi-instance correctness.
2. Rotate secrets and move to managed secret store.
3. Add image vulnerability scan and policy enforcement in CI.
4. Add RBAC scopes for control-plane endpoints (`/models/register`, `/models/{name}/promote`).
