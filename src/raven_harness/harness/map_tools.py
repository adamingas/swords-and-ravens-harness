"""Read-only neighbourhood queries against the player's current board."""

import json
from typing import Any, TypedDict

from agents import RunContextWrapper, function_tool

from ..game.state import region_is_blocked
from .actions import HarnessRunContext
from .legal import _controller, _orders, _regions
from .observation import HarnessContext, ORDER_LEGEND


class Area(TypedDict):
    id: str
    name: str
    owner: str | None
    type: str
    castleLevel: int
    supplyIcons: int
    crownIcons: int
    garrison: int
    isBlocked: bool
    units: list[dict[str, Any]]
    visibleOrder: dict[str, Any] | None


def neighbouring_areas(context: HarnessContext, area: str) -> list[Area]:
    """Join direct map edges with current, player-visible board facts."""

    if context.game is None:
        raise ValueError("The map is only available during a game.")
    regions, static_regions = _regions(context)
    source_id = _resolve_area_id(area, static_regions)
    orders = _orders(context)
    return [
        _area_details(region_id, regions, static_regions, orders)
        for region_id in static_regions[source_id]["neighbours"]
    ]


def _resolve_area_id(area: str, static_regions: dict[str, dict[str, Any]]) -> str:
    query = area.strip().casefold()
    matches = [
        region
        for region in static_regions.values()
        if query in (region["id"].casefold(), region["name"].casefold())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Unknown or ambiguous area {area!r}. Use an exact area ID or name "
            "from the system prompt's Map section."
        )
    return str(matches[0]["id"])


def _area_details(
    region_id: str,
    regions: dict[str, dict[str, Any]],
    static_regions: dict[str, dict[str, Any]],
    orders: dict[str, int],
) -> Area:
    static = static_regions[region_id]
    region = regions.get(region_id, {})
    order_id = orders.get(region_id)
    return Area(
        id=region_id,
        name=static["name"],
        owner=_controller(region_id, regions, static_regions),
        type=static["type"],
        castleLevel=static["castleLevel"],
        supplyIcons=static["supplyIcons"],
        crownIcons=static["crownIcons"],
        garrison=region.get("garrison", 0),
        isBlocked=region_is_blocked(region),
        units=[
            {
                "id": unit["id"],
                "type": unit["type"],
                "owner": unit["allegiance"],
                "wounded": unit.get("wounded", False),
            }
            for unit in region.get("units", [])
        ],
        visibleOrder=(
            {"id": order_id, "name": ORDER_LEGEND.get(order_id, "Unknown")}
            if order_id is not None
            else None
        ),
    )


@function_tool
async def check_neighbours(ctx: RunContextWrapper[HarnessRunContext], area: str) -> str:
    """List direct graph neighbours with current owners, units and visible orders.

    Includes land/sea/port type, castleLevel (0 none, 1 castle, 2 stronghold),
    supply/crown icons and garrisons. Units use the game's canonical type names.
    isBlocked=true (garrison 1000) marks an impassable area that cannot be entered.
    A null visibleOrder means no revealed order; hidden orders are not inferred.
    These are map edges, not a list of legal moves or eligible supporters:
    terrain and port restrictions still apply. Ship-transport destinations are
    not direct neighbours. Use reachable_areas for movement routes and
    actionGuidance for the current March decision.
    For support, query the BATTLEFIELD, not the marching army's origin.
    This read-only tool does not submit an action or finish your decision.
    After reading the result, continue exploring or finish your decision.

    Args:
        area: Exact area ID or display name, case-insensitive (e.g. winterfell).
    """

    return json.dumps(neighbouring_areas(ctx.context.current_game_context(), area))
