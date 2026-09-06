from pathlib import Path

from fastapi.testclient import TestClient

from raven_harness.app import create_app
from raven_harness.config import PROJECT_ROOT, Settings


class UnusedRunner:
    async def run_once(self, **_kwargs):
        raise AssertionError("The model should not run in this test")


def test_default_relative_data_paths_are_project_local() -> None:
    settings = Settings(
        database_path=Path("data/test.db"),
        rules_path=Path("data/test-rules.json"),
        _env_file=None,
    )

    assert settings.resolved_database_path == PROJECT_ROOT / "data/test.db"
    assert settings.resolved_rules_path == PROJECT_ROOT / "data/test-rules.json"


def test_dashboard_api_creates_and_lists_agents(tmp_path) -> None:
    app = create_app(
        Settings(database_path=tmp_path / "api.db", openai_api_key=""),
        runner=UnusedRunner(),
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/agents",
            json={
                "name": "Wolf",
                "model": "gpt-5",
                "gameServerUrl": "ws://localhost:5000",
                "gameId": "1",
                "userId": "2",
                "authToken": "secret",
            },
        )
        assert response.status_code == 201
        agent = response.json()["agent"]
        assert agent["name"] == "Wolf"
        assert "authToken" not in agent
        assert "authTokenConfigured" not in agent

        listed = client.get("/api/agents").json()["agents"]
        assert [item["id"] for item in listed] == [agent["id"]]
        dashboard = client.get("/api/dashboard").json()["agents"]
        assert dashboard[0]["agent"]["id"] == agent["id"]
        assert dashboard[0]["state"] is None
        assert dashboard[0]["metrics"]["runCount"] == 0
        assert dashboard[0]["recentRuns"] == []
        assert client.get("/").status_code == 200

        assert client.get("/api/harnesses").status_code == 404


def test_dashboard_rejects_removed_harness_selector(tmp_path) -> None:
    app = create_app(
        Settings(database_path=tmp_path / "api.db", openai_api_key=""),
        runner=UnusedRunner(),
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/agents",
            json={
                "name": "Remembering Wolf",
                "model": "gpt-5",
                "harnessId": "strategic-v1",
                "gameServerUrl": "ws://localhost:5000",
                "gameId": "1",
                "userId": "2",
                "authToken": "secret",
            },
        )
        assert response.status_code == 422

        response = client.post(
            "/api/agents",
            json={
                "name": "Remembering Wolf",
                "model": "gpt-5",
                "gameServerUrl": "ws://localhost:5000",
                "gameId": "1",
                "userId": "2",
                "authToken": "secret",
            },
        )
        assert response.status_code == 201
        agent = response.json()["agent"]
        assert client.get(f"/api/agents/{agent['id']}/memory").status_code == 200
        assert client.get(f"/api/agents/{agent['id']}/history").json() == {
            "history": []
        }
        assert client.get(f"/api/agents/{agent['id']}/metrics").json() == {
            "metrics": {
                "runCount": 0,
                "statusCounts": {},
                "modelRequests": 0,
                "tokens": {
                    "input": 0,
                    "output": 0,
                    "total": 0,
                    "cachedInput": 0,
                    "cacheWrite": 0,
                    "reasoning": 0,
                    "maxInputInRun": 0,
                },
                "costUsd": 0.0,
                "durationMs": {"total": 0, "average": 0, "maximum": 0},
                "historicalStates": 0,
            }
        }
        assert client.get(f"/api/agents/{agent['id']}/runs/missing").status_code == 404
