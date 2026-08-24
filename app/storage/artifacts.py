import hashlib
import os
import shutil
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings


class ChecksumMismatchError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_checksum(path: Path, expected_sha256: str | None):
    if not expected_sha256:
        return
    actual = sha256_file(path)
    if actual.lower() != expected_sha256.lower():
        raise ChecksumMismatchError(
            f"Checksum mismatch for {path}: expected {expected_sha256}, got {actual}"
        )


class ModelArtifactManager:
    def __init__(self, cache_dir: Path | None = None, s3_client=None):
        self.cache_dir = cache_dir or settings.model_cache_dir
        self.s3_client = s3_client

    def resolve(self, artifact_uri: str, expected_sha256: str | None = None) -> Path:
        parsed = urlparse(artifact_uri)
        if parsed.scheme == "s3":
            return self._resolve_s3(parsed.netloc, parsed.path.lstrip("/"), expected_sha256)
        if parsed.scheme == "file":
            path = Path(parsed.path)
        else:
            path = Path(artifact_uri)
        if not path.exists():
            raise FileNotFoundError(f"Missing model artifact: {path}")
        validate_checksum(path, expected_sha256)
        return path

    def _resolve_s3(self, bucket: str, key: str, expected_sha256: str | None) -> Path:
        cache_path = self.cache_dir / bucket / key
        if cache_path.exists():
            validate_checksum(cache_path, expected_sha256)
            return cache_path

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = cache_path.with_suffix(cache_path.suffix + ".tmp")
        self._client().download_file(bucket, key, str(temp_path))
        validate_checksum(temp_path, expected_sha256)
        os.replace(temp_path, cache_path)
        return cache_path

    def seed_cache_from_local(self, source_path: Path, artifact_uri: str):
        parsed = urlparse(artifact_uri)
        if parsed.scheme != "s3":
            return
        cache_path = self.cache_dir / parsed.netloc / parsed.path.lstrip("/")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, cache_path)

    def _client(self):
        if self.s3_client is None:
            import boto3

            self.s3_client = boto3.client("s3")
        return self.s3_client


artifact_manager = ModelArtifactManager()
