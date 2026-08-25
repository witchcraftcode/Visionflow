import json
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    app_name: str = "VisionFlow"
    api_v1_prefix: str = "/api/v1"
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", 5 * 1024 * 1024))
    default_job_timeout_seconds: int = int(os.getenv("DEFAULT_JOB_TIMEOUT_SECONDS", 60))
    allowed_image_mime_types: set[str] = {"image/jpeg", "image/png", "image/webp"}
    exempt_paths: set[str] = {"/health", "/ready", "/metrics"}
    admin_paths: set[str] = {"/models/register", "/admin/audit"}
    configs_dir: Path = Path(__file__).resolve().parents[1] / "configs" / "models"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./visionflow.db")
    aws_region: str = os.getenv(
        "AWS_REGION",
        "ap-south-1",
    )

    aws_access_key_id: str | None = os.getenv(
        "AWS_ACCESS_KEY_ID",
    )

    aws_secret_access_key: str | None = os.getenv(
        "AWS_SECRET_ACCESS_KEY",
    )

    s3_bucket: str = os.getenv(
        "S3_BUCKET",
        "visionflow-models",
    )

    model_cache_dir: Path = Path(
        os.getenv(
            "MODEL_CACHE_DIR",
            "./model_cache",
        )
    )
    auto_create_sqlite_schema: bool = os.getenv("AUTO_CREATE_SQLITE_SCHEMA", "true").lower() == "true"
 



settings = Settings()


def load_model_config(model_name: str):
    path = settings.configs_dir / f"{model_name}.json"
    if not path.exists():
        raise ValueError(f"No config for model '{model_name}'")

    with open(path) as f:
        return json.load(f)
