import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any
from uuid import uuid4

from websockets.asyncio.client import connect

from ..errors import safe_error_text
from .codec import decode_message, encode_message
from .state import apply_server_message

EventHandler = Callable[[str, dict[str, Any]], None]
ConnectionFactory = Callable[[str], Awaitable[Any]]


class GameConnectionLost(RuntimeError):
    """A gameplay operation cannot safely continue on the current socket."""


class SwordsAndRavensClient:
    def __init__(
        self,
        *,
        url: str,
        game_id: str,
        user_id: str,
        auth_token: str,
        connection_factory: ConnectionFactory = connect,
        on_event: EventHandler | None = None,
    ) -> None:
        self.url = url
        self.auth_data = {
            "gameId": game_id,
            "userId": user_id,
            "requestUserId": user_id,
            "authToken": auth_token,
        }
        self.connection_factory = connection_factory
        self.on_event = on_event or (lambda _kind, _payload: None)
        self.connection: Any | None = None
        self.connection_generation = 0
        self.snapshot: dict[str, Any] | None = None
        self.status = "stopped"
        self.recent_events: deque[dict[str, Any]] = deque(maxlen=30)
        self._authenticated = asyncio.Event()
        self._receive_task: asyncio.Task[None] | None = None
        self._ping_task: asyncio.Task[None] | None = None
        self._send_lock = asyncio.Lock()
        self._sync_requests: dict[str, asyncio.Future[dict[str, Any]]] = {}

    async def connect(self, timeout: float = 10) -> dict[str, Any]:
        if self.connection is not None or (
            self._receive_task is not None and not self._receive_task.done()
        ):
            raise RuntimeError("Client is already started")
        self._authenticated.clear()
        self.snapshot = None
        self.recent_events.clear()
        self._set_status("connecting")
        try:
            self.connection = await asyncio.wait_for(
                self.connection_factory(self.url), timeout
            )
            self.connection_generation += 1
            connection = self.connection
            self._receive_task = asyncio.create_task(
                self._receive_loop(connection)
            )
            await self.send(
                {"type": "authenticate", "authData": self.auth_data}, require_auth=False
            )
            await asyncio.wait_for(self._authenticated.wait(), timeout)
            if self.connection is None or self.status != "connected":
                raise RuntimeError("Game connection closed during authentication")
            self._ping_task = asyncio.create_task(self._ping_loop(connection))
        except BaseException:
            await self.close(status="banned" if self.status == "banned" else "error")
            raise
        if self.snapshot is None:
            raise RuntimeError("Game authenticated without returning a snapshot")
        return self.snapshot

    async def send(
        self,
        message: dict[str, Any],
        *,
        require_auth: bool = True,
        expected_generation: int | None = None,
    ) -> None:
        async with self._send_lock:
            self._require_generation(expected_generation)
            connection = self.connection
            if connection is None:
                raise GameConnectionLost("Game connection is not open")
            if require_auth and (self.snapshot is None or self.status != "connected"):
                raise GameConnectionLost("Game connection is not authenticated")
            try:
                await connection.send(encode_message(message))
            except asyncio.CancelledError:
                raise
            except Exception as error:
                if self.connection is connection:
                    await self._disconnect(connection)
                raise GameConnectionLost("Game connection closed while sending") from error
        self.on_event("sent", _redact(message))

    async def sync_snapshot(
        self,
        timeout: float = 10,
        *,
        expected_generation: int | None = None,
    ) -> dict[str, Any]:
        """Fetch a fresh player-scoped snapshot after earlier socket messages."""

        self._require_generation(expected_generation)
        if (
            self.connection is None
            or self.snapshot is None
            or self.status != "connected"
        ):
            raise GameConnectionLost("Game connection is not authenticated")
        request_id = str(uuid4())
        connection = self.connection
        assert connection is not None
        future = asyncio.get_running_loop().create_future()
        self._sync_requests[request_id] = future
        try:
            await self.send(
                {"type": "sync-game", "requestId": request_id},
                expected_generation=expected_generation,
            )
            snapshot = await asyncio.wait_for(future, timeout)
            self._require_generation(expected_generation)
            return snapshot
        except TimeoutError as error:
            await self._disconnect(connection)
            raise GameConnectionLost(
                f"Game server did not return an authoritative snapshot within {timeout:g} seconds"
            ) from error
        finally:
            self._sync_requests.pop(request_id, None)

    async def close(self, *, status: str = "stopped") -> None:
        current = asyncio.current_task()
        connection = self.connection
        self.connection = None
        self.snapshot = None
        self._authenticated.clear()
        self.recent_events.clear()
        tasks = [
            task
            for task in (self._ping_task, self._receive_task)
            if task is not None and task is not current
        ]
        for task in tasks:
            task.cancel()
        if connection is not None:
            with suppress(Exception):
                await connection.close()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for future in self._sync_requests.values():
            if not future.done():
                future.cancel()
        self._sync_requests.clear()
        self._ping_task = None
        self._receive_task = None
        self._set_status(status)

    async def _receive_loop(self, connection: Any) -> None:
        try:
            async for payload in connection:
                if self.connection is not connection:
                    return
                message = decode_message(payload)
                self._on_message(message)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self.on_event("error", {"message": safe_error_text(error)})
        finally:
            if self.connection is connection:
                await self._disconnect(connection)
            if self._receive_task is asyncio.current_task():
                self._receive_task = None

    def _on_message(self, message: dict[str, Any]) -> None:
        if message.get("type") == "authenticate-response":
            self.snapshot = message["game"]
            self._set_status("connected")
            self._authenticated.set()
            self.on_event("snapshot", {})
            return
        if message.get("type") == "game-snapshot":
            request_id = str(message.get("requestId", ""))
            future = self._sync_requests.get(request_id)
            game = message.get("game")
            if future is None or not isinstance(game, dict):
                return
            self.snapshot = game
            if not future.done():
                future.set_result(game)
            self.on_event("game-message", {"type": "game-snapshot"})
            self.on_event("snapshot", {})
            return
        if message.get("type") == "banned-response":
            self._set_status("banned")
            self._authenticated.set()
            return
        if self.snapshot is not None:
            apply_server_message(self.snapshot, message)
        self.recent_events.append(message)
        self.on_event("game-message", message)
        self.on_event("snapshot", {})

    async def _ping_loop(self, connection: Any) -> None:
        try:
            while True:
                await asyncio.sleep(30)
                await self.send({"type": "ping"}, require_auth=False)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self.on_event("error", {"message": safe_error_text(error)})
            if self.connection is connection:
                await self._disconnect(connection)

    async def _disconnect(self, connection: Any) -> None:
        """Retire exactly one socket and notify the manager after teardown completes."""

        if self.connection is not connection:
            return
        self.connection = None
        self.snapshot = None
        self._authenticated.clear()
        self.recent_events.clear()
        current = asyncio.current_task()
        tasks = [
            task
            for task in (self._ping_task, self._receive_task)
            if task is not None and task is not current
        ]
        for task in tasks:
            task.cancel()
        with suppress(Exception):
            await connection.close()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for future in self._sync_requests.values():
            if not future.done():
                future.set_exception(
                    GameConnectionLost(
                        "Game connection closed before synchronization"
                    )
                )
        if self._ping_task is not current:
            self._ping_task = None
        if self._receive_task is not current:
            self._receive_task = None
        if self.status not in {"banned", "stopped", "error"}:
            self._set_status("disconnected")

    def _require_generation(self, expected_generation: int | None) -> None:
        if (
            expected_generation is not None
            and expected_generation != self.connection_generation
        ):
            raise GameConnectionLost(
                "Game connection changed during the model decision; "
                "the action will not be replayed"
            )

    def _set_status(self, status: str) -> None:
        self.status = status
        self.on_event("status", {"status": status})


def _redact(message: dict[str, Any]) -> dict[str, Any]:
    if message.get("type") != "authenticate":
        return message
    return {
        "type": "authenticate",
        "authData": {**message["authData"], "authToken": "[redacted]"},
    }
