# Baratheon trace review

Source: `data/evaluations/structured-decisions-deepseek41-three-player-serial-game-morph/harness.db`; agent `32a13e26-7a06-4004-b0eb-2e16f21c2e9a`, seat 1, `deepseek/deepseek-v4.1-flash`. Reviewed the 62 run records, stored successful response/reasoning transcripts, tool outputs, observations, memory snapshots and action arguments, plus tool-event records for unsuccessful attempts. This is one game resumed under changing harness/provider settings, not a controlled comparison.

## Conclusion

Baratheon understood the victory objective and could carry out coherent expansion. It captured Crackclaw Point and The Reach in round 1, and executed a three-decision muster → orders → siege-engine attack on King's Landing in round 3. Its decisive weakness was retaining and executing dependencies between decisions while correctly considering opponents' next moves.

The clearest failure came in round 5: planning intended to capture The Narrow Sea first, then use it for an attack on Stark. At march resolution it instead emptied Crackclaw Point to attack Harrenhal before contesting the sea. Stark, already at six castles, immediately used its still-intact sea transport to capture empty Crackclaw Point and win. The model knew that route in round 4. It failed to apply it at the critical moment.

There was substantial rules and state confusion too. More tokens did not automatically resolve it: the final planning decision used 41,028 reasoning tokens, and the losing march used 29,494, both without an actual exploration call.

## What is already persistent

The harness does not carry the entire previous reasoning transcript into each new decision. The run context records `historyMode: current-observation-only`; previous session messages are removed from effective input. New observations include `strategicMemory`, a short `historyIndex`, and access to `recall_game_state`.

Baratheon did use durable memory extensively. Saved successful transcripts contain:

| Tool | Calls in successful transcripts | Completed tool events including unsuccessful attempts |
|---|---:|---:|
| `check_neighbours` | 58 | 90 |
| `remember_strategy` | 21 | 34 |
| `ask_rules_oracle` | 13 | 23 |
| `recall_game_state` | 5 | 17 |

The 21 successful memory writes contain real plans, threats, card budgets, intended future orders, and sometimes specific unit IDs. They are not just generic objectives. For example, the round 3 plan to upgrade a siege engine, support it from Crackclaw and capture King's Landing is carried through all three relevant decisions.

However, only `modelPlan` is model-authored. The separate `objectives` remain three generic harness defaults; `opponentModels` are generated score summaries, `commitments` are truncated recent action JSON, and `lessons` remains empty. A memory revision is generated after each accepted action, so revision 30 does **not** mean 30 model-authored plan updates. The situation assessment uses the pre-action observation and the action log records an attempt, not its eventual battle outcome.

All eight completed round 5 decisions have zero actual exploration calls. Their saved schemas still expose the tools, and their reasoning repeatedly proposes calling them. The final `modelPlan` consequently remains the round 4 note throughout round 5, while generated memory fields continue updating. This is visible and important; the traces alone do not establish whether provider handling of tools plus structured output, model behavior, or some other request-level change caused the abrupt cessation.

## The decisive sequence

1. **Round 4, consolidation — `5f200116-dbb3-40bc-9515-dab0104121fa`.** Baratheon identifies the precise threat: Stark can transport from The Eyrie through The Narrow Sea into Crackclaw Point. It saves: “CRISIS: Stark at 6 VP … Round 5 priorities: defend Crackclaw Point.”
2. **Round 5, planning — `97b4d9e2-f276-4319-b754-500428d8fc5b`.** It reasons about taking The Narrow Sea with three ships, cutting Stark's transport, then using the Crackclaw knight to attack White Harbor. It places March +0 on Shipbreaker Bay and March −1 on Crackclaw. It says Crackclaw is safe after the sea is cut. It makes no `remember_strategy` call, so the plan and required move order do not persist into later decisions.
3. **Round 5, defence — `44696c62-9cec-48e7-a2bb-50ec44401060`.** Lannister attacks Crackclaw. Baratheon plays Davos and keeps the area. Stark's subsequent march threat remains.
4. **Round 5, march — `5ac046a9-2f2e-4932-966b-6c6d427417d3`.** The current observation explicitly shows Stark's Eyrie March −1, its Narrow Sea ship, and Stark at six castles. Baratheon recognizes that Stark is one castle from victory, but considers its next castle mainly as a *next-round* problem. It says the order of its naval and land marches “doesn't matter much,” because their immediate battles do not interact. It attacks Harrenhal with its only Crackclaw knight and leaves a power token. This preserves ownership but supplies no defence. It ends by proposing neighbour checks, then emits final JSON without making them.
5. **Round 5, Harrenhal battle — `0f9b2a50-b487-4fb9-97e8-0e9cbf56ab76`.** It plays Brienne and captures Harrenhal. Stark then transports the Eyrie footman into undefended Crackclaw for the seventh castle. Baratheon's castle gain is immediately offset, and the game ends before its naval march.

Persisting the round 5 plan would have preserved the intended ordering, but it is not proof the model would have followed it. A more useful retained item would have been the explicit dependency: **Do not vacate Crackclaw until Stark's Narrow Sea transport has been removed; otherwise Eyrie's active march wins immediately.**

## Other confusion and mistakes

### Combat state is hard to reconstruct

In `0f9b2a50...`, the model repeatedly questions which battle is happening, whether events are chronological or reversed, and why its attacking knight is still shown at the origin. The observation has the current card-choice state and recent events from successive combats, but no concise authoritative combat record identifying attacker, defender, embattled area, attacking army, declared supports and current strength totals. The model spends much of the response trying to reconstruct this from event fragments.

There is similar reconstruction in round 2's defensive card selection, `28a8eb1e-7ca9-4adb-ade8-daab6cd6cc08`, where it uses two history recalls before selecting Renly. Full prior board retention is an expensive workaround for information the live combat state can supply directly.

### Card abilities are identifiers, not rules text

In `44696c62...`, Baratheon invents a possible Davos rule: +1 strength when supported. It repeatedly proposes asking the oracle for the actual text but never calls it. The engine's actual condition in `SerDavosSeaworthHouseCardAbility.ts` is that the house's strength-4 card has been used. Davos happens to receive his bonus here because Stannis was previously played. The choice succeeds despite the wrong explanation; this is not evidence of rule mastery.

### Spatial conclusions can contradict checked facts

Round 1 correctly uses Shipbreaker Bay transport from Dragonstone to Crackclaw. Nevertheless, round 3 planning (`92aebd65-98c3-4116-9fd0-769422347512`) saves “dragonstone knight stuck (no transport)” while two friendly ships occupy Shipbreaker Bay. In the same trace it briefly rediscovers the valid transport before returning to the false summary. Consolidating power can still be a reasonable action, but “no transport” is not a valid reason.

The rules oracle also answers generic garrison questions while Baratheon is assessing neutral King's Landing (`73c5d690...`, `92aebd65...`). The model blends home-garrison and neutral-force procedures, considers house cards and third-party support, and at one point invents Harrenhal–King's Landing adjacency despite the neighbour output not containing Harrenhal. Its actual siege-engine attack had enough strength and succeeded. The confusion did not invalidate that particular move, but it inflated the analysis and risked an incorrect combat calculation.

### Supply is mostly understood; resource planning is inconsistent

Baratheon generally distinguishes supply-track level from currently controlled icons, understands singles do not count as armies, and uses upgrades to avoid extra army slots. Both successful mustering actions report zero supply-unsafe recruitments omitted by the harness. There is no evidence of systematic inability to obey supply.

However, its round 4 note says “NEVER choose Supply” because a supply update would help opponents more at that moment. That absolute instruction persists even after the circumstances change. Its round 4 planning spends the only star on Dragonstone consolidation intending to muster, then consolidation changes to power because the fleet occupies the large army slot and the model underrates Dragonstone reinforcement routes. A change of plan can be rational, but the claimed supply/route facts were already available during order placement.

### Goals are understood but threats are not propagated

Baratheon repeatedly counts castle areas correctly, recognizes the immediate seven-castle victory, preserves control with tokens, and identifies Stark as the leader. The final mistake is therefore not failure to understand the objective. It is failure to connect the objective to an enemy legal move enabled by its own action and by the order of remaining marches.

## Failures and submission behavior

There are 30 completed actions, 28 failed attempts and 4 cancellations. Failure records break down into 10 output-token truncations, 7 invalid-final-action parsing failures, 4 API timeouts, 4 SDK `Max turns (6) exceeded`, 2 HTTP 429s and 1 connection error. These are distinct from illegal gameplay: successful mustering/march actions reviewed show no safety-filter omissions.

Early rounds include the earlier two-stage exploration/final-submission prompt. Later rounds use a single structured final answer. It would be incorrect to interpret early “submission comes separately” prose as confusion under the final harness. Conversely, late round 5 reasoning that promises a tool call but returns an action is a real unfulfilled exploration intention.

Failed attempts often have empty `response_json` despite recorded usage and tool lifecycle events. Their executed tool counts are recoverable, but their complete arguments/results/thinking are not preserved in the same way as successful runs. The database session transcript contains the same 97 successful exploration calls, not the additional unsuccessful-attempt calls. Those failures cannot be fully interpreted as strategy traces.

## Highest-value improvements

1. **Persist a compact current-round plan and dependencies in the same final structured response as the action.** Save model-authored targets, sequence, prerequisites, threats, reasons for abandoning the previous plan, and next decision to revisit. Commit the note only with an accepted action. No additional LLM call is needed. This would preserve the naval-first intention even when the model does not call the optional memory tool.
2. **Supply explicit active-combat facts and human-readable card abilities.** The model should not infer combat identity or Davos's rule from event fragments and an ability identifier. Include the mechanical strength breakdown and legal supporters, while keeping unknown enemy card selection hidden.
3. **Make transport reachability and immediate enemy threats available as structured derived facts.** Direct neighbours are helpful, but this loss turns on a nonadjacent sea-transport route. In the current-state briefing, highlight a house at six castles and visible marches that can reach the agent's castles. A lightweight action preview could expose which castles become undefended and whose remaining march can reach them; it need not enumerate every action.
4. **Persist selected deltas and conclusions, not every observation or full reasoning block.** Keep the latest board; retain model-authored strategic conclusions plus mechanical deltas such as “Stark changed Eyrie's defence order to March; Narrow Sea transport remains intact.” Label hypotheses, expire conditional advice like “never choose Supply,” and let current state override notebook facts.
5. **Investigate round 5's tool-call disappearance with actual requests before adding prompt pressure.** The briefing already encourages exploration and even says to check the battlefield before attacks. Required tool quotas would not address the underlying uncertainty about why intentions never became calls. A minimal provider integration probe for tools and structured output is more informative.

Recommended memory example for the losing position:

> Stark has six castles and Eyrie has an active March. Its Narrow Sea ship permits transport to Crackclaw. Keep the Crackclaw knight in place until that route is cut. Resolve the Shipbreaker Bay march first. If the naval attack fails or is no longer winning, reassess and retain Crackclaw's defender. Harrenhal expansion is secondary to preventing immediate defeat.

This is the kind of persistence missing at the decisive moment. Replaying tens of thousands of unstructured reasoning tokens would also replay uncertainty, contradictory alternatives and invented rules.

## Accepted-decision index

Run IDs are unambiguous prefixes of `agent_runs.id`; all 30 accepted decisions are included.

| Round | Run | Action and observation |
|---|---|---|
| 1 | `853674d0` | Orders for two free-castle captures and fleet support; saves plan. |
| 1 | `7bc3dcab` | Dragonstone army transports to Crackclaw; saves next march. |
| 1 | `1796f87b` | Kingswood footman captures The Reach; keeps Kingswood token. |
| 2 | `3589547e` | Bids 2 for Iron Throne; oracle and recall used. |
| 2 | `7d20b863` | Places Stark above Lannister in tied throne positions. |
| 2 | `b1a780a1` | Bids 1 on Fiefdoms; two recalls, oracle, map and memory. |
| 2 | `97365728` | Places Baratheon above Lannister in Fiefdoms tie. |
| 2 | `2b3ff70e` | Bids 1 on King's Court; asks about three-player stars. |
| 2 | `be015f65` | Places Stark above Lannister in King's Court tie. |
| 2 | `cc6be0d8` | Assigns tied-lowest wildling penalty to Lannister. |
| 2 | `a3031db8` | Orders Crackclaw starred march toward Harrenhal. |
| 2 | `8e0cca34` | Knight attacks Harrenhal; footman retains Crackclaw. |
| 2 | `727dcd7b` | Stannis for Harrenhal attack; anticipates counterattack. |
| 2 | `28a8eb1e` | Renly for Harrenhal defence; reconstructs battle using recalls. |
| 3 | `73c5d690` | Siege/knight upgrades and Dragonstone knight; sets King's Landing plan. |
| 3 | `92aebd65` | Orders execute siege/support plan; wrong Dragonstone immobility note. |
| 3 | `a096235b` | Captures King's Landing, keeps The Reach token. |
| 4 | `e85ee65f` | Chooses Mustering rather than Supply; conditional reasoning made absolute. |
| 4 | `bdb2859c` | Five recruitments, supply-safe; grows fleet and singles. |
| 4 | `710e5c89` | Defensive/power orders plus Mountains march; intended Dragonstone muster. |
| 4 | `0b001027` | Footman captures Mountains; knight stays at Crackclaw. |
| 4 | `5f200116` | Chooses power over muster; saves accurate Stark transport warning. |
| 5 | `1f6cea90` | Iron Throne bid 0, no exploration. |
| 5 | `90139f2c` | Breaks tie above Stark, no exploration. |
| 5 | `d2e3301f` | Fiefdoms bid 0, no exploration. |
| 5 | `22271f8d` | King's Court bid 3, no exploration. |
| 5 | `97b4d9e2` | Naval-first planning idea; no exploration or saved new plan. |
| 5 | `44696c62` | Defends Crackclaw with Davos; wrong ability explanation. |
| 5 | `5ac046a9` | Empties Crackclaw for Harrenhal before naval move; decisive loss. |
| 5 | `0f9b2a50` | Brienne takes Harrenhal; combat reconstruction confusion. |
