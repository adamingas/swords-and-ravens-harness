from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .evaluation import (
    HOUSES,
    TOURNAMENT_HARNESS_ID,
    TOURNAMENT_MODELS,
    _effective_instructions,
    _provider_attribution_summary,
    _sha256_text,
    _system_prompt,
    _terminal_winner,
    _validate_evaluation_schedule,
    summarize_results,
)


class EvaluationVerificationError(RuntimeError):
    """An evaluation artifact is missing, corrupt, or internally inconsistent."""


class EvaluationIncompleteError(EvaluationVerificationError):
    """A valid provisional evaluation was checked with --require-complete."""


def verify_evaluation(
    output: Path | str, *, require_complete: bool = False
) -> dict[str, Any]:
    """Validate saved evaluation artifacts without contacting a model provider."""

    root = Path(output).expanduser().resolve()
    if not root.is_dir():
        raise EvaluationVerificationError(
            f"Evaluation directory does not exist: {root}"
        )

    manifest = _read_json_object(root / "manifest.json", "manifest")
    (
        models,
        game_count,
        games,
        prompt_hash,
        aliases,
        canonical_slugs,
    ) = _validate_manifest(manifest)
    completed_results: list[dict[str, Any]] = []
    assignment_models: set[str] = set()
    status_counts: Counter[str] = Counter()
    checked_databases = 0
    provider_counts: Counter[str] = Counter()
    resolved_models: set[str] = set()

    for game in games:
        game_number = int(game["number"])
        attempts = game.get("attempts")
        if not isinstance(attempts, list):
            raise EvaluationVerificationError(
                f"Game {game_number} attempts must be a list"
            )
        attempt_numbers: list[int] = []
        completed_attempts: list[dict[str, Any]] = []
        for attempt in attempts:
            if not isinstance(attempt, dict):
                raise EvaluationVerificationError(
                    f"Game {game_number} contains a non-object attempt"
                )
            attempt_number = attempt.get("number")
            status = attempt.get("status")
            if not _is_int(attempt_number) or attempt_number < 1:
                raise EvaluationVerificationError(
                    f"Game {game_number} has an invalid attempt number"
                )
            if not isinstance(status, str) or status not in {
                "running",
                "failed",
                "cancelled",
                "completed",
            }:
                raise EvaluationVerificationError(
                    f"Game {game_number} attempt {attempt_number} has invalid status "
                    f"{status!r}"
                )
            attempt_numbers.append(attempt_number)
            status_counts[status] += 1
            _resolve_attempt_directory(
                root, attempt, game_number=game_number, require_exists=True
            )
            if status == "completed":
                completed_attempts.append(attempt)
        if sorted(attempt_numbers) != list(range(1, len(attempts) + 1)):
            raise EvaluationVerificationError(
                f"Game {game_number} attempt numbers are not consecutive"
            )
        if len(completed_attempts) > 1:
            raise EvaluationVerificationError(
                f"Game {game_number} has more than one completed attempt"
            )
        if not completed_attempts:
            continue

        attempt = completed_attempts[0]
        attempt_dir = _resolve_attempt_directory(
            root, attempt, game_number=game_number, require_exists=True
        )
        result = _read_json_object(
            attempt_dir / "result.json",
            f"game {game_number} completed result",
        )
        assignments = _read_json_list(
            attempt_dir / "assignments.json",
            f"game {game_number} assignments",
        )
        saved_game = _read_json_object(
            attempt_dir / "game.json",
            f"game {game_number} saved game",
        )
        assignment_models.update(
            _validate_completed_game(
                game=game,
                attempt=attempt,
                result=result,
                assignments=assignments,
                saved_game=saved_game,
                manifest_models=models,
                prompt_hash=prompt_hash,
            )
        )
        database_path = attempt_dir / "harness.db"
        _sqlite_quick_check(
            database_path, label=f"game {game_number} harness database"
        )
        database_responses = _database_response_rows(
            database_path,
            game_number=game_number,
            manifest_models=models,
        )
        provider_summary, game_resolved_models = _validate_provider_attribution(
            artifact=_read_json_object(
                attempt_dir / "provider-generations.json",
                f"game {game_number} provider attribution",
            ),
            result=result,
            game_number=game_number,
            manifest_models=models,
            aliases=aliases,
            canonical_slugs=canonical_slugs,
            database_responses=database_responses,
        )
        provider_counts.update(
            {
                "requested": provider_summary["requestedCount"],
                "attributed": provider_summary["attributedCount"],
                "modelAttributed": provider_summary["modelAttributedCount"],
                "costAttributed": provider_summary["costAttributedCount"],
                "unavailable": provider_summary["unavailableCount"],
            }
        )
        resolved_models.update(game_resolved_models)
        checked_databases += 1
        completed_results.append(result)

    if assignment_models and assignment_models != set(models):
        raise EvaluationVerificationError(
            "Completed assignments do not contain all manifest models: "
            f"{sorted(assignment_models)!r}"
        )

    stored_summary = _read_json_object(root / "summary.json", "summary")
    try:
        expected_summary = summarize_results(completed_results)
    except (KeyError, TypeError, ValueError) as error:
        raise EvaluationVerificationError(
            "Completed results cannot be summarized: "
            f"{type(error).__name__}: {error}"
        ) from None
    if stored_summary != expected_summary:
        raise EvaluationVerificationError(
            "summary.json does not equal the summary recomputed from completed results"
        )

    comparison_complete = bool(expected_summary.get("comparisonComplete"))
    report = {
        "schemaVersion": 1,
        "status": "valid",
        "evaluationStatus": "complete" if comparison_complete else "provisional",
        "directory": str(root),
        "models": models,
        "scheduledGames": game_count,
        "completedGames": len(completed_results),
        "attemptStatusCounts": {
            status: status_counts[status]
            for status in ("completed", "failed", "cancelled", "running")
        },
        "checkedDatabases": checked_databases,
        "providerAttribution": {
            "requestedCount": provider_counts["requested"],
            "attributedCount": provider_counts["attributed"],
            "modelAttributedCount": provider_counts["modelAttributed"],
            "costAttributedCount": provider_counts["costAttributed"],
            "unavailableCount": provider_counts["unavailable"],
            "resolvedModels": sorted(resolved_models),
        },
        "summaryMatches": True,
        "requiredObservationsPerModelHouse": expected_summary[
            "requiredObservationsPerModelHouse"
        ],
        "minimumObservationsPerModelHouse": expected_summary[
            "minimumObservationsPerModelHouse"
        ],
        "comparisonComplete": comparison_complete,
        "providerAttributionComplete": expected_summary[
            "providerAttributionComplete"
        ],
    }
    if require_complete and not comparison_complete:
        raise EvaluationIncompleteError(
            "Evaluation is valid but provisional: "
            f"{len(completed_results)}/12 completed games and minimum model-house "
            "appearances "
            f"{expected_summary['minimumObservationsPerModelHouse']}/"
            f"{expected_summary['requiredObservationsPerModelHouse']}; complete "
            "provider/model/cost attribution: "
            f"{expected_summary['providerAttributionComplete']}"
        )
    return report


def _validate_provider_attribution(
    *,
    artifact: dict[str, Any],
    result: dict[str, Any],
    game_number: int,
    manifest_models: list[str],
    aliases: dict[str, str | None],
    canonical_slugs: dict[str, str],
    database_responses: dict[tuple[str, str], str],
) -> tuple[dict[str, Any], set[str]]:
    generations = artifact.get("generations")
    if not isinstance(generations, list) or not all(
        isinstance(item, dict) for item in generations
    ):
        raise EvaluationVerificationError(
            f"Game {game_number} provider generations must be a list of objects"
        )
    expected_summary = _provider_attribution_summary({"generations": generations})
    for key, expected in expected_summary.items():
        if artifact.get(key) != expected:
            raise EvaluationVerificationError(
                f"Game {game_number} provider attribution has an invalid {key}"
            )
    if result.get("providerAttribution") != expected_summary:
        raise EvaluationVerificationError(
            f"Game {game_number} result provider attribution does not match its "
            "provider artifact"
        )

    expected_models = set(manifest_models)
    identities: set[tuple[str, str]] = set()
    resolved_models: set[str] = set()
    requested_models: set[str] = set()
    for generation in generations:
        run_id = generation.get("runId")
        response_id = generation.get("responseId")
        requested_model = generation.get("requestedModel")
        if not isinstance(run_id, str) or not run_id:
            raise EvaluationVerificationError(
                f"Game {game_number} provider generation has no run ID"
            )
        if not isinstance(response_id, str) or not response_id:
            raise EvaluationVerificationError(
                f"Game {game_number} provider generation has no response ID"
            )
        identity = (run_id, response_id)
        if identity in identities:
            raise EvaluationVerificationError(
                f"Game {game_number} provider generation is duplicated"
            )
        identities.add(identity)
        if requested_model not in expected_models:
            raise EvaluationVerificationError(
                f"Game {game_number} provider generation has an unknown requested model"
            )
        requested_models.add(str(requested_model))
        if identity not in database_responses:
            raise EvaluationVerificationError(
                f"Game {game_number} provider generation is absent from harness.db"
            )
        if requested_model != database_responses[identity]:
            raise EvaluationVerificationError(
                f"Game {game_number} provider generation has the wrong requested model"
            )
        resolved_model = generation.get("model")
        if resolved_model is None:
            continue
        if not isinstance(resolved_model, str) or not _resolved_model_matches(
            str(requested_model),
            resolved_model,
            alias=aliases.get(str(requested_model)),
            canonical_slug=canonical_slugs.get(str(requested_model)),
        ):
            raise EvaluationVerificationError(
                f"Game {game_number} provider resolved unexpected model "
                f"{resolved_model!r}"
            )
        resolved_models.add(resolved_model)
    if not artifact.get("collectionError") and identities != set(database_responses):
        raise EvaluationVerificationError(
            f"Game {game_number} provider attribution does not cover every response "
            "in harness.db"
        )
    if (
        expected_summary["requestedCount"] > 0
        and expected_summary["unavailableCount"] == 0
        and requested_models != expected_models
    ):
        raise EvaluationVerificationError(
            f"Game {game_number} complete provider attribution does not include "
            "every tournament model"
        )
    return expected_summary, resolved_models


def _resolved_model_matches(
    requested: str,
    resolved: str,
    *,
    alias: str | None = None,
    canonical_slug: str | None = None,
) -> bool:
    """Accept IDs derived from the catalog row for the exact requested model."""

    candidates = [
        requested,
        *([canonical_slug] if canonical_slug else []),
        *([alias] if alias else []),
    ]
    if any(
        resolved == candidate
        or bool(re.fullmatch(re.escape(candidate) + r"-\d{8}", resolved))
        for candidate in candidates
    ):
        return True
    if alias is None or not requested.startswith("~"):
        return False
    family = re.sub(r"-\d{4,8}$", "", alias)
    return resolved == family or bool(
        re.fullmatch(re.escape(family) + r"-\d{4,8}", resolved)
    )


def _validate_manifest(
    manifest: dict[str, Any],
) -> tuple[
    list[str],
    int,
    list[dict[str, Any]],
    str,
    dict[str, str | None],
    dict[str, str],
]:
    schema_version = manifest.get("schemaVersion")
    if schema_version != 4:
        raise EvaluationVerificationError(
            f"Unsupported evaluation manifest schemaVersion: {schema_version!r}"
        )
    models = manifest.get("models")
    if models != TOURNAMENT_MODELS:
        raise EvaluationVerificationError(
            "Manifest models do not match the canonical tournament model IDs"
        )
    if manifest.get("harness") != TOURNAMENT_HARNESS_ID:
        raise EvaluationVerificationError(
            "Manifest harness is not the canonical strategic-v1 harness"
        )
    game_count = manifest.get("gameCount")
    if not _is_int(game_count) or not 1 <= game_count <= 12:
        raise EvaluationVerificationError(
            "Manifest gameCount must be an integer from 1 through 12"
        )
    random_seed = manifest.get("randomSeed")
    if not _is_int(random_seed) or not 0 <= random_seed <= 0xFFFFFFFF:
        raise EvaluationVerificationError(
            "Manifest randomSeed must be an integer from 0 through 4294967295"
        )
    verification = manifest.get("modelVerification")
    if not isinstance(verification, dict) or verification.get("source") != (
        "OpenRouter GET /models"
    ):
        raise EvaluationVerificationError(
            "Manifest has no OpenRouter model verification"
        )
    verified_rows = verification.get("models")
    if not isinstance(verified_rows, list) or not all(
        isinstance(row, dict) for row in verified_rows
    ):
        raise EvaluationVerificationError(
            "Manifest model verification must contain model objects"
        )
    verified_ids = [row.get("id") for row in verified_rows]
    if verified_ids != models:
        raise EvaluationVerificationError(
            "Manifest model verification does not match the tournament models"
        )
    aliases: dict[str, str | None] = {}
    canonical_slugs: dict[str, str] = {}
    for row in verified_rows:
        parameters = row.get("supportedParameters")
        if not isinstance(parameters, list) or not {
            "tools",
            "tool_choice",
        } <= set(parameters):
            raise EvaluationVerificationError(
                f"Verified model {row.get('id')!r} lacks required tool parameters"
            )
        alias = row.get("aliasTarget")
        if alias is not None and not isinstance(alias, str):
            raise EvaluationVerificationError(
                f"Verified model {row.get('id')!r} has an invalid alias target"
            )
        aliases[str(row["id"])] = alias
        canonical_slug = row.get("canonicalSlug")
        if not isinstance(canonical_slug, str) or not canonical_slug:
            raise EvaluationVerificationError(
                f"Verified model {row.get('id')!r} has no canonical slug"
            )
        canonical_slugs[str(row["id"])] = canonical_slug

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict) or any(
        not isinstance(provenance.get(key), dict)
        for key in ("repositories", "rules", "harness", "models", "evaluation")
    ):
        raise EvaluationVerificationError(
            "Schema-4 manifest provenance is missing a required object"
        )
    if provenance["harness"].get("id") != TOURNAMENT_HARNESS_ID:
        raise EvaluationVerificationError(
            "Manifest harness does not match provenance.harness.id"
        )
    if provenance["models"].get("ids") != models:
        raise EvaluationVerificationError(
            "Manifest models do not match provenance.models.ids"
        )
    if provenance["evaluation"].get("randomSeed") != random_seed:
        raise EvaluationVerificationError(
            "Manifest randomSeed does not match provenance.evaluation.randomSeed"
        )
    configured_hash = provenance["harness"].get("systemPromptSha256")
    effective_hash = provenance["harness"].get("effectiveInstructionsSha256")
    if not _is_sha256(configured_hash) or not _is_sha256(effective_hash):
        raise EvaluationVerificationError(
            "Manifest harness prompt hashes are invalid"
        )
    if configured_hash != _sha256_text(_system_prompt()) or (
        effective_hash != _sha256_text(_effective_instructions())
    ):
        raise EvaluationVerificationError(
            "Manifest prompt hashes do not match the canonical strategic-v1 prompt"
        )
    games = manifest.get("games")
    try:
        _validate_evaluation_schedule(games, game_count, random_seed)
    except (AttributeError, RuntimeError, TypeError, ValueError) as error:
        raise EvaluationVerificationError(str(error)) from None
    assert isinstance(games, list)
    return models, game_count, games, effective_hash, aliases, canonical_slugs


def _validate_completed_game(
    *,
    game: dict[str, Any],
    attempt: dict[str, Any],
    result: dict[str, Any],
    assignments: list[Any],
    saved_game: dict[str, Any],
    manifest_models: list[str],
    prompt_hash: str,
) -> set[str]:
    game_number = int(game["number"])
    expected_model_set = set(manifest_models)
    if len(assignments) != 6 or not all(
        isinstance(item, dict) for item in assignments
    ):
        raise EvaluationVerificationError(
            f"Game {game_number} assignments must contain six objects"
        )
    assignment_models = [item.get("model") for item in assignments]
    if not all(isinstance(value, str) for value in assignment_models):
        raise EvaluationVerificationError(
            f"Game {game_number} assignment models must be strings"
        )
    assignment_by_model = {item["model"]: item for item in assignments}
    if (
        set(assignment_by_model) != expected_model_set
        or len(assignment_by_model) != len(assignments)
    ):
        raise EvaluationVerificationError(
            f"Game {game_number} assignments must contain each tournament model once"
        )
    houses = [item.get("house") for item in assignments]
    if not all(isinstance(value, str) for value in houses):
        raise EvaluationVerificationError(
            f"Game {game_number} assignment houses must be strings"
        )
    if len(set(houses)) != 6 or set(houses) != set(HOUSES):
        raise EvaluationVerificationError(
            f"Game {game_number} assignments must contain each base-game house once"
        )
    for model, assignment in assignment_by_model.items():
        if assignment.get("house") != game["rotation"].get(model):
            raise EvaluationVerificationError(
                f"Game {game_number} assignment house does not match its schedule"
            )
        if str(assignment.get("userId")) != str(game["users"].get(model)):
            raise EvaluationVerificationError(
                f"Game {game_number} assignment user does not match its schedule"
            )
        if assignment.get("harness") != TOURNAMENT_HARNESS_ID:
            raise EvaluationVerificationError(
                f"Game {game_number} assignment does not use strategic-v1"
            )
        if assignment.get("promptSha256") != prompt_hash:
            raise EvaluationVerificationError(
                f"Game {game_number} assignment prompt hash does not match the "
                f"manifest harness for {model!r}"
            )

    if not _is_int(result.get("gameNumber")) or result.get("gameNumber") != game_number:
        raise EvaluationVerificationError(
            f"Game {game_number} result has another game number"
        )
    if result.get("randomSeed") != game.get("randomSeed"):
        raise EvaluationVerificationError(
            f"Game {game_number} result random seed does not match its schedule"
        )
    winner = result.get("winner")
    if winner not in HOUSES:
        raise EvaluationVerificationError(
            f"Game {game_number} result has invalid winner {winner!r}"
        )
    if attempt.get("winner") is not None and attempt.get("winner") != winner:
        raise EvaluationVerificationError(
            f"Game {game_number} manifest and result winners disagree"
        )
    saved_winner = _terminal_winner(saved_game)
    if saved_winner != winner:
        raise EvaluationVerificationError(
            f"Game {game_number} saved terminal winner {saved_winner!r} does not "
            f"match result winner {winner!r}"
        )

    standings = result.get("standings")
    if not isinstance(standings, list) or len(standings) != 6 or not all(
        isinstance(item, dict) for item in standings
    ):
        raise EvaluationVerificationError(
            f"Game {game_number} result must contain six standings"
        )
    standing_models = [item.get("model") for item in standings]
    standing_house_values = [item.get("house") for item in standings]
    placement_values = [item.get("placement") for item in standings]
    if not all(isinstance(value, str) for value in standing_models):
        raise EvaluationVerificationError(
            f"Game {game_number} standing models must be strings"
        )
    if not all(isinstance(value, str) for value in standing_house_values):
        raise EvaluationVerificationError(
            f"Game {game_number} standing houses must be strings"
        )
    if not all(_is_int(value) for value in placement_values):
        raise EvaluationVerificationError(
            f"Game {game_number} standing placements must be integers"
        )
    standing_by_model = {item["model"]: item for item in standings}
    standing_houses = set(standing_house_values)
    placements = set(placement_values)
    if (
        set(standing_by_model) != expected_model_set
        or len(standing_by_model) != len(standings)
    ):
        raise EvaluationVerificationError(
            f"Game {game_number} result must contain each tournament model once"
        )
    if standing_houses != set(HOUSES):
        raise EvaluationVerificationError(
            f"Game {game_number} result must contain six unique base-game houses"
        )
    if placements != set(range(1, 7)):
        raise EvaluationVerificationError(
            f"Game {game_number} result placements must be the unique values 1-6"
        )
    for model, standing in standing_by_model.items():
        assignment = assignment_by_model[model]
        for key in ("house", "userId", "model", "harness", "promptSha256"):
            if standing.get(key) != assignment.get(key):
                raise EvaluationVerificationError(
                    f"Game {game_number} standing {model!r} has a different "
                    f"{key} than assignments.json"
                )
        metrics = standing.get("metrics")
        if not isinstance(metrics, dict):
            raise EvaluationVerificationError(
                f"Game {game_number} standing {model!r} has no metrics object"
            )
    return set(assignment_by_model)


def _resolve_attempt_directory(
    root: Path,
    attempt: dict[str, Any],
    *,
    game_number: int,
    require_exists: bool,
) -> Path:
    attempt_number = attempt.get("number")
    relative = attempt.get("directory")
    if not isinstance(relative, str) or not relative:
        raise EvaluationVerificationError(
            f"Game {game_number} attempt {attempt_number} has no artifact directory"
        )
    expected_relative = f"game-{game_number:02d}/attempt-{attempt_number:02d}"
    if relative != expected_relative:
        raise EvaluationVerificationError(
            f"Game {game_number} attempt {attempt_number} directory must be "
            f"{expected_relative!r}"
        )
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise EvaluationVerificationError(
            f"Game {game_number} attempt {attempt_number} directory escapes the "
            "evaluation directory"
        ) from None
    if require_exists and not candidate.is_dir():
        raise EvaluationVerificationError(
            f"Game {game_number} attempt {attempt_number} directory is missing: "
            f"{relative}"
        )
    return candidate


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _database_response_rows(
    path: Path,
    *,
    game_number: int,
    manifest_models: list[str],
) -> dict[tuple[str, str], str]:
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        agents = connection.execute(
            "SELECT id, model FROM agents ORDER BY created_at, id"
        ).fetchall()
        runs = connection.execute(
            """
            SELECT agent_runs.id, agent_runs.agent_id, agent_runs.response_id,
                   agent_runs.raw_usage_json
            FROM agent_runs
            ORDER BY agent_runs.created_at, agent_runs.id
            """
        ).fetchall()
    except sqlite3.Error as error:
        raise EvaluationVerificationError(
            f"Cannot inspect game {game_number} traces in harness.db: {error}"
        ) from None
    finally:
        if connection is not None:
            connection.close()

    model_by_agent = {str(row["id"]): str(row["model"]) for row in agents}
    if sorted(model_by_agent.values()) != sorted(manifest_models):
        raise EvaluationVerificationError(
            f"Game {game_number} harness.db does not contain the six tournament models"
        )
    run_agents = {str(row["agent_id"]) for row in runs}
    if run_agents != set(model_by_agent):
        raise EvaluationVerificationError(
            f"Game {game_number} harness.db has no trace for one or more models"
        )

    responses: dict[tuple[str, str], str] = {}
    for row in runs:
        try:
            raw_usage = json.loads(row["raw_usage_json"] or "[]")
        except (TypeError, json.JSONDecodeError):
            raise EvaluationVerificationError(
                f"Game {game_number} harness.db has invalid raw usage JSON"
            ) from None
        response_ids = [
            str(item["response_id"])
            for item in raw_usage
            if isinstance(item, dict) and item.get("response_id")
        ]
        if row["response_id"]:
            response_ids.append(str(row["response_id"]))
        for response_id in dict.fromkeys(response_ids):
            identity = (str(row["id"]), response_id)
            responses[identity] = model_by_agent[str(row["agent_id"])]
    if not responses:
        raise EvaluationVerificationError(
            f"Game {game_number} harness.db contains no provider response traces"
        )
    return responses


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    value = _read_json(path, label)
    if not isinstance(value, dict):
        raise EvaluationVerificationError(f"{label} must be a JSON object: {path}")
    return value


def _read_json_list(path: Path, label: str) -> list[Any]:
    value = _read_json(path, label)
    if not isinstance(value, list):
        raise EvaluationVerificationError(f"{label} must be a JSON list: {path}")
    return value


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise EvaluationVerificationError(f"Missing {label}: {path}") from None
    except OSError as error:
        raise EvaluationVerificationError(
            f"Cannot read {label} at {path}: {type(error).__name__}"
        ) from None
    except json.JSONDecodeError as error:
        raise EvaluationVerificationError(
            f"Invalid JSON in {label} at {path}: line {error.lineno}, "
            f"column {error.colno}"
        ) from None


def _sqlite_quick_check(path: Path, *, label: str) -> None:
    if not path.is_file():
        raise EvaluationVerificationError(f"Missing {label}: {path}")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        rows = connection.execute("PRAGMA quick_check").fetchall()
    except sqlite3.Error as error:
        raise EvaluationVerificationError(
            f"Cannot verify {label} at {path}: {error}"
        ) from None
    finally:
        if connection is not None:
            connection.close()
    messages = [str(row[0]) for row in rows]
    if messages != ["ok"]:
        raise EvaluationVerificationError(
            f"SQLite quick_check failed for {label}: {messages}"
        )


def _resolve_input(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify saved Raven evaluation artifacts without provider calls."
    )
    parser.add_argument("evaluation_directory")
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit unsuccessfully unless the complete 12-game comparison is present.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        report = verify_evaluation(
            _resolve_input(args.evaluation_directory),
            require_complete=args.require_complete,
        )
    except EvaluationIncompleteError as error:
        print(
            json.dumps(
                {"status": "valid", "evaluationStatus": "provisional", "error": str(error)}
            ),
            file=sys.stderr,
        )
        raise SystemExit(2) from None
    except EvaluationVerificationError as error:
        print(
            json.dumps({"status": "invalid", "error": str(error)}),
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
