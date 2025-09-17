from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class InsuranceProvider(models.Model):
    """Insurance companies and providers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    
    # Contact Information
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Claims Processing
    claims_address = models.TextField(blank=True)
    claims_phone = models.CharField(max_length=20, blank=True)
    claims_email = models.EmailField(blank=True)
    electronic_claims_id = models.CharField(max_length=50, blank=True)
    
    # Contract Information
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Payment Terms
    payment_terms_days = models.PositiveIntegerField(default=30)
    requires_prior_authorization = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'insurance_providers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class ServiceCode(models.Model):
    """CPT codes and service definitions for billing"""
    
    CODE_TYPE_CHOICES = [
        ('cpt', 'CPT Code'),
        ('hcpcs', 'HCPCS Code'),
        ('icd10_pcs', 'ICD-10-PCS'),
        ('custom', 'Custom Service'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    code_type = models.CharField(max_length=20, choices=CODE_TYPE_CHOICES)
    description = models.CharField(max_length=500)
    category = models.CharField(max_length=100, blank=True)
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # RVU Information (Relative Value Units)
    work_rvu = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Work Relative Value Units"
    )
    practice_expense_rvu = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True
    )
    malpractice_rvu = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    # Billing Information
    requires_modifier = models.BooleanField(default=False)
    billable_units = models.CharField(
        max_length=50,
        default='1',
        help_text="Default billable units (e.g., '1', 'per hour', 'per session')"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_codes'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['code_type']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.description}"
    
    @property
    def total_rvu(self):
        """Calculate total RVU"""
        total = Decimal('0.00')
        if self.work_rvu:
            total += self.work_rvu
        if self.practice_expense_rvu:
            total += self.practice_expense_rvu
        if self.malpractice_rvu:
            total += self.malpractice_rvu
        return total


class Invoice(models.Model):
    """Patient invoices and billing statements"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid in Full'),
        ('overpaid', 'Overpaid'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True)
    
    # Core Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    
    # Invoice Details
    invoice_date = models.DateField()
    due_date = models.DateField()
    service_date = models.DateField()
    
    # Financial Information
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Payment Tracking
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    
    # Notes and References
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['patient', 'invoice_date']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['due_date']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not provided
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculate amount due
        self.amount_due = self.total_amount - self.amount_paid
        
        # Update payment status based on amounts
        if self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
            if not self.paid_at:
                self.paid_at = timezone.now()
        elif self.amount_paid > Decimal('0.00'):
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.patient.user.full_name}"
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        year = datetime.now().year
        # Get the count of invoices this year
        count = Invoice.objects.filter(
            invoice_date__year=year
        ).count() + 1
        return f"INV-{year}-{count:06d}"
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return (
            self.payment_status != 'paid' and
            self.due_date < timezone.now().date()
        )
    
    def calculate_totals(self):
        """Recalculate invoice totals from line items"""
        line_items = self.line_items.all()
        self.subtotal = sum(item.total_amount for item in line_items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.amount_due = self.total_amount - self.amount_paid


class InvoiceLineItem(models.Model):
    """Individual line items on an invoice"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Relationships
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    service_code = models.ForeignKey(
        ServiceCode,
        on_delete=models.CASCADE,
        related_name='invoice_line_items'
    )
    
    # Service Details
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Modifiers and Additional Info
    modifier_codes = models.JSONField(default=list, blank=True)
    diagnosis_codes = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoice_line_items'
        ordering = ['id']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['service_code']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.service_code.code} - {self.description}"


class Payment(models.Model):
    """Payment records for invoices"""
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('insurance', 'Insurance Payment'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_number = models.CharField(max_length=50, unique=True)
    
    # Core Relationships
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField()
    
    # Payment Processing
    transaction_id = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    processor_response = models.JSONField(default=dict, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Additional Information
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payments'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['invoice', 'payment_date']),
            models.Index(fields=['patient', 'payment_date']),
            models.Index(fields=['payment_number']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate payment number if not provided
        if not self.payment_number:
            self.payment_number = self.generate_payment_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Payment {self.payment_number} - ${self.amount}"
    
    def generate_payment_number(self):
        """Generate unique payment number"""
        from datetime import datetime
        year = datetime.now().year
        count = Payment.objects.filter(
            payment_date__year=year
        ).count() + 1
        return f"PAY-{year}-{count:06d}"


class InsuranceClaim(models.Model):
    """Insurance claims for reimbursement"""
    
    CLAIM_TYPE_CHOICES = [
        ('primary', 'Primary Insurance'),
        ('secondary', 'Secondary Insurance'),
        ('tertiary', 'Tertiary Insurance'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('denied', 'Denied'),
        ('paid', 'Paid'),
        ('appealed', 'Under Appeal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim_number = models.CharField(max_length=50, unique=True)
    
    # Core Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='insurance_claims'
    )
    insurance_provider = models.ForeignKey(
        InsuranceProvider,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='insurance_claims'
    )
    
    # Claim Information
    claim_type = models.CharField(max_length=20, choices=CLAIM_TYPE_CHOICES)
    service_date = models.DateField()
    submission_date = models.DateField()
    
    # Financial Information
    billed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    approved_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    patient_responsibility = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Status and Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    denial_reason = models.TextField(blank=True)
    
    # Insurance Information
    policy_number = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True)
    authorization_number = models.CharField(max_length=100, blank=True)
    
    # Processing Dates
    processed_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'insurance_claims'
        ordering = ['-submission_date']
        indexes = [
            models.Index(fields=['patient', 'submission_date']),
            models.Index(fields=['insurance_provider', 'submission_date']),
            models.Index(fields=['claim_number']),
            models.Index(fields=['status']),
            models.Index(fields=['claim_type']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate claim number if not provided
        if not self.claim_number:
            self.claim_number = self.generate_claim_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Claim {self.claim_number} - {self.insurance_provider.name}"
    
    def generate_claim_number(self):
        """Generate unique claim number"""
        from datetime import datetime
        year = datetime.now().year
        count = InsuranceClaim.objects.filter(
            submission_date__year=year
        ).count() + 1
        return f"CLM-{year}-{count:06d}"
    
    @property
    def outstanding_amount(self):
        """Calculate outstanding amount"""
        return self.billed_amount - self.paid_amount


class PaymentPlan(models.Model):
    """Payment plans for patients"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_number = models.CharField(max_length=50, unique=True)
    
    # Core Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='payment_plans'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payment_plans'
    )
    
    # Plan Details
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    down_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    monthly_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    number_of_payments = models.PositiveIntegerField()
    
    # Dates
    start_date = models.DateField()
    first_payment_date = models.DateField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Terms and Conditions
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    late_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_plans'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['patient', 'start_date']),
            models.Index(fields=['plan_number']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate plan number if not provided
        if not self.plan_number:
            self.plan_number = self.generate_plan_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Payment Plan {self.plan_number} - {self.patient.user.full_name}"
    
    def generate_plan_number(self):
        """Generate unique plan number"""
        from datetime import datetime
        year = datetime.now().year
        count = PaymentPlan.objects.filter(
            start_date__year=year
        ).count() + 1
        return f"PLAN-{year}-{count:06d}"
    
    @property
    def remaining_balance(self):
        """Calculate remaining balance"""
        paid_installments = self.installments.filter(status='paid').count()
        return self.total_amount - (paid_installments * self.monthly_payment)


class PaymentPlanInstallment(models.Model):
    """Individual installments for payment plans"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Relationships
    payment_plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.CASCADE,
        related_name='installments'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installments'
    )
    
    # Installment Details
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_date = models.DateField(null=True, blank=True)
    
    # Late Fees
    late_fee_assessed = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_plan_installments'
        ordering = ['payment_plan', 'installment_number']
        unique_together = ['payment_plan', 'installment_number']
        indexes = [
            models.Index(fields=['payment_plan', 'due_date']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Installment {self.installment_number} - {self.payment_plan.plan_number}"
    
    @property
    def is_overdue(self):
        """Check if installment is overdue"""
        return (
            self.status == 'pending' and
            self.due_date < timezone.now().date()
        )
    
    @property
    def remaining_balance(self):
        """Calculate remaining balance for this installment"""
        return self.amount_due - self.amount_paid
