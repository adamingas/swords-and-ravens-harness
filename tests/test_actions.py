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
from raven_harness.harness.protocol_tools import (
    _is_base_game,
    gameplay_tools_for_context,
    muster_units,
)
from raven_harness.game.client import GameConnectionLost, OrderSubmission

from conftest import lobby_snapshot, planning_snapshot


class FakeClient:
    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.snapshot = snapshot
        self.recent_events: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []
        self.connection_generation = 1

    async def send(
        self,
        message: dict[str, Any],
        *,
        require_auth: bool = True,
        expected_generation: int | None = None,
    ) -> None:
        del require_auth
        if expected_generation != self.connection_generation:
            raise GameConnectionLost("stale connection generation")
        self.sent.append(message)

    async def sync_snapshot(
        self,
        timeout: float = 10,
        *,
        expected_generation: int | None = None,
    ) -> dict[str, Any]:
        del timeout
        if expected_generation != self.connection_generation:
            raise GameConnectionLost("stale connection generation")
        child = self.snapshot["childGameState"]
        if child.get("type") == "lobby" and self.sent[-1]["type"] == "choose-house":
            child["players"].append([self.sent[-1]["house"], "2"])
        else:
            self.snapshot["leafStateId"] += "-accepted"
        return self.snapshot

    async def submit_orders(
        self,
        orders: list[dict[str, Any]],
        timeout: float = 10,
        *,
        expected_generation: int | None = None,
    ) -> OrderSubmission:
        del timeout
        if expected_generation != self.connection_generation:
            raise GameConnectionLost("stale connection generation")
        message = {
            "type": "submit-orders",
            "requestId": "order-request-1",
            "orders": orders,
        }
        self.sent.append(message)
        self.snapshot["leafStateId"] += "-accepted"
        return OrderSubmission(
            message=message,
            response={
                "type": "submit-orders-response",
                "requestId": "order-request-1",
                "accepted": True,
                "reason": "ok",
                "stateId": self.snapshot["leafStateId"],
            },
            snapshot=self.snapshot,
        )


def test_mustering_requires_at_least_one_group() -> None:
    assert muster_units.params_json_schema["properties"]["musters"]["minItems"] == 1


def test_lobby_exposes_only_currently_applicable_tools() -> None:
    context = build_context(lobby_snapshot(), "2")
    tools = available_tools(context)

    assert [tool.name for tool in tools] == ["choose_house"]
    house_schema = tools[0].params_json_schema["properties"]["house_id"]
    assert house_schema["type"] == "string"
    assert house_schema["enum"] == ["stark", "lannister"]


@pytest.mark.asyncio
async def test_stale_run_never_sends_on_a_new_connection_generation() -> None:
    client = FakeClient(lobby_snapshot())
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    client.connection_generation += 1

    with pytest.raises(GameConnectionLost, match="stale connection generation"):
        await run_context.perform(
            "choose_house",
            {"house_id": "stark"},
            {"type": "choose-house", "house": "stark", "password": "wolf"},
        )

    assert client.sent == []


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

    assert json.loads(result) == {
        "ok": True,
        "accepted": True,
        "action": "choose_house",
        "stateId": "leaf-1",
    }
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
async def test_pydantic_rejects_bad_order_category_before_sending() -> None:
    with pytest.raises(ValidationError):
        OrderAssignment(
            region_id="winterfell",
            order="teleport",
            starred_preference="avoid",
            priority=50,
        )

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
                {
                    "region_id": "winterfell",
                    "order": "teleport",
                    "starred_preference": "avoid",
                    "priority": 50,
                },
                {
                    "region_id": "white-harbor",
                    "order": "march",
                    "starred_preference": "avoid",
                    "priority": 50,
                },
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
async def test_submit_orders_replaces_complete_draft_atomically() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["game"]["starredOrderRestrictions"] = [3]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": "winterfell",
                    "order": "defense",
                    "starred_preference": "avoid",
                    "priority": 80,
                },
                {
                    "region_id": "white-harbor",
                    "order": "defense",
                    "starred_preference": "avoid",
                    "priority": 20,
                },
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
        {
            "type": "submit-orders",
            "requestId": "order-request-1",
            "orders": [
                {"regionId": "winterfell", "orderId": 4},
                {"regionId": "white-harbor", "orderId": 5},
            ],
        }
    ]


@pytest.mark.asyncio
async def test_submit_orders_reports_server_rejection_without_taking_action() -> None:
    class RejectingOrderClient(FakeClient):
        async def submit_orders(
            self,
            orders: list[dict[str, Any]],
            timeout: float = 10,
            *,
            expected_generation: int | None = None,
        ) -> OrderSubmission:
            del timeout
            if expected_generation != self.connection_generation:
                raise GameConnectionLost("stale connection generation")
            message = {
                "type": "submit-orders",
                "requestId": "order-request-1",
                "orders": orders,
            }
            self.sent.append(message)
            return OrderSubmission(
                message=message,
                response={
                    "type": "submit-orders-response",
                    "requestId": "order-request-1",
                    "accepted": False,
                    "reason": "invalid-region-set",
                    "stateId": self.snapshot["leafStateId"],
                },
                snapshot=self.snapshot,
            )

    snapshot = planning_snapshot()
    client = RejectingOrderClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": region_id,
                    "order": "defense",
                    "starred_preference": "avoid",
                    "priority": 50,
                }
                for region_id in ("winterfell", "white-harbor")
            ]
        }
    )

    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-rejected-orders",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert "invalid-region-set" in result
    assert run_context.action_taken is None


@pytest.mark.asyncio
async def test_submit_orders_allocates_scarce_star_by_preference_and_priority() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["game"]["starredOrderRestrictions"] = [1]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    assignment_schema = tool.params_json_schema["$defs"]["OrderAssignment"]

    assert assignment_schema["properties"]["order"]["enum"] == [
        "march",
        "defense",
        "support",
        "consolidate_power",
        "raid",
    ]
    assert set(assignment_schema["required"]) == {
        "region_id",
        "order",
        "starred_preference",
        "priority",
    }

    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": "winterfell",
                    "order": "march",
                    "starred_preference": "prefer",
                    "priority": 20,
                },
                {
                    "region_id": "white-harbor",
                    "order": "consolidate_power",
                    "starred_preference": "prefer",
                    "priority": 80,
                },
            ]
        }
    )

    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-prioritized-orders",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent[0]["orders"] == [
        {"regionId": "winterfell", "orderId": 2},
        {"regionId": "white-harbor", "orderId": 12},
    ]


@pytest.mark.asyncio
async def test_submit_orders_respects_restriction_on_only_starred_family_member() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["game"]["starredOrderRestrictions"] = [3]
    planning = snapshot["childGameState"]["childGameState"]
    planning["planningRestrictions"] = ["no-march-plus-one-order"]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    order_values = tool.params_json_schema["$defs"]["OrderAssignment"][
        "properties"
    ]["order"]["enum"]

    assert "march" in order_values
    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": "winterfell",
                    "order": "march",
                    "starred_preference": "prefer",
                    "priority": 100,
                },
                {
                    "region_id": "white-harbor",
                    "order": "march",
                    "starred_preference": "prefer",
                    "priority": 10,
                },
            ]
        }
    )

    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-no-march-star",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent[0]["orders"] == [
        {"regionId": "winterfell", "orderId": 2},
        {"regionId": "white-harbor", "orderId": 1},
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
    assert tool.params_json_schema["properties"]["assignments"]["minItems"] == 2
    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": "winterfell",
                    "order": "defense",
                    "starred_preference": "avoid",
                    "priority": 50,
                },
                {
                    "region_id": "white-harbor",
                    "order": "support",
                    "starred_preference": "avoid",
                    "priority": 50,
                },
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

    assert "active Westeros restrictions" in result
    assert client.sent == []


@pytest.mark.asyncio
async def test_submit_orders_uses_restricted_token_only_after_legal_inventory() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    game = ingame["game"]
    game["starredOrderRestrictions"] = [0]
    game["world"]["regions"] = [
        {
            "id": f"region-{index}",
            "units": [{"id": index, "type": "footman", "allegiance": "stark"}],
        }
        for index in range(1, 10)
    ]
    ingame["childGameState"]["planningRestrictions"] = ["no-defense-order"]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    order_values = tool.params_json_schema["$defs"]["OrderAssignment"][
        "properties"
    ]["order"]["enum"]
    assert "defense" in order_values
    orders = [
        "march",
        "march",
        "support",
        "support",
        "consolidate_power",
        "consolidate_power",
        "raid",
        "raid",
        "defense",
    ]
    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": f"region-{index}",
                    "order": order,
                    "starred_preference": "avoid",
                    "priority": 100 - index,
                }
                for index, order in enumerate(orders, 1)
            ]
        }
    )

    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-forced-restricted-order",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert json.loads(result)["accepted"] is True
    assert client.sent[0]["orders"][-1] == {
        "regionId": "region-9",
        "orderId": 4,
    }


@pytest.mark.asyncio
async def test_submit_orders_never_treats_excess_star_as_a_fallback() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    game = ingame["game"]
    game["starredOrderRestrictions"] = [1]
    game["world"]["regions"] = [
        {
            "id": f"region-{index}",
            "units": [{"id": index, "type": "footman", "allegiance": "stark"}],
        }
        for index in range(1, 11)
    ]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    orders = [
        "march",
        "march",
        "march",
        "defense",
        "defense",
        "defense",
        "support",
        "support",
        "consolidate_power",
        "consolidate_power",
    ]
    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": f"region-{index}",
                    "order": order,
                    "starred_preference": "avoid",
                    "priority": 100 - index,
                }
                for index, order in enumerate(orders, 1)
            ]
        }
    )

    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-excess-star",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert "limit of 1 starred orders" in result
    assert client.sent == []


@pytest.mark.asyncio
async def test_submit_orders_rejects_more_than_three_of_one_category() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["game"]["starredOrderRestrictions"] = [3]
    ingame["game"]["world"]["regions"] = [
        {
            "id": f"region-{index}",
            "units": [{"id": index, "type": "footman", "allegiance": "stark"}],
        }
        for index in range(1, 5)
    ]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": f"region-{index}",
                    "order": "raid",
                    "starred_preference": "avoid",
                    "priority": 50,
                }
                for index in range(1, 5)
            ]
        }
    )

    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-family-over-capacity",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert "raid may be assigned to at most 3 regions" in result
    assert client.sent == []


@pytest.mark.asyncio
async def test_submit_orders_can_ready_with_no_eligible_regions() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["game"]["world"]["regions"] = []
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    assignment_list = tool.params_json_schema["properties"]["assignments"]

    assert assignment_list["minItems"] == 0
    assert assignment_list["maxItems"] == 0
    arguments = json.dumps({"assignments": []})
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-ready-without-orders",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert json.loads(result)["accepted"] is True
    assert client.sent[0]["orders"] == []


@pytest.mark.asyncio
async def test_submit_orders_leaves_regions_empty_when_usable_tokens_run_out() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["game"]["starredOrderRestrictions"] = [1]
    ingame["game"]["world"]["regions"] = [
        {
            "id": f"region-{index}",
            "units": [{"id": index, "type": "footman", "allegiance": "stark"}],
        }
        for index in range(1, 13)
    ]
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    assignment_list = tool.params_json_schema["properties"]["assignments"]
    orders = [
        "march",
        "march",
        "march",
        "defense",
        "defense",
        "support",
        "support",
        "consolidate_power",
        "consolidate_power",
        "raid",
        "raid",
    ]

    assert assignment_list["minItems"] == 11
    assert assignment_list["maxItems"] == 11
    arguments = json.dumps(
        {
            "assignments": [
                {
                    "region_id": f"region-{index}",
                    "order": order,
                    "starred_preference": "prefer" if index == 1 else "avoid",
                    "priority": 101 - index,
                }
                for index, order in enumerate(orders, 1)
            ]
        }
    )
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-exhausted-inventory",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert json.loads(result)["accepted"] is True
    placed = [
        order for order in client.sent[0]["orders"] if order.get("orderId")
    ]
    assert len(placed) == 11
    assert {message["regionId"] for message in placed} == {
        f"region-{index}" for index in range(1, 12)
    }


def test_submit_orders_caps_zero_star_inventory_at_all_fifteen_tokens() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["game"]["starredOrderRestrictions"] = [0]
    ingame["game"]["world"]["regions"] = [
        {
            "id": f"region-{index}",
            "units": [{"id": index, "type": "footman", "allegiance": "stark"}],
        }
        for index in range(1, 17)
    ]

    tool = available_tools(build_context(snapshot, "2"))[0]
    assignment_list = tool.params_json_schema["properties"]["assignments"]
    assert assignment_list["minItems"] == 15
    assert assignment_list["maxItems"] == 15


def test_observation_is_player_scoped_and_concise() -> None:
    context = build_context(lobby_snapshot(), "2", [{"type": "house-chosen"}])
    observation = build_observation(context)
    assert observation["game"]["phase"] == "lobby"
    assert observation["you"]["userId"] == "2"
    assert len(observation["lobby"]["seats"]) == 1
    assert observation["recentEvents"][0]["type"] == "house-chosen"
    assert "playerView" not in observation
    assert observation["statePath"] == ["lobby"]


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


def test_non_base_game_snapshot_exposes_no_protocol_tools() -> None:
    snapshot = planning_snapshot()
    snapshot["gameSettings"] = {
        "setupId": "mother-of-dragons",
        "playerCount": 8,
    }
    snapshot["childGameState"]["childGameState"] = {
        "type": "resolve-march-order",
        "childGameState": {
            "type": "resolve-single-march",
            "houseId": "stark",
        },
    }

    assert available_tools(build_context(snapshot, "2")) == []


def test_non_six_player_snapshot_exposes_no_protocol_tools() -> None:
    snapshot = planning_snapshot()
    snapshot["gameSettings"] = {"setupId": "base-game", "playerCount": 5}
    snapshot["childGameState"]["childGameState"] = {
        "type": "resolve-march-order"
    }

    assert available_tools(build_context(snapshot, "2")) == []


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"playerCount": 6},
        {"setupId": "mother-of-dragons", "playerCount": 6},
        {"setupId": "base-game"},
        {"setupId": "base-game", "playerCount": 5},
        {"setupId": "base-game", "playerCount": 6, "vassals": True},
    ],
)
def test_base_game_detection_fails_closed_for_missing_or_wrong_settings(settings) -> None:
    snapshot = planning_snapshot()
    if settings is None:
        snapshot.pop("gameSettings")
    else:
        snapshot["gameSettings"] = settings

    assert _is_base_game(snapshot) is False
    context = build_context(snapshot, "2")
    assert gameplay_tools_for_context(context, has_specific_tools=False) == []


def test_base_game_detection_accepts_omitted_false_vassal_setting() -> None:
    snapshot = planning_snapshot()
    assert "vassals" not in snapshot["gameSettings"]

    assert _is_base_game(snapshot) is True


def test_unknown_child_state_does_not_inherit_parent_tools() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {
        "type": "resolve-march-order",
        "childGameState": {"type": "unmapped-new-state"},
    }

    assert available_tools(build_context(snapshot, "2")) == []


def test_unknown_child_state_does_not_inherit_specific_parent_tools() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {
        "type": "bidding",
        "participatingHouses": ["stark"],
        "bids": [["stark", -1]],
        "childGameState": {"type": "unmapped-new-state"},
    }

    assert available_tools(build_context(snapshot, "2")) == []


def test_neutral_force_support_call_is_hidden_without_a_possible_supporter() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {
        "type": "resolve-march-order",
        "childGameState": {
            "type": "resolve-single-march",
            "houseId": "stark",
            "supportersAgainstNeutralForce": None,
        },
    }

    tools = available_tools(build_context(snapshot, "2"))

    assert [tool.name for tool in tools] == ["resolve_march"]


def test_neutral_force_support_call_requires_a_reachable_foreign_supporter() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = [["winterfell", 2], ["white-harbor", 7]]
    white_harbor = next(
        region
        for region in ingame["game"]["world"]["regions"]
        if region["id"] == "white-harbor"
    )
    white_harbor["units"] = [
        {"id": 2, "type": "footman", "allegiance": "lannister", "wounded": False}
    ]
    ingame["game"]["world"]["regions"].append(
        {"id": "moat-cailin", "units": [], "garrison": 3}
    )
    ingame["childGameState"] = {
        "type": "resolve-march-order",
        "childGameState": {
            "type": "resolve-single-march",
            "houseId": "stark",
            "supportersAgainstNeutralForce": None,
        },
    }

    tools = available_tools(build_context(snapshot, "2"))

    assert {tool.name for tool in tools} == {
        "call_for_support_against_neutral_force",
        "resolve_march",
    }


def test_neutral_force_support_call_is_hidden_after_support_was_requested() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {
        "type": "resolve-march-order",
        "childGameState": {
            "type": "resolve-single-march",
            "houseId": "stark",
            "supportersAgainstNeutralForce": [["moat-cailin", ["greyjoy"]]],
        },
    }

    tools = available_tools(build_context(snapshot, "2"))

    assert [tool.name for tool in tools] == ["resolve_march"]


def test_unattainable_neutral_force_is_not_a_march_destination() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = [["winterfell", 3]]
    ingame["game"]["world"]["regions"].append(
        {"id": "moat-cailin", "units": [], "garrison": 5}
    )
    ingame["childGameState"] = {
        "type": "resolve-march-order",
        "childGameState": {
            "type": "resolve-single-march",
            "houseId": "stark",
            "supportersAgainstNeutralForce": None,
        },
    }

    tool = next(
        item
        for item in available_tools(build_context(snapshot, "2"))
        if item.name == "resolve_march"
    )
    destinations = tool.params_json_schema["$defs"]["UnitMove"]["properties"][
        "destination_region_id"
    ]["enum"]

    assert "moat-cailin" not in destinations


def test_accepted_foreign_support_makes_neutral_force_attainable() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = [["winterfell", 2], ["white-harbor", 7]]
    white_harbor = next(
        region
        for region in ingame["game"]["world"]["regions"]
        if region["id"] == "white-harbor"
    )
    white_harbor["units"] = [
        {"id": 2, "type": "footman", "allegiance": "lannister", "wounded": False}
    ]
    ingame["game"]["world"]["regions"].append(
        {"id": "moat-cailin", "units": [], "garrison": 2}
    )
    ingame["childGameState"] = {
        "type": "resolve-march-order",
        "childGameState": {
            "type": "resolve-single-march",
            "houseId": "stark",
            "supportersAgainstNeutralForce": [["moat-cailin", ["lannister"]]],
        },
    }

    tools = available_tools(build_context(snapshot, "2"))
    assert [tool.name for tool in tools] == ["resolve_march"]
    destinations = tools[0].params_json_schema["$defs"]["UnitMove"]["properties"][
        "destination_region_id"
    ]["enum"]

    assert "moat-cailin" in destinations


@pytest.mark.asyncio
async def test_declining_support_uses_declare_support_with_null_house() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {
        "type": "combat",
        "attackerId": "lannister",
        "defenderId": "baratheon",
        "childGameState": {"type": "support", "houseId": "stark"},
    }
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    arguments = json.dumps({"house_id": "none"})

    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-decline-support",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent == [
        {"type": "declare-support", "supportedHouseId": None}
    ]


@pytest.mark.asyncio
async def test_state_specific_tool_rechecks_turn_before_send() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["childGameState"] = {
        "type": "bidding",
        "participatingHouses": ["stark"],
        "bids": [["stark", -1]],
    }
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]
    snapshot["childGameState"]["waitedForUserIds"] = []
    arguments = json.dumps({"amount": 1})

    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-late-bid",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert "not responsible for the current decision" in result
    assert client.sent == []


@pytest.mark.asyncio
async def test_typed_march_tool_translates_to_game_protocol() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["ordersOnBoard"] = [["winterfell", 2]]
    snapshot["childGameState"]["childGameState"] = {"type": "resolve-march-order"}
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = next(
        item
        for item in available_tools(build_context(snapshot, "2"))
        if item.name == "resolve_march"
    )
    assert tool.params_json_schema["properties"]["leave_power_token"]["const"] is False
    arguments = json.dumps(
        {
            "starting_region_id": "winterfell",
            "moves": [{"destination_region_id": "white-harbor", "unit_ids": [1]}],
            "leave_power_token": False,
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
            "leavePowerToken": False,
        }
    ]
    assert run_context.action_taken is not None
    assert run_context.action_taken.name == "resolve_march"


@pytest.mark.asyncio
async def test_march_omits_an_illegal_power_token_request() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["ordersOnBoard"] = [["winterfell", 2]]
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
            tool_call_id="call-march-illegal-token",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent[-1]["leavePowerToken"] is False
    assert run_context.action_taken is not None
    assert run_context.action_taken.arguments["leave_power_token"] is False
    assert (
        run_context.action_taken.arguments["omitted_illegal_power_token"] is True
    )


@pytest.mark.asyncio
async def test_march_rejects_a_weak_neutral_force_attack_before_sending() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = [["winterfell", 2]]
    winterfell = next(
        region
        for region in ingame["game"]["world"]["regions"]
        if region["id"] == "winterfell"
    )
    winterfell["units"].append(
        {
            "id": 3,
            "type": "knight",
            "allegiance": "stark",
            "wounded": False,
        }
    )
    ingame["game"]["world"]["regions"].append(
        {"id": "moat-cailin", "units": [], "garrison": 3}
    )
    ingame["childGameState"] = {
        "type": "resolve-march-order",
        "childGameState": {
            "type": "resolve-single-march",
            "houseId": "stark",
            "supportersAgainstNeutralForce": None,
        },
    }
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = next(
        item
        for item in available_tools(build_context(snapshot, "2"))
        if item.name == "resolve_march"
    )
    destinations = tool.params_json_schema["$defs"]["UnitMove"]["properties"][
        "destination_region_id"
    ]["enum"]
    assert "moat-cailin" in destinations
    weak = json.dumps(
        {
            "starting_region_id": "winterfell",
            "moves": [{"destination_region_id": "moat-cailin", "unit_ids": [1]}],
            "leave_power_token": False,
        }
    )

    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-weak-neutral-attack",
            tool_name=tool.name,
            tool_arguments=weak,
        ),
        weak,
    )

    assert "neutral force strength of 3" in result
    assert client.sent == []
    assert run_context.action_taken is None


@pytest.mark.asyncio
async def test_raid_schema_and_runtime_allow_only_raidable_enemy_orders() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = [
        ["winterfell", 13],
        ["karhold", 10],
        ["bay-of-ice", 7],
    ]
    ingame["game"]["world"]["regions"].extend(
        [
            {
                "id": "karhold",
                "units": [{"id": 10, "type": "footman", "allegiance": "lannister"}],
            },
            {
                "id": "bay-of-ice",
                "units": [{"id": 11, "type": "ship", "allegiance": "lannister"}],
            },
        ]
    )
    ingame["childGameState"] = {
        "type": "resolve-raid-order",
        "childGameState": {"type": "resolve-single-raid", "houseId": "stark"},
    }
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]

    assert tool.name == "resolve_raid"
    assert tool.params_json_schema["properties"]["order_region_id"]["enum"] == [
        "winterfell"
    ]
    assert tool.params_json_schema["properties"]["target_region_id"]["anyOf"][0][
        "enum"
    ] == ["karhold"]

    invalid = json.dumps(
        {"order_region_id": "winterfell", "target_region_id": "bay-of-ice"}
    )
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-invalid-raid",
            tool_name=tool.name,
            tool_arguments=invalid,
        ),
        invalid,
    )
    assert "not raidable" in result
    assert client.sent == []

    valid = json.dumps(
        {"order_region_id": "winterfell", "target_region_id": "karhold"}
    )
    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-valid-raid",
            tool_name=tool.name,
            tool_arguments=valid,
        ),
        valid,
    )
    assert client.sent == [
        {
            "type": "resolve-raid",
            "orderRegionId": "winterfell",
            "targetRegionId": "karhold",
        }
    ]


@pytest.mark.asyncio
async def test_base_game_consolidate_power_excludes_expansion_choices() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = [["winterfell", 10]]
    ingame["childGameState"] = {
        "type": "resolve-consolidate-power",
        "childGameState": {
            "type": "resolve-single-consolidate-power",
            "house": "stark",
        },
    }
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = available_tools(build_context(snapshot, "2"))[0]

    assert tool.name == "resolve_consolidate_power"
    assert tool.params_json_schema["properties"]["choice"]["enum"] == [
        "gain_power_tokens"
    ]
    assert "loan_id" not in tool.params_json_schema["properties"]
    invalid = json.dumps(
        {"region_id": "winterfell", "choice": "purchase_loan", "loan_id": 1}
    )
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-invalid-cp",
            tool_name=tool.name,
            tool_arguments=invalid,
        ),
        invalid,
    )
    assert "Invalid JSON input" in result
    assert client.sent == []

    valid = json.dumps(
        {"region_id": "winterfell", "choice": "gain_power_tokens"}
    )
    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-valid-cp",
            tool_name=tool.name,
            tool_arguments=valid,
        ),
        valid,
    )
    assert client.sent == [
        {
            "type": "resolve-consolidate-power-choice",
            "region": "winterfell",
            "gainPowerTokens": True,
        }
    ]


@pytest.mark.asyncio
async def test_starred_consolidate_power_mustering_is_limited_to_its_castle() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    house = ingame["game"]["houses"][0]
    house["unitLimits"] = [
        ["footman", 10],
        ["knight", 5],
        ["ship", 6],
        ["siege-engine", 2],
    ]
    ingame["game"]["supplyRestrictions"] = [[2, 2], [3, 2], [3, 2, 2]]
    ingame["ordersOnBoard"] = [["winterfell", 12]]
    ingame["childGameState"] = {
        "type": "resolve-consolidate-power",
        "childGameState": {
            "type": "player-mustering",
            "house": "stark",
            "musteringType": 1,
        },
    }
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = next(
        item
        for item in available_tools(build_context(snapshot, "2"))
        if item.name == "muster_units"
    )

    assert tool.params_json_schema["properties"]["musters"]["maxItems"] == 1
    assert tool.params_json_schema["$defs"]["MusterGroup"]["properties"][
        "mustering_region_id"
    ]["enum"] == ["winterfell"]

    too_expensive = json.dumps(
        {
            "musters": [
                {
                    "mustering_region_id": "winterfell",
                    "recruitments": [
                        {
                            "unit_type": "footman",
                            "region_id": "winterfell",
                            "upgrade_from_footman": False,
                        },
                        {
                            "unit_type": "ship",
                            "region_id": "bay-of-ice",
                            "upgrade_from_footman": False,
                        },
                        {
                            "unit_type": "ship",
                            "region_id": "the-shivering-sea",
                            "upgrade_from_footman": False,
                        },
                    ],
                }
            ]
        }
    )
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-over-muster",
            tool_name=tool.name,
            tool_arguments=too_expensive,
        ),
        too_expensive,
    )
    assert "mustering points" in result
    assert client.sent == []

    valid = json.dumps(
        {
            "musters": [
                {
                    "mustering_region_id": "winterfell",
                    "recruitments": [
                        {
                            "unit_type": "footman",
                            "region_id": "winterfell",
                            "upgrade_from_footman": False,
                        },
                        {
                            "unit_type": "ship",
                            "region_id": "bay-of-ice",
                            "upgrade_from_footman": False,
                        },
                    ],
                }
            ]
        }
    )
    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-valid-muster",
            tool_name=tool.name,
            tool_arguments=valid,
        ),
        valid,
    )
    assert client.sent == [
        {
            "type": "muster",
            "units": [
                [
                    "winterfell",
                    [
                        {"from": None, "to": "footman", "region": "winterfell"},
                        {"from": None, "to": "ship", "region": "bay-of-ice"},
                    ],
                ]
            ],
        }
    ]


@pytest.mark.asyncio
async def test_mustering_upgrade_uses_engine_canonical_footman_order() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    house = ingame["game"]["houses"][0]
    house["unitLimits"] = [
        ["footman", 10],
        ["knight", 5],
        ["ship", 6],
        ["siege-engine", 2],
    ]
    ingame["game"]["supplyRestrictions"] = [[2, 2], [3, 2], [3, 2, 2]]
    winterfell = next(
        region
        for region in ingame["game"]["world"]["regions"]
        if region["id"] == "winterfell"
    )
    winterfell["units"].append(
        {
            "id": 31,
            "type": "footman",
            "allegiance": "stark",
            "wounded": False,
        }
    )
    ingame["childGameState"] = {
        "type": "westeros",
        "childGameState": {
            "type": "mustering",
            "childGameState": {
                "type": "player-mustering",
                "house": "stark",
                "musteringType": 0,
            },
        },
    }
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    context = build_context(snapshot, "2")
    tool = next(
        item for item in available_tools(context) if item.name == "muster_units"
    )
    recruitment_schema = tool.params_json_schema["$defs"]["Recruitment"]

    assert "source_unit_id" not in recruitment_schema["properties"]
    assert "upgrade_from_footman" in recruitment_schema["required"]
    assert context.game is not None
    winterfell_guidance = next(
        origin
        for origin in build_observation(context)["actionGuidance"]["origins"]
        if origin["regionId"] == "winterfell"
    )
    observation_guidance = build_observation(context)["actionGuidance"]
    assert observation_guidance["supplyLimit"] == {
        "level": 2,
        "allowedArmySizes": [3, 2, 2],
        "currentArmies": [{"regionId": "winterfell", "unitCount": 2}],
        "singleUnitRegions": ["white-harbor"],
        "rule": (
            "Only regions with two or more units use an army slot. Sort army "
            "sizes largest first and compare them with allowedArmySizes."
        ),
    }
    winterfell_destination = next(
        destination
        for destination in winterfell_guidance["destinations"]
        if destination["regionId"] == "winterfell"
    )
    assert winterfell_destination["upgradeableFootmen"] == 2
    assert winterfell_destination["currentUnitCount"] == 2
    assert winterfell_destination["supplySafeNewUnitsWhenChosenAlone"] == 1
    bay_destination = next(
        destination
        for destination in winterfell_guidance["destinations"]
        if destination["regionId"] == "bay-of-ice"
    )
    assert bay_destination["currentUnitCount"] == 0
    assert bay_destination["supplySafeNewUnitsWhenChosenAlone"] == 3

    arguments = json.dumps(
        {
            "musters": [
                {
                    "mustering_region_id": "winterfell",
                    "recruitments": [
                        {
                            "unit_type": "knight",
                            "region_id": "winterfell",
                            "upgrade_from_footman": True,
                        },
                        {
                            "unit_type": "siege-engine",
                            "region_id": "winterfell",
                            "upgrade_from_footman": True,
                        },
                    ],
                }
            ]
        }
    )
    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-upgrade-muster",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent == [
        {
            "type": "muster",
            "units": [
                [
                    "winterfell",
                    [
                        {"from": 1, "to": "knight", "region": "winterfell"},
                        {
                            "from": 31,
                            "to": "siege-engine",
                            "region": "winterfell",
                        },
                    ],
                ]
            ],
        }
    ]


def _supply_limited_mustering_snapshot() -> dict[str, Any]:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    house = ingame["game"]["houses"][0]
    house["supplyLevel"] = 0
    house["unitLimits"] = [
        ["footman", 10],
        ["knight", 5],
        ["ship", 6],
        ["siege-engine", 2],
    ]
    ingame["game"]["supplyRestrictions"] = [[2]]
    ingame["game"]["world"]["regions"].append(
        {
            "id": "bay-of-ice",
            "units": [
                {
                    "id": 30,
                    "type": "ship",
                    "allegiance": "stark",
                    "wounded": False,
                }
            ],
        }
    )
    ingame["childGameState"] = {
        "type": "westeros",
        "childGameState": {
            "type": "mustering",
            "childGameState": {
                "type": "player-mustering",
                "house": "stark",
                "musteringType": 0,
            },
        },
    }
    return snapshot


@pytest.mark.asyncio
async def test_mustering_keeps_priority_ordered_supply_safe_recruitments() -> None:
    snapshot = _supply_limited_mustering_snapshot()
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = next(
        item
        for item in available_tools(build_context(snapshot, "2"))
        if item.name == "muster_units"
    )
    arguments = json.dumps(
        {
            "musters": [
                {
                    "mustering_region_id": "winterfell",
                    "recruitments": [
                        {
                            "unit_type": "footman",
                            "region_id": "winterfell",
                            "upgrade_from_footman": False,
                        },
                        {
                            "unit_type": "ship",
                            "region_id": "bay-of-ice",
                            "upgrade_from_footman": False,
                        },
                    ],
                }
            ]
        }
    )

    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-supply-safe-muster",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent == [
        {
            "type": "muster",
            "units": [
                [
                    "winterfell",
                    [{"from": None, "to": "footman", "region": "winterfell"}],
                ]
            ],
        }
    ]
    assert run_context.action_taken is not None
    assert run_context.action_taken.arguments["musters"][0]["recruitments"] == [
        {
            "unit_type": "footman",
            "region_id": "winterfell",
            "upgrade_from_footman": False,
        }
    ]
    assert (
        run_context.action_taken.arguments["omitted_supply_unsafe_recruitments"]
        == 1
    )


@pytest.mark.asyncio
async def test_mustering_submits_empty_plan_when_all_requests_exceed_supply() -> None:
    snapshot = _supply_limited_mustering_snapshot()
    winterfell = next(
        region
        for region in snapshot["childGameState"]["game"]["world"]["regions"]
        if region["id"] == "winterfell"
    )
    winterfell["units"].append(
        {
            "id": 31,
            "type": "footman",
            "allegiance": "stark",
            "wounded": False,
        }
    )
    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = next(
        item
        for item in available_tools(build_context(snapshot, "2"))
        if item.name == "muster_units"
    )
    arguments = json.dumps(
        {
            "musters": [
                {
                    "mustering_region_id": "winterfell",
                    "recruitments": [
                        {
                            "unit_type": "ship",
                            "region_id": "bay-of-ice",
                            "upgrade_from_footman": False,
                        }
                    ],
                }
            ]
        }
    )

    await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-no-supply-safe-muster",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert client.sent == [{"type": "muster", "units": []}]
    assert run_context.action_taken is not None
    assert run_context.action_taken.arguments == {
        "musters": [],
        "omitted_supply_unsafe_recruitments": 1,
    }


@pytest.mark.asyncio
async def test_raven_replacement_schema_uses_remaining_physical_tokens() -> None:
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    ingame["ordersOnBoard"] = [["winterfell", 1], ["white-harbor", 3]]
    ingame["game"]["starredOrderRestrictions"] = [1]
    ingame["childGameState"] = {
        "type": "use-raven",
        "childGameState": {"type": "replace-order"},
    }

    tool = next(
        item
        for item in available_tools(build_context(snapshot, "2"))
        if item.name == "replace_raven_order"
    )

    assert tool.params_json_schema["properties"]["region_id"]["enum"] == [
        "white-harbor",
        "winterfell",
    ]
    available_order_ids = tool.params_json_schema["properties"]["order_id"]["enum"]
    assert 2 in available_order_ids
    assert 15 in available_order_ids

    client = FakeClient(snapshot)
    run_context = HarnessRunContext(client=client, user_id="2")
    invalid = json.dumps({"region_id": "winterfell", "order_id": 15})
    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-invalid-raven",
            tool_name=tool.name,
            tool_arguments=invalid,
        ),
        invalid,
    )
    assert "not a legal Raven replacement" in result
    assert client.sent == []


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
    assert run_context.action_taken is not None
    assert run_context.action_taken.name == "auto_reconcile_armies"


@pytest.mark.asyncio
async def test_unacknowledged_action_is_not_recorded_as_taken() -> None:
    class RejectingClient(FakeClient):
        async def sync_snapshot(
            self,
            timeout: float = 10,
            *,
            expected_generation: int | None = None,
        ) -> dict[str, Any]:
            del timeout
            if expected_generation != self.connection_generation:
                raise GameConnectionLost("stale connection generation")
            return self.snapshot

    client = RejectingClient(lobby_snapshot())
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    tool = available_tools(build_context(client.snapshot, "2"))[0]
    arguments = json.dumps({"house_id": "stark"})

    result = await tool.on_invoke_tool(
        ToolContext(
            context=run_context,
            tool_call_id="call-rejected",
            tool_name=tool.name,
            tool_arguments=arguments,
        ),
        arguments,
    )

    assert "authoritative state did not reflect the action" in result
    assert run_context.action_taken is None
