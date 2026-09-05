from raven_harness.game.map_reference import load_map_reference


def test_map_reference_contains_rules_data_missing_from_wire_snapshot() -> None:
    game_map = load_map_reference(6)
    winterfell = next(
        region for region in game_map["regions"] if region["id"] == "winterfell"
    )

    assert winterfell["castleLevel"] == 2
    assert winterfell["supplyIcons"] == 1
    assert "white-harbor" in winterfell["neighbours"]
    assert "the-shivering-sea" in winterfell["neighbours"]
