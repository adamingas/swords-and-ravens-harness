from types import SimpleNamespace
from typing import Any
import pytest
from agents import ModelSettings
from raven_harness.models.tracing import _UsageCapturingResponsesModel
from raven_harness.models.results import _partial_result


class TerminalUsage:
    requests = 1
    input_tokens = 100
    output_tokens = 16
    total_tokens = 116

    def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
        return {"input_tokens": 100, "output_tokens": 16, "total_tokens": 116}


@pytest.mark.asyncio
async def test_failed_response_preserves_provider_error_details() -> None:
    async def create(**_kwargs: Any) -> Any:
        return SimpleNamespace(
            id="failed-1",
            status="failed",
            model="test-model",
            provider="Example Provider",
            service_tier="priority",
            _request_id="request-1",
            usage=TerminalUsage(),
            incomplete_details=None,
            error={"code": "server_error", "message": "Generation failed"},
            output=[],
        )

    responses = []
    model = _UsageCapturingResponsesModel(
        model="test-model",
        openai_client=SimpleNamespace(responses=SimpleNamespace(create=create)),
        response_sink=responses,
    )
    with pytest.raises(RuntimeError, match="Generation failed"):
        await model._fetch_response(
            None, [], ModelSettings(), [], None, [], stream=False
        )
    result = _partial_result([], {}, provider_responses=responses)
    assert result.response_items[0]["providerError"]["code"] == "server_error"
