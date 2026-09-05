from __future__ import annotations

import asyncio
from time import monotonic
from typing import Any

import httpx


FEATURED_MODELS = [
    "z-ai/glm-5.3-flash",
    "qwen/qwen3.7-flash",
    "inclusionai/ling-3.0-flash",
]
FALLBACK_MODELS = [
    {
        "id": FEATURED_MODELS[0],
        "name": "Z.ai: GLM 5.3 Flash",
        "promptPricePerMillion": 0.075,
        "completionPricePerMillion": 0.25,
    },
    {
        "id": FEATURED_MODELS[1],
        "name": "Qwen: Qwen3.7 Flash",
        "promptPricePerMillion": 0.03,
        "completionPricePerMillion": 0.13,
    },
    {
        "id": FEATURED_MODELS[2],
        "name": "inclusionAI: Ling 3.0 Flash",
        "promptPricePerMillion": 0.021,
        "completionPricePerMillion": 0.063,
    },
]


class OpenRouterModelCatalog:
    def __init__(
        self, *, base_url: str, api_key: str, ttl_seconds: float = 600
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.ttl_seconds = ttl_seconds
        self._models: list[dict[str, Any]] | None = None
        self._loaded_at = 0.0
        self._lock = asyncio.Lock()

    async def list_cheap_tool_models(self) -> list[dict[str, Any]]:
        if (
            self._models is not None
            and monotonic() - self._loaded_at < self.ttl_seconds
        ):
            return self._models
        async with self._lock:
            if (
                self._models is not None
                and monotonic() - self._loaded_at < self.ttl_seconds
            ):
                return self._models
            try:
                self._models = await self._fetch()
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                self._models = FALLBACK_MODELS
            self._loaded_at = monotonic()
            return self._models

    async def _fetch(self) -> list[dict[str, Any]]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=headers,
                params={
                    "supported_parameters": "tools",
                    "sort": "pricing-low-to-high",
                },
            )
            response.raise_for_status()
        candidates = []
        for model in response.json()["data"]:
            supported = set(model.get("supported_parameters") or [])
            if not {"tools", "tool_choice"}.issubset(supported):
                continue
            pricing = model.get("pricing") or {}
            prompt = _price_per_million(pricing.get("prompt"))
            completion = _price_per_million(pricing.get("completion"))
            if prompt <= 0 or completion <= 0:
                continue
            candidates.append(
                {
                    "id": model["id"],
                    "name": model.get("name") or model["id"],
                    "promptPricePerMillion": prompt,
                    "completionPricePerMillion": completion,
                    "contextLength": model.get("context_length"),
                }
            )
        cheap_candidates = [
            item
            for item in candidates
            if item["promptPricePerMillion"] <= 0.25
            and item["completionPricePerMillion"] <= 1
        ]
        cheap_candidates.sort(
            key=lambda item: item["promptPricePerMillion"]
            + item["completionPricePerMillion"]
        )
        featured = [
            item
            for model_id in FEATURED_MODELS
            for item in candidates
            if item["id"] == model_id
        ]
        featured_ids = {item["id"] for item in featured}
        selected = [
            *featured,
            *[item for item in cheap_candidates if item["id"] not in featured_ids][:24],
        ]
        return selected or FALLBACK_MODELS


def _price_per_million(value: Any) -> float:
    return float(value or 0) * 1_000_000
