"""Provider-independent run loops.

Factories supply a fresh Agent with model, instructions, settings and optional hooks.
The harness owns its tools and output type; memory belongs to the supplied context.
"""

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from abc import abstractmethod
from typing import Protocol, cast

from agents import Agent, FunctionTool, RunConfig, RunHooks, Runner, RunResult
from agents.items import TResponseInputItem
from agents.agent_output import AgentOutputSchemaBase


class OutputSchema[Output](AgentOutputSchemaBase):
    """Typed version of the SDK's custom output-schema interface."""

    @abstractmethod
    def validate_json(self, json_str: str) -> Output: ...


@dataclass
class Turn[Context, Output]:
    messages: str | list[TResponseInputItem]
    context: Context
    tools: list[FunctionTool]
    output_type: type[Output] | OutputSchema[Output]
    run_config: RunConfig = field(default_factory=RunConfig)
    hooks: RunHooks[Context] | None = None
    on_result: Callable[[RunResult], None] | None = None


class Harness[Context](Protocol):
    async def run[Output](self, turn: Turn[Context, Output]) -> Output: ...


def _new_agent[Context, Output](
    create_agent: Callable[[], Agent[Context]], turn: Turn[Context, Output]
) -> Agent[Context]:
    agent = create_agent()
    agent.tools = list(turn.tools)
    agent.mcp_servers = []
    agent.handoffs = []
    agent.output_type = turn.output_type
    agent.model_settings = replace(
        agent.model_settings.resolve(turn.run_config.model_settings), tool_choice="auto"
    )
    agent.tool_use_behavior = "run_llm_again"
    agent.reset_tool_choice = True
    return agent


async def _run[Context, Output](
    agent: Agent[Context],
    turn: Turn[Context, Output],
    messages: str | list[TResponseInputItem],
    max_turns: int,
) -> RunResult:
    result = await Runner.run(
        agent,
        messages,
        context=turn.context,
        max_turns=max_turns,
        # Settings were resolved onto the local agent, so stage changes take precedence.
        run_config=replace(turn.run_config, model_settings=None),
        hooks=turn.hooks,
    )
    if turn.on_result is not None:
        turn.on_result(result)
    return result


@dataclass
class StructuredOutputHarness[Context]:
    """Explore with tools and finish with a typed output in one SDK run."""

    create_agent: Callable[[], Agent[Context]]
    max_turns: int = 20

    async def run[Output](self, turn: Turn[Context, Output]) -> Output:
        agent = _new_agent(self.create_agent, turn)
        result = await _run(agent, turn, turn.messages, self.max_turns)
        return cast(Output, result.final_output)


@dataclass
class TwoStageHarness[Context]:
    """Explore, then reuse the decision's agent for one tool-free structured call."""

    create_agent: Callable[[], Agent[Context]]
    finalize_prompt: str
    max_turns: int = 20

    async def run[Output](self, turn: Turn[Context, Output]) -> Output:
        agent = _new_agent(self.create_agent, turn)
        agent.output_type = None
        exploration = await _run(agent, turn, turn.messages, self.max_turns)

        agent.tools = []
        agent.output_type = turn.output_type
        agent.model_settings = replace(
            agent.model_settings, tool_choice=None, parallel_tool_calls=None
        )
        messages = exploration.to_input_list()
        messages.append({"role": "user", "content": self.finalize_prompt})
        result = await _run(agent, turn, messages, 1)
        return cast(Output, result.final_output)
