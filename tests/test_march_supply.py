"""Regression for the shared march validator's port-capacity check."""

import pytest

from raven_harness.harness.legal import _march_counts_fit_supply
from raven_harness.harness.observation import build_context
from conftest import planning_snapshot


@pytest.mark.parametrize("supply", [None, [[4, 3, 2, 2]]])
def test_port_capacity_is_enforced_with_or_without_supply_table(supply):
    snapshot = planning_snapshot()
    game = snapshot["childGameState"]["game"]
    game["houses"][0]["supplyLevel"] = 0
    if supply is not None:
        game["supplyRestrictions"] = supply
    game["world"]["regions"] = [
        {
            "id": "bay-of-ice",
            "units": [{"id": 1, "type": "ship", "allegiance": "stark"}],
        },
        {
            "id": "port-of-winterfell",
            "units": [
                {"id": n, "type": "ship", "allegiance": "stark"} for n in [2, 3, 4]
            ],
        },
    ]
    assert not _march_counts_fit_supply(
        build_context(snapshot, "2"), "bay-of-ice", [("port-of-winterfell", 1)]
    )
