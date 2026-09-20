import copy

from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.card_tools import house_card_details

from conftest import planning_snapshot


class Client:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.recent_events = []
        self.connection_generation = 1


def test_house_card_lookup_returns_exact_printed_ability() -> None:
    snapshot = copy.deepcopy(planning_snapshot())
    snapshot["childGameState"]["game"]["houses"][0]["houseCards"] = [
        [
            "robb-stark",
            {
                "id": "robb-stark",
                "name": "Robb Stark",
                "houseId": "stark",
                "combatStrength": 3,
                "abilityId": "robb-stark",
                "state": 0,
            },
        ]
    ]
    context = HarnessRunContext(client=Client(snapshot), user_id="2")

    card = house_card_details(context, "Robb Stark")

    assert card["strength"] == 3
    assert card["available"] is True
    assert "choose the area to which your opponent" in card["abilityText"]
