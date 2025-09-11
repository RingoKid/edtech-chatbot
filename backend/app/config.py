from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Configuration settings for the EdTech Chatbot application."""
    
    model_config = SettingsConfigDict(
        env_file=".env",  # Load environment variables from .env file
        env_file_encoding="utf-8"
    )
    
    # AWS credentials and configuration
    aws_access_key_id: str = "dummy"
    aws_secret_access_key: str = "dummy"
    aws_region: str = "dummy"
    
    # DynamoDB configuration
    dynamodb_table_name: str = "EdTechChatbotTable"
    # Use local DynamoDB endpoint for development, None for production AWS
    dynamodb_endpoint_url: Optional[str] = "http://dynamodb-local:8000"

settings = Settings()