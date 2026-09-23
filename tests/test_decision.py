import json

import pytest

from raven_harness.harness.actions import HarnessRunContext, available_tools
from raven_harness.harness.decision import build_decision_contract
from raven_harness.harness.decision_briefing import build_decision_briefing
from raven_harness.harness.map_tools import check_neighbours, neighbouring_areas
from raven_harness.harness.observation import build_context, build_observation

from conftest import planning_snapshot


def selection_snapshot(effect="mammoth-riders-wildling-victory", count=2):
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["game"]["world"]["regions"] = [
        {
            "id": "winterfell",
            "units": [
                {"id": number, "type": kind, "allegiance": "stark", "wounded": False}
                for number, kind in [(1, "footman"), (2, "knight"), (3, "knight")]
            ],
        }
    ]
    ingame["childGameState"] = {
        "type": "westeros",
        "childGameState": {
            "type": effect,
            "childGameState": {
                "type": "select-units",
                "house": "stark",
                "possibleUnits": [1, 2, 3],
                "count": count,
                "canBeSkipped": False,
                "selectedUnitsMustBeOfSameRegion": False,
            },
        },
    }
    return snapshot


def march_snapshot(single_unit=False):
    snapshot = selection_snapshot()
    ingame = snapshot["childGameState"]
    ingame["game"]["world"]["regions"][0]["units"] = [
        {"id": number, "type": "knight", "allegiance": "stark", "wounded": False}
        for number in ([1] if single_unit else [1, 2])
    ]
    ingame["ordersOnBoard"] = [["winterfell", 2]]
    ingame["childGameState"] = {
        "type": "action",
        "childGameState": {
            "type": "resolve-single-march",
            "houseId": "stark",
            "supportersAgainstNeutralForce": None,
        },
    }
    return snapshot


def contract_for(snapshot):
    context = build_context(snapshot, "2")
    return build_decision_contract(context, available_tools(context))


def action(**values):
    return {
        **values,
        "strategic_handoff": "Preserve the current plan after this action.",
    }


class Client:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.recent_events = []
        self.connection_generation = 1
        self.sent = []

    async def send(self, message, **kwargs):
        assert kwargs["expected_generation"] == self.connection_generation
        self.sent.append(message)

    async def sync_snapshot(self, **kwargs):
        self.snapshot["leafStateId"] = "after-accepted-action"
        return self.snapshot


def test_destruction_briefing_states_the_penalty_and_what_selection_does():
    snapshot = selection_snapshot()
    context = build_context(snapshot, "2")
    contract = contract_for(snapshot)
    briefing = build_decision_briefing(context, contract, [check_neighbours])
    assert "Mammoth Riders" in briefing
    assert "Selected units are removed from the board" in briefing
    assert "Choose exactly 2 distinct units" in briefing
    assert "not limited to one tool call" in briefing
    assert "required output schema" in briefing
    schema = contract.output_schema.json_schema()
    assert set(schema["properties"]) == {"unit_ids_to_destroy", "strategic_handoff"}
    field = schema["properties"]["unit_ids_to_destroy"]
    assert field["items"]["enum"] == [1, 2, 3]
    assert field["minItems"] == field["maxItems"] == 2


def test_enemy_destruction_does_not_advise_preserving_the_enemy_army():
    snapshot = selection_snapshot("ser-ilyn-payne-asos-ability", count=1)
    for unit in snapshot["childGameState"]["game"]["world"]["regions"][0]["units"]:
        unit["allegiance"] = "lannister"
    context = build_context(snapshot, "2")
    briefing = build_decision_briefing(context, contract_for(snapshot), [])
    assert "enemy pieces to destroy" in briefing
    assert "lannister knight" in briefing
    assert "preserve your ability" not in briefing


def test_march_explains_home_control_and_empty_castle_capture():
    snapshot = march_snapshot(single_unit=True)
    context = build_context(snapshot, "2")
    briefing = build_decision_briefing(
        context, contract_for(snapshot), [check_neighbours]
    )
    assert "Winterfell currently contributes 1 castle area" in briefing
    assert "home symbol keeps this area yours when you leave it empty" in briefing
    assert "White Harbor (capture gains one castle area without combat)" in briefing
    assert "Castle Black (capture" not in briefing
    from raven_harness.harness.legal import legal_march_options

    source = legal_march_options(context)[0]
    assert source["castleAreasLostIfEmptiedWithoutToken"] == 0
    targets = {target["regionId"]: target for target in source["reachableRegions"]}
    assert targets["moat-cailin"]["castleAreasGainedIfCaptured"] == 1
    assert targets["castle-black"]["castleAreasGainedIfCaptured"] == 0


@pytest.mark.parametrize(
    "effect", ["crow-killers-nights-watch-victory", "renly-baratheon-ability"]
)
def test_upgrade_is_not_mislabelled_as_destruction(effect):
    contract = contract_for(selection_snapshot(effect))
    assert set(contract.output_schema.json_schema()["properties"]) == {
        "footman_ids_to_upgrade",
        "strategic_handoff",
    }
    assert "removed from the board" not in contract.actions[0].description


@pytest.mark.parametrize(
    "step,field", [(0, "knight_ids_to_replace"), (1, "unit_ids_to_destroy")]
)
def test_crow_killers_distinguishes_destruction_from_downgrade(step, field):
    snapshot = selection_snapshot("crow-killers-wildling-victory")
    snapshot["childGameState"]["childGameState"]["childGameState"]["step"] = step
    contract = contract_for(snapshot)
    assert set(contract.output_schema.json_schema()["properties"]) == {
        field,
        "strategic_handoff",
    }
    assert ("removed from the board" in contract.actions[0].description) == (step == 1)


@pytest.mark.asyncio
async def test_fully_determined_selection_requires_explicit_unit_ids():
    snapshot = selection_snapshot(count=3)
    client = Client(snapshot)
    contract = contract_for(snapshot)
    assert set(contract.output_schema.json_schema()["properties"]) == {
        "unit_ids_to_destroy",
        "strategic_handoff",
    }
    assert client.sent == []
    context = HarnessRunContext(client=client, user_id="2")
    with pytest.raises(ValueError, match="unit_ids_to_destroy"):
        await contract.execute(context, action())
    with pytest.raises(ValueError):
        await contract.execute(context, action(unit_ids_to_destroy=[1, 1, 2]))
    assert client.sent == []
    await contract.execute(context, action(unit_ids_to_destroy=[1, 2, 3]))
    assert context.action_taken.name == "select_units"
    assert client.sent == [
        {"type": "select-units", "units": [["winterfell", [1, 2, 3]]]}
    ]


@pytest.mark.asyncio
async def test_march_requires_explicit_source_and_token_flag_and_retains_splits():
    snapshot = march_snapshot()
    contract = contract_for(snapshot)
    assert set(contract.output_schema.json_schema()["properties"]) == {
        "moves",
        "starting_region_id",
        "leave_power_token",
        "strategic_handoff",
    }
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id="2")
    await contract.execute(
        context,
        action(
            starting_region_id="winterfell",
            leave_power_token=False,
            moves=[
                {"destination_region_id": "white-harbor", "unit_ids": [1]},
                {"destination_region_id": "moat-cailin", "unit_ids": [2]},
            ],
        ),
    )
    assert client.sent == [
        {
            "type": "resolve-march-order",
            "startingRegionId": "winterfell",
            "moves": [["white-harbor", [1]], ["moat-cailin", [2]]],
            "leavePowerToken": False,
        }
    ]


@pytest.mark.asyncio
async def test_single_movable_unit_is_explicit_without_removing_the_option_to_pass():
    snapshot = march_snapshot(single_unit=True)
    contract = contract_for(snapshot)
    fields = contract.output_schema.json_schema()["properties"]["moves"]["items"][
        "properties"
    ]
    assert set(fields) == {"destination_region_id", "unit_ids"}
    client = Client(snapshot)
    await contract.execute(
        HarnessRunContext(client=client, user_id="2"),
        action(starting_region_id="winterfell", leave_power_token=False, moves=[]),
    )
    assert client.sent[0]["moves"] == []


@pytest.mark.asyncio
async def test_three_player_blocked_castle_is_not_offered_or_submitted():
    # Reproduce the OSS round-three Dragonstone -> Storm's End failure.
    snapshot = march_snapshot()
    snapshot["gameSettings"]["playerCount"] = 3
    ingame = snapshot["childGameState"]
    ingame["players"][0]["houseId"] = "baratheon"
    ingame["game"]["houses"][0]["id"] = "baratheon"
    ingame["childGameState"]["childGameState"]["houseId"] = "baratheon"
    ingame["ordersOnBoard"] = [["dragonstone", 3], ["shipbreaker-bay", 7]]
    ingame["game"]["world"]["regions"] = [
        {
            "id": "dragonstone",
            "units": [
                {"id": 9, "type": "footman", "allegiance": "baratheon"},
                {"id": 10, "type": "knight", "allegiance": "baratheon"},
            ],
        },
        {
            "id": "shipbreaker-bay",
            "units": [
                {"id": 11, "type": "ship", "allegiance": "baratheon"},
                {"id": 12, "type": "ship", "allegiance": "baratheon"},
            ],
        },
        {"id": "storms-end", "garrison": 1000, "units": []},
        {"id": "kingswood", "controlPowerToken": "baratheon", "units": []},
        {"id": "crackclaw-point", "controlPowerToken": "baratheon", "units": []},
    ]
    context = build_context(snapshot, "2")
    observation = build_observation(context)
    targets = observation["actionGuidance"]["legalOrderRegions"][0]["reachableRegions"]
    assert {target["regionId"] for target in targets} == {
        "crackclaw-point",
        "kingswood",
    }
    board = {region["id"]: region for region in observation["board"]}
    assert board["storms-end"]["isBlocked"] is True
    assert board["dragonstone"]["isBlocked"] is False
    neighbours = {
        region["id"]: region
        for region in neighbouring_areas(context, "shipbreaker-bay")
    }
    assert neighbours["storms-end"]["isBlocked"] is True
    from raven_harness.harness.legal import neutral_force_attack_is_legal

    assert not neutral_force_attack_is_legal(
        context, "dragonstone", "storms-end", [9, 10]
    )
    contract = contract_for(snapshot)
    destinations = contract.output_schema.json_schema()["properties"]["moves"]["items"][
        "properties"
    ]["destination_region_id"]["enum"]
    assert destinations == ["crackclaw-point", "kingswood"]
    assert "Storm's End (" not in build_decision_briefing(context, contract, [])
    client = Client(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    invalid = json.dumps(
        action(
            starting_region_id="dragonstone",
            leave_power_token=False,
            moves=[{"destination_region_id": "storms-end", "unit_ids": [9, 10]}],
        )
    )
    with pytest.raises(ValueError, match="storms-end"):
        await contract.execute(run_context, json.loads(invalid))
    assert client.sent == [] and run_context.action_taken is None
    await contract.execute(
        run_context,
        action(
            starting_region_id="dragonstone",
            leave_power_token=False,
            moves=[{"destination_region_id": "crackclaw-point", "unit_ids": [9, 10]}],
        ),
    )
    assert client.sent[0]["moves"] == [["crackclaw-point", [9, 10]]]


@pytest.mark.asyncio
async def test_blocked_direct_destinations_leave_only_a_valid_pass_contract():
    from raven_harness.harness.legal import _regions

    snapshot = march_snapshot()
    _, static = _regions(build_context(snapshot, "2"))
    snapshot["childGameState"]["game"]["world"]["regions"].extend(
        {"id": area, "garrison": 1000, "units": []}
        for area in static["winterfell"]["neighbours"]
    )
    contract = contract_for(snapshot)
    assert set(contract.output_schema.json_schema()["properties"]) == {
        "starting_region_id",
        "moves",
        "leave_power_token",
        "strategic_handoff",
    }
    assert contract.actions[0].argument_schema["properties"]["moves"]["maxItems"] == 0
    client = Client(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    with pytest.raises(ValueError):
        await contract.execute(
            run_context,
            action(
                starting_region_id="winterfell",
                leave_power_token=False,
                moves=[{"destination_region_id": "moat-cailin", "unit_ids": [1]}],
            ),
        )
    assert client.sent == []
    await contract.execute(
        run_context,
        action(starting_region_id="winterfell", leave_power_token=False, moves=[]),
    )
    assert client.sent[0]["moves"] == []


@pytest.mark.asyncio
async def test_invalid_and_duplicate_selections_never_reach_the_server():
    snapshot = selection_snapshot()
    contract = contract_for(snapshot)
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id="2")
    for answer in (
        {"unit_ids_to_destroy": [99, 2]},
        {"unit_ids_to_destroy": [1]},
        {"unit_ids": [1, 2]},
        {"unit_ids_to_destroy": [1, 1]},
    ):
        with pytest.raises(ValueError):
            await contract.execute(context, answer)
    assert client.sent == [] and context.action_taken is None


@pytest.mark.asyncio
async def test_stale_decision_never_reaches_the_server():
    snapshot = selection_snapshot()
    contract = contract_for(snapshot)
    client = Client(snapshot)
    snapshot["leafStateId"] = "different-decision"
    with pytest.raises(ValueError, match="decision changed"):
        await contract.execute(
            HarnessRunContext(client=client, user_id="2"),
            action(unit_ids_to_destroy=[1, 2]),
        )
    assert client.sent == []


@pytest.mark.asyncio
async def test_multiple_action_types_use_a_constrained_final_choice():
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {
        "type": "player-mustering",
        "house": "stark",
        "musteringType": 0,
    }
    contract = contract_for(snapshot)
    assert {action.name for action in contract.actions} == {
        "muster_units",
        "skip_mustering",
    }
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id="2")
    with pytest.raises(ValueError):
        await contract.execute(context, {"decision": {"action": "resolve_march"}})
    assert client.sent == []
    await contract.execute(
        context,
        action(decision={"action": "skip_mustering"}),
    )
    assert context.action_taken.name == "skip_mustering"
    assert client.sent == [{"type": "muster", "units": []}]
