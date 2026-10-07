# DeepSeek 4.1 Flash: the same ten cases

**All ten produced locally valid decisions avoiding the original mistakes.** Nine succeeded on their first Together attempt; case 14 succeeded after retrying a provider stream error. DeepSeek's planning was more expansion-focused than the latest OSS batch.

This used the unchanged production `StrategicHarness.prepare_turn` and `run_turn`, with the current two-stage exploration/submission workflow. All ten initial prepared contexts match the latest OSS batch except regenerated history timestamps: identical rules, map, board, memory, briefing, tools and action schemas. The model was `deepseek/deepseek-v4.1-flash`, routed through Together. Historical snapshots were verified; gameplay commands were captured after local validation, before server transmission.

| Case | DeepSeek decision | Compared with latest OSS |
|---|---|---|
| 1 · Stark march | Footman takes Moat Cailin; token preserves White Harbor | Same |
| 2 · Stark planning | Marches at Castle Black and Winterfell; both seas Support; Karhold earns power | Two land Marches instead of one; eliminates wasted sea income orders |
| 3 · Stark march | Knight takes empty White Harbor; home symbol retains Winterfell | Different free castle; OSS took Flint's Finger |
| 4 · Stark march | Splits knights between Seagard and White Harbor, relinquishing Moat Cailin | Same net gain of one castle; OSS kept one knight at Moat Cailin |
| 6 · Martell march | Knight takes the Reach; Footman retains Kingswood | Preserves Kingswood without a token; OSS moved both units |
| 8 · Greyjoy march | Knight takes White Harbor; other knight retains Moat Cailin | Saves a token; OSS moved both knights and left a token |
| 10 · Martell march | Footman takes Starfall | Same |
| 12 · Martell losses | Destroys Ship 24 and Footman 27; keeps Knight 46 | Same |
| 14 · Greyjoy planning | Marches at Pyke and Greywater Watch; sea Support; port earns power | Two land Marches instead of one |
| 17 · Greyjoy losses | Destroys port Ships 7 and 8; keeps the land army | Same |

The returned explanations correctly distinguish destruction from movement, use home control and ship transport, and identify free castle captures. DeepSeek made **23 neighbour lookups** and five strategy-memory calls across the ten successful attempts. The planning decisions describe plausible expansion plans; their subsequent marches were not executed in these replays.

This is encouraging, not proof of optimal play. Splitting an army trades concentrated strength for broader control. In case 4, its statement that Moat Cailin “cannot be preserved” overlooks leaving one knight behind, although its chosen split still gains a castle overall. These are selected positions, one successful sample each, and the providers differ between models.

Fireworks initially rate-limited all ten cases; a DeepInfra probe also failed with a rate limit. Together's case-14 stream failure sent no command. Its retry includes that error in the current user context. No accepted decision was rerolled. These provider failures are retained separately and are not gameplay mistakes.

[Full prompts and unfiltered returned responses, including the failed Together attempt and retry](results-v8-deepseek41-together/all-prompts-and-answers.md) · [Machine-readable comparison](results-v8-deepseek41-together/comparison.json)
