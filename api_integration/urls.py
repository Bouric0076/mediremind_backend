from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api_integration'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'hospitals', views.HospitalIntegrationViewSet)

# Define URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/setup/', views.HospitalIntegrationSetupView.as_view(), name='setup-integration'),
    path('auth/verify/', views.VerifyAPIKeyView.as_view(), name='verify-api-key'),
    path('auth/rotate-key/', views.RotateAPIKeyView.as_view(), name='rotate-api-key'),
    
    # Data processing endpoints
    path('patients/', views.PatientDataView.as_view(), name='patient-data'),
    path('appointments/', views.AppointmentDataView.as_view(), name='appointment-data'),
    path('reminders/', views.ReminderDataView.as_view(), name='reminder-data'),
    
    # Consent management endpoints
    path('consents/request/', views.RequestConsentView.as_view(), name='request-consent'),
    path('consents/verify/', views.VerifyConsentView.as_view(), name='verify-consent'),
    path('consents/withdraw/', views.WithdrawConsentView.as_view(), name='withdraw-consent'),
    
    # Compliance endpoints
    path('compliance/status/', views.ComplianceStatusView.as_view(), name='compliance-status'),
    path('compliance/report/', views.ComplianceReportView.as_view(), name='compliance-report'),
    
    # ViewSet routes
    path('', include(router.urls)),
]