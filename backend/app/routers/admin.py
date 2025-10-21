"""
Admin router for form management operations.
Provides CRUD operations for educational forms in the admin portal.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json
import uuid
from datetime import datetime

from app.database import get_db
from app.service.form_retrieval_service import form_retrieval_service

router = APIRouter()

# Pydantic models for request/response
class FormUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Dict[str, Any]

class FormCreateRequest(BaseModel):
    category: str
    title: str
    content: Dict[str, Any]

class FormResponse(BaseModel):
    form_id: str
    category: str
    domain: str
    title: str
    content: Dict[str, Any]
    source_file: str
    created_at: str
    updated_at: str

class FormListResponse(BaseModel):
    forms: List[FormResponse]
    total_count: int


@router.get("/forms", response_model=FormListResponse)
async def get_all_forms():
    """
    Get all forms for the admin portal.
    Returns a list of all forms with their metadata.
    """
    try:
        # Get all forms using the form retrieval service
        forms_data = await form_retrieval_service.get_forms_by_domain("all")
        
        forms = []
        for item in forms_data:
            forms.append(FormResponse(
                form_id=item.get('form_id', ''),
                category=item.get('category', ''),
                domain=item.get('domain', ''),
                title=item.get('title', ''),
                content=item.get('content', {}),
                source_file=item.get('source_file', 'unknown'),
                created_at=item.get('created_at', ''),
                updated_at=item.get('updated_at', '')
            ))
        
        return FormListResponse(
            forms=forms,
            total_count=len(forms)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving forms: {str(e)}")

@router.get("/forms/{form_id}", response_model=FormResponse)
async def get_form_by_id(form_id: str):
    """
    Get a specific form by its ID.
    """
    try:
        table = get_db()
        response = table.query(
            KeyConditionExpression='PK = :pk AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': f'FORM#{form_id}',
                ':sk': 'METADATA'
            }
        )
        
        if not response.get('Items'):
            raise HTTPException(status_code=404, detail="Form not found")
        
        item = response['Items'][0]
        return FormResponse(
            form_id=item.get('form_id'),
            category=item.get('category'),
            domain=item.get('domain'),
            title=item.get('title'),
            content=item.get('content', {}),
            source_file=item.get('source_file'),
            created_at=item.get('created_at'),
            updated_at=item.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving form: {str(e)}")

@router.put("/forms/{form_id}", response_model=FormResponse)
async def update_form(form_id: str, form_update: FormUpdateRequest):
    """
    Update an existing form's content and metadata.
    """
    try:
        table = get_db()
        
        # First, get the existing form to preserve some metadata
        existing_response = table.query(
            KeyConditionExpression='PK = :pk AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': f'FORM#{form_id}',
                ':sk': 'METADATA'
            }
        )
        
        if not existing_response.get('Items'):
            raise HTTPException(status_code=404, detail="Form not found")
        
        existing_item = existing_response['Items'][0]
        
        # Prepare update expression
        update_expression = "SET updated_at = :updated_at"
        expression_attribute_values = {
            ':updated_at': datetime.utcnow().isoformat()
        }
        
        # Update title if provided
        if form_update.title is not None:
            update_expression += ", title = :title"
            expression_attribute_values[':title'] = form_update.title
        
        # Update content
        update_expression += ", content = :content"
        expression_attribute_values[':content'] = form_update.content
        
        # Perform the update
        table.update_item(
            Key={
                'PK': f'FORM#{form_id}',
                'SK': 'METADATA'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        # Return the updated form
        updated_response = table.query(
            KeyConditionExpression='PK = :pk AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': f'FORM#{form_id}',
                ':sk': 'METADATA'
            }
        )
        
        updated_item = updated_response['Items'][0]
        return FormResponse(
            form_id=updated_item.get('form_id'),
            category=updated_item.get('category'),
            domain=updated_item.get('domain'),
            title=updated_item.get('title'),
            content=updated_item.get('content', {}),
            source_file=updated_item.get('source_file'),
            created_at=updated_item.get('created_at'),
            updated_at=updated_item.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating form: {str(e)}")

@router.post("/forms", response_model=FormResponse)
async def create_form(form_create: FormCreateRequest):
    """
    Create a new form.
    """
    try:
        table = get_db()
        
        # Generate new form ID
        form_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Determine domain based on category
        domain_mapping = {
            'A': 'handwriting', 'B': 'handwriting', 'C': 'handwriting', 'D': 'handwriting',
            'E': 'handwriting', 'F': 'handwriting', 'G': 'handwriting', 'H': 'handwriting',
            'I': 'vocabulary', 'J': 'vocabulary', 'K': 'vocabulary', 'L': 'vocabulary',
            'M': 'ideas', 'N': 'ideas', 'O': 'ideas', 'P': 'general', 'Q': 'general'
        }
        
        domain = domain_mapping.get(form_create.category.upper(), 'general')
        
        # Create the form item
        item = {
            'PK': f'FORM#{form_id}',
            'SK': 'METADATA',
            'type': 'Form',
            'form_id': form_id,
            'category': form_create.category.upper(),
            'domain': domain,
            'title': form_create.title,
            'content': form_create.content,
            'source_file': f'admin_created_{form_id}.json',
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Insert into DynamoDB
        table.put_item(Item=item)
        
        return FormResponse(
            form_id=item['form_id'],
            category=item['category'],
            domain=item['domain'],
            title=item['title'],
            content=item['content'],
            source_file=item['source_file'],
            created_at=item['created_at'],
            updated_at=item['updated_at']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating form: {str(e)}")

@router.delete("/forms/{form_id}")
async def delete_form(form_id: str):
    """
    Delete a form by its ID.
    """
    try:
        table = get_db()
        
        # Check if form exists
        existing_response = table.query(
            KeyConditionExpression='PK = :pk AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': f'FORM#{form_id}',
                ':sk': 'METADATA'
            }
        )
        
        if not existing_response.get('Items'):
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Delete the form
        table.delete_item(
            Key={
                'PK': f'FORM#{form_id}',
                'SK': 'METADATA'
            }
        )
        
        return {"message": "Form deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting form: {str(e)}")

@router.get("/forms/categories")
async def get_form_categories():
    """
    Get all available form categories and their domains.
    """
    return {
        "handwriting": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "vocabulary": ["I", "J", "K", "L"],
        "ideas": ["M", "N", "O"],
        "general": ["P", "Q"]
    }

@router.get("/forms/stats")
async def get_form_statistics():
    """
    Get statistics about forms in the database.
    """
    try:
        stats = form_retrieval_service.get_cache_status()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")
