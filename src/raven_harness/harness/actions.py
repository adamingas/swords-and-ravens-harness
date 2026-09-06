from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field, replace
from enum import Enum
from itertools import combinations, product
from typing import Annotated, Any, Protocol

from agents import FunctionTool, RunContextWrapper, function_tool
from pydantic import BaseModel, ConfigDict, Field

from .observation import HarnessContext, build_context, is_waiting_for_player

Message = dict[str, Any]


class OrderCategory(str, Enum):
    MARCH = "march"
    DEFENSE = "defense"
    SUPPORT = "support"
    CONSOLIDATE_POWER = "consolidate_power"
    RAID = "raid"


class StarredPreference(str, Enum):
    PREFER = "prefer"
    AVOID = "avoid"


ORDER_TOKENS = {
    OrderCategory.MARCH: [1, 2, 3],
    OrderCategory.DEFENSE: [4, 5, 6],
    OrderCategory.SUPPORT: [7, 8, 9],
    OrderCategory.CONSOLIDATE_POWER: [10, 11, 12],
    OrderCategory.RAID: [13, 14, 15],
}
STARRED_ORDER_TOKENS = {3, 6, 9, 12, 15}
PLANNING_RESTRICTED_TOKENS = {
    "no-march-plus-one-order": {3},
    "no-defense-order": {4, 5, 6},
    "no-support-order": {7, 8, 9},
    "no-consolidate-power-order": {10, 11, 12},
    "no-raid-order": {13, 14, 15},
}
ORDER_TOKEN_STRENGTH = {
    1: -1,
    2: 0,
    3: 1,
    4: 1,
    5: 1,
    6: 2,
    7: 0,
    8: 0,
    9: 1,
    10: 0,
    11: 0,
    12: 1,
    13: 0,
    14: 0,
    15: 1,
}


class GameClient(Protocol):
    snapshot: dict[str, Any] | None
    recent_events: Any

    async def send(self, message: Message, *, require_auth: bool = True) -> None: ...

    async def sync_snapshot(self, timeout: float = 10) -> dict[str, Any]: ...


class HarnessMemory(Protocol):
    """Historical state exposed through a deliberate model tool."""

    def recall_state(self, turns_ago: int) -> dict[str, Any] | None: ...


class OrderAssignment(BaseModel):
    """One semantic order choice assigned to one board region."""

    model_config = ConfigDict(extra="forbid")

    region_id: str = Field(
        min_length=1, description="ID of a region containing your units."
    )
    order: OrderCategory = Field(
        description=(
            "Order category. The harness chooses the concrete modifier and physical "
            "token within this family."
        ),
    )
    starred_preference: StarredPreference = Field(
        description=(
            "Prefer a starred token when it is legal and available, or avoid one "
            "unless the order inventory forces it."
        )
    )
    priority: Annotated[int, Field(ge=0, le=100)] = Field(
        description=(
            "Relative importance from 0 to 100. Higher-priority regions receive "
            "scarce starred tokens and stronger March modifiers first."
        )
    )


@dataclass(frozen=True)
class ActionSpec:
    name: str
    legal_values: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionTaken:
    name: str
    arguments: dict[str, Any]
    messages: list[Message]


@dataclass
class HarnessRunContext:
    """Private runtime state available to tools, but never shown to the model."""

    client: GameClient
    user_id: str
    game_password: str = ""
    memory: HarnessMemory | None = None
    action_taken: ActionTaken | None = None

    def current_game_context(self) -> HarnessContext:
        if self.client.snapshot is None:
            raise RuntimeError("The game connection no longer has a snapshot")
        return build_context(
            self.client.snapshot,
            self.user_id,
            list(self.client.recent_events),
        )

    async def perform(
        self, name: str, arguments: dict[str, Any], messages: Message | list[Message]
    ) -> str:
        context = self.current_game_context()
        if context.ingame is not None and not is_waiting_for_player(context):
            raise RuntimeError("This player is not responsible for the current decision")
        _require_action(context, name)
        return await self._send_messages(name, arguments, messages)

    async def perform_protocol(
        self, name: str, arguments: dict[str, Any], messages: Message | list[Message]
    ) -> str:
        """Send a typed gameplay action and let the game server enforce detailed rules."""

        context = self.current_game_context()
        if self.action_taken is not None:
            raise RuntimeError("This model run has already taken an action")
        if context.ingame is None:
            raise RuntimeError(f"Tool {name!r} is only available after the game starts")
        if not is_waiting_for_player(context):
            raise RuntimeError("This player is not responsible for the current decision")
        from .protocol_tools import gameplay_tools_for_context

        available = {
            tool.name
            for tool in gameplay_tools_for_context(
                context,
                has_specific_tools=bool(available_action_specs(context)),
            )
        }
        if name not in available:
            raise ValueError(f"Tool {name!r} is not legal in the current game state")
        return await self._send_messages(name, arguments, messages)

    async def _send_messages(
        self, name: str, arguments: dict[str, Any], messages: Message | list[Message]
    ) -> str:
        if self.action_taken is not None:
            raise RuntimeError("This model run has already taken an action")
        before = self.current_game_context()
        before_state_id = before.snapshot.get("leafStateId")
        outgoing = messages if isinstance(messages, list) else [messages]
        for message in outgoing:
            await self.client.send(message)
        await self.client.sync_snapshot()
        after = self.current_game_context()
        if not _action_was_acknowledged(
            name, arguments, before_state_id, after
        ):
            raise RuntimeError(
                f"The game server did not accept {name!r}; its authoritative state did not reflect the action"
            )
        self.action_taken = ActionTaken(
            name=name, arguments=arguments, messages=outgoing
        )
        return json.dumps(
            {
                "ok": True,
                "accepted": True,
                "action": name,
                "stateId": after.snapshot.get("leafStateId"),
            }
        )


def _action_was_acknowledged(
    name: str,
    arguments: dict[str, Any],
    before_state_id: Any,
    after: HarnessContext,
) -> bool:
    """Confirm an action from the authoritative post-action player snapshot."""

    if before_state_id != after.snapshot.get("leafStateId"):
        return True

    child = after.snapshot.get("childGameState", {})
    if name == "choose_house" and child.get("type") == "lobby":
        return any(
            house_id == arguments.get("house_id") and str(user_id) == after.user_id
            for house_id, user_id in child.get("players", [])
        )
    if after.ingame is None:
        return False
    if not is_waiting_for_player(after):
        return True

    # A tool can disappear while a parent state remains active. This is the
    # authoritative signal for sequential protocol actions with a stable leaf ID.
    specific_names = {item.name for item in available_action_specs(after)}
    if name in specific_names:
        return False
    from .protocol_tools import gameplay_tools_for_context

    protocol_names = {
        tool.name
        for tool in gameplay_tools_for_context(
            after, has_specific_tools=bool(specific_names)
        )
    }
    return name not in protocol_names


def available_action_specs(context: HarnessContext) -> list[ActionSpec]:
    """Return only actions that make sense for this player in the current state."""

    snapshot = context.snapshot
    leaf = context.leaf
    user_id = context.user_id
    house_id = context.house_id
    actions: list[ActionSpec] = []

    child = snapshot.get("childGameState", {})
    if child.get("type") == "lobby":
        current_seat = next(
            (pair for pair in child.get("players", []) if str(pair[1]) == user_id), None
        )
        occupied = {pair[0] for pair in child.get("players", [])}
        available_house_ids = set(child.get("availableHouseIds", []))
        houses = [
            house["id"]
            for house in child.get("lobbyHouses", [])
            if house["id"] in available_house_ids
            and (
                house["id"] not in occupied
                or (current_seat and current_seat[0] == house["id"])
            )
        ]
        if houses and child.get("readyUsers") is None:
            actions.append(
                ActionSpec(
                    "choose_house",
                    {"house_ids": houses},
                )
            )
        return actions

    if not leaf or not house_id:
        return actions

    simple_choice_state = leaf if leaf.get("type") == "simple-choice" else None
    if simple_choice_state and simple_choice_state.get("houseId") == house_id:
        choices = simple_choice_state.get("choices", [])
        indexed_choices = {index: choice for index, choice in enumerate(choices)}
        actions.append(
            ActionSpec(
                "choose_option",
                {"choice_indexes": list(indexed_choices)},
            )
        )

    select_house_card_state = leaf if leaf.get("type") == "select-house-card" else None
    choose_house_card_state = leaf if leaf.get("type") == "choose-house-card" else None
    if select_house_card_state and select_house_card_state.get("house") == house_id:
        cards = select_house_card_state.get("houseCards", [])
        if cards:
            actions.append(
                ActionSpec(
                    "select_house_card",
                    {"house_card_ids": cards},
                )
            )
    elif choose_house_card_state:
        cards = next(
            (
                pair[1]
                for pair in choose_house_card_state.get("choosableHouseCards", [])
                if pair[0] == house_id
            ),
            [],
        )
        chosen = next(
            (
                pair[1]
                for pair in choose_house_card_state.get("houseCards", [])
                if pair[0] == house_id
            ),
            None,
        )
        if cards and not chosen:
            actions.append(
                ActionSpec(
                    "choose_combat_house_card",
                    {"house_card_ids": cards},
                )
            )

    bidding_state = leaf if leaf.get("type") == "bidding" else None
    if bidding_state and house_id in bidding_state.get("participatingHouses", []):
        existing = next(
            (pair for pair in bidding_state.get("bids", []) if pair[0] == house_id),
            None,
        )
        if existing is None or existing[1] is None or int(existing[1]) < 0:
            maximum = max(0, int((context.house or {}).get("powerTokens", 0)))
            actions.append(
                ActionSpec(
                    "submit_bid",
                    {"minimum": 0, "maximum": maximum},
                )
            )

    select_orders_state = leaf if leaf.get("type") == "select-orders" else None
    if select_orders_state and select_orders_state.get("house") == house_id:
        count = int(select_orders_state["count"])
        regions = select_orders_state.get("possibleRegions", [])
        actions.append(
            ActionSpec(
                "select_orders",
                {"count": count, "region_ids": regions},
            )
        )

    support_state = leaf if leaf.get("type") == "support" else None
    if support_state and support_state.get("houseId") == house_id and context.combat:
        choices = [context.combat["attackerId"], context.combat["defenderId"], "none"]
        actions.append(
            ActionSpec(
                "declare_support",
                {"house_ids": choices},
            )
        )

    place_orders_state = leaf if leaf.get("type") == "place-orders" else None
    if (
        place_orders_state
        and house_id not in place_orders_state.get("readyHouses", [])
        and context.game
        and context.planning
    ):
        regions = [
            region["id"]
            for region in context.game.get("world", {}).get("regions", [])
            if any(
                unit.get("allegiance") == house_id for unit in region.get("units", [])
            )
        ]
        kings_court = context.game.get("kingsCourtTrack", [])
        starred_restrictions = context.game.get("starredOrderRestrictions", [])
        track_position = (
            kings_court.index(house_id) if house_id in kings_court else -1
        )
        max_starred = (
            int(starred_restrictions[track_position])
            if 0 <= track_position < len(starred_restrictions)
            else 0
        )
        active_restrictions = context.planning.get("planningRestrictions", [])
        restricted_token_ids = {
            token_id
            for restriction in active_restrictions
            for token_id in PLANNING_RESTRICTED_TOKENS.get(restriction, set())
        }
        normal_capacity = _normal_order_capacity(restricted_token_ids, max_starred)
        assignment_count = min(
            len(regions), _usable_order_capacity(max_starred)
        )
        required_restricted = max(0, assignment_count - normal_capacity)
        restricted_order_categories = sorted(
            (
                category
                for category, token_ids in ORDER_TOKENS.items()
                if set(token_ids) <= restricted_token_ids
            ),
            key=lambda category: category.value,
        )
        restricted_starred_categories = sorted(
            (
                category
                for category, token_ids in ORDER_TOKENS.items()
                if next(
                    token_id
                    for token_id in token_ids
                    if token_id in STARRED_ORDER_TOKENS
                )
                in restricted_token_ids
            ),
            key=lambda category: category.value,
        )
        actions.append(
            ActionSpec(
                "submit_orders",
                {
                    "region_ids": regions,
                    "assignment_count": assignment_count,
                    "max_starred": max_starred,
                    "restricted_token_ids": restricted_token_ids,
                    "restricted_order_categories": restricted_order_categories,
                    "restricted_starred_categories": restricted_starred_categories,
                    "required_restricted": required_restricted,
                },
            )
        )

    return actions


def available_tools(context: HarnessContext) -> list[FunctionTool]:
    """Build the Agents SDK tool list for a particular player observation."""

    tools = [
        _tool_for_action(action)
        for action in available_action_specs(context)
    ]
    if context.ingame is not None:
        from .protocol_tools import gameplay_tools_for_context

        existing_names = {tool.name for tool in tools}
        tools.extend(
            tool
            for tool in gameplay_tools_for_context(
                context, has_specific_tools=bool(tools)
            )
            if tool.name not in existing_names
        )
    return tools


def _tool_for_action(action: ActionSpec) -> FunctionTool:
    """Narrow model-facing schemas to the values legal in this exact state."""

    tool = _TOOL_CATALOG[action.name]
    schema = deepcopy(tool.params_json_schema)
    properties = schema.get("properties", {})
    legal = action.legal_values

    enum_fields = {
        "choose_house": ("house_id", "house_ids"),
        "choose_option": ("choice_index", "choice_indexes"),
        "select_house_card": ("house_card_id", "house_card_ids"),
        "choose_combat_house_card": ("house_card_id", "house_card_ids"),
        "declare_support": ("house_id", "house_ids"),
    }
    if action.name in enum_fields:
        field_name, legal_name = enum_fields[action.name]
        properties[field_name]["enum"] = legal[legal_name]
    elif action.name == "submit_bid":
        properties["amount"]["minimum"] = legal["minimum"]
        properties["amount"]["maximum"] = legal["maximum"]
    elif action.name == "select_orders":
        region_ids = legal["region_ids"]
        properties["region_ids"]["items"]["enum"] = region_ids
        properties["region_ids"]["minItems"] = legal["count"]
        properties["region_ids"]["maxItems"] = legal["count"]
    elif action.name == "submit_orders":
        assignments = properties["assignments"]
        assignments["minItems"] = legal["assignment_count"]
        assignments["maxItems"] = legal["assignment_count"]
        assignment_properties = schema["$defs"]["OrderAssignment"]["properties"]
        assignment_properties["region_id"]["enum"] = legal["region_ids"]
        restricted = set(legal["restricted_order_categories"])
        allowed_orders = [
            order.value
            for order in OrderCategory
            if legal["required_restricted"] > 0 or order not in restricted
        ]
        assignment_properties["order"]["enum"] = allowed_orders
        schema["$defs"]["OrderCategory"]["enum"] = allowed_orders

    return replace(tool, params_json_schema=schema)


def describe_tools(tools: list[FunctionTool]) -> list[dict[str, Any]]:
    """Return the same model-facing definitions for the dashboard."""

    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.params_json_schema,
            "strict": tool.strict_json_schema,
        }
        for tool in tools
    ]


@function_tool
async def choose_house(ctx: RunContextWrapper[HarnessRunContext], house_id: str) -> str:
    """Join or change to an available house.

    Args:
        house_id: The exact ID of the house to join.
    """
    spec = _require_action(ctx.context.current_game_context(), "choose_house")
    _require_member("house_id", house_id, spec.legal_values["house_ids"])
    return await ctx.context.perform(
        "choose_house",
        {"house_id": house_id},
        {
            "type": "choose-house",
            "house": house_id,
            "password": ctx.context.game_password,
        },
    )


@function_tool
async def choose_option(
    ctx: RunContextWrapper[HarnessRunContext],
    choice_index: Annotated[int, Field(ge=0)],
) -> str:
    """Choose one of the currently offered options.

    Args:
        choice_index: The zero-based index of the chosen option.
    """
    spec = _require_action(ctx.context.current_game_context(), "choose_option")
    _require_member("choice_index", choice_index, spec.legal_values["choice_indexes"])
    return await ctx.context.perform(
        "choose_option",
        {"choice_index": choice_index},
        {"type": "choose-choice", "choice": choice_index},
    )


@function_tool
async def select_house_card(
    ctx: RunContextWrapper[HarnessRunContext], house_card_id: str
) -> str:
    """Select one of the currently offered house cards.

    Args:
        house_card_id: The exact ID of the card to select.
    """
    spec = _require_action(ctx.context.current_game_context(), "select_house_card")
    _require_member("house_card_id", house_card_id, spec.legal_values["house_card_ids"])
    return await ctx.context.perform(
        "select_house_card",
        {"house_card_id": house_card_id},
        {"type": "select-house-card", "houseCard": house_card_id},
    )


@function_tool
async def choose_combat_house_card(
    ctx: RunContextWrapper[HarnessRunContext],
    house_card_id: str,
    force_valyrian_blade_decision: bool,
) -> str:
    """Choose a house card for the current combat.

    Args:
        house_card_id: The exact ID of the card to play.
        force_valyrian_blade_decision: Ask for the blade decision even if the server could skip it.
    """
    spec = _require_action(
        ctx.context.current_game_context(), "choose_combat_house_card"
    )
    _require_member("house_card_id", house_card_id, spec.legal_values["house_card_ids"])
    return await ctx.context.perform(
        "choose_combat_house_card",
        {
            "house_card_id": house_card_id,
            "force_valyrian_blade_decision": force_valyrian_blade_decision,
        },
        {
            "type": "choose-house-card",
            "houseCardId": house_card_id,
            "dontSkipVsbQuestion": force_valyrian_blade_decision,
        },
    )


@function_tool
async def submit_bid(
    ctx: RunContextWrapper[HarnessRunContext],
    amount: Annotated[int, Field(ge=0)],
) -> str:
    """Submit a secret power-token bid.

    Args:
        amount: Number of power tokens to bid.
    """
    spec = _require_action(ctx.context.current_game_context(), "submit_bid")
    if not spec.legal_values["minimum"] <= amount <= spec.legal_values["maximum"]:
        raise ValueError(
            f"amount must be between {spec.legal_values['minimum']} and "
            f"{spec.legal_values['maximum']}"
        )
    return await ctx.context.perform(
        "submit_bid", {"amount": amount}, {"type": "bid", "powerTokens": amount}
    )


@function_tool
async def select_orders(
    ctx: RunContextWrapper[HarnessRunContext], region_ids: list[str]
) -> str:
    """Select a required number of regions from the offered set.

    Args:
        region_ids: Exact IDs of the distinct regions to select.
    """
    spec = _require_action(ctx.context.current_game_context(), "select_orders")
    allowed = spec.legal_values["region_ids"]
    count = spec.legal_values["count"]
    if len(region_ids) != count:
        raise ValueError(f"region_ids must contain exactly {count} items")
    if len(set(region_ids)) != len(region_ids):
        raise ValueError("region_ids must be distinct")
    invalid = [region_id for region_id in region_ids if region_id not in allowed]
    if invalid:
        raise ValueError(f"Illegal region_ids: {_choices(invalid)}")
    return await ctx.context.perform(
        "select_orders",
        {"region_ids": region_ids},
        {"type": "select-orders", "regions": region_ids},
    )


@function_tool
async def declare_support(
    ctx: RunContextWrapper[HarnessRunContext], house_id: str
) -> str:
    """Support one side in combat or refuse support.

    Args:
        house_id: Attacker or defender house ID, or the string 'none'.
    """
    spec = _require_action(ctx.context.current_game_context(), "declare_support")
    _require_member("house_id", house_id, spec.legal_values["house_ids"])
    message = {
        "type": "declare-support",
        "supportedHouseId": None if house_id == "none" else house_id,
    }
    return await ctx.context.perform("declare_support", {"house_id": house_id}, message)


@function_tool
async def submit_orders(
    ctx: RunContextWrapper[HarnessRunContext], assignments: list[OrderAssignment]
) -> str:
    """Place all planning orders and mark the house ready.

    Choose only the order category for each region. The harness assigns concrete
    modifiers and physical tokens deterministically. Each category can be used in
    at most three regions. Star preferences are soft: scarce legal starred tokens
    go to preferred, higher-priority regions first, while unavoidable starred or
    restricted tokens are allocated only when the physical inventory requires them.

    Args:
        assignments: The exact requested number of semantic order assignments.
            Region IDs must be distinct. When there are fewer usable tokens than
            occupied regions, choose which regions receive no order.
    """
    spec = _require_action(ctx.context.current_game_context(), "submit_orders")
    expected_regions = spec.legal_values["region_ids"]
    assignment_count = spec.legal_values["assignment_count"]
    supplied_regions = [assignment.region_id for assignment in assignments]
    if len(assignments) != assignment_count:
        raise ValueError(f"assignments must contain exactly {assignment_count} items")
    if len(set(supplied_regions)) != len(supplied_regions):
        raise ValueError("region_id values must be distinct")
    if not set(supplied_regions) <= set(expected_regions):
        raise ValueError("region_id must be one of the currently eligible regions")
    allocated_assignments = _allocate_order_tokens(
        assignments,
        restricted_token_ids=set(spec.legal_values["restricted_token_ids"]),
        max_starred=spec.legal_values["max_starred"],
        required_restricted=spec.legal_values["required_restricted"],
    )
    arguments = {
        "assignments": [
            assignment.model_dump(mode="json") for assignment in assignments
        ]
    }
    messages = [
        {"type": "place-order", "regionId": region_id, "orderId": None}
        for region_id in expected_regions
    ]
    fallback_tokens = set(spec.legal_values["restricted_token_ids"])
    if spec.legal_values["max_starred"] == 0:
        fallback_tokens.update(STARRED_ORDER_TOKENS)
    ordered_assignments = sorted(
        allocated_assignments,
        key=lambda item: (
            item[1] in fallback_tokens,
            expected_regions.index(item[0].region_id),
        ),
    )
    messages.extend(
        [
            {
                "type": "place-order",
                "regionId": assignment.region_id,
                "orderId": order_id,
            }
            for assignment, order_id in ordered_assignments
        ]
    )
    messages.append({"type": "ready"})
    return await ctx.context.perform("submit_orders", arguments, messages)


def _normal_order_capacity(
    restricted_token_ids: set[int], max_starred: int
) -> int:
    unstarred = sum(
        token_id not in restricted_token_ids
        for token_ids in ORDER_TOKENS.values()
        for token_id in token_ids
        if token_id not in STARRED_ORDER_TOKENS
    )
    starred = sum(
        token_id not in restricted_token_ids for token_id in STARRED_ORDER_TOKENS
    )
    return unstarred + min(max_starred, starred)


def _usable_order_capacity(max_starred: int) -> int:
    if max_starred == 0:
        return sum(len(token_ids) for token_ids in ORDER_TOKENS.values())
    unstarred = sum(
        token_id not in STARRED_ORDER_TOKENS
        for token_ids in ORDER_TOKENS.values()
        for token_id in token_ids
    )
    return unstarred + min(max_starred, len(STARRED_ORDER_TOKENS))


def _allocate_order_tokens(
    assignments: list[OrderAssignment],
    *,
    restricted_token_ids: set[int],
    max_starred: int,
    required_restricted: int,
) -> list[tuple[OrderAssignment, int]]:
    """Allocate physical tokens without exposing their inventory to the model."""

    indexed_groups: dict[OrderCategory, list[tuple[int, OrderAssignment]]] = {
        category: [] for category in OrderCategory
    }
    for index, assignment in enumerate(assignments):
        indexed_groups[assignment.order].append((index, assignment))

    for category, group in indexed_groups.items():
        capacity = len(ORDER_TOKENS[category])
        if len(group) > capacity:
            raise ValueError(
                f"order {category.value} may be assigned to at most {capacity} regions"
            )

    fallback_token_ids = set(restricted_token_ids)
    if max_starred == 0:
        fallback_token_ids.update(STARRED_ORDER_TOKENS)

    category_options: list[
        tuple[OrderCategory, list[tuple[int, ...]]]
    ] = []
    for category in OrderCategory:
        count = len(indexed_groups[category])
        category_options.append(
            (category, list(combinations(ORDER_TOKENS[category], count)))
        )

    candidates: list[
        tuple[tuple[int, int, tuple[int, ...]], list[tuple[OrderAssignment, int]]]
    ] = []
    for option_set in product(*(options for _category, options in category_options)):
        chosen_tokens = [token_id for option in option_set for token_id in option]
        if (
            sum(token_id in fallback_token_ids for token_id in chosen_tokens)
            != required_restricted
        ):
            continue
        starred_count = sum(
            token_id in STARRED_ORDER_TOKENS for token_id in chosen_tokens
        )
        if max_starred > 0 and starred_count > max_starred:
            continue

        allocated: list[tuple[int, OrderAssignment, int]] = []
        for (category, _options), token_ids in zip(
            category_options, option_set, strict=True
        ):
            allocated.extend(
                _assign_category_tokens(indexed_groups[category], token_ids)
            )
        allocated.sort(key=lambda item: item[1].region_id)

        starred_utility = sum(
            (
                1_000_000 + assignment.priority
                if assignment.starred_preference == StarredPreference.PREFER
                else -1_000_000 + assignment.priority
            )
            for _index, assignment, token_id in allocated
            if token_id in STARRED_ORDER_TOKENS
        )
        strength_utility = sum(
            (assignment.priority + 1) * ORDER_TOKEN_STRENGTH[token_id]
            for _index, assignment, token_id in allocated
        )
        token_vector = tuple(-token_id for _index, _assignment, token_id in allocated)
        candidates.append(
            (
                (starred_utility, strength_utility, token_vector),
                [(assignment, token_id) for _index, assignment, token_id in allocated],
            )
        )

    if not candidates:
        raise ValueError(
            "order categories cannot be allocated within the active Westeros "
            f"restrictions, the limit of {max_starred} starred orders, and the "
            "three-token capacity of each order family"
        )

    return max(candidates, key=lambda item: item[0])[1]


def _assign_category_tokens(
    indexed_assignments: list[tuple[int, OrderAssignment]],
    token_ids: tuple[int, ...],
) -> list[tuple[int, OrderAssignment, int]]:
    remaining = list(indexed_assignments)
    result: list[tuple[int, OrderAssignment, int]] = []
    starred_token = next(
        (token_id for token_id in token_ids if token_id in STARRED_ORDER_TOKENS),
        None,
    )
    if starred_token is not None:
        chosen = min(
            remaining,
            key=lambda item: (
                item[1].starred_preference != StarredPreference.PREFER,
                -item[1].priority,
                item[1].region_id,
            ),
        )
        remaining.remove(chosen)
        result.append((*chosen, starred_token))

    remaining_tokens = sorted(
        (token_id for token_id in token_ids if token_id != starred_token),
        key=lambda token_id: (-ORDER_TOKEN_STRENGTH[token_id], token_id),
    )
    remaining.sort(key=lambda item: (-item[1].priority, item[1].region_id))
    result.extend(
        (index, assignment, token_id)
        for (index, assignment), token_id in zip(
            remaining, remaining_tokens, strict=True
        )
    )
    return result


_TOOL_CATALOG: dict[str, FunctionTool] = {
    tool.name: tool
    for tool in [
        choose_house,
        choose_option,
        select_house_card,
        choose_combat_house_card,
        submit_bid,
        select_orders,
        declare_support,
        submit_orders,
    ]
}


def _require_action(context: HarnessContext, name: str) -> ActionSpec:
    action = next(
        (item for item in available_action_specs(context) if item.name == name), None
    )
    if action is None:
        raise ValueError(f"Tool {name!r} is not legal in the current game state")
    return action


def _require_member(field_name: str, value: Any, choices: list[Any]) -> None:
    if value not in choices:
        raise ValueError(f"{field_name} must be one of: {_choices(choices)}")


def _choices(values: list[Any]) -> str:
    return ", ".join(str(value) for value in values)
