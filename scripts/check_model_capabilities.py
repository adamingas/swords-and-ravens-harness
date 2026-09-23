"""Check model/provider capabilities through the Agents SDK; at most eight requests."""
import asyncio
from functools import partial
import secrets
from typing import Literal

from agents import Agent, ModelSettings, OpenAIResponsesModel, RunConfig, Runner, function_tool
import click
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field

from raven_harness.config import Settings


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Unit(Closed):
    region: Literal["region_c81f"]
    count: Literal[37]


class Recruit(Closed):
    action: Literal["recruit"]
    recruits: list[Unit] = Field(min_length=2, max_length=2)


class Move(Closed):
    action: Literal["move"]
    units: list[Unit] = Field(min_length=2, max_length=2)


class Submission(Closed):
    decision: Recruit | Move
    strategic_handoff: str


class Report(Closed):
    reference: str
    count: int


class Sample(Closed):
    name: str = Field(min_length=1)
    count: int = Field(ge=0)
    ratio: float = Field(ge=0, le=1)
    enabled: bool
    category: Literal["alpha", "beta"]
    tags: list[str] = Field(min_length=1)
    note: str | None = None
    retries: int = 3
    scores: list[int]


async def check_structured_output(model, settings):
    agent = Agent(name="structured_output_check", model=model, model_settings=settings,
                  output_type=Sample)
    result = await Runner.run(agent, "Return a sample satisfying the output schema. Use the defaults where defined.",
                              max_turns=1, run_config=RunConfig(tracing_disabled=True))
    return {"structured_output_without_tools": isinstance(result.final_output, Sample)}


async def check_simple_tools(model, settings):
    first, second = secrets.randbelow(90) + 10, secrets.randbelow(90) + 10
    calls, answers = [], []

    @function_tool(failure_error_function=None)
    def get_first_number() -> int:
        """Get the first number."""
        calls.append("get_first_number")
        return first

    @function_tool(failure_error_function=None)
    def get_second_number() -> int:
        """Get the second number."""
        calls.append("get_second_number")
        return second

    @function_tool(failure_error_function=None)
    def submit_answer(answer: int) -> str:
        """Submit the sum of the two numbers."""
        calls.append("submit_answer")
        answers.append(answer)
        return "accepted"

    agent = Agent(name="simple_tools_check", model=model, reset_tool_choice=False,
                  model_settings=settings.resolve(ModelSettings(tool_choice="auto")),
                  tools=[get_first_number, get_second_number, submit_answer],
                  tool_use_behavior={"stop_at_tool_names": ["submit_answer"]})
    await Runner.run(agent, "Get the two numbers using the tools, add them, and finish by calling submit_answer with their sum.",
                     max_turns=3, run_config=RunConfig(tracing_disabled=True))
    return {"simple_tools": len(calls) == 3 and set(calls[:2]) == {"get_first_number", "get_second_number"}
            and calls[-1] == "submit_answer" and answers == [first + second]}


async def check(model, settings, structured):
    expected = Report(reference=secrets.token_hex(16), count=secrets.randbelow(900000) + 100000)
    calls = []

    @function_tool(failure_error_function=None)
    def submit_action(submission: Submission) -> str:
        """Submit a synthetic action satisfying the tool schema."""
        calls.append("submit_action")
        return "accepted"

    @function_tool(failure_error_function=None)
    def read_reference() -> str:
        """Read the current reference."""
        calls.append("read_reference")
        return expected.reference

    @function_tool(failure_error_function=None)
    def read_count() -> int:
        """Read the current count."""
        calls.append("read_count")
        return expected.count

    agent = Agent(
        name="capability_check", model=model, reset_tool_choice=False,
        model_settings=settings.resolve(ModelSettings(tool_choice="auto")),
        tools=[read_reference, read_count] if structured else [submit_action],
        output_type=Report if structured else None,
        tool_use_behavior="run_llm_again" if structured else "stop_on_first_tool",
    )
    prompt = ("Read the current reference and count using the tools, then report both values."
              if structured else "Call submit_action once, satisfying every constraint in its schema. Either action is acceptable.")
    result = await Runner.run(agent, prompt, max_turns=3 if structured else 1,
                              run_config=RunConfig(tracing_disabled=True))
    if not structured:
        return {"complex_tool_schema": calls == ["submit_action"]}
    final = result.final_output
    return {"tools_to_structured_output": set(calls) == {"read_reference", "read_count"} and final == expected,
            "materialized_pydantic_type": isinstance(final, Report),
            "final_type": type(final).__name__}


@click.command(help=__doc__)
@click.option("--model", required=True)
@click.option("--provider", required=True, help="OpenRouter provider slug; fallbacks disabled")
@click.option("--max-output-tokens", type=click.IntRange(min=1), default=1024, show_default=True)
@click.option("--timeout", type=click.FloatRange(min=0, min_open=True), default=60, show_default=True,
              help="Seconds per capability check")
def main(**options):
    raise SystemExit(asyncio.run(run(**options)))


async def run(model, provider, max_output_tokens, timeout):
    config = Settings()
    if not config.openrouter_token:
        raise click.UsageError("Set OPENROUTER_TOKEN in your environment or .env")
    if provider.split("/")[0] in config.openrouter_blocked_providers:
        raise click.UsageError("Provider is blocked by the harness configuration")
    settings = ModelSettings(max_tokens=max_output_tokens, reasoning={"effort": "high"},
                             parallel_tool_calls=False, store=False,
                             extra_body={"provider": {"only": [provider], "allow_fallbacks": False,
                                                      "ignore": config.openrouter_blocked_providers}})
    checks = {}
    click.echo(f"{model} / {provider}")
    async with AsyncOpenAI(api_key=config.openrouter_token, base_url=config.openrouter_base_url,
                           max_retries=0, timeout=timeout) as client:
        sdk_model = OpenAIResponsesModel(model, client)
        for names, test in (
            (("tools_to_structured_output", "materialized_pydantic_type"), partial(check, structured=True)),
            (("complex_tool_schema",), partial(check, structured=False)),
            (("structured_output_without_tools",), check_structured_output),
            (("simple_tools",), check_simple_tools),
        ):
            try:
                async with asyncio.timeout(timeout):
                    checks.update(await test(sdk_model, settings))
            except Exception as error:
                checks.update(dict.fromkeys(names, False))
                click.echo(f"  {names[0]}: {type(error).__name__}: {error}")
    for name, value in checks.items():
        click.echo(f"  {name}: {('PASS' if value else 'FAIL') if isinstance(value, bool) else value}")
    return int(any(value is False for value in checks.values()))


if __name__ == "__main__":
    main()
