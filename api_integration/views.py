from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import HospitalIntegration, DataProcessingConsent, APILog, SecurityIncident
from .serializers import (
    HospitalIntegrationSerializer, DataProcessingConsentSerializer, 
    APILogSerializer, SecurityIncidentSerializer,
    HospitalIntegrationSetupSerializer, PatientDataSerializer,
    AppointmentDataSerializer, ReminderDataSerializer
)
from .authentication import HospitalAPIAuthentication, HospitalAPIPermission
from .security import RequestSignature, RateLimiter, DataEncryption
from .compliance import ComplianceReporter

logger = logging.getLogger(__name__)

class HospitalIntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing hospital integrations"""
    queryset = HospitalIntegration.objects.all()
    serializer_class = HospitalIntegrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter integrations based on user permissions"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return HospitalIntegration.objects.all()
        return HospitalIntegration.objects.filter(hospital__admin=user)
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a hospital integration"""
        integration = self.get_object()
        integration.status = 'suspended'
        integration.suspended_at = timezone.now()
        integration.suspended_reason = request.data.get('reason', 'Administrative suspension')
        integration.save()
        
        # Log the suspension
        APILog.objects.create(
            integration=integration,
            method='POST',
            endpoint=f'/api/integration/hospitals/{pk}/suspend/',
            status_code=200,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message='Integration suspended',
            data_categories=['integration_data']
        )
        
        return Response({'status': 'suspended'})
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a suspended integration"""
        integration = self.get_object()
        if integration.status != 'suspended':
            return Response({'error': 'Integration is not suspended'}, status=400)
        
        integration.status = 'active'
        integration.suspended_at = None
        integration.suspended_reason = None
        integration.save()
        
        # Log the reactivation
        APILog.objects.create(
            integration=integration,
            method='POST',
            endpoint=f'/api/integration/hospitals/{pk}/reactivate/',
            status_code=200,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message='Integration reactivated',
            data_categories=['integration_data']
        )
        
        return Response({'status': 'active'})
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class DataProcessingConsentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing data processing consents"""
    queryset = DataProcessingConsent.objects.all()
    serializer_class = DataProcessingConsentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter consents based on user permissions"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return DataProcessingConsent.objects.all()
        return DataProcessingConsent.objects.filter(integration__hospital__admin=user)

class APILogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing API logs (read-only)"""
    queryset = APILog.objects.all()
    serializer_class = APILogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter logs based on user permissions"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return APILog.objects.all()
        return APILog.objects.filter(integration__hospital__admin=user)

class SecurityIncidentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security incidents"""
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter incidents based on user permissions"""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return SecurityIncident.objects.all()
        return SecurityIncident.objects.filter(integration__hospital__admin=user)

class HospitalIntegrationSetupView(APIView):
    """API endpoint for hospital integration setup"""
    
    def post(self, request):
        """Create new hospital integration"""
        serializer = HospitalIntegrationSetupSerializer(data=request.data)
        if serializer.is_valid():
            integration = serializer.save()
            return Response({
                'status': 'success',
                'integration_id': str(integration.id),
                'api_key': integration.api_key,  # Only shown once
                'message': 'Integration created successfully. Please store the API key securely.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyAPIKeyView(APIView):
    """API endpoint for verifying API keys"""
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """Verify API key and return integration details"""
        api_key = request.data.get('api_key')
        if not api_key:
            return Response({'error': 'API key required'}, status=400)
        
        integration = HospitalIntegration.objects.filter(api_key=api_key).first()
        
        if integration:
            return Response({
                'status': 'valid',
                'integration_id': str(integration.id),
                'hospital_name': integration.hospital.name,
                'integration_status': integration.status,
                'encryption_enabled': integration.encryption_enabled
            })
        else:
            return Response({'error': 'Invalid API key'}, status=404)

class RotateAPIKeyView(APIView):
    """API endpoint for rotating API keys"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Rotate API key for integration"""
        integration_id = request.data.get('integration_id')
        if not integration_id:
            return Response({'error': 'Integration ID required'}, status=400)
        
        try:
            integration = HospitalIntegration.objects.get(id=integration_id)
            
            # Check permissions
            if not (request.user.is_staff or request.user.is_superuser or 
                   integration.hospital.admin == request.user):
                return Response({'error': 'Permission denied'}, status=403)
            
            # Generate new API key
            from .security import generate_api_key
            new_api_key = generate_api_key()
            
            # Store old key for audit
            old_api_key = integration.api_key
            
            # Update integration
            integration.api_key = new_api_key
            integration.last_key_rotation = timezone.now()
            integration.save()
            
            # Log the key rotation
            APILog.objects.create(
                integration=integration,
                method='POST',
                endpoint='/api/integration/auth/rotate-key/',
                status_code=200,
                ip_address=self.get_client_ip(request),
                auth_status='success',
                message='API key rotated',
                data_categories=['integration_data']
            )
            
            return Response({
                'status': 'success',
                'new_api_key': new_api_key,
                'message': 'API key rotated successfully. Update your systems immediately.'
            })
            
        except HospitalIntegration.DoesNotExist:
            return Response({'error': 'Integration not found'}, status=404)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PatientDataView(APIView):
    """API endpoint for patient data operations"""
    authentication_classes = [HospitalAPIAuthentication]
    permission_classes = [HospitalAPIPermission]
    
    def get(self, request):
        """Get patient data"""
        integration = request.user  # Set by authentication
        
        # Validate consent
        from .models import DataProcessingConsent
        consent = DataProcessingConsent.objects.filter(
            integration=integration,
            consent_type='patient_data',
            status='active'
        ).first()
        
        if not consent:
            return Response({'error': 'No valid consent for patient data processing'}, status=403)
        
        # Get patients for this hospital
        from appointments.models import Patient
        patients = Patient.objects.filter(hospital=integration.hospital, is_archived=False)
        
        # Apply filters if provided
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            patients = patients.filter(patient_id=patient_id)
        
        # Serialize data
        serializer = PatientDataSerializer(patients, many=True)
        
        # Log the access
        APILog.objects.create(
            integration=integration,
            method='GET',
            endpoint='/api/integration/patients/',
            status_code=200,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message='Patient data accessed',
            data_categories=['patient_data']
        )
        
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'patients': serializer.data
        })
    
    def post(self, request):
        """Create or update patient data"""
        integration = request.user  # Set by authentication
        
        # Validate consent
        from .models import DataProcessingConsent
        consent = DataProcessingConsent.objects.filter(
            integration=integration,
            consent_type='patient_data',
            status='active'
        ).first()
        
        if not consent:
            return Response({'error': 'No valid consent for patient data processing'}, status=403)
        
        # Validate data
        serializer = PatientDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        # Process data
        patient_data = serializer.validated_data
        
        # Encrypt sensitive data if enabled
        if integration.encryption_enabled:
            encryption = DataEncryption()
            patient_data['phone'] = encryption.encrypt_data(patient_data['phone'])
            if 'email' in patient_data:
                patient_data['email'] = encryption.encrypt_data(patient_data['email'])
        
        # Create or update patient
        from appointments.models import Patient
        patient, created = Patient.objects.update_or_create(
            hospital=integration.hospital,
            patient_id=patient_data['patient_id'],
            defaults=patient_data
        )
        
        # Log the operation
        APILog.objects.create(
            integration=integration,
            method='POST',
            endpoint='/api/integration/patients/',
            status_code=201 if created else 200,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message=f'Patient data {"created" if created else "updated"}',
            data_categories=['patient_data']
        )
        
        return Response({
            'status': 'success',
            'action': 'created' if created else 'updated',
            'patient_id': patient.patient_id
        }, status=201 if created else 200)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AppointmentDataView(APIView):
    """API endpoint for appointment data operations"""
    authentication_classes = [HospitalAPIAuthentication]
    permission_classes = [HospitalAPIPermission]
    
    def get(self, request):
        """Get appointment data"""
        integration = request.user  # Set by authentication
        
        # Validate consent
        from .models import DataProcessingConsent
        consent = DataProcessingConsent.objects.filter(
            integration=integration,
            consent_type='appointment_data',
            status='active'
        ).first()
        
        if not consent:
            return Response({'error': 'No valid consent for appointment data processing'}, status=403)
        
        # Get appointments for this hospital
        from appointments.models import Appointment
        appointments = Appointment.objects.filter(hospital=integration.hospital)
        
        # Apply date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            appointments = appointments.filter(appointment_date__gte=start_date)
        if end_date:
            appointments = appointments.filter(appointment_date__lte=end_date)
        
        # Serialize data
        serializer = AppointmentDataSerializer(appointments, many=True)
        
        # Log the access
        APILog.objects.create(
            integration=integration,
            method='GET',
            endpoint='/api/integration/appointments/',
            status_code=200,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message='Appointment data accessed',
            data_categories=['appointment_data']
        )
        
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'appointments': serializer.data
        })
    
    def post(self, request):
        """Create appointment data"""
        integration = request.user  # Set by authentication
        
        # Validate consent
        from .models import DataProcessingConsent
        consent = DataProcessingConsent.objects.filter(
            integration=integration,
            consent_type='appointment_data',
            status='active'
        ).first()
        
        if not consent:
            return Response({'error': 'No valid consent for appointment data processing'}, status=403)
        
        # Validate data
        serializer = AppointmentDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        # Process data
        appointment_data = serializer.validated_data
        appointment_data['hospital'] = integration.hospital
        
        # Create appointment
        from appointments.models import Appointment
        appointment = Appointment.objects.create(**appointment_data)
        
        # Log the creation
        APILog.objects.create(
            integration=integration,
            method='POST',
            endpoint='/api/integration/appointments/',
            status_code=201,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message='Appointment created',
            data_categories=['appointment_data']
        )
        
        return Response({
            'status': 'success',
            'appointment_id': appointment.id,
            'reminder_scheduled': appointment.send_reminder
        }, status=201)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ReminderDataView(APIView):
    """API endpoint for reminder data operations"""
    authentication_classes = [HospitalAPIAuthentication]
    permission_classes = [HospitalAPIPermission]
    
    def get(self, request):
        """Get reminder data"""
        integration = request.user  # Set by authentication
        
        # Validate consent
        from .models import DataProcessingConsent
        consent = DataProcessingConsent.objects.filter(
            integration=integration,
            consent_type='reminder_data',
            status='active'
        ).first()
        
        if not consent:
            return Response({'error': 'No valid consent for reminder data processing'}, status=403)
        
        # Get reminders for this hospital
        from notifications.models import Notification
        reminders = Notification.objects.filter(hospital=integration.hospital)
        
        # Apply status filters
        status_filter = request.query_params.get('status')
        if status_filter:
            reminders = reminders.filter(status=status_filter)
        
        # Serialize data
        serializer = ReminderDataSerializer(reminders, many=True)
        
        # Log the access
        APILog.objects.create(
            integration=integration,
            method='GET',
            endpoint='/api/integration/reminders/',
            status_code=200,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message='Reminder data accessed',
            data_categories=['reminder_data']
        )
        
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'reminders': serializer.data
        })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class RequestConsentView(APIView):
    """API endpoint for requesting data processing consent"""
    authentication_classes = [HospitalAPIAuthentication]
    permission_classes = [HospitalAPIPermission]
    
    def post(self, request):
        """Request consent for data processing"""
        integration = request.user  # Set by authentication
        
        consent_type = request.data.get('consent_type')
        if not consent_type:
            return Response({'error': 'Consent type required'}, status=400)
        
        # Check if consent already exists
        from .models import DataProcessingConsent
        existing_consent = DataProcessingConsent.objects.filter(
            integration=integration,
            consent_type=consent_type,
            status='active'
        ).first()
        
        if existing_consent:
            return Response({
                'error': 'Active consent already exists',
                'consent_id': str(existing_consent.id),
                'expires_at': existing_consent.expires_at
            }, status=400)
        
        # Create new consent request
        consent = DataProcessingConsent.objects.create(
            integration=integration,
            consent_type=consent_type,
            status='pending',
            requested_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=365)  # 1 year default
        )
        
        # Log the request
        APILog.objects.create(
            integration=integration,
            method='POST',
            endpoint='/api/integration/consents/request/',
            status_code=201,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message=f'Consent requested for {consent_type}',
            data_categories=['consent_data']
        )
        
        return Response({
            'status': 'success',
            'consent_id': str(consent.id),
            'consent_type': consent_type,
            'message': 'Consent request created. Awaiting approval.'
        }, status=201)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class VerifyConsentView(APIView):
    """API endpoint for verifying consent status"""
    authentication_classes = [HospitalAPIAuthentication]
    permission_classes = [HospitalAPIPermission]
    
    def get(self, request):
        """Verify consent status"""
        integration = request.user  # Set by authentication
        consent_type = request.query_params.get('consent_type')
        
        if not consent_type:
            return Response({'error': 'Consent type required'}, status=400)
        
        from .models import DataProcessingConsent
        consent = DataProcessingConsent.objects.filter(
            integration=integration,
            consent_type=consent_type
        ).first()
        
        if not consent:
            return Response({'error': 'No consent found'}, status=404)
        
        return Response({
            'consent_id': str(consent.id),
            'status': consent.status,
            'expires_at': consent.expires_at,
            'is_valid': consent.status == 'active' and consent.expires_at > timezone.now()
        })

class WithdrawConsentView(APIView):
    """API endpoint for withdrawing consent"""
    authentication_classes = [HospitalAPIAuthentication]
    permission_classes = [HospitalAPIPermission]
    
    def post(self, request):
        """Withdraw consent for data processing"""
        integration = request.user  # Set by authentication
        consent_type = request.data.get('consent_type')
        
        if not consent_type:
            return Response({'error': 'Consent type required'}, status=400)
        
        from .models import DataProcessingConsent
        consent = DataProcessingConsent.objects.filter(
            integration=integration,
            consent_type=consent_type,
            status='active'
        ).first()
        
        if not consent:
            return Response({'error': 'No active consent found'}, status=404)
        
        # Withdraw consent
        consent.status = 'withdrawn'
        consent.withdrawn_at = timezone.now()
        consent.save()
        
        # Log the withdrawal
        APILog.objects.create(
            integration=integration,
            method='POST',
            endpoint='/api/integration/consents/withdraw/',
            status_code=200,
            ip_address=self.get_client_ip(request),
            auth_status='success',
            message=f'Consent withdrawn for {consent_type}',
            data_categories=['consent_data']
        )
        
        return Response({
            'status': 'success',
            'message': 'Consent withdrawn successfully'
        })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ComplianceStatusView(APIView):
    """API endpoint for checking compliance status"""
    authentication_classes = [HospitalAPIAuthentication]
    permission_classes = [HospitalAPIPermission]
    
    def get(self, request):
        """Get compliance status for integration"""
        integration = request.user  # Set by authentication
        
        # Check consent status
        from .models import DataProcessingConsent
        consents = DataProcessingConsent.objects.filter(
            integration=integration
        )
        
        # Check recent security incidents
        recent_incidents = SecurityIncident.objects.filter(
            integration=integration,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Check API usage
        recent_api_calls = APILog.objects.filter(
            integration=integration,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        compliance_status = {
            'integration_status': integration.status,
            'data_retention_days': integration.data_retention_days,
            'encryption_enabled': integration.encryption_enabled,
            'consents': {
                'total': consents.count(),
                'active': consents.filter(status='active').count(),
                'expired': consents.filter(status='expired').count(),
                'withdrawn': consents.filter(status='withdrawn').count()
            },
            'security_incidents': {
                'recent_30_days': recent_incidents.count(),
                'high_severity': recent_incidents.filter(severity='high').count(),
                'medium_severity': recent_incidents.filter(severity='medium').count(),
                'low_severity': recent_incidents.filter(severity='low').count()
            },
            'api_usage': {
                'recent_30_days': recent_api_calls.count(),
                'successful_calls': recent_api_calls.filter(status_code__lt=400).count(),
                'failed_calls': recent_api_calls.filter(status_code__gte=400).count()
            },
            'compliance_score': self.calculate_compliance_score(integration, consents, recent_incidents)
        }
        
        return Response(compliance_status)
    
    def calculate_compliance_score(self, integration, consents, incidents):
        """Calculate compliance score based on various factors"""
        score = 100
        
        # Deduct points for expired consents
        expired_consents = consents.filter(status='expired').count()
        score -= expired_consents * 10
        
        # Deduct points for security incidents
        high_severity = incidents.filter(severity='high').count()
        medium_severity = incidents.filter(severity='medium').count()
        low_severity = incidents.filter(severity='low').count()
        
        score -= high_severity * 20
        score -= medium_severity * 10
        score -= low_severity * 5
        
        # Deduct points if encryption is disabled
        if not integration.encryption_enabled:
            score -= 15
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))

class ComplianceReportView(APIView):
    """API endpoint for generating compliance reports"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Generate compliance report"""
        # Check permissions
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Permission denied'}, status=403)
        
        # Generate report
        report = ComplianceReporter.generate_monthly_compliance_report()
        if report:
            return Response(report)
        else:
            return Response({'error': 'Failed to generate report'}, status=500)