# Raven Harness

We are building a harness that lets language models play *A Game of Thrones:
The Board Game (Second Edition)* through Swords & Ravens, alongside humans or
other models. We use games and recorded traces to improve how agents understand
the board, use tools, retain strategy, and choose actions, and to compare models.

## What lives here

- `src/raven_harness/`: the Python harness, model runner, dashboard, and evaluation tools.
- `swords-and-ravens/`: the upstream TypeScript game server and human browser client,
  included as a Git submodule. The server owns the rules and authoritative game state.
- `tests/`: automated checks for the harness and its game integration.
- `docs/`: detailed operating instructions, harness documentation, and investigations.
- `data/`: local databases, rules data, game saves, and evaluation outputs.

The harness connects each model player to the game server as a separate user over
WebSocket. Humans use the original Swords & Ravens browser client. The Python
dashboard lets an operator connect agents, run individual decisions, enable
autoplay, and inspect activity, traces, token usage, and cost.

## How an agent plays

The model is not continuously running. The harness watches the game between
decisions and invokes the model when that player needs to act.

1. The server updates the player's view of the game and identifies who must act.
2. The harness builds an **observation**: JSON describing the current board,
   player resources, visible information about other houses, recent events,
   and the pending decision. It contains only information that player may see.
3. A **decision** is one required choice, such as placing orders, resolving a
   march, bidding for influence, choosing a combat card, or retreating. One game
   round contains many decisions; the same kind of decision can recur.
4. A new **model run** starts with the current observation, a briefing for that
   decision, private strategic memory, and tools suited to the task. Static rules
   and the map are supplied in the system prompt.
5. Within that run, the model can make several tool calls and provider requests
   to inspect the map, cards, rules, or history before returning a structured action.
   An exploration tool call continues the same decision; it is not a new turn.
6. The harness validates the action against the current decision and sends it
   to the game server. It checks the resulting state for acceptance and records
   the outcome. Autoplay invokes the model again when another decision is needed.

Players who must decide simultaneously can run concurrently. A server update
does not automatically require a model run for every player.

## Context and memory between decisions

Each decision receives the full current observation. Earlier decisions' model
messages and tool exchanges are excluded from the next decision's model input.
Continuity comes from a private strategic notebook, a compact history index,
recent events, and a recall tool for earlier recorded observations.

SQLite retains distinct player snapshots, decision observations, model attempts,
actions, errors, and usage for inspection. A server
snapshot and a decision observation are different: snapshots can arrive while
the player has no decision to make.

An observation delta would describe changes since that agent's previous decision
observation. Automatically supplying such a delta with each new decision is a
proposed improvement, not the current context policy.

## Running and evaluating

The harness uses Python 3.12+, `uv`, and the OpenAI Agents SDK with an OpenRouter
or OpenAI endpoint. Local play also needs the upstream Node.js game server.
The optional rules oracle answers questions using prepared official rules.

Separate evaluation CLIs run model games, rotate houses, and report results,
reliability, latency, token use, and cost. They use the same player harness as
the dashboard; tournament scheduling is separate from the live harness server.

- [Setup, configuration, checks, and evaluation commands](docs/RUNNING.md)
- [Detailed lifecycle, observations, tools, and API guide](docs/HARNESS_GUIDE.md)
- [Game-server WebSocket protocol](docs/swords-and-ravens-websocket-guide.md)

For Python checks, run `uv run ruff check src tests` and `uv run pytest -q`.

`uv run pytest -q tests/test_gameplay_e2e.py` runs both execution modes through
the app API, Agents SDK, real WebSocket game server, and SQLite. Three players
take consecutive decisions, restart the app, recall private history, and recover
from a provider failure. The tests verify tool results, memory isolation and
commit behavior, fresh context between decisions, and persisted traces and usage.
Only the external model responses are scripted; no paid calls are made. These
tests require the game-server dependencies and fail if they are missing.

For a bounded model/provider capabilities check, see
[scripts/check_model_capabilities.py](scripts/check_model_capabilities.py).

Gameplay has one canonical [pipeline](src/raven_harness/harness/gameplay.py).
It shares observation preparation, prompts, tools, memory, context fingerprints,
tracing, usage accounting, and action validation. Only the
[execution loop](src/raven_harness/harness/execution.py) varies, through the same
typed `Harness.run(Turn) -> Output` interface:

- `HARNESS_MODE=two-stage` (default): explore with tools, then make one tool-free
  structured request using the same agent and full decision transcript.
- `HARNESS_MODE=structured`: use tools and structured output together in one SDK run.

Each decision owns a fresh agent. Models, providers, prompts, tools and memory
are supplied separately. Both modes validate the final action against the live
decision before sending it to the game server. `HARNESS_MAX_TURNS` defaults to
20 exploration/model turns; two-stage mode adds one finalization request.
`MODEL_MAX_OUTPUT_TOKENS` optionally caps each parent model response.

Refactors must preserve all tracing capabilities across both execution modes:
context and schema fingerprints, model/tool lifecycle events and timings, response
and tool records, nested rules-oracle traces, provider attribution, token/cache/cost
accounting, and partial traces on failures or cancellation. These belong to shared
components. Backward compatibility with old internal interfaces is not a requirement;
update callers and remove superseded implementations without compatibility shims.
