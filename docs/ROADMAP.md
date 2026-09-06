# Raven Harness Project Roadmap

This file records the complete project objective. Do not treat one completed
stage as completion of the full objective.

## 1. Rules evidence and oracle

- Inspect stored model runs and game errors for evidence that models fail
  because they do not know or misapply game rules.
- Locate the authoritative game rules file in the upstream project.
- Add an oracle-agent handoff only if the traces show a rules problem.
- Convert the rules to clean text that the oracle can read.
- Give the oracle section-based retrieval when the complete text is too large.
  Do not add vector search or RAG.
- Expose the handoff as a model tool and record its questions, answers, token
  use, and cost in the normal trace data.

## 2. Canonical implementation

- Review the complete Python harness code.
- Remove unused compatibility paths, duplicate representations, abandoned
  experiments, and interfaces that did not work in real matches.
- Keep one canonical harness interface and the implementations that are needed
  for the proven system.
- Keep the code small enough to review, with direct Pydantic types and Agents
  SDK tools.
- Run the complete test suite and a real game smoke test after consolidation.

## 3. System documentation

- Commit the implementation before the documentation stage.
- Write a stand-alone guide in simple ASD-STE100-style English.
- Explain when the agent receives state, how the harness represents that state,
  what the model sees, how it selects a tool, and what happens after each
  action.
- List every available tool and explain its effect.
- Use short introductions and motivating examples so a new reader can
  understand the complete data flow without reading the source first.
- Ask independent reviewers to test the guide for missing assumptions,
  confusing language, and incomplete tool coverage. Revise it and commit it.

## 4. Monitoring UI and tracing

- Improve the Python server dashboard so an operator can monitor each agent's
  current activity and player state, including cards, units, controlled areas,
  power tokens, tracks, supply, current decision, recent tool calls, failures,
  latency, token use, and cost.
- Add lightweight local tracing with OpenTelemetry and, if it remains a good
  fit after a small proof, Arize Phoenix.
- Make traces useful for comparing prompts, tools, state representations, and
  model behavior.
- Verify the UI in a browser at desktop and narrow widths.

## 5. Six-model tournament

- Use only the final strategic harness for evaluation games.
- Put the six requested model IDs in the six seats of every game.
- Give every model the same prompt, tool-selection policy, state representation,
  memory policy, request limits, and retry policy.
- Verify the exact IDs and tool-call support against OpenRouter before a run.
- Keep provider retries and provider-host fallback enabled. Do not switch to a
  different model after a failed request.
- Use stable provider prompt-cache keys. Do not add a local response cache.
- Run six-player games.
- Rotate houses so each model plays each house at least twice. This requires 12
  complete games when each game contains all six models.
- Derive and record one stable gameplay seed per game. Reuse the same seed when
  a failed game is retried.
- Preserve all game snapshots, agent traces, token use, cost, failures, and
  seat assignments.
- Produce model rankings that include match wins, placement or score,
  house effects, reliability, cost, and an Elo-style rating with stated
  assumptions.

## Completion criteria

The project is complete only when all five stages are implemented and verified,
the requested evaluation has at least two completed games for every
model-house pair, the artifacts are saved in the repository data
directory, and the final results can be reproduced from documented commands.
