"""External experiment supervision; never modifies harness or game state."""
import argparse
import contextlib
from datetime import datetime, timezone
import io
import json
import os
import signal
import sqlite3
import time

from audit import ROOT, main as audit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--launcher-pid', type=int, required=True)
args = parser.parse_args()
(ROOT/'supervision.json').write_text(json.dumps({
    'launcherPid': args.launcher_pid,
    'policy': 'Stop the experiment externally if one still-active decision reaches five submit_action attempts. Preserve the save and provider evidence; never patch the harness.',
    'pollSeconds': 5,
}, indent=2)+'\n')
last_signature = None
while True:
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            audit()
        report = json.loads((ROOT/'audit.json').read_text())
        signature = (report['status'], report['round'], len(report['decisions']), len(report['issues']))
        if signature != last_signature:
            print(json.dumps({'at': report['updatedAt'], 'status': signature[0], 'round': signature[1],
                              'attempts': signature[2], 'issues': signature[3]}), flush=True)
            last_signature = signature
        if report['status'] != 'running':
            break
        completed = {r['runId'] for r in report['decisions']}
        offender = next((a for a in report['active']
                         if a['run'] not in completed and a['tools'].get('submit_action', 0) >= 5), None)
        if offender:
            # Confirm the run has not finished since the audit snapshot.
            with sqlite3.connect((ROOT/'harness.db').resolve().as_uri()+'?mode=ro', uri=True) as db:
                finished = db.execute('select 1 from agent_runs where id=?', (offender['run'],)).fetchone()
            if not finished:
                alert = {'at': datetime.now(timezone.utc).isoformat(), 'reason': 'Repeated-submission guard', **offender}
                (ROOT/'supervision-alert.json').write_text(json.dumps(alert, indent=2)+'\n')
                print(json.dumps(alert), flush=True)
                os.kill(args.launcher_pid, signal.SIGINT)
                # Continue only read-only auditing while cancellation persists evidence.
                time.sleep(5)
        os.kill(args.launcher_pid, 0)
    except ProcessLookupError:
        break
    except (OSError, sqlite3.Error, json.JSONDecodeError) as error:
        print(type(error).__name__+': '+str(error), flush=True)
    time.sleep(5)
