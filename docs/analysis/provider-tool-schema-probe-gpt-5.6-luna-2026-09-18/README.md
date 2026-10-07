# GPT-5.6 Luna provider tool/schema probe

This repeats the same OpenAI Agents SDK dummy experiment with
`openai/gpt-5.6-luna`: one required `double_number` tool, explicit prose
requiring its use, `tool_choice="auto"`, and a Pydantic final-output type sent as
native structured output. Each OpenRouter provider was pinned with fallbacks
disabled.

| Provider | Outcome |
|---|---|
| OpenAI | Called `double_number(21)` and returned valid Pydantic output |
| Azure | Called `double_number(21)`; the follow-up request then received an upstream 429 |
| Amazon Bedrock | OpenRouter found no eligible Bedrock endpoint for this structured-output request |

The OpenAI route produced two clean Responses API steps: a function call,
followed by the schema-valid final message. Azure also emitted the correct tool
call, so its observed failure was capacity on the second request rather than a
failure to combine tools with structured output.

The repository has no direct `OPENAI_API_KEY` configured. These requests used
OpenRouter with the OpenAI and Azure providers pinned; they were not sent from
the harness directly to `api.openai.com`.
