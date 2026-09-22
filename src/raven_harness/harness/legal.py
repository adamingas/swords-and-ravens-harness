from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Any

from ..game.map_reference import load_map_reference
from ..game.state import region_is_blocked
from .observation import HarnessContext

RAID_ORDER_IDS = {13, 14, 15}
MARCH_ORDER_IDS = {1, 2, 3}
CONSOLIDATE_POWER_ORDER_IDS = {10, 11, 12}
STANDARD_RAID_TARGET_ORDER_IDS = {7, 8, 9, 10, 11, 12, 13, 14, 15}
STARRED_RAID_TARGET_ORDER_IDS = STANDARD_RAID_TARGET_ORDER_IDS | {4, 5, 6}
LAND_UNIT_TYPES = {"footman", "knight", "siege-engine"}
SUPPORT_ORDER_MODIFIERS = {7: 0, 8: 0, 9: 1, 17: 1, 21: 0}
MARCH_ORDER_MODIFIERS = {1: -1, 2: 0, 3: 1, 16: 0, 20: -1}


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
            if region_is_blocked(target):
                continue
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
            neutral_force = _neutral_force(context, target_id)
            if neutral_force is not None:
                feasible_groups = _feasible_neutral_force_unit_groups(
                    context,
                    region_id,
                    target_id,
                    units,
                )
                if not feasible_groups:
                    continue
                neutral_force = {
                    **neutral_force,
                    "feasibleUnitIdGroups": feasible_groups,
                }
            destinations.append(
                {
                    "regionId": target_id,
                    "type": static.get("type"),
                    "castleLevel": static.get("castleLevel", 0),
                    "castleAreasGainedIfCaptured": int(
                        bool(static.get("castleLevel")) and controller != context.house_id
                    ),
                    "garrison": target.get("garrison", 0),
                    "controller": controller,
                    "triggersCombat": bool(
                        controller != context.house_id
                        and (target.get("units") or target.get("garrison", 0) > 0)
                    ),
                    "neutralForce": neutral_force,
                    "supplySafeUnitIdGroupsWhenChosenAlone": [
                        list(group)
                        for size in range(1, len(units) + 1)
                        for group in combinations(
                            [int(unit["id"]) for unit in units], size
                        )
                        if _march_counts_fit_supply(
                            context,
                            region_id,
                            [(target_id, len(group))],
                        )
                    ],
                }
            )
        source = static_regions.get(region_id, {})
        result.append(
            {
                "regionId": region_id,
                "orderId": order_id,
                "order": _order_name(order_id),
                "unitIds": [int(unit["id"]) for unit in units],
                "castleAreasLostIfEmptiedWithoutToken": int(
                    bool(source.get("castleLevel"))
                    and (regions.get(region_id, {}).get("controlPowerToken") or source.get("homeController")) != context.house_id
                ),
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


def supply_safe_march_moves(
    context: HarnessContext,
    starting_region_id: str,
    moves: list[Any],
) -> list[Any]:
    """Keep requested march groups that fit Supply, in request priority order."""

    accepted: list[Any] = []
    for move in moves:
        candidate = [*accepted, move]
        if _march_counts_fit_supply(
            context,
            starting_region_id,
            [
                (item.destination_region_id, len(item.unit_ids))
                for item in candidate
            ],
        ):
            accepted.append(move)
    return accepted


def possible_neutral_force_support(
    context: HarnessContext,
) -> dict[str, list[str]]:
    """Return neutral-force targets with foreign houses the server can ask."""

    if (
        context.game is None
        or context.ingame is None
        or context.house_id is None
        or (context.leaf or {}).get("type") != "resolve-single-march"
        or (context.leaf or {}).get("supportersAgainstNeutralForce") is not None
    ):
        return {}
    regions, static_regions = _regions(context)
    result: dict[str, set[str]] = {}
    for source_id, order_id in _orders(context).items():
        if order_id not in MARCH_ORDER_IDS:
            continue
        if _controller(source_id, regions, static_regions) != context.house_id:
            continue
        source_static = static_regions.get(source_id, {})
        if _region_kind(source_static) != "land":
            continue
        target_ids = _reachable_regions(
            source_id,
            "land",
            context.house_id,
            regions,
            static_regions,
        )
        for target_id in target_ids:
            target = regions.get(target_id, {})
            if (
                int(target.get("garrison", 0)) <= 0
                or region_is_blocked(target)
                or _controller(target_id, regions, static_regions) is not None
            ):
                continue
            for support_id in _supporting_region_ids(
                context, target_id, static_regions
            ):
                controller = _controller(support_id, regions, static_regions)
                if controller is not None and controller != context.house_id:
                    result.setdefault(target_id, set()).add(controller)
    return {
        target_id: sorted(houses)
        for target_id, houses in sorted(result.items())
        if houses
    }


def neutral_force_attack_is_legal(
    context: HarnessContext,
    starting_region_id: str,
    target_region_id: str,
    unit_ids: list[int],
    prior_non_combat_moves: list[tuple[str, list[int]]] | None = None,
) -> bool:
    """Match the base engine's strength gate for an uncontrolled garrison."""

    regions, _ = _regions(context)
    if region_is_blocked(regions.get(target_region_id, {})):
        return False
    neutral_force = _neutral_force(context, target_region_id)
    if neutral_force is None:
        return True
    return _neutral_force_attack_strength(
        context,
        starting_region_id,
        target_region_id,
        unit_ids,
        prior_non_combat_moves or [],
    ) >= int(neutral_force["requiredStrength"])


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


def validate_musterings(
    context: HarnessContext,
    musters: list[Any],
    *,
    check_supply: bool = True,
    check_points: bool = True,
) -> None:
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
        if check_points and points[muster.mustering_region_id] > int(
            origin["musteringPoints"]
        ):
            raise ValueError("recruitments exceed the origin's mustering points")

    availability = _available_pieces(context)
    for unit_type, count in created.items():
        extra = upgrade_count if unit_type == "footman" else 0
        if count > availability.get(unit_type, 0) + extra:
            raise ValueError(f"not enough {unit_type} pieces remain")
    if check_supply:
        _validate_supply_after_recruitment(context, additions)


def supply_safe_musterings(
    context: HarnessContext, musters: list[Any]
) -> list[Any]:
    """Keep the priority-ordered subset that fits the current Supply track."""

    allowed = _allowed_army_sizes(context)
    if allowed is None:
        return list(musters)
    additions: dict[str, int] = {}
    result = []
    for muster in musters:
        recruitments = []
        for recruitment in muster.recruitments:
            if recruitment.upgrade_from_footman:
                recruitments.append(recruitment)
                continue
            candidate = dict(additions)
            candidate[recruitment.region_id] = (
                candidate.get(recruitment.region_id, 0) + 1
            )
            if _army_sizes_fit(_army_sizes_after_additions(context, candidate), allowed):
                additions = candidate
                recruitments.append(recruitment)
        if recruitments:
            result.append(muster.model_copy(update={"recruitments": recruitments}))
    return result


def point_safe_musterings(
    context: HarnessContext, musters: list[Any]
) -> list[Any]:
    """Keep each origin's priority-ordered subset within its mustering points."""

    options = {
        item["regionId"]: item for item in legal_mustering_options(context)["origins"]
    }
    result = []
    for muster in musters:
        remaining = int(options[muster.mustering_region_id]["musteringPoints"])
        recruitments = []
        for recruitment in muster.recruitments:
            cost = (
                1
                if recruitment.upgrade_from_footman
                or recruitment.unit_type in {"footman", "ship"}
                else 2
            )
            if cost <= remaining:
                recruitments.append(recruitment)
                remaining -= cost
        if recruitments:
            result.append(muster.model_copy(update={"recruitments": recruitments}))
    return result


def _neutral_force(
    context: HarnessContext, target_region_id: str
) -> dict[str, Any] | None:
    regions, static_regions = _regions(context)
    target = regions.get(target_region_id, {})
    required_strength = int(target.get("garrison", 0))
    if (
        required_strength <= 0
        or region_is_blocked(target)
        or _controller(target_region_id, regions, static_regions) is not None
    ):
        return None
    static = static_regions.get(target_region_id, {})
    has_structure = (
        int(static.get("castleLevel", 0)) + int(target.get("castleModifier", 0))
    ) > 0
    return {
        "requiredStrength": required_strength,
        "hasStructure": has_structure,
    }


def _feasible_neutral_force_unit_groups(
    context: HarnessContext,
    starting_region_id: str,
    target_region_id: str,
    units: list[dict[str, Any]],
) -> list[list[int]]:
    unit_ids = sorted(int(unit["id"]) for unit in units)
    return [
        list(group)
        for count in range(1, len(unit_ids) + 1)
        for group in combinations(unit_ids, count)
        if neutral_force_attack_is_legal(
            context,
            starting_region_id,
            target_region_id,
            list(group),
        )
    ]


def _neutral_force_attack_strength(
    context: HarnessContext,
    starting_region_id: str,
    target_region_id: str,
    unit_ids: list[int],
    prior_non_combat_moves: list[tuple[str, list[int]]],
) -> int:
    regions, static_regions = _regions(context)
    neutral_force = _neutral_force(context, target_region_id)
    if neutral_force is None:
        return 0
    attacking_structure = bool(neutral_force["hasStructure"])
    units_by_id = {
        int(unit["id"]): unit
        for region in regions.values()
        for unit in region.get("units", [])
    }
    strength = sum(
        _unit_strength(units_by_id[unit_id], attacking_structure)
        for unit_id in unit_ids
        if unit_id in units_by_id
    )
    march_order_id = _orders(context).get(starting_region_id)
    strength += MARCH_ORDER_MODIFIERS.get(march_order_id or 0, 0)

    accepted_foreign = _accepted_neutral_force_supporters(
        context, target_region_id
    )
    prior_units_by_destination = {
        destination_id: [
            units_by_id[unit_id]
            for unit_id in moved_unit_ids
            if unit_id in units_by_id
        ]
        for destination_id, moved_unit_ids in prior_non_combat_moves
    }
    for support_id in _supporting_region_ids(
        context, target_region_id, static_regions
    ):
        controller = _controller(support_id, regions, static_regions)
        if controller != context.house_id and controller not in accepted_foreign:
            continue
        strength += SUPPORT_ORDER_MODIFIERS[_orders(context)[support_id]]
        strength += sum(
            _unit_strength(unit, attacking_structure)
            for unit in regions.get(support_id, {}).get("units", [])
        )
        if controller == context.house_id:
            strength += sum(
                _unit_strength(unit, attacking_structure)
                for unit in prior_units_by_destination.get(support_id, [])
            )
    return strength


def _supporting_region_ids(
    context: HarnessContext,
    target_region_id: str,
    static_regions: dict[str, dict[str, Any]],
) -> list[str]:
    orders = _orders(context)
    result = []
    for region_id in static_regions.get(target_region_id, {}).get("neighbours", []):
        if orders.get(region_id) not in SUPPORT_ORDER_MODIFIERS:
            continue
        static = static_regions.get(region_id, {})
        if static.get("type") == "port" and target_region_id in static.get(
            "neighbours", []
        ):
            continue
        result.append(region_id)
    return result


def _accepted_neutral_force_supporters(
    context: HarnessContext, target_region_id: str
) -> set[str]:
    serialized = (context.leaf or {}).get("supportersAgainstNeutralForce") or []
    return {
        str(house_id)
        for region_id, house_ids in serialized
        if str(region_id) == target_region_id
        for house_id in house_ids
    }


def _unit_strength(unit: dict[str, Any], attacking_structure: bool) -> int:
    if unit.get("wounded", False):
        return 0
    unit_type = str(unit.get("type", ""))
    if unit_type == "knight":
        return 2
    if unit_type == "siege-engine":
        return 4 if attacking_structure else 0
    if unit_type in {"footman", "ship"}:
        return 1
    return 0


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


def _march_counts_fit_supply(
    context: HarnessContext,
    starting_region_id: str,
    moves: list[tuple[str, int]],
) -> bool:
    counts = _own_unit_counts(context)
    counts[starting_region_id] = max(
        0,
        counts.get(starting_region_id, 0) - sum(count for _, count in moves),
    )
    for destination_id, count in moves:
        counts[destination_id] = counts.get(destination_id, 0) + count

    allowed = _allowed_army_sizes(context)
    if allowed is not None and not _army_sizes_fit(
        sorted((count for count in counts.values() if count > 1), reverse=True),
        allowed,
    ):
        return False

    _, static_regions = _regions(context)
    return all(
        static_regions.get(destination_id, {}).get("type") != "port"
        or counts.get(destination_id, 0) <= 3
        for destination_id, _ in moves
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
    return (
        region.get("controlPowerToken")
        or region.get("overwrittenSuperControlPowerToken")
        or static.get("homeController")
    )


def _reachable_regions(
    starting_region_id: str,
    unit_kind: str,
    house_id: str,
    regions: dict[str, dict[str, Any]],
    static_regions: dict[str, dict[str, Any]],
) -> set[str]:
    return set(_reachable_routes(
        starting_region_id, unit_kind, house_id, regions, static_regions
    ))


def _reachable_routes(
    starting_region_id: str,
    unit_kind: str,
    house_id: str,
    regions: dict[str, dict[str, Any]],
    static_regions: dict[str, dict[str, Any]],
    *,
    exclude_blocked: bool = False,
) -> dict[str, list[str]]:
    """One shortest route per destination; only friendly transports bridge edges.

    These are geometric routes. Callers apply blocked-area, port, Supply and
    neutral-force restrictions. Wounded ships still transport per World.canActAsBridge.
    """
    pending = deque([[starting_region_id, target] for target in sorted(
        static_regions.get(starting_region_id, {}).get("neighbours", [])
    )])
    checked = {starting_region_id}
    routes: dict[str, list[str]] = {}
    while pending:
        route = pending.popleft()
        region_id = route[-1]
        if region_id in checked:
            continue
        checked.add(region_id)
        if exclude_blocked and region_is_blocked(regions.get(region_id, {})):
            continue
        static = static_regions.get(region_id, {})
        if _region_kind(static) == unit_kind:
            routes[region_id] = route
        if _can_bridge(region_id, unit_kind, house_id, regions, static_regions):
            pending.extend(
                [*route, neighbour]
                for neighbour in sorted(static.get("neighbours", []))
                if neighbour not in checked
            )
    return routes


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
