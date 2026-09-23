import json
from pathlib import Path
import select
import subprocess

import pytest

from raven_harness.harness.observation import build_context, build_observation
from raven_harness.harness.model_observation import compact_observation
from raven_harness.harness.tactical_observation import (
    combat_components, supportable_battlefields,
)
from conftest import planning_snapshot


def unit(uid, kind, house="stark", wounded=False):
    return {"id": uid, "type": kind, "allegiance": house, "wounded": wounded}


def combat_snapshot():
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    game = ingame["game"]
    game["houses"].append({"id": "lannister", "houseCards": []})
    game["fiefdomsTrack"] = ["lannister", "stark"]
    game["valyrianSteelBladeUsed"] = True
    game["world"]["regions"] = [
        {"id": "moat-cailin", "units": [unit(1, "knight"), unit(2, "siege-engine"), unit(3, "knight")]},
        {"id": "the-eyrie", "garrison": 2, "units": [unit(4, "footman", "lannister")]},
        {"id": "the-narrow-sea", "units": [unit(5, "ship"), unit(6, "ship", wounded=True)]},
        {"id": "the-shivering-sea", "units": [unit(7, "ship")]},
    ]
    ingame["ordersOnBoard"] = [["moat-cailin", 3], ["the-eyrie", 6], ["the-narrow-sea", 9], ["the-shivering-sea", 7]]
    ingame["childGameState"] = {"type": "action", "childGameState": {
        "type": "combat", "attackerId": "stark", "defenderId": "lannister", "order": 3,
        "houseCombatDatas": [["stark", {"army": [1, 2], "regionId": "moat-cailin", "houseCardId": None}],
                            ["lannister", {"army": [4], "regionId": "the-eyrie", "houseCardId": None}]],
        "supporters": [["stark", "stark"]], "houseCardModifiers": [],
        "childGameState": {"type": "choose-house-card", "houseCards": []},
    }}
    return snapshot


@pytest.fixture(scope="module")
def server():
    directory = Path(__file__).resolve().parents[1] / "swords-and-ravens/agot-bg-game-server"
    binary = directory / "node_modules/.bin/ts-node"
    if not binary.is_file():
        pytest.skip("Upstream Node dependencies required")
    process = subprocess.Popen(
        [str(binary), "--transpile-only", "--project", str(directory / "tsconfig.json"),
         str(Path(__file__).with_name("server_combat.ts"))],
        cwd=directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )

    def query(snapshot, **kwargs):
        process.stdin.write(json.dumps({"snapshot": snapshot, **kwargs}) + "\n")
        process.stdin.flush()
        assert select.select([process.stdout], [], [], 20)[0]
        result = json.loads(process.stdout.readline())
        assert "error" not in result, result
        return result

    yield query
    process.stdin.close()
    process.wait(timeout=10)


def test_participants_orders_wounded_support_and_garrison_match_server(server):
    snapshot = combat_snapshot()
    context = build_context(snapshot, "2")
    actual = combat_components(context)
    engine = server(snapshot)
    for role, expected in zip(("attacker", "defender"), engine["sides"], strict=True):
        side = actual[role]
        assert side["armyStrength"] == expected["army"]
        assert side["orderBonus"] == expected["order"]
        assert side["garrison"] == expected["garrison"]
        assert sum(s["strength"] for s in side["declaredSupport"]) == expected["support"]
        assert side["subtotalBeforeCards"] == expected["total"]
        assert side["revealedCardId"] is None
    assert actual["attacker"]["subtotalBeforeCards"] == 9
    assert actual["defender"]["subtotalBeforeCards"] == 5
    assert actual["tieWinnerBeforeAbilities"] == "lannister"
    assert actual["blade"]["usedThisRound"] is True
    compact = compact_observation(build_observation(context), context)
    assert compact["combat"] == actual
    assert "houseCombatDatas" not in compact["combat"]


def test_support_geometry_matches_upstream_for_every_area(server):
    snapshot = combat_snapshot()
    context = build_context(snapshot, "2")
    from raven_harness.harness.legal import _regions
    _, static = _regions(context)
    # Every possible source carries support, testing the complete terrain graph.
    orders = [[area, 7] for area in static]
    for battlefield in static:
        expected = server(snapshot, target=battlefield, orders=orders)["supportRegions"]
        actual = [area for area in static if battlefield in supportable_battlefields(context, area)]
        assert sorted(actual) == sorted(expected), battlefield


def test_pending_support_is_not_counted_and_missing_army_is_not_zero():
    snapshot = combat_snapshot()
    context = build_context(snapshot, "2")
    context.combat["supporters"] = []
    actual = combat_components(context)
    assert actual["attacker"]["subtotalBeforeCards"] == 7
    assert actual["supportOrdersAdjacentToBattlefield"][0]["declaration"] == "pending"
    context.combat["houseCombatDatas"][0][1]["army"].append(999)
    assert combat_components(context) is None


def test_blocked_support_geometry_and_variant_fallback():
    snapshot = combat_snapshot()
    context = build_context(snapshot, "2")
    context.game["world"]["regions"][1]["garrison"] = 1000
    assert "the-eyrie" not in supportable_battlefields(context, "the-narrow-sea")
    snapshot["gameSettings"]["vassals"] = True
    result = compact_observation(build_observation(context), context)
    assert "houseCombatDatas" in result["combat"]
