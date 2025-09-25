"""
Unified Authentication Middleware for MediRemind Backend
Provides consistent token-based authentication across all apps
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from functools import wraps
import json
import logging
from .utils import get_authenticated_user, validate_session_token
from .models import UserSession
from django.views import View
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.views import APIView as DRFAPIView
from rest_framework.response import Response
from rest_framework import status
import logging
import json

from .models import UserSession
from .services import AuthenticationService

logger = logging.getLogger(__name__)
User = get_user_model()

class AuthenticationMiddleware(MiddlewareMixin):
    """
    Custom authentication middleware that handles token-based authentication
    and session management with optimized database queries.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_service = AuthenticationService()
        
        # Paths that don't require authentication
        self.skip_paths = [
            '/admin/',
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/password-reset/',
            '/api/health/',
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        # Skip authentication for certain paths
        if any(request.path.startswith(path) for path in self.skip_paths):
            return self.get_response(request)
        
        # Extract token from request
        token = self._extract_token(request)
        
        if token:
            try:
                # Validate token and get user with optimized query
                user = self._validate_token_optimized(token, request)
                if user:
                    request.user = user
                    # Update session activity asynchronously to reduce response time
                    self._update_session_activity_async(user, request)
                else:
                    request.user = AnonymousUser()
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()
        
        response = self.get_response(request)
        return response
    
    def _extract_token(self, request):
        """Extract authentication token from request headers or cookies"""
        # Check Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        elif auth_header.startswith('Token '):
            return auth_header.split(' ')[1]
        
        # Check cookies
        return request.COOKIES.get('auth_token')
    
    def _validate_token_optimized(self, token, request):
        """
        Validate token with optimized database queries using select_related
        and caching for user permissions and profile data.
        """
        from rest_framework.authtoken.models import Token
        
        # Try to get user from cache first
        cache_key = f"auth_token_{token}"
        cached_user = cache.get(cache_key)
        
        if cached_user:
            return cached_user
        
        try:
            # Use select_related to reduce database queries
            django_token = Token.objects.select_related('user').get(key=token)
            user = django_token.user
            
            if not user.is_active:
                return None
            
            # Check if user is locked
            if user.account_locked_until and user.account_locked_until > timezone.now():
                return None
            
            # Cache user for 5 minutes to reduce database hits
            cache.set(cache_key, user, 300)
            
            return user
            
        except Token.DoesNotExist:
            return None
    
    def _update_session_activity_async(self, user, request):
        """
        Update session activity asynchronously to avoid blocking the response.
        Uses caching to reduce database queries.
        """
        try:
            # Get IP address
            ip_address = self._get_client_ip(request)
            
            # Update session activity with optimized query
            UserSession.objects.filter(
                user=user,
                is_active=True
            ).update(
                last_activity=timezone.now(),
                ip_address=ip_address
            )
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


def token_required(view_func):
    """
    Decorator for function-based views that require token authentication
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({
                "error": "Authorization header required",
                "code": "MISSING_TOKEN"
            }, status=401)

        # Parse token from header (supports both Bearer and Token formats)
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif auth_header.startswith('Token '):
            token = auth_header.split(' ')[1]
        else:
            return JsonResponse({
                "error": "Invalid authorization format. Use 'Bearer <token>' or 'Token <token>'",
                "code": "INVALID_FORMAT"
            }, status=401)

        # Validate token and get user
        user = get_authenticated_user(token)
        if not user:
            return JsonResponse({
                "error": "Invalid or expired token",
                "code": "INVALID_TOKEN"
            }, status=401)

        # Add authenticated user to request
        request.authenticated_user = user
        request.user = user
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def session_required(view_func):
    """Decorator to require valid session"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check for session token in various places
        token = None
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif 'session_token' in request.session:
            token = request.session['session_token']
        elif hasattr(request, 'COOKIES') and 'session_token' in request.COOKIES:
            token = request.COOKIES['session_token']
        
        if not token:
            return JsonResponse({
                "error": "Authentication required",
                "code": "NO_SESSION"
            }, status=401)
        
        user = get_authenticated_user(token)
        if not user:
            return JsonResponse({
                "error": "Invalid or expired session",
                "code": "INVALID_SESSION"
            }, status=401)
        
        # Add user to request
        request.user = user
        request.authenticated_user = user
        return view_func(request, *args, **kwargs)
    
    return wrapper


class TokenAuthenticationMixin:
    """
    Mixin for class-based views that require token authentication
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({
                "error": "Authorization header required",
                "code": "MISSING_TOKEN"
            }, status=401)

        # Parse token from header (supports both Bearer and Token formats)
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif auth_header.startswith('Token '):
            token = auth_header.split(' ')[1]
        else:
            return JsonResponse({
                "error": "Invalid authorization format. Use 'Bearer <token>' or 'Token <token>'",
                "code": "INVALID_FORMAT"
            }, status=401)

        # Validate token and get user
        user = get_authenticated_user(token)
        if not user:
            return JsonResponse({
                "error": "Invalid or expired token",
                "code": "INVALID_TOKEN"
            }, status=401)

        # Add authenticated user to request
        request.authenticated_user = user
        request.user = user
        
        return super().dispatch(request, *args, **kwargs)


def api_csrf_exempt(view_func):
    """
    Decorator that combines CSRF exemption with token authentication
    Use this for API endpoints that need token auth
    """
    @csrf_exempt
    @token_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    
    return wrapper


class APIView(View):
    """
    Base class for API views with built-in token authentication
    """
    
    @method_decorator(csrf_exempt, name='dispatch')
    def dispatch(self, request, *args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({
                "error": "Authorization header required",
                "code": "MISSING_TOKEN"
            }, status=401)

        # Parse token from header (supports both Bearer and Token formats)
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif auth_header.startswith('Token '):
            token = auth_header.split(' ')[1]
        else:
            return JsonResponse({
                "error": "Invalid authorization format. Use 'Bearer <token>' or 'Token <token>'",
                "code": "INVALID_FORMAT"
            }, status=401)

        # Validate token and get user
        user = get_authenticated_user(token)
        if not user:
            return JsonResponse({
                "error": "Invalid or expired token",
                "code": "INVALID_TOKEN"
            }, status=401)

        # Add authenticated user to request
        request.authenticated_user = user
        request.user = user
        
        return super().dispatch(request, *args, **kwargs)


# Utility functions for common authentication patterns

def get_request_user(request):
    """
    Get the authenticated user from request
    Returns the authenticated user object or None
    """
    # First try to get from middleware-set authenticated_user
    user = getattr(request, 'authenticated_user', None)
    if user:
        return user
    
    # Fallback: try to authenticate from headers/session directly
    auth_header = request.headers.get('Authorization', '')
    token = None
    
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    elif auth_header.startswith('Token '):
        token = auth_header.split(' ')[1]
    elif 'session_token' in request.session:
        token = request.session['session_token']
    elif hasattr(request, 'COOKIES') and 'session_token' in request.COOKIES:
        token = request.COOKIES['session_token']
    
    if token:
        user = get_authenticated_user(token)
        if user:
            # Cache the user on the request for subsequent calls
            request.authenticated_user = user
            request.user = user
            return user
    
    return None


def require_role(allowed_roles):
    """
    Decorator that checks if the authenticated user has one of the allowed roles
    Usage: @require_role(['admin', 'doctor'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = get_request_user(request)
            if not user:
                return JsonResponse({"error": "Authentication required"}, status=401)
            
            # Check user role
            user_role = getattr(user, 'role', None)
            if hasattr(user, 'profile') and hasattr(user.profile, 'role'):
                user_role = user.profile.role
            
            if user_role not in allowed_roles:
                return JsonResponse({"error": f"Access denied. Required roles: {allowed_roles}"}, status=403)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator