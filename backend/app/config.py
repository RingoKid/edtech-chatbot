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
    app_env: AppEnv = Field(default=AppEnv.SANDBOX, alias="APP_ENV")
    
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
    
    # JWT configuration for authentication
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, alias="JWT_EXPIRATION_HOURS")
    
    # PostgreSQL Database configuration
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="edtech_db", alias="DB_NAME")
    db_user: str = Field(default="edtech_user", alias="DB_USER")
    db_password: str = Field(default="edtech_password", alias="DB_PASSWORD")
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    
    @property
    def get_database_url(self) -> str:
        """
        Generate PostgreSQL database URL.
        Uses DATABASE_URL if provided, otherwise constructs from individual components.
        """
        if self.database_url:
            return self.database_url
        
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
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
    
    def initialize_langsmith(self):
        """Initialize LangSmith tracing if configured."""
        import os
        
        if self.langsmith_tracing and self.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = self.langsmith_tracing
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            
            if self.langsmith_endpoint:
                os.environ["LANGCHAIN_ENDPOINT"] = self.langsmith_endpoint
            if self.langsmith_project:
                os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project

settings = Settings()