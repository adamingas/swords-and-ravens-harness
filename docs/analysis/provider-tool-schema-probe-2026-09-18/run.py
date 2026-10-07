from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Literal

from agents import Agent, ModelSettings, RunConfig, Runner, function_tool
from openai import AsyncOpenAI
from pydantic import BaseModel

from raven_harness.models.openai_agent import _UsageCapturingResponsesModel


MODEL = os.environ.get("PROBE_MODEL", "deepseek/deepseek-v4.1-flash")
BASE_URL = "https://openrouter.ai/api/v1"
HERE = Path(__file__).resolve().parent
RESULTS_PATH = Path(os.environ.get("PROBE_RESULTS_PATH", HERE / "results.json"))
CONCURRENCY = 3
PROVIDER_SLUG_OVERRIDES = {
    "Amazon Bedrock": "amazon-bedrock",
    "AtlasCloud": "atlas-cloud",
    "InferenceNet": "inference-net",
    "Io Net": "io-net",
    "Near AI": "near-ai",
    "Sail Research": "sail-research",
    "Z.AI": "z-ai",
}


class DummyResult(BaseModel):
    input_value: int
    doubled_value: int
    tool_was_used: Literal[True]


def load_token() -> str:
    for line in Path(".env").read_text().splitlines():
        if line.startswith(("OPENROUTER_TOKEN=", "OPENROUTER_API_KEY=")):
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            if token:
                return token
    raise RuntimeError("No OpenRouter token found")


def load_providers() -> list[dict[str, object]]:
    url = f"{BASE_URL}/models/{MODEL}/endpoints"
    with urllib.request.urlopen(url) as response:
        endpoints = json.load(response)["data"]["endpoints"]
    providers: dict[str, dict[str, object]] = {}
    for endpoint in endpoints:
        name = endpoint["provider_name"]
        provider = providers.setdefault(
            name,
            {
                "name": name,
                "slug": PROVIDER_SLUG_OVERRIDES.get(name, name.lower()),
                "advertisedParameters": set(),
                "endpointCount": 0,
            },
        )
        provider["endpointCount"] += 1
        provider["advertisedParameters"].update(
            endpoint.get("supported_parameters") or []
        )
    return [
        {
            **provider,
            "advertisedParameters": sorted(provider["advertisedParameters"]),
        }
        for provider in providers.values()
    ]


def response_summary(response: object) -> dict[str, object]:
    output = list(getattr(response, "output", []) or [])
    return {
        "responseId": getattr(response, "id", None),
        "status": getattr(response, "status", None),
        "outputTypes": [getattr(item, "type", None) for item in output],
        "toolNames": [
            getattr(item, "name", None)
            for item in output
            if getattr(item, "type", None) == "function_call"
        ],
    }


async def probe(
    provider: dict[str, object], token: str, semaphore: asyncio.Semaphore
) -> dict[str, object]:
    name = str(provider["name"])
    slug = str(provider["slug"])
    tool_calls: list[int] = []
    raw_responses: list[tuple[str, object]] = []

    @function_tool
    async def double_number(value: int) -> dict[str, int]:
        """Double an integer and return both the input and computed result."""

        tool_calls.append(value)
        return {"input_value": value, "doubled_value": value * 2}

    client = AsyncOpenAI(
        api_key=token,
        base_url=BASE_URL,
        timeout=None,
        max_retries=0,
    )
    model = _UsageCapturingResponsesModel(
        model=MODEL,
        openai_client=client,
        response_sink=raw_responses,
    )
    agent = Agent(
        name="Provider tool and schema probe",
        instructions=(
            "You must call the double_number tool with value 21 before answering. "
            "Do not calculate or return the final answer until the tool result is available. "
            "After the tool returns, provide the final structured answer using its result."
        ),
        model=model,
        tools=[double_number],
        output_type=DummyResult,
        model_settings=ModelSettings(
            tool_choice="auto",
            parallel_tool_calls=False,
            reasoning={"effort": "high"},
            store=False,
            preserve_raw_usage=True,
            extra_body={
                "provider": {"only": [slug], "allow_fallbacks": False},
                "session_id": f"raven-dummy-tool-schema-{slug}",
            },
        ),
        tool_use_behavior="run_llm_again",
        reset_tool_choice=False,
    )
    started = time.monotonic()
    print(f"START {name}", flush=True)
    result: dict[str, object] = {
        **provider,
        "model": MODEL,
        "toolChoice": "auto",
        "outputSchema": DummyResult.model_json_schema(),
    }
    try:
        async with semaphore:
            run = await Runner.run(
                agent,
                input="Follow the instructions and return the doubled value.",
                max_turns=None,
                run_config=RunConfig(tracing_disabled=True),
            )
        final = run.final_output
        result.update(
            {
                "status": "completed",
                "toolCallArguments": tool_calls,
                "toolWasCalled": bool(tool_calls),
                "finalOutput": (
                    final.model_dump(mode="json")
                    if isinstance(final, BaseModel)
                    else final
                ),
                "responses": [
                    response_summary(response) for _scope, response in raw_responses
                ],
            }
        )
    except Exception as error:
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", {}) if response is not None else {}
        result.update(
            {
                "status": "error",
                "toolCallArguments": tool_calls,
                "toolWasCalled": bool(tool_calls),
                "errorType": type(error).__name__,
                "error": str(error),
                "retryAfter": headers.get("retry-after"),
                "responses": [
                    response_summary(response) for _scope, response in raw_responses
                ],
            }
        )
    finally:
        result["elapsedSeconds"] = round(time.monotonic() - started, 3)
        await client.close()
    print(
        f"DONE {name} status={result['status']} tool={result['toolWasCalled']} "
        f"seconds={result['elapsedSeconds']}",
        flush=True,
    )
    return result


async def main() -> None:
    token = load_token()
    providers = await asyncio.to_thread(load_providers)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    tasks = [asyncio.create_task(probe(provider, token, semaphore)) for provider in providers]
    results: list[dict[str, object]] = []
    for task in asyncio.as_completed(tasks):
        results.append(await task)
        RESULTS_PATH.write_text(
            json.dumps(
                {
                    "model": MODEL,
                    "concurrency": CONCURRENCY,
                    "providerCount": len(providers),
                    "results": sorted(results, key=lambda row: str(row["name"])),
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    asyncio.run(main())
