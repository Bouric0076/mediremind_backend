from django.db import models
from django.conf import settings

class PushSubscription(models.Model):
    """Model to store web push subscriptions"""
    user_id = models.CharField(max_length=255)  # Supabase user ID
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)  # User's public key
    auth = models.CharField(max_length=255)  # User's auth secret
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_id', 'endpoint')
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['endpoint'])
        ]

    def to_subscription_info(self):
        """Convert to subscription info format for webpush"""
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh,
                'auth': self.auth
            }
        } 