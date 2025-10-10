import pytest
from app.config import settings


def test_individual_env_variables():
    """
    Test that all required environment variables are accessible through settings.
    Works across all environments (local, sandbox, production).
    """
    # Test that all required settings exist and are non-empty
    required_settings = [
        ("aws_access_key_id", settings.aws_access_key_id),
        ("aws_secret_access_key", settings.aws_secret_access_key),
        ("aws_region", settings.aws_region),
        ("dynamodb_table_name", settings.dynamodb_table_name),
        ("dynamodb_endpoint_url", settings.dynamodb_endpoint_url),
        ("langsmith_tracing", settings.langsmith_tracing),
        ("langsmith_api_key", settings.langsmith_api_key),
        ("langsmith_endpoint", settings.langsmith_endpoint),
        ("langsmith_project", settings.langsmith_project),
    ]

    for setting_name, setting_value in required_settings:
        assert setting_value is not None, f"{setting_name} is not loaded"
        assert len(str(setting_value)) > 0, f"{setting_name} is empty"

    # Special handling for OpenAI API key (SecretStr)
    assert settings.openai_api_key is not None, "openai_api_key is not loaded"
    openai_key_value = settings.openai_api_key.get_secret_value()
    assert len(openai_key_value) > 0, "openai_api_key is empty"

    print("✅ All required environment variables loaded successfully")
