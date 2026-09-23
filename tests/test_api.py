import pytest
from pydantic import ValidationError

from raven_harness.schemas import LobbySetupRequest


def test_lobby_setup_request_rejects_unsupported_variants() -> None:
    assert LobbySetupRequest(playerCount=3).player_count == 3

    for field, value in (
        ("setupId", "mother-of-dragons"),
        ("playerCount", 5),
        ("vassals", True),
    ):
        with pytest.raises(ValidationError):
            LobbySetupRequest.model_validate({field: value})
