from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]
from app.graph.prompts import SYSTEM_PROMPT
from app.config import settings


class Context:
    """Configuration container for the AI agent."""
    system_prompt: str = SYSTEM_PROMPT

    @property
    def model(self) -> ChatOpenAI:
        """Lazy-load the model to avoid initialization issues."""
        model_kwargs = {"model": "gpt-4o", "temperature": 0}

        if settings.openai_api_key:
            return ChatOpenAI(
                api_key=settings.openai_api_key.get_secret_value(),
                **model_kwargs,
            )

        return ChatOpenAI(**model_kwargs)
