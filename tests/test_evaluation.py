import argparse
import asyncio
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.evaluation import (
    HOUSES,
    MUTABLE_GAME_SAVE_PATH,
    TOURNAMENT_HARNESS_ID,
    TOURNAMENT_MODELS,
    _build_provenance,
    _collect_openrouter_generations,
    _evaluation_schedule,
    _git_provenance,
    _load_manifest,
    _persisted_response_rows,
    _preflight_openrouter_models,
    _preflight_openrouter_quota,
    _preflight_model_catalog,
    _progress_signature,
    _require_sqlite_quick_check,
    _run_assignments,
    _start_game_server,
    _terminal_winner,
    _validate_evaluation_schedule,
    _validate_winner_house,
    _wait_for_terminal_game_document,
    derive_game_seed,
    house_rotation,
    run_game,
    run_evaluation,
    resolve_evaluation_output,
    summarize_results,
    user_rotation,
)
from raven_harness.schemas import AgentCreate


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
COMPLETE_PROVIDER_ATTRIBUTION = {
    "requestedCount": 6,
    "attributedCount": 6,
    "modelAttributedCount": 6,
    "costAttributedCount": 6,
    "unavailableCount": 0,
    "providerCounts": {"test": 6},
    "modelCounts": {model: 1 for model in TOURNAMENT_MODELS},
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


def test_explicit_three_seat_assignments_allow_one_repeated_model() -> None:
    model = "openai/gpt-oss-120b"

    assignments = _run_assignments(
        game_number=1,
        seat_models=[model, model, model],
        seat_houses=["baratheon", "lannister", "stark"],
    )

    assert [assignment["model"] for assignment in assignments] == [model] * 3
    assert [assignment["userId"] for assignment in assignments] == ["1", "2", "3"]
    assert {assignment["house"] for assignment in assignments} == {
        "baratheon",
        "lannister",
        "stark",
    }


@pytest.mark.asyncio
async def test_run_game_resolves_attempt_directory_before_starting_server(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured_game_path: Path | None = None

    async def fail_after_capture(**arguments):
        nonlocal captured_game_path
        captured_game_path = arguments["game_path"]
        raise RuntimeError("captured path")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "raven_harness.evaluation._start_game_server", fail_after_capture
    )

    with pytest.raises(RuntimeError, match="captured path"):
        await run_game(
            game_number=1,
            attempt_dir=Path("relative-attempt"),
            random_seed=1,
            game_port=0,
            max_rounds=1,
            poll_seconds=0.1,
            stall_seconds=1,
            match_timeout_seconds=1,
            settings=Settings(_env_file=None),
        )

    assert captured_game_path == (tmp_path / "relative-attempt/game.json").resolve()


def test_schedule_validation_ignores_attempt_history_but_rejects_user_changes() -> None:
    schedule = _evaluation_schedule(12)
    schedule[0]["attempts"].append({"status": "completed"})

    _validate_evaluation_schedule(schedule, 12)

    schedule[0]["users"][TOURNAMENT_MODELS[0]] = "2"
    with pytest.raises(RuntimeError, match="different seed, house, or user schedule"):
        _validate_evaluation_schedule(schedule, 12)


def test_twelve_game_schedule_has_stable_distinct_uint32_seeds() -> None:
    first = _evaluation_schedule(12, 0)
    repeated = _evaluation_schedule(12, 0)
    seeds = [game["randomSeed"] for game in first]

    assert first == repeated
    assert seeds == [derive_game_seed(0, number) for number in range(1, 13)]
    assert len(set(seeds)) == 12
    assert all(0 <= seed <= 0xFFFFFFFF for seed in seeds)
    assert seeds != [game["randomSeed"] for game in _evaluation_schedule(12, 1)]


def test_evaluation_output_must_stay_in_the_repository_data_directory(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evaluation_root = tmp_path / "data" / "evaluations"
    monkeypatch.setattr(
        "raven_harness.evaluation.EVALUATION_ROOT", evaluation_root
    )

    allowed = evaluation_root / "comparison"
    assert resolve_evaluation_output(
        str(allowed), default_prefix=""
    ) == allowed
    with pytest.raises(RuntimeError, match="must be inside"):
        resolve_evaluation_output(str(tmp_path / "outside"), default_prefix="")


@pytest.mark.asyncio
async def test_game_server_receives_the_exact_scheduled_seed(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    game_server_dir = tmp_path / "game-server"
    executable = game_server_dir / "node_modules" / ".bin" / "ts-node"
    executable.parent.mkdir(parents=True)
    executable.write_text("")
    captured: dict = {}
    expected_process = object()

    async def create_subprocess_exec(*command, **options):
        captured["command"] = command
        captured["options"] = options
        return expected_process

    monkeypatch.setattr(
        "raven_harness.evaluation.GAME_SERVER_DIR", game_server_dir
    )
    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_subprocess_exec)
    with (tmp_path / "server.log").open("wb") as log:
        process = await _start_game_server(
            game_path=tmp_path / "game.json",
            port=5101,
            max_rounds=None,
            random_seed=4294967295,
            log=log,
        )

    assert process is expected_process
    assert captured["options"]["env"]["HARNESS_RANDOM_SEED"] == "4294967295"


def test_load_manifest_rejects_legacy_schema_without_modifying_it(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "manifest.json"
    legacy = {
        "schemaVersion": 1,
        "model": "z-ai/glm-5.3-flash",
        "gameCount": 12,
        "games": _evaluation_schedule(12),
    }
    path.write_text(json.dumps(legacy))
    monkeypatch.setattr(
        "raven_harness.evaluation._build_provenance", lambda _args, _settings: {}
    )
    args = argparse.Namespace(games=12, random_seed=1)

    with pytest.raises(RuntimeError, match="unsupported schema version 1"):
        _load_manifest(
            path,
            args,
            tmp_path,
            Settings(_env_file=None),
            verified_models=VERIFIED_MODELS,
        )

    assert json.loads(path.read_text()) == legacy


def test_load_manifest_rejects_schema_four_without_provenance(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "manifest.json"
    manifest = {
        "schemaVersion": 4,
        "models": TOURNAMENT_MODELS,
        "modelVerification": {"models": VERIFIED_MODELS},
        "gameCount": 12,
        "randomSeed": 1,
        "games": _evaluation_schedule(12),
    }
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(
        "raven_harness.evaluation._build_provenance", lambda _args, _settings: {}
    )
    args = argparse.Namespace(games=12, random_seed=1)

    with pytest.raises(RuntimeError, match="no schema-4 provenance"):
        _load_manifest(
            path,
            args,
            tmp_path,
            Settings(_env_file=None),
            verified_models=VERIFIED_MODELS,
        )


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
        random_seed=1,
        game_port=5101,
        concurrent_games=4,
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
    assert len(provenance["harness"]["systemPromptSha256"]) == 64
    assert len(provenance["harness"]["effectiveInstructionsSha256"]) == 64
    assert provenance["harness"]["id"] == TOURNAMENT_HARNESS_ID
    assert provenance["harness"]["toolChoice"] == "required"
    assert provenance["harness"]["retryHistoryMode"] == (
        "current-observation-only"
    )
    assert provenance["models"]["ids"] == TOURNAMENT_MODELS
    assert provenance["evaluation"]["randomSeed"] == 1
    assert provenance["harness"]["maxConcurrency"] == 3
    assert provenance["harness"]["maxOutputTokens"] == 16_384
    serialized = str(provenance)
    assert "do-not-record-this-token" not in serialized
    assert "url-secret" not in serialized
    assert "hidden" not in serialized


def test_git_provenance_ignores_runtime_save_but_tracks_source_changes(
    tmp_path,
) -> None:
    child_source = tmp_path / "child-source"
    child_source.mkdir()
    _test_git(child_source, "init")
    _configure_test_git(child_source)
    (child_source / "source.txt").write_text("original source\n")
    save = child_source / MUTABLE_GAME_SAVE_PATH
    save.parent.mkdir(parents=True)
    save.write_text("original save\n")
    _test_git(child_source, "add", ".")
    _test_git(child_source, "commit", "-m", "initial child")

    root = tmp_path / "root"
    root.mkdir()
    _test_git(root, "init")
    _configure_test_git(root)
    (root / "README.md").write_text("root source\n")
    _test_git(root, "add", "README.md")
    _test_git(root, "commit", "-m", "initial root")
    _test_git(
        root,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        str(child_source),
        "swords-and-ravens",
    )
    _test_git(root, "commit", "-am", "add submodule")

    child = root / "swords-and-ravens"
    clean_root = _git_provenance(root, ignore_dirty_submodules=True)
    clean_child = _git_provenance(
        child, ignored_paths=(MUTABLE_GAME_SAVE_PATH,)
    )
    assert clean_root["dirty"] is False
    assert clean_child["dirty"] is False

    (child / MUTABLE_GAME_SAVE_PATH).write_text("runtime save\n")
    assert _git_provenance(root, ignore_dirty_submodules=True) == clean_root
    assert (
        _git_provenance(child, ignored_paths=(MUTABLE_GAME_SAVE_PATH,))
        == clean_child
    )

    (child / "source.txt").write_text("changed source\n")
    assert _git_provenance(
        child, ignored_paths=(MUTABLE_GAME_SAVE_PATH,)
    )["dirty"] is True
    _test_git(child, "add", "source.txt")
    _test_git(child, "commit", "-m", "change child source")
    assert _git_provenance(root, ignore_dirty_submodules=True)["dirty"] is True

    _test_git(root, "add", "swords-and-ravens")
    _test_git(root, "commit", "-m", "advance submodule")
    (root / "README.md").write_text("changed root source\n")
    assert _git_provenance(root, ignore_dirty_submodules=True)["dirty"] is True


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
                json={
                    "data": {"limit": 20, "limit_remaining": 2, "usage": 18}
                },
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
        with pytest.raises(RuntimeError, match="account credits are exhausted") as caught:
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
        verified = await _preflight_openrouter_models(settings, client=client)
    finally:
        await client.aclose()

    assert [row["id"] for row in verified] == TOURNAMENT_MODELS
    assert verified[3]["aliasTarget"] == "deepseek/deepseek-v4-flash-0731"
    assert all(row["supportedParameters"] == ["max_tokens", "tool_choice", "tools"] for row in verified)


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
            await _preflight_openrouter_models(settings, client=client)
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_model_preflight_uses_configured_openai_compatible_endpoint() -> None:
    rows = [{"id": model} for model in TOURNAMENT_MODELS]

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer compatible-secret"
        return httpx.Response(200, json={"data": rows})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(
        openrouter_token="",
        openai_api_key="compatible-secret",
        openai_base_url="https://models.example/v1",
        _env_file=None,
    )
    try:
        verified = await _preflight_model_catalog(settings, client=client)
    finally:
        await client.aclose()

    assert [row["id"] for row in verified] == TOURNAMENT_MODELS
    assert all(row["canonicalSlug"] == row["id"] for row in verified)
    assert all(row["supportedParameters"] is None for row in verified)


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

    monkeypatch.setattr(
        "raven_harness.evaluation.Settings", lambda **_kwargs: settings
    )
    monkeypatch.setattr(
        "raven_harness.evaluation._preflight_openrouter_quota", reject_quota
    )
    args = argparse.Namespace(
        output=str(output),
        random_seed=1,
        games=1,
        start_game=1,
        game_port=5101,
        concurrent_games=1,
        max_rounds=1,
        poll_seconds=1.0,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
        continue_on_error=False,
    )

    with pytest.raises(RuntimeError, match="quota rejected"):
        await run_evaluation(args)
    assert not output.exists()


@pytest.mark.asyncio
async def test_evaluation_runs_games_concurrently_on_distinct_ports(
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
    ports: dict[int, int] = {}

    async def accept_quota(_settings: Settings) -> None:
        return None

    async def accept_models(_settings: Settings) -> list[dict]:
        return VERIFIED_MODELS

    async def fake_run_game(**arguments):
        nonlocal active, peak_active
        game_number = arguments["game_number"]
        ports[game_number] = arguments["game_port"]
        active += 1
        peak_active = max(peak_active, active)
        try:
            await asyncio.sleep(0.02)
            return {"winner": HOUSES[game_number - 1]}
        finally:
            active -= 1

    monkeypatch.setattr(
        "raven_harness.evaluation.Settings", lambda **_kwargs: settings
    )
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
        games=4,
        start_game=1,
        game_port=5101,
        concurrent_games=3,
        max_rounds=1,
        poll_seconds=1.0,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
        continue_on_error=False,
    )

    assert await run_evaluation(args) == output
    assert peak_active == 3
    assert ports == {1: 5101, 2: 5102, 3: 5103, 4: 5104}
    manifest = json.loads((output / "manifest.json").read_text())
    assert [game["attempts"][0]["status"] for game in manifest["games"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
    ]


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

    monkeypatch.setattr(
        "raven_harness.evaluation.Settings", lambda **_kwargs: settings
    )
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
        games=1,
        start_game=1,
        game_port=5101,
        concurrent_games=1,
        max_rounds=1,
        poll_seconds=1.0,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
        continue_on_error=False,
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
async def test_evaluation_requires_a_configured_model_api_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    settings = Settings(
        rules_path=tmp_path / "rules.json",
        openrouter_token="",
        openai_api_key="",
        _env_file=None,
    )
    monkeypatch.setattr(
        "raven_harness.evaluation.Settings", lambda **_kwargs: settings
    )

    with pytest.raises(RuntimeError, match="Configure an API key"):
        await run_evaluation(argparse.Namespace())


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
                "requestedModel": "z-ai/glm-5.3-flash",
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
                name=model,
                model=model,
                user_id=str(index + 1),
                auth_token=str(index + 1),
            )
        )
        for index, model in enumerate(TOURNAMENT_MODELS[:2])
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
    assert artifact["costAttributedCount"] == 1
    assert artifact["unavailableCount"] == 1
    assert artifact["providerCounts"] == {"Fast Provider": 1}
    assert artifact["modelCounts"] == {"z-ai/glm-5.3-flash": 1}
    assert artifact["generations"][0] == {
        "runId": "run-1",
        "agentId": records[0].id,
        "requestedModel": TOURNAMENT_MODELS[0],
        "responseId": "gen-1",
        "responseIndex": 0,
        "provider": "Fast Provider",
        "model": "z-ai/glm-5.3-flash",
        "costUsd": 0.00125,
        "latencyMs": 842,
        "error": None,
    }
    assert artifact["generations"][1]["requestedModel"] == TOURNAMENT_MODELS[1]
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
        "modelRequests": 5,
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
                "winner": HOUSES[0],
                "standings": standings,
                "providerAttribution": COMPLETE_PROVIDER_ATTRIBUTION,
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
    assert summary["ranking"][0]["modelRequests"] == 5
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
        "modelRequests": 0,
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
                "winner": standings[0]["house"],
                "standings": standings,
                "providerAttribution": COMPLETE_PROVIDER_ATTRIBUTION,
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
