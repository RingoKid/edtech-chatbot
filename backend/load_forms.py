#!/usr/bin/env python3
"""
Script to load educational forms from JSON files into DynamoDB.
This script runs automatically on container startup.
"""
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import initialize_database, get_db
from app.config import settings

# Form category mappings
FORM_CATEGORIES = {
    'A': 'handwriting', 'B': 'handwriting', 'C': 'handwriting', 'D': 'handwriting',
    'E': 'handwriting', 'F': 'handwriting', 'G': 'handwriting', 'H': 'handwriting',
    'I': 'vocabulary', 'J': 'vocabulary', 'K': 'vocabulary', 'L': 'vocabulary',
    'M': 'ideas', 'N': 'ideas', 'O': 'ideas',
    'P': 'general', 'Q': 'general'
}


def extract_category_from_filename(filename):
    """
    Extract form category from filename.

    Examples:
        Form-A.json -> A
        FORM-P.json -> P
        Example_Handwriting&Spelling.json -> None

    Args:
        filename: Name of the JSON file

    Returns:
        str: Category letter or None
    """
    # Remove extension
    name = filename.replace('.json', '')

    # Match Form-X pattern
    if 'Form-' in name or 'FORM-' in name:
        parts = name.split('-')
        if len(parts) >= 2:
            category = parts[-1].upper()
            if category in FORM_CATEGORIES:
                return category

    return None


def load_form_from_file(filepath):
    """
    Load a form from a JSON file and prepare it for DynamoDB.

    Args:
        filepath: Path to the JSON file

    Returns:
        dict: DynamoDB item or None if invalid
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = json.load(f)

        filename = os.path.basename(filepath)
        category = extract_category_from_filename(filename)

        if not category:
            print(f"Skipping {filename} - no category found")
            return None

        # Generate form ID
        form_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Determine title from content or filename
        title = filename.replace('.json', '').replace('Form-', '').replace('FORM-', '')

        # Try to extract title from JSON content
        if isinstance(content, dict):
            if 'title' in content:
                title = content['title']
            elif list(content.keys()):
                # Use first key's value if it has a title
                first_key = list(content.keys())[0]
                if isinstance(content[first_key], dict) and 'title' in content[first_key]:
                    title = content[first_key]['title']

        # Create DynamoDB item
        item = {
            'PK': f'FORM#{form_id}',
            'SK': 'METADATA',
            'type': 'Form',
            'form_id': form_id,
            'category': category,
            'domain': FORM_CATEGORIES.get(category, 'general'),
            'title': title,
            'content': content,
            'source_file': filename,
            'created_at': timestamp,
            'updated_at': timestamp
        }

        return item

    except json.JSONDecodeError as e:
        print(f"Error parsing {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def load_all_forms(forms_directory):
    """
    Load all JSON forms from the specified directory into DynamoDB.

    Args:
        forms_directory: Path to directory containing form JSON files

    Returns:
        tuple: (success_count, error_count)
    """
    forms_dir = Path(forms_directory)

    if not forms_dir.exists():
        print(f"Forms directory not found: {forms_directory}")
        return 0, 0

    # Get all JSON files
    json_files = list(forms_dir.glob('*.json'))

    if not json_files:
        print(f"No JSON files found in {forms_directory}")
        return 0, 0

    print(f"Found {len(json_files)} JSON files")

    # Get DynamoDB table
    table = get_db()

    success_count = 0
    error_count = 0

    for json_file in json_files:
        filename = json_file.name

        # Skip non-form files
        if filename in ['prek_standards.json', 'kindergarten_standards.json', 'Untitled.rtf']:
            print(f"Skipping {filename} - not a form file")
            continue

        print(f"Processing {filename}...")

        # Load form data
        item = load_form_from_file(json_file)

        if item:
            try:
                # Check if form already exists (by source file) - COMMENTED OUT TO FORCE RELOAD
                # response = table.scan(
                #     FilterExpression='source_file = :filename',
                #     ExpressionAttributeValues={':filename': filename}
                # )

                # if response['Items']:
                #     print(f"   Already exists, skipping")
                #     success_count += 1
                #     continue

                # Insert into DynamoDB
                table.put_item(Item=item)
                print(f"   Loaded Form {item['category']}: {item['title']}")
                success_count += 1

            except Exception as e:
                print(f"   Failed to insert: {e}")
                error_count += 1
        else:
            error_count += 1

    return success_count, error_count


def main():
    """Main execution function."""
    print("=" * 50)
    print("EdTech Chatbot - Form Loader")
    print("=" * 50)

    # Initialize database
    print("\nInitializing DynamoDB...")
    if not initialize_database():
        print("Failed to initialize database")
        sys.exit(1)

    # Determine forms directory
    # Try both relative paths (for Docker) and absolute paths (for local dev)
    possible_paths = [
        '/app/data/Forms_Json',  # Docker container path
        'data/Forms_Json',       # Relative path
        '../data/Forms_Json',    # If running from backend directory
        os.path.join(os.path.dirname(__file__), '../data/Forms_Json')
    ]

    forms_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            forms_dir = path
            break

    if not forms_dir:
        print(f"Could not find Forms_Json directory")
        print(f"   Tried: {possible_paths}")
        sys.exit(1)

    print(f"\nLoading forms from: {forms_dir}")

    # Load all forms
    success_count, error_count = load_all_forms(forms_dir)

    # Print summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"Successfully loaded: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total processed: {success_count + error_count}")
    print("=" * 50)

    if error_count > 0:
        sys.exit(1)

    print("\nForm loading complete!")


if __name__ == '__main__':
    main()