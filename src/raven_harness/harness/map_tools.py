"""Read-only neighbourhood queries against the player's current board."""

import json
from typing import Any, TypedDict

from agents import RunContextWrapper, function_tool

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
    units: list[dict[str, Any]]
    visibleOrder: dict[str, Any] | None


def neighbouring_areas(context: HarnessContext, area: str) -> list[Area]:
    """Join direct map edges with current, player-visible board facts."""

    if context.game is None:
        raise ValueError("The map is only available during a game.")
    regions, static_regions = _regions(context)
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
    orders = _orders(context)
    result: list[Area] = []
    for region_id in matches[0]["neighbours"]:
        static = static_regions[region_id]
        region = regions.get(region_id, {})
        order_id = orders.get(region_id)
        result.append(
            Area(
                id=region_id,
                name=static["name"],
                owner=_controller(region_id, regions, static_regions),
                type=static["type"],
                castleLevel=static["castleLevel"],
                supplyIcons=static["supplyIcons"],
                crownIcons=static["crownIcons"],
                garrison=region.get("garrison", 0),
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
        )
    return result


@function_tool
async def check_neighbours(ctx: RunContextWrapper[HarnessRunContext], area: str) -> str:
    """List direct graph neighbours with current owners, units and visible orders.

    Includes land/sea/port type, castleLevel (0 none, 1 castle, 2 stronghold),
    supply/crown icons and garrisons. Units use the game's canonical type names.
    A null visibleOrder means no revealed order; hidden orders are not inferred.
    These are map edges, not a list of legal moves or eligible supporters:
    terrain and port restrictions still apply. Ship-transport destinations are
    not direct neighbours. Use actionGuidance for legal march destinations.
    For support, query the BATTLEFIELD, not the marching army's origin.
    This read-only tool does not submit an action or finish your decision.
    After reading the result, continue exploring or call submit_action.

    Args:
        area: Exact area ID or display name, case-insensitive (e.g. winterfell).
    """

    return json.dumps(neighbouring_areas(ctx.context.current_game_context(), area))
