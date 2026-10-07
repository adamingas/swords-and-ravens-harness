# Context strategies — tested prototypes

**Start with a current-situation briefing and progressive disclosure.** Four strategies are implemented as experiments; the live harness is unchanged.

1. **Situation first.** Generate a short introduction covering round, phase, role, immediate operation and costs. Use the game engine for combat strengths, wounds, confirmed support, card effects, ties and blade status. Mark unresolved choices explicitly; include Wildling strength and unambiguous scoring totals.

   “Round 8. Lannister attacks you at Harrenhal. You defend with a wounded knight: army strength 0. Lannister has 5 before its unrevealed card. Ties favour you; your blade remains unused.”

2. **Facts before intentions.** Separate the applied-action receipt and changes since this house’s previous decision from its fallible notebook. For D110: “Previously you mustered; one recruitment was omitted for Supply. The receipt contains no recruitment at The Reach.” Observed changes need not all result from your action. Simply adding this to the full dump **underperformed**; keep continuity small and pair it with current context.

3. **Progressive disclosure.** Start with the briefing, receipt, decision constraints and private plan. Retrieve board, opponents, cards, events or the full frozen observation as needed. Essential decision facts stay up front. This prototype retains the shared static rules/map.

4. **Verify dependencies.** Provide separate movement-route, support-eligibility and card-effect lookups, with instructions to check concrete assumptions. Instructions increased tool use without improving accuracy here. Mechanically enforcing verification remains untested.

GPT-OSS-120B/Cerebras answered **10 audited decision probes, repeated twice**, with identical tools and static rules/map across conditions:

| Context | Correct probes | Tool calls |
|---|---:|---:|
| Full JSON baseline | 16/20 | 6 |
| Situation briefing + full JSON | 18/20 | 5 |
| Receipt/delta + full JSON | 12/20 | 2 |
| Progressive: briefing + receipt + retrieval | 18/20 | 6 |
| Progressive + verification instructions | 18/20 | 8 |

Progressive context used **58% fewer initial dynamic-context tokens** and **11% fewer cumulative input tokens**, including tool follow-ups. The briefing corrected the stale-battle error in both repeats. Every condition still falsely counted Castle Black as a scoring area.

These are focused comprehension tests from one game, **not evidence of improved win rate**. Briefings also add missing facts, so this does not isolate natural language from information completeness. Temperature-zero repeats are not independent game samples.

[Method and validation](METHOD.md) · [Per-probe evidence](results.json)
