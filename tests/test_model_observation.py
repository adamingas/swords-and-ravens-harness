from copy import deepcopy

from raven_harness.harness.model_observation import compact_observation
from raven_harness.harness.observation import build_context, build_observation

from conftest import planning_snapshot


def test_compact_board_keeps_control_empty_targets_blocking_and_visible_orders():
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = [["winterfell", 7]]
    ingame["game"]["world"]["regions"].extend([
        {"id": "moat-cailin", "units": [], "controlPowerToken": "stark"},
        {"id": "storms-end", "units": [], "garrison": 1000},
    ])
    context = build_context(snapshot, "2")
    full = build_observation(context)
    before = deepcopy(full)
    compact = compact_observation(full, context)
    assert full == before
    board = {region["id"]: region for region in compact["board"]}
    assert board["moat-cailin"]["controller"] == "stark"
    assert board["moat-cailin"]["castlePoints"] == 1
    assert board["seagard"]["controller"] is None
    assert board["winterfell"]["orderId"] == 7
    assert "storms-end" not in board
    assert "storms-end" in compact["blockedAreas"]
    assert "revealedOrders" not in compact
    assert compact["game"]["roundStage"] == "planning"


def test_combat_context_uses_only_player_visible_parent_and_preserves_hidden_cards():
    snapshot = planning_snapshot()
    combat = {
        "type": "combat", "attackerId": "stark", "defenderId": "lannister",
        "order": 3,
        "houseCombatDatas": [
            ["stark", {"army": [1], "regionId": "winterfell", "houseCardId": None}],
            ["lannister", {"army": [7], "regionId": "moat-cailin", "houseCardId": None}],
        ],
        "supporters": [["baratheon", "stark"]],
        "houseCardModifiers": [], "stats": [], "tidesOfBattleDeck": [],
        "childGameState": {"type": "choose-house-card", "houseCards": []},
    }
    snapshot["childGameState"]["childGameState"] = {
        "type": "action", "childGameState": combat,
    }
    context = build_context(snapshot, "2")
    result = compact_observation(build_observation(context), context)
    assert result["combat"]["houseCombatDatas"] == combat["houseCombatDatas"]
    assert result["combat"]["supporters"] == [["baratheon", "stark"]]
    assert "childGameState" not in result["combat"]
    assert "tidesOfBattleDeck" not in result["combat"]
    assert "combat" not in compact_observation(
        build_observation(build_context(planning_snapshot(), "2")),
        build_context(planning_snapshot(), "2"),
    )


def test_current_resources_and_plan_are_not_duplicated_as_stale_summaries():
    context = build_context(planning_snapshot(), "2")
    full = build_observation(context)
    full["strategicOverview"] = {"housePositions": ["old"]}
    full["strategicMemory"] = {
        "modelPlan": "Capture the next castle", "lessons": ["keep transport"],
        "decisionJournal": ["old plan"] * 12, "situationAssessment": "outdated",
    }
    result = compact_observation(full, context)
    assert "strategicOverview" not in result
    assert result["strategicMemory"] == {
        "modelPlan": "Capture the next castle", "lessons": ["keep transport"],
    }
    assert result["houses"][0]["powerTokens"] == 5
    assert result["supplyLimit"]["level"] == 2
    assert "availableHouseCards" not in result["you"]
