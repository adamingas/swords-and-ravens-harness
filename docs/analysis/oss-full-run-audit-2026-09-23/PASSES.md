# Passes, skipped mustering and final-round inactivity

All six empty marches, eight mustering skips, seven Raven skips, two blade declines, and both final-round plans without a March are included. These 25 decisions are not 25 demonstrated mistakes.

| Run | Round / house | Action | Assessment |
|---|---|---|---|
| [D004](round-01.md#d004) | 1 / lannister | skip_raven_order_replacement | Optional Raven pass; not inherently bad. 29 schema rejections before acceptance. |
| [D017](round-02.md#d017) | 2 / lannister | skip_raven_order_replacement | Optional Raven pass; one schema rejection, no demonstrated strategic loss. |
| [D030](round-03.md#d030) | 3 / lannister | skip_raven_order_replacement | Optional Raven pass after D029 output exhaustion; one schema rejection. |
| [D036](round-03.md#d036) | 3 / stark | resolve_march | Clear interface-induced abandonment: 25 rejections, then discarded March instead of intended legal Winterfell move. |
| [D048](round-04.md#d048) | 4 / lannister | skip_mustering | Skipped free mustering to preserve power; six individually legal alternatives verified. Follows repeated failed mustering runs. |
| [D049](round-04.md#d049) | 4 / stark | skip_mustering | Skipped free mustering to preserve power; three legal alternatives verified. |
| [D056](round-04.md#d056) | 4 / lannister | skip_raven_order_replacement | Optional Raven pass; one schema rejection, no demonstrated strategic loss. |
| [D058](round-04.md#d058) | 4 / lannister | resolve_march | Abandoned planned Harrenhal attack; falsely feared vacating token-controlled Riverrun would lose it. Attack itself was risky. |
| [D069](round-05.md#d069) | 5 / baratheon | skip_raven_order_replacement | Optional Raven pass; one schema rejection, no demonstrated strategic loss. |
| [D071](round-05.md#d071) | 5 / lannister | resolve_march | Again abandoned Harrenhal attack. Sensible recognition of an unfavorable battle; earlier order allocation wasted. |
| [D085](round-06.md#d085) | 6 / lannister | resolve_march | Abandoned Winterfell attack; legitimate concern about vacating Moat Cailin without a token. Not established as a bad pass. |
| [D090](round-07.md#d090) | 7 / baratheon | skip_mustering | Skipped free mustering citing power/Supply; seven legal alternatives verified. |
| [D091](round-07.md#d091) | 7 / lannister | skip_mustering | Skipped free mustering citing resources/Supply; six legal alternatives verified. |
| [D092](round-07.md#d092) | 7 / stark | skip_mustering | Skipped rebuilding depleted Stark army; two legal alternatives verified. |
| [D104](round-07.md#d104) | 7 / lannister | resolve_march | Abandoned White Harbor move citing defenses, but destination was empty with zero garrison. Castle trade has positional tradeoffs. |
| [D117](round-08.md#d117) | 8 / baratheon | use_valyrian_steel_blade | Reasonable blade decline: 5+1 still loses to 7. The earlier card/support calculation caused the defeat. |
| [D144](round-09.md#d144) | 9 / baratheon | skip_raven_order_replacement | Raven pass after D143 attempted replacement failed; intent changed on retry, value of original replacement unproven. |
| [D154](round-09.md#d154) | 9 / baratheon | use_valyrian_steel_blade | Clear costly blade decline: ignored Kevan ability; +1 would turn 3–4 loss into 4–4 win on Fiefdoms. |
| [D157](round-10.md#d157) | 10 / baratheon | skip_mustering | Skipped free mustering to conserve power; seven legal alternatives verified. |
| [D158](round-10.md#d158) | 10 / stark | skip_mustering | Skipped free mustering because seven castles seemed unreachable, ignoring round-ten scoring; four legal alternatives verified. |
| [D159](round-10.md#d159) | 10 / lannister | skip_mustering | Skipped free mustering to preserve bidding tokens; five legal alternatives verified. |
| [D168](round-10.md#d168) | 10 / lannister | submit_orders | No March orders while tied on castles but losing tiebreak. False claims that attacks require ships and power affects final scoring. |
| [D169](round-10.md#d169) | 10 / stark | submit_orders | No March orders while trailing. Claims no attack opportunities; this relinquished any attempt to improve castle score. |
| [D172](round-10.md#d172) | 10 / baratheon | skip_raven_order_replacement | Raven pass after D171 attempted replacement failed. Original Stoney Sept “stronghold” plan itself used wrong map scoring. |
| [D173](round-10.md#d173) | 10 / baratheon | resolve_march | Reasonable final March pass while winning tiebreak. Its token rationale was wrong: source already had a control token. |

## Mustering counterfactuals

For every mustering skip, [verify_state.py](verify_state.py) loads the corresponding archived player snapshot and tests individual recruitment/upgrade plans with the harness validator. [mustering-alternatives.json](mustering-alternatives.json) preserves the plans. These are independent alternatives, not a claim they can all be combined; no counterfactual game was played.
