# VisionFlow

VisionFlow is a simple ML model deployment service: upload an image, pick a model, and get a prediction. The API enqueues jobs in Redis and a worker performs inference.

## Requirements
- Docker and Docker Compose
- ONNX model files placed at:
  - /Users/ashimaverma/visionflow/app/models/onnx/resnet18.onnx
  - /Users/ashimaverma/visionflow/app/models/onnx/mobilenet_v2.onnx
  - /Users/ashimaverma/visionflow/app/models/onnx/yolov5n.onnx

## Local (Docker Compose)
1. Build and start services:

```bash
cd /Users/ashimaverma/visionflow
docker compose up --build
```

2. Check available models:

```bash
curl -s http://localhost:8000/models | jq
```

3. Send a prediction request:

```bash
curl -s -X POST \
  -F model=resnet18 \
  -F file=@/Users/ashimaverma/visionflow/test.jpg \
  http://localhost:8000/predict | jq
```

4. Poll job status:

```bash
JOB_ID=$(curl -s -X POST -F model=resnet18 -F file=@/Users/ashimaverma/visionflow/test.jpg http://localhost:8000/predict | jq -r .job_id)

curl -s http://localhost:8000/status/$JOB_ID | jq
```

## Kubernetes
1. Build images locally (or push to a registry and update image names):

```bash
docker build -t visionflow-api -f /Users/ashimaverma/visionflow/Dockerfile.api /Users/ashimaverma/visionflow
docker build -t visionflow-worker -f /Users/ashimaverma/visionflow/Dockerfile.worker /Users/ashimaverma/visionflow
```

2. Apply manifests:

```bash
kubectl apply -f /Users/ashimaverma/visionflow/k8s
```

3. Port-forward the API:

```bash
kubectl port-forward svc/visionflow-api 8000:8000
```

4. Use the same curl commands as above against http://localhost:8000.

## Config
Per-model preprocessing configs live in:
- /Users/ashimaverma/visionflow/app/configs/models/resnet18.json
- /Users/ashimaverma/visionflow/app/configs/models/mobilenet.json
- /Users/ashimaverma/visionflow/app/configs/models/yolov5.json

Adjust `input_size`, `color_mode`, and `normalization` to match each model.

## API
- `GET /models`
- `POST /predict` (multipart form: `model`, `file`)
- `GET /status/{job_id}`
