"""State-specific action submissions used alongside exploratory model tools."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from typing import Any

from agents import FunctionTool
from agents.tool_context import ToolContext
from jsonschema import Draft202012Validator, ValidationError

from .actions import HarnessRunContext
from .legal import legal_march_options, supply_safe_march_moves
from .observation import HarnessContext


_UNSET = object()
_STRATEGIC_HANDOFF = "strategic_handoff"
SUBMIT_ACTION_TOOL_NAME = "submit_action"


def _fixed_value(schema: dict[str, Any]) -> Any:
    if "const" in schema:
        return deepcopy(schema["const"])
    if len(schema.get("enum", [])) == 1:
        return deepcopy(schema["enum"][0])
    if schema.get("type") == "null":
        return None
    if schema.get("type") == "integer" and "minimum" in schema:
        if schema["minimum"] == schema.get("maximum"):
            return schema["minimum"]
    if schema.get("type") == "array":
        if schema.get("maxItems") == 0:
            return []
        if schema.get("minItems") == schema.get("maxItems") == 1:
            value = _fixed_value(schema["items"])
            if value is not _UNSET:
                return [value]
    if len(schema.get("anyOf", [])) == 1:
        return _fixed_value(schema["anyOf"][0])
    return _UNSET


def _simplify(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove fixed object fields, including fields within destination groups."""
    result = deepcopy(schema)
    if result.get("type") == "object":
        result["properties"] = {
            key: _simplify(value)
            for key, value in schema.get("properties", {}).items()
            if _fixed_value(value) is _UNSET
        }
        result["required"] = list(result["properties"])
    if result.get("type") == "array":
        result["items"] = _simplify(schema["items"])
        if result["items"].get("type") == "object" and not result["items"].get("properties"):
            result["items"]["description"] = (
                "All fields in this item have fixed values supplied automatically. "
                "Use an empty object {} for this item; do not add destination or unit fields. "
                "An array containing [{}] selects the fixed item; an empty array [] selects none."
            )
    for keyword in ("anyOf", "oneOf"):
        if keyword in result:
            result[keyword] = [_simplify(branch) for branch in schema[keyword]]
    return result


def _restore(schema: dict[str, Any], value: Any) -> Any:
    if schema.get("type") == "object":
        result = {}
        for key, field in schema.get("properties", {}).items():
            fixed = _fixed_value(field)
            result[key] = fixed if fixed is not _UNSET else _restore(field, value[key])
        return result
    if schema.get("type") == "array":
        return [_restore(schema["items"], item) for item in value]
    # Current nullable unions contain scalar alternatives.
    return value


class DecisionOutputSchema:
    def __init__(self, schema: dict[str, Any]):
        Draft202012Validator.check_schema(schema)
        self.schema = schema
        self.validator = Draft202012Validator(schema)

    def json_schema(self) -> dict[str, Any]:
        return deepcopy(self.schema)

    def validate_json(self, json_str: str) -> dict[str, Any]:
        try:
            value = json.loads(json_str)
            self.validator.validate(value)
        except (json.JSONDecodeError, ValidationError) as error:
            detail = error.message if isinstance(error, ValidationError) else str(error)
            raise ValueError(f"Invalid action: {detail}") from error
        return value


@dataclass
class DecisionAction:
    tool: FunctionTool
    name: str
    description: str
    argument_schema: dict[str, Any]
    aliases: dict[str, str]

    @property
    def output_schema(self) -> dict[str, Any]:
        return _simplify(self.argument_schema)

    def arguments(self, value: dict[str, Any]) -> dict[str, Any]:
        restored = _restore(self.argument_schema, value)
        return {self.aliases.get(key, key): item for key, item in restored.items()}


@dataclass
class DecisionContract:
    state_id: str | None
    actions: list[DecisionAction]
    output_schema: DecisionOutputSchema

    def submission_tool(self) -> FunctionTool:
        """Expose this decision through one stable action-submission tool."""

        async def submit(tool_context: ToolContext[Any], arguments: str) -> str:
            try:
                answer = self.output_schema.validate_json(arguments)
            except ValueError as error:
                tool_context.context.last_tool_error = str(error)
                return json.dumps(
                    {
                        "accepted": False,
                        "error": str(error),
                        "instruction": (
                            "Correct the arguments using expected_schema below and call submit_action again. "
                            "For multiple actions, decision is an object containing action and that action's fields. "
                            "An object with no properties must be {}. Fixed fields are supplied automatically; "
                            "do not invent aliases. The rules oracle does not know this live action schema."
                        ),
                        "expected_schema": self.output_schema.json_schema(),
                    }
                )
            current = tool_context.context.current_game_context()
            if current.snapshot.get("leafStateId") != self.state_id:
                raise RuntimeError(
                    "The decision changed while you were thinking; a fresh observation is required."
                )
            try:
                result = await self.execute(tool_context.context, answer)
            except ValueError as error:
                tool_context.context.last_tool_error = str(error)
                return json.dumps(
                    {
                        "accepted": False,
                        "error": str(error),
                        "instruction": "Correct the arguments and call submit_action again.",
                    }
                )
            tool_context.context.last_tool_error = None
            return result

        return FunctionTool(
            name=SUBMIT_ACTION_TOOL_NAME,
            description=(
                "Submit your final gameplay action for the current decision. You MUST call "
                "this tool after you have explored and chosen an action. This is the only tool "
                "that can finish the decision. Its fields describe the action currently required "
                "by the game and change between decisions. If the tool rejects the arguments, "
                "inspect the error, correct them, and call submit_action again."
            ),
            params_json_schema=self.output_schema.json_schema(),
            on_invoke_tool=submit,
            strict_json_schema=True,
        )

    async def execute(self, context: HarnessRunContext, answer: dict[str, Any]) -> str:
        """Validate a submitted action, then invoke the server-checked game tool."""
        self.output_schema.validate_json(json.dumps(answer))
        current = context.current_game_context()
        if current.snapshot.get("leafStateId") != self.state_id:
            raise ValueError(
                "The decision changed while you were thinking. Read the new state before submitting."
            )
        if context.action_taken is not None:
            raise ValueError("This decision already has an accepted action.")
        handoff = str(answer[_STRATEGIC_HANDOFF]).strip()
        if not handoff:
            raise ValueError("The strategic handoff must not be empty.")
        context.pending_strategy_note = handoff
        if len(self.actions) == 1:
            action, values = (
                self.actions[0],
                {
                    key: value
                    for key, value in answer.items()
                    if key != _STRATEGIC_HANDOFF
                },
            )
        else:
            values = dict(answer["decision"])
            name = values.pop("action")
            action = next(item for item in self.actions if item.name == name)
        arguments = action.arguments(values)
        # Structured submissions must not silently discard move groups or change
        # an explicit token-spending decision before executing the answer.
        if action.tool.name == "resolve_march":
            from .protocol_tools import UnitMove

            moves = [UnitMove(**move) for move in arguments["moves"]]
            if (
                supply_safe_march_moves(current, arguments["starting_region_id"], moves)
                != moves
            ):
                raise ValueError(
                    "The submitted march exceeds Supply. Choose different unit groups; no move was submitted."
                )
            if arguments["leave_power_token"]:
                source = next(
                    (
                        item
                        for item in legal_march_options(current)
                        if item["regionId"] == arguments["starting_region_id"]
                    ),
                    None,
                )
                moved = {unit for move in moves for unit in move.unit_ids}
                if (
                    not source
                    or not source["canLeavePowerToken"]
                    or moved != set(source["unitIds"])
                ):
                    raise ValueError(
                        "A control token can only be left when legally vacating this source; no move was submitted."
                    )
        encoded = json.dumps(arguments)
        result = await action.tool.on_invoke_tool(
            ToolContext(
                context=context,
                tool_call_id="final-action",
                tool_name=action.tool.name,
                tool_arguments=encoded,
            ),
            encoded,
        )
        if context.action_taken is None:
            raise ValueError(f"The final action was not accepted: {result}")
        return str(result)


_DESTRUCTION_CAUSES = {
    "mammoth-riders-wildling-victory": "The wildlings won and Mammoth Riders imposes unit losses",
    "the-horde-descends-wildling-victory": "The wildlings won and The Horde Descends imposes unit losses",
    "preemptive-raid-wildling-victory": "You chose unit losses for the Preemptive Raid penalty",
    "choose-casualties": "Your army lost the battle and must suffer casualties. The game has already calculated the required loss count; you choose which eligible pieces are lost",
    "resolve-retreat": "Your retreat requires casualties before the survivors can move",
    "mace-tyrell-ability": "Mace Tyrell's ability destroys an eligible enemy Footman",
    "ser-ilyn-payne-ability": "Ser Ilyn Payne's ability destroys an eligible enemy Footman",
    "ser-ilyn-payne-asos-ability": "Ser Ilyn Payne's ability destroys an eligible enemy unit",
    "arianne-martell-1st-ability": "Arianne Martell's ability destroys an eligible enemy Footman",
    "beric-dondarrion-ability": "Beric Dondarrion's ability requires sacrificing a unit",
    "fire-made-flesh": "Fire Made Flesh requires sacrificing the selected Dragon",
}
_UPGRADE_CAUSES = {
    "crow-killers-nights-watch-victory": "The Crow Killers reward lets you replace selected Footmen with Knights",
    "renly-baratheon-ability": "Renly Baratheon's ability upgrades the selected Footman to a Knight",
    "ellaria-sand-1st-ability": "Ellaria Sand's ability upgrades the selected Footman to a Knight",
}


def _unit_selection(context: HarnessContext) -> tuple[str, str, str]:
    path = [state.get("type") for state in reversed(context.path)]
    for state in path:
        if state in _DESTRUCTION_CAUSES:
            return (
                "destroy_units",
                "unit_ids_to_destroy",
                (
                    _DESTRUCTION_CAUSES[state]
                    + ". Selected units are removed from the board. "
                    "You are choosing the losses; the unselected units are not removed by this selection."
                ),
            )
        if state in _UPGRADE_CAUSES:
            return (
                "upgrade_footmen",
                "footman_ids_to_upgrade",
                _UPGRADE_CAUSES[state] + ".",
            )
        if state == "crow-killers-wildling-victory":
            event = next(
                item for item in reversed(context.path) if item.get("type") == state
            )
            if event.get("step") == 1:
                return (
                    "destroy_units",
                    "unit_ids_to_destroy",
                    "The Crow Killers penalty requires destroying Knights because there are too few "
                    "replacement Footmen. Selected Knights are removed from the board. "
                    "Any replacement of surviving Knights happens after this loss selection.",
                )
            if event.get("step") != 0:
                raise ValueError(
                    "Crow Killers must specify whether Knights are destroyed or replaced."
                )
            return (
                "replace_knights",
                "knight_ids_to_replace",
                (
                    "The Crow Killers penalty replaces the selected Knights with available Footmen "
                    "in the same areas. You are choosing which Knights are downgraded."
                ),
            )
    effect = next(
        (
            state.get("description")
            for state in reversed(context.path)
            if state.get("description")
        ),
        None,
    )
    if effect:
        return (
            "select_units",
            "unit_ids",
            f"Resolve this unit-selection effect: {effect}",
        )
    raise ValueError(f"No explicit unit-selection description for state path {path}")


def build_decision_contract(
    context: HarnessContext, tools: list[FunctionTool]
) -> DecisionContract | None:
    if not tools:
        return None
    from .decision_briefing import describe_action

    actions = []
    for tool in tools:
        schema = deepcopy(tool.params_json_schema)
        name, description = tool.name, describe_action(context, tool)
        aliases = {}
        if tool.name == "resolve_march":
            schema["properties"]["moves"]["description"] = (
                "Destination groups and moving unit IDs. Unlisted units stay in the source. "
                "An empty list discards the order. Every group must be legal and fit Supply; "
                "an illegal final action is rejected without submitting the march."
            )
            schema["properties"]["leave_power_token"]["description"] = (
                "Spend one available power token to preserve control when legally vacating "
                "the source area. This must be false if units remain or control cannot be established."
            )
            move = schema["properties"]["moves"]["items"]["properties"]
            ids = move["unit_ids"]["items"].get("enum", [])
            if ids:
                move["unit_ids"]["maxItems"] = len(ids)
                max_moves = max(
                    len(option["unitIds"]) for option in legal_march_options(context)
                )
                moves_schema = schema["properties"]["moves"]
                moves_schema["maxItems"] = min(
                    moves_schema.get("maxItems", max_moves), max_moves
                )
        if tool.name == "select_units":
            name, field, description = _unit_selection(context)
            schema["properties"][field] = schema["properties"].pop("unit_ids")
            schema["required"] = [field]
            aliases[field] = "unit_ids"
            choices = schema["properties"][field]
            # This selection has set semantics: duplicates are not separate units.
            possible = choices.get("items", {}).get("enum", [])
            if possible and choices.get("minItems") == choices.get("maxItems") == len(
                possible
            ):
                choices["const"] = possible
            count = choices.get("maxItems")
            if count is not None:
                description += (
                    f" Choose exactly {count} distinct units."
                    if choices.get("minItems") == count
                    else f" Choose up to {count} distinct units; an empty list declines the effect."
                )
            if (context.leaf or {}).get("selectedUnitsMustBeOfSameRegion"):
                description += " All selected units must be in the same area."
        actions.append(DecisionAction(tool, name, description, schema, aliases))
    if len(actions) == 1:
        schema = actions[0].output_schema
        schema["description"] = actions[0].description
    else:
        branches = []
        for action in actions:
            branch = action.output_schema
            branch["properties"] = {
                "action": {"type": "string", "enum": [action.name]},
                **branch["properties"],
            }
            branch["required"] = ["action", *branch["required"]]
            branch["description"] = action.description
            branches.append(branch)
        schema = {
            "type": "object",
            "properties": {"decision": {"anyOf": branches}},
            "required": ["decision"],
            "additionalProperties": False,
        }
    schema["properties"][_STRATEGIC_HANDOFF] = {
        "type": "string",
        "minLength": 1,
        "maxLength": 2_000,
        "description": (
            "Concise private handoff to your future decisions. Record the current goal, "
            "ordered dependencies, immediate threats, reserved resources, assumptions that "
            "need checking, and why this action advances the plan. Summarize conclusions; "
            "omit exploratory second-guessing and facts already obvious from the board."
        ),
    }
    schema["required"].append(_STRATEGIC_HANDOFF)
    return DecisionContract(
        context.snapshot.get("leafStateId"), actions, DecisionOutputSchema(schema)
    )


def fixed_details(action: DecisionAction) -> dict[str, Any]:
    return {
        key: value
        for key, schema in action.argument_schema["properties"].items()
        if (value := _fixed_value(schema)) is not _UNSET
    }
