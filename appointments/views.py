from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction, models
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from authentication.utils import get_authenticated_user
from authentication.middleware import api_csrf_exempt, get_request_user
from .models import Appointment, AppointmentType, Room, Equipment, AppointmentWaitlist
from accounts.models import EnhancedPatient, EnhancedStaffProfile, HospitalPatient
from .serializers import (
    AppointmentSerializer, AppointmentCreateSerializer, AppointmentUpdateSerializer,
    AppointmentListSerializer, AppointmentTypeSerializer,
    AppointmentWaitlistSerializer, TimeSlotSerializer
)
from .forms import (
    AppointmentForm, AppointmentUpdateForm, AppointmentCancelForm,
    AppointmentSearchForm, AvailabilityCheckForm
)
from .utils import (
    validate_appointment_datetime,
    check_doctor_availability,
    check_patient_availability,
    validate_appointment_type,
    validate_appointment_status,
    process_immediate_reminders,  # Add this for free tier reminders
    get_filtered_appointments
)
from notifications.utils import send_appointment_confirmation, send_appointment_update
from notifications.appointment_reminders import appointment_reminder_service
from notifications.textsms_client import textsms_client
import json
import uuid
from datetime import datetime, timedelta, time, date
import logging
import phonenumbers
from phonenumbers import NumberParseException

logger = logging.getLogger(__name__)


def check_patient_hospital_relationship(patient, hospital):
    """Check if patient has a relationship with the given hospital"""
    return HospitalPatient.objects.filter(patient=patient, hospital=hospital, status='active').exists()


def send_appointment_notification(appointment_data, action, patient_email, doctor_email):
    """Send appointment notifications using synchronous calls for free tier"""
    try:
        from django.conf import settings
        
        # Send appointment creation emails for new appointments
        if action == "created":
            # Extract patient name from appointment data
            patient_name = appointment_data.get('patient', 'Patient')
            
            # Prepare appointment details for email with robust type checking
            def safe_get_provider_name():
                """Safely extract provider name with type checking"""
                provider_data = appointment_data.get('provider')
                if isinstance(provider_data, dict):
                    user_data = provider_data.get('user')
                    if isinstance(user_data, dict):
                        return user_data.get('full_name')
                    return provider_data.get('user_name') or provider_data.get('name')
                elif isinstance(provider_data, str):
                    return provider_data
                return None
            
            def safe_get_appointment_type():
                """Safely extract appointment type name with type checking"""
                appointment_type_data = appointment_data.get('appointment_type')
                if isinstance(appointment_type_data, dict):
                    return appointment_type_data.get('name')
                elif isinstance(appointment_type_data, str):
                    return appointment_type_data
                return None
            
            # Prepare appointment details using nested API structure for template compatibility
            appointment_details = {
                'id': appointment_data['id'],
                'appointment_date': appointment_data.get('appointment_date'),
                'start_time': appointment_data.get('start_time'),
                'duration': appointment_data.get('duration') or 30,
                'status': 'created',
                'patient': {
                    'id': appointment_data.get('patient_id'),
                    'name': appointment_data.get('patient_name', patient_name),
                    'email': appointment_data.get('patient_email', patient_email),
                },
                'provider': {
                    'id': appointment_data.get('provider_id'),
                    'name': appointment_data.get('provider_name') or safe_get_provider_name() or 'Dr. Smith',
                    'email': doctor_email
                },
                'appointment_type': {
                    'name': appointment_data.get('appointment_type_name') or safe_get_appointment_type() or 'Consultation'
                },
                'hospital': {
                    'name': appointment_data.get('hospital_name') or 'MediRemind Partner Clinic'
                },
                'room': {
                    'name': appointment_data.get('room_name') or 'Room 1'
                }
            }
            
            # Add legacy aliases for backward compatibility
            appointment_details.update({
                'date': appointment_data.get('appointment_date'),
                'time': appointment_data.get('start_time'),
                'doctor_name': appointment_data.get('provider_name') or safe_get_provider_name() or 'Dr. Smith',
                'appointment_type_name': appointment_data.get('appointment_type_name') or safe_get_appointment_type() or 'Consultation',
                'patient_id': appointment_data.get('patient_id'),
                'patient_name': appointment_data.get('patient_name', patient_name),
                'patient_email': appointment_data.get('patient_email', patient_email),
            })
            
            # Use async Celery tasks for appointment creation emails
            from notifications.tasks import send_appointment_creation_email_async
            
            # Send appointment creation email to patient (async)
            send_appointment_creation_email_async.delay(
                appointment_data=appointment_details,
                recipient_email=patient_email,
                is_patient=True
            )
            
            # Send appointment creation email to doctor (async)
            send_appointment_creation_email_async.delay(
                appointment_data=appointment_details,
                recipient_email=doctor_email,
                is_patient=False
            )
            
            # Return immediate success - emails will be sent asynchronously
            success = True
            response_message = "Appointment creation emails queued for delivery"
            
            if success:
                logger.info(f"Appointment creation emails sent successfully to patient {patient_email} and doctor {doctor_email}")
            else:
                logger.warning(f"Appointment creation emails failed: {response_message}")
        
        # Handle appointment updates - send update notifications
        elif action == "updated":
            try:
                # Extract patient name from appointment data
                patient_name = appointment_data.get('patient', 'Patient')
                
                # Determine update type based on status change
                old_status = appointment_data.get('changes', {}).get('status', {}).get('old', '')
                new_status = appointment_data.get('changes', {}).get('status', {}).get('new', '')
                
                logger.info(f"Status change detected: '{old_status}' -> '{new_status}'")
                
                # Default to 'reschedule' for general updates, use 'cancellation' for cancellations and no-shows
                update_type = 'reschedule'  # Default for most updates
                if old_status and new_status:
                    if new_status == 'cancelled':
                        update_type = 'cancellation'
                        logger.info(f"Setting update_type to 'cancellation' for status change to cancelled")
                    elif new_status == 'no-show':
                        update_type = 'no-show'  # Special case for no-show (sends to both patient and emergency contact)
                        logger.info(f"Setting update_type to 'no-show' for status change to no-show")
                    elif old_status == 'scheduled' and new_status == 'confirmed':
                        update_type = 'confirmation'  # Special case for confirmation
                        logger.info(f"Setting update_type to 'confirmation' for scheduled->confirmed change")
                    elif new_status == 'completed':
                        update_type = None  # Don't send email for completed appointments
                        logger.info(f"Setting update_type to None for completed status")
                    elif old_status != new_status:
                        update_type = 'reschedule'  # Any other status change
                        logger.info(f"Setting update_type to 'reschedule' for general status change")
                else:
                    logger.warning(f"No status change detected, using default update_type: '{update_type}'")
                
                # Prepare appointment details for email with robust type checking
                def safe_get_provider_name():
                    """Safely extract provider name with type checking"""
                    provider_data = appointment_data.get('provider')
                    if isinstance(provider_data, dict):
                        user_data = provider_data.get('user')
                        if isinstance(user_data, dict):
                            return user_data.get('full_name')
                        return provider_data.get('user_name') or provider_data.get('name')
                    elif isinstance(provider_data, str):
                        return provider_data
                    return None
                
                def safe_get_appointment_type():
                    """Safely extract appointment type name with type checking"""
                    appointment_type_data = appointment_data.get('appointment_type')
                    if isinstance(appointment_type_data, dict):
                        return appointment_type_data.get('name')
                    elif isinstance(appointment_type_data, str):
                        return appointment_type_data
                    return None
                
                # Extract appointment data with proper field mapping
                appointment_date = appointment_data.get('appointment_date') or appointment_data.get('date')
                start_time = appointment_data.get('start_time') or appointment_data.get('time')
                provider_name = appointment_data.get('provider_name') or safe_get_provider_name() or 'Doctor'
                appointment_type = appointment_data.get('appointment_type_name') or safe_get_appointment_type() or 'Consultation'
                location = appointment_data.get('hospital_name') or 'MediRemind Partner Clinic'
                
                # Create appointment details with both old and new field names for template compatibility
                appointment_details = {
                    'id': appointment_data['id'],
                    'appointment_date': appointment_date,
                    'start_time': start_time,
                    'provider_name': provider_name,
                    'appointment_type': appointment_type,
                    'location': location,
                    'patient_id': appointment_data.get('patient_id'),
                    'patient_name': appointment_data.get('patient_name') or appointment_data.get('patient', patient_name),
                    'patient_email': appointment_data.get('patient_email') or appointment_data.get('patient_email', patient_email),
                    'update_type': update_type,
                    'changes': appointment_data.get('changes', {}),
                    # Add nested appointment object for template compatibility
                    'appointment': {
                        'id': appointment_data['id'],
                        'appointment_date': appointment_date,
                        'date': appointment_date,  # Alias for template compatibility
                        'start_time': start_time,
                        'time': start_time,  # Alias for template compatibility
                        'provider_name': provider_name,
                        'doctor_name': provider_name,  # Alias for template compatibility
                        'appointment_type': appointment_type,
                        'type': appointment_type,  # Alias for template compatibility
                        'location': location,
                        'patient_id': appointment_data.get('patient_id'),
                        'patient_name': appointment_data.get('patient_name') or appointment_data.get('patient', patient_name),
                    }
                }
                
                logger.info(f"Appointment details prepared: provider_name='{appointment_details.get('provider_name')}', "
                           f"appointment_type='{appointment_details.get('appointment_type')}', "
                           f"appointment_date='{appointment_details.get('appointment_date')}', "
                           f"start_time='{appointment_details.get('start_time')}', "
                           f"location='{appointment_details.get('location')}'")
                
                # Handle completed appointments - send completion confirmation
                if update_type is None:
                    logger.info(f"Sending completion confirmation for appointment {appointment_data.get('id')}")
                    # For completed appointments, we'll treat it as a special confirmation type
                    update_type = 'completion'
                    # Don't return here - let the normal email flow handle it
                
                if settings.DEBUG:
                    # Development mode - use Django's console backend
                    from notifications.email_client import email_client
                    # Convert update type for email client compatibility
                    email_update_type = update_type
                    if update_type == 'reschedule':
                        email_update_type = 'reschedule'
                    elif update_type == 'cancellation':
                        email_update_type = 'cancellation'
                    elif update_type == 'no-show':
                        email_update_type = 'no-show'  # Use no-show template for no-show (consistent with production)
                    elif update_type == 'confirmation':
                        email_update_type = 'created'
                    elif update_type == 'completion':
                        email_update_type = 'created'  # Use confirmation template for completion
                    
                    # Use async Celery tasks for appointment update emails
                    from notifications.tasks import send_appointment_update_async
                    
                    # Send to patient (async)
                    send_appointment_update_async.delay(
                        appointment_data=appointment_details,
                        update_type=email_update_type,
                        recipient_email=patient_email,
                        is_patient=True
                    )
                    
                    # For cancellation and no-show, also send to emergency contact if available
                    if update_type in ['cancellation', 'no-show']:
                        emergency_contact_email = appointment_data.get('emergency_contact_email')
                        if emergency_contact_email:
                            send_appointment_update_async.delay(
                                appointment_data=appointment_details,
                                update_type=email_update_type,
                                recipient_email=emergency_contact_email,
                                is_patient=False  # Send as provider notification to emergency contact
                            )
                            logger.info(f"{update_type} notification queued for emergency contact {emergency_contact_email}")
                    
                    # Return immediate success - emails will be sent asynchronously
                    success = True
                    response_message = f"Appointment {update_type} emails queued for delivery"
                else:
                    # Use unified email client
                    from notifications.email_client import email_client
                    # Convert update type for Resend service compatibility (same as email client)
                    email_update_type = update_type
                    if update_type == 'reschedule':
                        email_update_type = 'rescheduled'
                    elif update_type == 'cancellation':
                        email_update_type = 'cancellation'
                    elif update_type == 'no-show':
                        email_update_type = 'no-show'
                    elif update_type == 'confirmation':
                        email_update_type = 'created'
                    elif update_type == 'completion':
                        email_update_type = 'created'  # Use confirmation template for completion
                    
                    logger.info(f"Converting update_type '{update_type}' to email_update_type '{email_update_type}' for unified email client")
                    
                    success, response_message = email_client.send_appointment_update_email(
                        appointment_data=appointment_details,
                        update_type=email_update_type,
                        recipient_email=patient_email,
                        is_patient=True
                    )
                    
                    # For cancellation and no-show, also send to emergency contact if available
                    if update_type in ['cancellation', 'no-show'] and success:
                        emergency_contact_email = appointment_data.get('emergency_contact_email')
                        if emergency_contact_email:
                            emergency_success, emergency_response = email_client.send_appointment_update_email(
                                appointment_data=appointment_details,
                                update_type=email_update_type,
                                recipient_email=emergency_contact_email,
                                is_patient=False  # Send as provider notification to emergency contact
                            )
                            if emergency_success:
                                logger.info(f"No-show notification sent to emergency contact {emergency_contact_email}")
                            else:
                                logger.warning(f"Failed to send no-show notification to emergency contact: {emergency_response}")
                
                if success:
                    logger.info(f"Appointment update notification sent successfully to {patient_email} (type: {update_type})")
                else:
                    logger.warning(f"Appointment update notification failed to {patient_email}: {response_message}")
                    
            except Exception as e:
                logger.error(f"Failed to send appointment update notification to {patient_email}: {str(e)}")
        
        # Handle appointment cancellations - send cancellation notifications
        elif action == "cancelled":
            try:
                # Extract patient name from appointment data
                patient_name = appointment_data.get('patient', 'Patient')
                
                # Prepare appointment details for email with robust type checking
                def safe_get_provider_name():
                    """Safely extract provider name with type checking"""
                    provider_data = appointment_data.get('provider')
                    if isinstance(provider_data, dict):
                        user_data = provider_data.get('user')
                        if isinstance(user_data, dict):
                            return user_data.get('full_name')
                        return provider_data.get('user_name') or provider_data.get('name')
                    elif isinstance(provider_data, str):
                        return provider_data
                    return None
                
                def safe_get_appointment_type():
                    """Safely extract appointment type name with type checking"""
                    appointment_type_data = appointment_data.get('appointment_type')
                    if isinstance(appointment_type_data, dict):
                        return appointment_type_data.get('name')
                    elif isinstance(appointment_type_data, str):
                        return appointment_type_data
                    return None
                
                appointment_details = {
                    'id': appointment_data['id'],
                    'appointment_date': appointment_data.get('appointment_date') or appointment_data.get('date'),
                    'start_time': appointment_data.get('start_time') or appointment_data.get('time'),
                    'provider_name': appointment_data.get('provider_name') or appointment_data.get('provider') or safe_get_provider_name() or 'Doctor',
                    'appointment_type': appointment_data.get('appointment_type_name') or appointment_data.get('type') or safe_get_appointment_type() or 'Consultation',
                    'location': appointment_data.get('hospital_name') or 'MediRemind Partner Clinic',
                    'patient_id': appointment_data.get('patient_id'),
                    'patient_name': appointment_data.get('patient_name') or appointment_data.get('patient', patient_name),
                    'patient_email': appointment_data.get('patient_email') or appointment_data.get('patient_email', patient_email),
                    'cancellation_reason': appointment_data.get('cancellation_reason') or appointment_data.get('reason', 'Not specified')
                }
                
                # Use async Celery tasks for appointment cancellation emails
                from notifications.tasks import send_appointment_update_async
                
                # Send cancellation notification to patient (async)
                send_appointment_update_async.delay(
                    appointment_data=appointment_details,
                    update_type='cancellation',
                    recipient_email=patient_email,
                    is_patient=True
                )
                
                # Return immediate success - email will be sent asynchronously
                success = True
                response_message = "Appointment cancellation email queued for delivery"
                
                if success:
                    logger.info(f"Appointment cancellation notification sent successfully to {patient_email}")
                else:
                    logger.warning(f"Appointment cancellation notification failed to {patient_email}: {response_message}")
                    
            except Exception as e:
                logger.error(f"Failed to send appointment cancellation notification to {patient_email}: {str(e)}")
            
    except Exception as e:
        logger.error(f"Failed to send appointment notification: {str(e)}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_appointment(request):
    """Create a new appointment - accessible by both staff and patients"""
    try:
        user_role = getattr(request.user, 'role', 'patient')
        user_hospital = None
        
        # Get user's hospital if staff/admin
        if user_role != 'patient':
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=request.user)
                user_hospital = staff_profile.hospital
                if not user_hospital:
                    return Response({
                        "error": "Hospital association not found"
                    }, status=status.HTTP_403_FORBIDDEN)
            except EnhancedStaffProfile.DoesNotExist:
                return Response({
                    "error": "Staff profile not found"
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Use serializer for validation and creation
        serializer = AppointmentCreateSerializer(
            data=request.data, 
            context={'request': request, 'user': request.user, 'hospital': user_hospital}
        )
        
        if serializer.is_valid():
            with transaction.atomic():
                appointment = serializer.save()
                
                # If staff/admin, ensure the appointment is linked to their hospital
                if user_role != 'patient' and user_hospital:
                    # Ensure HospitalPatient relationship exists for the patient
                    from accounts.models import HospitalPatient
                    hospital_patient, created = HospitalPatient.objects.get_or_create(
                        hospital=user_hospital,
                        patient=appointment.patient,
                        defaults={
                            'relationship_type': 'appointment',
                            'status': 'active',
                            'first_visit_date': timezone.now(),
                            'last_visit_date': timezone.now(),
                        }
                    )
                    
                    # Update provider's hospital if not set
                    if not appointment.provider.hospital:
                        appointment.provider.hospital = user_hospital
                        appointment.provider.save()
                
                # Store appointment data for notifications (to be sent after commit)
                appointment_data = {
                    'id': appointment.id,
                    'appointment_date': appointment.appointment_date,
                    'start_time': appointment.start_time,
                    'date': appointment.appointment_date,  # Legacy alias for template compatibility
                    'time': appointment.start_time,  # Legacy alias for template compatibility
                    'appointment_type': appointment.appointment_type.name,
                    'appointment_type_name': appointment.appointment_type.name,  # Alias for template compatibility
                    'type': appointment.appointment_type.name,  # Legacy alias for template compatibility
                    'patient_name': appointment.patient.user.get_full_name(),
                    'patient': appointment.patient.user.get_full_name(),  # Legacy alias for template compatibility
                    'provider_name': appointment.provider.user.get_full_name(),
                    'provider': appointment.provider.user.get_full_name(),  # Legacy alias for template compatibility
                    'doctor_name': appointment.provider.user.get_full_name(),  # Legacy alias for template compatibility
                    'hospital_name': appointment.provider.hospital.name if appointment.provider.hospital else 'MediRemind Partner Clinic',
                    'hospital_type': appointment.provider.hospital.hospital_type if appointment.provider.hospital else 'clinic',
                    'hospital_address': f"{appointment.provider.hospital.address_line_1}, {appointment.provider.hospital.city}" if appointment.provider.hospital else 'Main Location',
                    'hospital_phone': appointment.provider.hospital.phone if appointment.provider.hospital else 'Contact for details',
                    'location': appointment.provider.hospital.name if appointment.provider.hospital else 'MediRemind Partner Clinic',  # Alias for template compatibility
                }
                
                # Schedule reminder (this is database-only, safe inside transaction)
                appointment_reminder_service.schedule_appointment_reminders(appointment)
                
                # Return detailed appointment data
                response_serializer = AppointmentSerializer(appointment)
                response_data = {
                    "message": "Appointment created successfully",
                    "appointment": response_serializer.data
                }
                
                # Send notifications AFTER transaction commits successfully
                def send_notifications_and_reminders():
                    send_appointment_notification(
                        appointment_data, 
                        'created',
                        appointment.patient.user.email,
                        appointment.provider.user.email
                    )
                    # Process immediate reminders for free tier
                    process_immediate_reminders(appointment.id)
                
                transaction.on_commit(send_notifications_and_reminders)
                
                return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response({
            "error": "Validation failed",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Create appointment error: {str(e)}")
        return Response({
            "error": "Failed to create appointment"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_appointment(request, appointment_id):
    """Update an existing appointment"""
    try:
        # Get user's hospital if staff/admin
        user_role = getattr(request.user, 'role', 'patient')
        user_hospital = None
        
        if user_role != 'patient':
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=request.user)
                user_hospital = staff_profile.hospital
            except EnhancedStaffProfile.DoesNotExist:
                return Response({
                    "error": "Staff profile not found"
                }, status=status.HTTP_404_NOT_FOUND)
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        if user_role == 'patient' and appointment.patient.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        elif user_role == 'doctor' and appointment.provider.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        elif user_role not in ['patient', 'doctor']:
            # For admin/staff, check hospital association
            if user_hospital:
                patient_has_relationship = check_patient_hospital_relationship(appointment.patient, user_hospital)
                provider_hospital = getattr(appointment.provider, 'hospital', None)
                
                if not patient_has_relationship and provider_hospital != user_hospital:
                    return Response({"error": "Permission denied - hospital mismatch"}, 
                                   status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"error": "Hospital association not found"}, 
                               status=status.HTTP_403_FORBIDDEN)

        # Use serializer for validation and update
        serializer = AppointmentUpdateSerializer(
            appointment, 
            data=request.data, 
            partial=(request.method == 'PATCH'),
            context={'request': request, 'user': request.user, 'hospital': user_hospital}
        )
        
        if serializer.is_valid():
            with transaction.atomic():
                # Track changes for notifications
                old_data = AppointmentSerializer(appointment).data
                updated_appointment = serializer.save()
                new_data = AppointmentSerializer(updated_appointment).data
                
                # Identify changes
                changes = {}
                for key in ['appointment_date', 'start_time', 'status', 'priority']:
                    if old_data.get(key) != new_data.get(key):
                        changes[key] = {'old': old_data.get(key), 'new': new_data.get(key)}
                
                # Store appointment data for notifications (to be sent after commit)
                if changes:
                    appointment_data = {
                        'id': updated_appointment.id,
                        'date': updated_appointment.appointment_date,
                        'time': updated_appointment.start_time,
                        'type': updated_appointment.appointment_type.name,
                        'patient': updated_appointment.patient.user.get_full_name(),
                        'provider': updated_appointment.provider.user.get_full_name(),
                        'changes': changes
                    }

                response_data = {
                    "message": "Appointment updated successfully",
                    "appointment": AppointmentSerializer(updated_appointment).data,
                    "changes": changes
                }
                
                # Send notifications AFTER transaction commits successfully
                if changes:
                    transaction.on_commit(lambda: send_appointment_notification(
                        appointment_data,
                        'updated',
                        updated_appointment.patient.user.email,
                        updated_appointment.provider.user.email
                    ))
                
                return Response(response_data, status=status.HTTP_200_OK)
        
        return Response({
            "error": "Validation failed",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Update appointment error: {str(e)}")
        return Response({
            "error": "Failed to update appointment"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_csrf_exempt
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get user's hospital if staff/admin
        user_role = getattr(user, 'role', 'patient')
        user_hospital = None
        
        if user_role != 'patient':
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=user.user)
                user_hospital = staff_profile.hospital
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({
                    "error": "Staff profile not found"
                }, status=404)
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        if user_role == 'patient' and appointment.patient.user != user.user:
            return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor' and appointment.provider.user != user.user:
            return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role not in ['patient', 'doctor']:
            # For admin/staff, check hospital association
            if user_hospital:
                patient_has_relationship = check_patient_hospital_relationship(appointment.patient, user_hospital)
                provider_hospital = getattr(appointment.provider, 'hospital', None)
                
                if not patient_has_relationship and provider_hospital != user_hospital:
                    return JsonResponse({"error": "Permission denied - hospital mismatch"}, status=403)
            else:
                return JsonResponse({"error": "Hospital association not found"}, status=403)

        # Check if appointment can be cancelled
        if appointment.status in ['completed', 'cancelled']:
            return JsonResponse({"error": "Cannot cancel completed or already cancelled appointment"}, status=400)

        data = json.loads(request.body) if request.body else {}
        cancellation_reason = data.get('reason', 'No reason provided')

        with transaction.atomic():
            appointment.status = 'cancelled'
            appointment.cancellation_reason = cancellation_reason
            appointment.cancelled_by = user.user
            appointment.cancelled_at = timezone.now()
            appointment.save()

            # Send cancellation notifications
            appointment_data = {
                'id': appointment.id,
                'date': appointment.appointment_date,
                'time': appointment.start_time,
                'type': appointment.appointment_type.name,
                'patient': appointment.patient.user.get_full_name(),
                'provider': appointment.provider.user.get_full_name(),
                'reason': cancellation_reason
            }
            
            send_appointment_notification(
                appointment_data,
                'cancelled',
                appointment.patient.user.email,
                appointment.provider.user.email
            )

        return JsonResponse({
            "message": "Appointment cancelled successfully"
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Cancel appointment error: {str(e)}")
        return JsonResponse({"error": "Failed to cancel appointment"}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_appointment_detail(request, appointment_id):
    """Get detailed information about a specific appointment"""
    try:
        # Get user's hospital if staff/admin
        user_role = getattr(request.user, 'role', 'patient')
        user_hospital = None
        
        if user_role != 'patient':
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=request.user)
                user_hospital = staff_profile.hospital
            except EnhancedStaffProfile.DoesNotExist:
                return Response({
                    "error": "Staff profile not found"
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the appointment
        appointment = get_object_or_404(
            Appointment.objects.select_related(
                'patient__user', 'provider__user', 'appointment_type', 'room'
            ).prefetch_related('equipment_needed'),
            id=appointment_id
        )
        
        # Check permissions
        if user_role == 'patient' and appointment.patient.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        elif user_role == 'doctor' and appointment.provider.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        elif user_role not in ['patient', 'doctor']:
            # For admin/staff, check hospital association
            if user_hospital:
                patient_has_relationship = check_patient_hospital_relationship(appointment.patient, user_hospital)
                provider_hospital = getattr(appointment.provider, 'hospital', None)
                
                if not patient_has_relationship and provider_hospital != user_hospital:
                    return Response({"error": "Permission denied - hospital mismatch"}, 
                                   status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"error": "Hospital association not found"}, 
                               status=status.HTTP_403_FORBIDDEN)

        # Serialize appointment data
        serializer = AppointmentSerializer(appointment)

        return Response({
            "message": "Appointment details retrieved successfully",
            "appointment": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get appointment detail error: {str(e)}")
        return Response({
            "error": "Failed to retrieve appointment details"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_appointments(request):
    """List appointments with filtering and pagination"""
    try:
        user_role = getattr(request.user, 'role', 'patient')
        
        # Get user's hospital
        user_hospital = None
        if user_role != 'patient':
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=request.user)
                user_hospital = staff_profile.hospital
            except EnhancedStaffProfile.DoesNotExist:
                return Response({
                    "error": "Staff profile not found"
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Base queryset based on user role
        if user_role == 'patient':
            queryset = Appointment.objects.filter(patient__user=request.user)
        elif user_role == 'doctor':
            queryset = Appointment.objects.filter(provider__user=request.user)
        else:  # admin/staff
            if user_hospital:
                # Filter appointments by hospital through the many-to-many relationship
                # Get patients associated with this hospital through HospitalPatient relationship
                from accounts.models import HospitalPatient
                hospital_patient_ids = HospitalPatient.objects.filter(
                    hospital=user_hospital,
                    status='active'
                ).values_list('patient_id', flat=True)
                
                # Filter appointments for patients in this hospital or providers in this hospital
                queryset = Appointment.objects.filter(
                    models.Q(patient_id__in=hospital_patient_ids) | 
                    models.Q(provider__hospital=user_hospital)
                )
            else:
                return Response({
                    "error": "Hospital association not found"
                }, status=status.HTTP_403_FORBIDDEN)

        # Use search form for validation
        search_form = AppointmentSearchForm(request.GET)
        if search_form.is_valid():
            # Apply filters
            if search_form.cleaned_data.get('status'):
                queryset = queryset.filter(status=search_form.cleaned_data['status'])
            
            if search_form.cleaned_data.get('date_from'):
                queryset = queryset.filter(appointment_date__gte=search_form.cleaned_data['date_from'])
            
            if search_form.cleaned_data.get('date_to'):
                queryset = queryset.filter(appointment_date__lte=search_form.cleaned_data['date_to'])
            
            if search_form.cleaned_data.get('priority'):
                queryset = queryset.filter(priority=search_form.cleaned_data['priority'])
            
            if search_form.cleaned_data.get('patient'):
                queryset = queryset.filter(patient=search_form.cleaned_data['patient'])
            
            if search_form.cleaned_data.get('provider'):
                queryset = queryset.filter(provider=search_form.cleaned_data['provider'])
            
            if search_form.cleaned_data.get('appointment_type'):
                queryset = queryset.filter(appointment_type=search_form.cleaned_data['appointment_type'])

        # Ordering
        queryset = queryset.select_related(
            'patient__user', 'provider__user', 'appointment_type', 'room'
        ).order_by('appointment_date', 'start_time')

        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)  # Max 100 per page
        paginator = Paginator(queryset, per_page)
        appointments_page = paginator.get_page(page)

        # Serialize data
        serializer = AppointmentListSerializer(appointments_page, many=True)

        return Response({
            "message": "Appointments retrieved successfully",
            "appointments": serializer.data,
            "pagination": {
                "current_page": page,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "per_page": per_page,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous()
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"List appointments error: {str(e)}")
        return Response({
            "error": "Failed to retrieve appointments"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_appointment_history(request):
    """Get appointment history for the logged-in patient"""
    try:
        user_role = getattr(request.user, 'role', 'patient')
        
        # This endpoint is specifically for patients
        if user_role != 'patient':
            return Response({
                "error": "This endpoint is only accessible to patients"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get patient profile
        try:
            patient = EnhancedPatient.objects.get(user=request.user)
        except EnhancedPatient.DoesNotExist:
            return Response({
                "error": "Patient profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Base queryset for patient's appointments
        queryset = Appointment.objects.filter(patient=patient)
        
        # Apply filters from query parameters
        status_filter = request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_from = request.GET.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__gte=date_from)
            except ValueError:
                return Response({
                    "error": "Invalid date_from format. Use YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        date_to = request.GET.get('date_to')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__lte=date_to)
            except ValueError:
                return Response({
                    "error": "Invalid date_to format. Use YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ordering - most recent first
        queryset = queryset.select_related(
            'provider__user', 'appointment_type', 'room', 'hospital'
        ).order_by('-appointment_date', '-start_time')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)  # Max 100 per page
        paginator = Paginator(queryset, per_page)
        appointments_page = paginator.get_page(page)
        
        # Serialize data
        serializer = AppointmentListSerializer(appointments_page, many=True)
        
        return Response({
            "message": "Patient appointment history retrieved successfully",
            "appointments": serializer.data,
            "pagination": {
                "current_page": page,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "per_page": per_page,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Patient appointment history error: {str(e)}")
        return Response({
            "error": "Failed to retrieve appointment history"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_appointments(request):
    """Get appointments for the logged-in staff member's hospital"""
    try:
        user_role = getattr(request.user, 'role', 'patient')
        
        # This endpoint is specifically for hospital staff
        if user_role == 'patient':
            return Response({
                "error": "This endpoint is only accessible to hospital staff"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get user's hospital
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user=request.user)
            user_hospital = staff_profile.hospital
        except EnhancedStaffProfile.DoesNotExist:
            return Response({
                "error": "Staff profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Filter appointments by hospital through the many-to-many relationship
        from accounts.models import HospitalPatient
        hospital_patient_ids = HospitalPatient.objects.filter(
            hospital=user_hospital,
            status='active'
        ).values_list('patient_id', flat=True)
        
        # Filter appointments for patients in this hospital or providers in this hospital
        queryset = Appointment.objects.filter(
            models.Q(patient_id__in=hospital_patient_ids) | 
            models.Q(provider__hospital=user_hospital)
        )
        
        # Apply filters from query parameters
        status_filter = request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_from = request.GET.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__gte=date_from)
            except ValueError:
                return Response({
                    "error": "Invalid date_from format. Use YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        date_to = request.GET.get('date_to')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__lte=date_to)
            except ValueError:
                return Response({
                    "error": "Invalid date_to format. Use YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        priority_filter = request.GET.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        provider_id = request.GET.get('provider_id')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        appointment_type_id = request.GET.get('appointment_type_id')
        if appointment_type_id:
            queryset = queryset.filter(appointment_type_id=appointment_type_id)
        
        # Ordering
        queryset = queryset.select_related(
            'patient__user', 'provider__user', 'appointment_type', 'room'
        ).order_by('appointment_date', 'start_time')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)  # Max 100 per page
        paginator = Paginator(queryset, per_page)
        appointments_page = paginator.get_page(page)
        
        # Serialize data
        serializer = AppointmentListSerializer(appointments_page, many=True)
        
        return Response({
            "message": "Hospital appointments retrieved successfully",
            "hospital": user_hospital.name,
            "appointments": serializer.data,
            "pagination": {
                "current_page": page,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "per_page": per_page,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Hospital appointments error: {str(e)}")
        return Response({
            "error": "Failed to retrieve hospital appointments"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_availability(request):
    """Check provider availability for a specific date and time"""
    try:
        # Use form for validation
        form = AvailabilityCheckForm(request.data)
        if not form.is_valid():
            return Response({
                "error": "Validation failed",
                "details": form.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        provider_id = form.cleaned_data['provider_id']
        date = form.cleaned_data['date']
        time = form.cleaned_data['time']
        duration = form.cleaned_data.get('duration', 30)

        # Validate provider
        try:
            provider = EnhancedStaffProfile.objects.get(id=provider_id, role='doctor')
        except EnhancedStaffProfile.DoesNotExist:
            return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)

        # Parse date and time
        appointment_datetime = datetime.combine(date, time)
        end_datetime = appointment_datetime + timedelta(minutes=duration)

        # Check for conflicts
        conflicts = Appointment.objects.filter(
            provider=provider,
            appointment_date=date,
            status__in=['pending', 'confirmed']
        ).exclude(
            models.Q(start_time__gte=end_datetime.time()) | 
            models.Q(start_time__lt=time)
        )

        is_available = not conflicts.exists()

        return Response({
            "available": is_available,
            "conflicts": list(conflicts.values('id', 'start_time', 'default_duration')) if conflicts.exists() else [],
            "provider": provider.user.get_full_name(),
            "date": date,
            "time": time,
            "duration": duration
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Check availability error: {str(e)}")
        return Response({
            "error": "Failed to check availability"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_appointment_statistics(request):
    """Get appointment statistics for dashboard"""
    try:
        user_role = getattr(request.user, 'role', 'patient')
        today = timezone.now().date()
        
        if user_role == 'patient':
            # Patient statistics
            try:
                patient = EnhancedPatient.objects.get(user=request.user)
            except EnhancedPatient.DoesNotExist:
                return Response({"error": "Patient profile not found"}, status=status.HTTP_404_NOT_FOUND)
                
            stats = {
                'total_appointments': Appointment.objects.filter(patient=patient).count(),
                'upcoming_appointments': Appointment.objects.filter(
                    patient=patient,
                    appointment_date__gte=today,
                    status__in=['pending', 'confirmed']
                ).count(),
                'completed_appointments': Appointment.objects.filter(
                    patient=patient,
                    status='completed'
                ).count(),
                'cancelled_appointments': Appointment.objects.filter(
                    patient=patient,
                    status='cancelled'
                ).count(),
                'this_month_appointments': Appointment.objects.filter(
                    patient=patient,
                    appointment_date__year=today.year,
                    appointment_date__month=today.month
                ).count()
            }
        else:
            # Doctor/Admin statistics
            if user_role == 'doctor':
                try:
                    provider = EnhancedStaffProfile.objects.get(user=request.user, role='doctor')
                    base_filter = {'provider': provider}
                except EnhancedStaffProfile.DoesNotExist:
                    return Response({"error": "Provider profile not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                base_filter = {}
            
            stats = {
                'total_appointments': Appointment.objects.filter(**base_filter).count(),
                'today_appointments': Appointment.objects.filter(
                    appointment_date=today,
                    **base_filter
                ).count(),
                'upcoming_appointments': Appointment.objects.filter(
                    appointment_date__gte=today,
                    status__in=['pending', 'confirmed'],
                    **base_filter
                ).count(),
                'completed_appointments': Appointment.objects.filter(
                    status='completed',
                    **base_filter
                ).count(),
                'cancelled_appointments': Appointment.objects.filter(
                    status='cancelled',
                    **base_filter
                ).count(),
                'pending_appointments': Appointment.objects.filter(
                    status='pending',
                    **base_filter
                ).count()
            }

        return Response({
            "message": "Statistics retrieved successfully",
            "statistics": stats
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get statistics error: {str(e)}")
        return Response({
            "error": "Failed to retrieve statistics"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_time_slots(request):
    """Get available time slots for a provider on a specific date with enhanced conflict detection"""
    try:
        provider_id = request.GET.get('provider_id')
        date_str = request.GET.get('date')
        duration = int(request.GET.get('duration', 30))
        exclude_appointment_id = request.GET.get('exclude_appointment_id')  # For editing appointments

        if not all([provider_id, date_str]):
            return Response({"error": "Provider ID and date are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate provider
        try:
            provider = EnhancedStaffProfile.objects.get(id=provider_id, role='doctor')
        except EnhancedStaffProfile.DoesNotExist:
            return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)

        # Parse date
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

        # Get existing appointments for the provider on this date
        existing_appointments_query = Appointment.objects.filter(
            provider=provider,
            appointment_date=appointment_date,
            status__in=['scheduled', 'confirmed', 'pending', 'checked_in', 'in_progress']
        )
        
        # Exclude current appointment if editing
        if exclude_appointment_id:
            existing_appointments_query = existing_appointments_query.exclude(id=exclude_appointment_id)
        
        existing_appointments = existing_appointments_query.values_list('start_time', 'end_time', 'duration')

        # Generate time slots (8 AM to 6 PM, 15-minute intervals for better granularity)
        start_time = time(8, 0)
        end_time = time(18, 0)
        slot_interval = timedelta(minutes=15)  # Check every 15 minutes for better availability
        
        available_slots = []
        unavailable_slots = []
        current_time = datetime.combine(appointment_date, start_time)
        end_datetime = datetime.combine(appointment_date, end_time)

        while current_time + timedelta(minutes=duration) <= end_datetime:
            slot_time = current_time.time()
            slot_end_time = (current_time + timedelta(minutes=duration)).time()
            
            # Check if this slot conflicts with existing appointments
            is_available = True
            conflict_reason = None
            
            for appt_start_time, appt_end_time, appt_duration in existing_appointments:
                # Use end_time if available, otherwise calculate from start_time + duration
                if appt_end_time:
                    calculated_end_time = appt_end_time
                else:
                    calculated_end_time = (datetime.combine(appointment_date, appt_start_time) + 
                                         timedelta(minutes=appt_duration)).time()
                
                # Check for overlap: appointments overlap if one starts before the other ends
                if not (slot_end_time <= appt_start_time or slot_time >= calculated_end_time):
                    is_available = False
                    conflict_reason = f"Conflicts with appointment from {appt_start_time.strftime('%H:%M')} to {calculated_end_time.strftime('%H:%M')}"
                    break
            
            # Check if slot is in the past (for today's appointments)
            if appointment_date == date.today():
                now = datetime.now().time()
                if slot_time <= now:
                    is_available = False
                    conflict_reason = "Time has passed"
            
            slot_data = {
                'time': slot_time.strftime('%H:%M'),
                'end_time': slot_end_time.strftime('%H:%M'),
                'duration': duration,
                'available': is_available
            }
            
            if is_available:
                available_slots.append(slot_data)
            else:
                slot_data['reason'] = conflict_reason
                unavailable_slots.append(slot_data)
            
            current_time += slot_interval

        # Group slots by time periods for better UX
        time_periods = {
            'morning': {'label': 'Morning (8:00 AM - 12:00 PM)', 'slots': []},
            'afternoon': {'label': 'Afternoon (12:00 PM - 5:00 PM)', 'slots': []},
            'evening': {'label': 'Evening (5:00 PM - 6:00 PM)', 'slots': []}
        }
        
        for slot in available_slots:
            slot_hour = int(slot['time'].split(':')[0])
            if slot_hour < 12:
                time_periods['morning']['slots'].append(slot)
            elif slot_hour < 17:
                time_periods['afternoon']['slots'].append(slot)
            else:
                time_periods['evening']['slots'].append(slot)

        return Response({
            "message": "Available time slots retrieved successfully",
            "date": date_str,
            "provider": provider.user.get_full_name(),
            "provider_id": provider_id,
            "requested_duration": duration,
            "total_available_slots": len(available_slots),
            "available_slots": available_slots,
            "unavailable_slots": unavailable_slots[:10],  # Limit for performance
            "time_periods": time_periods,
            "working_hours": {
                "start": "08:00",
                "end": "18:00"
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get available time slots error: {str(e)}")
        return Response({"error": "Failed to retrieve available time slots"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_appointment_types(request):
    """List all active appointment types"""
    try:
        appointment_types = AppointmentType.objects.filter(is_active=True).order_by('name')
        serializer = AppointmentTypeSerializer(appointment_types, many=True)
        
        return Response({
            "message": "Appointment types retrieved successfully",
            "appointment_types": serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"List appointment types error: {str(e)}")
        return Response({"error": "Failed to retrieve appointment types"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_manual_sms_reminder(request, appointment_id):
    """Send a manual SMS reminder for an appointment - accessible by staff only"""
    try:
        # Check if user is staff/admin
        user_role = getattr(request.user, 'role', 'patient')
        if user_role == 'patient':
            return Response({
                "error": "Permission denied. Only staff members can send manual reminders"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get user's hospital if staff/admin
        user_hospital = None
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user=request.user)
            user_hospital = staff_profile.hospital
            if not user_hospital:
                return Response({
                    "error": "Hospital association not found"
                }, status=status.HTTP_403_FORBIDDEN)
        except EnhancedStaffProfile.DoesNotExist:
            return Response({
                "error": "Staff profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the appointment
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check hospital permissions
        patient_has_relationship = check_patient_hospital_relationship(appointment.patient, user_hospital)
        provider_hospital = getattr(appointment.provider, 'hospital', None)
        
        if not patient_has_relationship and provider_hospital != user_hospital:
            return Response({
                "error": "Permission denied - hospital mismatch"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get patient's phone number
        patient_phone = getattr(appointment.patient, 'phone', None)
        if not patient_phone:
            return Response({
                "error": "Patient phone number not found"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and format phone number for Kenyan SMS service
        try:
            from notifications.phone_utils import format_kenyan_phone_number
            formatted_phone = format_kenyan_phone_number(patient_phone)
        except ValueError as e:
            return Response({
                "error": f"Invalid phone number format: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Compose SMS message
        appointment_date = appointment.appointment_date.strftime('%Y-%m-%d')
        start_time = appointment.start_time.strftime('%H:%M')
        
        # Get location - hospital name is required, room name is optional
        location_name = appointment.hospital.name if appointment.hospital else 'Main Hospital'
        # Only add room info if available
        if appointment.room:
            location_name = f"{appointment.hospital.name} - {appointment.room.name}"
        
        sms_message = (
            f"Reminder: You have an appointment with {appointment.provider.user.get_full_name()} "
            f"on {appointment_date} at {start_time}. "
            f"Location: {location_name}. "
            f"Please arrive 15 minutes early. Reply STOP to unsubscribe."
        )
        
        # Send SMS using the existing SMS service
        success, response_message = textsms_client.send_sms(
            recipient=formatted_phone,
            message=sms_message
        )
        
        if success:
            # Log the manual reminder
            logger.info(f"Manual SMS reminder sent for appointment {appointment_id} to {formatted_phone}")
            
            return Response({
                "message": "SMS reminder sent successfully",
                "phone_number": formatted_phone,
                "appointment_id": appointment_id,
                "response": response_message
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Failed to send manual SMS reminder for appointment {appointment_id}: {response_message}")
            
            return Response({
                "error": "Failed to send SMS reminder",
                "details": response_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Send manual SMS reminder error for appointment {appointment_id}: {str(e)}")
        return Response({
            "error": "Failed to send SMS reminder"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
