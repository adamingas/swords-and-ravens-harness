from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from copy import deepcopy
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
    resolve_evaluation_output,
    run_game,
)
from .harness.actions import HarnessRunContext
from .models.openai_agent import ModelRunResult
from .schemas import AgentRecord


SMOKE_MODEL_ID = "deterministic-protocol-smoke"
PROTOCOL_SMOKE_RANDOM_SEED = 1
ORDER_PLAN = ("march", "raid", "consolidate_power", "support", "defense")
REQUIRED_TOOL_COVERAGE = {
    "choose_combat_house_card",
    "inspect_top_wildling_card",
    "place_inspected_wildling_card",
    "resolve_consolidate_power",
    "resolve_march",
    "resolve_raid",
    "submit_orders",
}
REQUIRED_TOOL_COUNTS = {
    name: 2 if name == "choose_combat_house_card" else 1
    for name in REQUIRED_TOOL_COVERAGE
}


class UnsupportedSmokeDecision(RuntimeError):
    """The real server requested a decision the safe smoke policy does not cover."""


class ScriptedProtocolRunner:
    """Coordinate six deterministic players without a model-provider request."""

    rules_oracle_available = False

    def __init__(self) -> None:
        self._decision_lock = asyncio.Lock()
        self.invocations: list[dict[str, Any]] = []
        self._combat_seen = False
        self._protected_houses: set[str] = set()
        self._order_rejection_checked = False
        self.order_rejection_probe: dict[str, Any] | None = None
        self._private_order_expectation: dict[str, Any] | None = None
        self.order_privacy_probe: dict[str, Any] | None = None

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
        async with self._decision_lock:
            return await self._run_once(
                agent_record=agent_record,
                observation=observation,
                context=context,
                tools=tools,
                instructions=instructions,
                max_turns=max_turns,
                stop_at_tool_names=stop_at_tool_names,
                prompt_cache_key=prompt_cache_key,
                trace_metadata=trace_metadata,
            )

    async def _run_once(
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
        house_id = str(observation.get("you", {}).get("houseId"))
        self._check_private_order_mask(context, house_id)
        gameplay_tools = [tool for tool in tools if tool.name in stop_at_tool_names]
        tool = _select_safe_tool(gameplay_tools, observation)
        if tool.name == "submit_orders":
            region_ids = (
                tool.params_json_schema.get("$defs", {})
                .get("OrderAssignment", {})
                .get("properties", {})
                .get("region_id", {})
                .get("enum", [])
            )
            adjacency = _enemy_adjacency(region_ids, observation)
            if adjacency is not None:
                self._protected_houses.update(
                    {
                        house_id,
                        adjacency[1],
                    }
                )
            if not self._order_rejection_checked:
                self.order_rejection_probe = await _probe_rejected_order_submission(
                    context,
                    region_ids,
                    house_id,
                )
                self._order_rejection_checked = True
        arguments = _safe_tool_arguments(
            tool,
            observation,
            combat_seen=self._combat_seen,
            protected_houses=self._protected_houses,
        )
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
        if tool.name == "submit_orders" and self._private_order_expectation is None:
            self._record_private_order_expectation(context, house_id)
        state_path = observation.get("statePath", [])
        if "combat" in state_path or tool.name in {
            "choose_combat_house_card",
            "declare_support",
            "use_valyrian_steel_blade",
        }:
            self._combat_seen = True
        self.invocations.append(
            {
                "tool": tool.name,
                "house": observation.get("you", {}).get("houseId"),
                "statePath": state_path,
                "accepted": True,
                "stateId": (context.client.snapshot or {}).get("leafStateId"),
            }
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

    def _record_private_order_expectation(
        self,
        context: HarnessRunContext,
        house_id: str,
    ) -> None:
        assert context.action_taken is not None
        message = context.action_taken.messages[0]
        orders = message.get("orders")
        if not isinstance(orders, list) or not orders:
            raise RuntimeError("The successful order submission has no wire orders")
        expected = sorted(
            [[item["regionId"], item["orderId"]] for item in orders],
            key=lambda item: str(item[0]),
        )
        region_ids = [str(item[0]) for item in expected]
        marker = _player_order_marker(context.client.snapshot, region_ids, house_id)
        if marker["orders"] != expected:
            raise RuntimeError("The submitting player did not receive its exact order IDs")
        self._private_order_expectation = {
            "ownerHouse": house_id,
            "regionIds": region_ids,
        }

    def _check_private_order_mask(
        self,
        context: HarnessRunContext,
        house_id: str,
    ) -> None:
        expected = self._private_order_expectation
        if (
            expected is None
            or self.order_privacy_probe is not None
            or house_id == expected["ownerHouse"]
        ):
            return
        marker = _player_order_marker(
            context.client.snapshot,
            expected["regionIds"],
            house_id,
        )
        orders = marker["orders"]
        if len(orders) != len(expected["regionIds"]) or any(
            item[1] is not None for item in orders
        ):
            raise RuntimeError("Another player received private planning order IDs")
        self.order_privacy_probe = {
            "ownerReceivedExactOrderIds": True,
            "opponentReceivedOnlyHiddenOrders": True,
            "observedOrderCount": len(orders),
        }

    async def shutdown(self) -> None:
        return None

    async def clear_session(self, agent_id: str) -> None:
        del agent_id


def _select_safe_tool(
    gameplay_tools: list[FunctionTool], observation: dict[str, Any]
) -> FunctionTool:
    tools_by_name = {tool.name: tool for tool in gameplay_tools}
    # Prefer decisions that exercise a complete base-game round. Each selection
    # is conservative: bids are zero, optional effects are declined, and combat
    # cards without abilities are preferred by the argument policy below.
    for name in (
        "submit_orders",
        "place_inspected_wildling_card",
        "inspect_top_wildling_card",
        "resolve_raid",
        "resolve_march",
        "declare_support",
        "choose_combat_house_card",
        "use_valyrian_steel_blade",
        "select_units",
        "select_region",
        "resolve_consolidate_power",
        "skip_mustering",
        "auto_reconcile_armies",
        "resolve_track_ties",
        "choose_option",
        "select_house_card",
        "submit_bid",
        "select_orders",
        "skip_raven_order_replacement",
    ):
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
    tool: FunctionTool,
    observation: dict[str, Any],
    *,
    combat_seen: bool = False,
    protected_houses: set[str] | None = None,
) -> dict[str, Any]:
    if tool.name in {
        "auto_reconcile_armies",
        "inspect_top_wildling_card",
        "skip_mustering",
        "skip_raven_order_replacement",
    }:
        return {}
    if tool.name == "submit_orders":
        return _safe_order_arguments(tool, observation)
    if tool.name == "place_inspected_wildling_card":
        return {"destination": "top"}
    if tool.name == "resolve_raid":
        return {
            "order_region_id": _first_enum(tool, "order_region_id"),
            "target_region_id": None,
        }
    if tool.name == "resolve_march":
        return _safe_march_arguments(tool, observation, combat_seen=combat_seen)
    if tool.name == "declare_support":
        return {"house_id": "none"}
    if tool.name in {"choose_combat_house_card", "select_house_card"}:
        card_field = "house_card_id"
        arguments = {card_field: _safe_house_card(tool, observation, card_field)}
        if tool.name == "choose_combat_house_card":
            arguments["force_valyrian_blade_decision"] = False
        return arguments
    if tool.name == "use_valyrian_steel_blade":
        return {"use": False}
    if tool.name == "select_units":
        return {"selections": _safe_unit_selections(tool, observation)}
    if tool.name == "select_region":
        return {"region_id": _first_enum(tool, "region_id")}
    if tool.name == "resolve_consolidate_power":
        return {
            "region_id": _first_enum(tool, "region_id"),
            "choice": "gain_power_tokens",
        }
    if tool.name == "resolve_track_ties":
        return {
            "ranked_tie_groups": [
                list(houses)
                for _bid, houses in observation.get("pendingDecision", {}).get(
                    "bidResults", []
                )
                if len(houses) > 1
            ]
        }
    if tool.name == "choose_option":
        return {
            "choice_index": _safe_choice_index(
                tool, observation, protected_houses or set()
            )
        }
    if tool.name == "submit_bid":
        return {"amount": 0}
    if tool.name == "select_orders":
        field = tool.params_json_schema.get("properties", {}).get("region_ids", {})
        count = field.get("minItems")
        region_ids = field.get("items", {}).get("enum")
        if not isinstance(count, int) or not isinstance(region_ids, list):
            raise UnsupportedSmokeDecision("select_orders did not expose exact regions")
        return {"region_ids": region_ids[:count]}
    raise UnsupportedSmokeDecision(
        f"No safe protocol-smoke arguments are defined for {tool.name!r}"
    )


def _safe_order_arguments(
    tool: FunctionTool, observation: dict[str, Any]
) -> dict[str, Any]:

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

    if required_count == 0:
        return {"assignments": []}

    # The initial six-player setup has one enemy-adjacent region pair. In round
    # one, the alphabetically first house Raids a Support order across that pair.
    # In round two, it Marches across the same pair to start a real combat. This
    # derives coordination from public state instead of hard-coded house or map IDs.
    adjacency = _enemy_adjacency(region_ids, observation)
    round_number = int(observation.get("game", {}).get("round") or 1)
    region_details = {
        item.get("id"): item
        for item in observation.get("map", {}).get("regions", [])
    }
    if adjacency is None:
        first_region = next(
            (
                item
                for item in region_ids
                if int(region_details.get(item, {}).get("castleLevel") or 0) == 0
            ),
            region_ids[0],
        )
        first_category = "march"
    else:
        first_region, enemy_house = adjacency
        own_house = str(observation.get("you", {}).get("houseId"))
        if own_house < enemy_house:
            first_category = "raid" if round_number == 1 else "march"
        else:
            first_category = "support"
    if (
        first_category not in order_ids
        or not isinstance(capacities.get(first_category), int)
        or capacities[first_category] < 1
    ):
        fallback_categories = (
            ("defense", "consolidate_power", "raid")
            if adjacency is not None and own_house >= enemy_house
            else ORDER_PLAN
        )
        first_category = next(
            (
                category
                for category in fallback_categories
                if category in order_ids
                and isinstance(capacities.get(category), int)
                and capacities[category] > 0
            ),
            "",
        )
        if not first_category:
            raise UnsupportedSmokeDecision(
                "submit_orders has no category for the first selected region"
            )
    remaining_regions = [item for item in region_ids if item != first_region]
    selected = [(first_region, first_category)]
    remaining_categories = [
        item
        for item in ORDER_PLAN
        if item != first_category
        and item in order_ids
        and isinstance(capacities.get(item), int)
        and capacities[item] > 0
    ]
    for category in remaining_categories:
        if not remaining_regions:
            break
        if category == "consolidate_power":
            region_id = next(
                (
                    item
                    for item in remaining_regions
                    if int(region_details.get(item, {}).get("castleLevel") or 0) > 0
                ),
                remaining_regions[0],
            )
        else:
            region_id = remaining_regions[0]
        selected.append((region_id, category))
        remaining_regions.remove(region_id)
    selected = selected[:required_count]
    selected_categories = [category for _region_id, category in selected]
    if len(selected_categories) != required_count:
        raise UnsupportedSmokeDecision(
            "The current planning state has more regions than the deterministic "
            "base-game order plan covers"
        )
    counts = Counter(selected_categories)
    if any(
        category not in order_ids
        or not isinstance(capacities.get(category), int)
        or count > capacities[category]
        for category, count in counts.items()
    ):
        raise UnsupportedSmokeDecision(
            "The deterministic base-game order plan exceeds a dynamic category capacity"
        )

    return {
        "assignments": [
            {
                "region_id": region_id,
                "order": category,
                "starred_preference": (
                    "prefer" if category == "consolidate_power" else "avoid"
                ),
                "priority": required_count - index,
            }
            for index, (region_id, category) in enumerate(selected)
        ]
    }


async def _probe_rejected_order_submission(
    context: HarnessRunContext,
    region_ids: list[str],
    house_id: str,
) -> dict[str, Any]:
    if not region_ids:
        raise UnsupportedSmokeDecision(
            "The atomic order-rejection probe requires at least one eligible region"
        )
    before = _player_order_marker(context.client.snapshot, region_ids, house_id)
    orders = [
        {
            "regionId": region_id,
            "orderId": 999_999 if index == 0 else None,
        }
        for index, region_id in enumerate(region_ids)
    ]
    result = await context.client.submit_orders(
        orders,
        expected_generation=context.connection_generation,
    )
    if result.response.get("accepted") is not False:
        raise RuntimeError("The game server accepted the invalid order probe")
    if result.response.get("reason") != "unknown-order":
        raise RuntimeError(
            "The game server returned an unexpected invalid-order reason: "
            f"{result.response.get('reason')!r}"
        )
    after = _player_order_marker(result.snapshot, region_ids, house_id)
    if after != before:
        raise RuntimeError("The rejected order probe changed authoritative player state")
    return {
        "accepted": False,
        "reason": "unknown-order",
        "stateId": result.response.get("stateId"),
        "stateUnchanged": True,
    }


def _player_order_marker(
    snapshot: dict[str, Any] | None,
    region_ids: list[str],
    house_id: str,
) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise RuntimeError("The order submission probe has no authoritative snapshot")
    ingame = snapshot.get("childGameState", {})
    planning = ingame.get("childGameState", {})
    place_orders = planning.get("childGameState", {})
    eligible = set(region_ids)
    player_orders = [
        item
        for item in planning.get("placedOrders", [])
        if isinstance(item, list) and len(item) == 2 and item[0] in eligible
    ]
    return deepcopy(
        {
            "leafStateId": snapshot.get("leafStateId"),
            "orders": sorted(player_orders, key=lambda item: str(item[0])),
            "ready": house_id in place_orders.get("readyHouses", []),
        }
    )


def _enemy_adjacency(
    eligible_region_ids: list[str], observation: dict[str, Any]
) -> tuple[str, str] | None:
    own_house = observation.get("you", {}).get("houseId")
    enemy_regions = {
        item.get("id"): str(item.get("units", [{}])[0].get("allegiance"))
        for item in observation.get("board", [])
        if item.get("units")
        and item["units"][0].get("allegiance") not in {None, own_house}
    }
    neighbours = {
        item.get("id"): set(item.get("neighbours", []))
        for item in observation.get("map", {}).get("regions", [])
    }
    for region_id in eligible_region_ids:
        adjacent_enemies = sorted(neighbours.get(region_id, set()) & enemy_regions.keys())
        if adjacent_enemies:
            return region_id, enemy_regions[adjacent_enemies[0]]
    return None


def _safe_march_arguments(
    tool: FunctionTool,
    observation: dict[str, Any],
    *,
    combat_seen: bool,
) -> dict[str, Any]:
    options = observation.get("actionGuidance", {}).get("legalOrderRegions", [])
    allowed_sources = set(
        tool.params_json_schema.get("properties", {})
        .get("starting_region_id", {})
        .get("enum", [])
    )
    if not isinstance(options, list) or not allowed_sources:
        raise UnsupportedSmokeDecision("resolve_march did not expose exact legal options")
    option = next(
        (item for item in options if item.get("regionId") in allowed_sources), None
    )
    if option is None:
        raise UnsupportedSmokeDecision("resolve_march has no usable order region")
    target = None
    if not combat_seen:
        target = next(
            (
                item
                for candidate in options
                if candidate.get("regionId") in allowed_sources
                for item in candidate.get("reachableRegions", [])
                if item.get("triggersCombat") and item.get("controller") is not None
            ),
            None,
        )
        if target is not None:
            option = next(
                candidate
                for candidate in options
                if target in candidate.get("reachableRegions", [])
            )
    moves = []
    if target is not None:
        moves.append(
            {
                "destination_region_id": target["regionId"],
                "unit_ids": list(option.get("unitIds", [])),
            }
        )
    return {
        "starting_region_id": option["regionId"],
        "moves": moves,
        "leave_power_token": False,
    }


def _safe_house_card(
    tool: FunctionTool, observation: dict[str, Any], field_name: str
) -> str:
    allowed = (
        tool.params_json_schema.get("properties", {}).get(field_name, {}).get("enum")
    )
    if not isinstance(allowed, list) or not allowed:
        raise UnsupportedSmokeDecision(f"{tool.name} did not expose exact card IDs")
    cards = {
        item.get("id"): item
        for item in observation.get("you", {}).get("availableHouseCards", [])
    }
    return max(
        allowed,
        key=lambda card_id: (
            cards.get(card_id, {}).get("ability") is None,
            int(cards.get(card_id, {}).get("strength") or 0),
            card_id,
        ),
    )


def _safe_unit_selections(
    tool: FunctionTool, observation: dict[str, Any]
) -> list[dict[str, Any]]:
    del tool
    pending = observation.get("pendingDecision", {})
    possible = [int(item) for item in pending.get("possibleUnits", [])]
    expected = min(int(pending.get("count", 0)), len(possible))
    if pending.get("canBeSkipped"):
        expected = 0
    if expected == 0:
        return []
    by_region: dict[str, list[int]] = {}
    for region in observation.get("board", []):
        selected = [
            int(unit["id"])
            for unit in region.get("units", [])
            if int(unit.get("id", -1)) in possible
        ]
        if selected:
            by_region[str(region["id"])] = selected
    if pending.get("selectedUnitsMustBeOfSameRegion"):
        region_id, unit_ids = next(
            (
                (region_id, unit_ids)
                for region_id, unit_ids in sorted(by_region.items())
                if len(unit_ids) >= expected
            ),
            ("", []),
        )
        if not region_id:
            raise UnsupportedSmokeDecision(
                "select_units cannot satisfy the same-region constraint"
            )
        return [{"region_id": region_id, "unit_ids": unit_ids[:expected]}]
    map_neighbours = {
        item.get("id"): set(item.get("neighbours", []))
        for item in observation.get("map", {}).get("regions", [])
    }
    own_house = observation.get("you", {}).get("houseId")
    enemy_regions = {
        region.get("id")
        for region in observation.get("board", [])
        if region.get("units")
        and region["units"][0].get("allegiance") not in {None, own_house}
    }
    ordered_regions = sorted(
        by_region.items(),
        key=lambda item: (
            bool(map_neighbours.get(item[0], set()) & enemy_regions),
            item[0],
        ),
    )
    result = []
    remaining = expected
    for region_id, unit_ids in ordered_regions:
        chosen = unit_ids[:remaining]
        if chosen:
            result.append({"region_id": region_id, "unit_ids": chosen})
            remaining -= len(chosen)
        if remaining == 0:
            return result
    raise UnsupportedSmokeDecision("select_units could not locate every offered unit")


def _safe_choice_index(
    tool: FunctionTool,
    observation: dict[str, Any],
    protected_houses: set[str],
) -> int:
    allowed = (
        tool.params_json_schema.get("properties", {})
        .get("choice_index", {})
        .get("enum")
    )
    if not isinstance(allowed, list) or not allowed:
        raise UnsupportedSmokeDecision("choose_option did not expose exact indexes")
    pending = observation.get("pendingDecision", {})
    choices = pending.get("choices", [])
    protected = {item.casefold() for item in protected_houses}
    candidates = [
        index
        for index in allowed
        if isinstance(index, int) and 0 <= index < len(choices)
    ]
    if not candidates:
        return int(allowed[0])

    description = str(pending.get("description", "")).casefold()
    if "lowest bidder" in description:
        unprotected = [
            index
            for index in candidates
            if str(choices[index]).casefold() not in protected
        ]
        if unprotected:
            candidates = unprotected

    destructive_terms = ("destroy", "remove", "kill", "discard")
    return min(
        candidates,
        key=lambda index: (
            any(term in str(choices[index]).casefold() for term in destructive_terms),
            index,
        ),
    )


def _first_enum(tool: FunctionTool, field_name: str) -> Any:
    values = (
        tool.params_json_schema.get("properties", {}).get(field_name, {}).get("enum")
    )
    if not isinstance(values, list) or not values:
        raise UnsupportedSmokeDecision(
            f"{tool.name}.{field_name} did not expose exact legal values"
        )
    return values[0]


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
        "randomSeed": PROTOCOL_SMOKE_RANDOM_SEED,
        "maxRounds": 2,
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
    runner = ScriptedProtocolRunner()
    try:
        result = await run_game(
            game_number=1,
            attempt_dir=output,
            model=SMOKE_MODEL_ID,
            random_seed=PROTOCOL_SMOKE_RANDOM_SEED,
            game_port=args.game_port,
            max_rounds=2,
            poll_seconds=0.1,
            stall_seconds=args.stall_seconds,
            match_timeout_seconds=args.timeout_seconds,
            settings=settings,
            model_runner=runner,
        )
        invoked_tools = [item["tool"] for item in runner.invocations]
        invoked_counts = Counter(invoked_tools)
        missing_tools = {
            name: required - invoked_counts[name]
            for name, required in REQUIRED_TOOL_COUNTS.items()
            if invoked_counts[name] < required
        }
        if missing_tools:
            raise RuntimeError(
                "The real-server smoke did not reach required tool counts: "
                + ", ".join(
                    f"{name} ({count} short)"
                    for name, count in sorted(missing_tools.items())
                )
            )
        if runner.order_privacy_probe is None:
            raise RuntimeError("The real-server smoke did not verify order privacy")
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
            "toolCoverage": {
                "required": dict(sorted(REQUIRED_TOOL_COUNTS.items())),
                "invoked": dict(sorted(invoked_counts.items())),
                "sequence": runner.invocations,
            },
            "orderSubmissionRejectionProbe": runner.order_rejection_probe,
            "orderSubmissionPrivacyProbe": runner.order_privacy_probe,
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
    return resolve_evaluation_output(value, default_prefix="protocol-smoke-")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic six-player two-round protocol smoke without model calls."
        )
    )
    parser.add_argument(
        "--output", help="New artifact directory under data/evaluations."
    )
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
