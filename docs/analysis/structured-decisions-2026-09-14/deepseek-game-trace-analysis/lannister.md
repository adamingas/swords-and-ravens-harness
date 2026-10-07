# Lannister trace review

Experiment: `data/evaluations/structured-decisions-deepseek41-three-player-serial-game-morph`. Player: user `2`, agent `aef474eb-e57d-4640-b136-bfa33d68de8e`, DeepSeek v4.1 Flash. Sources: `harness.db` (`agent_runs`, `agent_events`, `strategic_memories`) and the completed `game.json` combat log. Run IDs below identify exact stored observations, reasoning, tools and accepted actions.

## Conclusion

Lannister understood the expansion objective, successfully captured two castles in round 1, and made meaningful persistent plans. Its failure was not simply absence of spatial awareness or memory. The strongest problems were missing decision-specific facts, a sudden disappearance of actual exploration in round 5, and a final action contradicting its own analysis. It finished with two castles after losing Harrenhal.

There are 43 recorded model runs: 32 completed, eight failed and three cancelled. Failures include two 300-second timeouts, two output-token-limit failures, three six-response-limit failures, and one invalid JSON final answer. These are not evidence of illegal gameplay decisions. The game was resumed with changing harness conditions, so it is not a controlled comparison of one unchanged agent.

## Tool use and persistence

The event log records 122 completed exploration tool executions, including executions inside runs that subsequently failed or were cancelled:

| Tool | All attempts | In completed runs |
|---|---:|---:|
| `check_neighbours` | 79 | 59 |
| `remember_strategy` | 22 | 17 |
| `recall_game_state` | 9 | 6 |
| `ask_rules_oracle` | 12 | 5 |

Rules-oracle internal `read_rulebook_sections` calls are excluded from this table; they are not player tool calls. Seventeen remember calls occur across sixteen completed decisions because one decision revises its pending note twice. Memory is saved after accepted actions. Final memory revision is 32, matching completed decisions; this does not mean 32 model-written plans.

Lannister explicitly used the memory tool for castle targets, unit assignments, power budgets, supply constraints, threats, card conservation and next-round contingencies. Examples:

- `e76aea0a-57d7-404c-92f7-9d99fc318ce7`: save Riverrun capture now, Harrenhal next, reach three castles this round, then threaten Seagard.
- `51a05aab-4ef8-411d-9da4-49c64d57dbd3`: stage the Lannisport knight at Searoad Marches to attack The Reach next round; fund future influence bids; use support to deter Stark at Riverrun.
- `0d599390-7d77-4a9d-8933-eab201003e9a`: replace that plan when The Reach receives Defense +1; take Blackwater's supply icons instead, and record why the earlier attack is no longer attractive.

Previous raw thoughts are removed by `current-observation-only`; the model sees the current observation, a stored model-authored plan, generated situation/objective/commitment fields, and a history index. It can retrieve previous observations, not previous reasoning, with recall. Recall helped reconstruct the bidding sequence and the preceding Harrenhal battle. There is genuine cross-call strategic continuity in rounds 1–4.

The final plan was last written in round 4 (`f0d983df-03a6-4a09-a130-f6878b6ab716`). It still says supply track 0, although round 5 supply is 6. At the start of round-5 planning (`fc64ca00-0c23-434e-9640-9283a5504878`), the model notices and corrects this discrepancy from the current state. Generated objectives remain generic, and `lessons` is empty, even though useful lessons are buried inside the free-text plan. The plan also retains an implausible suggestion to contest a Dorne neutral force, despite the inaccessible 1000-strength southern areas.

## The most serious execution pattern

All eleven completed round-5 decisions contain **zero actual exploration calls** and exactly one model request. The four exploration tools are still present in saved `tools_json`. The reasoning repeatedly announces that it will call neighbours, recall or the oracle, then the response immediately ends with action JSON. Announcing a tool call did not execute it.

This is particularly severe in the final combat decisions:

1. `a3634d21-7cae-4f69-9774-78cf826ce0da`: attacks Crackclaw Point with two knights. It treats Baratheon's remaining cards as at most strength 2 and concludes the Blade can cover the worst case, while repeatedly promising a neighbour check that never happens.
2. `20c52ad6-2011-411c-bdbd-725a74aacc97`: chooses Jaime. It becomes uncertain about Davos's ability and promises an oracle call; no call occurs.
3. `0467fff0-62fb-44e4-b118-777dd0512a56`: declines the Blade. The recorded battle is Lannister 5 versus Baratheon 7: Davos contributes strength 3, and Baratheon receives two support. The Blade would not have rescued this attack, so declining it is defensible despite confused reasoning.
4. `554b10a4-2529-4194-b3f8-9f4fc9fbffd1`: Baratheon counterattacks Harrenhal, defended by a routed knight and The Hound. Lannister explicitly reasons that using the Blade saves Harrenhal, calls that the safe choice, then outputs `{"use":false}`. The actual battle is Baratheon 3 versus Lannister 2. With +1, Lannister would have tied at 3 and won on its superior Fiefdoms position. This is a concrete, consequential reasoning/final-action contradiction.

The stored trace alone cannot establish whether provider handling of tools plus structured output, model behavior, or another request condition caused this pattern. It warrants a narrow request-level reproduction before attributing it to a lack of strategic competence.

## Confusion and missing information

**Bidding track identity is inadequately exposed.** In rounds 2 and 5, the pending decision is simply `bidding`, the state path is `clash-of-kings/bidding`, and no action guidance identifies the active track. The briefing nevertheless claims those fields identify the track. Lannister repeatedly mistakes the event field `trackerI:1` for “Iron Throne” rather than an array index. In `702c6647-31bd-41a6-be43-713a0e5d5eea`, recall helps recover that this is King's Court. In round-5 `6d7ecaf2-b6c5-48eb-87dd-7632e64ac159`, it still discusses saving power for a later King's Court bid while already bidding on that track. A plain current-track name would remove this avoidable uncertainty.

**Card descriptions are missing.** In `f5890c84-fe3c-45e2-905c-3c4180499d6a`, Lannister asks for exact Lannister card abilities. The oracle says the supplied rulebook/FAQ do not include Tywin or Cersei's printed text and include only incomplete Tyrion information. Later Lannister invents/guesses effects, including treating Cersei as a card-text canceller and speculating that Davos's bonus depends on support. The final game log confirms Davos strength 3, while the attack plan assumed a maximum of 2. This is actionable observation incompleteness.

**Wildling inspection reveals an opaque number.** In `d46d8247-729e-49b0-8d74-2036128c8d4f`, the inspected card is #4. Lannister openly says it cannot map the number to an effect, recalls the preceding state, and ultimately keeps the card on top without understanding its consequences. Include the visible card's name and effects.

**Combat state is reconstructed from fragments.** Late combat reasoning repeatedly asks which battle is current, whether the knight is routed, what support is committed, and what card abilities apply. The blade pending decision contains only the house and a Tides flag. Board pieces remain represented at their source/battle locations during intermediate resolution, so the agent struggles to reconcile the board with recent events. A current-combat summary should expose attacker, defender, battlefield, committed units, routed contribution, accepted support, revealed card effects, present totals, Blade availability and tie winner.

**Supply is mostly understood correctly.** The model consistently distinguishes actual supply track from controlled icons, knows lone units do not form armies, upgrades footmen without increasing army size, and avoids forming a third size-two army at supply 0. It verifies these details with the oracle. In round 4 it deliberately requests a useless port March to manipulate the order allocator into giving +0 to its important land March, then discards the port March because combining ships would violate supply. This is awkward tool semantics rather than a misunderstanding that the port ship can legally move.

**Map reasoning is substantially functional.** The round-1 Riverrun/Harrenhal expansion is sound; neighbours establish exact supporting areas; the round-2 counterattack correctly recognizes Golden Sound cannot support Harrenhal. It adapts to Stark taking Seagard before its own march. It does overvalue defensive safety in rounds 3–4 while Stark climbs toward seven, and its round-4 “guaranteed” Reach attack claim ignores unrevealed defensive orders and card choices. After orders reveal, it correctly abandons that attack. This supports improving uncertainty and threat assessment, not concluding it cannot read the graph.

**Early submission protocol caused uncertainty.** Round-1 `f3adce2f-9973-4e17-921f-e6b347360b51` explicitly debates whether exploration prose or its final JSON submits the action because a later submission call is promised. That historical two-stage behavior is visible in this resumed game and should not be attributed to the later single-run design.

## Ranked improvements

1. **Investigate the round-5 tool/final mismatch first.** Reproduce a case that announces a tool call but emits JSON, and the Harrenhal Blade contradiction. Check the actual request/response pathway for the provider used; do not force a minimum tool count as a substitute.
2. **Expose exact current decision facts.** Add active bid track, readable card effects, and authoritative combat breakdowns. These directly address observed confusion and the lost Harrenhal defense. Structured output already ensures parseable actions; it does not ensure the action agrees with reasoning.
3. **Persist a small model-authored handoff as part of the existing decision output.** Store current target, intended next action, conditions that would change it, resources/cards reserved, unresolved questions, and concise verified lessons. Save it only after the action is accepted. Include latest observation and this handoff on the next call. Do not append the entire accumulated reasoning or all old observations. This would avoid round-5 silence leaving a stale round-4 plan.
4. **Compute factual deltas in the harness.** Examples: supply 0→6; Stark 5→6 castles; opponent army moved Seagard→Riverrun; planned target now has Defense +1. Keep inferred intent separately labelled and dated. Replace stale factual assertions in memory rather than concatenating contradictory snapshots.
5. **Use an explicit opponent-victory threat review in planning.** Lannister recognizes Stark at six but continues optimizing safe local improvements. A short current threat summary and contingency in the handoff would help connect its local decisions to the win condition. This is a strategy aid, not evidence that any one alternate move guarantees a better result.

Model-authored persistence should be a concise plan and factual lesson summary, not a dump of private reasoning. Lannister already demonstrates that a short durable plan can carry a multi-round objective. The immediate gap is keeping that plan current and ensuring planned exploration is actually executed.
