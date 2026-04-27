import os
import stat
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def test_publish_images_uses_custom_docker_and_push(tmp_path: Path):
    fake_docker = tmp_path / "docker"
    log_file = tmp_path / "docker.log"
    fake_docker.write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"$@\" >> \"{log_file}\"\n"
    )
    fake_docker.chmod(fake_docker.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["DOCKER_BIN"] = str(fake_docker)

    subprocess.run(
        [
            "bash",
            str(ROOT_DIR / "scripts" / "publish_images.sh"),
            "--registry",
            "ghcr.io/example",
            "--tag",
            "v1",
            "--platform",
            "linux/amd64",
            "--push",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    log = log_file.read_text()
    assert "buildx build --platform linux/amd64 --push -t ghcr.io/example/visionflow-api:v1" in log
    assert "buildx build --platform linux/amd64 --push -t ghcr.io/example/visionflow-worker:v1" in log
