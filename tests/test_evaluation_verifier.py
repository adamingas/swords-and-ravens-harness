import json

import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.evaluation import (
    TOURNAMENT_HARNESS_ID,
    TOURNAMENT_MODELS,
    _evaluation_schedule,
    _write_summary,
    house_rotation,
    user_rotation,
)
from raven_harness.evaluation_verifier import (
    EvaluationIncompleteError,
    EvaluationVerificationError,
    verify_evaluation,
)
from raven_harness.schemas import AgentCreate


EMPTY_METRICS = {
    "statusCounts": {"completed": 1},
    "modelCalls": {
        "started": 1,
        "responses": 1,
        "withoutResponse": 0,
        "responsesWithoutStart": 0,
        "startedByScope": {"agent": 1},
    },
    "tokens": {"input": 10, "output": 2, "total": 12},
    "costUsd": 0.001,
}
SYSTEM_PROMPT_HASH = "1" * 64
EFFECTIVE_PROMPT_HASH = "2" * 64
ENDPOINT_HASH = "3" * 64


def _verified_models() -> list[dict]:
    return [
        {
            "id": model,
            "name": model,
            "canonicalSlug": model,
            "aliasTarget": (
                "deepseek/deepseek-v4-flash-0731"
                if model.startswith("~deepseek/")
                else None
            ),
            "supportedParameters": ["tool_choice", "tools"],
        }
        for model in TOURNAMENT_MODELS
    ]


def _write_json(path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


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


def _completed_game(root, manifest, game_number: int) -> dict:
    rotation = house_rotation(game_number)
    users = user_rotation(game_number)
    relative = f"game-{game_number:02d}/attempt-01"
    attempt_dir = root / relative
    attempt_dir.mkdir(parents=True, exist_ok=True)
    assignments = [
        {
            "model": model,
            "house": rotation[model],
            "userId": users[model],
            "harness": TOURNAMENT_HARNESS_ID,
            "promptSha256": EFFECTIVE_PROMPT_HASH,
        }
        for model in TOURNAMENT_MODELS
    ]
    standings = [
        {
            **assignment,
            "placement": placement,
            "victoryPoints": 7 - placement,
            "metrics": EMPTY_METRICS,
        }
        for placement, assignment in enumerate(assignments, 1)
    ]
    winner = standings[0]["house"]
    database = Database(attempt_dir / "harness.db")
    store = AgentStore(database)
    for index, model in enumerate(TOURNAMENT_MODELS, 1):
        record = store.create_agent(
            AgentCreate(
                name=model,
                model=model,
                user_id=str(index),
                auth_token=str(index),
            )
        )
        store.add_run(
            run_id=f"run-{game_number}-{index}",
            agent_id=record.id,
            status="completed",
            observation={},
            response_id=f"response-{game_number}-{index}",
            usage={
                "requests": 1,
                "inputTokens": 10,
                "outputTokens": 2,
                "totalTokens": 12,
            },
            created_at=f"2026-09-06T00:00:{index:02d}+00:00",
        )
    database.close()
    result = {
        "gameNumber": game_number,
        "randomSeed": manifest["games"][game_number - 1]["randomSeed"],
        "endpointProvider": "Example endpoint",
        "winner": winner,
        "round": 10,
        "standings": standings,
    }
    _write_json(attempt_dir / "assignments.json", assignments)
    _write_json(attempt_dir / "game.json", _terminal_game(winner))
    _write_json(attempt_dir / "result.json", result)
    manifest["games"][game_number - 1]["attempts"] = [
        {
            "number": 1,
            "status": "completed",
            "directory": relative,
            "winner": winner,
            "activeElapsedSeconds": 10.0,
            "provenance": {
                "repositories": {},
                "harness": {
                    "id": TOURNAMENT_HARNESS_ID,
                    "runtimeSha256": "4" * 64,
                    "systemPromptSha256": SYSTEM_PROMPT_HASH,
                    "effectiveInstructionsSha256": EFFECTIVE_PROMPT_HASH,
                },
                "rules": {"available": True, "sha256": "5" * 64},
                "models": {
                    "ids": TOURNAMENT_MODELS,
                    "provider": "Example endpoint",
                    "baseUrlSha256": ENDPOINT_HASH,
                },
                "evaluation": {
                    "randomSeed": 1,
                    "gameCount": 12,
                    "gamesPerInvocation": 1,
                    "maxRounds": None,
                },
            },
            "modelVerification": {
                "source": "configured model endpoint catalog",
                "verifiedAt": "2026-09-06T00:00:00+00:00",
                "models": _verified_models(),
            },
        }
    ]
    return result


def _evaluation(root, *, game_count: int, completed_games: int) -> None:
    manifest = {
        "schemaVersion": 5,
        "experiment": "mixed-model-tournament",
        "harness": TOURNAMENT_HARNESS_ID,
        "models": TOURNAMENT_MODELS,
        "gameCount": game_count,
        "randomSeed": 1,
        "games": _evaluation_schedule(game_count),
    }
    results = [
        _completed_game(root, manifest, game_number)
        for game_number in range(1, completed_games + 1)
    ]
    if completed_games == game_count:
        manifest["finishedAt"] = "2026-09-06T00:10:00+00:00"
    _write_json(root / "manifest.json", manifest)
    assert len(results) == completed_games
    _write_summary(root, manifest)


def test_verifier_accepts_valid_partial_evaluation_as_provisional(tmp_path) -> None:
    root = tmp_path / "partial"
    _evaluation(root, game_count=12, completed_games=1)

    report = verify_evaluation(root)

    assert report["status"] == "valid"
    assert report["evaluationStatus"] == "provisional"
    assert report["scheduledGames"] == 12
    assert report["completedGames"] == 1
    assert report["checkedDatabases"] == 1
    assert report["summaryMatches"] is True
    assert report["comparisonComplete"] is False

    with pytest.raises(EvaluationIncompleteError, match="1/12 completed games"):
        verify_evaluation(root, require_complete=True)


def test_verifier_checks_failed_attempt_database(tmp_path) -> None:
    root = tmp_path / "failed-attempt"
    _evaluation(root, game_count=12, completed_games=1)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["games"][0]["attempts"][0]["status"] = "failed"
    manifest["games"][0]["attempts"][0]["error"] = "provider failed"
    _write_json(manifest_path, manifest)
    _write_summary(root, manifest)

    report = verify_evaluation(root)

    assert report["completedGames"] == 0
    assert report["checkedDatabases"] == 1
    database_path = root / "game-01/attempt-01/harness.db"
    database_path.write_text("not a SQLite database")
    with pytest.raises(
        EvaluationVerificationError, match="Cannot verify.*harness database"
    ):
        verify_evaluation(root)


def test_verifier_accepts_complete_two_rotation_comparison(tmp_path) -> None:
    root = tmp_path / "complete"
    _evaluation(root, game_count=12, completed_games=12)

    report = verify_evaluation(root, require_complete=True)

    assert report["evaluationStatus"] == "complete"
    assert report["completedGames"] == 12
    assert report["checkedDatabases"] == 12
    assert report["minimumObservationsPerModelHouse"] == 2
    assert report["comparisonComplete"] is True


def test_verifier_rejects_stale_summary(tmp_path) -> None:
    root = tmp_path / "stale-summary"
    _evaluation(root, game_count=12, completed_games=1)
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["completedGames"] = 0
    _write_json(summary_path, summary)

    with pytest.raises(EvaluationVerificationError, match="does not equal"):
        verify_evaluation(root)


def test_require_complete_reports_model_house_coverage_failure(
    tmp_path,
) -> None:
    root = tmp_path / "coverage"
    _evaluation(root, game_count=12, completed_games=11)

    report = verify_evaluation(root)

    assert report["evaluationStatus"] == "provisional"
    assert report["completedGames"] == 11
    assert report["minimumObservationsPerModelHouse"] == 1
    with pytest.raises(
        EvaluationIncompleteError,
        match="11/12 completed games.*minimum model-house appearances 1/2",
    ):
        verify_evaluation(root, require_complete=True)


def test_verifier_rejects_corrupt_harness_database(tmp_path) -> None:
    root = tmp_path / "corrupt-database"
    _evaluation(root, game_count=12, completed_games=1)
    (root / "game-01/attempt-01/harness.db").write_bytes(b"not a sqlite database")

    with pytest.raises(EvaluationVerificationError, match="Cannot verify.*database"):
        verify_evaluation(root)
