"""Run one three-player self-play game with the current production harness."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from raven_harness.config import Settings
from raven_harness.errors import safe_error_text
from raven_harness.evaluation import (
    _acquire_runner_lock,
    _build_provenance,
    _now,
    _preflight_model_catalog,
    _preflight_openrouter_quota,
    _write_json,
    run_game,
)
from raven_harness.models.openai_agent import OpenRouterAgentRunner
from raven_harness.models.runner import create_llm_runner
from raven_harness.rulebook import Rulebook

HOUSES = ["baratheon", "lannister", "stark"]
MODELS = {
    "oss": "openai/gpt-oss-120b",
    "deepseek": "deepseek/deepseek-v4.1-flash",
}


class CerebrasOnlyRunner(OpenRouterAgentRunner):
    """Change routing alone; retain the production decision loop and settings."""

    def _request_extra_body(self, *, user: str | None) -> dict[str, Any]:
        body = super()._request_extra_body(user=user)
        body.setdefault("provider", {}).update(
            only=["cerebras"], allow_fallbacks=False
        )
        return body


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=MODELS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--game-port", type=int, required=True)
    parser.add_argument("--random-seed", type=int, default=102)
    resume_options = parser.add_mutually_exclusive_group()
    resume_options.add_argument("--resume", action="store_true")
    resume_options.add_argument("--resume-from", type=Path, help="Continue a stopped save in a new output directory with explicitly changed runtime provenance")
    args = parser.parse_args()
    args.poll_seconds = 1.0
    args.stall_seconds = 0
    args.match_timeout_hours = 6
    args.output = args.output.resolve()
    model = MODELS[args.game]
    settings = Settings()
    if not settings.uses_openrouter:
        raise RuntimeError("This experiment requires the configured OpenRouter token")
    if not settings.resolved_rules_path.is_file():
        raise RuntimeError("Prepared rules are required for this experiment")
    if args.game == "oss" and "cerebras" in settings.openrouter_blocked_providers:
        raise RuntimeError("Cerebras is excluded by the configured provider blocklist")
    await _preflight_openrouter_quota(settings)
    verified = await _preflight_model_catalog(settings, model_ids=[model])

    rulebook = Rulebook.load_optional(settings.resolved_rules_path)
    runner = (
        CerebrasOnlyRunner(
            api_key=settings.openrouter_token,
            base_url=settings.openrouter_base_url,
            provider_blocklist=settings.openrouter_blocked_providers,
            max_output_tokens=40960,
            rulebook=rulebook,
        )
        if args.game == "oss"
        else create_llm_runner(settings, rulebook=rulebook)
    )
    routing = runner._request_extra_body(user=None).get("provider", {})
    provenance = _build_provenance(args, settings, model_ids=[model])
    provenance["evaluation"].update(gameCount=1, playerCount=3, houses=HOUSES)
    provenance["models"]["providerRouting"] = routing
    provenance["harness"]["maxOutputTokens"] = 40960 if args.game == "oss" else None
    provenance["evaluation"]["purpose"] = "geographic-reachability-with-schema-recovery"
    provenance["launcher"] = {
        "path": str(Path(__file__).resolve()),
        "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "productionRuntimeModified": False,
    }
    manifest = {
        "experiment": "geographic-reachability-with-schema-recovery",
        "status": "running",
        "startedAt": _now(),
        "players": 3,
        "model": model,
        "modelVerification": verified,
        "modelConcurrency": "normal simultaneous-player concurrency",
        "provenance": provenance,
    }
    args.output.mkdir(parents=True, exist_ok=args.resume)
    lock = _acquire_runner_lock(args.output)
    manifest_path = args.output / "manifest.json"
    if args.resume_from:
        source = args.resume_from.resolve()
        previous = json.loads((source / "manifest.json").read_text())
        if previous["status"] in {"running", "completed"}:
            raise RuntimeError("The source must be a stopped, unfinished experiment")
        if previous["model"] != model or previous["players"] != 3:
            raise RuntimeError("The source model and player count must match")
        for filename in ("game.json", "assignments.json"):
            shutil.copy2(source / filename, args.output / filename)
        with sqlite3.connect((source / "harness.db").as_uri() + "?mode=ro", uri=True) as old_db:
            with sqlite3.connect(args.output / "harness.db") as new_db:
                old_db.backup(new_db)
        manifest["continuedFrom"] = {
            "directory": str(source), "manifest": previous,
            "sourceManifestSha256": hashlib.sha256((source / "manifest.json").read_bytes()).hexdigest(),
            "runtimeChanges": ["Explicit schema-rejection feedback and fixed-item description", "Parent output allowance 40960; oracle remains 900"],
        }
    if args.resume:
        previous = json.loads(manifest_path.read_text())
        if previous["status"] == "completed":
            raise RuntimeError("The game is already completed")
        for key in ("harness", "rules", "models", "evaluation", "launcher"):
            if previous["provenance"][key] != provenance[key]:
                raise RuntimeError(f"Cannot resume: {key} provenance changed")
        manifest["previousSegments"] = [
            *previous.get("previousSegments", []),
            {k: v for k, v in previous.items() if k != "previousSegments"},
        ]
    _write_json(manifest_path, manifest)
    print(json.dumps({"status": "starting", "model": model, "routing": routing,
                      "houses": HOUSES, "seed": args.random_seed,
                      "output": str(args.output)}), flush=True)
    try:
        result = await run_game(
            game_number=1,
            attempt_dir=args.output,
            random_seed=args.random_seed,
            game_port=args.game_port,
            max_rounds=None,
            poll_seconds=args.poll_seconds,
            stall_seconds=args.stall_seconds,
            match_timeout_seconds=args.match_timeout_hours * 3600,
            settings=settings,
            model_runner=runner,
            seat_models=[model] * 3,
            seat_houses=HOUSES,
            resume=args.resume or args.resume_from is not None,
        )
        manifest.update(status="completed", finishedAt=_now(), result=result)
        print(json.dumps({"status": "completed", "model": model,
                          "winner": result["winner"], "round": result["round"]}),
              flush=True)
    except BaseException as error:
        status = (
            "interrupted"
            if isinstance(error, (asyncio.CancelledError, KeyboardInterrupt))
            else "failed"
        )
        manifest.update(status=status, finishedAt=_now(), error=safe_error_text(error))
        print(json.dumps({"status": status, "model": model,
                          "error": safe_error_text(error)}), flush=True)
        raise
    finally:
        _write_json(manifest_path, manifest)
        await runner.shutdown()
        lock.close()


if __name__ == "__main__":
    asyncio.run(main())
