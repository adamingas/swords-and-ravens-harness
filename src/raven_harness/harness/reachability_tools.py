"""Geographic movement routes on the calling player's current visible board."""

import json
from typing import Any

from agents import RunContextWrapper, function_tool

from ..game.state import region_is_blocked
from .actions import HarnessRunContext
from .legal import _reachable_routes, _region_kind, _regions
from .map_tools import _resolve_area_id
from .observation import HarnessContext
from .protocol_tools import _is_base_game


def movement_reachability(context: HarnessContext, area: str) -> dict[str, Any]:
    """Infer movement terrain from the origin, independently of its occupants."""
    if context.game is None or context.house_id is None:
        raise ValueError(
            "Reachability requires an in-game player with an assigned house."
        )
    if not _is_base_game(context.snapshot):
        raise ValueError(
            "Reachability supports three- and six-player base games without vassals."
        )
    regions, static = _regions(context)
    source_id = _resolve_area_id(area, static)
    kind = _region_kind(static[source_id])
    result = {
        "houseId": context.house_id,
        "source": {key: static[source_id][key] for key in ("id", "name", "type")},
        "movementType": kind,
        "destinations": [],
    }
    if region_is_blocked(regions.get(source_id, {})):
        return result
    routes = _reachable_routes(
        source_id, kind, context.house_id, regions, static, exclude_blocked=True
    )
    for target_id, route in sorted(routes.items()):
        result["destinations"].append(
            {
                **{key: static[target_id][key] for key in ("id", "name", "type")},
                "castlePoints": int(bool(static[target_id].get("castleLevel"))),
                "route": route,
                "transportShips": [
                    {
                        "regionId": step,
                        "unitIds": sorted(
                            int(unit["id"])
                            for unit in regions[step].get("units", [])
                            if unit.get("allegiance") == context.house_id
                            and unit.get("type") == "ship"
                        ),
                    }
                    for step in route[1:-1]
                ],
            }
        )
    return result


@function_tool
async def reachable_areas(ctx: RunContextWrapper[HarnessRunContext], area: str) -> str:
    """Find geographic movement routes from any area, even empty or enemy-held.

    Land origins imply land movement; sea/port origins imply ship movement.
    Land routes include transport through your CURRENT ships (wounded ships
    still transport). Returns destinations and one shortest route to each,
    identifying any transport ships and castlePoints (0 or 1) at each target.
    Blocked areas cannot be entered or crossed;
    a blocked origin returns no destinations. Land movement cannot chain across
    intervening land areas. Ships reach adjacent seas/ports only.
    This is NOT a legal-move list: unit counts, wounds, orders, Supply, combat
    strength, and port ownership/capacity do not filter destinations. Check
    actionGuidance and submit_action for move legality. For adjacency/support
    use check_neighbours. This read-only query does not finish your decision.

    Args:
        area: Exact starting area ID or display name, case-insensitive.
    """
    return json.dumps(movement_reachability(ctx.context.current_game_context(), area))
