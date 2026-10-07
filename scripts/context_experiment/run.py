"""Bounded context-comprehension experiment; paid read-only model calls, no game actions."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import random
import re
import time

from openai import AsyncOpenAI
from raven_harness.config import Settings
from raven_harness.harness.prompts import build_instructions
from raven_harness.game.map_reference import observation_map_reference
from raven_harness.harness.card_tools import _ability_texts
from raven_harness.harness.context_experiments import dump

POLICIES = ("baseline", "briefing", "continuity", "progressive", "verified")


def tool(name, description, field, choices=None):
    prop = {"type": "string"}
    if choices:
        prop["enum"] = choices
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {field: prop},
                "required": [field],
                "additionalProperties": False,
            },
        },
    }


TOOLS = [
    tool(
        "inspect_state",
        "Read sections of the frozen current PLAYER state. combat gives engine-calculated visible combat; public gives Wildling strength and ranking. Full returns the original observation.",
        "section",
        ["board", "houses", "cards", "events", "full", "combat", "public"],
    ),
    tool(
        "reachable_areas",
        "Check geographic movement routes using current ships. Does not establish support or complete move legality.",
        "area",
    ),
    tool(
        "support_eligibility",
        "Check which areas can support a battlefield with current REVEALED support orders; not a movement query or a prediction of future orders.",
        "battlefield",
    ),
    tool(
        "inspect_card",
        "Read printed strength and effects of a visible house card.",
        "card_id",
    ),
    tool(
        "recall_previous",
        "Read the previous distinct decision observation and accepted action receipt for this house.",
        "request",
    ),
]


def dispatch(case, name, args):
    obs = case["observation"]
    if name == "inspect_state":
        section = args["section"]
        if section == "full":
            return obs
        if section == "combat":
            return case["engine"]["combat"]
        if section == "public":
            return {key: case["engine"][key] for key in ("wildlingStrength", "ranking")}
        return obs[
            {
                "board": "board",
                "houses": "houses",
                "cards": "houseCardStatus",
                "events": "recentEvents",
            }[section]
        ]
    if name == "reachable_areas":
        from raven_harness.harness.observation import build_context
        from raven_harness.harness.reachability_tools import movement_reachability

        return movement_reachability(
            build_context(case["snapshot"], obs["you"]["userId"]), args["area"]
        )
    if name == "support_eligibility":
        area = args["battlefield"]
        return {
            "battlefield": area,
            "eligibleAreasWithRevealedSupportOrders": case["engine"]["support"][area],
            "meaning": "These areas are eligible now, not necessarily committed. No other area can currently support this battlefield.",
        }
    if name == "recall_previous":
        return case["previous"]
    if name == "inspect_card":
        query = args["card_id"]
        cards = [
            c
            for h in case["snapshot"]["childGameState"]["game"]["houses"]
            for _, c in h["houseCards"]
        ]
        c = next(c for c in cards if c["id"] == query)
        return {
            "id": c["id"],
            "strength": c["combatStrength"],
            "swords": c.get("swordIcons", 0),
            "fortifications": c.get("towerIcons", 0),
            "ability": _ability_texts().get(c.get("abilityId"), "No printed ability."),
        }
    raise ValueError("Unknown tool")


def score(record):
    """Semantic grading excludes harmless JSON/label variations from gameplay errors."""
    answers = list(record.get("answers", []))
    if record["key"] == "D116" and answers == ["0", "no", "no"]:
        answers = ["0", "no"]
    if record["key"] == "D076" and len(answers) == 2 and answers[1] == "unknown":
        answers[1] = "no"
    if record["key"] == "D154" and len(answers) == 3:
        answers[:2] = [
            re.sub(r"^(?:lannister|baratheon)\s+", "", a) for a in answers[:2]
        ]
    return answers == record["expected"]


async def run_one(client, case, policy, repeat, model, provider, max_requests):
    system = build_instructions(
        "You are playing A Game of Thrones as "
        + case["observation"]["you"]["houseId"]
        + ".",
        map_reference=observation_map_reference(case["observation"]),
    )
    question = (
        "\n\nContext comprehension check; do not submit a game action. "
        + case["question"]
        + '\nReturn JSON with "answers": an ordered list of short lowercase strings, and "reason": a short explanation. '
        "Use digits for numeric answers, yes/no for binary answers, area/house IDs for names. "
        "Say unknown if the supplied facts and tools cannot establish an answer. Tools are optional unless instructed otherwise."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": case["prompts"][policy] + question},
    ]
    record = {
        "key": case["key"],
        "policy": policy,
        "repeat": repeat,
        "model": model,
        "observationSha256": case["observationSha256"],
        "expected": case["expected"],
        "calls": [],
        "usage": [],
        "requestCount": 0,
    }
    started = time.monotonic()
    try:
        for _ in range(max_requests):
            record["requestCount"] += 1
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                temperature=0,
                max_tokens=4096,
                extra_body={
                    "reasoning": {"effort": "medium"},
                    "provider": {"only": [provider], "allow_fallbacks": False},
                },
            )
            if response.usage:
                record["usage"].append(response.usage.model_dump())
            message = response.choices[0].message
            record.setdefault("responses", []).append(message.model_dump())
            if not message.tool_calls:
                record["text"] = message.content or ""
                record["finishReason"] = response.choices[0].finish_reason
                try:
                    content = (
                        record["text"]
                        .strip()
                        .removeprefix("```json")
                        .removesuffix("```")
                        .strip()
                    )
                    answer = json.loads(content)
                    record["answers"] = [
                        str(a).lower().strip() for a in answer["answers"]
                    ]
                    record["correct"] = score(record)
                except (ValueError, KeyError, TypeError):
                    record["correct"] = False
                    record["parseFailure"] = True
                break
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [t.model_dump() for t in message.tool_calls],
                }
            )
            for call in message.tool_calls:
                try:
                    args = json.loads(call.function.arguments)
                    result = dispatch(case, call.function.name, args)
                except Exception as exc:
                    result = {"error": str(exc)}
                record["calls"].append(
                    {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                        "result": result,
                    }
                )
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": dump(result)}
                )
        else:
            record["error"] = "request_limit"
    except Exception as exc:
        # Do not dump client configuration or credentials.
        record["error"] = type(exc).__name__ + ": " + str(exc)[:500]
    record["durationSeconds"] = round(time.monotonic() - started, 2)
    return record


def summarize(records, cases):
    summary = {}
    for policy in POLICIES:
        runs = [r for r in records if r["policy"] == policy]
        if not runs:
            continue
        summary[policy] = {
            "runs": len(runs),
            "correct": sum(r.get("correct", False) for r in runs),
            "errors": sum("error" in r for r in runs),
            "parseFailures": sum(r.get("parseFailure", False) for r in runs),
            "toolCalls": sum(len(r["calls"]) for r in runs),
            "promptTokensAcrossRequests": sum(
                u.get("prompt_tokens", 0) for r in runs for u in r["usage"]
            ),
            "completionTokensAcrossRequests": sum(
                u.get("completion_tokens", 0) for r in runs for u in r["usage"]
            ),
            "estimatedInitialContextTokens": sum(
                c["estimatedContextTokens"][policy] for c in cases
            ),
            "correctByCase": {
                c["key"]: sum(
                    r.get("correct", False) for r in runs if r["key"] == c["key"]
                )
                for c in cases
            },
        }
    return summary


async def main(args):
    cases = json.loads((args.data / "cases.json").read_text())
    configuration = {
        "model": args.model,
        "provider": args.provider,
        "reasoning": "medium",
        "temperature": 0,
        "maxTokens": 4096,
        "maxRequests": args.max_requests,
        "inputsSha256": hashlib.sha256(
            dump(
                [
                    {
                        "key": case["key"],
                        "prompts": case["prompts"],
                        "question": case["question"],
                        "system": build_instructions(
                            "You are playing A Game of Thrones as "
                            + case["observation"]["you"]["houseId"]
                            + ".",
                            map_reference=observation_map_reference(
                                case["observation"]
                            ),
                        ),
                    }
                    for case in cases
                ]
            ).encode()
        ).hexdigest(),
        "toolsSha256": hashlib.sha256(dump(TOOLS).encode()).hexdigest(),
    }
    config_path = args.data / "configuration.json"
    if config_path.exists():
        if json.loads(config_path.read_text()) != configuration:
            raise SystemExit(
                "Experiment configuration changed; use a fresh --data directory."
            )
    elif (args.data / "results.jsonl").exists():
        raise SystemExit(
            "Existing results have no configuration manifest; use a fresh --data directory."
        )
    else:
        config_path.write_text(json.dumps(configuration, indent=2) + "\n")
    settings = Settings()
    if not settings.openrouter_token:
        raise SystemExit(
            "OpenRouter credentials unavailable; offline fixtures still usable."
        )
    output = args.data / "results.jsonl"
    records = (
        [json.loads(line) for line in output.read_text().splitlines()]
        if output.exists()
        else []
    )
    for record in records:
        record["correct"] = score(record)
    done = {(r["key"], r["policy"], r["repeat"]) for r in records}
    tasks = [
        (c, p, repeat)
        for repeat in range(args.repeats)
        for c in cases
        for p in POLICIES
        if (c["key"], p, repeat) not in done
    ]
    random.Random(20260923).shuffle(tasks)
    semaphore = asyncio.Semaphore(3)
    async with AsyncOpenAI(
        api_key=settings.openrouter_token,
        base_url=settings.openrouter_base_url,
        timeout=90,
        max_retries=0,
    ) as client:

        async def work(case, policy, repeat):
            async with semaphore:
                record = await run_one(
                    client,
                    case,
                    policy,
                    repeat,
                    args.model,
                    args.provider,
                    args.max_requests,
                )
                records.append(record)
                with output.open("a") as file:
                    file.write(dump(record) + "\n")
                print(
                    f"{case['key']} {policy} r{repeat}: correct={record.get('correct')} tools={len(record['calls'])} error={record.get('error', '')}",
                    flush=True,
                )

        await asyncio.gather(*(work(*item) for item in tasks))
    output.write_text("".join(dump(record) + "\n" for record in records))
    summary = summarize(records, cases)
    (args.data / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/context-experiment"))
    parser.add_argument("--model", default="openai/gpt-oss-120b")
    parser.add_argument("--provider", default="Cerebras")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--max-requests", type=int, default=4)
    asyncio.run(main(parser.parse_args()))
