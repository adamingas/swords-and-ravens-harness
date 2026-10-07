"""Run one complete three- or six-house game using the normal harness classes."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import raven_harness.evaluation as evaluation_module
from raven_harness.config import Settings
from raven_harness.evaluation import (
    HOUSES, _build_provenance, _now, _preflight_model_catalog,
    _preflight_openrouter_quota, _write_json, run_game,
)


THREE_PLAYER_HOUSES = ["baratheon", "lannister", "stark"]


class SemaphoreLimitedAgentRunner:
    """Serialize whole model turns so their provider requests cannot overlap."""

    def __init__(self, runner: Any, *, max_parallel_turns: int) -> None:
        self.runner = runner
        self._turn_semaphore = asyncio.Semaphore(max_parallel_turns)

    @property
    def rules_oracle_available(self):
        return self.runner.rules_oracle_available

    async def run_once(self, **kwargs: Any):
        async with self._turn_semaphore:
            return await self.runner.run_once(**kwargs)

    async def shutdown(self):
        return await self.runner.shutdown()


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="openai/gpt-oss-120b")
    parser.add_argument("--game-port", type=int, default=5141)
    parser.add_argument("--random-seed", type=int, default=102)
    parser.add_argument("--player-count", type=int, choices=(3, 6), default=6)
    parser.add_argument("--model-concurrency", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--allow-runtime-change",
        action="store_true",
        help="Resume a saved board after recording an intentional harness change",
    )
    args = parser.parse_args()
    args.poll_seconds = 0.5
    args.stall_seconds = 0
    args.match_timeout_hours = 6
    if args.model_concurrency < 1:
        parser.error("--model-concurrency must be at least 1")
    seat_houses = THREE_PLAYER_HOUSES if args.player_count == 3 else HOUSES
    settings = Settings(autoplay_max_consecutive_failures=5,
                        autoplay_max_capacity_failures=20, autoplay_capacity_retry_base_seconds=5)
    await _preflight_openrouter_quota(settings)
    models = await _preflight_model_catalog(settings, model_ids=[args.model])
    original_runner_factory = evaluation_module.create_llm_runner
    evaluation_module.create_llm_runner = lambda settings, **kwargs: SemaphoreLimitedAgentRunner(
        original_runner_factory(settings, **kwargs),
        max_parallel_turns=args.model_concurrency,
    )
    args.output.mkdir(parents=True, exist_ok=args.resume)
    manifest = {
        "experiment": "structured-decisions-complete-game", "startedAt": _now(),
        "status": "running", "modelVerification": models,
        "provenance": _build_provenance(args, settings, model_ids=[args.model]),
        "players": args.player_count,
        "modelConcurrency": args.model_concurrency,
    }
    if args.resume:
        previous = json.loads((args.output / "manifest.json").read_text())
        previous_runtime = previous["provenance"]["harness"]["runtimeSha256"]
        current_runtime = manifest["provenance"]["harness"]["runtimeSha256"]
        if previous_runtime != current_runtime:
            if not args.allow_runtime_change:
                raise RuntimeError(
                    "Runtime changed; pass --allow-runtime-change to record an intentional "
                    "changed-harness continuation"
                )
            manifest["runtimeChangedOnResume"] = {
                "previousRuntimeSha256": previous_runtime,
                "currentRuntimeSha256": current_runtime,
            }
        manifest["previousSegments"] = [*previous.get("previousSegments", []), {k: v for k, v in previous.items() if k != "previousSegments"}]
    _write_json(args.output / "manifest.json", manifest)
    try:
        result = await run_game(
            game_number=1, attempt_dir=args.output, random_seed=args.random_seed,
            game_port=args.game_port, max_rounds=None, poll_seconds=args.poll_seconds,
            stall_seconds=args.stall_seconds, match_timeout_seconds=args.match_timeout_hours * 3600,
            settings=settings, seat_models=[args.model] * len(seat_houses), seat_houses=seat_houses,
            resume=args.resume,
        )
        manifest.update(status="completed", finishedAt=_now(), result=result)
        print(json.dumps({"status": "completed", "winner": result.get("winner")}), flush=True)
    except BaseException as exc:
        manifest.update(status="interrupted" if isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt)) else "failed",
                        finishedAt=_now(), error=str(exc))
        raise
    finally:
        evaluation_module.create_llm_runner = original_runner_factory
        _write_json(args.output / "manifest.json", manifest)


if __name__ == "__main__":
    asyncio.run(main())
