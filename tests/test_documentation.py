import json
import re
from collections import Counter

from raven_harness.config import PROJECT_ROOT, Settings
from raven_harness.harness.actions import _TOOL_CATALOG
from raven_harness.harness.protocol_tools import GAMEPLAY_TOOLS
from raven_harness.harness.strategic import MEMORY_TOOLS
from raven_harness.rulebook import RULES_ORACLE_TOOL_NAME


def test_harness_guide_lists_exact_model_visible_tool_catalog() -> None:
    guide = (PROJECT_ROOT / "docs" / "HARNESS_GUIDE.md").read_text()
    documented = set(re.findall(r"^\| `?([a-z][a-z0-9_]*)\(", guide, re.MULTILINE))
    documented.update(
        re.findall(r"^### ([a-z][a-z0-9_]*)\(", guide, re.MULTILINE)
    )
    registered = {
        *_TOOL_CATALOG,
        *(tool.name for tool in GAMEPLAY_TOOLS),
        *(tool.name for tool in MEMORY_TOOLS),
        RULES_ORACLE_TOOL_NAME,
    }

    assert documented == registered


def test_rules_oracle_evidence_contains_the_sanitized_source_rows() -> None:
    evidence = json.loads(
        (PROJECT_ROOT / "docs" / "rules-oracle-evidence.json").read_text()
    )

    assert evidence["schemaVersion"] == 1
    rows = evidence["preOraclePlanningFailures"]
    assert len(rows) == 7
    assert len({row["runId"] for row in rows}) == 7
    assert Counter(row["ruleFailure"] for row in rows) == {
        "active Westeros restrictions prohibit order values defense_plus_two": 3,
        "assignments may contain at most 1 starred orders": 2,
        "order defense may be used at most 2 times": 2,
    }
    assert {row["player"] for row in rows} == {"player-a", "player-b"}
    assert all(row["phase"] == "place-orders" for row in rows)
    assert evidence["supplyChartOracleTest"]["sectionIds"] == [
        "supply-and-mustering",
        "faq-movement-supply-ports",
    ]


def test_harness_guide_lists_the_default_provider_order() -> None:
    guide = (PROJECT_ROOT / "docs" / "HARNESS_GUIDE.md").read_text()
    configured = Settings.model_fields["openrouter_provider_order"].default.split(",")
    display = {
        "reka": "Reka",
        "cloudflare": "Cloudflare",
        "coreweave": "CoreWeave",
        "fireworks": "Fireworks",
        "deepinfra": "DeepInfra",
        "together": "Together",
    }
    names = [display[name] for name in configured]
    sentence = f"defaults to {', '.join(names[:-1])}, and {names[-1]}."

    assert sentence in guide
