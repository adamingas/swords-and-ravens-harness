# OSS-120B full-game failure audit

Audited 23 September 2026. This is the three-player, seed-102 game through
OpenRouter with **Cerebras-only routing**, including its failed and cancelled
attempts and subsequent continuations. All three houses used GPT-OSS-120B.
The game finished after round ten: Baratheon won with four castles against
Lannister's four and Stark's three, winning the land-area tiebreak 7–5.
The separate Groq probes were not a full game and are outside these counts.

**The run exposes substantial interface failures and substantial gameplay
failures.** The interface sometimes prevented the model from expressing a move;
even after it could submit actions, it repeatedly misunderstood support,
combat cards, mustering, geography and endgame scoring. Completing this game
does not establish improved thinking. It was one self-play game, and its
reasoning setting and schema feedback changed during recovery.

## Scope and evidence

I reviewed all **173 run attempts**, their submissions and handoffs, the current
observations, recorded tool exchanges, and the reasoning associated with the
suspect decisions. This report catalogs the distinct problems found and lists
every recorded unsuccessful submission, failed run, exploration-tool error and
explicit pass. It cannot prove that every unflagged move was strategically best.

The cumulative source is
`data/evaluations/reachable-routes-oss-cerebras-20260922-medium/harness.db`, with
its manifest and decision audit. Earlier databases are copied into that
continuation; summing them again would double-count the same game.

- [Complete retry ledger](RETRIES.md): every unsuccessful submission and failed/cancelled run.
- [All passes and skipped opportunities](PASSES.md): 25 decisions, with individual assessments.
- [Machine-readable inventory](inventory.json): all 173 attempts, complete arguments, tool outputs, handoffs and returned reasoning.
- [Combat outcomes](combat-evidence.json): all six distinct authoritative server combat results.
- [Mustering alternatives](mustering-alternatives.json): legal alternatives to every mustering skip.
- Round transcripts: [1](round-01.md), [2](round-02.md), [3](round-03.md), [4](round-04.md), [5](round-05.md), [6](round-06.md), [7](round-07.md), [8](round-08.md), [9](round-09.md), [10](round-10.md).

“Definite error” below means a statement or calculation contradicted recorded
state or rules. “Costly outcome” means an actual loss followed. A counterfactual
card choice is compared with the opponent's actual card, not presented as a
guaranteed win against every possible response. Questionable strategic choices
are distinguished from provable rule errors.

## 1. Reliability: every retry counts as a failure of the intended interface

| Measure | Count |
|---|---:|
| Completed decisions | 158 |
| Failed run attempts | 13 |
| Cancelled run attempts | 2 |
| Returned responses with usage, including oracle | 527 |
| Parent responses / oracle responses | 493 / 34 |
| `submit_action` calls | 402 |
| Accepted submissions | 158 |
| Schema-invalid submissions | 243 |
| Additional game-legality rejection | 1 |
| Run attempts with invalid submissions or failed/cancelled status | 51 |
| Exploration-tool errors, separate from submissions | 8 |

There were **244 unsuccessful submissions**, approximately 61% of submission
attempts. Of these, **94 have explicit recorded rejection outputs** and **150
were independently revalidated against the exact stored action schema** because
the original tool outputs were missing. The latter are reconstructed validation
results, not quotations of what the model received.

The corrected response total is 527, not the earlier 514. Request-start events
and returned usage are different counters; exploration and oracle calls are
also requests, but are not automatically retries. The exhaustive ledger avoids
equating “multiple responses” with “multiple rejected moves.”

### R1. The schema was not reliably intelligible to OSS

Examples span Raven choices, mustering, marches, bids, retreats and card choices.
The model guessed strings instead of discriminator objects, invented field
aliases, and supplied fields which the harness had removed as fixed values.
The ledger lists every instance, including the recurring one-rejection pattern
after richer error feedback was added.

The [schema-rendering investigation](../schema-rendering-2026-09-22/REPORT.md)
reproduced the published GPT-OSS template reducing the multi-action schema to
`decision: any`, and some nested array structures to `any[]`. The SDK preserved
the full JSON schema in an offline HTTP capture. We cannot observe the actual
provider's internal rendering, so the published-template reproduction is strong
support for a schema-delivery problem, not proof of its exact internal code.
It is incorrect to describe all these retries as the model ignoring a clearly
visible schema.

### R2. Two mustering loops consumed 170 responses without taking a game action

| Attempt | Responses | Invalid submissions | Outcome |
|---|---:|---:|---|
| [D040](round-04.md#d040), Baratheon | 90: 80 parent + 10 oracle | 75 | Cancelled |
| [D042](round-04.md#d042), Baratheon | 80: 77 parent + 3 oracle | 73 | Cancelled |

These were **148 malformed submissions**, plus exploration and nested oracle
work. OSS repeatedly tried alternate JSON spellings and asked the rules oracle
for the action schema. The oracle did not possess the live action schema. The
harness continued the repair loop instead of stopping an unproductive exchange.
Restarting the decision with the same interface reproduced the failure.

### R3. The empty-object action encoding caused a real skipped move

In [D036](round-03.md#d036), Stark wanted to move its knight from The Stony Shore
to Winterfell. The harness had fixed both destination and units, so the legal
move was encoded as `moves: [{}]`; `moves: []` meant discard the March.
The model tried 24 schema-invalid forms, plus one illegal request to leave a
control token while submitting no move. It then passed instead of executing its
original legal move. This was **25 rejections and one accepted pass**, not merely
extra latency. The description still referred to destination groups and unit
IDs even when those fields had disappeared.

### R4. Optional actions also became long repair loops

Round-one Lannister's [D004](round-01.md#d004) needed only to skip the Raven.
It made **30 submissions: 29 rejected, one accepted**. Earlier notes incorrectly
called all 30 rejected. Along with D036 and the two mustering loops, these four
attempts consumed **226 of 527 responses (42.9%)**.

### R5. Output exhaustion caused 13 failed attempts and repeated decisions

All 13 failed attempts ended with `max_output_tokens`; the earlier limit
investigation found an effective 8,192-token ceiling even after a requested
40,960-token allowance. The final continuation changed parent reasoning from
high to medium; the oracle remained high with a 900-token allowance.

The repeated decision sequences were:

| Decision | Attempts, including eventual completion |
|---|---|
| Round 2 Lannister planning | D014 → D016 |
| Round 3 Baratheon planning | D024, D027 → D028 |
| Round 3 Lannister Raven | D029 → D030 |
| Round 4 Baratheon mustering | D038, D039, D040 cancelled, D041, D042 cancelled → D043 |
| Round 4 Lannister mustering | D044, D045, D046, D047 → D048, which skipped |
| Round 9 Baratheon Raven | D143 → D144, which skipped |
| Round 10 Baratheon Raven | D171 → D172, which skipped |

The two late Raven restarts changed intent from replacing an order to passing.
That is observable plan discontinuity, although the abandoned replacements are
not proven good moves. See [Cerebras investigation](../reachable-routes-2026-09-22/CEREBRAS_OUTPUT_LIMIT.md).

### R6. Exploration failures created additional retries and unresolved questions

There were six oracle output-limit errors: two in D010, two in D012, one in D023
and one in D150. D150 also hit the oracle's three-turn limit. In D120 the model
requested nonexistent card ID `renny-baratheon` instead of `renly-baratheon`.
All eight are listed in [RETRIES.md](RETRIES.md).

The oracle was also asked for live Wildling strength and the dynamic action
schema, neither of which it could supply from its static rules context. In D150
both oracle calls failed; the parent then submitted a card choice with a false
explanation. Speculation inside the failed oracle's reasoning is not a successful
answer delivered to the parent and should not be blamed as if it were one.

## 2. Concrete combat errors and their consequences

### C1. Stark declared victory, played a zero card, and lost both footmen

[D080](round-06.md#d080), [D086](round-06.md#d086), [D088](round-06.md#d088):
Stark attacked Moat Cailin with two footmen. Its plan counted support from The
Shivering Sea, which does **not** border Moat Cailin. At card selection it also
reasoned as if the destination were empty despite the visible Lannister footman.
It selected Catelyn, strength zero, saying “Victory already secured.”

The server resolved **Stark 2 against Lannister 4**, with Gregor's strength three,
and both Stark footmen died. Robb, strength three, was available: against the
actual Gregor play, that would have produced 5–4. This is a clear costly state
reading and combat calculation error, not an unavoidable bad matchup.

### C2. Baratheon invented eight support strength at Riverrun

[D110](round-08.md#d110), [D114](round-08.md#d114), [D116](round-08.md#d116):
Baratheon counted five support from two Kingswood knights with a starred Support
and three from Shipbreaker Bay. **Neither area borders Riverrun.** Actual support
was zero. It also omitted part of Lannister's real support from The Golden Sound.

It chose Melisandre, strength one, expecting an easy win. The actual result was
**Baratheon 5 against Lannister 7**: its footman died and its knight retreated
wounded. Available Renly, strength three, would have produced 7–7 against the
actual Jaime play, won by Baratheon's Fiefdoms position.

The returned reasoning additionally treated Brienne's own fortification as
cancelling her own sword. Fortifications oppose the enemy's swords; this false
rule affected the card comparison. D117's subsequent blade decline was sensible:
adding one after choosing Melisandre still leaves 6–7.

### C3. The next combat was mistaken for the previous one

[D120](round-08.md#d120): Lannister counterattacked Harrenhal. Baratheon was now
**defending with a wounded knight**, but its reasoning continued treating itself
as the attacker at Riverrun, queried Riverrun's neighbours, counted the wounded
knight's strength and carried over an earlier March bonus. It also said declining
the blade in the previous combat meant it could not use it now.

Actual army strength was zero for the wounded knight. The server resolved
**Lannister 7 against Baratheon 3**, and the knight died. Baratheon spent Renly even
though its own reasoning regarded the battle as lost; a cheaper card was
available. Even Renly plus the blade could not win against the actual Hound play.
This combined stale battle context, wounded-unit rules, blade rules and poor
card conservation.

### C4. Ignoring Kevan's ability cost Harrenhal when the blade could save it

[D153](round-09.md#d153), [D154](round-09.md#d154), [D155](round-09.md#d155):
Baratheon calculated a 3–3 tie and declined the blade. It omitted Kevan's bonus to
the attacking footman. The actual score was **Lannister 4 against Baratheon 3**.
Using the available blade would have made it **4–4, won by Baratheon's Fiefdoms
position**. Instead Baratheon retreated and lost Harrenhal. There was no later
Baratheon battle that round to justify the blade reservation after the fact.
Its retreat handoff then called the defending army an attacking army.

### C5. Other combat reasoning was wrong even when the action was defensible

| Evidence | Wrong reasoning | Assessment |
|---|---|---|
| [D032](round-03.md#d032), Lannister | Tywin would win and produce two power | Actual 7–7 lost on Fiefdoms to Baratheon. Overconfident prediction; Tywin may still have been its best attempt against an unrevealed opposing card. |
| [D115](round-08.md#d115), Lannister | Defending siege engine contributes four | It contributes zero while defending. Lannister nevertheless won through real support; a winning outcome concealed wrong arithmetic. |
| [D147](round-09.md#d147), Lannister | Tyrion's one strength secures Moat Cailin | Failed to budget for the attacker's card. The eventual 3–3 went to Stark on Fiefdoms. |
| [D149](round-09.md#d149), Lannister | Activating Tyrion gives “+1 combat strength” | His ability forces the opponent to replace its card. The actual effect and the stated purpose differ. |
| [D150](round-09.md#d150), Stark | Choosing Rodrick discards him to draw another card | This was selection of the replacement combat card after Tyrion. Rodrick actually fought and won 3–3; the explanation describes a different game operation. |

## 3. Mustering, economy and resource mistakes

### E1. Eight free mustering opportunities were skipped

Lannister and Stark skipped in round four; all three houses skipped in rounds
seven and ten: **D048, D049, D090, D091, D092, D157, D158, D159**.
Repeated explanations claimed to preserve power tokens or avoid Supply problems.
Mustering does not spend power. Supply does not forbid every new piece, and
upgrading a footman does not increase an army's size.

For **each of the eight** I reconstructed its archived player snapshot and
validated at least two individual recruit/upgrade alternatives. The respective
counts were **6, 3, 7, 6, 2, 7, 4, 5**. These are alternative plans, not a claim
all can be combined. They were checked with the harness validator, not replayed
through a counterfactual server game. See [evidence](mustering-alternatives.json).

Stark's round-seven skip was especially poor after its two footmen had died.
In round ten, Stark argued that it could not reach seven castles, overlooking
that the game also ends by comparing positions after round ten. Lannister and
Baratheon again invoked preserving bidding tokens, a nonexistent mustering cost.

### E2. Baratheon ordered Consolidate Power at sea five times for nonexistent income

[D001](round-01.md#d001), [D015](round-02.md#d015), [D028](round-03.md#d028),
[D053](round-04.md#d053), [D068](round-05.md#d068) placed Consolidate Power in
Shipbreaker Bay while describing power generation. That sea order earns no power.
The misconception persisted across five planning rounds and appeared in the
D008 handoff. A sea Consolidate order can be a placeholder; **the claim that it
generates income is the definite error**.

### E3. Capturing Supply icons was confused with immediately changing Supply

[D021](round-02.md#d021) described capturing Blackwater as increasing Supply.
The icons affect the next Supply update; they do not immediately move the track.
Plans that recruit or combine armies against an assumed immediate increase can
therefore be wrong even after the territory is successfully taken.

### E4. The mustering plan exceeded Supply and the handoff recorded a unit never created

[D107](round-08.md#d107) claimed its entire recruitment plan fit Supply four and
that a footman had been placed in The Reach. The applied action recorded
`omitted_supply_unsafe_recruitments: 1`; that recruitment was omitted.
The stored strategic handoff still claimed it happened. This is both a model
planning error and a harness feedback problem: acceptance ends the decision,
while its saved plan describes requested rather than applied effects.

### E5. Wildling bids relied on invented certainty and contradictory budgets

- **D010, round two:** tried to ask the rules oracle for current Wildling strength. This exposed a missing live observation field, rather than a rules question the oracle could answer.
- **[D051](round-04.md#d051), [D074](round-06.md#d074), Lannister:** bid all four/all three tokens while saying this preserved remaining power or future influence bids. The resource claim contradicts the action; the bid itself may be defensible.
- **[D075](round-06.md#d075), Stark:** bid zero relying on the richer opponents to defend. **[D076](round-06.md#d076), Baratheon:** claimed a known Night's Watch total of four against strength approximately two, despite opponents' bids being hidden. Actual strength was four, bids totalled three, and the players lost. One extra token from either zero-bidding house would have sufficed against the bids actually made, but neither knew those simultaneous bids in advance.
- **[D126](round-09.md#d126), Lannister:** correctly recognized the group could not beat strength twelve with ten available tokens, but assumed Stark would take the worst zero-bid penalty. All houses bid zero; the Iron Throne holder chose Lannister instead. It lost three pieces. The error is treating a hostile tie decision as guaranteed, not necessarily choosing zero in an unwinnable defense.

### E6. Valuable knights were sacrificed to preserve a largely unused fleet

[D129](round-09.md#d129) removed both Kingswood knights, keeping three Shipbreaker
Bay ships for transport. Removing two of those ships would still have left one
ship in that sea and the same transport connectivity, while retaining the
knights. This looks strategically poor after their repeated repositioning and
failed support plan. It is not strictly dominated: extra ships do add naval
combat strength, so this remains a strategic criticism rather than a proof of
illegality or a guaranteed better result.

## 4. Geography, orders and plans that went nowhere

### P1. Plans repeatedly assumed nonexistent routes or support

| Evidence | Plan | Problem |
|---|---|---|
| [D068](round-05.md#d068), Baratheon | Crackclaw Point → Riverrun, supported from The Reach | No direct adjacency or current friendly transport route; The Reach cannot support Riverrun. Actual march went to King's Landing. |
| [D080](round-06.md#d080), [D100](round-07.md#d100), [D112](round-08.md#d112), Stark | Shivering Sea supports Moat Cailin | Those areas are not adjacent. The error survived multiple rounds, including a lost battle. |
| [D089](round-06.md#d089), [D103](round-07.md#d103), Baratheon | Reposition east-coast knights for attacks/transport toward Lannisport | Current ships did not provide a route to the west coast. No operational route was established. |
| D110/D114/D116, Baratheon | Kingswood and Shipbreaker Bay support Riverrun | Neither is adjacent; eight imagined support strength became zero. |

The [map evidence](map-evidence.json) records these adjacencies. The new
`reachable_areas` tool was called **only four times**: D021, D025, D055 and D141
(one march decision and three planning decisions). There is no evidence in this
run that those four responses themselves returned a wrong route. The tool was
largely not used where the model subsequently invented transport plans. Route
reachability also does not establish support adjacency or combat victory.

### P2. Stark's knight spent most of the game oscillating, then died without an attack

Its route was Winterfell → Stony Shore (D020), intended return abandoned in D036,
back to Winterfell (D059), back to Stony Shore (D072), back to Winterfell (D105),
then Castle Black (D122), followed by removal to satisfy a Wildling penalty
(D130). The knight captured no new castle and never attacked. Some early
positioning could be useful, but the full sequence shows no sustained plan and
repeated expenditure of March orders on reversing earlier movement.

### P3. Baratheon's knights also accumulated movement without the intended payoff

Crackclaw Point → King's Landing (D070), back to Crackclaw Point (D089), then to
Kingswood (D103), where their supposed support for Riverrun was impossible, then
both removed in D129. This linked route misunderstanding, misplaced support and
poor resource retention across multiple decisions.

### P4. March orders were assigned and then abandoned

Besides the schema-induced D036 pass, Lannister cancelled planned attacks in
D058, D071, D085 and D104. These should not all be scored as foolish passes:
D071 recognized an unfavorable attack; D085 had a real problem retaining its
source castle. The repeated pattern is **planning an advance before checking
whether the resulting march is useful**.

D058 falsely feared losing Riverrun despite its existing control token. D104
claimed White Harbor had a garrison and support that would defeat it; White Harbor
was empty with zero garrison, so there would be no battle there. Moving would
trade its own source castle for another, rather than simply add one, so the
false justification does not establish that moving was always best.

D102 also replaced The Reach's March with Defense while describing continued
“expansion momentum.” This was a change to a defensive plan, not advancement.
See [PASSES.md](PASSES.md) for every case and its limitations.

### P5. Other orders or remembered orders did not deliver their stated purpose

- **D142:** Shipbreaker Bay was given Raid “to disrupt opponent orders,” with no eligible enemy order to raid in adjacent areas at resolution. No raid decision resulted.
- **D110:** the model's plan assumed both Kingswood and Shipbreaker Bay had starred Support. The applied token allocation gave Shipbreaker Bay ordinary Support. A preferred-order request is not a guarantee of the exact token; the handoff did not reconcile the applied allocation. The non-adjacency error would invalidate the intended Riverrun support anyway.

## 5. Scoring and endgame errors

### S1. Area names were treated as castle indicators

[D141](round-09.md#d141) planned to capture empty Castle Black “adding a new
castle.” **Castle Black has castle level zero.** Stark eventually chose a useful
Moat Cailin attack instead, so this is a wrong plan, not an executed ninth-round
capture of Castle Black. The earlier D122 knight move did reach Castle Black.
In D171, Baratheon's failed Raven reasoning similarly called Stoney Sept a
stronghold; it also has castle level zero.

### S2. Castles and strongholds were double-counted

[D160](round-10.md#d160) claimed Lannister held seven scoring areas when it held
four. The observation's overview showed four castles and three strongholds,
where strongholds are a **subset** of the castle count. Adding the fields is a
plausible explanation for seven, not directly proven internal causation. This
is a definite wrong board assessment and an avoidably ambiguous summary format.

### S3. Influence-track effects were confused

- **D139:** ranked Stark ahead on King's Court to give it earlier turn order. Iron Throne determines turn order; King's Court determines special-order allowance/Raven ownership.
- **D162:** resolved an Iron Throne tie while saying it would keep Lannister lower on Fiefdoms. These are separate tracks.
- **D132/D134:** Lannister's zero-bid reasoning assumed favorable retention of position, although the opposing throne holder controlled tied placement. This repeats the unsafe tie assumption seen in Wildling bidding.

### S4. Tokens were saved for benefits that did not exist

[D166](round-10.md#d166), Lannister, kept two power tokens in the last King's
Court auction, saying preserving them was optimal because there were no further
bidding opportunities. With the other bids actually zero, one token would have
secured first place. The subsequent D168 handoff said it was preserving power
“for final scoring.” Power tokens are not a final scoring tiebreaker. Keeping
some tokens can enable control tokens during marches, but that was not its
stated plan and it placed no March orders.

### S5. Both losing houses chose final-round plans without a March

[D168](round-10.md#d168), Lannister: entirely defensive orders while tied on
castles and losing the land-area tiebreak. It claimed it could not capture
castles without ships, despite land adjacencies such as Harrenhal–Crackclaw Point
and Seagard–Moat Cailin. Adjacency does not prove those attacks win, but the stated
geographical impossibility is false. It had also declined free mustering.

[D169](round-10.md#d169), Stark: Defense and Support while trailing on castles,
declaring no attack opportunities. Together with the skipped mustering, it made
no attempt to improve its final castle score. This is evidence of passive
endgame planning, not proof that a winning line existed.

By contrast, Baratheon's final empty March in **D173 was reasonable**: the current
position already won the tiebreak. Its explanation about lacking a power token
was wrong because Crackclaw Point already had one, but staying did preserve the
winning position. Counting that as a bad pass would distort the audit.

## 6. Harness problems that affect attribution and evaluation

These are observations for follow-up, not production changes made by this audit.

1. **Schema rendering and shifting action shapes.** The published OSS template loses structure; singleton removal changes familiar action fields into implicit values or empty objects. Richer feedback helped recovery but did not eliminate first-attempt failures.
2. **Unbounded within-decision repair.** The same misconception could consume dozens of calls. Across-run failure limits did not bound these loops. Restarting without changing the cause added further cost.
3. **Output limits and oracle limits.** Parent exhaustion stopped decisions; the 900-token high-reasoning oracle repeatedly exhausted its output budget. Raising the requested parent limit did not resolve the observed Cerebras ceiling.
4. **Missing live Wildling strength.** It exists in the player snapshot but is absent from the model observation. Models guessed a public game value or asked a static rules oracle for it. Do not classify failure to know an omitted value as pure model incompetence.
5. **No dedicated current-combat summary.** The observation supplies board state, pending leaf decision and recent events, but no explicit combat object collecting attacker, defender, battle area, order modifiers and support. D120 still contradicted available evidence, but this format makes confusing consecutive battles easier.
6. **Generic special-effect prompts.** The Tyrion activation/replacement sequence used generic choice/card selection language rather than a clear statement of the current effect. That contributed to ambiguity in D149–D150; the model's confident invented explanations remain errors.
7. **Requested versus applied actions diverge.** The D107 mustering omission was retained in applied arguments but not corrected in strategic memory. D110 likewise planned around preferred rather than applied order tokens. Acceptance should not leave memory claiming nonexistent pieces or bonuses.
8. **Overlapping scoring fields.** `castles` includes `strongholds`, but exposing both without an unmistakable subset relationship invites double-counting.
9. **Cancelled/failed transcripts lose some tool outputs.** There are 150 invalid submissions without original rejection outputs: 148 from the two cancelled mustering attempts and two from failed late Raven attempts. Revalidation recovers invalidity, not the exact original feedback.
10. **Persisted observations can mutate after the input was sent.** This audit discovered the additional recording defect described below.

### Observation-integrity finding: 83 stored observations did not match their recorded input hash

Blindly treating `agent_runs.observation_json` as the exact initial model input
would have corrupted parts of this audit. **83 of 173 rows did not match** their
recorded `context.currentInputSha256`. Shared nested state had changed before
the observation was persisted: pending decisions, planning readiness or wounds.
For example, a card-selection observation could appear to contain a selection
made only later.

I recovered all 83 inputs and verified **all 173 against the original SHA-256**:
69 by restoring earlier pending-decision fields, 11 by restoring the earlier
board, and three by recovering intermediate planning-ready lists. The original
90 matching inputs were left intact. [extract.py](extract.py) records the method;
each inventory entry includes the verification result and restored fields.

This is an **audit/persistence defect, not evidence that the model received future
or hidden information**. It also means future evaluators should verify input
hashes before judging what a model knew. The evidence in this report uses the
hash-matching reconstructed input.

## 7. What this run establishes

The most consequential observed failures were:

1. **The interface sometimes changed gameplay:** a legal Stark march became a pass after 25 rejections; repeated mustering/Raven failures ended in new attempts that skipped.
2. **Combat arithmetic was unreliable:** imaginary support, ignored card abilities, incorrect unit strength and confusion about which battle was active caused avoidable local losses.
3. **Expansion and rebuilding lacked continuity:** eight free musters skipped, knights moved back and forth, and plans repeatedly assumed nonexistent routes.
4. **The models did not reliably optimize the endgame:** false castle counts, irrelevant token saving and defensive final plans persisted while houses were losing.
5. **The harness does not yet provide clean evaluation conditions:** lossy schema delivery, missing facts, runaway repairs and mutable recorded observations contaminate conclusions about model quality.

The priorities suggested by this evidence are to make the full action contract
visible before the first submission, stop repeated identical failures, supply
unambiguous live combat/Wildling state, reconcile strategic memory with applied
actions, and preserve immutable input/output records. A subsequent controlled
run could then measure first-attempt validity and gameplay separately. This
audit does not run another experiment, change production code or claim a tested
fix for those issues.

## Reproducing this audit

From the repository root, with the archived cumulative database available:

```sh
uv run python docs/analysis/oss-full-run-audit-2026-09-23/extract.py
uv run python docs/analysis/oss-full-run-audit-2026-09-23/verify_state.py
uv run python docs/analysis/oss-full-run-audit-2026-09-23/build_appendices.py
```

The scripts read the database in read-only mode and write only these analysis
artifacts. They make no model calls or gameplay submissions. Checks assert the
173 matching input hashes, 402 submissions, 244 unsuccessful submissions, eight
exploration-tool errors, six unique combat results and 527 returned usage records.
