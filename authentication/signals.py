from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
import logging

# Removed Supabase-related imports - using Django-only authentication
# from .services import AuthenticationService
# from .sync_utils import SyncErrorHandler, safe_sync_operation

User = get_user_model()
logger = logging.getLogger(__name__)


# Disabled Supabase sync - using Django-only authentication
# @receiver(post_save, sender=User)
def sync_user_to_supabase(sender, instance, created, **kwargs):
    """
    DISABLED: Previously synced Django user creation/updates to Supabase
    Now using Django-only authentication approach
    """
    pass


# Disabled Supabase sync - using Django-only authentication
# @receiver(post_delete, sender=User)
def delete_user_from_supabase(sender, instance, **kwargs):
    """
    DISABLED: Previously deleted user from Supabase when Django user was deleted
    Now using Django-only authentication approach
    """
    pass


# Disabled Supabase sync - using Django-only authentication
# Signal to track password changes
# @receiver(pre_save, sender=User)
def track_password_changes(sender, instance, **kwargs):
    """
    DISABLED: Previously tracked password changes to sync with Supabase
    Now using Django-only authentication approach
    """
    pass


# @receiver(post_save, sender=User)
def sync_password_to_supabase(sender, instance, created, **kwargs):
    """
    DISABLED: Previously synced password changes to Supabase
    Now using Django-only authentication approach
    """
    pass