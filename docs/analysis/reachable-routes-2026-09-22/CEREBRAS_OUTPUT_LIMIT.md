# Cerebras OSS-120B output allowance investigation

**Follow-up result:** An explicit allowance alone did **not** fix this route.
Five subsequently authorized diagnostic generations showed that both
OpenRouter Responses and Chat Completions can terminate at 8,192 despite an
explicit 10,000-token allowance. OpenRouter generation metadata attributes the
truncation to the native Cerebras generation. See the follow-up section below;
the original recommendation is retained as investigation history, not a
validated remote fix.

The initial investigation on 2026-09-22 did not change the running game, modify
runtime code, or make paid inference requests. Authorized live diagnostics were
subsequently added below. Experiment:
`data/evaluations/reachable-routes-oss-cerebras-20260922`.

## Finding

The user is right: **8,192 is not the advertised maximum for this endpoint**.
Both the [Cerebras public model record](https://api.cerebras.ai/public/v1/models/gpt-oss-120b)
and the [OpenRouter endpoint catalog](https://openrouter.ai/api/v1/models/openai/gpt-oss-120b/endpoints)
currently advertise **40,960 maximum completion tokens** and **131,072 context
tokens** for GPT-OSS-120B on Cerebras. The OpenRouter entry is
`provider_name=Cerebras`, `tag=cerebras/fp16`.

The harness leaves the parent agent's output allowance unspecified. The SDK
omits the parameter from the HTTP body, so the upstream service chooses the
effective allowance. The repeated 8,192-token terminations are consistent with
an upstream default, not a local 8K constant or the model's maximum capacity.

**Unresolved attribution:** the available response records do not identify
whether Cerebras itself or OpenRouter's Responses adapter chooses 8,192. No
authoritative documentation found in this investigation explicitly states that
8,192 is the current default on this exact route. It would overstate the evidence
to attribute that number definitively to either service. OpenRouter's
[general parameter documentation](https://openrouter.ai/docs/api_reference/parameters)
says omitted sampling parameters are normally omitted upstream, allowing provider
defaults. That supports the provider-default explanation but does not establish
the implementation of this specific Responses adapter.

## Local code and serialization evidence

- `src/raven_harness/models/openai_agent.py:497` explicitly calls the parent
  agent's `_model_settings(max_tokens=None, ...)`.
- `_model_settings`, at line 588, passes that value into `ModelSettings` and
  separately requests `reasoning={"effort":"high"}`.
- The rules oracle is separate: line 472 explicitly sets `max_tokens=900`.
  Its budget does not explain parent-agent failures at 8,192.
- Installed `openai-agents==0.22.0`,
  `agents/models/openai_responses.py:980`, maps `ModelSettings.max_tokens` to
  `responses.create(max_output_tokens=...)`. Its helper at line 498 converts
  `None` to the SDK's omission sentinel.
- The harness's `_UsageCapturingResponsesModel._fetch_response` uses this
  SDK-built request directly; it does not insert another output-token limit.

An **offline HTTP serialization check** used the installed `openai==3.8.0`
client and `httpx==0.28.1` `MockTransport`, a dummy key, and an `.invalid` host.
It exercised the real harness settings builder and response adapter; no network
inference occurred. All requests retained high reasoning and Cerebras-only
routing with fallbacks disabled.

| Harness `max_tokens` | Serialized `/api/v1/responses` body |
| --- | --- |
| `None` | No `max_output_tokens` field and no `max_tokens` field |
| `900` | `max_output_tokens: 900`; no `max_tokens` field |
| `40960` | `max_output_tokens: 40960`; no `max_tokens` field |

Thus `None` means **use the upstream default**, not **allow the model maximum**.
OpenRouter's [Responses API documentation](https://openrouter.ai/docs/api_reference/responses/basic-usage)
also names `max_output_tokens` as the request parameter. Cerebras's native
[Chat Completions API](https://inference-docs.cerebras.ai/api-reference/chat-completions)
uses `max_completion_tokens`; this harness should continue using the Responses
parameter via the SDK rather than sending a native Cerebras parameter to the
wrong endpoint.

## Recorded failures

At the read-only database inspection there were six parent-agent requests in
failed runs with exactly 8,192 output tokens. These are a snapshot, not final
experiment counts. Three examples:

| Run ID | Input tokens | Output tokens | Reasoning tokens |
| --- | ---: | ---: | ---: |
| `12dd0c63-6ba5-4262-b95d-6e030d625f3b` | 35,677 | 8,192 | 8,189 |
| `b2430998-f70f-45a6-960a-7711110fd158` | 37,073 | 8,192 | 8,189 |
| `d25afcc3-e88c-4930-99ac-ce2de4f0ec6f` | 36,563 | 8,192 | 8,167 |

Their partial responses have `status=incomplete` and
`incomplete_details.reason=max_output_tokens`. These input lengths leave ample
room for 40,960 output tokens under the advertised 131,072-token context limit;
these examples are not exhaustion of the entire context window.

Cerebras documents that [reasoning tokens consume the completion allowance](https://inference-docs.cerebras.ai/capabilities/reasoning).
The model can therefore spend almost the whole unspecified default on reasoning
before emitting a usable tool call. `reasoning.effort=high` does not itself raise
the output allowance. The harness then correctly rejects the incomplete response
as a completed action; repeated failures can disable autoplay.

## Recommended change and validation

For a separately labelled Cerebras-only OSS experiment, explicitly set the
parent **`ModelSettings.max_tokens=40960`**, which serializes as
**`max_output_tokens: 40960`**. This matches the currently advertised maximum;
65,536 would exceed this endpoint's advertised completion capacity. Keep the
existing reasoning setting unchanged when testing this change in isolation.

Make the allowance configurable by model/provider or evaluation configuration,
record it in the experiment manifest and request metadata, and account for
prompt length on long within-decision continuations. Do not impose the Cerebras
value globally on unrelated endpoints. Keep the oracle's independently chosen
allowance explicit. A higher allowance is a ceiling, not a requirement to spend
40,960 tokens, and cannot fix malformed-action repair loops by itself.

Useful regression tests:

1. At the mock HTTP transport boundary, assert the configured parent allowance
   becomes the integer `max_output_tokens` in initial and continuation requests.
2. Assert the oracle remains at its separate allowance and parent settings do
   not leak into it; keep Cerebras routing, provider exclusions, and high
   reasoning intact.
3. Validate configured limits and preserve the effective value in provenance;
   test prompt-plus-output handling before a continuation exceeds context.
4. Simulate `status=incomplete` with `reason=max_output_tokens`: preserve usage
   and partial response evidence, never submit a partial tool call, and classify
   output exhaustion distinctly from malformed actions or capacity failures.

Finally replay a saved failing decision using the explicit allowance, recording
the request value, response status, output/reasoning usage, and whether a valid
action is eventually submitted. The offline check proves serialization; **it
does not prove the remote route will honor the larger allowance**. That last
claim requires a live response or provider-side evidence. No such replay was
performed as part of this read-only investigation.

## Follow-up: explicit allowance still terminates at 8,192

The main task subsequently implemented a configurable parent allowance and
resumed the saved game with `max_output_tokens=40960`. Two Lannister mustering
runs, `0ac4d779-caf5-458a-8003-06a2c33ee6e5` and
`b12bb675-0774-4fda-99dd-649a607a62cc`, still exhausted exactly 8,192 tokens.
These are recorded in
`data/evaluations/reachable-routes-oss-cerebras-20260922-recovery`.

The investigation was then authorized to make at most three bounded paid
diagnostic requests. All three used a synthetic counting task, with no gameplay
tools or actions, `openai/gpt-oss-120b`, `reasoning.effort=high`,
`provider.only=["cerebras"]`, `allow_fallbacks=false`, and the existing provider
exclusions. HTTP timeout was 60 seconds per request, no retries. None modified
the harness runtime. The synthetic task asked for integers 1 through 10,000,
creating output pressure independent of the game prompt or action schema.

| API and explicit fields | Actual completion tokens | Reasoning tokens | Result |
| --- | ---: | ---: | --- |
| Responses: `max_output_tokens=10000` | 8,192 | 3,418 | `incomplete`, `max_output_tokens` |
| Responses: `max_output_tokens=10000`, `max_tokens=10000` | 735 | 685 | Completed early with a statement that the requested list was too long |
| Chat Completions: `max_tokens=10000` | 8,192 | 4,373 | `finish_reason=length` |

Each request used 126 native input tokens, ruling out context exhaustion. The
first Responses response explicitly echoed `max_output_tokens:10000` despite
stopping at 8,192. The responses with 8,192 completion tokens emitted thousands
of visible tokens as well as reasoning: **8,192 is not a reasoning-only budget**.

Read-only `/api/v1/generation?id=...` queries subsequently confirmed
`provider_name=Cerebras` for all three. Both truncated generations reported
`native_tokens_completion=8192` and `native_finish_reason=length`:

- Responses generation `gen-1790113538-Pk1bUXXfTe1d93i7Ycyl`, upstream
  `chatcmpl-2f76e793-8388-40aa-887a-2b424e400e6d`.
- Chat generation `gen-1790113544-FXVd6LaQoK7BOen6qsXM`, upstream
  `chatcmpl-a467bd9a-b5e3-4f72-8bb4-30fd54dc4a54`.

Sanitized outbound bodies, full synthetic responses, compact summaries, and
generation metadata are saved under
`data/evaluations/cerebras-output-limit-diagnostics-20260922`. They contain no
authorization headers or credentials. Total reported inference cost for all
three diagnostic requests was **$0.01297155**.

### Revised diagnosis

1. The explicit field reaches OpenRouter and is reflected in its Responses
   response. This reproduces without the harness SDK or game prompt.
2. The same ceiling occurs through Chat Completions, so switching away from
   Responses alone is not an evidenced fix.
3. Native generation metadata identifies Cerebras as the backend and reports a
   native length stop. The local harness is not truncating the text after receipt.
4. The remaining possibilities include OpenRouter's shared Cerebras adapter
   failing to forward/translate the token allowance, or a Cerebras deployment
   enforcing a lower effective allowance than the catalogs advertise. The
   outbound OpenRouter-to-Cerebras request is not exposed by these records, so
   the investigation cannot distinguish those possibilities.
5. The dual-field probe ended naturally before the limit and is **inconclusive**.
   Do not claim adding `max_tokens` to a Responses request solves the problem.
   A `reasoning.max_tokens` workaround was not tested, and the mixed reasoning
   and visible token counts provide no evidence of a separate 8K thinking budget.

The explicit parent allowance remains correct configuration, but it is not a
verified fix for this upstream behavior. A next diagnostic could compare native
`max_completion_tokens` handling on the route, or compare a direct Cerebras
request using independent Cerebras credentials, using a long structured output
task that reliably reaches the cap. Provider investigation can use the recorded
generation and upstream IDs. No extra inference beyond the three authorized
diagnostics was performed, and no provider was contacted.

### Two further authorized parameter-name diagnostics

Two additional requests were subsequently authorized, each requesting at most
10,000 output tokens. A revised finite task requested a JSON array of integers
1 through 5,000 and explicitly allowed service-side truncation, avoiding the
earlier model refusal. Cerebras-only routing, no fallbacks, provider exclusions,
high reasoning, and 60-second HTTP timeout were preserved.

| API and explicit fields | Actual completion tokens | Reasoning tokens | Result |
| --- | ---: | ---: | --- |
| Chat Completions: `max_completion_tokens=10000`; no `max_tokens` | 8,192 | 2,657 | `finish_reason=length` |
| Responses: `max_output_tokens=10000`, `max_tokens=10000` | 8,192 | 1,820 | `incomplete`, `max_output_tokens` |

Both used 163 native input tokens. The Responses response again echoed the
requested 10,000-token allowance. These results show that **neither changing
the Chat Completions parameter to `max_completion_tokens` nor adding a second
`max_tokens` field to Responses overcame the ceiling in these tests**. The
previously inconclusive dual-field proposal now has a negative result under a
task that continued generating until the cutoff.

Generation IDs:

- Native-name Chat: `gen-1790113729-uReyFhkwyxtvShq5kg7a`.
- Dual-field Responses repeat: `gen-1790113732-ici1nOeLxY8UHzQMc8IR`.

Read-only generation metadata confirms `provider_name=Cerebras`,
`native_tokens_completion=8192`, and `native_finish_reason=length` for both.
Their upstream IDs are respectively
`chatcmpl-a7132766-e7eb-4165-ad72-0beb59554b25` and
`chatcmpl-e82404bd-5169-4c43-95f9-ae30860e5d73`.

Evidence files are in the same diagnostics directory, prefixed
`chat_native_limit` and `responses_both_limits_repeat`. The additional reported
cost was **$0.0124021**; all five diagnostics together cost **$0.02537365**.

Environment and `.env` **key names only** were checked for Cerebras credential
variables: no names containing Cerebras and KEY/TOKEN were present. No credential
values were displayed. A direct Cerebras comparison therefore cannot currently
be made using those configured credential sources. No direct-endpoint inference
or further paid diagnostic was performed. The remaining adapter-versus-backend
uncertainty requires provider-side evidence or a separately credentialed direct
test; there is still no validated parameter-only fix.

## Completed-game workaround

The main agent continued the same saved game with medium parent reasoning,
retaining the 40,960 request, high/900 oracle, and Cerebras-only routing. That
segment completed 124 decisions and the full game ended at round ten. Two more
8,192-token failures occurred and recovered on normal retries. This supports
medium reasoning as a practical workaround in this game; the advertised larger
completion allowance remains unverified on the actual route. See
[REPORT.md](REPORT.md) for interventions, results and cumulative accounting.
