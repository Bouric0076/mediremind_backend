"""
Token refresh utilities for calendar integrations.
Handles automatic refresh of expired OAuth tokens.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from .models import CalendarIntegration
from .google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)


class TokenRefreshManager:
    """
    Manages automatic token refresh for calendar integrations.
    """
    
    def __init__(self):
        self.google_service = GoogleCalendarService()
    
    def refresh_token_if_needed(self, integration):
        """
        Check if token needs refresh and refresh if necessary.
        
        Args:
            integration (CalendarIntegration): The integration to check
            
        Returns:
            bool: True if token was refreshed or is still valid, False if refresh failed
        """
        try:
            # Check if token is expired or will expire soon (within 5 minutes)
            if not self._needs_refresh(integration):
                return True
            
            logger.info(f"Refreshing token for integration {integration.id}")
            
            if integration.provider == 'google':
                return self._refresh_google_token(integration)
            elif integration.provider == 'outlook':
                return self._refresh_outlook_token(integration)
            else:
                logger.error(f"Unsupported provider for token refresh: {integration.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing token for integration {integration.id}: {e}")
            return False
    
    def _needs_refresh(self, integration):
        """
        Check if token needs to be refreshed.
        
        Args:
            integration (CalendarIntegration): The integration to check
            
        Returns:
            bool: True if token needs refresh
        """
        if not integration.token_expiry:
            # If no expiry is set, assume it needs refresh
            return True
        
        # Refresh if token expires within 5 minutes
        refresh_threshold = timezone.now() + timedelta(minutes=5)
        return integration.token_expiry <= refresh_threshold
    
    def _refresh_google_token(self, integration: CalendarIntegration) -> bool:
        """
        Refresh Google Calendar token for a specific integration.
        
        Args:
            integration: The CalendarIntegration instance to refresh
            
        Returns:
            bool: True if refresh was successful, False otherwise
        """
        try:
            # Create service instance
            service = GoogleCalendarService(integration)
            
            # Get current refresh token
            refresh_token = integration.refresh_token
            if not refresh_token:
                logger.warning(f"No refresh token available for integration {integration.id}")
                return False
            
            # Refresh the token
            token_data = service.refresh_access_token(refresh_token)
            
            # Update integration with new token data
            integration.access_token = token_data['access_token']
            
            # Update refresh token if provided
            if 'refresh_token' in token_data:
                integration.refresh_token = token_data['refresh_token']
            
            # Update token expiry
            if 'token_expiry' in token_data:
                integration.token_expiry = datetime.fromisoformat(token_data['token_expiry'])
            elif 'expires_in' in token_data:
                integration.token_expiry = timezone.now() + timedelta(seconds=token_data['expires_in'])
            
            integration.save()
            
            logger.info(f"Successfully refreshed token for integration {integration.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh Google token for integration {integration.id}: {e}")
            return False
    
    def _refresh_outlook_token(self, integration):
        """
        Refresh Outlook token (placeholder for future implementation).
        
        Args:
            integration (CalendarIntegration): The Outlook integration
            
        Returns:
            bool: True if refresh was successful
        """
        # TODO: Implement Outlook token refresh
        logger.warning(f"Outlook token refresh not implemented for integration {integration.id}")
        return False
    
    def refresh_all_expired_tokens(self):
        """
        Refresh all expired tokens across all integrations.
        
        Returns:
            dict: Summary of refresh results
        """
        results = {
            'total_checked': 0,
            'refreshed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            # Get all active integrations with tokens that might need refresh
            integrations = CalendarIntegration.objects.filter(
                status__in=['active', 'error'],
                sync_enabled=True
            ).exclude(
                refresh_token__isnull=True
            ).exclude(
                refresh_token=''
            )
            
            results['total_checked'] = integrations.count()
            
            for integration in integrations:
                try:
                    if self._needs_refresh(integration):
                        if self.refresh_token_if_needed(integration):
                            results['refreshed'] += 1
                        else:
                            results['failed'] += 1
                    else:
                        results['skipped'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing integration {integration.id}: {e}")
                    results['failed'] += 1
            
            logger.info(f"Token refresh batch completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch token refresh: {e}")
            return results


# Global instance for use throughout the application
token_refresh_manager = TokenRefreshManager()


def refresh_token_if_needed(integration):
    """
    Convenience function to refresh a token if needed.
    
    Args:
        integration (CalendarIntegration): The integration to refresh
        
    Returns:
        bool: True if token is valid (refreshed or not expired)
    """
    return token_refresh_manager.refresh_token_if_needed(integration)


def refresh_all_expired_tokens():
    """
    Convenience function to refresh all expired tokens.
    
    Returns:
        dict: Summary of refresh results
    """
    return token_refresh_manager.refresh_all_expired_tokens()