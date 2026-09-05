from __future__ import annotations

from itertools import combinations
from typing import Annotated, Any, Literal

from agents import FunctionTool, RunContextWrapper, function_tool
from pydantic import BaseModel, ConfigDict, Field

from .actions import HarnessRunContext


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
    source_unit_id: int | None = Field(
        default=None,
        description="Existing unit to upgrade, or null when recruiting a new unit.",
    )


class MusterGroup(ToolInput):
    mustering_region_id: str
    recruitments: list[Recruitment] = Field(min_length=1)


class PowerAllocation(ToolInput):
    house_id: str
    amount: Annotated[int, Field(ge=0)]


class SellswordPlacement(ToolInput):
    region_id: str
    unit_types: list[str] = Field(min_length=1)


@function_tool
async def place_planning_order(
    ctx: RunContextWrapper[HarnessRunContext],
    region_id: str,
    order_id: Annotated[int, Field(ge=1, le=15)],
) -> str:
    """Place or replace one planning order token.

    Args:
        region_id: Region receiving the order.
        order_id: Physical order token ID from 1 through 15.
    """
    return await _send(
        ctx,
        "place_planning_order",
        {"region_id": region_id, "order_id": order_id},
        {"type": "place-order", "regionId": region_id, "orderId": order_id},
    )


@function_tool
async def remove_planning_order(
    ctx: RunContextWrapper[HarnessRunContext], region_id: str
) -> str:
    """Remove the planning order currently assigned to a region.

    Args:
        region_id: Region whose order should be removed.
    """
    return await _send(
        ctx,
        "remove_planning_order",
        {"region_id": region_id},
        {"type": "place-order", "regionId": region_id, "orderId": None},
    )


@function_tool
async def mark_ready(ctx: RunContextWrapper[HarnessRunContext]) -> str:
    """Mark your current simultaneous decision or setup as complete."""
    return await _send(ctx, "mark_ready", {}, {"type": "ready"})


@function_tool
async def mark_unready(ctx: RunContextWrapper[HarnessRunContext]) -> str:
    """Withdraw ready status so a simultaneous decision can be edited."""
    return await _send(ctx, "mark_unready", {}, {"type": "unready"})


@function_tool
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


@function_tool
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
    """
    arguments = {
        "starting_region_id": starting_region_id,
        "moves": [move.model_dump() for move in moves],
        "leave_power_token": leave_power_token,
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


@function_tool
async def choose_casualties(
    ctx: RunContextWrapper[HarnessRunContext], unit_ids: list[int]
) -> str:
    """Choose the exact unit IDs to take as combat casualties.

    Args:
        unit_ids: Unit IDs that will be destroyed.
    """
    return await _send(
        ctx,
        "choose_casualties",
        {"unit_ids": unit_ids},
        {"type": "choose-casualties", "chosenCasualties": unit_ids},
    )


@function_tool
async def select_units(
    ctx: RunContextWrapper[HarnessRunContext], selections: list[RegionUnits]
) -> str:
    """Select units grouped by their current region for retreat, removal, or another prompted effect.

    Args:
        selections: Regions and exact unit IDs selected in each one.
    """
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


@function_tool
async def reconcile_armies(
    ctx: RunContextWrapper[HarnessRunContext], removals: list[RegionUnits]
) -> str:
    """Remove units grouped by region to satisfy a supply limit.

    Args:
        removals: Regions and exact unit IDs to remove.
    """
    arguments = {"removals": [removal.model_dump() for removal in removals]}
    return await _send(
        ctx,
        "reconcile_armies",
        arguments,
        {
            "type": "reconcile-armies",
            "unitsToRemove": [
                [removal.region_id, removal.unit_ids] for removal in removals
            ],
        },
    )


@function_tool
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


@function_tool
async def muster_units(
    ctx: RunContextWrapper[HarnessRunContext], musters: list[MusterGroup]
) -> str:
    """Resolve mustering by recruiting or upgrading units from one or more castles.

    Args:
        musters: Mustering castles and the recruitments paid for at each castle.
    """
    arguments = {"musters": [muster.model_dump() for muster in musters]}
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
                            "from": recruitment.source_unit_id,
                            "to": recruitment.unit_type,
                            "region": recruitment.region_id,
                        }
                        for recruitment in muster.recruitments
                    ],
                ]
                for muster in musters
            ],
        },
    )


@function_tool
async def skip_mustering(ctx: RunContextWrapper[HarnessRunContext]) -> str:
    """Finish the current mustering decision without recruiting any units."""
    return await _send(ctx, "skip_mustering", {}, {"type": "muster", "units": []})


@function_tool
async def resolve_track_ties(
    ctx: RunContextWrapper[HarnessRunContext], ranked_tie_groups: list[list[str]]
) -> str:
    """Resolve influence-track ties by ordering each tied group from highest to lowest.

    Args:
        ranked_tie_groups: One ordered list of house IDs for each tie group shown in the state.
    """
    return await _send(
        ctx,
        "resolve_track_ties",
        {"ranked_tie_groups": ranked_tie_groups},
        {"type": "resolve-ties", "resolvedTies": ranked_tie_groups},
    )


@function_tool
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


@function_tool
async def refuse_support(
    ctx: RunContextWrapper[HarnessRunContext], from_house_id: str | None
) -> str:
    """Refuse granted support, either from one house or from all supporters.

    Args:
        from_house_id: Supporting house to refuse, or null to refuse all support.
    """
    message = {"type": "refuse-support"}
    if from_house_id is not None:
        message["from"] = from_house_id
    return await _send(
        ctx,
        "refuse_support",
        {"from_house_id": from_house_id},
        message,
    )


@function_tool
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
    return await _send(
        ctx,
        "replace_raven_order",
        {"region_id": region_id, "order_id": order_id},
        {"type": "replace-order", "regionId": region_id, "orderId": order_id},
    )


@function_tool
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


@function_tool
async def inspect_top_wildling_card(ctx: RunContextWrapper[HarnessRunContext]) -> str:
    """Use the Messenger Raven to inspect the top Wildling card."""
    return await _send(
        ctx,
        "inspect_top_wildling_card",
        {},
        {"type": "choose-see-top-wildling-card"},
    )


@function_tool
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


@function_tool
async def select_region(
    ctx: RunContextWrapper[HarnessRunContext], region_id: str
) -> str:
    """Select one board region for the current prompted effect.

    Args:
        region_id: Exact ID of the selected region.
    """
    return await _send(
        ctx,
        "select_region",
        {"region_id": region_id},
        {"type": "select-region", "region": region_id},
    )


@function_tool
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


@function_tool
async def claim_vassals(
    ctx: RunContextWrapper[HarnessRunContext], house_ids: list[str]
) -> str:
    """Claim the listed vassal houses after an influence-track resolution.

    Args:
        house_ids: Exact IDs of all vassal houses being claimed.
    """
    return await _send(
        ctx,
        "claim_vassals",
        {"house_ids": house_ids},
        {"type": "claim-vassal", "houses": house_ids},
    )


@function_tool
async def gift_power_tokens(
    ctx: RunContextWrapper[HarnessRunContext],
    to_house_id: str,
    amount: Annotated[int, Field(ge=0)],
) -> str:
    """Gift power tokens to another house when prompted by an effect.

    Args:
        to_house_id: House receiving the tokens.
        amount: Number of tokens to give.
    """
    return await _send(
        ctx,
        "gift_power_tokens",
        {"to_house_id": to_house_id, "amount": amount},
        {"type": "gift-power-tokens", "toHouse": to_house_id, "powerTokens": amount},
    )


@function_tool
async def distribute_power_tokens(
    ctx: RunContextWrapper[HarnessRunContext], allocations: list[PowerAllocation]
) -> str:
    """Distribute power tokens among houses for the current effect.

    Args:
        allocations: House IDs and token amounts assigned to them.
    """
    arguments = {"allocations": [allocation.model_dump() for allocation in allocations]}
    return await _send(
        ctx,
        "distribute_power_tokens",
        arguments,
        {
            "type": "distribute-power-tokens",
            "powerTokensForHouses": [
                [allocation.house_id, allocation.amount] for allocation in allocations
            ],
        },
    )


@function_tool
async def drop_power_tokens(ctx: RunContextWrapper[HarnessRunContext]) -> str:
    """Drop the power tokens required by the current card or effect."""
    return await _send(ctx, "drop_power_tokens", {}, {"type": "drop-power-tokens"})


@function_tool
async def move_loyalty_token(
    ctx: RunContextWrapper[HarnessRunContext],
    from_region_id: str,
    to_region_id: str,
) -> str:
    """Move a loyalty token between regions for the current effect.

    Args:
        from_region_id: Region currently containing the token.
        to_region_id: Legal destination region.
    """
    return await _send(
        ctx,
        "move_loyalty_token",
        {"from_region_id": from_region_id, "to_region_id": to_region_id},
        {"type": "move-loyalty-token", "from": from_region_id, "to": to_region_id},
    )


@function_tool
async def resolve_consolidate_power(
    ctx: RunContextWrapper[HarnessRunContext],
    region_id: str,
    choice: Literal[
        "gain_power_tokens", "muster_units", "purchase_loan", "ignore_and_remove_order"
    ],
    loan_id: int | None,
) -> str:
    """Resolve a starred Consolidate Power order using one available option.

    Args:
        region_id: Region containing the order.
        choice: Available resolution shown in the current state.
        loan_id: Loan-card ID for purchase_loan, otherwise null.
    """
    if choice == "purchase_loan" and loan_id is None:
        raise ValueError("loan_id is required when choice is purchase_loan")
    message = {"type": "resolve-consolidate-power-choice", "region": region_id}
    if choice == "gain_power_tokens":
        message["gainPowerTokens"] = True
    elif choice == "muster_units":
        message["musterUnits"] = True
    elif choice == "purchase_loan":
        message["purchaseLoan"] = loan_id
    else:
        message["ignoreAndRemoveOrder"] = True
    return await _send(
        ctx,
        "resolve_consolidate_power",
        {"region_id": region_id, "choice": choice, "loan_id": loan_id},
        message,
    )


@function_tool
async def place_sellswords(
    ctx: RunContextWrapper[HarnessRunContext], placements: list[SellswordPlacement]
) -> str:
    """Place purchased sellsword unit types into regions.

    Args:
        placements: Region IDs and unit-type names placed in each region.
    """
    arguments = {"placements": [placement.model_dump() for placement in placements]}
    return await _send(
        ctx,
        "place_sellswords",
        arguments,
        {
            "type": "place-sellswords",
            "units": [
                [placement.region_id, placement.unit_types] for placement in placements
            ],
        },
    )


@function_tool
async def resolve_spymaster(
    ctx: RunContextWrapper[HarnessRunContext],
    top_card_ids: list[int],
    bottom_card_ids: list[int],
) -> str:
    """Reorder inspected Westeros cards between the top and bottom of the deck.

    Args:
        top_card_ids: Card IDs in the desired top-of-deck order.
        bottom_card_ids: Card IDs in the desired bottom-of-deck order.
    """
    return await _send(
        ctx,
        "resolve_spymaster",
        {"top_card_ids": top_card_ids, "bottom_card_ids": bottom_card_ids},
        {
            "type": "resolve-spymaster",
            "westerosCardIdsForTopOfDeck": top_card_ids,
            "westerosCardIdsForBottomOfDeck": bottom_card_ids,
        },
    )


@function_tool
async def select_objectives(
    ctx: RunContextWrapper[HarnessRunContext], objective_ids: list[str]
) -> str:
    """Select secret objectives from the currently offered objective IDs.

    Args:
        objective_ids: Exact IDs of all selected objectives.
    """
    return await _send(
        ctx,
        "select_objectives",
        {"objective_ids": objective_ids},
        {"type": "select-objectives", "objectives": objective_ids},
    )


@function_tool
async def score_objective(
    ctx: RunContextWrapper[HarnessRunContext], objective_id: str | None
) -> str:
    """Score an eligible objective, or pass by supplying null.

    Args:
        objective_id: Objective ID to score, or null to score none.
    """
    return await _send(
        ctx,
        "score_objective",
        {"objective_id": objective_id},
        {"type": "score-objective", "objective": objective_id},
    )


@function_tool
async def call_for_support_against_neutral_force(
    ctx: RunContextWrapper[HarnessRunContext],
) -> str:
    """Call for support when marching against a neutral force."""
    return await _send(
        ctx,
        "call_for_support_against_neutral_force",
        {},
        {"type": "call-for-support-against-neutral-force"},
    )


GAMEPLAY_TOOLS: list[FunctionTool] = [
    place_planning_order,
    remove_planning_order,
    mark_ready,
    mark_unready,
    resolve_raid,
    resolve_march,
    choose_casualties,
    select_units,
    reconcile_armies,
    auto_reconcile_armies,
    muster_units,
    skip_mustering,
    resolve_track_ties,
    use_valyrian_steel_blade,
    refuse_support,
    replace_raven_order,
    skip_raven_order_replacement,
    inspect_top_wildling_card,
    place_inspected_wildling_card,
    select_region,
    select_westeros_card,
    claim_vassals,
    gift_power_tokens,
    distribute_power_tokens,
    drop_power_tokens,
    move_loyalty_token,
    resolve_consolidate_power,
    place_sellswords,
    resolve_spymaster,
    select_objectives,
    score_objective,
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
    "place-orders": {
        "place_planning_order",
        "remove_planning_order",
        "mark_ready",
        "mark_unready",
    },
    "resolve-raid-order": {"resolve_raid"},
    "resolve-march-order": {
        "resolve_march",
    },
    "resolve-single-march": {
        "resolve_march",
    },
    "choose-casualties": {"choose_casualties"},
    "select-units": {"select_units"},
    "resolve-retreat": {"select_units", "select_region"},
    "select-region": {"select_region"},
    "reconcile-armies": {"auto_reconcile_armies"},
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
    "claim-vassal": {"claim_vassals"},
    "claim-vassals": {"claim_vassals"},
    "distribute-power-tokens": {"distribute_power_tokens"},
    "move-loyalty-tokens": {"move_loyalty_token"},
    "move-loyalty-token-choice": {"move_loyalty_token"},
    "resolve-consolidate-power": {"resolve_consolidate_power"},
    "resolve-single-consolidate-power": {"resolve_consolidate_power"},
    "place-sellswords": {"place_sellswords"},
    "resolve-spymaster": {"resolve_spymaster"},
    "spymaster": {"resolve_spymaster"},
    "select-objectives": {"select_objectives"},
    "choose-initial-objectives": {"select_objectives"},
    "score-objectives": {"score_objective"},
    "score-other-objectives": {"score_objective"},
    "call-for-support-against-neutral-force": {
        "call_for_support_against_neutral_force"
    },
    "support-attack-against-neutral-force": {"call_for_support_against_neutral_force"},
}


def gameplay_tools_for_state(
    state_types: list[str], *, has_specific_tools: bool
) -> list[FunctionTool]:
    """Use the deepest recognized state's tools; fall back broadly if uncovered."""

    if has_specific_tools:
        return []
    for state_type in reversed(state_types):
        if state_type in _TOOLS_BY_STATE:
            names = _TOOLS_BY_STATE[state_type]
            return [_TOOLS_BY_NAME[name] for name in sorted(names)]
    return GAMEPLAY_TOOLS


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
