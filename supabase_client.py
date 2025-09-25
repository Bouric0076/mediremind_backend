"""
Supabase client configuration for MediRemind Backend
"""

import os
import logging

logger = logging.getLogger(__name__)

# Try to import Django settings, but handle cases where it's not configured
try:
    from django.conf import settings
    SUPABASE_URL = getattr(settings, 'SUPABASE_URL', os.getenv('SUPABASE_URL'))
    SUPABASE_KEY = getattr(settings, 'SUPABASE_KEY', os.getenv('SUPABASE_KEY'))
    SUPABASE_SERVICE_KEY = getattr(settings, 'SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))
except:
    # Fallback to environment variables if Django settings are not configured
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Try to import Supabase client, but handle cases where it's not installed
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.warning("Supabase package not available, using mock client")
    SUPABASE_AVAILABLE = False
    Client = None

def create_supabase_client() -> Client:
    """Create a Supabase client instance"""
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase package not available")
        return None
        
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase URL or Key not configured")
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        return None

def create_admin_client() -> Client:
    """Create a Supabase admin client with service key"""
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase package not available")
        return None
        
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.warning("Supabase URL or Service Key not configured for admin client")
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        logger.error(f"Failed to create Supabase admin client: {str(e)}")
        return None

# Create client instances
supabase = create_supabase_client()
admin_client = create_admin_client()

# Mock client for development/testing when Supabase is not configured
class MockSupabaseClient:
    """Mock Supabase client for development/testing"""
    
    def __init__(self):
        self.table_data = {}
    
    def table(self, table_name: str):
        return MockTable(table_name, self.table_data)
    
    @property
    def auth(self):
        return MockAuth()

class MockTable:
    """Mock Supabase table for development/testing"""
    
    def __init__(self, table_name: str, data_store: dict):
        self.table_name = table_name
        self.data_store = data_store
        if table_name not in self.data_store:
            self.data_store[table_name] = []
    
    def select(self, columns: str = "*"):
        return MockQuery(self.table_name, self.data_store, "select", columns)
    
    def insert(self, data: dict):
        return MockQuery(self.table_name, self.data_store, "insert", data)
    
    def update(self, data: dict):
        return MockQuery(self.table_name, self.data_store, "update", data)
    
    def delete(self):
        return MockQuery(self.table_name, self.data_store, "delete")

class MockQuery:
    """Mock Supabase query for development/testing"""
    
    def __init__(self, table_name: str, data_store: dict, operation: str, data=None):
        self.table_name = table_name
        self.data_store = data_store
        self.operation = operation
        self.data = data
        self.filters = {}
    
    def eq(self, column: str, value):
        self.filters[column] = value
        return self
    
    def execute(self):
        """Execute the mock query"""
        if self.operation == "select":
            # Return filtered data
            result_data = []
            for item in self.data_store[self.table_name]:
                match = True
                for key, value in self.filters.items():
                    if item.get(key) != value:
                        match = False
                        break
                if match:
                    result_data.append(item)
            return MockResult(result_data)
        
        elif self.operation == "insert":
            # Add data to store
            if isinstance(self.data, list):
                self.data_store[self.table_name].extend(self.data)
            else:
                self.data_store[self.table_name].append(self.data)
            return MockResult(self.data)
        
        elif self.operation == "update":
            # Update matching records
            updated_count = 0
            for item in self.data_store[self.table_name]:
                match = True
                for key, value in self.filters.items():
                    if item.get(key) != value:
                        match = False
                        break
                if match:
                    item.update(self.data)
                    updated_count += 1
            return MockResult({"updated": updated_count})
        
        elif self.operation == "delete":
            # Delete matching records
            original_length = len(self.data_store[self.table_name])
            self.data_store[self.table_name] = [
                item for item in self.data_store[self.table_name]
                if not all(item.get(key) == value for key, value in self.filters.items())
            ]
            deleted_count = original_length - len(self.data_store[self.table_name])
            return MockResult({"deleted": deleted_count})
        
        return MockResult([])

class MockResult:
    """Mock Supabase result for development/testing"""
    
    def __init__(self, data):
        self.data = data

class MockAuth:
    """Mock Supabase auth for development/testing"""
    
    def sign_in_with_password(self, credentials: dict):
        return MockResult({"user": {"id": "mock_user_id", "email": credentials.get("email")}})

# Use mock clients if real ones are not available
if supabase is None:
    logger.info("Using mock Supabase client for development")
    supabase = MockSupabaseClient()

if admin_client is None:
    logger.info("Using mock Supabase admin client for development")
    admin_client = MockSupabaseClient()

__all__ = ['supabase', 'admin_client', 'create_supabase_client', 'create_admin_client']