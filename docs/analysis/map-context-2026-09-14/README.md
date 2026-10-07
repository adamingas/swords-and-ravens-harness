# Compact map and neighbour-tool experiment

**Some better actions, but no convincing improvement in spatial reasoning.**
All ten live replays completed. **None called `check_neighbours`**: every model
went straight to a gameplay tool. Compared with the previous full-rules run,
there is one clear new castle-capture choice, one useful control-token correction,
and one regression in land-expansion orders. Four actions repeated exactly;
the other changes do not establish an improvement.

| Case | New decision | Compared with full rules alone |
|---|---|---|
| 1 · OSS Stark R1 | White Harbor footman → Castle Black; leaves a token | **Partial improvement:** preserves White Harbor, but still misses empty Moat Cailin. |
| 2 · OSS Stark R5 | Defense/support orders, plus consolidation in Bay of Ice | Still no marches. Falsely believes marching requires at least two units; still expects sea consolidation to earn power. |
| 3 · OSS Stark R7 | Winterfell knight → friendly Castle Black | Avoids the previously miscalculated attack, but still misses empty castles. |
| 4 · OSS Stark R10 | Bay of Ice ship → Winterfell’s port | Defers the Moat Cailin march. **Inconclusive:** that land decision remains pending; this does not prove it would preserve or capture castles. |
| 6 · OSS Martell R3 | Kingswood army → empty Reach; leaves a token | **Better action:** takes a new castle. Its explanation still denies that the Reach has a castle. |
| 8 · OSS Greyjoy R6 | Both Moat Cailin knights attack Winterfell | Exact repeat. Still invents support and overlooks enemy supporters. |
| 10 · DeepSeek Martell R3 | Footman → empty Starfall | Exact repeat of the previous good capture. No reasoning returned. |
| 12 · OSS Martell R8 | Removes ship and knight, retains footman | Exact repeat. Still interprets removal as choosing units to keep. |
| 14 · OSS Greyjoy R2 | Defends Pyke; marches the Ironman’s Bay ship | **Regression for land expansion:** replaces the previous Pyke march with defense. |
| 17 · OSS Greyjoy R8 | Selects both knights for destruction | Exact repeat. Still thinks it is selecting attacking units. |

## What the traces show

- **Case 6:** “The Reach is a region (no castle)” and “The Reach adjacent to
  Lannisport? Yes.” Both contradict the supplied map. The better action therefore
  does not demonstrate better understanding of why it is valuable.
- **Case 8:** Counts Greywater Watch support for an attack on Winterfell, although
  those areas are not adjacent. Again calls Moat Cailin castle-free and misses
  Stark’s Castle Black/Karhold support. The compact graph did not fix this error.
- **Case 14:** Invents Ironman’s Bay connections to Shipbreaker Bay and Blackwater
  Bay. Neither connection exists.
- **Case 17:** “Choose strongest attacking units maybe knights.” The actual
  decision destroys the selected units. A map change does not clarify this action.

## Method and evidence

[All results and reasoning](results/summary.json); each case directory contains
its outgoing request and result. Comparison: the previous
[full-rules results](../full-rules-2026-09-14/results-final/summary.json).

Used `StrategicHarness.run_turn` → `OpenAIAgentRunner.run_once`. The real map
tool was available and able to return data and continue the run; 11 offline
controls verified this, including a two-request query-then-action test. Its board
state came from persisted player snapshots matching the original observations.

All ten outgoing requests were compared with the full-rules control: only the
map’s relocation/format, added tool, and cache key changed. Models, providers,
generation settings, historical transcript and dynamic observations stayed fixed.
Gameplay calls were captured before execution, so these are decision assessments,
not completed-game outcomes. One sample per case cannot establish a reliable
improvement rate. Since no model used the new tool, this batch cannot assess
whether reading its results would help. Total reported provider cost: **$0.1273**.

```sh
uv run python docs/analysis/map-context-2026-09-14/replay.py --live --output tmp/map-replay
```
