import asyncio
from typing import Any

import pytest

from raven_harness.game.client import SwordsAndRavensClient
from raven_harness.game.codec import decode_message, encode_message
from raven_harness.game.state import apply_server_message

from conftest import lobby_snapshot, planning_snapshot


class FakeConnection:
    def __init__(self) -> None:
        self.incoming: asyncio.Queue[str | None] = asyncio.Queue()
        self.closed = False

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
        elif message["type"] == "sync-game":
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
