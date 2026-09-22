import copy
import json
from pathlib import Path
import select
import subprocess
from types import SimpleNamespace

from agents.tool_context import ToolContext
from hypothesis import given, settings, strategies as st
import pytest

from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.legal import _regions
from raven_harness.harness.observation import build_context
from raven_harness.harness.reachability_tools import (
    movement_reachability,
    reachable_areas,
)

from conftest import lobby_snapshot, planning_snapshot


def unit(id, kind="footman", house="stark", wounded=False):
    return {"id": id, "type": kind, "allegiance": house, "wounded": wounded}


def board(*regions, player_count=6):
    snapshot = planning_snapshot()
    snapshot["gameSettings"]["playerCount"] = player_count
    snapshot["childGameState"]["game"]["world"]["regions"] = list(regions)
    return snapshot


def query(snapshot, source="winterfell"):
    return movement_reachability(build_context(snapshot, "2"), source)


def destinations(snapshot, source="winterfell"):
    return {r["id"]: r for r in query(snapshot, source)["destinations"]}


@pytest.fixture(scope="module")
def server_oracle():
    server = (
        Path(__file__).resolve().parents[1] / "swords-and-ravens/agot-bg-game-server"
    )
    ts_node = server / "node_modules/.bin/ts-node"
    if not ts_node.is_file():
        pytest.skip("Upstream Node dependencies are required for the server oracle")
    process = subprocess.Popen(
        [
            str(ts_node),
            "--transpile-only",
            "--project",
            str(server / "tsconfig.json"),
            str(Path(__file__).with_name("server_reachability.ts")),
        ],
        cwd=server,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def query(snapshot, source="winterfell"):
        process.stdin.write(
            json.dumps(
                {
                    "snapshot": snapshot,
                    "source": source,
                    "houseId": "stark",
                }
            )
            + "\n"
        )
        process.stdin.flush()
        assert select.select([process.stdout], [], [], 30)[0], "Server oracle timed out"
        line = process.stdout.readline()
        assert line, (
            process.stderr.read()
            if process.poll() is not None
            else "Oracle closed stdout"
        )
        result = json.loads(line)
        assert "error" not in result, result.get("error")
        return result

    yield query
    process.stdin.close()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    process.stdout.close()
    process.stderr.close()


@pytest.mark.parametrize("player_count", [3, 6])
@pytest.mark.parametrize(
    "occupants", [[], [unit(1)], [unit(1, wounded=True)], [unit(1, house="greyjoy")]]
)
def test_any_land_origin_including_empty_enemy_and_wounded(player_count, occupants):
    snapshot = board(
        {"id": "winterfell", "units": occupants}, player_count=player_count
    )
    result = query(snapshot, " WINTERFELL ")
    assert result["source"]["id"] == "winterfell"
    assert result["movementType"] == "land"
    assert set(destinations(snapshot)) == {
        "castle-black",
        "karhold",
        "the-stony-shore",
        "moat-cailin",
        "white-harbor",
    }
    for target in result["destinations"]:
        assert target["route"] == ["winterfell", target["id"]]
        assert target["transportShips"] == []
    assert "greywater-watch" not in destinations(snapshot)  # No chaining over land.
    assert destinations(snapshot)["castle-black"]["castlePoints"] == 0
    assert destinations(snapshot)["moat-cailin"]["castlePoints"] == 1


@pytest.mark.parametrize("wounded", [False, True])
def test_friendly_ship_chains_and_wounded_transports(wounded):
    snapshot = board(
        {"id": "bay-of-ice", "units": [unit(1, "ship", wounded=wounded)]},
        {"id": "sunset-sea", "units": [unit(2, "ship")]},
    )
    target = destinations(snapshot)["searoad-marches"]
    assert target["route"] == [
        "winterfell",
        "bay-of-ice",
        "sunset-sea",
        "searoad-marches",
    ]
    assert target["transportShips"] == [
        {"regionId": "bay-of-ice", "unitIds": [1]},
        {"regionId": "sunset-sea", "unitIds": [2]},
    ]
    snapshot["childGameState"]["game"]["world"]["regions"][0]["units"][0][
        "allegiance"
    ] = "greyjoy"
    assert "greywater-watch" not in destinations(snapshot)


@pytest.mark.parametrize("house", ["stark", "baratheon", "lannister"])
def test_uses_the_calling_house_for_transport(house):
    snapshot = board({"id": "bay-of-ice", "units": [unit(1, "ship", house)]})
    snapshot["childGameState"]["players"][0]["houseId"] = house
    snapshot["childGameState"]["game"]["houses"][0]["id"] = house
    assert query(snapshot)["houseId"] == house
    assert "greywater-watch" in destinations(snapshot)


@pytest.mark.parametrize("origin", ["bay-of-ice", "port-of-winterfell"])
def test_empty_sea_and_port_origins_infer_ship_movement(origin):
    snapshot = board(
        {"id": "winterfell", "controlPowerToken": "greyjoy"},
        {
            "id": "port-of-winterfell",
            "units": [unit(i, "ship", "greyjoy") for i in range(3)],
        },
    )
    result = query(snapshot, origin)
    assert result["movementType"] == "sea"
    assert set(destinations(snapshot, origin)) == (
        {"sunset-sea", "port-of-winterfell"}
        if origin == "bay-of-ice"
        else {"bay-of-ice"}
    )
    assert all(r["transportShips"] == [] for r in result["destinations"])


def test_supply_orders_neutral_strength_and_port_capacity_do_not_filter_routes():
    snapshot = board(
        {"id": "winterfell", "units": [unit(1, wounded=True)]},
        {"id": "moat-cailin", "garrison": 20},
        {"id": "port-of-winterfell", "units": [unit(i, "ship") for i in range(2, 5)]},
    )
    snapshot["childGameState"]["game"]["supplyRestrictions"] = [[]]
    snapshot["childGameState"]["ordersOnBoard"] = [["winterfell", 1]]
    assert "moat-cailin" in destinations(snapshot)
    assert "port-of-winterfell" in destinations(snapshot, "bay-of-ice")
    assert set(query(snapshot)) == {"houseId", "source", "movementType", "destinations"}
    assert set(destinations(snapshot)["moat-cailin"]) == {
        "id",
        "name",
        "type",
        "route",
        "transportShips",
        "castlePoints",
    }


def test_blocked_origins_destinations_and_bridges():
    snapshot = board(
        {"id": "moat-cailin", "garrison": 1000},
        {"id": "bay-of-ice", "garrison": 1000, "units": [unit(1, "ship")]},
    )
    assert "moat-cailin" not in destinations(snapshot)
    assert "greywater-watch" not in destinations(snapshot)
    assert query(snapshot, "moat-cailin")["destinations"] == []


def test_blocked_shortcut_does_not_hide_a_valid_longer_transport_route():
    snapshot = board(
        {"id": "bay-of-ice", "garrison": 1000, "units": [unit(1, "ship")]},
        *[
            {"id": id, "units": [unit(n, "ship")]}
            for n, id in enumerate(
                [
                    "the-shivering-sea",
                    "the-narrow-sea",
                    "shipbreaker-bay",
                    "east-summer-sea",
                    "west-summer-sea",
                    "sunset-sea",
                    "ironmans-bay",
                ],
                2,
            )
        ],
    )
    route = destinations(snapshot)["greywater-watch"]["route"]
    assert "bay-of-ice" not in route
    assert len(route) > 3


@pytest.mark.parametrize(
    "change", [{"playerCount": 7}, {"vassals": True}, {"setupId": "a-feast-for-crows"}]
)
def test_unsupported_setups_are_explicit(change):
    snapshot = board()
    snapshot["gameSettings"].update(change)
    with pytest.raises(ValueError, match="base games"):
        query(snapshot)


def test_lobby_spectator_and_unknown_area_are_rejected():
    for snapshot, user in [(lobby_snapshot(), "2"), (board(), "spectator")]:
        with pytest.raises(ValueError, match="in-game player"):
            movement_reachability(build_context(snapshot, user), "winterfell")
    with pytest.raises(ValueError, match="Unknown or ambiguous"):
        query(board(), "Winter")


@pytest.mark.asyncio
async def test_tool_refreshes_the_board_and_never_acts_or_mutates():
    snapshot = board({"id": "bay-of-ice", "units": [unit(1, "ship")]})
    client = SimpleNamespace(
        snapshot=snapshot, recent_events=[], connection_generation=1
    )
    run_context = HarnessRunContext(client=client, user_id="2")
    arguments = json.dumps({"area": "winterfell"})

    async def invoke():
        return json.loads(
            await reachable_areas.on_invoke_tool(
                ToolContext(
                    context=run_context,
                    tool_call_id="routes",
                    tool_name="reachable_areas",
                    tool_arguments=arguments,
                ),
                arguments,
            )
        )

    before = copy.deepcopy(snapshot)
    assert "greywater-watch" in {r["id"] for r in (await invoke())["destinations"]}
    assert snapshot == before
    client.snapshot = board()
    assert "greywater-watch" not in {r["id"] for r in (await invoke())["destinations"]}
    assert run_context.action_taken is None


@st.composite
def route_boards(draw):
    snapshot = board(player_count=draw(st.sampled_from([3, 6])))
    snapshot["gameSettings"]["addPortToTheEyrie"] = draw(st.booleans())
    _, static = _regions(build_context(snapshot, "2"))
    origin = draw(st.sampled_from(sorted(static)))
    occupied = draw(st.sets(st.sampled_from(sorted(static)), max_size=20))
    blocked = draw(st.sets(st.sampled_from(sorted(static)), max_size=6))
    regions = []
    for n, id in enumerate(sorted(occupied | blocked), 1):
        units = (
            [
                unit(
                    n,
                    "footman" if static[id]["type"] == "land" else "ship",
                    draw(st.sampled_from(["stark", "greyjoy"])),
                    draw(st.booleans()),
                )
            ]
            if id in occupied
            else []
        )
        regions.append(
            {"id": id, "units": units, "garrison": 1000 if id in blocked else 0}
        )
    snapshot["childGameState"]["game"]["world"]["regions"] = regions
    return snapshot, origin


@settings(max_examples=300, deadline=None)
@given(route_boards())
def test_destinations_match_upstream_geometric_algorithm(server_oracle, case):
    snapshot, source = case
    assert set(destinations(snapshot, source)) == set(
        server_oracle(snapshot, source)["routes"]
    )


@settings(max_examples=250, deadline=None)
@given(route_boards())
def test_routes_are_shortest_valid_paths_without_cycles(case):
    snapshot, source = case
    before = copy.deepcopy(snapshot)
    result = query(snapshot, source)
    regions, static = _regions(build_context(snapshot, "2"))
    assert snapshot == before
    distances = {source: 0}
    frontier = {source} if regions.get(source, {}).get("garrison") != 1000 else set()
    depth = 0
    while frontier:
        depth += 1
        reached = {
            n
            for id in frontier
            for n in static[id]["neighbours"]
            if regions.get(n, {}).get("garrison") != 1000
        } - distances.keys()
        distances.update({id: depth for id in reached})
        frontier = {
            id
            for id in reached
            if result["movementType"] == "land"
            and any(
                u["type"] == "ship" and u["allegiance"] == "stark"
                for u in regions.get(id, {}).get("units", [])
            )
        }
    assert len(result["destinations"]) == len(destinations(snapshot, source))
    for target in result["destinations"]:
        route = target["route"]
        assert route[0] == source and route[-1] == target["id"] != source
        assert len(route) == len(set(route))
        assert len(route) - 1 == distances[target["id"]]
        assert all(b in static[a]["neighbours"] for a, b in zip(route, route[1:]))
        assert all(regions.get(id, {}).get("garrison") != 1000 for id in route)
        assert (target["type"] == "land") == (result["movementType"] == "land")
        assert [t["regionId"] for t in target["transportShips"]] == route[1:-1]
        for bridge in target["transportShips"]:
            assert bridge["unitIds"] == sorted(
                u["id"]
                for u in regions[bridge["regionId"]]["units"]
                if u["type"] == "ship" and u["allegiance"] == "stark"
            )
            assert bridge["unitIds"]


@settings(max_examples=200, deadline=None)
@given(route_boards(), st.data())
def test_removing_a_transport_cannot_add_destinations(case, data):
    snapshot, source = case
    before = set(destinations(snapshot, source))
    changed = copy.deepcopy(snapshot)
    regions = changed["childGameState"]["game"]["world"]["regions"]
    if regions:
        region = data.draw(st.sampled_from(regions))
        region["units"] = [u for u in region["units"] if u["type"] != "ship"]
    assert set(destinations(changed, source)) <= before


@settings(max_examples=200, deadline=None)
@given(route_boards())
def test_irrelevant_legality_facts_cannot_change_routes(case):
    snapshot, source = case
    expected = query(snapshot, source)
    changed = copy.deepcopy(snapshot)
    game = changed["childGameState"]["game"]
    game["supplyRestrictions"] = [[]]
    game["houses"][0]["supplyLevel"] = 0
    changed["childGameState"]["ordersOnBoard"] = [[source, 1]]
    _, static = _regions(build_context(snapshot, "2"))
    for region in game["world"]["regions"]:
        for u in region["units"]:
            u["wounded"] = not u["wounded"]
        if static[region["id"]]["type"] == "land":
            region["units"] = [unit(10000, "knight", "lannister", True)] * 4
            region["controlPowerToken"] = "lannister"
            if region["garrison"] != 1000:
                region["garrison"] = 50
    assert query(changed, source) == expected


@settings(max_examples=200, deadline=None)
@given(route_boards())
def test_source_occupants_do_not_matter_and_input_order_is_irrelevant(case):
    snapshot, source = case
    expected = query(snapshot, source)
    changed = copy.deepcopy(snapshot)
    regions = changed["childGameState"]["game"]["world"]["regions"]
    regions.reverse()
    for region in regions:
        if region["id"] == source:
            region["units"] = []
        else:
            region["units"].reverse()
    assert query(changed, source) == expected
