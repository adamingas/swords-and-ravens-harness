# Stark trace review

Experiment: `data/evaluations/structured-decisions-deepseek41-three-player-serial-game-morph/harness.db`. Agent `49933751-ef60-4ad8-bb0d-a9e5932abbf5`, user 3, DeepSeek v4.1 Flash. Analysis covers all 48 recorded attempts: 35 completed, 10 failed, 3 cancelled. Evidence is the stored observations, model reasoning and responses, tool calls/results, accepted actions, and strategic memory. This game spans harness changes; it is not a controlled comparison of prompting techniques.

Stark won with seven castles in round 5. It understood the victory objective and executed a coherent expansion plan across several independent decisions. But it also misunderstood hidden bids, repeatedly lacked the actual Wildling card text, sometimes counted illegal support, and stopped actually calling tools in round 5 despite repeatedly saying it would. Persistence already exists and was useful; it needs better content and freshness, rather than indiscriminately retaining old observations or complete reasoning.

## What the player actually achieved

| Round | Plan and execution | Representative runs |
|---|---|---|
| 1 | March Winterfell’s knight and footman to Moat Cailin; move the Shivering Sea ship into the Narrow Sea to open transport routes. Three castles. | `f183c5cb-b10d-4bba-b330-01dbe59693ae`, `2062c316-e46b-47a9-987e-a63ce30f734f`, `8eb13ffe-b6ae-4298-a2ba-fd167f26f728` |
| 2 | Split Moat Cailin’s army: capture empty Seagard with the knight while retaining a footman at Moat Cailin. Upgrade White Harbor’s footman into a knight. Four castles. | `189af364-c4a8-4ab6-9bf6-ec3e64a98e2d`, `e10312d6-5fe0-4cbc-82a7-5b4aae83b236` |
| 3 | Transport White Harbor’s knight and footman to the neutral Eyrie. March +1 and starred naval support bring strength to six. Refill the vacated White Harbor from Winterfell to retain the additional castle. Move a Seagard knight to Greywater Watch as the first step toward Flint’s Finger. Five castles. | `f9c67485-6b8f-4774-b7db-adf15532181f`, `b8624b2c-a4e9-48c3-bd95-a6f636c5c6ce`, `75b51fd9-88ef-41ac-b215-037d49e948cb`, `e8e2e11a-870f-40a5-b65d-ab329cfa1d0f` |
| 4 | Move Greywater Watch’s knight to empty Flint’s Finger, leaving a power token to keep Greywater Watch’s supply icon. Six castles. | `585e192b-83a8-4afb-952b-31761ea2e360` |
| 5 | Initially choose defensive orders. Use the Raven to replace the Eyrie’s defense with March -1; support Baratheon against Lannister at Crackclaw Point; then send only the Eyrie footman into newly empty Crackclaw, keeping its knight behind. Seven castles and victory. | `1f0f4452-7182-4bd0-8866-fa633c1d3f3c`, `a7836e7f-df30-4583-bb4e-7cec3914d439`, `88aa21b4-8d81-469b-862c-fe5c1f34345d`, `c6ff5f90-cbf7-448e-b400-4005015ba8ee` |

The final march explicitly reasons that moving both units without a control token would lose the Eyrie and cancel the victory-point gain. It chooses the correct split. This is clear evidence of understanding ownership, supply, movement, and immediate victory.

## Tools and persistent planning

Counting outer tool calls by unique call ID, including calls preserved inside failed `partial_model_response` records:

| Tool | Calls |
|---|---:|
| `check_neighbours` | 87 |
| `remember_strategy` | 29 |
| `ask_rules_oracle` | 11 |
| `recall_game_state` | 7 |

That is 134 exploration/memory calls, matching the completed-tool event count. Completed gameplay runs contain 121 of these; failed attempts contain 13. Nested oracle rulebook reads are separate. Of the 29 memory calls, 27 are in successful runs, including one run with two writes; only the last queued note is saved after an accepted action.

The round-1 note already names Moat Cailin, the Narrow Sea bridge, and the Eyrie/Crackclaw/Seagard expansion corridor. Round-3 notes explicitly preserve the action sequence: capture the Eyrie, refill White Harbor, then advance a knight to Greywater Watch and next round to Flint’s Finger. Those later moves happen. This is strong evidence that compact memory supports continuity.

However, most notebook fields are automatic. `src/raven_harness/harness/strategic.py::_automatic_notes` supplies generic objectives, opponent resource counts, and recent action strings. `remember_strategy` edits only the 2,000-character `modelPlan`. The final `lessons` list is empty; the objectives remain generic. The notebook has no model-authored structured opponent hypotheses or durable learned-rule corrections.

Old conversation history is filtered out by `_SessionContextFilter` in `models/openai_agent.py`. The next decision receives the latest observation, notebook, history index, and optional recalled observations, rather than prior reasoning. Thus the user’s suspicion is partly correct: the player does not see all its earlier thinking, but it does see explicitly saved plans.

All seven completed round-5 runs have **zero actual tool calls** and one model request each. The tools are present in stored `tools_json`. Planning, Raven, support, and final march reasoning repeatedly announce tool calls, then produce final JSON without calling them. For example, the final march says “Let me call check_neighbours on crackclaw-point and the-eyrie,” followed immediately by the action JSON. The same pattern appears at the end of the Raven and planning decisions.

The final model plan therefore remains the round-4 note, including obsolete supply 0 and obsolete influence positions, even though automatic notebook fields and the current observation reflect round 5 and supply 4. The player often corrects these facts from the current observation, but repeatedly has to reconstruct plans and rules. The trace alone cannot establish whether the round-5 tool disappearance is caused by the provider’s handling of tools with structured output, the harness transition, or model behavior; it requires a targeted integration probe.

## Where it was confused

### Current bidding track and secret bid values

This is the clearest observation-format problem. Bidding `pendingDecision` exposes opponents’ submitted hidden bids as `-1` and does not name the current influence track. In `5200ce53-d8ff-4a09-a2ad-0a2c62cab0b3`, Stark repeatedly asks whether `-1` means zero, pass, withdrawal, or a hidden value. It recalls previous observations to determine which track it is bidding on.

The preceding `9ab7f785-a2cc-4bec-bdfa-2a00e0437ab8` saves the false premise that Baratheon and Lannister “both bid 0,” making a one-token Iron Throne bid a cheap win. The actual subsequent results show Baratheon bid two and won.

In `3dce3819-9238-4fd4-b6be-4f489eb1d298`, the model mistakes the completed Fiefdoms bidding event (`trackerI:1`) for an Iron Throne result, decides the explicit current track state is stale, and concludes it owns the Iron Throne. It asks the oracle the general rule about who breaks later bidding ties; the oracle correctly answers the rule but cannot correct the wrong board premise. Stark then saves “Won Iron Throne ... tie-break ... guarantees 1st” into memory. The next Wildling bid corrects this to Baratheon holding the Iron Throne.

Recommendation: expose `currentTrack`, `bidPurpose`, named tie-break holder, and `{submitted: true, amount: null, hidden: true}` rather than `-1`. Do not require event-log reconstruction for the current decision.

### Wildling inspection does not reveal usable card information

In rounds 2, 3, and 4, inspection yields only `topWildlingCard: 2`. Runs `8ef0c6ac-e639-4003-a282-99ffad793de3`, `43ce1707-27d3-48e0-ac84-968661453660`, and `48ff8f4b-ab3c-4679-8e63-d0d60e3ee4b2` all ask the oracle for the card list or ID mapping. Each answer explicitly says the provided rulebook lacks those card texts.

Stark guesses about the identity, then keeps the card on top to preserve “known information,” even though it never learned what the card does. It repeats this across three rounds rather than retaining the lesson that the oracle cannot answer. The actual card is legally visible to this player; the harness should expose its name and full effects directly. Memory alone cannot repair missing information.

### Map and support rules

Stark can use transport correctly, demonstrated by the Eyrie capture and final win. Nevertheless, round-5 planning repeatedly rediscovers that the Eyrie can reach Crackclaw through the Narrow Sea, oscillating between a two-round route through the Mountains of the Moon and direct transport. The stale round-4 memory contains only the longer route.

There are also genuine support-rule errors. In Raven run `a7836e7f-df30-4583-bb4e-7cec3914d439`, it counts Moat Cailin’s knight plus starred support toward defending the Narrow Sea, inflating defense from one to four. Land units cannot support sea combat. Earlier planning also treats Moat Cailin as potentially supporting an attack into Riverrun because it borders the attacking source, Seagard; support must border the battle destination. Some later passages self-correct these mistakes, but the false naval defense calculation remains in its assessment of the transport bridge’s safety.

Recommendation: provide computed transport destinations and valid support sources/strengths for candidate battles. Raw adjacency is helpful, but it still leaves the model to apply directional movement and support restrictions repeatedly.

### Supply and mustering: mostly competent

Stark correctly distinguishes supply track from controlled supply icons, single units from armies, and unit upgrades from additions. It musters within supply 0’s two-army limit, spreads singleton ships into separate areas, and preserves Greywater Watch’s supply with a control token. All accepted mustering/march outputs show zero omitted supply-unsafe groups/recruitments.

It asks the oracle useful questions about knight upgrades, singleton ships, and control-token supply. It also repeats some already-resolved questions because specific lessons do not persist. There is a recurring mistaken expectation that starred Consolidate Power grants both power and mustering; the actual choice schema steers it to a legal either/or action. No accepted action demonstrates a supply violation.

### Objective and strategy

The victory objective is understood throughout. The main strategic weakness is excessive reconsideration and risk aversion. Round-5 planning spends roughly 52,800 reasoning characters before requesting no land March order, despite being one castle short of victory. It argues that holding six castles until round 10 “basically guarantees victory,” an unsupported forecast while opponents still have five rounds to act.

It requests five Consolidate Power orders despite only three physical tokens; allocation changes the ports to defense and march. The model understands the category preferences abstractly but reasons about gaining power from all five, so the desired plan diverges from the applied orders. Exposing a compact inventory or draft-order preview would make these substitutions visible before submission.

The Raven decision repairs the defensive plan after enemy orders become visible. The later support decision contains good strategic reasoning: helping Baratheon retain Crackclaw leaves a weaker future defender, or forces Lannister to spend better combat resources. It also anticipates Baratheon vacating Crackclaw to capture empty Harrenhal, which is the opportunity Stark ultimately exploits. This is more than random legal play.

## Failures and practical improvements

The ten failed attempts comprise three 300-second API timeouts, one upstream Morph 429, four output-token-limit failures, and two malformed-final-action failures. Three further attempts were cancelled. These are distinct from gameplay errors. The two malformed responses attempt the sensible Winterfell-to-White-Harbor move but surround JSON with prose; the strict parser rejects them. Two oracle answers also hit an output-token limit. These older limits were removed during the experiment.

Ranked recommendations:

1. **Fix missing decision facts:** named current bidding track, explicit hidden bids, and actual inspected card effects. These directly caused confusion and cannot be solved by asking the model to think longer.
2. **Verify round-5 tool behavior through the actual provider/harness path:** tools are advertised but intentions never become calls. Do not force arbitrary exploration; ensure the model can actually interleave it with structured final output.
3. **Persist a concise model-authored decision summary alongside the final action:** intended next moves, why this action supports the plan, dependencies, contingencies, unresolved questions, and opponent hypotheses. Save it after successful submission. This avoids making memory updates depend entirely on an optional tool call and needs no additional model call.
4. **Keep current state authoritative and add meaningful deltas:** newly opened castle routes, changed supply/track position, enemy concentration/withdrawal, and whether the last intended move succeeded. Mark factual notebook claims with the round/state they refer to; remove or update contradicted facts rather than endlessly appending them.
5. **Expose computed tactical facts:** transport reachability and legal support sources. Add a compact allocation preview for order preferences that will be substituted.

A useful persisted summary would say: “We have six castles; win by taking Crackclaw while retaining the Eyrie. Our ship in the Narrow Sea is the transport dependency. If Baratheon vacates Crackclaw, send only the footman; otherwise compare legal support and available cards. Moat Cailin cannot support a sea defense.” Keep this as a bounded notebook or recent assistant-summary messages, plus the latest observation. Do not append full old observations or the very long, self-contradictory reasoning traces: those contain false Iron Throne claims, repeated speculative rules, and stale supply, and would magnify the confusion.
