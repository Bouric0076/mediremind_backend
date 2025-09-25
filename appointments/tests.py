"""
Comprehensive test suite for the appointments app
"""
import json
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import (
    AppointmentType, Room, Equipment, 
    Appointment, AppointmentWaitlist
)
from accounts.models import EnhancedPatient, EnhancedStaffProfile
from .serializers import (
    AppointmentCreateSerializer, AppointmentUpdateSerializer,
    AppointmentListSerializer, AppointmentSerializer
)
from .forms import (
    AppointmentForm, AppointmentUpdateForm, AppointmentCancelForm,
    AppointmentSearchForm, AvailabilityCheckForm, TimeSlotForm
)

User = get_user_model()


class AppointmentModelTestCase(TestCase):
    """Test cases for appointment models"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@test.com',
            password='testpass123',
            first_name='Dr. Jane',
            last_name='Smith'
        )
        
        # Create profiles
        self.patient = EnhancedPatient.objects.create(
            user=self.patient_user,
            phone='+1234567890',
            date_of_birth=date(1990, 1, 1),
            gender='M',
            address='123 Test St'
        )
        
        self.provider = EnhancedStaffProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123456',
            phone='+0987654321'
        )
        
        # Create appointment type
        self.appointment_type = AppointmentType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('100.00'),
            description='General medical consultation'
        )
        
        # Create room and equipment
        self.room = Room.objects.create(
            name='Room 101',
            room_type='consultation',
            capacity=2
        )
        
        self.equipment = Equipment.objects.create(
            name='Stethoscope',
            equipment_type='medical',
            status='available'
        )
    
    def test_appointment_creation(self):
        """Test appointment model creation"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            duration_minutes=30,
            title='Test Appointment',
            reason='Regular checkup',
            status='scheduled',
            priority='medium',
            estimated_cost=Decimal('100.00'),
            room=self.room
        )
        
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.provider, self.provider)
        self.assertEqual(appointment.status, 'scheduled')
        self.assertEqual(appointment.estimated_cost, Decimal('100.00'))
        
    def test_appointment_str_method(self):
        """Test appointment string representation"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            title='Test Appointment'
        )
        
        expected_str = f"Test Appointment - {self.patient.user.get_full_name()} with {self.provider.user.get_full_name()}"
        self.assertEqual(str(appointment), expected_str)
    
    def test_appointment_duration_property(self):
        """Test appointment duration calculation"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            duration_minutes=45
        )
        
        self.assertEqual(appointment.duration, timedelta(minutes=45))


class AppointmentSerializerTestCase(TestCase):
    """Test cases for appointment serializers"""
    
    def setUp(self):
        """Set up test data"""
        # Create users and profiles (same as model tests)
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@test.com',
            password='testpass123',
            first_name='Dr. Jane',
            last_name='Smith'
        )
        
        self.patient = EnhancedPatient.objects.create(
            user=self.patient_user,
            phone='+1234567890',
            date_of_birth=date(1990, 1, 1),
            gender='M'
        )
        
        self.provider = EnhancedStaffProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123456'
        )
        
        self.appointment_type = AppointmentType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('100.00')
        )
    
    def test_appointment_create_serializer(self):
        """Test appointment creation serializer"""
        data = {
            'patient': self.patient.id,
            'provider': self.provider.id,
            'appointment_type': self.appointment_type.id,
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'time': '10:00:00',
            'title': 'Test Appointment',
            'reason': 'Regular checkup',
            'priority': 'medium'
        }
        
        serializer = AppointmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        appointment = serializer.save()
        self.assertEqual(appointment.title, 'Test Appointment')
        self.assertEqual(appointment.patient, self.patient)
    
    def test_appointment_list_serializer(self):
        """Test appointment list serializer"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            title='Test Appointment'
        )
        
        serializer = AppointmentListSerializer(appointment)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Appointment')
        self.assertIn('patient_name', data)
        self.assertIn('provider_name', data)


class AppointmentFormTestCase(TestCase):
    """Test cases for appointment forms"""
    
    def setUp(self):
        """Set up test data"""
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@test.com',
            password='testpass123'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@test.com',
            password='testpass123'
        )
        
        self.patient = EnhancedPatient.objects.create(
            user=self.patient_user,
            phone='+1234567890',
            date_of_birth=date(1990, 1, 1)
        )
        
        self.provider = EnhancedStaffProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123456'
        )
        
        self.appointment_type = AppointmentType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('100.00')
        )
    
    def test_appointment_form_valid(self):
        """Test valid appointment form"""
        form_data = {
            'patient': self.patient.id,
            'provider': self.provider.id,
            'appointment_type': self.appointment_type.id,
            'date': date.today() + timedelta(days=1),
            'time': time(10, 0),
            'title': 'Test Appointment',
            'reason': 'Regular checkup',
            'priority': 'medium'
        }
        
        form = AppointmentForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_appointment_form_past_date_invalid(self):
        """Test appointment form with past date"""
        form_data = {
            'patient': self.patient.id,
            'provider': self.provider.id,
            'appointment_type': self.appointment_type.id,
            'date': date.today() - timedelta(days=1),
            'time': time(10, 0),
            'title': 'Test Appointment'
        }
        
        form = AppointmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)
    
    def test_availability_check_form(self):
        """Test availability check form"""
        form_data = {
            'provider_id': self.provider.id,
            'date': date.today() + timedelta(days=1),
            'time': time(10, 0),
            'duration': 30
        }
        
        form = AvailabilityCheckForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)


class AppointmentBusinessLogicTestCase(TestCase):
    """Test cases for appointment business logic"""
    
    def setUp(self):
        """Set up test data"""
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@test.com',
            password='testpass123'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@test.com',
            password='testpass123'
        )
        
        self.patient = EnhancedPatient.objects.create(
            user=self.patient_user,
            phone='+1234567890',
            date_of_birth=date(1990, 1, 1)
        )
        
        self.provider = EnhancedStaffProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123456'
        )
        
        self.appointment_type = AppointmentType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('100.00')
        )
    
    def test_appointment_conflict_detection(self):
        """Test appointment conflict detection"""
        # Create first appointment
        appointment1 = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            duration_minutes=30,
            status='scheduled'
        )
        
        # Try to create conflicting appointment
        form_data = {
            'patient': self.patient.id,
            'provider': self.provider.id,
            'appointment_type': self.appointment_type.id,
            'date': date.today() + timedelta(days=1),
            'time': time(10, 15),  # Overlaps with first appointment
            'duration_minutes': 30
        }
        
        form = AppointmentForm(data=form_data)
        # The form should detect the conflict in clean method
        self.assertFalse(form.is_valid())
    
    def test_appointment_status_transitions(self):
        """Test valid appointment status transitions"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            status='pending'
        )
        
        # Test valid transitions
        appointment.status = 'scheduled'
        appointment.save()
        self.assertEqual(appointment.status, 'scheduled')
        
        appointment.status = 'completed'
        appointment.save()
        self.assertEqual(appointment.status, 'completed')
    
    def test_appointment_cost_calculation(self):
        """Test appointment cost calculation"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            duration_minutes=60  # Double the standard duration
        )
        
        # Cost should be based on appointment type price
        expected_cost = self.appointment_type.price
        self.assertEqual(appointment.estimated_cost, expected_cost)


class AppointmentAPITestCase(APITestCase):
    """Test cases for appointment API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@test.com',
            password='testpass123',
            first_name='Dr. Jane',
            last_name='Smith'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create profiles
        self.patient = EnhancedPatient.objects.create(
            user=self.patient_user,
            phone='+1234567890',
            date_of_birth=date(1990, 1, 1),
            gender='M'
        )
        
        self.provider = EnhancedStaffProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123456'
        )
        
        self.appointment_type = AppointmentType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('100.00')
        )
        
        # Create tokens for authentication
        self.patient_token = Token.objects.create(user=self.patient_user)
        self.doctor_token = Token.objects.create(user=self.doctor_user)
        self.admin_token = Token.objects.create(user=self.admin_user)
        
        self.client = APIClient()
    
    def test_create_appointment_authenticated(self):
        """Test creating appointment with authentication"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        
        data = {
            'patient': self.patient.id,
            'provider': self.provider.id,
            'appointment_type': self.appointment_type.id,
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'time': '10:00:00',
            'title': 'Test Appointment',
            'reason': 'Regular checkup',
            'priority': 'medium'
        }
        
        response = self.client.post('/api/appointments/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Appointment')
    
    def test_create_appointment_unauthenticated(self):
        """Test creating appointment without authentication"""
        data = {
            'patient': self.patient.id,
            'provider': self.provider.id,
            'appointment_type': self.appointment_type.id,
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'time': '10:00:00',
            'title': 'Test Appointment'
        }
        
        response = self.client.post('/api/appointments/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_appointments_patient(self):
        """Test listing appointments as patient"""
        # Create test appointment
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            title='Test Appointment'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get('/api/appointments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Appointment')
    
    def test_update_appointment_authorized(self):
        """Test updating appointment with proper authorization"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            title='Original Title'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        
        data = {
            'title': 'Updated Title',
            'reason': 'Updated reason'
        }
        
        response = self.client.put(f'/api/appointments/{appointment.id}/update/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')
    
    def test_cancel_appointment(self):
        """Test canceling appointment"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            title='Test Appointment',
            status='scheduled'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        
        data = {
            'cancellation_reason': 'Personal emergency'
        }
        
        response = self.client.post(f'/api/appointments/{appointment.id}/cancel/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify appointment is canceled
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'cancelled')
    
    def test_check_availability(self):
        """Test checking provider availability"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        
        data = {
            'provider_id': self.provider.id,
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'time': '10:00:00',
            'duration': 30
        }
        
        response = self.client.post('/api/appointments/check-availability/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
    
    def test_get_appointment_statistics_admin(self):
        """Test getting appointment statistics as admin"""
        # Create test appointments
        Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today(),
            time=time(10, 0),
            status='completed'
        )
        
        Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(11, 0),
            status='scheduled'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get('/api/appointments/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_appointments', response.data)
        self.assertIn('completed_appointments', response.data)
        self.assertIn('scheduled_appointments', response.data)


class AppointmentWaitlistTestCase(TestCase):
    """Test cases for appointment waitlist functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@test.com',
            password='testpass123'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@test.com',
            password='testpass123'
        )
        
        self.patient = EnhancedPatient.objects.create(
            user=self.patient_user,
            phone='+1234567890',
            date_of_birth=date(1990, 1, 1)
        )
        
        self.provider = EnhancedStaffProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123456'
        )
        
        self.appointment_type = AppointmentType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('100.00')
        )
    
    def test_waitlist_creation(self):
        """Test creating waitlist entry"""
        waitlist_entry = AppointmentWaitlist.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time=time(10, 0),
            priority='medium',
            notes='Flexible with timing'
        )
        
        self.assertEqual(waitlist_entry.patient, self.patient)
        self.assertEqual(waitlist_entry.provider, self.provider)
        self.assertEqual(waitlist_entry.status, 'active')
    
    def test_waitlist_str_method(self):
        """Test waitlist string representation"""
        waitlist_entry = AppointmentWaitlist.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time=time(10, 0)
        )
        
        expected_str = f"Waitlist: {self.patient.user.get_full_name()} for {self.provider.user.get_full_name()}"
        self.assertEqual(str(waitlist_entry), expected_str)
    
    def test_waitlist_status_transitions(self):
        """Test waitlist status transitions"""
        waitlist_entry = AppointmentWaitlist.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time=time(10, 0),
            status='active'
        )
        
        # Test status change to fulfilled
        waitlist_entry.status = 'fulfilled'
        waitlist_entry.save()
        self.assertEqual(waitlist_entry.status, 'fulfilled')
        
        # Test status change to cancelled
        waitlist_entry.status = 'cancelled'
        waitlist_entry.save()
        self.assertEqual(waitlist_entry.status, 'cancelled')


class AppointmentIntegrationTestCase(TestCase):
    """Integration tests for appointment system"""
    
    def setUp(self):
        """Set up test data"""
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient@test.com',
            password='testpass123'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@test.com',
            password='testpass123'
        )
        
        self.patient = EnhancedPatient.objects.create(
            user=self.patient_user,
            phone='+1234567890',
            date_of_birth=date(1990, 1, 1)
        )
        
        self.provider = EnhancedStaffProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine',
            license_number='LIC123456'
        )
        
        self.appointment_type = AppointmentType.objects.create(
            name='General Consultation',
            duration_minutes=30,
            price=Decimal('100.00')
        )
        
        self.room = Room.objects.create(
            name='Room 101',
            room_type='consultation',
            capacity=2
        )
    
    def test_full_appointment_lifecycle(self):
        """Test complete appointment lifecycle"""
        # 1. Create appointment
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            title='Integration Test Appointment',
            status='pending',
            room=self.room
        )
        
        self.assertEqual(appointment.status, 'pending')
        
        # 2. Confirm appointment
        appointment.status = 'scheduled'
        appointment.save()
        self.assertEqual(appointment.status, 'scheduled')
        
        # 3. Complete appointment
        appointment.status = 'completed'
        appointment.actual_start_time = datetime.combine(appointment.date, appointment.time)
        appointment.actual_end_time = appointment.actual_start_time + timedelta(minutes=30)
        appointment.save()
        
        self.assertEqual(appointment.status, 'completed')
        self.assertIsNotNone(appointment.actual_start_time)
        self.assertIsNotNone(appointment.actual_end_time)
    
    def test_appointment_with_equipment(self):
        """Test appointment with equipment assignment"""
        equipment = Equipment.objects.create(
            name='X-Ray Machine',
            equipment_type='imaging',
            status='available'
        )
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            provider=self.provider,
            appointment_type=self.appointment_type,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            title='X-Ray Appointment',
            room=self.room
        )
        
        appointment.equipment.add(equipment)
        
        self.assertIn(equipment, appointment.equipment.all())
        self.assertEqual(appointment.equipment.count(), 1)
