from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum
from .models import (
    InsuranceProvider, ServiceCode, Invoice, InvoiceLineItem,
    Payment, InsuranceClaim, PaymentPlan, PaymentPlanInstallment
)


class InvoiceLineItemInline(admin.TabularInline):
    """Inline admin for invoice line items"""
    model = InvoiceLineItem
    extra = 1
    fields = (
        'service_code', 'description', 'quantity', 'unit_price',
        'discount_amount', 'total_amount'
    )
    readonly_fields = ('total_amount',)


class PaymentInline(admin.TabularInline):
    """Inline admin for payments"""
    model = Payment
    extra = 0
    fields = (
        'payment_method', 'amount', 'payment_date', 'status',
        'transaction_id'
    )
    readonly_fields = ('transaction_id',)


class PaymentPlanInstallmentInline(admin.TabularInline):
    """Inline admin for payment plan installments"""
    model = PaymentPlanInstallment
    extra = 1
    fields = (
        'installment_number', 'due_date', 'amount', 'status',
        'paid_date', 'paid_amount'
    )
    readonly_fields = ('installment_number',)


@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    """Admin interface for InsuranceProvider model"""
    
    list_display = (
        'name', 'code', 'phone', 'is_active'
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'provider_id', 'contact_phone', 'contact_email')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'provider_id', 'description'
            )
        }),
        ('Contact Information', {
            'fields': (
                'contact_phone', 'contact_email', 'website',
                'address', 'city', 'state', 'zip_code'
            )
        }),
        ('Coverage Details', {
            'fields': (
                'coverage_types', 'prior_authorization_required',
                'copay_amount', 'deductible_amount'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(ServiceCode)
class ServiceCodeAdmin(admin.ModelAdmin):
    """Admin interface for ServiceCode model"""
    
    list_display = (
        'code', 'description', 'category', 'base_price'
    )
    list_filter = ('category',)
    search_fields = ('code', 'description')
    ordering = ('code',)
    
    fieldsets = (
        ('Code Information', {
            'fields': (
                'code', 'description', 'category'
            )
        }),
        ('Pricing', {
            'fields': (
                'base_price',
            )
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin interface for Invoice model"""
    
    list_display = (
        'invoice_number', 'get_patient_name', 'invoice_date',
        'total_amount', 'amount_paid', 'amount_due', 'status'
    )
    list_filter = (
        'status', 'invoice_date', 'due_date', 'created_at'
    )
    search_fields = (
        'invoice_number', 'patient__user__first_name',
        'patient__user__last_name', 'appointment__appointment_id'
    )
    ordering = ('-invoice_date',)
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'patient', 'appointment', 'invoice_number'
            )
        }),
        ('Dates', {
            'fields': (
                'invoice_date', 'due_date', 'service_date'
            )
        }),
        ('Amounts', {
            'fields': (
                'subtotal', 'tax_amount', 'discount_amount',
                'total_amount', 'amount_paid', 'amount_due'
            )
        }),
        ('Insurance', {
            'fields': (
                'insurance_provider', 'insurance_claim_number',
                'insurance_paid_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Notes', {
            'fields': (
                'status', 'notes'
            )
        }),
    )
    
    readonly_fields = (
        'invoice_number', 'amount_due', 'created_at', 'updated_at'
    )
    inlines = [InvoiceLineItemInline, PaymentInline]
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.patient.user.get_full_name() or obj.patient.user.username
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'patient__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient__user', 'appointment', 'insurance_provider'
        )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate invoice number if not provided"""
        if not obj.invoice_number:
            obj.invoice_number = obj.generate_invoice_number()
        super().save_model(request, obj, form, change)


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    """Admin interface for InvoiceLineItem model"""
    
    list_display = (
        'get_invoice_number', 'get_patient_name', 'service_code',
        'description', 'quantity', 'unit_price', 'total_amount'
    )
    list_filter = (
        'service_code__category', 'invoice__status', 'invoice__invoice_date'
    )
    search_fields = (
        'invoice__invoice_number', 'service_code__code',
        'description', 'invoice__patient__user__first_name',
        'invoice__patient__user__last_name'
    )
    ordering = ('-invoice__invoice_date',)
    
    fieldsets = (
        ('Invoice Information', {
            'fields': (
                'invoice', 'service_code'
            )
        }),
        ('Service Details', {
            'fields': (
                'description', 'quantity', 'unit_price',
                'discount_amount', 'total_amount'
            )
        }),
    )
    
    readonly_fields = ('total_amount',)
    
    def get_invoice_number(self, obj):
        """Display invoice number"""
        return obj.invoice.invoice_number
    get_invoice_number.short_description = 'Invoice Number'
    get_invoice_number.admin_order_field = 'invoice__invoice_number'
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.invoice.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'invoice__patient__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'invoice__patient__user', 'service_code'
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model"""
    
    list_display = (
        'transaction_id', 'get_patient_name', 'get_invoice_number',
        'amount', 'payment_method', 'payment_date', 'status'
    )
    list_filter = (
        'payment_method', 'status', 'payment_date', 'created_at'
    )
    search_fields = (
        'transaction_id', 'invoice__invoice_number',
        'invoice__patient__user__first_name',
        'invoice__patient__user__last_name', 'reference_number'
    )
    ordering = ('-payment_date',)
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'invoice', 'amount', 'payment_method', 'payment_date'
            )
        }),
        ('Transaction Details', {
            'fields': (
                'transaction_id', 'reference_number', 'processor_response'
            )
        }),
        ('Status & Notes', {
            'fields': (
                'status', 'notes'
            )
        }),
    )
    
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.invoice.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'invoice__patient__user__first_name'
    
    def get_invoice_number(self, obj):
        """Display invoice number"""
        return obj.invoice.invoice_number
    get_invoice_number.short_description = 'Invoice Number'
    get_invoice_number.admin_order_field = 'invoice__invoice_number'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'invoice__patient__user'
        )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate transaction ID if not provided"""
        if not obj.transaction_id:
            obj.transaction_id = obj.generate_transaction_id()
        super().save_model(request, obj, form, change)


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    """Admin interface for InsuranceClaim model"""
    
    list_display = (
        'claim_number', 'get_patient_name', 'insurance_provider',
        'billed_amount', 'approved_amount', 'status', 'submission_date'
    )
    list_filter = (
        'status', 'submission_date', 'processed_date', 'insurance_provider'
    )
    search_fields = (
        'claim_number', 'invoice__patient__user__first_name',
        'invoice__patient__user__last_name', 'insurance_provider__name'
    )
    ordering = ('-submission_date',)
    
    fieldsets = (
        ('Claim Information', {
            'fields': (
                'invoice', 'insurance_provider', 'claim_number'
            )
        }),
        ('Amounts', {
            'fields': (
                'claim_amount', 'approved_amount', 'denied_amount',
                'patient_responsibility'
            )
        }),
        ('Dates', {
            'fields': (
                'submitted_date', 'processed_date'
            )
        }),
        ('Status & Details', {
            'fields': (
                'status', 'denial_reason', 'notes'
            )
        }),
    )
    
    readonly_fields = ('claim_number', 'created_at', 'updated_at')
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.invoice.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'invoice__patient__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'invoice__patient__user', 'insurance_provider'
        )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate claim number if not provided"""
        if not obj.claim_number:
            obj.claim_number = obj.generate_claim_number()
        super().save_model(request, obj, form, change)


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    """Admin interface for PaymentPlan model"""
    
    list_display = (
        'plan_number', 'get_patient_name', 'total_amount',
        'monthly_payment', 'status', 'start_date'
    )
    list_filter = (
        'status', 'start_date', 'created_at'
    )
    search_fields = (
        'plan_number', 'invoice__patient__user__first_name',
        'invoice__patient__user__last_name'
    )
    ordering = ('-start_date',)
    
    fieldsets = (
        ('Plan Information', {
            'fields': (
                'invoice', 'plan_number', 'total_amount', 'monthly_payment'
            )
        }),
        ('Schedule', {
            'fields': (
                'start_date', 'end_date', 'number_of_installments'
            )
        }),
        ('Terms', {
            'fields': (
                'interest_rate', 'late_fee_amount', 'terms_and_conditions'
            )
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )
    
    readonly_fields = ('plan_number', 'created_at', 'updated_at')
    inlines = [PaymentPlanInstallmentInline]
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.invoice.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'invoice__patient__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'invoice__patient__user'
        )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate plan number if not provided"""
        if not obj.plan_number:
            obj.plan_number = obj.generate_plan_number()
        super().save_model(request, obj, form, change)


@admin.register(PaymentPlanInstallment)
class PaymentPlanInstallmentAdmin(admin.ModelAdmin):
    """Admin interface for PaymentPlanInstallment model"""
    
    list_display = (
        'get_plan_number', 'get_patient_name', 'installment_number',
        'due_date', 'amount_due', 'amount_paid', 'status'
    )
    list_filter = (
        'status', 'due_date', 'paid_date'
    )
    search_fields = (
        'payment_plan__plan_number',
        'payment_plan__invoice__patient__user__first_name',
        'payment_plan__invoice__patient__user__last_name'
    )
    ordering = ('payment_plan', 'installment_number')
    
    fieldsets = (
        ('Installment Information', {
            'fields': (
                'payment_plan', 'installment_number', 'due_date', 'amount_due'
            )
        }),
        ('Payment Details', {
            'fields': (
                'paid_date', 'amount_paid', 'late_fee_charged', 'status'
            )
        }),
    )
    
    readonly_fields = ('installment_number',)
    
    def get_plan_number(self, obj):
        """Display payment plan number"""
        return obj.payment_plan.plan_number
    get_plan_number.short_description = 'Plan Number'
    get_plan_number.admin_order_field = 'payment_plan__plan_number'
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.payment_plan.invoice.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'payment_plan__invoice__patient__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'payment_plan__invoice__patient__user'
        )
