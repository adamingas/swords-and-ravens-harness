import sqlite3
from pathlib import Path
from threading import RLock


SCHEMA_VERSION = 3

SCHEMA = """
CREATE TABLE agents (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  model TEXT NOT NULL,
  system_prompt TEXT NOT NULL,
  game_server_url TEXT NOT NULL,
  game_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  auth_token TEXT NOT NULL,
  game_password TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);

CREATE TABLE agent_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE agent_runs (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  status TEXT NOT NULL,
  model TEXT,
  observation_json TEXT NOT NULL,
  context_json TEXT,
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

CREATE TABLE game_state_history (
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

CREATE TABLE strategic_memories (
  agent_id TEXT PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
  memory_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);

CREATE TABLE player_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  leaf_state_id TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  snapshot_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(agent_id, leaf_state_id, content_sha256)
);

CREATE INDEX IF NOT EXISTS agent_events_agent_id_id
  ON agent_events(agent_id, id DESC);
CREATE INDEX IF NOT EXISTS agent_runs_agent_id_created_at
  ON agent_runs(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS game_state_history_agent_id_id
  ON game_state_history(agent_id, id DESC);
CREATE INDEX IF NOT EXISTS player_snapshots_agent_id_id
  ON player_snapshots(agent_id, id DESC);
"""


class Database:
    def __init__(self, filename: Path) -> None:
        self.filename = filename.resolve()
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.filename, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = RLock()
        with self.lock:
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA foreign_keys = ON")
            version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
            has_tables = self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' LIMIT 1"
            ).fetchone()
            if version == 0 and has_tables is None:
                self.connection.executescript(SCHEMA)
                self.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            elif version != SCHEMA_VERSION:
                self.connection.close()
                raise RuntimeError(
                    f"Database schema version {version} is not supported; "
                    f"expected {SCHEMA_VERSION}. Use a new DATABASE_PATH."
                )

    def close(self) -> None:
        with self.lock:
            self.connection.close()
