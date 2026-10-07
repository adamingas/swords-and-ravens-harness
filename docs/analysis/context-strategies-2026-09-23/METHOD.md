# Reproduction

The experiment reads the archived database in read-only mode. It independently checks the reconstructed original input hashes for all ten current observations and their previous-house observations. Snapshot board, house, card, resource, order and track fields must match those verified inputs. Only the current leaf is restored from the verified observation; no future action or final combat result is used as model input.

Combat projections call the pinned TypeScript engine on the **player snapshot**, without advancing it. Hidden selections remain unresolved. The support tool calls the engine's support eligibility routine; movement uses the existing harness reachability implementation. Experimental totals are intended for these base-game fixtures, not a production serializer for every expansion or combat stage.

```sh
uv run python scripts/context_experiment/prepare.py --source /path/to/source-checkout-with-audit
uv run python scripts/context_experiment/run.py --repeats 2
uv run pytest -q tests/test_context_experiment.py
uv run ruff check src tests scripts/context_experiment
```

Initialize the pinned submodule and install its Node dependencies first. Live probes use configured OpenRouter credentials: GPT-OSS-120B, Cerebras only, medium reasoning, temperature 0, 4,096 output tokens, at most four requests per probe, three concurrent probes, no API retries. No gameplay actions are submitted. The experiment made 127 provider requests for 100 probes, costing approximately $1.57 according to returned usage.

The questions explicitly target the audit's mistakes: mustering cost, transport/support, Wildling strength, omitted recruitment, consecutive battles, scoring, Tyrion and the blade. They are more focused than ordinary gameplay decisions. All variants receive identical questions and tool schemas; the baseline therefore has better retrieval access than the original game. Tool-call counts do not establish that the model used the results correctly.

Initial dynamic token estimates use `o200k_base`, excluding common system rules/map, questions and tool schemas. Cumulative input totals use provider-reported usage across every request, including repeated prefixes and retrieved data; they are not cache-adjusted billed-token counts. Harmless grading aliases accept separately stated “no” answers for the two support areas, “unknown” for an unknown bid total, and house labels attached to numerical totals. Original responses are preserved in the evidence file.

Local `data/context-experiment/` retains the complete prompts, frozen inputs and raw responses. The checked-in regression fixtures omit historical logs and unused observation fields. They cover wounds, support, Kevan, hidden cards, Tyrion, receipts, house isolation and immutable rendering. Live gameplay defaults are unchanged.

Validation: all **206 tests passed**, including eight new context regressions and the real-server tests; Ruff passed. The fresh worktree initially lacked the generated `ClientMessage.json` schema; generating it resolved the four server-start failures.
