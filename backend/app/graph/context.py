from langchain_openai import ChatOpenAI
from app.graph.prompts import SYSTEM_PROMPT
from app.config import settings


class Context:
    """Configuration container for the AI agent."""
    system_prompt: str = SYSTEM_PROMPT
    model: ChatOpenAI = ChatOpenAI(
        model="gpt-4o",
        api_key=settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    )
