# API Integration Test Suite

import json
import hmac
import hashlib
import time
from django.test import TransactionTestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Hospital
from .models import HospitalIntegration, DataProcessingConsent, APILog, SecurityIncident
from .security import APIKeyGenerator, DataEncryption, RequestSignature

class HospitalIntegrationTestCase(TransactionTestCase):
    """Test cases for hospital integration API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test hospital
        self.hospital = Hospital.objects.create(
            name="Test Hospital",
            hospital_type="private",
            email="admin@testhospital.co.ke",
            phone="+254700123456"
        )
        
        # Create test integration
        self.integration = HospitalIntegration.objects.create(
            hospital=self.hospital,
            api_key=APIKeyGenerator.generate_api_key(),
            api_secret=APIKeyGenerator.generate_api_key(),  # Use same function for secret
            status="active",
            data_retention_days=2555,
            encryption_enabled=True
        )
        
        # Force save to ensure it's committed to database
        self.integration.save()
        
        # Create test consent
        self.consent = DataProcessingConsent.objects.create(
            integration=self.integration,
            consent_type="patient_data",
            status="granted",
            expires_at=timezone.now() + timedelta(days=365),
            consent_text="I consent to the processing of patient data for appointment reminders",
            ip_address="127.0.0.1"
        )
    
    def generate_signature(self, method, endpoint, body=""):
        """Generate HMAC signature for testing"""
        timestamp = str(int(time.time()))
        payload = f"{timestamp}:{body}"
        signature = hmac.new(
            self.integration.api_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return timestamp, signature
    
    def test_api_key_verification(self):
        """Test API key verification endpoint"""
        url = reverse('api_integration:verify-api-key')
        data = {
            "api_key": self.integration.api_key
        }
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'valid')
        self.assertEqual(response.data['hospital_name'], self.hospital.name)
    
    def test_invalid_api_key(self):
        """Test invalid API key verification"""
        url = reverse('api_integration:verify-api-key')
        data = {
            "api_key": "invalid-api-key"
        }
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Invalid API key')
    
    def test_patient_data_access_with_valid_consent(self):
        """Test patient data access with valid consent"""
        url = reverse('api_integration:patient-data')
        
        # Generate signature
        timestamp, signature = self.generate_signature('GET', url)
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': timestamp,
            'HTTP_X_SIGNATURE': signature
        }
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
    
    def test_patient_data_access_without_consent(self):
        """Test patient data access without valid consent"""
        # Deactivate consent
        self.consent.status = 'expired'
        self.consent.save()
        
        url = reverse('api_integration:patient-data')
        
        # Generate signature
        timestamp, signature = self.generate_signature('GET', url)
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': timestamp,
            'HTTP_X_SIGNATURE': signature
        }
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data) or self.assertIn('error', response.data)
    
    def test_invalid_signature(self):
        """Test request with invalid signature"""
        url = reverse('api_integration:patient-data')
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': str(int(time.time())),
            'HTTP_X_SIGNATURE': 'invalid-signature'
        }
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_expired_timestamp(self):
        """Test request with expired timestamp"""
        url = reverse('api_integration:patient-data')
        
        # Use expired timestamp (6 minutes ago)
        expired_timestamp = str(int(time.time()) - 360)
        payload = f"{expired_timestamp}:"
        signature = hmac.new(
            self.integration.api_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': expired_timestamp,
            'HTTP_X_SIGNATURE': signature
        }
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_data_encryption(self):
        """Test data encryption functionality"""
        encryption = DataEncryption()
        test_data = "+254700123456"
        
        # Encrypt data
        encrypted = encryption.encrypt_data(test_data)
        self.assertNotEqual(encrypted, test_data)
        
        # Decrypt data
        decrypted = encryption.decrypt_data(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_consent_request(self):
        """Test consent request creation"""
        url = reverse('api_integration:request-consent')
        
        # Generate signature
        timestamp, signature = self.generate_signature('POST', url, '{"consent_type": "appointment_data"}')
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': timestamp,
            'HTTP_X_SIGNATURE': signature,
            'CONTENT_TYPE': 'application/json'
        }
        
        data = {
            "consent_type": "appointment_data"
        }
        
        response = self.client.post(url, data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['consent_type'], 'appointment_data')
    
    def test_consent_withdrawal(self):
        """Test consent withdrawal"""
        url = reverse('api_integration:withdraw-consent')
        
        # Generate signature
        timestamp, signature = self.generate_signature('POST', url, '{"consent_type": "patient_data"}')
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': timestamp,
            'HTTP_X_SIGNATURE': signature,
            'CONTENT_TYPE': 'application/json'
        }
        
        data = {
            "consent_type": "patient_data"
        }
        
        response = self.client.post(url, data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify consent was withdrawn
        self.consent.refresh_from_db()
        self.assertEqual(self.consent.status, 'withdrawn')
    
    def test_compliance_status(self):
        """Test compliance status endpoint"""
        url = reverse('api_integration:compliance-status')
        
        # Generate signature
        timestamp, signature = self.generate_signature('GET', url)
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': timestamp,
            'HTTP_X_SIGNATURE': signature
        }
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('compliance_score', response.data)
        self.assertIn('consents', response.data)
        self.assertIn('security_incidents', response.data)
    
    def test_api_logging(self):
        """Test that API calls are properly logged"""
        initial_log_count = APILog.objects.count()
        
        url = reverse('api_integration:patient-data')
        
        # Generate signature
        timestamp, signature = self.generate_signature('GET', url)
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': timestamp,
            'HTTP_X_SIGNATURE': signature
        }
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that log was created
        self.assertEqual(APILog.objects.count(), initial_log_count + 1)
        
        # Verify log details
        log = APILog.objects.latest('created_at')
        self.assertEqual(log.integration, self.integration)
        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.auth_status, 'success')
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        url = reverse('api_integration:patient-data')
        
        # Make multiple requests quickly
        for i in range(105):  # Exceed burst limit
            timestamp, signature = self.generate_signature('GET', url)
            
            headers = {
                'HTTP_X_API_KEY': self.integration.api_key,
                'HTTP_X_TIMESTAMP': timestamp,
                'HTTP_X_SIGNATURE': signature
            }
            
            response = self.client.get(url, **headers)
            
            # Should start rate limiting after burst limit
            if i >= 100:
                # Note: Rate limiting implementation would need to be tested
                # This is a placeholder for the actual rate limiting test
                pass
    
    def test_integration_suspension(self):
        """Test integration suspension"""
        # Suspend integration
        self.integration.status = 'suspended'
        self.integration.suspended_at = timezone.now()
        self.integration.save()
        
        url = reverse('api_integration:patient-data')
        
        # Generate signature
        timestamp, signature = self.generate_signature('GET', url)
        
        headers = {
            'HTTP_X_API_KEY': self.integration.api_key,
            'HTTP_X_TIMESTAMP': timestamp,
            'HTTP_X_SIGNATURE': signature
        }
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class SecurityIncidentTestCase(TransactionTestCase):
    """Test cases for security incident handling"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test hospital and integration
        self.hospital = Hospital.objects.create(
            name="Test Hospital",
            hospital_type="private",
            email="admin@testhospital.co.ke",
            phone="+254700123456"
        )
        
        self.integration = HospitalIntegration.objects.create(
            hospital=self.hospital,
            api_key=APIKeyGenerator.generate_api_key(),
            api_secret=APIKeyGenerator.generate_api_key(),
            status="active",
            data_retention_days=2555,
            encryption_enabled=True
        )
    
    def test_security_incident_creation(self):
        """Test security incident creation"""
        incident = SecurityIncident.objects.create(
            integration=self.integration,
            title="Test Security Incident",
            description="This is a test security incident",
            severity="medium",
            incident_type="unauthorized_access"
        )
        
        self.assertEqual(incident.integration, self.integration)
        self.assertEqual(incident.severity, "medium")
        self.assertEqual(incident.status, "open")
    
    def test_security_incident_resolution(self):
        """Test security incident resolution"""
        incident = SecurityIncident.objects.create(
            integration=self.integration,
            title="Test Security Incident",
            description="This is a test security incident",
            severity="medium",
            incident_type="unauthorized_access"
        )
        
        # Resolve incident
        incident.status = "resolved"
        incident.resolved_at = timezone.now()
        incident.resolution_notes = "Issue resolved successfully"
        incident.save()
        
        self.assertEqual(incident.status, "resolved")
        self.assertIsNotNone(incident.resolved_at)
        self.assertEqual(incident.resolution_notes, "Issue resolved successfully")

class DataRetentionTestCase(TransactionTestCase):
    """Test cases for data retention policies"""
    
    def setUp(self):
        """Set up test data"""
        self.hospital = Hospital.objects.create(
            name="Test Hospital",
            hospital_type="private",
            email="admin@testhospital.co.ke",
            phone="+254700123456"
        )
        
        self.integration = HospitalIntegration.objects.create(
            hospital=self.hospital,
            api_key=APIKeyGenerator.generate_api_key(),
            api_secret=APIKeyGenerator.generate_api_key(),
            status="active",
            data_retention_days=2555,
            encryption_enabled=True
        )
    
    def test_data_retention_calculation(self):
        """Test data retention period calculation"""
        from .compliance import DataRetentionManager
        
        retention_date = DataRetentionManager.should_delete_data(self.integration, 'patient_data')
        expected_date = timezone.now() - timedelta(days=self.integration.data_retention_days)
        
        # Should be approximately equal (within 1 minute)
        self.assertLess(abs((retention_date - expected_date).total_seconds()), 60)
    
    def test_audit_log_retention(self):
        """Test audit log retention period"""
        from .compliance import DataRetentionManager
        
        retention_date = DataRetentionManager.should_delete_data(self.integration, 'audit_logs')
        expected_days = max(self.integration.data_retention_days, 2555)  # 7 years minimum
        expected_date = timezone.now() - timedelta(days=expected_days)
        
        # Should be approximately equal (within 1 minute)
        self.assertLess(abs((retention_date - expected_date).total_seconds()), 60)