from __future__ import annotations

import json
from typing import Any, Type


def safe_structured_invoke(model: Any, schema: Type[Any], prompt: str, strict: bool = False) -> Any:
    """Attempt structured output; fallback to JSON-mode parsing if unavailable.

    Returns an instance or dict compatible with the schema.
    """
    try:
        structured = model.with_structured_output(schema, strict=strict)
        return structured.invoke(prompt)
    except Exception:
        # Fallback: try raw generation as JSON and parse
        raw = model.invoke(prompt)
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception as e:
                raise RuntimeError(f"Failed to parse JSON fallback: {e}")
        raise RuntimeError("Model returned unsupported type for structured output fallback")


