"""Persistent memory, memory tools and automatic notes after accepted actions."""

from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Annotated, Any
from agents import RunContextWrapper, function_tool
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from ..agent_store import AgentStore
from ..schemas import AgentRecord
from .actions import HarnessRunContext
from .interface import PreparedTurn


class StrategicNotes(BaseModel):
    """Compact durable cognition retained across the complete game."""

    model_config = ConfigDict(
        extra="forbid", alias_generator=to_camel, populate_by_name=True
    )

    round_number: int = Field(
        ge=0, description="Latest game round incorporated into these notes."
    )
    situation_assessment: str = Field(max_length=2_000)
    objectives: list[str] = Field(max_length=8)
    opponent_models: list[str] = Field(max_length=8)
    commitments: list[str] = Field(max_length=8)
    lessons: list[str] = Field(max_length=8)
    model_plan: str = Field(default="", max_length=2_000)
    decision_journal: list[str] = Field(default_factory=list, max_length=12)


@dataclass
class PersistentGameMemory:
    store: AgentStore
    agent_id: str

    def recall_state(self, turns_ago: int) -> dict[str, Any] | None:
        return self.store.recall_state(self.agent_id, turns_ago)

    def list_history(self, limit: int) -> list[dict[str, Any]]:
        return self.store.list_state_history(self.agent_id, limit)

    def get_notes(self) -> dict[str, Any]:
        return {"modelPlan": "", **self.store.get_strategic_memory(self.agent_id)}

    def set_notes(self, notes: dict[str, Any]) -> dict[str, Any]:
        return self.store.set_strategic_memory(self.agent_id, notes)


@function_tool
async def recall_game_state(
    ctx: RunContextWrapper[HarnessRunContext],
    turns_ago: Annotated[
        int,
        Field(
            ge=1,
            le=50,
            description="How many distinct prior decision states to go back.",
        ),
    ],
) -> str:
    """Read an earlier decision's observation from this house's private history.

    Use this to check what changed or revisit an earlier action. turns_ago counts
    decisions, not game rounds. The current observation overrides older facts.
    This query does not submit an action; continue exploring or finish your decision.
    """

    if ctx.context.memory is None:
        raise RuntimeError("Historical memory is unavailable in this harness")
    recalled = ctx.context.memory.recall_state(turns_ago)
    if recalled is None:
        return json.dumps(
            {"found": False, "turnsAgo": turns_ago, "message": "No such prior state."}
        )
    # Older stored observations carried the full static map. Keep recalled
    # dynamic state without reintroducing that duplicate into model context.
    recalled = dict(recalled)
    observation = dict(recalled["observation"])
    old_map = observation.pop("map", None)
    if old_map is not None:
        observation.setdefault("mapVariant", old_map["variant"])
    recalled["observation"] = observation
    return json.dumps({"found": True, "turnsAgo": turns_ago, **recalled})


@function_tool
async def remember_strategy(
    ctx: RunContextWrapper[HarnessRunContext],
    note: Annotated[
        str,
        Field(
            min_length=1,
            max_length=2_000,
            description=(
                "Concise replacement for your durable multi-round strategic plan. "
                "Use only when the plan materially changes."
            ),
        ),
    ],
) -> str:
    """Replace your private strategic plan after your final action is accepted.

    Write a concise plan you want to remember at future decisions. This queues
    a note only: it does not place orders, move units or finish the decision.
    After saving the note, continue exploring or finish your decision.
    """

    stripped = note.strip()
    if not stripped:
        raise ValueError("Strategy note must contain non-whitespace text")
    ctx.context.pending_strategy_note = stripped
    return json.dumps(
        {
            "ok": True,
            "pending": True,
            "message": "Strategy note will be saved after an accepted gameplay action.",
        }
    )


def _automatic_notes(
    record: AgentRecord,
    prepared: PreparedTurn,
    context: HarnessRunContext,
    existing: dict[str, Any],
) -> dict[str, Any]:
    """Maintain a compact strategic index after every model decision."""

    observation = prepared.observation
    game = observation.get("game", {})
    house_id = observation.get("you", {}).get("houseId") or record.name
    positions = observation.get("strategicOverview", {}).get("housePositions", [])
    own = next(
        (position for position in positions if position.get("houseId") == house_id),
        {},
    )
    situation = (
        f"Round {game.get('round') or 0}, phase {game.get('phase') or 'unknown'}: "
        f"{house_id} controls {own.get('castles', 0)} castle regions and "
        f"{own.get('landAreas', 0)} land areas, with "
        f"{own.get('powerTokens', 0)} power tokens and supply "
        f"{own.get('supplyTrack', 0)}."
    )
    opponents = [
        (
            f"{position.get('houseId')}: {position.get('castles', 0)} castles, "
            f"{position.get('landAreas', 0)} land areas, "
            f"{position.get('powerTokens', 0)} power tokens"
        )
        for position in positions
        if position.get("houseId") != house_id
    ][:8]
    action = context.action_taken
    action_summary = (
        f"Round {game.get('round') or 0} {game.get('phase') or 'unknown'}: "
        f"used {action.name} {json.dumps(action.arguments, separators=(',', ':'))[:500]}"
        if action
        else ""
    )
    commitments = [*existing.get("commitments", [])[-7:]]
    if action_summary:
        commitments.append(action_summary)
    objectives = existing.get("objectives") or [
        "Reach the castle victory threshold before all opponents.",
        "Protect controlled castles while expanding toward the nearest attainable one.",
        "Keep armies supply-compatible and preserve decisive house cards.",
    ]
    return StrategicNotes(
        round_number=int(game.get("round") or 0),
        situation_assessment=situation,
        objectives=objectives[:8],
        opponent_models=opponents,
        commitments=commitments[-8:],
        lessons=existing.get("lessons", [])[-8:],
        model_plan=(
            context.pending_strategy_note
            if context.pending_strategy_note is not None
            else str(existing.get("modelPlan") or "")
        ),
        decision_journal=[
            *existing.get("decisionJournal", [])[-11:],
            *(
                [
                    f"Round {game.get('round') or 0} {game.get('phase') or 'unknown'}: "
                    f"{context.pending_strategy_note}"
                ]
                if context.pending_strategy_note is not None
                else []
            ),
        ][-12:],
    ).model_dump(by_alias=True)
