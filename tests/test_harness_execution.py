import asyncio
import json
from dataclasses import dataclass, field

import pytest
from agents import (
    Agent,
    Model,
    ModelResponse,
    ModelSettings,
    MaxTurnsExceeded,
    RunConfig,
    RunContextWrapper,
    RunHooks,
    Usage,
    function_tool,
)
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)
from pydantic import BaseModel, ConfigDict

from raven_harness.harness.execution import (
    Harness,
    StructuredOutputHarness,
    Turn,
    TwoStageHarness,
)


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    number: int


@dataclass
class Memory:
    number: int
    reads: list[int] = field(default_factory=list)


@function_tool
def read_number(ctx: RunContextWrapper[Memory]) -> int:
    """Read the number from memory."""
    ctx.context.reads.append(ctx.context.number)
    return ctx.context.number


def message(text):
    return ResponseOutputMessage(
        id="answer",
        role="assistant",
        status="completed",
        type="message",
        content=[ResponseOutputText(type="output_text", text=text, annotations=[])],
    )


def tool_call(index=0):
    return ResponseFunctionToolCall(
        call_id=f"read-{index}",
        name="read_number",
        arguments="{}",
        type="function_call",
    )


class ScriptedModel(Model):
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.requests = []

    async def get_response(self, **kwargs):
        self.requests.append(kwargs)
        output = next(self.outputs)
        if isinstance(output, BaseException):
            raise output
        if callable(output):
            output = await output()
        return ModelResponse(
            output=[output],
            usage=Usage(requests=1, input_tokens=10, output_tokens=5, total_tokens=15),
            response_id=f"response-{len(self.requests)}",
        )

    async def stream_response(self, **kwargs):
        raise NotImplementedError
        yield


class Recorder(RunHooks[Memory]):
    def __init__(self):
        self.agents = []
        self.contexts = []
        self.responses = []

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        self.agents.append(agent)
        self.contexts.append(context.context)

    async def on_llm_end(self, context, agent, response):
        self.responses.append(response)


def make_harness(kind, model, **kwargs):
    def factory():
        return Agent(
            name="player",
            model=model,
            instructions="Inspect memory before answering.",
            model_settings=ModelSettings(max_tokens=200, tool_choice="required"),
        )

    if kind is TwoStageHarness:
        kwargs["finalize_prompt"] = "Return your answer using the required output type."
    return kind(factory, **kwargs)


def turn(number=42, **kwargs):
    return Turn(
        messages=[{"role": "user", "content": "Read my number and return it."}],
        context=Memory(number),
        tools=[read_number],
        output_type=Answer,
        run_config=RunConfig(
            tracing_disabled=True,
            model_settings=ModelSettings(
                tool_choice="required",
                parallel_tool_calls=False,
                max_tokens=150,
            ),
        ),
        **kwargs,
    )


@pytest.mark.parametrize("kind", [StructuredOutputHarness, TwoStageHarness])
async def test_tools_run_and_typed_answer_preserves_context_and_transcript(kind):
    outputs = [tool_call()]
    if kind is TwoStageHarness:
        outputs.append(message("I have read the number."))
    outputs.append(message('{"number":42}'))
    model = ScriptedModel(outputs)
    hooks = Recorder()
    decision = turn(hooks=hooks)
    harness: Harness[Memory] = make_harness(kind, model)

    answer = await harness.run(decision)

    assert answer == Answer(number=42)
    assert isinstance(answer, Answer)
    assert decision.context.reads == [42]
    assert all(context is decision.context for context in hooks.contexts)
    assert all(agent is hooks.agents[0] for agent in hooks.agents)
    assert len(hooks.responses) == len(outputs)
    final = model.requests[-1]
    tool_results = [
        item for item in final["input"] if item.get("type") == "function_call_output"
    ]
    assert len(tool_results) == 1
    assert tool_results[0]["output"] == "42"
    assert tool_results[0]["call_id"] == "read-0"
    assert any(item.get("type") == "function_call" for item in final["input"])
    assert final["input"][0] == decision.messages[0]
    assert all(
        r["system_instructions"] == "Inspect memory before answering."
        for r in model.requests
    )
    assert all(r["model_settings"].max_tokens == 150 for r in model.requests)
    assert model.requests[0]["model_settings"].tool_choice == "auto"
    assert [t.name for t in model.requests[0]["tools"]] == ["read_number"]
    assert decision.tools == [read_number]
    assert len(decision.messages) == 1
    assert decision.run_config.model_settings.tool_choice == "required"

    if kind is TwoStageHarness:
        assert all(r["output_schema"] is None for r in model.requests[:-1])
        assert final["tools"] == []
        assert final["model_settings"].tool_choice is None
        assert final["model_settings"].parallel_tool_calls is None
        assert final["input"][-1]["content"] == harness.finalize_prompt
        assert any("I have read the number." in str(item) for item in final["input"])
    else:
        assert all(r["output_schema"] is not None for r in model.requests)
        assert [t.name for t in final["tools"]] == ["read_number"]
    assert final["output_schema"].validate_json('{"number":42}') == answer


@pytest.mark.parametrize("kind", [StructuredOutputHarness, TwoStageHarness])
async def test_repeated_tools_are_bounded(kind):
    model = ScriptedModel([tool_call(i) for i in range(3)])
    with pytest.raises(MaxTurnsExceeded):
        await make_harness(kind, model, max_turns=2).run(turn())
    assert len(model.requests) == 2


async def test_concurrent_turns_share_harness_but_not_agents_or_memory():
    both_started = asyncio.Event()
    started = 0
    models = []
    agents = []

    async def meet():
        nonlocal started
        started += 1
        if started == 2:
            both_started.set()
        await both_started.wait()
        return tool_call()

    def factory():
        number = 41 + len(agents)
        model = ScriptedModel(
            [meet, message("Ready."), message(json.dumps({"number": number}))]
        )
        agent = Agent(name="player", model=model)
        models.append(model)
        agents.append(agent)
        return agent

    harness = TwoStageHarness(factory, finalize_prompt="Return the number.")
    decisions = [turn(41, hooks=Recorder()), turn(42, hooks=Recorder())]
    results = await asyncio.wait_for(
        asyncio.gather(*(harness.run(decision) for decision in decisions)),
        timeout=5,
    )

    assert results == [Answer(number=41), Answer(number=42)]
    assert agents[0] is not agents[1]
    for decision, agent, model in zip(decisions, agents, models, strict=True):
        assert decision.context.reads == [decision.context.number]
        assert all(item is agent for item in decision.hooks.agents)
        assert model.requests[-1]["tools"] == []
        assert model.requests[0]["output_schema"] is None


async def test_cancelling_finalization_does_not_block_another_turn():
    finalizing = asyncio.Event()

    async def wait_for_cancellation():
        finalizing.set()
        await asyncio.Event().wait()

    models = iter(
        [
            ScriptedModel([message("Ready."), wait_for_cancellation]),
            ScriptedModel([tool_call(), message("Ready."), message('{"number":42}')]),
        ]
    )
    harness = TwoStageHarness(
        lambda: Agent(name="player", model=next(models)),
        finalize_prompt="Return the number.",
    )
    task = asyncio.create_task(harness.run(turn()))
    try:
        await asyncio.wait_for(finalizing.wait(), timeout=5)
        assert await asyncio.wait_for(harness.run(turn()), timeout=5) == Answer(
            number=42
        )
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_finalization_has_exactly_one_request_even_if_model_returns_nothing():
    class EmptyModel(ScriptedModel):
        async def get_response(self, **kwargs):
            response = await super().get_response(**kwargs)
            if len(self.requests) == 2:
                response.output = []
            return response

    model = EmptyModel([message("Ready."), message("")])
    with pytest.raises(MaxTurnsExceeded):
        await make_harness(TwoStageHarness, model).run(turn())
    assert len(model.requests) == 2
