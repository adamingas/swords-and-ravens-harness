"""Read-only, exhaustive inventory of recorded attempts; no model calls."""
import json
import hashlib
import itertools
import sqlite3
from collections import Counter
from pathlib import Path
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SOURCE = Path('data/evaluations/reachable-routes-oss-cerebras-20260922-medium')

def flatten(items):
    for i in items:
        if i.get('type') == 'partial_model_response':
            yield from flatten(i.get('output', []))
        else:
            yield i

def input_hash(o):
    o=dict(o);brief=o.pop('decisionBriefing')
    t=('Read the current board state, then follow the decision instructions below.'
       +'\n\nCurrent observation:\n'+json.dumps(o,separators=(',',':'))
       +'\n\nCurrent decision:\n'+brief+'\n\nHow to complete this decision:\n'
       +'You MUST call submit_action to submit your gameplay action. A text response '
       +'does not submit anything. Use the exact fields and enum values in the current '
       +'submit_action schema. Explore liberally with the other tools whenever they can '
       +'test a route, target, threat, rule, memory, or assumption. Inspect the results, '
       +'then call submit_action. Exploration tools do not submit an action.')
    return hashlib.sha256(t.encode()).hexdigest()

def main():
    with sqlite3.connect((SOURCE/'harness.db').resolve().as_uri()+'?mode=ro', uri=True) as db:
        db.row_factory=sqlite3.Row
        rows=db.execute('SELECT * FROM agent_runs ORDER BY created_at').fetchall()
        histories={r['id']:json.loads(r['observation_json']) for r in db.execute('SELECT id, observation_json FROM game_state_history')}
    audit=json.loads((SOURCE/'decision-audit.json').read_text())
    byid={d['runId']:d for d in audit['decisions']}
    records=[]
    for n,row in enumerate(rows,1):
        d=byid[row['id']];o=json.loads(row['observation_json']);context=json.loads(row['context_json'])
        original_hash_matches=input_hash(o)==context['currentInputSha256']
        history=histories[row['history_id']]
        changed=[k for k in history if history[k]!=o.get(k)]
        restored=[];verified=original_hash_matches
        if not verified:
            for size in range(1,len(changed)+1):
                for subset in itertools.combinations(changed,size):
                    candidate={**o,**{k:history[k] for k in subset}}
                    if input_hash(candidate)==context['currentInputSha256']:
                        o=candidate;restored=list(subset);verified=True;break
                if verified:break
        if not verified and o['pendingDecision'].get('type')=='place-orders':
            houses=[h['id'] for h in o['houses']]
            for size in range(len(houses)+1):
                for ready in itertools.permutations(houses,size):
                    candidate={**o,'pendingDecision':{**o['pendingDecision'],'readyHouses':list(ready)}}
                    if input_hash(candidate)==context['currentInputSha256']:
                        o=candidate;restored=['pendingDecision.readyHouses (intermediate state, hash-verified)'];verified=True;break
                if verified:break
        schema=context['actionOutputSchema'];v=Draft202012Validator(schema)
        items=list(flatten(json.loads(row['response_json'] or '[]')))
        outputs={i['call_id']:i['output'] for i in items if i.get('type')=='function_call_output'}
        calls=[];seen=set()
        for i in items:
            if i.get('type')!='function_call' or i.get('call_id') in seen:continue
            seen.add(i.get('call_id'));args=json.loads(i['arguments']);out=outputs.get(i.get('call_id'))
            if isinstance(out,str):
                try:out=json.loads(out)
                except ValueError:pass
            errors=[e.message for e in v.iter_errors(args)] if i['name']=='submit_action' else []
            calls.append({'ordinal':len(calls)+1,'name':i['name'],'arguments':args,'output':out,
                          'schemaErrorsReconstructed':errors})
        subs=[x for x in calls if x['name']=='submit_action']
        rejected=[x for x in subs if isinstance(x['output'],dict) and x['output'].get('accepted') is False]
        invalid=[x for x in subs if x['schemaErrorsReconstructed']]
        r={'key':f'D{n:03}',**d,'observation':o,'calls':calls,
           'inputVerification':{'originalHashMatches':original_hash_matches,'reconstructedHashMatches':verified,'restoredFields':restored},
           'counts':{'submissions':len(subs),'explicitRejections':len(rejected),
                     'schemaInvalidSubmissions':len(invalid),
                     'reconstructedInvalidWithoutOutput':sum(x['output'] is None for x in invalid),
                     'nonSchemaRejections':sum(not x['schemaErrorsReconstructed'] for x in rejected)},
           'usageScopes':dict(Counter(u.get('scope') for u in json.loads(row['raw_usage_json'] or '[]')))}
        records.append(r)
    (HERE/'inventory.json').write_text(json.dumps(records,indent=2)+'\n')
    for round_number in range(1,11):
        lines=[f'# Round {round_number}: recorded decisions and state evidence','']
        for r in records:
            if r['round']!=round_number:continue
            o=r['observation'];lines += [f"## {r['key']} — {r['house']} — {r['action'] or r['phase'][-1]} ({r['status']})",'',f"Run `{r['runId']}`. Requests: {r['modelRequests']}; counts: `{json.dumps(r['counts'])}`.",'',f"Action: `{json.dumps(r['arguments'])}`",'',f"Handoff: {r['strategicHandoff']}",'',f"Previous plan: {r['previousPlan']}",'',f"Pending: `{json.dumps(o['pendingDecision'])}`",'',f"Guidance: `{json.dumps(o.get('actionGuidance'))}`",'',f"Tracks: `{json.dumps(o.get('tracks'))}`",'',f"Houses: `{json.dumps(o.get('houses'))}`",'']
        (HERE/f'round-{round_number:02}.md').write_text('\n'.join(lines)+'\n')
    totals=Counter()
    for r in records:totals.update(r['counts'])
    print(json.dumps(dict(totals),indent=2))
    print('input hashes:',dict(Counter(str(r['inputVerification']) for r in records)))
    for r in records:
        c=r['counts']
        if c['explicitRejections'] or c['schemaInvalidSubmissions'] or r['status']!='completed':
            print(r['key'],r['round'],r['house'],r['phase'][-1],r['status'],r['modelRequests'],c)

if __name__=='__main__':main()
