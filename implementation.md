# Planning context implementation plan

A plan to modify the harness' context

## Intended structure

Separate stable instructions from changing game facts. Put planning instructions,
exploration guidance and completion instructions in the system prompt. Replace
the existing board-specific guidance with a concise **Current status** section
at the end of the decision's user message.

The stable prefix should be reusable across rounds and decisions so repeated
instructions can benefit from prompt caching. Measure cached input tokens and
actual cost, not just total context length; a cache hit reduces billed input
cost without shortening the model's logical context.

## System prompt

Keep the existing base instructions, rules and static map. Consolidate these
additional instructions into a deterministic, stable prefix:

- **Planning:** submitting a complete order plan using exact, readable order
  names, and respecting the available token counts. Make this a
  conditional instruction for the planning step, without injecting the current
  round, eligible areas or restrictions into the system prompt.
- **Exploration:** one concise policy explaining when to consult tools and how
  to use their results. Keep individual tool capabilities and argument details
  in tool definitions; remove the repeated tool catalog from the user message.
- **Completion:** the protocol for the configured execution mode. For two-stage
  execution, explain exploration and finalization once, with the current stage
  supplied as data. For structured execution, explain the direct structured
  response. Do not repeat these instructions after each observation.

Remove redundant rule reminders and prescriptive strategy from the old planning
paragraph. Home symbols, castle scoring, Supply and order effects already have
a home in the rules/map; do not repeat them as planning-time advice.

## User message

Use this order:

1. Compact current observation: round events, one house/resource summary,
   piece reserves, and decision-specific constraints. Area and card details
   are retrieved through tools rather than dumped here.
2. Private strategic memory and history references, clearly identified as
   historical intentions rather than authoritative current facts.
3. Any current retry/error feedback.
4. **Current status**, as the final section.

The status is generated deterministically from the same frozen observation as
the rest of the message, not from the notebook or an LLM summary. It identifies
the house, round, phase, current step, scoring-area total, victory points and
remaining power tokens. Include relevant constraints such as Supply, required
order count and starred-order allowance. Do not include strategy coaching or
repeat the rules.

Example for the recorded Baratheon planning position:

> **Current status**
>
> You are Baratheon in round 8 of 10, in the Planning phase.
> Your current step is to choose the complete order plan for 7 occupied areas.
> You control 5 scoring areas total, counting castles and strongholds once each.
> Your victory points are 5; the immediate-win target is 7.
> You have 9 power tokens remaining and Supply 4.
> You may use up to 3 starred orders. Consolidate Power is restricted this round.

Use explicit totals rather than overlapping “castles” and “strongholds” counters.
Keep victory points separate when the game variant makes them differ from the
number of scoring areas. Missing values must remain unknown, not become zero.

Remove game IDs, state UUIDs, user IDs and storage timestamps from model-facing
state/history where they serve no action or lookup purpose. Preserve them in
internal observations, validation and tracing. Expose readable area, house,
card and order names in actions and tools. Resolve protocol IDs internally,
including unit IDs, as specified below.

## Observation and tool changes

### Westeros cards and Wildlings

Currently the observation has no dedicated summary of the current Westeros
cards, their descriptions, remaining deck counts or Wildling strength. Recent
events and planning restrictions can convey fragments, but are not a reliable
replacement. The player snapshot already contains Westeros deck information,
revealed-card references and `wildlingStrength`.

Add these changing facts to the **user observation**, not the system prompt:

- The current round's revealed Westeros cards: deck, readable name, description,
  whether their resolution is pending or complete, and any effects still active.
  Preserve this round's effects through planning and action resolution; do not
  rely on their original events remaining in the recent-event window.
- Cards remaining in each Westeros deck, including remaining copies by card
  name where that composition is public. Separately identify how many of the
  current round's revealed cards still await resolution. Use engine semantics
  for revealed, discarded and reshuffled cards rather than raw array lengths.
- Current Wildling strength and any active Wildling event. Include a known
  top-card name/description only when this house is entitled to know it.

Remaining-deck composition is not draw order: the server deliberately shuffles
the unrevealed portion in player snapshots. Never describe that serialized
order as a forecast. Update counts after draws and reshuffles and clear expired
round effects. Descriptions of active events belong with these dynamic facts,
even though their printed wording is static.

### Remaining pieces

Currently `actionGuidance.availablePieces` is supplied for mustering, but not
as a general planning resource. Include the acting house's piece inventory in
every decision observation: **limit, on-board count and reserve count** for
footmen, knights, ships and siege engines. Derive limits from the configured
house/variant, not universal constants. For example, a base-game house has a
limit of two siege engines; one on the board leaves one in reserve.

Distinguish pieces physically available to recruit from what the current
mustering points and Supply permit. Wounded units still occupy physical pieces;
recruitment, upgrades and losses must update the counts. Store these resources
in the single house summary described below, not in a second duplicate table.

### House cards on demand

The current observation's `ability` value is an ability identifier, not the
printed effect description. Remove it, `you.availableHouseCards` and the
per-house `houseCardStatus` dumps from the normal observation.

Add this read-only tool:

```python
cards_of_house(name: str) -> list[Card]

Card:
    name: str
    strength: int
    swords: int
    towers: int
    used: bool
    available_to_play: bool
```

It accepts any house in the game and returns both its unused and used cards,
limited to information visible to the calling player. `available_to_play`
means currently selectable for combat, taking disabled cards and current
restrictions into account; it must not be inferred solely from `used == false`.
Do not turn unavailable/hidden information into a misleading empty hand.

Keep printed ability text in the existing card-description tool. Make its
model-facing argument a readable card name, resolved internally, so the model
can inspect any returned card without learning a second identifier. The list
tool does not repeat ability text or ability IDs. Card-selection action schemas
must use the same names and still validate current eligibility.

### Readable, exact order choices

The existing field is `orderLegend`, not `orderLength`. It maps protocol numbers
to order names. Current planning already accepts semantic category preferences,
but the harness then chooses physical tokens and can substitute categories.

Replace this with an exact Pydantic enum of readable order names, such as
`"March -1"`, `"March +0"` and `"March +1 starred"`. Each planning assignment
contains an area name and an order name. Remove numeric order IDs and the legend
from model-facing observations, tools and actions; use the same names for
revealed orders, Raven replacement and other order choices.

The harness maps names to physical tokens internally. Identical tokens share
one name with a remaining count. Validate both enum membership and the complete
plan's token inventory, occupied areas, starred allowance and Westeros
restrictions. An enum alone cannot prevent overusing a token or an invalid
combination. Reject an illegal plan with specific feedback instead of silently
substituting another order. This supersedes the earlier preference/priority
allocation design while retaining one submission for the entire planning phase.

### Area status on demand; no unit IDs

The observation currently includes a dynamic `board` list; static topology is
already in the system map. Remove the board-wide area/unit dump from the user
observation. Retain the compact list of areas eligible for the current decision
and add:

```python
area_status(name: AreaName) -> Status  # Enum of all areas in this game's map

Status:
    name: str
    control_power_token: str | None
    garrison: int
    is_blocked: bool
    units: list[UnitGroup]

UnitGroup:
    house: str
    type: UnitType
    count: int
    wounded: bool
```

Also return the current controller and visible order name: a control token is
not the same as ownership, and an unrevealed order must not be guessed. Group
units only when their mechanically relevant properties are identical; retain
any additional distinctions required by the selected variant. Empty areas
must also be queryable. Keep the existing static system map for this change;
do not duplicate it in the observation JSON.

Removing unit IDs requires changing action schemas too. Marches, casualties,
retreat selections and upgrades must select units by area, type, count and
relevant traits, rather than asking for hidden IDs. The harness resolves these
selections to actual pieces, checks the current decision and rejects stale or
ambiguous choices. Update all related tool outputs and legal guidance so they
do not reintroduce IDs. Preserve internal unit identity for the game protocol
and audit records. Movement reachability and support eligibility remain
separate from area status.

### One house summary

Keep `houses` as the single structured house/resource summary and remove
`strategicOverview.housePositions`. Merge useful derived fields there: scoring
areas total, victory points, land areas, Supply, power tokens and piece reserves.
Use one canonical value for every fact; `you` only needs to identify the acting
house rather than repeat that house's complete resource record.

The final Current status paragraph is a short rendering of that same summary,
not a separately calculated or conflicting second house overview. Preserve
the configured victory target and round limit once in game-level state.

## Implementation locations

- `prompts.py`: compose the stable instructions and completion protocols.
- `decision_briefing.py`: replace repeated advice with the factual status
  renderer; retain decision-specific operation semantics where needed.
- `observation.py` / `preparation.py`: produce a model-facing projection while
  preserving complete internal records and authoritative values. Add round
  events, deck counts, Wildling strength and piece reserves; remove duplicate
  house records, card dumps, numeric order legends and the board-wide dump.
- `card_tools.py` / `map_tools.py`: implement `cards_of_house` and `area_status`,
  and align card inspection and existing map tools with readable names and
  unit groups.
- `actions.py` / `protocol_tools.py` / `decision.py` / `legal.py`: expose exact
  order-name enums and unit-group selections, translate them to protocol IDs,
  and validate the requested choices without silent substitutions.
- `gameplay.py`: assemble the user message in the order above, ending with
  Current status; remove the appended exploration/completion boilerplate.
- `execution.py`: preserve the two-stage transcript and structured-output
  behavior. Use a short finalization-stage signal instead of restating the
  completion instructions in a new user message.
- `preparation.py`: review cache-key construction. It currently includes the
  changing action schema. Keep stable-prefix cache identity separate from
  per-decision schema fingerprints; retain the latter for tracing and validation.

## Acceptance checks

- Capture actual requests in both execution modes: stable text appears once,
  and the initial decision user message ends with Current status.
- Compare consecutive planning rounds: system-prefix text remains identical
  when configuration and map are unchanged; status and constraints update.
- Check scoring, power, missing values and status/observation consistency.
  Confirm internal IDs remain usable by validation but disappear from model text.
- Check current Westeros cards/descriptions, active effects, remaining deck
  counts after reshuffles, Wildling strength and private top-card visibility.
- Check reserves against configured limits after recruitment, upgrades and
  losses; confirm wounded pieces remain counted.
- Check used/unused card lookup for each house, disabled-card eligibility and
  card-description lookup by name without duplicated ability fields.
- Check area queries for occupied, empty and blocked areas, token/controller
  differences and hidden orders. Confirm unit-group actions preserve all
  meaningful distinctions and resolve deterministically to internal IDs.
- Check exact order enums, duplicate-token counts, starred limits and round
  restrictions; invalid combinations must fail rather than be substituted.
- Check that there is one house summary and no card/board dumps or protocol
  IDs reintroduced through model-facing history, guidance or tool results.
- Update schemas and callers together; preserve server validation, tool access,
  private memory isolation and all tracing.
- Compare cache hits and billed input cost on repeated requests; do not assume
  that moving text alone guarantees caching or a particular discount.
- Replay the context-comprehension probes with the new card/area tools, measuring
  retrieval use and accuracy as well as cost, and run the existing harness tests.
  Broader gameplay strategy changes remain outside this refactor.
