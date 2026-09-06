from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from opentelemetry.trace import Status, StatusCode

from .agent_store import AgentStore
from .game.client import ConnectionFactory, SwordsAndRavensClient
from .harness.actions import HarnessRunContext, describe_tools
from .harness.interface import PlayerHarness, PreparedTurn
from .harness.observation import build_context, is_waiting_for_player
from .models.openai_agent import ModelRunResult
from .schemas import AgentPublic, AgentRecord, AgentRuntime, LobbySetupRequest
from .telemetry import Telemetry, provider_cost


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
    ready_task: asyncio.Task[None] | None = None
    failure_leaf_id: str | None = None
    consecutive_failures: int = 0
    current_run_id: str | None = None
    run_started_at: str | None = None
    current_tools: list[str] | None = None


class AgentManager:
    def __init__(
        self,
        *,
        store: AgentStore,
        harness: PlayerHarness,
        connection_factory: ConnectionFactory | None = None,
        telemetry: Telemetry | None = None,
    ) -> None:
        self.store = store
        self.harness = harness
        self.connection_factory = connection_factory
        self.telemetry = telemetry or Telemetry.create(endpoint="")
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
            return AgentRuntime()
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
        )

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
                session.status = str(payload["status"])
                self.store.add_event(agent_id, "connection-status", payload)
            elif kind == "error":
                session.last_error = str(
                    payload.get("message", "Game connection failed")
                )
                self.store.add_event(agent_id, "connection-error", payload)
            elif kind == "sent":
                self.store.add_event(
                    agent_id, "game-message-sent", _summarize_message(payload)
                )
            elif kind == "game-message":
                self.store.add_event(
                    agent_id, "game-message-received", _summarize_message(payload)
                )
            elif kind == "snapshot" and session.client.snapshot is not None:
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
        session = AgentSession(status="connecting", client=client)
        self.sessions[agent_id] = session

        try:
            await client.connect()
            session.connected_at = datetime.now(timezone.utc).isoformat()
            session.status = "connected"
        except Exception as error:
            session.status = "error"
            session.last_error = str(error)
            self.store.add_event(agent_id, "connection-error", {"message": str(error)})
            if isinstance(error, RuntimeError):
                raise
            raise RuntimeError(str(error)) from error
        return self._require_public_agent(agent_id)

    async def stop(self, agent_id: str) -> AgentPublic | None:
        session = self.sessions.pop(agent_id, None)
        if session is not None:
            if (
                session.autoplay_task
                and session.autoplay_task is not asyncio.current_task()
            ):
                session.autoplay_task.cancel()
            if session.ready_task and session.ready_task is not asyncio.current_task():
                session.ready_task.cancel()
            await session.client.close()
            self.store.add_event(agent_id, "connection-status", {"status": "stopped"})
        return self.get_agent(agent_id)

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
                span.record_exception(error)
                span.set_status(Status(StatusCode.ERROR, str(error)))
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
        created_at = datetime.now(timezone.utc).isoformat()
        session.current_run_id = run_id
        session.run_started_at = created_at
        session.current_tools = []
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

        try:
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
            prepared = harness.prepare_turn(record, game_context, previous_error)
            observation = prepared.observation
            session.observation = observation
            tools = prepared.tools
            session.current_tools = [tool.name for tool in tools]
            if not prepared.metadata["gameToolNames"]:
                raise RuntimeError(
                    "No model tool is implemented for the current game state"
                )
            self.store.add_event(
                agent_id,
                "model-run-started",
                {
                    "runId": run_id,
                    "model": record.model,
                    "phase": observation["game"]["phase"],
                    "tools": [tool.name for tool in tools],
                },
            )

            run_context = HarnessRunContext(
                client=session.client,
                user_id=record.user_id,
                game_password=record.game_password.get_secret_value(),
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
        except asyncio.CancelledError:
            status = "cancelled"
            error_text = "Model run cancelled"
            self.store.add_event(
                agent_id,
                "model-run-cancelled",
                {"runId": run_id, "message": error_text},
            )
            raise
        except Exception as error:
            status = "failed"
            error_text = str(error)
            session.last_error = error_text
            self.store.add_event(
                agent_id,
                "model-run-failed",
                {"runId": run_id, "message": error_text},
            )
            if isinstance(error, RuntimeError):
                raise
            raise RuntimeError(error_text) from error
        finally:
            finished_at = datetime.now(timezone.utc).isoformat()
            self.store.add_run(
                run_id=run_id,
                agent_id=agent_id,
                status=status,
                observation=observation or session.observation or {},
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
            session.status = session.client.status
            session.current_run_id = None
            session.run_started_at = None
            session.current_tools = []

    def set_autoplay(self, agent_id: str, enabled: bool) -> AgentPublic:
        session = self.sessions.get(agent_id)
        if session is None or session.client.snapshot is None:
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
        return describe_tools(self.harness.preview_tools(record, context))

    def list_monitoring(self) -> list[dict[str, Any]]:
        """Return one compact dashboard record for every configured agent."""

        records = []
        for agent in self.list_agents():
            session = self.sessions.get(agent.id)
            observation = session.observation if session else None
            records.append(
                {
                    "agent": agent.model_dump(by_alias=True),
                    "state": _monitoring_state(
                        observation,
                        session.client.snapshot if session else None,
                    ),
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
        if current_settings.get("setupId") != setup.setup_id or int(
            current_settings.get("playerCount", 0)
        ) != setup.player_count:
            raise RuntimeError("The game server did not accept the lobby settings")
        self.store.add_event(agent_id, "lobby-configured", settings)
        return settings

    async def launch_game(self, agent_id: str) -> None:
        """Ask the upstream server to launch the configured lobby."""

        record, session = self._require_connected_session(agent_id)
        snapshot = session.client.snapshot
        assert snapshot is not None
        if snapshot.get("childGameState", {}).get("type") != "lobby":
            raise RuntimeError("The game is no longer in its lobby")
        if str(snapshot.get("ownerUserId")) != record.user_id:
            raise RuntimeError("Only the game owner can launch the game")
        await session.client.send({"type": "launch-game"})
        self.store.add_event(agent_id, "lobby-launch-requested", {})

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
                self._confirm_lobby_ready(agent_id, session)
            )

    async def _confirm_lobby_ready(
        self, agent_id: str, expected_session: AgentSession
    ) -> None:
        try:
            await expected_session.client.send({"type": "ready"})
            self.store.add_event(agent_id, "lobby-ready-confirmed", {})
        except Exception as error:
            expected_session.last_error = str(error)
            self.store.add_event(
                agent_id, "lobby-ready-failed", {"message": str(error)}
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
            except Exception:
                # Retry a bad model/tool call within the same decision, then leave
                # a stable failure visible in the dashboard for inspection.
                current_leaf_id = expected_session.client.snapshot.get("leafStateId")
                if expected_session.failure_leaf_id == current_leaf_id:
                    expected_session.consecutive_failures += 1
                else:
                    expected_session.failure_leaf_id = current_leaf_id
                    expected_session.consecutive_failures = 1
                expected_session.autoplay = expected_session.consecutive_failures < 3

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
        "tracks": observation.get("tracks", {}),
        "recentEvents": observation.get("recentEvents", [])[-6:],
    }
