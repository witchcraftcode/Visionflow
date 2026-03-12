# Model Lifecycle

## States
- `candidate`: registered but not default.
- `production`: set as default version for the model.
- `archived`: reserved for future cleanup workflow.

## Register New Version
1. Add ONNX artifact under `app/models/onnx/`.
2. Register metadata:
```bash
curl -X POST http://localhost:8000/models/register \
  -H "Content-Type: application/json" \
  -d '{
    "model":"resnet18",
    "version":"1.0.1",
    "runtime":"onnx",
    "artifact_uri":"app/models/onnx/resnet18.onnx",
    "class_path":"app.models.resnet18.ResNet18Model",
    "input_schema":{"type":"image"},
    "output_schema":{"type":"classification"},
    "resources":{"cpu":"500m","memory":"512Mi"}
  }'
```

## Promote Version
```bash
curl -X POST http://localhost:8000/models/resnet18/promote \
  -H "Content-Type: application/json" \
  -d '{"version":"1.0.1"}'
```

## Rollback
- Re-promote previously stable version.
