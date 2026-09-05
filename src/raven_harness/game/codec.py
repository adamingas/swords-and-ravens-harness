import base64
import json
import zlib
from typing import Any


def encode_message(message: dict[str, Any]) -> str:
    raw = json.dumps(message, separators=(",", ":")).encode()
    return base64.b64encode(zlib.compress(raw)).decode()


def decode_message(data: str | bytes) -> dict[str, Any]:
    encoded = data.encode() if isinstance(data, str) else data
    raw = zlib.decompress(base64.b64decode(encoded))
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Game protocol message must be a JSON object")
    return value
