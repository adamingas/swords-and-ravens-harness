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
later fails or is cancelled. It checkpoints each agent session immediately
before a provider call and after an accepted action.

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
resumes the saved game. Saves created before random-stream checkpoints are not
supported. For a fresh lobby, stop the server and move that file to a private
backup path before restarting it. Do not commit saved private game state to the
submodule.

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

The harness can run native three- or six-player base-game lobbies without
vassals. The dashboard's lobby button configures the six-player form. It can
create and connect agents, ask a model to choose a house, launch the game,
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

Autoplay is event-driven. A new server snapshot wakes each affected agent, and
all agents required to decide can make asynchronous model calls concurrently.

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

MODEL_REQUEST_TIMEOUT_SECONDS=90
MODEL_RUN_TIMEOUT_SECONDS=300
MODEL_MAX_OUTPUT_TOKENS=16384
MODEL_SESSION_HISTORY_ITEMS=32
AUTOPLAY_MAX_CONSECUTIVE_FAILURES=2
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
The sort setting is used only when `OPENROUTER_PROVIDER_ORDER` is empty.

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

Run the real-server protocol smoke before a paid evaluation. It uses six
deterministic clients for two rounds and makes no provider requests. Then run
the same-model house test or one game of the mixed-model tournament:

~~~bash
uv run raven-protocol-smoke
uv run raven-evaluate-houses \
  --output data/evaluations/gpt-oss-120b-house-test
uv run raven-evaluate \
  --random-seed 1 \
  --output data/evaluations/model-tournament
~~~

`raven-evaluate-houses` runs five complete games with `openai/gpt-oss-120b` in
all six seats. It has no round-limit option. The command requests the Cerebras
backend with fallback disabled and records each game's active elapsed time. It
runs one game at a time. Agents with simultaneous decisions make asynchronous
model requests without a harness concurrency limit. Reusing its output directory
resumes incomplete games from their saved game and agent checkpoints.
Its summary lists every completed, failed, and cancelled attempt. Request,
token, and cost totals include partial attempts instead of only finished games.
If a model run fails after one or more responses, those completed responses and
the final failed or incomplete Responses API payload remain in the run metrics.
The GPT-OSS house test limits each response to 4,096 output tokens; successful
responses in the first three games never exceeded 1,216 tokens.
If a completed game exceeds two minutes, the command stops before it starts the
next game so the latency can be investigated.
Each attempt records its exact runtime provenance. A documentation-only commit
does not prevent an interrupted attempt from resuming. A runtime, rules, model,
or game-server change requires a new attempt, while a new sequential game can
record a newer tested runtime after an investigation.

`raven-evaluate` always schedules 12 complete games. One command starts or
resumes only the first incomplete game and exits after that game. Run the same
command again only after you inspect its result, duration, failures, and cost.
There is no partial-game, game-count, start-game, concurrent-game, or
continue-on-error option. Every game uses the same port because games never run
at the same time. Within a game, all agents that must decide at the same time
make asynchronous model requests without a harness semaphore.

The six exact model IDs and their two complete house rotations are fixed in the
runner. The configured endpoint catalog must list every ID before an attempt
starts. All six seats use `strategic-v1`, required tool selection, the same
memory and rules tools, the same retry policy, and the same 16,384-token output
limit. Stable prompt-cache keys let the provider reuse common player and rules
prefixes. The harness does not keep a local response cache.

Verify any saved evaluation without contacting the provider:

~~~bash
uv run raven-verify-evaluation data/evaluations/model-tournament
uv run raven-verify-evaluation --require-complete \
  data/evaluations/model-tournament
~~~

The first command accepts an internally consistent partial evaluation and
labels its ranking `provisional`. The second succeeds only when all 12 games
are complete and every model-house pair has two completed games.

The evaluator derives one game seed from `--random-seed` and the game number.
It records that seed, and each saved game also records the current deterministic
random-stream state. Reusing an output directory skips completed games. An
incomplete attempt with both `game.json` and `harness.db` resumes in place with
the same agent IDs, model sessions, memories, and game state. If shutdown
interrupts a model call, the next process starts that decision again from the
saved pre-call boundary. An incomplete attempt resumes only when its game,
database, runtime, rules, endpoint configuration, and live catalog verification
still match. Otherwise, the runner marks it superseded and starts a new numbered
attempt. Completed games remain valid when documentation or later runtime code
changes; each attempt carries its own provenance.

Each result attributes all calls to the configured endpoint provider. Each
SQLite trace maps its response IDs, usage, cost, and status to the exact model
assigned to that agent. The runner does not poll a provider-specific generation
API and does not claim to identify an upstream host when the standard response
does not expose it. `summary.json` includes completed-game model statistics,
house effects, the pairwise Elo calculation, game duration, all attempt
statuses and errors, endpoint attribution, requests, tokens, cache tokens, and
cost from completed and failed attempts.
