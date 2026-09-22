"""Run one complete OSS 120B self-play game on Groq with high reasoning."""

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
    _run_assignments,
    _write_json,
    run_game,
)
from raven_harness.models.openai_agent import OpenRouterAgentRunner
from raven_harness.rulebook import Rulebook

THREE_HOUSES = ["baratheon", "lannister", "stark"]
SIX_HOUSES = ["stark", "greyjoy", "lannister", "tyrell", "martell", "baratheon"]
MODEL = "openai/gpt-oss-120b"


class GroqOnlyRunner(OpenRouterAgentRunner):
    """Change routing alone; retain the production decision loop and settings."""

    def _request_extra_body(self, *, user: str | None) -> dict[str, Any]:
        body = super()._request_extra_body(user=user)
        body.setdefault("provider", {}).update(
            only=["groq"], allow_fallbacks=False
        )
        return body


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=["oss"], default="oss")
    parser.add_argument("--players", type=int, choices=[3, 6], default=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--game-port", type=int, required=True)
    parser.add_argument("--random-seed", type=int, default=102)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--resume", action="store_true")
    options.add_argument("--resume-from", type=Path)
    args = parser.parse_args()
    args.poll_seconds = 1.0
    args.stall_seconds = 0
    args.match_timeout_hours = 6
    args.output = args.output.resolve()
    model = MODEL
    houses = THREE_HOUSES if args.players == 3 else SIX_HOUSES
    settings = Settings()
    if not settings.uses_openrouter:
        raise RuntimeError("This experiment requires the configured OpenRouter token")
    if not settings.resolved_rules_path.is_file():
        raise RuntimeError("Prepared rules are required for this experiment")
    if "groq" in settings.openrouter_blocked_providers:
        raise RuntimeError("Groq is excluded by the configured provider blocklist")
    await _preflight_openrouter_quota(settings)
    verified = await _preflight_model_catalog(settings, model_ids=[model])

    rulebook = Rulebook.load_optional(settings.resolved_rules_path)
    runner = GroqOnlyRunner(
        api_key=settings.openrouter_token,
        base_url=settings.openrouter_base_url,
        provider_blocklist=settings.openrouter_blocked_providers,
        max_output_tokens=32768,
        rulebook=rulebook,
    )
    routing = runner._request_extra_body(user=None).get("provider", {})
    provenance = _build_provenance(args, settings, model_ids=[model])
    provenance["evaluation"].update(gameCount=1, playerCount=args.players, houses=houses)
    provenance["models"]["providerRouting"] = routing
    provenance["harness"]["maxOutputTokens"] = 32768
    provenance["harness"]["parentReasoningEffort"] = "high"
    provenance["launcher"] = {
        "path": str(Path(__file__).resolve()),
        "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "productionRuntimeModified": False,
    }
    manifest = {
        "experiment": "oss-context-groq-high",
        "status": "running",
        "startedAt": _now(),
        "players": args.players,
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
        if previous["model"] != model or previous["players"] != args.players:
            raise RuntimeError("The source model and player count must match")
        for filename in ("game.json", "assignments.json"):
            shutil.copy2(source / filename, args.output / filename)
        previous_assignments = json.loads((source / "assignments.json").read_text())
        current_assignments = _run_assignments(
            game_number=1, seat_models=[model] * args.players, seat_houses=houses,
        )
        def seats(rows):
            return [{k: v for k, v in row.items() if k != "promptSha256"} for row in rows]
        if seats(previous_assignments) != seats(current_assignments):
            raise RuntimeError("Continuation must preserve all model/house/user assignments")
        # A continuation deliberately changes the shared prompt. Preserve its
        # old hash in provenance while scheduling the unchanged seats anew.
        _write_json(args.output / "assignments.json", current_assignments)
        with sqlite3.connect(source / "harness.db") as old_db:
            with sqlite3.connect(args.output / "harness.db") as new_db:
                old_db.backup(new_db)
        manifest["continuedFrom"] = {
            "directory": str(source), "manifest": previous,
            "sourceManifestSha256": hashlib.sha256((source / "manifest.json").read_bytes()).hexdigest(),
            "runtimeChanges": ["See current and source manifests for exact runtime hashes and settings"],
            "previousAssignments": previous_assignments,
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
                      "houses": houses, "seed": args.random_seed,
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
            seat_models=[model] * args.players,
            seat_houses=houses,
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
