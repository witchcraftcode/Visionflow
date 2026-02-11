from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from app.queue.redis_queue import enqueue_job, set_job, get_job
import uuid
from app.models.registry import has_model, list_models

app = FastAPI(title="VisionFlow")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/models")
def available_models():
    return {
        "available_models": list_models()
    }

@app.post("/predict")
async def predict(
    model: str = Form(...),
    file: UploadFile = File(...)
):
    if not has_model(model):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{model}'"
        )

    image_bytes = await file.read()
    job_id = str(uuid.uuid4())

    set_job(job_id, {
        "status": "queued",
        "model": model,
        "image_bytes": image_bytes.hex(),
        "result": None,
        "error": None
    })

    enqueue_job(job_id)

    return {
        "job_id": job_id,
        "model": model,
        "status": "queued"
    }


@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Do not expose raw input payloads in API responses.
    return {k: v for k, v in job.items() if k != "image_bytes"}
