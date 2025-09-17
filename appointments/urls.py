from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Core appointment management - API endpoints
    path('', views.get_all_appointments, name='appointment-list'),  # GET /appointments/
    path('create/', views.create_appointment, name='create_appointment'),  # POST /appointments/create/
    path('<uuid:appointment_id>/', views.get_appointment_detail, name='get_appointment_detail'),  # GET /appointments/{id}/
    path('<uuid:appointment_id>/update/', views.update_appointment, name='update_appointment'),  # PUT /appointments/{id}/update/
    path('<uuid:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),  # DELETE /appointments/{id}/cancel/
    
    # Enhanced appointment management endpoints
    path('availability/check/', views.check_availability, name='check_availability'),  # GET /appointments/availability/check/
    path('statistics/', views.get_appointment_statistics, name='appointment_statistics'),  # GET /appointments/statistics/
    path('bulk-update/', views.bulk_update_appointments, name='bulk_update_appointments'),  # POST /appointments/bulk-update/
    
    # Legacy endpoints (keeping for backward compatibility)
    path('list/', views.get_all_appointments, name='list_appointments'),
    path('stats/', views.get_appointment_stats, name='get_appointment_stats'),
]