import asyncio
import json

import httpx
import pytest
from agents.tool_context import ToolContext

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.harness.actions import HarnessRunContext, available_tools
from raven_harness.harness.decision import build_decision_contract
from raven_harness.harness.decision_briefing import build_decision_briefing
from raven_harness.harness.map_tools import check_neighbours, neighbouring_areas
from raven_harness.harness.observation import build_context, build_observation
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.models.openai_agent import (
    ModelRunCancelled,
    OpenAIAgentRunner,
)
from raven_harness.schemas import AgentCreate

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
    if 'decision' in values:
        return {'decision': action(**values['decision'])}
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
    assert contract.submission_tool().name == "submit_action"
    briefing = build_decision_briefing(context, contract, [check_neighbours])
    assert "Mammoth Riders" in briefing
    assert "Selected units are removed from the board" in briefing
    assert "Choose exactly 2 distinct units" in briefing
    assert "not limited to one tool call" in briefing
    assert "you MUST call submit_action" in briefing
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
async def test_fully_determined_selection_is_bound_but_waits_for_final_submission():
    snapshot = selection_snapshot(count=3)
    client = Client(snapshot)
    contract = contract_for(snapshot)
    assert set(contract.output_schema.json_schema()["properties"]) == {
        "strategic_handoff"
    }
    assert client.sent == []
    context = HarnessRunContext(client=client, user_id="2")
    await contract.execute(context, action())
    assert context.action_taken.name == "select_units"
    assert client.sent == [
        {"type": "select-units", "units": [["winterfell", [1, 2, 3]]]}
    ]


@pytest.mark.asyncio
async def test_march_binds_source_and_token_flag_but_retains_splits():
    snapshot = march_snapshot()
    contract = contract_for(snapshot)
    assert contract.submission_tool().name == "submit_action"
    assert set(contract.output_schema.json_schema()["properties"]) == {
        "moves",
        "strategic_handoff",
    }
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id="2")
    await contract.execute(
        context,
        action(
            moves=[
                {"destination_region_id": "white-harbor", "unit_ids": [1]},
                {"destination_region_id": "moat-cailin", "unit_ids": [2]},
            ]
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
async def test_single_movable_unit_is_bound_without_removing_the_option_to_pass():
    snapshot = march_snapshot(single_unit=True)
    contract = contract_for(snapshot)
    fields = contract.output_schema.json_schema()["properties"]["moves"]["items"][
        "properties"
    ]
    assert set(fields) == {"destination_region_id", "unit_ids"}
    assert fields["unit_ids"]["items"]["enum"] == [1]
    client = Client(snapshot)
    await contract.execute(
        HarnessRunContext(client=client, user_id="2"), action(moves=[])
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
    tool = contract.submission_tool()
    destinations = tool.params_json_schema["properties"]["moves"]["items"][
        "properties"
    ]["destination_region_id"]["enum"]
    assert destinations == ["crackclaw-point", "kingswood"]
    assert "Storm's End (" not in build_decision_briefing(context, contract, [])
    client = Client(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    invalid = json.dumps(
        action(moves=[{"destination_region_id": "storms-end", "unit_ids": [9, 10]}])
    )
    rejected = json.loads(
        await tool.on_invoke_tool(
            ToolContext(
                context=run_context,
                tool_call_id="blocked",
                tool_name="submit_action",
                tool_arguments=invalid,
            ),
            invalid,
        )
    )
    assert rejected["accepted"] is False
    assert "storms-end" in rejected["error"]
    assert client.sent == [] and run_context.action_taken is None
    await contract.execute(
        run_context,
        action(
            moves=[{"destination_region_id": "crackclaw-point", "unit_ids": [9, 10]}]
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
    assert set(contract.submission_tool().params_json_schema["properties"]) == {
        "strategic_handoff"
    }
    assert contract.actions[0].argument_schema["properties"]["moves"]["maxItems"] == 0
    client = Client(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    with pytest.raises(ValueError):
        await contract.execute(
            run_context,
            action(moves=[{"destination_region_id": "moat-cailin", "unit_ids": [1]}]),
        )
    assert client.sent == []
    await contract.execute(run_context, action())
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


@pytest.mark.asyncio
@pytest.mark.parametrize("output_limit", [None, 40960])
@pytest.mark.parametrize("exploration_tool", ["check_neighbours", "reachable_areas"])
@pytest.mark.parametrize(
    "reject,cancel", [(False, False), (True, False), (False, True)]
)
async def test_actual_wire_explores_then_submits_through_one_action_tool(
    tmp_path, reject, cancel, exploration_tool, output_limit
):
    database = Database(tmp_path / "structured.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(name="Stark", model="test-model", user_id="2", auth_token="unused")
    )
    client = Client(selection_snapshot())
    runner = OpenAIAgentRunner(
        api_key="unused",
        base_url="https://api.test/v1",
        max_output_tokens=output_limit,
    )
    harness = StrategicHarness(runner, store)
    context = HarnessRunContext(client=client, user_id="2")
    requests = []

    def respond(request):
        body = json.loads(request.content)
        if output_limit is None:
            assert "max_output_tokens" not in body
        else:
            assert body["max_output_tokens"] == output_limit
        requests.append(body)
        assert body["tool_choice"] == "auto"
        current_user = next(
            item["content"] for item in body["input"] if item.get("role") == "user"
        )
        assert "You MUST call submit_action" in current_user
        assert {tool["name"] for tool in body.get("tools", [])} == {
            "check_neighbours",
            "reachable_areas",
            "inspect_house_card",
            "recall_game_state",
            "remember_strategy",
            "submit_action",
        }
        submission = next(
            tool for tool in body["tools"] if tool["name"] == "submit_action"
        )
        assert "unit_ids_to_destroy" in submission["parameters"]["properties"]
        assert body["instructions"] == requests[0]["instructions"]
        assert "`submit_action`" in body["instructions"]
        assert "Mammoth Riders imposes" not in body["instructions"]
        assert "Mammoth Riders imposes" in body["input"][0]["content"]
        assert client.sent == []
        if len(requests) >= 2:
            exploration_output = json.loads(next(
                item["output"] for item in body["input"]
                if item.get("type") == "function_call_output"
                and item.get("call_id") == "explore-map"
            ))
            if exploration_tool == "reachable_areas":
                assert exploration_output["source"]["id"] == "winterfell"
                assert exploration_output["movementType"] == "land"
                assert exploration_output["destinations"]
            else:
                assert any(area["id"] == "castle-black" for area in exploration_output)
        if len(requests) == 2 and cancel:
            raise asyncio.CancelledError
        if len(requests) == 1:
            output = [
                {
                    "type": "function_call",
                    "name": exploration_tool,
                    "call_id": "explore-map",
                    "arguments": '{"area":"Winterfell"}',
                }
            ]
        elif reject and len(requests) == 2:
            output = [
                {
                    "type": "function_call",
                    "name": "submit_action",
                    "call_id": "invalid-action",
                    "arguments": json.dumps(action(unit_ids_to_destroy=[99, 2])),
                }
            ]
        else:
            assert len(requests) in {2, 3}
            assert any(
                item.get("type") == "function_call_output"
                and item.get("call_id") == "explore-map"
                for item in body["input"]
            )
            if reject:
                assert any(
                    item.get("type") == "function_call_output"
                    and item.get("call_id") == "invalid-action"
                    for item in body["input"]
                )
            output = [
                {
                    "type": "function_call",
                    "name": "submit_action",
                    "call_id": "accepted-action",
                    "arguments": json.dumps(action(unit_ids_to_destroy=[1, 2])),
                }
            ]
        return httpx.Response(
            200,
            json={
                "id": f"response-{len(requests)}",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "test-model",
                "output": output,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 30,
                    "total_tokens": 130,
                },
            },
        )

    await runner.client._client.aclose()
    runner.client._client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    prepared = harness.prepare_turn(record, build_context(client.snapshot, "2"), None)
    try:
        if cancel:
            with pytest.raises(ModelRunCancelled) as failure:
                await harness.run_turn(record, prepared, context, "test-run")
            assert client.sent == []
            assert failure.value.partial_result.usage["requests"] == 1
        else:
            result = await harness.run_turn(record, prepared, context, "test-run")
            assert context.action_taken.name == "select_units"
            assert len(client.sent) == 1
            assert "accepted" in result.output_text
        assert len(requests) == (3 if reject else 2)
    finally:
        await harness.shutdown()
        database.close()


@pytest.mark.asyncio
async def test_single_destination_and_unit_remain_explicit_and_recover_from_empty_object():
    snapshot = march_snapshot(single_unit=True)
    ingame = snapshot["childGameState"]
    ingame["game"]["world"]["regions"][0]["id"] = "the-stony-shore"
    ingame["ordersOnBoard"] = [["the-stony-shore", 2]]
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id="2")
    contract = contract_for(snapshot)
    tool = contract.submission_tool()

    async def invoke(answer):
        arguments = json.dumps(answer)
        return json.loads(await tool.on_invoke_tool(ToolContext(
            context=context, tool_call_id="schema-recovery", tool_name="submit_action",
            tool_arguments=arguments), arguments))

    rejected = await invoke(action(moves=[{}], leave_power_token=True))
    assert rejected["accepted"] is False
    item = rejected["expected_schema"]["properties"]["moves"]["items"]
    assert item["properties"]["destination_region_id"]["enum"] == ["winterfell"]
    assert item["properties"]["unit_ids"]["items"]["enum"] == [1]
    assert client.sent == []
    await invoke(action(moves=[{"destination_region_id": "winterfell", "unit_ids": [1]}], leave_power_token=True))
    assert context.action_taken is not None
    assert client.sent[0]["moves"] == [["winterfell", [1]]]


@pytest.mark.asyncio
async def test_multi_action_schema_error_returns_nested_action_discriminator():
    snapshot = planning_snapshot()
    snapshot["childGameState"]["ordersOnBoard"] = [["winterfell", 2]]
    snapshot["childGameState"]["childGameState"] = {
        "type": "action", "childGameState": {"type": "replace-order", "houseId": "stark"}
    }
    contract = contract_for(snapshot)
    arguments = json.dumps({"decision": "skip_raven_order_replacement"})
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id="2")
    rejected = json.loads(await contract.submission_tool().on_invoke_tool(ToolContext(
        context=context, tool_call_id="raven-schema", tool_name="submit_action", tool_arguments=arguments), arguments))
    assert not rejected["accepted"]
    branches = rejected["expected_schema"]["properties"]["decision"]["anyOf"]
    branch = next(b for b in branches if b["properties"]["action"]["enum"] == ["skip_raven_order_replacement"])
    assert branch["type"] == "object"
    assert branch["required"] == ["action", "strategic_handoff"]
    assert client.sent == []


def mustering_contract_snapshot():
    snapshot = planning_snapshot()
    ingame = snapshot['childGameState']
    ingame['game']['houses'][0]['unitLimits'] = [
        ['footman', 10], ['knight', 5], ['ship', 6], ['siege-engine', 2],
    ]
    ingame['game']['supplyRestrictions'] = [[2, 2], [3, 2], [3, 2, 2]]
    ingame['game']['world']['regions'][1]['units'] = []
    ingame['game']['world']['regions'][1]['controlPowerToken'] = 'stark'
    ingame['childGameState'] = {
        'type': 'westeros', 'childGameState': {
            'type': 'player-mustering', 'house': 'stark', 'musteringType': 0,
        },
    }
    return snapshot


@pytest.mark.asyncio
@pytest.mark.parametrize('target', ['karhold', 'discard'])
async def test_raid_uses_exact_string_choices_and_decodes_discard(target):
    snapshot = planning_snapshot()
    ingame = snapshot['childGameState']
    ingame['ordersOnBoard'] = [['winterfell', 13], ['karhold', 10]]
    ingame['game']['world']['regions'].append({
        'id': 'karhold',
        'units': [{'id': 10, 'type': 'footman', 'allegiance': 'lannister'}],
    })
    ingame['childGameState'] = {
        'type': 'resolve-raid-order',
        'childGameState': {'type': 'resolve-single-raid', 'houseId': 'stark'},
    }
    contract = contract_for(snapshot)
    field = contract.output_schema.json_schema()['properties']['raid_target']
    assert field == {
        'type': 'string', 'enum': ['karhold', 'discard'],
        'description': 'Exact enemy area to raid, or discard to remove this Raid without a target.',
    }
    with pytest.raises(ValueError):
        contract.output_schema.validate_json(json.dumps(action(raid_target=None)))
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id='2')
    await contract.execute(context, action(raid_target=target))
    assert context.action_taken.arguments['target_region_id'] == (
        None if target == 'discard' else target
    )
    assert len(client.sent) == 1


def muster_answer(origin, recruits):
    return action(decision={'action': 'muster_units', 'musters': [{
        'mustering_region_id': origin, 'recruitments': [
            f"{r['region_id']}/{r['unit_type']}/{'upgrade' if r['upgrade_from_footman'] else 'new'}"
            for r in recruits
        ],
    }]})


@pytest.mark.parametrize('stage,expected', [
    ('westeros', 'New units can receive orders and march THIS round'),
    ('action', 'those new units cannot march this round'),
])
def test_mustering_briefing_distinguishes_timing_even_in_final_round(stage, expected):
    snapshot = mustering_contract_snapshot()
    snapshot['childGameState']['game']['turn'] = 10
    snapshot['childGameState']['childGameState']['type'] = stage
    context = build_context(snapshot, '2')
    briefing = build_decision_briefing(context, contract_for(snapshot), [])
    assert expected in briefing


@pytest.mark.asyncio
async def test_mustering_without_origins_exposes_only_skip():
    snapshot = mustering_contract_snapshot()
    for region in snapshot['childGameState']['game']['world']['regions']:
        region['units'] = []
        region['controlPowerToken'] = 'lannister'
    contract = contract_for(snapshot)
    assert [item.name for item in contract.actions] == ['skip_mustering']
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id='2')
    await contract.execute(context, action())
    assert client.sent == [{'type': 'muster', 'units': []}]


def recruit(area, kind, upgrade=False):
    return {'region_id': area, 'unit_type': kind, 'upgrade_from_footman': upgrade}


@pytest.mark.parametrize('origin,recruitment', [
    ('white-harbor', recruit('bay-of-ice', 'ship')),
    ('winterfell', recruit('bay-of-ice', 'knight')),
    ('white-harbor', recruit('white-harbor', 'knight')),
    ('white-harbor', recruit('white-harbor', 'knight', True)),
    ('winterfell', recruit('winterfell', 'footman', True)),
])
def test_mustering_schema_rejects_mismatched_origin_terrain_cost_and_upgrade(origin, recruitment):
    contract = contract_for(mustering_contract_snapshot())
    with pytest.raises(ValueError):
        contract.output_schema.validate_json(json.dumps(muster_answer(origin, [recruitment])))


@pytest.mark.asyncio
async def test_mustering_rejects_combined_overspending_without_silently_dropping_units():
    snapshot = mustering_contract_snapshot()
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id='2')
    contract = contract_for(snapshot)
    # Each recruitment is affordable alone, but together costs three of two points.
    answer = muster_answer('winterfell', [
        recruit('winterfell', 'knight'), recruit('bay-of-ice', 'ship'),
    ])
    contract.output_schema.validate_json(json.dumps(answer))
    with pytest.raises(ValueError, match='mustering points'):
        await contract.execute(context, answer)
    assert client.sent == []
    await contract.execute(context, muster_answer('winterfell', [
        recruit('winterfell', 'knight', True), recruit('bay-of-ice', 'ship'),
    ]))
    assert context.action_taken.name == 'muster_units'
    assert len(client.sent[0]['units'][0][1]) == 2


@pytest.mark.asyncio
async def test_mustering_rejects_combined_supply_overflow_without_partial_submission():
    snapshot = mustering_contract_snapshot()
    game = snapshot['childGameState']['game']
    game['houses'][0]['supplyLevel'] = 0
    game['supplyRestrictions'] = [[2]]
    game['world']['regions'].append({
        'id': 'bay-of-ice',
        'units': [{'id': 30, 'type': 'ship', 'allegiance': 'stark'}],
    })
    client = Client(snapshot)
    context = HarnessRunContext(client=client, user_id='2')
    contract = contract_for(snapshot)
    answer = muster_answer('winterfell', [
        recruit('winterfell', 'footman'), recruit('bay-of-ice', 'ship'),
    ])
    contract.output_schema.validate_json(json.dumps(answer))
    with pytest.raises(ValueError, match='supply limit'):
        await contract.execute(context, answer)
    assert client.sent == []
    assert context.action_taken is None
