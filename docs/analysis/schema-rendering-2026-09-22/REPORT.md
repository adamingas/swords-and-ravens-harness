# Why the model appeared not to know the action schema

## Revised diagnosis

The earlier explanation—that the model simply ignored a fully visible schema—
was too strong. We know the harness constructs the correct schema. We do not
know that the provider exposes that complete structure to the model.

A new offline reproduction found a concrete mechanism that exactly matches the
recorded behavior: the published GPT-OSS-120B chat template renders this game's
`decision` property, defined through `anyOf`, as **`decision: any`**. It drops the
`muster_units` and `skip_mustering` branches and all nested recruitment fields.

The source run's returned reasoning explicitly states:

> The tool schema for submit_action: It expects field "decision" (any).

It also says the detailed schema is not provided and that it needs to guess.
That text alone would not prove the provider's prompt format; the independent
reproduction makes schema-rendering loss a strong explanation.

## Evidence

1. An offline request through the installed Agents SDK and an HTTP mock preserved
   the recorded schema exactly, including `decision.anyOf`, both action enums,
   and `strict: true`. The SDK serialization does not lose those fields.
2. The [published GPT-OSS template](https://huggingface.co/openai/gpt-oss-120b/raw/main/chat_template.jinja)
   has no `anyOf` rendering branch. A property with only `anyOf` falls through to
   `any` in `render_typescript_type`.
3. Rendering the exact schema from run
   `673bf8bb-c19c-4e44-998c-03127917072b` produces:

   ```typescript
   type submit_action = (_: {
     decision: any,
     strategic_handoff: string,
   }) => any;
   ```

   The actual output, with its descriptions, is saved in
   [rendered-submission.txt](rendered-submission.txt). Assertions verify that
   `muster_units`, `mustering_region_id`, and `recruitments` disappear entirely.
4. Returning the literal JSON schema in a later tool-error message recovered the
   stuck mustering decision in three requests. This is consistent with supplying
   previously hidden details as ordinary message text, though it is not a
   controlled causal test.

The template also abbreviates sufficiently long nested array-item types as
`any[]`; therefore simply avoiding the outer `anyOf` is not necessarily enough
to preserve every recruitment field in this renderer.

## Limits and next correction

The exact provider-side prompt/template is not exposed. Thus this is a verified
failure of the published renderer for our schema, and a strong hypothesis for
the Cerebras route—not direct proof of its internal implementation. The original
run did not capture raw outbound HTTP bodies; the SDK wire check is a current
offline reproduction. Provider-side enforcement of our `strict: true` request
also remains unverified; the invalid outputs demonstrate it was not effectively
enforcing this schema on the observed route.

The harness should expose the exact action contract as ordinary prompt text
before the first attempt, without depending solely on provider tool-schema
rendering. Keep the authoritative validator, test model-facing rendering as well
as HTTP serialization, and bound repeated invalid-action repair. No production
change or paid model request was made during this investigation.

Reproduce:

```sh
uv run --with jinja2 python docs/analysis/schema-rendering-2026-09-22/reproduce.py
```

The script downloads only the public template, renders its definition macros in
Jinja's sandbox, and reads the recorded schema from the completed experiment.
The template hash and source run are recorded in [evidence.json](evidence.json).

## Cross-provider follow-up (2026-09-23)

The 56-probe comparison supports a
model/provider-specific problem: OSS union readback failed on Cerebras and
DeepInfra, passed on Groq, and recovered on both failing routes when the same
schema was supplied as normal text. Numeric enum constraints were also missed
on the failing OSS routes. Luna, DeepSeek, Qwen and GLM passed the tested
readback cases.

The actual Cerebras array probe retained opaque field values that this published
template's array abbreviation would remove. Therefore this reproduction should
not be treated as proof that the deployed provider uses the exact published
template. The observed failures and successful controls are stronger evidence
than assuming a particular internal renderer.
