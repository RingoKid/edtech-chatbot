from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Type


class StructuredOutputCapable(Protocol):
    def with_structured_output(self, schema: Type[Any], strict: bool = False) -> "StructuredOutputCapable":
        ...

    def invoke(self, prompt: str) -> Any:
        ...


class TextModel(Protocol):
    def with_structured_output(self, schema: Type[Any], strict: bool = False) -> StructuredOutputCapable:
        ...

    def invoke(self, prompt: str) -> Any:
        ...


class FakeModel:
    """A simple fake model for tests and local runs without network access."""

    def __init__(self, response: Optional[Dict[str, Any]] = None) -> None:
        self._response = response or {}

    def with_structured_output(self, schema: Type[Any], strict: bool = False) -> "FakeModel":
        return self

    def invoke(self, prompt: str) -> Any:
        # Return the pre-configured response; caller may adapt to schema externally
        return self._response


class ModelRouter:
    """Maps (task_name, query_type, demand) to a model instance.

    In a real deployment, this could select between providers (OpenAI, Anthropic, etc.).
    """

    def __init__(self, overrides: Optional[Dict[str, TextModel]] = None) -> None:
        self._overrides = overrides or {}

    def get_model(self, task_name: str, query_type: Optional[str], demand: str = "balanced") -> TextModel:
        # First check explicit overrides
        key = f"{task_name}:{query_type or ''}:{demand}"
        if key in self._overrides:
            return self._overrides[key]

        # Fallback to task-level override
        key_task = f"{task_name}:*:#{demand}"
        if key_task in self._overrides:
            return self._overrides[key_task]

        # Default to a FakeModel placeholder; implementation should wire real models
        return FakeModel()


class Context:
    """Application context providing model access via a ModelRouter."""

    def __init__(self, router: Optional[ModelRouter] = None) -> None:
        self._router = router or ModelRouter()

    def get_model(self, task_name: str, query_type: Optional[str] = None, demand: str = "balanced") -> TextModel:
        return self._router.get_model(task_name, query_type, demand)

    @property
    def model(self) -> TextModel:
        # Legacy accessor: returns a generic model
        return self._router.get_model(task_name="*", query_type=None, demand="balanced")


