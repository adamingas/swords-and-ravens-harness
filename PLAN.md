# Raven Harness Plan

This plan defines the project goals and acceptance criteria.

## Original goal (verbatim)

~~~text
implement agent handover as a tool for the models to use to ask question about the rules of the game f they want arefresher. this will be an oracle agent which will have access to the rules. find the rules file and convert it to text that the oracle agent can read. dont use rag, but maybe a tool that fetches text per section? Only do this if you have found evidence that models struggle with rules

also, i want you to pass over  the code base and simplify and consolidate. i dont want bacjwards compatibility, or dead weight, i only want canonical interfaces and implementations of things taht have actually been used and worked. 

then i want you to commit and start documenting using simple ASD-ste100 standard english how the agent works, focusing on how the state is represented, when does it get access to it, when. also how it sees the state, what does it then do and what happens after every action. list all available tools and what they do. remember to make this readable with motivating examples, introductionary sentences and paragraphs. someone reading just this should be able to get a good idea on how the harness works and what data pass through it. use sub agents to help you tune it because i know you have poor theory of mind.

after that is done and committed i want you to work on the ui of the python server. i want to be able through it to monitor the agents and what they are doing, their state (cards, troops on the board, money, etc). also implement maybe a lightweight tracing solution like Arize Phoenix and opentelemetry to track stuff. 

after this i want us to use only the latest best strategic v1 harness with many models. i want us to run glm 5.3 flash, qwen 3.7 flash, gpt-oss-120b, ~deepseek/deepseek-v4-flash-latest, qwen/qwen3-235b-a22b-2507, and gpt 5.6 luna through it, for many iterations, and get some data on which is the best model. maybe an elo ranking. use 6 player game variant, and rotate the houses many times so all models play all the houses eventually at least two times.

this is a huge goal so please write it somewhere first so that you dont forget it
~~~

## Remaining work

### 1. Simplify and consolidate the codebase — complete

The codebase must:

- [x] Have one canonical implementation for each operation.
- [x] Remove compatibility layers that are not required.
- [x] Remove unused interfaces, parameters, branches, and dead code.
- [x] Avoid large abstractions for hypothetical future uses.
- [x] Keep the server, harness, game client, and experiment runner separate.
- [x] Use tests that verify business behavior and runtime results.
- [x] Do not use tests that parse source code, inspect import names, or assert architectural words.
- [x] Reduce both lines of code and unnecessary conceptual complexity.

  Identify the interfaces and implementations that have actually run successfully. Make those the only canonical paths. Remove all duplicate implementations, unused interfaces and parameters, unnecessary compatibility code, dead branches, and speculative abstractions. Verify preserved behavior with runtime and business-logic tests, measure the reduction in lines and concepts, and commit the consolidated code before starting tournament work.

  Evidence: commits `4b81262`, `d7cb7e4`, `a1c0492`, and `39e8eae`
  removed redundant turn derivation, duplicate persistence operations, unused
  parameters and properties, and legacy database migration code. From the
  parent of `4b81262` through `39e8eae`, `src/` and `tests/` changed by 160
  insertions and 229 deletions, a net reduction of 69 lines while adding
  behavior tests. The complete runtime suite and real-server smoke tests pass.




### 2. Run a model tournament

- [x] Within a game do not impose any limitations on concurrency for llm calls. This is an embarassingly parallel problem, hence all llms should be ran in parallel. In other words, dont use the semaphore.
Run games sequentially and observe. Between games you can make harness changes if you see failures or stupid latency mistakes.

  Evidence: the shared model-run semaphore and its configuration interface were
  removed. A runtime test admits six simultaneous agent calls. The same-model
  runner executes games sequentially, and snapshot-driven autoplay replaces
  the 0.75-second polling interval. The complete 221-test Python suite, the
  TypeScript compiler, schema generation, and a two-round real-server protocol
  smoke all pass. The smoke completed 53 accepted decisions in 4.6 seconds
  without a provider request.

#### 2.1 same model — in progress

note that a game should take around a minute or two. if it takes longer then investigate why.

- [x] Run six players with the same `strategic-v1` harness and exact
  `openai/gpt-oss-120b` model, served by Cerebras.
- [x] Run five complete games with no artificial round limit. (This means the games must have a winner)
- [x] Produce win-rate and placement statistics for every house.
- [x] Record the method, performance, cost, time taken to complete game, failure, and interpretation in
  `docs/GPT_OSS_120B_HOUSE_TEST.md`.

  Evidence: artifact
  `data/evaluations/gpt-oss-120b-house-test-b4279fb` contains five isolated
  attempt databases and five round-10 results. Lannister won three games;
  Greyjoy and Martell won one each. All attempts used `strategic-v1`, exact
  model ID `openai/gpt-oss-120b`, and Cerebras-only routing with fallback off.
  All five databases pass SQLite `quick_check`. The schema-2 manifest has a
  completion time and per-attempt provenance. The final method, results,
  timings, failure analysis, request accounting, cost bounds, house statistics,
  and interpretation are in `docs/GPT_OSS_120B_HOUSE_TEST.md`.

#### 2.2 different models — in progress (4/12 complete)
DO NOT START THIS UNLESS YOU ARE CERTAIN THE HARNESS WORKS AS EXPECTED.

  Progress: Games 1 through 4 are complete in
  `data/evaluations/model-tournament-ebae98a`. Game 4 stopped at a pre-model
  checkpoint in round 5 when the configured model-endpoint key reached its
  spending limit. After the limit changed, the same attempt restored that
  checkpoint and completed with a round-10 winner. Commit `29ddb94` prevents SDK
  history from an older game state from entering a new model call while
  retaining the complete session in SQLite. Commit `96955ce` reduces capacity
  retry delays from 15/30/30 seconds to 2/4/8 seconds. The 251-test Python suite,
  a 53-decision provider-free protocol smoke, and the evaluation verifier pass.

The tournament must:

- Use the same canonical strategic-v1 harness for every model.
- Put six different models in the six seats of each game.
- Measure model ability with an identical harness configuration for all seats.
- Use the six-player game.
- run 12 games, where you Rotate houses across models.
- Continue until every model has played every house at least twice.
- Run harnesses concurrently
- Save complete results, traces, token use, costs, failures, and model and provider attribution.
- Produce model-performance statistics and, if useful, an Elo-style ranking.

The requested model set is:

- GLM 5.3 Flash.
- Qwen 3.7 Flash.
- GPT-OSS-120B.
- DeepSeek V4 Flash Latest.
- Qwen3-235B-A22B-2507.
- GPT-5.6 Luna.

Verify the exact provider model IDs before the tournament starts.

The experiment runner must remain separate from the server and harness. House
rotation, match scheduling, repeated games, result aggregation, and Elo belong
in that external runner or in scripts.

### Remember

- Use `uv` for Python commands.
- Make heavy use of provider based caching (NOT local caching)
- Use working providers and appropriate retry handling.
- If an error is happening a lot, i.e. websocket error, or tool error, or network, it means you have fucked up someplace. Try to fix errors not patch them. 99% of the time, its an architecture decision that caused an error, and its 100% of the times your fault.
- Keep the dashboard and manual-harness database at `data/harness.db`.
  Tournament attempts use isolated `harness.db` files in their artifact directories.
- The submodule must point to master and not change except if it is impossible to use the harnesses otherwise
- Commit coherent changes only after verification.
