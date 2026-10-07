# Geographic reachability and OSS-120B self-play

## Outcome

**The full three-player game completed normally at the end of round ten.**
The server declared **Baratheon** the winner. All seats used
`openai/gpt-oss-120b`, routed exclusively to Cerebras through OpenRouter with
fallbacks disabled and the existing provider blocklist preserved.

| House | Final castles | Placement |
| --- | ---: | ---: |
| Baratheon | 4 | 1 |
| Lannister | 4 | 2 |
| Stark | 3 | 3 |

No operator submitted gameplay actions. The game used seed 102, normal victory
and ten-round rules, normal simultaneous-player concurrency, and no evaluation
round truncation. It required interrupted/restarted segments and authorized
harness changes. This is a diagnostic full game with documented interventions,
not a clean comparison of model thinking or a wholly high-reasoning run.

The final artifact directory is
`data/evaluations/reachable-routes-oss-cerebras-20260922-medium`.
Its `result.json`, `manifest.json`, saved game, SQLite traces,
`decision-audit.json`, and `reachability-audit.json` preserve the result and
all earlier runs. Earlier directories must **not** be added again when totaling
usage: their databases were carried forward into the final continuation.

## Tool redesign

Replaced the feasibility-heavy `reachable_areas(area)` with a geographic query.
Any named area can be queried, including empty areas and areas held by another
house. Its terrain determines movement kind. Land routes use direct land edges
and the calling house's existing ship chains; sea/port queries return adjacent
sea/port destinations. Blocked areas cannot be entered or crossed. The response
contains destination IDs, names, terrain, shortest routes and transport ship IDs.

Removed army enumeration, wound-based movement filtering, March-order checks,
Supply and port-capacity filtering, port-ownership filtering, neutral-force
strength checks, combat flags, and nullable feasibility lists from this tool.
Actual action validation still performs the applicable legality checks. The
previously discovered port-capacity validator fix is retained with separate
regression tests, independent of reachability.

## Validation

- **276 tests passed** after the schema and output-allowance changes; see
  [recovery-tests.txt](recovery-tests.txt). The initial simplified-tool suite had
  265 passing tests, recorded in [tests.txt](tests.txt).
- **1,150 passing Hypothesis examples** across five properties: agreement with
  the actual upstream geometric traversal (300), shortest valid routes (250),
  removing ships cannot add routes (200), ignored legality facts do not change
  routes (200), and source occupants/input ordering do not change routes (200).
- Focused cases cover empty/enemy/wounded origins, direct movement without ships,
  multi-sea transport, caller-specific ships, blocked origins/destinations,
  alternate routes around blocked shortcuts, sea/port terrain, and read-only
  queries using refreshed snapshots.
- Responses API wire tests exercise exploration followed by submission, rejected
  actions followed by schema-guided correction, and output-allowance serialization.
- Ruff and `git diff --check` passed. The real-server, six-player, two-round
  protocol smoke completed without paid model calls:
  `data/evaluations/reachable-routes-20260922-smoke`.
- The medium-reasoning experiment override was checked offline: parent
  medium/40,960, oracle high/900, Cerebras-only/no-fallback routing, and provider
  exclusions. This override lives in the experiment launcher; production still
  defaults to high reasoning.

These checks provide substantial coverage; they do not prove the absence of
all possible bugs.

## Changes required to finish

1. **Original simplified-tool run:** parent output allowance omitted, high
   reasoning. Repeated nested-schema mistakes and 8,192-token exhaustion blocked
   round-four mustering. Two unproductive mustering loops were interrupted.
2. **Schema recovery continuation:** added the exact current `expected_schema`
   to malformed-action feedback, explained nested action discriminators, and
   clarified fixed empty items (`[{}]` selects the fixed item; `[]` selects none).
   Explicitly requested 40,960 parent output tokens, leaving the oracle at 900.
   Baratheon's stuck mustering completed in three requests with one corrected
   submission. Lannister still repeatedly exhausted output at 8,192.
3. **Medium-reasoning continuation:** kept the same save, model, routing,
   strategic memory, schema fix and 40,960 request; changed only parent reasoning
   effort from high to medium. The oracle stayed high/900. This completed the
   remaining game in about 5 minutes 22 seconds, with 124 completed decisions and
   two failed attempts that normal retries recovered. Both remaining failures
   were Baratheon Raven decisions, in rounds nine and ten, at the same 8K ceiling.

The full process spanned approximately 28 minutes 19 seconds, including pauses
for investigation and fixes. Source/test archives and manifests record runtime
versions. Launchers and original segments:

- Original: `docs/analysis/current-harness-parallel-2026-09-20/run_game.py`;
  `data/evaluations/reachable-routes-oss-cerebras-20260922`.
- Schema recovery: [run_game.py](run_game.py);
  `data/evaluations/reachable-routes-oss-cerebras-20260922-recovery`.
- Medium continuation: [run_game_medium.py](run_game_medium.py);
  `data/evaluations/reachable-routes-oss-cerebras-20260922-medium`.

**The remote output ceiling remains unresolved.** The explicit local allowance
is implemented and tested, but five bounded live probes did not establish a
working way to exceed 8,192 on this route. Both API styles and the tested token
parameter variants still truncated. Diagnostic generation metadata identifies
Cerebras and native length stops; it does not distinguish OpenRouter parameter
translation from a Cerebras deployment restriction. Medium reasoning is a
workaround, not an output-limit fix. See
[CEREBRAS_OUTPUT_LIMIT.md](CEREBRAS_OUTPUT_LIMIT.md).

## Observed tool use and play

The models called `reachable_areas` **four times**, with successful results and
no recorded tool errors:

| House / round | Origin | Context and subsequent behavior |
| --- | --- | --- |
| Baratheon / 2 | The Reach | Queried during a march; moved to Blackwater and retained The Reach with a power token. |
| Lannister / 3 | Seagard | Queried during planning; assigned a March order there. |
| Stark / 4 | The Shivering Sea | Queried during planning; left the ship on Support. |
| Stark / 9 | The Shivering Sea | Queried again; assigned a March order. |

The Reach result included King's Landing despite insufficient current combat
strength, demonstrating the intended separation from move feasibility. The
Shivering Sea results correctly returned The Narrow Sea as the one adjacent sea.
No live call queried an empty origin or exercised a ship-transport route; those
behaviors are covered by the automated tests. Four calls are too few to establish
strategic benefit. The models used `check_neighbours` 39 times.

There were useful decisions: Baratheon preserved control when leaving The Reach,
and later captured King's Landing with a knight and supporting armies
(round-four run `d4393d7f-c510-44ed-9dbd-d059cfe6bd3c`). There were also persistent
mistakes: Stark moved its knight Winterfell → Stony Shore → Winterfell → Stony
Shore across rounds two, four and five; a round-three schema misunderstanding
had already caused it to abandon an intended return march. Baratheon's round-ten
mustering rationale said it would conserve power tokens by skipping mustering
(run `bd9004f8-a31e-4f51-a53d-e8af4b9c3a99`), although normal mustering costs no
power tokens. This run does **not** demonstrate that the models' thinking has
improved. It demonstrates successful geographic queries and more effective
schema recovery, alongside remaining strategic and interface weaknesses.

## Cumulative accounting and remaining failures

Across all segments: **158 completed decision runs, 13 failed attempts, and two
cancelled attempts**. All 13 failed runs encountered 8,192-token exhaustion;
11 preceded the medium continuation and two occurred during it. There were 94
explicit rejected-action outputs in retained transcripts, including 27 during
the medium continuation. This is not an exhaustive rejection count: cancelled
runs lose tool-result records even though their malformed calls are preserved.

Deduplicated response usage from the final database:

| Measure | Total |
| --- | ---: |
| Responses with recorded usage | 527 |
| Input tokens | 20,722,539 |
| Cached input tokens | 18,583,808 |
| Output tokens | 919,524 |
| Reasoning tokens | 854,600 |
| Recorded game cost | $7.94253165 |
| Separate five-call token diagnostics | $0.02537365 |
| Combined recorded cost | $7.96790530 |

Costs are reported response usage, not an independent billing reconciliation;
interrupted requests without returned usage cannot be priced from these traces.

Detailed evidence and unresolved issues—including long repair loops, misleading
singleton schemas, cancelled tool-output loss, and incomplete provider
attribution—are in [HARNESS_FAILURES.md](HARNESS_FAILURES.md).

## Later diagnosis: action schema may be lost before model inference

The published GPT-OSS template renders our nested `decision.anyOf` as
`decision: any`, omitting action names and recruitment fields. An offline
reproduction matches the model's recorded description of its tool schema.
This revises the earlier interpretation of the repair loops: the detailed
contract may not have been visible to the model despite valid outgoing JSON.
The provider's internal template is unobservable, so deployment attribution
remains a hypothesis. See
[the rendering investigation](../schema-rendering-2026-09-22/REPORT.md).
