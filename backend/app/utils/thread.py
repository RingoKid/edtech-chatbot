"""
Thread ID utilities.
"""

import uuid


def generate_thread_id(user_id: str) -> str:
    """
    Generate thread ID from user ID and UUID.

    Format: {user_id}_{uuid}

    Args:
        user_id: User's unique ID

    Returns:
        Thread ID string

    Example:
        >>> generate_thread_id("user_123")
        "user_123_abc-def-ghi-jkl-mno"
    """
    return f"{user_id}_{uuid.uuid4()}"


def extract_user_id_from_thread(thread_id: str) -> str:
    """
    Extract user ID from thread ID.

    Args:
        thread_id: Thread ID in format {user_id}_{uuid}

    Returns:
        User ID string

    Example:
        >>> extract_user_id_from_thread("user_123_abc-def-ghi")
        "user_123"
    """
    return thread_id.split("_")[0]
