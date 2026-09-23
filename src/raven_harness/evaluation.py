from __future__ import annotations

import argparse
import asyncio
import fcntl
import hashlib
import json
import os
import signal
import subprocess
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any, BinaryIO
from urllib.parse import urlsplit

import httpx

from .agent_store import AgentStore
from .config import PROJECT_ROOT, Settings
from .database import Database
from .errors import safe_error_text
from .game.map_reference import load_map_reference
from .harness.configure import create_game_harness
from .harness.interface import PlayerHarness
from .harness.prompts import build_instructions
from .manager import AgentManager
from .models.tracing import CONTEXT_POLICY_NAME
from .rulebook import Rulebook
from .schemas import AgentCreate, DEFAULT_PROMPT, LobbySetupRequest
from .telemetry import Telemetry


HOUSES = ["stark", "greyjoy", "lannister", "tyrell", "martell", "baratheon"]
TOURNAMENT_MODELS = [
    "z-ai/glm-5.3-flash",
    "qwen/qwen3.7-flash",
    "openai/gpt-oss-120b",
    "~deepseek/deepseek-v4-flash-latest",
    "qwen/qwen3-235b-a22b-2507",
    "openai/gpt-5.6-luna",
]
TOURNAMENT_HARNESS_ID = "strategic-v1"
TOURNAMENT_GAMES = 12
DEFAULT_RANDOM_SEED = 1
RANDOM_SEED_NAMESPACE = "raven-harness-evaluation-v1"
EVALUATION_ROOT = PROJECT_ROOT / "data" / "evaluations"
GAME_SERVER_DIR = PROJECT_ROOT / "swords-and-ravens" / "agot-bg-game-server"
MUTABLE_GAME_SAVE_PATH = (
    "agot-bg-game-server/src/server/website-client/local-entire-game.json"
)


def house_rotation(game_number: int) -> dict[str, str]:
    """Return a two-block rotation in which every model gets each house."""

    index = (game_number - 1) % 12
    if index < 6:
        house_indexes = [(model_index + index) % 6 for model_index in range(6)]
    else:
        mirrored = index - 6
        house_indexes = [(mirrored - model_index) % 6 for model_index in range(6)]
    return {
        model: HOUSES[house_index]
        for model, house_index in zip(TOURNAMENT_MODELS, house_indexes, strict=True)
    }


def user_rotation(game_number: int) -> dict[str, str]:
    """Rotate local identities so every model owns exactly two games."""

    round_index = (game_number - 1) % 6
    return {
        model: str(1 + ((index - round_index) % 6))
        for index, model in enumerate(TOURNAMENT_MODELS)
    }


async def run_evaluation(args: argparse.Namespace) -> Path:
    """Run or resume exactly one sequential game of the mixed-model tournament."""

    settings = Settings()
    if not settings.model_api_key:
        raise RuntimeError(
            "Configure an API key for the selected model endpoint before starting "
            "an evaluation"
        )
    if not settings.resolved_rules_path.is_file():
        raise RuntimeError(
            "Rules oracle data is required for evaluation; run uv run raven-prepare-rules"
        )
    await _preflight_openrouter_quota(settings)
    verified_models = await _preflight_model_catalog(settings)
    if [row.get("id") for row in verified_models] != TOURNAMENT_MODELS:
        raise RuntimeError("Verified model catalog does not match tournament models")
    output = _resolve_output(args.output)
    output.mkdir(parents=True, exist_ok=True)
    runner_lock = _acquire_runner_lock(output)
    try:
        return await _run_evaluation_game(
            args=args,
            settings=settings,
            verified_models=verified_models,
            output=output,
        )
    finally:
        fcntl.flock(runner_lock.fileno(), fcntl.LOCK_UN)
        runner_lock.close()


async def _run_evaluation_game(
    *,
    args: argparse.Namespace,
    settings: Settings,
    verified_models: list[dict[str, Any]],
    output: Path,
) -> Path:
    manifest_path = output / "manifest.json"
    manifest = _load_manifest(manifest_path, args, output)
    manifest.pop("finishedAt", None)
    provenance = _build_provenance(args, settings)
    model_verification = {
        "source": "configured model endpoint catalog",
        "verifiedAt": _now(),
        "models": verified_models,
    }

    game_entry = next(
        (
            game
            for game in manifest["games"]
            if not any(
                attempt.get("status") == "completed" for attempt in game["attempts"]
            )
        ),
        None,
    )
    if game_entry is None:
        manifest["finishedAt"] = _now()
        _write_json(manifest_path, manifest)
        _write_summary(output, manifest)
        print("Tournament: all 12 games are already completed")
        return output

    game_number = int(game_entry["number"])
    resumable = _resumable_attempt(output, game_entry)
    if resumable is not None:
        saved_attempt, _ = resumable
        try:
            saved_provenance = saved_attempt.get("provenance")
            if not isinstance(saved_provenance, dict):
                raise RuntimeError("saved attempt has no runtime provenance")
            _validate_resumable_provenance(saved_provenance, provenance)
            if (
                saved_attempt.get("modelVerification", {}).get("models")
                != (model_verification["models"])
            ):
                raise RuntimeError("the verified model catalog changed")
        except RuntimeError as error:
            _reject_attempt_resume(saved_attempt, reason=str(error))
            resumable = None
    elif game_entry["attempts"]:
        latest = game_entry["attempts"][-1]
        if latest.get("status") != "completed":
            _reject_attempt_resume(
                latest,
                reason="the durable game state or agent database is missing",
            )

    if resumable is None:
        attempt_number = len(game_entry["attempts"]) + 1
        attempt_dir = (
            output / f"game-{game_number:02d}" / f"attempt-{attempt_number:02d}"
        )
        try:
            attempt_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            if any(attempt_dir.iterdir()):
                raise RuntimeError(
                    f"Unrecorded nonempty attempt directory blocks game "
                    f"{game_number}: {attempt_dir}"
                ) from None
        attempt = {
            "number": attempt_number,
            "status": "running",
            "directory": str(attempt_dir.relative_to(output)),
            "startedAt": _now(),
            "resumeCount": 0,
            "activeElapsedSeconds": 0.0,
            "provenance": provenance,
            "modelVerification": model_verification,
        }
        game_entry["attempts"].append(attempt)
        resume = False
        verb = "starting"
    else:
        attempt, attempt_dir = resumable
        attempt_number = int(attempt["number"])
        attempt.setdefault("interruptions", []).append(
            {
                key: attempt[key]
                for key in ("status", "finishedAt", "error")
                if key in attempt
            }
        )
        for key in ("finishedAt", "error", "winner"):
            attempt.pop(key, None)
        attempt.update(
            {
                "status": "running",
                "resumedAt": _now(),
                "resumeCount": int(attempt.get("resumeCount", 0)) + 1,
            }
        )
        resume = True
        verb = "resuming"

    _write_json(manifest_path, manifest)
    _write_summary(output, manifest)
    print(
        f"Game {game_number}: {verb} attempt {attempt_number} on port {args.game_port}"
    )
    segment_started = monotonic()
    try:
        result = await run_game(
            game_number=game_number,
            attempt_dir=attempt_dir,
            random_seed=int(game_entry["randomSeed"]),
            game_port=args.game_port,
            max_rounds=None,
            poll_seconds=args.poll_seconds,
            stall_seconds=args.stall_seconds,
            match_timeout_seconds=args.match_timeout_hours * 3_600,
            settings=settings,
            resume=resume,
        )
        attempt.update(
            {
                "status": "completed",
                "finishedAt": _now(),
                "winner": result["winner"],
            }
        )
        print(f"Game {game_number}: winner {result['winner']}")
    except asyncio.CancelledError:
        attempt.update({"status": "cancelled", "finishedAt": _now()})
        raise
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
        raise RuntimeError(error_text) from None
    finally:
        elapsed = float(attempt.get("activeElapsedSeconds") or 0)
        attempt["activeElapsedSeconds"] = round(
            elapsed + monotonic() - segment_started, 3
        )
        if all(
            any(
                candidate.get("status") == "completed"
                for candidate in scheduled["attempts"]
            )
            for scheduled in manifest["games"]
        ):
            manifest["finishedAt"] = _now()
        _write_json(manifest_path, manifest)
        _write_summary(output, manifest)
    return output


def _acquire_runner_lock(output: Path) -> BinaryIO:
    lock = (output / ".runner.lock").open("a+b")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise RuntimeError(
            f"Another tournament runner is already active for {output}"
        ) from None
    return lock


def _supersede_attempt(attempt: dict[str, Any], *, reason: str) -> None:
    attempt.update(
        {
            "status": "superseded",
            "finishedAt": _now(),
            "error": f"Attempt cannot be resumed: {reason}",
        }
    )


def _reject_attempt_resume(attempt: dict[str, Any], *, reason: str) -> None:
    """Keep a terminal failure intact when a changed runtime starts anew."""

    if attempt.get("status") == "failed":
        attempt["resumeRejectedReason"] = f"Attempt cannot be resumed: {reason}"
        return
    _supersede_attempt(attempt, reason=reason)


def _resumable_attempt(
    output: Path, game_entry: dict[str, Any]
) -> tuple[dict[str, Any], Path] | None:
    """Return the latest incomplete attempt when both durable stores exist."""

    attempts = game_entry.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return None
    attempt = attempts[-1]
    if not isinstance(attempt, dict) or attempt.get("status") not in {
        "running",
        "failed",
        "cancelled",
    }:
        return None
    game_number = int(game_entry["number"])
    attempt_number = attempt.get("number")
    if not isinstance(attempt_number, int) or isinstance(attempt_number, bool):
        raise RuntimeError(f"Game {game_number} has an invalid latest attempt")
    relative = f"game-{game_number:02d}/attempt-{attempt_number:02d}"
    if attempt.get("directory") != relative:
        raise RuntimeError(
            f"Game {game_number} attempt {attempt_number} has an invalid directory"
        )
    attempt_dir = output / relative
    if (
        not (attempt_dir / "game.json").is_file()
        or not (attempt_dir / "harness.db").is_file()
    ):
        return None
    return attempt, attempt_dir


async def run_game(
    *,
    game_number: int,
    attempt_dir: Path,
    random_seed: int,
    game_port: int,
    max_rounds: int | None,
    poll_seconds: float,
    stall_seconds: float,
    match_timeout_seconds: float,
    settings: Settings,
    harness_factory: Callable[[AgentStore], PlayerHarness] | None = None,
    resume: bool = False,
    seat_models: list[str] | None = None,
    seat_houses: list[str] | None = None,
) -> dict[str, Any]:
    attempt_dir = attempt_dir.resolve()
    if await _port_is_open(game_port):
        raise RuntimeError(f"Game-server port {game_port} is already in use")

    game_path = attempt_dir / "game.json"
    database_path = attempt_dir / "harness.db"
    server_log_path = attempt_dir / "game-server.log"
    expected_assignments = _run_assignments(
        game_number=game_number,
        seat_models=seat_models,
        seat_houses=seat_houses,
    )
    assignment_path = attempt_dir / "assignments.json"
    if resume:
        try:
            assignments = json.loads(assignment_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("Saved assignments cannot be loaded") from error
        if assignments != expected_assignments:
            raise RuntimeError("Saved assignments do not match the scheduled game")
    else:
        assignments = expected_assignments
        _write_json(assignment_path, assignments)

    server_log: BinaryIO | None = None
    process: asyncio.subprocess.Process | None = None
    database: Database | None = None
    store: AgentStore | None = None
    manager: AgentManager | None = None
    telemetry: Telemetry | None = None
    records: list[Any] = []
    completed_result: dict[str, Any] | None = None
    game_mtime_ns: int | None = None
    quick_check_error: Exception | None = None
    try:
        server_log = server_log_path.open("ab" if resume else "wb")
        process = await _start_game_server(
            game_path=game_path,
            port=game_port,
            max_rounds=max_rounds,
            random_seed=random_seed,
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
        harness = (
            harness_factory(store)
            if harness_factory
            else create_game_harness(settings, store, rulebook=rulebook)
        )
        manager = AgentManager(
            store=store,
            harness=harness,
            telemetry=telemetry,
            autoplay_max_consecutive_failures=(
                settings.autoplay_max_consecutive_failures
            ),
            autoplay_retry_base_seconds=settings.autoplay_retry_base_seconds,
            autoplay_max_capacity_failures=(
                settings.autoplay_max_capacity_failures
            ),
            autoplay_capacity_retry_base_seconds=(
                settings.autoplay_capacity_retry_base_seconds
            ),
            durable_game_path=game_path,
        )

        assignment_by_user = {
            assignment["userId"]: assignment for assignment in assignments
        }
        if resume:
            records = store.list_agents()
            _validate_resumed_agents(
                records=records,
                assignments=assignments,
                game_port=game_port,
            )
        else:
            for assignment in assignments:
                model = assignment["model"]
                user_id = assignment["userId"]
                records.append(
                    store.create_agent(
                        AgentCreate(
                            name=_seat_name(assignment, assignments),
                            model=model,
                            system_prompt=DEFAULT_PROMPT,
                            game_server_url=f"ws://127.0.0.1:{game_port}",
                            game_id="1",
                            user_id=user_id,
                            auth_token=user_id,
                        )
                    )
                )

        for record in records:
            await manager.start(record.id)
        if not resume:
            owner = next(record for record in records if record.user_id == "1")
            await manager.configure_lobby(
                owner.id,
                LobbySetupRequest(
                    setup_id="base-game",
                    player_count=len(assignments),
                    pbem=True,
                    vassals=False,
                    victory_points_to_win=7,
                ),
            )
            for record in records:
                await manager.choose_lobby_house(
                    record.id, assignment_by_user[record.user_id]["house"]
                )
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
            random_seed=random_seed,
            winner=winner,
            assignments=assignments,
            game_document=game_document,
            records=records,
            store=store,
            endpoint_provider=settings.model_provider,
        )
        return completed_result
    finally:
        if manager is not None:
            await manager.stop_all()
        if telemetry is not None:
            telemetry.shutdown()
        if database is not None:
            try:
                if store is not None:
                    _write_json(
                        attempt_dir / "metrics.json",
                        _aggregate_run_metrics(
                            [
                                store.get_run_metrics(record.id)
                                for record in store.list_agents()
                            ]
                        ),
                    )
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


def _validate_resumed_agents(
    *,
    records: list[Any],
    assignments: list[dict[str, str]],
    game_port: int,
) -> None:
    if len(records) != len(assignments):
        raise RuntimeError("Saved attempt does not contain the expected agents")
    by_user = {record.user_id: record for record in records}
    if len(by_user) != len(records) or set(by_user) != {
        assignment["userId"] for assignment in assignments
    }:
        raise RuntimeError("Saved attempt agent seats do not match its assignments")
    expected_url = f"ws://127.0.0.1:{game_port}"
    for assignment in assignments:
        model = assignment["model"]
        record = by_user[assignment["userId"]]
        if (
            record.name != _seat_name(assignment, assignments)
            or record.model != model
            or record.system_prompt != DEFAULT_PROMPT
            or record.game_server_url != expected_url
            or record.game_id != "1"
            or record.user_id != assignment["userId"]
            or record.auth_token.get_secret_value() != assignment["userId"]
        ):
            raise RuntimeError(
                f"Saved agent {model!r} does not match its tournament assignment"
            )


def _run_assignments(
    *,
    game_number: int,
    seat_models: list[str] | None,
    seat_houses: list[str] | None,
) -> list[dict[str, str]]:
    if seat_models is None and seat_houses is None:
        rotation = house_rotation(game_number)
        users = user_rotation(game_number)
        pairs = [(model, rotation[model], users[model]) for model in TOURNAMENT_MODELS]
    else:
        if seat_models is None or seat_houses is None:
            raise RuntimeError("seat_models and seat_houses must be supplied together")
        if len(seat_models) != len(seat_houses):
            raise RuntimeError("seat_models and seat_houses must have equal lengths")
        supported_houses = {
            3: {"baratheon", "lannister", "stark"},
            6: set(HOUSES),
        }
        expected_houses = supported_houses.get(len(seat_models))
        if expected_houses is None or set(seat_houses) != expected_houses:
            raise RuntimeError(
                "Explicit seats must match the native three- or six-player "
                "base-game houses"
            )
        if any(
            not isinstance(model, str) or not model.strip() for model in seat_models
        ):
            raise RuntimeError("Every explicit seat must have a model ID")
        pairs = [
            (model.strip(), house, str(index))
            for index, (model, house) in enumerate(
                zip(seat_models, seat_houses, strict=True), start=1
            )
        ]
    return [
        {
            "model": model,
            "house": house,
            "userId": user_id,
            "harness": TOURNAMENT_HARNESS_ID,
            "promptSha256": _sha256_text(_effective_instructions()),
        }
        for model, house, user_id in pairs
    ]


def _seat_name(assignment: dict[str, str], assignments: list[dict[str, str]]) -> str:
    model = assignment["model"]
    if sum(item["model"] == model for item in assignments) == 1:
        return model
    return f"{model} seat {assignment['userId']}"


async def _start_game_server(
    *,
    game_path: Path,
    port: int,
    max_rounds: int | None,
    random_seed: int,
    log: BinaryIO,
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
            "HARNESS_RANDOM_SEED": str(_require_uint32(random_seed)),
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
            observation and observation.get("statePath", [None])[0] == "ingame"
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
                "model": record.model,
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
                            "model": record.model,
                            "status": runtime.status,
                            "autoplay": runtime.autoplay,
                            "stateId": (observation or {})
                            .get("game", {})
                            .get("stateId"),
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
        if stall_seconds > 0 and now - last_change > stall_seconds:
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
    """Reject an exhausted OpenRouter key limit or workspace credit balance."""

    if not settings.openrouter_token:
        return
    base_url = settings.openrouter_base_url.rstrip("/")
    owns_client = client is None
    active_client = client or httpx.AsyncClient(timeout=10)

    async def quota_data(path: str, label: str) -> dict[str, Any]:
        endpoint = base_url + path
        try:
            response = await active_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {settings.openrouter_token}"},
            )
        except httpx.HTTPError as error:
            raise RuntimeError(
                f"OpenRouter {label} preflight request failed ({type(error).__name__})"
            ) from error
        if response.status_code != 200:
            raise RuntimeError(
                f"OpenRouter {label} preflight returned HTTP {response.status_code}"
            )
        try:
            payload = response.json()
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                f"OpenRouter {label} preflight returned an invalid response"
            ) from error
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError(
                f"OpenRouter {label} preflight returned an invalid response"
            )
        return data

    try:
        key_data = await quota_data("/key", "key-limit")
        limit = _optional_number(key_data.get("limit"))
        if limit is not None:
            remaining = _optional_number(key_data.get("limit_remaining"))
            usage = _optional_number(key_data.get("usage"))
            exhausted = limit <= 0
            if remaining is not None:
                exhausted = exhausted or remaining <= 0
            elif usage is not None:
                exhausted = exhausted or usage >= limit
            if exhausted:
                raise RuntimeError(
                    "OpenRouter API key spending limit is exhausted; increase or "
                    "reset the limit before starting a new evaluation attempt"
                )

        credit_data = await quota_data("/credits", "account-credit")
        total_credits = _optional_number(credit_data.get("total_credits"))
        total_usage = _optional_number(credit_data.get("total_usage"))
        if (
            total_credits is not None
            and total_usage is not None
            and total_usage >= total_credits
        ):
            raise RuntimeError(
                "OpenRouter account credits are exhausted; add credits before "
                "starting a new evaluation attempt"
            )
    finally:
        if owns_client:
            await active_client.aclose()


async def _preflight_model_catalog(
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
    model_ids: list[str] | tuple[str, ...] = tuple(TOURNAMENT_MODELS),
) -> list[dict[str, Any]]:
    """Verify tournament IDs through the configured endpoint's model catalog."""

    endpoint = settings.model_base_url.rstrip("/") + "/models"
    owns_client = client is None
    active_client = client or httpx.AsyncClient(timeout=15)
    try:
        try:
            response = await active_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {settings.model_api_key}"},
            )
        except httpx.HTTPError as error:
            raise RuntimeError(
                f"Model-catalog preflight failed ({type(error).__name__})"
            ) from error
        if response.status_code != 200:
            raise RuntimeError(
                f"Model-catalog preflight returned HTTP {response.status_code}"
            )
        try:
            payload = response.json()
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "Model-catalog preflight returned an invalid response"
            ) from error
        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise RuntimeError("Model-catalog preflight returned an invalid response")
        by_id = {
            row.get("id"): row
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        missing = [model for model in model_ids if model not in by_id]
        if missing:
            raise RuntimeError(
                "The configured model endpoint does not list the exact tournament "
                "model IDs: " + ", ".join(missing)
            )
        verified = []
        for model in model_ids:
            row = by_id[model]
            advertised = row.get("supported_parameters")
            parameters = (
                sorted(value for value in advertised if isinstance(value, str))
                if isinstance(advertised, list)
                else None
            )
            if parameters is not None and not {
                "tools",
                "tool_choice",
            } <= set(parameters):
                raise RuntimeError(
                    f"The configured model endpoint reports no tool support for "
                    f"{model!r}"
                )
            alias = row.get("alias_target")
            canonical_slug = row.get("canonical_slug") or model
            verified.append(
                {
                    "id": model,
                    "name": row.get("name") or model,
                    "canonicalSlug": canonical_slug,
                    "aliasTarget": (
                        alias.get("slug") if isinstance(alias, dict) else None
                    ),
                    "supportedParameters": parameters,
                }
            )
        return verified
    finally:
        if owns_client:
            await active_client.aclose()


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
    random_seed: int,
    winner: str,
    assignments: list[dict[str, str]],
    game_document: dict[str, Any],
    records: list[Any],
    store: AgentStore,
    endpoint_provider: str,
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
    if len(assignment_by_house) != len(assignments):
        raise RuntimeError("Assignments contain duplicate houses")
    if set(assignment_by_house) != set(houses):
        raise RuntimeError(
            "Assignments do not match the houses in the saved game: "
            f"assigned={sorted(assignment_by_house)}, saved={sorted(houses)}"
        )
    if winner not in houses:
        raise RuntimeError(f"Winner house {winner!r} is absent from the saved game")
    metrics_by_user = {
        record.user_id: store.get_run_metrics(record.id) for record in records
    }
    standings = []
    for house_id, house in houses.items():
        assignment = assignment_by_house.get(house_id)
        if assignment is None:
            continue
        metrics = metrics_by_user[assignment["userId"]]
        standings.append(
            {
                **assignment,
                "victoryPoints": int(house.get("currentVictoryPoints") or 0),
                "landAreas": int(house.get("controlledLandAreaCount") or 0),
                "supply": int(house.get("supplyLevel") or 0),
                "powerTokens": int(house.get("powerTokens") or 0),
                "ironThronePosition": (
                    iron_throne.index(house_id) + 1 if house_id in iron_throne else None
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
        "randomSeed": _require_uint32(random_seed),
        "completedAt": _now(),
        "endpointProvider": endpoint_provider,
        "winner": winner,
        "round": game.get("turn"),
        "standings": standings,
    }


def _aggregate_run_metrics(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine per-agent run metrics without dropping failed attempt usage."""

    status_counts: Counter[str] = Counter()
    token_totals = {
        "input": 0,
        "output": 0,
        "total": 0,
        "cachedInput": 0,
        "cacheWrite": 0,
        "reasoning": 0,
        "maxInputInRun": 0,
    }
    run_count = 0
    model_calls: Counter[str] = Counter()
    model_call_scopes: Counter[str] = Counter()
    cost_coverage: Counter[str] = Counter()
    response_providers: Counter[str] = Counter()
    response_models: Counter[str] = Counter()
    cost_usd = upstream_inference_cost_usd = 0.0
    responses_without_provider = 0
    duration_total = duration_maximum = 0
    for item in metrics:
        item_run_count = int(item.get("runCount") or 0)
        run_count += item_run_count
        status_counts.update(item.get("statusCounts") or {})
        calls = item.get("modelCalls") or {}
        for key in ("started", "responses", "withoutResponse", "responsesWithoutStart"):
            model_calls[key] += int(calls.get(key) or 0)
        model_call_scopes.update(calls.get("startedByScope") or {})
        tokens = item.get("tokens") or {}
        for key in token_totals:
            value = int(tokens.get(key) or 0)
            if key == "maxInputInRun":
                token_totals[key] = max(token_totals[key], value)
            else:
                token_totals[key] += value
        cost_usd += float(item.get("costUsd") or 0)
        upstream_inference_cost_usd += float(
            item.get("upstreamInferenceCostUsd") or 0
        )
        cost_coverage.update(item.get("costCoverage") or {})
        attribution = item.get("responseAttribution") or {}
        response_providers.update(attribution.get("providers") or {})
        response_models.update(attribution.get("models") or {})
        responses_without_provider += int(
            attribution.get("responsesWithoutProvider") or 0
        )
        duration = item.get("durationMs") or {}
        duration_total += int(duration.get("total") or 0)
        duration_maximum = max(duration_maximum, int(duration.get("maximum") or 0))
    return {
        "runCount": run_count,
        "statusCounts": dict(sorted(status_counts.items())),
        "modelCalls": {
            **{key: model_calls[key] for key in (
                "started",
                "responses",
                "withoutResponse",
                "responsesWithoutStart",
            )},
            "startedByScope": dict(sorted(model_call_scopes.items())),
        },
        "tokens": token_totals,
        "costUsd": round(cost_usd, 9),
        "upstreamInferenceCostUsd": round(upstream_inference_cost_usd, 9),
        "costCoverage": dict(sorted(cost_coverage.items())),
        "responseAttribution": {
            "providers": dict(sorted(response_providers.items())),
            "models": dict(sorted(response_models.items())),
            "responsesWithoutProvider": responses_without_provider,
        },
        "durationMs": {
            "total": duration_total,
            "average": round(duration_total / run_count) if run_count else 0,
            "maximum": duration_maximum,
        },
    }


def _load_attempt_metrics(attempt_dir: Path) -> dict[str, Any]:
    metrics_path = attempt_dir / "metrics.json"
    database_path = attempt_dir / "harness.db"
    if database_path.is_file():
        database = Database(database_path)
        try:
            store = AgentStore(database)
            return _aggregate_run_metrics(
                [store.get_run_metrics(record.id) for record in store.list_agents()]
            )
        finally:
            database.close()
    if metrics_path.is_file():
        try:
            value = json.loads(metrics_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Saved attempt metrics cannot be loaded: {metrics_path}: {error}"
            ) from error
        if not isinstance(value, dict):
            raise RuntimeError(
                f"Saved attempt metrics must be a JSON object: {metrics_path}"
            )
        return value

    return _aggregate_run_metrics([])


def _load_manifest(
    path: Path,
    args: argparse.Namespace,
    output: Path,
) -> dict[str, Any]:
    if path.is_file():
        try:
            manifest = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Saved tournament manifest cannot be loaded: {error}")
        if not isinstance(manifest, dict):
            raise RuntimeError("Saved tournament manifest must be a JSON object")
        schema_version = manifest.get("schemaVersion")
        if schema_version != 5:
            raise RuntimeError(
                "Existing evaluation manifest uses unsupported schema version "
                f"{schema_version!r}; start a new evaluation directory"
            )
        if manifest.get("experiment") != "mixed-model-tournament":
            raise RuntimeError("Existing evaluation manifest is another experiment")
        if manifest.get("models") != TOURNAMENT_MODELS:
            raise RuntimeError("Existing evaluation manifest uses other model IDs")
        if manifest.get("gameCount") != TOURNAMENT_GAMES:
            raise RuntimeError("Existing evaluation manifest is not a 12-game run")
        if manifest.get("randomSeed") != args.random_seed:
            raise RuntimeError("Existing evaluation manifest uses another random seed")
        _validate_evaluation_schedule(
            manifest.get("games"), TOURNAMENT_GAMES, args.random_seed
        )
        for game in manifest["games"]:
            for attempt in game["attempts"]:
                if not isinstance(attempt.get("provenance"), dict) or not isinstance(
                    attempt.get("modelVerification"), dict
                ):
                    raise RuntimeError(
                        "Existing tournament attempt has no runtime provenance or "
                        "model verification"
                    )
        return manifest
    manifest = {
        "schemaVersion": 5,
        "experiment": "mixed-model-tournament",
        "createdAt": _now(),
        "outputDirectory": str(output),
        "harness": TOURNAMENT_HARNESS_ID,
        "models": TOURNAMENT_MODELS,
        "gameCount": TOURNAMENT_GAMES,
        "randomSeed": args.random_seed,
        "games": _evaluation_schedule(TOURNAMENT_GAMES, args.random_seed),
    }
    _write_json(path, manifest)
    return manifest


def _build_provenance(
    args: argparse.Namespace,
    settings: Settings,
    *,
    model_ids: list[str] | tuple[str, ...] = tuple(TOURNAMENT_MODELS),
) -> dict[str, Any]:
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
        "harness": {
            "id": TOURNAMENT_HARNESS_ID,
            "runtimeSha256": _runtime_fingerprint(),
            "systemPromptSha256": _sha256_text(_system_prompt()),
            "effectiveInstructionsSha256": _sha256_text(_effective_instructions()),
            "clientRetries": 0,
            "autoplayMaxConsecutiveFailures": (
                settings.autoplay_max_consecutive_failures
            ),
            "autoplayRetryBaseSeconds": settings.autoplay_retry_base_seconds,
            "autoplayMaxCapacityFailures": (
                settings.autoplay_max_capacity_failures
            ),
            "autoplayCapacityRetryBaseSeconds": (
                settings.autoplay_capacity_retry_base_seconds
            ),
            "reasoningEffort": "high",
            "toolChoice": "required",
            "actionSubmission": "submit-action-tool",
            "contextPolicy": CONTEXT_POLICY_NAME,
            "historyMode": "current-observation-only",
            "parallelToolCalls": False,
            "store": False,
            "resetToolChoice": False,
            "rulesOracleMaxOutputTokens": 900,
        },
        "rules": {
            "available": rules_path.is_file(),
            "sha256": _sha256_file(rules_path) if rules_path.is_file() else None,
        },
        "models": {
            "ids": list(model_ids),
            "provider": settings.model_provider,
            "baseUrl": _sanitized_base_url(settings.model_base_url),
            "baseUrlSha256": _sha256_text(settings.model_base_url),
            "providerRouting": (
                {"blockedProviders": settings.openrouter_blocked_providers}
                if settings.uses_openrouter
                else None
            ),
        },
        "evaluation": {
            "randomSeed": args.random_seed,
            "gameCount": TOURNAMENT_GAMES,
            "gamePort": args.game_port,
            "gamesPerInvocation": 1,
            "maxRounds": None,
            "pollSeconds": args.poll_seconds,
            "stallSeconds": args.stall_seconds,
            "matchTimeoutHours": args.match_timeout_hours,
        },
    }


def _validate_resumable_provenance(
    existing: dict[str, Any], current: dict[str, Any]
) -> None:
    """Require the same runtime for another segment of one saved attempt."""

    for key in ("harness", "rules", "models", "evaluation"):
        if existing.get(key) != current.get(key):
            raise RuntimeError(
                f"Saved attempt provenance has different {key}; start a new "
                "attempt instead of resuming it"
            )
    existing_repositories = existing.get("repositories") or {}
    current_repositories = current.get("repositories") or {}
    if existing_repositories.get("swordsAndRavens") != current_repositories.get(
        "swordsAndRavens"
    ):
        raise RuntimeError(
            "Saved attempt provenance has a different game server; start a new "
            "attempt instead of resuming it"
        )


def _runtime_fingerprint() -> str:
    """Hash runtime files without making documentation commits behavior changes."""

    paths = [PROJECT_ROOT / "pyproject.toml", PROJECT_ROOT / "uv.lock"]
    source_root = PROJECT_ROOT / "src" / "raven_harness"
    paths.extend(
        path
        for path in source_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = path.relative_to(PROJECT_ROOT)
        digest.update(str(relative).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _git_provenance(
    directory: Path,
    *,
    ignored_paths: tuple[str, ...] = (),
    ignore_dirty_submodules: bool = False,
) -> dict[str, Any]:
    commit = _run_git(directory, "rev-parse", "HEAD")
    submodule_option = ("--ignore-submodules=dirty",) if ignore_dirty_submodules else ()
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


def _system_prompt() -> str:
    return DEFAULT_PROMPT


def _effective_instructions() -> str:
    return build_instructions(_system_prompt(), map_reference=load_map_reference(6))


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


def derive_game_seed(base_seed: int, game_number: int) -> int:
    """Derive a stable uint32 seed for one scheduled game."""

    base_seed = _require_uint32(base_seed)
    if not 1 <= game_number <= 12:
        raise ValueError("game_number must be from 1 through 12")
    material = f"{RANDOM_SEED_NAMESPACE}:{base_seed}:{game_number}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "big")


def _require_uint32(value: Any) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 0xFFFFFFFF
    ):
        raise ValueError("random seed must be an integer from 0 through 4294967295")
    return value


def _parse_random_seed(value: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise argparse.ArgumentTypeError(
            "random seed must be a decimal integer from 0 through 4294967295"
        )
    try:
        return _require_uint32(int(value, 10))
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def _parse_port(value: str) -> int:
    try:
        port = int(value, 10)
    except ValueError:
        raise argparse.ArgumentTypeError("game port must be an integer") from None
    if not 1 <= port <= 65_535:
        raise argparse.ArgumentTypeError("game port must be from 1 through 65535")
    return port


def _evaluation_schedule(
    game_count: int, base_seed: int = DEFAULT_RANDOM_SEED
) -> list[dict[str, Any]]:
    base_seed = _require_uint32(base_seed)
    return [
        {
            "number": number,
            "randomSeed": derive_game_seed(base_seed, number),
            "rotation": house_rotation(number),
            "users": user_rotation(number),
            "attempts": [],
        }
        for number in range(1, game_count + 1)
    ]


def _validate_evaluation_schedule(
    value: Any, game_count: int, base_seed: int = DEFAULT_RANDOM_SEED
) -> None:
    expected = _evaluation_schedule(game_count, base_seed)
    if not isinstance(value, list) or len(value) != len(expected):
        raise RuntimeError("Existing evaluation manifest has a different schedule")
    for actual_game, expected_game in zip(value, expected, strict=True):
        if any(
            actual_game.get(key) != expected_game[key]
            for key in ("number", "randomSeed", "rotation", "users")
        ):
            raise RuntimeError(
                "Existing evaluation manifest has a different seed, house, or user "
                "schedule"
            )
    seeds = [game["randomSeed"] for game in expected]
    if len(seeds) != len(set(seeds)):
        raise RuntimeError("Evaluation schedule contains duplicate random seeds")


def _write_summary(output: Path, manifest: dict[str, Any]) -> None:
    results: list[dict[str, Any]] = []
    active_elapsed_seconds: dict[int, float] = {}
    attempts: list[dict[str, Any]] = []
    for game in manifest["games"]:
        game_number = int(game["number"])
        for attempt in game["attempts"]:
            attempt_dir = output / attempt["directory"]
            provenance = attempt.get("provenance") or {}
            model_provenance = provenance.get("models") or {}
            metrics = _load_attempt_metrics(attempt_dir)
            if (attempt_dir / "harness.db").is_file():
                _write_json(attempt_dir / "metrics.json", metrics)
            attempts.append(
                {
                    "gameNumber": game_number,
                    "attemptNumber": int(attempt["number"]),
                    "status": attempt.get("status"),
                    "activeElapsedSeconds": attempt.get("activeElapsedSeconds"),
                    "endpointProvider": model_provenance.get("provider"),
                    "error": attempt.get("error"),
                    **(
                        {
                            "resumeRejectedReason": attempt[
                                "resumeRejectedReason"
                            ]
                        }
                        if attempt.get("resumeRejectedReason")
                        else {}
                    ),
                    "metrics": metrics,
                }
            )
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
            active_elapsed_seconds[game_number] = float(
                completed.get("activeElapsedSeconds") or 0
            )
    _write_json(
        output / "summary.json",
        summarize_results(
            results,
            attempts=attempts,
            active_elapsed_seconds=active_elapsed_seconds,
        ),
    )


def summarize_results(
    results: list[dict[str, Any]],
    *,
    attempts: list[dict[str, Any]] | None = None,
    active_elapsed_seconds: dict[int, float] | None = None,
) -> dict[str, Any]:
    attempts = attempts or []
    active_elapsed_seconds = active_elapsed_seconds or {}
    ratings = {model: 1500.0 for model in TOURNAMENT_MODELS}
    model_house_counts = {
        model: {house: 0 for house in HOUSES} for model in TOURNAMENT_MODELS
    }
    models: dict[str, dict[str, Any]] = {
        model: {
            "model": model,
            "games": 0,
            "wins": 0,
            "placementTotal": 0,
            "victoryPointTotal": 0,
            "completedRuns": 0,
            "failedRuns": 0,
            "cancelledRuns": 0,
            "modelCallsStarted": 0,
            "modelResponses": 0,
            "modelCallsWithoutResponse": 0,
            "inputTokens": 0,
            "outputTokens": 0,
            "totalTokens": 0,
            "cachedInputTokens": 0,
            "costUsd": 0.0,
            "upstreamInferenceCostUsd": 0.0,
            "runDurationTotalMs": 0,
            "maximumRunDurationMs": 0,
            "responseProviderCounts": Counter(),
            "responsesWithoutProvider": 0,
        }
        for model in TOURNAMENT_MODELS
    }
    houses = {
        house: {"house": house, "games": 0, "wins": 0, "placementTotal": 0}
        for house in HOUSES
    }
    games: list[dict[str, Any]] = []
    endpoint_provider_counts: Counter[str] = Counter()

    for result in sorted(results, key=lambda item: item["gameNumber"]):
        game_number = int(result["gameNumber"])
        endpoint_provider = str(result["endpointProvider"])
        endpoint_provider_counts[endpoint_provider] += 1
        games.append(
            {
                "gameNumber": game_number,
                "randomSeed": int(result["randomSeed"]),
                "winner": result["winner"],
                "round": int(result["round"]),
                "activeElapsedSeconds": active_elapsed_seconds.get(game_number),
                "endpointProvider": endpoint_provider,
            }
        )
        standings = result["standings"]
        old_ratings = ratings.copy()
        deltas = {model: 0.0 for model in ratings}
        for standing in standings:
            model = standing["model"]
            house = standing["house"]
            metrics = standing["metrics"]
            values = models[model]
            model_house_counts[model][house] += 1
            values["games"] += 1
            values["wins"] += int(standing["house"] == result["winner"])
            values["placementTotal"] += standing["placement"]
            values["victoryPointTotal"] += standing["victoryPoints"]
            values["completedRuns"] += metrics["statusCounts"].get("completed", 0)
            values["failedRuns"] += metrics["statusCounts"].get("failed", 0)
            values["cancelledRuns"] += metrics["statusCounts"].get("cancelled", 0)
            model_calls = metrics.get("modelCalls") or {}
            values["modelCallsStarted"] += int(model_calls.get("started") or 0)
            values["modelResponses"] += int(model_calls.get("responses") or 0)
            values["modelCallsWithoutResponse"] += int(
                model_calls.get("withoutResponse") or 0
            )
            tokens = metrics.get("tokens") or {}
            values["inputTokens"] += int(tokens.get("input") or 0)
            values["outputTokens"] += int(tokens.get("output") or 0)
            values["totalTokens"] += int(tokens.get("total") or 0)
            values["cachedInputTokens"] += int(tokens.get("cachedInput") or 0)
            values["costUsd"] += metrics["costUsd"]
            values["upstreamInferenceCostUsd"] += float(
                metrics.get("upstreamInferenceCostUsd") or 0
            )
            duration = metrics.get("durationMs") or {}
            values["runDurationTotalMs"] += int(duration.get("total") or 0)
            values["maximumRunDurationMs"] = max(
                values["maximumRunDurationMs"],
                int(duration.get("maximum") or 0),
            )
            attribution = metrics.get("responseAttribution") or {}
            values["responseProviderCounts"].update(
                attribution.get("providers") or {}
            )
            values["responsesWithoutProvider"] += int(
                attribution.get("responsesWithoutProvider") or 0
            )
            house_values = houses[standing["house"]]
            house_values["games"] += 1
            house_values["wins"] += int(standing["house"] == result["winner"])
            house_values["placementTotal"] += standing["placement"]

        for index, first in enumerate(standings):
            for second in standings[index + 1 :]:
                first_model = first["model"]
                second_model = second["model"]
                expected = 1 / (
                    1
                    + 10
                    ** ((old_ratings[second_model] - old_ratings[first_model]) / 400)
                )
                actual = 1.0 if first["placement"] < second["placement"] else 0.5
                change = 24 * (actual - expected) / 5
                deltas[first_model] += change
                deltas[second_model] -= change
        for model, change in deltas.items():
            ratings[model] += change

    ranking = []
    for model, values in models.items():
        model_games = values.pop("games")
        run_attempts = (
            values["completedRuns"] + values["failedRuns"] + values["cancelledRuns"]
        )
        ranking.append(
            {
                "model": model,
                "games": model_games,
                "wins": values["wins"],
                "averagePlacement": (
                    round(values.pop("placementTotal") / model_games, 3)
                    if model_games
                    else None
                ),
                "averageVictoryPoints": (
                    round(values.pop("victoryPointTotal") / model_games, 3)
                    if model_games
                    else None
                ),
                "reliability": (
                    round(values["completedRuns"] / run_attempts, 4)
                    if run_attempts
                    else None
                ),
                "costUsd": round(values["costUsd"], 6),
                "upstreamInferenceCostUsd": round(
                    values["upstreamInferenceCostUsd"], 6
                ),
                "completedRuns": values["completedRuns"],
                "failedRuns": values["failedRuns"],
                "cancelledRuns": values["cancelledRuns"],
                "modelCallsStarted": values["modelCallsStarted"],
                "modelResponses": values["modelResponses"],
                "modelCallsWithoutResponse": values[
                    "modelCallsWithoutResponse"
                ],
                "averageRunDurationMs": (
                    round(values["runDurationTotalMs"] / run_attempts)
                    if run_attempts
                    else None
                ),
                "maximumRunDurationMs": values["maximumRunDurationMs"],
                "responseProviderCounts": dict(
                    sorted(values["responseProviderCounts"].items())
                ),
                "responsesWithoutProvider": values["responsesWithoutProvider"],
                "inputTokens": values["inputTokens"],
                "outputTokens": values["outputTokens"],
                "totalTokens": values["totalTokens"],
                "cachedInputTokens": values["cachedInputTokens"],
                "elo": round(ratings[model], 1),
            }
        )
    ranking.sort(key=lambda item: (-item["elo"], item["model"]))
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
    model_house_coverage = [
        {
            "model": model,
            "houses": model_house_counts[model],
            "minimumObservations": min(model_house_counts[model].values()),
        }
        for model in TOURNAMENT_MODELS
    ]
    required_observations = 2
    minimum_observations = min(
        count
        for house_counts in model_house_counts.values()
        for count in house_counts.values()
    )
    comparison_complete = (
        len(results) == TOURNAMENT_GAMES
        and minimum_observations >= required_observations
    )
    attempt_metrics = _aggregate_run_metrics(
        [attempt.get("metrics") or {} for attempt in attempts]
    )
    attempt_status_counts = Counter(str(attempt.get("status")) for attempt in attempts)
    attempt_endpoint_provider_counts = Counter(
        str(attempt["endpointProvider"])
        for attempt in attempts
        if attempt.get("endpointProvider")
    )
    durations = [
        float(value)
        for game in games
        if (value := game["activeElapsedSeconds"]) is not None
    ]
    return {
        "schemaVersion": 2,
        "harness": TOURNAMENT_HARNESS_ID,
        "scheduledGames": TOURNAMENT_GAMES,
        "completedGames": len(results),
        "comparisonComplete": comparison_complete,
        "rankingStatus": "complete" if comparison_complete else "provisional",
        "games": games,
        "attempts": attempts,
        "attemptStatusCounts": dict(sorted(attempt_status_counts.items())),
        "durationSeconds": {
            "minimum": round(min(durations), 3) if durations else None,
            "average": round(sum(durations) / len(durations), 3) if durations else None,
            "maximum": round(max(durations), 3) if durations else None,
        },
        "completedGameEndpointProviderCounts": dict(
            sorted(endpoint_provider_counts.items())
        ),
        "attemptEndpointProviderCounts": dict(
            sorted(attempt_endpoint_provider_counts.items())
        ),
        "runStatusCounts": attempt_metrics["statusCounts"],
        "modelCalls": attempt_metrics["modelCalls"],
        "tokens": attempt_metrics["tokens"],
        "costUsd": round(attempt_metrics["costUsd"], 6),
        "upstreamInferenceCostUsd": round(
            attempt_metrics["upstreamInferenceCostUsd"], 6
        ),
        "costCoverage": attempt_metrics["costCoverage"],
        "responseAttribution": attempt_metrics["responseAttribution"],
        "requiredObservationsPerModelHouse": required_observations,
        "minimumObservationsPerModelHouse": minimum_observations,
        "modelHouseCoverage": model_house_coverage,
        "ranking": ranking,
        "houseEffects": house_effects,
        "eloMethod": (
            "Initial rating 1500; K=24; each six-player result is five pairwise "
            "comparisons per model with K divided by five. Ratings update "
            "simultaneously after each game."
        ),
    }


def _resolve_output(value: str | None) -> Path:
    return resolve_evaluation_output(value, default_prefix="")


def resolve_evaluation_output(value: str | None, *, default_prefix: str) -> Path:
    root = EVALUATION_ROOT.resolve()
    if value:
        path = Path(value).expanduser()
        resolved = (
            path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
        )
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        resolved = root / f"{default_prefix}{stamp}"
    try:
        resolved.relative_to(root)
    except ValueError:
        raise RuntimeError(f"Evaluation output must be inside {root}") from None
    return resolved


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")
    temporary.replace(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run or resume one complete sequential game of the fixed 12-game "
            "six-model Raven Harness tournament."
        )
    )
    parser.add_argument("--output", help="Artifact directory under data/evaluations.")
    parser.add_argument(
        "--random-seed",
        type=_parse_random_seed,
        default=DEFAULT_RANDOM_SEED,
        help="Base uint32 seed used to derive one stable seed per game (default: 1).",
    )
    parser.add_argument("--game-port", type=_parse_port, default=5101)
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--stall-seconds", type=float, default=360.0)
    parser.add_argument("--match-timeout-hours", type=float, default=6.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        output = asyncio.run(run_evaluation(args))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    print(f"Evaluation artifacts: {output}")


if __name__ == "__main__":
    main()
