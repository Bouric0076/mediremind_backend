from django.contrib.auth import get_user_model, authenticate
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth.hashers import check_password
from rest_framework.authtoken.models import Token
from typing import Dict, Optional, Tuple, Any
import json
import hashlib
import secrets
import pyotp
import uuid
import logging
from datetime import timedelta
from .models import (
    MFADevice, LoginAttempt, UserSession, AuditLog
)
from .exceptions import (
    AuthenticationError, MFARequiredError, AccountLockedError,
    InvalidMFATokenError, SessionExpiredError, RateLimitExceededError
)
from .sync_utils import AuthErrorHandler, AuthMetrics

logger = logging.getLogger(__name__)

User = get_user_model()


class AuthenticationService:
    """Enhanced authentication service with MFA and security monitoring"""
    
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    SESSION_DURATION = timedelta(days=7)  # Extended from 8 hours to 7 days to reduce frequent logins
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self, email: str, password: str, 
                    mfa_token: Optional[str] = None,
                    ip_address: str = None,
                    user_agent: str = None) -> Dict:
        """
        Unified authentication flow using Django as primary authentication source
        
        Args:
            email: User email address
            password: User password
            mfa_token: Multi-factor authentication token (if required)
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            Dict containing authentication result
            
        Raises:
            AuthenticationError: For various authentication failures
            MFARequiredError: When MFA is required but not provided
            AccountLockedError: When account is temporarily locked
        """
        
        with transaction.atomic():
            # 1. Get Django user and perform pre-authentication checks
            user = self._get_user_by_email(email)
            if not user:
                self._log_login_attempt(None, ip_address, user_agent, 
                                      success=False, failure_reason='user_not_found')
                raise AuthenticationError('Invalid credentials')
            
            self._check_account_status(user)
            self._check_rate_limiting(user, ip_address)
            
            try:
                # 2. Validate credentials using Django authentication
                django_user = authenticate(username=email, password=password)
                if not django_user:
                    raise AuthenticationError('Invalid credentials')
                
                # 3. MFA verification if enabled
                if user.mfa_enabled:
                    if not mfa_token:
                        self._log_login_attempt(user, ip_address, user_agent, 
                                              success=False, mfa_required=True)
                        raise MFARequiredError('MFA token required', user_id=user.id)
                    
                    self._verify_mfa_token(user, mfa_token)
                
                # 4. Create secure session
                session = self._create_session(user, ip_address, user_agent)
                
                # Create or get auth token
                token, created = Token.objects.get_or_create(user=user)
                
                # 5. Reset failed attempts and log success
                user.failed_login_attempts = 0
                user.account_locked_until = None
                user.last_login_at = timezone.now()
                user.save(update_fields=['failed_login_attempts', 'account_locked_until', 'last_login_at'])
                
                self._log_login_attempt(user, ip_address, user_agent, success=True)
                self._log_audit_event(user, 'login', 'User logged in successfully')
                
                return {
                    'success': True,
                    'user': user,
                    'session': session,
                    'access_token': token.key,
                    'expires_at': session.expires_at
                }
                
            except Exception as e:
                # Handle authentication failures
                self._handle_failed_login(user, str(e))
                
                self._log_login_attempt(
                    user, ip_address, user_agent, 
                    success=False, failure_reason=str(e)
                )
                
                if isinstance(e, (MFARequiredError, AccountLockedError)):
                    raise
                
                raise AuthenticationError('Authentication failed')
    
    def refresh_session(self, access_token: str, session_key: str = '') -> Dict:
        """
        Refresh user session using Django authentication tokens
        
        Args:
            access_token: Django access token
            session_key: Optional session key
            
        Returns:
            Dict containing refreshed tokens
        """
        try:
            # Get user from Django token
            try:
                token = Token.objects.get(key=access_token)
                user = token.user
            except Token.DoesNotExist:
                raise SessionExpiredError("Invalid access token")
            
            # Check if user is still active
            if not user.is_active:
                raise SessionExpiredError("User account is inactive")
            
            # Check if session is still valid
            if session_key:
                session = UserSession.objects.filter(
                    user=user, 
                    session_key=session_key,
                    is_active=True,
                    expires_at__gt=timezone.now()
                ).first()
                
                if not session:
                    raise SessionExpiredError("Session expired")
                
                # Update session activity
                session.last_activity = timezone.now()
                session.save(update_fields=['last_activity'])
            
            # Token is still valid, return current token info
            return {
                'access_token': token.key,
                'expires_at': timezone.now() + timedelta(days=7)
            }
            
        except Exception as e:
            self.logger.error(f"Session refresh failed: {str(e)}")
            raise SessionExpiredError("Failed to refresh session")
    
    def logout(self, session_key: str, reason: str = 'user_logout') -> bool:
        """
        Logout user and terminate session
        
        Args:
            session_key: Session to terminate
            reason: Reason for logout
            
        Returns:
            bool: Success status
        """
        
        try:
            session = UserSession.objects.get(
                session_key=session_key,
                is_active=True
            )
            
            # Terminate session
            session.is_active = False
            session.terminated_at = timezone.now()
            session.termination_reason = reason
            session.save()
            
            # Log audit event
            self._log_audit_event(
                session.user, 'logout', 
                f'User logged out: {reason}'
            )
            
            # Remove auth token
            try:
                Token.objects.filter(user=session.user).delete()
            except:
                pass  # Don't fail logout if token deletion fails
            
            return True
            
        except UserSession.DoesNotExist:
            return False
    



    

    

    
    def setup_mfa(self, user: User, device_type: str, 
                  device_name: str, phone_number: str = None) -> Dict:
        """
        Setup multi-factor authentication for user
        
        Args:
            user: User instance
            device_type: Type of MFA device ('totp', 'sms', 'email')
            device_name: Human-readable device name
            phone_number: Phone number for SMS MFA
            
        Returns:
            Dict containing setup information
        """
        
        if device_type == 'totp':
            # Generate TOTP secret
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            
            # Create MFA device
            device = MFADevice.objects.create(
                user=user,
                device_type=device_type,
                device_name=device_name,
                secret_key=secret,
                is_active=False  # Activate after verification
            )
            
            # Generate QR code URL
            qr_url = totp.provisioning_uri(
                name=user.email,
                issuer_name='MediRemind'
            )
            
            return {
                'device_id': device.id,
                'secret': secret,
                'qr_url': qr_url,
                'backup_codes': self._generate_backup_codes(user)
            }
            
        elif device_type == 'sms':
            if not phone_number:
                raise ValidationError('Phone number required for SMS MFA')
            
            device = MFADevice.objects.create(
                user=user,
                device_type=device_type,
                device_name=device_name,
                phone_number=phone_number,
                is_active=False
            )
            
            # Send verification SMS
            verification_code = self._send_sms_verification(phone_number)
            
            return {
                'device_id': device.id,
                'verification_required': True,
                'phone_number': phone_number[-4:]  # Only show last 4 digits
            }
        
        else:
            raise ValidationError(f'Unsupported MFA device type: {device_type}')
    
    def verify_mfa_setup(self, device_id: int, verification_code: str) -> bool:
        """
        Verify MFA device setup
        
        Args:
            device_id: MFA device ID
            verification_code: Verification code from device
            
        Returns:
            bool: Verification success
        """
        
        try:
            device = MFADevice.objects.get(id=device_id, is_active=False)
            
            if device.device_type == 'totp':
                totp = pyotp.TOTP(device.secret_key)
                if totp.verify(verification_code, valid_window=1):
                    device.is_active = True
                    device.save()
                    
                    # Enable MFA for user if this is their first device
                    if not device.user.mfa_enabled:
                        device.user.mfa_enabled = True
                        device.user.save(update_fields=['mfa_enabled'])
                    
                    self._log_audit_event(
                        device.user, 'mfa_setup',
                        f'MFA device activated: {device.device_name}'
                    )
                    
                    return True
            
            return False
            
        except MFADevice.DoesNotExist:
            return False
    
    def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    def _check_account_status(self, user: User) -> None:
        """Check if user account is active and not locked"""
        if not user.is_active:
            raise AuthenticationError('Account is disabled')
        
        if user.account_locked_until and user.account_locked_until > timezone.now():
            raise AccountLockedError(
                'Account temporarily locked due to failed login attempts',
                locked_until=user.account_locked_until
            )
    
    def is_rate_limited(self, ip_address: str, email: str = None) -> bool:
        """Check if IP or user is rate limited"""
        # Check recent failed attempts from this IP
        recent_attempts = LoginAttempt.objects.filter(
            ip_address=ip_address,
            success=False,
            timestamp__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        
        return recent_attempts >= 10
    
    def authenticate_user(self, email: str, password: str, ip_address: str = None, 
                        user_agent: str = None, mfa_token: str = None, 
                        remember_me: bool = False) -> Dict:
        """Wrapper method for authenticate to match expected interface"""
        return self.authenticate(
            email=email,
            password=password,
            mfa_token=mfa_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def clear_failed_attempts(self, email: str, ip_address: str) -> None:
        """Clear failed login attempts for user and IP"""
        try:
            user = User.objects.get(email=email)
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
        except User.DoesNotExist:
            pass
        
        # Clear failed attempts from this IP
        LoginAttempt.objects.filter(
            ip_address=ip_address,
            success=False
        ).delete()
    
    def get_failed_attempts(self, email: str, ip_address: str) -> int:
        """Get number of recent failed attempts"""
        return LoginAttempt.objects.filter(
            email_attempted=email,
            ip_address=ip_address,
            success=False,
            timestamp__gte=timezone.now() - timedelta(minutes=15)
        ).count()
    
    def lock_account(self, user: User) -> None:
        """Lock user account temporarily"""
        user.account_locked_until = timezone.now() + self.LOCKOUT_DURATION
        user.save(update_fields=['account_locked_until'])
    
    def _check_rate_limiting(self, user: User, ip_address: str) -> None:
        """Check rate limiting for login attempts"""
        if self.is_rate_limited(ip_address):
            raise AuthenticationError('Too many failed attempts from this IP')
    

    
    def _get_or_create_user(self, email: str, **kwargs) -> User:
        """Get or create Django user"""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user with provided data
            user = User.objects.create_user(
                email=email,
                **kwargs
            )
        return user
    
    def _verify_mfa_token(self, user: User, token: str) -> None:
        """Verify MFA token"""
        # Try all active MFA devices
        devices = user.mfadevice_set.filter(is_active=True)
        
        for device in devices:
            if device.device_type == 'totp':
                totp = pyotp.TOTP(device.secret_key)
                if totp.verify(token, valid_window=1):
                    device.last_used = timezone.now()
                    device.save(update_fields=['last_used'])
                    return
        
        raise InvalidMFATokenError('Invalid MFA token')
    
    def _create_session(self, user: User, ip_address: str, user_agent: str) -> UserSession:
        """Create secure user session"""
        
        # Deactivate existing active sessions for this user
        UserSession.objects.filter(
            user=user, 
            is_active=True
        ).update(
            is_active=False,
            terminated_at=timezone.now(),
            termination_reason='new_login'
        )
        
        # Generate secure session key (ensure uniqueness across both tables)
        max_attempts = 10
        for attempt in range(max_attempts):
            session_key = secrets.token_urlsafe(32)
            # Check uniqueness in both UserSession and Django Session tables
            if (not UserSession.objects.filter(session_key=session_key).exists() and
                not Session.objects.filter(session_key=session_key).exists()):
                break
        else:
            # If we can't generate a unique key after max attempts, use UUID
            session_key = str(uuid.uuid4())
            # Ensure UUID is also unique
            while (UserSession.objects.filter(session_key=session_key).exists() or
                   Session.objects.filter(session_key=session_key).exists()):
                session_key = str(uuid.uuid4())
        
        # Create device fingerprint
        device_fingerprint = hashlib.sha256(
            f"{user_agent}{ip_address}".encode()
        ).hexdigest()[:32]
        
        session = UserSession.objects.create(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            expires_at=timezone.now() + self.SESSION_DURATION,
            is_active=True
        )
        
        return session
    
    def _handle_failed_login(self, user: User, error_message: str) -> None:
        """Handle failed login attempt"""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= self.MAX_LOGIN_ATTEMPTS:
            user.account_locked_until = timezone.now() + self.LOCKOUT_DURATION
        
        user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
    
    def _log_login_attempt(self, user: Optional[User], ip_address: str, 
                          user_agent: str, success: bool, 
                          failure_reason: str = None,
                          mfa_required: bool = False,
                          mfa_success: bool = None) -> None:
        """Log login attempt for security monitoring"""
        
        LoginAttempt.objects.create(
            user=user,
            email_attempted=user.email if user else 'unknown',
            ip_address=ip_address or '0.0.0.0',
            user_agent=user_agent or 'unknown',
            success=success,
            failure_reason=failure_reason or '',
            mfa_required=mfa_required,
            mfa_success=mfa_success
        )
    
    def _log_audit_event(self, user: User, action: str, description: str,
                        resource_type: str = 'user', resource_id: str = None,
                        patient_affected=None, risk_level: str = 'low') -> None:
        """Log audit event for compliance"""
        
        AuditLog.objects.create(
            user=user,
            user_role=user.role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id or str(user.id),
            description=description,
            patient_affected=patient_affected,
            risk_level=risk_level,
            ip_address='0.0.0.0',  # Will be updated by middleware
            user_agent='system'     # Will be updated by middleware
        )
    
    def _generate_backup_codes(self, user: User) -> list:
        """Generate backup codes for MFA recovery"""
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Store hashed versions
        hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in codes]
        
        # Save to user profile (you'll need to add this field)
        # user.mfa_backup_codes = hashed_codes
        # user.save()
        
        return codes
    
    def _send_sms_verification(self, phone_number: str) -> str:
        """Send SMS verification code (placeholder)"""
        # Implement SMS sending logic here
        # Return the verification code that was sent
        verification_code = f"{secrets.randbelow(1000000):06d}"
        
        # TODO: Integrate with SMS service (Twilio, etc.)
        print(f"SMS verification code for {phone_number}: {verification_code}")
        
        return verification_code
    



class PermissionService:
    """Service for handling user permissions and access control"""
    
    def __init__(self):
        self.auth_service = AuthenticationService()
        # Import here to avoid circular imports
        from .permissions_config import PERMISSIONS_CONFIG
        self.permissions_config = PERMISSIONS_CONFIG
    
    def check_permission(self, user: User, permission_code: str, 
                        resource=None, context: Dict = None) -> bool:
        """
        Check if user has specific permission
        
        Args:
            user: User instance
            permission_code: Permission code to check
            resource: Optional resource being accessed
            context: Additional context for permission check
            
        Returns:
            bool: Permission granted
        """
        
        # Basic active user check
        if not user.is_active:
            return False
        
        # Check role-based permissions using centralized config
        if self.permissions_config.has_permission(user.role, permission_code):
            return True
        
        # Check user-specific permissions
        if self._check_user_permission(user, permission_code):
            return True
        
        # Check resource-specific permissions
        if resource and self._check_resource_permission(user, permission_code, resource):
            return True
        
        return False
    
    def _check_role_permission(self, role: str, permission_code: str) -> bool:
        """Check role-based permissions using centralized config"""
        return self.permissions_config.has_permission(role, permission_code)
    
    def _check_user_permission(self, user: User, permission_code: str) -> bool:
        """Check user-specific permission overrides"""
        # This would check the UserPermission model
        # Implementation depends on your specific needs
        return False
    
    def _check_resource_permission(self, user: User, permission_code: str, resource) -> bool:
        """Check resource-specific permissions (e.g., patient relationship)"""
        # Example: Check if user has relationship with patient
        if hasattr(resource, 'primary_doctor') and resource.primary_doctor:
            if hasattr(resource.primary_doctor, 'user') and resource.primary_doctor.user == user:
                return True
        
        return False
    
    def get_user_permissions(self, user: User) -> list:
        """Get list of permissions for a user based on their role"""
        return self.permissions_config.get_role_permissions(user.role)
    
    def get_detailed_permissions(self, user: User) -> Dict:
        """Get detailed permissions with categories and descriptions"""
        return self.permissions_config.get_detailed_permissions(user.role)