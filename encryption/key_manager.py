"""
Encryption Key Management Service

This module provides secure encryption key management with automatic re-encryption
capabilities for when keys are rotated or compromised.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import transaction
from django.core.cache import cache

logger = logging.getLogger(__name__)


class EncryptionKeyManager:
    """
    Manages encryption keys with automatic re-encryption capabilities.
    Supports key rotation and secure key storage.
    """
    
    def __init__(self):
        self.current_key_version = self._get_current_key_version()
        self.keys = self._load_keys()
        self.primary_key = self.keys.get(self.current_key_version)
        
    def _get_current_key_version(self) -> str:
        """Get the current key version from settings or environment"""
        return getattr(settings, 'ENCRYPTION_KEY_VERSION', 'v1')
    
    def _load_keys(self) -> Dict[str, Fernet]:
        """Load all available encryption keys"""
        keys = {}
        
        # Load primary key from settings
        primary_key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
        if primary_key:
            keys[self.current_key_version] = Fernet(primary_key.encode())
            
        # Load backup keys if available
        backup_keys = getattr(settings, 'ENCRYPTION_BACKUP_KEYS', {})
        for version, key in backup_keys.items():
            try:
                keys[version] = Fernet(key.encode())
            except Exception as e:
                logger.warning(f"Failed to load backup key {version}: {e}")
                
        return keys
    
    def encrypt(self, data: str, key_version: Optional[str] = None) -> str:
        """
        Encrypt data using the specified key version or primary key
        
        Args:
            data: The plaintext data to encrypt
            key_version: Optional key version to use (defaults to current)
            
        Returns:
            Encrypted data as a Fernet token
        """
        if not data:
            return data
            
        key = self.keys.get(key_version, self.primary_key)
        if not key:
            raise ValueError(f"No encryption key available for version: {key_version}")
            
        try:
            encrypted = key.encrypt(data.encode()).decode()
            # Add key version prefix for tracking
            actual_version = key_version or self.current_key_version
            return f"{actual_version}:{encrypted}"
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data by trying all available keys
        
        Args:
            encrypted_data: The encrypted Fernet token
            
        Returns:
            Decrypted plaintext data
        """
        if not encrypted_data:
            return encrypted_data
            
        # Check if data includes version prefix
        if ':' in encrypted_data:
            key_version, token = encrypted_data.split(':', 1)
            if key_version in self.keys:
                try:
                    return self.keys[key_version].decrypt(token.encode()).decode()
                except Exception as e:
                    logger.warning(f"Failed to decrypt with key {key_version}: {e}")
                    # Fall back to trying all keys
        
        # Try all available keys
        for version, key in self.keys.items():
            try:
                # Try without version prefix first
                return key.decrypt(encrypted_data.encode()).decode()
            except Exception:
                try:
                    # Try with version prefix
                    return key.decrypt(f"{version}:{encrypted_data}".encode()).decode()
                except Exception:
                    continue
        
        # Try legacy decryption method (original EncryptedCharField)
        try:
            from cryptography.fernet import Fernet
            from django.conf import settings
            
            if hasattr(settings, 'FIELD_ENCRYPTION_KEY'):
                legacy_cipher = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
                decrypted = legacy_cipher.decrypt(encrypted_data.encode())
                return decrypted.decode('utf-8')
        except Exception:
            pass
                    
        logger.error(f"Failed to decrypt data with any available key")
        return encrypted_data  # Return as-is if decryption fails
    
    def rotate_key(self, new_key: str, reencrypt_data: bool = True) -> bool:
        """
        Rotate to a new encryption key
        
        Args:
            new_key: The new Fernet key
            reencrypt_data: Whether to re-encrypt existing data
            
        Returns:
            True if rotation was successful
        """
        try:
            new_fernet = Fernet(new_key.encode())
            new_version = f"v{int(self.current_key_version[1:]) + 1}"
            
            # Store current key as backup
            backup_keys = getattr(settings, 'ENCRYPTION_BACKUP_KEYS', {})
            backup_keys[self.current_key_version] = getattr(settings, 'FIELD_ENCRYPTION_KEY')
            
            # Update settings
            settings.FIELD_ENCRYPTION_KEY = new_key
            settings.ENCRYPTION_BACKUP_KEYS = backup_keys
            settings.ENCRYPTION_KEY_VERSION = new_version
            
            # Update key manager state
            self.keys[new_version] = new_fernet
            self.keys[self.current_key_version] = Fernet(backup_keys[self.current_key_version].encode())
            self.current_key_version = new_version
            self.primary_key = new_fernet
            
            if reencrypt_data:
                self._reencrypt_all_data()
                
            logger.info(f"Encryption key rotated to version {new_version}")
            return True
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return False
    
    def _reencrypt_all_data(self):
        """Re-encrypt all encrypted data in the database"""
        from accounts.models import EnhancedPatient
        
        logger.info("Starting data re-encryption...")
        
        # Define encrypted fields
        encrypted_fields = [
            'phone', 'address_line1', 'address_line2', 'allergies',
            'medical_conditions', 'current_medications', 'insurance_provider',
            'insurance_policy_number', 'insurance_group_number'
        ]
        
        patients_updated = 0
        
        try:
            with transaction.atomic():
                for patient in EnhancedPatient.objects.all():
                    updated = False
                    
                    for field_name in encrypted_fields:
                        field_value = getattr(patient, field_name)
                        if field_value and self.is_encrypted(field_value):
                            # Decrypt with old key and re-encrypt with new key
                            try:
                                decrypted = self.decrypt(field_value)
                                if decrypted != field_value:  # Decryption was successful
                                    encrypted = self.encrypt(decrypted)
                                    setattr(patient, field_name, encrypted)
                                    updated = True
                            except Exception as e:
                                logger.warning(f"Failed to re-encrypt {field_name} for patient {patient.id}: {e}")
                    
                    if updated:
                        patient.save()
                        patients_updated += 1
                        
                    if patients_updated % 100 == 0:
                        logger.info(f"Re-encrypted {patients_updated} patients...")
                        
        except Exception as e:
            logger.error(f"Data re-encryption failed: {e}")
            raise
            
        logger.info(f"Data re-encryption completed. Updated {patients_updated} patients.")
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted"""
        if not value or not isinstance(value, str):
            return False
            
        # Check for version prefix format (e.g., "v1:token")
        if ':' in value:
            parts = value.split(':', 1)
            if len(parts) == 2 and parts[0] in ['v1', 'v2', 'legacy'] and len(parts[1]) >= 60:
                value = parts[1]
        
        # Check for Fernet token format
        if len(value) < 60:
            return False
            
        # Check for base64url encoding
        import base64
        try:
            decoded = base64.urlsafe_b64decode(value)
            # Fernet tokens have version byte 128
            return len(decoded) >= 57 and decoded[0] == 128
        except Exception:
            return False
    
    def get_key_info(self) -> Dict[str, Any]:
        """Get information about current encryption keys"""
        return {
            'current_version': self.current_key_version,
            'available_versions': list(self.keys.keys()),
            'backup_keys_count': len(self.keys) - 1,
            'primary_key_valid': self.primary_key is not None
        }


# Global instance
key_manager = EncryptionKeyManager()

def encrypt_field(data: str, key_version: Optional[str] = None) -> str:
    """Encrypt field data using the key manager"""
    return key_manager.encrypt(data, key_version)

def decrypt_field(data: str) -> str:
    """Decrypt field data using the key manager"""
    return key_manager.decrypt(data)

def is_encrypted_field(data: str) -> bool:
    """Check if field data appears to be encrypted"""
    return key_manager.is_encrypted(data)