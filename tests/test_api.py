from fastapi.testclient import TestClient

from raven_harness.app import create_app
from raven_harness.config import Settings


class UnusedRunner:
    async def run_once(self, **_kwargs):
        raise AssertionError("The model should not run in this test")


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
        assert agent["harnessId"] == "legacy"
        assert "authToken" not in agent
        assert agent["authTokenConfigured"] is True

        listed = client.get("/api/agents").json()["agents"]
        assert [item["id"] for item in listed] == [agent["id"]]
        assert client.get("/").status_code == 200

        harnesses = client.get("/api/harnesses").json()["harnesses"]
        assert [item["id"] for item in harnesses] == ["legacy", "strategic-v1"]


def test_dashboard_can_create_strategic_agent(tmp_path) -> None:
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
        assert response.status_code == 201
        agent = response.json()["agent"]
        assert agent["harnessId"] == "strategic-v1"
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
                "conversationItems": 0,
                "historicalStates": 0,
            }
        }
        assert client.get(f"/api/agents/{agent['id']}/runs/missing").status_code == 404
