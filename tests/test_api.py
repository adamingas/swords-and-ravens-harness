from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from raven_harness.app import create_app
from raven_harness.config import PROJECT_ROOT, Settings
from raven_harness.schemas import LobbySetupRequest

from conftest import lobby_snapshot


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
        max_turns,
        stop_at_tool_names,
        prompt_cache_key,
        trace_metadata,
    ):
        raise AssertionError("The model should not run in this test")

    async def shutdown(self) -> None:
        pass

    async def clear_session(self, agent_id: str) -> None:
        del agent_id


def test_default_relative_data_paths_are_project_local() -> None:
    settings = Settings(
        database_path=Path("data/test.db"),
        rules_path=Path("data/test-rules.json"),
        _env_file=None,
    )

    assert settings.resolved_database_path == PROJECT_ROOT / "data/test.db"
    assert settings.resolved_rules_path == PROJECT_ROOT / "data/test-rules.json"


def test_openrouter_routing_prefers_compatible_hosts() -> None:
    settings = Settings(_env_file=None)

    assert settings.autoplay_max_consecutive_failures == 5
    assert settings.autoplay_retry_base_seconds == 2
    assert settings.model_id == "z-ai/glm-5.3-flash"
    assert settings.openrouter_provider_routing == {
        "allow_fallbacks": True,
        "require_parameters": False,
        "order": [
            "reka",
            "cloudflare",
            "coreweave",
            "fireworks",
            "together",
            "deepinfra",
        ],
        "only": [
            "reka",
            "cloudflare",
            "coreweave",
            "fireworks",
            "together",
            "deepinfra",
        ],
    }


def test_openrouter_routing_uses_sort_when_order_is_empty() -> None:
    settings = Settings(
        openrouter_provider_order="",
        openrouter_provider_sort="latency",
        _env_file=None,
    )

    assert settings.openrouter_provider_routing == {
        "allow_fallbacks": True,
        "require_parameters": False,
        "sort": "latency",
    }


def test_lobby_setup_request_accepts_only_supported_variant() -> None:
    assert LobbySetupRequest().model_dump() == {
        "setup_id": "base-game",
        "player_count": 6,
        "pbem": True,
        "vassals": False,
        "victory_points_to_win": 7,
    }

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
        assert client.get("/api/models").json() == {
            "provider": "OpenAI",
            "models": [
                {
                    "id": "z-ai/glm-5.3-flash",
                    "name": "z-ai/glm-5.3-flash",
                }
            ],
        }
        health = client.get("/api/health").json()
        assert health["modelId"] == "z-ai/glm-5.3-flash"
        assert health["rulesOracleAvailable"] is False
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
        assert dashboard[0]["metrics"]["runCount"] == 0
        assert dashboard[0]["recentRuns"] == []
        assert client.get("/").status_code == 200

        assert client.get("/api/harnesses").status_code == 404


def test_dashboard_enforces_one_configured_model(tmp_path) -> None:
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
        created = client.post("/api/agents", json=base_request)
        assert created.status_code == 201
        assert created.json()["agent"]["model"] == "provider/model-a"

        rejected = client.post(
            "/api/agents",
            json={**base_request, "name": "Other Wolf", "model": "provider/model-b"},
        )
        assert rejected.status_code == 400
        assert rejected.json() == {
            "error": "All agents on this harness must use provider/model-a"
        }


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
        assert client.get(
            f"/api/agents/{agent['id']}/snapshots/999999"
        ).status_code == 404
        assert client.get(
            f"/api/agents/{agent['id']}/snapshots", params={"limit": 0}
        ).status_code == 422
        assert client.get("/api/agents/missing/snapshots").status_code == 404
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
                "requestInputTokens": {
                    "reportedRequests": 0,
                    "average": 0,
                    "p50": 0,
                    "p90": 0,
                    "p99": 0,
                    "maximum": 0,
                },
                "rulesOracleRequestInputTokens": {
                    "reportedRequests": 0,
                    "average": 0,
                    "p50": 0,
                    "p90": 0,
                    "p99": 0,
                    "maximum": 0,
                },
                "costUsd": 0.0,
                "durationMs": {"total": 0, "average": 0, "maximum": 0},
                "historicalStates": 0,
            }
        }
        assert client.get(f"/api/agents/{agent['id']}/runs/missing").status_code == 404
