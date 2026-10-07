"""Read-only live audit; no inference or gameplay changes."""
import json
import sqlite3
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator
from raven_harness.rulebook import RuleSectionId

ROOT = Path('data/evaluations/luna-deepseek-qwen-20260923')


def flatten(items, scope='agent'):
    for item in items:
        if item.get('type') == 'partial_model_response':
            yield from flatten(item.get('output', []), item.get('scope', scope))
        else:
            yield {**item, '_auditScope': scope}


def main():
    db = sqlite3.connect((ROOT / 'harness.db').resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    agents = {r['id']: r['model'] for r in db.execute('select id, model from agents')}
    runs = db.execute('select * from agent_runs order by created_at').fetchall()
    progress = json.loads((ROOT / 'progress.json').read_text())
    models = {m: Counter() for m in agents.values()}
    issues = []
    decisions = []
    generations = []
    for r in runs:
        model = agents[r['agent_id']]
        stats = models[model]
        stats[r['status']] += 1
        observation = json.loads(r['observation_json'])
        items = list(flatten(json.loads(r['response_json'] or '[]')))
        context = json.loads(r['context_json'] or '{}')
        validator = Draft202012Validator(context.get('actionOutputSchema', {}))
        tool_validators = {t['name']: Draft202012Validator(t['parameters'])
                           for t in json.loads(r['tools_json'] or '[]')
                           if t.get('type') == 'function' and 'parameters' in t}
        # This nested tool belongs to the oracle, not the parent tools_json.
        # Its contract is derived from the unchanged Rulebook.build_oracle_tool.
        oracle_validator = Draft202012Validator({
            'type': 'object', 'required': ['section_ids'], 'additionalProperties': False,
            'properties': {'section_ids': {'type': 'array', 'minItems': 1, 'maxItems': 2,
                                         'items': {'type': 'string', 'enum': [s.value for s in RuleSectionId]}}},
        })
        outputs = {i['call_id']: i['output'] for i in items if i.get('type') == 'function_call_output'}
        calls = []
        seen = set()
        for i in items:
            if i.get('type') != 'function_call' or i.get('call_id') in seen:
                continue
            seen.add(i.get('call_id'))
            try:
                args = json.loads(i['arguments'])
            except (ValueError, TypeError) as error:
                stats['invalidToolJson'] += 1
                issues.append(dict(runId=r['id'], model=model, category='provider-invalid-tool-json',
                                   tool=i['name'], error=str(error), arguments=i['arguments']))
                continue
            out = outputs.get(i.get('call_id'))
            if isinstance(out, str):
                try:
                    out = json.loads(out)
                except ValueError:
                    pass
            call = dict(name=i['name'], scope=i['_auditScope'], arguments=args, output=out)
            calls.append(call)
            stats['toolCalls'] += 1
            if i['name'] != 'submit_action':
                tool_validator = (oracle_validator if i['_auditScope'] == 'rules-oracle' and i['name'] == 'read_rulebook_sections'
                                  else tool_validators.get(i['name']) if i['_auditScope'] == 'agent' else None)
                errors = ([e.message for e in tool_validator.iter_errors(args)]
                          if tool_validator else ['Tool name was not offered'])
                if errors:
                    stats['explorationSchemaInvalid'] += 1
                    issues.append(dict(runId=r['id'], model=model, category='provider-exploration-schema', errors=errors, call=call))
            if i['name'] == 'submit_action':
                stats['submissions'] += 1
                errors = [e.message for e in validator.iter_errors(args)]
                if errors:
                    stats['schemaInvalid'] += 1
                    issues.append(dict(runId=r['id'], model=model, category='provider-schema', errors=errors, call=call))
                elif isinstance(out, dict) and out.get('accepted') is False:
                    stats['domainRejected'] += 1
                    issues.append(dict(runId=r['id'], model=model, category='game-legality', call=call))
            elif isinstance(out, str) and out.startswith('An error occurred'):
                stats['toolErrors'] += 1
                issues.append(dict(runId=r['id'], model=model, category='exploration-tool-error', call=call))
        for u in json.loads(r['raw_usage_json'] or '[]'):
            stats['responses'] += 1
            stats['costUsd'] += u.get('cost') or 0
            stats['outputTokens'] += u.get('output_tokens') or 0
            if u.get('response_id'):
                generations.append(dict(model=model, responseId=u['response_id'], scope=u.get('scope')))
        decisions.append(dict(runId=r['id'], model=model, status=r['status'],
                              round=observation.get('game', {}).get('round'),
                              house=observation.get('you', {}).get('houseId'),
                              phase=observation.get('statePath'), action=r['tool_name'],
                              arguments=json.loads(r['tool_arguments_json'] or '{}'),
                              error=r['error'], calls=calls))
    active = []
    for a in progress['agents']:
        runid = a.get('currentRunId')
        tools = Counter()
        if runid:
            for e in db.execute("select payload_json from agent_events where kind='model-tool-started' and json_extract(payload_json,'$.runId')=?", (runid,)):
                tools[json.loads(e[0]).get('tool')] += 1
        active.append(dict(model=a['model'], phase=a['statePath'][-1], autoplay=a['autoplay'],
                           run=runid, started=a.get('runStartedAt'), tools=dict(tools), error=a.get('lastError')))
    report = dict(status=json.loads((ROOT/'manifest.json').read_text())['status'],
                  updatedAt=progress['updatedAt'], round=decisions[-1]['round'] if decisions else 1,
                  models=models, issues=issues, decisions=decisions, generations=generations, active=active)
    (ROOT/'audit.json').write_text(json.dumps(report, indent=2)+'\n')
    manifest = json.loads((ROOT/'manifest.json').read_text())
    lines = ['# Luna GPT-6 vs DeepSeek V4.1 Flash vs Qwen3.8-27B', '',
             f"Status: **{report['status']}**. Latest audit: {report['updatedAt']}. Latest recorded decision: round {report['round']}.", '',
             'One three-player base game, seed 102. Luna plays Baratheon through OpenAI; DeepSeek plays Lannister through Morph; Qwen plays Stark through DeepInfra BF16. Providers are pinned, fallback is disabled, and the existing six-provider blocklist is preserved.', '',
             'All use the unchanged production harness, high reasoning and a requested 40,960-token parent output allowance. The production rules oracle retains its existing high/900-token configuration. Only this experiment launcher selects a runner per model and pins provider routing. No prompt or schema workaround is applied.', '',
             'Arguments for all recorded function calls are checked against their offered schemas. Schema-invalid submissions and exploration calls are recorded as provider issues, as requested. Domain-legality errors and exploration-tool failures are counted separately. Completed decisions can include multiple exploration requests without any submission retry.', '',
             '| Model | Completed | Failed | Cancelled | Submissions | Schema invalid | Domain rejected | Responses | Reported cost |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for model, stats in models.items():
        lines.append(f"| {model} | {stats['completed']} | {stats['failed']} | {stats['cancelled']} | {stats['submissions']} | {stats['schemaInvalid']} | {stats['domainRejected']} | {stats['responses']} | ${stats['costUsd']:.6f} |")
    lines += ['', 'Counts cover persisted attempts; an active request may not yet have returned usage or been saved.', '']
    if manifest.get('result'):
        result = manifest['result']
        lines += [f"Winner: **{result['winner']}**, round {result['round']}.", '',
                  '| Place | House | Model | Castles | Land areas |', '|---:|---|---|---:|---:|']
        for standing in result['standings']:
            lines.append(f"| {standing['placement']} | {standing['house']} | {standing['model']} | {standing['victoryPoints']} | {standing['landAreas']} |")
    elif manifest.get('error'):
        lines += ['Stop reason: '+manifest['error'], '']
    lines += ['', '## Provider and tool observations', '']
    if not issues:
        lines += ['No schema-invalid submissions, domain rejections or exploration-tool errors in persisted traces so far.', '']
    for issue in issues:
        lines.append(f"- `{issue['runId']}` / {issue['model']} / **{issue['category']}**: {json.dumps(issue.get('errors', issue.get('call', {}).get('output')), ensure_ascii=False)}")
    lines += ['', '## Evidence', '',
              f"- [Manifest and routing]({(ROOT/'manifest.json').resolve()})",
              f"- [Detailed actions, errors and request accounting]({(ROOT/'audit.json').resolve()})",
              f"- [Player-scoped SQLite traces]({(ROOT/'harness.db').resolve()})",
              f"- [Saved game]({(ROOT/'game.json').resolve()})",
              f"- [Provider catalog snapshots]({ROOT.resolve()})", '',
              'The manifest includes source fingerprints and a runtime archive. `runtimeUnchangedAtExit` is checked when the launcher exits. Read-only audits do not issue inference requests.', '']
    outcome = Path(__file__).parent/'OUTCOME.md'
    if outcome.exists():
        lines += ['', outcome.read_text()]
    (Path(__file__).parent/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps({k:v for k,v in report.items() if k not in ['decisions', 'generations', 'issues']}, indent=2))
    print('Issues:', len(issues))
    db.close()


if __name__ == '__main__':
    main()
