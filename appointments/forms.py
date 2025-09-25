"""
Django Forms for Appointment Management System
Provides comprehensive form validation for appointment-related operations
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta
from accounts.models import EnhancedPatient, EnhancedStaffProfile
from .models import AppointmentType, Appointment, AppointmentWaitlist, Room


class AppointmentForm(forms.ModelForm):
    """Form for creating and updating appointments"""
    
    class Meta:
        model = Appointment
        fields = [
            'patient', 'provider', 'appointment_type', 'room',
            'appointment_date', 'start_time', 'priority',
            'reason', 'notes', 'title'
        ]
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'title': forms.TextInput(attrs={'placeholder': 'Appointment title'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter querysets based on user role
        if self.user:
            if hasattr(self.user, 'enhanced_patient'):
                # Patient can only book for themselves
                self.fields['patient'].queryset = EnhancedPatient.objects.filter(
                    user=self.user
                )
                self.fields['patient'].initial = self.user.enhanced_patient
                self.fields['patient'].widget = forms.HiddenInput()
            elif hasattr(self.user, 'enhanced_staff_profile'):
                # Staff can book for any patient
                self.fields['patient'].queryset = EnhancedPatient.objects.all()
        
        # Only show active appointment types
        self.fields['appointment_type'].queryset = AppointmentType.objects.filter(
            is_active=True
        )
        
        # Only show available rooms
        self.fields['room'].queryset = Room.objects.filter(is_available=True)
        self.fields['room'].required = False
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_appointment_date(self):
        """Validate appointment date"""
        date = self.cleaned_data.get('appointment_date')
        if date:
            if date <= timezone.now().date():
                raise ValidationError("Appointment must be scheduled for a future date")
            
            # Check if date is too far in the future (e.g., 1 year)
            max_future_date = timezone.now().date() + timedelta(days=365)
            if date > max_future_date:
                raise ValidationError("Appointment cannot be scheduled more than 1 year in advance")
        
        return date
    
    def clean_start_time(self):
        """Validate appointment time"""
        start_time = self.cleaned_data.get('start_time')
        if start_time:
            # Check working hours (8 AM to 6 PM)
            working_start = time(8, 0)
            working_end = time(18, 0)
            
            if start_time < working_start or start_time > working_end:
                raise ValidationError("Appointments must be scheduled between 8:00 AM and 6:00 PM")
        
        return start_time
    
    def clean(self):
        """Comprehensive form validation"""
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        start_time = cleaned_data.get('start_time')
        patient = cleaned_data.get('patient')
        provider = cleaned_data.get('provider')
        
        # Check if appointment is in the future
        if appointment_date and start_time:
            appointment_datetime = timezone.make_aware(
                datetime.combine(appointment_date, start_time)
            )
            if appointment_datetime <= timezone.now():
                raise ValidationError("Appointment must be scheduled for a future date and time")
        
        # Check for scheduling conflicts
        if appointment_date and start_time and patient and provider:
            existing_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                start_time=start_time,
                status__in=['scheduled', 'confirmed', 'pending']
            )
            
            # Exclude current appointment if updating
            if self.instance and self.instance.pk:
                existing_appointments = existing_appointments.exclude(pk=self.instance.pk)
            
            # Check provider availability
            provider_conflict = existing_appointments.filter(provider=provider).first()
            if provider_conflict:
                raise ValidationError(
                    f"Provider {provider} is already booked at this time"
                )
            
            # Check patient availability
            patient_conflict = existing_appointments.filter(patient=patient).first()
            if patient_conflict:
                raise ValidationError(
                    f"Patient {patient} already has an appointment at this time"
                )
        
        return cleaned_data


class AppointmentUpdateForm(forms.ModelForm):
    """Form for updating existing appointments"""
    
    class Meta:
        model = Appointment
        fields = [
            'appointment_date', 'start_time', 'status', 'priority',
            'reason', 'notes', 'title', 'room'
        ]
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'title': forms.TextInput(attrs={'placeholder': 'Appointment title'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show available rooms
        self.fields['room'].queryset = Room.objects.filter(is_available=True)
        self.fields['room'].required = False
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_status(self):
        """Validate status transitions"""
        new_status = self.cleaned_data.get('status')
        
        if self.instance and self.instance.pk:
            current_status = self.instance.status
            
            # Define valid status transitions
            valid_transitions = {
                'pending': ['scheduled', 'cancelled', 'declined'],
                'scheduled': ['confirmed', 'cancelled', 'rescheduled', 'completed'],
                'confirmed': ['completed', 'cancelled', 'no_show'],
                'rescheduled': ['scheduled', 'cancelled'],
                'completed': [],  # Cannot change from completed
                'cancelled': [],  # Cannot change from cancelled
                'no_show': [],   # Cannot change from no_show
                'declined': []   # Cannot change from declined
            }
            
            if current_status in valid_transitions:
                if new_status not in valid_transitions[current_status]:
                    raise ValidationError(
                        f"Cannot change status from '{current_status}' to '{new_status}'"
                    )
        
        return new_status
    
    def clean(self):
        """Validate appointment updates"""
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        start_time = cleaned_data.get('start_time')
        
        # If date or time is being changed, validate conflicts
        if (appointment_date and start_time and 
            self.instance and self.instance.pk and
            (appointment_date != self.instance.appointment_date or 
             start_time != self.instance.start_time)):
            
            # Check for conflicts with the new time
            existing_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                start_time=start_time,
                status__in=['scheduled', 'confirmed', 'pending']
            ).exclude(pk=self.instance.pk)
            
            # Check provider availability
            provider_conflict = existing_appointments.filter(
                provider=self.instance.provider
            ).first()
            if provider_conflict:
                raise ValidationError(
                    f"Provider is already booked at the new time"
                )
            
            # Check patient availability
            patient_conflict = existing_appointments.filter(
                patient=self.instance.patient
            ).first()
            if patient_conflict:
                raise ValidationError(
                    f"Patient already has an appointment at the new time"
                )
        
        return cleaned_data


class AppointmentCancelForm(forms.Form):
    """Form for cancelling appointments"""
    reason = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Please provide a reason for cancellation...',
            'class': 'form-control'
        }),
        help_text="Please provide a reason for cancelling this appointment"
    )
    
    def clean_reason(self):
        """Validate cancellation reason"""
        reason = self.cleaned_data.get('reason')
        if not reason or len(reason.strip()) < 10:
            raise ValidationError("Please provide a detailed reason for cancellation (minimum 10 characters)")
        return reason.strip()


class AppointmentWaitlistForm(forms.ModelForm):
    """Form for adding patients to appointment waitlist"""
    
    class Meta:
        model = AppointmentWaitlist
        fields = [
            'patient', 'provider', 'appointment_type',
            'preferred_date_start', 'preferred_date_end', 
            'preferred_time_start', 'preferred_time_end',
            'priority', 'reason'
        ]
        widgets = {
            'preferred_date_start': forms.DateInput(attrs={'type': 'date'}),
            'preferred_date_end': forms.DateInput(attrs={'type': 'date'}),
            'preferred_time_start': forms.TimeInput(attrs={'type': 'time'}),
            'preferred_time_end': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter querysets based on user role
        if self.user and hasattr(self.user, 'enhanced_patient'):
            # Patient can only add themselves to waitlist
            self.fields['patient'].queryset = EnhancedPatient.objects.filter(
                user=self.user
            )
            self.fields['patient'].initial = self.user.enhanced_patient
            self.fields['patient'].widget = forms.HiddenInput()
        
        # Only show active appointment types
        self.fields['appointment_type'].queryset = AppointmentType.objects.filter(
            is_active=True
        )
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_preferred_date_start(self):
        """Validate preferred start date"""
        date = self.cleaned_data.get('preferred_date_start')
        if date and date <= timezone.now().date():
            raise ValidationError("Preferred start date must be in the future")
        return date


class AppointmentSearchForm(forms.Form):
    """Form for searching and filtering appointments"""
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
        ('declined', 'Declined'),
    ]
    
    PRIORITY_CHOICES = [
        ('', 'All Priorities'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    
    patient = forms.ModelChoiceField(
        queryset=EnhancedPatient.objects.all(),
        required=False,
        empty_label="All Patients",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    provider = forms.ModelChoiceField(
        queryset=EnhancedStaffProfile.objects.all(),
        required=False,
        empty_label="All Providers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    appointment_type = forms.ModelChoiceField(
        queryset=AppointmentType.objects.filter(is_active=True),
        required=False,
        empty_label="All Types",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def clean(self):
        """Validate date range"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Start date must be before end date")
        
        return cleaned_data


class AvailabilityCheckForm(forms.Form):
    """Form for checking provider availability"""
    
    provider = forms.ModelChoiceField(
        queryset=EnhancedStaffProfile.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    appointment_type = forms.ModelChoiceField(
        queryset=AppointmentType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_date(self):
        """Validate date is in the future"""
        date = self.cleaned_data.get('date')
        if date and date <= timezone.now().date():
            raise ValidationError("Date must be in the future")
        return date


class TimeSlotForm(forms.Form):
    """Form for getting available time slots"""
    provider = forms.ModelChoiceField(
        queryset=EnhancedStaffProfile.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    duration = forms.IntegerField(
        min_value=15,
        max_value=240,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def clean_date(self):
        """Validate date is in the future"""
        date = self.cleaned_data.get('date')
        if date and date < timezone.now().date():
            raise ValidationError("Cannot get time slots for past dates.")
        return date