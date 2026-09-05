import sqlite3
from pathlib import Path
from threading import RLock


SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  model TEXT NOT NULL,
  harness_id TEXT NOT NULL DEFAULT 'legacy',
  system_prompt TEXT NOT NULL,
  game_server_url TEXT NOT NULL,
  game_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  auth_token TEXT NOT NULL,
  game_password TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  status TEXT NOT NULL,
  harness_id TEXT NOT NULL DEFAULT 'legacy',
  model TEXT,
  observation_json TEXT NOT NULL,
  instructions TEXT,
  tools_json TEXT,
  tool_name TEXT,
  tool_arguments_json TEXT,
  model_output TEXT,
  response_id TEXT,
  response_json TEXT,
  usage_json TEXT,
  raw_usage_json TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  duration_ms INTEGER,
  history_id INTEGER
);

CREATE TABLE IF NOT EXISTS game_state_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  state_id TEXT NOT NULL,
  round_number INTEGER,
  phase TEXT NOT NULL,
  observation_json TEXT NOT NULL,
  action_name TEXT,
  action_arguments_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(agent_id, state_id)
);

CREATE TABLE IF NOT EXISTS strategic_memories (
  agent_id TEXT PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
  memory_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS agent_events_agent_id_id
  ON agent_events(agent_id, id DESC);
CREATE INDEX IF NOT EXISTS agent_runs_agent_id_created_at
  ON agent_runs(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS game_state_history_agent_id_id
  ON game_state_history(agent_id, id DESC);
"""


AGENT_RUN_MIGRATIONS = {
    "harness_id": "TEXT NOT NULL DEFAULT 'legacy'",
    "model": "TEXT",
    "instructions": "TEXT",
    "tools_json": "TEXT",
    "response_id": "TEXT",
    "response_json": "TEXT",
    "usage_json": "TEXT",
    "raw_usage_json": "TEXT",
    "finished_at": "TEXT",
    "duration_ms": "INTEGER",
    "history_id": "INTEGER",
}


class Database:
    def __init__(self, filename: Path) -> None:
        filename.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(filename, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = RLock()
        with self.lock:
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.executescript(SCHEMA)
            self._ensure_column(
                "agents", "harness_id", "TEXT NOT NULL DEFAULT 'legacy'"
            )
            for name, declaration in AGENT_RUN_MIGRATIONS.items():
                self._ensure_column("agent_runs", name, declaration)

    def _ensure_column(self, table: str, name: str, declaration: str) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute(f"PRAGMA table_info({table})")
        }
        if name not in columns:
            self.connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {name} {declaration}"
            )

    def close(self) -> None:
        with self.lock:
            self.connection.close()
