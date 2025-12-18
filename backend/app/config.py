from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional
from enum import Enum
import os
from dotenv import load_dotenv


class AppEnv(str, Enum):
    PRODUCTION = "production"
    SANDBOX = "sandbox"
    LOCAL = "local"


# Load environment files before Settings class initialization
def _load_env_files():
    """Load appropriate .env files based on APP_ENV."""
    # First load base .env if it exists
    if os.path.exists(".env"):
        load_dotenv(".env")

    # Get APP_ENV and load environment-specific file
    app_env = os.getenv("APP_ENV", "local")
    env_file = f".env.{app_env}"
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  Environment file {env_file} not found")

# Load env files before class definition
_load_env_files()


class Settings(BaseSettings):
    """Configuration settings for the EdTech Chatbot application."""
    
    # Application environment - loaded from environment variable APP_ENV
    app_env: AppEnv = Field(default=AppEnv.LOCAL, alias="APP_ENV")
    
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
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

    # Authentication & JWT
    secret_key: SecretStr = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    # Speechmatics configuration for voice transcription
    SPEECHMATICS_API_KEY: Optional[str] = Field(default=None, alias="SPEECHMATICS_API_KEY")
    CONNECTION_URL: str = Field(default="wss://us2.rt.speechmatics.com/v2", alias="CONNECTION_URL")

    def initialize_langsmith(self) -> None:
        """Initialize LangSmith tracing if configured."""
        if self.langsmith_tracing and self.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = self.langsmith_tracing
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            if self.langsmith_endpoint:
                os.environ["LANGCHAIN_ENDPOINT"] = self.langsmith_endpoint
            if self.langsmith_project:
                os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
            print(f"✅ LangSmith tracing initialized for project: {self.langsmith_project or 'default'}")
        else:
            print("⚠️  LangSmith tracing not initialized - missing LANGSMITH_TRACING or LANGSMITH_API_KEY")

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

    @property
    def checkpoint_table_name(self) -> str:
        """Generate checkpoint table name based on environment."""
        base_name = "EdTechChatbotCheckpoints"
        if self.app_env == AppEnv.LOCAL:
            return f"{base_name}-local"
        elif self.app_env == AppEnv.SANDBOX:
            return f"{base_name}-sandbox"
        else:
            return f"{base_name}-prod"

settings = Settings()