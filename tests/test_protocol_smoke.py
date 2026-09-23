import argparse
import asyncio
import json
import socket

import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.evaluation import (
    GAME_SERVER_DIR,
    run_game,
)
from raven_harness.protocol_smoke import (
    REQUIRED_TOOL_COVERAGE,
    REQUIRED_TOOL_COUNTS,
    ScriptedProtocolHarness,
    run_protocol_smoke,
)


class BlockingProtocolHarness(ScriptedProtocolHarness):
    rules_oracle_available = False

    def __init__(self) -> None:
        self.started = asyncio.Event()

    async def run_turn(self, record, prepared, context, run_id):
        self.started.set()
        await asyncio.Event().wait()

    async def shutdown(self) -> None:
        return None


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
    blocking_runner = BlockingProtocolHarness()
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
            harness_factory=blocking_runner.bind,
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
            harness_factory=ScriptedProtocolHarness().bind,
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
