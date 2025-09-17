from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from authentication.utils import get_authenticated_user
from .scheduler import scheduler, TaskPriority, get_scheduler_status
from .queue_manager import queue_manager, QueueType, get_queue_health
from .background_tasks import (
    background_task_manager, 
    TaskType, 
    get_background_task_status,
    run_task_immediately
)

logger = logging.getLogger(__name__)

def require_staff_auth(view_func):
    """Decorator to require staff authentication"""
    def wrapper(request, *args, **kwargs):
        try:
            user = get_authenticated_user(request)
            if not user or not getattr(user, 'is_staff', False):
                return JsonResponse({
                    'error': 'Staff authentication required',
                    'code': 'UNAUTHORIZED'
                }, status=401)
            request.user = user
            return view_func(request, *args, **kwargs)
        except Exception as e:
            return JsonResponse({
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR',
                'details': str(e)
            }, status=401)
    return wrapper

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_staff_auth, name='dispatch')
class SchedulerStatusView(View):
    """API endpoint for scheduler status and management"""
    
    def get(self, request):
        """Get scheduler status"""
        try:
            status = get_scheduler_status()
            return JsonResponse({
                'success': True,
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to get scheduler status',
                'details': str(e)
            }, status=500)
    
    def post(self, request):
        """Control scheduler operations"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'start':
                if not scheduler.is_running:
                    scheduler.start()
                    return JsonResponse({
                        'success': True,
                        'message': 'Scheduler started successfully'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Scheduler is already running'
                    }, status=400)
            
            elif action == 'stop':
                if scheduler.is_running:
                    scheduler.stop()
                    return JsonResponse({
                        'success': True,
                        'message': 'Scheduler stopped successfully'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Scheduler is not running'
                    }, status=400)
            
            elif action == 'restart':
                if scheduler.is_running:
                    scheduler.stop()
                scheduler.start()
                return JsonResponse({
                    'success': True,
                    'message': 'Scheduler restarted successfully'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action. Use: start, stop, or restart'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error controlling scheduler: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to control scheduler',
                'details': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_staff_auth, name='dispatch')
class QueueStatusView(View):
    """API endpoint for queue status and management"""
    
    def get(self, request):
        """Get queue status"""
        try:
            queue_type = request.GET.get('type')
            
            if queue_type:
                try:
                    qt = QueueType(queue_type)
                    status = queue_manager.get_queue_status(qt)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid queue type: {queue_type}'
                    }, status=400)
            else:
                status = queue_manager.get_queue_status()
            
            health = get_queue_health()
            
            return JsonResponse({
                'success': True,
                'data': {
                    'status': status,
                    'health': health
                },
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to get queue status',
                'details': str(e)
            }, status=500)
    
    def post(self, request):
        """Control queue operations"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            queue_type = data.get('queue_type')
            
            if not queue_type:
                return JsonResponse({
                    'success': False,
                    'error': 'queue_type is required'
                }, status=400)
            
            try:
                qt = QueueType(queue_type)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid queue type: {queue_type}'
                }, status=400)
            
            if action == 'pause':
                queue_manager.pause_queue(qt)
                return JsonResponse({
                    'success': True,
                    'message': f'Queue {queue_type} paused successfully'
                })
            
            elif action == 'resume':
                queue_manager.resume_queue(qt)
                return JsonResponse({
                    'success': True,
                    'message': f'Queue {queue_type} resumed successfully'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action. Use: pause or resume'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error controlling queue: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to control queue',
                'details': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_staff_auth, name='dispatch')
class BackgroundTasksView(View):
    """API endpoint for background tasks management"""
    
    def get(self, request):
        """Get background tasks status"""
        try:
            status = get_background_task_status()
            return JsonResponse({
                'success': True,
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting background tasks status: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to get background tasks status',
                'details': str(e)
            }, status=500)
    
    def post(self, request):
        """Control background tasks"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            task_type = data.get('task_type')
            
            if action == 'run_now':
                if not task_type:
                    return JsonResponse({
                        'success': False,
                        'error': 'task_type is required for run_now action'
                    }, status=400)
                
                try:
                    tt = TaskType(task_type)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid task type: {task_type}'
                    }, status=400)
                
                success = run_task_immediately(tt)
                if success:
                    return JsonResponse({
                        'success': True,
                        'message': f'Task {task_type} started successfully'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'Failed to start task {task_type}'
                    }, status=500)
            
            elif action == 'enable':
                if not task_type:
                    return JsonResponse({
                        'success': False,
                        'error': 'task_type is required for enable action'
                    }, status=400)
                
                try:
                    tt = TaskType(task_type)
                    background_task_manager.enable_task(tt)
                    return JsonResponse({
                        'success': True,
                        'message': f'Task {task_type} enabled successfully'
                    })
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid task type: {task_type}'
                    }, status=400)
            
            elif action == 'disable':
                if not task_type:
                    return JsonResponse({
                        'success': False,
                        'error': 'task_type is required for disable action'
                    }, status=400)
                
                try:
                    tt = TaskType(task_type)
                    background_task_manager.disable_task(tt)
                    return JsonResponse({
                        'success': True,
                        'message': f'Task {task_type} disabled successfully'
                    })
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid task type: {task_type}'
                    }, status=400)
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action. Use: run_now, enable, or disable'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error controlling background tasks: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to control background tasks',
                'details': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_staff_auth, name='dispatch')
class ScheduleReminderView(View):
    """API endpoint for scheduling reminders"""
    
    def post(self, request):
        """Schedule a new reminder"""
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['appointment_id', 'reminder_type', 'scheduled_time']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            appointment_id = data['appointment_id']
            reminder_type = data['reminder_type']
            scheduled_time_str = data['scheduled_time']
            delivery_method = data.get('delivery_method', 'sms')
            priority_str = data.get('priority', 'medium')
            
            # Parse scheduled time
            try:
                scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid scheduled_time format. Use ISO format.'
                }, status=400)
            
            # Parse priority
            priority_map = {
                'urgent': TaskPriority.URGENT,
                'high': TaskPriority.HIGH,
                'medium': TaskPriority.MEDIUM,
                'low': TaskPriority.LOW
            }
            priority = priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)
            
            # Schedule the reminder
            task_id = scheduler.schedule_reminder(
                appointment_id=appointment_id,
                reminder_type=reminder_type,
                scheduled_time=scheduled_time,
                delivery_method=delivery_method,
                priority=priority
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'task_id': task_id,
                    'appointment_id': appointment_id,
                    'reminder_type': reminder_type,
                    'scheduled_time': scheduled_time.isoformat(),
                    'delivery_method': delivery_method,
                    'priority': priority_str
                },
                'message': 'Reminder scheduled successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error scheduling reminder: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to schedule reminder',
                'details': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_staff_auth, name='dispatch')
class CancelReminderView(View):
    """API endpoint for canceling reminders"""
    
    def post(self, request):
        """Cancel a scheduled reminder"""
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            
            if not task_id:
                return JsonResponse({
                    'success': False,
                    'error': 'task_id is required'
                }, status=400)
            
            success = scheduler.cancel_task(task_id)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Reminder {task_id} cancelled successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to cancel reminder {task_id}'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error canceling reminder: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to cancel reminder',
                'details': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_staff_auth, name='dispatch')
class SystemHealthView(View):
    """API endpoint for overall system health"""
    
    def get(self, request):
        """Get overall system health status"""
        try:
            scheduler_status = get_scheduler_status()
            queue_health = get_queue_health()
            background_status = get_background_task_status()
            
            # Calculate overall health score
            health_factors = [
                scheduler_status['is_running'],
                queue_health['health_score'] >= 80,
                background_status['is_running'],
                queue_health['error_queues'] == 0
            ]
            
            health_score = (sum(health_factors) / len(health_factors)) * 100
            
            # Determine status
            if health_score >= 90:
                status = 'excellent'
            elif health_score >= 75:
                status = 'good'
            elif health_score >= 50:
                status = 'degraded'
            else:
                status = 'critical'
            
            return JsonResponse({
                'success': True,
                'data': {
                    'overall_health': {
                        'score': health_score,
                        'status': status,
                        'timestamp': datetime.now().isoformat()
                    },
                    'components': {
                        'scheduler': {
                            'status': 'healthy' if scheduler_status['is_running'] else 'unhealthy',
                            'details': scheduler_status
                        },
                        'queue_manager': {
                            'status': queue_health['status'],
                            'details': queue_health
                        },
                        'background_tasks': {
                            'status': 'healthy' if background_status['is_running'] else 'unhealthy',
                            'details': background_status
                        }
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to get system health',
                'details': str(e)
            }, status=500)

# URL patterns for the scheduler API
from django.urls import path

scheduler_api_urls = [
    path('scheduler/status/', SchedulerStatusView.as_view(), name='scheduler_status'),
    path('scheduler/queue/', QueueStatusView.as_view(), name='queue_status'),
    path('scheduler/background-tasks/', BackgroundTasksView.as_view(), name='background_tasks'),
    path('scheduler/schedule-reminder/', ScheduleReminderView.as_view(), name='schedule_reminder'),
    path('scheduler/cancel-reminder/', CancelReminderView.as_view(), name='cancel_reminder'),
    path('scheduler/health/', SystemHealthView.as_view(), name='system_health'),
]

__all__ = [
    'SchedulerStatusView', 'QueueStatusView', 'BackgroundTasksView',
    'ScheduleReminderView', 'CancelReminderView', 'SystemHealthView',
    'scheduler_api_urls'
]