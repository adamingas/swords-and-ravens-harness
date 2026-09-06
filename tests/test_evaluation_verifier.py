import json
import sys

import pytest

from raven_harness.database import Database
from raven_harness.evaluation import (
    HOUSES,
    PROMPT_CONFIGURATIONS,
    _effective_instructions,
    _evaluation_schedule,
    _provider_attribution_summary,
    _sha256_text,
    _system_prompt,
    house_rotation,
    summarize_results,
    user_rotation,
)
from raven_harness.evaluation_verifier import (
    EvaluationIncompleteError,
    EvaluationVerificationError,
    main,
    verify_evaluation,
)


MODEL = "z-ai/glm-5.3-flash"
EMPTY_METRICS = {
    "statusCounts": {"completed": 1},
    "modelRequests": 1,
    "tokens": {"input": 10, "output": 2, "total": 12},
    "costUsd": 0.001,
}
EMPTY_PROVIDER_ATTRIBUTION = _provider_attribution_summary({"generations": []})


def _prompt_provenance() -> list[dict[str, str]]:
    return [
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
    assignments = [
        {
            "configuration": configuration.name,
            "house": rotation[configuration.name],
            "userId": users[configuration.name],
            "model": MODEL,
            "promptSha256": _sha256_text(_effective_instructions(configuration)),
        }
        for configuration in PROMPT_CONFIGURATIONS
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
    result = {
        "gameNumber": game_number,
        "randomSeed": manifest["games"][game_number - 1]["randomSeed"],
        "winner": winner,
        "round": 10,
        "standings": standings,
        "providerAttribution": EMPTY_PROVIDER_ATTRIBUTION,
    }
    relative = f"game-{game_number:02d}/attempt-01"
    attempt_dir = root / relative
    _write_json(attempt_dir / "assignments.json", assignments)
    _write_json(attempt_dir / "game.json", _terminal_game(winner))
    _write_json(attempt_dir / "result.json", result)
    _write_json(
        attempt_dir / "provider-generations.json",
        {"generations": [], **EMPTY_PROVIDER_ATTRIBUTION},
    )
    Database(attempt_dir / "harness.db").close()
    manifest["games"][game_number - 1]["attempts"] = [
        {
            "number": 1,
            "status": "completed",
            "directory": relative,
            "winner": winner,
        }
    ]
    return result


def _evaluation(root, *, game_count: int, completed_games: int) -> None:
    manifest = {
        "schemaVersion": 3,
        "model": MODEL,
        "gameCount": game_count,
        "randomSeed": 1,
        "configurations": [
            configuration.model_dump() for configuration in PROMPT_CONFIGURATIONS
        ],
        "provenance": {
            "repositories": {},
            "prompts": _prompt_provenance(),
            "rules": {},
            "model": {"id": MODEL},
            "evaluation": {"randomSeed": 1},
        },
        "games": _evaluation_schedule(game_count),
    }
    results = [
        _completed_game(root, manifest, game_number)
        for game_number in range(1, completed_games + 1)
    ]
    _write_json(root / "manifest.json", manifest)
    _write_json(root / "summary.json", summarize_results(results))


def test_verifier_accepts_valid_partial_evaluation_as_provisional(tmp_path) -> None:
    root = tmp_path / "partial"
    _evaluation(root, game_count=1, completed_games=1)

    report = verify_evaluation(root)

    assert report["status"] == "valid"
    assert report["evaluationStatus"] == "provisional"
    assert report["scheduledGames"] == 1
    assert report["completedGames"] == 1
    assert report["checkedDatabases"] == 1
    assert report["summaryMatches"] is True
    assert report["comparisonComplete"] is False

    with pytest.raises(EvaluationIncompleteError, match="1/12 completed games"):
        verify_evaluation(root, require_complete=True)


def test_verifier_accepts_complete_two_rotation_comparison(tmp_path) -> None:
    root = tmp_path / "complete"
    _evaluation(root, game_count=12, completed_games=12)

    report = verify_evaluation(root, require_complete=True)

    assert report["evaluationStatus"] == "complete"
    assert report["completedGames"] == 12
    assert report["checkedDatabases"] == 12
    assert report["minimumObservationsPerConfigurationHouse"] == 2
    assert report["comparisonComplete"] is True


def test_verifier_rejects_missing_completed_result(tmp_path) -> None:
    root = tmp_path / "missing-result"
    _evaluation(root, game_count=1, completed_games=1)
    (root / "game-01/attempt-01/result.json").unlink()

    with pytest.raises(EvaluationVerificationError, match="Missing game 1 completed result"):
        verify_evaluation(root)


def test_verifier_rejects_corrupt_completed_result(tmp_path) -> None:
    root = tmp_path / "corrupt-result"
    _evaluation(root, game_count=1, completed_games=1)
    (root / "game-01/attempt-01/result.json").write_text("{not-json")

    with pytest.raises(EvaluationVerificationError, match="Invalid JSON.*completed result"):
        verify_evaluation(root)


def test_verifier_rejects_stale_summary(tmp_path) -> None:
    root = tmp_path / "stale-summary"
    _evaluation(root, game_count=1, completed_games=1)
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["completedGames"] = 0
    _write_json(summary_path, summary)

    with pytest.raises(EvaluationVerificationError, match="does not equal"):
        verify_evaluation(root)


def test_require_complete_reports_configuration_house_coverage_failure(
    tmp_path,
) -> None:
    root = tmp_path / "coverage"
    _evaluation(root, game_count=12, completed_games=11)

    report = verify_evaluation(root)

    assert report["evaluationStatus"] == "provisional"
    assert report["completedGames"] == 11
    assert report["minimumObservationsPerConfigurationHouse"] == 1
    with pytest.raises(
        EvaluationIncompleteError,
        match="11/12 completed games.*minimum config-house observations 1/2",
    ):
        verify_evaluation(root, require_complete=True)


def test_verifier_rejects_assignment_model_mismatch(tmp_path) -> None:
    root = tmp_path / "model-mismatch"
    _evaluation(root, game_count=1, completed_games=1)
    assignment_path = root / "game-01/attempt-01/assignments.json"
    assignments = json.loads(assignment_path.read_text())
    assignments[0]["model"] = "another-model"
    _write_json(assignment_path, assignments)

    with pytest.raises(EvaluationVerificationError, match="must all use model"):
        verify_evaluation(root)


def test_verifier_rejects_result_random_seed_mismatch(tmp_path) -> None:
    root = tmp_path / "seed-mismatch"
    _evaluation(root, game_count=1, completed_games=1)
    result_path = root / "game-01/attempt-01/result.json"
    result = json.loads(result_path.read_text())
    result["randomSeed"] ^= 1
    _write_json(result_path, result)

    with pytest.raises(EvaluationVerificationError, match="random seed"):
        verify_evaluation(root)


def test_verifier_rejects_schedule_random_seed_mismatch(tmp_path) -> None:
    root = tmp_path / "schedule-seed-mismatch"
    _evaluation(root, game_count=1, completed_games=0)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["games"][0]["randomSeed"] ^= 1
    _write_json(manifest_path, manifest)

    with pytest.raises(EvaluationVerificationError, match="different seed"):
        verify_evaluation(root)


def test_verifier_rejects_missing_schema_three_provenance(tmp_path) -> None:
    root = tmp_path / "missing-provenance"
    _evaluation(root, game_count=1, completed_games=1)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    del manifest["provenance"]
    _write_json(manifest_path, manifest)

    with pytest.raises(EvaluationVerificationError, match="provenance is missing"):
        verify_evaluation(root)


def test_verifier_rejects_assignment_prompt_hash_mismatch(tmp_path) -> None:
    root = tmp_path / "prompt-mismatch"
    _evaluation(root, game_count=1, completed_games=1)
    assignment_path = root / "game-01/attempt-01/assignments.json"
    assignments = json.loads(assignment_path.read_text())
    assignments[0]["promptSha256"] = "0" * 64
    _write_json(assignment_path, assignments)

    with pytest.raises(EvaluationVerificationError, match="prompt hash"):
        verify_evaluation(root)


def test_verifier_rejects_noncanonical_provenance_prompt_hash(tmp_path) -> None:
    root = tmp_path / "provenance-prompt-mismatch"
    _evaluation(root, game_count=1, completed_games=1)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["provenance"]["prompts"][0]["effectiveInstructionsSha256"] = "0" * 64
    _write_json(manifest_path, manifest)

    with pytest.raises(EvaluationVerificationError, match="canonical prompt"):
        verify_evaluation(root)


def test_verifier_rejects_saved_winner_mismatch(tmp_path) -> None:
    root = tmp_path / "winner-mismatch"
    _evaluation(root, game_count=1, completed_games=1)
    winner = house_rotation(1)[PROMPT_CONFIGURATIONS[0].name]
    other = next(house for house in HOUSES if house != winner)
    _write_json(root / "game-01/attempt-01/game.json", _terminal_game(other))

    with pytest.raises(EvaluationVerificationError, match="saved terminal winner"):
        verify_evaluation(root)


def test_verifier_rejects_corrupt_harness_database(tmp_path) -> None:
    root = tmp_path / "corrupt-database"
    _evaluation(root, game_count=1, completed_games=1)
    (root / "game-01/attempt-01/harness.db").write_bytes(b"not a sqlite database")

    with pytest.raises(EvaluationVerificationError, match="Cannot verify.*database"):
        verify_evaluation(root)


def test_verifier_rejects_missing_provider_attribution(tmp_path) -> None:
    root = tmp_path / "missing-provider-attribution"
    _evaluation(root, game_count=1, completed_games=1)
    (root / "game-01/attempt-01/provider-generations.json").unlink()

    with pytest.raises(EvaluationVerificationError, match="provider attribution"):
        verify_evaluation(root)


def test_verifier_rejects_unexpected_resolved_provider_model(tmp_path) -> None:
    root = tmp_path / "resolved-model-mismatch"
    _evaluation(root, game_count=1, completed_games=1)
    generation = {
        "runId": "run-1",
        "agentId": "agent-1",
        "configuration": "Balanced",
        "responseId": "response-1",
        "responseIndex": 0,
        "provider": "Example",
        "model": "another/model",
        "costUsd": 0.001,
        "latencyMs": 10,
        "error": None,
    }
    summary = _provider_attribution_summary({"generations": [generation]})
    _write_json(
        root / "game-01/attempt-01/provider-generations.json",
        {"generations": [generation], **summary},
    )
    result_path = root / "game-01/attempt-01/result.json"
    result = json.loads(result_path.read_text())
    result["providerAttribution"] = summary
    _write_json(result_path, result)
    _write_json(root / "summary.json", summarize_results([result]))

    with pytest.raises(EvaluationVerificationError, match="unexpected model"):
        verify_evaluation(root)


def test_cli_uses_distinct_exit_for_valid_but_incomplete_evaluation(
    tmp_path, monkeypatch, capsys
) -> None:
    root = tmp_path / "cli-partial"
    _evaluation(root, game_count=1, completed_games=1)
    monkeypatch.setattr(
        sys,
        "argv",
        ["raven-verify-evaluation", str(root), "--require-complete"],
    )

    with pytest.raises(SystemExit) as caught:
        main()

    assert caught.value.code == 2
    output = json.loads(capsys.readouterr().err)
    assert output["status"] == "valid"
    assert output["evaluationStatus"] == "provisional"
