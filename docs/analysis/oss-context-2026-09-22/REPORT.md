# OSS 120B context investigation

Worktree: `.worktrees/oss-context`, branch `codex/oss-context`, based on
`c5a71ba`. The root checkout's uncommitted changes were not copied or modified.
`.env` was copied privately (mode 0600), and rules data was copied locally.

## Final results

The tuned three-house game completed normally: **Stark won with seven castles
in round six**. The six-house coverage run completed three rounds and was
intentionally stopped during round-four Westeros mustering. It has no winner.
All seats used OSS 120B/Groq/high. No actions were chosen by the operator.

The final v4 runtime completed **84 new decisions with zero failed parent
runs**: 42 in each game. One in-flight six-house run was cancelled when closing
the pilot. Seven nonfatal exploration-tool errors still occurred in those 84
completed decisions, mainly inside the rules oracle; zero failed runs does not
mean every tool call succeeded.

| Experiment (including its saved continuation history) | Completed decisions | Failed runs | Operator cancellations | End state |
| --- | ---: | ---: | ---: | --- |
| Compatible full-context baseline, 3 houses | 46 | 10 | 0 | Stopped by provider validation in round 4 |
| Tuned game, 3 houses | 112 | 13 | 2 | Stark wins in round 6 |
| Tuned coverage run, 6 houses | 99 | 2 | 7 | Deliberately stopped at start of round 4 |

The cumulative failures above include earlier revisions; the 84-decision final
runtime slice is a subset, not an additional set of games. Resumed database
copies must not be added together. Recorded response costs for the two tuned
runs are approximately **$0.923** and **$0.755** respectively, including retained
failed/interrupted work with returned usage. Calls cancelled before usage is
returned may incur additional provider cost.

The full-context baseline placed eight open-sea power orders among 40 assigned
orders (12 planning decisions). The completed tuned three-house game placed
zero among 70 orders (18 planning decisions). The six-house pilot placed two
among 63 orders (18 planning decisions); both were explicitly described as
zero-income fillers. This is a useful diagnostic contrast, not a controlled
estimate of strategic strength.

The winning Stark move (`37a171ec-2f71-49b7-923a-819a5662d361`) combined a siege
engine, knight and footman to take Riverrun while leaving a control token at
Seagard. The handoff explicitly connected the retained castle and the new
capture to seven points. However, the losing Lannister trace still described
The Hound's towers as harming the opponent and discussed future rounds after
an immediate loss. The harness changes do not eliminate all strategic or rules
misconceptions.

Validation: **293 tests passed**, Ruff and `git diff --check` passed, and the
final real-server six-player two-round protocol smoke passed. The matched
opening context is **77.2% smaller**, excluding tool schemas. The evidence does
**not** establish an across-house win-rate improvement.

## Configuration and evidence

All live model seats use `openai/gpt-oss-120b` through OpenRouter, pinned to
**Groq only**, with fallback disabled and the configured provider blocklist
preserved. Gameplay uses **high** reasoning and **32,768** maximum output tokens.
The final rules oracle also uses high reasoning, with a separate **16,384**
allowance. No gameplay actions were chosen by the experiment operator.

Groq's [model documentation](https://console.groq.com/docs/model/openai/gpt-oss-120b)
advertises 65,536 maximum output tokens. Baseline traces actually include
responses exceeding 8,192 tokens; this is not just a catalog assumption.
Returned provider errors identify Groq, and manifests record Groq-only routing.

The first comparison uses native three-player self-play, seed 102, with the
normal seven-castle/ten-round victory rules. The baseline is the original
runtime with the minimal nested-singleton schema compatibility correction.
Every house in an experiment uses the same instructions. Source archives,
player snapshots, actions, complete recorded model responses, request inputs,
usage, failures and provenance remain under `data/evaluations/`.

The experiments are diagnostic. Self-play outcomes and a small number of
scenarios cannot establish a win-rate improvement. A shorter prompt alone is
not proof of stronger play. Interrupted and failed attempts must remain in
cost/reliability accounting; resumed database copies must not be double-counted.

## Trace findings and resulting changes

1. **The schema sometimes hid the move itself.** In the unmodified Groq run,
   Stark's Shivering Sea march had one legal destination and one unit. The
   schema reduced the move to an empty object. Groq rejected this schema before
   inference (`d0f53787-1e2f-4906-98a4-641fa416ba4a`). Earlier Cerebras traces
   also showed models discarding useful orders during attempts to repair these
   shapes. Nested destination and unit fields now remain explicit, even with
   one option. Fixed top-level context is still bound and explained by the
   briefing. Passing remains an explicit empty move list.

2. **Long context did not prevent elementary rule errors.** Baseline Baratheon
   run `ac084ed3-fc58-4104-80af-4e5af0f01329` explicitly planned to earn one power
   token at Shipbreaker Bay. The accepted order was open-sea Consolidate Power,
   which earns nothing. The baseline accumulated eight such orders by round
   four. Other traces confused stronghold capacity with scoring, imagined card
   abilities, or treated a losing final score as a reason to stop improving.
   The common strategy instructions now emphasize concrete targets, net castle
   gains, transport sequencing, free mustering, actual supply slots, full combat
   totals and final-round victory below seven.

3. **Important combat facts were missing from the model view.** The observation
   exposed the leaf decision but omitted its parent combat state. It now includes
   the player-visible attacker/defender, participating unit IDs, battlefield,
   declared support, revealed card data/modifiers and server combat statistics.
   Available cards of the participating houses include their printed ability
   text. No hidden opponent choice is inferred, and no administrative save is
   used to construct this information. The briefing clarifies that requesting
   a later Blade question does not itself spend the Blade.

4. **Mustering could be malformed or silently weakened.** The baseline stopped
   at round-four mustering after provider validation failures involving nested
   fields such as `upgrade_from_footmen` and misplaced `strategic_handoff`.
   The new schema offers origin-specific exact recruitment entries, e.g.
   `winterfell/knight/upgrade`. Choices retain source/destination/type/upgrade
   relationships and individual affordability. Local validation checks the
   complete plan's points, available pieces, port capacity and Supply before
   sending it. Invalid combinations are rejected for correction rather than
   silently trimming the player's requested recruitment.

5. **The oracle's 900-token cap became a bottleneck.** The first compact-context
   attempt repeatedly exhausted the oracle's high-reasoning output allowance.
   By the round-two bidding decisions, the model was repeatedly asking the
   same rule question and sometimes guessing after oracle failures. This
   attempt was deliberately interrupted and retained. The allowance is now
   16,384, independent of the parent allowance; high reasoning is retained.
   The concise rules reference also explicitly distinguishes Wildling victory
   penalties from the highest-bid reward after a Night's Watch victory.

6. **Redundant representations competed with the current state.** Models received
   resources/cards/orders repeatedly, automatic summaries, a latest plan, up to
   twelve old plans and twelve history entries, plus a roughly 20,000-word
   rulebook. The model now gets one scoreboard/card location, explicit board
   control and terrain/scoring, latest plan/lessons, four history entries and
   relevant events. The full history remains available through recall. Base
   games with the oracle available use a concise rules reference; other cases
   keep the full rules. The dashboard and canonical stored snapshots/history
   retain their detailed representations.

## Provider schema constraints observed

Groq rejected `uniqueItems` and rejected a recruitment `anyOf` with several
possible discriminator properties. Those experimental forms were discarded.
Duplicate-unit checks remain in runtime validation. The final recruitment
schema uses a single origin discriminator and string choices. A live Groq
probe accepted it and returned schema-valid recruitment arguments; see
`data/evaluations/prompt-comparison/groq-mustering-schema-probe.json`.
JSON Schema alone does not express every combined move/recruitment constraint;
validation and the game server remain necessary.

## Context size

On the same opening snapshot (baseline run
`d6927792-0c49-4145-b7f2-f248e5ab6494`), the final model context measured with
`o200k_base`, excluding tool schemas, was:

| Component | Baseline | Tuned final |
| --- | ---: | ---: |
| Instructions including map | 28,163 | 4,516 |
| Observation and briefing | 4,380 | 2,896 |
| Total | 32,543 | 7,412 |

That is a **77.2% reduction** in this snapshot. Counts are local tokenizer
estimates, not a claim about every provider request. Exploration, oracle calls
and later board complexity change actual request usage.

Reproduce without provider requests:

```sh
uv run python docs/analysis/oss-context-2026-09-22/compare_context.py \
  --database data/evaluations/oss-context-baseline-ready-102/harness.db \
  --output data/evaluations/context-comparison-final
```

## Paired final-round replay: mixed evidence

A saved Stark round-ten Mustering decision originally skipped all recruitment
(run `56ae9286-fcc1-4ec9-bbec-a7335ccde399` in the root checkout's
`reachable-routes-oss-cerebras-20260922-medium` evaluation). We replayed that
same player snapshot and private memory using both contexts on **Groq/high**.
The replay used a local action sink and pre-submit validation, not a live game
server; it does not test server acceptance or the eventual outcome.

Both contexts mustered, including an upgrade. The tuned action used all four
available points and constructed transport/support plans, but its handoff still
confused supporting the attacking origin with supporting the battlefield and
imagined that a player could defend a neutral garrison. The original skip was
not reproduced by the Groq baseline, so this pair does **not** demonstrate that
instruction tuning cured the skip.

| Context | Requests | Input tokens | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 1 | 36,383 | 9,288 | 45,671 |
| Tuned v2 | 2 | 34,930 | 21,949 | 56,879 |

Smaller context did not reduce total tokens in this case. Both replay records,
including full responses and exact actions, are in
`replay-final-muster-baseline/replay.json` and
`replay-final-muster-tuned/replay.json`.

## Final trace-driven revision

The final revision also includes `castlePoints` in geographic route results and
explicitly tells every house to use it for scoring targets. The common support
instruction names the battlefield as the required adjacent area. Empty-origin
mustering decisions expose only the skip action.

Provider `tool_choice` is now `auto`. An accepted `submit_action` is still the
only completion condition. This allows the existing transcript-preserving
reminder to recover text-only responses which Groq otherwise rejects before
returning them. Three text-only completions fail with trace/usage retained;
it is not an unbounded prose loop. Tests exercise successful recovery and
bounded failure. High reasoning and output allowances are unchanged.

The v2 games were deliberately interrupted to apply this revision. Final runs
are labelled continuations with the source manifest and previous assignment
hashes retained, rather than silently pretending the runtime never changed.
The first v3 launch attempts failed the unchanged-prompt assignment check
before any new model calls; the diagnostic continuation launcher now explicitly
records the prompt-hash change while requiring all seats/models to match.

The six-house v2 opening also included one Martell open-sea Consolidate Power
order (`a4838216-4453-48c1-8d9f-5dc8ef49dda5`). Its handoff explicitly said it
would earn nothing and treated it as an order filler. This is distinct from the
baseline's belief that the sea order generates power; the metric alone does
not prove a rules misconception or strategic loss.

### Timing and argument placement follow-up

A further replay on the v3 context skipped final-round recruitment, explicitly
claiming that all combats had already happened. The source was actually
**Westeros** mustering. The final observation now names `game.roundStage`, and
mustering briefings explicitly distinguish pre-planning Westeros recruitment
from post-march Consolidate Power recruitment. This wording is shared by houses.

The timing-only replay then failed at the provider because the model placed
`strategic_handoff` inside `decision` instead of at the schema's outer level.
The final schema groups the handoff with the selected action's other fields
inside `decision` for multi-action choices. Single-action schemas keep one
flat payload. A separate live raid failure involving the nullable target was
addressed by using `raid_target` string choices plus explicit `discard`, decoded
to protocol null internally. The continued six-house game passed that raid.

| Final-round follow-up | Requests | Input tokens | Output tokens | Result |
| --- | ---: | ---: | ---: | --- |
| v3, before explicit timing | 1 | 11,150 | 2,681 | Skipped under the false belief combat was over |
| v4, explicit timing and grouped handoff | 1 | 11,512 | 18,768 | Mustered siege engine, ship and upgrade |

The v4 handoff now plans an attack during the upcoming action phase, but still
incorrectly includes Shivering Sea support for a Crackclaw Point battle.
These individual stochastic samples illustrate a corrected timing explanation;
they do not establish a statistical improvement. The baseline also mustered in
its earlier paired replay. All attempts, including the failed timing-only call,
are retained in `replay-final-muster-final`, `replay-final-muster-timing`, and
`replay-final-muster-v4` respectively.

## Remaining weaknesses

- Earlier Groq runs returned provider errors: required tool not called, an
  invented `json` tool, and malformed arguments. The automatic-tool setting
  removes the forced-tool rejection path, but invented tools and malformed
  arguments can still stop games after the runner's retry allowance. Same-save restarts retain failures in the database
  and are recorded as separate manifest segments.
- The tuned model still sometimes calls Castle Black a scoring castle despite
  its explicit zero-point board entry, or plans support based on adjacency to
  the attacking origin. Accurate supplied facts are necessary but do not ensure
  the model uses them correctly.
- The larger oracle allowance removes the observed 900-token bottleneck, but
  repeated excerpt reads and nonexistent tool names can still exhaust its
  three-turn limit. Do not interpret every tool failure as a gameplay violation.
- These experiments do not establish stronger play or higher win rate across
  houses. A larger paired-seed evaluation against fixed opponents is still
  needed for that claim.

## Validation and artifacts

The final runtime passed **293 tests**. Ruff and
`git diff --check` passed. A real-server six-player, two-round protocol smoke
passed again on the final runtime (`oss-context-v4-smoke`). Regression coverage includes identical shared instructions across all
six houses, player-visible combat context, explicit control/empty/blocked areas,
singleton moves, impossible recruitment combinations, and rejection of combined
point/Supply overflow without partial submission, distinct mustering timing,
explicit raid discard decoding, and bounded text-completion recovery.

Artifact directories:

- `oss-context-baseline-102`: unmodified baseline, stopped by the empty-move schema.
- `oss-context-baseline-fixed-102`: baseline with nested fields retained; stopped
  by an unsupported schema keyword tested during this investigation.
- `oss-context-baseline-ready-102`: continued baseline after removing that keyword;
  includes the preceding fixed-baseline traces and all resumed segments. Stopped
  in round four with 46 completed decisions and 10 failed runs.
- `oss-context-tuned-102`: first compact-context attempt, intentionally interrupted
  after identifying oracle output exhaustion.
- `oss-context-tuned-v2-102`: fresh game after the oracle and explicit-board fixes.
- `oss-context-final-smoke`, `oss-context-v3-smoke`, and `oss-context-v4-smoke`: real-server protocol smokes.
- `oss-context-final-102` and `oss-context-final-six-103`: v3 continuations.
- `oss-context-v4-102`: completed three-house game, including retained earlier revisions.
- `oss-context-v4-six-103`: deliberately interrupted six-house coverage run, including earlier revisions.
- `oss-context-runtime`: runtime source archives and test logs.
- `context-comparison-final`: before/after prompt texts and size measurements.

Run a new complete game:

```sh
uv run python docs/analysis/oss-context-2026-09-22/run_game.py \
  --players 3 --random-seed 102 --game-port 5312 \
  --output data/evaluations/my-oss-context-game
```

Use `--players 6` for all houses. `--resume` requires matching provenance;
`--resume-from` creates an explicitly labelled continuation in a new directory.
Use `audit.py DIRECTORY...` to regenerate trace summaries without provider calls.
