"""Offline controls: use recorded responses; never call a model provider."""

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location("historical_replay", Path(__file__).with_name("replay.py"))
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)
CASES = json.loads(Path(__file__).with_name("cases.json").read_text())["cases"]
CASES += json.loads(Path(__file__).with_name("added-candidates.json").read_text())["cases"]


@pytest.fixture(autouse=True)
def offline_settings(monkeypatch):
    monkeypatch.setattr(replay, "Settings", lambda: SimpleNamespace(
        model_api_key="offline-test-key", model_base_url="https://openrouter.ai/api/v1",
    ))


def recorded_transport(data, *, change_decision=False):
    def respond(request):
        output = [i for i in json.loads(data["run"]["response_json"]) if i["type"] != "function_call_output"]
        if change_decision:
            call = next(i for i in output if i["type"] == "function_call")
            arguments = json.loads(call["arguments"])
            arguments["moves"] = []
            call["arguments"] = json.dumps(arguments)
        return httpx.Response(200, json={
            "id": "offline-response", "object": "response", "created_at": 0,
            "status": "completed", "model": data["case"]["model"], "output": output,
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        })
    return httpx.MockTransport(respond)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda c: str(c["case"]))
async def test_original_response_reproduces_requested_operation(case, tmp_path):
    data = replay.load_case(case)
    result = await replay.replay(data, tmp_path, transport=recorded_transport(data))
    assert result["status"] == "same", result["error"]
    assert result["inputHashVerified"] and result["wireToolsVerified"]
    assert not result["gameToolsExecuted"]
    if case["case"] == 5:
        # GLM requested a move which the historical harness subsequently omitted.
        # A replay must compare the request with the request, not accepted args.
        assert result["replayOperations"][0]["arguments"]["moves"]
        assert result["historicalAcceptedAction"]["arguments"]["moves"] == []


@pytest.mark.asyncio
async def test_changed_model_decision_is_a_failed_equality_assertion(tmp_path):
    data = replay.load_case(CASES[0])
    result = await replay.replay(data, tmp_path, transport=recorded_transport(data, change_decision=True))
    assert result["status"] == "different"
    assert result["assertionFailure"]
    assert result["error"] is None
    assert result["inputHashVerified"] and result["wireToolsVerified"]


@pytest.mark.asyncio
async def test_corrupted_input_is_rejected_before_http_request(tmp_path):
    data = copy.deepcopy(replay.load_case(CASES[0]))
    data["inputs"][0]["content"][0]["text"] += " CORRUPTION"

    def no_request(request):
        pytest.fail("Corrupted input must never reach the model endpoint")

    result = await replay.replay(data, tmp_path, transport=httpx.MockTransport(no_request))
    assert result["status"] == "error"
    assert not result["wireToolsVerified"]
    assert "mismatch" in result["error"]


def test_selected_set_has_ten_verified_cases_and_explicit_exceptions():
    manifest = json.loads(Path(__file__).with_name("test-set.json").read_text())
    selected = manifest["cases"]
    assert len(selected) == len({c["run_id"] for c in selected}) == 10
    assert {c["case"] for c in selected if c["baseline_replay"]["status"] == "different"} == {1, 3}
    for case in selected:
        replay.load_case(case)
        result_path = Path(__file__).parent / case["baseline_replay"]["result_file"]
        result = json.loads(result_path.read_text())
        assert result["inputHashVerified"] and result["wireToolsVerified"]
        if case["case"] not in {1, 3}:
            assert result["status"] == "same"
            assert result["originalOperations"] == result["replayOperations"]


@pytest.mark.asyncio
async def test_rules_variant_changes_only_instructions_and_prompt_cache_key(tmp_path):
    data = replay.load_case(CASES[0])
    baseline = tmp_path / "baseline"
    variant = tmp_path / "rules"
    baseline.mkdir()
    variant.mkdir()
    for directory, full_rules in [(baseline, False), (variant, True)]:
        result = await replay.replay(
            data, directory, transport=recorded_transport(data), full_rules=full_rules,
        )
        assert result["status"] == "same", result["error"]
        assert result["inputHashVerified"] and result["wireToolsVerified"]
    original_request = json.loads((baseline / "request.json").read_text())
    rules_request = json.loads((variant / "request.json").read_text())
    original_prompt = original_request.pop("instructions")
    rules_prompt = rules_request.pop("instructions")
    assert original_request.pop("prompt_cache_key") != rules_request.pop("prompt_cache_key")
    assert original_request == rules_request
    assert rules_prompt.startswith(original_prompt.rstrip() + "\n\n# Rules\n")
    assert rules_prompt.count("\n# Rules\n") == 1
    assert "## FAQ: Mother of Dragons, continued" in rules_prompt
