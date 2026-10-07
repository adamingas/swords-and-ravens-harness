# Full-rulebook prompt experiment

The editable rules are in [rules.md](../../../src/raven_harness/rules.md).
`StrategicHarness.build_instructions` appends this document under `# Rules` for
normal games and the replay variant. It contains the locally downloaded Rules
of Play and FAQ/errata, Markdown headings, and the existing supply-table
transcription. Duplicate pages, picture-only labels and page references were
removed; broken extraction order was repaired. It is approximately 20,000 words.

**Adding the rules helped some decisions, but did not reliably fix play.**
The final ten-case replay produced one clear immediate expansion improvement,
two actions with partial practical benefits, and seven decisions with serious
problems still present. The OSS reasoning does not demonstrate dependable improvement.

| Case | Final rules-prompt decision | Assessment |
|---|---|---|
| 1 · Stark R1 | White Harbor footman → Winterfell, no control token | Still abandons a castle. |
| 2 · Stark R5 | Exact original orders: defense, support and sea consolidation | Still no expansion; sea consolidation still wastes orders. |
| 3 · Stark R7 | Lone knight attacks Greywater Watch | Counts Castle Black support based on adjacency to the **starting area**, not the battlefield. Still misses empty White Harbor. |
| 4 · Stark R10 | Both knights leave Moat Cailin for Winterfell | Exact original castle abandonment. |
| 6 · Martell R3 | Kingswood army → owned Storm’s End | Exact original missed capture of the empty Reach. |
| 8 · Greyjoy R6 | Attacks Winterfell; leaves a token at Moat Cailin | Predicts victory by overlooking Defense +1 and six available adjacent support strength; also falsely says Moat Cailin has no castle. Actual combat was not executed. |
| 10 · DeepSeek Martell R3 | Footman → empty Starfall | Clear improvement: requests the available castle capture. |
| 12 · Martell R8 | Removes ship and knight, keeping the Starfall footman | Partial improvement: retains a land unit, though sacrificing the footman instead would preserve the knight. |
| 14 · Greyjoy R2 | Assigns March to Pyke | Partial improvement: explicitly recognizes ship transport and enables land expansion; still consolidates at sea. |
| 17 · Greyjoy R8 | Selects both knights for destruction | Exact original failure; reasoning still treats selection as choosing units to keep. |

All cases used `StrategicHarness.run_turn` and `OpenAIAgentRunner.run_once`.
Historical observations, selected history, tools, model IDs, providers and
generation settings were held fixed. Only system instructions and their prompt
cache key changed. Every outgoing call passed input and tool checks. Calls were
captured before game execution; these are decision assessments, not game outcomes.

The table uses [results-final/summary.json](results-final/summary.json), matching
the saved Markdown. An earlier pass before final reference cleanup is retained
in [results/summary.json](results/summary.json); it also fixed DeepSeek’s Starfall
decision, but several OSS choices differed. These small stochastic samples do
not establish a reliable improvement rate.

Validation: 76 focused tests passed, including 21 replay controls; the built wheel
includes the Markdown. The controlled-request test verifies that the added-rules
variant changes only instructions and the corresponding cache key.

## What OSS's recorded reasoning shows

- **Wrong meaning of the action (17):** “Choose best units to keep” and “Choose
  two knights to strengthen attacks.” It selects the knights for destruction.
  The tool description still covers “retreat, removal, or another prompted
  effect”; the pending decision gives IDs and a count without an explicit
  destruction instruction. The effect must be inferred from the state path.
- **Wrong spatial relationship (3):** It counts Castle Black's four support
  strength because Castle Black neighbours the march's origin, Winterfell.
  The battle is at Greywater Watch, which Castle Black does not neighbour.
- **Invented board facts (8):** “Moat Cailin is land no castle” contradicts
  `castleLevel: 1`. “Possibly from castle black? Not adjacent” contradicts
  Castle Black's adjacency to Winterfell. It predicts 4 versus 3 before cards;
  the defender has 4 locally and can receive another 6 from legal support.
- **Historical-action confusion (2):** It spends most of its reasoning asking
  whether it already submitted the orders, eventually recognizes the previous
  round, then copies the same pattern. These controlled replays deliberately
  retain the historical transcript; production's newer context policy excludes it.
- **Feasibility replaces strategy (4, 6):** It checks that consolidating an army
  is supply-legal, then chooses that move without comparing the castle gain/loss.
  In round 10 this means abandoning Moat Cailin to reinforce Winterfell.

The partial changes also deserve caution. Case 12 still says “Choose likely
strongest” before sacrificing a knight. Case 14 eventually enables transport,
but repeatedly reverses itself about whether ships and transported land units
can march. The evidence suggests poor application of rules to the current
state, ambiguous action meaning and historical anchoring; it does not establish
the causal contribution of each. Adding the rulebook alone does not resolve them.

```sh
.venv/bin/python docs/analysis/replay-baseline-2026-09-14/replay.py --live --full-rules --manifest docs/analysis/replay-baseline-2026-09-14/test-set.json --output tmp/new-full-rules-replay
```
