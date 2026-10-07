"""Read-only state checks supporting the audit; no actions or inference."""
import json
import sqlite3
from pathlib import Path
from raven_harness.game.map_reference import load_map_reference
from raven_harness.harness.observation import build_context
from raven_harness.harness.legal import legal_mustering_options, validate_musterings
from raven_harness.harness.protocol_tools import MusterGroup, Recruitment

HERE=Path(__file__).resolve().parent
rows=json.loads((HERE/'inventory.json').read_text())
conn=sqlite3.connect('file:data/evaluations/reachable-routes-oss-cerebras-20260922-medium/harness.db?mode=ro',uri=True)
conn.row_factory=sqlite3.Row
proofs=[]
for r in rows:
    if r['action']!='skip_mustering':continue
    run=conn.execute('SELECT * FROM agent_runs WHERE id=?',(r['runId'],)).fetchone()
    snap=conn.execute('SELECT snapshot_json FROM player_snapshots WHERE agent_id=? AND leaf_state_id=? AND created_at<=? ORDER BY id DESC LIMIT 1',(run['agent_id'],r['observation']['game']['stateId'],run['created_at'])).fetchone()
    context=build_context(json.loads(snap[0]),r['observation']['you']['userId'])
    opts=legal_mustering_options(context);examples=[]
    for origin in opts['origins']:
        dest=next(d for d in origin['destinations'] if d['regionId']==origin['regionId'])
        for kind,upgrade in [('footman',False),('knight',True)]:
            plan=[MusterGroup(mustering_region_id=origin['regionId'],recruitments=[Recruitment(unit_type=kind,region_id=origin['regionId'],upgrade_from_footman=upgrade)])]
            try:validate_musterings(context,plan)
            except ValueError:continue
            examples.append([m.model_dump() for m in plan])
    proofs.append({'key':r['key'],'runId':r['runId'],'options':opts,'individuallyValidAlternativePlans':examples})
    print(r['key'],'valid single-recruit alternatives',len(examples),examples[:1])
(HERE/'mustering-alternatives.json').write_text(json.dumps(proofs,indent=2)+'\n')
regions={r['id']:r for r in load_map_reference(3)['regions']}
selected=['castle-black','the-stony-shore','stoney-sept','crackclaw-point','riverrun','kingswood','shipbreaker-bay','the-shivering-sea','moat-cailin','white-harbor','the-reach','the-golden-sound']
(HERE/'map-evidence.json').write_text(json.dumps({k:regions[k] for k in selected},indent=2)+'\n')
print('Map pairs',[(a,b,b in regions[a]['neighbours']) for a,b in [('crackclaw-point','riverrun'),('kingswood','riverrun'),('shipbreaker-bay','riverrun'),('the-shivering-sea','moat-cailin'),('the-reach','riverrun')]])
