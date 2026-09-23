import copy
import sqlite3

import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.schemas import AgentCreate

from conftest import lobby_snapshot


def test_player_snapshots_are_append_only_and_deduplicated(tmp_path) -> None:
    database = Database(tmp_path / "snapshots.db")
    store = AgentStore(database)
    agent = store.create_agent(
        AgentCreate(
            name="Snapshot Wolf",
            model="test-model",
            user_id="2",
            auth_token="secret",
        )
    )
    first = lobby_snapshot()

    first_id = store.record_snapshot(agent.id, first)
    duplicate_id = store.record_snapshot(agent.id, copy.deepcopy(first))
    changed = copy.deepcopy(first)
    changed["childGameState"]["players"].append(["stark", "2"])
    second_id = store.record_snapshot(agent.id, changed)

    assert first_id is not None
    assert duplicate_id is None
    assert second_id is not None
    assert second_id > first_id
    newest = store.list_snapshots(agent.id, limit=1)
    assert len(newest) == 1
    assert newest[0]["id"] == second_id
    assert newest[0]["leafStateId"] == "leaf-1"
    assert store.get_snapshot(agent.id, second_id)["snapshot"] == changed
    latest = store.get_latest_snapshot(agent.id)
    assert latest is not None
    assert latest["id"] == second_id
    assert latest["snapshot"] == changed

    assert store.delete_agent(agent.id) is True
    assert store.list_snapshots(agent.id) == []
    assert store.get_latest_snapshot(agent.id) is None
    database.close()


def test_database_rejects_non_current_existing_schema(tmp_path) -> None:
    version = 3
    path = tmp_path / f"schema-{version}.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE existing_data (value TEXT)")
    connection.execute("INSERT INTO existing_data VALUES ('preserve me')")
    connection.execute(f"PRAGMA user_version = {version}")
    connection.commit()
    connection.close()

    with pytest.raises(
        RuntimeError, match=f"schema version {version} is not supported"
    ):
        Database(path)

    connection = sqlite3.connect(path)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == version
    assert connection.execute("SELECT value FROM existing_data").fetchone()[0] == (
        "preserve me"
    )
    connection.close()


def test_state_history_memory_and_run_persist(tmp_path) -> None:
    database = Database(tmp_path / "memory.db")
    store = AgentStore(database)
    agent = store.create_agent(
        AgentCreate(
            name="Remembering Wolf",
            model="test-model",
            user_id="2",
            auth_token="secret",
        )
    )
    assert store.get_strategic_memory(agent.id)["modelPlan"] == ""
    first = {"game": {"stateId": "leaf-1", "round": 1, "phase": "place-orders"}}
    second = {"game": {"stateId": "leaf-2", "round": 1, "phase": "march"}}
    first_id = store.record_state(agent.id, first)
    store.record_history_action(first_id, "submit_orders", {"assignments": []})
    store.record_state(agent.id, second)
    recalled = store.recall_state(agent.id, 1)
    assert recalled is not None
    assert recalled["stateId"] == "leaf-1"
    assert recalled["action"] == "submit_orders"
    assert recalled["observation"] == first

    memory = store.set_strategic_memory(
        agent.id,
        {
            "situationAssessment": "Hold Winterfell.",
            "objectives": ["Take another castle"],
            "opponentModels": [],
            "commitments": [],
            "lessons": [],
        },
    )
    assert memory["revision"] == 1
    assert store.get_strategic_memory(agent.id)["objectives"] == ["Take another castle"]

    store.add_run(
        run_id="run-1",
        agent_id=agent.id,
        status="completed",
        model="test-model",
        observation=second,
        context_manifest={
            "mode": "current-observation-and-memory",
            "items": [{"kind": "observation", "characters": 512}],
        },
        instructions="stable prompt",
        tools=[{"name": "resolve_march"}],
        tool_name="resolve_march",
        tool_arguments={"from": "winterfell"},
        response_id="resp-1",
        response=[{"type": "function_call", "name": "resolve_march"}],
        usage={
            "requests": 2,
            "inputTokens": 120,
            "outputTokens": 25,
            "totalTokens": 145,
        },
        raw_usage=[
            {
                "input_tokens": 100,
                "input_tokens_details": {
                    "cached_tokens": 40,
                    "cache_write_tokens": 10,
                },
                "output_tokens_details": {"reasoning_tokens": 12},
                "cost": 0.001,
                "cost_details": {"upstream_inference_cost": 0.0008},
                "response_provider": "Example Provider",
                "response_model": "test-model-2026-09-01",
            },
            {
                "input_tokens": 500,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 3},
                "cost": 0.0005,
                "scope": "rules-oracle",
            },
            {
                "input_tokens": 20,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0},
                "cost": 0.0001,
                "scope": "agent",
            },
        ],
        created_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00",
        duration_ms=1000,
        history_id=first_id,
    )
    trace = store.get_run(agent.id, "run-1")
    assert trace is not None
    assert trace["observation"] == second
    assert trace["instructions"] == "stable prompt"
    assert trace["response"] == [{"type": "function_call", "name": "resolve_march"}]
    assert store.get_run(agent.id, "unknown") is None

    database.close()
