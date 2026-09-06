from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Iterable, MutableSequence
from datetime import datetime, timezone
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any

import httpx
from agents import Agent, FunctionTool, ModelSettings, RunConfig, RunResult, function_tool
from pydantic import BaseModel, ConfigDict, Field
from pypdf import PdfReader


RULES_ORACLE_TOOL_NAME = "ask_rules_oracle"
RULES_ORACLE_DESCRIPTION = (
    "Ask a private rules specialist one focused question when a rule is unclear. "
    "The specialist reads the official rulebook and FAQ. This does not take your "
    "required game action, so you must still call one gameplay tool afterward."
)

# The Supply track on page 8 is artwork in the official PDF, so PDF text
# extraction does not capture its army-size values. Keep a transcription beside
# the extracted text that the rules oracle reads.
BASE_GAME_SUPPLY_LIMITS: dict[int, tuple[int, ...]] = {
    0: (2, 2),
    1: (3, 2),
    2: (3, 2, 2),
    3: (3, 2, 2, 2),
    4: (3, 3, 2, 2),
    5: (4, 3, 2, 2),
    6: (4, 3, 2, 2, 2),
}
SUPPLY_TRACK_TRANSCRIPTION = (
    "[Rules of Play, page 8, Supply track chart transcription]\n"
    "Each list gives the maximum unit count of every army a player may have "
    "at that Supply level:\n"
    + "\n".join(
        f"Supply {level}: {list(army_sizes)}"
        for level, army_sizes in BASE_GAME_SUPPLY_LIMITS.items()
    )
)


class RuleSectionId(str, Enum):
    OVERVIEW_SETUP_TERMS = "overview-setup-terms"
    ROUND_AND_WESTEROS = "round-and-westeros"
    SUPPLY_AND_MUSTERING = "supply-and-mustering"
    INFLUENCE_AND_BIDDING = "influence-and-bidding"
    PLANNING_AND_ORDERS = "planning-and-orders"
    ACTION_ORDERS_AND_VICTORY = "action-orders-and-victory"
    COMBAT_AND_SUPPORT = "combat-and-support"
    WILDLINGS = "wildlings"
    SHIP_TRANSPORT_CONTROL_POWER = "ship-transport-control-power"
    PORTS_GARRISONS_BOARD = "ports-garrisons-board"
    PLAYER_COUNTS_AND_TIDES = "player-counts-and-tides"
    FAQ_CORRECTIONS_AND_CARDS = "faq-corrections-and-cards"
    FAQ_MOVEMENT_SUPPLY_PORTS = "faq-movement-supply-ports"
    FAQ_EXPANSIONS = "faq-expansions"


class RuleSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    url: str
    sha256: str


class RuleSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: RuleSectionId
    title: str
    summary: str
    source_id: str
    pages: list[int]
    text: str


class RulebookData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format_version: int = 1
    generated_at: str
    sources: list[RuleSource]
    sections: list[RuleSection]


class RulesQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=3,
        max_length=1_200,
        description="A focused question about one game rule.",
    )


SOURCE_SPECS = {
    "rules": RuleSource(
        id="rules",
        title="A Game of Thrones: The Board Game Second Edition - Rules of Play",
        url=(
            "https://images-cdn.fantasyflightgames.com/ffg_content/"
            "agot-bg-2nd-ed/support/VA65_AGoT2_Rulebook_web.pdf"
        ),
        sha256="6063393641108ddf388d0621aa89ffdd973184d1dbc3be3710229a74004532e8",
    ),
    "faq": RuleSource(
        id="faq",
        title="A Game of Thrones: The Board Game Second Edition - Errata and FAQ 2.0",
        url=(
            "https://images-cdn.fantasyflightgames.com/filer_public/cf/06/"
            "cf06eb26-48e3-46b9-b57c-f053beb2518d/agotbg_faq_v2_forweb.pdf"
        ),
        sha256="bd53615d494b704b1586ff0d1b1d9f1dd6b8fea48828c3877adf06faf79c23ba",
    ),
}


SECTION_SPECS: list[tuple[RuleSectionId, str, str, str, list[int]]] = [
    (
        RuleSectionId.OVERVIEW_SETUP_TERMS,
        "Overview, setup, and important terms",
        "Objective, components, setup, turn order, units, areas, armies, and basic terms.",
        "rules",
        [2, 3, 4, 5, 6],
    ),
    (
        RuleSectionId.ROUND_AND_WESTEROS,
        "Game round and Westeros phase",
        "Round sequence, Westeros cards, wildling icons, and round progression.",
        "rules",
        [7],
    ),
    (
        RuleSectionId.SUPPLY_AND_MUSTERING,
        "Supply and mustering",
        "Army-size limits, supply adjustment, muster points, recruitment, and upgrades.",
        "rules",
        [8, 9],
    ),
    (
        RuleSectionId.INFLUENCE_AND_BIDDING,
        "Influence tracks, bidding, and dominance tokens",
        "Clash of Kings bids, tie decisions, turn order, special orders, and token powers.",
        "rules",
        [10, 11],
    ),
    (
        RuleSectionId.PLANNING_AND_ORDERS,
        "Planning and order tokens",
        "Order placement, order-token inventory, special-order limits, and order effects.",
        "rules",
        [12, 13, 22],
    ),
    (
        RuleSectionId.ACTION_ORDERS_AND_VICTORY,
        "Action phase, raid, march, consolidate power, and victory",
        "Action order, raid and march resolution, control tokens, power collection, and victory.",
        "rules",
        [14, 15, 16],
    ),
    (
        RuleSectionId.COMBAT_AND_SUPPORT,
        "Combat and support",
        "Support, strength, house cards, the blade, casualties, retreats, and routed units.",
        "rules",
        [17, 18, 19, 20, 21],
    ),
    (
        RuleSectionId.WILDLINGS,
        "Wildling attacks",
        "Wildling bids, victory and defeat, card effects, and threat-track adjustment.",
        "rules",
        [22, 23],
    ),
    (
        RuleSectionId.SHIP_TRANSPORT_CONTROL_POWER,
        "Ship transport, area control, and power tokens",
        "Coastal movement, transport chains, control tokens, and available power.",
        "rules",
        [23, 24],
    ),
    (
        RuleSectionId.PORTS_GARRISONS_BOARD,
        "Ports, garrisons, neutral forces, alliances, and board features",
        "Port rules, garrisons, neutral forces, rivers, islands, and hidden information.",
        "rules",
        [25, 26, 27],
    ),
    (
        RuleSectionId.PLAYER_COUNTS_AND_TIDES,
        "Fewer than six players and Tides of Battle",
        "Three- to five-player changes and the optional Tides of Battle module.",
        "rules",
        [28, 29],
    ),
    (
        RuleSectionId.FAQ_CORRECTIONS_AND_CARDS,
        "FAQ corrections and house cards",
        "Official rules corrections, current end-game ties, combat timing, and card rulings.",
        "faq",
        [1, 2, 3],
    ),
    (
        RuleSectionId.FAQ_MOVEMENT_SUPPLY_PORTS,
        "FAQ movement, supply, control, and ports",
        "Detailed answers for movement, supply, control, retreats, mustering, and ports.",
        "faq",
        [4, 5],
    ),
    (
        RuleSectionId.FAQ_EXPANSIONS,
        "FAQ expansion rules",
        "Clarifications for Feast for Crows and Mother of Dragons mechanics.",
        "faq",
        [6, 7],
    ),
]


class Rulebook:
    def __init__(self, data: RulebookData) -> None:
        self.data = data
        self._sections = {section.id: section for section in data.sections}

    @classmethod
    def load(cls, path: Path) -> Rulebook:
        return cls(RulebookData.model_validate_json(path.read_text()))

    @classmethod
    def load_optional(cls, path: Path) -> Rulebook | None:
        return cls.load(path) if path.is_file() else None

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "id": section.id.value,
                "title": section.title,
                "summary": section.summary,
                "source": section.source_id,
                "pages": section.pages,
            }
            for section in self.data.sections
        ]

    def read(self, section_ids: Iterable[RuleSectionId]) -> list[dict[str, Any]]:
        result = []
        for section_id in section_ids:
            section = self._sections[section_id]
            text = section.text
            if section_id is RuleSectionId.SUPPLY_AND_MUSTERING:
                text = f"{text.rstrip()}\n\n{SUPPLY_TRACK_TRANSCRIPTION}"
            result.append(
                {
                    "id": section.id.value,
                    "title": section.title,
                    "source": section.source_id,
                    "pages": section.pages,
                    "text": text,
                }
            )
        return result

    @property
    def cache_fingerprint(self) -> str:
        material = "|".join(
            [
                *(source.sha256 for source in self.data.sources),
                SUPPLY_TRACK_TRANSCRIPTION,
            ]
        )
        return hashlib.sha256(material.encode()).hexdigest()[:24]

    def build_oracle_tool(
        self,
        *,
        model: Any,
        model_settings: ModelSettings,
        interaction_sink: MutableSequence[dict[str, Any]],
        run_config: RunConfig,
    ) -> FunctionTool:
        section_reads: list[RuleSectionId] = []
        current_question = ""

        @function_tool
        async def read_rulebook_sections(
            section_ids: Annotated[
                list[RuleSectionId],
                Field(
                    min_length=1,
                    max_length=2,
                    description="One or two section IDs from the supplied catalog.",
                ),
            ],
        ) -> str:
            """Read exact text from one or two official rulebook sections."""

            section_reads.extend(section_ids)
            return json.dumps({"sections": self.read(section_ids)})

        oracle = Agent(
            name="Rules oracle",
            instructions=(
                "Answer only the player's rules question. First call "
                "read_rulebook_sections with the smallest useful set of sections. "
                "Use the official FAQ when it changes the base rulebook. Distinguish "
                "a printed rule from a server-specific behavior. If the supplied "
                "sections do not answer the question, say that you do not know. "
                "Give a concise answer and cite section titles and page numbers. Do "
                "not recommend a strategy or choose the player's game action."
            ),
            model=model,
            tools=[read_rulebook_sections],
            model_settings=model_settings,
        )

        def build_input(options: dict[str, Any]) -> str:
            nonlocal current_question
            params = options.get("params") or {}
            current_question = str(params.get("question") or "")
            section_reads.clear()
            return (
                "Player question:\n"
                f"{current_question}\n\n"
                "Rule section catalog:\n"
                + json.dumps(self.catalog(), separators=(",", ":"))
            )

        async def record_answer(result: RunResult) -> str:
            answer = str(result.final_output or "")
            response_items: list[dict[str, Any]] = []
            raw_usage: list[dict[str, Any]] = []
            interaction_usage = {
                "requests": 0,
                "inputTokens": 0,
                "outputTokens": 0,
                "totalTokens": 0,
            }
            for response in result.raw_responses:
                response_items.extend(_jsonable(item) for item in response.output)
                response_usage = response.usage
                interaction_usage["requests"] += response_usage.requests
                interaction_usage["inputTokens"] += response_usage.input_tokens
                interaction_usage["outputTokens"] += response_usage.output_tokens
                interaction_usage["totalTokens"] += response_usage.total_tokens
                if response.raw_usage is not None:
                    usage = _jsonable(response.raw_usage)
                else:
                    usage = {}
                usage["scope"] = "rules-oracle"
                usage["response_id"] = response.response_id
                raw_usage.append(usage)
            interaction_sink.append(
                {
                    "question": current_question,
                    "answer": answer,
                    "sectionIds": list(
                        dict.fromkeys(item.value for item in section_reads)
                    ),
                    "responseItems": response_items,
                    "rawUsage": raw_usage,
                    "usage": interaction_usage,
                }
            )
            return answer

        return oracle.as_tool(
            tool_name=RULES_ORACLE_TOOL_NAME,
            tool_description=RULES_ORACLE_DESCRIPTION,
            parameters=RulesQuestion,
            input_builder=build_input,
            custom_output_extractor=record_answer,
            max_turns=3,
            run_config=run_config,
        )


def prepare_rulebook(output_path: Path) -> RulebookData:
    source_bytes = {
        source.id: _download_source(source) for source in SOURCE_SPECS.values()
    }
    readers = {
        source_id: PdfReader(BytesIO(content))
        for source_id, content in source_bytes.items()
    }
    sections = []
    for section_id, title, summary, source_id, pages in SECTION_SPECS:
        reader = readers[source_id]
        if max(pages) > len(reader.pages):
            raise ValueError(f"Source {source_id!r} does not contain pages {pages}")
        text = "\n\n".join(
            f"[{SOURCE_SPECS[source_id].title}, page {page_number}]\n"
            + _extract_page(reader.pages[page_number - 1])
            for page_number in pages
        )
        sections.append(
            RuleSection(
                id=section_id,
                title=title,
                summary=summary,
                source_id=source_id,
                pages=pages,
                text=text,
            )
        )
    data = RulebookData(
        generated_at=datetime.now(timezone.utc).isoformat(),
        sources=list(SOURCE_SPECS.values()),
        sections=sections,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data.model_dump(mode="json"), indent=2) + "\n")
    return data


def _download_source(source: RuleSource) -> bytes:
    response = httpx.get(source.url, follow_redirects=True, timeout=60)
    response.raise_for_status()
    content = response.content
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != source.sha256:
        raise ValueError(
            f"Unexpected SHA-256 for {source.title}: {actual_hash}; "
            f"expected {source.sha256}"
        )
    return content


def _extract_page(page: Any) -> str:
    fragments: list[list[str]] = [[], []]
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)

    def collect(
        text: str,
        _current_matrix: list[float],
        text_matrix: list[float],
        _font: dict[str, Any] | None,
        _font_size: float,
    ) -> None:
        x, y = float(text_matrix[4]), float(text_matrix[5])
        if 30 < y < height - 30:
            fragments[0 if x < width / 2 else 1].append(text)

    page.extract_text(visitor_text=collect)
    return _normalize_text("".join(fragments[0]) + "\n" + "".join(fragments[1]))


def _normalize_text(text: str) -> str:
    text = text.replace("ɇ", "-").replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if not line or re.fullmatch(r"\d{1,2}", line):
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if line.casefold() == "a game of thrones":
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _jsonable(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return value
    return {"value": str(value)}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and extract the official game rules for the local oracle."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/rules.json"),
        help="Generated JSON file (default: data/rules.json).",
    )
    args = parser.parse_args()
    data = prepare_rulebook(args.output.resolve())
    print(
        f"Wrote {len(data.sections)} rule sections from "
        f"{len(data.sources)} official sources to {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()
