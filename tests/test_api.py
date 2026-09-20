from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from raven_harness.app import create_app
from raven_harness.config import PROJECT_ROOT, Settings
from raven_harness.schemas import LobbySetupRequest

from conftest import lobby_snapshot, planning_snapshot


class UnusedRunner:
    rules_oracle_available = False

    async def run_once(
        self,
        *,
        agent_record,
        observation,
        context,
        tools,
        instructions,
        prompt_cache_key,
        trace_metadata,
    ):
        raise AssertionError("The model should not run in this test")

    async def shutdown(self) -> None:
        pass


def test_relative_data_paths_and_endpoint_selection() -> None:
    settings = Settings(
        database_path=Path("data/test.db"),
        rules_path=Path("data/test-rules.json"),
        _env_file=None,
    )

    assert settings.resolved_database_path == PROJECT_ROOT / "data/test.db"
    assert settings.resolved_rules_path == PROJECT_ROOT / "data/test-rules.json"
    assert settings.model_provider == "api.openai.com"
    assert settings.uses_openrouter is False
    assert Settings(openrouter_token="secret", _env_file=None).uses_openrouter is True
    assert (
        Settings(
            openai_base_url="https://models.example.test/v1",
            _env_file=None,
        ).model_provider
        == "models.example.test"
    )


def test_openrouter_blocklist_ignores_empty_items() -> None:
    settings = Settings(
        openrouter_provider_blocklist="together, ,novita",
        _env_file=None,
    )

    assert settings.openrouter_blocked_providers == ["together", "novita"]


def test_lobby_setup_request_rejects_unsupported_variants() -> None:
    assert LobbySetupRequest(playerCount=3).player_count == 3

    for field, value in (
        ("setupId", "mother-of-dragons"),
        ("playerCount", 5),
        ("vassals", True),
    ):
        with pytest.raises(ValidationError):
            LobbySetupRequest.model_validate({field: value})


def test_dashboard_api_creates_and_lists_agents(tmp_path) -> None:
    app = create_app(
        Settings(
            database_path=tmp_path / "api.db",
            openrouter_token="",
            openai_api_key="",
        ),
        runner=UnusedRunner(),
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/agents",
            json={
                "name": "Wolf",
                "model": "z-ai/glm-5.3-flash",
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
        assert dashboard[0]["stateStatus"] == {
            "source": None,
            "capturedAt": None,
            "actionable": False,
        }
        assert dashboard[0]["metrics"]["runCount"] == 0
        assert dashboard[0]["recentRuns"] == []
        assert client.get("/").status_code == 200

        assert client.get("/api/harnesses").status_code == 404


def test_dashboard_restores_last_saved_player_state_after_restart(tmp_path) -> None:
    settings = Settings(
        database_path=tmp_path / "persistent-dashboard.db",
        openrouter_token="",
        openai_api_key="",
    )
    app = create_app(settings, runner=UnusedRunner())
    with TestClient(app) as client:
        response = client.post(
            "/api/agents",
            json={
                "name": "Wolf",
                "gameServerUrl": "ws://localhost:5000",
                "gameId": "1",
                "userId": "2",
                "authToken": "secret",
            },
        )
        agent_id = response.json()["agent"]["id"]
        client.app.state.store.record_snapshot(agent_id, planning_snapshot())

    restarted = create_app(settings, runner=UnusedRunner())
    with TestClient(restarted) as client:
        monitor = client.get("/api/dashboard").json()["agents"][0]

    assert monitor["agent"]["runtime"]["status"] == "stopped"
    assert monitor["stateStatus"]["source"] == "saved"
    assert monitor["stateStatus"]["capturedAt"]
    assert monitor["stateStatus"]["actionable"] is False
    assert monitor["state"]["game"]["stateId"] == "leaf-2"
    assert monitor["state"]["player"]["houseId"] == "stark"
    assert monitor["state"]["player"]["powerTokens"] == 5
    assert [unit["id"] for unit in monitor["state"]["player"]["units"]] == [1, 2]


def test_dashboard_accepts_per_agent_models(tmp_path) -> None:
    app = create_app(
        Settings(
            database_path=tmp_path / "api.db",
            model_id="provider/model-a",
            openrouter_token="",
            openai_api_key="",
        ),
        runner=UnusedRunner(),
    )
    base_request = {
        "name": "Wolf",
        "gameServerUrl": "ws://localhost:5000",
        "gameId": "1",
        "userId": "2",
        "authToken": "secret",
    }
    with TestClient(app) as client:
        other = client.post(
            "/api/agents",
            json={**base_request, "name": "Other Wolf", "model": "provider/model-b"},
        )
        assert other.status_code == 201
        assert other.json()["agent"]["model"] == "provider/model-b"


def test_dashboard_rejects_removed_harness_selector(tmp_path) -> None:
    app = create_app(
        Settings(
            database_path=tmp_path / "api.db",
            openrouter_token="",
            openai_api_key="",
        ),
        runner=UnusedRunner(),
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/agents",
            json={
                "name": "Remembering Wolf",
                "model": "z-ai/glm-5.3-flash",
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
                "model": "z-ai/glm-5.3-flash",
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
        client.app.state.store.record_snapshot(agent["id"], lobby_snapshot())
        snapshots = client.get(
            f"/api/agents/{agent['id']}/snapshots", params={"limit": 1}
        ).json()["snapshots"]
        assert len(snapshots) == 1
        assert snapshots[0]["leafStateId"] == "leaf-1"
        assert "snapshot" not in snapshots[0]
        stored_snapshot = client.get(
            f"/api/agents/{agent['id']}/snapshots/{snapshots[0]['id']}"
        ).json()["snapshot"]
        assert stored_snapshot["snapshot"] == lobby_snapshot()
        assert (
            client.get(f"/api/agents/{agent['id']}/snapshots/999999").status_code == 404
        )
        assert (
            client.get(
                f"/api/agents/{agent['id']}/snapshots", params={"limit": 0}
            ).status_code
            == 422
        )
        assert client.get("/api/agents/missing/snapshots").status_code == 404
        assert client.get(f"/api/agents/{agent['id']}/runs/missing").status_code == 404
