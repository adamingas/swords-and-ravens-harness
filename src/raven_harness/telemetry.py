from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


@dataclass
class Telemetry:
    """Optional OTLP export for coarse agent-decision spans."""

    tracer: trace.Tracer
    provider: TracerProvider | None = None

    @classmethod
    def create(
        cls, *, endpoint: str, service_name: str = "raven-harness"
    ) -> Telemetry:
        endpoint = endpoint.strip()
        if not endpoint:
            return cls(trace.get_tracer(service_name))

        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": service_name,
                    "openinference.project.name": service_name,
                }
            )
        )
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        )
        return cls(provider.get_tracer(service_name), provider)

    def shutdown(self) -> None:
        if self.provider is not None:
            self.provider.shutdown()


def provider_cost(raw_usage: list[dict[str, Any]] | None) -> float:
    return sum(float(item.get("cost") or 0) for item in raw_usage or [])
