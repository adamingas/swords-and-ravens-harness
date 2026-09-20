"""Read-only access to printed House-card information."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
import json
from typing import Annotated, Any

from agents import RunContextWrapper, function_tool
from pydantic import Field

from .actions import HarnessRunContext


@lru_cache(maxsize=1)
def _ability_texts() -> dict[str, str]:
    resource = files("raven_harness").joinpath("house_card_abilities.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def house_card_details(context: HarnessRunContext, card_id: str) -> dict[str, Any]:
    game = context.current_game_context().game or {}
    query = card_id.strip().casefold()
    matches: list[dict[str, Any]] = []
    for house in game.get("houses", []):
        for pair in house.get("houseCards", []):
            if (
                not isinstance(pair, list)
                or len(pair) != 2
                or not isinstance(pair[1], dict)
            ):
                continue
            card = pair[1]
            if query not in {
                str(card.get("id") or pair[0]).casefold(),
                str(card.get("name") or "").casefold(),
            }:
                continue
            ability_id = card.get("abilityId")
            matches.append(
                {
                    "id": card.get("id") or pair[0],
                    "name": card.get("name"),
                    "house": card.get("houseId") or house.get("id"),
                    "strength": card.get("combatStrength", 0),
                    "swords": card.get("swordIcons", 0),
                    "fortifications": card.get("towerIcons", 0),
                    "available": card.get("state", 0) == 0,
                    "abilityId": ability_id,
                    "abilityText": (
                        _ability_texts().get(str(ability_id))
                        if ability_id is not None
                        else "This card has no printed text ability."
                    ),
                }
            )
    if len(matches) != 1:
        raise ValueError(
            f"Unknown or ambiguous House card {card_id!r}. Use an exact card ID or name "
            "from availableHouseCards or houseCardStatus."
        )
    if matches[0]["abilityId"] is not None and matches[0]["abilityText"] is None:
        matches[0]["abilityText"] = (
            "No local printed text is available for this ability ID. Ask the rules oracle "
            "about the specific card."
        )
    return matches[0]


@function_tool
async def inspect_house_card(
    ctx: RunContextWrapper[HarnessRunContext],
    card_id: Annotated[
        str,
        Field(description="Exact House-card ID or printed name from the current game."),
    ],
) -> str:
    """Return one House card's printed strength, icons, ability and availability.

    Use this before choosing a combat card or evaluating an opponent's possible
    card play. Printed House-card information and discard status are public.
    This read-only lookup does not submit an action or finish the decision. Call
    submit_action when you have made the final choice.
    """

    return json.dumps(house_card_details(ctx.context, card_id))
