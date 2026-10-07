"""Offline reproduction after downloading only the published chat template."""
import hashlib
import json
import sqlite3
from pathlib import Path

import httpx
from jinja2.sandbox import ImmutableSandboxedEnvironment

from raven_harness.harness.decision import DecisionContract, DecisionOutputSchema

ROOT = Path(__file__).resolve().parent
URL = 'https://huggingface.co/openai/gpt-oss-120b/raw/main/chat_template.jinja'
response = httpx.get(URL, follow_redirects=True, timeout=20)
response.raise_for_status()
source = response.text
(ROOT / 'chat_template.jinja').write_text(source)
with sqlite3.connect('file:data/evaluations/reachable-routes-oss-cerebras-20260922-medium/harness.db?mode=ro', uri=True) as db:
    context, responses = db.execute(
        'SELECT context_json,response_json FROM agent_runs WHERE id=?',
        ('673bf8bb-c19c-4e44-998c-03127917072b',)).fetchone()
schema = json.loads(context)['actionOutputSchema']
tool = DecisionContract(None, [], DecisionOutputSchema(schema)).submission_tool()
# Render only the definition macros; no model inference or game actions.
macro_source = source.split('{#- System Message Construction')[0]
macros = ImmutableSandboxedEnvironment().from_string(macro_source).module
rendered = macros.render_tool_namespace('functions', [{
    'type': 'function', 'function': {'name': tool.name, 'description': tool.description,
                                    'parameters': tool.params_json_schema, 'strict': True}}])
assert 'decision: any,' in rendered
assert 'muster_units' not in rendered
assert 'mustering_region_id' not in rendered
assert 'recruitments' not in rendered
(ROOT / 'rendered-submission.txt').write_text(rendered + '\n')
(ROOT / 'input-schema.json').write_text(json.dumps(schema, indent=2) + '\n')
evidence = {'source': URL, 'templateSha256': hashlib.sha256(response.content).hexdigest(),
            'sourceRun': '673bf8bb-c19c-4e44-998c-03127917072b',
            'finding': 'Published template renders decision anyOf as decision: any and omits both action branches',
            'scope': 'Offline reproduction with published template; provider internal template is not observable'}
(ROOT / 'evidence.json').write_text(json.dumps(evidence, indent=2)+'\n')
print(rendered)
