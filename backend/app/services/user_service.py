"""
User service for managing user data in DynamoDB.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from app.database import get_db
from app.utils.auth import hash_password, verify_password


def create_user(name: str, email: str, password: str) -> Dict[str, Any]:
    """
    Create a new user in the database.
    
    Args:
        name: User's full name
        email: User's email address
        password: Plain text password (will be hashed)
        
    Returns:
        Dictionary containing user data
        
    Raises:
        ValueError: If email already exists
    """
    db = get_db()
    user_id = str(uuid.uuid4())
    
    # Check if user with this email already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        raise ValueError("Email already registered")
    
    # Hash the password
    hashed_password = hash_password(password)
    
    # Create user record
    user_data = {
        "PK": f"USER#{user_id}",
        "SK": "PROFILE",
        "user_id": user_id,
        "email": email,
        "name": name,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "type": "user"
    }
    
    # Save to database
    db.put_item(Item=user_data)
    
    # Return user data without password
    return {
        "id": user_id,
        "email": email,
        "name": name,
        "created_at": user_data["created_at"]
    }


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by email address.
    
    Args:
        email: User's email address
        
    Returns:
        User dictionary if found, None otherwise
    """
    db = get_db()
    
    try:
        # Check if it's file database (has items attribute)
        if hasattr(db, 'items'):
            # File database - iterate through items
            for key, item in db.items.items():
                if item.get("email") == email and item.get("type") == "user":
                    return item
        else:
            # DynamoDB - use scan with filter
            try:
                response = db.scan(
                    FilterExpression="email = :email AND #type = :type",
                    ExpressionAttributeNames={"#type": "type"},
                    ExpressionAttributeValues={":email": email, ":type": "user"}
                )
                items = response.get('Items', [])
                if items:
                    return items[0]
            except Exception:
                # Fallback: scan all and filter manually
                response = db.scan()
                items = response.get('Items', [])
                for item in items:
                    if item.get("email") == email and item.get("type") == "user":
                        return item
    except Exception:
        pass
    
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by user ID.
    
    Args:
        user_id: User's unique ID
        
    Returns:
        User dictionary if found, None otherwise
    """
    db = get_db()
    
    try:
        # Check if it's file database
        if hasattr(db, 'items'):
            # File database - use key format
            key = f"USER#{user_id}#PROFILE"
            if key in db.items:
                return db.items[key]
        else:
            # DynamoDB - use get_item
            response = db.get_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": "PROFILE"
                }
            )
            if 'Item' in response:
                return response['Item']
    except Exception:
        pass
    
    return None


def verify_user_credentials(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verify user credentials and return user data if valid.
    
    Args:
        email: User's email address
        password: Plain text password
        
    Returns:
        User dictionary (without password) if credentials are valid, None otherwise
    """
    user = get_user_by_email(email)
    
    if not user:
        return None
    
    # Verify password
    password_hash = user.get("password_hash")
    if not password_hash:
        return None
    
    if not verify_password(password, password_hash):
        return None
    
    # Return user data without password
    return {
        "id": user.get("user_id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "created_at": user.get("created_at")
    }

