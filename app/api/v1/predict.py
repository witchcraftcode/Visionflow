from fastapi import APIRouter, File, Form, Header, Request, UploadFile

from app.schemas.predict import PredictResponse
from app.services.inference import enqueue_prediction

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: Request,
    model: str = Form(...),
    model_version: str | None = Form(default=None),
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await enqueue_prediction(
        request=request,
        model=model,
        model_version=model_version,
        files=[file],
        idempotency_key=idempotency_key,
        batch_mode=False,
    )


@router.post("/predict/batch", response_model=PredictResponse)
async def predict_batch(
    request: Request,
    model: str = Form(...),
    model_version: str | None = Form(default=None),
    files: list[UploadFile] = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await enqueue_prediction(
        request=request,
        model=model,
        model_version=model_version,
        files=files,
        idempotency_key=idempotency_key,
        batch_mode=True,
    )
