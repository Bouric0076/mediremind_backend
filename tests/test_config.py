import os
import sys
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import tempfile
import shutil
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestConfig:
    """Configuration for test environment"""
    
    # Test database settings
    TEST_DATABASE_URL = "postgresql://test_user:test_pass@localhost:5432/test_mediremind"
    
    # Test Supabase settings
    TEST_SUPABASE_URL = "https://test.supabase.co"
    TEST_SUPABASE_KEY = "test_key_123"
    
    # Test notification settings
    TEST_SMS_PROVIDER = "test_sms"
    TEST_EMAIL_PROVIDER = "test_email"
    TEST_PUSH_PROVIDER = "test_push"
    
    # Test cache settings
    TEST_REDIS_URL = "redis://localhost:6379/1"
    TEST_CACHE_TTL = 300
    
    # Test file paths
    TEST_LOG_DIR = tempfile.mkdtemp(prefix="mediremind_test_logs_")
    TEST_DATA_DIR = tempfile.mkdtemp(prefix="mediremind_test_data_")
    
    # Test timing settings
    TEST_SCHEDULER_INTERVAL = 0.1  # 100ms for faster testing
    TEST_QUEUE_PROCESS_INTERVAL = 0.1
    TEST_BACKGROUND_TASK_INTERVAL = 1
    
    @classmethod
    def setup_test_environment(cls):
        """Set up the test environment"""
        # Set environment variables for testing
        os.environ['TESTING'] = 'true'
        os.environ['DATABASE_URL'] = cls.TEST_DATABASE_URL
        os.environ['SUPABASE_URL'] = cls.TEST_SUPABASE_URL
        os.environ['SUPABASE_KEY'] = cls.TEST_SUPABASE_KEY
        os.environ['LOG_DIR'] = cls.TEST_LOG_DIR
        os.environ['DATA_DIR'] = cls.TEST_DATA_DIR
        
        # Create test directories
        os.makedirs(cls.TEST_LOG_DIR, exist_ok=True)
        os.makedirs(cls.TEST_DATA_DIR, exist_ok=True)
    
    @classmethod
    def cleanup_test_environment(cls):
        """Clean up the test environment"""
        # Remove test directories
        if os.path.exists(cls.TEST_LOG_DIR):
            shutil.rmtree(cls.TEST_LOG_DIR)
        if os.path.exists(cls.TEST_DATA_DIR):
            shutil.rmtree(cls.TEST_DATA_DIR)
        
        # Clean up environment variables
        test_env_vars = ['TESTING', 'DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_KEY', 'LOG_DIR', 'DATA_DIR']
        for var in test_env_vars:
            if var in os.environ:
                del os.environ[var]

class MockSupabaseClient:
    """Mock Supabase client for testing"""
    
    def __init__(self):
        self.data_store = {}
        self.call_log = []
    
    def table(self, table_name: str):
        """Mock table method"""
        return MockSupabaseTable(table_name, self)
    
    def auth(self):
        """Mock auth method"""
        return MockSupabaseAuth()
    
    def storage(self):
        """Mock storage method"""
        return MockSupabaseStorage()
    
    def reset_mock(self):
        """Reset mock state"""
        self.data_store.clear()
        self.call_log.clear()

class MockSupabaseTable:
    """Mock Supabase table operations"""
    
    def __init__(self, table_name: str, client: MockSupabaseClient):
        self.table_name = table_name
        self.client = client
        self.query_builder = MockQueryBuilder(table_name, client)
    
    def select(self, columns: str = "*"):
        """Mock select operation"""
        self.client.call_log.append(('select', self.table_name, columns))
        return self.query_builder
    
    def insert(self, data: Dict[str, Any]):
        """Mock insert operation"""
        self.client.call_log.append(('insert', self.table_name, data))
        return self.query_builder
    
    def update(self, data: Dict[str, Any]):
        """Mock update operation"""
        self.client.call_log.append(('update', self.table_name, data))
        return self.query_builder
    
    def delete(self):
        """Mock delete operation"""
        self.client.call_log.append(('delete', self.table_name))
        return self.query_builder
    
    def upsert(self, data: Dict[str, Any]):
        """Mock upsert operation"""
        self.client.call_log.append(('upsert', self.table_name, data))
        return self.query_builder

class MockQueryBuilder:
    """Mock Supabase query builder"""
    
    def __init__(self, table_name: str, client: MockSupabaseClient):
        self.table_name = table_name
        self.client = client
        self.filters = []
        self.order_by_clause = None
        self.limit_clause = None
    
    def eq(self, column: str, value: Any):
        """Mock equality filter"""
        self.filters.append(('eq', column, value))
        return self
    
    def neq(self, column: str, value: Any):
        """Mock not equal filter"""
        self.filters.append(('neq', column, value))
        return self
    
    def gt(self, column: str, value: Any):
        """Mock greater than filter"""
        self.filters.append(('gt', column, value))
        return self
    
    def gte(self, column: str, value: Any):
        """Mock greater than or equal filter"""
        self.filters.append(('gte', column, value))
        return self
    
    def lt(self, column: str, value: Any):
        """Mock less than filter"""
        self.filters.append(('lt', column, value))
        return self
    
    def lte(self, column: str, value: Any):
        """Mock less than or equal filter"""
        self.filters.append(('lte', column, value))
        return self
    
    def like(self, column: str, pattern: str):
        """Mock like filter"""
        self.filters.append(('like', column, pattern))
        return self
    
    def ilike(self, column: str, pattern: str):
        """Mock case-insensitive like filter"""
        self.filters.append(('ilike', column, pattern))
        return self
    
    def is_(self, column: str, value: Any):
        """Mock is filter"""
        self.filters.append(('is', column, value))
        return self
    
    def in_(self, column: str, values: list):
        """Mock in filter"""
        self.filters.append(('in', column, values))
        return self
    
    def order(self, column: str, desc: bool = False):
        """Mock order by"""
        self.order_by_clause = (column, desc)
        return self
    
    def limit(self, count: int):
        """Mock limit"""
        self.limit_clause = count
        return self
    
    def execute(self):
        """Mock execute operation"""
        # Generate mock response based on table and operation
        if self.table_name not in self.client.data_store:
            self.client.data_store[self.table_name] = []
        
        # For testing, return predefined responses
        mock_data = self._generate_mock_data()
        
        return MockSupabaseResponse(mock_data)
    
    def _generate_mock_data(self) -> list:
        """Generate mock data based on table name and filters"""
        if self.table_name == 'scheduled_reminders':
            return [
                {
                    'id': 'reminder_1',
                    'appointment_id': 'appt_123',
                    'user_id': 'user_456',
                    'scheduled_time': datetime.now().isoformat(),
                    'message': 'Test reminder',
                    'status': 'pending',
                    'priority': 'medium'
                }
            ]
        elif self.table_name == 'delivery_attempts':
            return [
                {
                    'id': 'attempt_1',
                    'task_id': 'task_123',
                    'method': 'email',
                    'status': 'success',
                    'attempted_at': datetime.now().isoformat()
                }
            ]
        elif self.table_name == 'notification_logs':
            return [
                {
                    'id': 'log_1',
                    'level': 'info',
                    'message': 'Test log message',
                    'timestamp': datetime.now().isoformat(),
                    'category': 'scheduler'
                }
            ]
        elif self.table_name == 'system_metrics':
            return [
                {
                    'id': 'metric_1',
                    'metric_name': 'queue_size',
                    'metric_value': 10,
                    'timestamp': datetime.now().isoformat()
                }
            ]
        else:
            return []

class MockSupabaseResponse:
    """Mock Supabase response"""
    
    def __init__(self, data: list):
        self.data = data
        self.count = len(data) if data else 0
        self.error = None
        self.status_code = 200

class MockSupabaseAuth:
    """Mock Supabase auth"""
    
    def sign_in_with_password(self, credentials: Dict[str, str]):
        """Mock sign in"""
        return MockSupabaseResponse([{'user': {'id': 'test_user'}}])
    
    def sign_out(self):
        """Mock sign out"""
        return MockSupabaseResponse([])
    
    def get_user(self):
        """Mock get user"""
        return MockSupabaseResponse([{'user': {'id': 'test_user'}}])

class MockSupabaseStorage:
    """Mock Supabase storage"""
    
    def from_(self, bucket: str):
        """Mock storage bucket"""
        return MockStorageBucket(bucket)

class MockStorageBucket:
    """Mock storage bucket"""
    
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
    
    def upload(self, path: str, file_data: bytes):
        """Mock file upload"""
        return MockSupabaseResponse([{'path': path}])
    
    def download(self, path: str):
        """Mock file download"""
        return b"mock file content"
    
    def list(self, path: str = ""):
        """Mock file listing"""
        return MockSupabaseResponse([{'name': 'test_file.txt'}])

class MockNotificationProviders:
    """Mock notification providers for testing"""
    
    class MockSMSProvider:
        def __init__(self):
            self.sent_messages = []
            self.should_fail = False
        
        def send(self, phone_number: str, message: str) -> bool:
            if self.should_fail:
                return False
            self.sent_messages.append({
                'phone_number': phone_number,
                'message': message,
                'timestamp': datetime.now()
            })
            return True
        
        def get_delivery_status(self, message_id: str) -> str:
            return "delivered" if not self.should_fail else "failed"
    
    class MockEmailProvider:
        def __init__(self):
            self.sent_emails = []
            self.should_fail = False
        
        def send(self, email: str, subject: str, message: str) -> bool:
            if self.should_fail:
                return False
            self.sent_emails.append({
                'email': email,
                'subject': subject,
                'message': message,
                'timestamp': datetime.now()
            })
            return True
        
        def get_delivery_status(self, message_id: str) -> str:
            return "delivered" if not self.should_fail else "failed"
    
    class MockPushProvider:
        def __init__(self):
            self.sent_notifications = []
            self.should_fail = False
        
        def send(self, device_token: str, title: str, message: str) -> bool:
            if self.should_fail:
                return False
            self.sent_notifications.append({
                'device_token': device_token,
                'title': title,
                'message': message,
                'timestamp': datetime.now()
            })
            return True
        
        def get_delivery_status(self, message_id: str) -> str:
            return "delivered" if not self.should_fail else "failed"

class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_test_user(user_id: str = "test_user_123") -> Dict[str, Any]:
        """Create test user data"""
        return {
            'id': user_id,
            'email': f'{user_id}@test.com',
            'phone': '+1234567890',
            'name': f'Test User {user_id}',
            'created_at': datetime.now().isoformat(),
            'preferences': {
                'email_notifications': True,
                'sms_notifications': True,
                'push_notifications': True
            }
        }
    
    @staticmethod
    def create_test_appointment(appointment_id: str = "test_appt_123", user_id: str = "test_user_123") -> Dict[str, Any]:
        """Create test appointment data"""
        return {
            'id': appointment_id,
            'user_id': user_id,
            'doctor_name': 'Dr. Test',
            'appointment_time': (datetime.now() + timedelta(days=1)).isoformat(),
            'status': 'scheduled',
            'type': 'consultation',
            'location': 'Test Clinic',
            'notes': 'Test appointment notes'
        }
    
    @staticmethod
    def create_test_reminder(reminder_id: str = "test_reminder_123", appointment_id: str = "test_appt_123") -> Dict[str, Any]:
        """Create test reminder data"""
        return {
            'id': reminder_id,
            'appointment_id': appointment_id,
            'user_id': 'test_user_123',
            'scheduled_time': (datetime.now() + timedelta(hours=1)).isoformat(),
            'message': 'Test reminder message',
            'status': 'pending',
            'priority': 'medium',
            'delivery_methods': ['email', 'sms']
        }
    
    @staticmethod
    def create_test_notification(notification_id: str = "test_notif_123") -> Dict[str, Any]:
        """Create test notification data"""
        return {
            'id': notification_id,
            'user_id': 'test_user_123',
            'type': 'reminder',
            'title': 'Test Notification',
            'message': 'This is a test notification',
            'scheduled_time': datetime.now().isoformat(),
            'delivery_methods': ['email'],
            'status': 'pending'
        }

class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and teardown"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        TestConfig.setup_test_environment()
    
    @classmethod
    def tearDownClass(cls):
        """Tear down test class"""
        TestConfig.cleanup_test_environment()
    
    def setUp(self):
        """Set up individual test"""
        # Create mock Supabase client
        self.mock_supabase = MockSupabaseClient()
        
        # Create mock notification providers
        self.mock_providers = MockNotificationProviders()
        self.mock_sms_provider = self.mock_providers.MockSMSProvider()
        self.mock_email_provider = self.mock_providers.MockEmailProvider()
        self.mock_push_provider = self.mock_providers.MockPushProvider()
        
        # Patch Supabase client
        self.supabase_patcher = patch('notifications.scheduler.supabase', self.mock_supabase)
        self.supabase_patcher.start()
        
        # Patch other modules that use Supabase
        modules_to_patch = [
            'notifications.queue_manager.supabase',
            'notifications.background_tasks.supabase',
            'notifications.failsafe.supabase',
            'notifications.logging_config.supabase',
            'notifications.monitoring.supabase',
            'notifications.performance.supabase',
            'notifications.database_optimization.supabase'
        ]
        
        self.additional_patchers = []
        for module_path in modules_to_patch:
            try:
                patcher = patch(module_path, self.mock_supabase)
                patcher.start()
                self.additional_patchers.append(patcher)
            except ImportError:
                # Module might not exist or import might fail
                pass
    
    def tearDown(self):
        """Tear down individual test"""
        # Stop all patchers
        self.supabase_patcher.stop()
        for patcher in self.additional_patchers:
            patcher.stop()
        
        # Reset mock state
        self.mock_supabase.reset_mock()
    
    def assert_supabase_called_with(self, operation: str, table: str, data: Optional[Dict[str, Any]] = None):
        """Assert that Supabase was called with specific parameters"""
        calls = [call for call in self.mock_supabase.call_log if call[0] == operation and call[1] == table]
        self.assertGreater(len(calls), 0, f"Expected {operation} operation on {table} table")
        
        if data:
            # Check if any call contains the expected data
            found_matching_call = False
            for call in calls:
                if len(call) > 2 and call[2] == data:
                    found_matching_call = True
                    break
            self.assertTrue(found_matching_call, f"Expected call with data {data} not found")
    
    def create_test_data(self):
        """Create common test data"""
        self.test_user = TestDataFactory.create_test_user()
        self.test_appointment = TestDataFactory.create_test_appointment()
        self.test_reminder = TestDataFactory.create_test_reminder()
        self.test_notification = TestDataFactory.create_test_notification()

# Test utilities
def run_async_test(async_func):
    """Decorator to run async tests"""
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

def with_timeout(timeout_seconds: float = 5.0):
    """Decorator to add timeout to tests"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Test timed out after {timeout_seconds} seconds")
            
            # Set up timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout_seconds))
            
            try:
                return func(*args, **kwargs)
            finally:
                # Clean up timeout
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

# Export commonly used classes and functions
__all__ = [
    'TestConfig',
    'MockSupabaseClient',
    'MockNotificationProviders',
    'TestDataFactory',
    'BaseTestCase',
    'run_async_test',
    'with_timeout'
]