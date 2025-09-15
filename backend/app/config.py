from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum


class AppEnv(str, Enum):
    PRODUCTION = "production"
    SANDBOX = "sandbox"
    LOCAL = "local"


class Settings(BaseSettings):
    """Configuration settings for the EdTech Chatbot application."""
    
    model_config = SettingsConfigDict(
        env_file=".env",  # Load environment variables from .env file
        env_file_encoding="utf-8"
    )
    
    # Application environment
    app_env: AppEnv = AppEnv.LOCAL
    
    # AWS credentials and configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "dummy"
    
    # DynamoDB configuration
    dynamodb_table_name: str = "EdTechChatbotTable"
    # Use local DynamoDB endpoint for development, None for production AWS
    dynamodb_endpoint_url: Optional[str] = None

settings = Settings()