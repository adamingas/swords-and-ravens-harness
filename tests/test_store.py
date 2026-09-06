import copy
import sqlite3

from raven_harness.agent_store import AgentStore
from raven_harness.database import SCHEMA_VERSION, Database
from raven_harness.schemas import AgentCreate, AgentPublic

from conftest import lobby_snapshot


LEGACY_AGENT_RUNS_SCHEMA = """
CREATE TABLE agent_runs (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  status TEXT NOT NULL,
  model TEXT,
  observation_json TEXT NOT NULL,
  instructions TEXT,
  tools_json TEXT,
  tool_name TEXT,
  tool_arguments_json TEXT,
  model_output TEXT,
  response_id TEXT,
  response_json TEXT,
  usage_json TEXT,
  raw_usage_json TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  duration_ms INTEGER,
  history_id INTEGER
);
"""


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
    newest = store.list_snapshots(agent.id, limit=1)
    assert len(newest) == 1
    assert newest[0]["id"] == second_id
    assert newest[0]["leafStateId"] == "leaf-1"
    assert len(newest[0]["contentSha256"]) == 64
    assert store.get_snapshot(agent.id, second_id)["snapshot"] == changed

    assert store.delete_agent(agent.id) is True
    assert store.list_snapshots(agent.id) == []
    database.close()


def test_fresh_database_uses_current_schema(tmp_path) -> None:
    database = Database(tmp_path / "fresh.db")

    version = database.connection.execute("PRAGMA user_version").fetchone()[0]
    run_columns = {
        row["name"]
        for row in database.connection.execute("PRAGMA table_info(agent_runs)")
    }

    assert version == SCHEMA_VERSION == 3
    assert "context_json" in run_columns
    database.close()


def test_database_migrates_version_one_through_current_schema(tmp_path) -> None:
    path = tmp_path / "version-one.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE agents (id TEXT PRIMARY KEY)")
    connection.executescript(LEGACY_AGENT_RUNS_SCHEMA)
    connection.execute("PRAGMA user_version = 1")
    connection.commit()
    connection.close()

    database = Database(path)

    version = database.connection.execute("PRAGMA user_version").fetchone()[0]
    table = database.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'player_snapshots'"
    ).fetchone()
    run_columns = {
        row["name"]
        for row in database.connection.execute("PRAGMA table_info(agent_runs)")
    }
    assert version == SCHEMA_VERSION == 3
    assert table is not None
    assert "context_json" in run_columns
    database.close()


def test_database_migrates_version_two_runs_with_null_context(tmp_path) -> None:
    path = tmp_path / "version-two.db"
    connection = sqlite3.connect(path)
    connection.executescript(LEGACY_AGENT_RUNS_SCHEMA)
    connection.execute(
        """
        INSERT INTO agent_runs (
          id, agent_id, status, observation_json, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ("old-run", "old-agent", "completed", "{}", "2026-01-01T00:00:00Z"),
    )
    connection.execute("PRAGMA user_version = 2")
    connection.commit()
    connection.close()

    database = Database(path)
    trace = AgentStore(database).get_run("old-agent", "old-run")

    assert database.connection.execute("PRAGMA user_version").fetchone()[0] == 3
    assert trace is not None
    assert trace["contextManifest"] is None
    database.close()


def test_database_recovers_when_version_two_already_has_context_column(
    tmp_path,
) -> None:
    path = tmp_path / "interrupted-version-two.db"
    connection = sqlite3.connect(path)
    connection.executescript(LEGACY_AGENT_RUNS_SCHEMA)
    connection.execute("ALTER TABLE agent_runs ADD COLUMN context_json TEXT")
    connection.execute("PRAGMA user_version = 2")
    connection.commit()
    connection.close()

    database = Database(path)

    columns = [
        row["name"]
        for row in database.connection.execute("PRAGMA table_info(agent_runs)")
    ]
    assert database.connection.execute("PRAGMA user_version").fetchone()[0] == 3
    assert columns.count("context_json") == 1
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
    run = store.list_runs(agent.id)[0]
    assert run["responseId"] == "resp-1"
    assert run["rawUsage"][0]["cost"] == 0.001
    assert run["durationMs"] == 1000
    trace = store.get_run(agent.id, "run-1")
    assert trace is not None
    assert trace["observation"] == second
    assert trace["contextManifest"] == {
        "mode": "current-observation-and-memory",
        "items": [{"kind": "observation", "characters": 512}],
    }
    assert trace["instructions"] == "stable prompt"
    assert trace["response"] == [{"type": "function_call", "name": "resolve_march"}]
    assert store.get_run(agent.id, "unknown") is None

    metrics = store.get_run_metrics(agent.id)
    assert metrics == {
        "runCount": 1,
        "statusCounts": {"completed": 1},
        "modelRequests": 2,
        "tokens": {
            "input": 120,
            "output": 25,
            "total": 145,
            "cachedInput": 40,
            "cacheWrite": 10,
            "reasoning": 15,
            "maxInputInRun": 120,
        },
        "requestInputTokens": {
            "reportedRequests": 2,
            "average": 60,
            "p50": 20,
            "p90": 100,
            "p99": 100,
            "maximum": 100,
        },
        "rulesOracleRequestInputTokens": {
            "reportedRequests": 1,
            "average": 500,
            "p50": 500,
            "p90": 500,
            "p99": 500,
            "maximum": 500,
        },
        "costUsd": 0.0016,
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
