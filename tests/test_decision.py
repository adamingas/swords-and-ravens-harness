import asyncio
import json

import httpx
import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.harness.actions import HarnessRunContext, available_tools
from raven_harness.harness.decision import build_decision_contract
from raven_harness.harness.decision_briefing import build_decision_briefing
from raven_harness.harness.map_tools import check_neighbours
from raven_harness.harness.observation import build_context
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
    assert set(fields) == {"destination_region_id"}
    client = Client(snapshot)
    await contract.execute(
        HarnessRunContext(client=client, user_id="2"), action(moves=[])
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reject,cancel", [(False, False), (True, False), (False, True)]
)
async def test_actual_wire_explores_then_submits_through_one_action_tool(
    tmp_path, reject, cancel
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
    )
    harness = StrategicHarness(runner, store)
    context = HarnessRunContext(client=client, user_id="2")
    requests = []

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert body["tool_choice"] == "required"
        current_user = next(
            item["content"] for item in body["input"] if item.get("role") == "user"
        )
        assert "You MUST call submit_action" in current_user
        assert {tool["name"] for tool in body.get("tools", [])} == {
            "check_neighbours",
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
        if len(requests) == 2 and cancel:
            raise asyncio.CancelledError
        if len(requests) == 1:
            output = [
                {
                    "type": "function_call",
                    "name": "check_neighbours",
                    "call_id": "explore-map",
                    "arguments": '{"area":"Castle Black"}',
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
