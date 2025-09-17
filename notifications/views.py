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
        data = json.loads(request.body)
        test_type = data.get('type', 'reminder')  # reminder, confirmation, update
        appointment_id = data.get('appointment_id')

        if not appointment_id:
            return JsonResponse({"error": "appointment_id is required"}, status=400)

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