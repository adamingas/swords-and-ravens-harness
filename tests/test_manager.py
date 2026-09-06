import asyncio

import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.game.codec import decode_message, encode_message
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.manager import AgentManager
from raven_harness.schemas import AgentCreate

from conftest import lobby_snapshot


class UnusedRunner:
    rules_oracle_available = False

    async def run_once(self, **_kwargs):
        raise AssertionError("The model should not run in this test")


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
