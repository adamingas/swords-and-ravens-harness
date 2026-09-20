import copy
import json

from raven_harness.harness.observation import build_context, build_observation

from conftest import planning_snapshot


def test_observation_exposes_public_card_status_and_revealed_orders() -> None:
    snapshot = copy.deepcopy(planning_snapshot())
    ingame = snapshot["childGameState"]
    game = ingame["game"]
    game["houses"][0]["houseCards"] = [
        [
            "available-stark-card",
            {
                "id": "available-stark-card",
                "name": "Available Stark Card",
                "combatStrength": 3,
                "abilityId": "public-ability",
                "state": 0,
                "houseId": "stark",
            },
        ],
        [
            "used-stark-card",
            {
                "id": "used-stark-card",
                "name": "Used Stark Card",
                "combatStrength": 4,
                "state": 1,
                "houseId": "stark",
            },
        ],
    ]
    game["houses"].append(
        {
            "id": "lannister",
            "name": "Lannister",
            "powerTokens": 4,
            "supplyLevel": 2,
            "currentVictoryPoints": 1,
            "controlledLandAreaCount": 1,
            "controlledCastleAreaCount": 0,
            "controlledSupplyIcons": 0,
            "controlledRegionIds": ["stoney-sept"],
            "houseCards": [
                [
                    "available-lannister-card",
                    {
                        "id": "available-lannister-card",
                        "name": "Available Lannister Card",
                        "combatStrength": 2,
                        "swordIcons": 1,
                        "state": 0,
                        "houseId": "lannister",
                    },
                ],
                [
                    "used-private-identity",
                    {
                        "id": "used-private-identity",
                        "name": "Used Private Identity",
                        "combatStrength": 4,
                        "state": 1,
                        "houseId": "lannister",
                    },
                ],
                [
                    "disabled-lannister-card",
                    {
                        "id": "disabled-lannister-card",
                        "name": "Disabled Lannister Card",
                        "combatStrength": 1,
                        "state": 0,
                        "disabled": True,
                        "houseId": "lannister",
                    },
                ],
            ],
            "laterHouseCards": [["private-future-card", {"id": "private-future-card"}]],
            "secretObjectives": ["private-objective"],
        }
    )
    game["world"]["regions"].append(
        {
            "id": "stoney-sept",
            "units": [
                {
                    "id": 3,
                    "type": "footman",
                    "allegiance": "lannister",
                    "wounded": False,
                }
            ],
        }
    )
    ingame["ordersOnBoard"] = [["winterfell", 3], ["stoney-sept", 7]]
    ingame["childGameState"] = {"type": "resolve-march-order"}

    observation = build_observation(build_context(snapshot, "2"))

    assert observation["houseCardStatus"] == [
        {
            "houseId": "stark",
            "houseName": "Stark",
            "detailsVisible": True,
            "totalCount": 2,
            "availableCount": 1,
            "usedCount": 1,
            "disabledCount": 0,
            "availableCards": [
                {
                    "id": "available-stark-card",
                    "name": "Available Stark Card",
                    "strength": 3,
                    "swords": 0,
                    "towers": 0,
                    "ability": "public-ability",
                }
            ],
        },
        {
            "houseId": "lannister",
            "houseName": "Lannister",
            "detailsVisible": True,
            "totalCount": 3,
            "availableCount": 1,
            "usedCount": 1,
            "disabledCount": 1,
            "availableCards": [
                {
                    "id": "available-lannister-card",
                    "name": "Available Lannister Card",
                    "strength": 2,
                    "swords": 1,
                    "towers": 0,
                    "ability": None,
                }
            ],
        },
    ]
    assert observation["revealedOrders"] == [
        {
            "regionId": "winterfell",
            "regionName": "Winterfell",
            "orderId": 3,
            "order": "March +1",
        },
        {
            "regionId": "stoney-sept",
            "regionName": "Stoney Sept",
            "orderId": 7,
            "order": "Support +0",
        },
    ]
    board_by_id = {region["id"]: region for region in observation["board"]}
    assert board_by_id["winterfell"]["revealedOrder"]["order"] == "March +1"
    assert board_by_id["stoney-sept"]["revealedOrder"]["order"] == "Support +0"
    serialized = json.dumps(observation)
    assert "used-private-identity" not in serialized
    assert "private-future-card" not in serialized
    assert "private-objective" not in serialized


def test_bidding_observation_names_track_and_explains_hidden_bids() -> None:
    snapshot = copy.deepcopy(planning_snapshot())
    snapshot["childGameState"]["childGameState"] = {
        "type": "westeros",
        "childGameState": {
            "type": "clash-of-kings",
            "currentTrackI": 1,
            "childGameState": {
                "type": "bidding",
                "participatingHouses": ["stark", "lannister"],
                "bids": [["lannister", -1]],
            },
        },
    }

    pending = build_observation(build_context(snapshot, "2"))["pendingDecision"]

    assert pending["currentTrack"]["name"] == "Fiefdoms"
    assert "wins a tied combat" in pending["currentTrack"]["meaning"]
    assert "does not mean zero" in pending["bidFieldMeaning"]


def test_observation_does_not_label_private_planning_drafts_as_revealed() -> None:
    snapshot = copy.deepcopy(planning_snapshot())
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = []
    ingame["childGameState"]["placedOrders"] = [
        ["winterfell", 3],
        ["stoney-sept", None],
    ]

    observation = build_observation(build_context(snapshot, "2"))

    assert observation["revealedOrders"] == []
    assert all(region["revealedOrder"] is None for region in observation["board"])
