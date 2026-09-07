from __future__ import annotations

from copy import deepcopy
from typing import Any


def inline_local_definitions(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline local ``$defs`` references for provider-portable tool schemas.

    Some OpenAI-compatible providers expose nested local references to the model as
    unconstrained values. Function-tool inputs are small, so duplicating definitions
    is preferable to silently losing their field names and validation constraints.
    """

    definitions = schema.get("$defs", {})
    if not isinstance(definitions, dict):
        return deepcopy(schema)

    def expand(value: Any, active: tuple[str, ...] = ()) -> Any:
        if isinstance(value, list):
            return [expand(item, active) for item in value]
        if not isinstance(value, dict):
            return deepcopy(value)

        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            name = reference.removeprefix("#/$defs/").replace("~1", "/").replace(
                "~0", "~"
            )
            definition = definitions.get(name)
            if not isinstance(definition, dict):
                raise ValueError(f"Tool schema references missing definition {name!r}")
            if name in active:
                raise ValueError(f"Tool schema contains recursive definition {name!r}")
            merged = {
                **deepcopy(definition),
                **{key: item for key, item in value.items() if key != "$ref"},
            }
            return expand(merged, (*active, name))

        return {
            key: expand(item, active)
            for key, item in value.items()
            if key != "$defs" and not (key == "enum" and item == [])
        }

    result = expand(schema)
    if not isinstance(result, dict):
        raise TypeError("A JSON tool schema must be an object")
    return result
