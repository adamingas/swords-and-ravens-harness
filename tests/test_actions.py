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
    distribute_power_tokens,
    muster_units,
    place_sellswords,
)

from conftest import lobby_snapshot, planning_snapshot


class FakeClient:
    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.snapshot = snapshot
        self.recent_events: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []

    async def send(self, message: dict[str, Any], *, require_auth: bool = True) -> None:
        self.sent.append(message)

    async def sync_snapshot(self, timeout: float = 10) -> dict[str, Any]:
        del timeout
        child = self.snapshot["childGameState"]
        if child.get("type") == "lobby" and self.sent[-1]["type"] == "choose-house":
            child["players"].append([self.sent[-1]["house"], "2"])
        else:
            self.snapshot["leafStateId"] += "-accepted"
        return self.snapshot


def test_collection_protocol_tools_require_at_least_one_item() -> None:
    assert muster_units.params_json_schema["properties"]["musters"]["minItems"] == 1
    assert (
        distribute_power_tokens.params_json_schema["properties"]["allocations"][
            "minItems"
        ]
        == 1
    )
    assert (
        place_sellswords.params_json_schema["properties"]["placements"]["minItems"]
        == 1
    )


def test_lobby_exposes_only_currently_applicable_tools() -> None:
    context = build_context(lobby_snapshot(), "2")
    tools = available_tools(context)

    assert [tool.name for tool in tools] == ["choose_house"]
    house_schema = tools[0].params_json_schema["properties"]["house_id"]
    assert house_schema["type"] == "string"
    assert house_schema["enum"] == ["stark", "lannister"]


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
        "march_minus_one",
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
                {"region_id": f"region-{index}", "order": order}
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
    assert client.sent[-2] == {
        "type": "place-order",
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
        "march_minus_one",
        "march",
        "support",
        "support",
        "consolidate_power",
        "consolidate_power",
        "raid",
        "raid",
        "march_plus_one",
        "defense_plus_two",
    ]
    arguments = json.dumps(
        {
            "assignments": [
                {"region_id": f"region-{index}", "order": order}
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

    assert "at most 1 starred orders" in result
    assert client.sent == []


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


def test_neutral_force_support_call_is_available_during_single_march() -> None:
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

    assert {tool.name for tool in tools} == {
        "call_for_support_against_neutral_force",
        "resolve_march",
    }


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
    assert "choice must be one of gain_power_tokens" in result
    assert client.sent == []


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
                            "source_unit_id": None,
                        },
                        {
                            "unit_type": "ship",
                            "region_id": "bay-of-ice",
                            "source_unit_id": None,
                        },
                        {
                            "unit_type": "ship",
                            "region_id": "the-shivering-sea",
                            "source_unit_id": None,
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
                            "source_unit_id": None,
                        },
                        {
                            "unit_type": "ship",
                            "region_id": "bay-of-ice",
                            "source_unit_id": None,
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
        async def sync_snapshot(self, timeout: float = 10) -> dict[str, Any]:
            del timeout
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
