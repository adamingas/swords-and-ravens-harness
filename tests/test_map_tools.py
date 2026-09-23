import copy
import json
from types import SimpleNamespace

import pytest
from agents.tool_context import ToolContext

from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.map_tools import check_neighbours, neighbouring_areas
from raven_harness.harness.observation import build_context

from conftest import lobby_snapshot, planning_snapshot


def test_neighbours_correct_the_observed_spatial_and_castle_errors():
    context = build_context(planning_snapshot(), "2")
    castle_black = neighbouring_areas(context, " Castle Black ")
    assert {area["id"] for area in castle_black} == {
        "winterfell",
        "karhold",
        "bay-of-ice",
        "the-shivering-sea",
    }
    winterfell = {
        area["id"]: area for area in neighbouring_areas(context, "WINTERFELL")
    }
    assert winterfell["moat-cailin"]["castleLevel"] == 1
    assert winterfell["white-harbor"]["castleLevel"] == 1
    assert winterfell["castle-black"]["castleLevel"] == 0
    assert winterfell["port-of-winterfell"]["type"] == "port"
    assert winterfell["port-of-winterfell"]["owner"] == "stark"
    assert winterfell["moat-cailin"]["owner"] is None
    assert "greywater-watch" not in winterfell  # Transport is not a direct edge.


@pytest.mark.asyncio
async def test_tool_reads_fresh_visible_state_without_taking_an_action():
    snapshot = planning_snapshot()
    ingame = snapshot["childGameState"]
    winterfell = ingame["game"]["world"]["regions"][0]
    winterfell["units"][0]["wounded"] = True
    winterfell["garrison"] = 2
    ingame["ordersOnBoard"] = [["winterfell", 7], ["karhold", None]]
    ingame["childGameState"]["placedOrders"] = [["karhold", 3]]
    client = SimpleNamespace(
        snapshot=snapshot, recent_events=[], connection_generation=1
    )
    run_context = HarnessRunContext(client=client, user_id="2")
    args = json.dumps({"area": "castle-black"})

    async def invoke():
        output = await check_neighbours.on_invoke_tool(
            ToolContext(
                context=run_context,
                tool_call_id="map-1",
                tool_name="check_neighbours",
                tool_arguments=args,
            ),
            args,
        )
        return {area["id"]: area for area in json.loads(output)}

    before = copy.deepcopy(snapshot)
    result = await invoke()
    assert result["winterfell"]["units"] == [
        {"id": 1, "type": "footman", "owner": "stark", "wounded": True}
    ]
    assert result["winterfell"]["garrison"] == 2
    assert result["winterfell"]["visibleOrder"] == {"id": 7, "name": "Support +0"}
    assert result["karhold"]["visibleOrder"] is None
    assert snapshot == before
    assert run_context.action_taken is None

    winterfell["units"] = []
    winterfell["controlPowerToken"] = "greyjoy"
    result = await invoke()
    assert result["winterfell"]["owner"] == "greyjoy"
    assert result["winterfell"]["units"] == []
    winterfell.pop("controlPowerToken")
    winterfell["overwrittenSuperControlPowerToken"] = "lannister"
    assert (await invoke())["winterfell"]["owner"] == "lannister"
    winterfell.pop("overwrittenSuperControlPowerToken")
    assert (await invoke())["winterfell"]["owner"] == "stark"


def test_unknown_names_and_lobby_are_rejected():
    with pytest.raises(ValueError, match="Unknown or ambiguous"):
        neighbouring_areas(build_context(planning_snapshot(), "2"), "Winter")
    with pytest.raises(ValueError, match="only available during a game"):
        neighbouring_areas(build_context(lobby_snapshot(), "2"), "winterfell")
