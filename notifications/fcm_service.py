"""
Firebase Cloud Messaging (FCM) service for Django backend.
Handles FCM token registration, push notification sending, and topic management.
"""

import json
import requests
from django.conf import settings
from django.core.cache import cache
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta
from .models import PushSubscription, ScheduledTask
from authentication.models import User
# FCM v1 imports
import os
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleAuthRequest

logger = logging.getLogger(__name__)


class FCMService:
    """Service for handling Firebase Cloud Messaging operations"""
    
    def __init__(self):
        # FCM v1-only configuration
        self.project_id = getattr(settings, 'FCM_PROJECT_ID', None)
        self._credentials = None
        
        if not self.project_id:
            raise ValueError("FCM_PROJECT_ID is required for FCM v1 operation")
        
        self._credentials = self._load_service_account_credentials()
        if not self._credentials:
            raise ValueError("FCM v1 service account credentials are required but not properly configured")
        
        logger.info("FCM v1 service initialized successfully")
    
    def is_configured(self) -> bool:
        """Check if FCM is properly configured for v1-only mode"""
        return bool(self._credentials) and bool(self.project_id)

    def _load_service_account_credentials(self) -> Optional[service_account.Credentials]:
        """Load service account credentials from GOOGLE_APPLICATION_CREDENTIALS or env vars."""
        try:
            creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
            scopes = ['https://www.googleapis.com/auth/firebase.messaging']
            if creds_path:
                return service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
            info = {
                "type": "service_account",
                "project_id": os.getenv("FCM_PROJECT_ID") or self.project_id or "",
                "private_key_id": os.getenv("FCM_PRIVATE_KEY_ID", ""),
                "private_key": os.getenv("FCM_PRIVATE_KEY", ""),
                "client_email": os.getenv("FCM_CLIENT_EMAIL", ""),
                "client_id": os.getenv("FCM_CLIENT_ID", ""),
                "auth_uri": os.getenv("FCM_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("FCM_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("FCM_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": os.getenv("FCM_CLIENT_X509_CERT_URL", ""),
            }
            pk = info.get("private_key", "")
            if pk and "\\n" in pk:
                info["private_key"] = pk.replace("\\n", "\n")
            if info["project_id"] and info["private_key"] and info["client_email"]:
                return service_account.Credentials.from_service_account_info(info, scopes=scopes)
            return None
        except Exception as e:
            logger.error(f"Error loading FCM v1 service account credentials: {e}")
            return None

    def _get_access_token(self) -> Optional[str]:
        """Obtain OAuth2 access token for FCM v1."""
        try:
            if not self._credentials:
                return None
            self._credentials.refresh(GoogleAuthRequest())
            return self._credentials.token
        except Exception as e:
            logger.error(f"Error obtaining FCM v1 access token: {e}")
            return None

    def _v1_messages_send(self, message: Dict[str, Any]) -> (bool, str):
        """Send a single message using FCM HTTP v1."""
        access_token = self._get_access_token()
        if not access_token:
            return False, "FCM v1 access token unavailable"
        url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(url, headers=headers, json={"message": message}, timeout=30)
            if response.status_code == 200:
                return True, ""
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except requests.RequestException as e:
            return False, f"Request error: {str(e)}"
    
    def register_token(self, user_id: str, fcm_token: str, device_info: Dict = None) -> bool:
        """
        Register FCM token for a user
        
        Args:
            user_id: User ID
            fcm_token: FCM token from the mobile app
            device_info: Optional device information
            
        Returns:
            bool: True if registration successful
        """
        try:
            # Check if user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User {user_id} not found for FCM token registration")
                return False
            
            # Store or update FCM token in database
            subscription, created = PushSubscription.objects.update_or_create(
                user_id=user_id,
                endpoint=f"fcm:{fcm_token}",  # Use FCM prefix to distinguish from web push
                defaults={
                    'p256dh': fcm_token,  # Store FCM token in p256dh field
                    'auth': json.dumps(device_info) if device_info else '{}',
                    'updated_at': datetime.now()
                }
            )
            
            # Cache the token for quick access
            cache.set(f"fcm_token:{user_id}", fcm_token, timeout=86400)  # 24 hours
            
            logger.info(f"FCM token {'registered' if created else 'updated'} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering FCM token for user {user_id}: {str(e)}")
            return False
    
    def unregister_token(self, user_id: str, fcm_token: str = None) -> bool:
        """
        Unregister FCM token for a user
        
        Args:
            user_id: User ID
            fcm_token: Specific FCM token to unregister (optional)
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            if fcm_token:
                # Remove specific token
                PushSubscription.objects.filter(
                    user_id=user_id,
                    endpoint=f"fcm:{fcm_token}"
                ).delete()
            else:
                # Remove all FCM tokens for user
                PushSubscription.objects.filter(
                    user_id=user_id,
                    endpoint__startswith="fcm:"
                ).delete()
            
            # Clear cache
            cache.delete(f"fcm_token:{user_id}")
            
            logger.info(f"FCM token unregistered for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering FCM token for user {user_id}: {str(e)}")
            return False
    
    def get_user_tokens(self, user_id: str) -> List[str]:
        """
        Get all FCM tokens for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List[str]: List of FCM tokens
        """
        try:
            subscriptions = PushSubscription.objects.filter(
                user_id=user_id,
                endpoint__startswith="fcm:"
            )
            
            tokens = []
            for sub in subscriptions:
                # Extract token from p256dh field
                if sub.p256dh:
                    tokens.append(sub.p256dh)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Error getting FCM tokens for user {user_id}: {str(e)}")
            return []
    
    def send_notification(self, 
                         tokens: List[str], 
                         title: str, 
                         body: str, 
                         data: Dict = None,
                         priority: str = 'high') -> Dict:
        """
        Send FCM notification to multiple tokens
        
        Args:
            tokens: List of FCM tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            priority: Notification priority ('high' or 'normal')
            
        Returns:
            Dict: Response with success/failure counts
        """
        if not self.is_configured():
            logger.error("FCM not configured. Cannot send notification.")
            return {'success': 0, 'failure': len(tokens), 'errors': ['FCM not configured']}
        
        if not tokens:
            logger.warning("No FCM tokens provided for notification")
            return {'success': 0, 'failure': 0, 'errors': ['No tokens provided']}
        
        # Prepare notification payload
        success_count = 0
        failure_count = 0
        errors = []
        
        # Send to each token using v1
        for token in tokens:
            message = {
                'token': token,
                'notification': {
                    'title': title,
                    'body': body,
                },
                'data': data or {},
            }
            if priority:
                message['android'] = {
                    'priority': 'HIGH' if str(priority).lower() == 'high' else 'NORMAL'
                }
            ok, err = self._v1_messages_send(message)
            if ok:
                success_count += 1
                logger.info(f"FCM v1 notification sent successfully to token: {token[:20]}...")
            else:
                failure_count += 1
                errors.append(f"Token {token[:20]}...: {err}")
                logger.error(f"FCM v1 notification failed for token {token[:20]}...: {err}")
        
        return {
            'success': success_count,
            'failure': failure_count,
            'errors': errors
        }
    
    def send_to_user(self, 
                     user_id: str, 
                     title: str, 
                     body: str, 
                     data: Dict = None,
                     priority: str = 'high') -> Dict:
        """
        Send FCM notification to a specific user
        
        Args:
            user_id: User ID
            title: Notification title
            body: Notification body
            data: Additional data payload
            priority: Notification priority
            
        Returns:
            Dict: Response with success/failure counts
        """
        tokens = self.get_user_tokens(user_id)
        if not tokens:
            logger.warning(f"No FCM tokens found for user {user_id}")
            return {'success': 0, 'failure': 0, 'errors': ['No tokens found for user']}
        
        return self.send_notification(tokens, title, body, data, priority)
    
    def send_to_topic(self, 
                      topic: str, 
                      title: str, 
                      body: str, 
                      data: Dict = None,
                      priority: str = 'high') -> Dict:
        """
        Send FCM notification to a topic
        
        Args:
            topic: Topic name
            title: Notification title
            body: Notification body
            data: Additional data payload
            priority: Notification priority
            
        Returns:
            Dict: Response with success/failure counts
        """
        if not self.is_configured():
            logger.error("FCM not configured. Cannot send notification.")
            return {'success': 0, 'failure': 1, 'errors': ['FCM not configured']}
        
        message = {
            'topic': topic,
            'notification': {
                'title': title,
                'body': body,
            },
            'data': data or {},
        }
        if priority:
            message['android'] = {
                'priority': 'HIGH' if str(priority).lower() == 'high' else 'NORMAL'
            }
        ok, err = self._v1_messages_send(message)
        if ok:
            logger.info(f"FCM v1 notification sent to topic '{topic}'")
            return {'success': 1, 'failure': 0, 'errors': []}
        else:
            logger.error(f"FCM v1 topic notification failed: {err}")
            return {'success': 0, 'failure': 1, 'errors': [err]}
    
    def subscribe_to_topic(self, tokens: List[str], topic: str) -> Dict:
        """
        Subscribe tokens to a topic (not implemented for v1-only without server-side management).
        """
        logger.warning("Topic subscription via backend is not implemented in v1-only mode. Use client-side SDK topic management.")
        return {'success': 0, 'failure': len(tokens), 'errors': ['Not implemented in v1-only mode']}
    
    def unsubscribe_from_topic(self, tokens: List[str], topic: str) -> Dict:
        """
        Unsubscribe tokens from a topic (not implemented in v1-only mode).
        """
        logger.warning("Topic unsubscription via backend is not implemented in v1-only mode. Use client-side SDK topic management.")
        return {'success': 0, 'failure': len(tokens), 'errors': ['Not implemented in v1-only mode']}


# Global FCM service instance
fcm_service = FCMService()