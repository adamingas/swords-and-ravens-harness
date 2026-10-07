"""Export saved wire prompts and unfiltered provider-returned answers."""

import argparse
import json
from pathlib import Path
import re


def block(value, language="json"):
    content = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
    width = max(3, max((len(x) + 1 for x in re.findall(r"`+", content)), default=0))
    fence = "`" * width
    return f"{fence}{language}\n{content}\n{fence}\n"


def returned_text(items):
    for item in items:
        if item.get("type") == "partial_model_response":
            yield from returned_text(item["output"])
        else:
            for content in item.get("content", []):
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    yield item["type"], content["text"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    parts = [
        "# Full prompts and returned answers\n",
        "Actual request bodies and complete recorded response items, including all reasoning "
        "the provider returned. JSON whitespace is expanded for reading. Authentication headers "
        "were never recorded. No hidden reasoning is inferred.\n",
        "These experiments call the production StrategicHarness.prepare_turn and run_turn. "
        "Gameplay commands are captured after local validation and before server transmission. "
        "No historical game was mutated and server acceptance is not simulated.\n",
    ]
    for directory in sorted(args.results.glob("case-*")):
        result = json.loads((directory / "result.json").read_text())
        parts.append(f"## Case {result['case']} — {result['house']}, round {result['round']}\n")
        parts.append(f"Model: {result['model']}.\n")
        for kind, content in returned_text(result["responseItems"]):
            parts.extend([f"### Returned {kind} text\n", block(content, "text")])
        parts.extend(["### Complete recorded result\n", block(result)])
        for number, path in enumerate(sorted(directory.glob("request-*.json")), 1):
            request = json.loads(path.read_text())
            parts.extend([
                f"### Request {number}: system instructions\n", block(request["instructions"], "markdown"),
                f"### Request {number}: exact ordered conversation input\n", block(request["input"]),
                f"### Request {number}: tools, final schema and every other request field\n",
                block({key: value for key, value in request.items() if key not in {"instructions", "input"}}),
            ])
    target = args.results / "full-prompts-and-answers.md"
    target.write_text("\n".join(parts))
    print(target)


if __name__ == "__main__":
    main()
