"""Plain-language instructions rebuilt for each player decision."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from agents import FunctionTool

from .observation import HarnessContext
from .legal import (
    _controller,
    _neutral_force,
    _reachable_regions,
    _regions,
    legal_march_options,
)

if TYPE_CHECKING:
    from .decision import DecisionContract


_ACTION_DESCRIPTIONS = {
    "submit_orders": (
        "You are placing planning orders for this round. Assign an order preference to each "
        "required occupied area, respecting the displayed restrictions and starred-order limit. "
        "submit_action submits the whole order draft and marks your house ready. "
        "These orders determine what your armies can do later; this decision does not move units. "
        "A single land unit can capture an empty castle with a March order. Defence and Support "
        "orders do not move that unit or claim neighbouring land. Consolidate Power in an open "
        "sea earns no power; a port follows the separate port rule. "
        "The harness allocates the physical order tokens, preserving higher-priority preferences "
        "when not all requested categories fit the available tokens."
        " Priority 100 is most important; 0 is least important. Plan how to gain castle areas "
        "this round. Use Defence or Support when you have a concrete battle to protect or assist; "
        "otherwise these orders can leave an army unable to expand."
    ),
    "resolve_march": (
        "You are resolving one of your March orders. You choose which remaining March area "
        "to resolve now. Choose which units move and their "
        "destinations. Units you omit remain in the source area; you may split an army across "
        "destinations, and a single unit can march on its own. An empty moves list removes this "
        "March order without moving anyone. Only one destination may start combat. "
        "Use the reachable destinations in actionGuidance and keep the resulting armies within "
        "Supply. Leaving a control token costs one available power token and preserves control "
        "of the source when you legally vacate it. Compare castles gained and lost, and count "
        "support around the destination battlefield before choosing an attack. "
        "submit_action resolves this one order; another remaining order is a later decision."
    ),
    "resolve_raid": (
        "You are resolving one Raid order. Choose an eligible adjacent enemy order to remove, "
        "or choose a null target to discard your Raid without raiding. Your units do not move."
    ),
    "choose_combat_house_card": (
        "A battle is underway. Choose an available House card for this combat. Its strength, "
        "icons and ability affect the battle, and playing it spends that card until it is recovered."
    ),
    "declare_support": (
        "You are deciding whom to support in the current battle. Your supporting units remain "
        "where they are; this choice commits their eligible combat strength to the selected side."
    ),
    "submit_bid": (
        "You are submitting a power-token bid for the current event. The tokens bid are spent "
        "under that event's rules. Read the event and your available power before choosing the amount."
    ),
    "muster_units": (
        "You are recruiting units at the eligible mustering areas. Spend their mustering points "
        "on new pieces or Footman upgrades, using available pieces and legal destinations. "
        "The resulting armies must fit your current Supply. Upgrading a Footman replaces it "
        "with the chosen unit and does not increase that army's number of units."
    ),
    "resolve_consolidate_power": (
        "You are resolving a Consolidate Power order in one of the listed areas. "
        "Choosing gain_power_tokens resolves that order now and collects its power income. "
        "When muster_units is offered, choosing it opens a separate recruitment decision "
        "for that area's mustering points. These are alternatives: taking power does not "
        "also recruit units. Choose the option that serves your plan for this army."
    ),
    "skip_mustering": "Decline this mustering opportunity and recruit no units.",
    "auto_reconcile_armies": (
        "Your armies exceed the current Supply limit. Submitting this answer asks the harness "
        "to compute and destroy a minimum number of units so the remaining armies fit Supply."
    ),
    "use_valyrian_steel_blade": (
        "Decide whether to spend the available Valyrian Steel Blade use on this battle for "
        "+1 combat strength. Declining preserves its use for a later battle this round."
    ),
    "replace_raven_order": "Use the Messenger Raven to replace one of your placed orders with an available order token.",
    "skip_raven_order_replacement": "Decline the Messenger Raven opportunity and keep the placed orders.",
    "inspect_top_wildling_card": (
        "Use this Messenger Raven opportunity to inspect the top Wildling card. "
        "This spends the decision; keeping or burying the revealed card is a subsequent decision."
    ),
    "place_inspected_wildling_card": "Choose whether the inspected Wildling card stays on top of its deck or moves to the bottom.",
    "call_for_support_against_neutral_force": (
        "Ask the eligible foreign houses for support against a neutral force before committing "
        "the march. Their support decisions can change whether that attack is legal."
    ),
    "resolve_track_ties": "Resolve the tied bids on the current influence track by ranking the tied houses in your preferred order.",
    "select_westeros_card": "Choose the Westeros event to resolve from the cards offered for this decision.",
    "choose_house": "Choose an available house to occupy in this game lobby.",
    "select_orders": "Select the required number of eligible orders for the current event's effect.",
    "select_house_card": "Select an eligible House card for the current event's effect.",
}


def describe_action(context: HarnessContext, tool: FunctionTool) -> str:
    path = {state.get("type") for state in context.path}
    leaf = context.leaf or {}
    if tool.name == "choose_option":
        choices = "; ".join(
            f"{index}: {choice}" for index, choice in enumerate(leaf.get("choices", []))
        )
        return f"Choose one option for this event. {leaf.get('description', '')} Available choices: {choices}."
    if tool.name == "select_region" and "resolve-retreat" in path:
        return (
            "Your army lost the battle. Choose one of the legal retreat areas for its survivors. "
            "Any required retreat casualties are a separate selection; this answer chooses the destination. "
            "Survivors become routed and cannot move again this round. They recover during cleanup "
            "at the end of this round."
        )
    description = _ACTION_DESCRIPTIONS.get(
        tool.name, tool.description.split("\n\nArgs:", 1)[0]
    )
    if tool.name in {
        "submit_bid",
        "select_orders",
        "select_house_card",
        "select_region",
    }:
        event = next(
            (
                state.get("description")
                for state in reversed(context.path)
                if state.get("description")
            ),
            None,
        )
        if event:
            description += f" The current event says: {event}"
        elif tool.name == "submit_bid":
            if "wildlings-attack" in path:
                description += " This bid contributes to the Night's Watch defence against the wildlings."
            else:
                description += (
                    " pendingDecision.currentTrack explicitly names the influence track. "
                    "Other houses' -1 bid values mean submitted but secret, never a zero bid."
                )
    return description


_EXPLORATION_DESCRIPTIONS = {
    "reachable_areas": (
        "reachable_areas finds geographic movement routes from any area, even empty or "
        "enemy-held, using your current ships for transport. It returns routes and "
        "transport ships, not legal unit groups. Armies, orders, Supply, combat strength "
        "and port control do not filter the results; use actionGuidance for legality."
    ),
    "check_neighbours": (
        "check_neighbours looks up an area's direct neighbours and their current owners, units, "
        "wounds, orders, terrain and castles. Ask about the battlefield when checking possible "
        "support. Direct neighbours are not the same as all legal ship-transport destinations."
    ),
    "inspect_house_card": (
        "inspect_house_card returns the exact printed strength, combat icons and ability text "
        "for one House card in this game, plus whether it is currently available. Use it when "
        "card text could change a combat calculation."
    ),
    "recall_game_state": (
        "recall_game_state retrieves an earlier observation from your private game history. "
        "Use it when a past decision matters; the current observation takes precedence if facts differ."
    ),
    "remember_strategy": (
        "remember_strategy records a proposed update to your private plan. It does not place orders "
        "or move units, and the note is saved only after your final action is accepted."
    ),
    "ask_rules_oracle": (
        "ask_rules_oracle asks a rules specialist a focused question using the local rulebook and FAQ. "
        "It explains rules; it does not choose or submit your action."
    ),
}


def _fixed_detail_sentence(name: str, value: object) -> str:
    area = str(value).replace("-", " ").title()
    if name == "starting_region_id":
        return f"This march starts in {area}."
    if name in {"region_id", "order_region_id"}:
        return f"The area for this choice is {area}."
    if name == "leave_power_token" and value is False:
        return "No control token will be spent."
    if name == "moves" and value == []:
        return "No units can move; this choice only removes the March order."
    if name == "unit_ids_to_destroy":
        return f"All eligible units must be removed: {json.dumps(value)}."
    return f"{name.replace('_', ' ').capitalize()} is fixed at {json.dumps(value)}."


def _board_briefing(context: HarnessContext, contract: DecisionContract) -> list[str]:
    """Explain only the board facts relevant to this decision, without choosing it."""
    if context.game is None or context.house_id is None:
        return []
    regions, static = _regions(context)
    names = {key: value["name"] for key, value in static.items()}
    paragraphs = []
    actions = {action.tool.name for action in contract.actions}
    if actions & {"resolve_march", "submit_orders"}:
        paragraphs.append(
            "A castle and a stronghold each count as ONE controlled castle area for victory. "
            "The map's castle=2 denotes a stronghold's mustering capacity, not two victory points. "
            "Single units in separate areas do not count as armies against Supply; an army has two or more units."
        )
    if "resolve_march" in actions:
        paragraphs.append(
            "Before attacking another army, use check_neighbours on that battlefield "
            "during exploration to verify the supporting areas."
        )
        for source in legal_march_options(context):
            area = source["regionId"]
            reference = static[area]
            if reference["type"] != "land":
                continue
            castle = bool(reference.get("castleLevel"))
            empty_controller = regions.get(area, {}).get(
                "controlPowerToken"
            ) or reference.get("homeController")
            if empty_controller == context.house_id:
                control = "Your existing control token or home symbol keeps this area yours when you leave it empty; no new token is needed."
            elif source["canLeavePowerToken"]:
                control = "Moving every unit out without leaving a power token loses this area. You can spend one power token to keep it."
            else:
                control = "Moving every unit out loses this area; you cannot leave a power token here. Keeping at least one unit preserves it."
            paragraphs.append(
                f"{names[area]} currently contributes {1 if castle else 0} castle area to your score. {control}"
            )
            targets = []
            for target in source["reachableRegions"]:
                target_id = target["regionId"]
                if not static[target_id].get("castleLevel"):
                    continue
                if target["controller"] == context.house_id:
                    effect = "already yours; no castle gain"
                elif target["neutralForce"]:
                    effect = "neutral force must be defeated"
                elif target["triggersCombat"]:
                    effect = "enemy defence must be defeated"
                else:
                    effect = "capture gains one castle area without combat"
                targets.append(f"{names[target_id]} ({effect})")
            if targets:
                paragraphs.append(
                    f"Castle destinations reachable from {names[area]}: "
                    + "; ".join(targets)
                    + ". Check the listed Supply-safe groups before choosing units."
                )
    if "submit_orders" in actions:
        for area, region in regions.items():
            if (
                static.get(area, {}).get("type") != "land"
                or _controller(area, regions, static) != context.house_id
            ):
                continue
            if not any(
                unit.get("allegiance") == context.house_id
                for unit in region.get("units", [])
            ):
                continue
            points = int(bool(static[area].get("castleLevel")))
            paragraphs.append(
                f"{names[area]} contributes {points} castle area to your score."
            )
            if static[area].get("homeController") == context.house_id:
                paragraphs.append(
                    f"Your home symbol keeps {names[area]} yours when your last unit leaves; no power token is needed."
                )
            targets = sorted(
                names[target]
                for target in _reachable_regions(
                    area, "land", context.house_id, regions, static
                )
                if static[target].get("castleLevel")
                and _controller(target, regions, static) != context.house_id
                and not regions.get(target, {}).get("units")
                and not regions.get(target, {}).get("garrison", 0)
                and _neutral_force(context, target) is None
            )
            if targets:
                paragraphs.append(
                    f"From {names[area]}, the current land connections and friendly Ships reach these "
                    f"undefended castle areas you do not own: {', '.join(targets)}. A March order here "
                    "would let you try to capture one later; opponents may change the position before it resolves. "
                    "Check Supply and preserve control of any castle you leave."
                )
    if "select_units" in actions:
        eligible = set((context.leaf or {}).get("possibleUnits", []))
        labels = []
        eligible_owners = []
        for area, region in regions.items():
            for unit in region.get("units", []):
                if unit["id"] in eligible:
                    eligible_owners.append(unit.get("allegiance"))
                    labels.append(
                        f"{unit['id']}: {unit.get('allegiance', 'unknown owner')} {unit['type']} in {names.get(area, area)}"
                    )
        if labels:
            paragraphs.append("The eligible pieces are " + "; ".join(labels) + ".")
        if any(action.name == "destroy_units" for action in contract.actions):
            if eligible_owners and all(
                owner == context.house_id for owner in eligible_owners
            ):
                paragraphs.append(
                    "These are your units. Choose losses that preserve your ability to hold and capture "
                    "castle areas. Only land units occupy land castles. Ships are useful for transport "
                    "when they occupy the connecting sea areas; Ships sitting in a port do not provide "
                    "that transport."
                )
            elif eligible_owners and all(
                owner is not None and owner != context.house_id
                for owner in eligible_owners
            ):
                paragraphs.append(
                    "These are enemy units. You are choosing which enemy pieces to destroy, "
                    "so consider which losses most weaken their position."
                )
            for area, region in regions.items():
                if not any(unit["id"] in eligible for unit in region.get("units", [])):
                    continue
                reference = static[area]
                if reference["type"] == "land":
                    paragraphs.append(
                        f"{names[area]} contains {'a castle or stronghold' if reference.get('castleLevel') else 'no castle or stronghold'}."
                    )
                elif reference["type"] == "port":
                    for neighbour in reference["neighbours"]:
                        if static[neighbour]["type"] != "sea":
                            continue
                        occupants = regions.get(neighbour, {}).get("units", [])
                        force = (
                            ", ".join(
                                f"{unit['allegiance']} {unit['type']}"
                                for unit in occupants
                            )
                            or "no units"
                        )
                        paragraphs.append(
                            f"{names[area]}'s adjacent sea is {names[neighbour]}, currently containing {force}."
                        )
    return paragraphs


def build_decision_briefing(
    context: HarnessContext,
    contract: DecisionContract,
    exploration_tools: list[FunctionTool],
) -> str:
    from .decision import fixed_details

    identity = (
        f"You are playing House {(context.house or {}).get('name', context.house_id)}"
        if context.house_id
        else "You are choosing your seat"
    )
    round_number = (context.game or {}).get("turn")
    opening = identity + (
        f" in round {round_number}." if round_number is not None else "."
    )
    paragraphs = [
        opening + " This is a new decision; you have not submitted an action for it."
    ]
    for action in contract.actions:
        paragraphs.append(
            action.description
            if len(contract.actions) == 1
            else f"{action.name}: {action.description}"
        )
        fixed = fixed_details(action)
        if fixed:
            paragraphs.append(
                " ".join(
                    _fixed_detail_sentence(name, value) for name, value in fixed.items()
                )
                + " These details are already settled. submit_action only needs the remaining choices."
            )
    paragraphs.extend(_board_briefing(context, contract))
    if exploration_tools:
        paragraphs.append(
            "Explore liberally before deciding. Use the tools whenever they can test a route, "
            "target, threat, rule, memory, or assumption. Do not avoid a useful tool call merely "
            "to save tokens. The available tools have these purposes:"
        )
        paragraphs.extend(
            _EXPLORATION_DESCRIPTIONS[tool.name] for tool in exploration_tools
        )
        paragraphs.append(
            "These tools do not submit a gameplay action. After a tool returns, inspect its result "
            "and follow up wherever uncertainty remains. Use multiple calls when they test different "
            "targets, threats, rules, or memories. Treat tool results as evidence and revise your "
            "plan when they contradict an assumption. You are not limited to one tool call."
        )
    paragraphs.append(
        "Explore as deeply as the decision warrants. Tool calls return evidence to this same run, "
        "so inspect each result and continue exploring when useful. When ready, you MUST call "
        "submit_action with arguments matching its current schema. That tool is the only way to "
        "submit the action and finish this decision. The harness checks it against the current "
        "game state before sending it to the server."
    )
    return "\n\n".join(paragraphs)
