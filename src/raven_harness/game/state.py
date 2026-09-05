from typing import Any

JsonObject = dict[str, Any]


def state_path(serialized_game: JsonObject) -> list[JsonObject]:
    path: list[JsonObject] = []
    state = serialized_game.get("childGameState")
    while isinstance(state, dict):
        path.append(state)
        state = state.get("childGameState")
    return path


def leaf_state(serialized_game: JsonObject) -> JsonObject | None:
    path = state_path(serialized_game)
    return path[-1] if path else None


def find_state(path: list[JsonObject], state_type: str) -> JsonObject | None:
    return next((state for state in path if state.get("type") == state_type), None)


def ingame_state(serialized_game: JsonObject) -> JsonObject | None:
    child = serialized_game.get("childGameState")
    return child if isinstance(child, dict) and child.get("type") == "ingame" else None


def player_house(serialized_game: JsonObject, user_id: str) -> str | None:
    ingame = ingame_state(serialized_game)
    if not ingame:
        return None
    player = next(
        (
            item
            for item in ingame.get("players", [])
            if str(item.get("userId")) == str(user_id)
        ),
        None,
    )
    return player.get("houseId") if player else None


def apply_server_message(serialized_game: JsonObject, message: JsonObject) -> None:
    message_type = message.get("type")
    if message_type == "game-state-change":
        _replace_state(
            serialized_game,
            int(message["level"]),
            message["serializedGameState"],
        )
        serialized_game["leafStateId"] = message["newLeafId"]
        ingame = ingame_state(serialized_game)
        if ingame is not None and isinstance(message.get("waitedForUserIds"), list):
            ingame["waitedForUserIds"] = message["waitedForUserIds"]
        return

    if message_type == "game-settings-changed":
        serialized_game["gameSettings"] = message["settings"]
        return

    path = state_path(serialized_game)
    leaf = path[-1] if path else None
    lobby = serialized_game.get("childGameState")
    lobby = lobby if isinstance(lobby, dict) and lobby.get("type") == "lobby" else None
    ingame = ingame_state(serialized_game)
    game = ingame.get("game", {}) if ingame else {}

    if message_type == "house-chosen" and lobby is not None:
        lobby["players"] = message["players"]
    elif message_type == "ready-check" and lobby is not None:
        lobby["readyUsers"] = message.get("readyUsers")
        lobby["readyCheckWillTimeoutAt"] = message.get("readyCheckWillTimeoutAt")
    elif message_type in {"player-ready", "player-unready"}:
        if ingame is not None and "waitedForUserIds" in ingame:
            waited_user_ids = {str(item) for item in ingame.get("waitedForUserIds", [])}
            user_id = str(message.get("userId"))
            if message_type == "player-ready":
                waited_user_ids.discard(user_id)
            else:
                waited_user_ids.add(user_id)
            ingame["waitedForUserIds"] = sorted(waited_user_ids)
        if lobby is not None and lobby.get("readyUsers") is not None:
            ready_users = lobby.setdefault("readyUsers", [])
            user_id = str(message.get("userId"))
            if message_type == "player-ready" and user_id not in ready_users:
                ready_users.append(user_id)
            elif message_type == "player-unready":
                lobby["readyUsers"] = [
                    str(item) for item in ready_users if str(item) != user_id
                ]
        elif leaf and ingame and leaf.get("type") == "place-orders":
            house_id = next(
                (
                    player.get("houseId")
                    for player in ingame.get("players", [])
                    if str(player.get("userId")) == str(message.get("userId"))
                ),
                None,
            )
            ready = leaf.setdefault("readyHouses", [])
            if message_type == "player-ready" and house_id and house_id not in ready:
                ready.append(house_id)
            elif message_type == "player-unready":
                leaf["readyHouses"] = [item for item in ready if item != house_id]
    elif message_type == "order-placed":
        planning = find_state(path, "planning")
        if planning:
            _upsert_pair(
                planning.setdefault("placedOrders", []),
                message["region"],
                message.get("order"),
            )
    elif message_type == "remove-placed-order":
        planning = find_state(path, "planning")
        if planning:
            planning["placedOrders"] = [
                pair
                for pair in planning.get("placedOrders", [])
                if pair[0] != message["regionId"]
            ]
    elif message_type == "bid-done" and leaf and leaf.get("type") == "bidding":
        _upsert_pair(
            leaf.setdefault("bids", []), message["houseId"], message.get("value")
        )
    elif (
        message_type == "house-card-chosen"
        and leaf
        and leaf.get("type") == "choose-house-card"
    ):
        _upsert_pair(
            leaf.setdefault("houseCards", []),
            message["houseId"],
            message.get("houseCardId"),
        )
    elif message_type == "support-declared":
        combat = find_state(path, "combat")
        if combat:
            _upsert_pair(
                combat.setdefault("supporters", []),
                message["houseId"],
                message.get("supportedHouseId"),
            )
    elif message_type == "change-power-token" and ingame:
        house = _find_house(game, message.get("houseId"))
        if house:
            house["powerTokens"] = message["powerTokenCount"]
    elif message_type == "update-waited-for-data" and ingame:
        player = next(
            (
                item
                for item in ingame.get("players", [])
                if str(item.get("userId")) == str(message.get("userId"))
            ),
            None,
        )
        if player is not None:
            if message.get("waitedForData") is None:
                player.pop("waitedForData", None)
            else:
                player["waitedForData"] = message["waitedForData"]
    elif message_type == "move-units" and ingame:
        source = _find_region(game, message.get("from"))
        target = _find_region(game, message.get("to"))
        if source is not None and target is not None:
            unit_ids = set(message.get("units", []))
            moved = [
                unit for unit in source.get("units", []) if unit.get("id") in unit_ids
            ]
            source["units"] = [
                unit
                for unit in source.get("units", [])
                if unit.get("id") not in unit_ids
            ]
            target.setdefault("units", []).extend(moved)
    elif message_type == "add-units" and ingame:
        region = _find_region(game, message.get("regionId"))
        if region is not None:
            existing_ids = {unit.get("id") for unit in region.get("units", [])}
            region.setdefault("units", []).extend(
                unit
                for unit in message.get("units", [])
                if unit.get("id") not in existing_ids
            )
    elif message_type == "remove-units" and ingame:
        region = _find_region(game, message.get("regionId"))
        if region is not None:
            removed = set(message.get("unitIds", []))
            region["units"] = [
                unit
                for unit in region.get("units", [])
                if unit.get("id") not in removed
            ]
    elif message_type == "units-wounded" and ingame:
        region = _find_region(game, message.get("regionId"))
        wounded = set(message.get("unitIds", []))
        if region is not None:
            for unit in region.get("units", []):
                if unit.get("id") in wounded:
                    unit["wounded"] = True
    elif message_type == "change-garrison" and ingame:
        region = _find_region(game, message.get("region"))
        if region is not None:
            region["garrison"] = message.get("newGarrison", 0)
    elif message_type == "change-control-power-token" and ingame:
        region = _find_region(game, message.get("regionId"))
        if region is not None:
            region["controlPowerToken"] = message.get("houseId")
    elif message_type == "supply-adjusted" and ingame:
        for house_id, supply in message.get("supplies", []):
            house = _find_house(game, house_id)
            if house is not None:
                house["supplyLevel"] = supply
    elif message_type == "change-tracker" and ingame:
        key = {0: "ironThroneTrack", 1: "fiefdomsTrack", 2: "kingsCourtTrack"}.get(
            message.get("trackerI")
        )
        if key:
            game[key] = message.get("tracker", [])
    elif message_type == "change-valyrian-steel-blade-use" and ingame:
        game["valyrianSteelBladeUsed"] = message.get("used", False)
    elif message_type == "change-wildling-strength" and ingame:
        game["wildlingStrength"] = message.get("wildlingStrength", 0)
    elif message_type == "new-turn" and ingame:
        game["turn"] = int(game.get("turn", 0)) + 1
    elif (
        message_type in {"action-phase-change-order", "raven-order-replaced"} and ingame
    ):
        region_id = message.get("region") or message.get("regionId")
        order_id = (
            message.get("order") if "order" in message else message.get("orderId")
        )
        _upsert_pair(ingame.setdefault("ordersOnBoard", []), region_id, order_id)
    elif message_type == "reveal-orders" and ingame:
        ingame["ordersOnBoard"] = message.get("orders", [])
    elif message_type == "remove-orders" and ingame:
        removed = set(message.get("regions", []))
        ingame["ordersOnBoard"] = [
            pair for pair in ingame.get("ordersOnBoard", []) if pair[0] not in removed
        ]
    elif message_type == "change-state-house-card" and ingame:
        house = _find_house(game, message.get("houseId"))
        card_ids = set(message.get("cardIds", []))
        if house is not None:
            for card_id, card in house.get("houseCards", []):
                if card_id in card_ids:
                    card["state"] = message.get("state")
    elif message_type in {"loyalty-token-gained", "loyalty-token-placed"} and ingame:
        region = _find_region(game, message.get("region"))
        if region is not None:
            region["loyaltyTokens"] = message.get("newLoyaltyTokenCount", 0)
    elif message_type == "update-max-turns" and ingame:
        game["maxTurns"] = message.get("maxTurns")


def _replace_state(
    serialized_game: JsonObject, level: int, replacement: JsonObject
) -> None:
    if level <= 0:
        serialized_game.clear()
        serialized_game.update(replacement)
        return
    parent = serialized_game
    for _ in range(1, level):
        parent = parent.get("childGameState")
        if not isinstance(parent, dict):
            raise ValueError(f"Invalid game-state-change level {level}")
    parent["childGameState"] = replacement


def _upsert_pair(pairs: list[list[Any]], key: Any, value: Any) -> None:
    pair = next((item for item in pairs if item[0] == key), None)
    if pair:
        pair[1] = value
    else:
        pairs.append([key, value])


def _find_region(game: JsonObject, region_id: Any) -> JsonObject | None:
    return next(
        (
            region
            for region in game.get("world", {}).get("regions", [])
            if region.get("id") == region_id
        ),
        None,
    )


def _find_house(game: JsonObject, house_id: Any) -> JsonObject | None:
    return next(
        (house for house in game.get("houses", []) if house.get("id") == house_id),
        None,
    )
