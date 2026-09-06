# Raven Harness

Raven Harness lets language-model players and human players share one
*Swords & Ravens* game. The Python server gives each model a player-scoped
observation, phase-specific tools, private strategic memory, and an optional
official-rules oracle.

The project uses one canonical harness. Each model decision receives the
complete current observation, recent model and tool items, and structured
long-term memory. Old full observations stay in SQLite for audit, but the
harness removes them from the next provider request. SQLite stores every
distinct player snapshot, model attempt, accepted game action, error, and
duration. Attempts that reach the model runner also store an effective-context
manifest. SQLite keeps completed rules-oracle work when the parent model call
later fails or is cancelled.

See [the system and tool guide](docs/HARNESS_GUIDE.md) for the complete data
flow, observation format, tool catalog, retry behavior, and API reference.
Tournament scheduling, house rotation, and ranking are in the separate
`raven-evaluate` CLI. They are not server or harness responsibilities.

## Quick start

Initialize the game-server submodule and Python environment:

~~~bash
git submodule update --init --recursive
uv sync
test -e .env || cp .env.example .env
~~~

Add an OpenRouter token to .env. The default model is
z-ai/glm-5.3-flash. From a source checkout, the default database is stored at
data/harness.db in this repository unless `DATABASE_PATH` selects another
project-relative or absolute path. An installed wheel uses the operating
system's per-user application-data directory. OpenRouter retries retryable HTTP and
connection failures and can try another provider for the same exact model ID.
Handled tool errors stay inside the current Agents SDK run so the model can
correct its call. An account or authentication failure stops autoplay for all
agents instead of repeating requests.

Prepare the rules oracle. The dashboard can run without it, but evaluation
requires it:

~~~bash
uv run raven-prepare-rules
~~~

Start the Python harness:

~~~bash
uv run raven-harness
~~~

Open <http://127.0.0.1:8787>.

## Start Swords & Ravens

Install and prepare the upstream application:

~~~bash
cd swords-and-ravens/agot-bg-game-server
npx --yes yarn@1.22.22 install --frozen-lockfile --ignore-scripts
npm install --no-save --package-lock=false --ignore-scripts --legacy-peer-deps sass@1.77.8
npm run generate-json-schemas
~~~

Start its server in a separate terminal:

~~~bash
NODE_ENV=development PORT=5001 ./node_modules/.bin/ts-node -T src/server/server.ts
~~~

A valid
`swords-and-ravens/agot-bg-game-server/src/server/website-client/local-entire-game.json`
resumes the saved game. For a fresh lobby, stop the server and move that file
to a private backup path before restarting it. Do not commit saved private game
state to the submodule.

Set `LOCAL_GAME_PATH` to an absolute or project-relative JSON path when a run
needs an isolated save file. The evaluation command does this automatically.

Start its human browser client in another terminal:

~~~bash
NODE_ENV=development \
GAME_SERVER_WEBSOCKET_URL=ws://localhost:5001 \
./node_modules/.bin/webpack-dev-server \
  --config webpack.client.dev.js --mode=development
~~~

Open <http://localhost:8080/static/#1>. Local development user IDs and
authentication tokens are equal. Give every human or model player a different
user ID.

The harness dashboard can create and connect agents, ask a model to choose a
house, configure a six-player base-game lobby without vassals through an owner
agent, launch the game,
run one decision, and enable autoplay. Humans continue to use the original
browser client. Agent cards show live model-request and tool activity. The
detail view keeps the recent activity timeline, complete run traces, player
state, token use, and provider cost. After a Python-server restart, it displays
the latest persisted player state with a saved-state label until reconnection.

After an established game WebSocket drops, the harness keeps autoplay enabled
and reauthenticates with capped exponential backoff. The authentication response
replaces local state with a fresh player-scoped snapshot. An action interrupted
by the drop is never replayed on the replacement socket; the next decision is
built from that authoritative snapshot.

## Configuration

~~~text
HOST=127.0.0.1
PORT=8787
DATABASE_PATH=./data/harness.db
RULES_PATH=./data/rules.json
MODEL_ID=z-ai/glm-5.3-flash

OPENROUTER_TOKEN=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1

MODEL_REQUEST_TIMEOUT_SECONDS=45
MODEL_RUN_TIMEOUT_SECONDS=300
MODEL_API_MAX_RETRIES=2
MODEL_MAX_CONCURRENCY=1
MODEL_MAX_OUTPUT_TOKENS=16384
MODEL_SESSION_HISTORY_ITEMS=32
AUTOPLAY_MAX_CONSECUTIVE_FAILURES=5
AUTOPLAY_RETRY_BASE_SECONDS=2

OPENROUTER_PROVIDER_ORDER=reka,cloudflare,coreweave,fireworks,deepinfra,together
OPENROUTER_ALLOW_UNLISTED_PROVIDERS=false
OPENROUTER_PROVIDER_SORT=throughput
OPENROUTER_ALLOW_FALLBACKS=true
OPENROUTER_REQUIRE_PARAMETERS=false

OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=
OTEL_SERVICE_NAME=raven-harness
~~~

OpenRouter takes precedence when both API keys exist. `MODEL_ID` is the default
for a new dashboard agent. Each agent can select a different model that the
configured endpoint supports. The default provider order is a six-host
fallback pool and does not fall through to unlisted hosts. The OpenAI client
retries the pool twice on retryable failures. Reka is first because it
completed the existing GLM tool-call smoke runs; every fallback still serves
the model requested by that agent.
MODEL_MAX_CONCURRENCY applies to all agents in the Python process. The sort
setting is used only when `OPENROUTER_PROVIDER_ORDER` is empty.

Keep HOST at 127.0.0.1 unless you add authentication and transport security.
The dashboard API has no authentication. The local SQLite database contains
game credentials, prompts, and private player observations in plain text.

Optional decision spans can be viewed in a local Phoenix instance:

~~~bash
uvx arize-phoenix serve
~~~

Set `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:6006/v1/traces` and
restart the harness. SQLite remains the canonical local trace store; failed SDK
runs can lack partial parent response items and provider-returned parent usage.

## Verification

Run Python checks from the repository root:

~~~bash
uv run ruff check src tests
uv run pytest -q
~~~

Run game-server checks from swords-and-ravens/agot-bg-game-server:

~~~bash
npx tsc --noEmit
npm run generate-json-schemas
~~~

For a one-round smoke game, start the game server with
HARNESS_TEST_MAX_TURNS=1. Omit that variable for normal games.

The evaluation runner starts an isolated game server, stores its database and
game JSON below `data/evaluations/`, and assigns the same model to all six
players. Run a one-round smoke before a complete 12-game comparison:

~~~bash
uv run raven-protocol-smoke
uv run raven-evaluate --games 1 --max-rounds 1 \
  --output data/evaluations/glm-one-round-smoke
uv run raven-evaluate --games 12 \
  --random-seed 1 \
  --concurrent-games 12 \
  --output data/evaluations/glm-prompt-comparison
~~~

`raven-protocol-smoke` starts the real TypeScript server and six harness
clients, then completes two rounds with a deterministic policy. It invokes the
same dynamic gameplay tools as a model, records required and observed tool
coverage, and makes no provider requests. Use it to test local protocol and
persistence changes before the paid model smoke.

Verify any saved evaluation without contacting the provider:

~~~bash
uv run raven-verify-evaluation data/evaluations/glm-one-round-smoke
uv run raven-verify-evaluation --require-complete \
  data/evaluations/glm-prompt-comparison
~~~

The first command accepts an internally consistent partial evaluation and
labels it `provisional`. The second exits unsuccessfully unless all 12 games
and both observations for every configuration-house pair are present.

The evaluator derives one game seed from `--random-seed` and the game number.
It records that seed and reuses it for every retry of that game. Reusing an
output directory skips completed games and preserves failed attempts. The
manifest rejects changes to the model, prompts, seed, schedule, source commits,
rules, or runtime settings. Independent games run concurrently. Each game uses
one port, starting at `--game-port` and increasing with the game number. The
default `--concurrent-games 12` runs the complete schedule at once. Before it
creates a new attempt, the runner stops
if OpenRouter reports that the configured key has exhausted its spending
limit. The summary labels rankings as provisional until all 12 games are
complete and every configuration has played each house twice.
