"""
Cache utilities for authentication system to improve performance
by caching user permissions and profile data.
"""

from django.core.cache import cache
from django.contrib.auth import get_user_model
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class AuthCacheManager:
    """Manages caching for authentication-related data"""
    
    # Cache timeout settings (in seconds)
    USER_PERMISSIONS_TIMEOUT = 300  # 5 minutes
    USER_PROFILE_TIMEOUT = 600      # 10 minutes
    USER_ROLES_TIMEOUT = 300        # 5 minutes
    
    @classmethod
    def get_user_permissions_cache_key(cls, user_id: str) -> str:
        """Generate cache key for user permissions"""
        return f"user_permissions_{user_id}"
    
    @classmethod
    def get_user_profile_cache_key(cls, user_id: str) -> str:
        """Generate cache key for user profile"""
        return f"user_profile_{user_id}"
    
    @classmethod
    def get_user_roles_cache_key(cls, user_id: str) -> str:
        """Generate cache key for user roles"""
        return f"user_roles_{user_id}"
    
    @classmethod
    def cache_user_permissions(cls, user_id: str, permissions: List[str]) -> None:
        """Cache user permissions"""
        cache_key = cls.get_user_permissions_cache_key(user_id)
        cache.set(cache_key, permissions, cls.USER_PERMISSIONS_TIMEOUT)
        logger.debug(f"Cached permissions for user {user_id}")
    
    @classmethod
    def get_cached_user_permissions(cls, user_id: str) -> Optional[List[str]]:
        """Get cached user permissions"""
        cache_key = cls.get_user_permissions_cache_key(user_id)
        permissions = cache.get(cache_key)
        if permissions:
            logger.debug(f"Retrieved cached permissions for user {user_id}")
        return permissions
    
    @classmethod
    def cache_user_profile(cls, user_id: str, profile_data: Dict) -> None:
        """Cache user profile data"""
        cache_key = cls.get_user_profile_cache_key(user_id)
        cache.set(cache_key, profile_data, cls.USER_PROFILE_TIMEOUT)
        logger.debug(f"Cached profile data for user {user_id}")
    
    @classmethod
    def get_cached_user_profile(cls, user_id: str) -> Optional[Dict]:
        """Get cached user profile data"""
        cache_key = cls.get_user_profile_cache_key(user_id)
        profile_data = cache.get(cache_key)
        if profile_data:
            logger.debug(f"Retrieved cached profile data for user {user_id}")
        return profile_data
    
    @classmethod
    def cache_user_roles(cls, user_id: str, roles: List[str]) -> None:
        """Cache user roles"""
        cache_key = cls.get_user_roles_cache_key(user_id)
        cache.set(cache_key, roles, cls.USER_ROLES_TIMEOUT)
        logger.debug(f"Cached roles for user {user_id}")
    
    @classmethod
    def get_cached_user_roles(cls, user_id: str) -> Optional[List[str]]:
        """Get cached user roles"""
        cache_key = cls.get_user_roles_cache_key(user_id)
        roles = cache.get(cache_key)
        if roles:
            logger.debug(f"Retrieved cached roles for user {user_id}")
        return roles
    
    @classmethod
    def invalidate_user_cache(cls, user_id: str) -> None:
        """Invalidate all cached data for a user"""
        cache_keys = [
            cls.get_user_permissions_cache_key(user_id),
            cls.get_user_profile_cache_key(user_id),
            cls.get_user_roles_cache_key(user_id)
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        logger.info(f"Invalidated all cached data for user {user_id}")
    
    @classmethod
    def warm_user_cache(cls, user: User) -> None:
        """Pre-populate cache with user data"""
        try:
            # Cache user permissions
            from .services import PermissionService
            permission_service = PermissionService()
            permissions = permission_service.get_user_permissions(user)
            cls.cache_user_permissions(str(user.id), permissions)
            
            # Cache user roles
            roles = [user.role] if hasattr(user, 'role') else []
            cls.cache_user_roles(str(user.id), roles)
            
            # Cache basic profile data
            profile_data = {
                'id': str(user.id),
                'email': user.email,
                'full_name': getattr(user, 'full_name', ''),
                'role': getattr(user, 'role', ''),
                'is_active': user.is_active,
                'is_verified': getattr(user, 'is_verified', False),
            }
            cls.cache_user_profile(str(user.id), profile_data)
            
            logger.info(f"Warmed cache for user {user.id}")
            
        except Exception as e:
            logger.error(f"Failed to warm cache for user {user.id}: {str(e)}")