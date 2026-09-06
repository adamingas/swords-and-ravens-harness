from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from agents import FunctionTool
from agents.tool_context import ToolContext

from .config import PROJECT_ROOT, Settings
from .errors import safe_error_text
from .evaluation import (
    MUTABLE_GAME_SAVE_PATH,
    _git_provenance,
    _write_json,
    run_game,
)
from .harness.actions import HarnessRunContext
from .models.openai_agent import ModelRunResult
from .schemas import AgentRecord


SMOKE_MODEL_ID = "deterministic-protocol-smoke"
SAFE_ORDER_CATEGORIES = ("defense", "support")


class UnsupportedSmokeDecision(RuntimeError):
    """The real server requested a decision the safe smoke policy does not cover."""


class ScriptedProtocolRunner:
    """Invoke dynamic harness tools without making a model-provider request."""

    rules_oracle_available = False

    async def run_once(
        self,
        *,
        agent_record: AgentRecord,
        observation: dict[str, Any],
        context: HarnessRunContext,
        tools: list[FunctionTool],
        instructions: str,
        max_turns: int,
        stop_at_tool_names: list[str],
        prompt_cache_key: str,
        trace_metadata: dict[str, str],
    ) -> ModelRunResult:
        del agent_record, instructions, max_turns, prompt_cache_key, trace_metadata
        gameplay_tools = [tool for tool in tools if tool.name in stop_at_tool_names]
        tool = _select_safe_tool(gameplay_tools, observation)
        arguments = _safe_tool_arguments(tool, observation)
        encoded_arguments = json.dumps(arguments, separators=(",", ":"))
        call_id = f"protocol-smoke-{uuid4()}"
        output = await tool.on_invoke_tool(
            ToolContext(
                context=context,
                tool_call_id=call_id,
                tool_name=tool.name,
                tool_arguments=encoded_arguments,
            ),
            encoded_arguments,
        )
        if context.action_taken is None:
            raise RuntimeError(
                f"Scripted protocol tool {tool.name!r} returned without an accepted action"
            )
        output_text = str(output)
        return ModelRunResult(
            response_id=None,
            output_text=output_text,
            usage={
                "requests": 0,
                "inputTokens": 0,
                "outputTokens": 0,
                "totalTokens": 0,
            },
            response_items=[
                {
                    "type": "function_call",
                    "call_id": call_id,
                    "name": tool.name,
                    "arguments": encoded_arguments,
                },
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": output_text,
                },
            ],
            raw_usage=[],
            context_manifest={
                "policy": "deterministic-protocol-smoke-v1",
                "providerRequests": 0,
                "selectedTool": tool.name,
            },
        )

    async def shutdown(self) -> None:
        return None

    async def clear_session(self, agent_id: str) -> None:
        del agent_id


def _select_safe_tool(
    gameplay_tools: list[FunctionTool], observation: dict[str, Any]
) -> FunctionTool:
    tools_by_name = {tool.name: tool for tool in gameplay_tools}
    for name in ("submit_orders", "skip_raven_order_replacement"):
        if name in tools_by_name:
            return tools_by_name[name]
    state_path = observation.get("statePath", [])
    schemas = {
        tool.name: tool.params_json_schema for tool in gameplay_tools
    }
    raise UnsupportedSmokeDecision(
        "No fail-closed protocol-smoke policy for authoritative state "
        f"{state_path!r}; dynamic tool schemas: "
        f"{json.dumps(schemas, sort_keys=True, separators=(',', ':'))}"
    )


def _safe_tool_arguments(
    tool: FunctionTool, observation: dict[str, Any]
) -> dict[str, Any]:
    if tool.name == "skip_raven_order_replacement":
        return {}
    if tool.name != "submit_orders":
        raise UnsupportedSmokeDecision(
            f"No safe protocol-smoke arguments are defined for {tool.name!r}"
        )

    schema = tool.params_json_schema
    assignment_schema = schema.get("$defs", {}).get("OrderAssignment", {})
    assignment_properties = assignment_schema.get("properties", {})
    region_ids = assignment_properties.get("region_id", {}).get("enum")
    order_ids = assignment_properties.get("order", {}).get("enum")
    assignments_schema = schema.get("properties", {}).get("assignments", {})
    required_count = assignments_schema.get("minItems")
    constraints = observation.get("planningConstraints", {})
    capacities = constraints.get("maxAssignmentsByOrderCategory", {})
    if (
        not isinstance(region_ids, list)
        or not all(isinstance(item, str) for item in region_ids)
        or not isinstance(order_ids, list)
        or not isinstance(required_count, int)
        or required_count < 0
        or len(region_ids) < required_count
        or not isinstance(capacities, dict)
    ):
        raise UnsupportedSmokeDecision(
            "submit_orders did not expose the expected dynamic region, count, and "
            "category-capacity constraints"
        )

    selected_categories: list[str] = []
    for category in SAFE_ORDER_CATEGORIES:
        if category not in order_ids:
            continue
        capacity = capacities.get(category)
        if not isinstance(capacity, int) or capacity < 0:
            raise UnsupportedSmokeDecision(
                f"submit_orders did not expose a valid {category!r} capacity"
            )
        selected_categories.extend(
            [category] * min(capacity, required_count - len(selected_categories))
        )
        if len(selected_categories) == required_count:
            break
    if len(selected_categories) != required_count:
        raise UnsupportedSmokeDecision(
            "The current planning state requires an active order; the no-provider "
            "smoke only uses Defense and Support to avoid fabricating targets"
        )

    return {
        "assignments": [
            {
                "region_id": region_id,
                "order": category,
                "starred_preference": "avoid",
                "priority": required_count - index,
            }
            for index, (region_id, category) in enumerate(
                zip(region_ids[:required_count], selected_categories, strict=True)
            )
        ]
    }


async def run_protocol_smoke(args: argparse.Namespace) -> Path:
    output = _resolve_output(args.output)
    output.mkdir(parents=True, exist_ok=False)
    artifact_path = output / "smoke.json"
    artifact: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "deterministic-no-provider-protocol-smoke",
        "status": "running",
        "startedAt": _now(),
        "providerRequests": 0,
        "maxRounds": 1,
        "repositories": {
            "root": _git_provenance(PROJECT_ROOT, ignore_dirty_submodules=True),
            "swordsAndRavens": _git_provenance(
                PROJECT_ROOT / "swords-and-ravens",
                ignored_paths=(MUTABLE_GAME_SAVE_PATH,),
            ),
        },
    }
    _write_json(artifact_path, artifact)
    settings = Settings(
        openrouter_token="",
        openai_api_key="",
        otel_exporter_otlp_traces_endpoint="",
        autoplay_max_consecutive_failures=1,
        autoplay_retry_base_seconds=0.1,
        _env_file=None,
    )
    try:
        result = await run_game(
            game_number=1,
            attempt_dir=output,
            model=SMOKE_MODEL_ID,
            game_port=args.game_port,
            max_rounds=1,
            poll_seconds=0.1,
            stall_seconds=args.stall_seconds,
            match_timeout_seconds=args.timeout_seconds,
            settings=settings,
            model_runner=ScriptedProtocolRunner(),
        )
    except Exception as error:
        artifact.update(
            {
                "status": "failed",
                "finishedAt": _now(),
                "error": safe_error_text(error),
            }
        )
        _write_json(artifact_path, artifact)
        raise RuntimeError(artifact["error"]) from None

    artifact.update(
        {
            "status": "completed",
            "finishedAt": _now(),
            "winner": result["winner"],
            "round": result["round"],
            "runCounts": {
                standing["configuration"]: standing["metrics"]["statusCounts"]
                for standing in result["standings"]
            },
            "artifacts": {
                "database": "harness.db",
                "game": "game.json",
                "result": "result.json",
                "serverLog": "game-server.log",
            },
        }
    )
    _write_json(artifact_path, artifact)
    return output


def _resolve_output(value: str | None) -> Path:
    if value:
        path = Path(value).expanduser()
        return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return PROJECT_ROOT / "data" / "evaluations" / f"protocol-smoke-{stamp}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic six-player one-round protocol smoke without model calls."
        )
    )
    parser.add_argument("--output", help="New artifact directory under the project root.")
    parser.add_argument("--game-port", type=int, default=5102)
    parser.add_argument("--stall-seconds", type=float, default=30, help=argparse.SUPPRESS)
    parser.add_argument("--timeout-seconds", type=float, default=180, help=argparse.SUPPRESS)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        output = asyncio.run(run_protocol_smoke(args))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    print(f"Protocol smoke artifacts: {output}")


if __name__ == "__main__":
    main()
