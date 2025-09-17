from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='refresh_token'),
    path('me/', views.get_user_profile, name='current_user'),
    
    # User profile and permissions
    path('profile/', views.get_user_profile, name='user_profile'),
    path('permissions/', views.get_user_permissions, name='user_permissions'),
    
    # Multi-Factor Authentication
    path('mfa/setup/', views.MFASetupView.as_view(), name='mfa_setup'),
    path('mfa/verify/', views.MFAVerifyView.as_view(), name='mfa_verify'),
    
    # Session management
    path('sessions/<uuid:session_id>/terminate/', views.terminate_session, name='terminate_session'),
    
    # Security dashboard
    path('security/dashboard/', views.get_security_dashboard, name='security_dashboard'),
]