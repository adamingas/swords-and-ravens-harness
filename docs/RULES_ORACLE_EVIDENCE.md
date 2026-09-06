# Evidence for the rules oracle

This report records why Raven Harness includes a rules oracle. The project did
not add the oracle only because it seemed useful. Stored model runs showed that
players repeated rule errors across failed model runs.

The upstream Swords and Ravens repository does not contain the board-game
rulebook or FAQ. Its only `rules.html` file contains platform conduct and
community rules. It is not a source for game legality. The oracle therefore
uses the publisher's official Fantasy Flight Games rulebook and FAQ PDFs.
`src/raven_harness/rulebook.py` pins both source URLs and SHA-256 digests. The
generated `data/rules.json` also records that source metadata.

## Evidence before the oracle

The local trace database `data/match.db` contains model runs from 5 September
2026. These runs happened before the first tracked rules-oracle implementation
on 6 September 2026.

The trace contains seven failed planning runs in three groups:

| Failure | Repetitions |
| --- | ---: |
| The model selected a Defense +2 order during an active Westeros restriction. | 3 |
| The model selected more starred orders than its current limit. | 2 |
| The model selected more physical Defense orders than the house owned. | 2 |

Each failure came from a model tool call. The same player then had to make
another model request for the same decision. The repeated attempts are evidence
that the model did not reliably apply the order rules from its prompt and game
state.

The source database has SHA-256 digest
`d1d6dad70485645b0c8ccffd499443c9bc9924b552c24e05eaff2ea70fd69ee9`.
It is not committed because it contains private player observations and model
traces. The digest identifies the source used for this report.

The tracked [sanitized evidence](rules-oracle-evidence.json) contains the seven
run IDs, pseudonymous players, times, state IDs, phases, and final rule errors.
It does not contain observations, prompts, credentials, or model output. The
following SQL selected the source rows. The extraction then read `stateId` and
`phase` from `observation_json` and removed the generic tool-error prefix.

The private source databases are intentionally ignored by Git. Regenerating
the tracked extract requires those local databases. Check their recorded
SHA-256 digests before using them so the source rows cannot change silently.

~~~sql
SELECT id, agent_id, created_at, observation_json, error
FROM agent_runs
WHERE status = 'failed'
  AND (
    error LIKE '%active Westeros restrictions prohibit order values defense_plus_two'
    OR error LIKE '%assignments may contain at most 1 starred orders'
    OR error LIKE '%order defense may be used at most 2 times'
  )
ORDER BY created_at;
~~~

The extraction visits the filtered rows in this order. It calls the first
distinct `agent_id` `player-a` and the second distinct `agent_id` `player-b`.
It does not copy either source ID into the tracked file.

## Evidence during oracle testing

A later evaluation exposed a second rules problem. An agent asked the oracle
for the army limits at Supply 1 after several rejected mustering attempts. The
extracted PDF text did not contain the values from the graphical Supply chart.
The oracle answered that Supply 1 permits two armies of size two. The correct
chart value is three armies of size two.

The harness now appends a verified text transcription of that chart to the
`supply-and-mustering` section. The source evaluation database has SHA-256
digest
`f87ffdf7e768e66d0906dd7f8b0af1bd8d07e8b8329280b79e533826062b0fe6`.

## Resulting design

This evidence supports an optional rules oracle. The oracle uses the same model
as the player. It can read one or two named rule sections for each question. It
does not use embeddings, similarity search, or RAG. The main player receives
the answer and must still select one gameplay action.

The game server remains authoritative. The legality layer also rejects known
illegal inputs before it sends them. The oracle helps with rules reasoning; it
does not replace server validation.
