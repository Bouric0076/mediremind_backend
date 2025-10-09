"""
Token encryption utilities for calendar integrations.
Provides secure storage and retrieval of OAuth tokens.
"""

import base64
import os
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)


class TokenEncryption:
    """
    Handles encryption and decryption of OAuth tokens using Fernet symmetric encryption.
    """
    
    def __init__(self):
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)
    
    def _get_encryption_key(self):
        """
        Get or generate encryption key for token encryption.
        """
        # Try to get key from settings first
        if hasattr(settings, 'CALENDAR_TOKEN_ENCRYPTION_KEY'):
            key = settings.CALENDAR_TOKEN_ENCRYPTION_KEY
            if isinstance(key, str):
                key = key.encode()
            return key
        
        # Try to get from environment variable
        env_key = os.environ.get('CALENDAR_TOKEN_ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()
        
        # Generate a new key for development (not recommended for production)
        if settings.DEBUG:
            logger.warning("No encryption key found. Generating new key for development.")
            key = Fernet.generate_key()
            logger.warning(f"Generated encryption key: {key.decode()}")
            logger.warning("Please set CALENDAR_TOKEN_ENCRYPTION_KEY in your environment for production.")
            return key
        
        raise ImproperlyConfigured(
            "CALENDAR_TOKEN_ENCRYPTION_KEY must be set in settings or environment variables for production."
        )
    
    def encrypt_token(self, token):
        """
        Encrypt a token string.
        
        Args:
            token (str): The token to encrypt
            
        Returns:
            str: Base64 encoded encrypted token
        """
        if not token:
            return token
        
        try:
            # Convert to bytes if string
            if isinstance(token, str):
                token = token.encode('utf-8')
            
            # Encrypt the token
            encrypted_token = self.cipher.encrypt(token)
            
            # Return base64 encoded string for database storage
            return base64.b64encode(encrypted_token).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encrypting token: {e}")
            raise
    
    def decrypt_token(self, encrypted_token):
        """
        Decrypt an encrypted token.
        
        Args:
            encrypted_token (str): Base64 encoded encrypted token
            
        Returns:
            str: Decrypted token string
        """
        if not encrypted_token:
            return encrypted_token
        
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_token.encode('utf-8'))
            
            # Decrypt the token
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            
            # Return as string
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error decrypting token: {e}")
            # Return None to indicate decryption failure
            return None


# Global instance for use throughout the application (initialized lazily)
_token_encryption = None


def get_token_encryption():
    """
    Get or create the global token encryption instance.
    This is done lazily to avoid initialization errors during import.
    """
    global _token_encryption
    if _token_encryption is None:
        _token_encryption = TokenEncryption()
    return _token_encryption


def encrypt_token(token):
    """
    Convenience function to encrypt a token.
    """
    return get_token_encryption().encrypt_token(token)


def decrypt_token(encrypted_token):
    """
    Convenience function to decrypt a token.
    """
    return get_token_encryption().decrypt_token(encrypted_token)