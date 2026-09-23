from typing import Any

from raven_harness.config import Settings
from raven_harness.harness.configure import create_game_harness


def make_harness(
    store,
    *,
    api_key="test-key",
    base_url="https://api.test/v1",
    rulebook=None,
    provider_blocklist=None,
    max_output_tokens=None,
    mode="structured",
    max_turns=20,
):
    """Exercise the production composition with explicit, offline test settings."""
    router = provider_blocklist is not None
    return create_game_harness(
        Settings(
            openai_api_key="" if router else api_key,
            openai_base_url=base_url,
            openrouter_token=api_key if router else "",
            openrouter_base_url=base_url,
            openrouter_provider_blocklist=",".join(provider_blocklist or []),
            harness_mode=mode,
            harness_max_turns=max_turns,
            model_max_output_tokens=max_output_tokens,
            _env_file=None,
        ),
        store,
        rulebook=rulebook,
    )


def lobby_snapshot() -> dict[str, Any]:
    return {
        "id": "1",
        "name": "Test game",
        "ownerUserId": "1",
        "leafStateId": "leaf-1",
        "gameSettings": {
            "setupId": "base-game",
            "playerCount": 6,
            "pbem": True,
        },
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
        "gameSettings": {
            "setupId": "base-game",
            "playerCount": 6,
            "pbem": True,
        },
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
