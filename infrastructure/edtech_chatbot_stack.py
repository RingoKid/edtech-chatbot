#!/usr/bin/env python3
import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
)
from constructs import Construct


class EdTechChatbotInfraStack(Stack):
    """
    AWS CDK Stack for EdTech Chatbot Infrastructure

    This stack creates the necessary AWS resources for the EdTech Chatbot application,
    including a DynamoDB table with environment-specific naming.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get environment from APP_ENV environment variable, default to 'sandbox'
        app_env = os.environ.get('APP_ENV', 'sandbox')

        # Construct dynamic table name based on environment
        table_name = f'EdTechChatbotTable-{app_env}'

        # Create DynamoDB table with partition key (PK) and sort key (SK)
        self.chatbot_table = dynamodb.Table(
            self,
            "EdTechChatbotTable",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Auto-delete when stack is destroyed
        )

        # Add Global Secondary Index for email lookups
        self.chatbot_table.add_global_secondary_index(
            index_name="EmailIndex",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL  # Project all attributes
        )

        # Output the table name and ARN for reference
        from aws_cdk import CfnOutput

        CfnOutput(
            self,
            "DynamoDBTableName",
            value=self.chatbot_table.table_name,
            description=f"DynamoDB table name for {app_env} environment"
        )

        CfnOutput(
            self,
            "DynamoDBTableArn",
            value=self.chatbot_table.table_arn,
            description=f"DynamoDB table ARN for {app_env} environment"
        )
