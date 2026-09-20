import pytest

from raven_harness.game.map_reference import (
    format_map_reference,
    load_map_reference,
    observation_map_reference,
)


def test_map_reference_contains_rules_data_missing_from_wire_snapshot() -> None:
    game_map = load_map_reference(6)
    winterfell = next(
        region for region in game_map["regions"] if region["id"] == "winterfell"
    )

    assert winterfell["castleLevel"] == 2
    assert winterfell["supplyIcons"] == 1
    assert winterfell["homeController"] == "stark"
    assert "white-harbor" in winterfell["neighbours"]
    assert "the-shivering-sea" in winterfell["neighbours"]


@pytest.mark.parametrize("count,port", [(6, False), (7, False), (8, False), (4, True)])
def test_compact_map_preserves_every_edge_and_static_game_attribute(count, port):
    reference = load_map_reference(count, port)
    assert observation_map_reference({"mapVariant": reference["variant"]}) == reference
    formatted = format_map_reference(reference)
    rows = {}
    for line in formatted.splitlines():
        if "]: " not in line or line.startswith("Each line"):
            continue
        area_and_attributes, neighbours = line.split("]: ", 1)
        area, attributes = area_and_attributes.split(" [", 1)
        fields = attributes.split("; ")
        rows[area] = (fields[0], dict(field.split("=", 1) for field in fields[1:]),
                      neighbours.split(", ") if neighbours else [])
    assert set(rows) == {region["id"] for region in reference["regions"]}
    for region in reference["regions"]:
        terrain, attributes, neighbours = rows[region["id"]]
        assert terrain == region["type"]
        assert neighbours == region["neighbours"]
        assert int(attributes.get("castle", 0)) == region["castleLevel"]
        assert int(attributes.get("supply", 0)) == region["supplyIcons"]
        assert int(attributes.get("crown", 0)) == region["crownIcons"]
        assert attributes.get("home") == region["homeController"]
