import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from django.test import TestCase, override_settings
from django.conf import settings
from django.urls import reverse

# Import the modules we need to test
from appointments.models import Appointment, AppointmentType, Room
from accounts.models import Hospital
from notifications.utils import send_appointment_update
from notifications.template_manager import TemplateManager, TemplateType
from notifications.email_client import email_client
# from notifications.resend_service import resend_service  # Removed - using unified email_client


class TestEndToEndNotificationFlow(TestCase):
    """Integration tests for complete notification flow"""
    
    def setUp(self):
        """Set up test data"""
        self.test_patient_email = 'patient@example.com'
        self.test_patient_name = 'John Doe'
        self.test_provider_name = 'Dr. Sarah Smith'
        self.test_appointment_date = '2024-01-15'
        self.test_start_time = '14:30'
        self.test_location = 'Test Hospital, Room 101'
        
        self.base_appointment_data = {
            'id': '123',
            'patient_name': self.test_patient_name,
            'patient_email': self.test_patient_email,
            'provider_name': self.test_provider_name,
            'appointment_date': self.test_appointment_date,
            'start_time': self.test_start_time,
            'appointment_type': 'General Consultation',
            'location': self.test_location,
            'emergency_contact_email': 'emergency@example.com',
            'emergency_contact_name': 'Jane Emergency'
        }
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_appointment_confirmation_flow(self, mock_render_template, mock_send_email):
        """Test complete appointment confirmation notification flow"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Confirmed - Jan 15, 2024 at 2:30 PM',
            '<html><body>Your appointment with Dr. Sarah Smith is confirmed for Jan 15, 2024 at 2:30 PM.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = (True, 'Email sent successfully')
        
        # Send confirmation notification (use 'created' for confirmation)
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='created',
            patient_email=self.test_patient_email,
            doctor_email='doctor@example.com'
        )
        
        # Verify the flow completed successfully
        self.assertTrue(success)
        # Should be called twice - once for patient, once for doctor
        self.assertEqual(mock_render_template.call_count, 2)
        self.assertEqual(mock_send_email.call_count, 2)
        
        # Verify first call was for patient confirmation
        first_call = mock_render_template.call_args_list[0]
        self.assertEqual(first_call[0][0], 'appointment_confirmation_patient')
        self.assertEqual(first_call[0][1].recipient_name, self.test_patient_name)
        
        # Verify second call was for doctor confirmation
        second_call = mock_render_template.call_args_list[1]
        self.assertEqual(second_call[0][0], 'appointment_confirmation_doctor')
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_appointment_cancellation_flow(self, mock_render_template, mock_send_email):
        """Test complete appointment cancellation notification flow"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Cancelled - Jan 15, 2024 at 2:30 PM',
            '<html><body>Your appointment with Dr. Sarah Smith has been cancelled.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = (True, 'Email sent successfully')
        
        # Send cancellation notification
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='cancellation',
            patient_email=self.test_patient_email,
            doctor_email='doctor@example.com'
        )
        
        # Verify the flow completed successfully
        self.assertTrue(success)
        self.assertEqual(mock_render_template.call_count, 2)  # Called for patient and doctor
        self.assertEqual(mock_send_email.call_count, 2)  # Called for patient and doctor
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_appointment_reschedule_flow(self, mock_render_template, mock_send_email):
        """Test complete appointment reschedule notification flow"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Rescheduled - Jan 15, 2024 at 2:30 PM',
            '<html><body>Your appointment with Dr. Sarah Smith has been rescheduled to Jan 15, 2024 at 2:30 PM.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Send reschedule notification
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='reschedule',
            patient_email=self.test_patient_email,
            doctor_email='doctor@example.com'
        )
        
        # Verify the flow completed successfully
        self.assertTrue(success)
        self.assertEqual(mock_render_template.call_count, 2)  # Called for patient and doctor
        self.assertEqual(mock_send_email.call_count, 2)  # Called for patient and doctor
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_appointment_no_show_flow(self, mock_render_template, mock_send_email):
        """Test complete appointment no-show notification flow"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Missed Appointment Alert - Jan 15, 2024 at 2:30 PM',
            '<html><body>This is to inform you that you missed your appointment with Dr. Sarah Smith.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Send no-show notification
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='no-show',
            patient_email=self.test_patient_email,
            doctor_email='doctor@example.com'
        )
        
        # Verify the flow completed successfully
        self.assertTrue(success)
        self.assertEqual(mock_render_template.call_count, 2)  # Called for patient and doctor
        self.assertEqual(mock_send_email.call_count, 2)  # Called for patient and doctor
    
    @override_settings(DEBUG=False)  # Production mode
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_production_notification_flow(self, mock_render_template, mock_send_email):
        """Test complete notification flow in production mode"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Confirmed',
            '<html><body>Your appointment is confirmed.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = (True, 'Email sent successfully')
        
        # Send confirmation notification in production mode (use 'created' for confirmation)
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='created',
            patient_email=self.test_patient_email,
            doctor_email='doctor@example.com'
        )
        
        # Verify the flow completed successfully
        self.assertTrue(success)
        self.assertEqual(mock_render_template.call_count, 2)  # Called for patient and doctor
        self.assertEqual(mock_send_email.call_count, 2)  # Called for patient and doctor


class TestEmergencyContactIntegration(TestCase):
    """Integration tests for emergency contact notifications"""
    
    def setUp(self):
        """Set up test data"""
        self.test_appointment_data = {
            'id': '123',
            'patient_name': 'John Doe',
            'patient_email': 'patient@example.com',
            'provider_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'start_time': '14:30',
            'appointment_type': 'General Consultation',
            'location': 'Test Hospital',
            'emergency_contact_email': 'emergency@example.com',
            'emergency_contact_name': 'Jane Emergency'
        }
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_cancellation_emergency_contact_notification(self, mock_render_template, mock_send_email):
        """Test that cancellation notifications are sent to emergency contacts"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Cancelled',
            '<html><body>Appointment cancelled.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Send cancellation notification (should trigger emergency contact notification)
        success, message = send_appointment_update(
            appointment_data=self.test_appointment_data,
            update_type='cancellation',
            patient_email=self.test_appointment_data['patient_email'],
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(success)
        # Should be called twice - once for patient, once for emergency contact
        self.assertEqual(mock_send_email.call_count, 2)
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_no_show_emergency_contact_notification(self, mock_render_template, mock_send_email):
        """Test that no-show notifications are sent to emergency contacts"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Missed Appointment Alert',
            '<html><body>Missed appointment.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Send no-show notification (should trigger emergency contact notification)
        success, message = send_appointment_update(
            appointment_data=self.test_appointment_data,
            update_type='no-show',
            patient_email=self.test_appointment_data['patient_email'],
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(success)
        # Should be called twice - once for patient, once for emergency contact
        self.assertEqual(mock_send_email.call_count, 2)


class TestStatusChangeScenarios(TestCase):
    """Integration tests for various status change scenarios"""
    
    def setUp(self):
        """Set up test data"""
        self.base_appointment_data = {
            'id': '123',
            'patient_name': 'John Doe',
            'patient_email': 'patient@example.com',
            'provider_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'start_time': '14:30',
            'appointment_type': 'General Consultation',
            'location': 'Test Hospital'
        }
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_scheduled_to_confirmed_transition(self, mock_render_template, mock_send_email):
        """Test notification flow when appointment status changes from scheduled to confirmed"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Confirmed',
            '<html><body>Your appointment is confirmed.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Simulate scheduled -> confirmed transition (use 'created' for confirmation)
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='created',
            patient_email=self.base_appointment_data['patient_email'],
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(success)
        mock_render_template.assert_called_once()
        mock_send_email.assert_called_once()
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_scheduled_to_cancelled_transition(self, mock_render_template, mock_send_email):
        """Test notification flow when appointment status changes from scheduled to cancelled"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Cancelled',
            '<html><body>Your appointment has been cancelled.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Simulate scheduled -> cancelled transition
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='cancellation',
            patient_email=self.base_appointment_data['patient_email'],
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(success)
        mock_render_template.assert_called_once()
        mock_send_email.assert_called_once()
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_scheduled_to_no_show_transition(self, mock_render_template, mock_send_email):
        """Test notification flow when appointment status changes from scheduled to no-show"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Missed Appointment Alert',
            '<html><body>You missed your appointment.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Simulate scheduled -> no-show transition
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='no-show',
            patient_email=self.base_appointment_data['patient_email'],
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(success)
        mock_render_template.assert_called_once()
        mock_send_email.assert_called_once()


class TestErrorHandlingAndEdgeCases(TestCase):
    """Integration tests for error handling and edge cases"""
    
    def setUp(self):
        """Set up test data"""
        self.base_appointment_data = {
            'id': '123',
            'patient_name': 'John Doe',
            'patient_email': 'patient@example.com',
            'provider_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'start_time': '14:30',
            'appointment_type': 'General Consultation',
            'location': 'Test Hospital'
        }
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_missing_required_fields_handling(self, mock_render_template, mock_send_email):
        """Test handling of missing required fields"""
        # Create appointment data with missing required fields
        incomplete_appointment_data = {
            'id': '123',
            'patient_name': 'John Doe',
            'patient_email': 'patient@example.com'
            # Missing provider_name, appointment_date, start_time, etc.
        }
        
        # Mock template rendering (should handle missing fields gracefully)
        mock_render_template.return_value = (
            'Appointment Confirmed',
            '<html><body>Your appointment is confirmed.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Should still send notification despite missing fields (use 'created' for confirmation)
        success, message = send_appointment_update(
            appointment_data=incomplete_appointment_data,
            update_type='created',
            patient_email=incomplete_appointment_data['patient_email'],
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(success)
        mock_render_template.assert_called_once()
        mock_send_email.assert_called_once()
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_invalid_email_address_handling(self, mock_render_template, mock_send_email):
        """Test handling of invalid email addresses"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Confirmed',
            '<html><body>Your appointment is confirmed.</body></html>'
        )
        
        # Mock email sending to fail
        mock_send_email.return_value = False
        
        # Send notification with invalid email (use 'created' for confirmation)
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='created',
            patient_email='invalid-email-address',
            doctor_email='doctor@example.com'
        )
        
        self.assertFalse(success)
        mock_render_template.assert_called_once()
        mock_send_email.assert_called_once()
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_template_rendering_failure_handling(self, mock_render_template, mock_send_email):
        """Test handling of template rendering failures"""
        # Mock template rendering to fail
        mock_render_template.side_effect = Exception('Template rendering failed')
        
        # Should handle the error gracefully (use 'created' for confirmation)
        success, message = send_appointment_update(
            appointment_data=self.base_appointment_data,
            update_type='created',
            patient_email=self.base_appointment_data['patient_email'],
            doctor_email='doctor@example.com'
        )
        
        self.assertFalse(success)
        mock_render_template.assert_called_once()
        mock_send_email.assert_not_called()  # Should not attempt to send if rendering fails


class TestDataPipelineIntegration(TestCase):
    """Integration tests for the complete data pipeline"""
    
    def setUp(self):
        """Set up test data"""
        self.test_appointment_data = {
            'id': '123',
            'patient_name': 'John Doe',
            'patient_email': 'patient@example.com',
            'provider_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'start_time': '14:30',
            'appointment_type': 'General Consultation',
            'location': 'Test Hospital, Room 101'
        }
    
    @override_settings(DEBUG=True)
    @patch('notifications.email_client.EmailClient.send_email')
    @patch('notifications.template_manager.template_manager.render_template')
    def test_data_formatting_through_pipeline(self, mock_render_template, mock_send_email):
        """Test that data is properly formatted throughout the entire pipeline"""
        # Mock template rendering
        mock_render_template.return_value = (
            'Appointment Confirmed',
            '<html><body>Your appointment is confirmed.</body></html>'
        )
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Send notification (use 'created' for confirmation)
        success, message = send_appointment_update(
            appointment_data=self.test_appointment_data,
            update_type='created',
            patient_email=self.test_appointment_data['patient_email'],
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(success)
        
        # Verify data formatting
        call_args = mock_render_template.call_args
        template_data = call_args[0][1]
        
        # Check that all required fields are present and properly formatted
        self.assertEqual(template_data['patient_name'], 'John Doe')
        self.assertEqual(template_data['appointment']['provider_name'], 'Dr. Smith')
        self.assertEqual(template_data['appointment']['appointment_date'], '2024-01-15')
        self.assertEqual(template_data['appointment']['start_time'], '14:30')
        self.assertEqual(template_data['appointment']['location'], 'Test Hospital, Room 101')


if __name__ == '__main__':
    unittest.main()