import json
from datetime import datetime, timezone
from typing import Any

from pydantic import SecretStr

from .database import Database
from .schemas import AgentCreate, AgentEvent, AgentRecord


class AgentStore:
    def __init__(self, database: Database) -> None:
        self.database = database

    def list_agents(self) -> list[AgentRecord]:
        with self.database.lock:
            rows = self.database.connection.execute(
                "SELECT * FROM agents ORDER BY created_at ASC"
            ).fetchall()
        return [self._record(row) for row in rows]

    def get_agent(self, agent_id: str) -> AgentRecord | None:
        with self.database.lock:
            row = self.database.connection.execute(
                "SELECT * FROM agents WHERE id = ?", (agent_id,)
            ).fetchone()
        return self._record(row) if row else None

    def create_agent(self, value: AgentCreate) -> AgentRecord:
        agent = AgentRecord.from_create(value)
        with self.database.lock, self.database.connection:
            self.database.connection.execute(
                """
                INSERT INTO agents (
                  id, name, model, system_prompt, game_server_url, game_id,
                  user_id, auth_token, game_password, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent.id,
                    agent.name,
                    agent.model,
                    agent.system_prompt,
                    agent.game_server_url,
                    agent.game_id,
                    agent.user_id,
                    agent.auth_token.get_secret_value(),
                    agent.game_password.get_secret_value(),
                    agent.created_at,
                ),
            )
        return agent

    def delete_agent(self, agent_id: str) -> bool:
        with self.database.lock, self.database.connection:
            cursor = self.database.connection.execute(
                "DELETE FROM agents WHERE id = ?", (agent_id,)
            )
        return cursor.rowcount > 0

    def add_event(self, agent_id: str, kind: str, payload: dict[str, Any]) -> None:
        with self.database.lock, self.database.connection:
            self.database.connection.execute(
                """
                INSERT INTO agent_events (agent_id, kind, payload_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    agent_id,
                    kind,
                    json.dumps(payload, separators=(",", ":")),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def list_events(self, agent_id: str, limit: int = 80) -> list[AgentEvent]:
        with self.database.lock:
            rows = self.database.connection.execute(
                """
                SELECT id, kind, payload_json, created_at
                FROM agent_events WHERE agent_id = ? ORDER BY id DESC LIMIT ?
                """,
                (agent_id, limit),
            ).fetchall()
        return [
            AgentEvent(
                id=row["id"],
                kind=row["kind"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def add_run(
        self,
        *,
        run_id: str,
        agent_id: str,
        status: str,
        observation: dict[str, Any],
        tool_name: str | None = None,
        tool_arguments: dict[str, Any] | None = None,
        model_output: str | None = None,
        model: str | None = None,
        instructions: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_id: str | None = None,
        response: list[dict[str, Any]] | None = None,
        usage: dict[str, Any] | None = None,
        raw_usage: list[dict[str, Any]] | None = None,
        error: str | None = None,
        created_at: str,
        finished_at: str | None = None,
        duration_ms: int | None = None,
        history_id: int | None = None,
    ) -> None:
        with self.database.lock, self.database.connection:
            self.database.connection.execute(
                """
                INSERT INTO agent_runs (
                  id, agent_id, status, model, observation_json,
                  instructions, tools_json, tool_name, tool_arguments_json,
                  model_output, response_id, response_json, usage_json,
                  raw_usage_json, error, created_at, finished_at, duration_ms,
                  history_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    agent_id,
                    status,
                    model,
                    json.dumps(observation),
                    instructions,
                    json.dumps(tools) if tools is not None else None,
                    tool_name,
                    json.dumps(tool_arguments) if tool_arguments is not None else None,
                    model_output,
                    response_id,
                    json.dumps(response) if response is not None else None,
                    json.dumps(usage) if usage is not None else None,
                    json.dumps(raw_usage) if raw_usage is not None else None,
                    error,
                    created_at,
                    finished_at,
                    duration_ms,
                    history_id,
                ),
            )

    def record_state(self, agent_id: str, observation: dict[str, Any]) -> int:
        game = observation.get("game", {})
        state_id = str(game.get("stateId") or "unknown")
        created_at = datetime.now(timezone.utc).isoformat()
        with self.database.lock, self.database.connection:
            self.database.connection.execute(
                """
                INSERT OR IGNORE INTO game_state_history (
                  agent_id, state_id, round_number, phase, observation_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    state_id,
                    game.get("round"),
                    str(game.get("phase") or "unknown"),
                    json.dumps(observation),
                    created_at,
                ),
            )
            row = self.database.connection.execute(
                """
                SELECT id FROM game_state_history
                WHERE agent_id = ? AND state_id = ?
                """,
                (agent_id, state_id),
            ).fetchone()
        assert row is not None
        return int(row["id"])

    def record_history_action(
        self, history_id: int, name: str, arguments: dict[str, Any]
    ) -> None:
        with self.database.lock, self.database.connection:
            self.database.connection.execute(
                """
                UPDATE game_state_history
                SET action_name = ?, action_arguments_json = ?
                WHERE id = ?
                """,
                (name, json.dumps(arguments), history_id),
            )

    def recall_state(self, agent_id: str, turns_ago: int) -> dict[str, Any] | None:
        with self.database.lock:
            row = self.database.connection.execute(
                """
                SELECT id, state_id, round_number, phase, observation_json,
                       action_name, action_arguments_json, created_at
                FROM game_state_history
                WHERE agent_id = ? ORDER BY id DESC LIMIT 1 OFFSET ?
                """,
                (agent_id, turns_ago),
            ).fetchone()
        return self._history_row(row, include_observation=True) if row else None

    def list_state_history(
        self, agent_id: str, limit: int = 20, *, include_observation: bool = False
    ) -> list[dict[str, Any]]:
        with self.database.lock:
            rows = self.database.connection.execute(
                """
                SELECT id, state_id, round_number, phase, observation_json,
                       action_name, action_arguments_json, created_at
                FROM game_state_history
                WHERE agent_id = ? ORDER BY id DESC LIMIT ?
                """,
                (agent_id, limit),
            ).fetchall()
        return [
            self._history_row(row, include_observation=include_observation)
            for row in rows
        ]

    def get_strategic_memory(self, agent_id: str) -> dict[str, Any]:
        with self.database.lock:
            row = self.database.connection.execute(
                """
                SELECT memory_json, revision, updated_at
                FROM strategic_memories WHERE agent_id = ?
                """,
                (agent_id,),
            ).fetchone()
        if row is None:
            return {
                "roundNumber": None,
                "situationAssessment": "",
                "objectives": [],
                "opponentModels": [],
                "commitments": [],
                "lessons": [],
                "revision": 0,
                "updatedAt": None,
            }
        return {
            **json.loads(row["memory_json"]),
            "revision": row["revision"],
            "updatedAt": row["updated_at"],
        }

    def set_strategic_memory(
        self, agent_id: str, memory: dict[str, Any]
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self.database.lock, self.database.connection:
            self.database.connection.execute(
                """
                INSERT INTO strategic_memories (
                  agent_id, memory_json, revision, updated_at
                ) VALUES (?, ?, 1, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                  memory_json = excluded.memory_json,
                  revision = strategic_memories.revision + 1,
                  updated_at = excluded.updated_at
                """,
                (agent_id, json.dumps(memory), now),
            )
        return self.get_strategic_memory(agent_id)

    def list_runs(self, agent_id: str, limit: int = 80) -> list[dict[str, Any]]:
        with self.database.lock:
            rows = self.database.connection.execute(
                """
                SELECT id, status, model, tool_name,
                       tool_arguments_json, response_id, usage_json,
                       raw_usage_json, error, created_at, finished_at, duration_ms
                FROM agent_runs WHERE agent_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (agent_id, limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "status": row["status"],
                "model": row["model"],
                "tool": row["tool_name"],
                "arguments": self._load_optional_json(row["tool_arguments_json"]),
                "responseId": row["response_id"],
                "usage": self._load_optional_json(row["usage_json"]),
                "rawUsage": self._load_optional_json(row["raw_usage_json"]),
                "error": row["error"],
                "createdAt": row["created_at"],
                "finishedAt": row["finished_at"],
                "durationMs": row["duration_ms"],
            }
            for row in rows
        ]

    def get_run(self, agent_id: str, run_id: str) -> dict[str, Any] | None:
        """Return the complete replayable trace for one model attempt."""

        with self.database.lock:
            row = self.database.connection.execute(
                """
                SELECT id, status, model, observation_json,
                       instructions, tools_json, tool_name, tool_arguments_json,
                       model_output, response_id, response_json, usage_json,
                       raw_usage_json, error, created_at, finished_at,
                       duration_ms, history_id
                FROM agent_runs WHERE agent_id = ? AND id = ?
                """,
                (agent_id, run_id),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "status": row["status"],
            "model": row["model"],
            "observation": json.loads(row["observation_json"]),
            "instructions": row["instructions"],
            "tools": self._load_optional_json(row["tools_json"]),
            "tool": row["tool_name"],
            "arguments": self._load_optional_json(row["tool_arguments_json"]),
            "modelOutput": row["model_output"],
            "responseId": row["response_id"],
            "response": self._load_optional_json(row["response_json"]),
            "usage": self._load_optional_json(row["usage_json"]),
            "rawUsage": self._load_optional_json(row["raw_usage_json"]),
            "error": row["error"],
            "createdAt": row["created_at"],
            "finishedAt": row["finished_at"],
            "durationMs": row["duration_ms"],
            "historyId": row["history_id"],
        }

    def get_run_metrics(self, agent_id: str) -> dict[str, Any]:
        """Aggregate local and provider-native usage for experiment comparison."""

        with self.database.lock:
            rows = self.database.connection.execute(
                """
                SELECT status, usage_json, raw_usage_json, duration_ms
                FROM agent_runs WHERE agent_id = ? ORDER BY created_at ASC
                """,
                (agent_id,),
            ).fetchall()
            history_count = self.database.connection.execute(
                "SELECT COUNT(*) FROM game_state_history WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()[0]

        statuses: dict[str, int] = {}
        requests = input_tokens = output_tokens = total_tokens = 0
        cached_tokens = cache_write_tokens = reasoning_tokens = 0
        cost = 0.0
        durations: list[int] = []
        max_input_tokens = 0
        for row in rows:
            status = str(row["status"])
            statuses[status] = statuses.get(status, 0) + 1
            usage = self._load_optional_json(row["usage_json"]) or {}
            requests += int(usage.get("requests") or 0)
            input_tokens += int(usage.get("inputTokens") or 0)
            output_tokens += int(usage.get("outputTokens") or 0)
            total_tokens += int(usage.get("totalTokens") or 0)
            max_input_tokens = max(max_input_tokens, int(usage.get("inputTokens") or 0))
            for native in self._load_optional_json(row["raw_usage_json"]) or []:
                details = native.get("input_tokens_details") or {}
                output_details = native.get("output_tokens_details") or {}
                cached_tokens += int(details.get("cached_tokens") or 0)
                cache_write_tokens += int(details.get("cache_write_tokens") or 0)
                reasoning_tokens += int(output_details.get("reasoning_tokens") or 0)
                cost += float(native.get("cost") or 0)
                max_input_tokens = max(
                    max_input_tokens, int(native.get("input_tokens") or 0)
                )
            if row["duration_ms"] is not None:
                durations.append(int(row["duration_ms"]))

        return {
            "runCount": len(rows),
            "statusCounts": statuses,
            "modelRequests": requests,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens,
                "cachedInput": cached_tokens,
                "cacheWrite": cache_write_tokens,
                "reasoning": reasoning_tokens,
                "maxInputInRun": max_input_tokens,
            },
            "costUsd": cost,
            "durationMs": {
                "total": sum(durations),
                "average": round(sum(durations) / len(durations)) if durations else 0,
                "maximum": max(durations, default=0),
            },
            "historicalStates": int(history_count),
        }

    @staticmethod
    def _load_optional_json(value: str | None) -> Any:
        return json.loads(value) if value is not None else None

    @classmethod
    def _history_row(cls, row: Any, *, include_observation: bool) -> dict[str, Any]:
        result = {
            "id": row["id"],
            "stateId": row["state_id"],
            "round": row["round_number"],
            "phase": row["phase"],
            "action": row["action_name"],
            "arguments": cls._load_optional_json(row["action_arguments_json"]),
            "createdAt": row["created_at"],
        }
        if include_observation:
            result["observation"] = json.loads(row["observation_json"])
        return result

    @staticmethod
    def _record(row: Any) -> AgentRecord:
        return AgentRecord(
            id=row["id"],
            name=row["name"],
            model=row["model"],
            system_prompt=row["system_prompt"],
            game_server_url=row["game_server_url"],
            game_id=row["game_id"],
            user_id=row["user_id"],
            auth_token=SecretStr(row["auth_token"]),
            game_password=SecretStr(row["game_password"]),
            created_at=row["created_at"],
        )
