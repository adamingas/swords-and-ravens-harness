"""Regression probes for experimental briefing facts, privacy and continuity."""

import copy
import json
from pathlib import Path
import subprocess

import pytest

from raven_harness.harness.context_experiments import continuity, render, situation

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    c["key"]: c
    for c in json.loads((ROOT / "tests/fixtures/context_replay.json").read_text())
}


def test_briefing_disambiguates_consecutive_battles_and_unknown_cards():
    case = CASES["D120"]
    text = situation(case["observation"], case["engine"])
    assert "lannister attacks baratheon at harrenhal. You are defending" in text
    assert "wounded; strength 0" in text
    assert "unrevealed/unresolved" in text
    assert "UNKNOWN, not a zero-strength play" in text
    assert "Declining it earlier does not spend it" in text


def test_blade_decision_includes_kevan_modified_army_strength():
    case = CASES["D154"]
    text = situation(case["observation"], case["engine"])
    assert "army 2 + order 1 + confirmed support 0" in text
    assert "current visible total 4" in text
    assert "current visible total 3" in text
    assert "Tied totals go to baratheon" in text


def test_receipt_overrides_hallucinated_mustering_without_rewriting_strategy():
    case = copy.deepcopy(CASES["D110"])
    original = copy.deepcopy(case)
    text = continuity(case["observation"], case["previous"])
    assert '"omitted_supply_unsafe_recruitments":1' in text
    assert "omitted recruitments were NOT created" in text
    assert "not proof your action caused every change" in text
    assert case == original
    assert "The Reach" in case["observation"]["strategicMemory"]["modelPlan"]


def test_failed_action_is_not_reported_as_accepted_and_other_house_is_rejected():
    case = copy.deepcopy(CASES["D110"])
    case["previous"]["status"] = "failed"
    assert "no accepted action is established" in continuity(
        case["observation"], case["previous"]
    )
    case["previous"]["observation"]["you"]["houseId"] = "stark"
    with pytest.raises(AssertionError, match="House-private"):
        continuity(case["observation"], case["previous"])


def test_compact_context_keeps_critical_facts_and_exploration_directory():
    case = CASES["D160"]
    text = render("progressive", case["observation"], case["engine"], case["previous"])
    assert "lannister has 4 scoring areas TOTAL, including 3 strongholds" in text
    assert "0 rounds after this one" in text
    assert "inspect_state" in text and "support_eligibility" in text
    assert '"pendingDecision"' in text
    assert len(text) < len(
        render("baseline", case["observation"], case["engine"], case["previous"])
    )


def test_tyrion_replacement_is_not_a_discard_or_draw():
    case = CASES["D150"]
    text = situation(case["observation"], case["engine"])
    assert "REPLACEMENT card that will fight this battle" in text


def test_rendering_does_not_mutate_observation():
    for case in CASES.values():
        original = copy.deepcopy(case)
        for policy in ("baseline", "briefing", "continuity", "progressive", "verified"):
            render(policy, case["observation"], case["engine"], case["previous"])
        assert case == original


def test_engine_projection_matches_audited_combat_and_does_not_reveal_cards():
    server = ROOT / "swords-and-ravens/agot-bg-game-server"
    ts_node = server / "node_modules/.bin/ts-node"
    if not ts_node.exists():
        pytest.skip("Requires pinned upstream server dependencies")
    inputs = [copy.deepcopy(CASES[k]) for k in ("D116", "D120", "D154")]
    # The cards held in hands are public; none may be reported as a selected
    # opposing card before the player snapshot reveals the choice.
    result = subprocess.run(
        [
            str(ts_node),
            "--transpile-only",
            "--project",
            str(server / "tsconfig.json"),
            str(ROOT / "scripts/context_experiment/engine_context.ts"),
        ],
        cwd=server,
        input=json.dumps(inputs),
        text=True,
        capture_output=True,
        check=True,
    )
    actual = {c["key"]: c for c in json.loads(result.stdout)}
    for key in actual:
        assert actual[key] == CASES[key]["engine"]
    combat = actual["D116"]["combat"]
    assert [s["support"] for s in combat["sides"]] == [0, 4]
    assert all(s["card"] is None for s in combat["sides"])
    assert actual["D120"]["combat"]["sides"][1]["army"] == 0
    assert [s["total"] for s in actual["D154"]["combat"]["sides"]] == [4, 3]
