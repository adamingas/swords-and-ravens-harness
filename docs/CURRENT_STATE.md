# Current Repository State

This file describes the working-tree harness as of 2026-09-23.
It is a handoff for continuing the current experiments. Treat the
code as authoritative if this document becomes stale.

## Purpose

Raven Harness lets language models play *A Game of Thrones: The Board Game
(Second Edition)* through the Swords & Ravens server. The TypeScript game server
owns the rules and authoritative state. The Python harness gives each model a
player-scoped observation, lets it inspect the game with read-only tools, turns
its chosen action into an exact server command, and records the resulting trace.

The immediate research question is whether models play materially better when
they receive explicit rules, compact map structure, state-specific action
instructions, useful spatial/card tools, and durable strategic memory.

## Current experiment status

The current bad-decision test set contains ten historical decisions in
`docs/analysis/replay-baseline-2026-09-14/test-set.json`. It is intentionally a
diagnostic set rather than an unbiased benchmark: eight cases repeated their
original bad action in live baseline replays, while two retained Stark cases
changed but remained poor. The set includes Stark examples and GPT-OSS examples
from Stark, Martell, and Greyjoy.

A historical live replay at
`tmp/submit-action-stark-round5-replay-20260919-v2/summary.json` used the earlier
submission-tool loop. DeepSeek V4.1 Flash won that case after exploring the map.
It is not evidence for the current structured-output implementation.

The current implementation is tested through the real Agents SDK and mocked
Responses API transport. A live full-game comparison of the two new execution
modes remains to be run. Model/provider capability observations are consolidated
in `docs/model_provider_capabilities.json`.

## Canonical model loop

Every required gameplay decision uses one path:

1. The manager confirms from the latest player-scoped snapshot that this user
   must act.
2. `GameHarness.prepare_turn` uses the shared `DecisionPreparation` to build the current observation, record it in
   history, derives the legal gameplay handlers, creates a `DecisionContract`,
   and builds a plain-language decision briefing.
3. The configured harness exposes exploration and memory tools. The underlying
   gameplay handlers are not model-callable tools.
4. With `HARNESS_MODE=two-stage` (default), the model explores until it returns
   text. The same decision-local agent then receives the complete transcript and
   makes one tool-free structured-output request. With `structured`, the final
   output schema is available alongside tools throughout one SDK run.
5. The SDK validates the final output against the current decision schema,
   including the mandatory `strategic_handoff`.
6. The contract rechecks the current leaf state and legal action, invokes the
   gameplay handler, synchronizes with the server, and confirms acceptance.
7. Only an accepted action updates persistent strategic memory. Autoplay waits
   for the next decision or applies its existing bounded failure policy.

| Setting | Current value |
| --- | --- |
| API | Responses API through an OpenAI-compatible client |
| Reasoning effort | `high` |
| Tool choice | automatic during exploration; no tools in two-stage finalization |
| Parallel tool calls | disabled during exploration |
| Final submission | validated structured output, then internal gameplay handler |
| SDK turn limit | `HARNESS_MAX_TURNS`, default 20; two-stage adds one final request |
| Gameplay output-token limit | optional `MODEL_MAX_OUTPUT_TOKENS`; otherwise provider default |
| HTTP timeout | none imposed by the harness |
| OpenAI client retries | zero |
| Provider-side response storage | disabled |

`GameHarness` is the single gameplay pipeline. Observation preparation, prompts,
tools, memory, context manifests, response capture, usage reconciliation, and
action validation each have one shared implementation outside the execution loops.
`StructuredOutputHarness` and `TwoStageHarness` implement the same typed interface.
The factory creates a fresh agent per decision, so simultaneous players cannot
change each other's agent configuration. Models, providers, prompts, tools and
memory are composed externally. OpenAI/OpenRouter provider objects contain endpoint
configuration; neither subclasses the game runner.

Invalid structured output fails the attempt. The old terminal-tool and unlimited
submission-reminder loops have been removed. The harness does not repair malformed
provider output or extract an action from prose or reasoning text.

## Prompt and context

The system instructions are stable across decisions and contain:

- the agent record's base system prompt;
- the Raven strategic instructions and victory objective;
- the full formatted rules from `src/raven_harness/rules.md`;
- a compact static map reference with all areas, terrain, icons, home control,
  ports, and graph edges.

The user input is rebuilt for each decision. It contains the complete current
player-scoped observation, a state-specific decision briefing, and direct prose
explaining the chosen exploration/completion mode. Tool definitions and the final
output schema are supplied through the SDK, rather than pasted into prompt text.

The observation contains dynamic state rather than repeating the static map. It
includes the current state path and pending decision, the player's resources
and units, visible board state, public opponent information, influence tracks
with meaningful descriptions, card availability, recent events, legal action
guidance, planning constraints when relevant, a strategic overview, durable
memory, and a compact history index.

Previous model messages, reasoning, and tool exchanges are not carried into the
next gameplay decision. Continuity between decisions comes from explicit game
state:

- `strategicMemory`, including the current plan and automatic situation notes;
- `historyIndex`, covering the latest twelve recorded decision states;
- `recall_game_state`, which can retrieve a prior observation;
- the mandatory `strategic_handoff` submitted with every action.

The handoff should contain the current goal, dependencies, threats, reserved
resources, assumptions to check, and why the chosen action advances the plan.
After acceptance, the harness combines that handoff with an automatic summary
of the current position and action. `remember_strategy` is also still exposed;
it queues a plan update, but the handoff supplied by the final structured action
is the final pending plan for that decision.

## Tools available to the model

The exploration set is intentionally small:

- `check_neighbours(area)` returns direct graph neighbours joined with current
  owners, units, wounds, visible orders, terrain, garrisons, castles, and icons.
  It is a map-edge query, not a legal-move generator. Legal ship transport and
  march destinations remain in `actionGuidance`.
- `inspect_house_card(card_id)` returns exact printed strength, combat icons,
  ability text, house, and current availability.
- `recall_game_state(turns_ago)` retrieves a private earlier observation.
- `remember_strategy(note)` queues a private plan update that is committed only
  after an accepted action.
- `ask_rules_oracle(question)` is present when prepared rules data is available.
  It runs a nested rules agent with a 900-token output limit and at most three
  oracle turns.
- `reachable_areas(area)` computes movement routes from the current revealed board.

The final structured schema changes with the active game state. When several
choices are legal, it contains a constrained action discriminator. All required
fields remain explicit, including fields with only one possible value.

## Validation and game safety

The decision contract is tied to the current `leafStateId`. A stale decision is
rejected before any server command is sent. JSON Schema validates submitted
arguments. The original typed gameplay handler then rechecks current turn
ownership and legal values before sending a command.

The harness also performs domain checks that matter beyond shape validation,
including supply-safe marches and mustering, legal control-token placement,
order inventory and starred-order limits, unique unit selections, neutral-force
strength, and atomic complete order drafts. The game server remains the final
authority. The client synchronizes after submission and records an action only
after authoritative acceptance evidence.

A per-run action lock prevents duplicate gameplay commands from crossing the
network. It does not serialize different players. Players whose decisions are
simultaneous can plan concurrently.

## Provider behavior

`create_game_harness` composes the shared gameplay pipeline with an independently
selected execution loop and provider:

- Direct OpenAI uses `OPENAI_API_KEY` and `OPENAI_BASE_URL`.
- OpenRouter is selected when `OPENROUTER_TOKEN` is present. It sends a stable
  `session_id` derived from the agent ID for provider/cache affinity and asks
  OpenRouter to ignore the configured provider blocklist.

The default OpenRouter blocklist is:

`together,gmicloud,alibaba,novita,makora,siliconflow`

It can be replaced with `OPENROUTER_PROVIDER_BLOCKLIST`. OpenRouter otherwise
chooses the provider. The harness does not maintain per-model primary/fallback
provider routes and does not require providers to advertise every request
parameter.

Every raw provider response is captured before SDK processing. Traces retain
response IDs, reported usage, model/provider attribution when returned, rules
oracle interactions, partial responses on failure, request-input hashes, and
timings. Credentials and sensitive URL components are redacted from errors.

## Retry and concurrency behavior

The model client itself does not retry. Autoplay handles failures at the
game-decision level while the leaf state remains unchanged:

- ordinary failures allow two consecutive failures by default;
- HTTP 429 and 503 capacity failures have a separate default limit of four;
- retry delay is exponential and capped at 30 seconds;
- permanent authentication, quota, or account failures disable autoplay for
  every agent rather than repeatedly charging requests;
- connection loss does not replay an ambiguous gameplay command.

There is no global model semaphore in the production harness. Independent
players can issue model requests concurrently. Experimental wrappers may impose
a semaphore, but that is not part of `GameHarness`.

## Persistence

SQLite schema version 4 contains six durable concepts:

- `agents`: connection credentials, model, system prompt, and game identity;
- `agent_events`: connection and model/tool lifecycle events;
- `agent_runs`: one attempted decision with observation, effective-context
  manifest, instructions, offered tools, response items, action, usage, error,
  and timing;
- `game_state_history`: distinct decision observations and their accepted
  actions;
- `strategic_memories`: the current private plan and automatic notes;
- `player_snapshots`: distinct complete player-scoped server snapshots.

There is no persisted Agents SDK conversation and no model-session checkpoint.
Restart recovery comes from the authoritative game save, current player
snapshot, stored agent identity, and explicit strategic/history state. Existing
databases must already be schema version 4; the code does not migrate older
schemas.

## Evaluation and monitoring

The dashboard shows connection state, whether an agent is actionable, current
phase/round, observation, tool names, live model/tool activity, recent runs,
usage, and errors. `model-request-started`, `model-request-completed`,
`model-tool-started`, and `model-tool-completed` events are emitted without
request bodies.

Evaluation CLIs use the same `GameHarness` and configuration factory as the
dashboard. They record model verification, source/runtime hashes, random seed,
assignments, player standings, response attribution, usage, cache tokens, cost,
latency, failures, game saves, and SQLite traces. Historical manifests embed
their own runtime provenance and should be interpreted according to that
provenance rather than assumed to represent the current code.

## Current validation and working tree

Tests cover both production modes through the actual SDK and a mocked Responses
endpoint, including OpenAI/OpenRouter settings, real exploration-tool execution,
transcript continuity, invalid output, stale state, cancellation, memory commits,
usage and trace accounting. Separate execution tests cover concurrent decisions
and model-turn limits. This migration is in the working tree and is not committed.

## Main code locations

- `src/raven_harness/harness/execution.py`: the shared typed interface and two run loops.
- `src/raven_harness/harness/gameplay.py`: the canonical gameplay pipeline.
- `src/raven_harness/harness/configure.py`: configuration composition.
- `src/raven_harness/harness/prompts.py`: shared system and mode-specific completion instructions.
- `src/raven_harness/harness/preparation.py`: observation enrichment, exploration tools,
  decision preparation, and prompt-cache keys.
- `src/raven_harness/harness/memory.py`: private history, strategic memory tools,
  and automatic strategy summaries.
- `src/raven_harness/models/providers.py`: OpenAI/OpenRouter endpoint configuration.
- `src/raven_harness/models/tracing.py`: context manifests, lifecycle events,
  raw provider response capture, and attribution.
- `src/raven_harness/models/results.py`: shared results, errors, and usage reconciliation.
- `src/raven_harness/harness/decision.py`: dynamic structured-output schema,
  validation, and execution.
- `src/raven_harness/harness/decision_briefing.py`: state-specific prose and
  consequences shown for the current action.
- `src/raven_harness/harness/observation.py`: player-scoped dynamic observation.
- `src/raven_harness/harness/legal.py`: legal choices and action guidance.
- `src/raven_harness/harness/map_tools.py`: current-state neighbour lookup.
- `src/raven_harness/harness/card_tools.py`: printed House-card lookup.
- `src/raven_harness/manager.py`: connections, autoplay, retries, concurrency,
  monitoring, and run persistence.
- `src/raven_harness/evaluation.py`: reproducible full-game evaluation runner.
