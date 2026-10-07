# Current test set: ten decisions

Kept original cases **1, 2, 3, 4, 6, 8, 10**, and added **12, 14, 17**.
Case IDs stay unchanged so earlier reports and traces remain traceable.

| New case | Player | Original and replayed tool call |
|---|---|---|
| 12 | GPT-OSS Martell, round 8 | `select_units`: Starfall units **27 and 46**. Destroys its last footman and knight, retaining only a ship. |
| 14 | GPT-OSS Greyjoy, round 2 | `submit_orders`: defend Pyke and Greywater Watch; consolidate in Port of Pyke and Ironman's Bay. No marches despite available ship transport; sea consolidation earns nothing. |
| 17 | GPT-OSS Greyjoy, round 8 | `select_units`: Greywater Watch knights **6 and 37**. Destroys both knights while retaining two ships in port and a footman. |

**All three additions repeated the exact tool names and parsed arguments** on
their first successful live replay, using verified historical SDK inputs and
tool schemas through the harness. For case 14 this includes assignment order,
priorities and starred preferences. Tool execution was intercepted.

The full set contains **eight exact repeats** and **two explicitly retained
Stark examples** (1 and 3) whose moves changed but remained poor. It does not
claim ten identical outputs or deterministic future behavior.

Seven additional candidates were screened. Cases 11, 15 and 16 changed; case 13
received HTTP 503 twice from its original provider. All attempts are retained in
the [screening manifest](added-candidates.json) and linked result directories in
[test-set.json](test-set.json). No candidate with a changed response was rerolled
until it matched. This selected set is for prompt experiments, not an unbiased
estimate of model repeatability.

```sh
# Validate all ten historical inputs without model calls:
.venv/bin/python docs/analysis/replay-baseline-2026-09-14/replay.py --manifest docs/analysis/replay-baseline-2026-09-14/test-set.json
```
