import argparse
import re
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER_HOSTS = {"visionflow.example.com", "api.visionflow.example.com"}
PLACEHOLDER_SECRET_VALUES = {"replace-me", "replace-me-admin"}


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text()


def _extract_hosts(ingress_text: str) -> list[str]:
    return re.findall(r"^\s*-\s*([A-Za-z0-9.-]+)\s*$|^\s*host:\s*([A-Za-z0-9.-]+)\s*$", ingress_text, re.MULTILINE)


def _normalized_hosts(ingress_text: str) -> list[str]:
    hosts = []
    for tuple_match in _extract_hosts(ingress_text):
        host = next((candidate for candidate in tuple_match if candidate), "")
        if host:
            hosts.append(host)
    return hosts


def validate_overlay(
    overlay: str,
    ingress_file: Path | None = None,
    allow_missing_host: bool = False,
    allow_missing_tls: bool = False,
) -> list[str]:
    issues: list[str] = []
    ingress_path = ingress_file or (ROOT_DIR / "k8s" / "overlays" / overlay / "ingress.yaml")
    kustomization_path = ROOT_DIR / "k8s" / "overlays" / overlay / "kustomization.yaml"

    ingress_text = _read(ingress_path)
    kustomization_text = _read(kustomization_path)

    hosts = _normalized_hosts(ingress_text)
    if not hosts and not allow_missing_host:
        issues.append(f"{ingress_path} does not declare any ingress host.")
    for host in hosts:
        if host in PLACEHOLDER_HOSTS:
            issues.append(f"{ingress_path} still uses placeholder host '{host}'.")

    if (
        "secretName:" not in ingress_text
        and "alb.ingress.kubernetes.io/certificate-arn:" not in ingress_text
        and not allow_missing_tls
    ):
        issues.append(f"{ingress_path} is missing a TLS secretName.")
    if "REGION" in kustomization_text:
        issues.append(f"{kustomization_path} still contains the REGION placeholder.")
    if "newName: visionflow-api" in kustomization_text or "newName: visionflow-worker" in kustomization_text:
        issues.append(f"{kustomization_path} still points at local image names.")

    return issues


def validate_secret(secret_path: Path) -> list[str]:
    issues: list[str] = []
    secret_text = _read(secret_path)
    for value in PLACEHOLDER_SECRET_VALUES:
        if f'"{value}"' in secret_text:
            issues.append(f"{secret_path} still contains placeholder secret value '{value}'.")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate VisionFlow deployment configuration.")
    parser.add_argument("--overlay", default="prod")
    parser.add_argument("--ingress-file", type=Path, default=None)
    parser.add_argument("--secret-file", type=Path, default=None)
    parser.add_argument("--allow-missing-host", action="store_true")
    parser.add_argument("--allow-missing-tls", action="store_true")
    args = parser.parse_args()

    issues = validate_overlay(
        args.overlay,
        ingress_file=args.ingress_file,
        allow_missing_host=args.allow_missing_host,
        allow_missing_tls=args.allow_missing_tls,
    )
    if args.secret_file is not None:
        issues.extend(validate_secret(args.secret_file))

    if issues:
        for issue in issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        return 1

    print(f"Deployment overlay '{args.overlay}' passed preflight validation.")
    if args.secret_file is not None:
        print(f"Secret manifest '{args.secret_file}' passed placeholder validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
