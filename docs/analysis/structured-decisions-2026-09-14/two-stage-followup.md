# Two-stage implementation notes

Implemented and promoted from the isolated test copy. The production suite passes 281 tests. The final saved-position experiment is `results-v8-two-stage-task-reminder`. The OSS game in `data/evaluations/structured-decisions-oss-two-stage-full-game` reached round 8, then stopped at the OpenRouter key's spending limit; see the report for the resume command. The DeepSeek attempt was stopped in round 4 after sustained rate limits. Both boards and traces are retained.

Case 8 in `results-provider-format-diagnostic-wire` motivated separating exploration and submission: without native output constraints the player made six exploration calls and selected a good move, but its prose-wrapped JSON failed final validation. With native constraints, the full-game player had made no exploration calls in its first 70 recorded responses.

Implementation in `OpenAIAgentRunner.run_once`:

1. Run the actual exploration tools with no native final-output schema. A fresh user-message instruction encourages liberal, iterative tool use and says not to avoid useful calls merely to save tokens. Tool choice remains automatic, and this stage cannot submit a game action.
2. Carry the current decision's complete tool results and intended action into a final call with the state-specific schema and no tools. A fresh user message explicitly requests the final JSON submission. Keep the static system prompt unchanged between stages.
3. Validate and execute through the same `DecisionContract` and original handlers. No parsing guesses or extracting JSON from prose. No server action occurs after exploration alone.

Preserve both stages in response traces, raw usage, model-input hashes and durable session history. The current `_SessionContextFilter` deliberately discards earlier-turn history; do not accidentally discard the exploration transcript in the final stage. Keep the original observation hash for auditing. Both stages share the existing run timeout and cancellation/rollback boundary. Include the submission stage in the prompt cache key and evaluation provenance.

Tests should demonstrate an exploration call, a prose intention that sends no game command, then a correctly schema-constrained final request without tools and exactly one accepted command. Verify failure/cancellation between stages sends nothing and accounts for both stages' usage. Re-run the ten saved positions through production `prepare_turn`/`run_turn` after the implementation.

Other small pending wording fixes: explain both Consolidate Power choices; label selection pieces by owner and distinguish destroying enemies from choosing one's own losses; state that the March source can be chosen among remaining orders and that a casualty count is already determined by the game.
