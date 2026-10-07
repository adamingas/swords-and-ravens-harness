# Groq high-reasoning output-limit check

Three bounded diagnostic requests used `openai/gpt-oss-120b` through OpenRouter,
with `provider.only=["groq"]`, `allow_fallbacks=false`, the existing provider
blocklist, `reasoning.effort=high`, and `max_output_tokens=40960`. No gameplay
commands were executed and no full game was launched.

**Groq exceeded 8,192 tokens: one response reported 11,815 output tokens. However,
this was a failed response, so this does not establish successful gameplay.**
Both tool-bearing probes failed at provider-side tool validation/parsing before
the harness could give corrective feedback. The full requested 40,960 allowance
was not reached or verified.

| Probe | Output tokens | Outcome |
| --- | ---: | --- |
| Same synthetic array prompt as the Cerebras probe | 374 | Completed with a refusal; inconclusive about the ceiling. |
| First request from the previously failing Lannister mustering decision | 7,040 | Failed: Groq rejected the model's malformed `submit_action` arguments. |
| Long integer-fixture tool call | 11,815 | Failed: Groq could not parse the generated tool arguments as JSON. |

The mustering replay reconstructed the original user input and verified its
SHA-256 against the recorded context. It included the original instructions,
exploration tools and action schema. It was a first-request-only replay; no tools
were executed. Groq's error reported that `strategic_handoff` was missing at the
root and had instead appeared inside `decision`. This reproduces action-shape
confusion through a different provider. Provider-side rejection prevents the
normal harness tool-result correction loop from handling that response.

The long fixture request forced an `emit_fixture` call containing 5,000 literal
integers. It ran for 87.935 seconds and returned `status=failed`, with all 11,815
reported output tokens classified as reasoning and the error:
`Upstream error from Groq: Failed to parse tool call arguments as JSON`.
The failed payload does not expose the malformed argument text, so its precise
JSON defect cannot be independently inspected.

OpenRouter's live endpoint catalog advertised 65,536 maximum completion tokens
for Groq. We requested 40,960 for consistency with the Cerebras test. Catalog:
https://openrouter.ai/api/v1/models/openai/gpt-oss-120b/endpoints

Read-only generation metadata confirmed Groq for all three probes after
initial metadata lookups returned 404. Response errors also explicitly identify
Groq. Artifacts, including outbound bodies without credentials, responses,
summaries and metadata:
`data/evaluations/groq-output-limit-diagnostics-20260922`.
The diagnostic script is [probe.py](probe.py). Production routing and settings
were not changed.

The appropriate conclusion is: **the observed Cerebras-route 8K ceiling is not
universal to the harness/OpenRouter Responses path, but Groq has not passed the
end-to-end action test.** Further retries were deliberately not launched.
