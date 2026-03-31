import boto3
from .config import settings, AppEnv

_dynamodb = None
_table = None


def _create_dynamodb_resource():
    """
    Create and return a DynamoDB resource based on the application environment.

    Returns:
        boto3.resource: DynamoDB resource configured for local, sandbox, or production environment
    """
    if settings.app_env == AppEnv.LOCAL:
        return boto3.resource(
            'dynamodb',
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or "dummy",
            aws_secret_access_key=settings.aws_secret_access_key or "dummy"
        )
    elif settings.app_env == AppEnv.SANDBOX:
        return boto3.resource(
            'dynamodb',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
    else:  # PRODUCTION
        return boto3.resource(
            'dynamodb',
            region_name=settings.aws_region
        )


def init_db():
    """Initialize DynamoDB connection. Called once at app startup via lifespan."""
    global _dynamodb, _table
    _dynamodb = _create_dynamodb_resource()
    _table = _dynamodb.Table(settings.table_name)


def get_db():
    """Get the DynamoDB table. Must be called after init_db()."""
    if _table is None:
        raise RuntimeError("Database not initialized — init_db() not called yet")
    return _table


def get_dynamodb():
    """Get the DynamoDB resource. Must be called after init_db()."""
    if _dynamodb is None:
        raise RuntimeError("Database not initialized — init_db() not called yet")
    return _dynamodb