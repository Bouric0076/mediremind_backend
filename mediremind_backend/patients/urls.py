from django.urls import path
from .views import (
    patient_dashboard,
    patient_profile,
    update_patient_profile,
    view_appointments,
    request_appointment,
    respond_to_appointment,
    get_all_patients
)

urlpatterns = [
    path('dashboard/', patient_dashboard, name='patient_dashboard'),
    path('profile/', patient_profile, name='patient_profile'),
    path('profile/update/', update_patient_profile, name='update_patient_profile'),
    path('appointments/', view_appointments, name='view_appointments'),
    path('appointments/request/', request_appointment, name='request_appointment'),
    path('appointments/<str:appointment_id>/respond/', respond_to_appointment, name='respond_to_appointment'),
    path('list/', get_all_patients, name='get_all_patients'),
]
