# Harness failure observations: OSS-120B / Cerebras

Experiment: `data/evaluations/reachable-routes-oss-cerebras-20260922`.
The game completed at round ten with Baratheon winning (castle counts 4–4–3).
Entries below preserve observations at the time; final counts are in the closing
section and [REPORT.md](REPORT.md).
Source evidence is the experiment's `harness.db`, `decision-audit.json`,
`reachability-audit.json`, and `manifest.json`. No gameplay action was supplied
by the experiment operator. After the user authorized fixes, the saved game was
continued in `data/evaluations/reachable-routes-oss-cerebras-20260922-recovery`
with explicit schema feedback and a requested 40,960-token parent allowance.
The continuation records the original manifest and retains all earlier traces.

## 1. Raven action schema caused a long repair loop

**Observed:** Round-one Lannister wanted to skip changing an order. It made 30
`submit_action` calls: 29 rejected and one accepted, taking 60.2 seconds for that
decision. Run ID: `7117fe67-a05f-41d4-bab5-453f5c8c1193`.

Count corrected by the [23 September full-run audit](../oss-full-run-audit-2026-09-23/REPORT.md),
which also catalogs all gameplay mistakes, every unsuccessful submission and
every explicit pass. That audit discovered 83 persisted observations had mutated
after their model inputs were sent; it recovered and verified all 173 initial
inputs against their recorded hashes before assessing gameplay. The new report
contains the evidence and distinguishes this persistence defect from information
actually received by the model.

The first rejected arguments supplied `decision` as the string
`"skip_raven_order_replacement"`. Later attempts guessed other strings, used
`type` instead of `action`, or omitted `decision`. The eventual accepted shape
was `{"decision":{"action":"skip_raven_order_replacement"},"strategic_handoff":"…"}`.

**Assessment:** The validator correctly rejected malformed actions. However,
this is an interface/recovery weakness: the generic “not valid under any of the
given schemas” error and “correct the arguments” instruction did not make the
required object/discriminator shape clear enough to this model. Unbounded
within-decision repair allowed the same misunderstanding to consume many calls.
It is not evidence that the new reachability tool failed.

**Recovery:** The model eventually corrected itself; no restart or human move.

**Follow-up:** Return the failing JSON path, expected object shape, valid action
discriminators, and an example grounded in the currently offered schema. Consider
explicit handling of repeated identical validation errors, without silently
rewriting model intent or submitting a guessed action. Evaluate a flatter
multi-action schema against the existing nested shape before changing it.

## 2. Removing singleton action fields surprises the model

**Observed:** Several march decisions included `unit_ids` even though that field
had been removed from the model-facing schema because only one selection was
possible. The model sometimes changed it to `unitIds`, causing another rejection,
before omitting it. Examples:

- `312c329f-5628-46da-a62d-23069b8d431a`: unexpected `unit_ids`.
- `cfaaeb30-478a-4cda-abb1-ace5fb44e20f`: unexpected `unitIds`.
- `86fee893-a09e-4fdf-a0f7-7334e31004b8`: the first use of `reachable_areas`;
  rejected both spellings, then accepted a destination without either field.

**Assessment:** Validation and singleton restoration behaved as implemented.
The changing action shape creates avoidable repair work: the model sees units
in observations and remembers action conventions, but a field disappears in
some decisions. This is a harness usability issue rather than a wrong route.

**More consequential case:** Round-three Stark, run
`973e8175-07a1-4f9d-b70b-c46db002431a`, spent 63.5 seconds on 26 requests. Its
observation explicitly listed a supply-safe knight move from The Stony Shore to
Winterfell. However, `context_json.actionOutputSchema` reduced each `moves`
item to `{"type":"object","properties":{},"required":[],"additionalProperties":false}`.
The field description still instructed the model to supply destination groups
and unit IDs. Moving required `"moves":[{}]`; passing required `"moves":[]`.
The model tried multiple spellings of the removed fields, then discarded the
March order instead of executing its initially intended legal move. That is
observable loss of intended gameplay, not just latency. The schema's prose and
remaining fields give a particularly confusing interface in this case.

**Recovery:** Earlier examples removed extra fields and submitted accepted moves.
Stark instead abandoned the move. No human action or schema change was made.

**Follow-up:** Explicitly tell the model which values are supplied automatically,
or test retaining singleton fields with constrained values. Do not infer that
all extra fields should simply be ignored; an unexpected value can represent a
materially different intended move.

## 3. Output exhaustion stops complete-game autoplay

**Observed:** Some parent-agent Responses API calls ended with
`status=incomplete` and `incomplete_details.reason=max_output_tokens`. Their raw
usage recorded exactly 8,192 output tokens, almost entirely reasoning. The
harness does not explicitly set a parent output limit in this experiment.

Examples:

- Round-two Lannister, run `12dd0c63-6ba5-4262-b95d-6e030d625f3b`: 8,192 output
  tokens, 8,189 reasoning tokens; a normal retry recovered.
- Round-three Baratheon, runs `b2430998-f70f-45a6-960a-7711110fd158` and
  `d25afcc3-e88c-4930-99ac-ce2de4f0ec6f`: consecutive failures. The configured
  failure limit disabled autoplay and stopped the first process segment.

**Assessment:** These payloads indicate an effective endpoint output ceiling;
they do not establish which upstream layer imposed it. The response correctly
was not treated as an accepted gameplay action. The current bounded retry policy
can therefore prevent a full evaluation from completing unattended.

**Recovery:** Resumed the same saved game, agents, memory, model, routing and
runtime with the launcher's `--resume` option. No instructions, model parameters,
or game actions were changed. All failed runs and response usage remain recorded.

**Follow-up:** Investigate an explicit supported output allowance and/or reasoning
setting in a separately labelled experiment. Treat output exhaustion distinctly
from malformed actions and transport failures. Preserve failed response usage
and account for all resumed segments when reporting latency and cost.

## 4. Mustering repair loop and misuse of the rules oracle

**Observed:** Round-four Baratheon run
`673bf8bb-c19c-4e44-998c-03127917072b` made 75 `submit_action` attempts, four
rules-oracle calls, and one memory lookup without submitting a game action.
The segment was interrupted after 149.3 seconds to stop unproductive requests.
Partial raw responses and usage were preserved; the same save was retried with
a fresh decision transcript and unchanged runtime.

The model repeatedly invented `mustering_units` / `musteringUnits` shapes,
omitted the `action` discriminator, and did not construct the specified
`musters` / `mustering_region_id` / `recruitments` hierarchy. It asked the rules
oracle for the JSON action schema. That oracle knows game rules; it is not a
reliable source of the live parent action schema.

**Assessment:** Another failure to recover from nested-schema confusion. The
retry loop offers neither sufficiently explicit schema feedback nor a bound
on unproductive repair. Asking a rules-only oracle about a dynamic tool schema
also creates a misleading path for recovery.

**Follow-up:** Give schema errors actionable structure from the actual contract,
clarify the rules oracle's scope, and detect repeated unchanged failures.

## 5. Cancelled runs preserve calls but lose tool-result evidence

**Observed:** The interrupted mustering run stores 80 `partial_model_response`
blocks and four `rules_oracle` records. Flattening the parent responses yields
80 function calls but zero `function_call_output` records. Consequently the
exact validation errors returned to the model cannot be reconstructed from the
normal stored transcript; live event records only name tools and timings.

**Assessment:** This is an observability gap in cancellation persistence. A count
of explicit `{accepted:false}` outputs undercounts rejected submissions when
cancelled runs are included. The malformed calls can be independently compared
with `context_json.actionOutputSchema`, but that is a reconstructed validation
result, not the original returned error.

**Follow-up:** Persist tool calls and their complete results incrementally, or
capture the SDK transcript on cancellation in addition to raw provider payloads.
Do not label observed error-output counts as exhaustive.

## 6. Provider attribution is incomplete

**Observed:** Requests explicitly constrain OpenRouter to `only=["cerebras"]`
with `allow_fallbacks=false`. Returned trace records identify
`openai/gpt-oss-120b` but have no upstream `response_provider` field.

**Assessment:** Cerebras-only routing is recorded and reproducible, but backend
identity cannot be independently verified from those returned payloads. This is
an observability limitation, not evidence of incorrect routing.

## Reachability-specific status

At the time of this entry, Baratheon and Lannister had each used the tool once.
Both returned route results successfully. Baratheon's The Reach query included
King's Landing despite an insufficient current army, demonstrating geographic
rather than combat-feasibility filtering. It ultimately marched to Blackwater.
Lannister queried Seagard during planning. No reachability-tool error has been
observed so far; a completed game cannot by itself establish absence of bugs.

## Output-limit investigation

A delegated investigation confirmed the parent runner sets `max_tokens=None`,
which the installed Agents SDK serializes by omitting `max_output_tokens`.
Both live official catalogs advertise 40,960 completion tokens for this route.
An offline SDK wire test confirms that explicitly setting 40,960 sends the
corresponding Responses parameter. The layer imposing the 8,192 default remains
unidentified. See [CEREBRAS_OUTPUT_LIMIT.md](CEREBRAS_OUTPUT_LIMIT.md).

## Authorized recovery: schema repair succeeds, output ceiling persists

The recovery runner returns the exact current `expected_schema` on malformed
submissions, explains the nested action object, and labels fixed empty objects
explicitly (`[{}]` selects the fixed item; `[]` selects none). Wire tests cover
the rejected submission followed by a corrected, accepted action.

Round-four Baratheon mustering, previously stuck in two long loops, completed
in 11.352 seconds and three requests (run
`a4fdbf9e-9864-40a9-a53a-da6eca4340b8`). One malformed submission was followed
by a correct recruitment plan after receiving the schema. This is useful
evidence of recovery, though one decision is not a controlled comparison.

The next two Lannister attempts still exhausted output at exactly 8,192 tokens
despite the explicit 40,960 request (runs
`0ac4d779-caf5-458a-8003-06a2c33ee6e5` and
`b12bb675-0774-4fda-99dd-649a607a62cc`). Thus the local configuration fix alone
is insufficient. Separate bounded live probes reproduce 8,192 via both
Responses and Chat Completions; generation metadata attributes the probes to
Cerebras and reports a native length stop. The investigation report separates
verified behavior from the unresolved upstream cause.

Validation after these changes: 276 tests passed, including the original
Hypothesis properties, schema-repair wire tests, parent output-allowance tests,
and isolation of the oracle's 900-token allowance. See `recovery-tests.txt`.

## Medium-reasoning continuation

A further unchanged high-reasoning retry produced two more 8,192-token failures
at the same Lannister mustering decision. Five separate bounded diagnostics
(total $0.02537365) ruled out the tested Responses/Chat parameter spelling
workarounds; no direct Cerebras credentials are configured.

To continue the authorized full game, `run_game_medium.py` changes parent
reasoning effort from high to medium in a separately recorded continuation:
`data/evaluations/reachable-routes-oss-cerebras-20260922-medium`. It retains the
40,960-token request, model, Cerebras-only routing, provider blocklist, save,
private memory, and all earlier traces. The oracle remains high/900. An offline
settings check verified these distinctions. Lannister then completed the
previously blocked mustering decision. This is a workaround for reasoning
exhaustion, not a repair of the remote output ceiling.

## Final accounting and unresolved issues

The final continuation completed on 2026-09-22 at 21:55:15 UTC. Across all
segments there were 158 completed decision runs, 13 failed attempts, and two
cancelled attempts. All 13 failures involved 8,192-token exhaustion. Eleven
occurred before medium reasoning; two occurred during it. The medium segment
completed 124 decisions and recovered both failures through normal retries,
without another operator restart.

The two medium failures were Baratheon Raven order-replacement decisions:
`e6c6ef2f-9747-4f97-85e2-3c902c8e048f` (round nine) and
`5a00b219-72f0-403c-b556-471d2f24d3ff` (round ten). Both included invented schema
fields before output exhaustion. Thus explicit schema feedback materially helped
the blocked mustering case but did not eliminate all action-shape mistakes.

There were 94 explicit rejected-action outputs in retained transcripts, 27
during the medium continuation. Cancellation-related missing tool outputs make
this an incomplete rejection count. The unbounded repair loop, cancelled-output
persistence gap, and remote output ceiling remain unresolved. No fix to these
remaining issues is claimed.

`reachable_areas` was called four times: Baratheon once, Lannister once, Stark
twice. All returned successfully. There were no live empty-origin or transport
queries; automated tests cover those cases. The final database contains 527
recorded responses costing $7.94253165; five independent token diagnostics add
$0.02537365. See the report for cumulative token accounting and play examples.

## Why the request count was excessive

The final database contains **527 recorded provider responses**, comprising
493 parent-agent responses and 34 rules-oracle responses. This is distinct from
158 accepted game decisions. There are also 529 request-start events, two of
which have no returned usage record. A previously viewed intermediate count
(such as 514) should not be treated as the final total.

Two cancelled attempts at the same Baratheon mustering decision consumed 90
and 80 responses, including nested oracle work. Lannister's round-one Raven
decision consumed another 30 responses; Stark's round-three march consumed 26.
These four attempts alone account for **226 responses (42.9% of all recorded
responses)**. Across all runs, completed decisions used 340 responses, failed
attempts 17, and the two cancelled loops 170.

The operational mistake was letting the invalid-action loops continue for so
long. Consecutive-run failure limits do not limit validation failures inside an
ongoing run, because each rejected action is returned as an ordinary tool result
and generation continues. Schema feedback improved recovery but did not add
that missing bound. A targeted repeated-invalid-action safeguard is warranted;
this should distinguish unsuccessful repair from legitimate exploration. No
such safeguard was implemented during this experiment.

### Exact anatomy of the two mustering loops

Both attempts had the correct `submit_action` schema in the harness contract.
That does not prove the model saw its nested details: the later template
investigation reproduced their loss as `decision: any` (see below). The model
repeatedly guessed field names. The recorded arguments
have now been independently revalidated against each recorded schema: **75 of
75 submissions in the first attempt, and 73 of 73 in the second, were invalid**.
Neither attempt submitted a gameplay action.

| Attempt | Invalid submissions | Oracle calls | Memory calls | Nested oracle responses | Total responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| First | 75 | 4 | 1 | 10 | 90 |
| Second | 73 | 1 | 3 | 3 | 80 |

The parent responses corresponded to those submission/exploration calls; nested
oracle generations added another 13 responses. Total: 148 + 5 + 4 + 13 = 170.

For example, the model tried `decision: {skip_mustering: true}` instead of
`decision: {action: "skip_mustering"}`. Recruitment attempts invented
`mustering_units` or `musteringUnits`, omitted the `action` discriminator, and
failed to use the required `musters` groups containing `mustering_region_id` and
`recruitments`. The recruitment plan itself remained substantially unchanged.
It explicitly asked the rules oracle for the JSON field names, which that oracle
did not have.

The invalid-action feedback did not effectively guide correction, and the
within-run loop had no bound on repeated validation failures. Restarting without
fixing that cause reproduced the problem. These two attempts lasted about five
minutes combined and made zero gameplay progress. The later explicit-schema
feedback recovered this mustering decision in three requests.

## Important correction: likely loss in model-facing schema rendering

The initial interpretation that the model simply ignored a fully visible schema
was too strong. Its recorded reasoning explicitly describes `decision` as `any`.
An offline reproduction using the published GPT-OSS-120B chat template and the
actual recorded mustering schema produces exactly `decision: any`, discarding
both action branches and their required nested fields. The SDK preserves the
full JSON schema in its outbound serialization; the public template drops it
when rendering model-facing tool definitions.

This is verified for the published template. We cannot inspect Cerebras's
internal template, so attribution to its deployment remains a strong hypothesis
rather than directly observed fact. See
[the reproduction and revised diagnosis](../schema-rendering-2026-09-22/REPORT.md).
The earlier local-schema tests did not cover this provider-rendering boundary.

## Cross-model/provider experiments (2026-09-23)

The bounded comparison completed 56
single-request probes, with no repair loops, costing $0.1345032755 in reported
usage. OSS on Cerebras and DeepInfra failed union readback and controlled
mustering argument construction. OSS on Groq passed schema readback and built
valid nested mustering arguments, though it exceeded the requested recruitment
plan. The same providers worked with other tested models. Supplying literal
schema text recovered the OSS union readback on both failing routes.

The historical DeepSeek game had 147 schema-valid recorded submissions, including
ten first-attempt valid mustering plans. Generation metadata attributes those
ten mustering submissions to DeepInfra. The schema-visibility failure does not
explain all prior DeepSeek gameplay problems.
