from django.urls import path
from .views import (
    staff_dashboard,
    staff_profile,
    view_appointments,
    schedule_appointment,
    respond_to_request,
    get_available_doctors
)

urlpatterns = [
    path('dashboard/', staff_dashboard, name='staff_dashboard'),
    path('profile/', staff_profile, name='staff_profile'),
    path('appointments/', view_appointments, name='staff_view_appointments'),
    path('appointments/schedule/', schedule_appointment, name='schedule_appointment'),
    path('appointments/<str:appointment_id>/respond/', respond_to_request, name='respond_to_request'),
    path('doctors/', get_available_doctors, name='get_available_doctors'),
]
