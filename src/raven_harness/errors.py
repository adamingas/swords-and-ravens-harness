from __future__ import annotations

import re
from typing import Any


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)([\"']?\b(?:api[_-]?key|auth(?:orization|_token)?|password|secret|"
    r"access[_-]?token)\b[\"']?\s*[:=]\s*[\"']?)(?:bearer\s+)?"
    r"[^\s,;&}\]\"']+"
)
_SECRET_QUERY = re.compile(
    r"(?i)([?&](?:api[_-]?key|key|token|auth|secret|password)=)[^&#\s]+"
)
_KEY_PATH = re.compile(r"(?i)(/(?:keys?|tokens?|credentials?)/)[^/?#\s)\]}]+")
_URL_USERINFO = re.compile(r"(https?://)[^/\s:@]+:[^@\s/]+@", re.IGNORECASE)
_BEARER_VALUE = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=-]+")
_SECRET_TOKEN = re.compile(r"\b(?:sk|key|token)-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE)
MAX_SAFE_ERROR_CHARACTERS = 2_000


def safe_error_text(error: BaseException | Any) -> str:
    """Return useful error text without provider credentials or key identifiers."""

    text = str(error)
    text = _URL_USERINFO.sub(r"\1[redacted]@", text)
    text = _SECRET_QUERY.sub(r"\1[redacted]", text)
    text = _KEY_PATH.sub(r"\1[redacted]", text)
    text = _SECRET_ASSIGNMENT.sub(r"\1[redacted]", text)
    text = _BEARER_VALUE.sub(r"\1[redacted]", text)
    text = _SECRET_TOKEN.sub("[redacted]", text)
    if len(text) > MAX_SAFE_ERROR_CHARACTERS:
        text = text[:MAX_SAFE_ERROR_CHARACTERS] + "… [truncated]"
    return text


def is_permanent_provider_error(error: BaseException | Any) -> bool:
    """Identify account/auth failures that retries cannot repair."""

    status_code = getattr(error, "status_code", None)
    if status_code in {401, 402}:
        return True
    normalized = str(error).casefold()
    return any(
        marker in normalized
        for marker in (
            "spending limit",
            "insufficient credit",
            "credit balance",
            "quota exhausted",
            "quota exceeded",
            "invalid api key",
            "invalid_api_key",
            "authentication failed",
        )
    )
