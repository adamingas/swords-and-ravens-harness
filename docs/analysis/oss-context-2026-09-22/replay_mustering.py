"""Replay one saved mustering decision against a local sink, never a game server.

This tests model choices and local validation, not server acceptance or win rate.
The recorded private plan is restored; historical observations are not imported.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from raven_harness.agent_store import AgentStore
from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.errors import safe_error_text
from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.observation import build_context
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.rulebook import Rulebook
from raven_harness.schemas import AgentCreate
from run_game import GroqOnlyRunner


class LocalActionSink:
    connection_generation = 1

    def __init__(self, snapshot):
        self.snapshot = deepcopy(snapshot)
        self.recent_events = []
        self.messages = []

    async def send(self, message, **kwargs):
        assert kwargs['expected_generation'] == 1
        self.messages.append(message)

    async def sync_snapshot(self, **kwargs):
        assert kwargs['expected_generation'] == 1
        self.snapshot['leafStateId'] = 'local-replay-finished'
        return self.snapshot


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = sqlite3.connect(args.database)
    source.row_factory = sqlite3.Row
    row = source.execute('SELECT * FROM agent_runs WHERE id=?', (args.run_id,)).fetchone()
    old = json.loads(row['observation_json'])
    saved = source.execute(
        'SELECT snapshot_json FROM player_snapshots WHERE agent_id=? AND leaf_state_id=? ORDER BY id DESC LIMIT 1',
        (row['agent_id'], old['game']['stateId']),
    ).fetchone()
    user = source.execute(
        'SELECT user_id FROM agents WHERE id=?', (row['agent_id'],),
    ).fetchone()[0]
    source.close()
    snapshot = json.loads(saved[0])
    game_context = build_context(snapshot, user)
    if game_context.leaf['type'] != 'player-mustering':
        raise ValueError('Only mustering decisions may be replayed by this local sink')
    settings = Settings()
    runner = GroqOnlyRunner(
        api_key=settings.openrouter_token, base_url=settings.openrouter_base_url,
        provider_blocklist=settings.openrouter_blocked_providers,
        max_output_tokens=32768, rulebook=Rulebook.load_optional(settings.resolved_rules_path),
    )
    database = Database(args.output / 'harness.db')
    store = AgentStore(database)
    record = store.create_agent(AgentCreate(
        name='Mustering replay', user_id=user, auth_token=user, model='openai/gpt-oss-120b',
    ))
    store.set_strategic_memory(record.id, old['strategicMemory'])
    harness = StrategicHarness(runner, store)
    prepared = harness.prepare_turn(record, game_context, None)
    sink = LocalActionSink(snapshot)
    context = HarnessRunContext(client=sink, user_id=user)
    evidence = {
        'sourceDatabase': str(args.database.resolve()), 'sourceRunId': args.run_id,
        'localReplayOnly': True, 'serverAcceptanceTested': False,
        'observation': prepared.observation, 'instructions': prepared.instructions,
        'schema': prepared.decision.output_schema.json_schema(),
    }
    try:
        result = await asyncio.wait_for(harness.run_turn(
            record, prepared, context, 'mustering-replay',
        ), timeout=180)
        evidence.update(result=asdict(result), action=asdict(context.action_taken), handoff=context.pending_strategy_note)
        print(json.dumps({'action': evidence['action'], 'handoff': evidence['handoff'], 'usage': result.usage}))
    except BaseException as error:
        evidence['error'] = safe_error_text(error)
        partial = getattr(error, 'partial_result', None)
        if partial is None:
            partial = getattr(error.__cause__, 'partial_result', None)
        if partial is not None:
            evidence['partialResult'] = asdict(partial)
        raise
    finally:
        (args.output / 'replay.json').write_text(json.dumps(evidence, indent=2)+'\n')
        await runner.shutdown()
        database.close()


if __name__ == '__main__':
    asyncio.run(main())
