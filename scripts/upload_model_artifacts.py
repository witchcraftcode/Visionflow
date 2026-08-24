#!/usr/bin/env python3
import argparse
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.storage.artifacts import sha256_file

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = {
    "resnet18/v1/resnet18.onnx": ROOT_DIR / "app" / "models" / "onnx" / "resnet18.onnx",
    "mobilenet/v1/mobilenet_v2.onnx": ROOT_DIR / "app" / "models" / "onnx" / "mobilenet_v2.onnx",
    "yolov5/v1/yolov5n.onnx": ROOT_DIR / "app" / "models" / "onnx" / "yolov5n.onnx",
}


def ensure_bucket(s3_client, bucket: str, region: str):
    try:
        s3_client.head_bucket(Bucket=bucket)
        return
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status not in {403, 404}:
            raise

    kwargs = {"Bucket": bucket}
    if region != "us-east-1":
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3_client.create_bucket(**kwargs)


def upload_artifact(s3_client, bucket: str, key: str, path: Path, dry_run: bool):
    if not path.exists():
        raise FileNotFoundError(f"Missing model artifact: {path}")
    checksum = sha256_file(path)
    print(f"{path} -> s3://{bucket}/{key} sha256={checksum}")
    if dry_run:
        return checksum
    s3_client.upload_file(
        str(path),
        bucket,
        key,
        ExtraArgs={
            "Metadata": {"sha256": checksum},
            "ContentType": "application/octet-stream",
        },
    )
    return checksum


def parse_args():
    parser = argparse.ArgumentParser(description="Upload VisionFlow model artifacts to S3.")
    parser.add_argument("--bucket", default=settings.model_artifact_bucket)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--no-create-bucket", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    s3_client = boto3.client("s3", region_name=args.region)
    if not args.no_create_bucket and not args.dry_run:
        ensure_bucket(s3_client, args.bucket, args.region)

    for key, path in DEFAULT_ARTIFACTS.items():
        upload_artifact(s3_client, args.bucket, key, path, args.dry_run)


if __name__ == "__main__":
    main()
