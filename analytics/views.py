from django.shortcuts import render
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from collections import defaultdict

# Import models from other apps
from appointments.models import Appointment
from billing.models import Invoice
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription
from .models import (
    SystemMetrics, UserActivity, AppointmentAnalytics,
    RevenueAnalytics, PatientDemographics, SystemPerformance,
    PopularServices
)

User = get_user_model()


@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    """Get comprehensive dashboard overview with key metrics filtered by user's hospital"""
    try:
        # Get current user's hospital
        user = request.user
        staff_profile = getattr(user, 'staff_profile', None)
        if not staff_profile or not staff_profile.hospital:
            return Response(
                {'error': 'User must be associated with a hospital'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        hospital = staff_profile.hospital
        
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        last_7_days = today - timedelta(days=7)
        
        # User Statistics - filtered by hospital
        hospital_users = User.objects.filter(staff_profile__hospital__pk=hospital.pk)
        total_users = hospital_users.count()
        active_users_30d = hospital_users.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        new_users_7d = hospital_users.filter(
            date_joined__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Appointment Statistics - filtered by hospital
        hospital_appointments = Appointment.objects.filter(hospital__pk=hospital.pk)
        total_appointments = hospital_appointments.count()
        appointments_today = hospital_appointments.filter(
            appointment_date=today
        ).count()
        appointments_this_week = hospital_appointments.filter(
            appointment_date__gte=last_7_days
        ).count()
        
        completed_appointments = hospital_appointments.filter(
            status='completed'
        ).count()
        
        pending_appointments = hospital_appointments.filter(
            status='scheduled',
            appointment_date__gte=today
        ).count()
        
        # Revenue Statistics (if billing app exists) - filtered by hospital
        try:
            # Filter invoices by hospital through appointment relationship
            hospital_invoices = Invoice.objects.filter(
                appointment__hospital__pk=hospital.pk
            )
            total_revenue = hospital_invoices.filter(
                status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            revenue_this_month = hospital_invoices.filter(
                status='paid',
                created_at__month=today.month,
                created_at__year=today.year
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            outstanding_payments = hospital_invoices.filter(
                status__in=['pending', 'overdue']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
        except:
            total_revenue = 0
            revenue_this_month = 0
            outstanding_payments = 0
        
        # Department-wise appointment distribution - filtered by hospital
        department_stats = hospital_appointments.values('provider__department').annotate(
            count=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            pending=Count('id', filter=Q(status='scheduled'))
        ).order_by('-count')[:6]
        
        # Recent activity trends (last 7 days) - filtered by hospital
        activity_trends = []
        for i in range(7):
            date = today - timedelta(days=i)
            appointments_count = hospital_appointments.filter(
                appointment_date=date
            ).count()
            
            new_users_count = hospital_users.filter(
                date_joined__date=date
            ).count()
            
            activity_trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'appointments': appointments_count,
                'new_users': new_users_count
            })
        
        # Top services/treatments - filtered by hospital
        popular_services = hospital_appointments.values('appointment_type__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # System health indicators - filtered by hospital
        system_health = {
            'database_status': 'healthy',
            'api_response_time': '< 200ms',
            'uptime': '99.9%',
            'active_sessions': hospital_users.filter(
                last_login__gte=timezone.now() - timedelta(hours=1)
            ).count()
        }
        
        dashboard_data = {
            'overview': {
                'total_users': total_users,
                'active_users_30d': active_users_30d,
                'new_users_7d': new_users_7d,
                'total_appointments': total_appointments,
                'appointments_today': appointments_today,
                'appointments_this_week': appointments_this_week,
                'completed_appointments': completed_appointments,
                'pending_appointments': pending_appointments,
                'total_revenue': float(total_revenue),
                'revenue_this_month': float(revenue_this_month),
                'outstanding_payments': float(outstanding_payments)
            },
            'department_stats': list(department_stats),
            'activity_trends': activity_trends,
            'popular_services': list(popular_services),
            'system_health': system_health,
            'last_updated': timezone.now().isoformat()
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch dashboard data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def appointment_analytics(request):
    """Get detailed appointment analytics"""
    try:
        # Get date range from query params
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Appointment status distribution
        status_distribution = Appointment.objects.filter(
            appointment_date__range=[start_date, end_date]
        ).values('status').annotate(count=Count('id'))
        
        # Daily appointment trends
        daily_trends = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            daily_count = Appointment.objects.filter(
                appointment_date=date
            ).count()
            daily_trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'appointments': daily_count
            })
        
        # Department performance
        department_performance = Appointment.objects.filter(
            appointment_date__range=[start_date, end_date]
        ).values('provider__department').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            cancelled=Count('id', filter=Q(status='cancelled')),
            no_show=Count('id', filter=Q(status='no_show'))
        ).order_by('-total')
        
        # Peak hours analysis
        hourly_distribution = Appointment.objects.filter(
            appointment_date__range=[start_date, end_date]
        ).extra(
            select={'hour': 'EXTRACT(hour FROM appointment_time)'}
        ).values('hour').annotate(count=Count('id')).order_by('hour')
        
        analytics_data = {
            'status_distribution': list(status_distribution),
            'daily_trends': daily_trends,
            'department_performance': list(department_performance),
            'hourly_distribution': list(hourly_distribution),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch appointment analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def revenue_analytics(request):
    """Get detailed revenue analytics"""
    try:
        # Get date range from query params
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Revenue trends
        revenue_trends = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            daily_revenue = Invoice.objects.filter(
                created_at__date=date,
                status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            revenue_trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'revenue': float(daily_revenue)
            })
        
        # Payment method distribution
        payment_methods = Invoice.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='paid'
        ).values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        )
        
        # Department revenue
        department_revenue = Invoice.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='paid'
        ).values('appointment__provider__department').annotate(
            revenue=Sum('total_amount'),
            count=Count('id')
        ).order_by('-revenue')
        
        # Outstanding payments
        outstanding = Invoice.objects.filter(
            status__in=['pending', 'overdue']
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        
        revenue_data = {
            'revenue_trends': revenue_trends,
            'payment_methods': list(payment_methods),
            'department_revenue': list(department_revenue),
            'outstanding_payments': {
                'total': float(outstanding['total'] or 0),
                'count': outstanding['count']
            },
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
        return Response(revenue_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch revenue analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def user_analytics(request):
    """Get user behavior and demographics analytics"""
    try:
        # Get date range from query params
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # User registration trends
        registration_trends = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            daily_registrations = User.objects.filter(
                date_joined__date=date
            ).count()
            
            registration_trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'registrations': daily_registrations
            })
        
        # User activity patterns
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=days)
        ).count()
        
        inactive_users = User.objects.filter(
            Q(last_login__lt=timezone.now() - timedelta(days=days)) |
            Q(last_login__isnull=True)
        ).count()
        
        # User role distribution
        role_distribution = User.objects.values('role').annotate(
            count=Count('id')
        )
        
        # Most active users (by appointment count)
        active_patients = User.objects.filter(
            role='patient'
        ).annotate(
            appointment_count=Count('appointment')
        ).order_by('-appointment_count')[:10]
        
        user_data = {
            'registration_trends': registration_trends,
            'activity_summary': {
                'active_users': active_users,
                'inactive_users': inactive_users,
                'total_users': User.objects.count()
            },
            'role_distribution': list(role_distribution),
            'most_active_patients': [
                {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'appointment_count': user.appointment_count
                } for user in active_patients
            ],
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
        return Response(user_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch user analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def system_performance(request):
    """Get system performance metrics"""
    try:
        # Mock system performance data (in a real system, this would come from monitoring tools)
        performance_data = {
            'current_metrics': {
                'cpu_usage': 45.2,
                'memory_usage': 67.8,
                'disk_usage': 34.1,
                'active_sessions': User.objects.filter(
                    last_login__gte=timezone.now() - timedelta(hours=1)
                ).count(),
                'api_response_time': 156.7,
                'database_queries_per_minute': 1247,
                'error_rate': 0.02,
                'uptime_hours': 720.5
            },
            'alerts': [
                {
                    'type': 'info',
                    'message': 'System running normally',
                    'timestamp': timezone.now().isoformat()
                }
            ],
            'recent_errors': [],
            'performance_trends': [
                {
                    'timestamp': (timezone.now() - timedelta(minutes=i*5)).isoformat(),
                    'response_time': 150 + (i * 2),
                    'cpu_usage': 40 + (i * 1.5)
                } for i in range(12)
            ]
        }
        
        return Response(performance_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch system performance: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
