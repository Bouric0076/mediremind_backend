from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from supabase_client import admin_client
from authentication.utils import get_authenticated_user
from authentication.middleware import api_csrf_exempt, get_request_user
from datetime import datetime
from .utils import (
    send_appointment_reminder,
    send_appointment_confirmation,
    send_appointment_update,
    trigger_manual_reminder
)
from .models import ScheduledTask
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.models import EnhancedStaffProfile
from django.utils import timezone

@api_csrf_exempt
def save_subscription(request):
    """Save a push notification subscription"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
        subscription_data = data.get('subscription')
        
        if not subscription_data:
            return JsonResponse({"error": "Subscription data required"}, status=400)

        # Extract subscription info
        endpoint = subscription_data.get('endpoint')
        p256dh = subscription_data.get('keys', {}).get('p256dh')
        auth = subscription_data.get('keys', {}).get('auth')

        if not all([endpoint, p256dh, auth]):
            return JsonResponse({"error": "Invalid subscription data"}, status=400)

        # Check if subscription exists
        existing = admin_client.table("push_subscriptions").select("id").eq("user_id", user.id).eq("endpoint", endpoint).execute()
        
        if existing.data:
            # Update existing subscription
            admin_client.table("push_subscriptions").update({
                'p256dh': p256dh,
                'auth': auth,
                'updated_at': datetime.now().isoformat()
            }).eq("id", existing.data[0]['id']).execute()
            created = False
        else:
            # Create new subscription
            admin_client.table("push_subscriptions").insert({
                'user_id': user.id,
                'endpoint': endpoint,
                'p256dh': p256dh,
                'auth': auth,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).execute()
            created = True

        return JsonResponse({
            "message": "Subscription saved successfully",
            "created": created
        }, status=201 if created else 200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_csrf_exempt
def get_notifications(request):
    """Get paginated list of notifications/scheduled tasks"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get user role and hospital association
        user_role = getattr(user, 'role', user.profile.get('role') if hasattr(user, 'profile') else None)
        user_hospital = None
        
        if user_role in ['admin', 'staff']:
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=user)
                user_hospital = staff_profile.hospital
                if not user_hospital:
                    return JsonResponse({"error": "No hospital association found for staff user"}, status=403)
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({"error": "Staff profile not found"}, status=403)
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        status_filter = request.GET.get('status', '')
        task_type_filter = request.GET.get('task_type', '')
        delivery_method_filter = request.GET.get('delivery_method', '')

        # Build query
        queryset = ScheduledTask.objects.all()
        
        # Apply hospital filter for staff/admin users
        if user_hospital:
            # Get appointments associated with this hospital
            hospital_appointments = []
            try:
                # Get patients from this hospital
                patient_result = admin_client.table("patients").select("id").eq("hospital_id", str(user_hospital.id)).execute()
                if patient_result.data:
                    patient_ids = [p['id'] for p in patient_result.data]
                    
                    # Get appointments for these patients
                    if patient_ids:
                        appt_result = admin_client.table("appointments").select("id").in_("patient_id", patient_ids).execute()
                        if appt_result.data:
                            hospital_appointments = [a['id'] for a in appt_result.data]
                
                # Filter notifications to only those related to hospital's appointments
                if hospital_appointments:
                    queryset = queryset.filter(appointment_id__in=hospital_appointments)
                else:
                    # No appointments found for this hospital, return empty set
                    queryset = ScheduledTask.objects.none()
            except Exception as e:
                print(f"Error filtering notifications by hospital: {e}")
                return JsonResponse({"error": "Error filtering notifications by hospital"}, status=500)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if task_type_filter:
            queryset = queryset.filter(task_type=task_type_filter)
        if delivery_method_filter:
            queryset = queryset.filter(delivery_method=delivery_method_filter)

        # Order by priority and scheduled time
        queryset = queryset.order_by('priority', '-created_at')

        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Format notifications
        notifications = []
        for task in page_obj:
            # Get appointment and patient data
            appointment_data = None
            patient_data = None
            
            try:
                appointment_result = admin_client.table("appointments").select(
                    "id, patient_id, provider_id, appointment_date, appointment_time, location, status"
                ).eq("id", str(task.appointment_id)).execute()
                
                if appointment_result.data:
                    appointment_data = appointment_result.data[0]
                    
                    # Get patient data
                    patient_result = admin_client.table("patients").select(
                        "id, first_name, last_name, email, phone"
                    ).eq("id", appointment_data['patient_id']).execute()
                    
                    if patient_result.data:
                        patient_data = patient_result.data[0]
            except Exception as e:
                print(f"Error fetching appointment/patient data: {e}")

            notification = {
                'id': str(task.id),
                'type': task.delivery_method,
                'recipient': {
                    'id': patient_data['id'] if patient_data else '',
                    'name': f"{patient_data['first_name']} {patient_data['last_name']}" if patient_data else 'Unknown Patient',
                    'contact': patient_data['email'] if patient_data and task.delivery_method == 'email' else patient_data['phone'] if patient_data else ''
                },
                'subject': f"{task.get_task_type_display()} - {task.get_delivery_method_display()}",
                'message': task.message_data.get('message', f"{task.task_type} notification"),
                'status': task.status,
                'scheduledAt': task.scheduled_time.isoformat() if task.scheduled_time else None,
                'sentAt': task.last_attempt.isoformat() if task.last_attempt else None,
                'deliveredAt': task.completed_at.isoformat() if task.completed_at else None,
                'priority': ['urgent', 'high', 'medium', 'low'][task.priority],
                'category': task.task_type,
                'appointment': {
                    'id': str(task.appointment_id),
                    'date': appointment_data['appointment_date'] if appointment_data else None,
                    'time': appointment_data['appointment_time'] if appointment_data else None,
                    'location': appointment_data['location'] if appointment_data else None,
                } if appointment_data else None,
                'error_message': task.error_message,
                'retry_count': task.retry_count,
                'created_at': task.created_at.isoformat()
            }
            notifications.append(notification)

        return JsonResponse({
            'notifications': notifications,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_csrf_exempt
def get_notification_templates(request):
    """Get notification templates"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # For now, return predefined templates since we don't have a templates table
        # In a full implementation, you would query a NotificationTemplate model
        templates = [
            {
                'id': '1',
                'name': 'Appointment Reminder - 24 Hours',
                'type': 'email',
                'category': 'reminder',
                'subject': 'Appointment Reminder - {{appointment_date}} at {{appointment_time}}',
                'content': 'Dear {{patient_name}}, this is a reminder that you have an appointment scheduled for {{appointment_date}} at {{appointment_time}} with {{provider_name}} at {{location}}. Please arrive 15 minutes early.',
                'variables': ['patient_name', 'appointment_date', 'appointment_time', 'provider_name', 'location'],
                'isActive': True,
                'createdAt': '2024-01-01T00:00:00Z',
                'updatedAt': '2024-01-15T00:00:00Z'
            },
            {
                'id': '2',
                'name': 'Appointment Confirmation',
                'type': 'email',
                'category': 'confirmation',
                'subject': 'Appointment Confirmed - {{appointment_date}}',
                'content': 'Dear {{patient_name}}, your appointment has been confirmed for {{appointment_date}} at {{appointment_time}} with {{provider_name}}.',
                'variables': ['patient_name', 'appointment_date', 'appointment_time', 'provider_name'],
                'isActive': True,
                'createdAt': '2024-01-01T00:00:00Z',
                'updatedAt': '2024-01-10T00:00:00Z'
            },
            {
                'id': '3',
                'name': 'SMS Appointment Reminder',
                'type': 'sms',
                'category': 'reminder',
                'subject': 'Appointment Reminder',
                'content': 'Hi {{patient_name}}, reminder: appointment {{appointment_date}} at {{appointment_time}} with {{provider_name}}. Reply CONFIRM to confirm.',
                'variables': ['patient_name', 'appointment_date', 'appointment_time', 'provider_name'],
                'isActive': True,
                'createdAt': '2024-01-01T00:00:00Z',
                'updatedAt': '2024-01-05T00:00:00Z'
            },
            {
                'id': '4',
                'name': 'Appointment Cancellation',
                'type': 'email',
                'category': 'cancellation',
                'subject': 'Appointment Cancelled - {{appointment_date}}',
                'content': 'Dear {{patient_name}}, your appointment scheduled for {{appointment_date}} at {{appointment_time}} has been cancelled. Please contact us to reschedule.',
                'variables': ['patient_name', 'appointment_date', 'appointment_time'],
                'isActive': True,
                'createdAt': '2024-01-01T00:00:00Z',
                'updatedAt': '2024-01-08T00:00:00Z'
            }
        ]

        return JsonResponse({
            'templates': templates,
            'total_count': len(templates)
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_csrf_exempt
def send_manual_notification(request):
    """Send a manual notification"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get user role and hospital association
        user_role = getattr(user, 'role', user.profile.get('role') if hasattr(user, 'profile') else None)
        user_hospital = None
        
        if user_role in ['admin', 'staff']:
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=user)
                user_hospital = staff_profile.hospital
                if not user_hospital:
                    return JsonResponse({"error": "No hospital association found for staff user"}, status=403)
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({"error": "Staff profile not found"}, status=403)
        
        data = json.loads(request.body)
        
        notification_type = data.get('type')  # email, sms, push
        recipient_id = data.get('recipient_id')
        subject = data.get('subject', '')
        message = data.get('message', '')
        appointment_id = data.get('appointment_id')
        
        if not all([notification_type, recipient_id, message]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # For staff/admin users, verify recipient belongs to their hospital
        if user_hospital:
            try:
                # Check if recipient is a patient of this hospital
                patient_result = admin_client.table("patients").select("hospital_id").eq("id", recipient_id).execute()
                
                if not patient_result.data or str(patient_result.data[0]['hospital_id']) != str(user_hospital.id):
                    return JsonResponse({"error": "You can only send notifications to patients in your hospital"}, status=403)
                
                # If appointment is provided, verify it belongs to this hospital
                if appointment_id:
                    appt_result = admin_client.table("appointments").select("patient_id").eq("id", appointment_id).execute()
                    
                    if appt_result.data:
                        patient_id = appt_result.data[0]['patient_id']
                        patient_check = admin_client.table("patients").select("hospital_id").eq("id", patient_id).execute()
                        
                        if not patient_check.data or str(patient_check.data[0]['hospital_id']) != str(user_hospital.id):
                            return JsonResponse({"error": "You can only send notifications for appointments in your hospital"}, status=403)
            except Exception as e:
                print(f"Error verifying hospital association: {e}")
                return JsonResponse({"error": "Error verifying hospital association"}, status=500)

        # Create a manual scheduled task
        task = ScheduledTask.objects.create(
            task_type='manual',
            appointment_id=appointment_id or '00000000-0000-0000-0000-000000000000',
            delivery_method=notification_type,
            scheduled_time=timezone.now(),
            priority=1,  # High priority for manual notifications
            message_data={
                'subject': subject,
                'message': message,
                'recipient_id': recipient_id,
                'manual': True
            }
        )

        return JsonResponse({
            'success': True,
            'message': 'Notification queued successfully',
            'notification_id': str(task.id)
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def delete_subscription(request):
    """Delete a push notification subscription"""
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return JsonResponse({"error": "Endpoint required"}, status=400)

        # Delete subscription
        result = admin_client.table("push_subscriptions").delete().eq("user_id", user.id).eq("endpoint", endpoint).execute()
        
        if result.data:
            return JsonResponse({"message": "Subscription deleted successfully"})
        else:
            return JsonResponse({"error": "Subscription not found"}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_vapid_public_key(request):
    """Return VAPID public key for frontend subscription"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    return JsonResponse({
        "vapidPublicKey": settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY']
    })

@csrf_exempt
def test_notifications(request):
    """Test endpoint for notifications"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Get user role and hospital association
        user_role = getattr(user, 'role', user.profile.get('role') if hasattr(user, 'profile') else None)
        user_hospital = None
        
        if user_role in ['admin', 'staff']:
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=user)
                user_hospital = staff_profile.hospital
                if not user_hospital:
                    return JsonResponse({"error": "No hospital association found for staff user"}, status=403)
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({"error": "Staff profile not found"}, status=403)
        
        data = json.loads(request.body)
        test_type = data.get('type', 'reminder')  # reminder, confirmation, update
        appointment_id = data.get('appointment_id')

        if not appointment_id:
            return JsonResponse({"error": "appointment_id is required"}, status=400)
            
        # For staff/admin users, verify appointment belongs to their hospital
        if user_hospital:
            try:
                # Get appointment details
                appt_result = admin_client.table("appointments").select("patient_id").eq("id", appointment_id).execute()
                
                if not appt_result.data:
                    return JsonResponse({"error": "Appointment not found"}, status=404)
                    
                patient_id = appt_result.data[0]['patient_id']
                
                # Check if patient belongs to user's hospital
                patient_result = admin_client.table("patients").select("hospital_id").eq("id", patient_id).execute()
                
                if not patient_result.data or str(patient_result.data[0]['hospital_id']) != str(user_hospital.id):
                    return JsonResponse({"error": "You can only test notifications for appointments in your hospital"}, status=403)
            except Exception as e:
                print(f"Error verifying hospital association: {e}")
                return JsonResponse({"error": "Error verifying hospital association"}, status=500)

        # Test different notification types
        if test_type == 'reminder':
            success, message = trigger_manual_reminder(appointment_id)
        elif test_type == 'confirmation':
            success, message = send_appointment_confirmation(appointment_id)
        elif test_type == 'update':
            update_type = data.get('update_type', 'reschedule')
            success, message = send_appointment_update(appointment_id, update_type)
        else:
            return JsonResponse({"error": "Invalid test type"}, status=400)

        return JsonResponse({
            "success": success,
            "message": message,
            "test_type": test_type,
            "appointment_id": appointment_id
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def test_upcoming_reminders(request):
    """Test endpoint to trigger upcoming appointment reminders"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Get all appointments for testing
        appointments = admin_client.table("appointments").select("id").execute()
        
        if not appointments.data:
            return JsonResponse({"message": "No appointments found"}, status=404)

        results = []
        for appointment in appointments.data:
            success, message = trigger_manual_reminder(appointment["id"])
            results.append({
                "appointment_id": appointment["id"],
                "success": success,
                "message": message
            })

        return JsonResponse({
            "message": "Test completed",
            "results": results
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def check_subscriptions(request):
    """Debug endpoint to check user's push subscriptions"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Get all subscriptions for the user
        result = admin_client.table("push_subscriptions").select("*").eq("user_id", user.id).execute()
        
        return JsonResponse({
            "user_id": user.id,
            "subscriptions": result.data if result.data else []
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)