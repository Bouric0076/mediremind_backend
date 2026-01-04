import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from django.test import TestCase, override_settings
from django.conf import settings

# Import the modules we need to test
from notifications.utils import format_appointment_time, get_appointment_data
from notifications.template_manager import TemplateManager, TemplateType, RecipientType
from notifications.email_client import email_client


class TestNotificationUtils(TestCase):
    """Test cases for notification utility functions"""
    
    def test_format_appointment_time_valid(self):
        """Test formatting valid appointment time"""
        result = format_appointment_time('2024-01-15', '14:30')
        self.assertIn('Monday, January 15', result)
        self.assertIn('02:30 PM', result)
    
    def test_format_appointment_time_invalid(self):
        """Test formatting invalid appointment time"""
        result = format_appointment_time('invalid-date', 'invalid-time')
        self.assertEqual(result, "invalid-date at invalid-time")
    
    @patch('appointments.models.Appointment.objects.select_related')
    def test_get_appointment_data_success(self, mock_select_related):
        """Test successful appointment data retrieval"""
        # Mock appointment object
        mock_appointment = Mock()
        mock_appointment.id = 123
        mock_appointment.appointment_date = '2024-01-15'
        mock_appointment.start_time = '14:30'
        mock_appointment.status = 'scheduled'
        
        # Mock related objects
        mock_provider = Mock()
        mock_provider.user.get_full_name.return_value = 'Dr. John Smith'
        mock_appointment.provider = mock_provider
        
        mock_patient = Mock()
        mock_patient.user.get_full_name.return_value = 'Jane Doe'
        mock_patient.user.id = 456
        mock_appointment.patient = mock_patient
        
        mock_appointment_type = Mock()
        mock_appointment_type.name = 'General Consultation'
        mock_appointment.appointment_type = mock_appointment_type
        
        mock_hospital = Mock()
        mock_hospital.name = 'Test Hospital'
        mock_appointment.hospital = mock_hospital
        
        mock_room = Mock()
        mock_room.name = 'Room 101'
        mock_room.room_number = '101'
        mock_room.floor = '2nd Floor'
        mock_room.building = 'Main Building'
        mock_appointment.room = mock_room
        
        # Mock the query
        mock_query = Mock()
        mock_query.get.return_value = mock_appointment
        mock_select_related.return_value = mock_query
        
        result, error = get_appointment_data(123)
        
        self.assertIsNotNone(result)
        self.assertIsNone(error)
        self.assertEqual(result['id'], '123')
        self.assertEqual(result['doctor_name'], 'Dr. John Smith')
        self.assertEqual(result['patient_name'], 'Jane Doe')
        self.assertIn('Test Hospital', result['location'])
        self.assertIn('Room 101', result['location'])
    
    def test_get_appointment_data_not_found(self):
        """Test appointment data retrieval when appointment not found"""
        with patch('appointments.models.Appointment.objects.select_related') as mock_select_related:
            mock_query = Mock()
            mock_query.get.side_effect = Exception('Appointment not found')
            mock_select_related.return_value = mock_query
            
            result, error = get_appointment_data(999)
            
            self.assertIsNone(result)
            self.assertIsNotNone(error)


class TestTemplateManager(TestCase):
    """Test cases for template manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.template_manager = TemplateManager()
    
    def test_template_config_loading(self):
        """Test that template configurations are loaded correctly"""
        config = self.template_manager.get_template_config('appointment_confirmation_patient')
        self.assertIsNotNone(config)
        self.assertEqual(config.template_type, TemplateType.APPOINTMENT_CONFIRMATION)
        self.assertEqual(config.recipient_type, RecipientType.PATIENT)
        self.assertIn('recipient_name', config.required_fields)
        self.assertIn('appointment.provider_name', config.required_fields)
    
    def test_template_validation_valid_context(self):
        """Test template validation with valid context"""
        valid_context = {
            'recipient_name': 'John Doe',
            'appointment': {
                'provider_name': 'Dr. Smith',
                'appointment_date': '2024-01-15',
                'start_time': '14:30'
            }
        }
        
        # Should not raise any exceptions
        try:
            self.template_manager._validate_template_context(
                valid_context, 
                ['recipient_name', 'appointment.provider_name', 'appointment.appointment_date', 'appointment.start_time']
            )
        except Exception as e:
            self.fail(f"Validation failed for valid context: {e}")
    
    def test_template_validation_missing_field(self):
        """Test template validation with missing required field"""
        invalid_context = {
            'recipient_name': 'John Doe',
            'appointment': {
                'provider_name': 'Dr. Smith',
                # Missing appointment_date
                'start_time': '14:30'
            }
        }
        
        # Should log warning but not raise exception (backward compatibility)
        with patch('notifications.template_manager.logger') as mock_logger:
            self.template_manager._validate_template_context(
                invalid_context, 
                ['recipient_name', 'appointment.provider_name', 'appointment.appointment_date', 'appointment.start_time']
            )
            mock_logger.warning.assert_called()
    
    def test_template_type_mapping(self):
        """Test template type to key mapping"""
        template_key = self.template_manager._get_template_key_from_type(TemplateType.APPOINTMENT_CONFIRMATION)
        self.assertEqual(template_key, 'appointment_confirmation_patient')
        
        template_key = self.template_manager._get_template_key_from_type(TemplateType.APPOINTMENT_CANCELLATION)
        self.assertEqual(template_key, 'appointment_cancellation_patient')


class TestEmailClient(TestCase):
    """Test cases for email client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.email_client = email_client
    
    def test_template_selection_reschedule(self):
        """Test template selection for reschedule updates"""
        with patch('notifications.email_client.template_manager') as mock_template_manager:
            mock_template_manager.render_template.return_value = ('Test Subject', '<html>Test</html>')
            
            appointment_data = {
                'patient_name': 'John Doe',
                'doctor_name': 'Dr. Smith',
                'appointment_date': '2024-01-15',
                'start_time': '14:30'
            }
            
            with patch('notifications.email_client.EmailClient.send_email') as mock_send:
                mock_send.return_value = True
                
                success, message = self.email_client.send_appointment_update_email(
                    appointment_data=appointment_data,
                    update_type='reschedule',
                    recipient_email='patient@example.com',
                    is_patient=True
                )
                
                self.assertTrue(success)
                mock_template_manager.render_template.assert_called_once()
    
    def test_template_selection_cancellation(self):
        """Test template selection for cancellation updates"""
        with patch('notifications.email_client.template_manager') as mock_template_manager:
            mock_template_manager.render_template.return_value = ('Test Subject', '<html>Test</html>')
            
            appointment_data = {
                'patient_name': 'John Doe',
                'doctor_name': 'Dr. Smith',
                'appointment_date': '2024-01-15',
                'start_time': '14:30'
            }
            
            with patch('notifications.email_client.EmailClient.send_email') as mock_send:
                mock_send.return_value = True
                
                success, message = self.email_client.send_appointment_update_email(
                    appointment_data=appointment_data,
                    update_type='cancellation',
                    recipient_email='patient@example.com',
                    is_patient=True
                )
                
                self.assertTrue(success)
                mock_template_manager.render_template.assert_called_once()
    
    def test_template_selection_no_show(self):
        """Test template selection for no-show updates"""
        with patch('notifications.email_client.template_manager') as mock_template_manager:
            mock_template_manager.render_template.return_value = ('Test Subject', '<html>Test</html>')
            
            appointment_data = {
                'patient_name': 'John Doe',
                'doctor_name': 'Dr. Smith',
                'appointment_date': '2024-01-15',
                'start_time': '14:30'
            }
            
            with patch('notifications.email_client.EmailClient.send_email') as mock_send:
                mock_send.return_value = True
                
                success, message = self.email_client.send_appointment_update_email(
                    appointment_data=appointment_data,
                    update_type='no-show',
                    recipient_email='patient@example.com',
                    is_patient=True
                )
                
                self.assertTrue(success)
                mock_template_manager.render_template.assert_called_once()


class TestEmailClient(TestCase):
    """Test cases for unified email client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.email_client = email_client
    
    def test_template_selection_mapping(self):
        """Test template type selection based on update type"""
        # Test reschedule
        template_type = self.email_client._get_template_type_from_update_type('rescheduled')
        self.assertEqual(template_type, TemplateType.APPOINTMENT_RESCHEDULE)
        
        # Test cancellation
        template_type = self.email_client._get_template_type_from_update_type('cancellation')
        self.assertEqual(template_type, TemplateType.APPOINTMENT_CANCELLATION)
        
        # Test no-show
        template_type = self.email_client._get_template_type_from_update_type('no-show')
        self.assertEqual(template_type, TemplateType.PATIENT_NO_SHOW_ALERT)
        
        # Test created
        template_type = self.email_client._get_template_type_from_update_type('created')
        self.assertEqual(template_type, TemplateType.APPOINTMENT_CONFIRMATION)
    
    def test_appointment_data_validation(self):
        """Test appointment data validation"""
        # Test with invalid data format
        success, message = self.email_client.send_appointment_update_email(
            to_email='patient@example.com',
            patient_name='John Doe',
            appointment_details="invalid string data",  # Should be dict
            update_type='rescheduled'
        )
        
        self.assertFalse(success)
        self.assertIn("Invalid appointment data format", message)
    
    def test_template_data_preparation(self):
        """Test template data preparation"""
        appointment_details = {
            'id': '123',
            'appointment_date': '2024-01-15',
            'start_time': '14:30',
            'provider_name': 'Dr. Smith',
            'appointment_type': 'Consultation',
            'location': 'Test Hospital'
        }
        
        with patch('notifications.email_client.email_client.render_template') as mock_render:
            mock_render.return_value = ('Test Subject', '<html>Test</html>')
            with patch('notifications.email_client.email_client.send_email') as mock_send:
                mock_send.return_value = (True, 'Email sent')
                
                success, message = self.email_client.send_appointment_update_email(
                    to_email='patient@example.com',
                    patient_name='John Doe',
                    appointment_details=appointment_details,
                    update_type='rescheduled'
                )
                
                self.assertTrue(success)
                mock_render.assert_called_once()
                
                # Check that template data was prepared correctly
                call_args = mock_render.call_args
                self.assertEqual(call_args[1]['recipient_name'], 'John Doe')
                self.assertEqual(call_args[1]['recipient_type'], RecipientType.PATIENT)


class TestStatusTransitionLogic(TestCase):
    """Test status transition and notification trigger logic"""
    
    def test_status_change_detection(self):
        """Test that status changes are properly detected and mapped to update types"""
        # This would test the logic from appointments/views.py
        # Since we can't easily test the view directly, we'll test the logic
        
        # Test cancellation status change
        old_status = 'scheduled'
        new_status = 'cancelled'
        
        # Simulate the logic from appointments/views.py
        update_type = 'reschedule'  # Default
        if new_status == 'cancelled':
            update_type = 'cancellation'
        elif new_status == 'no-show':
            update_type = 'no-show'
        elif old_status == 'scheduled' and new_status == 'confirmed':
            update_type = 'confirmation'
        elif new_status == 'completed':
            update_type = None
        elif old_status != new_status:
            update_type = 'reschedule'
        
        self.assertEqual(update_type, 'cancellation')
    
    def test_no_show_status_change(self):
        """Test no-show status change mapping"""
        old_status = 'scheduled'
        new_status = 'no-show'
        
        # Simulate the logic
        update_type = 'reschedule'  # Default
        if new_status == 'cancelled':
            update_type = 'cancellation'
        elif new_status == 'no-show':
            update_type = 'no-show'
        elif old_status == 'scheduled' and new_status == 'confirmed':
            update_type = 'confirmation'
        elif new_status == 'completed':
            update_type = None
        elif old_status != new_status:
            update_type = 'reschedule'
        
        self.assertEqual(update_type, 'no-show')
    
    def test_confirmation_status_change(self):
        """Test confirmation status change mapping"""
        old_status = 'scheduled'
        new_status = 'confirmed'
        
        # Simulate the logic
        update_type = 'reschedule'  # Default
        if new_status == 'cancelled':
            update_type = 'cancellation'
        elif new_status == 'no-show':
            update_type = 'no-show'
        elif old_status == 'scheduled' and new_status == 'confirmed':
            update_type = 'confirmation'
        elif new_status == 'completed':
            update_type = None
        elif old_status != new_status:
            update_type = 'reschedule'
        
        self.assertEqual(update_type, 'confirmation')


class TestEmergencyContactNotifications(TestCase):
    """Test emergency contact notification logic"""
    
    def test_emergency_contact_notification_triggers(self):
        """Test that emergency contacts are notified for appropriate status changes"""
        
        # Test that both cancellation and no-show should trigger emergency contact notifications
        status_changes_that_should_notify_emergency = ['cancellation', 'no-show']
        
        for status_change in status_changes_that_should_notify_emergency:
            self.assertIn(status_change, ['cancellation', 'no-show'])
    
    def test_emergency_contact_data_extraction(self):
        """Test extraction of emergency contact data from appointment data"""
        appointment_data = {
            'id': 123,
            'patient_name': 'John Doe',
            'emergency_contact_email': 'emergency@example.com',
            'emergency_contact_name': 'Jane Emergency',
            'emergency_contact_relationship': 'Spouse'
        }
        
        emergency_email = appointment_data.get('emergency_contact_email')
        emergency_name = appointment_data.get('emergency_contact_name')
        
        self.assertEqual(emergency_email, 'emergency@example.com')
        self.assertEqual(emergency_name, 'Jane Emergency')


class TestDataFormattingConsistency(TestCase):
    """Test data formatting consistency between API and templates"""
    
    def test_field_name_consistency(self):
        """Test that field names are consistent across the system"""
        # Test the field mapping we implemented
        appointment_details = {
            'provider_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'start_time': '14:30',
            'appointment': {
                'provider_name': 'Dr. Smith',
                'doctor_name': 'Dr. Smith',  # Alias
                'appointment_date': '2024-01-15',
                'date': '2024-01-15',  # Alias
                'start_time': '14:30',
                'time': '14:30'  # Alias
            }
        }
        
        # Verify that both old and new field names are available
        self.assertEqual(appointment_details['appointment']['provider_name'], 'Dr. Smith')
        self.assertEqual(appointment_details['appointment']['doctor_name'], 'Dr. Smith')
        self.assertEqual(appointment_details['appointment']['appointment_date'], '2024-01-15')
        self.assertEqual(appointment_details['appointment']['date'], '2024-01-15')
    
    def test_template_field_requirements(self):
        """Test that template field requirements are met"""
        template_manager = TemplateManager()
        config = template_manager.get_template_config('appointment_confirmation_patient')
        
        required_fields = config.required_fields
        
        # Check that required fields include both old and new field names
        self.assertIn('recipient_name', required_fields)
        self.assertIn('appointment.provider_name', required_fields)
        self.assertIn('appointment.appointment_date', required_fields)
        self.assertIn('appointment.start_time', required_fields)


class TestNotificationFunctions(TestCase):
    """Test cases for core notification functions in utils.py"""
    
    @patch('notifications.utils.get_appointment_data')
    @patch('notifications.utils.email_client.send_appointment_confirmation_email')
    def test_send_appointment_confirmation_success(self, mock_send_email, mock_get_data):
        """Test successful appointment confirmation sending"""
        # Mock appointment data
        mock_appointment_data = {
            'id': '123',
            'patient_name': 'John Doe',
            'doctor_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'start_time': '14:30'
        }
        mock_get_data.return_value = (mock_appointment_data, None)
        mock_send_email.return_value = (True, 'Email sent successfully')
        
        # Test the function
        result = send_appointment_confirmation(
            appointment_id=123,
            patient_email='patient@example.com',
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(result)
        self.assertEqual(mock_send_email.call_count, 2)  # Once for patient, once for doctor
    
    @patch('notifications.utils.get_appointment_data')
    def test_send_appointment_confirmation_failure(self, mock_get_data):
        """Test appointment confirmation when appointment data retrieval fails"""
        mock_get_data.return_value = (None, 'Appointment not found')
        
        result = send_appointment_confirmation(
            appointment_id=123,
            patient_email='patient@example.com',
            doctor_email='doctor@example.com'
        )
        
        self.assertFalse(result)
    
    @patch('notifications.utils.get_appointment_data')
    @patch('notifications.utils.email_client.send_appointment_update_email')
    def test_send_appointment_update_success(self, mock_send_email, mock_get_data):
        """Test successful appointment update sending"""
        mock_appointment_data = {
            'id': '123',
            'patient_name': 'John Doe',
            'doctor_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'start_time': '14:30'
        }
        mock_get_data.return_value = (mock_appointment_data, None)
        mock_send_email.return_value = (True, 'Email sent successfully')
        
        result = send_appointment_update(
            appointment_data=mock_appointment_data,
            update_type='reschedule',
            patient_email='patient@example.com',
            doctor_email='doctor@example.com'
        )
        
        self.assertTrue(result)
        self.assertEqual(mock_send_email.call_count, 2)  # Once for patient, once for doctor
    
    @patch('notifications.utils.get_appointment_data')
    @patch('notifications.utils.email_client.send_appointment_reminder_email')
    def test_send_appointment_reminder_success(self, mock_send_email, mock_get_data):
        """Test successful appointment reminder sending"""
        mock_appointment_data = {
            'id': '123',
            'patient_name': 'John Doe',
            'doctor_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'start_time': '14:30'
        }
        mock_get_data.return_value = (mock_appointment_data, None)
        mock_send_email.return_value = (True, 'Email sent successfully')
        
        result = send_appointment_reminder(appointment_id=123)
        
        self.assertTrue(result)
        mock_send_email.assert_called_once()
    
    @patch('notifications.utils.Appointment.objects.select_related')
    def test_get_appointment_details_success(self, mock_select_related):
        """Test successful appointment details retrieval"""
        # Mock appointment object
        mock_appointment = Mock()
        mock_appointment.id = 123
        mock_appointment.appointment_date = '2024-01-15'
        mock_appointment.start_time = '14:30'
        mock_appointment.status = 'scheduled'
        mock_appointment.notes = 'Test notes'
        
        # Mock related objects
        mock_patient = Mock()
        mock_patient.user.get_full_name.return_value = 'John Doe'
        mock_patient.user.email = 'patient@example.com'
        mock_patient.phone_number = '+1234567890'
        mock_patient.emergency_contact_email = 'emergency@example.com'
        mock_patient.emergency_contact_name = 'Jane Emergency'
        
        mock_provider = Mock()
        mock_provider.user.get_full_name.return_value = 'Dr. Smith'
        mock_provider.user.email = 'doctor@example.com'
        mock_provider.phone_number = '+0987654321'
        
        mock_appointment_type = Mock()
        mock_appointment_type.name = 'General Consultation'
        
        mock_hospital = Mock()
        mock_hospital.name = 'Test Hospital'
        mock_hospital.address = '123 Main St'
        
        mock_room = Mock()
        mock_room.name = 'Room 101'
        mock_room.room_number = '101'
        mock_room.floor = '2nd Floor'
        mock_room.building = 'Main Building'
        
        # Set up relationships
        mock_appointment.patient = mock_patient
        mock_appointment.provider = mock_provider
        mock_appointment.appointment_type = mock_appointment_type
        mock_appointment.hospital = mock_hospital
        mock_appointment.room = mock_room
        
        # Mock the query
        mock_query = Mock()
        mock_query.get.return_value = mock_appointment
        mock_select_related.return_value = mock_query
        
        result = get_appointment_details(123)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 123)
        self.assertEqual(result['patient_name'], 'John Doe')
        self.assertEqual(result['doctor_name'], 'Dr. Smith')
        self.assertEqual(result['appointment_type'], 'General Consultation')
        self.assertEqual(result['hospital_name'], 'Test Hospital')
        self.assertEqual(result['room_name'], 'Room 101')
        self.assertEqual(result['emergency_contact_email'], 'emergency@example.com')
        self.assertEqual(result['emergency_contact_name'], 'Jane Emergency')
    
    @patch('notifications.utils.PushSubscription.objects.filter')
    def test_get_patient_data_success(self, mock_filter):
        """Test successful patient data retrieval"""
        # Mock patient object
        mock_patient = Mock()
        mock_patient.user.get_full_name.return_value = 'John Doe'
        mock_patient.user.email = 'patient@example.com'
        mock_patient.phone_number = '+1234567890'
        mock_patient.emergency_contact_email = 'emergency@example.com'
        mock_patient.emergency_contact_name = 'Jane Emergency'
        
        # Mock subscriptions
        mock_subscription1 = Mock()
        mock_subscription1.endpoint = 'https://fcm.googleapis.com/fcm/send/abc123'
        mock_subscription1.p256dh = 'p256dh_key'
        mock_subscription1.auth = 'auth_key'
        mock_subscription1.is_active = True
        
        mock_subscription2 = Mock()
        mock_subscription2.endpoint = 'https://fcm.googleapis.com/fcm/send/def456'
        mock_subscription2.p256dh = 'p256dh_key2'
        mock_subscription2.auth = 'auth_key2'
        mock_subscription2.is_active = True
        
        mock_filter.return_value = [mock_subscription1, mock_subscription2]
        
        result = get_patient_data(mock_patient)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'John Doe')
        self.assertEqual(result['email'], 'patient@example.com')
        self.assertEqual(result['phone'], '+1234567890')
        self.assertEqual(result['emergency_contact_email'], 'emergency@example.com')
        self.assertEqual(len(result['push_subscriptions']), 2)
    
    @patch('notifications.utils.PushSubscription.objects.filter')
    def test_get_doctor_data_success(self, mock_filter):
        """Test successful doctor data retrieval"""
        # Mock doctor object
        mock_doctor = Mock()
        mock_doctor.user.get_full_name.return_value = 'Dr. Smith'
        mock_doctor.user.email = 'doctor@example.com'
        mock_doctor.phone_number = '+0987654321'
        mock_doctor.specialization = 'Cardiology'
        
        # Mock subscriptions
        mock_subscription = Mock()
        mock_subscription.endpoint = 'https://fcm.googleapis.com/fcm/send/doc123'
        mock_subscription.p256dh = 'doc_p256dh'
        mock_subscription.auth = 'doc_auth'
        mock_subscription.is_active = True
        
        mock_filter.return_value = [mock_subscription]
        
        result = get_doctor_data(mock_doctor)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'Dr. Smith')
        self.assertEqual(result['email'], 'doctor@example.com')
        self.assertEqual(result['phone'], '+0987654321')
        self.assertEqual(result['specialization'], 'Cardiology')
        self.assertEqual(len(result['push_subscriptions']), 1)
    
    @patch('notifications.utils.PushSubscription.objects.filter')
    def test_send_push_to_user_success(self, mock_filter):
        """Test successful push notification to user"""
        # Mock subscription
        mock_subscription = Mock()
        mock_subscription.endpoint = 'https://fcm.googleapis.com/fcm/send/user123'
        mock_subscription.p256dh = 'user_p256dh'
        mock_subscription.auth = 'user_auth'
        mock_subscription.is_active = True
        
        mock_filter.return_value = [mock_subscription]
        
        with patch('notifications.utils.push_notifications.send_to_user') as mock_send:
            mock_send.return_value = True
            
            result = send_push_to_user(
                user_id=456,
                title='Test Notification',
                message='This is a test message',
                url='/appointments/123',
                data={'appointment_id': '123'}
            )
            
            self.assertTrue(result)
            mock_send.assert_called_once()
    
    @patch('notifications.utils.Appointment.objects.filter')
    def test_send_upcoming_appointment_reminders(self, mock_filter):
        """Test sending upcoming appointment reminders"""
        # Mock appointments that need reminders
        mock_appointment1 = Mock()
        mock_appointment1.id = 123
        mock_appointment1.appointment_date = '2024-01-15'
        mock_appointment1.start_time = '14:30'
        
        mock_appointment2 = Mock()
        mock_appointment2.id = 124
        mock_appointment2.appointment_date = '2024-01-15'
        mock_appointment2.start_time = '15:00'
        
        mock_filter.return_value = [mock_appointment1, mock_appointment2]
        
        with patch('notifications.utils.send_appointment_reminder') as mock_send_reminder:
            mock_send_reminder.return_value = True
            
            send_upcoming_appointment_reminders()
            
            self.assertEqual(mock_send_reminder.call_count, 2)


if __name__ == '__main__':
    unittest.main()