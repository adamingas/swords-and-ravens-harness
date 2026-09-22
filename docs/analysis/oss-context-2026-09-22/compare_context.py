"""Measure old versus current context on the same recorded opening snapshot.

No provider requests. Token estimates use o200k_base and exclude tool schemas.
"""
import argparse
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import tiktoken

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.harness.observation import build_context
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.schemas import AgentCreate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(args.database)
    source.row_factory = sqlite3.Row
    row = source.execute("SELECT * FROM agent_runs WHERE tool_name='submit_orders' ORDER BY created_at LIMIT 1").fetchone()
    old = json.loads(row['observation_json'])
    snapshot = source.execute(
        'SELECT snapshot_json FROM player_snapshots WHERE agent_id=? AND leaf_state_id=? ORDER BY id DESC LIMIT 1',
        (row['agent_id'], old['game']['stateId']),
    ).fetchone()
    user = source.execute('SELECT user_id FROM agents WHERE id=?', (row['agent_id'],)).fetchone()[0]
    source.close()
    database = Database(args.output / 'harness.db')
    store = AgentStore(database)
    record = store.create_agent(AgentCreate(name='Context comparison', model='openai/gpt-oss-120b', user_id=user, auth_token='local'))
    harness = StrategicHarness(SimpleNamespace(rules_oracle_available=True), store)
    prepared = harness.prepare_turn(record, build_context(json.loads(snapshot[0]), user), None)
    encoder = tiktoken.get_encoding('o200k_base')
    metrics = {'sourceRunId': row['id'], 'tokenizer': 'o200k_base', 'excludesToolSchemas': True}
    for label, instructions, observation in [('baseline', row['instructions'], old), ('tuned', prepared.instructions, prepared.observation)]:
        text = instructions + '\n' + json.dumps(observation, separators=(',', ':'))
        metrics[label] = {
            'instructionTokens': len(encoder.encode(instructions)),
            'observationTokens': len(encoder.encode(json.dumps(observation, separators=(',', ':')))),
            'totalTokensExcludingTools': len(encoder.encode(text)),
        }
        (args.output / f'{label}.txt').write_text(text)
    (args.output / 'metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
    print(json.dumps(metrics, indent=2))
    database.close()


if __name__ == '__main__':
    main()
