"""
File-based database implementation for local development.
This provides persistent storage that mimics DynamoDB behavior using JSON files.
"""

import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

class FileDynamoDBTable:
    """File-based DynamoDB table implementation using JSON files for persistence."""
    
    def __init__(self, table_name: str, data_dir: str = "data/dynamodb"):
        self.table_name = table_name
        self.data_dir = data_dir
        self.file_path = os.path.join(data_dir, f"{table_name}.json")
        self.items = {}  # Store items as {PK#SK: item}
        self.indexes = {
            'TypeIndex': defaultdict(list),
            'CategoryIndex': defaultdict(list)
        }
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = data.get('items', {})
                    self.indexes = data.get('indexes', {
                        'TypeIndex': defaultdict(list),
                        'CategoryIndex': defaultdict(list)
                    })
                
                # Rebuild indexes from items to ensure consistency
                self._rebuild_indexes()
                print(f"Loaded {len(self.items)} items from {self.file_path}")
                print(f"CategoryIndex has {len(self.indexes['CategoryIndex'])} categories")
            except Exception as e:
                print(f"Error loading data: {e}")
                self.items = {}
                self.indexes = {
                    'TypeIndex': defaultdict(list),
                    'CategoryIndex': defaultdict(list)
                }
    
    def _rebuild_indexes(self):
        """Rebuild all indexes from the current items."""
        # Clear existing indexes
        self.indexes = {
            'TypeIndex': defaultdict(list),
            'CategoryIndex': defaultdict(list)
        }
        
        # Rebuild indexes from items
        for item in self.items.values():
            item_type = item.get('type')
            category = item.get('category')
            
            if item_type:
                self.indexes['TypeIndex'][item_type].append(item)
            
            if category:
                self.indexes['CategoryIndex'][category].append(item)
    
    def _save_data(self):
        """Save data to JSON file."""
        try:
            # Convert defaultdict to regular dict for JSON serialization
            indexes_data = {}
            for index_name, index_data in self.indexes.items():
                indexes_data[index_name] = dict(index_data)
            
            data = {
                'items': self.items,
                'indexes': indexes_data,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def put_item(self, Item: Dict[str, Any]) -> Dict[str, Any]:
        """Put an item into the table."""
        pk = Item.get('PK')
        sk = Item.get('SK')
        
        if not pk or not sk:
            raise ValueError("PK and SK are required")
        
        key = f"{pk}#{sk}"
        self.items[key] = Item.copy()
        
        # Update indexes
        item_type = Item.get('type')
        category = Item.get('category')
        
        if item_type:
            # Remove old entries for this item
            self.indexes['TypeIndex'][item_type] = [
                item for item in self.indexes['TypeIndex'][item_type]
                if not (item.get('PK') == pk and item.get('SK') == sk)
            ]
            self.indexes['TypeIndex'][item_type].append(Item)
        
        if category:
            # Remove old entries for this item
            self.indexes['CategoryIndex'][category] = [
                item for item in self.indexes['CategoryIndex'][category]
                if not (item.get('PK') == pk and item.get('SK') == sk)
            ]
            self.indexes['CategoryIndex'][category].append(Item)
        
        # Save to file
        self._save_data()
        
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}
    
    def get_item(self, Key: Dict[str, str]) -> Dict[str, Any]:
        """Get an item from the table."""
        pk = Key.get('PK')
        sk = Key.get('SK')
        
        if not pk or not sk:
            raise ValueError("PK and SK are required")
        
        key = f"{pk}#{sk}"
        item = self.items.get(key)
        
        if item:
            return {'Item': item}
        else:
            return {}
    
    def query(self, **kwargs) -> Dict[str, Any]:
        """Query the table."""
        if 'KeyConditionExpression' in kwargs:
            # Simple key condition query
            pk = kwargs.get('ExpressionAttributeValues', {}).get(':pk')
            sk = kwargs.get('ExpressionAttributeValues', {}).get(':sk')
            
            if pk and sk:
                key = f"{pk}#{sk}"
                item = self.items.get(key)
                return {'Items': [item] if item else []}
            elif pk:
                # Query by PK only
                items = [item for key, item in self.items.items() if key.startswith(f"{pk}#")]
                return {'Items': items}
        
        # Index queries
        if 'IndexName' in kwargs:
            index_name = kwargs['IndexName']
            if index_name in self.indexes:
                if 'KeyConditionExpression' in kwargs:
                    # Handle different index types
                    key_condition = kwargs['KeyConditionExpression']
                    key_values = kwargs.get('ExpressionAttributeValues', {})
                    
                    if 'category = :cat' in key_condition:
                        # CategoryIndex query
                        category_value = key_values.get(':cat')
                        if category_value:
                            items = self.indexes['CategoryIndex'].get(category_value, [])
                            return {'Items': items}
                    
                    elif '#type = :type_val' in key_condition:
                        # TypeIndex query
                        type_value = key_values.get(':type_val')
                        if type_value:
                            items = self.indexes['TypeIndex'].get(type_value, [])
                            
                            # Apply filter if present
                            if 'FilterExpression' in kwargs:
                                filter_attr = kwargs.get('ExpressionAttributeNames', {}).get('#grade', 'grade')
                                filter_value = kwargs.get('ExpressionAttributeValues', {}).get(':grade')
                                
                                if filter_attr == 'grade' and filter_value:
                                    items = [item for item in items if item.get('grade') == filter_value]
                            
                            return {'Items': items}
        
        return {'Items': []}
    
    def scan(self, **kwargs) -> Dict[str, Any]:
        """Scan the table."""
        items = list(self.items.values())
        
        # Apply filters
        if 'FilterExpression' in kwargs and 'ExpressionAttributeValues' in kwargs:
            filter_expr = kwargs['FilterExpression']
            attr_values = kwargs['ExpressionAttributeValues']
            attr_names = kwargs.get('ExpressionAttributeNames', {})
            
            # Handle simple equality filters like 'source_file = :filename'
            if 'source_file = :filename' in filter_expr:
                filename = attr_values.get(':filename')
                if filename:
                    items = [item for item in items if item.get('source_file') == filename]
            elif 'type = :type' in filter_expr or '#type = :type' in filter_expr:
                type_value = attr_values.get(':type')
                if type_value:
                    items = [item for item in items if item.get('type') == type_value]
            elif 'email = :email' in filter_expr:
                # Handle email filter
                email = attr_values.get(':email')
                type_value = attr_values.get(':type')
                if email:
                    items = [item for item in items if item.get('email') == email]
                    # Also filter by type if provided
                    if type_value:
                        items = [item for item in items if item.get('type') == type_value]
            elif 'email = :email AND #type = :type' in filter_expr:
                # Handle combined email and type filter
                email = attr_values.get(':email')
                type_value = attr_values.get(':type')
                if email and type_value:
                    items = [
                        item for item in items 
                        if item.get('email') == email and item.get('type') == type_value
                    ]
        
        return {'Items': items}
    
    def delete_item(self, Key: Dict[str, str]) -> Dict[str, Any]:
        """Delete an item from the table."""
        pk = Key.get('PK')
        sk = Key.get('SK')
        
        if not pk or not sk:
            raise ValueError("PK and SK are required")
        
        key = f"{pk}#{sk}"
        if key in self.items:
            del self.items[key]
            
            # Remove from indexes
            for index_name, index_data in self.indexes.items():
                for category, items in index_data.items():
                    self.indexes[index_name][category] = [
                        item for item in items 
                        if not (item.get('PK') == pk and item.get('SK') == sk)
                    ]
            
            # Save to file
            self._save_data()
        
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}
    
    def update_item(self, Key: Dict[str, str], UpdateExpression: str, 
                   ExpressionAttributeValues: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Update an item in the table."""
        pk = Key.get('PK')
        sk = Key.get('SK')
        
        if not pk or not sk:
            raise ValueError("PK and SK are required")
        
        key = f"{pk}#{sk}"
        if key not in self.items:
            raise ValueError("Item not found")
        
        # Simple update - just replace the item
        if 'ReturnValues' in kwargs and kwargs['ReturnValues'] == 'ALL_NEW':
            # Update the item with new values
            item = self.items[key].copy()
            for attr_name, attr_value in ExpressionAttributeValues.items():
                if attr_name.startswith(':'):
                    field_name = attr_name[1:]  # Remove the ':'
                    item[field_name] = attr_value
            
            self.items[key] = item
            
            # Update indexes
            item_type = item.get('type')
            category = item.get('category')
            
            if item_type:
                # Remove old entries and add new one
                self.indexes['TypeIndex'][item_type] = [
                    i for i in self.indexes['TypeIndex'][item_type]
                    if not (i.get('PK') == pk and i.get('SK') == sk)
                ]
                self.indexes['TypeIndex'][item_type].append(item)
            
            if category:
                # Remove old entries and add new one
                self.indexes['CategoryIndex'][category] = [
                    i for i in self.indexes['CategoryIndex'][category]
                    if not (i.get('PK') == pk and i.get('SK') == sk)
                ]
                self.indexes['CategoryIndex'][category].append(item)
            
            # Save to file
            self._save_data()
            
            return {'Attributes': item}
        
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}

class FileDynamoDB:
    """File-based DynamoDB resource."""
    
    def __init__(self, data_dir: str = "backend/data/dynamodb"):
        self.data_dir = data_dir
        self.tables = {}
    
    def Table(self, table_name: str) -> FileDynamoDBTable:
        """Get or create a table."""
        if table_name not in self.tables:
            self.tables[table_name] = FileDynamoDBTable(table_name, self.data_dir)
        return self.tables[table_name]
    
    def create_table(self, **kwargs) -> FileDynamoDBTable:
        """Create a table."""
        table_name = kwargs['TableName']
        table = FileDynamoDBTable(table_name, self.data_dir)
        self.tables[table_name] = table
        return table

# Global file-based DynamoDB instance
file_dynamodb = FileDynamoDB()

def get_file_db():
    """Get the file-based database table."""
    return file_dynamodb.Table("EdTechChatbotTable-local")

def initialize_file_database():
    """Initialize the file-based database."""
    print("Initializing file-based database...")
    table = get_file_db()
    print("File-based database initialized successfully")
    return True

def test_file_connection():
    """Test the file-based database connection."""
    try:
        table = get_file_db()
        print("File-based database connection test successful")
        return True
    except Exception as e:
        print(f"File-based database connection test failed: {e}")
        return False

