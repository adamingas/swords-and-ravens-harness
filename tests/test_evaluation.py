import argparse
import asyncio
import hashlib
import json
from types import SimpleNamespace

import httpx
import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.evaluation import (
    HOUSES,
    PROMPT_CONFIGURATIONS,
    _build_provenance,
    _collect_openrouter_generations,
    _evaluation_schedule,
    _persisted_response_rows,
    _progress_signature,
    _require_sqlite_quick_check,
    _terminal_winner,
    _validate_evaluation_schedule,
    _validate_winner_house,
    _wait_for_terminal_game_document,
    house_rotation,
    summarize_results,
    user_rotation,
)
from raven_harness.schemas import AgentCreate


def test_twelve_game_rotation_assigns_each_house_twice() -> None:
    names = [configuration.name for configuration in PROMPT_CONFIGURATIONS]

    for name in names:
        assignments = [house_rotation(game)[name] for game in range(1, 13)]
        assert sorted(assignments) == sorted(HOUSES * 2)

    for game in range(1, 13):
        assert sorted(house_rotation(game).values()) == sorted(HOUSES)


def test_twelve_game_user_rotation_makes_each_configuration_owner_twice() -> None:
    names = [configuration.name for configuration in PROMPT_CONFIGURATIONS]

    for game in range(1, 13):
        assert sorted(user_rotation(game).values()) == [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
        ]

    for name in names:
        user_ids = [user_rotation(game)[name] for game in range(1, 13)]
        assert user_ids.count("1") == 2
        assert sorted(user_ids) == sorted([str(value) for value in range(1, 7)] * 2)


def test_schedule_validation_ignores_attempt_history_but_rejects_user_changes() -> None:
    schedule = _evaluation_schedule(12)
    schedule[0]["attempts"].append({"status": "completed"})

    _validate_evaluation_schedule(schedule, 12)

    schedule[0]["users"]["Balanced"] = "2"
    with pytest.raises(RuntimeError, match="different house or user schedule"):
        _validate_evaluation_schedule(schedule, 12)


def test_progress_signature_includes_runtime_and_completed_run_progress() -> None:
    records = [SimpleNamespace(id="agent-1")]
    observations = [{"game": {"stateId": "leaf-1", "phase": "planning"}}]
    idle = [
        SimpleNamespace(
            status="connected", current_run_id=None, run_started_at=None
        )
    ]
    running = [
        SimpleNamespace(
            status="running", current_run_id="run-1", run_started_at="now"
        )
    ]

    initial = _progress_signature(
        records=records,
        observations=observations,
        runtimes=idle,
        run_counts=[0],
    )
    in_flight = _progress_signature(
        records=records,
        observations=observations,
        runtimes=running,
        run_counts=[0],
    )
    completed = _progress_signature(
        records=records,
        observations=observations,
        runtimes=idle,
        run_counts=[1],
    )

    assert initial != in_flight
    assert in_flight != completed
    assert initial != completed


def test_provenance_hashes_prompts_rules_and_omits_api_key(tmp_path) -> None:
    rules_path = tmp_path / "rules.json"
    rules_path.write_text('{"rules": true}\n')
    settings = Settings(
        rules_path=rules_path,
        openrouter_token="do-not-record-this-token",
        openrouter_base_url="https://url-secret@example.test/api/v1?key=hidden",
        model_max_concurrency=3,
    )
    args = argparse.Namespace(
        model="z-ai/glm-5.3-flash",
        game_port=5101,
        max_rounds=None,
        poll_seconds=1.0,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
    )

    provenance = _build_provenance(args, settings)

    assert provenance["repositories"]["root"]["commit"]
    assert provenance["repositories"]["swordsAndRavens"]["commit"]
    assert len(provenance["repositories"]["root"]["worktreeSha256"]) == 64
    assert len(
        provenance["repositories"]["swordsAndRavens"]["worktreeSha256"]
    ) == 64
    assert provenance["rules"]["sha256"] == hashlib.sha256(
        rules_path.read_bytes()
    ).hexdigest()
    assert len(provenance["prompts"]) == 6
    assert all(
        len(item["configuredSystemPromptSha256"]) == 64
        and len(item["effectiveInstructionsSha256"]) == 64
        for item in provenance["prompts"]
    )
    assert provenance["model"]["id"] == "z-ai/glm-5.3-flash"
    assert provenance["model"]["maxConcurrency"] == 3
    serialized = str(provenance)
    assert "do-not-record-this-token" not in serialized
    assert "url-secret" not in serialized
    assert "hidden" not in serialized


def _terminal_game(winner: str) -> dict:
    return {
        "childGameState": {
            "type": "ingame",
            "childGameState": {
                "type": "action",
                "childGameState": {"type": "game-ended", "winner": winner},
            },
        }
    }


def test_terminal_winner_requires_a_known_base_game_house() -> None:
    assert _terminal_winner(_terminal_game("stark")) == "stark"
    assert _validate_winner_house("martell", source="test") == "martell"

    with pytest.raises(RuntimeError, match="Invalid winner house"):
        _validate_winner_house("arryn", source="test")


@pytest.mark.asyncio
async def test_terminal_save_must_be_stable_and_match_observed_winner(
    tmp_path,
) -> None:
    path = tmp_path / "game.json"
    path.write_text(json.dumps(_terminal_game("stark")))

    document, mtime_ns = await _wait_for_terminal_game_document(
        path,
        expected_winner="stark",
        timeout=1,
        stable_seconds=0.01,
        poll_seconds=0.005,
    )

    assert _terminal_winner(document) == "stark"
    assert mtime_ns == path.stat().st_mtime_ns

    with pytest.raises(RuntimeError, match="does not match"):
        await _wait_for_terminal_game_document(
            path,
            expected_winner="martell",
            timeout=1,
            stable_seconds=0.01,
            poll_seconds=0.005,
        )


def test_sqlite_quick_check_accepts_evaluation_database(tmp_path) -> None:
    database = Database(tmp_path / "harness.db")
    try:
        _require_sqlite_quick_check(database)
    finally:
        database.close()


def test_provider_attribution_includes_nested_response_from_failed_parent(
    tmp_path,
) -> None:
    database = Database(tmp_path / "harness.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(
            name="Balanced",
            model="z-ai/glm-5.3-flash",
            user_id="1",
            auth_token="1",
        )
    )
    store.add_run(
        run_id="failed-parent",
        agent_id=record.id,
        status="failed",
        observation={},
        response_id=None,
        raw_usage=[
            {
                "scope": "rules-oracle",
                "response_id": "oracle-generation",
            }
        ],
        error="parent failed",
        created_at="2026-01-01T00:00:01+00:00",
    )

    try:
        assert _persisted_response_rows(database, [record]) == [
            {
                "runId": "failed-parent",
                "agentId": record.id,
                "configuration": "Balanced",
                "responseId": "oracle-generation",
                "responseIndex": 0,
            }
        ]
    finally:
        database.close()


@pytest.mark.asyncio
async def test_openrouter_generation_attribution_is_best_effort_and_secret_free(
    tmp_path,
) -> None:
    database = Database(tmp_path / "harness.db")
    store = AgentStore(database)
    records = [
        store.create_agent(
            AgentCreate(
                name=name,
                model="z-ai/glm-5.3-flash",
                user_id=str(index + 1),
                auth_token=str(index + 1),
            )
        )
        for index, name in enumerate(("Balanced", "Expansion"))
    ]
    for index, record in enumerate(records, 1):
        store.add_run(
            run_id=f"run-{index}",
            agent_id=record.id,
            status="completed",
            observation={},
            response_id=f"gen-{index}",
            created_at=f"2026-01-01T00:00:0{index}+00:00",
        )

    seen_authorization = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_authorization.append(request.headers.get("authorization"))
        response_id = request.url.params["id"]
        if response_id == "gen-1":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "provider_name": "Fast Provider",
                        "model": "z-ai/glm-5.3-flash",
                        "total_cost": 0.00125,
                        "latency": 842,
                    }
                },
            )
        return httpx.Response(503, json={"error": {"message": "try later"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(
        openrouter_token="provider-token-must-not-be-recorded",
        openrouter_base_url="https://openrouter.example/api/v1",
    )
    try:
        artifact = await _collect_openrouter_generations(
            database=database,
            records=records,
            settings=settings,
            client=client,
            retries=0,
        )
    finally:
        await client.aclose()
        database.close()

    assert seen_authorization == [
        "Bearer provider-token-must-not-be-recorded",
        "Bearer provider-token-must-not-be-recorded",
    ]
    assert artifact["requestedCount"] == 2
    assert artifact["attributedCount"] == 1
    assert artifact["modelAttributedCount"] == 1
    assert artifact["unavailableCount"] == 1
    assert artifact["providerCounts"] == {"Fast Provider": 1}
    assert artifact["modelCounts"] == {"z-ai/glm-5.3-flash": 1}
    assert artifact["generations"][0] == {
        "runId": "run-1",
        "agentId": records[0].id,
        "configuration": "Balanced",
        "responseId": "gen-1",
        "responseIndex": 0,
        "provider": "Fast Provider",
        "model": "z-ai/glm-5.3-flash",
        "costUsd": 0.00125,
        "latencyMs": 842,
        "error": None,
    }
    assert artifact["generations"][1]["configuration"] == "Expansion"
    assert artifact["generations"][1]["provider"] is None
    assert artifact["generations"][1]["error"] == "OpenRouter returned HTTP 503"
    assert "provider-token-must-not-be-recorded" not in str(artifact)


@pytest.mark.asyncio
async def test_openrouter_generation_attribution_has_an_overall_deadline(
    tmp_path,
) -> None:
    database = Database(tmp_path / "harness.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(
            name="Balanced",
            model="z-ai/glm-5.3-flash",
            user_id="1",
            auth_token="1",
        )
    )
    store.add_run(
        run_id="run-1",
        agent_id=record.id,
        status="completed",
        observation={},
        response_id="gen-1",
        created_at="2026-01-01T00:00:01+00:00",
    )

    async def handler(_request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(1)
        return httpx.Response(200, json={"data": {"provider_name": "Too Late"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(openrouter_token="token", _env_file=None)
    try:
        artifact = await _collect_openrouter_generations(
            database=database,
            records=[record],
            settings=settings,
            client=client,
            retries=0,
            deadline_seconds=0.01,
        )
    finally:
        await client.aclose()
        database.close()

    assert artifact["requestedCount"] == 1
    assert artifact["attributedCount"] == 0
    assert artifact["unavailableCount"] == 1
    assert artifact["generations"][0]["error"] == (
        "OpenRouter attribution exceeded its deadline"
    )


def test_summary_aggregates_rankings_house_effects_and_pairwise_elo() -> None:
    metrics = {
        "statusCounts": {"completed": 3, "failed": 1},
        "costUsd": 0.25,
    }
    standings = [
        {
            "configuration": configuration.name,
            "house": house,
            "placement": index + 1,
            "victoryPoints": 7 - index,
            "metrics": metrics,
        }
        for index, (configuration, house) in enumerate(
            zip(PROMPT_CONFIGURATIONS, HOUSES, strict=True)
        )
    ]

    summary = summarize_results(
        [
            {
                "gameNumber": 1,
                "winner": HOUSES[0],
                "standings": standings,
            }
        ]
    )

    assert summary["completedGames"] == 1
    assert summary["ranking"][0]["configuration"] == "Balanced"
    assert summary["ranking"][0]["elo"] > 1500
    assert summary["ranking"][0]["reliability"] == 0.75
    assert summary["ranking"][0]["costUsd"] == 0.25
    assert summary["houseEffects"][0] == {
        "house": "stark",
        "games": 1,
        "wins": 1,
        "averagePlacement": 1.0,
    }
