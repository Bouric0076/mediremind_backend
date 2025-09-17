from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.dashboard_overview, name='dashboard_overview'),
    path('appointments/', views.appointment_analytics, name='appointment_analytics'),
    path('revenue/', views.revenue_analytics, name='revenue_analytics'),
    path('users/', views.user_analytics, name='user_analytics'),
    path('performance/', views.system_performance, name='system_performance'),
]