"""
Feedback service for persisting user feedback to DynamoDB.
Handles save and query operations for feedback records.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key

from app.config import settings


class FeedbackService:
    """Service for managing feedback records in DynamoDB."""

    def __init__(self, table=None):
        """
        Initialize the service.

        Args:
            table: Optional DynamoDB table resource. If not provided,
                   uses the default table from settings.
        """
        if table is not None:
            self.table = table
        else:
            dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=settings.dynamodb_endpoint_url,
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id or 'dummy',
                aws_secret_access_key=settings.aws_secret_access_key or 'dummy'
            )
            self.table = dynamodb.Table(settings.table_name)

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    async def save_feedback(
        self,
        thread_id: str,
        user_id: str,
        task_type: str,
        category: str,
        text: str,
        rating: Optional[int] = None,
    ) -> dict:
        """
        Save a feedback record to DynamoDB.

        Args:
            thread_id: The conversation thread ID
            user_id: The user who submitted feedback
            task_type: The lesson task type (handwriting, vocabulary, etc.)
            category: Feedback category (lesson, platform, general)
            text: Free-text feedback
            rating: Optional 1-5 rating (omitted from record if None or 0)

        Returns:
            dict: The saved feedback item
        """
        feedback_id = str(uuid.uuid4())
        created_at = self._now_iso()

        item = {
            'PK': f'THREAD#{thread_id}',
            'SK': f'FEEDBACK#{feedback_id}',
            'GSI1PK': f'USER#{user_id}',
            'GSI1SK': f'FEEDBACK#{created_at}',
            'type': 'Feedback',
            'feedback_id': feedback_id,
            'thread_id': thread_id,
            'user_id': user_id,
            'task_type': task_type,
            'category': category,
            'text': text,
            'created_at': created_at,
        }

        # Only include rating if provided and non-zero
        if rating and rating > 0:
            item['rating'] = rating

        await asyncio.to_thread(self.table.put_item, Item=item)
        return item

    async def get_feedback_by_thread(self, thread_id: str) -> List[dict]:
        """
        Get all feedback records for a conversation thread.

        Args:
            thread_id: The conversation thread ID

        Returns:
            List of feedback items
        """
        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression=(
                Key('PK').eq(f'THREAD#{thread_id}')
                & Key('SK').begins_with('FEEDBACK#')
            )
        )
        return response.get('Items', [])

    async def get_feedback_by_user(self, user_id: str) -> List[dict]:
        """
        Get all feedback records for a user via GSI1.

        Args:
            user_id: The user ID

        Returns:
            List of feedback items sorted by creation time
        """
        response = await asyncio.to_thread(
            self.table.query,
            IndexName='GSI1',
            KeyConditionExpression=(
                Key('GSI1PK').eq(f'USER#{user_id}')
                & Key('GSI1SK').begins_with('FEEDBACK#')
            )
        )
        return response.get('Items', [])


# Singleton instance
_feedback_service: Optional[FeedbackService] = None


def get_feedback_service(table=None) -> FeedbackService:
    """Get the FeedbackService singleton (or create with custom table for tests)."""
    global _feedback_service

    if table is not None:
        return FeedbackService(table=table)

    if _feedback_service is None:
        _feedback_service = FeedbackService()

    return _feedback_service
