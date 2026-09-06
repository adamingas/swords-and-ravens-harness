from raven_harness.errors import is_permanent_provider_error, safe_error_text


def test_safe_error_text_redacts_provider_credentials_and_key_urls() -> None:
    error = RuntimeError(
        "HTTP 403 key=key-secret-value "
        "https://provider.test/settings/keys/account-key-id?token=query-secret "
        "Authorization: Bearer opaque-header-value "
        "{'api_key': 'opaque-dict-value'} sk-abcdefghijklmnop"
    )

    message = safe_error_text(error)

    assert "key-secret-value" not in message
    assert "account-key-id" not in message
    assert "query-secret" not in message
    assert "opaque-header-value" not in message
    assert "opaque-dict-value" not in message
    assert "sk-abcdefghijklmnop" not in message
    assert message.count("[redacted]") >= 4


def test_permanent_provider_error_classification_excludes_transient_limits() -> None:
    assert is_permanent_provider_error(RuntimeError("spending limit exhausted"))
    assert is_permanent_provider_error(RuntimeError("invalid API key"))
    assert not is_permanent_provider_error(RuntimeError("HTTP 429 rate limit"))
    assert not is_permanent_provider_error(RuntimeError("connection timed out"))

    class PolicyError(RuntimeError):
        status_code = 403

    assert not is_permanent_provider_error(PolicyError("provider policy rejection"))
