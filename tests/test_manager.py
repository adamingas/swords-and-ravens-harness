import asyncio
import copy

import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.game.client import GameConnectionLost
from raven_harness.game.codec import decode_message, encode_message
from raven_harness.harness.actions import ActionTaken
from raven_harness.harness.interface import PreparedTurn
from raven_harness.harness.observation import build_context
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.manager import (
    AgentManager,
    AgentSession,
    _monitoring_state,
    _next_reconnect_delay,
)
from raven_harness.models.openai_agent import (
    ModelRunCancelled,
    ModelRunError,
    ModelRunResult,
    PermanentModelError,
    TransientProviderCapacityError,
)
from raven_harness.schemas import AgentCreate, LobbySetupRequest

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


class FakeConnection:
    def __init__(self, snapshot=None, *, banned: bool = False) -> None:
        self.incoming: asyncio.Queue[str | None] = asyncio.Queue()
        self.snapshot = snapshot or lobby_snapshot()
        self.sent: list[dict] = []
        self.closed = False
        self.banned = banned

    def __aiter__(self) -> "FakeConnection":
        return self

    async def __anext__(self) -> str:
        value = await self.incoming.get()
        if value is None:
            raise StopAsyncIteration
        return value

    async def send(self, payload: str) -> None:
        message = decode_message(payload)
        self.sent.append(message)
        if message["type"] == "authenticate":
            if self.banned:
                await self.incoming.put(encode_message({"type": "banned-response"}))
                return
            await self.incoming.put(
                encode_message(
                    {
                        "type": "authenticate-response",
                        "userId": message["authData"]["userId"],
                        "game": self.snapshot,
                    }
                )
            )

    async def close(self) -> None:
        self.closed = True
        await self.incoming.put(None)


class FakeRunClient:
    status = "connected"
    snapshot = lobby_snapshot()
    recent_events: list[dict] = []
    connection_generation = 1


class FakeLobbyClient:
    status = "connected"
    recent_events: list[dict] = []
    connection_generation = 1

    def __init__(self, returned_settings: dict) -> None:
        self.snapshot = lobby_snapshot()
        self.synced_snapshot = lobby_snapshot()
        self.synced_snapshot["gameSettings"] = returned_settings
        self.sent: list[dict] = []

    async def send(self, message: dict) -> None:
        self.sent.append(message)

    async def sync_snapshot(self) -> dict:
        return self.synced_snapshot


class ContextManifestHarness:
    def __init__(self, outcome: str = "completed") -> None:
        self.outcome = outcome
        self.manifest = {
            "mode": "current-observation-and-memory",
            "items": [{"kind": "observation", "characters": 256}],
        }

    def prepare_turn(self, record, context, previous_error) -> PreparedTurn:
        del record, context, previous_error
        return PreparedTurn(
            observation={"game": {"phase": "lobby"}},
            tools=[],
            instructions="test instructions",
            prompt_cache_key="test-cache-key",
            decision=object(),  # type: ignore[arg-type]
        )

    async def run_turn(self, record, prepared, context, run_id):
        del record, prepared, run_id
        result = ModelRunResult(
            response_id="response-1",
            output_text="",
            usage={
                "requests": 1,
                "inputTokens": 100,
                "outputTokens": 10,
                "totalTokens": 110,
            },
            response_items=[],
            raw_usage=[],
            context_manifest=self.manifest,
        )
        if self.outcome == "failed":
            raise ModelRunError("model failed", result)
        if self.outcome == "permanent":
            raise PermanentModelError(
                "spending limit exhausted at "
                "https://provider.test/settings/keys/private-key-id",
                result,
            )
        if self.outcome == "cancelled":
            raise ModelRunCancelled(result)
        context.action_taken = ActionTaken(
            name="choose_house",
            arguments={"house_id": "stark"},
            messages=[{"type": "choose-house", "house": "stark"}],
        )
        return result


class ConnectionLossHarness(ContextManifestHarness):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()

    async def run_turn(self, record, prepared, context, run_id):
        del record, prepared, context, run_id
        self.started.set()
        raise GameConnectionLost("connection changed")


class RetryingHarness(ContextManifestHarness):
    def __init__(self, failures_before_success: int, *, capacity: bool) -> None:
        super().__init__()
        self.failures_before_success = failures_before_success
        self.capacity = capacity
        self.attempts = 0
        self.completed = asyncio.Event()

    async def run_turn(self, record, prepared, context, run_id):
        self.attempts += 1
        if self.attempts <= self.failures_before_success:
            result = ModelRunResult(
                response_id=None,
                output_text="",
                usage={
                    "requests": 0,
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0,
                },
                response_items=[],
                raw_usage=[],
                context_manifest=self.manifest,
            )
            error_type = (
                TransientProviderCapacityError if self.capacity else ModelRunError
            )
            raise error_type("provider unavailable", result)
        result = await super().run_turn(record, prepared, context, run_id)
        self.completed.set()
        return result


class ErrorRecordingHarness(ContextManifestHarness):
    def __init__(self, outcome: str = "completed") -> None:
        super().__init__(outcome)
        self.previous_errors: list[str | None] = []

    def prepare_turn(self, record, context, previous_error) -> PreparedTurn:
        self.previous_errors.append(previous_error)
        return super().prepare_turn(record, context, previous_error)


class BlockingActivityHarness(ContextManifestHarness):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def run_turn(self, record, prepared, context, run_id):
        for request_index in range(1, 11):
            context.report_activity(
                "model-request-started",
                {
                    "requestIndex": request_index,
                    "scope": "rules-oracle" if request_index == 10 else "agent",
                    "inputItemCount": request_index + 2,
                    "prompt": "private prompt body",
                    "authorization": "Bearer private-token",
                },
            )
        self.started.set()
        await self.release.wait()
        context.report_activity(
            "model-request-completed",
            {
                "requestIndex": 10,
                "scope": "rules-oracle",
                "responseId": "response-10",
                "outputItemCount": 1,
                "usage": {
                    "requests": 1,
                    "inputTokens": 100,
                    "outputTokens": 10,
                    "totalTokens": 110,
                    "providerSecret": "private usage body",
                },
                "durationMs": 25,
                "result": "private result body",
            },
        )
        return await super().run_turn(record, prepared, context, run_id)


def manifest_manager(tmp_path, outcome: str = "completed"):
    database = Database(tmp_path / f"manager-{outcome}.db")
    store = AgentStore(database)
    harness = ContextManifestHarness(outcome)
    manager = AgentManager(store=store, harness=harness)
    agent = store.create_agent(
        AgentCreate(
            name="Manifest Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )
    manager.sessions[agent.id] = AgentSession(
        status="connected", client=FakeRunClient()
    )
    return database, store, harness, manager, agent


def lobby_manager(tmp_path, returned_settings: dict):
    database = Database(tmp_path / "lobby-manager.db")
    store = AgentStore(database)
    manager = AgentManager(
        store=store,
        harness=StrategicHarness(UnusedRunner(), store),
    )
    agent = store.create_agent(
        AgentCreate(
            name="Lobby Owner",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="1",
            auth_token="secret",
        )
    )
    client = FakeLobbyClient(returned_settings)
    manager.sessions[agent.id] = AgentSession(status="connected", client=client)
    return database, manager, agent, client


@pytest.mark.asyncio
async def test_configure_lobby_verifies_all_accepted_settings(tmp_path) -> None:
    sent = {
        "setupId": "base-game",
        "playerCount": 6,
        "pbem": False,
        "vassals": False,
        "victoryPointsCountNeededToWin": 7,
    }
    serialized = {
        "setupId": "base-game",
        "playerCount": 6,
        "pbem": False,
    }
    database, manager, agent, client = lobby_manager(tmp_path, serialized)

    result = await manager.configure_lobby(
        agent.id,
        LobbySetupRequest(pbem=False),
    )

    assert result == sent
    assert client.sent == [{"type": "change-game-settings", "settings": sent}]
    database.close()


@pytest.mark.asyncio
async def test_configure_lobby_rejects_partially_applied_settings(tmp_path) -> None:
    returned = {
        "setupId": "base-game",
        "playerCount": 6,
        "pbem": True,
        "vassals": False,
        "victoryPointsCountNeededToWin": 7,
    }
    database, manager, agent, _client = lobby_manager(tmp_path, returned)

    with pytest.raises(RuntimeError, match="did not accept"):
        await manager.configure_lobby(
            agent.id,
            LobbySetupRequest(pbem=False),
        )

    database.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("child_state", "expected"),
    [
        ({"type": "ingame"}, {"started": True, "readyCheck": False}),
        (
            {"type": "lobby", "readyUsers": []},
            {"started": False, "readyCheck": True},
        ),
    ],
)
async def test_launch_game_verifies_authoritative_result(
    tmp_path, child_state, expected
) -> None:
    database, manager, agent, client = lobby_manager(tmp_path, {})
    client.synced_snapshot["childGameState"] = child_state

    result = await manager.launch_game(agent.id)

    assert result == expected
    assert client.sent == [{"type": "launch-game"}]
    database.close()


@pytest.mark.asyncio
async def test_launch_game_rejects_unchanged_lobby(tmp_path) -> None:
    database, manager, agent, client = lobby_manager(tmp_path, {})

    with pytest.raises(RuntimeError, match="did not accept"):
        await manager.launch_game(agent.id)

    assert client.sent == [{"type": "launch-game"}]
    database.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "child_state",
    [
        {"type": "lobby", "readyUsers": ["1"]},
        {"type": "ingame"},
    ],
)
async def test_lobby_ready_verifies_authoritative_result(tmp_path, child_state) -> None:
    database, manager, agent, client = lobby_manager(tmp_path, {})
    client.synced_snapshot["childGameState"] = child_state
    session = manager.sessions[agent.id]

    await manager._confirm_lobby_ready(agent.id, session, agent.user_id)

    assert client.sent == [{"type": "ready"}]
    assert manager.store.list_events(agent.id)[-1].kind == "lobby-ready-accepted"
    database.close()


@pytest.mark.asyncio
async def test_lobby_ready_records_rejected_response(tmp_path) -> None:
    database, manager, agent, client = lobby_manager(tmp_path, {})
    client.synced_snapshot["childGameState"] = {
        "type": "lobby",
        "readyUsers": [],
    }
    session = manager.sessions[agent.id]

    await manager._confirm_lobby_ready(agent.id, session, agent.user_id)

    assert session.last_error == "The game server did not accept the ready response"
    assert manager.store.list_events(agent.id)[-1].kind == "lobby-ready-failed"
    database.close()


@pytest.mark.asyncio
async def test_permanent_provider_error_stops_all_autoplay_and_is_redacted(
    tmp_path,
) -> None:
    database, store, harness, manager, agent = manifest_manager(tmp_path, "permanent")
    second = store.create_agent(
        AgentCreate(
            name="Second Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="3",
            auth_token="secret",
        )
    )
    manager.sessions[agent.id].autoplay = True
    manager.sessions[second.id] = AgentSession(
        status="connected", client=FakeRunClient(), autoplay=True
    )

    with pytest.raises(PermanentModelError) as raised:
        await manager.run_once(agent.id)

    assert "private-key-id" not in str(raised.value)
    assert all(not session.autoplay for session in manager.sessions.values())
    trace = store.get_run(agent.id, store.list_runs(agent.id)[0]["id"])
    assert trace is not None
    assert "private-key-id" not in (trace["error"] or "")
    serialized_events = str(
        [event.payload for event in store.list_events(agent.id)]
        + [event.payload for event in store.list_events(second.id)]
    )
    assert "private-key-id" not in serialized_events
    assert "permanent-provider-error" in serialized_events
    database.close()


@pytest.mark.asyncio
async def test_manager_records_each_distinct_player_snapshot(tmp_path) -> None:
    database = Database(tmp_path / "manager.db")
    store = AgentStore(database)
    harness = StrategicHarness(UnusedRunner(), store)
    connection = FakeConnection()

    async def connect(_url: str) -> FakeConnection:
        return connection

    manager = AgentManager(
        store=store,
        harness=harness,
        connection_factory=connect,
    )
    agent = store.create_agent(
        AgentCreate(
            name="Connected Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )

    await manager.start(agent.id)
    assert len(store.list_snapshots(agent.id)) == 1

    update = encode_message(
        {"type": "house-chosen", "players": [["baratheon", "1"], ["stark", "2"]]}
    )
    await connection.incoming.put(update)
    await _wait_for_received_events(store, agent.id, 1)
    assert len(store.list_snapshots(agent.id)) == 2

    await connection.incoming.put(update)
    await _wait_for_received_events(store, agent.id, 2)
    assert len(store.list_snapshots(agent.id)) == 2

    snapshots = store.list_snapshots(agent.id)
    latest = store.get_snapshot(agent.id, snapshots[0]["id"])
    first = store.get_snapshot(agent.id, snapshots[1]["id"])
    assert latest["snapshot"]["childGameState"]["players"] == [
        ["baratheon", "1"],
        ["stark", "2"],
    ]
    assert first["snapshot"] == lobby_snapshot()

    await manager.stop_all()
    database.close()


@pytest.mark.asyncio
async def test_manager_reconnects_once_and_preserves_autoplay(tmp_path) -> None:
    database = Database(tmp_path / "reconnect.db")
    store = AgentStore(database)
    first = FakeConnection()
    replacement = lobby_snapshot()
    replacement["leafStateId"] = "leaf-after-reconnect"
    second = FakeConnection(replacement)
    connections = iter((first, second))
    connection_count = 0

    async def connect(_url: str) -> FakeConnection:
        nonlocal connection_count
        connection_count += 1
        return next(connections)

    manager = AgentManager(
        store=store,
        harness=StrategicHarness(UnusedRunner(), store),
        connection_factory=connect,
        reconnect_retry_base_seconds=0.01,
        reconnect_retry_max_seconds=0.02,
    )
    agent = store.create_agent(
        AgentCreate(
            name="Reconnecting Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )
    await manager.start(agent.id)
    manager.set_autoplay(agent.id, True)
    original_autoplay_task = manager.sessions[agent.id].autoplay_task

    await first.incoming.put(None)
    for _ in range(200):
        session = manager.sessions[agent.id]
        if session.status == "connected" and session.client.connection_generation == 2:
            break
        await asyncio.sleep(0.005)

    session = manager.sessions[agent.id]
    assert connection_count == 2
    assert session.status == "connected"
    assert session.client.snapshot["leafStateId"] == "leaf-after-reconnect"
    assert session.autoplay is True
    assert session.autoplay_task is original_autoplay_task
    assert session.reconnect_task is None
    statuses = [
        event.payload["status"]
        for event in store.list_events(agent.id)
        if event.kind == "connection-status"
    ]
    assert "reconnecting" in statuses

    await manager.stop_all()
    database.close()


@pytest.mark.asyncio
async def test_stop_cancels_reconnect_backoff(tmp_path) -> None:
    database = Database(tmp_path / "reconnect-stop.db")
    store = AgentStore(database)
    first = FakeConnection()
    retry_attempted = asyncio.Event()
    connection_count = 0

    async def connect(_url: str) -> FakeConnection:
        nonlocal connection_count
        connection_count += 1
        if connection_count == 1:
            return first
        retry_attempted.set()
        raise OSError("server unavailable")

    manager = AgentManager(
        store=store,
        harness=StrategicHarness(UnusedRunner(), store),
        connection_factory=connect,
        reconnect_retry_base_seconds=0.2,
        reconnect_retry_max_seconds=0.2,
    )
    agent = store.create_agent(
        AgentCreate(
            name="Stopped Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )
    await manager.start(agent.id)
    await first.incoming.put(None)
    await asyncio.wait_for(retry_attempted.wait(), timeout=0.5)

    await asyncio.wait_for(manager.stop(agent.id), timeout=0.5)
    await asyncio.sleep(0.25)

    assert connection_count == 2
    assert agent.id not in manager.sessions
    database.close()


@pytest.mark.asyncio
async def test_sync_timeout_reconnects_without_replaying_request(tmp_path) -> None:
    database = Database(tmp_path / "sync-timeout.db")
    store = AgentStore(database)
    first = FakeConnection()
    replacement = lobby_snapshot()
    replacement["leafStateId"] = "authoritative-reconnect-leaf"
    second = FakeConnection(replacement)
    connections = iter((first, second))

    async def connect(_url: str) -> FakeConnection:
        return next(connections)

    manager = AgentManager(
        store=store,
        harness=StrategicHarness(UnusedRunner(), store),
        connection_factory=connect,
        reconnect_retry_base_seconds=0.01,
        reconnect_retry_max_seconds=0.02,
    )
    agent = store.create_agent(
        AgentCreate(
            name="Sync Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )
    await manager.start(agent.id)

    with pytest.raises(GameConnectionLost, match="authoritative snapshot"):
        await manager.sessions[agent.id].client.sync_snapshot(timeout=0.01)
    for _ in range(200):
        session = manager.sessions[agent.id]
        if session.status == "connected" and session.client.connection_generation == 2:
            break
        await asyncio.sleep(0.005)

    session = manager.sessions[agent.id]
    assert session.client.snapshot["leafStateId"] == "authoritative-reconnect-leaf"
    assert [message["type"] for message in first.sent] == [
        "authenticate",
        "sync-game",
    ]
    assert [message["type"] for message in second.sent] == ["authenticate"]
    await manager.stop_all()
    database.close()


@pytest.mark.asyncio
async def test_banned_initial_connection_is_terminal(tmp_path) -> None:
    database = Database(tmp_path / "banned.db")
    store = AgentStore(database)
    connection = FakeConnection(banned=True)
    connection_count = 0

    async def connect(_url: str) -> FakeConnection:
        nonlocal connection_count
        connection_count += 1
        return connection

    manager = AgentManager(
        store=store,
        harness=StrategicHarness(UnusedRunner(), store),
        connection_factory=connect,
    )
    agent = store.create_agent(
        AgentCreate(
            name="Banned Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )

    with pytest.raises(RuntimeError, match="closed during authentication"):
        await manager.start(agent.id)

    assert manager.sessions[agent.id].status == "banned"
    assert manager.sessions[agent.id].reconnect_task is None
    assert connection_count == 1
    await manager.stop_all()
    database.close()


def test_reconnect_backoff_is_capped_without_exponential_growth() -> None:
    delay = 0.0
    observed = []
    for _ in range(8):
        delay = _next_reconnect_delay(delay, 1, 5)
        observed.append(delay)

    assert observed == [1, 2, 4, 5, 5, 5, 5, 5]


@pytest.mark.asyncio
async def test_connection_loss_does_not_consume_autoplay_failure_budget(
    tmp_path,
) -> None:
    database = Database(tmp_path / "autoplay-connection-loss.db")
    store = AgentStore(database)
    harness = ConnectionLossHarness()
    manager = AgentManager(store=store, harness=harness)
    agent = store.create_agent(
        AgentCreate(
            name="Network Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )
    client = FakeRunClient()
    client.snapshot = planning_snapshot()
    session = AgentSession(
        status="connected",
        client=client,
        autoplay=True,
        has_connected=True,
    )
    manager.sessions[agent.id] = session
    manager._schedule_autoplay(agent.id, session)
    await asyncio.wait_for(harness.started.wait(), timeout=0.5)
    manager.set_autoplay(agent.id, False)
    assert session.autoplay_task is not None
    await asyncio.wait_for(session.autoplay_task, timeout=2)

    assert session.general_failures == 0
    assert session.capacity_failures == 0
    assert session.failure_leaf_id is None
    assert session.last_error is None
    database.close()


@pytest.mark.asyncio
async def test_capacity_rejections_get_the_separate_retry_budget(tmp_path) -> None:
    database = Database(tmp_path / "autoplay-capacity.db")
    store = AgentStore(database)
    harness = RetryingHarness(3, capacity=True)
    manager = AgentManager(
        store=store,
        harness=harness,
        autoplay_max_consecutive_failures=2,
        autoplay_retry_base_seconds=0.001,
        autoplay_max_capacity_failures=4,
        autoplay_capacity_retry_base_seconds=0.001,
    )
    agent = store.create_agent(
        AgentCreate(
            name="Capacity Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )
    client = FakeRunClient()
    client.snapshot = planning_snapshot()
    session = AgentSession(
        status="connected",
        client=client,
        autoplay=True,
        has_connected=True,
    )
    manager.sessions[agent.id] = session
    manager._schedule_autoplay(agent.id, session)

    await asyncio.wait_for(harness.completed.wait(), timeout=1)
    manager.set_autoplay(agent.id, False)
    assert session.autoplay_task is not None
    await asyncio.wait_for(session.autoplay_task, timeout=1)

    assert harness.attempts == 4
    assert [run["status"] for run in store.list_runs(agent.id)] == [
        "completed",
        "failed",
        "failed",
        "failed",
    ]
    assert session.general_failures == 0
    assert session.capacity_failures == 0
    assert session.failure_leaf_id is None
    assert session.last_error is None
    database.close()


@pytest.mark.asyncio
async def test_non_capacity_failures_keep_the_strict_retry_budget(tmp_path) -> None:
    database = Database(tmp_path / "autoplay-general-failure.db")
    store = AgentStore(database)
    harness = RetryingHarness(2, capacity=False)
    manager = AgentManager(
        store=store,
        harness=harness,
        autoplay_max_consecutive_failures=2,
        autoplay_retry_base_seconds=0.001,
        autoplay_max_capacity_failures=4,
        autoplay_capacity_retry_base_seconds=0.001,
    )
    agent = store.create_agent(
        AgentCreate(
            name="Strict Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )
    client = FakeRunClient()
    client.snapshot = planning_snapshot()
    session = AgentSession(
        status="connected",
        client=client,
        autoplay=True,
        has_connected=True,
    )
    manager.sessions[agent.id] = session
    manager._schedule_autoplay(agent.id, session)
    assert session.autoplay_task is not None

    await asyncio.wait_for(session.autoplay_task, timeout=1)

    assert harness.attempts == 2
    assert [run["status"] for run in store.list_runs(agent.id)] == [
        "failed",
        "failed",
    ]
    assert session.autoplay is False
    assert session.general_failures == 2
    assert session.capacity_failures == 0
    database.close()


@pytest.mark.asyncio
async def test_model_error_is_reused_only_for_the_same_game_state(tmp_path) -> None:
    database = Database(tmp_path / "state-scoped-error.db")
    store = AgentStore(database)
    harness = ErrorRecordingHarness("failed")
    manager = AgentManager(store=store, harness=harness)
    agent = store.create_agent(
        AgentCreate(
            name="State-scoped Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="secret",
        )
    )
    first_snapshot = copy.deepcopy(FakeRunClient.snapshot)
    first_snapshot["leafStateId"] = "state-a"
    client = FakeRunClient()
    client.snapshot = first_snapshot
    session = AgentSession(status="connected", client=client)
    manager.sessions[agent.id] = session

    with pytest.raises(RuntimeError, match="model failed"):
        await manager._run_once(agent.id)

    harness.outcome = "completed"
    same_state_result = await manager._run_once(agent.id)
    assert same_state_result["decision"]["name"] == "choose_house"
    assert harness.previous_errors == [None, "model failed"]

    harness.outcome = "failed"
    with pytest.raises(RuntimeError, match="model failed"):
        await manager._run_once(agent.id)
    client.snapshot = copy.deepcopy(first_snapshot)
    client.snapshot["leafStateId"] = "state-b"
    harness.outcome = "completed"
    later_state_result = await manager._run_once(agent.id)

    assert later_state_result["decision"]["name"] == "choose_house"
    assert harness.previous_errors[-2:] == [None, None]
    assert session.last_error is None
    assert session.failure_leaf_id is None
    assert session.general_failures == 0
    assert session.capacity_failures == 0
    database.close()


async def _wait_for_received_events(
    store: AgentStore, agent_id: str, expected: int
) -> None:
    for _ in range(100):
        received = [
            event
            for event in store.list_events(agent_id)
            if event.kind == "game-message-received"
        ]
        if len(received) >= expected:
            return
        await asyncio.sleep(0)
    raise AssertionError(f"Expected {expected} received game messages")


def test_non_live_monitoring_uses_one_saved_snapshot_source(tmp_path) -> None:
    database = Database(tmp_path / "saved-monitoring.db")
    store = AgentStore(database)
    manager = AgentManager(
        store=store,
        harness=StrategicHarness(UnusedRunner(), store),
    )
    agent = store.create_agent(
        AgentCreate(
            name="Saved Wolf",
            model="test-model",
            user_id="2",
            auth_token="secret",
        )
    )
    saved = copy.deepcopy(planning_snapshot())
    saved["ownerUserId"] = "2"
    store.record_snapshot(agent.id, saved)
    disconnected_client = FakeRunClient()
    disconnected_client.snapshot = None
    manager.sessions[agent.id] = AgentSession(
        status="reconnecting",
        client=disconnected_client,
        observation={
            "game": {"stateId": "stale-memory", "phase": "lobby"},
            "you": {"userId": "2", "houseId": None},
            "isYourTurn": False,
        },
    )

    monitor = manager.list_monitoring()[0]

    assert monitor["stateStatus"]["source"] == "saved"
    assert monitor["stateStatus"]["actionable"] is False
    assert monitor["state"]["game"]["stateId"] == "leaf-2"
    assert monitor["state"]["player"]["houseId"] == "stark"
    assert monitor["state"]["isOwner"] is True
    database.close()


def test_live_monitoring_marks_a_required_turn_actionable(tmp_path) -> None:
    database = Database(tmp_path / "live-monitoring.db")
    store = AgentStore(database)
    harness = StrategicHarness(UnusedRunner(), store)
    manager = AgentManager(store=store, harness=harness)
    agent = store.create_agent(
        AgentCreate(
            name="Live Wolf",
            model="test-model",
            user_id="2",
            auth_token="secret",
        )
    )
    snapshot = planning_snapshot()
    client = FakeRunClient()
    client.snapshot = snapshot
    observation = harness.preview_observation(
        agent,
        build_context(snapshot, agent.user_id),
    )
    manager.sessions[agent.id] = AgentSession(
        status="connected",
        client=client,
        observation=observation,
    )

    monitor = manager.list_monitoring()[0]

    assert monitor["stateStatus"] == {
        "source": "live",
        "capturedAt": None,
        "actionable": True,
    }
    assert monitor["state"]["isYourTurn"] is True
    database.close()


def test_monitoring_state_exposes_structured_public_game_data() -> None:
    observation = {
        "game": {"round": 2, "phase": "action"},
        "you": {
            "userId": "2",
            "houseId": "stark",
            "controlledRegions": ["winterfell"],
            "availableHouseCards": [
                {
                    "id": "robb-stark",
                    "name": "Robb Stark",
                    "strength": 3,
                    "swords": 0,
                    "towers": 0,
                    "ability": "robb-stark",
                }
            ],
        },
        "houses": [
            {
                "id": "stark",
                "name": "Stark",
                "currentVictoryPoints": 2,
                "controlledCastleAreas": 2,
            }
        ],
        "houseCardStatus": [
            {
                "houseId": "stark",
                "houseName": "Stark",
                "detailsVisible": True,
                "totalCount": 2,
                "availableCount": 1,
                "usedCount": 1,
                "disabledCount": 0,
                "availableCards": [
                    {
                        "id": "robb-stark",
                        "name": "Robb Stark",
                        "strength": 3,
                        "swords": 0,
                        "towers": 0,
                        "ability": "robb-stark",
                    }
                ],
            }
        ],
        "map": {
            "regions": [
                {
                    "id": "winterfell",
                    "name": "Winterfell",
                    "type": "land",
                    "castleLevel": 2,
                    "supplyIcons": 1,
                    "crownIcons": 1,
                }
            ]
        },
        "board": [
            {
                "id": "winterfell",
                "controlPowerToken": "stark",
                "garrison": 2,
                "revealedOrder": {
                    "regionId": "winterfell",
                    "regionName": "Winterfell",
                    "orderId": 3,
                    "order": "March +1",
                },
                "units": [
                    {
                        "id": 1,
                        "type": "footman",
                        "allegiance": "stark",
                        "wounded": False,
                    }
                ],
            }
        ],
        "revealedOrders": [
            {
                "regionId": "winterfell",
                "regionName": "Winterfell",
                "orderId": 3,
                "order": "March +1",
            }
        ],
        "actionGuidance": {
            "decision": "march",
            "legalOrderRegions": ["winterfell"],
        },
        "tracks": {"ironThrone": ["stark"]},
    }

    state = _monitoring_state(observation, {"ownerUserId": "2"})

    assert state is not None
    assert state["standings"] == observation["houses"]
    assert state["board"] == [
        {
            "id": "winterfell",
            "name": "Winterfell",
            "type": "land",
            "castleLevel": 2,
            "supplyIcons": 1,
            "crownIcons": 1,
            "controlPowerToken": "stark",
            "garrison": 2,
            "units": observation["board"][0]["units"],
            "revealedOrder": observation["revealedOrders"][0],
        }
    ]
    assert state["houseCardStatus"] == observation["houseCardStatus"]
    assert state["revealedOrders"] == observation["revealedOrders"]
    assert state["actionGuidance"] == observation["actionGuidance"]
    assert state["player"]["availableHouseCards"][0]["ability"] == "robb-stark"
    assert state["isOwner"] is True


def test_monitoring_state_uses_planning_constraints_as_action_guidance() -> None:
    observation = {
        "game": {"phase": "planning"},
        "you": {"userId": "2", "houseId": "stark"},
        "planningConstraints": {
            "legalRegions": ["winterfell"],
            "requiredOrderCount": 3,
        },
    }

    state = _monitoring_state(observation, None)

    assert state is not None
    assert state["actionGuidance"] == {
        "decision": "planning",
        "legalRegions": ["winterfell"],
        "requiredOrderCount": 3,
    }
