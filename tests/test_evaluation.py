import argparse
import asyncio
import copy
import json
import subprocess
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr

from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.evaluation import (
    HOUSES,
    TOURNAMENT_GAMES,
    TOURNAMENT_MODELS,
    _evaluation_schedule,
    _validate_resumable_provenance,
    _preflight_openrouter_quota,
    _preflight_model_catalog,
    _run_assignments,
    _terminal_winner,
    _validate_evaluation_schedule,
    _validate_resumed_agents,
    _wait_for_terminal_game_document,
    house_rotation,
    run_evaluation,
    resolve_evaluation_output,
    summarize_results,
    user_rotation,
)
from raven_harness.schemas import DEFAULT_PROMPT


VERIFIED_MODELS = [
    {
        "id": model,
        "name": model,
        "canonicalSlug": model,
        "aliasTarget": None,
        "supportedParameters": ["tool_choice", "tools"],
    }
    for model in TOURNAMENT_MODELS
]


def _test_runtime_provenance(version: str) -> dict:
    return {
        "repositories": {
            "root": {"commit": "root"},
            "swordsAndRavens": {"commit": "game"},
        },
        "harness": {"version": version},
        "rules": {"sha256": "rules"},
        "models": {"ids": TOURNAMENT_MODELS},
        "evaluation": {"randomSeed": 1},
    }


def test_twelve_game_rotation_assigns_each_house_twice() -> None:
    for model in TOURNAMENT_MODELS:
        assignments = [house_rotation(game)[model] for game in range(1, 13)]
        assert sorted(assignments) == sorted(HOUSES * 2)

    for game in range(1, 13):
        assert sorted(house_rotation(game).values()) == sorted(HOUSES)


def test_twelve_game_user_rotation_makes_each_model_owner_twice() -> None:
    for game in range(1, 13):
        assert sorted(user_rotation(game).values()) == [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
        ]
    for model in TOURNAMENT_MODELS:
        user_ids = [user_rotation(game)[model] for game in range(1, 13)]
        assert user_ids.count("1") == 2
        assert sorted(user_ids) == sorted([str(value) for value in range(1, 7)] * 2)


def test_resumed_agents_must_keep_their_scheduled_models() -> None:
    assignments = _run_assignments(
        game_number=1,
        seat_models=None,
        seat_houses=None,
    )
    records = [
        SimpleNamespace(
            name=assignment["model"],
            model=assignment["model"],
            system_prompt=DEFAULT_PROMPT,
            game_server_url="ws://127.0.0.1:5101",
            game_id="1",
            user_id=assignment["userId"],
            auth_token=SecretStr(assignment["userId"]),
        )
        for assignment in assignments
    ]
    records[0].model = "another/model"

    with pytest.raises(RuntimeError, match="does not match"):
        _validate_resumed_agents(
            records=records,
            assignments=assignments,
            game_port=5101,
        )


def test_schedule_validation_ignores_attempt_history_but_rejects_user_changes() -> None:
    schedule = _evaluation_schedule(12)
    schedule[0]["attempts"].append({"status": "completed"})

    _validate_evaluation_schedule(schedule, 12)

    schedule[0]["users"][TOURNAMENT_MODELS[0]] = "2"
    with pytest.raises(RuntimeError, match="different seed, house, or user schedule"):
        _validate_evaluation_schedule(schedule, 12)


def test_evaluation_output_must_stay_in_the_repository_data_directory(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evaluation_root = tmp_path / "data" / "evaluations"
    monkeypatch.setattr("raven_harness.evaluation.EVALUATION_ROOT", evaluation_root)

    allowed = evaluation_root / "comparison"
    assert resolve_evaluation_output(str(allowed), default_prefix="") == allowed
    with pytest.raises(RuntimeError, match="must be inside"):
        resolve_evaluation_output(str(tmp_path / "outside"), default_prefix="")


def test_resumable_provenance_ignores_docs_commit_but_rejects_runtime_change() -> None:
    existing = {
        "repositories": {
            "root": {"commit": "before-docs"},
            "swordsAndRavens": {"commit": "game-server"},
        },
        "harness": {"runtimeSha256": "runtime-a"},
        "rules": {"sha256": "rules"},
        "models": {"ids": ["model"]},
        "evaluation": {"randomSeed": 1},
    }
    after_docs = copy.deepcopy(existing)
    after_docs["repositories"]["root"]["commit"] = "after-docs"

    _validate_resumable_provenance(existing, after_docs)

    after_runtime_change = copy.deepcopy(after_docs)
    after_runtime_change["harness"]["runtimeSha256"] = "runtime-b"
    with pytest.raises(RuntimeError, match="different harness"):
        _validate_resumable_provenance(existing, after_runtime_change)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data",
    [
        {},
        {"limit": None, "usage": 1_000_000},
        {"limit": 10, "usage": 9.5},
        {"limit": 10},
    ],
)
async def test_openrouter_quota_preflight_tolerates_available_or_unlimited_keys(
    data,
) -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": data})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(
        openrouter_token="quota-key-must-stay-secret",
        openrouter_base_url="https://openrouter.example/api/v1",
        _env_file=None,
    )
    try:
        assert await _preflight_openrouter_quota(settings, client=client) is None
    finally:
        await client.aclose()

    assert [str(request.url) for request in requests] == [
        "https://openrouter.example/api/v1/key",
        "https://openrouter.example/api/v1/credits",
    ]
    assert all(
        request.headers["authorization"] == "Bearer quota-key-must-stay-secret"
        for request in requests
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data",
    [
        {"limit": 10, "limit_remaining": 0, "usage": 9},
        {"limit": 10, "usage": 10},
        {"limit": 0},
    ],
)
async def test_openrouter_quota_preflight_rejects_explicitly_exhausted_key(
    data,
) -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": data})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    secret = "exhausted-key-must-stay-secret"
    settings = Settings(
        openrouter_token=secret,
        openrouter_base_url="https://openrouter.example/api/v1",
        _env_file=None,
    )
    try:
        with pytest.raises(RuntimeError, match="spending limit is exhausted") as caught:
            await _preflight_openrouter_quota(settings, client=client)
    finally:
        await client.aclose()

    assert secret not in str(caught.value)


@pytest.mark.asyncio
async def test_openrouter_quota_preflight_rejects_exhausted_account_credits() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200,
                json={"data": {"limit": 20, "limit_remaining": 2, "usage": 18}},
            )
        return httpx.Response(
            200,
            json={"data": {"total_credits": 35, "total_usage": 35.18}},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    secret = "credit-key-must-stay-secret"
    settings = Settings(
        openrouter_token=secret,
        openrouter_base_url="https://openrouter.example/api/v1",
        _env_file=None,
    )
    try:
        with pytest.raises(
            RuntimeError, match="account credits are exhausted"
        ) as caught:
            await _preflight_openrouter_quota(settings, client=client)
    finally:
        await client.aclose()

    assert len(requests) == 2
    assert secret not in str(caught.value)


@pytest.mark.asyncio
async def test_model_preflight_verifies_exact_ids_tools_and_aliases() -> None:
    rows = [
        {
            "id": model,
            "name": f"Name for {model}",
            "canonical_slug": model,
            "alias_target": (
                {"slug": "deepseek/deepseek-v4-flash-0731"}
                if model.startswith("~deepseek/")
                else None
            ),
            "supported_parameters": ["max_tokens", "tools", "tool_choice"],
        }
        for model in TOURNAMENT_MODELS
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer secret"
        return httpx.Response(200, json={"data": rows})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(
        openrouter_token="secret",
        openrouter_base_url="https://openrouter.example/api/v1",
        _env_file=None,
    )
    try:
        verified = await _preflight_model_catalog(settings, client=client)
    finally:
        await client.aclose()

    assert [row["id"] for row in verified] == TOURNAMENT_MODELS
    assert verified[3]["aliasTarget"] == "deepseek/deepseek-v4-flash-0731"
    assert all(
        row["supportedParameters"] == ["max_tokens", "tool_choice", "tools"]
        for row in verified
    )


@pytest.mark.asyncio
async def test_model_preflight_rejects_missing_or_non_tool_models() -> None:
    rows = [
        {
            "id": model,
            "supported_parameters": ["tools", "tool_choice"],
        }
        for model in TOURNAMENT_MODELS[:-1]
    ]

    async def missing_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": rows})

    client = httpx.AsyncClient(transport=httpx.MockTransport(missing_handler))
    settings = Settings(openrouter_token="secret", _env_file=None)
    try:
        with pytest.raises(RuntimeError, match="does not list the exact"):
            await _preflight_model_catalog(settings, client=client)
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_quota_preflight_runs_before_evaluation_output_is_created(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    output = tmp_path / "must-not-exist"
    rules = tmp_path / "rules.json"
    rules.write_text("{}\n")
    settings = Settings(
        rules_path=rules,
        openrouter_token="secret",
        _env_file=None,
    )

    async def reject_quota(_settings: Settings) -> None:
        assert not output.exists()
        raise RuntimeError("quota rejected")

    monkeypatch.setattr("raven_harness.evaluation.Settings", lambda **_kwargs: settings)
    monkeypatch.setattr(
        "raven_harness.evaluation._preflight_openrouter_quota", reject_quota
    )
    args = argparse.Namespace(
        output=str(output),
        random_seed=1,
        game_port=5101,
        poll_seconds=1.0,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
    )

    with pytest.raises(RuntimeError, match="quota rejected"):
        await run_evaluation(args)
    assert not output.exists()


@pytest.mark.asyncio
async def test_evaluation_runs_one_full_game_per_invocation_on_one_port(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    evaluation_root = tmp_path / "evaluations"
    output = evaluation_root / "comparison"
    rules = tmp_path / "rules.json"
    rules.write_text("{}\n")
    settings = Settings(
        rules_path=rules,
        openrouter_token="secret",
        _env_file=None,
    )
    active = 0
    peak_active = 0
    ports: list[int] = []

    async def accept_quota(_settings: Settings) -> None:
        return None

    async def accept_models(_settings: Settings) -> list[dict]:
        return VERIFIED_MODELS

    async def fake_run_game(**arguments):
        nonlocal active, peak_active
        game_number = arguments["game_number"]
        ports.append(arguments["game_port"])
        active += 1
        peak_active = max(peak_active, active)
        try:
            if game_number == 1:
                with pytest.raises(RuntimeError, match="runner is already active"):
                    await run_evaluation(args)
            await asyncio.sleep(0.02)
            result = {
                "gameNumber": game_number,
                "randomSeed": arguments["random_seed"],
                "endpointProvider": "OpenRouter",
                "winner": HOUSES[(game_number - 1) % len(HOUSES)],
                "round": 10,
                "standings": [],
            }
            (arguments["attempt_dir"] / "result.json").write_text(json.dumps(result))
            return result
        finally:
            active -= 1

    monkeypatch.setattr("raven_harness.evaluation.Settings", lambda **_kwargs: settings)
    monkeypatch.setattr(
        "raven_harness.evaluation._preflight_openrouter_quota", accept_quota
    )
    monkeypatch.setattr(
        "raven_harness.evaluation._preflight_model_catalog", accept_models
    )
    monkeypatch.setattr("raven_harness.evaluation.run_game", fake_run_game)
    monkeypatch.setattr("raven_harness.evaluation.EVALUATION_ROOT", evaluation_root)
    monkeypatch.setattr(
        "raven_harness.evaluation._build_provenance",
        lambda _args, _settings: {"test": True},
    )
    args = argparse.Namespace(
        output=str(output),
        random_seed=1,
        game_port=5101,
        poll_seconds=1.0,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
    )

    for expected_game in range(1, TOURNAMENT_GAMES + 1):
        assert await run_evaluation(args) == output
        manifest = json.loads((output / "manifest.json").read_text())
        assert (
            sum(
                attempt.get("status") == "completed"
                for game in manifest["games"]
                for attempt in game["attempts"]
            )
            == expected_game
        )

    assert peak_active == 1
    assert ports == [5101] * TOURNAMENT_GAMES
    manifest = json.loads((output / "manifest.json").read_text())
    assert [game["attempts"][0]["status"] for game in manifest["games"]] == [
        "completed"
    ] * TOURNAMENT_GAMES
    assert all(
        game["attempts"][0]["provenance"] == {"test": True}
        for game in manifest["games"]
    )
    assert "finishedAt" in manifest
    summary = json.loads((output / "summary.json").read_text())
    assert summary["completedGames"] == TOURNAMENT_GAMES
    assert summary["scheduledGames"] == TOURNAMENT_GAMES
    assert summary["attemptStatusCounts"] == {"completed": TOURNAMENT_GAMES}


@pytest.mark.asyncio
async def test_evaluation_resumes_the_same_durable_attempt(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    evaluation_root = tmp_path / "evaluations"
    output = evaluation_root / "resumable"
    rules = tmp_path / "rules.json"
    rules.write_text("{}\n")
    settings = Settings(
        rules_path=rules,
        openrouter_token="secret",
        _env_file=None,
    )
    calls: list[dict] = []

    async def accept_quota(_settings: Settings) -> None:
        return None

    async def accept_models(_settings: Settings) -> list[dict]:
        return VERIFIED_MODELS

    async def fake_run_game(**arguments):
        calls.append(arguments)
        attempt_dir = arguments["attempt_dir"]
        if len(calls) == 1:
            (attempt_dir / "game.json").write_text('{"saved":true}\n')
            Database(attempt_dir / "harness.db").close()
            raise RuntimeError("operator stopped the process")
        assert arguments["resume"] is True
        return {"winner": "stark"}

    monkeypatch.setattr("raven_harness.evaluation.Settings", lambda **_kwargs: settings)
    monkeypatch.setattr(
        "raven_harness.evaluation._preflight_openrouter_quota", accept_quota
    )
    monkeypatch.setattr(
        "raven_harness.evaluation._preflight_model_catalog", accept_models
    )
    monkeypatch.setattr("raven_harness.evaluation.run_game", fake_run_game)
    monkeypatch.setattr("raven_harness.evaluation.EVALUATION_ROOT", evaluation_root)
    monkeypatch.setattr(
        "raven_harness.evaluation._build_provenance",
        lambda _args, _settings: {"test": True},
    )
    args = argparse.Namespace(
        output=str(output),
        random_seed=1,
        game_port=5101,
        poll_seconds=1.0,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
    )

    with pytest.raises(RuntimeError, match="operator stopped"):
        await run_evaluation(args)
    assert calls[0]["resume"] is False

    assert await run_evaluation(args) == output
    assert calls[1]["attempt_dir"] == calls[0]["attempt_dir"]
    manifest = json.loads((output / "manifest.json").read_text())
    attempts = manifest["games"][0]["attempts"]
    assert len(attempts) == 1
    assert attempts[0]["status"] == "completed"
    assert attempts[0]["resumeCount"] == 1
    assert attempts[0]["interruptions"][0]["status"] == "failed"


@pytest.mark.asyncio
async def test_evaluation_starts_a_new_attempt_after_runtime_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    evaluation_root = tmp_path / "evaluations"
    output = evaluation_root / "changed-runtime"
    rules = tmp_path / "rules.json"
    rules.write_text("{}\n")
    settings = Settings(rules_path=rules, openrouter_token="secret", _env_file=None)
    runtime_version = ["first"]
    calls: list[dict] = []

    async def accept_quota(_settings: Settings) -> None:
        return None

    async def accept_models(_settings: Settings) -> list[dict]:
        return VERIFIED_MODELS

    async def fake_run_game(**arguments):
        calls.append(arguments)
        if len(calls) == 1:
            (arguments["attempt_dir"] / "game.json").write_text('{"saved":true}\n')
            Database(arguments["attempt_dir"] / "harness.db").close()
            raise RuntimeError("first runtime failed")
        assert arguments["resume"] is False
        return {"winner": "stark"}

    monkeypatch.setattr("raven_harness.evaluation.Settings", lambda **_kwargs: settings)
    monkeypatch.setattr(
        "raven_harness.evaluation._preflight_openrouter_quota", accept_quota
    )
    monkeypatch.setattr(
        "raven_harness.evaluation._preflight_model_catalog", accept_models
    )
    monkeypatch.setattr("raven_harness.evaluation.run_game", fake_run_game)
    monkeypatch.setattr("raven_harness.evaluation.EVALUATION_ROOT", evaluation_root)
    monkeypatch.setattr(
        "raven_harness.evaluation._build_provenance",
        lambda _args, _settings: _test_runtime_provenance(runtime_version[0]),
    )
    args = argparse.Namespace(
        output=str(output),
        random_seed=1,
        game_port=5101,
        poll_seconds=1.0,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
    )

    with pytest.raises(RuntimeError, match="first runtime failed"):
        await run_evaluation(args)
    runtime_version[0] = "second"
    assert await run_evaluation(args) == output

    assert calls[0]["attempt_dir"].name == "attempt-01"
    assert calls[1]["attempt_dir"].name == "attempt-02"
    manifest = json.loads((output / "manifest.json").read_text())
    first, second = manifest["games"][0]["attempts"]
    assert first["status"] == "failed"
    assert first["error"] == "first runtime failed"
    assert "different harness" in first["resumeRejectedReason"]
    assert second["status"] == "completed"


def _test_git(directory, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(directory), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def _configure_test_git(directory) -> None:
    _test_git(directory, "config", "user.name", "Raven Test")
    _test_git(directory, "config", "user.email", "raven@example.test")


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


def test_summary_aggregates_rankings_house_effects_and_pairwise_elo() -> None:
    metrics = {
        "statusCounts": {"completed": 3, "failed": 1},
        "modelCalls": {
            "started": 5,
            "responses": 5,
            "withoutResponse": 0,
            "responsesWithoutStart": 0,
            "startedByScope": {"agent": 5},
        },
        "tokens": {
            "input": 1_000,
            "output": 200,
            "total": 1_200,
            "cachedInput": 300,
        },
        "costUsd": 0.25,
    }
    standings = [
        {
            "model": model,
            "house": house,
            "placement": index + 1,
            "victoryPoints": 7 - index,
            "metrics": metrics,
        }
        for index, (model, house) in enumerate(
            zip(TOURNAMENT_MODELS, HOUSES, strict=True)
        )
    ]

    summary = summarize_results(
        [
            {
                "gameNumber": 1,
                "randomSeed": 1,
                "round": 10,
                "endpointProvider": "Example endpoint",
                "winner": HOUSES[0],
                "standings": standings,
            }
        ]
    )

    assert summary["completedGames"] == 1
    assert summary["comparisonComplete"] is False
    assert summary["rankingStatus"] == "provisional"
    assert summary["requiredObservationsPerModelHouse"] == 2
    assert summary["minimumObservationsPerModelHouse"] == 0
    assert summary["ranking"][0]["model"] == TOURNAMENT_MODELS[0]
    assert summary["ranking"][0]["elo"] > 1500
    assert summary["ranking"][0]["reliability"] == 0.75
    assert summary["ranking"][0]["costUsd"] == 0.25
    assert summary["ranking"][0]["modelCallsStarted"] == 5
    assert summary["ranking"][0]["modelResponses"] == 5
    assert summary["ranking"][0]["inputTokens"] == 1_000
    assert summary["ranking"][0]["outputTokens"] == 200
    assert summary["ranking"][0]["totalTokens"] == 1_200
    assert summary["ranking"][0]["cachedInputTokens"] == 300
    assert summary["houseEffects"][0] == {
        "house": "stark",
        "games": 1,
        "wins": 1,
        "averagePlacement": 1.0,
    }


def test_summary_requires_two_complete_house_rotations() -> None:
    empty_metrics = {
        "statusCounts": {},
        "modelCalls": {},
        "tokens": {},
        "costUsd": 0,
    }
    results = []
    for game_number in range(1, 13):
        rotation = house_rotation(game_number)
        standings = [
            {
                "model": model,
                "house": rotation[model],
                "placement": placement,
                "victoryPoints": 7 - placement,
                "metrics": empty_metrics,
            }
            for placement, model in enumerate(TOURNAMENT_MODELS, 1)
        ]
        results.append(
            {
                "gameNumber": game_number,
                "randomSeed": game_number,
                "round": 10,
                "endpointProvider": "Example endpoint",
                "winner": standings[0]["house"],
                "standings": standings,
            }
        )

    summary = summarize_results(results)

    assert summary["completedGames"] == 12
    assert summary["comparisonComplete"] is True
    assert summary["rankingStatus"] == "complete"
    assert summary["minimumObservationsPerModelHouse"] == 2
    assert summary["modelHouseCoverage"] == [
        {
            "model": model,
            "houses": {house: 2 for house in HOUSES},
            "minimumObservations": 2,
        }
        for model in TOURNAMENT_MODELS
    ]


def test_summary_keeps_failed_attempt_usage_and_endpoint_attribution() -> None:
    attempt = {
        "gameNumber": 1,
        "attemptNumber": 1,
        "status": "failed",
        "activeElapsedSeconds": 12.5,
        "endpointProvider": "Example endpoint",
        "error": "request failed",
        "metrics": {
            "runCount": 2,
            "statusCounts": {"completed": 1, "failed": 1},
            "modelCalls": {
                "started": 3,
                "responses": 2,
                "withoutResponse": 1,
                "responsesWithoutStart": 0,
                "startedByScope": {"agent": 3},
            },
            "tokens": {
                "input": 100,
                "output": 20,
                "total": 120,
                "cachedInput": 50,
            },
            "costUsd": 0.02,
            "durationMs": {"total": 1000, "maximum": 800},
        },
    }

    summary = summarize_results([], attempts=[attempt])

    assert summary["completedGames"] == 0
    assert summary["attempts"] == [attempt]
    assert summary["attemptStatusCounts"] == {"failed": 1}
    assert summary["attemptEndpointProviderCounts"] == {"Example endpoint": 1}
    assert summary["runStatusCounts"] == {"completed": 1, "failed": 1}
    assert summary["modelCalls"] == {
        "started": 3,
        "responses": 2,
        "withoutResponse": 1,
        "responsesWithoutStart": 0,
        "startedByScope": {"agent": 3},
    }
    assert summary["tokens"]["cachedInput"] == 50
    assert summary["costUsd"] == 0.02
