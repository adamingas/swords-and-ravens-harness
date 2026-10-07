# GLM 5.3 Flash provider tool/schema probe

This repeats the DeepSeek dummy experiment with `z-ai/glm-5.3-flash` and the
same OpenAI Agents SDK setup: one required `double_number` tool, explicit prose
requiring its use, `tool_choice="auto"`, and a Pydantic final-output type sent as
native structured output. Each OpenRouter provider was pinned with fallbacks
disabled, and at most three requests ran concurrently.

There were 27 unique providers across 29 endpoints.

| Outcome | Providers |
|---|---|
| Called tool and returned valid Pydantic output | NextBit |
| Skipped tool; returned schema-valid answer | Cloudflare, DeepInfra, Friendli, InferenceNet, Modal, Parasail, Together, Venice, Wafer |
| Called tool; final output failed Pydantic parsing | DigitalOcean, GMICloud, Io Net, Phala, Reka, Relace, SiliconFlow, StreamLake, Z.AI |
| Request rejected | AtlasCloud, Novita |
| Rate limited after retry | BaseTen, CoreWeave, Crusoe, Fireworks, Near AI, Sail Research |

NextBit made one `double_number(21)` call and then returned the valid final
object. The skipped-tool providers returned `tool_was_used: true` even though
the harness recorded no tool execution. Near AI supplied `Retry-After: 2`; the
probe waited two seconds and retried, but received another 429. Other 429
responses did not include a `Retry-After` header.

This is one completed sample per available provider, plus the documented retry
of temporarily unavailable endpoints. It is evidence of protocol behavior for
these requests rather than a statistical tool-use rate.
