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

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(MiddlewareMixin):
    """Middleware to handle authentication for API requests"""
    
    def process_request(self, request):
        """Process incoming request to authenticate user"""
        # Skip authentication for certain paths
        skip_paths = ['/admin/', '/static/', '/media/', '/auth/login/', '/auth/register/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get token from Authorization header or session
        auth_header = request.headers.get('Authorization', '')
        token = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif 'session_token' in request.session:
            token = request.session['session_token']
        
        if token:
            user = get_authenticated_user(token)
            if user:
                request.user = user
                request.authenticated_user = user
                # Update session activity if it's a session token
                if not auth_header.startswith('Bearer '):
                    try:
                        session = UserSession.objects.get(session_key=token, is_active=True)
                        session.last_activity = timezone.now()
                        session.save(update_fields=['last_activity'])
                    except UserSession.DoesNotExist:
                        pass
        
        return None


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
    return getattr(request, 'authenticated_user', None)


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