"""
Unit tests for FeedbackService — DynamoDB read/write verification.

Run with:
    docker compose exec backend pytest tests/unit/test_feedback_service.py -v
"""

import pytest
from decimal import Decimal

from app.services.feedback_service import FeedbackService


@pytest.fixture
def feedback_service(dynamodb_tables):
    """Create a FeedbackService using the shared test table."""
    return FeedbackService(table=dynamodb_tables["main"])


@pytest.mark.asyncio
async def test_save_feedback(feedback_service):
    """Write feedback record, verify all DynamoDB attributes."""
    item = await feedback_service.save_feedback(
        thread_id="thread-001",
        user_id="user-001",
        task_type="handwriting",
        category="lesson",
        rating=5,
        text="Great lesson!",
    )

    assert item['PK'] == 'THREAD#thread-001'
    assert item['SK'].startswith('FEEDBACK#')
    assert item['GSI1PK'] == 'USER#user-001'
    assert item['GSI1SK'].startswith('FEEDBACK#')
    assert item['type'] == 'Feedback'
    assert item['task_type'] == 'handwriting'
    assert item['category'] == 'lesson'
    assert item['rating'] == 5
    assert item['text'] == 'Great lesson!'
    assert item['feedback_id'] is not None
    assert item['created_at'] is not None


@pytest.mark.asyncio
async def test_get_feedback_by_thread(feedback_service):
    """Query by PK = THREAD#{thread_id} returns correct records."""
    thread_id = "thread-query-test"

    # Save two feedback records for the same thread
    await feedback_service.save_feedback(
        thread_id=thread_id,
        user_id="user-002",
        task_type="handwriting",
        category="lesson",
        text="Good lesson",
    )
    await feedback_service.save_feedback(
        thread_id=thread_id,
        user_id="user-002",
        task_type="handwriting",
        category="platform",
        text="App is fast",
    )

    results = await feedback_service.get_feedback_by_thread(thread_id)

    assert len(results) >= 2
    categories = {r['category'] for r in results}
    assert 'lesson' in categories
    assert 'platform' in categories


@pytest.mark.asyncio
async def test_get_feedback_by_user(feedback_service):
    """GSI1 query by USER#{user_id} returns correct records."""
    user_id = "user-gsi1-test"

    await feedback_service.save_feedback(
        thread_id="thread-a",
        user_id=user_id,
        task_type="vocabulary",
        category="general",
        text="Nice platform",
    )
    await feedback_service.save_feedback(
        thread_id="thread-b",
        user_id=user_id,
        task_type="handwriting",
        category="lesson",
        text="Good content",
    )

    results = await feedback_service.get_feedback_by_user(user_id)

    assert len(results) >= 2
    thread_ids = {r['thread_id'] for r in results}
    assert 'thread-a' in thread_ids
    assert 'thread-b' in thread_ids


@pytest.mark.asyncio
async def test_save_feedback_without_rating(feedback_service):
    """Rating field omitted when not provided."""
    item = await feedback_service.save_feedback(
        thread_id="thread-no-rating",
        user_id="user-003",
        task_type="handwriting",
        category="lesson",
        text="Decent lesson",
        rating=0,  # 0 means no rating
    )

    # Rating should not be in the item when 0
    assert 'rating' not in item

    # Also test with None
    item2 = await feedback_service.save_feedback(
        thread_id="thread-no-rating-2",
        user_id="user-003",
        task_type="handwriting",
        category="lesson",
        text="Another lesson",
        rating=None,
    )

    assert 'rating' not in item2
