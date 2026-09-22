"""Summarize recorded game decisions without making model requests."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import statistics

from raven_harness.game.map_reference import load_map_reference


def audit(directory):
    db = sqlite3.connect(directory / 'harness.db')
    db.row_factory = sqlite3.Row
    regions = {r['id']: r for r in load_map_reference(6)['regions']}
    decisions = []
    calls = Counter()
    errors = []
    usages = []
    for row in db.execute('SELECT * FROM agent_runs ORDER BY created_at'):
        observation = json.loads(row['observation_json'])
        response = json.loads(row['response_json'] or '[]')
        failed_calls = []
        handoff = ''
        for item in response:
            if item.get('type') == 'function_call':
                calls[item.get('name')] += 1
                if item.get('name') == 'submit_action':
                    try:
                        submitted = json.loads(item.get('arguments', '{}'))
                        handoff = submitted.get('decision', submitted).get('strategic_handoff', '') or submitted.get('strategic_handoff', '')
                    except (ValueError, AttributeError):
                        pass
            if item.get('type') == 'function_call_output':
                try:
                    output = json.loads(item.get('output', '{}'))
                    if isinstance(output, dict) and (output.get('accepted') is False or output.get('error')):
                        failed_calls.append(output.get('error', output))
                except (ValueError, TypeError):
                    if 'error' in str(item.get('output', '')).lower():
                        failed_calls.append(item['output'])
        args = json.loads(row['tool_arguments_json'] or '{}')
        sea_power = [
            order['region_id'] for order in args.get('applied_orders', [])
            if order['order_id'] in (10, 11, 12)
            and regions.get(order['region_id'], {}).get('type') == 'sea'
        ]
        raw_usage = json.loads(row['raw_usage_json'] or '[]')
        usages.extend(raw_usage)
        decision = {
            'id': row['id'], 'house': observation.get('you', {}).get('houseId'),
            'round': observation['game'].get('round'), 'phase': observation['game']['phase'],
            'status': row['status'], 'action': row['tool_name'], 'arguments': args,
            'handoff': handoff, 'toolErrors': failed_calls, 'error': row['error'],
            'durationMs': row['duration_ms'],
            'usage': json.loads(row['usage_json'] or '{}'),
            'observationCharacters': len(row['observation_json']),
            'instructionsCharacters': len(row['instructions'] or ''),
            'openSeaPowerOrders': sea_power,
        }
        decisions.append(decision)
        if row['status'] == 'failed':
            errors.append({'id': row['id'], 'error': row['error']})
    db.close()
    successes = [d for d in decisions if d['status'] == 'completed']
    summary = {
        'directory': str(directory), 'runs': len(decisions), 'completedDecisions': len(successes),
        'statusCounts': dict(Counter(d['status'] for d in decisions)),
        'cancelledRuns': [d['id'] for d in decisions if d['status'] == 'cancelled'],
        'latestRound': max((d['round'] or 0 for d in decisions), default=0),
        'failedRuns': errors, 'observedToolErrors': sum(len(d['toolErrors']) for d in decisions),
        'toolCalls': dict(calls),
        'emptyMarches': [d['id'] for d in successes if d['action'] == 'resolve_march' and not d['arguments'].get('moves')],
        'skippedMustering': [d['id'] for d in successes if d['action'] == 'skip_mustering'],
        'openSeaPowerOrders': sum(len(d['openSeaPowerOrders']) for d in decisions),
        'requests': sum(d['usage'].get('requests', 0) for d in decisions),
        'inputTokens': sum(u.get('input_tokens', 0) for u in usages),
        'outputTokens': sum(u.get('output_tokens', 0) for u in usages),
        'maxResponseOutputTokens': max((u.get('output_tokens', 0) for u in usages), default=0),
        'cost': sum(u.get('cost') or 0 for u in usages),
        'medianSuccessfulDecisionMs': statistics.median([d['durationMs'] for d in successes]) if successes else None,
    }
    (directory / 'trace-audit.json').write_text(json.dumps({'summary': summary, 'decisions': decisions}, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps([audit(d.resolve()) for d in args.directories], indent=2))
