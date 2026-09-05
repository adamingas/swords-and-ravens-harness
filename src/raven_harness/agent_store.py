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
                  user_id, auth_token, game_password, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    agent.updated_at,
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
        error: str | None = None,
        created_at: str,
    ) -> None:
        with self.database.lock, self.database.connection:
            self.database.connection.execute(
                """
                INSERT INTO agent_runs (
                  id, agent_id, status, observation_json, tool_name,
                  tool_arguments_json, model_output, error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    agent_id,
                    status,
                    json.dumps(observation),
                    tool_name,
                    json.dumps(tool_arguments) if tool_arguments is not None else None,
                    model_output,
                    error,
                    created_at,
                ),
            )

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
            updated_at=row["updated_at"],
        )
