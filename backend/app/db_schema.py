"""
Single source of truth for DynamoDB table schemas.
Used by init_db.py and tests to ensure consistent table structure.
"""

# Main application table schema (EdTechChatbotTable-{env})
# Stores: Users, Refresh Tokens, Conversations
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

# Checkpoint table schema (EdTechChatbotCheckpoints-{env})
# Stores: LangGraph conversation state checkpoints
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

# Feedback key patterns (documentation — no schema changes needed)
# These patterns use the existing PK/SK + GSI1 on the main table.
FEEDBACK_KEY_PATTERNS = {
    'PK': 'THREAD#{thread_id}',
    'SK': 'FEEDBACK#{feedback_id}',
    'GSI1PK': 'USER#{user_id}',
    'GSI1SK': 'FEEDBACK#{created_at}',
}

# TTL configuration for main table (for refresh token auto-deletion)
MAIN_TABLE_TTL_CONFIG = {
    'Enabled': True,
    'AttributeName': 'expires_at'
}
