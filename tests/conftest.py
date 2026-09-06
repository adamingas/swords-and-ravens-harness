from typing import Any


def lobby_snapshot() -> dict[str, Any]:
    return {
        "id": "1",
        "name": "Test game",
        "ownerUserId": "1",
        "leafStateId": "leaf-1",
        "gameSettings": {"playerCount": 3},
        "childGameState": {
            "type": "lobby",
            "players": [["baratheon", "1"]],
            "lobbyHouses": [
                {"id": "stark", "name": "Stark", "color": "#fff"},
                {"id": "baratheon", "name": "Baratheon", "color": "#000"},
                {"id": "lannister", "name": "Lannister", "color": "#f00"},
            ],
            "availableHouseIds": ["stark", "baratheon", "lannister"],
            "password": "",
            "readyUsers": None,
            "readyCheckWillTimeoutAt": None,
        },
    }


def planning_snapshot() -> dict[str, Any]:
    return {
        "id": "1",
        "name": "Test game",
        "ownerUserId": "1",
        "leafStateId": "leaf-2",
        "childGameState": {
            "type": "ingame",
            "waitedForUserIds": ["2"],
            "players": [{"userId": "2", "houseId": "stark"}],
            "game": {
                "turn": 1,
                "houses": [
                    {
                        "id": "stark",
                        "name": "Stark",
                        "powerTokens": 5,
                        "supplyLevel": 2,
                        "currentVictoryPoints": 1,
                        "controlledLandAreaCount": 2,
                        "controlledCastleAreaCount": 1,
                        "controlledSupplyIcons": 1,
                        "controlledRegionIds": ["winterfell", "white-harbor"],
                        "houseCards": [],
                    }
                ],
                "world": {
                    "regions": [
                        {
                            "id": "winterfell",
                            "units": [
                                {
                                    "id": 1,
                                    "type": "footman",
                                    "allegiance": "stark",
                                    "wounded": False,
                                }
                            ],
                        },
                        {
                            "id": "white-harbor",
                            "units": [
                                {
                                    "id": 2,
                                    "type": "ship",
                                    "allegiance": "stark",
                                    "wounded": False,
                                }
                            ],
                        },
                    ]
                },
                "ironThroneTrack": ["stark"],
                "fiefdomsTrack": ["stark"],
                "kingsCourtTrack": ["stark"],
                "victoryPointsCountNeededToWin": 7,
                "maxTurns": 10,
            },
            "childGameState": {
                "type": "planning",
                "placedOrders": [],
                "childGameState": {"type": "place-orders", "readyHouses": []},
            },
        },
    }
