from langchain_openai import ChatOpenAI
from app.graph.prompts import SYSTEM_PROMPT
from app.config import settings


class Context:
    """Configuration container for the AI agent."""
    system_prompt: str = SYSTEM_PROMPT

    @property
    def model(self) -> ChatOpenAI:
        """Lazy-load the model to avoid initialization issues."""
        if settings.openai_api_key:
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.openai_api_key.get_secret_value()
            )
        else:
            return ChatOpenAI(model="gpt-4o")
