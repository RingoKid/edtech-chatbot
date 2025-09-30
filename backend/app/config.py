from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional, Any
from enum import Enum
import os


class AppEnv(str, Enum):
    PRODUCTION = "production"
    SANDBOX = "sandbox"
    LOCAL = "local"


def get_env_files():
    """
    Dynamically determine which environment files to load based on APP_ENV.
    
    Returns:
        list: List of environment files to load in order of precedence
    """
    from dotenv import load_dotenv

    base_env = ".env"
    load_dotenv(base_env)
    app_env = os.getenv("APP_ENV", "sandbox")
    env_specific = f".env.{app_env}"
    
    # Return files in order: base env file first, then environment-specific file
    # Environment-specific variables will override base variables
    return [base_env, env_specific]


class Settings(BaseSettings):
    """Configuration settings for the EdTech Chatbot application."""
    
    # Application environment - loaded from environment variable APP_ENV
    app_env: AppEnv = Field(default=AppEnv.LOCAL, alias="APP_ENV")
    
    model_config = SettingsConfigDict(
        env_file=get_env_files(),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # AWS credentials and configuration
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY") 
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    
    # DynamoDB configuration
    dynamodb_table_name: Optional[str] = Field(default=None, alias="DYNAMODB_TABLE_NAME")
    # Use local DynamoDB endpoint for development, None for production AWS
    dynamodb_endpoint_url: Optional[str] = Field(default=None, alias="DYNAMODB_ENDPOINT_URL")
    
    # LangSmith configuration for tracing and monitoring
    langsmith_tracing: Optional[str] = Field(default=None, alias="LANGSMITH_TRACING")
    langsmith_api_key: Optional[str] = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_endpoint: Optional[str] = Field(default=None, alias="LANGSMITH_ENDPOINT")
    langsmith_project: Optional[str] = Field(default=None, alias="LANGSMITH_PROJECT")
    
    # OpenAI API configuration
    openai_api_key: Optional[SecretStr] = Field(default=None, alias="OPENAI_API_KEY")
    
    @property
    def table_name(self) -> str:
        """
        Generate table name based on environment.
        Returns environment-specific table names:
        - LOCAL: EdTechChatbotTable-local
        - SANDBOX: EdTechChatbotTable-sandbox  
        - PRODUCTION: EdTechChatbotTable-prod
        """
        base_name = self.dynamodb_table_name or "EdTechChatbotTable"
        
        if self.app_env == AppEnv.LOCAL:
            return f"{base_name}-local"
        elif self.app_env == AppEnv.SANDBOX:
            return f"{base_name}-sandbox"
        else:  # PRODUCTION
            return f"{base_name}-prod"

settings = Settings()