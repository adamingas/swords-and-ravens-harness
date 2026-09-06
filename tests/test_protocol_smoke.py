import argparse
import json
import socket
import sqlite3
from dataclasses import replace

import pytest

from raven_harness.harness.actions import HarnessRunContext, available_tools
from raven_harness.harness.observation import build_context
from raven_harness.evaluation import GAME_SERVER_DIR
from raven_harness.protocol_smoke import (
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

    async def send(self, message, *, require_auth=True):
        del require_auth
        self.sent.append(message)

    async def sync_snapshot(self, timeout=10):
        del timeout
        self.snapshot["leafStateId"] += "-accepted"
        return self.snapshot


def test_safe_planning_arguments_use_dynamic_non_active_order_capacity() -> None:
    snapshot = planning_snapshot()
    context = build_context(snapshot, "2")
    submit_orders = available_tools(context)[0]
    observation = {
        "planningConstraints": {
            "maxAssignmentsByOrderCategory": {
                "defense": 2,
                "support": 2,
            }
        }
    }

    arguments = _safe_tool_arguments(submit_orders, observation)

    assert arguments == {
        "assignments": [
            {
                "region_id": "winterfell",
                "order": "defense",
                "starred_preference": "avoid",
                "priority": 2,
            },
            {
                "region_id": "white-harbor",
                "order": "defense",
                "starred_preference": "avoid",
                "priority": 1,
            },
        ]
    }


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
                "defense": 2,
                "support": 2,
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
    assert client.sent[-1] == {"type": "ready"}


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
async def test_real_server_protocol_smoke_writes_verified_artifacts(tmp_path) -> None:
    if not (GAME_SERVER_DIR / "node_modules" / ".bin" / "ts-node").is_file():
        pytest.skip("upstream game-server dependencies are not installed")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        game_port = int(reservation.getsockname()[1])

    output = tmp_path / "protocol-smoke"
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
    assert smoke["status"] == "completed"
    assert smoke["providerRequests"] == 0
    assert smoke["winner"] == game_result["winner"]
    assert game_result["artifacts"]["sqliteQuickCheck"] == "ok"
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
    assert statuses == {"completed": 7}
    assert provider_requests == 0
