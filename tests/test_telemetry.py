from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from fastapi.testclient import TestClient
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)

from raven_harness.app import create_app
from raven_harness.config import Settings
from raven_harness.schemas import AgentCreate
from raven_harness.telemetry import Telemetry, provider_cost


class NoopRunner:
    rules_oracle_available = False

    async def run_once(self, **_kwargs):
        raise AssertionError("the telemetry wiring test must not call a model")

    async def shutdown(self) -> None:
        pass

    async def clear_session(self, _agent_id: str) -> None:
        pass


def test_telemetry_is_optional_and_provider_cost_is_aggregated() -> None:
    telemetry = Telemetry.create(endpoint="")

    assert provider_cost([{"cost": 0.25}, {"cost": 0.75}, {}]) == 1.0
    telemetry.shutdown()


def test_application_lifespan_exports_and_flushes_otlp_http_protobuf(
    tmp_path, monkeypatch,
) -> None:
    received: list[dict[str, object]] = []

    class Collector(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            received.append(
                {
                    "path": self.path,
                    "contentType": self.headers.get("Content-Type"),
                    "body": self.rfile.read(length),
                }
            )
            self.send_response(200)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Collector)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    settings = Settings(
        database_path=tmp_path / "telemetry.db",
        openrouter_token="",
        openai_api_key="",
        otel_exporter_otlp_traces_endpoint=(
            f"http://127.0.0.1:{server.server_port}/v1/traces"
        ),
        otel_service_name="raven-lifespan-test",
        _env_file=None,
    )
    app = create_app(settings, runner=NoopRunner())
    try:
        with TestClient(app) as client:
            assert client.get("/api/health").json()[
                "telemetryExportConfigured"
            ] is True
            agent = client.app.state.store.create_agent(
                AgentCreate(
                    name="Telemetry Wolf",
                    model=settings.model_id,
                    user_id="1",
                    auth_token="test-token",
                )
            )

            async def completed_run(agent_id: str) -> dict[str, object]:
                assert agent_id == agent.id
                return {
                    "runId": "production-path-run",
                    "decision": {
                        "name": "choose_house",
                        "usage": {
                            "inputTokens": 10,
                            "outputTokens": 2,
                            "totalTokens": 12,
                        },
                    },
                    "result": {"sentMessageTypes": ["choose-house"]},
                }

            monkeypatch.setattr(
                client.app.state.manager, "_run_once", completed_run
            )
            response = client.post(f"/api/agents/{agent.id}/run")
            assert response.status_code == 200
            assert response.json()["runId"] == "production-path-run"
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)

    assert len(received) == 1
    assert received[0]["path"] == "/v1/traces"
    assert received[0]["contentType"] == "application/x-protobuf"
    assert received[0]["body"]
    export = ExportTraceServiceRequest.FromString(received[0]["body"])
    resource_spans = export.resource_spans
    assert len(resource_spans) == 1
    resource_attributes = {
        attribute.key: attribute.value.string_value
        for attribute in resource_spans[0].resource.attributes
    }
    assert resource_attributes["service.name"] == "raven-lifespan-test"
    assert resource_attributes["openinference.project.name"] == (
        "raven-lifespan-test"
    )
    spans = [
        span
        for scope in resource_spans[0].scope_spans
        for span in scope.spans
    ]
    assert [span.name for span in spans] == ["raven.agent.decision"]
    span_attributes = {
        attribute.key: attribute.value for attribute in spans[0].attributes
    }
    assert span_attributes["raven.action"].string_value == "choose_house"
    assert span_attributes["raven.run.id"].string_value == "production-path-run"
    assert span_attributes["gen_ai.usage.input_tokens"].int_value == 10
    assert span_attributes["gen_ai.usage.output_tokens"].int_value == 2
