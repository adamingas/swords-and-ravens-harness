from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from itertools import combinations
from typing import Annotated, Any, Literal

from agents import FunctionTool, RunContextWrapper, function_tool
from pydantic import BaseModel, ConfigDict, Field

from .actions import HarnessRunContext, gameplay_tool_error
from .legal import (
    legal_consolidate_power_options,
    legal_march_options,
    legal_mustering_options,
    legal_raven_replacements,
    legal_raid_options,
    neutral_force_attack_is_legal,
    possible_neutral_force_support,
    supply_safe_musterings,
    validate_musterings,
)
from .tool_schema import inline_local_definitions


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UnitMove(ToolInput):
    destination_region_id: str
    unit_ids: list[int] = Field(min_length=1)


class RegionUnits(ToolInput):
    region_id: str
    unit_ids: list[int] = Field(min_length=1)


class Recruitment(ToolInput):
    unit_type: str = Field(
        description="Unit type to create, such as footman, knight, ship, or siege-engine."
    )
    region_id: str = Field(
        description="Region where the resulting unit will be placed."
    )
    upgrade_from_footman: bool = Field(
        description=(
            "Whether to upgrade an existing Footman instead of creating a new unit. "
            "Only knight and siege-engine upgrades are valid."
        ),
    )


class MusterGroup(ToolInput):
    mustering_region_id: str
    recruitments: list[Recruitment] = Field(min_length=1)


@function_tool(failure_error_function=gameplay_tool_error)
async def resolve_raid(
    ctx: RunContextWrapper[HarnessRunContext],
    order_region_id: str,
    target_region_id: str | None,
) -> str:
    """Resolve a raid order, or decline it by using a null target.

    Args:
        order_region_id: Region containing your raid order.
        target_region_id: Adjacent enemy order to raid, or null to remove your raid without a target.
    """
    context = ctx.context.current_game_context()
    option = next(
        (
            item
            for item in legal_raid_options(context)
            if item["regionId"] == order_region_id
        ),
        None,
    )
    if option is None:
        raise ValueError("order_region_id must identify one of your Raid orders")
    legal_targets = {
        item["regionId"] for item in option.get("raidableTargets", [])
    }
    if target_region_id is not None and target_region_id not in legal_targets:
        raise ValueError(
            "target_region_id is not raidable from the selected order region"
        )
    return await _send(
        ctx,
        "resolve_raid",
        {"order_region_id": order_region_id, "target_region_id": target_region_id},
        {
            "type": "resolve-raid",
            "orderRegionId": order_region_id,
            "targetRegionId": target_region_id,
        },
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def resolve_march(
    ctx: RunContextWrapper[HarnessRunContext],
    starting_region_id: str,
    moves: list[UnitMove],
    leave_power_token: bool,
) -> str:
    """Resolve one march order by moving specified units to destination regions.

    Args:
        starting_region_id: Region containing the march order and moving units.
        moves: Destination groups and exact unit IDs to move to each destination.
        leave_power_token: Whether to leave a control token after vacating the starting land region.
            The harness changes this to false when the current move cannot legally leave one.
    """
    context = ctx.context.current_game_context()
    option = next(
        (
            item
            for item in legal_march_options(context)
            if item["regionId"] == starting_region_id
        ),
        None,
    )
    if option is None:
        raise ValueError("starting_region_id must identify one of your March orders")
    available_units = set(option.get("unitIds", []))
    moved_units = [unit_id for move in moves for unit_id in move.unit_ids]
    if len(moved_units) != len(set(moved_units)):
        raise ValueError("each unit_id may be moved at most once")
    invalid_units = sorted(set(moved_units) - available_units)
    if invalid_units:
        raise ValueError(f"unit_ids are not movable from this region: {invalid_units}")
    destinations = [move.destination_region_id for move in moves]
    if len(destinations) != len(set(destinations)):
        raise ValueError("each destination_region_id may appear at most once")
    legal_destinations = {
        item["regionId"]: item for item in option.get("reachableRegions", [])
    }
    invalid_destinations = sorted(set(destinations) - set(legal_destinations))
    if invalid_destinations:
        raise ValueError(
            f"destination_region_id is not reachable: {invalid_destinations}"
        )
    if sum(
        bool(legal_destinations[destination].get("triggersCombat"))
        for destination in destinations
    ) > 1:
        raise ValueError("at most one destination may trigger combat")
    prior_non_combat_moves: list[tuple[str, list[int]]] = []
    for move in moves:
        destination = legal_destinations[move.destination_region_id]
        if destination.get("neutralForce") and not neutral_force_attack_is_legal(
            context,
            starting_region_id,
            move.destination_region_id,
            move.unit_ids,
            prior_non_combat_moves,
        ):
            required = destination["neutralForce"]["requiredStrength"]
            raise ValueError(
                "the selected units and accepted support do not meet the neutral "
                f"force strength of {required}"
            )
        if not destination.get("triggersCombat"):
            prior_non_combat_moves.append(
                (move.destination_region_id, move.unit_ids)
            )
    requested_leave_power_token = leave_power_token
    leave_power_token = bool(
        leave_power_token
        and option.get("canLeavePowerToken")
        and set(moved_units) == available_units
    )
    arguments = {
        "starting_region_id": starting_region_id,
        "moves": [move.model_dump() for move in moves],
        "leave_power_token": leave_power_token,
        "omitted_illegal_power_token": (
            requested_leave_power_token and not leave_power_token
        ),
    }
    return await _send(
        ctx,
        "resolve_march",
        arguments,
        {
            "type": "resolve-march-order",
            "startingRegionId": starting_region_id,
            "moves": [[move.destination_region_id, move.unit_ids] for move in moves],
            "leavePowerToken": leave_power_token,
        },
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def select_units(
    ctx: RunContextWrapper[HarnessRunContext], selections: list[RegionUnits]
) -> str:
    """Select units grouped by their current region for retreat, removal, or another prompted effect.

    Args:
        selections: Regions and exact unit IDs selected in each one.
    """
    context = ctx.context.current_game_context()
    leaf = context.leaf or {}
    if leaf.get("type") == "select-units":
        possible_units = {int(unit_id) for unit_id in leaf.get("possibleUnits", [])}
        selected_units = [
            unit_id for selection in selections for unit_id in selection.unit_ids
        ]
        if len(selected_units) != len(set(selected_units)):
            raise ValueError("each unit_id may be selected at most once")
        if not set(selected_units).issubset(possible_units):
            raise ValueError("unit_ids must come from pendingDecision.possibleUnits")
        expected = min(int(leaf.get("count", 0)), len(possible_units))
        if leaf.get("canBeSkipped"):
            if len(selected_units) > expected:
                raise ValueError(f"select at most {expected} units")
        elif len(selected_units) != expected:
            raise ValueError(f"select exactly {expected} units")
        unit_regions = _unit_regions(context.game or {})
        if any(
            unit_regions.get(unit_id) != selection.region_id
            for selection in selections
            for unit_id in selection.unit_ids
        ):
            raise ValueError("each selected unit must be grouped under its current region")
        if leaf.get("selectedUnitsMustBeOfSameRegion") and len(selections) > 1:
            raise ValueError("all selected units must come from one region")
    arguments = {"selections": [selection.model_dump() for selection in selections]}
    return await _send(
        ctx,
        "select_units",
        arguments,
        {
            "type": "select-units",
            "units": [
                [selection.region_id, selection.unit_ids] for selection in selections
            ],
        },
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def auto_reconcile_armies(
    ctx: RunContextWrapper[HarnessRunContext],
) -> str:
    """Compute and submit a minimal legal set of unit removals for the current supply limit."""

    context = ctx.context.current_game_context()
    target_house = (context.leaf or {}).get("house")
    if not target_house or target_house != context.house_id or context.game is None:
        raise RuntimeError(
            "This player is not responsible for the current reconciliation"
        )
    removals = _minimal_reconciliation_removals(context.game, target_house)
    arguments = {
        "removals": [
            {"region_id": region_id, "unit_ids": unit_ids}
            for region_id, unit_ids in removals
        ]
    }
    return await _send(
        ctx,
        "auto_reconcile_armies",
        arguments,
        {
            "type": "reconcile-armies",
            "unitsToRemove": removals,
        },
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def muster_units(
    ctx: RunContextWrapper[HarnessRunContext],
    musters: Annotated[list[MusterGroup], Field(min_length=1)],
) -> str:
    """Resolve mustering by recruiting or upgrading units from one or more castles.

    Args:
        musters: Mustering castles and recruitments in priority order. The harness
            omits later new units that would exceed Supply. It keeps legal upgrades.
            The applied plan can be empty when no requested new unit is Supply-safe.
    """
    context = ctx.context.current_game_context()
    validate_musterings(context, musters, check_supply=False)
    applied_musters = supply_safe_musterings(context, musters)
    if applied_musters:
        validate_musterings(context, applied_musters)
    requested_count = sum(len(muster.recruitments) for muster in musters)
    applied_count = sum(len(muster.recruitments) for muster in applied_musters)
    arguments = {
        "musters": [muster.model_dump() for muster in applied_musters],
        "omitted_supply_unsafe_recruitments": requested_count - applied_count,
    }
    return await _send(
        ctx,
        "muster_units",
        arguments,
        {
            "type": "muster",
            "units": [
                [
                    muster.mustering_region_id,
                    [
                        {
                            "from": source_unit_id,
                            "to": recruitment.unit_type,
                            "region": recruitment.region_id,
                        }
                        for recruitment, source_unit_id in zip(
                            muster.recruitments,
                            source_unit_ids,
                            strict=True,
                        )
                    ],
                ]
                for muster, source_unit_ids in zip(
                    applied_musters,
                    _canonical_mustering_source_ids(context, applied_musters),
                    strict=True,
                )
            ],
        },
    )


def _canonical_mustering_source_ids(
    context: Any, musters: list[MusterGroup]
) -> list[list[int | None]]:
    """Choose upgrade pieces exactly as the upstream game client does.

    Swords & Ravens treats same-type units as interchangeable and only accepts
    the first unused matching unit in the region's internal order. Keeping this
    engine detail out of the model-facing tool avoids advertising choices the
    server will silently reject.
    """

    regions = {
        str(region["id"]): region
        for region in (context.game or {}).get("world", {}).get("regions", [])
    }
    available_by_region = {
        region_id: [
            int(unit["id"])
            for unit in region.get("units", [])
            if unit.get("allegiance") == context.house_id
            and unit.get("type") == "footman"
        ]
        for region_id, region in regions.items()
    }
    used_by_region: dict[str, int] = {}
    result: list[list[int | None]] = []
    for muster in musters:
        group: list[int | None] = []
        for recruitment in muster.recruitments:
            if not recruitment.upgrade_from_footman:
                group.append(None)
                continue
            region_id = recruitment.region_id
            used = used_by_region.get(region_id, 0)
            candidates = available_by_region.get(region_id, [])
            if used >= len(candidates):
                raise ValueError(
                    f"no unused Footman is available to upgrade in {region_id}"
                )
            group.append(candidates[used])
            used_by_region[region_id] = used + 1
        result.append(group)
    return result


@function_tool(failure_error_function=gameplay_tool_error)
async def skip_mustering(ctx: RunContextWrapper[HarnessRunContext]) -> str:
    """Finish the current mustering decision without recruiting any units."""
    return await _send(ctx, "skip_mustering", {}, {"type": "muster", "units": []})


@function_tool(failure_error_function=gameplay_tool_error)
async def resolve_track_ties(
    ctx: RunContextWrapper[HarnessRunContext], ranked_house_ids: list[str]
) -> str:
    """Resolve influence-track ties with one highest-to-lowest house ranking.

    Args:
        ranked_house_ids: Every house involved in a tie, ordered from highest to
            lowest. The harness applies this ranking within each tied bid group.
    """
    leaf = ctx.context.current_game_context().leaf or {}
    tied_groups = [
        list(houses)
        for _bid, houses in leaf.get("bidResults", [])
        if len(houses) > 1
    ]
    expected_house_ids = {house for group in tied_groups for house in group}
    if (
        len(ranked_house_ids) != len(set(ranked_house_ids))
        or set(ranked_house_ids) != expected_house_ids
    ):
        raise ValueError(
            "ranked_house_ids must contain every house involved in a tie exactly once"
        )
    rank = {house: index for index, house in enumerate(ranked_house_ids)}
    resolved_ties = [sorted(group, key=rank.__getitem__) for group in tied_groups]
    return await _send(
        ctx,
        "resolve_track_ties",
        {"ranked_house_ids": ranked_house_ids},
        {"type": "resolve-ties", "resolvedTies": resolved_ties},
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def use_valyrian_steel_blade(
    ctx: RunContextWrapper[HarnessRunContext], use: bool
) -> str:
    """Choose whether to use the Valyrian Steel Blade in the current combat.

    Args:
        use: True to use the blade now, false to decline.
    """
    return await _send(
        ctx,
        "use_valyrian_steel_blade",
        {"use": use},
        {"type": "use-valyrian-steel-blade", "use": use},
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def replace_raven_order(
    ctx: RunContextWrapper[HarnessRunContext],
    region_id: str,
    order_id: Annotated[int, Field(ge=1, le=15)],
) -> str:
    """Use the Messenger Raven to replace one revealed order.

    Args:
        region_id: Region whose order will be replaced.
        order_id: Unused physical order token ID to place there.
    """
    context = ctx.context.current_game_context()
    option = next(
        (
            item
            for item in legal_raven_replacements(context)
            if item["regionId"] == region_id
        ),
        None,
    )
    if option is None or order_id not in option["availableOrderIds"]:
        raise ValueError("region_id and order_id are not a legal Raven replacement")
    return await _send(
        ctx,
        "replace_raven_order",
        {"region_id": region_id, "order_id": order_id},
        {"type": "replace-order", "regionId": region_id, "orderId": order_id},
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def skip_raven_order_replacement(
    ctx: RunContextWrapper[HarnessRunContext],
) -> str:
    """Decline to replace an order with the Messenger Raven."""
    return await _send(
        ctx,
        "skip_raven_order_replacement",
        {},
        {"type": "skip-replace-order"},
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def inspect_top_wildling_card(ctx: RunContextWrapper[HarnessRunContext]) -> str:
    """Use the Messenger Raven to inspect the top Wildling card."""
    return await _send(
        ctx,
        "inspect_top_wildling_card",
        {},
        {"type": "choose-see-top-wildling-card"},
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def place_inspected_wildling_card(
    ctx: RunContextWrapper[HarnessRunContext],
    destination: Literal["top", "bottom"],
) -> str:
    """Return an inspected Wildling card to the top or put it at the bottom.

    Args:
        destination: Place the inspected card at the top or bottom of the deck.
    """
    action = 0 if destination == "top" else 1
    return await _send(
        ctx,
        "place_inspected_wildling_card",
        {"destination": destination},
        {"type": "choose-top-wildling-card-action", "action": action},
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def select_region(
    ctx: RunContextWrapper[HarnessRunContext], region_id: str
) -> str:
    """Select one board region for the current prompted effect.

    Args:
        region_id: Exact ID of the selected region.
    """
    leaf = ctx.context.current_game_context().leaf or {}
    regions = leaf.get("regions")
    if isinstance(regions, list) and region_id not in regions:
        raise ValueError("region_id must be one of pendingDecision.regions")
    return await _send(
        ctx,
        "select_region",
        {"region_id": region_id},
        {"type": "select-region", "region": region_id},
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def select_westeros_card(
    ctx: RunContextWrapper[HarnessRunContext], deck_id: int, card_id: int
) -> str:
    """Select a Westeros card when the current state asks you to choose one.

    Args:
        deck_id: Westeros deck identifier shown by the state.
        card_id: Card identifier shown by the state.
    """
    return await _send(
        ctx,
        "select_westeros_card",
        {"deck_id": deck_id, "card_id": card_id},
        {"type": "select-westeros-card", "deckId": deck_id, "westerosCardId": card_id},
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def resolve_consolidate_power(
    ctx: RunContextWrapper[HarnessRunContext],
    region_id: str,
    choice: Literal["gain_power_tokens", "muster_units"],
) -> str:
    """Resolve a base-game Consolidate Power order using one available option.

    Args:
        region_id: Region containing the order.
        choice: Available resolution shown in the current state.
    """
    context = ctx.context.current_game_context()
    option = next(
        (
            item
            for item in legal_consolidate_power_options(context)
            if item["regionId"] == region_id
        ),
        None,
    )
    if option is None:
        raise ValueError(
            "region_id must identify one of your Consolidate Power orders"
        )
    if choice not in option["choices"]:
        raise ValueError(
            f"choice must be one of {', '.join(option['choices'])} for this order"
        )
    message = {"type": "resolve-consolidate-power-choice", "region": region_id}
    if choice == "gain_power_tokens":
        message["gainPowerTokens"] = True
    else:
        message["musterUnits"] = True
    return await _send(
        ctx,
        "resolve_consolidate_power",
        {"region_id": region_id, "choice": choice},
        message,
    )


@function_tool(failure_error_function=gameplay_tool_error)
async def call_for_support_against_neutral_force(
    ctx: RunContextWrapper[HarnessRunContext],
) -> str:
    """Call for support when marching against a neutral force."""
    context = ctx.context.current_game_context()
    if not possible_neutral_force_support(context):
        raise ValueError("no foreign house can support a reachable neutral-force target")
    return await _send(
        ctx,
        "call_for_support_against_neutral_force",
        {},
        {"type": "call-for-support-against-neutral-force"},
    )


GAMEPLAY_TOOLS: list[FunctionTool] = [
    resolve_raid,
    resolve_march,
    select_units,
    auto_reconcile_armies,
    muster_units,
    skip_mustering,
    resolve_track_ties,
    use_valyrian_steel_blade,
    replace_raven_order,
    skip_raven_order_replacement,
    inspect_top_wildling_card,
    place_inspected_wildling_card,
    select_region,
    select_westeros_card,
    resolve_consolidate_power,
    call_for_support_against_neutral_force,
]

_TOOLS_BY_NAME = {tool.name: tool for tool in GAMEPLAY_TOOLS}
_TOOLS_BY_STATE: dict[str, set[str]] = {
    "bidding": set(),
    "simple-choice": set(),
    "select-house-card": set(),
    "choose-house-card": set(),
    "select-orders": set(),
    "support": set(),
    "place-orders": set(),
    "resolve-raid-order": {"resolve_raid"},
    "resolve-single-raid": {"resolve_raid"},
    "resolve-march-order": {
        "resolve_march",
    },
    "resolve-single-march": {
        "call_for_support_against_neutral_force",
        "resolve_march",
    },
    "select-units": {"select_units"},
    "resolve-retreat": {"select_units", "select_region"},
    "select-region": {"select_region"},
    "reconcile-armies": {"auto_reconcile_armies"},
    "player-reconcile-armies": {"auto_reconcile_armies"},
    "mustering": {"muster_units", "skip_mustering"},
    "player-mustering": {"muster_units", "skip_mustering"},
    "resolve-ties": {"resolve_track_ties"},
    "use-valyrian-steel-blade": {"use_valyrian_steel_blade"},
    "replace-order": {
        "replace_raven_order",
        "skip_raven_order_replacement",
        "inspect_top_wildling_card",
    },
    "use-raven": {
        "replace_raven_order",
        "skip_raven_order_replacement",
        "inspect_top_wildling_card",
    },
    "see-top-wildling-card": {"place_inspected_wildling_card"},
    "select-westeros-card": {"select_westeros_card"},
    "resolve-consolidate-power": {"resolve_consolidate_power"},
    "resolve-single-consolidate-power": {"resolve_consolidate_power"},
}


def gameplay_tools_for_state(
    state_types: list[str], *, has_specific_tools: bool
) -> list[FunctionTool]:
    """Return tools for the deepest recognized state and no tools for unknown states."""

    if has_specific_tools or not state_types:
        return []
    names = _TOOLS_BY_STATE.get(state_types[-1], set())
    return [_TOOLS_BY_NAME[name] for name in sorted(names)]


def gameplay_tools_for_context(
    context: Any, *, has_specific_tools: bool
) -> list[FunctionTool]:
    """Return protocol tools with model-facing schemas narrowed to this snapshot."""

    if not _is_base_game(context.snapshot):
        return []
    state_types = [state["type"] for state in context.path if state.get("type")]
    tools = gameplay_tools_for_state(
        state_types, has_specific_tools=has_specific_tools
    )
    if not possible_neutral_force_support(context):
        tools = [
            tool
            for tool in tools
            if tool.name != "call_for_support_against_neutral_force"
        ]
    return [_narrow_base_game_tool(tool, context) for tool in tools]


def _narrow_base_game_tool(tool: FunctionTool, context: Any) -> FunctionTool:
    schema = deepcopy(tool.params_json_schema)
    properties = schema.get("properties", {})
    if tool.name == "resolve_raid":
        options = legal_raid_options(context)
        properties["order_region_id"]["enum"] = [
            item["regionId"] for item in options
        ]
        targets = sorted(
            {
                target["regionId"]
                for item in options
                for target in item.get("raidableTargets", [])
            }
        )
        properties["target_region_id"]["anyOf"][0]["enum"] = targets
    elif tool.name == "resolve_march":
        options = legal_march_options(context)
        properties["starting_region_id"]["enum"] = [
            item["regionId"] for item in options
        ]
        destinations = sorted(
            {
                target["regionId"]
                for item in options
                for target in item.get("reachableRegions", [])
            }
        )
        unit_ids = sorted(
            {unit_id for item in options for unit_id in item.get("unitIds", [])}
        )
        move_properties = schema["$defs"]["UnitMove"]["properties"]
        move_properties["destination_region_id"]["enum"] = destinations
        move_properties["unit_ids"]["items"]["enum"] = unit_ids
        if options and not any(option.get("canLeavePowerToken") for option in options):
            properties["leave_power_token"]["const"] = False
        properties["leave_power_token"]["description"] += (
            " True also requires moving every listed unit from the selected source."
        )
    elif tool.name == "resolve_consolidate_power":
        options = legal_consolidate_power_options(context)
        properties["region_id"]["enum"] = [item["regionId"] for item in options]
        properties["choice"]["enum"] = sorted(
            {choice for item in options for choice in item["choices"]}
        )
    elif tool.name == "muster_units":
        guidance = legal_mustering_options(context)
        origins = guidance["origins"]
        muster_properties = schema["$defs"]["MusterGroup"]["properties"]
        muster_properties["mustering_region_id"]["enum"] = [
            item["regionId"] for item in origins
        ]
        properties["musters"]["maxItems"] = guidance["maxOriginGroups"]
        recruit_properties = schema["$defs"]["Recruitment"]["properties"]
        recruit_properties["region_id"]["enum"] = sorted(
            {
                destination["regionId"]
                for origin in origins
                for destination in origin["destinations"]
            }
        )
        recruit_properties["unit_type"]["enum"] = sorted(
            {
                unit_type
                for origin in origins
                for destination in origin["destinations"]
                for unit_type in destination["newUnitTypes"]
            }
        )
    elif tool.name == "select_units":
        leaf = context.leaf or {}
        possible_units = [int(unit_id) for unit_id in leaf.get("possibleUnits", [])]
        expected = min(int(leaf.get("count", 0)), len(possible_units))
        unit_regions = _unit_regions(context.game or {})
        region_ids = sorted(
            {
                unit_regions[unit_id]
                for unit_id in possible_units
                if unit_id in unit_regions
            }
        )
        selections = properties["selections"]
        selections["minItems"] = 0 if leaf.get("canBeSkipped") else int(expected > 0)
        selections["maxItems"] = 1 if leaf.get(
            "selectedUnitsMustBeOfSameRegion"
        ) else expected
        region_units = schema["$defs"]["RegionUnits"]["properties"]
        region_units["region_id"]["enum"] = region_ids
        region_units["unit_ids"]["items"]["enum"] = possible_units
    elif tool.name == "select_region":
        regions = (context.leaf or {}).get("regions")
        if isinstance(regions, list):
            properties["region_id"]["enum"] = regions
    elif tool.name == "resolve_track_ties":
        groups = [
            list(houses)
            for _bid, houses in (context.leaf or {}).get("bidResults", [])
            if len(houses) > 1
        ]
        house_ids = [house for group in groups for house in group]
        field = properties["ranked_house_ids"]
        field["minItems"] = len(house_ids)
        field["maxItems"] = len(house_ids)
        field["description"] = (
            "Return one flat highest-to-lowest list containing exactly these house "
            f"IDs: {house_ids}. Do not use nested arrays. The server's tied groups "
            f"are {groups}; the harness applies the flat ranking within each group."
        )
        field["items"]["enum"] = sorted(house_ids)
    elif tool.name == "replace_raven_order":
        options = legal_raven_replacements(context)
        properties["region_id"]["enum"] = [item["regionId"] for item in options]
        properties["order_id"]["enum"] = sorted(
            {
                order_id
                for item in options
                for order_id in item["availableOrderIds"]
            }
        )
    return replace(tool, params_json_schema=inline_local_definitions(schema))


def _is_base_game(snapshot: dict[str, Any]) -> bool:
    settings = snapshot.get("gameSettings")
    if not isinstance(settings, dict):
        return False
    return (
        settings.get("setupId") == "base-game"
        and settings.get("playerCount") in {3, 6}
        # The upstream serializer omits false boolean settings.
        and settings.get("vassals", False) is False
    )


def _unit_regions(game: dict[str, Any]) -> dict[int, str]:
    return {
        int(unit["id"]): str(region["id"])
        for region in game.get("world", {}).get("regions", [])
        for unit in region.get("units", [])
    }


async def _send(
    ctx: RunContextWrapper[HarnessRunContext],
    name: str,
    arguments: dict,
    message: dict,
) -> str:
    return await ctx.context.perform_protocol(name, arguments, message)


def _minimal_reconciliation_removals(
    game: dict[str, Any], house_id: str
) -> list[list[Any]]:
    """Find the smallest removal set that satisfies the upstream supply algorithm."""

    house = next(
        (
            candidate
            for candidate in game.get("houses", [])
            if candidate.get("id") == house_id
        ),
        None,
    )
    if house is None:
        raise RuntimeError(f"House {house_id!r} is missing from the game state")
    supply_level = int(house.get("supplyLevel", 0))
    restrictions = game.get("supplyRestrictions", [])
    if not 0 <= supply_level < len(restrictions):
        raise RuntimeError("Supply restrictions are missing from the game state")
    allowed_sizes = [int(size) for size in restrictions[supply_level]]

    regions: dict[str, list[dict[str, Any]]] = {}
    for region in game.get("world", {}).get("regions", []):
        units = [
            unit
            for unit in region.get("units", [])
            if unit.get("allegiance") == house_id
        ]
        if units:
            regions[str(region["id"])] = units

    def is_legal(removed: set[int]) -> bool:
        army_sizes = sorted(
            (
                sum(int(unit.get("id")) not in removed for unit in units)
                for units in regions.values()
            ),
            reverse=True,
        )
        army_sizes = [size for size in army_sizes if size > 1]
        return len(army_sizes) <= len(allowed_sizes) and all(
            size <= allowed_sizes[index] for index, size in enumerate(army_sizes)
        )

    if is_legal(set()):
        return []

    removal_priority = {"footman": 0, "ship": 1, "knight": 2, "siege-engine": 3}
    candidates = sorted(
        (
            (region_id, unit)
            for region_id, units in regions.items()
            if len(units) > 1
            for unit in units
        ),
        key=lambda item: (
            removal_priority.get(str(item[1].get("type")), 4),
            int(item[1].get("id")),
        ),
    )
    for count in range(1, len(candidates) + 1):
        for selected in combinations(candidates, count):
            removed = {int(unit["id"]) for _, unit in selected}
            if not is_legal(removed):
                continue
            grouped: dict[str, list[int]] = {}
            for region_id, unit in selected:
                grouped.setdefault(region_id, []).append(int(unit["id"]))
            return [[region_id, unit_ids] for region_id, unit_ids in grouped.items()]
    raise RuntimeError("Could not compute a legal supply reconciliation")
