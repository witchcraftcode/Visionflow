import os
import stat
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def test_prepare_release_requires_env(tmp_path: Path):
    env = os.environ.copy()
    env.pop("VISIONFLOW_API_KEY", None)
    env.pop("VISIONFLOW_ADMIN_API_KEY", None)
    env.pop("VISIONFLOW_HOST", None)
    result = subprocess.run(
        ["bash", str(ROOT_DIR / "scripts" / "prepare_release.sh"), "--output-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "VISIONFLOW_API_KEY" in result.stderr


def test_prepare_release_renders_files_and_commands(tmp_path: Path):
    env = os.environ.copy()
    env["VISIONFLOW_API_KEY"] = "user-key"
    env["VISIONFLOW_ADMIN_API_KEY"] = "admin-key"
    env["VISIONFLOW_HOST"] = "api.example.com"
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"
    result = subprocess.run(
        ["bash", str(ROOT_DIR / "scripts" / "prepare_release.sh"), "--output-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert (tmp_path / "visionflow-secret.yaml").exists()
    assert (tmp_path / "visionflow-ingress.yaml").exists()
    assert "kubectl apply -f" in result.stdout
    assert "passed preflight validation" in result.stdout


def test_prepare_release_apply_uses_custom_kubectl(tmp_path: Path):
    fake_kubectl = tmp_path / "kubectl"
    log_file = tmp_path / "kubectl.log"
    fake_kubectl.write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" >> \"{log_file}\"\n"
    )
    fake_kubectl.chmod(fake_kubectl.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["VISIONFLOW_API_KEY"] = "user-key"
    env["VISIONFLOW_ADMIN_API_KEY"] = "admin-key"
    env["VISIONFLOW_HOST"] = "api.example.com"
    env["KUBECTL_BIN"] = str(fake_kubectl)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"

    subprocess.run(
        [
            "bash",
            str(ROOT_DIR / "scripts" / "prepare_release.sh"),
            "--output-dir",
            str(tmp_path),
            "--apply",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    log = log_file.read_text()
    assert "apply -f" in log
    assert "apply -k" in log


def test_prepare_release_requires_acm_for_eks(tmp_path: Path):
    env = os.environ.copy()
    env["VISIONFLOW_API_KEY"] = "user-key"
    env["VISIONFLOW_ADMIN_API_KEY"] = "admin-key"
    env["VISIONFLOW_HOST"] = "api.example.com"
    env.pop("VISIONFLOW_ACM_CERTIFICATE_ARN", None)
    result = subprocess.run(
        [
            "bash",
            str(ROOT_DIR / "scripts" / "prepare_release.sh"),
            "--overlay",
            "eks-prod",
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "VISIONFLOW_ACM_CERTIFICATE_ARN" in result.stderr


def test_prepare_release_supports_eks_overlay(tmp_path: Path):
    env = os.environ.copy()
    env["VISIONFLOW_API_KEY"] = "user-key"
    env["VISIONFLOW_ADMIN_API_KEY"] = "admin-key"
    env["VISIONFLOW_HOST"] = "api.example.com"
    env["VISIONFLOW_ACM_CERTIFICATE_ARN"] = "arn:aws:acm:us-east-1:123456789012:certificate/test"
    result = subprocess.run(
        [
            "bash",
            str(ROOT_DIR / "scripts" / "prepare_release.sh"),
            "--overlay",
            "eks-prod",
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert "overlays/eks-prod" in result.stdout
    assert (tmp_path / "visionflow-ingress.yaml").exists()


def test_prepare_release_supports_public_eks_without_domain(tmp_path: Path):
    env = os.environ.copy()
    env["VISIONFLOW_API_KEY"] = "user-key"
    env["VISIONFLOW_ADMIN_API_KEY"] = "admin-key"
    env.pop("VISIONFLOW_HOST", None)
    env.pop("VISIONFLOW_ACM_CERTIFICATE_ARN", None)
    result = subprocess.run(
        [
            "bash",
            str(ROOT_DIR / "scripts" / "prepare_release.sh"),
            "--overlay",
            "eks-prod",
            "--public-without-domain",
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert "passed preflight validation" in result.stdout
    assert (tmp_path / "visionflow-ingress.yaml").exists()
