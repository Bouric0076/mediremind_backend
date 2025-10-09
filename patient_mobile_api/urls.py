"""
URL Configuration for Patient Mobile API
Defines URL patterns for patient mobile application endpoints
"""

from django.urls import path
from .views import PatientDashboardAPIView, PatientProfileAPIView, PatientMedicationAPIView

app_name = 'patient_mobile_api'

urlpatterns = [
    # Dashboard endpoint
    path('dashboard/', PatientDashboardAPIView.as_view(), name='patient_dashboard'),
    
    # Profile endpoints
    path('profile/', PatientProfileAPIView.as_view(), name='patient_profile'),
    
    # Medication endpoints
    path('medications/', PatientMedicationAPIView.as_view(), name='patient_medications'),
    path('medications/<int:medication_id>/', PatientMedicationAPIView.as_view(), name='patient_medication_detail'),
    path('medications/create/', PatientMedicationAPIView.as_view(), name='patient_medication_create'),
    path('medications/<int:medication_id>/update/', PatientMedicationAPIView.as_view(), name='patient_medication_update'),
    path('medications/<int:medication_id>/delete/', PatientMedicationAPIView.as_view(), name='patient_medication_delete'),
    path('medications/adherence/', PatientMedicationAPIView.as_view(), name='patient_medication_adherence'),
]