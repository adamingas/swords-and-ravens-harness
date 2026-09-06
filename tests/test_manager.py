import asyncio

import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.game.codec import decode_message, encode_message
from raven_harness.harness.actions import ActionTaken
from raven_harness.harness.interface import PreparedTurn
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.manager import AgentManager, AgentSession, _monitoring_state
from raven_harness.models.openai_agent import (
    ModelRunCancelled,
    ModelRunError,
    ModelRunResult,
    PermanentModelError,
)
from raven_harness.schemas import AgentCreate

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


class FakeConnection:
    def __init__(self) -> None:
        self.incoming: asyncio.Queue[str | None] = asyncio.Queue()

    def __aiter__(self) -> "FakeConnection":
        return self

    async def __anext__(self) -> str:
        value = await self.incoming.get()
        if value is None:
            raise StopAsyncIteration
        return value

    async def send(self, payload: str) -> None:
        message = decode_message(payload)
        if message["type"] == "authenticate":
            await self.incoming.put(
                encode_message(
                    {
                        "type": "authenticate-response",
                        "userId": message["authData"]["userId"],
                        "game": lobby_snapshot(),
                    }
                )
            )

    async def close(self) -> None:
        await self.incoming.put(None)


class FakeRunClient:
    status = "connected"
    snapshot = lobby_snapshot()
    recent_events: list[dict] = []


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
            metadata={"gameToolNames": ["choose_house"]},
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


@pytest.mark.asyncio
async def test_manager_persists_effective_context_manifest(tmp_path) -> None:
    database, store, harness, manager, agent = manifest_manager(tmp_path)

    result = await manager.run_once(agent.id)
    trace = store.get_run(agent.id, result["runId"])

    assert trace is not None
    assert trace["contextManifest"] == harness.manifest
    database.close()


@pytest.mark.asyncio
async def test_manager_exposes_bounded_sanitized_live_activity(tmp_path) -> None:
    database = Database(tmp_path / "activity.db")
    store = AgentStore(database)
    harness = BlockingActivityHarness()
    manager = AgentManager(store=store, harness=harness)
    agent = store.create_agent(
        AgentCreate(
            name="Activity Wolf",
            model="test-model",
            game_server_url="ws://game.test",
            game_id="1",
            user_id="2",
            auth_token="private-agent-token",
            game_password="private-game-password",
        )
    )
    manager.sessions[agent.id] = AgentSession(
        status="connected", client=FakeRunClient()
    )

    task = asyncio.create_task(manager.run_once(agent.id))
    await harness.started.wait()

    live = manager.get_runtime(agent.id).model_dump(by_alias=True)
    assert live["currentActivity"]["kind"] == "model-request-started"
    assert live["currentActivity"]["requestIndex"] == 10
    assert len(live["recentActivity"]) == 8
    assert [item["requestIndex"] for item in live["recentActivity"]] == list(
        range(3, 11)
    )
    harness.release.set()
    result = await task

    stopped = manager.get_runtime(agent.id).model_dump(by_alias=True)
    assert stopped["currentActivity"] is None
    assert len(stopped["recentActivity"]) == 8
    assert stopped["recentActivity"][-1]["kind"] == "model-run-completed"
    events = store.list_events(agent.id)
    request_events = [event for event in events if event.kind.startswith("model-request-")]
    assert len(request_events) == 11
    completed = next(
        event for event in request_events if event.kind == "model-request-completed"
    )
    assert completed.payload["runId"] == result["runId"]
    assert completed.payload["usage"] == {
        "requests": 1,
        "inputTokens": 100,
        "outputTokens": 10,
        "totalTokens": 110,
    }
    serialized = str([event.payload for event in request_events])
    assert "private prompt body" not in serialized
    assert "private-token" not in serialized
    assert "private usage body" not in serialized
    assert "private result body" not in serialized
    assert "private-game-password" not in serialized

    for index in range(100):
        store.add_event(agent.id, "game-message-received", {"index": index})
    restarted_manager = AgentManager(store=store, harness=ContextManifestHarness())
    persisted = restarted_manager.get_runtime(agent.id).model_dump(by_alias=True)
    assert persisted["currentActivity"] is None
    assert len(persisted["recentActivity"]) == 8
    assert persisted["recentActivity"][-1]["kind"] == "model-run-completed"
    database.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["failed", "cancelled"])
async def test_manager_persists_partial_result_context_manifest(
    tmp_path, outcome
) -> None:
    database, store, harness, manager, agent = manifest_manager(tmp_path, outcome)
    error_type = RuntimeError if outcome == "failed" else asyncio.CancelledError

    with pytest.raises(error_type):
        await manager._run_once(agent.id)

    trace = store.get_run(agent.id, store.list_runs(agent.id)[0]["id"])
    assert trace is not None
    assert trace["status"] == outcome
    assert trace["contextManifest"] == harness.manifest
    activity = manager.get_runtime(agent.id).recent_activity
    assert activity[-1]["kind"] == f"model-run-{outcome}"
    database.close()


@pytest.mark.asyncio
async def test_permanent_provider_error_stops_all_autoplay_and_is_redacted(
    tmp_path,
) -> None:
    database, store, harness, manager, agent = manifest_manager(
        tmp_path, "permanent"
    )
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

    snapshots = store.list_snapshots(agent.id, include_snapshot=True)
    assert snapshots[0]["snapshot"]["childGameState"]["players"] == [
        ["baratheon", "1"],
        ["stark", "2"],
    ]
    assert snapshots[1]["snapshot"] == lobby_snapshot()

    await manager.stop_all()
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
        }
    ]
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
