import json
from typing import Any

import pytest
from agents.tool_context import ToolContext
from pydantic import ValidationError

from raven_harness.harness.actions import (
    HarnessRunContext,
    OrderAssignment,
    available_tools,
)
from raven_harness.harness.observation import build_context, build_observation

from conftest import lobby_snapshot, planning_snapshot


class FakeClient:
    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.snapshot = snapshot
        self.recent_events: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []

    async def send(self, message: dict[str, Any], *, require_auth: bool = True) -> None:
        self.sent.append(message)


def test_lobby_exposes_only_currently_applicable_tools() -> None:
    context = build_context(lobby_snapshot(), "2")
    tools = available_tools(context)

    assert [tool.name for tool in tools] == ["choose_house"]
    assert "stark, lannister" in tools[0].description
    assert tools[0].params_json_schema["properties"]["house_id"]["type"] == "string"


@pytest.mark.asyncio
async def test_agents_sdk_tool_sends_a_legal_action() -> None:
    client = FakeClient(lobby_snapshot())
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    tool = available_tools(build_context(client.snapshot, "2"))[0]

    arguments = json.dumps({"house_id": "stark"})
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-1",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert json.loads(result) == {"ok": True, "action": "choose_house"}
    assert client.sent == [
        {"type": "choose-house", "house": "stark", "password": "wolf"}
    ]
    assert run_context.action_taken is not None
    assert run_context.action_taken.name == "choose_house"


@pytest.mark.asyncio
async def test_illegal_dynamic_choice_never_reaches_game_server() -> None:
    client = FakeClient(lobby_snapshot())
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(client.snapshot, "2"))[0]

    arguments = json.dumps({"house_id": "greyjoy"})
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-2",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert "greyjoy" not in client.sent
    assert "must be one of" in result
    assert client.sent == []
    assert run_context.action_taken is None


@pytest.mark.asyncio
async def test_pydantic_rejects_bad_order_token_before_sending() -> None:
    with pytest.raises(ValidationError):
        OrderAssignment(region_id="winterfell", order="teleport")

    client = FakeClient(planning_snapshot())
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = next(
        item
        for item in available_tools(build_context(client.snapshot, "2"))
        if item.name == "submit_orders"
    )

    arguments = json.dumps(
        {
            "assignments": [
                {"region_id": "winterfell", "order": "teleport"},
                {"region_id": "white-harbor", "order": "march"},
            ]
        }
    )
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-3",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert "Invalid JSON input" in result
    assert client.sent == []


@pytest.mark.asyncio
async def test_submit_orders_clears_partial_draft_before_replacing_it() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["game"]["starredOrderRestrictions"] = [3]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    arguments = json.dumps(
        {
            "assignments": [
                {"region_id": "winterfell", "order": "defense"},
                {"region_id": "white-harbor", "order": "defense"},
            ]
        }
    )

    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-idempotent-orders",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent == [
        {"type": "place-order", "regionId": "winterfell", "orderId": None},
        {"type": "place-order", "regionId": "white-harbor", "orderId": None},
        {"type": "place-order", "regionId": "winterfell", "orderId": 4},
        {"type": "place-order", "regionId": "white-harbor", "orderId": 5},
        {"type": "ready"},
    ]


@pytest.mark.asyncio
async def test_submit_orders_rejects_active_westeros_restriction() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["game"]["starredOrderRestrictions"] = [3]
    planning = snapshot["childGameState"]["childGameState"]
    planning["planningRestrictions"] = ["no-defense-order"]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    assignment_schema = tool.params_json_schema["$defs"]["OrderAssignment"]
    assert "defense" not in assignment_schema["properties"]["order"]["enum"]
    assert "defense_plus_two" not in assignment_schema["properties"]["order"]["enum"]
    assert tool.params_json_schema["properties"]["assignments"]["minItems"] == 2
    arguments = json.dumps(
        {
            "assignments": [
                {"region_id": "winterfell", "order": "defense"},
                {"region_id": "white-harbor", "order": "support"},
            ]
        }
    )

    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-restricted-orders",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert "restrictions prohibit order values defense" in result
    assert client.sent == []


def test_observation_is_player_scoped_and_concise() -> None:
    context = build_context(lobby_snapshot(), "2", [{"type": "house-chosen"}])
    observation = build_observation(context)
    assert observation["game"]["phase"] == "lobby"
    assert observation["you"]["userId"] == "2"
    assert len(observation["lobby"]["seats"]) == 1
    assert observation["recentEvents"][0]["type"] == "house-chosen"
    assert "playerView" not in observation
    assert [state["type"] for state in observation["activeStatePath"]] == ["lobby"]


def test_known_ingame_phase_gets_a_small_relevant_toolset() -> None:
    tools = available_tools(build_context(planning_snapshot(), "2"))
    assert {tool.name for tool in tools} == {"submit_orders"}


def test_authoritative_waited_user_ids_drive_turn_detection() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["waitedForUserIds"] = ["2"]

    assert build_observation(build_context(snapshot, "2"))["isYourTurn"] is True
    assert build_observation(build_context(snapshot, "3"))["isYourTurn"] is False


def test_submitted_secret_bid_is_not_replayed_by_autoplay() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["waitedForUserIds"] = ["2"]
    snapshot["childGameState"]["childGameState"] = {
        "type": "bidding",
        "participatingHouses": ["stark", "lannister"],
        "bids": [["stark", 0], ["lannister", -1]],
    }

    assert build_observation(build_context(snapshot, "2"))["isYourTurn"] is False
    snapshot["childGameState"]["childGameState"]["bids"][0][1] = -1
    assert build_observation(build_context(snapshot, "2"))["isYourTurn"] is True


def test_deepest_protocol_state_hides_parent_state_tools() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {
        "type": "use-raven",
        "childGameState": {"type": "see-top-wildling-card"},
    }

    tools = available_tools(build_context(snapshot, "2"))

    assert [tool.name for tool in tools] == ["place_inspected_wildling_card"]


@pytest.mark.asyncio
async def test_typed_march_tool_translates_to_game_protocol() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {"type": "resolve-march-order"}
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = next(
        item
        for item in available_tools(build_context(snapshot, "2"))
        if item.name == "resolve_march"
    )
    arguments = json.dumps(
        {
            "starting_region_id": "winterfell",
            "moves": [{"destination_region_id": "white-harbor", "unit_ids": [1]}],
            "leave_power_token": True,
        }
    )

    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-march",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent == [
        {
            "type": "resolve-march-order",
            "startingRegionId": "winterfell",
            "moves": [["white-harbor", [1]]],
            "leavePowerToken": True,
        }
    ]


@pytest.mark.asyncio
async def test_supply_reconciliation_computes_minimal_legal_removals() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    game = ingame["game"]
    game["houses"][0]["supplyLevel"] = 0
    game["supplyRestrictions"] = [[2, 2]]
    game["world"]["regions"] = [
        {
            "id": "winterfell",
            "units": [
                {"id": 1, "type": "footman", "allegiance": "stark"},
                {"id": 2, "type": "footman", "allegiance": "stark"},
                {"id": 3, "type": "knight", "allegiance": "stark"},
                {"id": 4, "type": "knight", "allegiance": "stark"},
            ],
        },
        {
            "id": "white-harbor",
            "units": [{"id": 5, "type": "footman", "allegiance": "stark"}],
        },
    ]
    ingame["childGameState"] = {
        "type": "reconcile-armies",
        "childGameState": {"house": "stark"},
    }
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]

    assert tool.name == "auto_reconcile_armies"
    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-auto-reconcile",
            tool_name=tool.name,
            tool_arguments="{}",
        ),
        "{}",
    )

    assert client.sent == [
        {
            "type": "reconcile-armies",
            "unitsToRemove": [["winterfell", [1, 2]]],
        }
    ]
