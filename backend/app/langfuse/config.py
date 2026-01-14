"""Langfuse configuration - reads from environment variables."""

import os
from dataclasses import dataclass


@dataclass
class LangfuseConfig:
    """Langfuse SDK configuration."""
    public_key: str
    secret_key: str
    host: str = "https://cloud.langfuse.com"
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "LangfuseConfig":
        """Load configuration from environment variables."""
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")

        # Disable if keys are not set
        enabled = bool(public_key and secret_key)

        return cls(
            public_key=public_key,
            secret_key=secret_key,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            enabled=enabled,
        )


# Singleton config instance
_config: LangfuseConfig | None = None


def get_langfuse_config() -> LangfuseConfig:
    """Get Langfuse configuration (singleton)."""
    global _config
    if _config is None:
        _config = LangfuseConfig.from_env()
    return _config
