import re

from raven_harness.config import PROJECT_ROOT
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
