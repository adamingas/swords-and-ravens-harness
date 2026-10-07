"""Export every saved request field and model response into one readable file."""

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def fenced(text, language="text"):
    longest = max((len(match) for match in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text}\n{fence}\n"


def json_block(value):
    rendered = json.dumps(value, indent=2, ensure_ascii=False)
    assert json.loads(rendered) == value
    return fenced(rendered, "json")


def response_text(items):
    for item in items:
        if item.get("type") == "partial_model_response":
            yield from response_text(item["output"])
        else:
            for block in item.get("content", []):
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    yield item["type"], block["text"]


def main():
    summary = json.loads((ROOT / "results/summary.json").read_text())
    cases = summary["cases"]
    parts = [
        "# Full prompts and unfiltered recorded answers — ten map-context replays\n",
        "These are the actual saved outgoing requests and complete stored model "
        "outputs from the compact-map experiment. Nothing is shortened or redacted. "
        "JSON is pretty-printed; system instructions and returned answer text are "
        "also shown as literal text for reading. The observation appears both "
        "inside the exact input and in an expanded reading view.\n",
        "The API sends system instructions, conversation input, and tool definitions "
        "as separate fields. All are included below, with every other request setting. "
        "The entire system prompt is repeated for each case.\n",
        "**How the runs stopped:** all ten models issued a gameplay function call "
        "on their first response; none queried `check_neighbours`. The replay raised "
        "`DecisionCaptured` at gameplay dispatch, before executing the action or "
        "returning a tool result. No second model request was made. The production "
        "harness normally stops after one accepted gameplay action, but allows "
        "read-only tool calls beforehand.\n",
        "**What is recorded:** the full SDK-persisted response items, including "
        "returned reasoning, messages, tool calls, IDs and statuses. The label "
        "`partial_model_response` is the harness wrapper used when dispatch was "
        "interrupted; all ten wrapped provider responses have status `completed`. "
        "This export cannot supply reasoning the provider did not return, or an "
        "HTTP response envelope that was not saved. DeepSeek returned no reasoning "
        "text. Even stray output text is retained. Authentication headers were "
        "never recorded and are not part of these prompts.\n",
        "## Cases\n",
    ]
    parts.extend(
        f"- [Case {case['case']:02d}](#case-{case['case']:02d}) — "
        f"{case['model']}, {case['house']}, round {case['round']}"
        for case in cases
    )
    for case in cases:
        directory = ROOT / "results" / f"case-{case['case']:02d}"
        result = json.loads((directory / "result.json").read_text())
        requests = sorted(directory.glob("request-*.json"))
        assert len(requests) == result["requestCount"] == 1
        parts.extend([
            f"\n## Case {case['case']:02d}\n",
            f"Model: `{case['model']}`. House: **{case['house']}**. "
            f"Round: **{case['round']}**.\n",
            "### Full returned answer — reading view\n",
        ])
        text_items = list(response_text(result["responseItems"]))
        if not any(kind == "reasoning" for kind, _ in text_items):
            parts.append("No reasoning text was returned by the provider.\n")
        for kind, text in text_items:
            parts.extend([f"Returned {kind} text (verbatim):\n", fenced(text)])
        parts.extend([
            "Gameplay function calls:\n", json_block(result["replayOperations"]),
            "### Full recorded response items — unfiltered\n",
            json_block(result["responseItems"]),
        ])
        for number, path in enumerate(requests, 1):
            request = json.loads(path.read_text())
            settings = {key: value for key, value in request.items()
                        if key not in {"instructions", "tools", "input"}}
            assert {**settings, **{key: request[key] for key in ("instructions", "tools", "input")}} == request
            parts.extend([
                f"### Request {number}: full system instructions (verbatim)\n",
                fenced(request["instructions"], "markdown"),
                f"### Request {number}: complete tool definitions\n",
                json_block(request["tools"]),
                f"### Request {number}: complete ordered conversation input\n",
                "This includes historical reasoning/actions/tool results and the "
                "current user observation, in their original order. JSON string "
                "escapes here are part of the representation, not omissions.\n",
                json_block(request["input"]),
            ])
            content = request["input"][-1]["content"]
            prefix, observation = content.split("\n\n", 1)
            parts.extend([
                "### Current observation — expanded reading view\n",
                fenced(prefix), json_block(json.loads(observation)),
                f"### Request {number}: every other request field\n",
                json_block(settings),
                "### Remaining recorded result fields\n",
                json_block({key: value for key, value in result.items()
                            if key != "responseItems"}),
            ])
    output = ROOT / "full-prompts-and-answers.md"
    output.write_text("\n".join(parts) + "\n")
    content = output.read_text()
    assert len(re.findall(r"^## Case \d+$", content, re.MULTILINE)) == len(cases) == 10
    print(f"Exported {len(cases)} complete cases to {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
