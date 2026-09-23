"""Real app, SDK, SQLite and game server; only the paid model boundary is scripted."""

import asyncio
import hashlib
import json
import socket
from collections import defaultdict

import httpx
import pytest

from raven_harness.app import create_app
from raven_harness.config import Settings
from raven_harness.evaluation import (
    GAME_SERVER_DIR,
    _start_game_server,
    _stop_process,
    _wait_for_server,
)
from raven_harness.harness.configure import create_game_harness


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def fingerprint(text):
    return hashlib.sha256(text.encode()).hexdigest()


def choose_action(schema):
    """Consolidate in planning, skip the raven, then collect power."""
    properties = schema["properties"]
    if "decision" in properties:
        branches = properties["decision"]["anyOf"]
        branch = next(
            branch
            for branch in branches
            if branch["properties"]["action"]["enum"][0]
            in {
                "skip_raven_order_replacement",
                "resolve_consolidate_power",
                "skip_mustering",
            }
        )
        return {"decision": choose_action(branch)}
    if "assignments" in properties:
        regions = properties["assignments"]["items"]["properties"]["region_id"]["enum"]
        return {
            "assignments": [
                {
                    "region_id": region,
                    "preferred_order": "consolidate_power",
                    "starred_preference": "avoid",
                    "priority": 1,
                }
                for region in regions
            ]
        }
    answer = {}
    for key, field in properties.items():
        if key == "strategic_handoff":
            continue
        assert "enum" in field, (key, field)
        answer[key] = (
            "gain_power_tokens"
            if "gain_power_tokens" in field["enum"]
            else field["enum"][0]
        )
    return answer


class ScriptedProvider:
    def __init__(self, mode):
        self.mode = mode
        self.requests = defaultdict(list)
        self.previous_observations = {}
        self.plans = {}
        self.previous_states = {}
        self.fail_agent = None
        self.failed_run = None
        self.errors = []

    def respond(self, request):
        try:
            return self._respond(request)
        except Exception as error:
            self.errors.append(repr(error))
            raise

    def _respond(self, request):
        body = json.loads(request.content)
        agent_id, run_id = body["metadata"]["agent_id"], body["metadata"]["run_id"]
        requests = self.requests[run_id]
        requests.append(body)
        step = len(requests)
        assert step <= (5 if self.mode == "two-stage" else 4)
        initial = body["input"][0]["content"]
        observation = json.loads(
            initial.split("Current observation:\n")[1].split("\n\nCurrent decision:")[0]
        )
        assert body["max_output_tokens"] == 1024
        if step == 1:
            assert len(body["input"]) == 1
            assert "exploration-only-marker" not in initial
            assert observation["strategicMemory"]["modelPlan"] == self.plans.get(
                agent_id, ""
            )
            for other_id, plan in self.plans.items():
                if other_id != agent_id:
                    assert plan not in initial
            assert observation["game"]["stateId"]
        else:
            results = {
                item["call_id"].rsplit("-", 1)[1]: json.loads(item["output"])
                for item in body["input"]
                if item.get("type") == "function_call_output"
            }
            assert "castle-black" in {area["id"] for area in results["map"]}
            if step > 2:
                assert results["remember"]["pending"] is True
            if step > 3:
                recalled = results["recall"]
                previous = self.previous_states.get(agent_id)
                assert recalled["found"] == (previous is not None)
                if previous:
                    assert recalled["stateId"] == previous
                    assert (
                        recalled["observation"]["you"]["houseId"]
                        == observation["you"]["houseId"]
                    )
                    assert (
                        recalled["observation"]["board"]
                        == self.previous_observations[agent_id]["board"]
                    )
        if step <= 3:
            name, arguments, suffix = [
                ("check_neighbours", {"area": "Winterfell"}, "map"),
                (
                    "remember_strategy",
                    {"note": f"pending-private-plan-{agent_id}"},
                    "remember",
                ),
                ("recall_game_state", {"turns_ago": 1}, "recall"),
            ][step - 1]
            assert name in {tool["name"] for tool in body["tools"]}
            output = [
                {
                    "type": "function_call",
                    "name": name,
                    "call_id": f"{run_id}-{suffix}",
                    "arguments": json.dumps(arguments),
                }
            ]
        else:
            if self.fail_agent == agent_id:
                self.fail_agent = None
                self.failed_run = run_id
                return httpx.Response(
                    503, json={"error": {"message": "capacity unavailable"}}
                )
            schema = body.get("text", {}).get("format", {}).get("schema")
            if schema:
                if self.mode == "two-stage":
                    assert body.get("tools", []) == []
                    assert any(
                        "exploration-only-marker" in str(item) for item in body["input"]
                    )
                answer = {
                    **choose_action(schema),
                    "strategic_handoff": f"private-plan-{agent_id}-{run_id}",
                }
                text = json.dumps(answer)
            else:
                assert self.mode == "two-stage" and step == 4
                text = "exploration-only-marker: collect power this round."
            output = [
                {
                    "type": "message",
                    "id": f"message-{step}",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {"type": "output_text", "text": text, "annotations": []}
                    ],
                }
            ]
        return httpx.Response(
            200,
            headers={"x-request-id": f"request-{run_id}-{step}"},
            json={
                "id": f"response-{run_id}-{step}",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "scripted-model",
                "provider": "scripted-provider",
                "output": output,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "total_tokens": 120,
                    "input_tokens_details": {"cached_tokens": 40},
                    "cost": 0.001,
                },
            },
        )

    def verify_trace(self, trace):
        requests = self.requests[trace["id"]]
        failed = trace["id"] == self.failed_run
        completed = len(requests) - int(failed)
        assert trace["status"] == ("failed" if failed else "completed")
        assert trace["usage"]["requests"] == completed
        assert trace["usage"]["totalTokens"] == completed * 120
        assert len(trace["rawUsage"]) == completed
        assert sum(item["cost"] for item in trace["rawUsage"]) == pytest.approx(
            completed * 0.001
        )
        assert all(
            item["response_provider"] == "scripted-provider"
            for item in trace["rawUsage"]
        )
        assert all(
            item["input_tokens_details"]["cached_tokens"] == 40
            for item in trace["rawUsage"]
        )
        manifest = trace["contextManifest"]
        assert manifest["currentInputSha256"] == fingerprint(
            requests[0]["input"][0]["content"]
        )
        assert len(manifest["modelRequestInputs"]) == len(requests)
        for recorded, request in zip(
            manifest["modelRequestInputs"], requests, strict=True
        ):
            assert recorded["inputSha256"] == fingerprint(encoded(request["input"]))
            assert recorded["instructionsSha256"] == fingerprint(
                request["instructions"]
            )
        if not failed:
            assert (
                manifest["actionOutputSchema"]
                == requests[-1]["text"]["format"]["schema"]
            )
            outputs = [
                i for i in trace["response"] if i.get("type") == "function_call_output"
            ]
            assert len(outputs) == 3
            assert all(trace["id"] in item["call_id"] for item in outputs)


@pytest.mark.parametrize("mode", ["structured", "two-stage"])
async def test_gameplay_survives_turns_restart_and_failed_attempt(tmp_path, mode):
    assert (GAME_SERVER_DIR / "node_modules/.bin/ts-node").is_file(), (
        "Install game-server dependencies to run E2E tests"
    )
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    provider = ScriptedProvider(mode)
    settings = Settings(
        database_path=tmp_path / "game.db",
        rules_path=tmp_path / "no-oracle.json",
        openai_api_key="test",
        openrouter_token="",
        openai_base_url="https://model.test/v1",
        otel_exporter_otlp_traces_endpoint="",
        harness_mode=mode,
        harness_max_turns=8,
        model_max_output_tokens=1024,
        _env_file=None,
    )

    def factory(store):
        harness = create_game_harness(settings, store)
        harness.provider.client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(provider.respond)
        )
        return harness

    async def call(client, path, payload=None):
        response = await client.post(path, json=payload or {})
        assert response.is_success, (response.text, provider.errors)
        return response.json()

    async def run_decision(client, app, agent_id):
        result = await call(client, f"/api/agents/{agent_id}/run")
        trace = (
            await client.get(f"/api/agents/{agent_id}/runs/{result['runId']}")
        ).json()["run"]
        provider.verify_trace(trace)
        plan = f"private-plan-{agent_id}-{trace['id']}"
        memory = app.state.store.get_strategic_memory(agent_id)
        assert memory["modelPlan"] == plan
        assert (
            memory["situationAssessment"]
            and memory["decisionJournal"]
            and memory["commitments"]
        )
        assert trace["observation"]["game"]["stateId"] != provider.previous_states.get(
            agent_id
        )
        provider.plans[agent_id] = plan
        provider.previous_states[agent_id] = trace["observation"]["game"]["stateId"]
        provider.previous_observations[agent_id] = trace["observation"]
        return trace

    with (tmp_path / "server.log").open("wb") as log:
        process = await _start_game_server(
            game_path=tmp_path / "game.json",
            port=port,
            max_rounds=2,
            random_seed=1,
            log=log,
        )
        try:
            await _wait_for_server(process, port, timeout=20)
            app = create_app(settings, harness_factory=factory)
            async with (
                app.router.lifespan_context(app),
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://harness.test",
                ) as client,
            ):
                ids = []
                for index, house in enumerate(["baratheon", "lannister", "stark"], 1):
                    created = await call(
                        client,
                        "/api/agents",
                        {
                            "name": house,
                            "model": "scripted-model",
                            "userId": str(index),
                            "authToken": str(index),
                            "gameId": "1",
                            "gameServerUrl": f"ws://127.0.0.1:{port}",
                        },
                    )
                    ids.append(created["agent"]["id"])
                    assert "authToken" not in created["agent"]
                    await call(client, f"/api/agents/{ids[-1]}/start")
                await call(
                    client,
                    f"/api/agents/{ids[0]}/lobby/setup",
                    {"playerCount": 3, "pbem": True},
                )
                for agent_id, house in zip(
                    ids, ["baratheon", "lannister", "stark"], strict=True
                ):
                    await call(
                        client,
                        f"/api/agents/{agent_id}/lobby/house",
                        {"houseId": house},
                    )
                await call(client, f"/api/agents/{ids[0]}/lobby/launch")
                async with asyncio.timeout(15):
                    while True:
                        board = (await client.get("/api/dashboard")).json()["agents"]
                        if all(item["stateStatus"]["actionable"] for item in board):
                            break
                        await asyncio.sleep(0.05)
                # Simultaneous planning exercises isolated memory and SDK agents.
                first = await asyncio.gather(
                    *(run_decision(client, app, agent_id) for agent_id in ids)
                )
                assert all(trace["tool"] == "submit_orders" for trace in first)
                saved_memories = {
                    agent_id: app.state.store.get_strategic_memory(agent_id)
                    for agent_id in ids
                }

            # A new application, store and harness must recover the plans, not SDK transcripts.
            app = create_app(settings, harness_factory=factory)
            async with (
                app.router.lifespan_context(app),
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://harness.test",
                ) as client,
            ):
                for agent_id in ids:
                    assert (
                        app.state.store.get_strategic_memory(agent_id)
                        == saved_memories[agent_id]
                    )
                    await call(client, f"/api/agents/{agent_id}/start")
                finished = set()
                async with asyncio.timeout(25):
                    while len(finished) != 3:
                        board = (await client.get("/api/dashboard")).json()["agents"]
                        for item in board:
                            if not item["stateStatus"]["actionable"]:
                                continue
                            agent_id = item["agent"]["id"]
                            if provider.failed_run is None:
                                provider.fail_agent = agent_id
                                before = app.state.store.get_strategic_memory(agent_id)
                                failed = await client.post(
                                    f"/api/agents/{agent_id}/run"
                                )
                                assert failed.status_code == 400, failed.text
                                assert (
                                    app.state.store.get_strategic_memory(agent_id)
                                    == before
                                )
                                trace = (
                                    await client.get(
                                        f"/api/agents/{agent_id}/runs/{provider.failed_run}"
                                    )
                                ).json()["run"]
                                provider.verify_trace(trace)
                                assert trace["tool"] is None
                                retry = await run_decision(client, app, agent_id)
                                assert (
                                    retry["observation"]["game"]["stateId"]
                                    == trace["observation"]["game"]["stateId"]
                                )
                                assert (
                                    "capacity unavailable"
                                    in retry["observation"]["previousAttemptError"]
                                )
                            else:
                                await run_decision(client, app, agent_id)
                            finished.add(agent_id)
                        await asyncio.sleep(0.05)
                assert provider.failed_run
                for agent_id in ids:
                    events = (
                        await client.get(f"/api/agents/{agent_id}/events")
                    ).json()["events"]
                    kinds = {event["kind"] for event in events}
                    assert {
                        "model-request-started",
                        "model-request-completed",
                        "model-tool-started",
                        "model-tool-completed",
                    } <= kinds
                assert len(provider.requests) >= 7
        finally:
            await _stop_process(process)
