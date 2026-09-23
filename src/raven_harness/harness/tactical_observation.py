"""Player-visible geometry and combat components, without selecting a strategy."""

from typing import Any

from ..game.state import region_is_blocked
from .legal import (
    MARCH_ORDER_MODIFIERS,
    SUPPORT_ORDER_MODIFIERS,
    _controller,
    _orders,
    _regions,
    _unit_strength,
)
from .observation import HarnessContext


def supportable_battlefields(context: HarnessContext, source: str) -> list[str]:
    """Direct support geometry. Orders, declaration and card effects are separate."""
    regions, static = _regions(context)
    origin = static.get(source, {})
    if region_is_blocked(regions.get(source, {})):
        return []
    return [
        target for target in origin.get("neighbours", [])
        if not region_is_blocked(regions.get(target, {}))
        and not (origin.get("type") == "port" and static[target]["type"] == "land")
        and not (origin.get("type") == "land" and static[target]["type"] == "sea")
    ]


def combat_components(context: HarnessContext) -> dict[str, Any] | None:
    """Baseline strength before cards/abilities, Blade and Tides of Battle.

    Never interpret a hidden card as a zero-strength card. Missing participating
    units make the arithmetic unavailable, rather than silently counting zero.
    """
    combat = context.combat
    if not combat or not context.game:
        return None
    participants = dict(combat.get("houseCombatDatas", []))
    attacker, defender = combat.get("attackerId"), combat.get("defenderId")
    if attacker not in participants or defender not in participants:
        return None
    regions, static = _regions(context)
    battlefield = participants[defender].get("regionId")
    if battlefield not in static:
        return None
    units = {u["id"]: u for r in regions.values() for u in r.get("units", [])}
    orders = _orders(context)
    declarations = dict(combat.get("supporters", []))
    eligible = [
        area for area, order in orders.items()
        if order in SUPPORT_ORDER_MODIFIERS
        and battlefield in supportable_battlefields(context, area)
    ]
    sides = {}
    for role, house in (("attacker", attacker), ("defender", defender)):
        data = participants[house]
        army_ids = data.get("army", [])
        if any(uid not in units for uid in army_ids):
            return None
        attacking_structure = role == "attacker" and bool(
            static[battlefield].get("castleLevel", 0)
            + regions.get(battlefield, {}).get("castleModifier", 0) > 0
        )
        army = [
            {"id": uid, "type": units[uid]["type"],
             "strength": _unit_strength(units[uid], attacking_structure)}
            for uid in army_ids
        ]
        order = orders.get(data["regionId"])
        order_bonus = (
            MARCH_ORDER_MODIFIERS.get(order, 0) if role == "attacker"
            else {4: 1, 5: 1, 6: 2}.get(order, 0)
        )
        support = []
        for area in eligible:
            owner = _controller(area, regions, static)
            if declarations.get(owner) != house:
                continue
            support.append({
                "regionId": area, "houseId": owner,
                "strength": sum(_unit_strength(u, attacking_structure)
                                for u in regions.get(area, {}).get("units", []))
                + SUPPORT_ORDER_MODIFIERS[orders[area]],
            })
        garrison = regions.get(battlefield, {}).get("garrison", 0) if role == "defender" else 0
        sides[role] = {
            "houseId": house, "regionId": data["regionId"], "participatingUnits": army,
            "armyStrength": sum(u["strength"] for u in army), "orderBonus": order_bonus,
            "garrison": garrison, "declaredSupport": support,
            "subtotalBeforeCards": sum(u["strength"] for u in army) + order_bonus
            + garrison + sum(s["strength"] for s in support),
            "revealedCardId": data.get("houseCardId"),
        }
    fiefdoms = context.game.get("fiefdomsTrack", [])
    return {
        "battlefield": battlefield, **sides,
        "tieWinnerBeforeAbilities": next((h for h in fiefdoms if h in {attacker, defender}), None),
        "blade": {"holder": fiefdoms[0] if fiefdoms else None,
                  "usedThisRound": context.game.get("valyrianSteelBladeUsed", False),
                  "visibleUser": combat.get("valyrianSteelBladeUser")},
        "supportOrdersAdjacentToBattlefield": [
            {"regionId": area, "houseId": _controller(area, regions, static),
             "declaration": declarations.get(_controller(area, regions, static), "pending")}
            for area in eligible
        ],
        "calculationScope": (
            "Subtotals include ONLY the listed participating units, orders, garrison and "
            "declared support. Before comparing, apply BOTH cards and their abilities, "
            "Blade and any Tides of Battle. A null revealedCardId is unknown, not zero. "
            "Towers prevent your casualties if you lose; swords cause casualties if you win."
        ),
    }
