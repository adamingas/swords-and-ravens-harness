from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from time import monotonic
from typing import Any

from .config import Settings
from .errors import safe_error_text
from .evaluation import (
    HOUSES,
    TOURNAMENT_HARNESS_ID,
    _aggregate_run_metrics,
    _build_provenance,
    _load_attempt_metrics,
    _now,
    _preflight_model_catalog,
    _preflight_openrouter_quota,
    _resumable_attempt,
    _validate_resumable_provenance,
    _write_json,
    derive_game_seed,
    resolve_evaluation_output,
    run_game,
)


HOUSE_TEST_MODEL = "openai/gpt-oss-120b"
HOUSE_TEST_PROVIDER = "cerebras"
HOUSE_TEST_GAMES = 5
HOUSE_TEST_RANDOM_SEED = 102
HOUSE_TEST_INVESTIGATE_AFTER_SECONDS = 120
HOUSE_TEST_MAX_OUTPUT_TOKENS = 4_096


async def run_house_evaluation(args: argparse.Namespace) -> Path:
    """Run complete games with one model in all six seats."""

    settings = Settings(
        openrouter_provider_order=HOUSE_TEST_PROVIDER,
        openrouter_allow_unlisted_providers=False,
        openrouter_allow_fallbacks=False,
        openrouter_require_parameters=False,
        model_max_output_tokens=HOUSE_TEST_MAX_OUTPUT_TOKENS,
    )
    if settings.model_provider != "OpenRouter":
        raise RuntimeError(
            "The GPT-OSS house experiment requires an endpoint adapter that can "
            "restrict requests to the Cerebras backend"
        )
    if not settings.model_api_key:
        raise RuntimeError(
            "Configure an API key for the selected model endpoint before starting "
            "the GPT-OSS house experiment"
        )
    if not settings.resolved_rules_path.is_file():
        raise RuntimeError(
            "Rules oracle data is required; run uv run raven-prepare-rules"
        )
    await _preflight_openrouter_quota(settings)
    verified_models = await _preflight_model_catalog(
        settings, model_ids=[HOUSE_TEST_MODEL]
    )

    output = resolve_evaluation_output(
        args.output, default_prefix="gpt-oss-120b-house-test-"
    )
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    provenance = _build_provenance(
        args, settings, model_ids=[HOUSE_TEST_MODEL]
    )
    manifest = _load_or_create_manifest(
        manifest_path,
        provenance=provenance,
        verified_models=verified_models,
        args=args,
    )
    manifest.pop("finishedAt", None)

    last_port = args.game_port + HOUSE_TEST_GAMES - 1
    if last_port > 65_535:
        raise RuntimeError(
            f"Game-server port range ends at {last_port}; choose a lower --game-port"
        )

    async def run_scheduled_game(game_number: int) -> dict[str, Any] | None:
        game_entry = manifest["games"][game_number - 1]
        completed = next(
            (
                attempt
                for attempt in game_entry["attempts"]
                if attempt.get("status") == "completed"
            ),
            None,
        )
        if completed is not None:
            print(f"Game {game_number}: already completed")
            return None

        resumable = _resumable_attempt(output, game_entry)
        if resumable is None:
            attempt_number = len(game_entry["attempts"]) + 1
            attempt_dir = (
                output
                / f"game-{game_number:02d}"
                / f"attempt-{attempt_number:02d}"
            )
            attempt_dir.mkdir(parents=True, exist_ok=False)
            attempt = {
                "number": attempt_number,
                "status": "running",
                "directory": str(attempt_dir.relative_to(output)),
                "startedAt": _now(),
                "resumeCount": 0,
                "activeElapsedSeconds": 0.0,
                "provenance": provenance,
            }
            game_entry["attempts"].append(attempt)
            resume = False
            verb = "starting"
        else:
            attempt, attempt_dir = resumable
            attempt_provenance = attempt.get("provenance")
            if not isinstance(attempt_provenance, dict):
                raise RuntimeError(
                    "Saved house-test attempt has no runtime provenance"
                )
            _validate_resumable_provenance(attempt_provenance, provenance)
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
        game_port = args.game_port + game_number - 1
        print(
            f"Game {game_number}: {verb} attempt {attempt_number} "
            f"on port {game_port}"
        )
        segment_started = monotonic()
        try:
            result = await run_game(
                game_number=game_number,
                attempt_dir=attempt_dir,
                random_seed=int(game_entry["randomSeed"]),
                game_port=game_port,
                max_rounds=None,
                poll_seconds=args.poll_seconds,
                stall_seconds=args.stall_seconds,
                match_timeout_seconds=args.match_timeout_hours * 3_600,
                settings=settings,
                resume=resume,
                seat_models=[HOUSE_TEST_MODEL] * len(HOUSES),
                seat_houses=HOUSES,
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
            if not args.continue_on_error:
                raise RuntimeError(error_text) from None
        finally:
            elapsed = float(attempt.get("activeElapsedSeconds") or 0)
            attempt["activeElapsedSeconds"] = round(
                elapsed + monotonic() - segment_started, 3
            )
            _write_json(manifest_path, manifest)
            _write_house_summary(output, manifest)
        return attempt

    for game_number in range(1, HOUSE_TEST_GAMES + 1):
        attempt = await run_scheduled_game(game_number)
        _require_expected_game_duration(game_number, attempt)

    manifest["finishedAt"] = _now()
    _write_json(manifest_path, manifest)
    _write_house_summary(output, manifest)
    return output


def _require_expected_game_duration(
    game_number: int, attempt: dict[str, Any] | None
) -> None:
    if (
        game_number == HOUSE_TEST_GAMES
        or attempt is None
        or attempt.get("status") != "completed"
    ):
        return
    elapsed = float(attempt["activeElapsedSeconds"])
    if elapsed <= HOUSE_TEST_INVESTIGATE_AFTER_SECONDS:
        return
    raise RuntimeError(
        f"Game {game_number} took {elapsed:.3f} seconds; stopped before starting "
        "another game because the expected maximum is "
        f"{HOUSE_TEST_INVESTIGATE_AFTER_SECONDS} seconds"
    )


def summarize_house_results(
    results: list[dict[str, Any]],
    *,
    active_elapsed_seconds: dict[int, float],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    houses = {
        house: {
            "house": house,
            "games": 0,
            "wins": 0,
            "placementTotal": 0,
            "victoryPointTotal": 0,
            "landAreaTotal": 0,
        }
        for house in HOUSES
    }
    games: list[dict[str, Any]] = []

    for result in sorted(results, key=lambda item: int(item["gameNumber"])):
        game_number = int(result["gameNumber"])
        games.append(
            {
                "gameNumber": game_number,
                "randomSeed": int(result["randomSeed"]),
                "winner": result["winner"],
                "round": int(result["round"]),
                "activeElapsedSeconds": active_elapsed_seconds.get(game_number),
            }
        )
        for standing in result["standings"]:
            house = houses[str(standing["house"])]
            house["games"] += 1
            house["wins"] += int(standing["house"] == result["winner"])
            house["placementTotal"] += int(standing["placement"])
            house["victoryPointTotal"] += int(standing["victoryPoints"])
            house["landAreaTotal"] += int(standing["landAreas"])

    house_statistics = []
    for values in houses.values():
        game_count = int(values["games"])
        house_statistics.append(
            {
                "house": values["house"],
                "games": game_count,
                "wins": values["wins"],
                "winRate": round(values["wins"] / game_count, 4)
                if game_count
                else None,
                "averagePlacement": round(
                    values["placementTotal"] / game_count, 3
                )
                if game_count
                else None,
                "averageVictoryPoints": round(
                    values["victoryPointTotal"] / game_count, 3
                )
                if game_count
                else None,
                "averageLandAreas": round(
                    values["landAreaTotal"] / game_count, 3
                )
                if game_count
                else None,
            }
        )

    completed_games = len(results)
    durations = [
        value
        for game in games
        if (value := game["activeElapsedSeconds"]) is not None
    ]
    metrics = _aggregate_run_metrics(
        [attempt.get("metrics") or {} for attempt in attempts]
    )
    return {
        "schemaVersion": 1,
        "model": HOUSE_TEST_MODEL,
        "harness": TOURNAMENT_HARNESS_ID,
        "scheduledGames": HOUSE_TEST_GAMES,
        "completedGames": completed_games,
        "complete": completed_games == HOUSE_TEST_GAMES,
        "games": games,
        "attempts": attempts,
        "durationSeconds": {
            "minimum": round(min(durations), 3) if durations else None,
            "average": round(sum(durations) / len(durations), 3)
            if durations
            else None,
            "maximum": round(max(durations), 3) if durations else None,
            "allUnderOneMinute": bool(durations)
            and len(durations) == HOUSE_TEST_GAMES
            and all(value < 60 for value in durations),
        },
        "houseStatistics": house_statistics,
        "runStatusCounts": metrics["statusCounts"],
        "modelRequests": metrics["modelRequests"],
        "tokens": metrics["tokens"],
        "costUsd": round(metrics["costUsd"], 6),
    }


def _load_or_create_manifest(
    path: Path,
    *,
    provenance: dict[str, Any],
    verified_models: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    if path.is_file():
        try:
            manifest = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Saved house-test manifest cannot be loaded: {error}")
        if not isinstance(manifest, dict):
            raise RuntimeError("Saved house-test manifest must be a JSON object")
        if (
            manifest.get("schemaVersion") != 2
            or manifest.get("experiment") != "same-model-house-test"
            or manifest.get("model") != HOUSE_TEST_MODEL
            or manifest.get("gameCount") != HOUSE_TEST_GAMES
            or manifest.get("randomSeed") != HOUSE_TEST_RANDOM_SEED
            or manifest.get("maxRounds") is not None
        ):
            raise RuntimeError(
                "Existing output contains a different house-test configuration"
            )
        if not isinstance(manifest.get("provenance"), dict):
            raise RuntimeError("Existing house-test manifest has no provenance")
        for game in manifest.get("games", []):
            for attempt in game.get("attempts", []):
                if not isinstance(attempt.get("provenance"), dict):
                    raise RuntimeError(
                        "Existing house-test attempt has no runtime provenance"
                    )
        return manifest

    manifest = {
        "schemaVersion": 2,
        "experiment": "same-model-house-test",
        "harness": TOURNAMENT_HARNESS_ID,
        "model": HOUSE_TEST_MODEL,
        "requestedProvider": HOUSE_TEST_PROVIDER,
        "providerFallbacks": False,
        "gameCount": HOUSE_TEST_GAMES,
        "randomSeed": HOUSE_TEST_RANDOM_SEED,
        "maxRounds": None,
        "modelVerification": {
            "source": "configured model endpoint catalog",
            "verifiedAt": _now(),
            "models": verified_models,
        },
        "provenance": provenance,
        "games": [
            {
                "number": game_number,
                "randomSeed": derive_game_seed(
                    HOUSE_TEST_RANDOM_SEED, game_number
                ),
                "attempts": [],
            }
            for game_number in range(1, HOUSE_TEST_GAMES + 1)
        ],
    }
    _write_json(path, manifest)
    return manifest


def _write_house_summary(output: Path, manifest: dict[str, Any]) -> None:
    results: list[dict[str, Any]] = []
    elapsed: dict[int, float] = {}
    attempts: list[dict[str, Any]] = []
    for game in manifest["games"]:
        for attempt in game["attempts"]:
            attempt_dir = output / attempt["directory"]
            attempts.append(
                {
                    "gameNumber": int(game["number"]),
                    "attemptNumber": int(attempt["number"]),
                    "status": attempt.get("status"),
                    "activeElapsedSeconds": attempt.get("activeElapsedSeconds"),
                    "error": attempt.get("error"),
                    "metrics": _load_attempt_metrics(attempt_dir),
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
        if not result_path.is_file():
            continue
        results.append(json.loads(result_path.read_text()))
        elapsed[int(game["number"])] = float(
            completed.get("activeElapsedSeconds") or 0
        )
    _write_json(
        output / "summary.json",
        summarize_house_results(
            results,
            active_elapsed_seconds=elapsed,
            attempts=attempts,
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run five complete six-player games with GPT-OSS-120B in every seat."
        )
    )
    parser.add_argument(
        "--output", help="Artifact directory under data/evaluations."
    )
    parser.add_argument("--game-port", type=int, default=5121)
    parser.add_argument("--poll-seconds", type=float, default=0.25)
    parser.add_argument("--stall-seconds", type=float, default=360.0)
    parser.add_argument("--match-timeout-hours", type=float, default=6.0)
    parser.add_argument("--continue-on-error", action="store_true")
    parser.set_defaults(random_seed=HOUSE_TEST_RANDOM_SEED)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        output = asyncio.run(run_house_evaluation(args))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    print(f"House-test artifacts: {output}")


if __name__ == "__main__":
    main()
