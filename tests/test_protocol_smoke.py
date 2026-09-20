import argparse
import asyncio
import json
import socket
from dataclasses import replace

import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.harness.actions import HarnessRunContext, available_tools
from raven_harness.harness.decision import build_decision_contract
from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.harness.observation import build_context
from raven_harness.game.client import OrderSubmission
from raven_harness.evaluation import (
    GAME_SERVER_DIR,
    run_game,
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

    async def send(self, message, *, require_auth=True, expected_generation=None):
        del require_auth
        assert expected_generation == self.connection_generation
        self.sent.append(message)

    async def sync_snapshot(self, timeout=10, *, expected_generation=None):
        del timeout
        assert expected_generation == self.connection_generation
        self.snapshot["leafStateId"] += "-accepted"
        return self.snapshot

    async def submit_orders(self, orders, timeout=10, *, expected_generation=None):
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


class BlockingProtocolRunner:
    rules_oracle_available = False

    def __init__(self) -> None:
        self.started = asyncio.Event()

    async def run_once(self, **_arguments):
        self.started.set()
        await asyncio.Event().wait()

    async def shutdown(self) -> None:
        return None


def test_safe_planning_arguments_use_dynamic_action_order_plan() -> None:
    snapshot = planning_snapshot()
    context = build_context(snapshot, "2")
    submit_orders = available_tools(context)[0]
    observation = {"planningConstraints": {}}

    arguments = _safe_tool_arguments(submit_orders, observation)

    assert arguments == {
        "assignments": [
            {
                "region_id": "winterfell",
                "preferred_order": "march",
                "starred_preference": "avoid",
                "priority": 2,
            },
            {
                "region_id": "white-harbor",
                "preferred_order": "raid",
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
        {"planningConstraints": {}},
    ) == {"assignments": []}


@pytest.mark.asyncio
async def test_scripted_runner_invokes_dynamic_function_tool() -> None:
    snapshot = planning_snapshot()
    client = FakeClient(snapshot)
    context = build_context(snapshot, "2")
    tools = available_tools(context)
    run_context = HarnessRunContext(client=client, user_id="2")
    run_context.decision = build_decision_contract(context, tools)
    observation = {
        "statePath": ["ingame", "planning", "place-orders"],
        "planningConstraints": {},
    }

    result = await ScriptedProtocolRunner().run_once(
        agent_record=None,  # type: ignore[arg-type]
        observation=observation,
        context=run_context,
        tools=tools,
        instructions="unused",
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
    assert smoke["status"] == "completed"
    assert smoke["providerRequests"] == 0
    assert smoke["winner"] == game_result["winner"]
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


@pytest.mark.asyncio
async def test_real_server_resumes_saved_game_with_the_same_agents(tmp_path) -> None:
    if not (GAME_SERVER_DIR / "node_modules" / ".bin" / "ts-node").is_file():
        pytest.skip("upstream game-server dependencies are not installed")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        game_port = int(reservation.getsockname()[1])

    attempt_dir = tmp_path / "resumed-game"
    attempt_dir.mkdir()
    settings = Settings(
        openrouter_token="",
        openai_api_key="",
        otel_exporter_otlp_traces_endpoint="",
        autoplay_max_consecutive_failures=1,
        autoplay_retry_base_seconds=0.1,
        _env_file=None,
    )
    blocking_runner = BlockingProtocolRunner()
    interrupted = asyncio.create_task(
        run_game(
            game_number=1,
            attempt_dir=attempt_dir,
            random_seed=123,
            game_port=game_port,
            max_rounds=1,
            poll_seconds=0.1,
            stall_seconds=30,
            match_timeout_seconds=60,
            settings=settings,
            model_runner=blocking_runner,
        )
    )
    await asyncio.wait_for(blocking_runner.started.wait(), timeout=30)
    interrupted.cancel()
    with pytest.raises(asyncio.CancelledError):
        await interrupted

    saved_game = json.loads((attempt_dir / "game.json").read_text())
    assert isinstance(saved_game["harnessRandomState"], int)
    database = Database(attempt_dir / "harness.db")
    before_agent_ids = [record.id for record in AgentStore(database).list_agents()]
    database.close()
    assert len(before_agent_ids) == 6

    result = await asyncio.wait_for(
        run_game(
            game_number=1,
            attempt_dir=attempt_dir,
            random_seed=123,
            game_port=game_port,
            max_rounds=1,
            poll_seconds=0.1,
            stall_seconds=30,
            match_timeout_seconds=60,
            settings=settings,
            model_runner=ScriptedProtocolRunner(),
            resume=True,
        ),
        timeout=60,
    )

    database = Database(attempt_dir / "harness.db")
    after_agent_ids = [record.id for record in AgentStore(database).list_agents()]
    database.close()
    assert after_agent_ids == before_agent_ids
    assert result["winner"] in {
        assignment["house"]
        for assignment in json.loads((attempt_dir / "assignments.json").read_text())
    }
