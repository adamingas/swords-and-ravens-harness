import copy


from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.harness.observation import build_context
from raven_harness.schemas import AgentCreate

from conftest import make_harness, planning_snapshot


def test_gameplay_prepares_prompt_tools_and_decision(tmp_path) -> None:
    database = Database(tmp_path / "strategic.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(
            name="Wolf",
            model="test-model",
            user_id="2",
            auth_token="secret",
        )
    )
    harness = make_harness(store)
    context = build_context(planning_snapshot(), "2")
    prepared = harness.prepare_turn(record, context, previous_error=None)
    names = [tool.name for tool in prepared.tools]
    assert "submit_orders" not in names
    assert "check_neighbours" in names
    assert "reachable_areas" in names
    assert prepared.instructions.count("\n# Map\n") == 1
    assert "castle-black [land; crown=1]:" in prepared.instructions
    assert "map" not in prepared.observation
    assert prepared.observation["mapVariant"] == "westeros"
    assert "placing planning orders" in prepared.observation["decisionBriefing"]
    assert "check_neighbours looks up" in prepared.observation["decisionBriefing"]
    assert "reachable_areas finds" in prepared.observation["decisionBriefing"]
    assert "not limited to one tool call" in prepared.observation["decisionBriefing"]
    assert "final structured action" in prepared.instructions
    assert "placing planning orders" not in prepared.instructions
    assert "\n# Rules\n" in prepared.instructions
    submit_schema = prepared.decision.output_schema.json_schema()
    assignment = submit_schema["properties"]["assignments"]["items"]["properties"]
    assert assignment["region_id"]["enum"] == ["winterfell", "white-harbor"]

    later_snapshot = copy.deepcopy(planning_snapshot())
    later_snapshot["leafStateId"] = "leaf-later"
    later_snapshot["childGameState"]["game"]["turn"] = 2
    later = harness.prepare_turn(
        record, build_context(later_snapshot, "2"), previous_error=None
    )
    assert later.prompt_cache_key == prepared.prompt_cache_key
    assert later.instructions == prepared.instructions

    retry = harness.prepare_turn(
        record,
        build_context(later_snapshot, "2"),
        previous_error="The model returned text instead of a game action",
    )
    assert (
        "return a corrected structured action" in retry.observation["retryInstruction"]
    )
    alternate_snapshot = copy.deepcopy(later_snapshot)
    alternate_snapshot["gameSettings"]["addPortToTheEyrie"] = True
    alternate = harness.prepare_turn(
        record, build_context(alternate_snapshot, "2"), previous_error=None
    )
    assert alternate.observation["mapVariant"] == "ffc-eyrie-with-port"
    assert "Variant: ffc-eyrie-with-port." in alternate.instructions
    assert alternate.prompt_cache_key != prepared.prompt_cache_key
    database.close()
