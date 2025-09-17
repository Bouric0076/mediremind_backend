from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Appointment CRUD operations
    path('create/', views.create_appointment, name='create_appointment'),
    path('<int:appointment_id>/', views.get_appointment, name='get_appointment'),
    path('<int:appointment_id>/update/', views.update_appointment, name='update_appointment'),
    path('<int:appointment_id>/delete/', views.delete_appointment, name='delete_appointment'),
    
    # Appointment listing and statistics
    path('list/', views.list_appointments, name='list_appointments'),
    path('stats/', views.get_appointment_stats, name='get_appointment_stats'),
]