#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.storage.artifacts import sha256_file
from app.services.registry_db import register_model_version

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


def upload_artifact(
    s3_client,
    bucket,
    key,
    path,
    dry_run,
):
    if not path.exists():
        raise FileNotFoundError(f"Missing model artifact: {path}")

    checksum = sha256_file(path)
    uri = f"s3://{bucket}/{key}"

    print(f"{path} -> {uri} sha256={checksum}")

    if dry_run:
        return checksum, uri

    s3_client.upload_file(
        str(path),
        bucket,
        key,
        ExtraArgs={
            "Metadata": {"sha256": checksum},
            "ContentType": "application/octet-stream",
        },
    )

    return checksum, uri


def parse_args():
    parser = argparse.ArgumentParser(description="Upload VisionFlow model artifacts to S3.")
    parser.add_argument(
        "--bucket",
        default=settings.s3_bucket,
    )
    parser.add_argument(
        "--region",
        default=settings.aws_region,
    )
    parser.add_argument("--no-create-bucket", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    kwargs = {
        "region_name": args.region,
    }

    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id

    if settings.aws_secret_access_key:
        kwargs["aws_secret_access_key"] = (
            settings.aws_secret_access_key
        )

    s3_client = boto3.client("s3", **kwargs)
    if not args.no_create_bucket and not args.dry_run:
        ensure_bucket(s3_client, args.bucket, args.region)

    for key, path in DEFAULT_ARTIFACTS.items():
        checksum, uri = upload_artifact(
            s3_client,
            args.bucket,
            key,
            path,
            args.dry_run,
        )

        if not args.dry_run:

            model_name, version, _ = key.split("/", 2)

            CLASS_PATHS = {
                "resnet18": "app.models.resnet18.ResNet18Model",
                "mobilenet": "app.models.mobilenet.MobileNetV2Model",
                "yolov5": "app.models.yolov5.YOLOv5Model",
            }

            register_model_version(
                model_name=model_name,
                version=version,
                payload={
                    "runtime": "onnxruntime",
                    "artifact_uri": uri,
                    "artifact_sha256": checksum,
                    "class": CLASS_PATHS[model_name],
                    "input_schema": {},
                    "output_schema": {},
                    "resources": {},
                },
            )

            print(f"Registered {model_name}:{version}")

if __name__ == "__main__":
    main()
