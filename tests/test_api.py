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
        assert "authToken" not in agent
        assert agent["authTokenConfigured"] is True

        listed = client.get("/api/agents").json()["agents"]
        assert [item["id"] for item in listed] == [agent["id"]]
        assert client.get("/").status_code == 200
