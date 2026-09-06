from dataclasses import dataclass
from typing import Any

from ..game.map_reference import load_map_reference
from ..game.state import find_state, ingame_state, player_house, state_path

ORDER_LEGEND = {
    1: "March -1",
    2: "March +0",
    3: "March +1",
    4: "Defense +1",
    5: "Defense +1",
    6: "Defense +2 starred",
    7: "Support +0",
    8: "Support +0",
    9: "Support +1 starred",
    10: "Consolidate Power",
    11: "Consolidate Power",
    12: "Consolidate Power starred",
    13: "Raid",
    14: "Raid",
    15: "Raid starred",
}


@dataclass(frozen=True)
class HarnessContext:
    snapshot: dict[str, Any]
    user_id: str
    path: list[dict[str, Any]]
    leaf: dict[str, Any] | None
    ingame: dict[str, Any] | None
    game: dict[str, Any] | None
    house_id: str | None
    house: dict[str, Any] | None
    planning: dict[str, Any] | None
    combat: dict[str, Any] | None
    recent_events: list[dict[str, Any]]


def build_context(
    snapshot: dict[str, Any],
    user_id: str,
    recent_events: list[dict[str, Any]] | None = None,
) -> HarnessContext:
    path = state_path(snapshot)
    ingame = ingame_state(snapshot)
    game = ingame.get("game") if ingame else None
    house_id = player_house(snapshot, user_id)
    house = next(
        (item for item in (game or {}).get("houses", []) if item.get("id") == house_id),
        None,
    )
    return HarnessContext(
        snapshot=snapshot,
        user_id=str(user_id),
        path=path,
        leaf=path[-1] if path else None,
        ingame=ingame,
        game=game,
        house_id=house_id,
        house=house,
        planning=find_state(path, "planning"),
        combat=find_state(path, "combat"),
        recent_events=recent_events or [],
    )


def build_observation(context: HarnessContext) -> dict[str, Any]:
    snapshot = context.snapshot
    leaf = context.leaf
    observation: dict[str, Any] = {
        "game": {
            "id": snapshot.get("id"),
            "name": snapshot.get("name"),
            "stateId": snapshot.get("leafStateId"),
            "phase": next(
                (
                    state["type"]
                    for state in reversed(context.path)
                    if state.get("type")
                ),
                "unknown",
            ),
        },
        "you": {"userId": context.user_id, "houseId": context.house_id},
        "isYourTurn": is_waiting_for_player(context),
        "pendingDecision": (
            {key: value for key, value in leaf.items() if key != "childGameState"}
            if leaf
            else None
        ),
        "statePath": [state.get("type", "unknown") for state in context.path],
        "recentEvents": [_sanitize_event(item) for item in context.recent_events[-12:]],
        "orderLegend": ORDER_LEGEND,
    }

    child = snapshot.get("childGameState", {})
    if child.get("type") == "lobby":
        observation["lobby"] = {
            "houses": child.get("lobbyHouses", []),
            "availableHouseIds": child.get("availableHouseIds", []),
            "seats": [
                {"houseId": house_id, "userId": str(user_id)}
                for house_id, user_id in child.get("players", [])
            ],
            "readyUserIds": (
                [str(value) for value in child["readyUsers"]]
                if child.get("readyUsers") is not None
                else None
            ),
        }
        return observation

    game = context.game
    house = context.house
    if context.ingame and game:
        settings = snapshot.get("gameSettings", {})
        observation["map"] = load_map_reference(
            int(settings.get("playerCount", 6)),
            bool(settings.get("addPortToTheEyrie", False)),
        )
        observation["game"]["round"] = game.get("turn")
        observation["game"]["victoryPointsToWin"] = game.get(
            "victoryPointsCountNeededToWin"
        )
        observation["game"]["maxRounds"] = game.get("maxTurns")
        observation["you"].update(
            {
                "powerTokens": (house or {}).get("powerTokens"),
                "supply": (house or {}).get("supplyLevel"),
                "currentVictoryPoints": (house or {}).get("currentVictoryPoints"),
                "controlledLandAreas": (house or {}).get(
                    "controlledLandAreaCount"
                ),
                "controlledCastleAreas": (house or {}).get(
                    "controlledCastleAreaCount"
                ),
                "controlledSupplyIcons": (house or {}).get(
                    "controlledSupplyIcons"
                ),
                "controlledRegions": (house or {}).get("controlledRegionIds", []),
                "availableHouseCards": [
                    {
                        "id": card.get("id"),
                        "name": card.get("name"),
                        "strength": card.get("combatStrength"),
                        "swords": card.get("swordIcons", 0),
                        "towers": card.get("towerIcons", 0),
                        "ability": card.get("abilityId"),
                    }
                    for _, card in (house or {}).get("houseCards", [])
                    if card.get("state") == 0 and not card.get("disabled", False)
                ],
            }
        )
        observation["houses"] = [
            {
                "id": candidate.get("id"),
                "name": candidate.get("name"),
                "powerTokens": candidate.get("powerTokens"),
                "supply": candidate.get("supplyLevel"),
                "currentVictoryPoints": candidate.get("currentVictoryPoints"),
                "controlledLandAreas": candidate.get("controlledLandAreaCount"),
                "controlledCastleAreas": candidate.get(
                    "controlledCastleAreaCount"
                ),
                "controlledSupplyIcons": candidate.get("controlledSupplyIcons"),
                "controlledRegions": candidate.get("controlledRegionIds", []),
            }
            for candidate in game.get("houses", [])
        ]
        observation["tracks"] = {
            "ironThrone": game.get("ironThroneTrack", []),
            "fiefdoms": game.get("fiefdomsTrack", []),
            "kingsCourt": game.get("kingsCourtTrack", []),
        }
        observation["board"] = [
            {
                "id": region.get("id"),
                "controlPowerToken": region.get("controlPowerToken"),
                "garrison": region.get("garrison", 0),
                "units": region.get("units", []),
            }
            for region in game.get("world", {}).get("regions", [])
            if region.get("units")
            or region.get("garrison")
            or region.get("controlPowerToken")
        ]
        guidance = _action_guidance(context, observation["map"])
        if guidance:
            observation["actionGuidance"] = guidance
    return observation


def _action_guidance(
    context: HarnessContext, map_reference: dict[str, Any]
) -> dict[str, Any] | None:
    """Compute obvious legal IDs omitted by several upstream leaf serializers."""

    if context.ingame is None or context.game is None or context.house_id is None:
        return None
    leaf_type = (context.leaf or {}).get("type")
    order_ids: set[int]
    kind: str
    if leaf_type in {"resolve-march-order", "resolve-single-march"}:
        order_ids, kind = {1, 2, 3}, "march"
    elif leaf_type in {"resolve-raid-order", "resolve-single-raid"}:
        order_ids, kind = {13, 14, 15}, "raid"
    elif leaf_type in {
        "resolve-consolidate-power",
        "resolve-single-consolidate-power",
    }:
        order_ids, kind = {10, 11, 12}, "consolidate-power"
    elif leaf_type == "player-mustering":
        map_regions = {region["id"]: region for region in map_reference["regions"]}
        regions = context.game.get("world", {}).get("regions", [])
        controlled = []
        for region in regions:
            region_id = region.get("id")
            static = map_regions.get(region_id, {})
            if not static.get("castleLevel"):
                continue
            owns_units = any(
                unit.get("allegiance") == context.house_id
                for unit in region.get("units", [])
            )
            if not owns_units and region.get("controlPowerToken") != context.house_id:
                continue
            controlled.append(
                {
                    "regionId": region_id,
                    "musteringPoints": static["castleLevel"],
                    "units": region.get("units", []),
                    "adjacentSeaRegions": [
                        neighbour_id
                        for neighbour_id in static.get("neighbours", [])
                        if map_regions.get(neighbour_id, {}).get("type") == "sea"
                        and next(
                            (
                                candidate.get("garrison", 0)
                                for candidate in regions
                                if candidate.get("id") == neighbour_id
                            ),
                            0,
                        )
                        < 1000
                    ],
                }
            )
        return {
            "decision": "mustering",
            "controlledCastles": controlled,
            "unitCosts": {
                "footman": 1,
                "ship": 1,
                "knight": 2,
                "siege-engine": 2,
                "footmanUpgradeToKnightOrSiege": 1,
            },
            "safePass": "Call skip_mustering to submit no recruits.",
        }
    else:
        return None

    regions = {
        region["id"]: region
        for region in context.game.get("world", {}).get("regions", [])
    }
    map_regions = {region["id"]: region for region in map_reference["regions"]}
    legal_regions = []
    for region_id, order_id in context.ingame.get("ordersOnBoard", []):
        if order_id not in order_ids:
            continue
        region = regions.get(region_id, {})
        units = [
            unit
            for unit in region.get("units", [])
            if unit.get("allegiance") == context.house_id
        ]
        controls_region = (
            bool(units) or region.get("controlPowerToken") == context.house_id
        )
        if not controls_region:
            continue
        item: dict[str, Any] = {
            "regionId": region_id,
            "orderId": order_id,
            "order": ORDER_LEGEND[order_id],
            "unitIds": [unit.get("id") for unit in units],
        }
        if kind in {"march", "raid"}:
            item["adjacentRegions"] = [
                {
                    "regionId": neighbour_id,
                    "type": map_regions.get(neighbour_id, {}).get("type"),
                    "garrison": regions.get(neighbour_id, {}).get("garrison", 0),
                    "controller": regions.get(neighbour_id, {}).get(
                        "controlPowerToken"
                    ),
                }
                for neighbour_id in map_regions.get(region_id, {}).get("neighbours", [])
                if regions.get(neighbour_id, {}).get("garrison", 0) < 1000
            ]
        legal_regions.append(item)
    guidance: dict[str, Any] = {"decision": kind, "legalOrderRegions": legal_regions}
    if kind == "march":
        guidance["safePass"] = (
            "To discard a March order without moving, call resolve_march with a legal "
            "starting_region_id, moves=[], and leave_power_token=false."
        )
    elif kind == "raid":
        guidance["safePass"] = (
            "To discard a Raid order, call resolve_raid with a legal order_region_id "
            "and target_region_id=null."
        )
    return guidance


def _sanitize_event(event: dict[str, Any]) -> dict[str, Any]:
    if event.get("type") == "add-game-log":
        data = event.get("data") or {}
        if data.get("type") == "orders-revealed":
            orders = [
                {
                    "regionId": region.get("id"),
                    "order": (region.get("order") or {}).get("type"),
                }
                for region in data.get("worldState", [])
                if region.get("order")
            ]
            return {
                "type": "game-log",
                "event": "orders-revealed",
                "orders": orders,
            }
        return {
            "type": "game-log",
            "event": data.get("type", "unknown"),
            "details": {
                key: value
                for key, value in data.items()
                if key not in {"type", "worldState", "gameSnapshot"}
            },
        }
    allowed = {
        "type",
        "houseId",
        "supportedHouseId",
        "userId",
        "region",
        "regionId",
        "order",
        "value",
        "newTurn",
        "winner",
    }
    return {key: value for key, value in event.items() if key in allowed}


def is_waiting_for_player(context: HarnessContext) -> bool:
    if context.ingame is None:
        return False
    if _completed_simultaneous_decision(context):
        return False
    waited_user_ids = context.ingame.get("waitedForUserIds")
    if isinstance(waited_user_ids, list):
        return context.user_id in {str(user_id) for user_id in waited_user_ids}
    player = next(
        (
            item
            for item in context.ingame.get("players", [])
            if str(item.get("userId")) == context.user_id
        ),
        None,
    )
    waited_for = (player or {}).get("waitedForData")
    return bool(
        waited_for
        and not waited_for.get("handled", False)
        and waited_for.get("leafStateId") == context.snapshot.get("leafStateId")
    )


def _completed_simultaneous_decision(context: HarnessContext) -> bool:
    """Detect private submissions in states whose server wait-set stays broad."""

    if context.house_id is None:
        return False
    bidding = find_state(context.path, "bidding")
    if bidding is not None:
        own_bid = next(
            (
                value
                for house_id, value in bidding.get("bids", [])
                if house_id == context.house_id
            ),
            -1,
        )
        if own_bid is not None and own_bid >= 0:
            return True
    place_orders = find_state(context.path, "place-orders")
    if place_orders is not None and context.house_id in place_orders.get(
        "readyHouses", []
    ):
        return True
    choose_card = find_state(context.path, "choose-house-card")
    if choose_card is not None:
        own_card = next(
            (
                card_id
                for house_id, card_id in choose_card.get("houseCards", [])
                if house_id == context.house_id
            ),
            None,
        )
        if own_card:
            return True
    for state_type in (
        "select-objectives",
        "choose-initial-objectives",
        "score-objectives",
        "score-other-objectives",
        "agree-on-game-start",
        "draft-map",
    ):
        state = find_state(context.path, state_type)
        if state is not None and context.house_id in state.get("readyHouses", []):
            return True
    return False


def _redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]"
            if key in {"authToken", "password"}
            else _redact_secrets(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_redact_secrets(item) for item in value]
    return value
