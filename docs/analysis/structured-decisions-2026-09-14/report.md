# Harness instruction experiment

The harness now separates exploration from structured submission and explains the current task in fresh user messages. The latest OSS batch avoids the original bad decision in all ten saved positions, but secondary strategic mistakes remain. The game test stopped in round 8 because the OpenRouter key reached its spending limit; there is no completed-game result yet.

## What changed

- A fresh **user-message briefing** explains the decision, consequences, exploration tools and submission. It follows the board data; the system prompt retains the static rules and map.
- **Exploration has tools and no native output constraint. Submission is a separate call with a state-specific JSON schema and no tools.** The final call retains this decision's exploration transcript and repeats the task in prose. Forced arguments are omitted and restored by the harness.
- The final schema is visible in the user message as well as enforced through structured output. Supplying an API schema alone did not stop OSS guessing field names.
- March destinations include castle gain/loss facts. The briefing explains home-area control, why lone units do not consume army slots, and which nearby areas contain castles.
- Unit-loss choices explicitly say **destroy**, identify pieces and their owners, and distinguish one's own casualties from enemy targets. Crow Killers distinguishes destruction from downgrading. Consolidate Power explains the choice between income and a later recruitment decision.
- Both stages share cancellation and rollback handling. Reaching the exploration tool-use budget proceeds to submission. Only an accepted action commits a proposed memory update.
- Exploration keeps automatic tool choice but explicitly encourages liberal, iterative tool use: test routes, targets, threats, rules, memories and assumptions; inspect results; follow up on uncertainty; and do not avoid useful calls merely to save tokens.

## Final replay results

Every replay uses production `StrategicHarness.prepare_turn` and `run_turn`, matched snapshots, restored private memory, real exploration tools and local action validation. Commands are captured before server transmission. These are changed-context experiments, not exact-input baseline repeats.

Latest batch: OSS 120B through Cerebras, `results-v8-two-stage-task-reminder`. All ten submitted locally valid actions on their first attempt.

| Case | Result |
|---|---|
| 1 Stark march | Takes Moat Cailin; token preserves White Harbor |
| 2 Stark planning | Places a March at Winterfell; still wastes Consolidate Power orders at sea |
| 3 Stark march | Takes Flint’s Finger |
| 4 Stark march | One Knight takes Seagard; one stays in Moat Cailin |
| 6 Martell march | Takes the Reach |
| 8 Greyjoy march | Takes White Harbor; token preserves Moat Cailin |
| 10 Martell march | Takes Starfall |
| 12 Martell losses | Removes Ship and Footman; Knight survives |
| 14 Greyjoy planning | Places a March at Pyke; Greywater Watch supports |
| 17 Greyjoy losses | Removes both port Ships; all land units survive |

Earlier, the combined tools/schema version produced nine good OSS decisions and a response-limit failure. DeepSeek produced good decisions in all ten positions after retrying case 2. Those results and the preceding two-stage batch are retained; they are not the final-version results. Repeated batches have shown variation, so ten successful submissions do not establish reliable or optimal play.

## What the traces show

Follow-up: the unchanged final harness also produced **10/10 valid DeepSeek 4.1 Flash decisions avoiding the original mistakes**, with one provider-error retry on Together. Both planning cases chose two land Marches and avoided useless sea income orders. [Comparison and complete traces](deepseek-v8-report.md).

OSS repeatedly calls Castle Black a castle, treats Bay of Ice as land, or reasons that leaving Winterfell loses ownership. The full rulebook and map do not ensure it applies them. Relevant facts beside the decision help, but returned reasoning still contains errors.

The first live game's Baratheon planned March orders in its reasoning but submitted Raids and Defence while guessing the format. After the schema was made explicitly visible, replaying that position produced land Marches. This supports a format-visibility problem, although one replay does not establish causality.

Sol solved case 1 with the second-version prompt that OSS still misread. This shows a capability difference on that position, not that the interface needs no further work.

### Exploration and output constraints

The first 70 recorded DeepSeek responses in its game contained no exploration calls, although their reasoning often announced one. A controlled case-8 replay omitted only the provider-side output-format parameter. It then made six exploration calls, selected a sensible White Harbor capture, and returned JSON inside prose and a code fence. Validation rejected it without sending a command. This motivated the two-stage implementation. The route/model interaction is strongly suggested, not isolated conclusively by one probe. [Diagnostic requests and answers](results-provider-format-diagnostic-wire/full-prompts-and-answers.md).

Earlier `results-provider-format-diagnostic*` directories without the `-wire` suffix are local diagnostic setup failures (a missing import, then an HTTPX/HTTPX2 stream mismatch), not evidence about model or provider behaviour.

## Game test: stopped at the account limit

Six OSS players on Cerebras reached round 8 using the revised harness. Baratheon controls **4 castles**, Stark, Martell, Greyjoy and Tyrell **3 each**, and Lannister **2**. These are interim scores, not final standings.

The [action audit](../../../data/evaluations/structured-decisions-oss-two-stage-full-game/decision-audit.json) verifies all **199 accepted actions** against their recorded inputs and confirms an exploration stage followed by one structured submission for each. The stored sessions contain **91 neighbour lookups, one history recall and four oracle calls**. Failed attempts comprise 19 rate limits, three locally rejected actions, and five responses reporting the key spending limit.

Expansion and action submission work, but play is still imperfect. Four planning decisions placed no land March. In round 6, Tyrell attacked the Dornish Marches while mistakenly calling it a stronghold; it has no castle. The attack failed and its Knight retreated. Stark lost a Footman defending Seagard, then later recovered to three castles. The game has not exercised a unit-destruction selection: the saved loss cases provide that evidence, and the two logged combat deaths were Footmen. This is not proof of error-free unit management.

The board, session checkpoints and traces are preserved in `data/evaluations/structured-decisions-oss-two-stage-full-game`. The current runtime fingerprint matches the saved game. After raising the OpenRouter key's total spending limit, resume the same board with:

```sh
uv run python docs/analysis/structured-decisions-2026-09-14/full_game.py \
  --output data/evaluations/structured-decisions-oss-two-stage-full-game \
  --model openai/gpt-oss-120b --provider cerebras --game-port 5145 --resume
```

Earlier OSS attempts and the DeepSeek attempt remain as partial experiments. DeepSeek reached round 4, demonstrated successful expansion and coordinated attacks, and was stopped after sustained Fireworks rate limits. None is presented as a completed game.

## Evidence and limitations

[Latest full prompts and returned answers](results-v8-two-stage-task-reminder/full-prompts-and-answers.md), [earlier OSS traces](results-v6/full-prompts-and-answers.md), [DeepSeek traces](results-v6-deepseek41-all/full-prompts-and-answers.md). Earlier variants, failed probes and retries are retained.

Cerebras rejected combined tools/schema requests but accepts the separated stages. Provider changes, changed context and stochastic outputs prevent attributing every improvement to prose alone. Validation: 281 tests and lint pass; an earlier real-server protocol smoke test also passed. Replays do not prove optimality or server acceptance; the live-game audit checks actual accepted actions against hash-verified model inputs.
