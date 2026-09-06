import argparse
import json
import socket
import sqlite3
from dataclasses import replace

import pytest

from raven_harness.harness.actions import HarnessRunContext, available_tools
from raven_harness.harness.observation import build_context
from raven_harness.game.client import OrderSubmission
from raven_harness.evaluation import (
    GAME_SERVER_DIR,
    TOURNAMENT_HARNESS_ID,
    TOURNAMENT_MODELS,
)
from raven_harness.protocol_smoke import (
    REQUIRED_TOOL_COVERAGE,
    REQUIRED_TOOL_COUNTS,
    ScriptedProtocolRunner,
    UnsupportedSmokeDecision,
    _safe_tool_arguments,
    _select_safe_tool,
    run_protocol_smoke,
)

from conftest import planning_snapshot


class FakeClient:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.recent_events = []
        self.sent = []
        self.connection_generation = 1

    async def send(
        self, message, *, require_auth=True, expected_generation=None
    ):
        del require_auth
        assert expected_generation == self.connection_generation
        self.sent.append(message)

    async def sync_snapshot(
        self, timeout=10, *, expected_generation=None
    ):
        del timeout
        assert expected_generation == self.connection_generation
        self.snapshot["leafStateId"] += "-accepted"
        return self.snapshot

    async def submit_orders(
        self, orders, timeout=10, *, expected_generation=None
    ):
        del timeout
        assert expected_generation == self.connection_generation
        message = {
            "type": "submit-orders",
            "requestId": "order-request-1",
            "orders": orders,
        }
        self.sent.append(message)
        accepted = not any(order.get("orderId") == 999_999 for order in orders)
        if accepted:
            self.snapshot["childGameState"]["childGameState"]["placedOrders"] = [
                [order["regionId"], order["orderId"]] for order in orders
            ]
            self.snapshot["leafStateId"] += "-accepted"
        return OrderSubmission(
            message=message,
            response={
                "type": "submit-orders-response",
                "requestId": "order-request-1",
                "accepted": accepted,
                "reason": "ok" if accepted else "unknown-order",
                "stateId": self.snapshot["leafStateId"],
            },
            snapshot=self.snapshot,
        )


def test_safe_planning_arguments_use_dynamic_action_order_plan() -> None:
    snapshot = planning_snapshot()
    context = build_context(snapshot, "2")
    submit_orders = available_tools(context)[0]
    observation = {
        "planningConstraints": {
            "maxAssignmentsByOrderCategory": {
                "march": 2,
                "raid": 2,
            }
        }
    }

    arguments = _safe_tool_arguments(submit_orders, observation)

    assert arguments == {
        "assignments": [
            {
                "region_id": "winterfell",
                "order": "march",
                "starred_preference": "avoid",
                "priority": 2,
            },
            {
                "region_id": "white-harbor",
                "order": "raid",
                "starred_preference": "avoid",
                "priority": 1,
            },
        ]
    }


def test_safe_planning_arguments_support_empty_order_state() -> None:
    snapshot = planning_snapshot()
    snapshot["childGameState"]["game"]["world"]["regions"] = []
    tool = available_tools(build_context(snapshot, "2"))[0]

    assert _safe_tool_arguments(
        tool,
        {"planningConstraints": {"maxAssignmentsByOrderCategory": {}}},
    ) == {"assignments": []}


@pytest.mark.asyncio
async def test_scripted_runner_invokes_dynamic_function_tool() -> None:
    snapshot = planning_snapshot()
    client = FakeClient(snapshot)
    context = build_context(snapshot, "2")
    tools = available_tools(context)
    run_context = HarnessRunContext(client=client, user_id="2")
    tool = tools[0]
    observation = {
        "statePath": ["ingame", "planning", "place-orders"],
        "planningConstraints": {
            "maxAssignmentsByOrderCategory": {
                "march": 2,
                "raid": 2,
            }
        },
    }

    result = await ScriptedProtocolRunner().run_once(
        agent_record=None,  # type: ignore[arg-type]
        observation=observation,
        context=run_context,
        tools=tools,
        instructions="unused",
        max_turns=1,
        stop_at_tool_names=[tool.name],
        prompt_cache_key="unused",
        trace_metadata={},
    )

    assert run_context.action_taken is not None
    assert run_context.action_taken.name == "submit_orders"
    assert result.usage["requests"] == 0
    assert [item["type"] for item in result.response_items] == [
        "function_call",
        "function_call_output",
    ]
    assert client.sent[-1]["type"] == "submit-orders"
    assert len(client.sent) == 2
    assert result.context_manifest["selectedTool"] == "submit_orders"


def test_scripted_runner_fails_closed_with_dynamic_schema() -> None:
    snapshot = planning_snapshot()
    tool = available_tools(build_context(snapshot, "2"))[0]
    tool = replace(
        tool,
        name="unsafe_action",
    )

    with pytest.raises(UnsupportedSmokeDecision, match="unsafe_action") as caught:
        _select_safe_tool([tool], {"statePath": ["ingame", "unknown"]})

    assert "OrderAssignment" in str(caught.value)


@pytest.mark.asyncio
async def test_real_server_protocol_smoke_writes_verified_artifacts(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not (GAME_SERVER_DIR / "node_modules" / ".bin" / "ts-node").is_file():
        pytest.skip("upstream game-server dependencies are not installed")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        game_port = int(reservation.getsockname()[1])

    output = tmp_path / "protocol-smoke"
    monkeypatch.setattr("raven_harness.evaluation.EVALUATION_ROOT", tmp_path)
    result = await run_protocol_smoke(
        argparse.Namespace(
            output=str(output),
            game_port=game_port,
            stall_seconds=30,
            timeout_seconds=60,
        )
    )

    assert result == output
    smoke = json.loads((output / "smoke.json").read_text())
    game_result = json.loads((output / "result.json").read_text())
    assignments = json.loads((output / "assignments.json").read_text())
    assert smoke["status"] == "completed"
    assert smoke["providerRequests"] == 0
    assert smoke["randomSeed"] == 1
    assert game_result["randomSeed"] == smoke["randomSeed"]
    assert smoke["winner"] == game_result["winner"]
    assert [assignment["model"] for assignment in assignments] == TOURNAMENT_MODELS
    assert {assignment["harness"] for assignment in assignments} == {
        TOURNAMENT_HARNESS_ID
    }
    assert len({assignment["promptSha256"] for assignment in assignments}) == 1
    assert set(smoke["toolCoverage"]["invoked"]) >= REQUIRED_TOOL_COVERAGE
    assert smoke["toolCoverage"]["required"] == REQUIRED_TOOL_COUNTS
    assert all(
        smoke["toolCoverage"]["invoked"][name] >= required
        for name, required in REQUIRED_TOOL_COUNTS.items()
    )
    assert len(smoke["toolCoverage"]["sequence"]) == sum(
        smoke["toolCoverage"]["invoked"].values()
    )
    assert game_result["artifacts"]["sqliteQuickCheck"] == "ok"
    rejection_probe = smoke["orderSubmissionRejectionProbe"]
    assert rejection_probe["accepted"] is False
    assert rejection_probe["reason"] == "unknown-order"
    assert rejection_probe["stateUnchanged"] is True
    assert isinstance(rejection_probe["stateId"], str)
    privacy_probe = smoke["orderSubmissionPrivacyProbe"]
    assert privacy_probe["ownerReceivedExactOrderIds"] is True
    assert privacy_probe["opponentReceivedOnlyHiddenOrders"] is True
    assert privacy_probe["observedOrderCount"] > 0
    connection = sqlite3.connect(output / "harness.db")
    try:
        statuses = dict(
            connection.execute(
                "SELECT status, COUNT(*) FROM agent_runs GROUP BY status"
            ).fetchall()
        )
        provider_requests = connection.execute(
            """
            SELECT COALESCE(SUM(json_extract(usage_json, '$.requests')), 0)
            FROM agent_runs
            """
        ).fetchone()[0]
    finally:
        connection.close()
    assert statuses == {
        "completed": len(smoke["toolCoverage"]["sequence"]),
    }
    assert provider_requests == 0
