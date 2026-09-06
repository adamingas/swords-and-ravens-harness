# Raven Harness: System and Tool Guide

## 1. Purpose

Raven Harness lets a language model play *A Game of Thrones: The Board Game
(Second Edition)* through the Swords & Ravens game server. A human can play in
the normal Swords & Ravens browser client. Model players connect as separate,
authenticated users.

The harness gives each model three things:

- a player-scoped view of the current game;
- only the tools that apply to the current decision;
- private strategic memory and an optional official-rules oracle.

The model does not receive a WebSocket, credentials, or an unrestricted server
message tool. The Swords & Ravens server remains the authority for all game
rules and state changes.

The current harness does not give models a chat or negotiation tool. Add that
capability only after game traces show that it improves play without mixing
untrusted player text with system instructions.

## 2. System boundary

The local workflow has four running components: the Python harness, the
TypeScript game server, the webpack development server, and the human browser.
The model provider is external.

~~~text
Human browser ─────────────────────────────┐
                                           v
Model provider <── Python harness <──WebSocket──> Swords & Ravens server
                       │                           │
                       v                           v
                 data/harness.db             saved game JSON
~~~

The Python process serves the harness dashboard and REST API. It also owns one
WebSocket client for each active model player. SQLite stores agent settings,
model attempts, usage, game events, snapshots, state history, and strategic
memory.

The evaluation CLI is a separate orchestration process. It calls the canonical
harness directly and starts isolated game servers. Only the evaluation modules
contain house rotations, repeated-game schedules, prompt comparisons, and Elo
calculations. The dashboard server does not schedule a tournament or calculate
a ranking. Each normal agent record can select its own model.

Terms used in this guide:

- A **snapshot** is the complete game state that the server sends to one
  authenticated player.
- A **player-scoped** value contains only information that this player may see.
- A **leaf state** is the deepest active state in the server's nested state
  machine. It identifies the current decision.
- An **SDK item** is one persisted Agents SDK input, model output, tool call, or
  tool result.
- An **effective-context manifest** records what the harness selected from SDK
  history. At the SDK call-model filter, it records fingerprints for the
  parent input list and instructions. It does not hash the complete provider
  request or repeat the complete current observation.

From a source checkout, the default SQLite file is `./data/harness.db` and
relative data paths resolve from the harness repository. An installed wheel
stores default and relative data under the operating system's per-user
application-data directory. An explicit absolute `DATABASE_PATH` is unchanged
in both cases. Tests use temporary databases so that they do not change the
repository file.

The dashboard and REST API have no authentication and use plain HTTP. Keep the
default 127.0.0.1 host for local use. The SQLite file stores game tokens and
passwords as plain text. Prompts, traces, and player-scoped observations can
also contain private game information. Protect the data directory and do not
run two harness processes against the same file.

## 3. Start the system

### 3.1 Prepare the harness

Run these commands from the repository root:

~~~bash
git submodule update --init --recursive
uv sync
test -e .env || cp .env.example .env
~~~

Python 3.12 or later is required. The game server also requires Node.js and
npm. Run the harness, game server, and browser development server in separate
terminals.

Set OPENROUTER_TOKEN in .env. Then prepare the optional rules oracle:

~~~bash
uv run raven-prepare-rules
~~~

This command downloads the official rulebook and FAQ. It verifies both files
with fixed SHA-256 hashes. It writes sectioned text to data/rules.json. The
harness omits the oracle tool if this file does not exist.

Start the harness:

~~~bash
uv run raven-harness
~~~

Open <http://127.0.0.1:8787>.

The settings loader looks for .env in the current working directory. Start the
harness from the repository root unless you export the settings yourself.

### 3.2 Prepare the game server and browser client

Run these commands once:

~~~bash
cd swords-and-ravens/agot-bg-game-server
npx --yes yarn@1.22.22 install --frozen-lockfile --ignore-scripts
npm install --no-save --package-lock=false --ignore-scripts --legacy-peer-deps sass@1.77.8
npm run generate-json-schemas
~~~

Start the local game server on port 5001:

~~~bash
NODE_ENV=development PORT=5001 ./node_modules/.bin/ts-node -T src/server/server.ts
~~~

If `local-entire-game.json` contains a saved game, the server resumes it. For a
fresh game, stop the server and move that file to a private backup path before
you start the server again.

Start the human browser client in another terminal:

~~~bash
NODE_ENV=development \
GAME_SERVER_WEBSOCKET_URL=ws://localhost:5001 \
./node_modules/.bin/webpack-dev-server \
  --config webpack.client.dev.js --mode=development
~~~

Open <http://localhost:8080/static/#1> for local user 1. The local development
server creates room 1, makes user 1 its owner, and treats the URL fragment as
both the user ID and authentication token. Use #2, #3, and so on for other
local users. A deployed server requires accounts and a room to exist first.

For one human against five agents, use user 1 in the browser and create five
dashboard records with these shared fields:

| Agent field | Value |
| --- | --- |
| Model | Any model ID supported by the configured provider. The form starts with `MODEL_ID`. |
| Game server WebSocket | ws://localhost:5001 |
| Game / room ID | 1 |
| User ID and auth token | 2/2, 3/3, 4/4, 5/5, and 6/6 |

In the original browser client, first configure a six-player base game. Then
connect the five agents and use **Take one action** to let each choose an
available house. Take the remaining house as user 1 and launch the game. Enable
agent autoplay after the game starts.

## 4. Agent lifecycle

Use the dashboard to create one agent for each model-controlled user. Each
record contains one model ID, prompt, game URL, game ID, user ID, and
authentication token. The API never returns the token.

The harness does not create a Swords & Ravens room or account. The local
development server supplies room 1 and development identities. On a deployed
server, create the game and user identities first. Give each human and agent a
different user ID.

The lifecycle is:

1. Start opens the agent's WebSocket connection.
2. The client authenticates and receives a player-scoped full snapshot.
3. The manager updates the dashboard view after each server message.
4. Take one action runs one model decision.
5. Autoplay runs a decision when the server waits for that user.
6. Stop closes the connection. It does not delete the saved agent or traces.

After an established WebSocket connection fails, the client reconnects
automatically: it retries immediately, then uses capped exponential backoff.
Successful reauthentication supplies a new authoritative player-scoped
snapshot. Autoplay remains enabled, but a decision from the old connection
generation cannot send tools through the new socket. The harness never replays
an action whose delivery or acknowledgement is ambiguous; it makes another
decision only if the fresh snapshot still requires one.
The retry loop stops if the game server rejects authentication and marks the
session as banned. Correct the saved user ID or token, then reconnect manually.

This recovery applies while the harness process remains running. Agent records,
trace rows, and player-scoped snapshots survive a Python harness restart. The
dashboard shows the latest saved state and labels it as saved until the agent
reconnects. WebSocket connections, runtime state, and autoplay do not survive.
Reconnect the agents and enable autoplay again after a process restart.

An agent that owns the game can configure and launch the lobby. Setup sends the
settings and verifies the complete supported configuration in a fresh snapshot.
House selection, launch, and automatic lobby-ready responses also request a
fresh authoritative snapshot before they report success. A launch succeeds
when the game has started or the non-PBEM ready check is active. A ready
response succeeds when the user appears in the ready list or the response
started the game. Ready confirmation is transport work, not a strategic
decision.

Autoplay retries a failed model attempt while the same leaf-state ID remains
active. It disables autoplay at the configured failure limit. The default is
five consecutive failures for one leaf-state ID. Other snapshot data can
change without resetting this counter. The dashboard keeps the last error
visible.

## 5. What happens for one decision

The model is not continuously running. The WebSocket client observes changes
between decisions. The model sees state only when the harness starts a
`Runner.run` call. The following sequence applies to each required player
action.

1. The game server sends state changes and authoritative waitedForUserIds.
2. The harness confirms that the current user must act.
3. The harness creates a clean observation from the latest snapshot.
4. The harness selects tools for the active leaf state. It does not fall back
   to a recognized parent when the leaf is unknown.
5. The harness adds the history-recall and strategy-note tools. It also adds
   the rules oracle when prepared rules data is available.
6. The harness starts one Agents SDK run with the selected model and the
   player's recent model and tool items. It appends one complete current
   observation. The SDK can make more than one provider request inside that
   run.
7. The model can recall an older decision state, replace its durable plan, or
   ask the oracle.
8. The model must call exactly one gameplay tool.
9. Pydantic validates the tool arguments.
10. The tool checks the latest state again and sends typed server messages.
11. The harness requests a fresh player-scoped snapshot with sync-game.
12. The harness infers acceptance from a changed leaf state, changed turn
    ownership, a disappeared tool, or an occupied lobby seat.
13. The harness updates the automatic notebook when the SDK run returns. If
    the model queued a plan and the game action was accepted, the harness also
    saves that plan. It then saves the attempt and links the action to its
    source state.

Each decision is a new `Runner.run` invocation, but it is not a new
conversation. The Agents SDK stores the player's input messages, function
calls, function results, and model items in SQLite. By default, it reads the
latest 32 stored items before a decision. The harness removes every old full
observation from that window. It keeps later assistant and reasoning items,
plus gameplay function calls and results. It removes only old recall,
strategy-note, and rules-oracle calls and their matching results. These
support results remain available during the current SDK run, but they are not
replayed in a later decision. The harness then appends exactly one complete
current observation. The automatic strategic notebook and state-history index
are inside that observation.

The filter also discards an incomplete prefix when the 32-item window starts
in the middle of an older decision. The raw SDK rows remain in SQLite. Thus,
the audit history is complete while repeated board states do not inflate the
provider request. The 32-item setting bounds recent model and tool continuity;
it is not a token limit. Tool schemas, instructions, the current observation,
and several provider requests inside one SDK run can still use many tokens.
The structured notebook and `recall_game_state` preserve selected information
beyond the recent window.

This hybrid design gives the model conversational continuity and keeps each
attempt inspectable from local data. It does not guarantee deterministic replay
because model providers and the live game server are external systems.

The history table stores the base player observation, before strategic memory,
historyIndex, planning constraints, and previousAttemptError are added. The
current state is recorded before historyIndex is built, so the first history
entry can describe the present decision. recall_game_state(1) skips that entry
and returns the previous distinct recorded decision state. The recalled base
observation excludes strategic overview, memory, planning constraints,
historyIndex, and the prior error. Its action can be null if no action was
accepted from that state. History is recorded when the harness prepares a model
run. The separate `player_snapshots` table stores every distinct snapshot from
the game server, including states that do not require a model decision.

Short visible output does not mean that the model received little state. A
simple choice can need only a short function call while its input includes the
current board, recent conversation, tools, and memory. The current state is sent
again for each decision.

## 6. The model observation

The observation is JSON. It contains no credentials. Its main fields are:

| Field | Content |
| --- | --- |
| game | Game ID, state ID, phase, round, victory target, and maximum rounds. |
| you | House, resources, controlled regions, score, and available house cards. |
| isYourTurn | Whether the server currently waits for this user. |
| pendingDecision | Data from the deepest active game state. |
| statePath | Nested state types from the game root to the active state. |
| recentEvents | Up to 12 compact server events and game-log entries. |
| orderLegend | Mapping from upstream physical order-token IDs to readable order names. |
| lobby | Lobby houses, available house IDs, seats, and ready users. Present only before launch. |
| map | Stable region types, icons, castles, and adjacency data. |
| houses | Public score, control, power, and supply data for all houses. |
| houseCardStatus | Public available-card details and available, used, and disabled counts for each house. Used-card identities are omitted. |
| tracks | Iron Throne, Fiefdoms, and King's Court order. |
| board | Occupied, controlled, garrisoned, or ordered regions, their units, and any currently revealed order. |
| revealedOrders | Orders in the server's public post-reveal order map, with region and readable token name. |
| actionGuidance | Harness-derived base-game sources, targets, units, and choices for march, raid, mustering, consolidate-power, and Raven states. |
| strategicOverview | A deterministic score and resource summary. |
| strategicMemory | The player's private structured notebook. |
| historyIndex | A compact index of the current recorded decision state and earlier decision states. |
| planningConstraints | Starred-order limits, active order restrictions, per-category assignment capacities, and the number of restricted dummy orders required by exhausted token inventory. |
| previousAttemptError | The most recent error in the current connected session. It is usually an autoplay retry error, but is not guaranteed to belong to the same leaf state. |

The map reference is complete, but the board field is sparse. Empty regions
without a garrison, control token, or revealed order do not appear in board.
Use map for adjacency and printed board features. Use board for current pieces,
control, and revealed orders.

House-card status uses only cards present in this player's upstream snapshot.
It exposes the card faces that the normal client shows as available and reports
used and disabled totals without copying hidden card identities. When the
upstream server hides a house's cards, `detailsVisible` is false and the harness
does not infer them. The harness builds `revealedOrders` only from
`ordersOnBoard`, which the server fills after orders are revealed. It never
copies private `planning.placedOrders` into that public field.

This shortened planning observation shows the shape. A real observation
contains the complete map, all public houses, the full sparse board, the
automatic notebook, and up to 12 history entries.

~~~json
{
  "game": {"id": "1", "stateId": "leaf-2", "phase": "place-orders", "round": 1},
  "you": {
    "userId": "2",
    "houseId": "stark",
    "powerTokens": 5,
    "supply": 2,
    "controlledRegions": ["winterfell", "white-harbor"]
  },
  "isYourTurn": true,
  "pendingDecision": {"type": "place-orders", "readyHouses": []},
  "statePath": ["ingame", "planning", "place-orders"],
  "board": [
    {
      "id": "winterfell",
      "units": [{"id": 1, "type": "footman", "allegiance": "stark"}]
    }
  ],
  "actionGuidance": null,
  "strategicMemory": {
    "roundNumber": 0,
    "situationAssessment": "",
    "objectives": [],
    "modelPlan": ""
  },
  "historyIndex": [{"stateId": "leaf-2", "phase": "place-orders"}],
  "planningConstraints": {
    "requiredAssignmentCount": 2,
    "maxStarredOrders": 1,
    "maxAssignmentsByOrderCategory": {
      "march": 3,
      "defense": 3,
      "support": 3,
      "consolidate_power": 3,
      "raid": 3
    }
  }
}
~~~

## 7. How the harness limits illegal actions

The harness uses four checks.

1. **Tool selection:** The model sees gameplay tools only for the active state.
2. **Tool schema:** Pydantic rejects missing fields, wrong types, and extra
   fields. Some tools also receive state-specific enum or range constraints.
3. **Runtime check:** Immediately before a send, the tool checks the latest
   state and turn ownership. Base-game raid, march, mustering,
   consolidate-power, Raven replacement, unit selection, region selection, and
   tie-resolution tools also validate state-specific values locally.
4. **Snapshot inference:** The harness fetches a new authoritative snapshot and
   checks for evidence that the action was processed.

Two narrow corrections avoid wasting another model request. An ineligible
March control-token request is applied as false. Mustering treats recruitments
as a priority-ordered list and omits later new units that do not fit Supply.
The accepted action trace records the applied arguments and an omission count
or flag; the raw SDK response still records the model's original tool call.

The canonical harness supports a six-player base game with vassals disabled.
PBEM mode and the victory-point target remain configurable. It exposes no
protocol tool when the snapshot omits the setup or player-count identity, or
identifies another setup, player count, or an explicitly enabled vassal mode.
The upstream serializer normally omits `vassals: false`. Most post-action tests
infer acceptance from the next authoritative snapshot. A model can still make
a bad attempt. A server transition can also make acceptance ambiguous.

`submit_orders` is the exception. The harness sends the complete planning draft
as one correlated request. The game server validates the complete draft before
it changes the board, then sends a private acceptance or rejection response.
The harness requests a fresh player-scoped snapshot after that response. A
connection failure can still hide a response, so the harness does not replay
the request automatically.

For an unknown state, the harness exposes no gameplay tool. This fail-closed
behavior makes missing state coverage visible.

## 8. Strategic gameplay tools

These tools use state-specific schemas and local legality checks.

| Tool | Availability and effect |
| --- | --- |
| choose_house(house_id) | Lobby only. Join one currently available house. |
| choose_option(choice_index) | A simple-choice prompt. Select one offered zero-based index. |
| select_house_card(house_card_id) | A house-card selection prompt. Select one offered card. |
| choose_combat_house_card(house_card_id, force_valyrian_blade_decision) | Combat card selection. Play one currently choosable card. A true blade flag prevents automatic skipping when a blade decision can apply; it cannot make an unavailable blade decision appear. |
| submit_bid(amount) | A bidding prompt. Submit zero through the player's current power-token limit. |
| select_orders(region_ids) | Select the exact required count of distinct offered regions. |
| declare_support(house_id) | Support the attacker or defender, or use none to refuse. |
| submit_orders(assignments) | Planning. Set the requested number of semantic orders in distinct eligible regions, replace any partial draft, and mark the house ready. |

Each `submit_orders` assignment has `region_id`, `order`,
`starred_preference`, and `priority`. Valid order categories are `march`,
`defense`, `support`, `consolidate_power`, and `raid`. Set
`starred_preference` to `prefer` or `avoid`, and use `priority` from 0 through
100 to rank the importance of that region relative to the other assignments.

The tool enforces the three-token inventory for each category, the King's
Court starred-order limit, and active Westeros restrictions. The harness
allocates concrete modifiers and physical token IDs deterministically. It gives
scarce starred tokens and stronger March modifiers to preferred,
higher-priority assignments first. `planningConstraints.requiredAssignmentCount`
is normally the number of occupied regions. If the house has more occupied
regions than usable base-game tokens, it is smaller and the model chooses which
regions receive no order. When normal tokens are exhausted, the server permits
the minimum necessary restricted tokens; the harness sends normally legal
tokens before those forced dummy orders.
`planningConstraints.maxAssignmentsByOrderCategory` and the state-specific
tool description give the usable maximum for each family in the current state.

This allocator covers the 15 standard player order tokens used by the base
game. Optional sea-order and Iron Bank order tokens are not yet model-facing.

When `maxStarredOrders` is greater than zero, the normal starred limit is
strict. When it is zero and normal inventory is exhausted, the upstream server
requires the minimum number of otherwise restricted starred tokens as dummy
orders. The harness permits only that forced exception.

Example:

~~~json
{
  "assignments": [
    {
      "region_id": "winterfell",
      "order": "march",
      "starred_preference": "prefer",
      "priority": 90
    },
    {
      "region_id": "white-harbor",
      "order": "support",
      "starred_preference": "avoid",
      "priority": 70
    },
    {
      "region_id": "the-shivering-sea",
      "order": "raid",
      "starred_preference": "avoid",
      "priority": 40
    }
  ]
}
~~~

For this example, the full path is:

1. The current leaf state is `place-orders`.
2. The harness builds the observation and offers only `submit_orders` plus the
   support tools.
3. The model calls `submit_orders` with the JSON above.
4. Pydantic checks the object shape. The harness checks region eligibility,
   order inventory, starred limits, and current turn ownership.
5. The harness converts semantic orders to physical order tokens. It sends one
   complete `submit-orders` request.
6. The server validates the full draft before mutation and sends a private
   correlated response. The client then requests `sync-game` and replaces its
   state with the returned player-scoped snapshot.
7. SQLite stores the input observation, instructions, offered tool schemas,
   SDK response items, selected arguments, usage, timing, and any error.

## 9. Core protocol gameplay tools

These tools translate typed model input to one Swords & Ravens message. The
active state controls when each tool is visible.

| Tool | Exact leaf state | Effect |
| --- | --- | --- |
| `resolve_raid(order_region_id, target_region_id)` | `resolve-raid-order`; `resolve-single-raid` | Resolve a raid. Base-game schemas list exact source and target regions. Use a null target to discard the order. |
| `resolve_march(starting_region_id, moves, leave_power_token)` | `resolve-march-order`; `resolve-single-march` | Resolve one march. Each move gives a destination and exact unit IDs. An empty move list discards the march. Unattainable neutral forces are excluded, and the selected army's neutral-force strength is checked locally. |
| `select_units(selections)` | `select-units`; `resolve-retreat` | Select exact units grouped by current region for a retreat, removal, or another effect. |
| `auto_reconcile_armies()` | `reconcile-armies`; `player-reconcile-armies` | Compute and submit the smallest deterministic set of removals that satisfies the current supply limit. |
| `muster_units(musters)` | `mustering`; `player-mustering` | Recruit or upgrade units at legal mustering castles. Base-game mode, origin, destination, piece, points, and supply checks run locally; later Supply-unsafe new units are omitted. |
| `skip_mustering()` | `mustering`; `player-mustering` | Finish the current mustering decision without recruits. |
| `resolve_track_ties(ranked_tie_groups)` | `resolve-ties` | Rank each displayed tied group from highest to lowest. |
| `use_valyrian_steel_blade(use)` | `use-valyrian-steel-blade` | Use or decline the blade in the current combat. |
| `replace_raven_order(region_id, order_id)` | `replace-order`; `use-raven` | Replace one revealed order with an available physical order token. Base-game region/token pairs are checked locally. |
| `skip_raven_order_replacement()` | `replace-order`; `use-raven` | Decline Messenger Raven order replacement. |
| `inspect_top_wildling_card()` | `replace-order`; `use-raven` | Use the Messenger Raven to inspect the top Wildling card. |
| `place_inspected_wildling_card(destination)` | `see-top-wildling-card` | Return the inspected card to top or put it on bottom. |
| `select_region(region_id)` | `select-region`; `resolve-retreat` | Select one region for the current prompted effect. |
| `select_westeros_card(deck_id, card_id)` | `select-westeros-card` | Select a displayed card from a Westeros deck. |
| `resolve_consolidate_power(region_id, choice)` | `resolve-consolidate-power`; `resolve-single-consolidate-power` | Resolve one base-game order. Choose `gain_power_tokens`, or choose `muster_units` for a starred order on a castle. |
| `call_for_support_against_neutral_force()` | `resolve-single-march`, before a support request | Ask for support during a march against a neutral force. The harness exposes it only when a reachable neutral force has at least one eligible foreign supporting house. |

`UnitMove` has `destination_region_id` and a non-empty `unit_ids` list.
`RegionUnits` has `region_id` and a non-empty `unit_ids` list. A recruitment
has `unit_type`, `region_id`, and `upgrade_from_footman`. Set the boolean when
the target unit should replace an existing Footman; the harness selects the
engine-compatible Footman internally. `muster_units` requires a non-empty
`musters` list. Each muster group has `mustering_region_id` and a non-empty
`recruitments` list. Recruitment order is priority order. Legal upgrades are
kept because they do not change army size; later new units that would exceed
Supply are omitted. If every requested new unit is unsafe, the harness submits
an empty mustering plan to finish the decision.

`leave_power_token=true` requires an eligible land source and every listed
source unit to leave. When no offered source is eligible, the state-specific
schema fixes this field to false. The runtime also converts an illegal true
value to false and records `omitted_illegal_power_token=true` in the applied
action. Neutral-force destination guidance includes the required strength and
the feasible moving-unit groups.

Mustering guidance includes the current Supply level, the allowed army-size
slots, each current army, and every single-unit region. Each destination also
has `supplySafeNewUnitsWhenChosenAlone`. That number applies only when the
model adds units to that one destination. Combined recruits are applied in the
submitted priority order through the full local Supply validator.

## 10. Private support tools

Support tools do not end the required gameplay decision. The two memory tools
are available in every model run. The rules oracle is available only when the
prepared rules data is loaded. The harness rebuilds the factual fields in
`strategicMemory` after an accepted action. The model can write only the
`modelPlan` text through `remember_strategy`.

### recall_game_state(turns_ago)

This tool returns one earlier stored base observation and the action selected
from it. `turns_ago` is from 1 through 50. The current observation already
contains a 12-entry history index, including the present recorded state, so use
recall only when exact old data can change the decision.

### remember_strategy(note)

This tool queues a private replacement for `strategicMemory.modelPlan`. The
note is plain text from 1 through 2,000 characters. Use it only when the
durable multi-round plan changes. The harness saves the note only after the
same SDK run completes an accepted gameplay action. A failed, cancelled, or
no-action run does not change the stored plan.

### ask_rules_oracle(question)

The question must contain 3 through 1,200 characters. This tool starts a short
child-agent run with the same model as the player. The
oracle sees a catalog of 14 rulebook and FAQ sections. Its private
`read_rulebook_sections` tool can read one or two sections before it answers
the focused question. The parent player never receives that internal tool. The
oracle must not choose strategy or a game action.

The oracle exists because recorded games showed repeated rules problems. Seven
planning runs repeated order-restriction, starred-order, and physical-token
errors before the oracle was added. Later testing also showed that extracted
PDF text omitted the graphical Supply chart. The harness now appends a verified
text transcription of that chart to the Supply section. See
[Evidence for the rules oracle](RULES_ORACLE_EVIDENCE.md) for the bounded trace
evidence and source database digests.

The parent model receives the answer and must still call one gameplay tool.
The trace stores each completed oracle question, answer, section read, child
response item, token count, response ID, and provider-reported cost. The
harness keeps that oracle trace even if the parent call later fails or is
cancelled.

## 11. Persistence and traces

The harness schema has six core tables. The Agents SDK adds two conversation
tables when the first session-backed run starts:

| Table | Stored data |
| --- | --- |
| agents | Agent identity, model, prompt, connection settings, and credentials. Treat this local file as sensitive. |
| agent_events | Compact connection, protocol, autoplay, and run events. Authentication tokens are redacted from event payloads. |
| agent_runs | One model attempt: observation, effective-context manifest, instructions, tool definitions, serialized Agents SDK result items, returned usage, action, error, and timing. Nested-oracle records are appended to those items. |
| game_state_history | One player-scoped base observation per distinct state at which a model run was prepared, plus the accepted action selected from that state. |
| strategic_memories | Current private notebook and revision number for each agent. |
| player_snapshots | Each distinct player-scoped WebSocket snapshot. Each row contains the complete serialized snapshot. |
| agent_sessions | One persisted Agents SDK conversation identity per player. |
| agent_messages | The input, model, tool-call, and tool-result items used for recent conversational continuity. |

The harness records failed attempts. A failure is evidence about model or tool
reliability and must remain available for evaluation. A failed parent call
keeps each oracle interaction that completed before the failure. A provider
exception can still prevent the SDK from returning partial parent response
items or parent usage. The harness always stores the error and elapsed time.

The database uses schema version 3. The server creates only this schema and
rejects every other existing version. It does not migrate old databases. Use a
new `DATABASE_PATH` when the schema is incompatible. A model attempt stores an
effective-context manifest when it reaches the model runner, including runner
errors and cancellations. The field is null when observation or tool
preparation fails first. Deleting an agent permanently removes its events,
runs, snapshots, history, memory, and SDK conversation.

Useful endpoints are:

~~~text
GET    /api/health
GET    /api/dashboard
GET    /api/models              provider and default model for new agents
GET    /api/agents
POST   /api/agents
GET    /api/agents/{agent_id}
DELETE /api/agents/{agent_id}
POST   /api/agents/{agent_id}/start
POST   /api/agents/{agent_id}/stop
POST   /api/agents/{agent_id}/run
POST   /api/agents/{agent_id}/autoplay
POST   /api/agents/{agent_id}/lobby/setup
POST   /api/agents/{agent_id}/lobby/house
POST   /api/agents/{agent_id}/lobby/launch
GET /api/agents/{agent_id}/observation
GET /api/agents/{agent_id}/tools
GET /api/agents/{agent_id}/events
GET /api/agents/{agent_id}/runs
GET /api/agents/{agent_id}/runs/{run_id}
GET /api/agents/{agent_id}/metrics
GET /api/agents/{agent_id}/memory
GET /api/agents/{agent_id}/history
GET /api/agents/{agent_id}/snapshots?limit=80
GET /api/agents/{agent_id}/snapshots/{snapshot_id}
~~~

The list endpoints return the latest 80 events, runs, or snapshot metadata.
Use the snapshot-detail endpoint for one complete snapshot. This avoids large
repeated dashboard responses. SQLite retains older rows. Use the run-detail
endpoint or query the database for experiment export.

The dashboard header totals the agent count, model runs, failures, tokens, and
provider-reported cost. Open an agent to see its available house cards and
card abilities. The agent view also shows public card availability for every
house, units, controlled regions, and public standings. It shows occupied board
regions, currently revealed orders, current action guidance, and influence
tracks. The remaining panels show model usage, run traces, snapshots, and
memory. Board rows are intentionally sparse. They contain only occupied,
garrisoned, controlled, or currently ordered regions.

The dashboard distinguishes a live state from the latest saved state. A saved
state includes its capture time. It is useful after a harness restart, but it
does not mean that the agent still has the turn. Each dashboard record contains
`stateStatus.actionable`; it is true only for a live state that requires this
player to act. Reconnect the agent before you run a model action or enable
autoplay. The observation endpoint returns only a live session observation and
reports an error while the agent is stopped. The dashboard alone reconstructs
its compact monitor view from the latest saved snapshot.

While a run is active, the agent card shows whether the harness waits for a
model response or invokes a tool. It also shows the last five lifecycle steps.
The Overview tab shows the last eight steps for the current or most recent
run. These steps survive a server restart because they use `agent_events`.
They contain only bounded metadata: occurrence time, run and response IDs,
model and phase, offered tool names, request and tool sequence numbers, input
and output item counts, duration, and token totals. They do not contain prompts,
observations, tool arguments, tool results, or credentials.

Provider-native usage can include cached tokens, reasoning tokens, and cost.
The standard usage object contains request, input-token, output-token, and total
token counts. Per-agent metrics report separate request-input distributions for
the gameplay agent and rules oracle. A provider request is not the same as an
SDK run. One SDK run can contain several requests.

The metrics response has these groups:

| Key | Meaning |
| --- | --- |
| runCount; statusCounts | Attempt total and completed, failed, or cancelled totals. |
| modelRequests | Accumulated standard SDK request count for a gameplay run, including nested oracle requests. |
| tokens.input; output; total | Standard accumulated token counts. |
| tokens.cachedInput; cacheWrite; reasoning | Provider-native detailed token counts when reported. |
| tokens.maxInputInRun | Largest accumulated standard input count for one SDK run, including nested oracle work. |
| requestInputTokens | Reported request count and average, p50, p90, p99, and maximum input for gameplay-agent provider requests. |
| rulesOracleRequestInputTokens | The same distribution for rules-oracle provider requests. |
| costUsd | Sum of provider-native cost fields. |
| durationMs | Total, average, and maximum attempt duration. |
| historicalStates | Number of distinct stored decision states. |

A run detail includes this context manifest:

| Field | Meaning |
| --- | --- |
| policy | Name of the active context-selection policy. |
| sessionHistoryLimit | Maximum SDK items read from the session. |
| retrievedHistoryItemCount | Items returned by the session read. |
| discardedPrefixItemCount | Items discarded before the first complete decision boundary. |
| removedObservationItemCount; removedObservationCharacters | Old full observations removed from the request. |
| removedSupportToolItemCount; removedSupportToolCharacters | Old recall, strategy-note, and oracle call/result items removed from the request. |
| selectedHistoryItems | History items selected by the harness callback. The SDK can still normalize, deduplicate, or prune these items. |
| currentInputItemCount; currentInputCharacters; currentInputSha256 | Size and fingerprint of the one current observation input. |
| modelRequestInputs | Item count, character count, and SHA-256 fingerprints for the parent input list at the SDK call-model filter. The field also fingerprints the instructions. The SDK can still deduplicate items afterward. It is not a hash of tools, settings, metadata, model ID, or provider serialization. |

The current observation itself is stored beside the manifest. The manifest
does not store API keys. Recorded duration begins before observation
preparation and includes time waiting for the process-wide model semaphore.
The 300-second model-run timeout begins only after that semaphore is acquired.

An agent that has connected successfully stays started across transient game
WebSocket failures. Its runtime becomes reconnecting, autoplay remains enabled,
and authentication is retried with an immediate attempt followed by capped
exponential backoff. A reconnect authentication response is the authoritative
player-scoped resynchronization. The harness never replays an action whose send
or acknowledgement was interrupted; it starts a fresh decision only after the
new snapshot shows that the player still needs to act.
The retry loop ends if authentication is rejected and the runtime becomes
`banned`. Fix the saved credentials and reconnect manually.

A zero cost value can mean that a provider omitted its cost field. It does not
always mean that the request was free. Git ignores root `data/*.db`,
`data/*.db-shm`, `data/*.db-wal`, `data/*.json`, and `data/evaluations/`.
Evaluation artifacts stay next to the code but are not committed; back them up
separately when needed.

## 12. Provider behavior

The default model is z-ai/glm-5.3-flash through OpenRouter. `MODEL_ID` selects
the initial model value in the new-agent form. Each agent record can use a
different model that the configured endpoint supports. Provider fallback can
select another host for the model requested by that agent. It does not change
the model ID.

If `OPENROUTER_TOKEN` is empty, the harness uses the direct OpenAI-compatible
base URL and key. Set `MODEL_ID` to a model supported by that endpoint before
creating agents.

MODEL_API_MAX_RETRIES controls OpenAI-client retries for connection failures and
selected transient HTTP responses. The default two means two retries after the
initial request.
OPENROUTER_ALLOW_FALLBACKS controls OpenRouter host fallback.
MODEL_REQUEST_TIMEOUT_SECONDS limits one provider attempt.
MODEL_RUN_TIMEOUT_SECONDS limits the complete Agents SDK run.
MODEL_MAX_CONCURRENCY limits simultaneous model runs. The default is one to
avoid overloading low-cost providers.
MODEL_SESSION_HISTORY_ITEMS limits the recent Agents SDK conversation window.
The harness filters old observation inputs from that window before the model
request. It does not delete them from SQLite.
AUTOPLAY_MAX_CONSECUTIVE_FAILURES limits failed attempts for one unchanged
game decision. AUTOPLAY_RETRY_BASE_SECONDS controls exponential retry backoff;
the delay is capped at 30 seconds.
Validation and upstream non-acknowledgement errors are returned to the model
inside the same SDK run. The run stops only after the harness records an
accepted gameplay action. Provider account, quota, and authentication failures
stop autoplay for all running agents immediately. Persisted and API-visible
error text redacts credential assignments, sensitive URL parameters, and
provider key-management identifiers.
OPENROUTER_PROVIDER_ORDER is a comma-separated preferred host order. It
defaults to Reka, Cloudflare, CoreWeave, Fireworks, DeepInfra, and Together.
OpenRouter tries those hosts in order and uses the same list as an allow-list
by default. Reka is first because it completed the existing GLM tool-call
smoke runs.
Host fallback remains enabled within that list, and the OpenAI client retries
the ordered pool on retryable failures. Set
`OPENROUTER_ALLOW_UNLISTED_PROVIDERS=true` to permit other same-model hosts.
OPENROUTER_PROVIDER_SORT is used only when the explicit order is empty.
`OPENROUTER_REQUIRE_PARAMETERS` remains available for simpler request shapes,
but it is off by default because OpenRouter rejects the Agents SDK request when
this filter is enabled.

| Mechanism | Default |
| --- | ---: |
| WebSocket authentication wait | 10 seconds |
| Authoritative snapshot wait | 10 seconds |
| WebSocket ping interval | 30 seconds |
| Autoplay polling interval | 0.75 seconds |
| Model request timeout | 45 seconds per attempt |
| Model API retries | 2 |
| Complete model-run timeout | 300 seconds after queue acquisition |
| Concurrent model runs | 1 |
| Parent Agents SDK turns | 6 |
| Rules-oracle turns | 3 |
| Maximum model output | 16,384 tokens |
| Recent conversation window | 32 SDK items |

For a controlled harness comparison, assign the same exact model ID to every
player. Rotate houses and user IDs between games.

## 13. Optional OpenTelemetry export

SQLite is the authoritative local trace store. The harness can also export one
span per `run_once` invocation to any OTLP/HTTP trace collector. Every span
starts with agent, game, and model identifiers. After a run starts, the span
also records its run ID and sanitized lifecycle events for the model run,
provider requests, and tool calls. These events contain indexes, tool names,
durations, item counts, and token totals. A successful decision adds its chosen
action, input/output token totals, and cost. Cost is zero when the provider
omits it. A failed invocation records a sanitized exception and error status.
An invocation that fails before model-run setup can lack a run ID.

Spans do not export prompts, observations, credentials, tool arguments, tool
results, or response bodies as attributes. Failed spans include exception
events, and a sanitized exception message can contain model output. Treat the
OTLP collector as sensitive.

For a local Phoenix viewer, start Phoenix in a separate terminal:

~~~bash
uvx arize-phoenix serve
~~~

Then add this setting to `.env` and restart the harness:

~~~text
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:6006/v1/traces
~~~

Open <http://localhost:6006> to inspect the spans. See the
[Phoenix self-hosting configuration](https://arize.com/docs/phoenix/self-hosting/configuration)
and the
[OpenTelemetry Python exporter guide](https://opentelemetry.io/docs/languages/python/exporters/)
for other deployment and collector options. OTLP export is optional; an empty
endpoint disables the harness-created exporter.

## 14. Required game-server extensions

The submodule contains small extensions for machine clients:

- GAME_SERVER_WEBSOCKET_URL configures the browser client's WebSocket URL.
- Authoritative waited-user IDs identify which model must act.
- sync-game and game-snapshot provide a correlated player-scoped refresh.
- availableHouseIds limits lobby choices to the selected setup.
- House snapshots include authoritative score, control, and supply totals.
- HARNESS_TEST_MAX_TURNS shortens development smoke games only.
- LOCAL_GAME_PATH selects an isolated local saved-game JSON.
- Nested raid and reconciliation states serialize explicit type names.

By default, the game server stores its current local game in
swords-and-ravens/agot-bg-game-server/src/server/website-client/local-entire-game.json.
Stop the server before you replace this file to create a fresh local lobby.
This file is tracked inside the submodule, so normal play makes the submodule
dirty. Do not commit a saved game that contains private state.

The local saved-game JSON is written only after a game starts and can contain
private player state. Treat it as sensitive.

## 15. Six-model tournament

`raven-evaluate` runs isolated six-player games. Each game contains these exact
OpenRouter model IDs:

- `z-ai/glm-5.3-flash`
- `qwen/qwen3.7-flash`
- `openai/gpt-oss-120b`
- `~deepseek/deepseek-v4-flash-latest`
- `qwen/qwen3-235b-a22b-2507`
- `openai/gpt-5.6-luna`

All six models receive the same `strategic-v1` harness. They receive the same
system prompt, tool-selection policy, state representation, memory behavior,
retry limits, and output limit. The legal game state determines which tools a
model can use on a turn. Models rotate through all six houses twice across 12
games. Local user IDs rotate too, so each model owns two lobbies.
Evaluation requires prepared rules data. Run `uv run raven-prepare-rules`
before the smoke game.

The command checks the OpenRouter key and live model catalog once. It does this
before it creates the output directory and schedules attempts. It stops when
the key's spending limit is exhausted. It also stops when an exact model ID is
absent or lacks tool-call support. The manifest records the catalog data and
the target of an alias. These checks do not write the key to an artifact.

The tournament requires `OPENROUTER_TOKEN` and ignores `MODEL_ID`. It does not
use the dashboard's provider allow-list. It uses one routing policy for all
models. The policy allows all listed hosts and provider fallbacks. It selects
hosts by throughput and requires support for the request parameters.

The harness sends stable provider prompt-cache keys. Player calls use a key for
the model and current tool set. Rules-oracle calls use a separate key for the
model and rulebook. The harness does not keep a local response cache. A
provider decides whether to cache a request. The summary includes cached input
tokens when the provider returns them.

Start with a one-round smoke:

~~~bash
uv run raven-protocol-smoke
uv run raven-evaluate --games 1 --max-rounds 1 \
  --output data/evaluations/model-tournament-smoke
~~~

`raven-protocol-smoke` starts the real TypeScript server and six harness
clients. A deterministic runner finishes two rounds without a model provider.
It must exercise planning submission, Raven inspection, Raid, March, combat
card selection, and consolidate-power resolution. It records the actual tool
counts and sequence in `smoke.json`. It also proves that one rejected draft
does not change the submitting player's state and that another player sees
only hidden planning orders. It fails closed at an unexpected required
decision and writes `harness.db`, the saved game, result, and server log below
`data/evaluations/`. This test verifies the protocol and persistence path. It
does not replace the paid model smoke.

Verify saved evaluation artifacts without a provider request:

~~~bash
uv run raven-verify-evaluation data/evaluations/model-tournament-smoke
uv run raven-verify-evaluation --require-complete \
  data/evaluations/model-tournament
~~~

The verifier checks stored catalog data, seeds, rotations, assignments, and
results. It checks the terminal saved winner and the integrity of each SQLite
file. It also checks requested and resolved model IDs, the common harness
prompt, provider and cost attribution, and the recomputed summary. A valid
partial run exits successfully and reports `provisional`. `--require-complete`
exits with status 2 until 12 games are complete. Each model-house pair must
have two completed games. Every provider response must have model, provider,
and cost attribution. Invalid or corrupt artifacts exit with status 1.

Then run the complete comparison:

~~~bash
uv run raven-evaluate --games 12 \
  --random-seed 1 \
  --concurrent-games 12 \
  --output data/evaluations/model-tournament
~~~

The runner starts independent games concurrently. Each active game has one
TypeScript server and six clients. Game 1 uses port 5101 by default. Each later
game uses the next port. A 12-game run uses ports 5101 through 5112. The
`--concurrent-games` value limits the number of active games. Its default is
12. At this value, the command starts 12 servers and 72 clients. The default
`MODEL_MAX_CONCURRENCY=1` permits one active model call in each game, or up to
12 calls across the evaluator. Reduce `--concurrent-games` when the machine or
provider cannot support this load.

A completed attempt contains `game.json`, `harness.db`, assignments,
`provider-generations.json`, a server log, and a result. Progress data is
written during a long game. A failed or cancelled attempt can contain fewer
files because failure can occur at any stage. The manifest always records the
attempt status and known error. Provider data is collected when the database
exists. The
manifest records source commits, harness prompt and rules hashes, the exact
model set, model settings, provider routing, the base random seed, and the fixed
house and user schedule.
The evaluator derives a distinct uint32 seed for each game and reuses it for
every attempt of that game. The game result records the exact seed, and the
verifier checks it against the schedule. Client-only hidden-deck shuffles use a
separate secure source, so connects and reconnects do not consume the gameplay
random stream. API keys are not recorded. Reusing the same output directory
preserves failed and cancelled attempts. The default is fail-fast: one failed
game cancels unfinished sibling games. Use `--continue-on-error` to keep those
games running. An exact rerun skips completed games and starts a new attempt
for each incomplete game. A resume must use the same source, rules, game count,
seed, port, concurrency, round limit, polling values, timeouts, and model
settings.

The seed makes fresh game-server randomness reproducible. It does not make the
model provider deterministic. Restoring an arbitrary mid-game save also does
not restore the process-local random-generator position.

The provenance check ignores only the upstream local saved-game JSON because
normal play changes that file. It still rejects changes to harness source,
upstream source, or the recorded submodule commit.

Completion requires a matching terminal winner in the live observation and
the stable saved JSON. The runner also executes SQLite `PRAGMA quick_check`.
`summary.json` reports wins, placement, victory points, reliability, provider
requests, input/output/total/cached token counts, cost, house effects, and a
stated pairwise Elo calculation. It also reports the completed-game count for
each model-house pair. A ranking is `provisional` until 12 games are complete,
every pair has two games, and provider attribution is complete.
`comparisonComplete` is true only when these conditions are met.

## 16. Verify changes

Run the Python checks from the repository root:

~~~bash
uv run ruff check src tests
uv run pytest -q
~~~

Run the game-server checks from swords-and-ravens/agot-bg-game-server:

~~~bash
npx tsc --noEmit
npm run generate-json-schemas
~~~

Use HARNESS_TEST_MAX_TURNS=1 only for lifecycle smoke tests. Do not set it for a
normal game.
