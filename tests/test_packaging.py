from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_uv(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", *arguments],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
        timeout=180,
    )


def test_wheel_serves_dashboard_and_uses_writable_installed_data_dir(
    tmp_path: Path,
) -> None:
    wheel_directory = tmp_path / "wheel"
    _run_uv("build", "--wheel", "--out-dir", str(wheel_directory), cwd=PROJECT_ROOT)
    wheel_path = next(wheel_directory.glob("*.whl"))

    with zipfile.ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
    assert {
        "raven_harness/public/index.html",
        "raven_harness/public/app.js",
        "raven_harness/public/styles.css",
    } <= names

    environment_directory = tmp_path / "environment"
    _run_uv(
        "venv",
        "--python",
        sys.executable,
        str(environment_directory),
        cwd=PROJECT_ROOT,
    )
    python = environment_directory / "bin" / "python"
    if os.name == "nt":
        python = environment_directory / "Scripts" / "python.exe"
    _run_uv(
        "pip",
        "install",
        "--python",
        str(python),
        str(wheel_path),
        cwd=PROJECT_ROOT,
    )

    isolated_home = tmp_path / "home"
    isolated_home.mkdir()
    isolated_data = tmp_path / "xdg-data"
    explicit_database = tmp_path / "explicit" / "harness.db"
    script = r"""
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from raven_harness.app import create_app
from raven_harness.config import Settings


class NoopRunner:
    rules_oracle_available = False

    async def run_once(self, **kwargs):
        raise AssertionError("the packaging check must not call the model")

    async def shutdown(self):
        pass

    async def clear_session(self, agent_id):
        del agent_id


def check_app(settings):
    app = create_app(settings, runner=NoopRunner())
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert "Raven Harness" in client.get("/").text
        assert client.get("/app.js").status_code == 200
        assert client.get("/styles.css").status_code == 200
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["databasePath"] == str(settings.resolved_database_path)
    assert settings.resolved_database_path.is_file()


default_settings = Settings(_env_file=None)
check_app(default_settings)

explicit_settings = Settings(
    database_path=Path(os.environ["EXPLICIT_DATABASE"]),
    _env_file=None,
)
check_app(explicit_settings)

print(json.dumps({
    "default_database": str(default_settings.resolved_database_path),
    "explicit_database": str(explicit_settings.resolved_database_path),
}))
"""
    child_environment = {
        **os.environ,
        "HOME": str(isolated_home),
        "XDG_DATA_HOME": str(isolated_data),
        "OPENROUTER_TOKEN": "",
        "OPENAI_API_KEY": "",
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": "",
        "EXPLICIT_DATABASE": str(explicit_database),
        "PYTHONNOUSERSITE": "1",
    }
    child_environment.pop("PYTHONPATH", None)
    child_environment.pop("DATABASE_PATH", None)
    child_environment.pop("RULES_PATH", None)
    result = subprocess.run(
        [str(python), "-c", script],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
        env=child_environment,
        timeout=60,
    )
    output = json.loads(result.stdout)
    assert Path(output["default_database"]).is_file()
    assert Path(output["explicit_database"]) == explicit_database
    assert explicit_database.is_file()
