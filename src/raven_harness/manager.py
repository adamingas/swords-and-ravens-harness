from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import uuid4

from opentelemetry.trace import Status, StatusCode, get_current_span

from .agent_store import AgentStore
from .errors import safe_error_text
from .game.client import (
    ConnectionFactory,
    GameConnectionLost,
    SwordsAndRavensClient,
)
from .harness.actions import HarnessRunContext, describe_tools
from .harness.interface import PlayerHarness, PreparedTurn
from .harness.observation import build_context, is_waiting_for_player
from .models.openai_agent import (
    ModelRunCancelled,
    ModelRunError,
    ModelRunResult,
    PermanentModelError,
)
from .schemas import AgentPublic, AgentRecord, AgentRuntime, LobbySetupRequest
from .telemetry import Telemetry, provider_cost


_MODEL_ACTIVITY_KINDS = {
    "model-run-started",
    "model-run-completed",
    "model-run-failed",
    "model-run-cancelled",
    "model-request-started",
    "model-request-completed",
    "model-tool-started",
    "model-tool-completed",
}
_TERMINAL_MODEL_ACTIVITY_KINDS = {
    "model-run-completed",
    "model-run-failed",
    "model-run-cancelled",
}


@dataclass
class AgentSession:
    status: str
    client: SwordsAndRavensClient
    observation: dict[str, Any] | None = None
    last_error: str | None = None
    connected_at: str | None = None
    running: bool = False
    autoplay: bool = False
    autoplay_task: asyncio.Task[None] | None = None
    reconnect_task: asyncio.Task[None] | None = None
    ready_task: asyncio.Task[None] | None = None
    has_connected: bool = False
    failure_leaf_id: str | None = None
    consecutive_failures: int = 0
    current_run_id: str | None = None
    run_started_at: str | None = None
    current_tools: list[str] | None = None
    current_activity: dict[str, Any] | None = None
    recent_activity: list[dict[str, Any]] = field(default_factory=list)


class AgentManager:
    def __init__(
        self,
        *,
        store: AgentStore,
        harness: PlayerHarness,
        connection_factory: ConnectionFactory | None = None,
        telemetry: Telemetry | None = None,
        autoplay_max_consecutive_failures: int = 5,
        autoplay_retry_base_seconds: float = 2,
        reconnect_retry_base_seconds: float = 1,
        reconnect_retry_max_seconds: float = 30,
        durable_game_path: Path | None = None,
    ) -> None:
        self.store = store
        self.harness = harness
        self.connection_factory = connection_factory
        self.telemetry = telemetry or Telemetry.create(endpoint="")
        self.autoplay_max_consecutive_failures = autoplay_max_consecutive_failures
        self.autoplay_retry_base_seconds = autoplay_retry_base_seconds
        self.reconnect_retry_base_seconds = reconnect_retry_base_seconds
        self.reconnect_retry_max_seconds = reconnect_retry_max_seconds
        self.durable_game_path = durable_game_path
        self.sessions: dict[str, AgentSession] = {}

    def list_agents(self) -> list[AgentPublic]:
        return [
            AgentPublic.from_record(record, self.get_runtime(record.id))
            for record in self.store.list_agents()
        ]

    def get_agent(self, agent_id: str) -> AgentPublic | None:
        record = self.store.get_agent(agent_id)
        return (
            AgentPublic.from_record(record, self.get_runtime(agent_id))
            if record
            else None
        )

    def get_runtime(self, agent_id: str) -> AgentRuntime:
        session = self.sessions.get(agent_id)
        if session is None:
            return AgentRuntime(recent_activity=self._stored_model_activity(agent_id))
        observation = session.observation or {}
        return AgentRuntime(
            status=session.status,
            phase=observation.get("game", {}).get("phase"),
            house_id=observation.get("you", {}).get("houseId"),
            last_error=session.last_error,
            connected_at=session.connected_at,
            autoplay=session.autoplay,
            current_run_id=session.current_run_id,
            run_started_at=session.run_started_at,
            current_tools=session.current_tools or [],
            current_activity=session.current_activity,
            recent_activity=session.recent_activity,
        )

    def _stored_model_activity(self, agent_id: str) -> list[dict[str, Any]]:
        """Load the bounded activity timeline for the most recent model run."""

        newest_first: list[dict[str, Any]] = []
        latest_run_id: str | None = None
        for event in self.store.list_events(
            agent_id, kinds=_MODEL_ACTIVITY_KINDS
        ):
            if event.kind not in _MODEL_ACTIVITY_KINDS:
                continue
            run_id = event.payload.get("runId")
            if not isinstance(run_id, str):
                continue
            if latest_run_id is None:
                latest_run_id = run_id
            if run_id != latest_run_id:
                continue
            newest_first.append({"kind": event.kind, **event.payload})
            if len(newest_first) == 8:
                break
        activity = list(reversed(newest_first))
        if activity and activity[-1]["kind"] not in _TERMINAL_MODEL_ACTIVITY_KINDS:
            activity.append(
                {
                    "kind": "model-run-interrupted",
                    "runId": latest_run_id,
                }
            )
        return activity[-8:]

    async def start(self, agent_id: str) -> AgentPublic:
        existing = self.sessions.get(agent_id)
        if existing:
            if existing.status in {"error", "disconnected", "banned", "stopped"}:
                await self.stop(agent_id)
            else:
                raise RuntimeError("Agent is already started")

        record = self._require_agent(agent_id)
        session: AgentSession

        def on_event(kind: str, payload: dict[str, Any]) -> None:
            if kind == "status":
                client_status = str(payload["status"])
                if client_status == "connected":
                    session.last_error = None
                    session.status = "running" if session.running else "connected"
                elif (
                    session.has_connected
                    and client_status in {"connecting", "disconnected", "error"}
                    and self.sessions.get(agent_id) is session
                ):
                    session.status = "reconnecting"
                else:
                    session.status = client_status
                self.store.add_event(
                    agent_id, "connection-status", {"status": session.status}
                )
                if client_status == "disconnected":
                    self._schedule_reconnect(agent_id, session)
            elif kind == "error":
                message = safe_error_text(
                    payload.get("message", "Game connection failed")
                )
                session.last_error = message
                self.store.add_event(
                    agent_id, "connection-error", {"message": message}
                )
            elif kind == "sent":
                self.store.add_event(
                    agent_id, "game-message-sent", _summarize_message(payload)
                )
            elif kind == "game-message":
                self.store.add_event(
                    agent_id, "game-message-received", _summarize_message(payload)
                )
            elif kind == "snapshot" and session.client.snapshot is not None:
                self.store.record_snapshot(agent_id, session.client.snapshot)
                context = build_context(
                    session.client.snapshot,
                    record.user_id,
                    list(session.client.recent_events),
                )
                session.observation = self.harness.preview_observation(
                    record, context
                )
                self._schedule_lobby_ready(agent_id, session, record)
                self._schedule_autoplay(agent_id, session)

        client_args: dict[str, Any] = {
            "url": record.game_server_url,
            "game_id": record.game_id,
            "user_id": record.user_id,
            "auth_token": record.auth_token.get_secret_value(),
            "on_event": on_event,
        }
        if self.connection_factory is not None:
            client_args["connection_factory"] = self.connection_factory
        client = SwordsAndRavensClient(**client_args)
        session = AgentSession(
            status="connecting",
            client=client,
            recent_activity=self._stored_model_activity(agent_id),
        )
        self.sessions[agent_id] = session

        try:
            await client.connect()
            session.has_connected = True
            session.connected_at = datetime.now(timezone.utc).isoformat()
            session.status = client.status
        except Exception as error:
            message = safe_error_text(error)
            session.status = "banned" if client.status == "banned" else "error"
            session.last_error = message
            self.store.add_event(agent_id, "connection-error", {"message": message})
            raise RuntimeError(message) from None
        return self._require_public_agent(agent_id)

    async def stop(self, agent_id: str) -> AgentPublic | None:
        session = self.sessions.pop(agent_id, None)
        if session is not None:
            pending_tasks: list[asyncio.Task[None]] = []
            for task in (
                session.autoplay_task,
                session.reconnect_task,
                session.ready_task,
            ):
                if task and task is not asyncio.current_task():
                    task.cancel()
                    pending_tasks.append(task)
            if pending_tasks:
                await asyncio.gather(*pending_tasks, return_exceptions=True)
            await session.client.close()
            self.store.add_event(agent_id, "connection-status", {"status": "stopped"})
        return self.get_agent(agent_id)

    async def delete(self, agent_id: str) -> bool:
        if self.store.get_agent(agent_id) is None:
            return False
        await self.stop(agent_id)
        await self.harness.clear_agent_history(agent_id)
        return self.store.delete_agent(agent_id)

    async def run_once(self, agent_id: str) -> dict[str, Any]:
        record = self._require_agent(agent_id)
        with self.telemetry.tracer.start_as_current_span(
            "raven.agent.decision",
            attributes={
                "raven.agent.id": record.id,
                "raven.agent.name": record.name,
                "raven.game.id": record.game_id,
                "raven.model": record.model,
            },
        ) as span:
            try:
                result = await self._run_once(agent_id)
            except Exception as error:
                message = safe_error_text(error)
                if isinstance(error, PermanentModelError):
                    self._disable_all_autoplay(message)
                span.record_exception(RuntimeError(message))
                span.set_status(Status(StatusCode.ERROR, message))
                raise
            decision = result["decision"]
            usage = decision["usage"]
            trace_run = self.store.get_run(agent_id, result["runId"])
            span.set_attributes(
                {
                    "raven.run.id": result["runId"],
                    "raven.action": decision["name"],
                    "gen_ai.usage.input_tokens": usage["inputTokens"],
                    "gen_ai.usage.output_tokens": usage["outputTokens"],
                    "raven.cost.usd": provider_cost(
                        trace_run.get("rawUsage") if trace_run else None
                    ),
                }
            )
            span.add_event(
                "raven.game.action",
                {"raven.action": decision["name"]},
            )
            return result

    async def _run_once(self, agent_id: str) -> dict[str, Any]:
        record = self._require_agent(agent_id)
        session = self.sessions.get(agent_id)
        if (
            session is None
            or session.client.snapshot is None
            or session.status != "connected"
        ):
            raise RuntimeError("Agent must be connected before it can run")
        if session.running:
            raise RuntimeError("Agent is already running")

        session.running = True
        session.status = "running"
        previous_error = session.last_error
        session.last_error = None
        run_id = str(uuid4())
        active_span = get_current_span()
        if active_span.is_recording():
            active_span.set_attribute("raven.run.id", run_id)
        created_at = datetime.now(timezone.utc).isoformat()
        session.current_run_id = run_id
        session.run_started_at = created_at
        session.current_tools = []
        session.current_activity = None
        session.recent_activity = []
        observation: dict[str, Any] = {}
        action_name: str | None = None
        action_arguments: dict[str, Any] | None = None
        output_text: str | None = None
        error_text: str | None = None
        prepared: PreparedTurn | None = None
        model_result: ModelRunResult | None = None
        status = "running"
        started_at = monotonic()
        harness = self.harness

        def record_activity(kind: str, payload: dict[str, Any]) -> None:
            if session.current_run_id != run_id:
                return
            sanitized = _sanitize_model_activity(kind, payload)
            if sanitized is None:
                return
            occurred_at = datetime.now(timezone.utc).isoformat()
            event_payload = {
                "runId": run_id,
                "occurredAt": occurred_at,
                **sanitized,
            }
            self.store.add_event(agent_id, kind, event_payload)
            if active_span.is_recording():
                active_span.add_event(
                    f"raven.{kind}",
                    _telemetry_activity_attributes(run_id, kind, sanitized),
                )
            activity = {"kind": kind, **event_payload}
            session.current_activity = activity
            session.recent_activity = [*session.recent_activity, activity][-8:]

        try:
            if self.durable_game_path is not None:
                await session.client.sync_snapshot()
                if session.client.snapshot is None:
                    raise RuntimeError(
                        "Game checkpoint sync returned without a player snapshot"
                    )
            game_context = build_context(
                session.client.snapshot,
                record.user_id,
                list(session.client.recent_events),
            )
            if game_context.ingame is not None and not is_waiting_for_player(
                game_context
            ):
                raise RuntimeError(
                    "This player is not responsible for the current decision"
                )
            checkpoint = self.store.get_agent_checkpoint(agent_id)
            current_state_id = str(
                game_context.snapshot.get("leafStateId") or "unknown"
            )
            if (
                checkpoint is not None
                and checkpoint["phase"] == "before-model"
                and checkpoint["stateId"] == current_state_id
            ):
                checkpoint_error = checkpoint["observation"].get(
                    "previousAttemptError"
                )
                if isinstance(checkpoint_error, str) and checkpoint_error:
                    previous_error = checkpoint_error
            prepared = harness.prepare_turn(record, game_context, previous_error)
            observation = prepared.observation
            session.observation = observation
            tools = prepared.tools
            session.current_tools = [tool.name for tool in tools]
            if not prepared.game_tool_names:
                raise RuntimeError(
                    "No model tool is implemented for the current game state"
                )
            if self.durable_game_path is not None:
                await _wait_for_durable_game_state(
                    self.durable_game_path,
                    str(observation["game"].get("stateId") or "unknown"),
                )
            record_activity(
                "model-run-started",
                {
                    "model": record.model,
                    "phase": observation["game"]["phase"],
                    "tools": [tool.name for tool in tools],
                },
            )

            run_context = HarnessRunContext(
                client=session.client,
                user_id=record.user_id,
                game_password=record.game_password.get_secret_value(),
                activity_sink=record_activity,
            )
            model_result = await harness.run_turn(
                record,
                prepared,
                context=run_context,
                run_id=run_id,
            )
            output_text = model_result.output_text
            if run_context.action_taken is None:
                raise RuntimeError(
                    "The model run finished without taking a game action"
                    + (f": {output_text}" if output_text else "")
                )

            action_name = run_context.action_taken.name
            action_arguments = run_context.action_taken.arguments
            if prepared.history_id is not None:
                self.store.record_history_action(
                    prepared.history_id, action_name, action_arguments
                )
            session.failure_leaf_id = None
            session.consecutive_failures = 0
            status = "completed"
            record_activity("model-run-completed", {"tool": action_name})
            result = {
                "runId": run_id,
                "decision": {
                    "responseId": model_result.response_id,
                    "name": action_name,
                    "arguments": action_arguments,
                    "outputText": output_text,
                    "usage": model_result.usage,
                },
                "result": {
                    "sentMessageTypes": [
                        message["type"] for message in run_context.action_taken.messages
                    ]
                },
            }
            self.store.add_event(
                agent_id,
                "model-action",
                {
                    "runId": run_id,
                    "model": record.model,
                    "responseId": model_result.response_id,
                    "tool": action_name,
                    "arguments": action_arguments,
                    "sentMessageTypes": result["result"]["sentMessageTypes"],
                    "usage": model_result.usage,
                    "rawUsage": model_result.raw_usage,
                },
            )
            return result
        except asyncio.CancelledError as error:
            status = "cancelled"
            error_text = "Model run cancelled"
            if isinstance(error, ModelRunCancelled):
                model_result = error.partial_result
            record_activity("model-run-cancelled", {})
            raise
        except Exception as error:
            status = "failed"
            error_text = safe_error_text(error)
            if isinstance(error, ModelRunError):
                model_result = error.partial_result
                if error_text != str(error):
                    error = type(error)(error_text, error.partial_result)
            session.last_error = error_text
            record_activity("model-run-failed", {})
            if isinstance(error, RuntimeError):
                if str(error) == error_text:
                    raise error from None
                raise RuntimeError(error_text) from None
            raise RuntimeError(error_text) from None
        finally:
            finished_at = datetime.now(timezone.utc).isoformat()
            self.store.add_run(
                run_id=run_id,
                agent_id=agent_id,
                status=status,
                observation=observation or session.observation or {},
                context_manifest=model_result.context_manifest
                if model_result
                else None,
                tool_name=action_name,
                tool_arguments=action_arguments,
                model_output=output_text,
                model=record.model,
                instructions=prepared.instructions
                if prepared
                else record.system_prompt,
                tools=describe_tools(prepared.tools) if prepared else None,
                response_id=model_result.response_id if model_result else None,
                response=model_result.response_items if model_result else None,
                usage=model_result.usage if model_result else None,
                raw_usage=model_result.raw_usage if model_result else None,
                error=error_text,
                created_at=created_at,
                finished_at=finished_at,
                duration_ms=int((monotonic() - started_at) * 1_000),
                history_id=prepared.history_id if prepared else None,
            )
            session.running = False
            session.status = (
                "reconnecting"
                if session.reconnect_task is not None
                and not session.reconnect_task.done()
                else session.client.status
            )
            session.current_run_id = None
            session.run_started_at = None
            session.current_tools = []
            session.current_activity = None

    def set_autoplay(self, agent_id: str, enabled: bool) -> AgentPublic:
        session = self.sessions.get(agent_id)
        if session is None or (enabled and not session.has_connected):
            raise RuntimeError("Agent must be connected before autoplay can be changed")
        if enabled and not session.autoplay:
            session.failure_leaf_id = None
            session.consecutive_failures = 0
        session.autoplay = enabled
        self.store.add_event(agent_id, "autoplay-changed", {"enabled": enabled})
        if enabled:
            self._schedule_autoplay(agent_id, session)
        return self._require_public_agent(agent_id)

    def get_observation(self, agent_id: str) -> dict[str, Any] | None:
        session = self.sessions.get(agent_id)
        if session is None:
            raise RuntimeError("Agent is not started")
        return session.observation

    def get_tools(self, agent_id: str) -> list[dict[str, Any]]:
        record = self.store.get_agent(agent_id)
        session = self.sessions.get(agent_id)
        if record is None or session is None or session.client.snapshot is None:
            return []
        context = build_context(
            session.client.snapshot,
            record.user_id,
            list(session.client.recent_events),
        )
        return describe_tools(self.harness.preview_tools(context))

    def list_monitoring(self) -> list[dict[str, Any]]:
        """Return one compact dashboard record for every configured agent."""

        records = []
        for agent_record in self.store.list_agents():
            session = self.sessions.get(agent_record.id)
            runtime = self.get_runtime(agent_record.id)
            agent = AgentPublic.from_record(agent_record, runtime)
            observation = session.observation if session else None
            snapshot = session.client.snapshot if session else None
            live = bool(
                observation is not None
                and session is not None
                and session.status in {"connected", "running"}
            )
            state_status: dict[str, Any] = {
                "source": "live" if live else None,
                "capturedAt": None,
            }
            if not live:
                stored = self.store.get_latest_snapshot(agent_record.id)
                if stored is not None:
                    snapshot = stored["snapshot"]
                    context = build_context(snapshot, agent_record.user_id)
                    observation = self.harness.preview_observation(
                        agent_record, context
                    )
                    state_status = {
                        "source": "saved",
                        "capturedAt": stored["createdAt"],
                    }
            state_status["actionable"] = bool(
                live and observation and observation.get("isYourTurn")
            )
            records.append(
                {
                    "agent": agent.model_dump(by_alias=True),
                    "state": _monitoring_state(observation, snapshot),
                    "stateStatus": state_status,
                    "metrics": self.store.get_run_metrics(agent.id),
                    "recentRuns": self.store.list_runs(agent.id, limit=6),
                }
            )
        return records

    async def configure_lobby(
        self, agent_id: str, setup: LobbySetupRequest
    ) -> dict[str, Any]:
        """Configure a lobby through an authenticated owner agent."""

        record, session = self._require_connected_session(agent_id)
        snapshot = session.client.snapshot
        assert snapshot is not None
        lobby = snapshot.get("childGameState", {})
        if lobby.get("type") != "lobby":
            raise RuntimeError("The game is no longer in its lobby")
        if str(snapshot.get("ownerUserId")) != record.user_id:
            raise RuntimeError("Only the game owner can configure the lobby")

        settings = {
            "setupId": setup.setup_id,
            "playerCount": setup.player_count,
            "pbem": setup.pbem,
            "vassals": setup.vassals,
            "victoryPointsCountNeededToWin": setup.victory_points_to_win,
        }
        await session.client.send(
            {"type": "change-game-settings", "settings": settings}
        )
        snapshot = await session.client.sync_snapshot()
        current_settings = snapshot.get("gameSettings", {})
        normalized_settings = (
            {
                "vassals": False,
                "victoryPointsCountNeededToWin": 7,
                **current_settings,
            }
            if isinstance(current_settings, dict)
            else {}
        )
        if (
            not isinstance(current_settings, dict)
            or any(
                type(normalized_settings.get(key)) is not type(expected)
                or normalized_settings.get(key) != expected
                for key, expected in settings.items()
            )
        ):
            raise RuntimeError("The game server did not accept the lobby settings")
        self.store.add_event(agent_id, "lobby-configured", settings)
        return settings

    async def choose_lobby_house(self, agent_id: str, house_id: str) -> None:
        """Seat an agent deterministically without exposing control to its model."""

        record, session = self._require_connected_session(agent_id)
        snapshot = session.client.snapshot
        assert snapshot is not None
        lobby = snapshot.get("childGameState", {})
        if lobby.get("type") != "lobby":
            raise RuntimeError("The game is no longer in its lobby")
        available = set(lobby.get("availableHouseIds", []))
        known = {house.get("id") for house in lobby.get("lobbyHouses", [])}
        if house_id not in known or house_id not in available:
            raise RuntimeError(f"House {house_id!r} is not available in this lobby")
        occupied = {
            selected_house: str(user_id)
            for selected_house, user_id in lobby.get("players", [])
        }
        occupant = occupied.get(house_id)
        if occupant is not None and occupant != record.user_id:
            raise RuntimeError(f"House {house_id!r} is already occupied")

        await session.client.send(
            {
                "type": "choose-house",
                "house": house_id,
                "password": record.game_password.get_secret_value(),
            }
        )
        snapshot = await session.client.sync_snapshot()
        seated = any(
            selected_house == house_id and str(user_id) == record.user_id
            for selected_house, user_id in snapshot.get("childGameState", {}).get(
                "players", []
            )
        )
        if not seated:
            raise RuntimeError("The game server did not accept the house selection")
        self.store.add_event(agent_id, "lobby-house-selected", {"houseId": house_id})

    async def launch_game(self, agent_id: str) -> dict[str, bool]:
        """Launch the lobby and verify the server's resulting state."""

        record, session = self._require_connected_session(agent_id)
        snapshot = session.client.snapshot
        assert snapshot is not None
        if snapshot.get("childGameState", {}).get("type") != "lobby":
            raise RuntimeError("The game is no longer in its lobby")
        if str(snapshot.get("ownerUserId")) != record.user_id:
            raise RuntimeError("Only the game owner can launch the game")
        await session.client.send({"type": "launch-game"})
        snapshot = await session.client.sync_snapshot()
        child_state = snapshot.get("childGameState", {})
        started = child_state.get("type") == "ingame"
        ready_check = (
            child_state.get("type") == "lobby"
            and isinstance(child_state.get("readyUsers"), list)
        )
        if not started and not ready_check:
            raise RuntimeError("The game server did not accept the launch request")
        result = {"started": started, "readyCheck": ready_check}
        self.store.add_event(agent_id, "lobby-launch-accepted", result)
        return result

    async def stop_all(self) -> None:
        for agent_id in list(self.sessions):
            await self.stop(agent_id)
        await self.harness.shutdown()

    def _schedule_autoplay(self, agent_id: str, session: AgentSession) -> None:
        if not session.autoplay or session.client.snapshot is None:
            return
        if session.autoplay_task is None or session.autoplay_task.done():
            session.autoplay_task = asyncio.create_task(
                self._autoplay_loop(agent_id, session)
            )

    def _schedule_reconnect(self, agent_id: str, session: AgentSession) -> None:
        if (
            not session.has_connected
            or self.sessions.get(agent_id) is not session
            or session.client.status in {"banned", "stopped"}
        ):
            return
        if session.reconnect_task is None or session.reconnect_task.done():
            session.status = "reconnecting"
            session.reconnect_task = asyncio.create_task(
                self._reconnect_loop(agent_id, session)
            )

    async def _reconnect_loop(
        self, agent_id: str, expected_session: AgentSession
    ) -> None:
        reconnect_task = asyncio.current_task()
        delay = 0.0
        try:
            while self.sessions.get(agent_id) is expected_session:
                if delay:
                    await asyncio.sleep(delay)
                if self.sessions.get(agent_id) is not expected_session:
                    return
                expected_session.status = "reconnecting"
                try:
                    await expected_session.client.connect()
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    if expected_session.client.status == "banned":
                        expected_session.status = "banned"
                        return
                    message = safe_error_text(error)
                    expected_session.last_error = message
                    expected_session.status = "reconnecting"
                    self.store.add_event(
                        agent_id,
                        "connection-retry-failed",
                        {"message": message},
                    )
                    delay = _next_reconnect_delay(
                        delay,
                        self.reconnect_retry_base_seconds,
                        self.reconnect_retry_max_seconds,
                    )
                    continue
                expected_session.last_error = None
                expected_session.connected_at = datetime.now(timezone.utc).isoformat()
                expected_session.status = (
                    "running" if expected_session.running else "connected"
                )
                return
        finally:
            if expected_session.reconnect_task is reconnect_task:
                expected_session.reconnect_task = None

    def _schedule_lobby_ready(
        self, agent_id: str, session: AgentSession, record: AgentRecord
    ) -> None:
        snapshot = session.client.snapshot or {}
        lobby = snapshot.get("childGameState", {})
        ready_users = lobby.get("readyUsers")
        seated = any(
            str(user_id) == record.user_id for _, user_id in lobby.get("players", [])
        )
        if (
            lobby.get("type") != "lobby"
            or not isinstance(ready_users, list)
            or record.user_id in {str(user_id) for user_id in ready_users}
            or not seated
        ):
            return
        if session.ready_task is None or session.ready_task.done():
            session.ready_task = asyncio.create_task(
                self._confirm_lobby_ready(agent_id, session, record.user_id)
            )

    async def _confirm_lobby_ready(
        self,
        agent_id: str,
        expected_session: AgentSession,
        user_id: str,
    ) -> None:
        try:
            await expected_session.client.send({"type": "ready"})
            snapshot = await expected_session.client.sync_snapshot()
            child_state = snapshot.get("childGameState", {})
            started = child_state.get("type") == "ingame"
            ready_users = child_state.get("readyUsers")
            confirmed = (
                child_state.get("type") == "lobby"
                and isinstance(ready_users, list)
                and user_id in {str(ready_user_id) for ready_user_id in ready_users}
            )
            if not started and not confirmed:
                raise RuntimeError("The game server did not accept the ready response")
            self.store.add_event(
                agent_id,
                "lobby-ready-accepted",
                {"startedGame": started},
            )
        except Exception as error:
            message = safe_error_text(error)
            expected_session.last_error = message
            self.store.add_event(
                agent_id, "lobby-ready-failed", {"message": message}
            )

    async def _autoplay_loop(
        self, agent_id: str, expected_session: AgentSession
    ) -> None:
        while (
            self.sessions.get(agent_id) is expected_session
            and expected_session.autoplay
        ):
            await asyncio.sleep(0.75)
            if expected_session.running or (
                expected_session.status != "connected"
                or expected_session.client.snapshot is None
            ):
                continue
            record = self.store.get_agent(agent_id)
            if record is None:
                return
            context = build_context(
                expected_session.client.snapshot,
                record.user_id,
                list(expected_session.client.recent_events),
            )
            if context.ingame is None or not is_waiting_for_player(context):
                continue
            try:
                await self.run_once(agent_id)
            except GameConnectionLost:
                expected_session.last_error = None
                continue
            except Exception:
                # Retry a bad model/tool call within the same decision, then leave
                # a stable failure visible in the dashboard for inspection.
                snapshot = expected_session.client.snapshot
                if snapshot is None:
                    continue
                current_leaf_id = snapshot.get("leafStateId")
                if expected_session.failure_leaf_id == current_leaf_id:
                    expected_session.consecutive_failures += 1
                else:
                    expected_session.failure_leaf_id = current_leaf_id
                    expected_session.consecutive_failures = 1
                expected_session.autoplay = (
                    expected_session.consecutive_failures
                    < self.autoplay_max_consecutive_failures
                )
                if expected_session.autoplay:
                    delay = min(
                        30,
                        self.autoplay_retry_base_seconds
                        * 2 ** (expected_session.consecutive_failures - 1),
                    )
                    await asyncio.sleep(delay)

    def _disable_all_autoplay(self, message: str) -> None:
        for agent_id, session in self.sessions.items():
            if not session.autoplay:
                continue
            session.autoplay = False
            session.last_error = message
            self.store.add_event(
                agent_id,
                "autoplay-stopped",
                {"reason": "permanent-provider-error", "message": message},
            )

    def _require_agent(self, agent_id: str) -> AgentRecord:
        record = self.store.get_agent(agent_id)
        if record is None:
            raise KeyError("Agent not found")
        return record

    def _require_public_agent(self, agent_id: str) -> AgentPublic:
        agent = self.get_agent(agent_id)
        if agent is None:
            raise KeyError("Agent not found")
        return agent

    def _require_connected_session(
        self, agent_id: str
    ) -> tuple[AgentRecord, AgentSession]:
        record = self._require_agent(agent_id)
        session = self.sessions.get(agent_id)
        if (
            session is None
            or session.client.snapshot is None
            or session.status not in {"connected", "running"}
        ):
            raise RuntimeError("Agent must be connected")
        return record, session


def _summarize_message(message: dict[str, Any]) -> dict[str, Any]:
    summary = {"type": message.get("type", "unknown")}
    if message.get("newLeafId") is not None:
        summary["newLeafId"] = message["newLeafId"]
    state = message.get("serializedGameState")
    if isinstance(state, dict) and state.get("type"):
        summary["state"] = state["type"]
    for key in ("houseId", "userId", "region", "regionId", "order", "value"):
        if key in message:
            summary[key] = message[key]
    return summary


def _sanitize_model_activity(
    kind: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    """Allow only bounded lifecycle metadata into the monitoring event stream."""

    if kind == "model-run-started":
        return {
            "model": str(payload.get("model", ""))[:160],
            "phase": str(payload.get("phase", ""))[:80],
            "tools": [str(name)[:120] for name in payload.get("tools", [])[:64]],
        }
    if kind == "model-run-completed":
        return {"tool": str(payload.get("tool", "unknown"))[:120]}
    if kind in {"model-run-failed", "model-run-cancelled"}:
        return {}
    if kind == "model-request-started":
        return {
            "requestIndex": _nonnegative_int(payload.get("requestIndex")),
            "inputItemCount": _nonnegative_int(payload.get("inputItemCount")),
        }
    if kind == "model-request-completed":
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            usage = {}
        return {
            "requestIndex": _nonnegative_int(payload.get("requestIndex")),
            "responseId": str(payload["responseId"])[:200]
            if payload.get("responseId") is not None
            else None,
            "outputItemCount": _nonnegative_int(payload.get("outputItemCount")),
            "usage": {
                key: _nonnegative_int(usage.get(key))
                for key in (
                    "requests",
                    "inputTokens",
                    "outputTokens",
                    "totalTokens",
                )
            },
            "durationMs": _optional_nonnegative_int(payload.get("durationMs")),
        }
    if kind in {"model-tool-started", "model-tool-completed"}:
        sanitized: dict[str, Any] = {
            "tool": str(payload.get("tool", "unknown"))[:120],
            "sequence": _nonnegative_int(payload.get("sequence")),
        }
        if kind == "model-tool-completed":
            sanitized["durationMs"] = _optional_nonnegative_int(
                payload.get("durationMs")
            )
        return sanitized
    return None


def _nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def _optional_nonnegative_int(value: Any) -> int | None:
    if value is None:
        return None
    return _nonnegative_int(value)


def _telemetry_activity_attributes(
    run_id: str, kind: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Flatten sanitized activity fields into OpenTelemetry event attributes."""

    attributes: dict[str, Any] = {
        "raven.run.id": run_id,
        "raven.activity.kind": kind,
    }
    mappings = {
        "model": "raven.model",
        "phase": "raven.phase",
        "tool": "raven.tool",
        "responseId": "gen_ai.response.id",
        "requestIndex": "gen_ai.request.index",
        "sequence": "raven.tool.sequence",
        "inputItemCount": "gen_ai.request.input_items",
        "outputItemCount": "gen_ai.response.output_items",
        "durationMs": "raven.duration.ms",
    }
    for source, target in mappings.items():
        value = payload.get(source)
        if isinstance(value, (str, int, float, bool)):
            attributes[target] = value
    tools = payload.get("tools")
    if isinstance(tools, list) and all(isinstance(value, str) for value in tools):
        attributes["raven.tools"] = tuple(tools)
    usage = payload.get("usage")
    if isinstance(usage, dict):
        for source, target in (
            ("requests", "gen_ai.usage.requests"),
            ("inputTokens", "gen_ai.usage.input_tokens"),
            ("outputTokens", "gen_ai.usage.output_tokens"),
            ("totalTokens", "gen_ai.usage.total_tokens"),
        ):
            value = usage.get(source)
            if isinstance(value, int) and not isinstance(value, bool):
                attributes[target] = max(0, value)
    return attributes


def _next_reconnect_delay(current: float, base: float, maximum: float) -> float:
    """Advance capped reconnect backoff without an unbounded exponent."""

    return min(maximum, base if current <= 0 else current * 2)


async def _wait_for_durable_game_state(
    path: Path,
    state_id: str,
    *,
    timeout: float = 10,
    poll_seconds: float = 0.02,
) -> None:
    """Fence a model call behind the matching atomic game-server save."""

    deadline = monotonic() + timeout
    last_problem = "the save does not exist"
    while monotonic() < deadline:
        try:
            saved = json.loads(path.read_text())
        except FileNotFoundError:
            last_problem = "the save does not exist"
        except (OSError, json.JSONDecodeError) as error:
            last_problem = safe_error_text(error)
        else:
            if not isinstance(saved, dict):
                last_problem = "the save is not a JSON object"
            elif "harnessRandomState" not in saved:
                last_problem = "the save has no random-stream checkpoint"
            elif str(saved.get("leafStateId") or "unknown") != state_id:
                last_problem = (
                    f"saved state {saved.get('leafStateId')!r} does not match "
                    f"agent state {state_id!r}"
                )
            else:
                return
        await asyncio.sleep(poll_seconds)
    raise RuntimeError(
        f"Game state was not durably saved before the model call: {last_problem}"
    )


def _monitoring_state(
    observation: dict[str, Any] | None,
    snapshot: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if observation is None:
        return None
    you = observation.get("you", {})
    house_id = you.get("houseId")
    own_units = [
        {"regionId": region.get("id"), **unit}
        for region in observation.get("board", [])
        for unit in region.get("units", [])
        if unit.get("allegiance") == house_id
    ]
    map_by_id = {
        region.get("id"): region for region in observation.get("map", {}).get("regions", [])
    }
    controlled_regions = [
        {
            "id": region_id,
            "name": map_by_id.get(region_id, {}).get("name", region_id),
            "type": map_by_id.get(region_id, {}).get("type"),
            "castleLevel": map_by_id.get(region_id, {}).get("castleLevel", 0),
        }
        for region_id in you.get("controlledRegions", [])
    ]
    board = [
        {
            "id": region.get("id"),
            "name": map_by_id.get(region.get("id"), {}).get(
                "name", region.get("id")
            ),
            "type": map_by_id.get(region.get("id"), {}).get("type"),
            "castleLevel": map_by_id.get(region.get("id"), {}).get(
                "castleLevel", 0
            ),
            "supplyIcons": map_by_id.get(region.get("id"), {}).get(
                "supplyIcons", 0
            ),
            "crownIcons": map_by_id.get(region.get("id"), {}).get("crownIcons", 0),
            "controlPowerToken": region.get("controlPowerToken"),
            "garrison": region.get("garrison", 0),
            "units": region.get("units", []),
            "revealedOrder": region.get("revealedOrder"),
        }
        for region in observation.get("board", [])
    ]
    action_guidance = observation.get("actionGuidance")
    if action_guidance is None and observation.get("planningConstraints") is not None:
        action_guidance = {
            "decision": "planning",
            **observation["planningConstraints"],
        }
    return {
        "game": observation.get("game", {}),
        "isOwner": bool(
            snapshot
            and str(snapshot.get("ownerUserId")) == str(you.get("userId"))
        ),
        "isYourTurn": observation.get("isYourTurn", False),
        "pendingDecision": observation.get("pendingDecision"),
        "statePath": observation.get("statePath", []),
        "player": {**you, "units": own_units, "controlledRegionDetails": controlled_regions},
        "standings": observation.get("houses", []),
        "houseCardStatus": observation.get("houseCardStatus", []),
        "board": board,
        "revealedOrders": observation.get("revealedOrders", []),
        "actionGuidance": action_guidance,
        "tracks": observation.get("tracks", {}),
        "recentEvents": observation.get("recentEvents", [])[-6:],
    }
