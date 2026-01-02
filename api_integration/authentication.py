from rest_framework import authentication, exceptions
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import HospitalIntegration, APILog
from .security import RequestSignature, RateLimiter
import redis
import json

User = get_user_model()

class HospitalAPIAuthentication(authentication.BaseAuthentication):
    """Custom authentication for hospital API integrations"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.rate_limiter = RateLimiter(self.redis_client)
        except:
            self.redis_client = None
            self.rate_limiter = RateLimiter(None)
    
    def authenticate(self, request):
        """Authenticate the request using API key and signature"""
        
        # Get API key from header
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            raise exceptions.AuthenticationFailed('API key required')
        
        # Get integration details
        try:
            integration = HospitalIntegration.objects.select_related('hospital').get(
                api_key=api_key,
                status='active'
            )
        except HospitalIntegration.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')
        
        # Check rate limiting
        if self.is_rate_limited(integration, request):
            raise exceptions.AuthenticationFailed('Rate limit exceeded')
        
        # Verify request signature
        signature = request.META.get('HTTP_X_SIGNATURE')
        timestamp = request.META.get('HTTP_X_TIMESTAMP')
        
        if not signature or not timestamp:
            raise exceptions.AuthenticationFailed('Signature and timestamp required')
        
        # Get request body for signature verification
        body = request.body.decode('utf-8') if request.body else ''
        
        if not RequestSignature.verify_signature(
            integration.api_secret, body, timestamp, signature
        ):
            raise exceptions.AuthenticationFailed('Invalid signature')
        
        # Update last accessed time
        integration.last_accessed = timezone.now()
        integration.save(update_fields=['last_accessed'])
        
        # Log authentication success
        self.log_api_request(request, integration, 200, 'Authentication successful')
        
        return (integration, None)
    
    def is_rate_limited(self, integration, request):
        """Check if request is rate limited"""
        client_ip = self.get_client_ip(request)
        
        # Check different rate limits
        limits = [
            ('per_minute', integration.rate_limit_per_minute, 60),
            ('per_hour', integration.rate_limit_per_hour, 3600),
            ('per_day', integration.rate_limit_per_day, 86400)
        ]
        
        for limit_type, limit, window in limits:
            if self.rate_limiter.is_rate_limited(
                f"{integration.id}:{client_ip}", 
                limit_type, 
                limit, 
                window
            ):
                return True
        
        return False
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_api_request(self, request, integration, status_code, message, **kwargs):
        """Log API request for audit purposes"""
        try:
            # Get request details
            endpoint = request.path
            method = request.method
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create log entry
            APILog.objects.create(
                integration=integration,
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                response_time_ms=kwargs.get('response_time_ms', 0),
                ip_address=ip_address,
                user_agent=user_agent,
                auth_status='success' if status_code == 200 else 'failed',
                message=message,
                **kwargs
            )
        except Exception as e:
            # Don't fail the request if logging fails
            pass

class HospitalAPIPermission:
    """Custom permission class for hospital API"""
    
    def has_permission(self, request, view):
        """Check if the integration has permission to access the endpoint"""
        
        if not hasattr(request, 'user') or not isinstance(request.user, HospitalIntegration):
            return False
        
        integration = request.user
        
        # Check if integration is active
        if not integration.is_active():
            return False
        
        # Check if data processing agreement is signed
        if not integration.data_processing_agreement_signed:
            return False
        
        # Check if consent is valid for the requested operation
        if not self.has_valid_consent(integration, request):
            return False
        
        # Check if endpoint is allowed
        if not self.is_endpoint_allowed(integration, request):
            return False
        
        return True
    
    def has_valid_consent(self, integration, request):
        """Check if integration has valid consent for the operation"""
        from .models import DataProcessingConsent
        
        # Map request path to consent type
        consent_type_map = {
            '/api/integration/patients/': 'patient_data',
            '/api/integration/appointments/': 'appointment_reminders',
            '/api/integration/emergency/': 'emergency_contact',
            '/api/integration/analytics/': 'analytics',
        }
        
        consent_type = None
        for path, consent in consent_type_map.items():
            if request.path.startswith(path):
                consent_type = consent
                break
        
        if not consent_type:
            return True  # No specific consent required
        
        try:
            consent = DataProcessingConsent.objects.get(
                integration=integration,
                consent_type=consent_type,
                status='granted'
            )
            return consent.is_valid()
        except DataProcessingConsent.DoesNotExist:
            return False
    
    def is_endpoint_allowed(self, integration, request):
        """Check if endpoint is in the allowed list"""
        allowed_endpoints = integration.allowed_endpoints or []
        
        if not allowed_endpoints:
            return True  # No restrictions
        
        # Check if any allowed endpoint matches the request path
        for allowed_endpoint in allowed_endpoints:
            if request.path.startswith(allowed_endpoint):
                return True
        
        return False