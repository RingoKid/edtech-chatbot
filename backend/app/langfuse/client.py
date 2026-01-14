"""Langfuse client singleton - provides access to the Langfuse SDK."""

from langfuse import Langfuse

from app.langfuse.config import get_langfuse_config


# Singleton client instance
_client: Langfuse | None = None


def get_langfuse_client() -> Langfuse | None:
    """
    Get the Langfuse client singleton.

    Returns None if Langfuse is not configured (missing keys).
    """
    global _client

    config = get_langfuse_config()

    if not config.enabled:
        return None

    if _client is None:
        _client = Langfuse(
            public_key=config.public_key,
            secret_key=config.secret_key,
            host=config.host,
        )

    return _client


def flush_langfuse() -> None:
    """Flush pending Langfuse events."""
    client = get_langfuse_client()
    if client:
        client.flush()
