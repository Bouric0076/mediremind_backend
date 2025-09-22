from django.urls import path
from . import views
from .views import (
    permission_sync_data,
    validate_user_permissions,
    permission_health_check,
    check_permission,
    user_detailed_permissions
)

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='refresh_token'),
    path('me/', views.get_user_profile, name='current_user'),
    
    # User profile endpoints
    path('profile/', views.get_user_profile, name='user_profile'),
    path('permissions/', views.get_user_permissions, name='user_permissions'),
    
    # Permission synchronization endpoints
    path('permissions/sync/', permission_sync_data, name='permission_sync'),
    path('permissions/validate/', validate_user_permissions, name='validate_permissions'),
    path('permissions/health/', permission_health_check, name='permission_health'),
    path('permissions/check/', check_permission, name='check_permission'),
    path('permissions/detailed/', user_detailed_permissions, name='detailed_permissions'),
    
    # MFA endpoints
    path('mfa/setup/', views.MFASetupView.as_view(), name='mfa_setup'),
    path('mfa/verify/', views.MFAVerifyView.as_view(), name='mfa_verify'),
    
    # Session management
    path('sessions/<uuid:session_id>/terminate/', views.terminate_session, name='terminate_session'),
    
    # Security dashboard
    path('security/dashboard/', views.get_security_dashboard, name='security_dashboard'),
    
    # User sync endpoints
    path('sync/', views.UserSyncView.as_view(), name='user_sync'),
    path('sync/health/', views.SyncHealthView.as_view(), name='sync_health'),
]