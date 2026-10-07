"""Read-only provider attribution for saved response IDs; no model calls."""
import asyncio
import json
from collections import Counter
from pathlib import Path
import httpx
from raven_harness.config import Settings

ROOT = Path('data/evaluations/luna-deepseek-qwen-20260923')

async def main():
    audit = json.loads((ROOT/'audit.json').read_text())
    path = ROOT/'generation-metadata.json'
    saved = json.loads(path.read_text()) if path.exists() else {}
    settings = Settings()
    async with httpx.AsyncClient(timeout=30) as client:
        for g in audit['generations']:
            rid = g['responseId']
            if rid in saved:
                continue
            response = await client.get(settings.openrouter_base_url+'/generation',
                params={'id':rid}, headers={'Authorization':'Bearer '+settings.openrouter_token})
            data = response.json().get('data')
            if not data:
                continue
            saved[rid] = {**g, **{k: data.get(k) for k in ['provider_name', 'model', 'finish_reason', 'native_finish_reason', 'latency', 'generation_time', 'total_cost']}}
    path.write_text(json.dumps(saved, indent=2)+'\n')
    print(dict(Counter((g['model'], g['provider_name']) for g in saved.values())))

if __name__ == '__main__':
    asyncio.run(main())
