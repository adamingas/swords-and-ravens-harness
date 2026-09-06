import asyncio
from typing import Any

import pytest

from raven_harness.game.client import GameConnectionLost, SwordsAndRavensClient
from raven_harness.game.codec import decode_message, encode_message
from raven_harness.game.state import apply_server_message

from conftest import lobby_snapshot, planning_snapshot


class FakeConnection:
    def __init__(
        self,
        *,
        answer_sync: bool = True,
        close_after_auth: bool = False,
        snapshot: dict[str, Any] | None = None,
    ) -> None:
        self.incoming: asyncio.Queue[str | None] = asyncio.Queue()
        self.closed = False
        self.answer_sync = answer_sync
        self.close_after_auth = close_after_auth
        self.snapshot = snapshot or lobby_snapshot()
        self.sent: list[dict[str, Any]] = []

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
            await self.incoming.put(
                encode_message(
                    {
                        "type": "authenticate-response",
                        "userId": message["authData"]["userId"],
                        "game": self.snapshot,
                    }
                )
            )
            if self.close_after_auth:
                await self.incoming.put(None)
        elif message["type"] == "sync-game" and self.answer_sync:
            game = lobby_snapshot()
            game["leafStateId"] = "synced-leaf"
            await self.incoming.put(
                encode_message(
                    {
                        "type": "game-snapshot",
                        "requestId": message["requestId"],
                        "game": game,
                    }
                )
            )

    async def close(self) -> None:
        self.closed = True
        await self.incoming.put(None)


@pytest.mark.asyncio
async def test_client_authenticates_and_applies_lobby_updates() -> None:
    connection = FakeConnection()

    async def connect(_url: str) -> FakeConnection:
        return connection

    events: list[tuple[str, dict[str, Any]]] = []
    client = SwordsAndRavensClient(
        url="ws://game.test",
        game_id="1",
        user_id="2",
        auth_token="secret",
        connection_factory=connect,
        on_event=lambda kind, payload: events.append((kind, payload)),
    )
    await client.connect(timeout=0.5)
    assert client.status == "connected"
    assert client.snapshot is not None
    assert (
        next(payload for kind, payload in events if kind == "sent")["authData"][
            "authToken"
        ]
        == "[redacted]"
    )

    await connection.incoming.put(
        encode_message({"type": "house-chosen", "players": [["stark", "2"]]})
    )
    await asyncio.sleep(0)
    assert client.snapshot["childGameState"]["players"] == [["stark", "2"]]
    snapshot = await client.sync_snapshot(timeout=0.5)
    assert snapshot["leafStateId"] == "synced-leaf"
    assert client.snapshot is snapshot
    await client.close()


@pytest.mark.asyncio
async def test_normal_socket_eof_disconnects_and_fails_pending_sync() -> None:
    connection = FakeConnection(answer_sync=False)

    async def connect(_url: str) -> FakeConnection:
        return connection

    client = SwordsAndRavensClient(
        url="ws://game.test",
        game_id="1",
        user_id="2",
        auth_token="secret",
        connection_factory=connect,
    )
    await client.connect(timeout=0.5)
    pending_sync = asyncio.create_task(client.sync_snapshot(timeout=10))
    await asyncio.sleep(0)

    await connection.incoming.put(None)

    with pytest.raises(GameConnectionLost, match="closed before synchronization"):
        await asyncio.wait_for(pending_sync, timeout=0.5)
    assert client.status == "disconnected"
    assert client.connection is None
    assert client._sync_requests == {}
    await client.close()


@pytest.mark.asyncio
async def test_new_connection_generation_replaces_state_and_rejects_stale_send() -> None:
    first = FakeConnection(snapshot=lobby_snapshot())
    replacement = lobby_snapshot()
    replacement["leafStateId"] = "replacement-leaf"
    second = FakeConnection(snapshot=replacement)
    connections = iter((first, second))

    async def connect(_url: str) -> FakeConnection:
        return next(connections)

    client = SwordsAndRavensClient(
        url="ws://game.test",
        game_id="1",
        user_id="2",
        auth_token="secret",
        connection_factory=connect,
    )
    await client.connect(timeout=0.5)
    original_generation = client.connection_generation
    await first.incoming.put(
        encode_message({"type": "house-chosen", "players": [["stark", "2"]]})
    )
    await asyncio.sleep(0)
    assert client.recent_events

    await first.incoming.put(None)
    for _ in range(100):
        if client.status == "disconnected":
            break
        await asyncio.sleep(0)
    assert client.status == "disconnected"
    assert client.snapshot is None
    assert list(client.recent_events) == []

    snapshot = await client.connect(timeout=0.5)
    assert snapshot["leafStateId"] == "replacement-leaf"
    assert client.connection_generation == original_generation + 1
    with pytest.raises(GameConnectionLost, match="will not be replayed"):
        await client.send(
            {"type": "ready"}, expected_generation=original_generation
        )
    assert [message["type"] for message in second.sent] == ["authenticate"]
    await client.close()


@pytest.mark.asyncio
async def test_authentication_does_not_succeed_after_immediate_socket_eof() -> None:
    connection = FakeConnection(close_after_auth=True)

    async def connect(_url: str) -> FakeConnection:
        return connection

    client = SwordsAndRavensClient(
        url="ws://game.test",
        game_id="1",
        user_id="2",
        auth_token="secret",
        connection_factory=connect,
    )

    with pytest.raises(RuntimeError, match="closed during authentication"):
        await client.connect(timeout=0.5)
    assert client.status == "error"
    assert client.connection is None


def test_state_mirror_tracks_turn_units_and_waited_player() -> None:
    snapshot = {
        "childGameState": {
            "type": "ingame",
            "players": [{"userId": "2", "houseId": "stark"}],
            "game": {
                "turn": 1,
                "houses": [],
                "world": {
                    "regions": [
                        {
                            "id": "winterfell",
                            "units": [{"id": 1, "allegiance": "stark"}],
                        },
                        {"id": "white-harbor", "units": []},
                    ]
                },
            },
        }
    }
    waited = {
        "date": 1,
        "leafStateId": "leaf-2",
        "handled": False,
        "hasBeenReactivated": False,
    }

    apply_server_message(
        snapshot,
        {
            "type": "update-waited-for-data",
            "userId": "2",
            "waitedForData": waited,
        },
    )
    apply_server_message(
        snapshot,
        {
            "type": "move-units",
            "from": "winterfell",
            "to": "white-harbor",
            "units": [1],
        },
    )
    apply_server_message(snapshot, {"type": "new-turn"})

    ingame = snapshot["childGameState"]
    assert ingame["players"][0]["waitedForData"] == waited
    assert ingame["game"]["world"]["regions"][0]["units"] == []
    assert ingame["game"]["world"]["regions"][1]["units"][0]["id"] == 1
    assert ingame["game"]["turn"] == 2


def test_state_change_refreshes_authoritative_waited_users() -> None:
    snapshot = planning_snapshot()
    apply_server_message(
        snapshot,
        {
            "type": "game-state-change",
            "level": 3,
            "serializedGameState": {"type": "replace-order"},
            "newLeafId": "next-leaf",
            "waitedForUserIds": ["2"],
        },
    )

    assert snapshot["leafStateId"] == "next-leaf"
    assert snapshot["childGameState"]["waitedForUserIds"] == ["2"]


def test_settings_change_refreshes_available_lobby_houses() -> None:
    snapshot = lobby_snapshot()

    apply_server_message(
        snapshot,
        {
            "type": "game-settings-changed",
            "settings": {"setupId": "base-game", "playerCount": 3},
            "availableHouseIds": ["baratheon", "lannister", "stark"],
        },
    )

    assert snapshot["gameSettings"]["playerCount"] == 3
    assert snapshot["childGameState"]["availableHouseIds"] == [
        "baratheon",
        "lannister",
        "stark",
    ]
