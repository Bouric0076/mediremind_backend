"""
FCM-specific views for token registration and push notifications
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from authentication.middleware import api_csrf_exempt, get_request_user
from .fcm_service import fcm_service
from .models import ScheduledTask
from datetime import datetime

logger = logging.getLogger(__name__)


@api_csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def register_fcm_token(request):
    """
    Register FCM token for a user
    
    Expected payload:
    {
        "fcm_token": "string",
        "device_info": {
            "platform": "android|ios",
            "device_id": "string",
            "app_version": "string"
        }
    }
    """
    if request.method == "OPTIONS":
        return JsonResponse({"message": "OK"}, status=200)
    
    # Get authenticated user
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    try:
        data = json.loads(request.body)
        fcm_token = data.get('fcm_token')
        device_info = data.get('device_info', {})
        
        if not fcm_token:
            return JsonResponse({"error": "fcm_token is required"}, status=400)
        
        # Register token with FCM service
        success = fcm_service.register_token(
            user_id=str(user.id),
            fcm_token=fcm_token,
            device_info=device_info
        )
        
        if success:
            logger.info(f"FCM token registered successfully for user {user.id}")
            return JsonResponse({
                "message": "FCM token registered successfully",
                "user_id": str(user.id)
            }, status=200)
        else:
            logger.error(f"Failed to register FCM token for user {user.id}")
            return JsonResponse({"error": "Failed to register FCM token"}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        logger.error(f"Error in register_fcm_token: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@api_csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def unregister_fcm_token(request):
    """
    Unregister FCM token for a user
    
    Expected payload:
    {
        "fcm_token": "string" (optional - if not provided, all tokens for user are removed)
    }
    """
    if request.method == "OPTIONS":
        return JsonResponse({"message": "OK"}, status=200)
    
    # Get authenticated user
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    try:
        data = json.loads(request.body)
        fcm_token = data.get('fcm_token')
        
        # Unregister token with FCM service
        success = fcm_service.unregister_token(
            user_id=str(user.id),
            fcm_token=fcm_token
        )
        
        if success:
            logger.info(f"FCM token unregistered successfully for user {user.id}")
            return JsonResponse({
                "message": "FCM token unregistered successfully",
                "user_id": str(user.id)
            }, status=200)
        else:
            logger.error(f"Failed to unregister FCM token for user {user.id}")
            return JsonResponse({"error": "Failed to unregister FCM token"}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        logger.error(f"Error in unregister_fcm_token: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@api_csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def send_test_notification(request):
    """
    Send a test FCM notification to the authenticated user
    
    Expected payload:
    {
        "title": "string",
        "body": "string",
        "data": {} (optional)
    }
    """
    if request.method == "OPTIONS":
        return JsonResponse({"message": "OK"}, status=200)
    
    # Get authenticated user
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    try:
        data = json.loads(request.body)
        title = data.get('title', 'Test Notification')
        body = data.get('body', 'This is a test notification from MediRemind')
        notification_data = data.get('data', {})
        
        # Send notification to user
        result = fcm_service.send_to_user(
            user_id=str(user.id),
            title=title,
            body=body,
            data=notification_data
        )
        
        if result['success'] > 0:
            logger.info(f"Test notification sent successfully to user {user.id}")
            return JsonResponse({
                "message": "Test notification sent successfully",
                "result": result
            }, status=200)
        else:
            logger.warning(f"Test notification failed for user {user.id}: {result}")
            return JsonResponse({
                "message": "Test notification failed",
                "result": result
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        logger.error(f"Error in send_test_notification: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@api_csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def send_notification_to_user(request):
    """
    Send FCM notification to a specific user (admin/staff only)
    
    Expected payload:
    {
        "user_id": "string",
        "title": "string",
        "body": "string",
        "data": {} (optional),
        "priority": "high|normal" (optional, default: high)
    }
    """
    if request.method == "OPTIONS":
        return JsonResponse({"message": "OK"}, status=200)
    
    # Get authenticated user
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    # Check if user has permission to send notifications
    user_role = getattr(user, 'role', None)
    if user_role not in ['admin', 'staff']:
        return JsonResponse({"error": "Insufficient permissions"}, status=403)
    
    try:
        data = json.loads(request.body)
        target_user_id = data.get('user_id')
        title = data.get('title')
        body = data.get('body')
        notification_data = data.get('data', {})
        priority = data.get('priority', 'high')
        
        if not all([target_user_id, title, body]):
            return JsonResponse({
                "error": "user_id, title, and body are required"
            }, status=400)
        
        # Send notification to target user
        result = fcm_service.send_to_user(
            user_id=target_user_id,
            title=title,
            body=body,
            data=notification_data,
            priority=priority
        )
        
        # Log the notification sending
        ScheduledTask.objects.create(
            task_type='notification',
            delivery_method='push',
            recipient_id=target_user_id,
            title=title,
            message=body,
            metadata={
                'sent_by': str(user.id),
                'fcm_result': result,
                'data': notification_data
            },
            status='completed' if result['success'] > 0 else 'failed',
            scheduled_time=datetime.now(),
            completed_at=datetime.now() if result['success'] > 0 else None
        )
        
        if result['success'] > 0:
            logger.info(f"Notification sent successfully to user {target_user_id} by {user.id}")
            return JsonResponse({
                "message": "Notification sent successfully",
                "result": result
            }, status=200)
        else:
            logger.warning(f"Notification failed for user {target_user_id}: {result}")
            return JsonResponse({
                "message": "Notification sending failed",
                "result": result
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        logger.error(f"Error in send_notification_to_user: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@api_csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def send_notification_to_topic(request):
    """
    Send FCM notification to a topic (admin only)
    
    Expected payload:
    {
        "topic": "string",
        "title": "string",
        "body": "string",
        "data": {} (optional),
        "priority": "high|normal" (optional, default: high)
    }
    """
    if request.method == "OPTIONS":
        return JsonResponse({"message": "OK"}, status=200)
    
    # Get authenticated user
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    # Check if user has admin permission
    user_role = getattr(user, 'role', None)
    if user_role != 'admin':
        return JsonResponse({"error": "Admin permissions required"}, status=403)
    
    try:
        data = json.loads(request.body)
        topic = data.get('topic')
        title = data.get('title')
        body = data.get('body')
        notification_data = data.get('data', {})
        priority = data.get('priority', 'high')
        
        if not all([topic, title, body]):
            return JsonResponse({
                "error": "topic, title, and body are required"
            }, status=400)
        
        # Send notification to topic
        result = fcm_service.send_to_topic(
            topic=topic,
            title=title,
            body=body,
            data=notification_data,
            priority=priority
        )
        
        # Log the notification sending
        ScheduledTask.objects.create(
            task_type='notification',
            delivery_method='push',
            recipient_id=f'topic:{topic}',
            title=title,
            message=body,
            metadata={
                'sent_by': str(user.id),
                'fcm_result': result,
                'data': notification_data,
                'topic': topic
            },
            status='completed' if result['success'] > 0 else 'failed',
            scheduled_time=datetime.now(),
            completed_at=datetime.now() if result['success'] > 0 else None
        )
        
        if result['success'] > 0:
            logger.info(f"Topic notification sent successfully to '{topic}' by {user.id}")
            return JsonResponse({
                "message": "Topic notification sent successfully",
                "result": result
            }, status=200)
        else:
            logger.warning(f"Topic notification failed for '{topic}': {result}")
            return JsonResponse({
                "message": "Topic notification sending failed",
                "result": result
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        logger.error(f"Error in send_notification_to_topic: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@api_csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def get_fcm_status(request):
    """
    Get FCM configuration status and user token information
    """
    if request.method == "OPTIONS":
        return JsonResponse({"message": "OK"}, status=200)
    
    # Get authenticated user
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    try:
        # Get user's FCM tokens
        user_tokens = fcm_service.get_user_tokens(str(user.id))
        
        return JsonResponse({
            "fcm_configured": fcm_service.is_configured(),
            "user_id": str(user.id),
            "registered_tokens": len(user_tokens),
            "has_tokens": len(user_tokens) > 0
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error in get_fcm_status: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@method_decorator(api_csrf_exempt, name='dispatch')
class FCMTopicManagementView(View):
    """
    View for managing FCM topic subscriptions
    """
    
    def post(self, request):
        """
        Subscribe/unsubscribe tokens to/from topics
        
        Expected payload:
        {
            "action": "subscribe|unsubscribe",
            "topic": "string",
            "tokens": ["token1", "token2"] (optional - uses user's tokens if not provided)
        }
        """
        # Get authenticated user
        user = get_request_user(request)
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Check permissions
        user_role = getattr(user, 'role', None)
        if user_role not in ['admin', 'staff']:
            return JsonResponse({"error": "Insufficient permissions"}, status=403)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            topic = data.get('topic')
            tokens = data.get('tokens')
            
            if not all([action, topic]):
                return JsonResponse({
                    "error": "action and topic are required"
                }, status=400)
            
            if action not in ['subscribe', 'unsubscribe']:
                return JsonResponse({
                    "error": "action must be 'subscribe' or 'unsubscribe'"
                }, status=400)
            
            # Use provided tokens or get user's tokens
            if not tokens:
                tokens = fcm_service.get_user_tokens(str(user.id))
                if not tokens:
                    return JsonResponse({
                        "error": "No FCM tokens found for user"
                    }, status=400)
            
            # Perform the action
            if action == 'subscribe':
                result = fcm_service.subscribe_to_topic(tokens, topic)
            else:
                result = fcm_service.unsubscribe_from_topic(tokens, topic)
            
            logger.info(f"Topic {action} completed for topic '{topic}': {result}")
            return JsonResponse({
                "message": f"Topic {action} completed",
                "result": result
            }, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)
        except Exception as e:
            logger.error(f"Error in FCMTopicManagementView: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    
    def options(self, request):
        return JsonResponse({"message": "OK"}, status=200)