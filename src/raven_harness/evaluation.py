from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import signal
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any, BinaryIO
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict

from .agent_store import AgentStore
from .config import DEFAULT_MODEL_ID, PROJECT_ROOT, Settings
from .database import Database
from .errors import safe_error_text
from .harness.strategic import (
    AGENT_SDK_MAX_TURNS,
    STRATEGIC_INSTRUCTIONS,
    StrategicHarness,
)
from .manager import AgentManager
from .models.openai_agent import OpenAIAgentRunner
from .rulebook import Rulebook
from .schemas import AgentCreate, DEFAULT_PROMPT, LobbySetupRequest
from .telemetry import Telemetry


HOUSES = ["stark", "greyjoy", "lannister", "tyrell", "martell", "baratheon"]
GAME_SERVER_DIR = PROJECT_ROOT / "swords-and-ravens" / "agot-bg-game-server"
MUTABLE_GAME_SAVE_PATH = (
    "agot-bg-game-server/src/server/website-client/local-entire-game.json"
)


class PromptConfiguration(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    suffix: str


PROMPT_CONFIGURATIONS = [
    PromptConfiguration(
        name="Balanced",
        suffix=(
            "Strategic policy: Use an adaptive, low-regret strategy. Compare "
            "expansion, defense, resources, and denial for each decision. Avoid "
            "extreme commitments unless they create or prevent a decisive victory. "
            "Prefer actions that preserve several strong follow-up options."
        ),
    ),
    PromptConfiguration(
        name="Expansion",
        suffix=(
            "Strategic policy: Prioritize control of new castles and strongholds. "
            "Use early marches and coordinated support before opponents consolidate. "
            "Accept moderate resource or card costs when they materially accelerate "
            "victory. Defend only holdings that are critical to continued expansion."
        ),
    ),
    PromptConfiguration(
        name="Economy",
        suffix=(
            "Strategic policy: Prioritize power tokens, supply, efficient mustering, "
            "influence positions, and house-card efficiency. Expand when you can "
            "retain the gain. Prefer durable resource advantages over speculative "
            "combat. Convert accumulated resources into a late victory push."
        ),
    ),
    PromptConfiguration(
        name="Defense",
        suffix=(
            "Strategic policy: Prioritize castles, retreat routes, and protection "
            "against catastrophic losses. Use defense and support to make enemy "
            "attacks inefficient. Avoid marginal battles and preserve decisive "
            "cards. Expand through low-risk openings or counterattacks against "
            "overextended opponents."
        ),
    ),
    PromptConfiguration(
        name="Aggression",
        suffix=(
            "Strategic policy: Prioritize initiative and tactical pressure. Attack "
            "exposed castles, disrupt support, and force opponents to spend strong "
            "cards. Accept calculated exchanges that improve tempo or weaken the "
            "current leader. Spend resources when immediate pressure creates a "
            "stronger winning chance."
        ),
    ),
    PromptConfiguration(
        name="Leader Control",
        suffix=(
            "Strategic policy: Prioritize reducing the strongest opponent's victory "
            "probability. Identify the leader from castles, land, supply, cards, and "
            "influence. Raid, outbid, block, or attack that leader when cost-effective. "
            "Avoid creating a replacement leader. Take your own winning line whenever "
            "one is available."
        ),
    ),
]


def house_rotation(game_number: int) -> dict[str, str]:
    """Return a two-block rotation in which every configuration gets each house."""

    index = (game_number - 1) % 12
    if index < 6:
        house_indexes = [(configuration + index) % 6 for configuration in range(6)]
    else:
        mirrored = index - 6
        house_indexes = [(mirrored - configuration) % 6 for configuration in range(6)]
    return {
        configuration.name: HOUSES[house_index]
        for configuration, house_index in zip(
            PROMPT_CONFIGURATIONS, house_indexes, strict=True
        )
    }


def user_rotation(game_number: int) -> dict[str, str]:
    """Rotate local identities so every configuration owns exactly two games."""

    round_index = (game_number - 1) % 6
    return {
        configuration.name: str(1 + ((index - round_index) % 6))
        for index, configuration in enumerate(PROMPT_CONFIGURATIONS)
    }


async def run_evaluation(args: argparse.Namespace) -> Path:
    settings = Settings()
    if not settings.model_api_key:
        raise RuntimeError("Set OPENROUTER_TOKEN before starting an evaluation")
    if not settings.resolved_rules_path.is_file():
        raise RuntimeError(
            "Rules oracle data is required for evaluation; run uv run raven-prepare-rules"
        )
    await _preflight_openrouter_quota(settings)
    output = _resolve_output(args.output)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest = _load_manifest(manifest_path, args, output, settings)

    for game_number in range(args.start_game, args.games + 1):
        game_entry = _game_entry(manifest, game_number)
        completed_attempt = next(
            (
                attempt
                for attempt in game_entry["attempts"]
                if attempt.get("status") == "completed"
            ),
            None,
        )
        if completed_attempt is not None:
            refreshed = await _refresh_completed_provider_attribution(
                output=output,
                attempt=completed_attempt,
                settings=settings,
            )
            if refreshed:
                _write_summary(output, manifest)
            print(f"Game {game_number}: already completed")
            continue
        attempt_number = len(game_entry["attempts"]) + 1
        attempt_dir = output / f"game-{game_number:02d}" / f"attempt-{attempt_number:02d}"
        attempt_dir.mkdir(parents=True, exist_ok=False)
        attempt = {
            "number": attempt_number,
            "status": "running",
            "directory": str(attempt_dir.relative_to(output)),
            "startedAt": _now(),
        }
        game_entry["attempts"].append(attempt)
        _write_json(manifest_path, manifest)
        print(f"Game {game_number}: starting attempt {attempt_number}")
        try:
            result = await run_game(
                game_number=game_number,
                attempt_dir=attempt_dir,
                model=args.model,
                game_port=args.game_port,
                max_rounds=args.max_rounds,
                poll_seconds=args.poll_seconds,
                stall_seconds=args.stall_seconds,
                match_timeout_seconds=args.match_timeout_hours * 3_600,
                settings=settings,
            )
            attempt.update(
                {
                    "status": "completed",
                    "finishedAt": _now(),
                    "winner": result["winner"],
                }
            )
            print(f"Game {game_number}: winner {result['winner']}")
        except Exception as error:
            error_text = safe_error_text(error)
            attempt.update(
                {
                    "status": "failed",
                    "finishedAt": _now(),
                    "error": error_text,
                }
            )
            _write_json(attempt_dir / "failure.json", attempt)
            print(f"Game {game_number}: failed: {error_text}")
            if not args.continue_on_error:
                _write_json(manifest_path, manifest)
                _write_summary(output, manifest)
                raise RuntimeError(error_text) from None
        finally:
            _write_json(manifest_path, manifest)
            _write_summary(output, manifest)

    manifest["finishedAt"] = _now()
    _write_json(manifest_path, manifest)
    _write_summary(output, manifest)
    return output


async def run_game(
    *,
    game_number: int,
    attempt_dir: Path,
    model: str,
    game_port: int,
    max_rounds: int | None,
    poll_seconds: float,
    stall_seconds: float,
    match_timeout_seconds: float,
    settings: Settings,
) -> dict[str, Any]:
    if await _port_is_open(game_port):
        raise RuntimeError(f"Game-server port {game_port} is already in use")

    game_path = attempt_dir / "game.json"
    database_path = attempt_dir / "harness.db"
    server_log_path = attempt_dir / "game-server.log"
    rotation = house_rotation(game_number)
    users = user_rotation(game_number)
    assignments = [
        {
            "configuration": configuration.name,
            "house": rotation[configuration.name],
            "userId": users[configuration.name],
            "model": model,
            "promptSha256": _sha256_text(_effective_instructions(configuration)),
        }
        for configuration in PROMPT_CONFIGURATIONS
    ]
    _write_json(attempt_dir / "assignments.json", assignments)

    server_log: BinaryIO | None = None
    process: asyncio.subprocess.Process | None = None
    database: Database | None = None
    manager: AgentManager | None = None
    telemetry: Telemetry | None = None
    runner: OpenAIAgentRunner | None = None
    records: list[Any] = []
    completed_result: dict[str, Any] | None = None
    game_mtime_ns: int | None = None
    quick_check_error: Exception | None = None
    try:
        server_log = server_log_path.open("wb")
        process = await _start_game_server(
            game_path=game_path,
            port=game_port,
            max_rounds=max_rounds,
            log=server_log,
        )
        await _wait_for_server(process, game_port, timeout=20)

        database = Database(database_path)
        store = AgentStore(database)
        rulebook = Rulebook.load_optional(settings.resolved_rules_path)
        telemetry = Telemetry.create(
            endpoint=settings.otel_exporter_otlp_traces_endpoint,
            service_name=settings.otel_service_name,
        )
        runner = OpenAIAgentRunner(
            api_key=settings.model_api_key,
            base_url=settings.model_base_url,
            request_timeout_seconds=settings.model_request_timeout_seconds,
            run_timeout_seconds=settings.model_run_timeout_seconds,
            max_retries=settings.model_api_max_retries,
            max_concurrency=settings.model_max_concurrency,
            max_output_tokens=settings.model_max_output_tokens,
            session_database_path=database_path,
            session_history_items=settings.model_session_history_items,
            provider_routing=(
                settings.openrouter_provider_routing
                if settings.model_provider == "OpenRouter"
                else None
            ),
            rulebook=rulebook,
        )
        harness = StrategicHarness(runner, store)
        manager = AgentManager(
            store=store,
            harness=harness,
            telemetry=telemetry,
            autoplay_max_consecutive_failures=(
                settings.autoplay_max_consecutive_failures
            ),
            autoplay_retry_base_seconds=settings.autoplay_retry_base_seconds,
            required_model_id=model,
        )

        assignment_by_configuration = {
            assignment["configuration"]: assignment for assignment in assignments
        }
        for configuration in PROMPT_CONFIGURATIONS:
            user_id = assignment_by_configuration[configuration.name]["userId"]
            records.append(
                store.create_agent(
                    AgentCreate(
                        name=configuration.name,
                        model=model,
                        system_prompt=_system_prompt(configuration),
                        game_server_url=f"ws://127.0.0.1:{game_port}",
                        game_id="1",
                        user_id=user_id,
                        auth_token=user_id,
                    )
                )
            )

        for record in records:
            await manager.start(record.id)
        owner = next(record for record in records if record.user_id == "1")
        await manager.configure_lobby(
            owner.id,
            LobbySetupRequest(
                setup_id="base-game",
                player_count=6,
                pbem=True,
                vassals=False,
                victory_points_to_win=7,
            ),
        )
        for record, configuration in zip(
            records, PROMPT_CONFIGURATIONS, strict=True
        ):
            await manager.choose_lobby_house(record.id, rotation[configuration.name])
        await manager.launch_game(owner.id)
        await _wait_for_game_start(manager, records, timeout=30)
        for record in records:
            manager.set_autoplay(record.id, True)

        winner = await _wait_for_game_end(
            manager=manager,
            records=records,
            attempt_dir=attempt_dir,
            poll_seconds=poll_seconds,
            stall_seconds=stall_seconds,
            timeout_seconds=match_timeout_seconds,
        )
        game_document, game_mtime_ns = await _wait_for_terminal_game_document(
            game_path,
            expected_winner=winner,
        )
        completed_result = _build_game_result(
            game_number=game_number,
            winner=winner,
            assignments=assignments,
            game_document=game_document,
            records=records,
            store=store,
        )
        return completed_result
    finally:
        if manager is not None:
            await manager.stop_all()
        if telemetry is not None:
            telemetry.shutdown()
        if database is not None:
            try:
                provider_generations = await _collect_openrouter_generations(
                    database=database,
                    records=records,
                    settings=settings,
                )
            except Exception as error:
                provider_generations = _failed_provider_attribution(error)
            _write_json(
                attempt_dir / "provider-generations.json", provider_generations
            )
            if completed_result is not None:
                completed_result["providerAttribution"] = (
                    _provider_attribution_summary(provider_generations)
                )
            try:
                if completed_result is not None:
                    _require_sqlite_quick_check(database)
            except Exception as error:
                quick_check_error = error
            finally:
                database.close()
        if process is not None:
            await _stop_process(process)
        if server_log is not None:
            server_log.close()
        if quick_check_error is not None:
            raise quick_check_error
        if completed_result is not None:
            completed_result["artifacts"] = {
                "gameSavedMtimeNs": game_mtime_ns,
                "sqliteQuickCheck": "ok",
            }
            _write_json(attempt_dir / "result.json", completed_result)


async def _start_game_server(
    *, game_path: Path, port: int, max_rounds: int | None, log: BinaryIO
) -> asyncio.subprocess.Process:
    executable = GAME_SERVER_DIR / "node_modules" / ".bin" / "ts-node"
    if not executable.is_file():
        raise RuntimeError(
            "Game-server dependencies are missing; follow README.md before evaluation"
        )
    environment = os.environ.copy()
    environment.pop("MASTER_API_ENABLED", None)
    environment.update(
        {
            "NODE_ENV": "development",
            "PORT": str(port),
            "LOCAL_GAME_PATH": str(game_path),
        }
    )
    if max_rounds is not None:
        environment["HARNESS_TEST_MAX_TURNS"] = str(max_rounds)
    else:
        environment.pop("HARNESS_TEST_MAX_TURNS", None)
    return await asyncio.create_subprocess_exec(
        str(executable),
        "-T",
        "src/server/server.ts",
        cwd=GAME_SERVER_DIR,
        env=environment,
        stdout=log,
        stderr=asyncio.subprocess.STDOUT,
    )


async def _wait_for_server(
    process: asyncio.subprocess.Process, port: int, *, timeout: float
) -> None:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        if process.returncode is not None:
            raise RuntimeError(f"Game server exited with status {process.returncode}")
        if await _port_is_open(port):
            return
        await asyncio.sleep(0.1)
    raise RuntimeError(f"Game server did not listen on port {port} within {timeout:g}s")


async def _port_is_open(port: int) -> bool:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", port), timeout=0.25
        )
    except (OSError, TimeoutError):
        return False
    writer.close()
    await writer.wait_closed()
    return True


async def _wait_for_game_start(
    manager: AgentManager, records: list[Any], *, timeout: float
) -> None:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        observations = [manager.get_observation(record.id) for record in records]
        if all(
            observation
            and observation.get("statePath", [None])[0] == "ingame"
            for observation in observations
        ):
            return
        await asyncio.sleep(0.1)
    raise RuntimeError("The lobby did not launch within the timeout")


async def _wait_for_game_end(
    *,
    manager: AgentManager,
    records: list[Any],
    attempt_dir: Path,
    poll_seconds: float,
    stall_seconds: float,
    timeout_seconds: float,
) -> str:
    started = monotonic()
    last_change = started
    last_signature: tuple[Any, ...] | None = None
    last_progress_write = 0.0
    while monotonic() - started < timeout_seconds:
        observations = [manager.get_observation(record.id) for record in records]
        runtimes = [manager.get_runtime(record.id) for record in records]
        run_counts = [
            manager.store.get_run_metrics(record.id)["runCount"] for record in records
        ]
        signature = _progress_signature(
            records=records,
            observations=observations,
            runtimes=runtimes,
            run_counts=run_counts,
        )
        if signature != last_signature:
            last_signature = signature
            last_change = monotonic()

        terminal_winner: str | None = None
        for observation in observations:
            path = (observation or {}).get("statePath", [])
            if path and path[-1] == "game-ended":
                winner = (observation or {}).get("pendingDecision", {}).get("winner")
                terminal_winner = _validate_winner_house(
                    winner, source="terminal observation"
                )
                break
        if terminal_winner is not None and all(
            runtime.current_run_id is None for runtime in runtimes
        ):
            return terminal_winner

        blocked = [
            {
                "configuration": record.name,
                "statePath": (observation or {}).get("statePath", []),
                "error": runtime.last_error,
            }
            for record, observation, runtime in zip(
                records, observations, runtimes, strict=True
            )
            if (observation or {}).get("isYourTurn")
            and not runtime.autoplay
            and runtime.status != "running"
        ]
        if blocked:
            raise RuntimeError(f"Autoplay stopped at a required decision: {blocked}")
        disconnected = [
            record.name
            for record, runtime in zip(records, runtimes, strict=True)
            if runtime.status in {"error", "disconnected", "banned", "stopped"}
        ]
        if disconnected:
            raise RuntimeError(f"Game connections failed: {disconnected}")

        now = monotonic()
        if now - last_progress_write >= 10:
            _write_json(
                attempt_dir / "progress.json",
                {
                    "updatedAt": _now(),
                    "elapsedSeconds": round(now - started, 1),
                    "agents": [
                        {
                            "configuration": record.name,
                            "status": runtime.status,
                            "autoplay": runtime.autoplay,
                            "stateId": (observation or {}).get("game", {}).get(
                                "stateId"
                            ),
                            "statePath": (observation or {}).get("statePath", []),
                            "isYourTurn": (observation or {}).get("isYourTurn"),
                            "lastError": runtime.last_error,
                            "currentRunId": runtime.current_run_id,
                            "runStartedAt": runtime.run_started_at,
                            "runCount": run_count,
                        }
                        for record, observation, runtime, run_count in zip(
                            records, observations, runtimes, run_counts, strict=True
                        )
                    ],
                },
            )
            last_progress_write = now
        if now - last_change > stall_seconds:
            raise RuntimeError(
                f"Game state did not change for {stall_seconds:g} seconds"
            )
        await asyncio.sleep(poll_seconds)
    raise RuntimeError(f"Game exceeded the {timeout_seconds / 3_600:g}-hour timeout")


def _progress_signature(
    *,
    records: list[Any],
    observations: list[dict[str, Any] | None],
    runtimes: list[Any],
    run_counts: list[int],
) -> tuple[Any, ...]:
    """Represent durable and in-flight progress without using elapsed time."""

    return tuple(
        (
            record.id,
            (observation or {}).get("game", {}).get("stateId"),
            (observation or {}).get("game", {}).get("phase"),
            runtime.status,
            runtime.current_run_id,
            runtime.run_started_at,
            run_count,
        )
        for record, observation, runtime, run_count in zip(
            records, observations, runtimes, run_counts, strict=True
        )
    )


async def _wait_for_terminal_game_document(
    path: Path,
    *,
    expected_winner: str,
    timeout: float = 15.0,
    stable_seconds: float = 1.0,
    poll_seconds: float = 0.1,
) -> tuple[dict[str, Any], int]:
    """Wait for a matching terminal save whose mtime has stopped changing."""

    expected_winner = _validate_winner_house(
        expected_winner, source="terminal observation"
    )
    deadline = monotonic() + timeout
    stable_signature: tuple[int, int] | None = None
    stable_since: float | None = None
    last_problem = "the save file does not exist"
    while monotonic() < deadline:
        try:
            before = path.stat()
            document = json.loads(path.read_text())
            after = path.stat()
        except (OSError, json.JSONDecodeError) as error:
            last_problem = str(error)
            stable_signature = None
            stable_since = None
            await asyncio.sleep(poll_seconds)
            continue

        signature = (after.st_mtime_ns, after.st_size)
        if signature != (before.st_mtime_ns, before.st_size):
            last_problem = "the save changed while it was being read"
            stable_signature = None
            stable_since = None
            await asyncio.sleep(poll_seconds)
            continue

        saved_winner = _terminal_winner(document)
        if saved_winner is None:
            last_problem = "the saved game is not terminal"
            stable_signature = None
            stable_since = None
        else:
            saved_winner = _validate_winner_house(
                saved_winner, source="saved terminal game"
            )
            if saved_winner != expected_winner:
                raise RuntimeError(
                    "Saved terminal winner does not match the authoritative "
                    f"observation: {saved_winner!r} != {expected_winner!r}"
                )
            now = monotonic()
            if signature != stable_signature:
                stable_signature = signature
                stable_since = now
            elif stable_since is not None and now - stable_since >= stable_seconds:
                return document, after.st_mtime_ns

        await asyncio.sleep(poll_seconds)
    raise RuntimeError(
        f"The game server did not produce a stable terminal save within {timeout:g}s: "
        f"{last_problem}"
    )


def _terminal_winner(game_document: dict[str, Any]) -> Any:
    state: Any = game_document.get("childGameState")
    if not isinstance(state, dict) or state.get("type") != "ingame":
        return None
    while isinstance(state.get("childGameState"), dict):
        state = state["childGameState"]
    return state.get("winner") if state.get("type") == "game-ended" else None


def _validate_winner_house(value: Any, *, source: str) -> str:
    if not isinstance(value, str) or value not in HOUSES:
        raise RuntimeError(f"Invalid winner house from {source}: {value!r}")
    return value


def _require_sqlite_quick_check(database: Database) -> None:
    with database.lock:
        rows = database.connection.execute("PRAGMA quick_check").fetchall()
    messages = [str(row[0]) for row in rows]
    if messages != ["ok"]:
        raise RuntimeError(f"SQLite quick_check failed: {messages}")


async def _preflight_openrouter_quota(
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Reject a key whose explicit OpenRouter spending limit is exhausted."""

    if settings.model_provider != "OpenRouter" or not settings.openrouter_token:
        return
    endpoint = settings.openrouter_base_url.rstrip("/") + "/key"
    owns_client = client is None
    active_client = client or httpx.AsyncClient(timeout=10)
    try:
        try:
            response = await active_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {settings.openrouter_token}"},
            )
        except httpx.HTTPError as error:
            raise RuntimeError(
                "OpenRouter quota preflight request failed "
                f"({type(error).__name__})"
            ) from error
        if response.status_code != 200:
            raise RuntimeError(
                f"OpenRouter quota preflight returned HTTP {response.status_code}"
            )
        try:
            payload = response.json()
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "OpenRouter quota preflight returned an invalid response"
            ) from error
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError("OpenRouter quota preflight returned an invalid response")

        limit = _optional_number(data.get("limit"))
        if limit is None:
            return
        remaining = _optional_number(data.get("limit_remaining"))
        usage = _optional_number(data.get("usage"))
        exhausted = limit <= 0
        if remaining is not None:
            exhausted = exhausted or remaining <= 0
        elif usage is not None:
            exhausted = exhausted or usage >= limit
        if exhausted:
            raise RuntimeError(
                "OpenRouter API key spending limit is exhausted; increase or reset "
                "the limit before starting a new evaluation attempt"
            )
    finally:
        if owns_client:
            await active_client.aclose()


async def _collect_openrouter_generations(
    *,
    database: Database,
    records: list[Any],
    settings: Settings,
    client: httpx.AsyncClient | None = None,
    retries: int = 2,
    retry_delay_seconds: float = 0.25,
    deadline_seconds: float = 60,
) -> dict[str, Any]:
    """Fetch non-textual routing metadata for every persisted model response."""

    response_rows = _persisted_response_rows(database, records)
    if not response_rows:
        return _provider_generation_artifact([])
    if settings.model_provider != "OpenRouter" or not settings.openrouter_token:
        generations = [
            {
                **row,
                "provider": None,
                "model": None,
                "costUsd": None,
                "latencyMs": None,
                "error": "OpenRouter attribution is not configured",
            }
            for row in response_rows
        ]
        return _provider_generation_artifact(generations)

    endpoint = settings.openrouter_base_url.rstrip("/") + "/generation"
    owns_client = client is None
    active_client = client or httpx.AsyncClient(timeout=10)
    semaphore = asyncio.Semaphore(4)

    def unavailable(row: dict[str, Any], error: str) -> dict[str, Any]:
        return {
            **row,
            "provider": None,
            "model": None,
            "costUsd": None,
            "latencyMs": None,
            "error": error,
        }

    async def collect(row: dict[str, Any]) -> dict[str, Any]:
        try:
            async with semaphore:
                metadata, error = await _fetch_openrouter_generation(
                    client=active_client,
                    endpoint=endpoint,
                    api_key=settings.openrouter_token,
                    response_id=row["responseId"],
                    retries=retries,
                    retry_delay_seconds=retry_delay_seconds,
                )
            return {
                **row,
                "provider": metadata.get("provider_name") if metadata else None,
                "model": metadata.get("model") if metadata else None,
                "costUsd": _optional_number(metadata.get("total_cost"))
                if metadata
                else None,
                "latencyMs": _optional_number(metadata.get("latency"))
                if metadata
                else None,
                "error": error,
            }
        except asyncio.CancelledError:
            raise
        except Exception as error:
            return unavailable(
                row,
                f"OpenRouter attribution failed ({type(error).__name__})",
            )

    tasks = [asyncio.create_task(collect(row)) for row in response_rows]
    try:
        done, pending = await asyncio.wait(tasks, timeout=deadline_seconds)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        generations = [
            task.result()
            if task in done
            else unavailable(row, "OpenRouter attribution exceeded its deadline")
            for row, task in zip(response_rows, tasks, strict=True)
        ]
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if owns_client:
            await active_client.aclose()
    return _provider_generation_artifact(generations)


def _persisted_response_rows(
    database: Database, records: list[Any]
) -> list[dict[str, Any]]:
    configurations = {record.id: record.name for record in records}
    with database.lock:
        rows = database.connection.execute(
            """
            SELECT id, agent_id, response_id, raw_usage_json
            FROM agent_runs
            WHERE (response_id IS NOT NULL AND response_id != '')
               OR (raw_usage_json IS NOT NULL AND raw_usage_json != '[]')
            ORDER BY created_at ASC, id ASC
            """
        ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        raw_usage = json.loads(row["raw_usage_json"] or "[]")
        response_ids = [
            str(item["response_id"])
            for item in raw_usage
            if isinstance(item, dict) and item.get("response_id")
        ]
        if row["response_id"]:
            response_ids.append(str(row["response_id"]))
        for response_index, response_id in enumerate(dict.fromkeys(response_ids)):
            result.append(
                {
                    "runId": str(row["id"]),
                    "agentId": str(row["agent_id"]),
                    "configuration": configurations.get(
                        str(row["agent_id"]), "unknown"
                    ),
                    "responseId": response_id,
                    "responseIndex": response_index,
                }
            )
    return result


async def _fetch_openrouter_generation(
    *,
    client: httpx.AsyncClient,
    endpoint: str,
    api_key: str,
    response_id: str,
    retries: int,
    retry_delay_seconds: float,
) -> tuple[dict[str, Any] | None, str | None]:
    problem = "OpenRouter attribution is unavailable"
    for attempt in range(retries + 1):
        transient = False
        try:
            response = await client.get(
                endpoint,
                params={"id": response_id},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if response.status_code == 200:
                payload = response.json()
                data = payload.get("data") if isinstance(payload, dict) else None
                if isinstance(data, dict):
                    return data, None
                problem = "OpenRouter returned an invalid generation document"
            else:
                problem = f"OpenRouter returned HTTP {response.status_code}"
                transient = response.status_code in {404, 408, 409, 425, 429} or (
                    response.status_code >= 500
                )
        except httpx.HTTPError as error:
            problem = f"OpenRouter request failed ({type(error).__name__})"
            transient = True
        except (TypeError, ValueError):
            problem = "OpenRouter returned an invalid generation document"

        if not transient or attempt == retries:
            break
        await asyncio.sleep(retry_delay_seconds * (2**attempt))
    return None, problem


def _provider_generation_artifact(
    generations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "generatedAt": _now(),
        "source": "OpenRouter GET /generation",
        "generations": generations,
        **_provider_attribution_summary({"generations": generations}),
    }


def _provider_attribution_summary(value: dict[str, Any]) -> dict[str, Any]:
    generations = value.get("generations", [])
    provider_counts = Counter(
        item["provider"] for item in generations if item.get("provider")
    )
    model_counts = Counter(item["model"] for item in generations if item.get("model"))
    attributed = sum(1 for item in generations if item.get("provider"))
    model_attributed = sum(1 for item in generations if item.get("model"))
    return {
        "requestedCount": len(generations),
        "attributedCount": attributed,
        "modelAttributedCount": model_attributed,
        "unavailableCount": len(generations) - attributed,
        "providerCounts": dict(sorted(provider_counts.items())),
        "modelCounts": dict(sorted(model_counts.items())),
    }


def _failed_provider_attribution(error: Exception) -> dict[str, Any]:
    return {
        "generatedAt": _now(),
        "source": "OpenRouter GET /generation",
        "generations": [],
        "collectionError": (
            "Provider attribution was temporarily unavailable "
            f"({type(error).__name__})"
        ),
        "requestedCount": 0,
        "attributedCount": 0,
        "modelAttributedCount": 0,
        "unavailableCount": 0,
        "providerCounts": {},
        "modelCounts": {},
    }


async def _refresh_completed_provider_attribution(
    *, output: Path, attempt: dict[str, Any], settings: Settings
) -> bool:
    """Retry missing provider metadata without replaying a completed game."""

    attempt_dir = output / str(attempt["directory"])
    artifact_path = attempt_dir / "provider-generations.json"
    try:
        existing = (
            json.loads(artifact_path.read_text()) if artifact_path.is_file() else None
        )
    except (OSError, json.JSONDecodeError):
        existing = None
    if (
        isinstance(existing, dict)
        and not existing.get("collectionError")
        and int(existing.get("unavailableCount") or 0) == 0
    ):
        return False

    database_path = attempt_dir / "harness.db"
    result_path = attempt_dir / "result.json"
    if not database_path.is_file() or not result_path.is_file():
        return False

    database: Database | None = None
    try:
        database = Database(database_path)
        records = AgentStore(database).list_agents()
        artifact = await _collect_openrouter_generations(
            database=database,
            records=records,
            settings=settings,
        )
        result = json.loads(result_path.read_text())
        result["providerAttribution"] = _provider_attribution_summary(artifact)
        _write_json(artifact_path, artifact)
        _write_json(result_path, result)
        return True
    except Exception:
        return False
    finally:
        if database is not None:
            database.close()


def _optional_number(value: Any) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _stop_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except TimeoutError:
        process.kill()
        await process.wait()


def _build_game_result(
    *,
    game_number: int,
    winner: str,
    assignments: list[dict[str, str]],
    game_document: dict[str, Any],
    records: list[Any],
    store: AgentStore,
) -> dict[str, Any]:
    winner = _validate_winner_house(winner, source="result builder")
    saved_winner = _terminal_winner(game_document)
    if saved_winner != winner:
        raise RuntimeError(
            f"Saved terminal winner does not match result winner: {saved_winner!r}"
        )
    ingame = game_document.get("childGameState", {})
    game = ingame.get("game", {})
    houses = {house["id"]: house for house in game.get("houses", [])}
    iron_throne = list(game.get("ironThroneTrack", []))
    assignment_by_house = {item["house"]: item for item in assignments}
    if set(assignment_by_house) != set(HOUSES):
        raise RuntimeError("Assignments do not contain each six-player house exactly once")
    missing_houses = set(HOUSES) - set(houses)
    if missing_houses:
        raise RuntimeError(
            f"Saved game is missing assigned houses: {sorted(missing_houses)}"
        )
    if winner not in houses:
        raise RuntimeError(f"Winner house {winner!r} is absent from the saved game")
    metrics_by_name = {
        record.name: store.get_run_metrics(record.id) for record in records
    }
    standings = []
    for house_id, house in houses.items():
        assignment = assignment_by_house.get(house_id)
        if assignment is None:
            continue
        metrics = metrics_by_name[assignment["configuration"]]
        standings.append(
            {
                **assignment,
                "victoryPoints": int(house.get("currentVictoryPoints") or 0),
                "landAreas": int(house.get("controlledLandAreaCount") or 0),
                "supply": int(house.get("supplyLevel") or 0),
                "powerTokens": int(house.get("powerTokens") or 0),
                "ironThronePosition": (
                    iron_throne.index(house_id) + 1
                    if house_id in iron_throne
                    else None
                ),
                "metrics": metrics,
            }
        )
    standings.sort(
        key=lambda item: (
            -item["victoryPoints"],
            -item["landAreas"],
            -item["supply"],
            item["ironThronePosition"] or 99,
        )
    )
    for placement, standing in enumerate(standings, 1):
        standing["placement"] = placement
    return {
        "gameNumber": game_number,
        "completedAt": _now(),
        "winner": winner,
        "round": game.get("turn"),
        "standings": standings,
    }


def _load_manifest(
    path: Path, args: argparse.Namespace, output: Path, settings: Settings
) -> dict[str, Any]:
    provenance = _build_provenance(args, settings)
    if path.is_file():
        manifest = json.loads(path.read_text())
        if manifest.get("model") != args.model:
            raise RuntimeError("Existing evaluation manifest uses another model ID")
        if int(manifest.get("gameCount", 0)) != args.games:
            raise RuntimeError("Existing evaluation manifest uses another game count")
        existing_provenance = manifest.get("provenance")
        if existing_provenance is None:
            if any(game.get("attempts") for game in manifest.get("games", [])):
                raise RuntimeError(
                    "Existing evaluation has attempts but no provenance; start a new "
                    "evaluation directory"
                )
            manifest["provenance"] = provenance
            manifest["schemaVersion"] = 2
            manifest["configurations"] = [
                item.model_dump() for item in PROMPT_CONFIGURATIONS
            ]
            manifest["games"] = _evaluation_schedule(args.games)
            _write_json(path, manifest)
        else:
            _validate_reproducible_provenance(existing_provenance, provenance)
            _validate_evaluation_schedule(manifest.get("games"), args.games)
        return manifest
    manifest = {
        "schemaVersion": 2,
        "createdAt": _now(),
        "outputDirectory": str(output),
        "model": args.model,
        "gameCount": args.games,
        "maxRounds": args.max_rounds,
        "configurations": [item.model_dump() for item in PROMPT_CONFIGURATIONS],
        "provenance": provenance,
        "games": _evaluation_schedule(args.games),
    }
    _write_json(path, manifest)
    return manifest


def _build_provenance(args: argparse.Namespace, settings: Settings) -> dict[str, Any]:
    rules_path = settings.resolved_rules_path
    return {
        "repositories": {
            "root": _git_provenance(
                PROJECT_ROOT,
                ignore_dirty_submodules=True,
            ),
            "swordsAndRavens": _git_provenance(
                PROJECT_ROOT / "swords-and-ravens",
                ignored_paths=(MUTABLE_GAME_SAVE_PATH,),
            ),
        },
        "prompts": [
            {
                "configuration": configuration.name,
                "configuredSystemPromptSha256": _sha256_text(
                    _system_prompt(configuration)
                ),
                "effectiveInstructionsSha256": _sha256_text(
                    _effective_instructions(configuration)
                ),
            }
            for configuration in PROMPT_CONFIGURATIONS
        ],
        "rules": {
            "available": rules_path.is_file(),
            "sha256": _sha256_file(rules_path) if rules_path.is_file() else None,
        },
        "model": {
            "id": args.model,
            "provider": settings.model_provider,
            "baseUrl": _sanitized_base_url(settings.model_base_url),
            "baseUrlSha256": _sha256_text(settings.model_base_url),
            "requestTimeoutSeconds": settings.model_request_timeout_seconds,
            "runTimeoutSeconds": settings.model_run_timeout_seconds,
            "apiMaxRetries": settings.model_api_max_retries,
            "maxConcurrency": settings.model_max_concurrency,
            "maxOutputTokens": settings.model_max_output_tokens,
            "sessionHistoryItems": settings.model_session_history_items,
            "autoplayMaxConsecutiveFailures": (
                settings.autoplay_max_consecutive_failures
            ),
            "autoplayRetryBaseSeconds": settings.autoplay_retry_base_seconds,
            "reasoningEffort": "low",
            "toolChoice": "required",
            "parallelToolCalls": False,
            "store": False,
            "agentSdkMaxTurns": AGENT_SDK_MAX_TURNS,
            "resetToolChoice": False,
            "rulesOracleMaxOutputTokens": 900,
            "providerRouting": (
                settings.openrouter_provider_routing
                if settings.model_provider == "OpenRouter"
                else None
            ),
        },
        "evaluation": {
            "gamePort": args.game_port,
            "maxRounds": args.max_rounds,
            "pollSeconds": args.poll_seconds,
            "stallSeconds": args.stall_seconds,
            "matchTimeoutHours": args.match_timeout_hours,
        },
    }


def _validate_reproducible_provenance(
    existing: dict[str, Any], current: dict[str, Any]
) -> None:
    for key in ("repositories", "prompts", "rules", "model", "evaluation"):
        if existing.get(key) != current.get(key):
            raise RuntimeError(
                f"Existing evaluation provenance has different {key}; start a new "
                "evaluation directory"
            )


def _git_provenance(
    directory: Path,
    *,
    ignored_paths: tuple[str, ...] = (),
    ignore_dirty_submodules: bool = False,
) -> dict[str, Any]:
    commit = _run_git(directory, "rev-parse", "HEAD")
    submodule_option = (
        ("--ignore-submodules=dirty",) if ignore_dirty_submodules else ()
    )
    pathspec = (".", *(f":(exclude){path}" for path in ignored_paths))
    status = _run_git(
        directory,
        "status",
        "--porcelain",
        "--untracked-files=normal",
        *submodule_option,
        "--",
        *pathspec,
    )
    diff = _run_git(
        directory,
        "diff",
        "--no-ext-diff",
        "--binary",
        *submodule_option,
        "HEAD",
        "--",
        *pathspec,
    )
    untracked = _hash_untracked_files(directory, ignored_paths=ignored_paths)
    worktree_fingerprint = (
        _sha256_text(f"{status}\0{diff}\0{untracked}")
        if status is not None and diff is not None and untracked is not None
        else None
    )
    return {
        "commit": commit or None,
        "dirty": bool(status) if status is not None else None,
        "worktreeSha256": worktree_fingerprint,
    }


def _hash_untracked_files(
    directory: Path, *, ignored_paths: tuple[str, ...] = ()
) -> str | None:
    listing = _run_git(
        directory,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
    )
    if listing is None:
        return None
    digest = hashlib.sha256()
    ignored = set(ignored_paths)
    for relative_name in sorted(
        name for name in listing.split("\0") if name and name not in ignored
    ):
        digest.update(relative_name.encode(errors="surrogateescape"))
        path = directory / relative_name
        try:
            if path.is_symlink():
                digest.update(b"symlink\0")
                digest.update(os.readlink(path).encode(errors="surrogateescape"))
            elif path.is_file():
                digest.update(b"file\0")
                with path.open("rb") as source:
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk)
            else:
                digest.update(b"other\0")
        except OSError as error:
            digest.update(f"error:{type(error).__name__}".encode())
    return digest.hexdigest()


def _run_git(directory: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _system_prompt(configuration: PromptConfiguration) -> str:
    return f"{DEFAULT_PROMPT}\n\n{configuration.suffix}"


def _effective_instructions(configuration: PromptConfiguration) -> str:
    return _system_prompt(configuration).rstrip() + STRATEGIC_INSTRUCTIONS


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sanitized_base_url(value: str) -> str:
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return f"{parsed.scheme}://{host}{parsed.path}".rstrip("/")


def _evaluation_schedule(game_count: int) -> list[dict[str, Any]]:
    return [
        {
            "number": number,
            "rotation": house_rotation(number),
            "users": user_rotation(number),
            "attempts": [],
        }
        for number in range(1, game_count + 1)
    ]


def _validate_evaluation_schedule(value: Any, game_count: int) -> None:
    expected = _evaluation_schedule(game_count)
    if not isinstance(value, list) or len(value) != len(expected):
        raise RuntimeError("Existing evaluation manifest has a different schedule")
    for actual_game, expected_game in zip(value, expected, strict=True):
        if any(
            actual_game.get(key) != expected_game[key]
            for key in ("number", "rotation", "users")
        ):
            raise RuntimeError(
                "Existing evaluation manifest has a different house or user schedule"
            )


def _game_entry(manifest: dict[str, Any], number: int) -> dict[str, Any]:
    return next(game for game in manifest["games"] if game["number"] == number)


def _write_summary(output: Path, manifest: dict[str, Any]) -> None:
    results = []
    for game in manifest["games"]:
        completed = next(
            (
                attempt
                for attempt in game["attempts"]
                if attempt.get("status") == "completed"
            ),
            None,
        )
        if completed is None:
            continue
        result_path = output / completed["directory"] / "result.json"
        if result_path.is_file():
            results.append(json.loads(result_path.read_text()))
    _write_json(output / "summary.json", summarize_results(results))


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    ratings = {item.name: 1500.0 for item in PROMPT_CONFIGURATIONS}
    configurations: dict[str, dict[str, Any]] = {
        item.name: {
            "configuration": item.name,
            "games": 0,
            "wins": 0,
            "placementTotal": 0,
            "victoryPointTotal": 0,
            "completedRuns": 0,
            "failedRuns": 0,
            "cancelledRuns": 0,
            "modelRequests": 0,
            "inputTokens": 0,
            "outputTokens": 0,
            "totalTokens": 0,
            "cachedInputTokens": 0,
            "costUsd": 0.0,
        }
        for item in PROMPT_CONFIGURATIONS
    }
    houses = {
        house: {"house": house, "games": 0, "wins": 0, "placementTotal": 0}
        for house in HOUSES
    }

    for result in sorted(results, key=lambda item: item["gameNumber"]):
        standings = result["standings"]
        old_ratings = ratings.copy()
        deltas = {name: 0.0 for name in ratings}
        for standing in standings:
            name = standing["configuration"]
            metrics = standing["metrics"]
            values = configurations[name]
            values["games"] += 1
            values["wins"] += int(standing["house"] == result["winner"])
            values["placementTotal"] += standing["placement"]
            values["victoryPointTotal"] += standing["victoryPoints"]
            values["completedRuns"] += metrics["statusCounts"].get("completed", 0)
            values["failedRuns"] += metrics["statusCounts"].get("failed", 0)
            values["cancelledRuns"] += metrics["statusCounts"].get("cancelled", 0)
            values["modelRequests"] += int(metrics.get("modelRequests") or 0)
            tokens = metrics.get("tokens") or {}
            values["inputTokens"] += int(tokens.get("input") or 0)
            values["outputTokens"] += int(tokens.get("output") or 0)
            values["totalTokens"] += int(tokens.get("total") or 0)
            values["cachedInputTokens"] += int(tokens.get("cachedInput") or 0)
            values["costUsd"] += metrics["costUsd"]
            house_values = houses[standing["house"]]
            house_values["games"] += 1
            house_values["wins"] += int(standing["house"] == result["winner"])
            house_values["placementTotal"] += standing["placement"]

        for index, first in enumerate(standings):
            for second in standings[index + 1 :]:
                first_name = first["configuration"]
                second_name = second["configuration"]
                expected = 1 / (
                    1 + 10 ** ((old_ratings[second_name] - old_ratings[first_name]) / 400)
                )
                actual = 1.0 if first["placement"] < second["placement"] else 0.5
                change = 24 * (actual - expected) / 5
                deltas[first_name] += change
                deltas[second_name] -= change
        for name, change in deltas.items():
            ratings[name] += change

    ranking = []
    for name, values in configurations.items():
        games = values.pop("games")
        attempts = (
            values["completedRuns"] + values["failedRuns"] + values["cancelledRuns"]
        )
        ranking.append(
            {
                "configuration": name,
                "games": games,
                "wins": values["wins"],
                "averagePlacement": (
                    round(values.pop("placementTotal") / games, 3) if games else None
                ),
                "averageVictoryPoints": (
                    round(values.pop("victoryPointTotal") / games, 3)
                    if games
                    else None
                ),
                "reliability": (
                    round(values["completedRuns"] / attempts, 4) if attempts else None
                ),
                "costUsd": round(values["costUsd"], 6),
                "completedRuns": values["completedRuns"],
                "failedRuns": values["failedRuns"],
                "cancelledRuns": values["cancelledRuns"],
                "modelRequests": values["modelRequests"],
                "inputTokens": values["inputTokens"],
                "outputTokens": values["outputTokens"],
                "totalTokens": values["totalTokens"],
                "cachedInputTokens": values["cachedInputTokens"],
                "elo": round(ratings[name], 1),
            }
        )
    ranking.sort(key=lambda item: (-item["elo"], item["configuration"]))
    house_effects = [
        {
            "house": house,
            "games": values["games"],
            "wins": values["wins"],
            "averagePlacement": (
                round(values["placementTotal"] / values["games"], 3)
                if values["games"]
                else None
            ),
        }
        for house, values in houses.items()
    ]
    return {
        "completedGames": len(results),
        "ranking": ranking,
        "houseEffects": house_effects,
        "eloMethod": (
            "Initial rating 1500; K=24; each six-player result is five pairwise "
            "comparisons per configuration with K divided by five. Ratings update "
            "simultaneously after each game."
        ),
    }


def _resolve_output(value: str | None) -> Path:
    if value:
        path = Path(value).expanduser()
        return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return PROJECT_ROOT / "data" / "evaluations" / stamp


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")
    temporary.replace(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run resumable same-model Raven Harness evaluation games."
    )
    parser.add_argument("--output", help="Artifact directory under the project root.")
    parser.add_argument("--model", default=DEFAULT_MODEL_ID)
    parser.add_argument("--games", type=int, default=12, choices=range(1, 13))
    parser.add_argument("--start-game", type=int, default=1, choices=range(1, 13))
    parser.add_argument("--game-port", type=int, default=5101)
    parser.add_argument("--max-rounds", type=int, choices=range(1, 11))
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--stall-seconds", type=float, default=360.0)
    parser.add_argument("--match-timeout-hours", type=float, default=6.0)
    parser.add_argument("--continue-on-error", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.start_game > args.games:
        raise SystemExit("--start-game cannot exceed --games")
    try:
        output = asyncio.run(run_evaluation(args))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    print(f"Evaluation artifacts: {output}")


if __name__ == "__main__":
    main()
