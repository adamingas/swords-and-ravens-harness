import argparse
import asyncio
import json

import pytest

from raven_harness.config import Settings
from raven_harness.evaluation import HOUSES
from raven_harness.house_evaluation import (
    HOUSE_TEST_AGENT_CONCURRENCY,
    HOUSE_TEST_GAMES,
    HOUSE_TEST_MODEL,
    run_house_evaluation,
    summarize_house_results,
)


def _result(game_number: int, winner: str = "stark") -> dict:
    standings = []
    for placement, house in enumerate(HOUSES, 1):
        standings.append(
            {
                "model": HOUSE_TEST_MODEL,
                "house": house,
                "placement": placement,
                "victoryPoints": 8 - placement,
                "landAreas": 8 - placement,
                "metrics": {
                    "statusCounts": {"completed": 2},
                    "modelRequests": 2,
                    "tokens": {
                        "input": 10,
                        "output": 2,
                        "total": 12,
                        "cachedInput": 3,
                    },
                    "costUsd": 0.01,
                },
            }
        )
    return {
        "gameNumber": game_number,
        "randomSeed": game_number,
        "winner": winner,
        "round": 10,
        "standings": standings,
    }


def test_house_summary_uses_complete_game_results_and_measured_time() -> None:
    results = [_result(game) for game in range(1, HOUSE_TEST_GAMES + 1)]

    summary = summarize_house_results(
        results,
        active_elapsed_seconds={game: 42.5 for game in range(1, 6)},
    )

    assert summary["complete"] is True
    assert summary["durationSeconds"] == {
        "minimum": 42.5,
        "average": 42.5,
        "maximum": 42.5,
        "allUnderOneMinute": True,
    }
    assert summary["houseStatistics"][0] == {
        "house": "stark",
        "games": 5,
        "wins": 5,
        "winRate": 1.0,
        "averagePlacement": 1.0,
        "averageVictoryPoints": 7.0,
        "averageLandAreas": 7.0,
    }
    assert summary["runStatusCounts"] == {"completed": 60}
    assert summary["modelRequests"] == 60
    assert summary["tokens"] == {
        "input": 300,
        "output": 60,
        "total": 360,
        "cachedInput": 90,
    }
    assert summary["costUsd"] == 0.3


@pytest.mark.asyncio
async def test_house_runner_uses_five_unrestricted_isolated_games(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    evaluation_root = tmp_path / "evaluations"
    output = evaluation_root / "house-test"
    rules = tmp_path / "rules.json"
    rules.write_text("{}\n")
    settings = Settings(
        rules_path=rules,
        openrouter_token="secret",
        _env_file=None,
    )
    settings_arguments: dict = {}
    calls: list[dict] = []
    active = 0
    peak_active = 0

    async def fake_run_game(**arguments):
        nonlocal active, peak_active
        calls.append(arguments)
        active += 1
        peak_active = max(peak_active, active)
        try:
            await asyncio.sleep(0.01)
            result = _result(arguments["game_number"])
            result_path = arguments["attempt_dir"] / "result.json"
            result_path.write_text(json.dumps(result))
            return result
        finally:
            active -= 1

    async def accept_quota(_settings):
        return None

    async def accept_model(_settings, *, model_ids):
        assert model_ids == [HOUSE_TEST_MODEL]
        return [{"id": HOUSE_TEST_MODEL}]

    def configured_settings(**kwargs):
        settings_arguments.update(kwargs)
        return settings

    monkeypatch.setattr("raven_harness.house_evaluation.Settings", configured_settings)
    monkeypatch.setattr(
        "raven_harness.house_evaluation._preflight_openrouter_quota", accept_quota
    )
    monkeypatch.setattr(
        "raven_harness.house_evaluation._preflight_model_catalog", accept_model
    )
    monkeypatch.setattr(
        "raven_harness.house_evaluation._build_provenance",
        lambda _args, _settings, *, model_ids: {
            "repositories": {},
            "harness": {},
            "rules": {},
            "models": {"ids": model_ids},
            "evaluation": {},
        },
    )
    monkeypatch.setattr("raven_harness.house_evaluation.run_game", fake_run_game)
    monkeypatch.setattr(
        "raven_harness.house_evaluation.resolve_evaluation_output",
        lambda _value, *, default_prefix: output,
    )
    args = argparse.Namespace(
        output=str(output),
        game_port=5201,
        concurrent_games=5,
        poll_seconds=0.25,
        stall_seconds=360.0,
        match_timeout_hours=6.0,
        continue_on_error=False,
        random_seed=102,
        max_rounds=None,
    )

    assert await run_house_evaluation(args) == output

    assert settings_arguments["model_max_concurrency"] == HOUSE_TEST_AGENT_CONCURRENCY
    assert peak_active == 5
    assert [call["game_port"] for call in calls] == list(range(5201, 5206))
    assert all(call["max_rounds"] is None for call in calls)
    assert all(call["seat_models"] == [HOUSE_TEST_MODEL] * 6 for call in calls)
    assert all(call["seat_houses"] == HOUSES for call in calls)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["maxRounds"] is None
    assert [game["attempts"][0]["status"] for game in manifest["games"]] == [
        "completed"
    ] * 5
    summary = json.loads((output / "summary.json").read_text())
    assert summary["completedGames"] == 5
