from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone
from rest_framework.authtoken.models import Token
from .models import UserSession
# Removed Supabase import - using Django-only authentication
# from supabase_client import supabase
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class AuthenticatedUser:
    """Class to represent an authenticated user with their profile data"""
    def __init__(self, user):
        self.id = str(user.id)
        self.email = user.email
        self.user = user
        self.profile = self._get_profile_data(user)
    
    def _get_profile_data(self, user):
        """Get profile data based on user role"""
        profile_data = {
            'role': user.role,
            'full_name': user.full_name,
            'is_verified': user.is_verified,
            'mfa_enabled': user.mfa_enabled
        }
        
        # Add role-specific profile data
        try:
            if user.role == 'patient':
                from accounts.models import EnhancedPatient
                patient_profile = EnhancedPatient.objects.get(user=user)
                profile_data.update({
                    'patient_id': str(patient_profile.id),
                    'phone_number': patient_profile.phone,
                    'date_of_birth': patient_profile.date_of_birth.isoformat() if patient_profile.date_of_birth else None,
                    'address_line1': patient_profile.address_line1,
                    'address_line2': patient_profile.address_line2,
                    'city': patient_profile.city,
                    'state': patient_profile.state,
                    'zip_code': patient_profile.zip_code,
                    'emergency_contact': patient_profile.emergency_contact_name,
                    'emergency_phone': patient_profile.emergency_contact_phone
                })
            elif user.role in ['doctor', 'nurse', 'staff']:
                from accounts.models import EnhancedStaffProfile
                staff_profile = EnhancedStaffProfile.objects.get(user=user)
                profile_data.update({
                    'staff_id': str(staff_profile.id),
                    'department': staff_profile.department,
                    'specialization': staff_profile.specialization,
                    'license_number': staff_profile.license_number,
                    'phone_number': staff_profile.work_phone
                })
        except Exception as e:
            logger.warning(f"Could not load profile data for user {user.id}: {str(e)}")
        
        return profile_data

def get_authenticated_user(token: str) -> AuthenticatedUser:
    """
    Get authenticated user from Django token (Django-only authentication)
    
    Args:
        token: Authentication token (Django token or session key)
        
    Returns:
        AuthenticatedUser instance or None
    """
    if not token:
        logger.debug("No access token provided")
        return None
        
    try:
        # Try Django token authentication first
        try:
            django_token = Token.objects.select_related('user').get(key=token)
            user = django_token.user
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive user attempted authentication: {user.email}")
                return None
            
            # Check if account is locked
            if user.account_locked_until and user.account_locked_until > timezone.now():
                logger.warning(f"Locked account attempted authentication: {user.email}")
                return None
            
            # Update session activity if exists
            UserSession.objects.filter(
                user=user, is_active=True
            ).update(last_activity=timezone.now())
            
            logger.info(f"User authenticated via Django token: {user.email}")
            return AuthenticatedUser(user)
            
        except Token.DoesNotExist:
            logger.debug("Token not found in Django tokens, trying session authentication...")
            
            # Try session-based authentication as fallback
            try:
                session = UserSession.objects.select_related('user').get(
                    session_key=token,
                    is_active=True,
                    expires_at__gt=timezone.now()
                )
                
                user = session.user
                
                # Check if user is active
                if not user.is_active:
                    logger.warning(f"Inactive user attempted session authentication: {user.email}")
                    return None
                
                # Update session last activity
                session.last_activity = timezone.now()
                session.save(update_fields=['last_activity'])
                
                logger.info(f"User authenticated via session: {user.email}")
                return AuthenticatedUser(user)
                
            except UserSession.DoesNotExist:
                logger.debug("Session not found or expired")
                pass

        logger.warning(f"Authentication failed for token: {token[:10]}...")
        return None

    except Exception as e:
        logger.error(f"Authentication error in get_authenticated_user: {str(e)}")
        return None

def get_user_by_id(user_id):
    """Get user by ID from Django database"""
    try:
        user = User.objects.get(id=user_id)
        return {
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'mfa_enabled': user.mfa_enabled,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    except User.DoesNotExist:
        logger.warning(f"User not found with ID: {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error getting user by ID {user_id}: {str(e)}")
        return None

def get_user_profile(user_id, role=None):
    """Get user profile based on role using Django models"""
    try:
        user = User.objects.get(id=user_id)
        user_role = role or user.role
        
        if user_role == 'patient':
            from accounts.models import EnhancedPatient
            try:
                patient_profile = EnhancedPatient.objects.get(user=user)
                return {
                    'id': str(patient_profile.id),
                    'user_id': str(user.id),
                    'phone_number': patient_profile.phone,
                    'date_of_birth': patient_profile.date_of_birth.isoformat() if patient_profile.date_of_birth else None,
                    'gender': patient_profile.gender,
                    'address_line1': patient_profile.address_line1,
                    'address_line2': patient_profile.address_line2,
                    'city': patient_profile.city,
                    'state': patient_profile.state,
                    'zip_code': patient_profile.zip_code,
                    'emergency_contact_name': patient_profile.emergency_contact_name,
                    'emergency_contact_phone': patient_profile.emergency_contact_phone,
                    'insurance_provider': patient_profile.insurance_provider,
                    'insurance_policy_number': patient_profile.insurance_policy_number,
                    'family_medical_history': patient_profile.family_medical_history,
                    'allergies': patient_profile.allergies,
                    'current_medications': patient_profile.current_medications
                }
            except EnhancedPatient.DoesNotExist:
                logger.warning(f"Patient profile not found for user {user_id}")
                return None
                
        elif user_role in ['doctor', 'nurse', 'staff']:
            from accounts.models import EnhancedStaffProfile
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=user)
                return {
                    'id': str(staff_profile.id),
                    'user_id': str(user.id),
                    'department': staff_profile.department,
                    'specialization': staff_profile.specialization,
                    'license_number': staff_profile.license_number,
                    'phone_number': staff_profile.work_phone,
                    'office_location': staff_profile.office_location,
                    'years_experience': staff_profile.years_experience,
                    'education': staff_profile.education,
                    'board_certifications': staff_profile.board_certifications,
                    'languages_spoken': staff_profile.languages_spoken,
                    'default_schedule': staff_profile.default_schedule
                }
            except EnhancedStaffProfile.DoesNotExist:
                logger.warning(f"Staff profile not found for user {user_id}")
                return None
        
        return None
        
    except User.DoesNotExist:
        logger.warning(f"User not found with ID: {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error getting user profile for {user_id}: {str(e)}")
        return None

def validate_session_token(session_token):
    """Validate session token and return user if valid"""
    try:
        session = UserSession.objects.select_related('user').get(
            session_key=session_token,
            is_active=True,
            expires_at__gt=timezone.now()
        )
        
        # Update last activity
        session.last_activity = timezone.now()
        session.save(update_fields=['last_activity'])
        
        return session.user
    except UserSession.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error validating session token: {str(e)}")
        return None

def create_auth_token(user):
    """Create or get authentication token for user"""
    try:
        token, created = Token.objects.get_or_create(user=user)
        return token.key
    except Exception as e:
        logger.error(f"Error creating auth token for user {user.id}: {str(e)}")
        return None