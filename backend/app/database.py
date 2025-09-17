import boto3
from .config import settings


def get_dynamodb_resource():
    """
    Create and return a DynamoDB resource based on the configuration.
    
    Returns:
        boto3.resource: DynamoDB resource configured for local or production environment
    """
    if settings.dynamodb_endpoint_url:
        # Local environment configuration
        return boto3.resource(
            'dynamodb',
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or "dummy",
            aws_secret_access_key=settings.aws_secret_access_key or "dummy"
        )
    else:
        # Sandbox and production environment configuration
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