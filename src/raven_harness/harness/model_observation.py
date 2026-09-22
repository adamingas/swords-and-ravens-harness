"""A compact model view; canonical snapshots/history retain their full detail."""

from copy import deepcopy
from typing import Any

from .card_tools import _ability_texts
from .legal import _controller, _regions, _supply_guidance
from .observation import HarnessContext


def compact_observation(
    observation: dict[str, Any], context: HarnessContext
) -> dict[str, Any]:
    result = deepcopy(observation)
    if context.game is None or context.house_id is None:
        return result

    # One authoritative scoreboard, one card list, one order location. Repeated
    # generated memory summaries otherwise compete with the actual current state.
    result.pop("strategicOverview", None)
    result["you"] = {"houseId": context.house_id}
    cards = {
        item["houseId"]: item for item in result.pop("houseCardStatus", [])
    }
    for house in result.get("houses", []):
        house.pop("name", None)
        house["cards"] = {
            key: value for key, value in cards.get(house["id"], {}).items()
            if key not in {"houseId", "houseName"}
        }
        if context.combat and house["id"] in {
            context.combat.get("attackerId"), context.combat.get("defenderId")
        }:
            for card in house["cards"].get("availableCards", []):
                ability = card.get("ability")
                if ability:
                    card["abilityText"] = _ability_texts().get(
                        ability, "Use inspect_house_card or ask_rules_oracle for this ability."
                    )
    result.pop("revealedOrders", None)
    result["supplyLimit"] = _supply_guidance(context)
    result["game"]["roundStage"] = next(
        (state["type"] for state in context.path
         if state.get("type") in {"westeros", "planning", "action", "game-ended"}),
        "other",
    )
    for key in ("wildlingStrength", "valyrianSteelBladeUsed"):
        if key in context.game:
            result["game"][key] = context.game[key]

    memory = result.get("strategicMemory", {})
    result["strategicMemory"] = {
        "modelPlan": memory.get("modelPlan", ""),
        "lessons": memory.get("lessons", []),
    }
    # Recall remains available for the full decision history. Avoid injecting
    # twelve old plans plus duplicated serialized actions into every decision.
    result["historyIndex"] = result.get("historyIndex", [])[:4]
    result["recentEvents"] = [
        event for event in result.get("recentEvents", [])
        if len(event) > 1
    ]

    regions, static = _regions(context)
    visible = {item["id"]: item for item in result.get("board", [])}
    board = []
    blocked = []
    for area, reference in static.items():
        raw = visible.get(area, {})
        if raw.get("isBlocked"):
            blocked.append(area)
            continue
        entry: dict[str, Any] = {
            "id": area,
            "terrain": reference["type"],
            "controller": _controller(area, regions, static),
            "castlePoints": int(bool(reference.get("castleLevel"))),
        }
        for key in ("controlPowerToken", "garrison"):
            if raw.get(key):
                entry[key] = raw[key]
        if raw.get("units"):
            entry["units"] = [
                {key: value for key, value in unit.items()
                 if key != "wounded" or value}
                for unit in raw["units"]
            ]
        if raw.get("revealedOrder"):
            order = raw["revealedOrder"]
            entry["order"] = order["order"]
            entry["orderId"] = order["orderId"]
        board.append(entry)
    result["board"] = board
    result["blockedAreas"] = sorted(blocked)
    result["boardLegend"] = (
        "Every playable area is listed. Omitted units means empty; omitted order means "
        "no revealed order (planning orders may be hidden); omitted wounded means false. "
        "controller includes control tokens and home control, not just occupying units. "
        "blockedAreas cannot be entered. Static terrain, icons and connections are in the map."
    )

    # These facts live above the leaf decision in the server state tree. Copy
    # only from the authenticated player's already-redacted view, never a save.
    if context.combat:
        result["combat"] = {
            key: deepcopy(context.combat[key])
            for key in (
                "attackerId", "defenderId", "order", "houseCombatDatas",
                "supporters", "houseCardModifiers", "valyrianSteelBladeUser", "stats",
            )
            if key in context.combat
        }
        result["combat"]["meaning"] = (
            "houseCombatDatas lists each side's actual participating unit IDs and origin/defence "
            "area; the defender's region is the battlefield. Board units in the attacker's "
            "origin may include units left behind. supporters lists declared support by house. "
            "A null card is not revealed. Use the battlefield's neighbours for support."
        )
    return result
