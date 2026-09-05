# Raven Harness

Raven Harness seats model-driven players in a Swords & Ravens game while humans
continue to use the original game UI. Each agent has its own authenticated game
connection, model, prompt, player-scoped state, and Pydantic-defined tools.

The working vertical slice includes:

- a FastAPI dashboard for creating any number of agents;
- SQLite persistence for configurations, events, and model runs;
- a model picker populated from OpenRouter's inexpensive tool-capable models;
- one isolated Swords & Ravens WebSocket connection per agent;
- OpenAI Agents SDK execution through the OpenRouter Responses API;
- phase-specific tools plus typed protocol-tool coverage for the broader game;
- authoritative turn ownership supplied by the patched game server;
- manual single actions and continuous autoplay;
- owner controls for a three-player base-game lobby.
- interchangeable `legacy` and `strategic-v1` harness implementations;
- persistent per-seat conversations, strategic notebooks, exact historical-state
  recall, cache routing, and replayable local traces for strategic agents.

## Run the harness

Initialize the upstream game submodule, install Python dependencies, and create
your local configuration:

```bash
git submodule update --init --recursive
uv sync
cp .env.example .env
```

Put `OPENROUTER_TOKEN` in `.env`, then start the harness:

```bash
uv run raven-harness
```

Open <http://127.0.0.1:8787>. The default model is
`z-ai/glm-5.3-flash`; the dashboard also fetches other inexpensive models that
advertise both `tools` and `tool_choice` support.

Configuration:

```text
HOST=127.0.0.1
PORT=8787
DATABASE_PATH=./data/harness.db
OPENROUTER_TOKEN=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL_REQUEST_TIMEOUT_SECONDS=90
MODEL_MAX_OUTPUT_TOKENS=8192
STRATEGIC_CONVERSATION_ITEM_LIMIT=30
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
```

`OPENAI_API_KEY` is an optional direct-OpenAI fallback. OpenRouter takes
precedence when both credentials are present.

## Run the local game and human UI

The local game uses port 5001 because macOS commonly reserves port 5000 for
AirPlay. Install the upstream dependencies and generate its protocol schema:

```bash
cd swords-and-ravens/agot-bg-game-server
npx --yes yarn@1.22.22 install --frozen-lockfile --ignore-scripts
npm install --no-save --package-lock=false --ignore-scripts --legacy-peer-deps sass@1.77.8
npx --yes yarn@1.22.22 generate-json-schemas
```

Start the game server:

```bash
NODE_ENV=development PORT=5001 ./node_modules/.bin/ts-node -T src/server/server.ts
```

In another terminal, start the human client:

```bash
NODE_ENV=development \
GAME_SERVER_WEBSOCKET_URL=ws://localhost:5001 \
./node_modules/.bin/webpack-dev-server \
  --config webpack.client.dev.js --mode=development
```

Open <http://localhost:8080/static/#1> for local user 1. Change the hash to
`#2`, `#3`, and so on for other development users; in the local server their
auth token is the same as their user ID. The harness defaults to game ID `1`
and `ws://localhost:5001`.

The upstream submodule is patched in four narrow places:

- the browser client's WebSocket URL can come from
  `GAME_SERVER_WEBSOCKET_URL`;
- each state change includes the engine's authoritative waited-user IDs;
- full in-game snapshots contain that same waited-user list;
- development servers accept `HARNESS_TEST_MAX_TURNS` for lifecycle smoke tests.

Without `HARNESS_TEST_MAX_TURNS`, games keep their normal turn limit. To run a
one-round end-to-end smoke game, start the server with:

```bash
NODE_ENV=development HARNESS_TEST_MAX_TURNS=1 PORT=5001 \
  ./node_modules/.bin/ts-node -T src/server/server.ts
```

The local game server persists its current game at
`src/server/website-client/local-entire-game.json`. Move that file aside before
starting if you need a fresh lobby.

## Playing

Create one harness agent per game user and connect each one. On the owner agent,
`3-player setup` selects the base game with Baratheon, Lannister, and Stark.
Agents can choose their houses with `Take one action`; humans can instead choose
seats in the original game UI. Once all seats are occupied, use `Launch game`
on the owner and enable `Autoplay` for model-controlled seats.

Each player selects a harness independently:

- `legacy` preserves the original behavior: one stateless model call for each
  required game action.
- `strategic-v1` retains a bounded Agents SDK conversation in SQLite, injects a
  durable structured strategy notebook, provides exact `recall_game_state` and
  indexed-history tools, and asks the model to finish memory work with a real
  game action in the same run. Current authoritative state is always appended;
  older conversation items are bounded while their exact observations remain
  available in `game_state_history`.

Strategic prompts and static tool descriptions receive a stable
`prompt_cache_key`. The key is scoped to the model, instructions, and active
tool bundle, so repeated phases can reuse provider prompt caching without
mixing different agent configurations.

For each action the harness:

1. receives the game server's player-specific snapshot;
2. builds a compact, credential-free observation with the active state path,
   board, tracks, and map data rather than sending the raw engine snapshot;
3. attaches only the deepest recognized state's Agents SDK tools;
4. asks the selected model for exactly one tool call;
5. validates arguments through Pydantic and translates the call to the typed
   Swords & Ravens protocol;
6. lets the game server remain the final rules authority.

Planning uses semantic order names; the harness allocates physical order tokens,
enforces starred-order and Westeros-card restrictions, and safely replaces a
partial draft on retry. Supply reconciliation is computed deterministically.
Autoplay bounds failures per decision and model requests time out after
`MODEL_REQUEST_TIMEOUT_SECONDS`, so a provider cannot leave a seat permanently
running.

The model never receives credentials, the raw WebSocket, or a generic protocol
escape hatch. Unknown game states temporarily receive the complete typed
gameplay tool catalog so uncommon expansion paths fail open during development
rather than stopping the match.

## Experiments and traces

The dashboard exposes each agent's runs, aggregate token/cost metrics,
conversation, strategy memory, state history, and protocol events. `agent_runs`
stores the exact model, harness,
instructions, observation, tool definitions, function-call response items,
standard and provider-native usage, response ID, timing, action, and error for
each attempt. OpenRouter's provider-native usage includes cost, cache, and
reasoning details when supplied by the selected provider.

`GET /api/agents/{agent_id}/metrics` summarizes request counts, input/output,
cached and reasoning tokens, provider cost, latency, conversation size, and
historical-state count. `GET /api/agents/{agent_id}/runs/{run_id}` returns the
complete replayable trace for a single attempt.

The Agents SDK conversation items live in `agent_sessions` and
`agent_messages`. Strategy summaries live in `strategic_memories`, while exact
player-scoped historical positions and the actions selected from them live in
`game_state_history`. This separation keeps short-horizon conversation useful
without discarding long-horizon evidence needed for evaluation or replay.

## Verification

Run the Python checks with:

```bash
uvx ruff check src tests
uv run pytest
```

The suite covers persistence, API serialization, protocol compression, the
headless WebSocket client, state reduction, turn ownership, Pydantic validation,
tool routing, map extraction, and an Agents SDK tool-call round trip without an
external request. The end-to-end acceptance run also completed a normal
three-agent, ten-round base game against the real server and reached its
`game-ended` state.
