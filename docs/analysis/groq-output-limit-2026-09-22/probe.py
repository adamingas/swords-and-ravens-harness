"""Bounded Groq-only Responses probes; never executes a gameplay action."""
import argparse
import asyncio
import hashlib
import json
import sqlite3
import time
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator

from raven_harness.config import Settings
from raven_harness.harness.decision import DecisionContract, DecisionOutputSchema
from raven_harness.models.openai_agent import OpenRouterAgentRunner

OUT = Path('data/evaluations/groq-output-limit-diagnostics-20260922')
SOURCE = Path('data/evaluations/reachable-routes-oss-cerebras-20260922-medium/harness.db')
RUN_ID = '0ac4d779-caf5-458a-8003-06a2c33ee6e5'


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def request(case, settings):
    body = dict(model='openai/gpt-oss-120b', reasoning={'effort': 'high'},
                max_output_tokens=40960, store=False)
    schema = None
    if case == 'synthetic':
        source = Path('data/evaluations/cerebras-output-limit-diagnostics-20260922/responses_both_limits_repeat.request.json')
        body['input'] = json.loads(source.read_text())['input']
    elif case == 'long_tool':
        body.update(
            input='Generate a test fixture for a JSON integer parser. Call emit_fixture with the complete array of integers from 1 through 5000 inclusive, in ascending order. The fixture needs literal integer values, not code or a description. This long tool payload is intentional and will be saved as test data.',
            tools=[{'type': 'function', 'name': 'emit_fixture',
                    'description': 'Save the literal integer fixture for the parser test.',
                    'strict': True, 'parameters': {'type':'object',
                        'properties': {'numbers': {'type':'array',
                            'items':{'type':'integer'}, 'minItems':5000, 'maxItems':5000}},
                        'required':['numbers'], 'additionalProperties':False}}],
            tool_choice={'type':'function','name':'emit_fixture'}, parallel_tool_calls=False)
    else:
        with sqlite3.connect(SOURCE.resolve().as_uri() + '?mode=ro', uri=True) as db:
            db.row_factory = sqlite3.Row
            row = db.execute('SELECT * FROM agent_runs WHERE id=?', (RUN_ID,)).fetchone()
        observation = json.loads(row['observation_json'])
        briefing = observation.pop('decisionBriefing')
        current_input = (
            'Read the current board state, then follow the decision instructions below.'
            '\n\nCurrent observation:\n' + json.dumps(observation, separators=(',', ':'))
            + '\n\nCurrent decision:\n' + briefing
            + '\n\nHow to complete this decision:\n'
            'You MUST call submit_action to submit your gameplay action. A text response '
            'does not submit anything. Use the exact fields and enum values in the current '
            'submit_action schema. Explore liberally with the other tools whenever they can '
            'test a route, target, threat, rule, memory, or assumption. Inspect the results, '
            'then call submit_action. Exploration tools do not submit an action.'
        )
        context = json.loads(row['context_json'])
        assert hashlib.sha256(current_input.encode()).hexdigest() == context['currentInputSha256']
        schema = context['actionOutputSchema']
        submission = DecisionContract(None, [], DecisionOutputSchema(schema)).submission_tool()
        tools = json.loads(row['tools_json']) + [{
            'type': 'function', 'name': submission.name, 'description': submission.description,
            'parameters': submission.params_json_schema, 'strict': submission.strict_json_schema,
        }]
        body.update(input=[{'role': 'user', 'content': current_input}],
                    instructions=row['instructions'], tools=tools,
                    tool_choice='required', parallel_tool_calls=False)
        write('mustering.source.json', {'database': str(SOURCE), 'runId': RUN_ID,
              'inputSha256': context['currentInputSha256'],
              'scope': 'First provider request replay only; tools and actions are not executed'})
    body['provider'] = {'only': ['groq'], 'allow_fallbacks': False,
                        'ignore': settings.openrouter_blocked_providers}
    return body, schema


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=['synthetic', 'mustering', 'long_tool'])
    case = parser.parse_args().case
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / f'{case}.request.json').exists():
        raise RuntimeError('This probe already has a request artifact; refusing accidental repeat')
    settings = Settings()
    assert settings.uses_openrouter and 'groq' not in settings.openrouter_blocked_providers
    body, schema = request(case, settings)
    write(f'{case}.request.json', body)
    print(f'Starting {case}: Groq only, high reasoning, max_output_tokens=40960', flush=True)
    runner = OpenRouterAgentRunner(api_key=settings.openrouter_token,
             base_url=settings.openrouter_base_url,
             provider_blocklist=settings.openrouter_blocked_providers, max_output_tokens=40960)
    start = time.monotonic()
    try:
        extra_body = {'provider': body.pop('provider')}
        response = await runner.client.with_options(timeout=180, max_retries=0).responses.create(
            **body, extra_body=extra_body)
        raw = response.model_dump(mode='json')
        write(f'{case}.response.json', raw)
        usage = raw.get('usage') or {}
        summary = {'responseId': raw['id'], 'status': raw['status'],
                   'elapsedSeconds': round(time.monotonic()-start, 3),
                   'requestedMaxOutputTokens': 40960, 'reasoningEffort': 'high',
                   'usage': usage, 'incompleteDetails': raw.get('incomplete_details'), 'error':raw.get('error'),
                   'calls': [{k: i.get(k) for k in ('name', 'arguments')}
                             for i in raw.get('output', []) if i.get('type') == 'function_call']}
        if schema:
            summary['submissionSchemaErrors'] = [
                str(e.message) for call in summary['calls'] if call['name']=='submit_action'
                for e in Draft202012Validator(schema).iter_errors(json.loads(call['arguments']))]
        write(f'{case}.summary.json', summary)
        print(json.dumps({**summary, 'calls':[{'name':c['name'], 'argumentCharacters':len(c['arguments'] or '')} for c in summary['calls']]}), flush=True)
        async with httpx.AsyncClient(timeout=30) as client:
            generation = await client.get(settings.openrouter_base_url + '/generation',
                params={'id':raw['id']}, headers={'Authorization':'Bearer '+settings.openrouter_token})
        write(f'{case}.generation.json', generation.json())
        data = generation.json().get('data', {})
        print(json.dumps({k:data.get(k) for k in ('provider_name','native_tokens_completion','native_finish_reason','total_cost')}), flush=True)
    finally:
        await runner.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
