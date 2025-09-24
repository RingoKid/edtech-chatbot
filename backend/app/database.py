import boto3
from .config import settings, AppEnv


def get_dynamodb_resource():
    """
    Create and return a DynamoDB resource based on the application environment.
    
    Returns:
        boto3.resource: DynamoDB resource configured for local, sandbox, or production environment
    """
    if settings.app_env == AppEnv.LOCAL:
        # Local environment configuration - uses local DynamoDB endpoint
        return boto3.resource(
            'dynamodb',
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or "dummy",
            aws_secret_access_key=settings.aws_secret_access_key or "dummy"
        )
    elif settings.app_env == AppEnv.SANDBOX:
        # Sandbox environment configuration - uses AWS DynamoDB with explicit credentials
        return boto3.resource(
            'dynamodb',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
    else:  # PRODUCTION
        # Production environment configuration - uses AWS DynamoDB with IAM role/profile
        return boto3.resource(
            'dynamodb',
            region_name=settings.aws_region
        )


# Global DynamoDB resource
dynamodb = get_dynamodb_resource()

# Global table reference
table = dynamodb.Table(settings.table_name)


def get_db():
    """
    FastAPI dependency function to provide database access.
    
    Returns:
        boto3.resources.dynamodb.Table: The DynamoDB table resource
    """
    return table