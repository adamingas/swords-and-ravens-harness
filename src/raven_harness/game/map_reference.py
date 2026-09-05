from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=4)
def load_map_reference(
    player_count: int, add_port_to_eyrie: bool = False
) -> dict[str, Any]:
    """Load the same static Tiled map data used by the Swords & Ravens client."""

    if add_port_to_eyrie:
        filename = "ffc-eyrie-with-port.json"
    elif player_count == 8:
        filename = "westeros-with-essos.json"
    elif player_count == 7:
        filename = "westeros-7p.json"
    else:
        filename = "westeros.json"

    path = (
        Path(__file__).resolve().parents[3]
        / "swords-and-ravens"
        / "agot-bg-game-server"
        / "data"
        / filename
    )
    tiled_map = json.loads(path.read_text())
    regions_layer = next(
        layer for layer in tiled_map["layers"] if layer["name"] == "Regions"
    )
    borders_layer = next(
        layer for layer in tiled_map["layers"] if layer["name"] == "Borders"
    )

    neighbours: dict[str, set[str]] = {}
    for border in borders_layer["objects"]:
        properties = _properties(border)
        start = properties.get("from")
        end = properties.get("to")
        if start and end:
            neighbours.setdefault(start, set()).add(end)
            neighbours.setdefault(end, set()).add(start)

    return {
        "variant": filename.removesuffix(".json"),
        "regions": [
            {
                "id": properties["id"],
                "name": region["name"],
                "type": properties["type"],
                "castleLevel": properties.get("castleLevel", 0),
                "supplyIcons": properties.get("supplyIcons", 0),
                "crownIcons": properties.get("crownIcons", 0),
                "neighbours": sorted(neighbours.get(properties["id"], set())),
            }
            for region in regions_layer["objects"]
            for properties in [_properties(region)]
        ],
    }


def _properties(item: dict[str, Any]) -> dict[str, Any]:
    return {
        property_["name"]: property_["value"]
        for property_ in item.get("properties", [])
    }
