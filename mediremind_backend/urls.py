"""
URL configuration for mediremind_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from notifications.scheduler_api import scheduler_api_urls
from .health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints with /api/ prefix for frontend
    path('api/auth/', include('authentication.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/calendar/', include('calendar_integrations.urls')),
    path('api/scheduler/', include(scheduler_api_urls)),
    path('api/patient/', include('patient_mobile_api.urls')),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Note: Legacy duplicate endpoints removed to avoid URL namespace conflicts.
    # All API endpoints are served under the /api/ prefix.
]
