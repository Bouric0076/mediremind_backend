from django.urls import path
from . import views
from .interactive_email_views import (
    InteractiveEmailActionView,
    RealTimeStatusView
)
from . import fcm_views
from . import medication_views

app_name = 'notifications'

urlpatterns = [
    # Existing notification endpoints
    path('subscribe/', views.save_subscription, name='save_subscription'),
    path('unsubscribe/', views.delete_subscription, name='delete_subscription'),
    path('vapid-public-key/', views.get_vapid_public_key, name='get_vapid_public_key'),
    path('test/', views.test_notifications, name='test_notifications'),
    path('test-upcoming/', views.test_upcoming_reminders, name='test_upcoming_reminders'),
    path('check-subscriptions/', views.check_subscriptions, name='check_subscriptions'),
    
    # FCM endpoints
    path('fcm/register-token/', fcm_views.register_fcm_token, name='register_fcm_token'),
    path('fcm/unregister-token/', fcm_views.unregister_fcm_token, name='unregister_fcm_token'),
    path('fcm/test/', fcm_views.send_test_notification, name='send_test_fcm_notification'),
    path('fcm/send-to-user/', fcm_views.send_notification_to_user, name='send_fcm_to_user'),
    path('fcm/send-to-topic/', fcm_views.send_notification_to_topic, name='send_fcm_to_topic'),
    path('fcm/status/', fcm_views.get_fcm_status, name='get_fcm_status'),
    path('fcm/topics/', fcm_views.FCMTopicManagementView.as_view(), name='fcm_topic_management'),
    
    # Medication reminder endpoints
    path('medications/schedule/', medication_views.schedule_medication_reminder, name='schedule_medication_reminder'),
    path('medications/send-immediate/', medication_views.send_immediate_reminder, name='send_immediate_reminder'),
    path('medications/mark-taken/', medication_views.mark_medication_taken, name='mark_medication_taken'),
    path('medications/snooze/', medication_views.snooze_reminder, name='snooze_reminder'),
    path('medications/upcoming/', medication_views.get_upcoming_reminders, name='get_upcoming_reminders'),
    path('medications/cancel/', medication_views.cancel_medication_reminders, name='cancel_medication_reminders'),
    path('medications/history/', medication_views.get_medication_history, name='get_medication_history'),
    path('medications/stats/', medication_views.MedicationReminderStatsView.as_view(), name='medication_stats'),
    
    # New notification management endpoints
    path('list/', views.get_notifications, name='get_notifications'),
    path('templates/', views.get_notification_templates, name='get_notification_templates'),
    path('send/', views.send_manual_notification, name='send_manual_notification'),
     path('preferences/', views.notification_preferences, name='notification_preferences'),
    path('mark-read/<str:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    
    # Interactive email action endpoints
    path('interactive/<str:action_type>/<str:user_id>/<str:resource_id>/', 
         InteractiveEmailActionView.as_view(), 
         name='interactive_action'),
    
    # Real-time status updates
    path('status/<str:resource_type>/<str:resource_id>/', 
         RealTimeStatusView.as_view(), 
         name='real_time_status'),
    
    # Appointment actions
    path('appointments/<str:appointment_id>/confirm/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'confirm_appointment'}, 
         name='confirm_appointment'),
    
    path('appointments/<str:appointment_id>/reschedule/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'reschedule_appointment'}, 
         name='reschedule_appointment'),
    
    path('appointments/<str:appointment_id>/cancel/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'cancel_appointment'}, 
         name='cancel_appointment'),
    
    # Medication actions
    path('medications/<str:medication_id>/taken/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'mark_taken'}, 
         name='mark_medication_taken'),
    
    path('medications/<str:medication_id>/snooze/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'snooze_reminder'}, 
         name='snooze_medication'),
    
    # Survey actions
    path('surveys/<str:survey_id>/start/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'start_survey'}, 
         name='start_survey'),
    
    path('surveys/<str:survey_id>/rate/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'quick_rating'}, 
         name='quick_survey_rating'),
    
    # Billing actions
    path('billing/<str:bill_id>/pay/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'pay_bill'}, 
         name='pay_bill'),
    
    path('billing/<str:bill_id>/plan/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'payment_plan'}, 
         name='payment_plan'),
    
    # Provider actions
    path('provider/call/<str:patient_id>/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'call_patient'}, 
         name='call_patient'),
    
    path('provider/message/<str:patient_id>/', 
         InteractiveEmailActionView.as_view(), 
         {'action_type': 'send_message'}, 
         name='send_message'),
]