"""One mixed-model game. Only routing/configuration differ from production."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import tarfile

from raven_harness.config import Settings
from raven_harness.errors import safe_error_text
from raven_harness.evaluation import (
    _acquire_runner_lock, _build_provenance, _now, _preflight_model_catalog,
    _preflight_openrouter_quota, _runtime_fingerprint, _write_json, run_game,
)
from raven_harness.models.openai_agent import OpenRouterAgentRunner
from raven_harness.rulebook import Rulebook

ROUTES = {
    'openai/gpt-6-luna': 'openai',
    'deepseek/deepseek-v4.1-flash': 'morph',
    'qwen/qwen3.8-27b': 'deepinfra/bf16',
}
HOUSES = ['baratheon', 'lannister', 'stark']


class PinnedRunner(OpenRouterAgentRunner):
    def __init__(self, *, provider, **kwargs):
        super().__init__(**kwargs)
        self.provider = provider

    def _request_extra_body(self, *, user):
        body = super()._request_extra_body(user=user)
        body.setdefault('provider', {}).update(only=[self.provider], allow_fallbacks=False)
        return body


class SeatRouter:
    """Select an unchanged production runner for each model, including its oracle."""
    def __init__(self, settings, rulebook):
        self.runners = {}
        for model, provider in ROUTES.items():
            if provider.split('/')[0] in settings.openrouter_blocked_providers:
                raise ValueError(f'Requested provider is blocked: {provider}')
            self.runners[model] = PinnedRunner(
                provider=provider, api_key=settings.openrouter_token,
                base_url=settings.openrouter_base_url,
                provider_blocklist=settings.openrouter_blocked_providers,
                rulebook=rulebook, max_output_tokens=40960,
            )

    @property
    def rules_oracle_available(self):
        return all(r.rules_oracle_available for r in self.runners.values())

    async def run_once(self, **kwargs):
        return await self.runners[kwargs['agent_record'].model].run_once(**kwargs)

    async def shutdown(self):
        await asyncio.gather(*(r.shutdown() for r in self.runners.values()))


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/evaluations/luna-deepseek-qwen-20260923'))
    parser.add_argument('--game-port', type=int, default=5223)
    parser.add_argument('--random-seed', type=int, default=102)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    args.poll_seconds = 1.0
    args.stall_seconds = 0
    args.match_timeout_hours = 6
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / 'manifest.json'
    if manifest_path.exists() and not args.resume:
        raise RuntimeError('Existing experiment; use --resume deliberately')
    lock = _acquire_runner_lock(args.output)
    settings = Settings()
    if not settings.uses_openrouter:
        raise RuntimeError('Configured OpenRouter credential required')
    await _preflight_openrouter_quota(settings)
    verified = await _preflight_model_catalog(settings, model_ids=list(ROUTES))
    rulebook = Rulebook.load_optional(settings.resolved_rules_path)
    if rulebook is None:
        raise RuntimeError('Prepared rules required')
    runner = SeatRouter(settings, rulebook)
    provenance = _build_provenance(args, settings, model_ids=list(ROUTES))
    provenance['harness']['maxOutputTokens'] = 40960
    provenance['models']['providerRouting'] = {
        model: r._request_extra_body(user=None)['provider']
        for model, r in runner.runners.items()
    }
    provenance['evaluation'].update(gameCount=1, playerCount=3, houses=HOUSES)
    provenance['launcher'] = {
        'path': str(Path(__file__).resolve()),
        'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'productionRuntimeModified': False,
    }
    manifest = dict(experiment='luna-deepseek-qwen-three-player', status='running',
                    startedAt=_now(), modelVerification=verified, provenance=provenance,
                    schemaFailurePolicy='Attribute invalid schema retries to provider; no harness workarounds or repairs.')
    if args.resume:
        previous = json.loads(manifest_path.read_text())
        if previous['status'] == 'completed':
            raise RuntimeError('Game already completed')
        for key in ['harness', 'rules', 'models', 'evaluation', 'launcher']:
            if previous['provenance'][key] != provenance[key]:
                raise RuntimeError(f'Resume provenance changed: {key}')
        manifest['previousSegments'] = [*previous.get('previousSegments', []),
            {k: v for k, v in previous.items() if k != 'previousSegments'}]
    else:
        with tarfile.open(args.output / 'runtime-source.tar.gz', 'w:gz') as archive:
            archive.add('src/raven_harness', arcname='src/raven_harness',
                        filter=lambda item: None if '__pycache__' in item.name else item)
    _write_json(manifest_path, manifest)
    print(json.dumps({'status': 'starting', 'routes': ROUTES, 'houses': HOUSES}), flush=True)
    try:
        result = await run_game(
            game_number=1, attempt_dir=args.output, random_seed=args.random_seed,
            game_port=args.game_port, max_rounds=None, poll_seconds=1,
            stall_seconds=0, match_timeout_seconds=6 * 3600, settings=settings,
            model_runner=runner, seat_models=list(ROUTES), seat_houses=HOUSES,
            resume=args.resume,
        )
        manifest.update(status='completed', finishedAt=_now(), result=result)
        print(json.dumps({'status': 'completed', 'winner': result['winner'], 'round': result['round']}), flush=True)
    except BaseException as error:
        manifest.update(status='interrupted' if isinstance(error, (KeyboardInterrupt, asyncio.CancelledError)) else 'failed',
                        finishedAt=_now(), error=safe_error_text(error))
        print(json.dumps({'status': manifest['status'], 'error': manifest['error']}), flush=True)
        raise
    finally:
        manifest['runtimeUnchangedAtExit'] = _runtime_fingerprint() == provenance['harness']['runtimeSha256']
        _write_json(manifest_path, manifest)
        await runner.shutdown()
        lock.close()


if __name__ == '__main__':
    asyncio.run(main())
