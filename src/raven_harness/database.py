import sqlite3
from pathlib import Path
from threading import RLock


SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  model TEXT NOT NULL,
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
  observation_json TEXT NOT NULL,
  tool_name TEXT,
  tool_arguments_json TEXT,
  model_output TEXT,
  error TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS agent_events_agent_id_id
  ON agent_events(agent_id, id DESC);
CREATE INDEX IF NOT EXISTS agent_runs_agent_id_created_at
  ON agent_runs(agent_id, created_at DESC);
"""


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

    def close(self) -> None:
        with self.lock:
            self.connection.close()
