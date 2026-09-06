from __future__ import annotations

from typing import Any

from ..game.map_reference import load_map_reference
from .observation import HarnessContext

RAID_ORDER_IDS = {13, 14, 15}
MARCH_ORDER_IDS = {1, 2, 3}
CONSOLIDATE_POWER_ORDER_IDS = {10, 11, 12}
STANDARD_RAID_TARGET_ORDER_IDS = {7, 8, 9, 10, 11, 12, 13, 14, 15}
STARRED_RAID_TARGET_ORDER_IDS = STANDARD_RAID_TARGET_ORDER_IDS | {4, 5, 6}
LAND_UNIT_TYPES = {"footman", "knight", "siege-engine"}


def legal_raid_options(context: HarnessContext) -> list[dict[str, Any]]:
    """Return base-game raid sources and their exact currently legal targets."""

    if context.ingame is None or context.game is None or context.house_id is None:
        return []
    regions, static_regions = _regions(context)
    orders = _orders(context)
    result: list[dict[str, Any]] = []
    for region_id, order_id in orders.items():
        if order_id not in RAID_ORDER_IDS:
            continue
        if _controller(region_id, regions, static_regions) != context.house_id:
            continue
        source = static_regions.get(region_id, {})
        source_kind = _region_kind(source)
        target_order_ids = (
            STARRED_RAID_TARGET_ORDER_IDS
            if order_id == 15
            else STANDARD_RAID_TARGET_ORDER_IDS
        )
        targets = []
        for target_id in source.get("neighbours", []):
            target_order_id = orders.get(target_id)
            if target_order_id not in target_order_ids:
                continue
            if _controller(target_id, regions, static_regions) in {
                None,
                context.house_id,
            }:
                continue
            target_kind = _region_kind(static_regions.get(target_id, {}))
            if source_kind == "land" and target_kind != "land":
                continue
            targets.append(
                {
                    "regionId": target_id,
                    "orderId": target_order_id,
                    "order": _order_name(target_order_id),
                    "controller": _controller(target_id, regions, static_regions),
                }
            )
        result.append(
            {
                "regionId": region_id,
                "orderId": order_id,
                "order": _order_name(order_id),
                "raidableTargets": sorted(targets, key=lambda item: item["regionId"]),
            }
        )
    return sorted(result, key=lambda item: item["regionId"])


def legal_march_options(context: HarnessContext) -> list[dict[str, Any]]:
    """Return march sources, movable units, and reachable base-game destinations."""

    if context.ingame is None or context.game is None or context.house_id is None:
        return []
    regions, static_regions = _regions(context)
    orders = _orders(context)
    result: list[dict[str, Any]] = []
    for region_id, order_id in orders.items():
        if order_id not in MARCH_ORDER_IDS:
            continue
        if _controller(region_id, regions, static_regions) != context.house_id:
            continue
        units = [
            unit
            for unit in regions.get(region_id, {}).get("units", [])
            if unit.get("allegiance") == context.house_id
            and not unit.get("wounded", False)
        ]
        if not units:
            continue
        unit_kind = _unit_kind(str(units[0].get("type", "")))
        if unit_kind is None or any(
            _unit_kind(str(unit.get("type", ""))) != unit_kind for unit in units
        ):
            continue
        destinations = []
        for target_id in _reachable_regions(
            region_id,
            unit_kind,
            context.house_id,
            regions,
            static_regions,
        ):
            target = regions.get(target_id, {})
            static = static_regions.get(target_id, {})
            controller = _controller(target_id, regions, static_regions)
            if static.get("type") == "port":
                adjacent_land = next(
                    (
                        neighbour_id
                        for neighbour_id in static.get("neighbours", [])
                        if _region_kind(static_regions.get(neighbour_id, {})) == "land"
                    ),
                    None,
                )
                if (
                    adjacent_land is None
                    or _controller(adjacent_land, regions, static_regions)
                    != context.house_id
                ):
                    continue
            destinations.append(
                {
                    "regionId": target_id,
                    "type": static.get("type"),
                    "garrison": target.get("garrison", 0),
                    "controller": controller,
                    "triggersCombat": bool(
                        controller != context.house_id
                        and (target.get("units") or target.get("garrison", 0) > 0)
                    ),
                }
            )
        source = static_regions.get(region_id, {})
        result.append(
            {
                "regionId": region_id,
                "orderId": order_id,
                "order": _order_name(order_id),
                "unitIds": [int(unit["id"]) for unit in units],
                "reachableRegions": sorted(
                    destinations, key=lambda item: item["regionId"]
                ),
                "canLeavePowerToken": (
                    _region_kind(source) == "land"
                    and not regions.get(region_id, {}).get("controlPowerToken")
                    and source.get("homeController") != context.house_id
                    and int((context.house or {}).get("powerTokens", 0)) > 0
                ),
            }
        )
    return sorted(result, key=lambda item: item["regionId"])


def legal_consolidate_power_options(
    context: HarnessContext,
) -> list[dict[str, Any]]:
    """Return normal base-game Consolidate Power choices per order region."""

    if context.ingame is None or context.game is None or context.house_id is None:
        return []
    regions, static_regions = _regions(context)
    result = []
    for region_id, order_id in _orders(context).items():
        if order_id not in CONSOLIDATE_POWER_ORDER_IDS:
            continue
        if _controller(region_id, regions, static_regions) != context.house_id:
            continue
        choices = ["gain_power_tokens"]
        if order_id == 12 and int(static_regions.get(region_id, {}).get("castleLevel", 0)):
            choices.append("muster_units")
        result.append(
            {
                "regionId": region_id,
                "orderId": order_id,
                "order": _order_name(order_id),
                "choices": choices,
            }
        )
    return sorted(result, key=lambda item: item["regionId"])


def legal_mustering_options(context: HarnessContext) -> dict[str, Any]:
    """Return base-game mustering origins and static recruitment constraints."""

    if context.game is None or context.house_id is None:
        return {"musteringType": None, "maxOriginGroups": 0, "origins": []}
    leaf = context.leaf or {}
    mustering_type = int(leaf.get("musteringType", 0))
    regions, static_regions = _regions(context)
    orders = _orders(context)
    origins = []
    for region_id, static in static_regions.items():
        castle_level = int(static.get("castleLevel", 0))
        if castle_level <= 0:
            continue
        if _controller(region_id, regions, static_regions) != context.house_id:
            continue
        if mustering_type == 1 and orders.get(region_id) != 12:
            continue
        if mustering_type == 4 and castle_level != 1:
            continue
        destinations = []
        for destination_id in [region_id, *static.get("neighbours", [])]:
            destination_static = static_regions.get(destination_id, {})
            destination_kind = _region_kind(destination_static)
            if destination_id != region_id and destination_kind != "sea":
                continue
            controller = _controller(destination_id, regions, static_regions)
            target = regions.get(destination_id, {})
            if controller not in {None, context.house_id}:
                continue
            if int(target.get("garrison", 0)) > 0 and controller != context.house_id:
                continue
            unit_types = (
                ["footman", "knight", "siege-engine"]
                if destination_kind == "land"
                else ["ship"]
            )
            destinations.append(
                {
                    "regionId": destination_id,
                    "type": destination_static.get("type"),
                    "newUnitTypes": unit_types,
                    "currentUnitCount": _own_unit_counts(context).get(
                        destination_id, 0
                    ),
                    "supplySafeNewUnitsWhenChosenAlone": (
                        _maximum_supply_safe_additions(context, destination_id)
                    ),
                    "upgradeableFootmen": sum(
                        1
                        for unit in target.get("units", [])
                        if unit.get("allegiance") == context.house_id
                        and unit.get("type") == "footman"
                    ),
                }
            )
        origins.append(
            {
                "regionId": region_id,
                "musteringPoints": castle_level,
                "destinations": destinations,
            }
        )
    maximum = 1 if mustering_type in {1, 2, 3} else len(origins)
    return {
        "musteringType": mustering_type,
        "maxOriginGroups": maximum,
        "origins": sorted(origins, key=lambda item: item["regionId"]),
        "availablePieces": _available_pieces(context),
        "supplyLimit": _supply_guidance(context),
    }


def legal_raven_replacements(context: HarnessContext) -> list[dict[str, Any]]:
    """Return base-game region/token pairs accepted for a Raven replacement."""

    if context.game is None or context.ingame is None or context.house_id is None:
        return []
    regions, static_regions = _regions(context)
    own_orders = {
        region_id: order_id
        for region_id, order_id in _orders(context).items()
        if _controller(region_id, regions, static_regions) == context.house_id
    }
    kings_court = list(context.game.get("kingsCourtTrack", []))
    restrictions = list(context.game.get("starredOrderRestrictions", []))
    position = (
        kings_court.index(context.house_id)
        if context.house_id in kings_court
        else -1
    )
    allowed_stars = (
        int(restrictions[position]) if 0 <= position < len(restrictions) else 0
    )
    starred = {3, 6, 9, 12, 15}
    result = []
    for region_id, original_order_id in own_orders.items():
        used_elsewhere = {
            order_id
            for other_region_id, order_id in own_orders.items()
            if other_region_id != region_id
        }
        available = [order_id for order_id in range(1, 16) if order_id not in used_elsewhere]
        if allowed_stars > 0:
            used_stars = sum(order_id in starred for order_id in used_elsewhere)
            if used_stars >= allowed_stars:
                available = [order_id for order_id in available if order_id not in starred]
        result.append(
            {
                "regionId": region_id,
                "originalOrderId": original_order_id,
                "availableOrderIds": available,
            }
        )
    return sorted(result, key=lambda item: item["regionId"])


def validate_musterings(context: HarnessContext, musters: list[Any]) -> None:
    """Reject statically illegal base-game recruitments before server submission."""

    guidance = legal_mustering_options(context)
    options = {item["regionId"]: item for item in guidance["origins"]}
    origin_ids = [muster.mustering_region_id for muster in musters]
    if len(origin_ids) != len(set(origin_ids)):
        raise ValueError("each mustering_region_id may appear at most once")
    if len(origin_ids) > guidance["maxOriginGroups"]:
        raise ValueError(
            f"this mustering decision permits at most {guidance['maxOriginGroups']} origin"
        )
    invalid_origins = sorted(set(origin_ids) - set(options))
    if invalid_origins:
        raise ValueError(f"mustering_region_id is not legal: {invalid_origins}")

    upgrades_by_region: dict[str, int] = {}
    upgrade_count = 0
    created = {unit_type: 0 for unit_type in _available_pieces(context)}
    points = {origin_id: 0 for origin_id in origin_ids}
    additions: dict[str, int] = {}
    for muster in musters:
        origin = options[muster.mustering_region_id]
        destinations = {
            item["regionId"]: item for item in origin.get("destinations", [])
        }
        for recruitment in muster.recruitments:
            destination = destinations.get(recruitment.region_id)
            if destination is None:
                raise ValueError(
                    "recruitment region is not legal for its mustering origin"
                )
            if recruitment.unit_type not in destination["newUnitTypes"]:
                raise ValueError("unit_type cannot be mustered in this region")
            if not recruitment.upgrade_from_footman:
                cost = 1 if recruitment.unit_type in {"footman", "ship"} else 2
                created[recruitment.unit_type] = (
                    created.get(recruitment.unit_type, 0) + 1
                )
                additions[recruitment.region_id] = (
                    additions.get(recruitment.region_id, 0) + 1
                )
            else:
                if recruitment.unit_type not in {"knight", "siege-engine"}:
                    raise ValueError(
                        "a Footman can upgrade only to knight or siege-engine"
                    )
                used = upgrades_by_region.get(recruitment.region_id, 0)
                if used >= int(destination["upgradeableFootmen"]):
                    raise ValueError(
                        "no unused Footman is available to upgrade in the recruitment region"
                    )
                upgrades_by_region[recruitment.region_id] = used + 1
                upgrade_count += 1
                created[recruitment.unit_type] = (
                    created.get(recruitment.unit_type, 0) + 1
                )
                cost = 1
            points[muster.mustering_region_id] += cost
        if points[muster.mustering_region_id] > int(origin["musteringPoints"]):
            raise ValueError("recruitments exceed the origin's mustering points")

    availability = _available_pieces(context)
    for unit_type, count in created.items():
        extra = upgrade_count if unit_type == "footman" else 0
        if count > availability.get(unit_type, 0) + extra:
            raise ValueError(f"not enough {unit_type} pieces remain")
    _validate_supply_after_recruitment(context, additions)


def _regions(
    context: HarnessContext,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    settings = context.snapshot.get("gameSettings", {})
    map_reference = load_map_reference(
        int(settings.get("playerCount", 6)),
        bool(settings.get("addPortToTheEyrie", False)),
    )
    regions = {
        str(region["id"]): region
        for region in (context.game or {}).get("world", {}).get("regions", [])
    }
    static_regions = {
        str(region["id"]): region for region in map_reference.get("regions", [])
    }
    return regions, static_regions


def _orders(context: HarnessContext) -> dict[str, int]:
    return {
        str(region_id): int(order_id)
        for region_id, order_id in (context.ingame or {}).get("ordersOnBoard", [])
        if order_id is not None
    }


def _available_pieces(context: HarnessContext) -> dict[str, int]:
    limits = {
        str(unit_type): int(limit)
        for unit_type, limit in (context.house or {}).get("unitLimits", [])
    }
    if not limits:
        limits = {"footman": 10, "knight": 5, "ship": 6, "siege-engine": 2}
    used = {unit_type: 0 for unit_type in limits}
    for region in (context.game or {}).get("world", {}).get("regions", []):
        for unit in region.get("units", []):
            if unit.get("allegiance") == context.house_id:
                unit_type = str(unit.get("type"))
                used[unit_type] = used.get(unit_type, 0) + 1
    return {
        unit_type: max(0, limit - used.get(unit_type, 0))
        for unit_type, limit in limits.items()
    }


def _validate_supply_after_recruitment(
    context: HarnessContext, additions: dict[str, int]
) -> None:
    allowed = _allowed_army_sizes(context)
    if allowed is None:
        return
    if not _army_sizes_fit(_army_sizes_after_additions(context, additions), allowed):
        raise ValueError("recruitments would exceed the house supply limit")


def _supply_guidance(context: HarnessContext) -> dict[str, Any]:
    """Describe the exact army slots used by the mustering validator."""

    supply = int((context.house or {}).get("supplyLevel", 0))
    allowed = _allowed_army_sizes(context)
    counts = _own_unit_counts(context)
    current_armies = sorted(
        (
            {"regionId": region_id, "unitCount": count}
            for region_id, count in counts.items()
            if count > 1
        ),
        key=lambda item: (-item["unitCount"], item["regionId"]),
    )
    return {
        "level": supply,
        "allowedArmySizes": allowed or [],
        "currentArmies": current_armies,
        "singleUnitRegions": sorted(
            region_id for region_id, count in counts.items() if count == 1
        ),
        "rule": (
            "Only regions with two or more units use an army slot. Sort army "
            "sizes largest first and compare them with allowedArmySizes."
        ),
    }


def _allowed_army_sizes(context: HarnessContext) -> list[int] | None:
    restrictions = (context.game or {}).get("supplyRestrictions", [])
    supply = int((context.house or {}).get("supplyLevel", 0))
    if not 0 <= supply < len(restrictions):
        return None
    return [int(value) for value in restrictions[supply]]


def _own_unit_counts(context: HarnessContext) -> dict[str, int]:
    return {
        str(region.get("id")): sum(
            unit.get("allegiance") == context.house_id
            for unit in region.get("units", [])
        )
        for region in (context.game or {}).get("world", {}).get("regions", [])
    }


def _army_sizes_after_additions(
    context: HarnessContext, additions: dict[str, int]
) -> list[int]:
    counts = _own_unit_counts(context)
    for region_id, count in additions.items():
        counts[region_id] = counts.get(region_id, 0) + count
    return sorted((count for count in counts.values() if count > 1), reverse=True)


def _army_sizes_fit(army_sizes: list[int], allowed: list[int]) -> bool:
    return len(army_sizes) <= len(allowed) and all(
        size <= allowed[index] for index, size in enumerate(army_sizes)
    )


def _maximum_supply_safe_additions(
    context: HarnessContext, region_id: str
) -> int | None:
    """Return capacity for one destination without implying combined capacity."""

    allowed = _allowed_army_sizes(context)
    if allowed is None:
        return None
    upper_bound = max(allowed, default=1)
    safe = 0
    for additions in range(1, upper_bound + 1):
        if not _army_sizes_fit(
            _army_sizes_after_additions(context, {region_id: additions}), allowed
        ):
            break
        safe = additions
    return safe


def _controller(
    region_id: str,
    regions: dict[str, dict[str, Any]],
    static_regions: dict[str, dict[str, Any]],
) -> str | None:
    region = regions.get(region_id, {})
    units = region.get("units", [])
    if units:
        return units[0].get("allegiance")
    static = static_regions.get(region_id, {})
    if static.get("type") == "port":
        land_id = next(
            (
                neighbour_id
                for neighbour_id in static.get("neighbours", [])
                if _region_kind(static_regions.get(neighbour_id, {})) == "land"
            ),
            None,
        )
        return (
            _controller(land_id, regions, static_regions)
            if land_id is not None
            else None
        )
    return region.get("controlPowerToken") or static.get("homeController")


def _reachable_regions(
    starting_region_id: str,
    unit_kind: str,
    house_id: str,
    regions: dict[str, dict[str, Any]],
    static_regions: dict[str, dict[str, Any]],
) -> set[str]:
    pending = list(static_regions.get(starting_region_id, {}).get("neighbours", []))
    checked: set[str] = set()
    reachable: set[str] = set()
    while pending:
        region_id = pending.pop()
        if region_id in checked:
            continue
        static = static_regions.get(region_id, {})
        if _region_kind(static) == unit_kind and region_id != starting_region_id:
            reachable.add(region_id)
        if _can_bridge(region_id, unit_kind, house_id, regions, static_regions):
            pending.extend(static.get("neighbours", []))
        checked.add(region_id)
    return reachable


def _can_bridge(
    region_id: str,
    unit_kind: str,
    house_id: str,
    regions: dict[str, dict[str, Any]],
    static_regions: dict[str, dict[str, Any]],
) -> bool:
    if unit_kind != "land":
        return False
    if _controller(region_id, regions, static_regions) != house_id:
        return False
    return any(
        unit.get("allegiance") == house_id and unit.get("type") == "ship"
        for unit in regions.get(region_id, {}).get("units", [])
    )


def _region_kind(region: dict[str, Any]) -> str | None:
    region_type = region.get("type")
    if region_type == "land":
        return "land"
    if region_type in {"sea", "port"}:
        return "sea"
    return None


def _unit_kind(unit_type: str) -> str | None:
    if unit_type in LAND_UNIT_TYPES:
        return "land"
    if unit_type == "ship":
        return "sea"
    return None


def _order_name(order_id: int) -> str:
    from .observation import ORDER_LEGEND

    return ORDER_LEGEND.get(order_id, f"Order {order_id}")
