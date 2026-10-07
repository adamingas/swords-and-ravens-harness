"""Build audit ledgers from extracted evidence without model or server calls."""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "inventory.json").read_text())


def link(row):
    return f"[{row['key']}](round-{row['round']:02}.md#{row['key'].lower()})"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


# Add stable links and preserve returned reasoning separately from conclusions.
for number in range(1, 11):
    path = HERE / f"round-{number:02}.md"
    content = path.read_text()
    for row in rows:
        if row['round'] != number:
            continue
        anchor = f"<a id=\"{row['key'].lower()}\"></a>"
        if anchor not in content:
            content = content.replace(f"## {row['key']} —", f"{anchor}\n\n## {row['key']} —")
    path.write_text(content)

events = []
tool_errors = []
combats = {}
for row in rows:
    for call in row['calls']:
        out = call['output']
        explicit = isinstance(out, dict) and out.get('accepted') is False
        if call['name'] == 'submit_action' and (explicit or call['schemaErrorsReconstructed']):
            events.append({'key': row['key'], 'runId': row['runId'], 'round': row['round'],
                           'house': row['house'], **call,
                           'evidence': 'recorded rejection' if explicit else 'revalidated stored arguments; original output missing'})
        if call['name'] != 'submit_action' and isinstance(out, str) and out.startswith('An error occurred while running the tool.'):
            tool_errors.append({'key': row['key'], **call})
    for event in row['observation'].get('recentEvents', []):
        if event.get('event') == 'combat-result':
            ident = json.dumps(event, sort_keys=True)
            combats.setdefault(ident, {'firstObservedAt': row['key'], 'round': row['round'], 'event': event})

(HERE / 'retry-events.json').write_text(json.dumps(events, indent=2) + '\n')
(HERE / 'tool-errors.json').write_text(json.dumps(tool_errors, indent=2) + '\n')
(HERE / 'combat-evidence.json').write_text(json.dumps(list(combats.values()), indent=2) + '\n')
bad = [r for r in rows if r['status'] != 'completed' or r['counts']['schemaInvalidSubmissions'] or r['counts']['nonSchemaRejections']]
lines = ['# Exhaustive retry and failure ledger', '',
         'Each D-number identifies one model-run attempt, not a game round. Requests include parent and rules-oracle responses with usage. Exploration requests are not automatically retries.', '',
         '402 submissions: 158 accepted, 243 schema-invalid, and one domain-legality rejection. Of the 244 unsuccessful submissions, 94 have recorded rejection outputs; 150 are independently revalidated from their arguments because their outputs were not persisted. The latter are not fabricated tool feedback.', '',
         f'{len(bad)} run attempts had invalid submissions or ended failed/cancelled. All 13 failed attempts ended in output exhaustion; the two cancelled attempts are the mustering loops. See the individual ledger below for every unsuccessful submission.', '',
         '| Run | Round / house | Status | Responses | Submissions | Schema invalid | Domain invalid | Missing invalid outputs |',
         '|---|---|---|---:|---:|---:|---:|---:|']
for r in bad:
    c = r['counts']
    lines.append(f"| {link(r)} | {r['round']} / {r['house']} | {r['status']} | {r['modelRequests']} | {c['submissions']} | {c['schemaInvalidSubmissions']} | {c['nonSchemaRejections']} | {c['reconstructedInvalidWithoutOutput']} |")
lines += ['', '## All 244 unsuccessful submissions', '',
          'Call numbers are chronological within each run, including exploration calls. Error excerpts are abbreviated here; exact arguments, complete errors and original outputs are in [retry-events.json](retry-events.json). “Reconstructed” means schema validation now, not an archived response.', '',
          '| Run | Call | Evidence | Error excerpt |', '|---|---:|---|---|']
by_key = {r['key']: r for r in rows}
for e in events:
    out = e['output']
    error = out.get('error') if isinstance(out, dict) else None
    error = error or '; '.join(e['schemaErrorsReconstructed'])
    lines.append(f"| {link(by_key[e['key']])} | {e['ordinal']} | {'Recorded' if e['evidence']=='recorded rejection' else 'Reconstructed'} | {cell(error[:260])} |")
lines += ['', '## Exploration-tool failures', '',
          'These are separate from submit-action rejection counts. They include six oracle output-limit failures, one oracle turn-limit failure, and one misspelled card ID. A later attempt may repeat the failed query; the ledger preserves every occurrence.', '',
          '| Run | Call | Tool | Error |', '|---|---:|---|---|']
for e in tool_errors:
    lines.append(f"| {link(by_key[e['key']])} | {e['ordinal']} | {e['name']} | {cell(e['output'])} |")
(HERE / 'RETRIES.md').write_text('\n'.join(lines) + '\n')

assessments = {
    'D004': 'Optional Raven pass; not inherently bad. 29 schema rejections before acceptance.',
    'D017': 'Optional Raven pass; one schema rejection, no demonstrated strategic loss.',
    'D030': 'Optional Raven pass after D029 output exhaustion; one schema rejection.',
    'D036': 'Clear interface-induced abandonment: 25 rejections, then discarded March instead of intended legal Winterfell move.',
    'D048': 'Skipped free mustering to preserve power; six individually legal alternatives verified. Follows repeated failed mustering runs.',
    'D049': 'Skipped free mustering to preserve power; three legal alternatives verified.',
    'D056': 'Optional Raven pass; one schema rejection, no demonstrated strategic loss.',
    'D058': 'Abandoned planned Harrenhal attack; falsely feared vacating token-controlled Riverrun would lose it. Attack itself was risky.',
    'D069': 'Optional Raven pass; one schema rejection, no demonstrated strategic loss.',
    'D071': 'Again abandoned Harrenhal attack. Sensible recognition of an unfavorable battle; earlier order allocation wasted.',
    'D085': 'Abandoned Winterfell attack; legitimate concern about vacating Moat Cailin without a token. Not established as a bad pass.',
    'D090': 'Skipped free mustering citing power/Supply; seven legal alternatives verified.',
    'D091': 'Skipped free mustering citing resources/Supply; six legal alternatives verified.',
    'D092': 'Skipped rebuilding depleted Stark army; two legal alternatives verified.',
    'D104': 'Abandoned White Harbor move citing defenses, but destination was empty with zero garrison. Castle trade has positional tradeoffs.',
    'D117': 'Reasonable blade decline: 5+1 still loses to 7. The earlier card/support calculation caused the defeat.',
    'D144': 'Raven pass after D143 attempted replacement failed; intent changed on retry, value of original replacement unproven.',
    'D154': 'Clear costly blade decline: ignored Kevan ability; +1 would turn 3–4 loss into 4–4 win on Fiefdoms.',
    'D157': 'Skipped free mustering to conserve power; seven legal alternatives verified.',
    'D158': 'Skipped free mustering because seven castles seemed unreachable, ignoring round-ten scoring; four legal alternatives verified.',
    'D159': 'Skipped free mustering to preserve bidding tokens; five legal alternatives verified.',
    'D168': 'No March orders while tied on castles but losing tiebreak. False claims that attacks require ships and power affects final scoring.',
    'D169': 'No March orders while trailing. Claims no attack opportunities; this relinquished any attempt to improve castle score.',
    'D172': 'Raven pass after D171 attempted replacement failed. Original Stoney Sept “stronghold” plan itself used wrong map scoring.',
    'D173': 'Reasonable final March pass while winning tiebreak. Its token rationale was wrong: source already had a control token.',
}
lines = ['# Passes, skipped mustering and final-round inactivity', '',
         'All six empty marches, eight mustering skips, seven Raven skips, two blade declines, and both final-round plans without a March are included. These 25 decisions are not 25 demonstrated mistakes.', '',
         '| Run | Round / house | Action | Assessment |', '|---|---|---|---|']
for key, assessment in sorted(assessments.items()):
    r = by_key[key]
    lines.append(f"| {link(r)} | {r['round']} / {r['house']} | {r['action']} | {assessment} |")
lines += ['', '## Mustering counterfactuals', '',
          'For every mustering skip, [verify_state.py](verify_state.py) loads the corresponding archived player snapshot and tests individual recruitment/upgrade plans with the harness validator. [mustering-alternatives.json](mustering-alternatives.json) preserves the plans. These are independent alternatives, not a claim they can all be combined; no counterfactual game was played.', '']
(HERE / 'PASSES.md').write_text('\n'.join(lines))

assert len(rows) == 173
assert all(r['inputVerification']['reconstructedHashMatches'] for r in rows)
assert sum(r['counts']['submissions'] for r in rows) == 402
assert len(events) == 244
assert len(tool_errors) == 8
assert len(combats) == 6
assert sum(r['modelRequests'] for r in rows) == 527
assert Counter(r['status'] for r in rows) == {'completed': 158, 'failed': 13, 'cancelled': 2}
assert sum(not r['inputVerification']['originalHashMatches'] for r in rows) == 83
print(f'Verified 173 input hashes, {len(events)} unsuccessful submissions, {len(tool_errors)} tool failures, six combats; {len(bad)} problem runs.')
