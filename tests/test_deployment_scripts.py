import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parent.parent


def test_render_k8s_secret_requires_env():
    env = os.environ.copy()
    env.pop("VISIONFLOW_API_KEY", None)
    env.pop("VISIONFLOW_ADMIN_API_KEY", None)
    result = subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "render_k8s_secret.py")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "VISIONFLOW_API_KEY" in result.stderr


def test_render_k8s_secret_outputs_manifest():
    env = os.environ.copy()
    env["VISIONFLOW_API_KEY"] = "user-key"
    env["VISIONFLOW_ADMIN_API_KEY"] = "admin-key"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "render_k8s_secret.py"),
            "--namespace",
            "visionflow-prod",
            "--name",
            "visionflow-secrets",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert 'namespace: visionflow-prod' in result.stdout
    assert 'api_key: "user-key"' in result.stdout
    assert 'admin_api_key: "admin-key"' in result.stdout


def test_render_ingress_requires_host():
    env = os.environ.copy()
    env.pop("VISIONFLOW_HOST", None)
    result = subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "render_ingress.py"), "--overlay", "prod"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "VISIONFLOW_HOST" in result.stderr


def test_render_ingress_outputs_prod_manifest():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "render_ingress.py"),
            "--overlay",
            "prod",
            "--host",
            "api.example.com",
            "--tls-secret-name",
            "visionflow-tls",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "host: api.example.com" in result.stdout
    assert "secretName: visionflow-tls" in result.stdout


def test_render_ingress_outputs_eks_manifest():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "render_ingress.py"),
            "--overlay",
            "eks-prod",
            "--host",
            "api.example.com",
            "--certificate-arn",
            "arn:aws:acm:us-east-1:123456789012:certificate/test",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "alb.ingress.kubernetes.io/certificate-arn" in result.stdout
    assert "host: api.example.com" in result.stdout


def test_render_ingress_outputs_public_eks_manifest_without_domain():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "render_ingress.py"),
            "--overlay",
            "eks-prod",
            "--public-without-domain",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert 'alb.ingress.kubernetes.io/listen-ports: \'[{"HTTP": 80}]' in result.stdout
    assert "certificate-arn" not in result.stdout
    assert "host:" not in result.stdout


def test_validate_deployment_detects_placeholder_host():
    result = subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "validate_deployment.py"), "--overlay", "prod"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "placeholder host" in result.stderr


def test_validate_deployment_passes_custom_overlay(tmp_path: Path):
    overlay_dir = tmp_path / "k8s" / "overlays" / "custom"
    overlay_dir.mkdir(parents=True)
    (overlay_dir / "ingress.yaml").write_text(
        """apiVersion: networking.k8s.io/v1
kind: Ingress
spec:
  tls:
    - hosts:
        - api.example.com
      secretName: visionflow-tls
  rules:
    - host: api.example.com
"""
    )
    (overlay_dir / "kustomization.yaml").write_text(
        """images:
  - name: visionflow-api
    newName: ghcr.io/example/visionflow-api
  - name: visionflow-worker
    newName: ghcr.io/example/visionflow-worker
"""
    )

    script_path = ROOT_DIR / "scripts" / "validate_deployment.py"
    source = script_path.read_text().replace('ROOT_DIR = Path(__file__).resolve().parent.parent', f'ROOT_DIR = Path(r"{tmp_path}")')
    temp_script = tmp_path / "validate_deployment.py"
    temp_script.write_text(source)

    result = subprocess.run(
        [sys.executable, str(temp_script), "--overlay", "custom"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "passed preflight validation" in result.stdout


def test_validate_deployment_accepts_rendered_eks_ingress(tmp_path: Path):
    ingress_path = tmp_path / "ingress.yaml"
    ingress_path.write_text(
        """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/test
spec:
  ingressClassName: alb
  tls:
    - hosts:
        - api.example.com
  rules:
    - host: api.example.com
"""
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "validate_deployment.py"),
            "--overlay",
            "eks-prod",
            "--ingress-file",
            str(ingress_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "passed preflight validation" in result.stdout


def test_validate_deployment_accepts_missing_host_when_allowed(tmp_path: Path):
    ingress_path = tmp_path / "ingress.yaml"
    ingress_path.write_text(
        """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
"""
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "validate_deployment.py"),
            "--overlay",
            "eks-prod",
            "--ingress-file",
            str(ingress_path),
            "--allow-missing-host",
            "--allow-missing-tls",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "passed preflight validation" in result.stdout


def test_validate_deployment_checks_secret_file(tmp_path: Path):
    secret_path = tmp_path / "secret.yaml"
    secret_path.write_text(
        """apiVersion: v1
kind: Secret
stringData:
  api_key: "replace-me"
  admin_api_key: "replace-me-admin"
"""
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "validate_deployment.py"),
            "--overlay",
            "eks-prod",
            "--secret-file",
            str(secret_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "placeholder secret value" in result.stderr
