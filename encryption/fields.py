"""
Enhanced Encrypted Fields with Key Management

This module provides Django model fields with automatic key management
and backward compatibility for existing encrypted data.
"""

from django.db import models
from django.conf import settings
from encryption.key_manager import key_manager, encrypt_field, decrypt_field, is_encrypted_field
import logging

logger = logging.getLogger(__name__)


class EnhancedEncryptedCharField(models.CharField):
    """
    Enhanced encrypted character field with automatic key management.
    Supports multiple encryption keys and automatic decryption of legacy data.
    """
    
    def __init__(self, *args, **kwargs):
        # Support for legacy key specification
        self.legacy_key = kwargs.pop('legacy_key', None)
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """
        Convert value from database to Python object.
        Handles both legacy and new encrypted data.
        """
        if value is None:
            return value
            
        # Check if this is encrypted data
        if is_encrypted_field(value):
            try:
                # Use key manager to decrypt (handles multiple keys)
                decrypted = decrypt_field(value)
                return decrypted
            except Exception as e:
                logger.warning(f"Failed to decrypt field value: {e}")
                # For backward compatibility, return as-is if decryption fails
                return value
        
        # Return plain text as-is
        return value
    
    def to_python(self, value):
        """Convert value to Python object"""
        if isinstance(value, str) or value is None:
            return value
        return str(value)
    
    def get_prep_value(self, value):
        """
        Convert Python object to database value.
        Encrypts the value before storing in database.
        """
        if value is None:
            return value
            
        # Don't re-encrypt already encrypted data
        if is_encrypted_field(value):
            return value
            
        try:
            # Use key manager to encrypt with current key
            encrypted = encrypt_field(value)
            return encrypted
        except Exception as e:
            logger.error(f"Encryption failed for field: {e}")
            # Return original value if encryption fails
            return value
    
    def deconstruct(self):
        """Return field deconstruction for migrations"""
        name, path, args, kwargs = super().deconstruct()
        # Only include our custom kwargs if they differ from defaults
        if self.legacy_key:
            kwargs['legacy_key'] = self.legacy_key
        return name, path, args, kwargs


class EnhancedEncryptedTextField(models.TextField):
    """
    Enhanced encrypted text field with automatic key management.
    Supports multiple encryption keys and automatic decryption of legacy data.
    """
    
    def __init__(self, *args, **kwargs):
        self.legacy_key = kwargs.pop('legacy_key', None)
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """Convert value from database to Python object"""
        if value is None:
            return value
            
        if is_encrypted_field(value):
            try:
                decrypted = decrypt_field(value)
                return decrypted
            except Exception as e:
                logger.warning(f"Failed to decrypt text field value: {e}")
                return value
        
        return value
    
    def to_python(self, value):
        """Convert value to Python object"""
        if isinstance(value, str) or value is None:
            return value
        return str(value)
    
    def get_prep_value(self, value):
        """Convert Python object to database value"""
        if value is None:
            return value
            
        # Don't re-encrypt already encrypted data
        if is_encrypted_field(value):
            return value
            
        try:
            encrypted = encrypt_field(value)
            return encrypted
        except Exception as e:
            logger.error(f"Text field encryption failed: {e}")
            return value
    
    def deconstruct(self):
        """Return field deconstruction for migrations"""
        name, path, args, kwargs = super().deconstruct()
        if self.legacy_key:
            kwargs['legacy_key'] = self.legacy_key
        return name, path, args, kwargs


# Backward compatibility aliases
EncryptedCharField = EnhancedEncryptedCharField
EncryptedTextField = EnhancedEncryptedTextField