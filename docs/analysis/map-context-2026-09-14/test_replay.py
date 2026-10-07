"""Offline controls for snapshot restoration and real multi-request map dispatch."""

import importlib.util
import json
from pathlib import Path

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location("map_replay", Path(__file__).with_name("replay.py"))
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)
CASES = json.loads((replay.BASE / "test-set.json").read_text())["cases"]


@pytest.fixture(autouse=True)
def offline_settings(monkeypatch):
    settings = replay.Settings().model_copy(update={"model_api_key": "offline-test-key"})
    monkeypatch.setattr(replay, "Settings", lambda: settings)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda c: str(c["case"]))
async def test_current_harness_accepts_each_verified_historical_state(case, tmp_path):
    data = replay.baseline.load_case(case)

    def respond(request):
        output = [i for i in json.loads(data["run"]["response_json"])
                  if i["type"] != "function_call_output"]
        return httpx.Response(200, json={
            "id": "offline-response", "object": "response", "created_at": 0,
            "status": "completed", "model": case["model"], "output": output,
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        })

    result = await replay.replay(data, tmp_path, transport=httpx.MockTransport(respond))
    assert result["error"] is None
    assert result["snapshotBoardVerified"] and result["inputVerified"] and result["wireToolsVerified"]
    assert result["requestCount"] == 1
    assert result["replayOperations"] == result["originalOperations"]
    request = json.loads((tmp_path / "request-01.json").read_text())
    assert request["instructions"].count("\n# Map\n") == 1
    observation = json.loads(request["input"][-1]["content"].split("\n\n", 1)[1])
    assert "map" not in observation and observation["mapVariant"] == "westeros"


@pytest.mark.asyncio
async def test_real_map_tool_executes_and_its_result_reaches_the_next_model_call(tmp_path):
    data = replay.baseline.load_case(CASES[0])
    calls = []

    def respond(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            output = [{"type": "function_call", "name": "check_neighbours",
                       "call_id": "map-test", "arguments": '{"area":"Castle Black"}'}]
        else:
            assert len(calls) == 2
            tool_output = next(item["output"] for item in body["input"]
                               if item.get("type") == "function_call_output"
                               and item.get("call_id") == "map-test")
            areas = {area["id"]: area for area in json.loads(tool_output)}
            assert set(areas) == {"winterfell", "karhold", "bay-of-ice", "the-shivering-sea"}
            assert areas["winterfell"]["castleLevel"] == 2
            assert areas["winterfell"]["owner"] == "stark"
            output = [i for i in json.loads(data["run"]["response_json"])
                      if i["type"] != "function_call_output"]
        return httpx.Response(200, json={
            "id": f"offline-response-{len(calls)}", "object": "response", "created_at": 0,
            "status": "completed", "model": data["case"]["model"], "output": output,
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        })

    result = await replay.replay(data, tmp_path, transport=httpx.MockTransport(respond))
    assert result["error"] is None
    assert result["requestCount"] == 2
    assert result["mapCalls"] == [{"name": "check_neighbours", "arguments": {"area": "Castle Black"}}]
    assert result["replayOperations"] == result["originalOperations"]
    assert not result["gameToolsExecuted"]
