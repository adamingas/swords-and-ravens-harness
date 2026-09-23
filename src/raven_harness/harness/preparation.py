"""The shared observation, prompt and cache-key preparation for every decision."""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from typing import Any
from agents import FunctionTool
from ..agent_store import AgentStore
from ..game.map_reference import observation_map_reference
from ..rulebook import ask_rules_oracle
from ..schemas import AgentRecord
from .actions import ActionSpec, available_action_specs, available_tools, describe_tools
from .interface import PreparedTurn
from .decision import build_decision_contract
from .decision_briefing import build_decision_briefing
from .card_tools import inspect_house_card
from .map_tools import check_neighbours
from .reachability_tools import reachable_areas
from .protocol_tools import _is_base_game
from .observation import HarnessContext, build_observation
from .memory import PersistentGameMemory, recall_game_state, remember_strategy
from .prompts import build_instructions

MEMORY_TOOLS = [recall_game_state, remember_strategy]


@dataclass
class DecisionPreparation:
    store: AgentStore
    oracle_available: bool = False

    def _memory(self, record: AgentRecord) -> PersistentGameMemory:
        return PersistentGameMemory(self.store, record.id)

    def preview_observation(
        self, record: AgentRecord, context: HarnessContext
    ) -> dict[str, Any]:
        observation = build_observation(context)
        action_specs = available_action_specs(context)
        contract = build_decision_contract(
            context, available_tools(context, action_specs=action_specs)
        )
        if contract:
            observation["decisionBriefing"] = build_decision_briefing(
                context, contract, self.preview_tools(context)
            )
        return self._enrich_observation(record, observation, action_specs)

    def _enrich_observation(
        self,
        record: AgentRecord,
        observation: dict[str, Any],
        action_specs: list[ActionSpec],
    ) -> dict[str, Any]:
        observation["strategicOverview"] = _strategic_overview(observation)
        observation["strategicMemory"] = self._memory(record).get_notes()
        observation["historyIndex"] = self._memory(record).list_history(12)
        planning = next(
            (action for action in action_specs if action.name == "submit_orders"),
            None,
        )
        if planning is not None:
            observation["planningConstraints"] = {
                "eligibleRegionCount": len(planning.legal_values["region_ids"]),
                "eligibleRegionIds": planning.legal_values["region_ids"],
                "requiredAssignmentCount": planning.legal_values["assignment_count"],
                "maxStarredOrders": planning.legal_values["max_starred"],
                "restrictedOrderCategories": [
                    order.value
                    for order in planning.legal_values["restricted_order_categories"]
                ],
                "restrictedStarredOrderCategories": [
                    order.value
                    for order in planning.legal_values["restricted_starred_categories"]
                ],
                "requiredRestrictedOrders": planning.legal_values[
                    "required_restricted"
                ],
            }
        return observation

    def prepare_turn(
        self,
        record: AgentRecord,
        context: HarnessContext,
        previous_error: str | None,
    ) -> PreparedTurn:
        action_specs = available_action_specs(context)
        game_tools = available_tools(context, action_specs=action_specs)
        decision = build_decision_contract(context, game_tools)
        tools = self.preview_tools(context)
        base_observation = build_observation(context)
        history_id = self.store.record_state(record.id, base_observation)
        observation = self._enrich_observation(record, base_observation, action_specs)
        if decision:
            observation["decisionBriefing"] = build_decision_briefing(
                context, decision, tools
            )
        if previous_error:
            observation["previousAttemptError"] = previous_error
            observation["retryInstruction"] = (
                "Your previous action was not accepted. Read previousAttemptError and "
                "the current decision again. Use exploration tools as needed, then return "
                "a corrected structured action."
            )
        instructions = build_instructions(
            record.system_prompt, map_reference=observation_map_reference(observation)
        )
        cache_material = json.dumps(
            {
                "model": record.model,
                "instructions": instructions,
                "tools": describe_tools(tools),
                "actionOutputSchema": decision.output_schema.json_schema()
                if decision
                else None,
            },
            sort_keys=True,
        )
        cache_key = "raven-" + hashlib.sha256(cache_material.encode()).hexdigest()[:32]
        return PreparedTurn(
            observation=observation,
            tools=tools,
            instructions=instructions,
            prompt_cache_key=cache_key,
            history_id=history_id,
            decision=decision,
        )

    def preview_tools(self, context: HarnessContext) -> list[FunctionTool]:
        exploration_tools = (
            [check_neighbours, inspect_house_card] if context.game is not None else []
        )
        if context.game is not None and _is_base_game(context.snapshot):
            exploration_tools.insert(1, reachable_areas)
        return self._tools_for_game(exploration_tools)

    def _tools_for_game(self, game_tools: list[FunctionTool]) -> list[FunctionTool]:
        tools = [
            *game_tools,
            *MEMORY_TOOLS,
        ]
        if self.oracle_available:
            tools.append(ask_rules_oracle)
        return tools


def _strategic_overview(observation: dict[str, Any]) -> dict[str, Any]:
    """Derive a stable score/resource synopsis the engine does not serialize directly."""

    regions = {
        item["id"]: item for item in observation_map_reference(observation)["regions"]
    }
    houses = {item["id"]: item for item in observation.get("houses", [])}
    stats = {
        house_id: {
            "houseId": house_id,
            "castles": house.get("controlledCastleAreas"),
            "strongholds": 0,
            "landAreas": house.get("controlledLandAreas"),
            "supplyIconsControlled": house.get("controlledSupplyIcons"),
            "crownIconsControlled": 0,
            "powerTokens": house.get("powerTokens"),
            "supplyTrack": house.get("supply"),
            "victoryPoints": house.get("currentVictoryPoints"),
            "controlledRegions": house.get("controlledRegions", []),
        }
        for house_id, house in houses.items()
    }
    for board_region in observation.get("board", []):
        reference = regions.get(board_region.get("id"), {})
        units = board_region.get("units") or []
        controller = (
            units[0].get("allegiance")
            if units
            else board_region.get("controlPowerToken")
            or reference.get("homeController")
        )
        if controller not in stats or reference.get("type") != "land":
            continue
        castle_level = int(reference.get("castleLevel", 0))
        if castle_level > 1:
            stats[controller]["strongholds"] += 1
        stats[controller]["crownIconsControlled"] += int(reference.get("crownIcons", 0))
    game = observation.get("game", {})
    target = game.get("victoryPointsToWin") or 7
    max_rounds = game.get("maxRounds") or 10
    return {
        "round": game.get("round"),
        "victoryPoints": {
            house_id: (
                value["victoryPoints"]
                if value["victoryPoints"] is not None
                else value["castles"]
            )
            for house_id, value in stats.items()
        },
        "housePositions": list(stats.values()),
        "victoryCondition": (
            f"Reach {target} victory points, or lead after round {max_rounds}."
        ),
    }
