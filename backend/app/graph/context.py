from langchain_openai import ChatOpenAI
from app.graph.prompts import SYSTEM_PROMPT
from app.config import settings
from typing import Optional


class Context:
    """Configuration container for the AI agent."""
    system_prompt: str = SYSTEM_PROMPT
    _model: Optional[ChatOpenAI] = None
    
    @property
    def model(self) -> ChatOpenAI:
        """Lazy initialization of the ChatOpenAI model."""
        if self._model is None:
            api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else "dummy-key"
            self._model = ChatOpenAI(
                model="gpt-4o",
                api_key=api_key
            )
        return self._model
