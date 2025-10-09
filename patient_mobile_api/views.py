"""
Patient Mobile API Views
Provides API endpoints specifically designed for the patient mobile application
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
from accounts.models import EnhancedPatient, Hospital
from appointments.models import Appointment, AppointmentType
from prescriptions.models import Prescription, MedicationReminder
from notifications.models import ScheduledTask
from .serializers import (
    PatientDashboardSerializer,
    DashboardAppointmentSerializer,
    DashboardMedicationSerializer,
    DashboardNotificationSerializer,
    DashboardStatsSerializer,
    DashboardServiceSerializer
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class PatientDashboardAPIView(APIView):
    """
    Main dashboard API endpoint that provides comprehensive dashboard data
    for the patient mobile application
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get comprehensive dashboard data for the authenticated patient
        """
        try:
            # Get the patient profile
            try:
                patient = EnhancedPatient.objects.select_related('user').get(user=request.user)
            except EnhancedPatient.DoesNotExist:
                return Response(
                    {'error': 'Patient profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get today's date
            today = timezone.now().date()
            
            # Aggregate dashboard data
            dashboard_data = {
                'patient_name': patient.user.full_name,
                'todays_stats': self._get_today_stats(patient, today),
                'upcoming_appointments': self._get_upcoming_appointments(patient),
                'current_medications': self._get_current_medications(patient),
                'recent_notifications': self._get_recent_notifications(patient),
                'services': self._get_available_services(),
                'last_updated': timezone.now()
            }
            
            # Serialize the data
            serializer = PatientDashboardSerializer(dashboard_data)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Dashboard API error for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to load dashboard data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_today_stats(self, patient, today):
        """Get today's statistics for the dashboard"""
        try:
            # Count appointments today
            appointments_today = Appointment.objects.filter(
                patient=patient,
                appointment_date=today,
                status__in=['scheduled', 'confirmed', 'in_progress']
            ).count()
            
            # Count medications due today (simplified logic)
            medications_due = MedicationReminder.objects.filter(
                prescription__patient=patient,
                is_active=True
            ).count()
            
            # Count pending reminders
            pending_reminders = ScheduledTask.objects.filter(
                status='pending',
                scheduled_time__date=today
            ).count()
            
            # Reports available (placeholder - would need actual reports model)
            reports_available = 0
            
            return {
                'appointments_today': appointments_today,
                'medications_due': medications_due,
                'pending_reminders': pending_reminders,
                'reports_available': reports_available
            }
        except Exception as e:
            logger.error(f"Error getting today stats: {str(e)}")
            return {
                'appointments_today': 0,
                'medications_due': 0,
                'pending_reminders': 0,
                'reports_available': 0
            }
    
    def _get_upcoming_appointments(self, patient):
        """Get upcoming appointments for the patient"""
        try:
            # Get next 5 upcoming appointments
            upcoming_appointments = Appointment.objects.filter(
                patient=patient,
                appointment_date__gte=timezone.now().date(),
                status__in=['scheduled', 'confirmed']
            ).select_related(
                'provider__user',
                'hospital',
                'appointment_type'
            ).order_by('appointment_date', 'start_time')[:5]
            
            return upcoming_appointments
        except Exception as e:
            logger.error(f"Error getting upcoming appointments: {str(e)}")
            return []
    
    def _get_current_medications(self, patient):
        """Get current active medications for the patient"""
        try:
            # Get active medication reminders
            current_medications = MedicationReminder.objects.filter(
                prescription__patient=patient,
                is_active=True
            ).select_related('prescription__drug')[:5]
            
            return current_medications
        except Exception as e:
            logger.error(f"Error getting current medications: {str(e)}")
            return []
    
    def _get_recent_notifications(self, patient):
        """Get recent notifications for the patient"""
        try:
            # Get recent notifications (last 24 hours)
            yesterday = timezone.now() - timedelta(days=1)
            recent_notifications = ScheduledTask.objects.filter(
                created_at__gte=yesterday
            ).order_by('-created_at')[:5]
            
            return recent_notifications
        except Exception as e:
            logger.error(f"Error getting recent notifications: {str(e)}")
            return []
    
    def _get_available_services(self):
        """Get available services for the dashboard"""
        try:
            # Static services data matching the Flutter dashboard
            services = [
                {
                    'id': 'consultation',
                    'name': 'Consultation',
                    'icon': 'consultation_icon',
                    'description': 'Book a consultation with a doctor',
                    'is_available': True
                },
                {
                    'id': 'pharmacy',
                    'name': 'Pharmacy',
                    'icon': 'pharmacy_icon',
                    'description': 'Order medications and prescriptions',
                    'is_available': True
                },
                {
                    'id': 'reports',
                    'name': 'Reports',
                    'icon': 'reports_icon',
                    'description': 'View your medical reports',
                    'is_available': True
                },
                {
                    'id': 'health',
                    'name': 'Health',
                    'icon': 'health_icon',
                    'description': 'Track your health metrics',
                    'is_available': True
                }
            ]
            
            return services
        except Exception as e:
            logger.error(f"Error getting available services: {str(e)}")
            return []


class PatientMedicationAPIView(APIView):
    """
    API endpoint for patient medication management
    Provides CRUD operations for patient medications
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, medication_id=None):
        """
        Get patient medications, a specific medication, or adherence data
        """
        try:
            # Check if this is an adherence request
            if request.path.endswith('/adherence/'):
                return self.get_adherence(request)
            
            patient = EnhancedPatient.objects.select_related('user').get(user=request.user)
            
            if medication_id:
                # Get specific medication
                try:
                    medication = MedicationReminder.objects.get(
                        id=medication_id,
                        prescription__patient=patient
                    )
                    serializer = DashboardMedicationSerializer(medication)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                except MedicationReminder.DoesNotExist:
                    return Response(
                        {'error': 'Medication not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Get all medications for the patient
                medications = MedicationReminder.objects.filter(
                    prescription__patient=patient,
                    is_active=True
                ).select_related('prescription__drug')
                
                serializer = DashboardMedicationSerializer(medications, many=True)
                # Return the list directly for Flutter compatibility
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except EnhancedPatient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Medication API error for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to load medications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Create a new medication reminder
        """
        try:
            patient = EnhancedPatient.objects.select_related('user').get(user=request.user)
            
            # Create a prescription first (required for medication reminder)
            prescription_data = {
                'patient': patient,
                'medication': request.data.get('medication_name', 'Unknown Medication'),
                'dosage': request.data.get('dosage', ''),
                'frequency': request.data.get('frequency', 'daily'),
                'quantity': request.data.get('quantity', 30),
                'refills': request.data.get('refills_remaining', 0),
                'prescribed_by': request.data.get('prescribed_by', ''),
                'instructions': request.data.get('instructions', ''),
                'pharmacy': request.data.get('pharmacy', ''),
                'is_active': True
            }
            
            prescription = Prescription.objects.create(**prescription_data)
            
            # Create medication reminder
            reminder_data = {
                'prescription': prescription,
                'dosage': request.data.get('dosage', ''),
                'frequency': request.data.get('frequency', 'daily'),
                'times': request.data.get('times', ['08:00']),
                'start_date': request.data.get('start_date', timezone.now().date()),
                'end_date': request.data.get('end_date'),
                'instructions': request.data.get('instructions', ''),
                'is_active': True,
                'send_sms': request.data.get('send_sms', False),
                'send_email': request.data.get('send_email', False),
                'send_push': request.data.get('send_push', True),
                'advance_notice_minutes': request.data.get('advance_notice_minutes', 15),
                'snooze_minutes': request.data.get('snooze_minutes', 15),
                'max_snoozes': request.data.get('max_snoozes', 3)
            }
            
            medication_reminder = MedicationReminder.objects.create(**reminder_data)
            
            serializer = DashboardMedicationSerializer(medication_reminder)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except EnhancedPatient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Create medication API error for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to create medication'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, medication_id):
        """
        Update an existing medication reminder
        """
        try:
            patient = EnhancedPatient.objects.select_related('user').get(user=request.user)
            
            medication = MedicationReminder.objects.get(
                id=medication_id,
                prescription__patient=patient
            )
            
            # Update prescription if needed
            prescription = medication.prescription
            if 'medication_name' in request.data:
                prescription.medication = request.data['medication_name']
            if 'prescribed_by' in request.data:
                prescription.prescribed_by = request.data['prescribed_by']
            if 'pharmacy' in request.data:
                prescription.pharmacy = request.data['pharmacy']
            if 'refills_remaining' in request.data:
                prescription.refills = request.data['refills_remaining']
            if 'instructions' in request.data:
                prescription.instructions = request.data['instructions']
            prescription.save()
            
            # Update medication reminder
            if 'dosage' in request.data:
                medication.dosage = request.data['dosage']
            if 'frequency' in request.data:
                medication.frequency = request.data['frequency']
            if 'times' in request.data:
                medication.times = request.data['times']
            if 'start_date' in request.data:
                medication.start_date = request.data['start_date']
            if 'end_date' in request.data:
                medication.end_date = request.data['end_date']
            if 'is_active' in request.data:
                medication.is_active = request.data['is_active']
            if 'send_sms' in request.data:
                medication.send_sms = request.data['send_sms']
            if 'send_email' in request.data:
                medication.send_email = request.data['send_email']
            if 'send_push' in request.data:
                medication.send_push = request.data['send_push']
            if 'advance_notice_minutes' in request.data:
                medication.advance_notice_minutes = request.data['advance_notice_minutes']
            if 'snooze_minutes' in request.data:
                medication.snooze_minutes = request.data['snooze_minutes']
            if 'max_snoozes' in request.data:
                medication.max_snoozes = request.data['max_snoozes']
            
            medication.save()
            
            serializer = DashboardMedicationSerializer(medication)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except EnhancedPatient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except MedicationReminder.DoesNotExist:
            return Response(
                {'error': 'Medication not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Update medication API error for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to update medication'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, medication_id):
        """
        Delete a medication reminder
        """
        try:
            patient = EnhancedPatient.objects.select_related('user').get(user=request.user)
            
            medication = MedicationReminder.objects.get(
                id=medication_id,
                prescription__patient=patient
            )
            
            # Soft delete by setting is_active to False
            medication.is_active = False
            medication.save()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except EnhancedPatient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except MedicationReminder.DoesNotExist:
            return Response(
                {'error': 'Medication not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
                logger.error(f"Delete medication API error for user {request.user.id}: {str(e)}")
                return Response(
                    {'error': 'Failed to delete medication'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def get_adherence(self, request):
        """
        Get medication adherence data for the patient
        """
        try:
            patient = EnhancedPatient.objects.select_related('user').get(user=request.user)
            
            # Get adherence records for the patient's prescriptions
            from prescriptions.models import MedicationAdherence
            
            adherence_records = MedicationAdherence.objects.filter(
                prescription__patient=patient
            ).select_related('prescription__drug').order_by('-period_end')
            
            # Serialize the adherence data
            adherence_data = []
            for record in adherence_records:
                adherence_data.append({
                    'id': str(record.id),
                    'medication_name': record.prescription.drug.generic_name if record.prescription.drug else record.prescription.medication,
                    'period_start': record.period_start,
                    'period_end': record.period_end,
                    'doses_prescribed': record.doses_prescribed,
                    'doses_taken': record.doses_taken,
                    'adherence_percentage': float(record.adherence_percentage),
                    'adherence_rating': record.adherence_rating,
                    'tracking_method': record.tracking_method,
                    'notes': record.notes,
                    'created_at': record.created_at
                })
            
            return Response(adherence_data, status=status.HTTP_200_OK)
            
        except EnhancedPatient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Adherence API error for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to load adherence data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PatientProfileAPIView(APIView):
    """
    API endpoint for patient profile management
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get patient profile information"""
        try:
            patient = EnhancedPatient.objects.select_related('user').get(user=request.user)
            
            profile_data = {
                'id': str(patient.id),
                'full_name': patient.user.full_name,
                'email': patient.user.email,
                'phone': patient.phone,
                'date_of_birth': patient.date_of_birth,
                'emergency_contact_name': patient.emergency_contact_name,
                'emergency_contact_phone': patient.emergency_contact_phone,
                'created_at': patient.created_at
            }
            
            return Response({
                'success': True,
                'data': profile_data
            }, status=status.HTTP_200_OK)
            
        except EnhancedPatient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Profile API error for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to load profile data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
