import hashlib
import json
import math
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

    def list_events(
        self,
        agent_id: str,
        limit: int = 80,
        *,
        kinds: set[str] | None = None,
    ) -> list[AgentEvent]:
        if kinds is not None and not kinds:
            return []
        kind_filter = ""
        parameters: list[Any] = [agent_id]
        if kinds is not None:
            placeholders = ",".join("?" for _kind in kinds)
            kind_filter = f" AND kind IN ({placeholders})"
            parameters.extend(sorted(kinds))
        parameters.append(limit)
        with self.database.lock:
            rows = self.database.connection.execute(
                f"""
                SELECT id, kind, payload_json, created_at
                FROM agent_events
                WHERE agent_id = ?{kind_filter}
                ORDER BY id DESC LIMIT ?
                """,
                parameters,
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

    def record_snapshot(self, agent_id: str, snapshot: dict[str, Any]) -> int | None:
        """Append a player-scoped snapshot unless its state and content already exist."""

        serialized = json.dumps(
            snapshot,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        content_sha256 = hashlib.sha256(serialized.encode()).hexdigest()
        leaf_state_id = str(snapshot.get("leafStateId") or "unknown")
        created_at = datetime.now(timezone.utc).isoformat()
        with self.database.lock, self.database.connection:
            cursor = self.database.connection.execute(
                """
                INSERT OR IGNORE INTO player_snapshots (
                  agent_id, leaf_state_id, content_sha256, snapshot_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    leaf_state_id,
                    content_sha256,
                    serialized,
                    created_at,
                ),
            )
        return int(cursor.lastrowid) if cursor.rowcount else None

    def list_snapshots(
        self, agent_id: str, limit: int = 80
    ) -> list[dict[str, Any]]:
        """Return newest snapshot metadata."""

        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        with self.database.lock:
            rows = self.database.connection.execute(
                """
                SELECT id, leaf_state_id, content_sha256, created_at
                FROM player_snapshots
                WHERE agent_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (agent_id, limit),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "leafStateId": row["leaf_state_id"],
                "contentSha256": row["content_sha256"],
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

    def get_snapshot(
        self, agent_id: str, snapshot_id: int
    ) -> dict[str, Any] | None:
        """Return one complete player snapshot."""

        with self.database.lock:
            row = self.database.connection.execute(
                """
                SELECT id, leaf_state_id, content_sha256, snapshot_json, created_at
                FROM player_snapshots
                WHERE agent_id = ? AND id = ?
                """,
                (agent_id, snapshot_id),
            ).fetchone()
        if row is None:
            return None
        return self._snapshot_row(row)

    def get_latest_snapshot(self, agent_id: str) -> dict[str, Any] | None:
        """Return the newest complete player snapshot for one agent."""

        with self.database.lock:
            row = self.database.connection.execute(
                """
                SELECT id, leaf_state_id, content_sha256, snapshot_json, created_at
                FROM player_snapshots
                WHERE agent_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (agent_id,),
            ).fetchone()
        if row is None:
            return None
        return self._snapshot_row(row)

    @staticmethod
    def _snapshot_row(row: Any) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "leafStateId": row["leaf_state_id"],
            "contentSha256": row["content_sha256"],
            "snapshot": json.loads(row["snapshot_json"]),
            "createdAt": row["created_at"],
        }

    def add_run(
        self,
        *,
        run_id: str,
        agent_id: str,
        status: str,
        observation: dict[str, Any],
        context_manifest: dict[str, Any] | None = None,
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
                  id, agent_id, status, model, observation_json, context_json,
                  instructions, tools_json, tool_name, tool_arguments_json,
                  model_output, response_id, response_json, usage_json,
                  raw_usage_json, error, created_at, finished_at, duration_ms,
                  history_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    agent_id,
                    status,
                    model,
                    json.dumps(observation),
                    json.dumps(context_manifest)
                    if context_manifest is not None
                    else None,
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
        if row is None:
            return None
        result = self._history_row(row)
        result["observation"] = json.loads(row["observation_json"])
        return result

    def list_state_history(
        self, agent_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        with self.database.lock:
            rows = self.database.connection.execute(
                """
                SELECT id, state_id, round_number, phase, action_name,
                       action_arguments_json, created_at
                FROM game_state_history
                WHERE agent_id = ? ORDER BY id DESC LIMIT ?
                """,
                (agent_id, limit),
            ).fetchall()
        return [self._history_row(row) for row in rows]

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
                "modelPlan": "",
                "objectives": [],
                "opponentModels": [],
                "commitments": [],
                "lessons": [],
                "decisionJournal": [],
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
                       context_json, instructions, tools_json, tool_name,
                       tool_arguments_json,
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
            "contextManifest": self._load_optional_json(row["context_json"]),
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
            request_events = self.database.connection.execute(
                """
                SELECT payload_json FROM agent_events
                WHERE agent_id = ? AND kind = 'model-request-started'
                ORDER BY id ASC
                """,
                (agent_id,),
            ).fetchall()

        statuses: dict[str, int] = {}
        responses = input_tokens = output_tokens = total_tokens = 0
        cached_tokens = cache_write_tokens = reasoning_tokens = 0
        charged_cost = upstream_inference_cost = 0.0
        usage_records = charged_cost_records = upstream_cost_records = 0
        response_provider_counts: dict[str, int] = {}
        response_model_counts: dict[str, int] = {}
        durations: list[int] = []
        max_input_tokens_in_run = 0
        request_input_tokens: list[int] = []
        rules_oracle_request_input_tokens: list[int] = []
        for row in rows:
            status = str(row["status"])
            statuses[status] = statuses.get(status, 0) + 1
            usage = self._load_optional_json(row["usage_json"]) or {}
            responses += int(usage.get("requests") or 0)
            input_tokens += int(usage.get("inputTokens") or 0)
            output_tokens += int(usage.get("outputTokens") or 0)
            total_tokens += int(usage.get("totalTokens") or 0)
            max_input_tokens_in_run = max(
                max_input_tokens_in_run, int(usage.get("inputTokens") or 0)
            )
            for native in self._load_optional_json(row["raw_usage_json"]) or []:
                usage_records += 1
                details = native.get("input_tokens_details") or {}
                output_details = native.get("output_tokens_details") or {}
                cost_details = native.get("cost_details") or {}
                cached_tokens += int(details.get("cached_tokens") or 0)
                cache_write_tokens += int(details.get("cache_write_tokens") or 0)
                reasoning_tokens += int(output_details.get("reasoning_tokens") or 0)
                if isinstance(native.get("cost"), (int, float)):
                    charged_cost += float(native["cost"])
                    charged_cost_records += 1
                upstream_cost = cost_details.get("upstream_inference_cost")
                if isinstance(upstream_cost, (int, float)):
                    upstream_inference_cost += float(upstream_cost)
                    upstream_cost_records += 1
                response_provider = native.get("response_provider")
                if isinstance(response_provider, str) and response_provider:
                    response_provider_counts[response_provider] = (
                        response_provider_counts.get(response_provider, 0) + 1
                    )
                response_model = native.get("response_model")
                if isinstance(response_model, str) and response_model:
                    response_model_counts[response_model] = (
                        response_model_counts.get(response_model, 0) + 1
                    )
                if native.get("input_tokens") is not None:
                    destination = (
                        rules_oracle_request_input_tokens
                        if native.get("scope") == "rules-oracle"
                        else request_input_tokens
                    )
                    destination.append(int(native["input_tokens"]))
            if row["duration_ms"] is not None:
                durations.append(int(row["duration_ms"]))

        starts_by_scope: dict[str, int] = {}
        for event in request_events:
            payload = self._load_optional_json(event["payload_json"]) or {}
            scope = str(payload.get("scope") or "agent")
            starts_by_scope[scope] = starts_by_scope.get(scope, 0) + 1
        starts = sum(starts_by_scope.values())

        return {
            "runCount": len(rows),
            "statusCounts": statuses,
            "modelCalls": {
                "started": starts,
                "responses": responses,
                "withoutResponse": max(0, starts - responses),
                "responsesWithoutStart": max(0, responses - starts),
                "startedByScope": dict(sorted(starts_by_scope.items())),
            },
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens,
                "cachedInput": cached_tokens,
                "cacheWrite": cache_write_tokens,
                "reasoning": reasoning_tokens,
                "maxInputInRun": max_input_tokens_in_run,
            },
            "requestInputTokens": self._input_token_distribution(
                request_input_tokens
            ),
            "rulesOracleRequestInputTokens": self._input_token_distribution(
                rules_oracle_request_input_tokens
            ),
            "costUsd": charged_cost,
            "upstreamInferenceCostUsd": upstream_inference_cost,
            "costCoverage": {
                "responseUsageRecords": usage_records,
                "chargedCostRecords": charged_cost_records,
                "upstreamInferenceCostRecords": upstream_cost_records,
            },
            "responseAttribution": {
                "providers": dict(sorted(response_provider_counts.items())),
                "models": dict(sorted(response_model_counts.items())),
                "responsesWithoutProvider": max(
                    0, usage_records - sum(response_provider_counts.values())
                ),
            },
            "durationMs": {
                "total": sum(durations),
                "average": round(sum(durations) / len(durations)) if durations else 0,
                "p50": self._nearest_rank(durations, 0.5),
                "p90": self._nearest_rank(durations, 0.9),
                "p99": self._nearest_rank(durations, 0.99),
                "maximum": max(durations, default=0),
            },
            "historicalStates": int(history_count),
        }

    @staticmethod
    def _load_optional_json(value: str | None) -> Any:
        return json.loads(value) if value is not None else None

    @staticmethod
    def _nearest_rank(values: list[int], percentile: float) -> int:
        if not values:
            return 0
        ordered = sorted(values)
        return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]

    @classmethod
    def _input_token_distribution(cls, values: list[int]) -> dict[str, int]:
        return {
            "reportedRequests": len(values),
            "average": round(sum(values) / len(values)) if values else 0,
            "p50": cls._nearest_rank(values, 0.50),
            "p90": cls._nearest_rank(values, 0.90),
            "p99": cls._nearest_rank(values, 0.99),
            "maximum": max(values, default=0),
        }

    @classmethod
    def _history_row(cls, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "stateId": row["state_id"],
            "round": row["round_number"],
            "phase": row["phase"],
            "action": row["action_name"],
            "arguments": cls._load_optional_json(row["action_arguments_json"]),
            "createdAt": row["created_at"],
        }

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
