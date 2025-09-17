from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from appointments.models import Appointment
from billing.models import Invoice
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription

User = get_user_model()


class SystemMetrics(models.Model):
    """Track overall system performance metrics"""
    date = models.DateField(unique=True)
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_registrations = models.IntegerField(default=0)
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'System Metric'
        verbose_name_plural = 'System Metrics'

    def __str__(self):
        return f"System Metrics for {self.date}"


class UserActivity(models.Model):
    """Track individual user activity patterns"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    login_count = models.IntegerField(default=0)
    appointments_booked = models.IntegerField(default=0)
    appointments_attended = models.IntegerField(default=0)
    prescriptions_filled = models.IntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)
    session_duration = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date', 'user']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'

    def __str__(self):
        return f"{self.user.username} activity on {self.date}"


class AppointmentAnalytics(models.Model):
    """Detailed analytics for appointment patterns"""
    DEPARTMENT_CHOICES = [
        ('cardiology', 'Cardiology'),
        ('dermatology', 'Dermatology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('general', 'General Medicine'),
    ]
    
    date = models.DateField()
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    no_show_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    average_duration = models.DurationField(null=True, blank=True)
    peak_hour = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date', 'department']
        ordering = ['-date', 'department']
        verbose_name = 'Appointment Analytics'
        verbose_name_plural = 'Appointment Analytics'

    def __str__(self):
        return f"{self.department} appointments on {self.date}"


class RevenueAnalytics(models.Model):
    """Track revenue and financial metrics"""
    date = models.DateField()
    department = models.CharField(max_length=50, choices=AppointmentAnalytics.DEPARTMENT_CHOICES)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    consultation_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    procedure_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prescription_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    outstanding_payments = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method_card = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date', 'department']
        ordering = ['-date', 'department']
        verbose_name = 'Revenue Analytics'
        verbose_name_plural = 'Revenue Analytics'

    def __str__(self):
        return f"{self.department} revenue on {self.date}"


class PatientDemographics(models.Model):
    """Track patient demographic information for analytics"""
    AGE_GROUPS = [
        ('0-18', '0-18 years'),
        ('19-35', '19-35 years'),
        ('36-50', '36-50 years'),
        ('51-65', '51-65 years'),
        ('65+', '65+ years'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    date = models.DateField()
    age_group = models.CharField(max_length=10, choices=AGE_GROUPS)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    total_patients = models.IntegerField(default=0)
    new_patients = models.IntegerField(default=0)
    returning_patients = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date', 'age_group', 'gender']
        ordering = ['-date', 'age_group', 'gender']
        verbose_name = 'Patient Demographics'
        verbose_name_plural = 'Patient Demographics'

    def __str__(self):
        return f"{self.age_group} {self.gender} patients on {self.date}"


class SystemPerformance(models.Model):
    """Track system performance and technical metrics"""
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_usage = models.FloatField(help_text="CPU usage percentage")
    memory_usage = models.FloatField(help_text="Memory usage percentage")
    disk_usage = models.FloatField(help_text="Disk usage percentage")
    active_sessions = models.IntegerField(default=0)
    api_response_time = models.FloatField(help_text="Average API response time in ms")
    database_queries = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    uptime_hours = models.FloatField(default=0)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'System Performance'
        verbose_name_plural = 'System Performance'

    def __str__(self):
        return f"Performance metrics at {self.timestamp}"


class PopularServices(models.Model):
    """Track most popular services and treatments"""
    date = models.DateField()
    service_name = models.CharField(max_length=200)
    department = models.CharField(max_length=50, choices=AppointmentAnalytics.DEPARTMENT_CHOICES)
    booking_count = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0.0, help_text="Percentage of completed appointments")
    average_rating = models.FloatField(null=True, blank=True)
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date', 'service_name', 'department']
        ordering = ['-date', '-booking_count']
        verbose_name = 'Popular Service'
        verbose_name_plural = 'Popular Services'

    def __str__(self):
        return f"{self.service_name} ({self.department}) on {self.date}"
