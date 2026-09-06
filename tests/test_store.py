import copy
import sqlite3

from raven_harness.agent_store import AgentStore
from raven_harness.database import SCHEMA_VERSION, Database
from raven_harness.schemas import AgentCreate, AgentPublic

from conftest import lobby_snapshot


def test_agent_configuration_persists_without_exposing_credentials(tmp_path) -> None:
    database = Database(tmp_path / "test.db")
    store = AgentStore(database)
    created = store.create_agent(
        AgentCreate(
            name="A Wolf",
            model="gpt-5",
            game_server_url="ws://localhost:5000",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )

    loaded = store.get_agent(created.id)
    assert loaded is not None
    assert loaded.auth_token.get_secret_value() == "secret"
    public = AgentPublic.from_record(loaded).model_dump(by_alias=True)
    assert "authToken" not in public
    assert "authTokenConfigured" not in public
    assert "harnessId" not in public
    database.close()


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
    newest = store.list_snapshots(agent.id, limit=1, include_snapshot=True)
    assert len(newest) == 1
    assert newest[0]["id"] == second_id
    assert newest[0]["leafStateId"] == "leaf-1"
    assert len(newest[0]["contentSha256"]) == 64
    assert newest[0]["snapshot"] == changed

    assert store.delete_agent(agent.id) is True
    assert store.list_snapshots(agent.id) == []
    database.close()


def test_database_migrates_version_one_for_player_snapshots(tmp_path) -> None:
    path = tmp_path / "version-one.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE agents (id TEXT PRIMARY KEY)")
    connection.execute("PRAGMA user_version = 1")
    connection.commit()
    connection.close()

    database = Database(path)

    version = database.connection.execute("PRAGMA user_version").fetchone()[0]
    table = database.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'player_snapshots'"
    ).fetchone()
    assert version == SCHEMA_VERSION == 2
    assert table is not None
    database.close()


def test_state_history_memory_and_rich_run_trace_persist(tmp_path) -> None:
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
        instructions="stable prompt",
        tools=[{"name": "resolve_march"}],
        tool_name="resolve_march",
        tool_arguments={"from": "winterfell"},
        response_id="resp-1",
        response=[{"type": "function_call", "name": "resolve_march"}],
        usage={"inputTokens": 100, "outputTokens": 20, "totalTokens": 120},
        raw_usage=[
            {
                "input_tokens": 100,
                "input_tokens_details": {
                    "cached_tokens": 40,
                    "cache_write_tokens": 10,
                },
                "output_tokens_details": {"reasoning_tokens": 12},
                "cost": 0.001,
            }
        ],
        created_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:00:01+00:00",
        duration_ms=1000,
        history_id=first_id,
    )
    run = store.list_runs(agent.id)[0]
    assert run["responseId"] == "resp-1"
    assert run["rawUsage"][0]["cost"] == 0.001
    assert run["durationMs"] == 1000
    trace = store.get_run(agent.id, "run-1")
    assert trace is not None
    assert trace["observation"] == second
    assert trace["instructions"] == "stable prompt"
    assert trace["response"] == [{"type": "function_call", "name": "resolve_march"}]
    assert store.get_run(agent.id, "unknown") is None

    metrics = store.get_run_metrics(agent.id)
    assert metrics == {
        "runCount": 1,
        "statusCounts": {"completed": 1},
        "modelRequests": 0,
        "tokens": {
            "input": 100,
            "output": 20,
            "total": 120,
            "cachedInput": 40,
            "cacheWrite": 10,
            "reasoning": 12,
            "maxInputInRun": 100,
        },
        "costUsd": 0.001,
        "durationMs": {"total": 1000, "average": 1000, "maximum": 1000},
        "historicalStates": 2,
    }
    database.close()


def test_exact_state_can_be_recalled_three_decisions_ago(tmp_path) -> None:
    database = Database(tmp_path / "recall.db")
    store = AgentStore(database)
    agent = store.create_agent(
        AgentCreate(
            name="Historical Wolf",
            model="test-model",
            user_id="3",
            auth_token="secret",
        )
    )
    for number in range(1, 5):
        store.record_state(
            agent.id,
            {
                "game": {
                    "stateId": f"leaf-{number}",
                    "round": number,
                    "phase": "place-orders",
                },
                "marker": f"position-{number}",
            },
        )

    recalled = store.recall_state(agent.id, 3)

    assert recalled is not None
    assert recalled["stateId"] == "leaf-1"
    assert recalled["observation"]["marker"] == "position-1"
    database.close()
