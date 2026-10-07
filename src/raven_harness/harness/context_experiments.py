"""Experimental context policies. No changes to the live gameplay pipeline."""

from __future__ import annotations

import copy
import json
from typing import Any

from raven_harness.game.map_reference import observation_map_reference
from raven_harness.harness.card_tools import _ability_texts


def dump(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def situation(observation: dict, engine: dict) -> str:
    game, you = observation["game"], observation["you"]
    round_number, maximum = game["round"], game["maxRounds"]
    lines = [
        f"Now you are {you['houseId']} in round {round_number} of {maximum}, "
        f"at {game['phase']}. There are {maximum - round_number} rounds after this one.",
        f"Public Wildling strength is {engine['wildlingStrength']}. Other houses' secret bids are unknown.",
    ]
    static = {r["id"]: r for r in observation_map_reference(observation)["regions"]}
    houses = {h["id"]: h for h in observation["houses"]}
    throne = observation["tracks"]["ironThrone"]
    for rank, house_id in enumerate(engine["ranking"], 1):
        house = houses[house_id]
        strongholds = sum(
            static[r]["castleLevel"] == 2 for r in house["controlledRegions"]
        )
        lines.append(
            f"Rank {rank}: {house_id} has {house['controlledCastleAreas']} scoring areas TOTAL, "
            f"including {strongholds} strongholds; {house['controlledLandAreas']} land areas, "
            f"Supply {house['supply']}, Iron Throne position {throne.index(house_id) + 1}."
        )
    lines.append(
        "Final-round ranking compares scoring areas, land areas, Supply, then Iron Throne. "
        "A stronghold is one scoring area, not an extra point."
    )
    path = observation["statePath"]
    if "player-mustering" in path:
        lines.append(
            "Now recruit or upgrade with the listed mustering points. Mustering costs ZERO power tokens. "
            "Keep armies within current Supply; upgrading a footman does not increase army size."
        )
    if "tyrion-lannister-ability" in path and game["phase"] == "select-house-card":
        lines.append(
            "Tyrion cancelled your combat card. Choose the REPLACEMENT card that will fight this battle. "
            "You are not discarding a card to draw another."
        )
    combat = engine.get("combat")
    if combat:
        role = (
            "attacking"
            if you["houseId"] == combat["attacker"]
            else (
                "defending"
                if you["houseId"] == combat["defender"]
                else "a potential supporter"
            )
        )
        lines.append(
            f"CURRENT battle: {combat['attacker']} attacks {combat['defender']} at "
            f"{combat['battlefield']}. You are {role}. Tied totals go to {combat['tieWinner']}."
        )
        lines.append(
            "Engine-calculated strength from currently visible choices; unresolved cards, support "
            "and abilities can change it. An unrevealed card is UNKNOWN, not a zero-strength play."
        )
        for side in combat["sides"]:
            units = ", ".join(
                f"{u['type']} #{u['id']} ({'wounded; ' if u['wounded'] else ''}strength {u['strength']})"
                for u in side["units"]
            )
            lines.append(
                f"{side['house']}: {units}; army {side['army']} + order {side['order']} + confirmed support "
                f"{side['support']} + garrison {side['garrison']} + visible card {side['cardStrength']} "
                f"+ spent blade {side['blade']} = current visible total {side['total']}. "
                f"Card: {side['card'] or 'unrevealed/unresolved'}."
            )
            if side["card"]:
                card = next(
                    (
                        c
                        for h in observation["houseCardStatus"]
                        for c in h["availableCards"]
                        if c["id"] == side["card"]
                    ),
                    None,
                )
                if card:
                    lines.append(
                        f"{side['card']} effect: {_ability_texts().get(card['ability'], 'No printed ability.')}"
                    )
        lines.append(
            f"Blade holder: {combat['bladeHolder']}; already used this round: {combat['bladeUsedThisRound']}. "
            "Declining it earlier does not spend it. When offered, using it adds +1."
        )
        lines.append(
            "Eligible supporting areas with REVEALED support orders: "
            + dump(combat["eligibleSupportingAreas"])
            + ". Confirmed declarations: "
            + dump(combat["supporters"])
            + ". Undeclared support is not included in the totals."
        )
    return "\n".join(lines)


def continuity(current: dict, previous: dict | None) -> str:
    if previous is None:
        return "No previous decision is recorded for this house."
    old = previous["observation"]
    assert old["you"]["houseId"] == current["you"]["houseId"], (
        "House-private continuity only"
    )
    lines = [
        f"Since your previous distinct decision in round {old['game']['round']} "
        f"({old['game']['phase']}):"
    ]
    if previous.get("status") == "completed":
        lines.append(
            f"Last accepted action receipt: {previous['action']} {dump(previous['arguments'])}. "
            "These are applied arguments; omitted recruitments were NOT created. "
            "An accepted order or card choice does not establish a won battle."
        )
    else:
        lines.append(
            "The previous attempt did not complete; no accepted action is established by this record."
        )
    for field in (
        "powerTokens",
        "supply",
        "controlledCastleAreas",
        "controlledLandAreas",
    ):
        before, after = old["you"].get(field), current["you"].get(field)
        if before != after:
            lines.append(f"Your {field}: {before} -> {after}.")

    def units(obs):
        return {
            u["id"]: {
                "area": r["id"],
                "type": u["type"],
                "house": u["allegiance"],
                "wounded": u.get("wounded", False),
            }
            for r in obs["board"]
            for u in r["units"]
        }

    before_units, after_units = units(old), units(current)
    for uid in sorted(before_units.keys() | after_units.keys()):
        before, after = before_units.get(uid), after_units.get(uid)
        if before != after:
            lines.append(
                f"Unit {uid}: {dump(before)} -> {dump(after)} (null means absent from this observation)."
            )
    for key in ("revealedOrders", "tracks"):
        if old.get(key) != current.get(key):
            lines.append(f"{key} now: {dump(current.get(key))}.")
    lines.append(
        "Changes are between your decision observations, not proof your action caused every change. "
        "Your notebook contains intentions and fallible claims. Current state and this receipt override it."
    )
    return "\n".join(lines)


def render(policy: str, observation: dict, engine: dict, previous: dict | None) -> str:
    obs = copy.deepcopy(observation)
    briefing = obs.pop("decisionBriefing", "")
    if policy == "baseline":
        return "Current observation:\n" + dump(obs) + "\nCurrent decision:\n" + briefing
    if policy == "briefing":
        return (
            situation(obs, engine)
            + "\n\n"
            + render("baseline", observation, engine, previous)
        )
    if policy == "continuity":
        return (
            continuity(obs, previous)
            + "\n\n"
            + render("baseline", observation, engine, previous)
        )
    if policy not in {"progressive", "verified"}:
        raise ValueError(policy)
    # Mandatory facts stay up front; every omitted public field remains retrievable.
    required = {
        key: obs[key]
        for key in ("you", "pendingDecision", "actionGuidance", "planningConstraints")
        if key in obs
    }
    text = situation(obs, engine) + "\n\n" + continuity(obs, previous)
    text += "\n\nDecision details:\n" + dump(required) + "\n" + briefing
    text += "\n\nPrivate strategic intentions (fallible):\n" + dump(
        obs.get("strategicMemory", {})
    )
    text += (
        "\n\nExplore as needed with inspect_state: board, houses, cards, events, or full. "
        "It returns the same frozen player observation. reachable_areas checks movement routes; "
        "support_eligibility separately checks the battlefield's support orders and adjacency. "
        "inspect_card gives printed effects. These are read-only tools."
    )
    if policy == "verified":
        text += (
            "\nBefore endorsing a concrete move, call reachable_areas for its source. "
            "Before relying on support, call support_eligibility for the battlefield. "
            "Before relying on a card effect, call inspect_card. A route does not establish support. "
            "If a dependency fails, revise the plan. Do not claim verification without a tool result."
        )
    return text
