from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from raven_harness.telemetry import Telemetry, provider_cost


def test_telemetry_is_optional_and_provider_cost_is_aggregated() -> None:
    telemetry = Telemetry.create(endpoint="")

    assert telemetry.enabled is False
    assert provider_cost([{"cost": 0.25}, {"cost": 0.75}, {}]) == 1.0
    telemetry.shutdown()


def test_telemetry_exports_otlp_http_protobuf() -> None:
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
    telemetry = Telemetry.create(
        endpoint=f"http://127.0.0.1:{server.server_port}/v1/traces"
    )
    try:
        with telemetry.tracer.start_as_current_span("test-decision") as span:
            span.set_attribute("raven.action", "choose_house")
        telemetry.shutdown()
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)

    assert len(received) == 1
    assert received[0]["path"] == "/v1/traces"
    assert received[0]["contentType"] == "application/x-protobuf"
    assert received[0]["body"]
