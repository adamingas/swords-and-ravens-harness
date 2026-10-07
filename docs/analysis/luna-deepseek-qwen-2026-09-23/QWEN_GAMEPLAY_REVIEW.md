# Why Qwen finished with one castle

Qwen/Stark lost both battles it fought against Luna/Baratheon. DeepSeek/Lannister also defeated it twice and occupied White Harbor without a battle. The most convincing explanations are failures to apply turn order, account for immediate enemy threats, and update combat assumptions after the influence tracks changed. Qwen also spent long periods reconsidering plans without resolving these errors.

This is an analysis of this one fixed-seat game, not a general ranking of the models. I checked the authoritative game log, accepted actions, recorded observations, tool results, and provider-returned reasoning. Counterfactual alternatives below were not replayed and are not claims of guaranteed victory. No harness, prompt, schema or provider was changed during this review.

## Battle record

Scores below are total combat strength, not castle counts.

| Round | Location | Opponent | Qwen's card | Result |
| --- | --- | --- | --- | --- |
| 3 | Crackclaw Point | Luna attacking | Eddard Stark | Lost 7–9; knight retreated |
| 3 | Moat Cailin | DeepSeek attacking | Roose Bolton | Lost 4–6; wounded knight and footman destroyed |
| 5 | Crackclaw Point | Luna attacking | Eddard Stark | Lost 6–6 on Fiefdoms tiebreak; footman retreated; Patchface discarded Robb |
| 6 | Winterfell | DeepSeek attacking | Roose Bolton | Lost 8–9; knight retreated |
| 7 | White Harbor | Qwen attacking DeepSeek | Catelyn Stark | Won 3–3 on Fiefdoms tiebreak |

Qwen's record was **one win, four losses**. It made only one attack that resulted in a player-versus-player battle. It also took undefended Crackclaw Point twice, in rounds two and four. In round four DeepSeek occupied the White Harbor Qwen had vacated; that was not a battle.

Its castle trajectory was: 2 initially → 3 in round one → 4 in round two → 2 after round three → briefly 3 then 2 in round four → 1 in round five → 0 in round six → 1 in round seven and at game end.

## 1. It planned expansion as if opponents would wait for it

Round-three planning run `298ec638-3825-4c95-9ecc-7a5c0755f196` acknowledged that Stark was **last on the Iron Throne track**. Nevertheless, it planned to move its knight out of Crackclaw Point and its footman out of Moat Cailin, leaving control tokens behind, while dismissing the adjacent enemy armies:

> “None of these are threatening my positions directly.”

Its next sentences explicitly identified Lannister's footman and knight at Seagard, adjacent to Moat Cailin, and Baratheon's footman and knight at King's Landing, adjacent to Crackclaw Point. It reasoned that Crackclaw was safe because it would move its knight out. That failed to account for Baratheon and Lannister acting before Stark.

The actual order was Luna's attack at Crackclaw, then DeepSeek's attack at Moat Cailin, before Qwen could execute either planned escape. Both Stark march orders were removed with the lost positions. Only its Mountains of the Moon march survived.

Defense orders were prohibited that round, so simply saying “place defense” would be an invalid correction. The underlying mistake was the threat assessment and action sequencing. A sound plan needed to consider enemy attacks before Stark's first march and preserve forces accordingly, rather than assume uncontested expansion.

## 2. It retreated a wounded knight directly into the next attack

Retreat run `42b146c7-6bdc-41e2-849d-a7a46a281745` selected Moat Cailin after the Crackclaw defeat. Its neighbour-tool result explicitly showed **a Lannister footman and knight at Seagard with March +1**. White Harbor and several other locations were offered as legal retreat destinations.

Qwen understood that the retreating knight would be routed and have zero combat strength until cleanup. Yet it called Moat Cailin the safest consolidation point and its submitted handoff described a “strong 3-strength army.” That description counted the knight's future recovered strength as if it protected the position now.

DeepSeek attacked Moat Cailin immediately. The combat log records the knight under `woundedUnits`, contributing zero strength. After the defeat, it was automatically destroyed for already being wounded; the footman was also killed.

This is a high-confidence avoidable exposure of a valuable unit. Retreating elsewhere would not guarantee a winning game, but the visible board gave Qwen ample reason not to call Moat Cailin safe. It focused on distance from Luna while neglecting DeepSeek's next move.

## 3. It invented a Blade bonus and the wrong tiebreak in round five

This is the clearest calculation failure. Round-five Clash of Kings had changed Fiefdoms to **Baratheon, Stark, Lannister**. The saved planning and combat observations both show that order. Baratheon therefore held the Blade and won combat ties against Stark.

Qwen nevertheless continued to claim it was first on Fiefdoms in planning run `8a598690-6fd0-4601-9fb2-ca88d099684d` and combat run `a0926514-b48f-4c66-80e2-ebdf5d6b68bb`.

At Crackclaw Point:

- Luna's strength before a house card was **6**: two footmen, one supporting footman, and two supporting ships with Support +1.
- Qwen's strength before a house card was **2**: one footman and one supporting ship.
- Eddard added four, giving Qwen **6**, with no Blade available to it.
- Luna's weakest available card, Patchface, added zero. Luna still won **6–6** on Fiefdoms.

Qwen instead evaluated “Eddard + Valyrian Steel Blade” as seven, claimed it won ties, and assigned itself a **40% chance** to keep Crackclaw. That percentage also assumed the opponent's five cards were equally likely, without evidence for that distribution. With the actual ownership and support, none of Qwen's available cards could win this combat against the available Baratheon choices.

Qwen submitted `force_valyrian_blade_decision: true`. The offered schema described this as asking for a Blade decision even if the server could skip it; it did not confer ownership or directly apply a bonus. The server correctly recorded zero Blade bonus for Stark. This was a legal, schema-valid action chosen under false assumptions, not a provider schema failure.

Luna's contemporaneous handoff in run `99a63f70-78d3-4b93-96ce-1bd6745668f9` correctly states:

> “Even against Eddard (4), the final tie at 6 is ours because Baratheon leads Fiefdoms.”

Luna deliberately conserved its strong cards, played Patchface, and then discarded Qwen's Robb in run `60f9ff64-b798-4221-8983-6a5f9949f583`. This was an accurately calculated exploitation of Qwen's position.

A casualty-protection card such as Rodrick or Blackfish would have been a reasonable way to accept an unavoidable loss without spending Eddard. Patchface could still discard another card, so this is not a claim that saving Eddard guaranteed Winterfell's survival.

## 4. It repeatedly deferred rebuilding and initiative

After the initial overextension, Qwen's completed round-five and round-six plans contained **no march orders**. It kept defending Winterfell with one knight, left its ship in the Narrow Sea, and allocated other orders to support, defense or collecting power.

It repeatedly wrote that it would muster next round and eventually take the Eyrie. But a future Westeros mustering opportunity was not guaranteed, and those plans did not assemble the force needed for the Eyrie. In round six it lost its last castle; the next round's actual Mustering event consequently produced **zero recruits** for Stark.

Some defensive caution was justified by its weak position. I would not label every zero-march round a mistake or assert that replacing Winterfell's defense with recruitment was safe. The supported criticism is that Qwen had no effective recovery sequence: it repeatedly postponed the ship repositioning and force concentration its own analysis said it needed, while losing recruitment locations.

The round-four move from White Harbor to undefended Crackclaw was also not an accidental abandonment: Qwen explicitly anticipated losing White Harbor to Lannister and preferred saving the footman elsewhere. The problem was the sustainability of the resulting position, not ignorance of that immediate tradeoff.

## 5. Rules and map assumptions kept changing inside the analysis

Examples that matter when interpreting its reasoning:

- In round-three combat reasoning it calculated that two units plus Eddard could defeat the Eyrie's neutral strength six. Neutral forces do **not** use house cards or the Blade; the original runtime's supplied `rules.md`, lines 970–984, states this explicitly. This was an unexecuted hypothetical, not an illegal move that the harness accepted. Later reasoning sometimes assessed the Eyrie's strength without cards correctly, so the evidence is inconsistent understanding rather than one permanently held misconception.
- It repeatedly initially counted Narrow Sea support for Winterfell, although those areas are not adjacent. It eventually corrected this in round-five planning. That correction should not be misreported as an executed support error, but it illustrates the effort spent rediscovering the same facts.
- It asked for four march preferences in round three and wrote that all four were assigned. The accepted action's `applied_orders` actually contained three marches and a support order on the ship. This is a mismatch between its intended plan and its handoff, not a schema violation; the fallback support was helpful in the battles.

## 6. More deliberation did not reliably produce better decisions

The round-four planning decision `7d0b6f1d-b1af-4e79-b04c-afe08dbe6385` took **63.95 minutes**, made **31 function calls including its one submission**, and its recorded reasoning used “reconsider” **76 times**. Round-seven planning `b0e6ae2b-adf7-4c73-a7aa-c325d4783a1f` took **50.33 minutes**, with 13 function calls and 43 occurrences of “reconsider.”

These are indicators of repetitive deliberation, not proof that every repeated check was unnecessary. The more important result is that long reasoning did not prevent basic stale-state assumptions in round five. Latency itself did not let opponents take additional turns; the game waited for required decisions.

## What Qwen did correctly

- It expanded to four castles by round two and exploited undefended Crackclaw twice.
- Its round-six Roose choice was reasonable given the available hand. Eddard was spent and Robb had been discarded by Patchface. Roose matched its best available effective strength, recovered the discarded cards on losing, and its knight survived. Calling that card choice itself the cause of losing Winterfell would be misleading.
- It recovered White Harbor in round seven using the cheap Catelyn card, correctly winning a 3–3 tie against Lannister. It had begun rebuilding there when Luna ended the game elsewhere in round eight.
- All 35 completed Qwen decisions submitted an accepted action on their first submission. Its earlier funding failures, oracle caps, and one incorrect area identifier are separate from these gameplay errors.

## Evidence and limitations

### Follow-up: how much did context presentation contribute?

The strongest context concern is stale strategy competing with current facts. This qualifies the earlier model-focused explanation: the factual track data was correct, but the harness presented a large amount of conflicting historical prose alongside it.

In round-five planning (`8a598690-6fd0-4601-9fb2-ca88d099684d`), `tracks.fiefdoms` was `[baratheon, stark, lannister]`. However, `strategicMemory.modelPlan` was the note written when Qwen submitted its Fiefdoms bid, before the result was known. It still said Stark was first and held the Blade. The memory object, including its journal, contained the literal phrase “Fiefdoms 1st” 13 times. The subsequent combat input also contained 13 occurrences; by then the latest plan itself repeated the incorrect assumption from planning.

The model authored these notes. The harness retained the latest plan plus up to 12 decision-journal entries, eight action commitments and a 12-entry history index, without reconciling obsolete factual claims. It did explicitly instruct the model to obey the current observation over history. Thus this is **correct live facts plus stale, repetitive memory**, not a finding that the harness supplied the wrong live track.

There was also no persistent summary of changes since Qwen's previous decision. The observation included only the last 12 recent protocol events. By round-five planning those events covered the later King's Court bidding and transition to planning; the Fiefdoms result was no longer in that window. A fresh state array remained available, but there was no prominent “you lost the Blade / your Fiefdoms position changed” summary.

Measured context sizes for the round-five card decision:

- System instructions: **127,567 characters**, including the full rules/FAQ and static map. This included optional/expansion material explicitly marked as applicable only when enabled.
- Recorded current user input: **42,929 characters**.
- Within the saved compact observation, strategic memory occupied **19,876 characters**, including a **15,466-character journal**. The board occupied 6,690 characters, all three track arrays together 140, and the history index 4,593.
- The first actual parent request reported **43,453 input tokens**. By its sixth request, accumulated reasoning and tool exchanges raised that to **65,222**. These token figures cover the whole provider request, not the observation alone.
- The round-five planning request similarly grew from **43,058 to 83,092 input tokens** across six requests.

Combat presentation also imposed reconstruction work. The card-decision briefing said only that a battle was underway and to select a card, followed by general tool instructions. There was no compact combat summary giving the two current base strengths, applicable supporting areas, tiebreak winner and Blade owner. Qwen had to combine attack/support events, board and order data, static adjacency and rules. The basic information for this battle was present; its salience and organization were poor. Likewise, the retreat briefing correctly said survivors become routed, and the neighbour tool showed the adjacent Lannister March +1, but it did not summarize the next actor or immediate threats to each legal retreat.

Assessment by failure:

| Failure | Context contribution | What the evidence supports |
| --- | --- | --- |
| Wrong Blade/tiebreak in round five | Strongest evidence of a contributor | Correct live array competed with 13 stale first-place claims; the relevant change had fallen out of recent events. Causal magnitude is untested. |
| Miscounting support / rules uncertainty | Plausible contributor | The model repeatedly reconstructed facts scattered across full rules, map, board and events. Some mistaken calculations were corrected before acting. |
| Long reconsideration loops | Plausible contributor | Multiple instructions encouraged liberal/deep exploration, while the full reference and growing transcript provided ample material to revisit. This does not establish that prompt wording caused the measured latency. |
| Retreat into Moat Cailin | Primarily failure to use available evidence | Routing was explained and the immediate enemy march was explicitly returned by a tool. A clearer next-action summary could help, but missing information is not the explanation. |
| Expanding despite moving last | Primarily threat/sequencing failure, possibly reinforced by memory | The model acknowledged moving last, yet acted as if neighbours would not attack. Earlier notes repeatedly described opponents as no immediate threat. |
| Repeatedly deferring recovery | Mixed / weaker attribution | The harness recirculated future plans, but the pressure and limited forces were real. The trace alone cannot identify a superior safe recovery plan. |

The highest-value context experiments would be to separate model plans from authoritative facts, replace redundant journals with a concise relevant history, surface changes since the previous decision, and expose deterministic combat/turn facts in a short decision summary. Those are proposed experiments, not implemented changes. Comparing the same saved positions with and without those changes would be needed to attribute an improvement causally. Luna's correct reading under the same general harness format shows that the task was solvable; it does not show that the presentation was equally usable by every model.

Primary data: `data/evaluations/luna-deepseek-qwen-20260923/game.json` → `childGameState.gameLogManager.logs`, and `harness.db` → `agent_runs` (`response_json`, `observation_json`, `tool_arguments_json`). Log array indices are zero-based:

- 72–90: both round-three battles, retreat and unit deaths.
- 131–136: round-four Crackclaw capture and White Harbor loss.
- 155–156: round-five Fiefdoms bids and resulting order.
- 173–180: second Crackclaw battle and Patchface discarding Robb.
- 222–230: Winterfell battle, Roose recovery and retreat.
- 239–241: round-seven mustering, including Stark's empty recruitment.
- 282–289: Stark retakes White Harbor.

The older runtime's stored observations can reflect state changes after a request (for example, ready-player or selected-card fields). I therefore use the authoritative log for outcomes and sequencing, and corroborate claimed model assumptions with the recorded reasoning and tool results. The Fiefdoms ordering was established before both round-five decisions and remained unchanged throughout them. This review does not infer access to an opponent's hidden card from a later-mutated snapshot.

The overall explanation is not bad luck in four isolated fights. Qwen exposed small forces, failed to model the next enemy action, and then used outdated advantages to justify a losing battle. Luna accurately calculated and exploited those weaknesses; DeepSeek's northern attacks compounded them.
