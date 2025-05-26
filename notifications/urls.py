from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('subscribe/', views.save_subscription, name='save_subscription'),
    path('unsubscribe/', views.delete_subscription, name='delete_subscription'),
    path('vapid-public-key/', views.get_vapid_public_key, name='get_vapid_public_key'),
    path('test/', views.test_notifications, name='test_notifications'),
    path('test-upcoming/', views.test_upcoming_reminders, name='test_upcoming_reminders'),
    path('check-subscriptions/', views.check_subscriptions, name='check_subscriptions'),
] 