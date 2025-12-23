# 006: Chat History System

## Overview

This spec covers:
1. Switching from SQLite to DynamoDB checkpointer for conversation persistence
2. Adding APIs to retrieve chat history for authenticated users

---

## Architecture Decisions

### Decision 1: thread_id Format

**Choice:** Plain UUID (no user_id embedded)

```python
# Before
thread_id = f"{user_id}_{uuid.uuid4().hex[:8]}"  # "user123_abc12345"

# After
thread_id = str(uuid.uuid4())  # "550e8400-e29b-41d4-a716-446655440000"
```

**Rationale:**
- User-thread relationship stored in `Conversation` table (not in thread_id)
- Cleaner separation of concerns
- Thread_id used as-is for checkpointer lookups

### Decision 2: Checkpointer Timing

**Choice:** Checkpointer kicks in after first user message, NOT on `/chat/init`

| Endpoint | Graph Invoke | Checkpointer |
|----------|--------------|--------------|
| `GET /chat/init` | No | No |
| `POST /chat/message` (first) | Yes | Yes |
| `POST /chat/message` (subsequent) | Yes | Yes |

**Rationale:**
- `/chat/init` only returns a static greeting
- No need to persist state until user actually engages
- Reduces unnecessary writes to DynamoDB

### Decision 3: Separate Concerns for Storage

| Data | Storage | Table |
|------|---------|-------|
| Graph state (messages, task_name, params) | DynamoDB Checkpointer | `EdTechChatbotCheckpoints-{env}` |
| User-thread mapping (title, preview) | Conversation model | `EdTechChatbotTable-{env}` |

---

## Prerequisite: Single Source of Truth for DB Schema

### Goal
Extract DynamoDB table schemas to shared module to avoid duplication between `init_db.py` and tests.

### Create: `backend/app/db_schema.py`

```python
"""Single source of truth for DynamoDB table schemas."""

MAIN_TABLE_SCHEMA = {
    'KeySchema': [
        {'AttributeName': 'PK', 'KeyType': 'HASH'},
        {'AttributeName': 'SK', 'KeyType': 'RANGE'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'PK', 'AttributeType': 'S'},
        {'AttributeName': 'SK', 'AttributeType': 'S'},
        {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
        {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'GSI1',
            'KeySchema': [
                {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ]
}

CHECKPOINT_TABLE_SCHEMA = {
    'KeySchema': [
        {'AttributeName': 'PK', 'KeyType': 'HASH'},
        {'AttributeName': 'SK', 'KeyType': 'RANGE'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'PK', 'AttributeType': 'S'},
        {'AttributeName': 'SK', 'AttributeType': 'S'}
    ]
}
```

### Modify: `backend/scripts/init_db.py`

```python
from app.db_schema import MAIN_TABLE_SCHEMA, CHECKPOINT_TABLE_SCHEMA

def create_main_table(dynamodb_client, table_name):
    dynamodb_client.create_table(
        TableName=table_name,
        BillingMode='PAY_PER_REQUEST',
        **MAIN_TABLE_SCHEMA
    )
```

---

## Phase 1: DynamoDB Checkpointer Integration

### Goal
Replace `AsyncSqliteSaver` with `DynamoDBSaver` for conversation persistence.

### Modify: `backend/app/graph/graph.py`

```python
# Before
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite

async def create_graph():
    conn = await aiosqlite.connect("checkpointer.sqlite")
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    ...

# After
from langgraph_dynamodb_checkpoint import DynamoDBSaver
from app.config import settings
import boto3

async def create_graph():
    # Create DynamoDB client based on environment
    if settings.app_env == AppEnv.LOCAL:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)

    checkpointer = DynamoDBSaver(
        table_name=settings.checkpoint_table_name,
        dynamodb_resource=dynamodb
    )
    ...
```

### Modify: `backend/app/services/chat_service.py`

```python
# Update thread_id generation - plain UUID
def create_new_thread(self) -> str:
    """Create a new thread ID."""
    return str(uuid.uuid4())

# Update init_chat - no graph invoke
async def init_chat(self, user_id: str) -> ChatMessageResponse:
    """
    Initialize a new chat session.
    Returns greeting without invoking graph (no checkpoint created yet).
    """
    thread_id = self.create_new_thread()

    # Create conversation record
    await chat_history_service.create_conversation(user_id, thread_id)

    # Return static greeting (no graph invoke)
    return ChatMessageResponse(
        thread_id=thread_id,
        reply=GREETING_WELCOME_MESSAGE
    )
```

---

## Phase 2: Chat History APIs

### Data Model

#### Modify: `backend/app/models.py`

```python
class Conversation(BaseModel):
    pk: str = Field(alias='PK')
    sk: str = Field(alias='SK')
    type: Literal["Conversation"]
    thread_id: str                          # Renamed from conversation_id
    user_id: str
    title: str = "New Conversation"
    last_message_preview: Optional[str] = None  # Added
    created_at: str
    updated_at: str
```

### Title Generation

**Mapping (in `chat_history_service.py`):**

```python
TASK_NAME_TO_TITLE = {
    "Handwriting": "Handwriting Practice",
    "Vocabulary": "Vocabulary Learning",
    "Idea Generation": "Idea Generation",
}
```

### Conversation Lifecycle

| Event | Action | Fields |
|-------|--------|--------|
| `/chat/init` | CREATE | All fields, `title="New Conversation"` |
| `task_name` set | UPDATE | `title`, `updated_at` |
| Every message | UPDATE | `last_message_preview`, `updated_at` |

### API Endpoints

#### GET `/api/v1/chat/history`

- **Auth:** Required (JWT)
- **Returns:** List of conversation summaries for authenticated user

**Response:**
```json
{
  "conversations": [
    {
      "thread_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Handwriting Practice",
      "last_message_preview": "Let's work on letter formation...",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T11:45:00Z"
    }
  ]
}
```

#### GET `/api/v1/chat/{thread_id}/messages`

- **Auth:** Required (JWT)
- **Validates:** User owns the thread (403 if not)
- **Returns:** Full message history

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "role": "assistant",
      "content": "Hello! How can I help you today?",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "role": "user",
      "content": "I want to practice handwriting",
      "timestamp": "2025-01-15T10:30:15Z"
    }
  ]
}
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `backend/app/db_schema.py` | Create | Single source of truth for table schemas |
| `backend/app/models.py` | Modify | Update Conversation model |
| `backend/app/services/chat_history_service.py` | Create | CRUD for conversation records |
| `backend/app/schemas/chat_history.py` | Create | API response models |
| `backend/app/routers/chat.py` | Modify | Add history endpoints |
| `backend/app/services/chat_service.py` | Modify | Integrate with chat_history_service |
| `backend/app/graph/graph.py` | Modify | Switch to DynamoDB checkpointer |
| `backend/scripts/init_db.py` | Modify | Use shared schema |

---

## Unit Tests (TDD Approach)

All tests run against **DynamoDB Local only**.

### Create: `backend/tests/unit/test_db_schema.py`

```python
"""Test that DynamoDB table structure matches expected schema."""

import pytest
import boto3
from app.db_schema import MAIN_TABLE_SCHEMA, CHECKPOINT_TABLE_SCHEMA
from app.config import settings


@pytest.fixture(scope="module")
def dynamodb_client():
    """Connect to DynamoDB Local."""
    return boto3.client(
        'dynamodb',
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )


def test_main_table_structure_matches_schema(dynamodb_client):
    """Verify main table schema matches expected structure."""
    table_desc = dynamodb_client.describe_table(TableName=settings.table_name)

    assert table_desc['Table']['KeySchema'] == MAIN_TABLE_SCHEMA['KeySchema']

    # Verify GSI exists
    gsi_names = [gsi['IndexName'] for gsi in table_desc['Table'].get('GlobalSecondaryIndexes', [])]
    assert 'GSI1' in gsi_names


def test_checkpoint_table_structure_matches_schema(dynamodb_client):
    """Verify checkpoint table schema matches expected structure."""
    table_desc = dynamodb_client.describe_table(TableName=settings.checkpoint_table_name)

    assert table_desc['Table']['KeySchema'] == CHECKPOINT_TABLE_SCHEMA['KeySchema']
```

### Create: `backend/tests/unit/test_dynamodb_checkpointer.py`

```python
"""Unit tests for DynamoDB checkpointer integration."""

import pytest
import boto3
from app.config import settings
from app.graph.graph import create_graph
from langchain_core.messages import HumanMessage


@pytest.fixture(scope="module")
def dynamodb_table():
    """Setup checkpoint table in DynamoDB Local."""
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    table = dynamodb.Table(settings.checkpoint_table_name)
    yield table


@pytest.mark.asyncio
async def test_checkpointer_saves_state(dynamodb_table):
    """Test that checkpointer saves graph state to DynamoDB."""
    graph = await create_graph()
    thread_id = "test-thread-001"
    config = {"configurable": {"thread_id": thread_id}}

    # Invoke graph
    await graph.ainvoke({"messages": [HumanMessage(content="Hello")]}, config=config)

    # Verify state was saved
    state = await graph.aget_state(config)
    assert state is not None
    assert len(state.values.get("messages", [])) > 0


@pytest.mark.asyncio
async def test_checkpointer_resumes_conversation(dynamodb_table):
    """Test that checkpointer can resume from saved state."""
    graph = await create_graph()
    thread_id = "test-thread-002"
    config = {"configurable": {"thread_id": thread_id}}

    # First message
    await graph.ainvoke({"messages": [HumanMessage(content="I want handwriting")]}, config=config)

    # Get state and verify task_name
    state = await graph.aget_state(config)
    initial_message_count = len(state.values.get("messages", []))

    # Resume with second message
    await graph.aupdate_state(config, {"messages": [HumanMessage(content="Kindergarten")]})
    await graph.ainvoke(None, config=config)

    # Verify state accumulated
    state = await graph.aget_state(config)
    assert len(state.values.get("messages", [])) > initial_message_count


@pytest.mark.asyncio
async def test_checkpointer_handles_timeout():
    """Test graceful handling of DynamoDB timeout."""
    from unittest.mock import patch, MagicMock
    from botocore.exceptions import ConnectTimeoutError

    with patch('boto3.resource') as mock_resource:
        mock_resource.side_effect = ConnectTimeoutError(endpoint_url="http://localhost:8000")

        with pytest.raises(ConnectTimeoutError):
            await create_graph()


@pytest.mark.asyncio
async def test_checkpointer_handles_unavailable():
    """Test graceful handling when DynamoDB is unavailable."""
    from unittest.mock import patch
    from botocore.exceptions import ClientError

    error_response = {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}}

    with patch('boto3.resource') as mock_resource:
        mock_resource.return_value.Table.return_value.get_item.side_effect = ClientError(
            error_response, 'GetItem'
        )

        # Should handle gracefully or raise appropriate error
        # Implementation will determine exact behavior
```

### Create: `backend/tests/unit/test_chat_history_service.py`

```python
"""Unit tests for chat history service."""

import pytest
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from app.config import settings
from app.services.chat_history_service import ChatHistoryService
from app.db_schema import MAIN_TABLE_SCHEMA


@pytest.fixture(scope="module")
def dynamodb_table():
    """Setup main table in DynamoDB Local."""
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )

    table_name = f"test-{settings.table_name}"

    # Delete if exists
    try:
        dynamodb.Table(table_name).delete()
        dynamodb.Table(table_name).wait_until_not_exists()
    except ClientError:
        pass

    # Create table
    table = dynamodb.create_table(
        TableName=table_name,
        BillingMode='PAY_PER_REQUEST',
        **MAIN_TABLE_SCHEMA
    )
    table.wait_until_exists()

    yield table

    # Cleanup
    table.delete()


@pytest.fixture
def chat_history_service(dynamodb_table):
    """Create ChatHistoryService instance."""
    return ChatHistoryService(table=dynamodb_table)


class TestCreateConversation:
    """Tests for create_conversation method."""

    @pytest.mark.asyncio
    async def test_creates_conversation_with_default_title(self, chat_history_service):
        """Test creating conversation with default 'New Conversation' title."""
        user_id = "user-001"
        thread_id = "thread-001"

        await chat_history_service.create_conversation(user_id, thread_id)

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation is not None
        assert conversation.title == "New Conversation"
        assert conversation.thread_id == thread_id
        assert conversation.user_id == user_id

    @pytest.mark.asyncio
    async def test_creates_conversation_with_timestamps(self, chat_history_service):
        """Test that created_at and updated_at are set."""
        user_id = "user-002"
        thread_id = "thread-002"

        await chat_history_service.create_conversation(user_id, thread_id)

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.created_at is not None
        assert conversation.updated_at is not None


class TestGetUserConversations:
    """Tests for get_user_conversations method."""

    @pytest.mark.asyncio
    async def test_returns_all_user_conversations(self, chat_history_service):
        """Test retrieving all conversations for a user."""
        user_id = "user-003"

        # Create multiple conversations
        await chat_history_service.create_conversation(user_id, "thread-a")
        await chat_history_service.create_conversation(user_id, "thread-b")
        await chat_history_service.create_conversation(user_id, "thread-c")

        conversations = await chat_history_service.get_user_conversations(user_id)
        assert len(conversations) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_new_user(self, chat_history_service):
        """Test that new user gets empty conversation list."""
        user_id = "user-new-no-conversations"

        conversations = await chat_history_service.get_user_conversations(user_id)
        assert conversations == []

    @pytest.mark.asyncio
    async def test_does_not_return_other_users_conversations(self, chat_history_service):
        """Test that user only sees their own conversations."""
        user_a = "user-a"
        user_b = "user-b"

        await chat_history_service.create_conversation(user_a, "thread-user-a")
        await chat_history_service.create_conversation(user_b, "thread-user-b")

        conversations_a = await chat_history_service.get_user_conversations(user_a)
        thread_ids = [c.thread_id for c in conversations_a]

        assert "thread-user-a" in thread_ids
        assert "thread-user-b" not in thread_ids


class TestUpdateTitle:
    """Tests for update_title method."""

    @pytest.mark.asyncio
    async def test_updates_title_from_task_name(self, chat_history_service):
        """Test updating title based on task_name."""
        user_id = "user-004"
        thread_id = "thread-004"

        await chat_history_service.create_conversation(user_id, thread_id)
        await chat_history_service.update_title(user_id, thread_id, "Handwriting")

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.title == "Handwriting Practice"

    @pytest.mark.asyncio
    async def test_updates_updated_at_timestamp(self, chat_history_service):
        """Test that updated_at changes when title is updated."""
        user_id = "user-005"
        thread_id = "thread-005"

        await chat_history_service.create_conversation(user_id, thread_id)
        conversation_before = await chat_history_service.get_conversation(user_id, thread_id)

        # Small delay to ensure timestamp difference
        import asyncio
        await asyncio.sleep(0.1)

        await chat_history_service.update_title(user_id, thread_id, "Vocabulary")
        conversation_after = await chat_history_service.get_conversation(user_id, thread_id)

        assert conversation_after.updated_at > conversation_before.updated_at


class TestUpdatePreview:
    """Tests for update_preview method."""

    @pytest.mark.asyncio
    async def test_updates_last_message_preview(self, chat_history_service):
        """Test updating last_message_preview."""
        user_id = "user-006"
        thread_id = "thread-006"

        await chat_history_service.create_conversation(user_id, thread_id)
        await chat_history_service.update_preview(user_id, thread_id, "Let's practice writing letters!")

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.last_message_preview == "Let's practice writing letters!"

    @pytest.mark.asyncio
    async def test_truncates_long_preview(self, chat_history_service):
        """Test that preview is truncated to 100 characters."""
        user_id = "user-007"
        thread_id = "thread-007"
        long_message = "A" * 200

        await chat_history_service.create_conversation(user_id, thread_id)
        await chat_history_service.update_preview(user_id, thread_id, long_message)

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert len(conversation.last_message_preview) <= 100


class TestOwnershipValidation:
    """Tests for ownership validation."""

    @pytest.mark.asyncio
    async def test_user_can_access_own_thread(self, chat_history_service):
        """Test that user can access their own thread."""
        user_id = "user-008"
        thread_id = "thread-008"

        await chat_history_service.create_conversation(user_id, thread_id)

        is_owner = await chat_history_service.verify_ownership(user_id, thread_id)
        assert is_owner is True

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_thread(self, chat_history_service):
        """Test that user cannot access another user's thread."""
        owner = "user-owner"
        other = "user-other"
        thread_id = "thread-009"

        await chat_history_service.create_conversation(owner, thread_id)

        is_owner = await chat_history_service.verify_ownership(other, thread_id)
        assert is_owner is False
```

### Create: `backend/tests/integration/test_chat_history_routes.py`

```python
"""Integration tests for chat history API routes."""

import pytest
from fastapi.testclient import TestClient
import boto3
from botocore.exceptions import ClientError
from app.config import settings
from app.main import app
from app.db_schema import MAIN_TABLE_SCHEMA


@pytest.fixture(scope="module")
def dynamodb_table():
    """Setup DynamoDB table for testing."""
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )

    table_name = settings.table_name

    # Delete if exists
    try:
        table = dynamodb.Table(table_name)
        table.delete()
        table.wait_until_not_exists()
    except ClientError:
        pass

    # Create table
    table = dynamodb.create_table(
        TableName=table_name,
        BillingMode='PAY_PER_REQUEST',
        **MAIN_TABLE_SCHEMA
    )
    table.wait_until_exists()

    yield table

    # Cleanup
    try:
        table.delete()
    except ClientError:
        pass


@pytest.fixture
def client(dynamodb_table):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get auth headers for authenticated requests."""
    # Create test user and login
    client.post("/api/v1/auth/signup", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123"
    })

    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestGetHistory:
    """Tests for GET /chat/history endpoint."""

    def test_returns_conversation_list(self, client, auth_headers):
        """Test that authenticated user gets their conversation list."""
        # Create some conversations first via /chat/init
        client.get("/api/v1/chat/init", headers=auth_headers)
        client.get("/api/v1/chat/init", headers=auth_headers)

        response = client.get("/api/v1/chat/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert len(data["conversations"]) >= 2

    def test_returns_empty_list_for_new_user(self, client):
        """Test that new user gets empty list."""
        # Create new user
        client.post("/api/v1/auth/signup", json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "password123"
        })

        login_response = client.post("/api/v1/auth/login", json={
            "email": "newuser@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/chat/history", headers=headers)

        assert response.status_code == 200
        assert response.json()["conversations"] == []

    def test_requires_authentication(self, client):
        """Test that unauthenticated request is rejected."""
        response = client.get("/api/v1/chat/history")

        assert response.status_code == 401


class TestGetMessages:
    """Tests for GET /chat/{thread_id}/messages endpoint."""

    def test_returns_messages_for_own_thread(self, client, auth_headers):
        """Test retrieving messages from own thread."""
        # Create conversation
        init_response = client.get("/api/v1/chat/init", headers=auth_headers)
        thread_id = init_response.json()["thread_id"]

        # Send a message
        client.post("/api/v1/chat/message", headers=auth_headers, json={
            "thread_id": thread_id,
            "message": "Hello, I want to practice handwriting"
        })

        # Get messages
        response = client.get(f"/api/v1/chat/{thread_id}/messages", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == thread_id
        assert "messages" in data
        assert len(data["messages"]) > 0

    def test_returns_404_for_nonexistent_thread(self, client, auth_headers):
        """Test 404 for non-existent thread."""
        response = client.get("/api/v1/chat/nonexistent-thread/messages", headers=auth_headers)

        assert response.status_code == 404

    def test_returns_403_for_other_users_thread(self, client, auth_headers):
        """Test 403 when accessing another user's thread."""
        # Create conversation as first user
        init_response = client.get("/api/v1/chat/init", headers=auth_headers)
        thread_id = init_response.json()["thread_id"]

        # Create second user
        client.post("/api/v1/auth/signup", json={
            "name": "Other User",
            "email": "other@example.com",
            "password": "password123"
        })

        login_response = client.post("/api/v1/auth/login", json={
            "email": "other@example.com",
            "password": "password123"
        })
        other_token = login_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access first user's thread
        response = client.get(f"/api/v1/chat/{thread_id}/messages", headers=other_headers)

        assert response.status_code == 403

    def test_requires_authentication(self, client):
        """Test that unauthenticated request is rejected."""
        response = client.get("/api/v1/chat/some-thread/messages")

        assert response.status_code == 401
```

---

## Implementation Order

### Step 1: Prerequisite - DB Schema Module
1. Create `backend/app/db_schema.py`
2. Update `backend/scripts/init_db.py` to use shared schema
3. Run `test_db_schema.py` to verify

### Step 2: Phase 1 - DynamoDB Checkpointer
1. Write tests in `test_dynamodb_checkpointer.py`
2. Modify `backend/app/graph/graph.py`
3. Run tests to verify

### Step 3: Phase 2a - Conversation Model & Service
1. Update `backend/app/models.py` (Conversation model)
2. Write tests in `test_chat_history_service.py`
3. Create `backend/app/services/chat_history_service.py`
4. Run tests to verify

### Step 4: Phase 2b - Chat History Routes
1. Create `backend/app/schemas/chat_history.py`
2. Write tests in `test_chat_history_routes.py`
3. Modify `backend/app/routers/chat.py`
4. Modify `backend/app/services/chat_service.py`
5. Run all tests

---

## Environment Support

| Environment | DynamoDB | Table Names |
|-------------|----------|-------------|
| LOCAL | DynamoDB Local (docker) | `*-local` |
| SANDBOX | AWS DynamoDB | `*-sandbox` |

Configured via `APP_ENV` variable in `.env` file.
