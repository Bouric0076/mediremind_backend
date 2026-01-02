import hashlib
import hmac
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from cryptography.fernet import Fernet
import base64

class APIKeyGenerator:
    """Secure API key generation and management"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_api_secret() -> str:
        """Generate a secure API secret"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def generate_webhook_secret() -> str:
        """Generate a secure webhook secret"""
        return secrets.token_urlsafe(48)
    
    @staticmethod
    def hash_api_secret(secret: str) -> str:
        """Hash API secret for storage"""
        return hashlib.sha256(secret.encode()).hexdigest()

class DataEncryption:
    """Encryption utilities for sensitive data"""
    
    def __init__(self, key: Optional[str] = None):
        if key:
            self.key = key.encode() if isinstance(key, str) else key
        else:
            # Use Django's SECRET_KEY as base for encryption key
            self.key = base64.urlsafe_b64encode(
                hashlib.sha256(settings.SECRET_KEY.encode()).digest()[:32]
            )
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt dictionary data"""
        json_data = json.dumps(data)
        return self.encrypt_data(json_data)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt dictionary data"""
        json_data = self.decrypt_data(encrypted_data)
        return json.loads(json_data)

class RequestSignature:
    """HMAC signature verification for API requests"""
    
    @staticmethod
    def generate_signature(secret: str, payload: str, timestamp: str) -> str:
        """Generate HMAC signature"""
        message = f"{timestamp}:{payload}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(secret: str, payload: str, timestamp: str, signature: str, 
                        max_age: int = 300) -> bool:
        """Verify HMAC signature and timestamp"""
        # Check timestamp to prevent replay attacks
        try:
            request_time = datetime.fromtimestamp(int(timestamp))
            current_time = timezone.now()
            
            if abs((current_time - request_time).total_seconds()) > max_age:
                return False
        except (ValueError, TypeError):
            return False
        
        # Verify signature
        expected_signature = RequestSignature.generate_signature(secret, payload, timestamp)
        return hmac.compare_digest(expected_signature, signature)

class RateLimiter:
    """Rate limiting utilities"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
    
    def is_rate_limited(self, api_key: str, limit_type: str, limit: int, 
                       window_seconds: int = 3600) -> bool:
        """Check if request is rate limited"""
        if not self.redis_client:
            return False
        
        key = f"rate_limit:{api_key}:{limit_type}"
        current_count = self.redis_client.get(key) or 0
        
        if int(current_count) >= limit:
            return True
        
        # Increment counter
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        pipe.execute()
        
        return False
    
    def get_remaining_requests(self, api_key: str, limit_type: str, limit: int) -> int:
        """Get remaining requests for rate limit"""
        if not self.redis_client:
            return limit
        
        key = f"rate_limit:{api_key}:{limit_type}"
        current_count = self.redis_client.get(key) or 0
        return max(0, limit - int(current_count))

class DataValidator:
    """Data validation utilities for healthcare data"""
    
    @staticmethod
    def validate_patient_data(data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate patient data for compliance"""
        errors = []
        
        # Required fields
        required_fields = ['patient_id', 'name', 'phone', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate phone number format
        if 'phone' in data and data['phone']:
            import re
            phone_pattern = r'^\+?1?\d{9,15}$'
            if not re.match(phone_pattern, data['phone']):
                errors.append("Invalid phone number format")
        
        # Validate email format
        if 'email' in data and data['email']:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                errors.append("Invalid email format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_data(data: Dict[str, Any], allowed_fields: list) -> Dict[str, Any]:
        """Sanitize data to only include allowed fields"""
        return {k: v for k, v in data.items() if k in allowed_fields}
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data for logging"""
        masked_data = data.copy()
        
        # Fields to mask
        sensitive_fields = ['phone', 'email', 'national_id', 'insurance_number']
        
        for field in sensitive_fields:
            if field in masked_data and masked_data[field]:
                value = str(masked_data[field])
                if len(value) > 4:
                    masked_data[field] = f"{value[:2]}***{value[-2:]}"
                else:
                    masked_data[field] = "***"
        
        return masked_data

class ComplianceChecker:
    """Compliance checking utilities"""
    
    @staticmethod
    def check_data_retention_policy(created_at: datetime, retention_days: int) -> bool:
        """Check if data should be retained based on retention policy"""
        if not created_at:
            return False
        
        retention_date = created_at + timedelta(days=retention_days)
        return timezone.now() <= retention_date
    
    @staticmethod
    def check_consent_validity(granted_at: Optional[datetime], expires_at: Optional[datetime]) -> bool:
        """Check if consent is still valid"""
        if not granted_at:
            return False
        
        if expires_at and timezone.now() > expires_at:
            return False
        
        return True
    
    @staticmethod
    def check_cross_border_transfer_requirements(data_categories: list) -> dict:
        """Check requirements for cross-border data transfer"""
        sensitive_categories = ['health_data', 'biometric_data', 'genetic_data']
        has_sensitive_data = any(cat in data_categories for cat in sensitive_categories)
        
        requirements = {
            'requires_consent': has_sensitive_data,
            'requires_adequate_safeguards': True,
            'requires_odpc_approval': has_sensitive_data,
            'recommended_encryption': True,
            'recommended_anonymization': not has_sensitive_data
        }
        
        return requirements