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
            "players": [{"userId": "2", "houseId": "stark"}],
            "game": {
                "turn": 1,
                "houses": [
                    {
                        "id": "stark",
                        "name": "Stark",
                        "powerTokens": 5,
                        "supplyLevel": 2,
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
            },
            "childGameState": {
                "type": "planning",
                "placedOrders": [],
                "childGameState": {"type": "place-orders", "readyHouses": []},
            },
        },
    }
