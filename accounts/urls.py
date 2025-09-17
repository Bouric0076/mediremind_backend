from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Test endpoint for debugging
    path('test-auth/', views.test_auth, name='test-auth'),  # GET/POST /accounts/test-auth/
    
    # User profile
    path('profile/', views.get_user_profile, name='user-profile'),  # GET /accounts/profile/
    
    # Patient management - API endpoints
    path('patients/', views.get_all_patients, name='patient-list'),  # GET /patients/
    path('patients/<uuid:pk>/', views.get_patient_detail, name='patient-detail'),  # GET /patients/{id}/
    path('patients/create/', views.create_patient, name='patient-create'),  # POST /patients/create/
    path('patients/<uuid:pk>/update/', views.update_patient, name='patient-update'),  # PUT /patients/{id}/update/
    path('patients/<uuid:pk>/delete/', views.delete_patient, name='patient-delete'),  # DELETE /patients/{id}/delete/
    
    # Staff management
    path('staff/', views.get_all_staff, name='staff-list'),
    path('staff/<uuid:pk>/', views.get_staff_detail, name='staff-detail'),
    path('staff/create/', views.create_staff, name='staff-create'),
    path('staff/<uuid:pk>/update/', views.update_staff, name='staff-update'),
    
    # Care team management
    path('care-teams/', views.get_care_teams, name='care-team-list'),
    path('care-teams/create/', views.create_care_team, name='care-team-create'),
    
    # Staff credentials
    path('staff/<uuid:staff_id>/credentials/', views.get_staff_credentials, name='staff-credentials'),
    path('credentials/<uuid:pk>/', views.get_credential_detail, name='credential-detail'),
]