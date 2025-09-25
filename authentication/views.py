from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.cache import cache
from django.contrib.sessions.models import Session

import json
import logging
import pyotp
import qrcode
import io
import base64
from datetime import timedelta, datetime
from typing import Dict, Any, Optional

from .models import (
    MFADevice, LoginAttempt, UserSession, AuditLog, 
    SecurityAlert, Permission, UserPermission, RolePermission
)
from .services import AuthenticationService, PermissionService
from .sync_utils import AuthErrorHandler, AuthMetrics
from accounts.models import EnhancedPatient
from accounts.models import EnhancedStaffProfile

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationView(View):
    """Base authentication view with common functionality"""
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthenticationService()
        self.permission_service = PermissionService()
    
    def get_client_info(self, request):
        """Extract client information from request"""
        return {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'device_fingerprint': request.META.get('HTTP_X_DEVICE_FINGERPRINT', ''),
        }
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_audit_event(self, user, action, resource_type, resource_id, 
                       description, request, old_values=None, new_values=None,
                       patient_affected=None, risk_level='low'):
        """Log audit event"""
        client_info = self.get_client_info(request)
        
        AuditLog.objects.create(
            user=user,
            user_role=user.role if user else 'anonymous',
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            timestamp=timezone.now(),
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            description=description,
            old_values=old_values,
            new_values=new_values,
            patient_affected=patient_affected,
            risk_level=risk_level,
            session_id=request.session.session_key or '',
            request_id=getattr(request, 'id', ''),
        )


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(AuthenticationView):
    """Enhanced login with MFA and security monitoring"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email', '').lower().strip()
            password = data.get('password', '')
            mfa_code = data.get('mfa_code', '')
            remember_me = data.get('remember_me', False)
            
            client_info = self.get_client_info(request)
            
            # Rate limiting check
            if self.auth_service.is_rate_limited(client_info['ip_address'], email):
                self.log_login_attempt(
                    email, client_info, False, 'rate_limited'
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Too many login attempts. Please try again later.',
                    'retry_after': 300  # 5 minutes
                }, status=429)
            
            # Basic validation
            if not email or not password:
                self.log_login_attempt(
                    email, client_info, False, 'missing_credentials'
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Email and password are required'
                }, status=400)
            
            # Authenticate user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                self.log_login_attempt(
                    email, client_info, False, 'user_not_found'
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=401)
            
            # Check if account is locked
            if not user.is_active:
                self.log_login_attempt(
                    email, client_info, False, 'account_locked'
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Account is locked. Please contact support.'
                }, status=401)
            
            # Verify password
            if not user.check_password(password):
                self.log_login_attempt(
                    email, client_info, False, 'invalid_password'
                )
                
                # Check for account lockout
                failed_attempts = self.auth_service.get_failed_attempts(
                    email, client_info['ip_address']
                )
                
                if failed_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    self.auth_service.lock_account(user)
                    SecurityAlert.objects.create(
                        alert_type='account_lockout',
                        severity='medium',
                        title=f'Account locked: {email}',
                        description=f'Account locked due to {failed_attempts} failed login attempts',
                        user_affected=user,
                        ip_address=client_info['ip_address']
                    )
                
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=401)
            
            # Check MFA requirement
            mfa_devices = MFADevice.objects.filter(
                user=user, is_active=True, device_type__in=['totp', 'sms']
            )
            
            requires_mfa = mfa_devices.exists()
            mfa_verified = False
            
            if requires_mfa:
                if not mfa_code:
                    self.log_login_attempt(
                        email, client_info, False, 'mfa_required', user
                    )
                    return JsonResponse({
                        'success': False,
                        'mfa_required': True,
                        'error': 'MFA code required'
                    }, status=200)
                
                # Verify MFA code
                mfa_verified = self.verify_mfa_code(user, mfa_code)
                if not mfa_verified:
                    self.log_login_attempt(
                        email, client_info, False, 'invalid_mfa', user
                    )
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid MFA code'
                    }, status=401)
            
            # Successful authentication using AuthenticationService
            try:
                auth_result = self.auth_service.authenticate_user(
                    email=email,
                    password=password,
                    ip_address=client_info['ip_address'],
                    user_agent=client_info['user_agent'],
                    mfa_token=mfa_code if mfa_verified else None,
                    remember_me=remember_me
                )
                
                # Django session login for compatibility
                login(request, user)
                
                # Force session creation and save
                if not request.session.session_key:
                    request.session.create()
                
                # Get user profile
                profile_data = self.get_user_profile_data(user)
                
                return JsonResponse({
                    'success': True,
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'full_name': user.full_name,
                        'role': user.role,
                        'profile': profile_data,
                        'permissions': self.permission_service.get_user_permissions(user),
                    },
                    'token': auth_result['access_token'],
                    'session_id': str(auth_result['session'].id) if 'session' in auth_result else None,
                    'expires_at': auth_result.get('expires_at').isoformat() if auth_result.get('expires_at') else None
                })
                
            except Exception as auth_error:
                logger.error(f"Authentication service error: {str(auth_error)}")
                
                # Log failed login attempt
                self.log_login_attempt(
                    email, client_info, False, f'auth_service_error: {str(auth_error)}', user
                )
                
                # Return proper error response instead of fallback success
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication failed. Please check your credentials and try again.'
                }, status=401)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during login'
            }, status=500)
    
    def log_login_attempt(self, email, client_info, success, failure_reason=None, 
                         user=None, mfa_success=None):
        """Log login attempt"""
        LoginAttempt.objects.create(
            user=user,
            email_attempted=email,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            success=success,
            failure_reason=failure_reason or '',
            mfa_required=user and MFADevice.objects.filter(
                user=user, is_active=True
            ).exists() if user else False,
            mfa_success=mfa_success,
            session_id=getattr(self.request, 'session', {}).get('session_key', '')
        )
    
    def verify_mfa_code(self, user, code):
        """Verify MFA code"""
        totp_device = MFADevice.objects.filter(
            user=user, device_type='totp', is_active=True
        ).first()
        
        if totp_device and totp_device.secret_key:
            totp = pyotp.TOTP(totp_device.secret_key)
            if totp.verify(code, valid_window=1):
                # Update device usage
                totp_device.last_used = timezone.now()
                totp_device.use_count += 1
                totp_device.save(update_fields=['last_used', 'use_count'])
                return True
        
        return False
    
    def get_user_profile_data(self, user):
        """Get user profile data based on role"""
        if user.role == 'patient':
            try:
                patient = EnhancedPatient.objects.get(user=user)
                return {
                    'type': 'patient',
                    'id': str(patient.id),
                    'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                    'phone': patient.phone,
                    'emergency_contact': patient.emergency_contact_name,
                }
            except EnhancedPatient.DoesNotExist:
                return {'type': 'patient', 'incomplete': True}
        else:
            try:
                staff = EnhancedStaffProfile.objects.get(user=user)
                return {
                    'type': 'staff',
                    'id': str(staff.id),
                    'specialization': staff.specialization.name if staff.specialization else None,
                    'license_number': staff.license_number,
                    'department': staff.department,
                }
            except EnhancedStaffProfile.DoesNotExist:
                return {'type': 'staff', 'incomplete': True}


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(AuthenticationView):
    """Enhanced logout with session cleanup"""
    
    def post(self, request):
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return JsonResponse({"error": "Authorization header required"}, status=401)

            # Parse token from header
            token = None
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            elif auth_header.startswith('Token '):
                token = auth_header.split(' ')[1]
            else:
                return JsonResponse({"error": "Invalid authorization format"}, status=401)

            # Get authenticated user
            from .utils import get_authenticated_user
            user = get_authenticated_user(token)
            if not user:
                return JsonResponse({"error": "Invalid or expired token"}, status=401)

            # Get the actual Django user instance
            if hasattr(user, 'user'):
                django_user = user.user
            else:
                from .models import User
                django_user = User.objects.get(id=user.id)
            
            # Terminate user sessions
            UserSession.objects.filter(
                user=django_user, is_active=True
            ).update(
                is_active=False,
                terminated_at=timezone.now(),
                termination_reason='user_logout'
            )
            
            # Delete the Django token if it exists
            try:
                from rest_framework.authtoken.models import Token
                Token.objects.filter(user=django_user).delete()
            except:
                pass  # Token might not exist
            
            # Log audit event
            self.log_audit_event(
                django_user, 'logout', 'user_session', 'token_based',
                'User logged out via token', request
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Logged out successfully'
            })
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during logout'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(AuthenticationView):
    """Token refresh endpoint"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            refresh_token = data.get('refreshToken')
            
            if not refresh_token:
                return JsonResponse({
                    'success': False,
                    'error': 'Refresh token is required'
                }, status=400)
            
            # Handle session-based fallback
            if refresh_token == 'session_based_auth':
                if request.user.is_authenticated:
                    return JsonResponse({
                        'success': True,
                        'token': 'session_based_auth',
                        'refreshToken': 'session_based_auth'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Session expired'
                    }, status=401)
            
            # Use AuthenticationService for token refresh
            try:
                session_key = request.session.session_key or ''
                refresh_result = self.auth_service.refresh_session(
                    refresh_token, session_key
                )
                
                return JsonResponse({
                    'success': True,
                    'token': refresh_result['access_token'],
                    'expires_at': refresh_result.get('expires_at').isoformat() if refresh_result.get('expires_at') else None
                })
                
            except Exception as refresh_error:
                logger.error(f"Token refresh error: {str(refresh_error)}")
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to refresh token'
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Refresh token error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during token refresh'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MFASetupView(AuthenticationView):
    """MFA device setup and management"""
    
    @method_decorator(login_required)
    def post(self, request):
        try:
            data = json.loads(request.body)
            device_type = data.get('device_type', 'totp')
            device_name = data.get('device_name', 'Authenticator App')
            
            user = request.user
            
            if device_type == 'totp':
                return self.setup_totp_device(user, device_name, request)
            elif device_type == 'sms':
                phone_number = data.get('phone_number')
                return self.setup_sms_device(user, device_name, phone_number, request)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Unsupported device type'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"MFA setup error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during MFA setup'
            }, status=500)
    
    def setup_totp_device(self, user, device_name, request):
        """Setup TOTP device"""
        # Generate secret key
        secret = pyotp.random_base32()
        
        # Create TOTP URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="MediRemind"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Create MFA device (inactive until verified)
        mfa_device = MFADevice.objects.create(
            user=user,
            device_type='totp',
            device_name=device_name,
            secret_key=secret,
            is_active=False  # Will be activated after verification
        )
        
        # Log audit event
        self.log_audit_event(
            user, 'create', 'mfa_device', mfa_device.id,
            f'TOTP device setup initiated: {device_name}', request
        )
        
        return JsonResponse({
            'success': True,
            'device_id': str(mfa_device.id),
            'qr_code': f"data:image/png;base64,{qr_code_data}",
            'secret': secret,  # For manual entry
            'message': 'Scan the QR code with your authenticator app and verify with a code'
        })
    
    def setup_sms_device(self, user, device_name, phone_number, request):
        """Setup SMS device"""
        if not phone_number:
            return JsonResponse({
                'success': False,
                'error': 'Phone number is required for SMS MFA'
            }, status=400)
        
        # Create MFA device
        mfa_device = MFADevice.objects.create(
            user=user,
            device_type='sms',
            device_name=device_name,
            phone_number=phone_number,
            is_active=False  # Will be activated after verification
        )
        
        # Log audit event
        self.log_audit_event(
            user, 'create', 'mfa_device', mfa_device.id,
            f'SMS device setup initiated: {device_name}', request
        )
        
        return JsonResponse({
            'success': True,
            'device_id': str(mfa_device.id),
            'message': 'SMS device created. Verify with a test code to activate.'
        })


@method_decorator(csrf_exempt, name='dispatch')
class MFAVerifyView(AuthenticationView):
    """Verify and activate MFA device"""
    
    @method_decorator(login_required)
    def post(self, request):
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            verification_code = data.get('code')
            
            if not device_id or not verification_code:
                return JsonResponse({
                    'success': False,
                    'error': 'Device ID and verification code are required'
                }, status=400)
            
            try:
                mfa_device = MFADevice.objects.get(
                    id=device_id, user=request.user, is_active=False
                )
            except MFADevice.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid device ID or device already active'
                }, status=404)
            
            # Verify code based on device type
            if mfa_device.device_type == 'totp':
                totp = pyotp.TOTP(mfa_device.secret_key)
                if totp.verify(verification_code, valid_window=1):
                    mfa_device.is_active = True
                    mfa_device.last_used = timezone.now()
                    mfa_device.use_count = 1
                    mfa_device.save()
                    
                    # Log audit event
                    self.log_audit_event(
                        request.user, 'update', 'mfa_device', mfa_device.id,
                        f'TOTP device activated: {mfa_device.device_name}', request
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'MFA device activated successfully'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid verification code'
                    }, status=400)
            
            # Add SMS verification logic here if needed
            
            return JsonResponse({
                'success': False,
                'error': 'Unsupported device type for verification'
            }, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"MFA verification error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during verification'
            }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get current user profile and permissions"""
    try:
        user = request.user
        
        # Get profile data
        from .utils import get_user_profile
        profile_data = get_user_profile(user.id, user.role)
        permissions = PermissionService().get_user_permissions(user)
        
        # Get active sessions
        active_sessions = UserSession.objects.filter(
            user=user, is_active=True
        ).count()
        
        # Get MFA devices
        mfa_devices = MFADevice.objects.filter(
            user=user, is_active=True
        ).values('id', 'device_type', 'device_name', 'created_at', 'last_used')
        
        return Response({
            'success': True,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'profile': profile_data,
                'permissions': permissions,
                'active_sessions': active_sessions,
                'mfa_devices': list(mfa_devices),
            }
        })
        
    except Exception as e:
        logger.error(f"Get user profile error: {str(e)}")
        return Response({
            'success': False,
            'error': 'An error occurred while fetching user profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(login_required)
def get_user_permissions(request):
    """Get detailed user permissions"""
    try:
        user = request.user
        permission_service = PermissionService()
        
        # Get all permissions with details
        permissions = permission_service.get_detailed_permissions(user)
        
        return JsonResponse({
            'success': True,
            'permissions': permissions
        })
        
    except Exception as e:
        logger.error(f"Get user permissions error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching permissions'
        }, status=500)


@method_decorator(login_required)
def terminate_session(request, session_id):
    """Terminate a specific user session"""
    try:
        user = request.user
        
        session = UserSession.objects.filter(
            id=session_id, user=user, is_active=True
        ).first()
        
        if not session:
            return JsonResponse({
                'success': False,
                'error': 'Session not found or already terminated'
            }, status=404)
        
        session.terminate('user_request')
        
        # Log audit event
        auth_view = AuthenticationView()
        auth_view.log_audit_event(
            user, 'update', 'user_session', session.id,
            f'Session terminated by user', request
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Session terminated successfully'
        })
        
    except Exception as e:
        logger.error(f"Terminate session error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while terminating session'
        }, status=500)


@method_decorator(login_required)
def get_security_dashboard(request):
    """Get security dashboard data for the user"""
    try:
        user = request.user
        
        # Recent login attempts
        recent_attempts = LoginAttempt.objects.filter(
            user=user
        ).order_by('-timestamp')[:10].values(
            'timestamp', 'ip_address', 'success', 'failure_reason'
        )
        
        # Active sessions
        active_sessions = UserSession.objects.filter(
            user=user, is_active=True
        ).values(
            'id', 'ip_address', 'user_agent', 'created_at', 'last_activity'
        )
        
        # Recent audit logs
        recent_audits = AuditLog.objects.filter(
            user=user
        ).order_by('-timestamp')[:20].values(
            'action', 'resource_type', 'description', 'timestamp', 'ip_address'
        )
        
        # Security alerts
        security_alerts = SecurityAlert.objects.filter(
            user_affected=user, status='open'
        ).values(
            'alert_type', 'severity', 'title', 'detected_at'
        )
        
        return JsonResponse({
            'success': True,
            'dashboard': {
                'recent_login_attempts': list(recent_attempts),
                'active_sessions': list(active_sessions),
                'recent_audit_logs': list(recent_audits),
                'security_alerts': list(security_alerts),
            }
        })
        
    except Exception as e:
        logger.error(f"Security dashboard error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching security dashboard'
        }, status=500)


class UserRegistrationView(AuthenticationView):
    """User registration view that synchronizes Django and Supabase"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        """Register a new user in both Django and Supabase"""
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['email', 'password', 'full_name', 'role']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            email = data['email'].lower().strip()
            password = data['password']
            full_name = data['full_name'].strip()
            role = data['role'].lower()
            
            # Validate role
            if role not in ['patient', 'staff', 'admin']:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid role. Must be patient, staff, or admin'
                }, status=400)
            
            # Check if user already exists in Django
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'User with this email already exists'
                }, status=400)
            
            # Use transaction to ensure atomicity
            with transaction.atomic():
                # Create Django user
                django_user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    full_name=full_name,
                    role=role,
                    is_active=True
                )
                
                # Create role-specific profile
                if role == 'patient':
                    from datetime import date
                    EnhancedPatient.objects.create(
                        user=django_user,
                        date_of_birth=date(1990, 1, 1),  # Placeholder - should be collected in registration form
                        gender='P',  # Prefer not to say - should be collected in registration form
                        phone='000-000-0000',  # Placeholder
                        address_line1='Not provided',  # Placeholder
                        city='Not provided',  # Placeholder
                        state='Not provided',  # Placeholder
                        zip_code='00000',  # Placeholder
                        emergency_contact_name='Not provided',  # Placeholder
                        emergency_contact_relationship='Not provided',  # Placeholder
                        emergency_contact_phone='000-000-0000',  # Placeholder
                    )
                elif role in ['staff', 'admin']:
                    EnhancedStaffProfile.objects.create(
                        user=django_user
                    )
                
                # Log the registration
                AuditLog.objects.create(
                    user=django_user,
                    action='USER_REGISTERED',
                    resource_type='User',
                    description=f'New {role} user registered: {email}',
                    ip_address=self.get_client_info(request)['ip_address']
                )
                
                logger.info(f"Successfully registered new {role} user: {email}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'User registered successfully',
                    'user': {
                        'id': str(django_user.id),
                        'email': email,
                        'full_name': full_name,
                        'role': role
                    }
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return JsonResponse({
                 'success': False,
                 'error': 'An error occurred during registration'
             }, status=500)


class UserSyncView(AuthenticationView):
    """User synchronization service for existing users"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        """Synchronize existing users between Django and Supabase"""
        try:
            data = json.loads(request.body)
            
            # Check if user has admin permissions
            if not request.user.is_authenticated or not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'error': 'Admin permissions required'
                }, status=403)
            
            sync_type = data.get('sync_type', 'audit')  # 'audit', 'fix', or 'specific'
            email = data.get('email')  # For specific user sync
            
            if sync_type == 'specific' and not email:
                return JsonResponse({
                    'success': False,
                    'error': 'Email required for specific user sync'
                }, status=400)
            
            # Perform synchronization audit
            sync_results = self._perform_sync_audit(sync_type, email)
            
            return JsonResponse({
                'success': True,
                'sync_results': sync_results
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"User sync error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during synchronization'
            }, status=500)


class SyncHealthView(AuthenticationView):
    """
    Monitor synchronization health and provide detailed status information
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        """
        Get comprehensive sync health status
        """
        try:
            # Check if user has admin permissions
            if not request.user.is_authenticated or not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'error': 'Admin permissions required'
                }, status=403)
            
            # Get overall health metrics
            health_status = AuthMetrics.get_sync_health_status()
            
            # Get recent sync operations
            recent_logs = AuditLog.objects.filter(
                action__startswith='SYNC_',
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-timestamp')[:20]
            
            recent_operations = []
            for log in recent_logs:
                recent_operations.append({
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.action,
                    'user_email': log.user.email if log.user else 'system',
                    'description': log.description,
                    'ip_address': log.ip_address
                })
            
            # Get sync error summary
            error_summary = {}
            error_logs = AuditLog.objects.filter(
                action__startswith='SYNC_ERROR',
                timestamp__gte=timezone.now() - timedelta(hours=24)
            )
            
            for log in error_logs:
                error_type = 'sync_error'
                if 'network' in log.description.lower():
                    error_type = 'network_error'
                elif 'rate' in log.description.lower():
                    error_type = 'rate_limit'
                elif 'auth' in log.description.lower():
                    error_type = 'authorization_error'
                
                if error_type not in error_summary:
                    error_summary[error_type] = 0
                error_summary[error_type] += 1
            
            return JsonResponse({
                'success': True,
                'health_status': health_status,
                'recent_operations': recent_operations,
                'error_summary': error_summary,
                'recommendations': self._get_health_recommendations(health_status, error_summary)
            })
            
        except Exception as e:
            AuthErrorHandler.log_auth_operation(
                'health_check', request.user.email if request.user.is_authenticated else 'anonymous',
                False, {'endpoint': 'sync_health'}, e
            )
            return JsonResponse({
                'success': False,
                'error': 'Failed to get sync health status',
                'details': str(e)
            }, status=500)
    
    def _get_health_recommendations(self, health_status: dict, error_summary: dict) -> list:
        """
        Generate health recommendations based on current status
        """
        recommendations = []
        
        # Check overall health
        if health_status.get('health_status') == 'critical':
            if not health_status.get('supabase_available'):
                recommendations.append({
                    'priority': 'high',
                    'message': 'Supabase is not available. Check network connectivity and API keys.',
                    'action': 'Check Supabase configuration and network'
                })
            elif health_status.get('sync_ratio', 0) < 0.8:
                recommendations.append({
                    'priority': 'high',
                    'message': f"Sync ratio is low ({health_status.get('sync_ratio', 0):.1%}). Run audit command to fix sync issues.",
                    'action': 'python manage.py audit_user_sync --fix'
                })
        
        # Check error patterns
        if error_summary.get('network_error', 0) > 5:
            recommendations.append({
                'priority': 'medium',
                'message': 'Multiple network errors detected. Check Supabase connectivity.',
                'action': 'Monitor network stability and Supabase status'
            })
        
        if error_summary.get('rate_limit', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'message': 'Rate limiting detected. Consider implementing retry logic with backoff.',
                'action': 'Review API usage patterns and implement rate limiting'
            })
        
        if error_summary.get('authorization_error', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'message': 'Authorization errors detected. Check Supabase API keys and permissions.',
                'action': 'Verify Supabase configuration and API keys'
            })
        
        # Default recommendation if healthy
        if not recommendations and health_status.get('health_status') == 'healthy':
            recommendations.append({
                'priority': 'low',
                'message': 'Sync system is healthy. Continue monitoring.',
                'action': 'Regular monitoring'
            })
        
        return recommendations
    
    def _perform_sync_audit(self, sync_type, email=None):
        """DISABLED: Previously performed user synchronization audit with Supabase"""
        # Get Django users for basic reporting
        if email:
            django_users = User.objects.filter(email=email)
            if not django_users.exists():
                return {
                    'error': f'User with email {email} not found in Django',
                    'django_count': 0,
                    'message': 'Using Django-only authentication'
                }
        else:
            django_users = User.objects.all()
        
        return {
            'django_count': len(django_users),
            'sync_status': 'django_only',
            'message': 'Sync functionality disabled - using Django-only authentication',
            'issues_found': 0
        }
    
    def _fix_sync_issues(self, missing_in_supabase, missing_in_django, supabase_users):
        """Fix synchronization issues - Django-only approach"""
        fix_results = {
            'django_fixes': [],
            'errors': [],
            'message': 'Sync functionality disabled - using Django-only authentication'
        }
        
        # Note: With Django-only authentication, we no longer sync with Supabase
        # All user management is handled through Django
        
        return fix_results


# Permission Synchronization API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permission_sync_data(request):
    """
    API endpoint to provide permission synchronization data for frontend
    """
    try:
        # Get all permissions
        all_permissions = list(PERMISSIONS_CONFIG._permissions.keys())
        
        # Get all roles
        all_roles = list(PERMISSIONS_CONFIG._role_permissions.keys())
        
        # Get role permissions mapping
        role_permissions = {}
        for role in all_roles:
            role_permissions[role] = PERMISSIONS_CONFIG.get_role_permissions(role)
        
        # Get detailed permissions for each role
        detailed_permissions = {}
        permission_service = PermissionService()
        
        for role in all_roles:
            # Create a mock user with this role to get detailed permissions
            class MockUser:
                def __init__(self, role):
                    self.role = role
                    self.email = f"mock_{role}@example.com"
            
            mock_user = MockUser(role)
            detailed_permissions[role] = permission_service.get_detailed_permissions(mock_user)
        
        # Get permission details
        permission_details = {}
        for perm_code, permission in PERMISSIONS_CONFIG._permissions.items():
            permission_details[perm_code] = {
                'code': permission.code,
                'name': permission.name,
                'description': permission.description,
                'category': permission.category,
                'level': permission.level
            }
        
        # Get role hierarchy
        role_hierarchy = PERMISSIONS_CONFIG._role_hierarchy.copy()
        
        sync_data = {
            'permissions': all_permissions,
            'roles': all_roles,
            'rolePermissions': role_permissions,
            'detailedPermissions': detailed_permissions,
            'permissionDetails': permission_details,
            'roleHierarchy': role_hierarchy,
            'timestamp': request.META.get('HTTP_DATE', ''),
            'version': '1.0'  # Version for compatibility checking
        }
        
        return Response(sync_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to generate sync data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_user_permissions(request):
    """
    Validate user permissions against their role
    """
    try:
        user = request.user
        permission_service = PermissionService()
        
        # Get user's current permissions
        user_permissions = permission_service.get_user_permissions(user)
        expected_permissions = PERMISSIONS_CONFIG.get_role_permissions(user.userprofile.role)
        
        # Compare permissions
        user_perm_set = set(user_permissions)
        expected_perm_set = set(expected_permissions)
        
        missing_permissions = list(expected_perm_set - user_perm_set)
        extra_permissions = list(user_perm_set - expected_perm_set)
        
        validation_result = {
            'isValid': len(missing_permissions) == 0,
            'userRole': user.userprofile.role,
            'userPermissions': user_permissions,
            'expectedPermissions': expected_permissions,
            'missingPermissions': missing_permissions,
            'extraPermissions': extra_permissions,
            'timestamp': request.META.get('HTTP_DATE', '')
        }
        
        return Response(validation_result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to validate user permissions: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def permission_health_check(request):
    """
    Health check endpoint for permission system
    """
    try:
        health_data = {
            'status': 'healthy',
            'permissionSystemVersion': '1.0',
            'totalPermissions': len(PERMISSIONS_CONFIG._permissions),
            'totalRoles': len(PERMISSIONS_CONFIG._role_permissions),
            'configurationValid': True,
            'timestamp': request.META.get('HTTP_DATE', '')
        }
        
        # Basic validation checks
        errors = []
        warnings = []
        
        # Check if all role permissions reference valid permissions
        for role, permissions in PERMISSIONS_CONFIG._role_permissions.items():
            for perm in permissions:
                if perm not in PERMISSIONS_CONFIG._permissions:
                    errors.append(f"Role {role} references undefined permission: {perm}")
        
        # Check for orphaned permissions
        all_permissions = set(PERMISSIONS_CONFIG._permissions.keys())
        assigned_permissions = set()
        for role_perms in PERMISSIONS_CONFIG._role_permissions.values():
            assigned_permissions.update(role_perms)
        
        orphaned = all_permissions - assigned_permissions
        if orphaned:
            warnings.extend([f"Orphaned permission: {perm}" for perm in orphaned])
        
        if errors:
            health_data['status'] = 'unhealthy'
            health_data['configurationValid'] = False
        elif warnings:
            health_data['status'] = 'degraded'
        
        health_data['errors'] = errors
        health_data['warnings'] = warnings
        
        return Response(health_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'status': 'unhealthy',
                'error': f'Health check failed: {str(e)}',
                'timestamp': request.META.get('HTTP_DATE', '')
            }, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def check_permission(request):
    """
    Check if user has a specific permission
    """
    try:
        permission_code = request.data.get('permission')
        if not permission_code:
            return Response(
                {'error': 'Permission code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        permission_service = PermissionService()
        
        has_permission = permission_service.check_permission(user, permission_code)
        
        result = {
            'hasPermission': has_permission,
            'permission': permission_code,
            'userRole': user.userprofile.role,
            'timestamp': request.META.get('HTTP_DATE', '')
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to check permission: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def user_detailed_permissions(request):
    """
    Get detailed permissions for the current user
    """
    try:
        user = request.user
        permission_service = PermissionService()
        
        detailed_permissions = permission_service.get_detailed_permissions(user)
        user_permissions = permission_service.get_user_permissions(user)
        
        result = {
            'userRole': user.userprofile.role,
            'permissions': user_permissions,
            'detailedPermissions': detailed_permissions,
            'timestamp': request.META.get('HTTP_DATE', '')
        }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get user permissions: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )