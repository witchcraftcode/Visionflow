# API Contract

## Error Envelope
All API errors use:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {},
    "trace_id": "string"
  }
}
```

## Endpoints

### `GET /health`
- Returns service health.

### `GET /ready`
- Checks dependency readiness.
- Includes queue and dead-letter depth.

### `GET /metrics`
- Prometheus metrics payload.

### `GET /models`
- Returns available models with default version and versions.

### `GET /models/{model_name}/versions`
- Returns all registered versions for one model.

### `POST /models/register`
- Registers new model version metadata.
- Currently supports runtime `onnx`.

Request:
```json
{
  "model": "custom",
  "version": "1.0.0",
  "runtime": "onnx",
  "artifact_uri": "app/models/onnx/custom.onnx",
  "class_path": "app.models.onnx_model.ONNXVisionModel",
  "input_schema": {"type":"image"},
  "output_schema": {"type":"classification"},
  "resources": {"cpu":"500m","memory":"512Mi"}
}
```

### `POST /models/{model_name}/promote`
- Promotes a model version to default.

Request:
```json
{
  "version": "1.0.1"
}
```

### `POST /predict`
- Multipart form:
  - `model` (required)
  - `model_version` (optional)
  - `file` (required image)
- Optional header:
  - `Idempotency-Key`

Response:
```json
{
  "job_id": "uuid",
  "model": "resnet18",
  "model_version": "1.0.0",
  "status": "queued",
  "idempotency_reused": false
}
```

### `GET /status/{job_id}`
- Returns job state.
- Never returns raw `image_bytes`.

Status values:
- `queued`
- `processing`
- `completed`
- `failed`
- `timed_out`
- `dead_lettered`
- `cancel_requested`

### `POST /jobs/{job_id}/cancel`
- Marks pending job as cancel requested.

### `GET /admin/audit`
- Returns recent admin audit events for model-management actions.
- Query param:
  - `limit` (optional, default `50`)

### `POST /monitoring/drift/baseline`
- Sets baseline statistics for features.

### `POST /monitoring/drift/observe`
- Records one observation payload (features and optional label).

### `GET /monitoring/drift/summary`
- Returns current drift summary and prediction distribution.

## Authentication
- If `VISIONFLOW_API_KEY` is set, all endpoints except `/health`, `/ready`, `/metrics` require `X-API-Key`.
- If `VISIONFLOW_ADMIN_API_KEY` is set, `POST /models/register`, `POST /models/{model_name}/promote`, and `GET /admin/audit` also require `X-Admin-Key`.
