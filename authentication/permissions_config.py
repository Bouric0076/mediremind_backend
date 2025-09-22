"""
Centralized Permission Configuration
====================================

This module serves as the single source of truth for all permission-related
configurations across the MediRemind application. It defines roles, permissions,
and their relationships to ensure consistency between frontend and backend.

Usage:
    from authentication.permissions_config import PERMISSIONS_CONFIG
    
    # Get permissions for a role
    permissions = PERMISSIONS_CONFIG.get_role_permissions('physician')
    
    # Check if role has permission
    has_perm = PERMISSIONS_CONFIG.has_permission('nurse', 'view_patient_profile')
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class PermissionLevel(Enum):
    """Permission access levels"""
    READ = "read"
    WRITE = "write" 
    DELETE = "delete"
    ADMIN = "admin"


class PermissionCategory(Enum):
    """Permission categories for organization"""
    PROFILE = "profile"
    PATIENTS = "patients"
    APPOINTMENTS = "appointments"
    MEDICAL_RECORDS = "medical_records"
    PRESCRIPTIONS = "prescriptions"
    BILLING = "billing"
    REPORTS = "reports"
    ADMINISTRATION = "administration"
    SYSTEM = "system"


@dataclass
class Permission:
    """Individual permission definition"""
    code: str
    name: str
    description: str
    category: PermissionCategory
    level: PermissionLevel
    is_sensitive: bool = False
    requires_mfa: bool = False
    requires_justification: bool = False


class PermissionsConfig:
    """Centralized permissions configuration manager"""
    
    def __init__(self):
        self._permissions = self._define_permissions()
        self._role_permissions = self._define_role_permissions()
        self._role_hierarchy = self._define_role_hierarchy()
    
    def _define_permissions(self) -> Dict[str, Permission]:
        """Define all available permissions"""
        permissions = [
            # Profile permissions
            Permission("view_own_profile", "View Own Profile", 
                      "View own profile information", 
                      PermissionCategory.PROFILE, PermissionLevel.READ),
            Permission("update_own_profile", "Update Own Profile", 
                      "Update own profile information", 
                      PermissionCategory.PROFILE, PermissionLevel.WRITE),
            
            # Patient permissions
            Permission("view_patient_profile", "View Patient Profile", 
                      "View patient profiles and basic information", 
                      PermissionCategory.PATIENTS, PermissionLevel.READ),
            Permission("update_patient_profile", "Update Patient Profile", 
                      "Update patient profile information", 
                      PermissionCategory.PATIENTS, PermissionLevel.WRITE),
            Permission("view_patient_basic_info", "View Patient Basic Info", 
                      "View basic patient contact information", 
                      PermissionCategory.PATIENTS, PermissionLevel.READ),
            Permission("update_patient_contact_info", "Update Patient Contact", 
                      "Update patient contact information", 
                      PermissionCategory.PATIENTS, PermissionLevel.WRITE),
            
            # Medical Records permissions
            Permission("view_patient_medical_records", "View Medical Records", 
                      "View patient medical records and history", 
                      PermissionCategory.MEDICAL_RECORDS, PermissionLevel.READ, 
                      is_sensitive=True),
            Permission("create_medical_record", "Create Medical Record", 
                      "Create new medical records", 
                      PermissionCategory.MEDICAL_RECORDS, PermissionLevel.WRITE, 
                      is_sensitive=True),
            Permission("update_patient_vitals", "Update Patient Vitals", 
                      "Update patient vital signs and measurements", 
                      PermissionCategory.MEDICAL_RECORDS, PermissionLevel.WRITE),
            
            # Appointment permissions
            Permission("view_own_appointments", "View Own Appointments", 
                      "View own appointments", 
                      PermissionCategory.APPOINTMENTS, PermissionLevel.READ),
            Permission("book_appointment", "Book Appointment", 
                      "Book new appointments", 
                      PermissionCategory.APPOINTMENTS, PermissionLevel.WRITE),
            Permission("cancel_own_appointment", "Cancel Own Appointment", 
                      "Cancel own appointments", 
                      PermissionCategory.APPOINTMENTS, PermissionLevel.WRITE),
            Permission("view_appointments", "View All Appointments", 
                      "View all appointments in the system", 
                      PermissionCategory.APPOINTMENTS, PermissionLevel.READ),
            Permission("manage_appointments", "Manage Appointments", 
                      "Create, update, and cancel any appointments", 
                      PermissionCategory.APPOINTMENTS, PermissionLevel.WRITE),
            Permission("schedule_appointments", "Schedule Appointments", 
                      "Schedule appointments for patients", 
                      PermissionCategory.APPOINTMENTS, PermissionLevel.WRITE),
            Permission("cancel_appointments", "Cancel Appointments", 
                      "Cancel patient appointments", 
                      PermissionCategory.APPOINTMENTS, PermissionLevel.WRITE),
            
            # Prescription permissions
            Permission("prescribe_medication", "Prescribe Medication", 
                      "Prescribe medications to patients", 
                      PermissionCategory.PRESCRIPTIONS, PermissionLevel.WRITE, 
                      is_sensitive=True, requires_mfa=True),
            Permission("administer_medication", "Administer Medication", 
                      "Administer prescribed medications", 
                      PermissionCategory.PRESCRIPTIONS, PermissionLevel.WRITE),
            Permission("order_tests", "Order Tests", 
                      "Order medical tests and procedures", 
                      PermissionCategory.MEDICAL_RECORDS, PermissionLevel.WRITE),
            
            # Administration permissions
            Permission("manage_users", "Manage Users", 
                      "Create, update, and manage system users", 
                      PermissionCategory.ADMINISTRATION, PermissionLevel.ADMIN, 
                      is_sensitive=True, requires_mfa=True),
            Permission("system_configuration", "System Configuration", 
                      "Configure system settings and parameters", 
                      PermissionCategory.ADMINISTRATION, PermissionLevel.ADMIN, 
                      is_sensitive=True, requires_mfa=True),
            Permission("view_audit_logs", "View Audit Logs", 
                      "View system audit logs and security events", 
                      PermissionCategory.ADMINISTRATION, PermissionLevel.READ, 
                      is_sensitive=True),
            Permission("manage_roles", "Manage Roles", 
                      "Manage user roles and permissions", 
                      PermissionCategory.ADMINISTRATION, PermissionLevel.ADMIN, 
                      is_sensitive=True, requires_mfa=True),
            
            # Billing permissions
            Permission("view_billing", "View Billing", 
                      "View billing information and invoices", 
                      PermissionCategory.BILLING, PermissionLevel.READ),
            Permission("manage_billing", "Manage Billing", 
                      "Create and manage billing records", 
                      PermissionCategory.BILLING, PermissionLevel.WRITE),
            
            # Reports permissions
            Permission("view_reports", "View Reports", 
                      "View system reports and analytics", 
                      PermissionCategory.REPORTS, PermissionLevel.READ),
            Permission("generate_reports", "Generate Reports", 
                      "Generate custom reports", 
                      PermissionCategory.REPORTS, PermissionLevel.WRITE),
        ]
        
        return {perm.code: perm for perm in permissions}
    
    def _define_role_permissions(self) -> Dict[str, List[str]]:
        """Define permissions for each role"""
        return {
            'patient': [
                'view_own_profile',
                'update_own_profile',
                'view_own_appointments',
                'book_appointment',
                'cancel_own_appointment'
            ],
            'patient_guardian': [
                'view_own_profile',
                'update_own_profile',
                'view_own_appointments',
                'book_appointment',
                'cancel_own_appointment',
                'view_patient_profile',  # For their dependents
                'update_patient_contact_info'  # For their dependents
            ],
            'physician': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'update_patient_profile',
                'view_patient_medical_records',
                'create_medical_record',
                'prescribe_medication',
                'order_tests',
                'view_appointments',
                'manage_appointments',
                'view_billing',
                'view_reports'
            ],
            'nurse': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'update_patient_vitals',
                'view_patient_medical_records',
                'administer_medication',
                'view_appointments',
                'schedule_appointments'
            ],
            'nurse_practitioner': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'update_patient_profile',
                'view_patient_medical_records',
                'create_medical_record',
                'update_patient_vitals',
                'prescribe_medication',
                'order_tests',
                'administer_medication',
                'view_appointments',
                'manage_appointments'
            ],
            'physician_assistant': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'update_patient_profile',
                'view_patient_medical_records',
                'create_medical_record',
                'update_patient_vitals',
                'prescribe_medication',
                'order_tests',
                'view_appointments',
                'manage_appointments'
            ],
            'therapist': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'view_patient_medical_records',
                'create_medical_record',
                'update_patient_vitals',
                'view_appointments',
                'manage_appointments'
            ],
            'technician': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_basic_info',
                'update_patient_vitals',
                'view_appointments'
            ],
            'receptionist': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_basic_info',
                'update_patient_contact_info',
                'schedule_appointments',
                'cancel_appointments',
                'view_appointments',
                'view_billing'
            ],
            'billing_specialist': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_basic_info',
                'view_billing',
                'manage_billing',
                'view_reports'
            ],
            'medical_records_clerk': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'update_patient_contact_info',
                'view_patient_medical_records',
                'create_medical_record'
            ],
            'practice_manager': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'update_patient_profile',
                'view_patient_medical_records',
                'view_appointments',
                'manage_appointments',
                'schedule_appointments',
                'cancel_appointments',
                'view_billing',
                'manage_billing',
                'view_reports',
                'generate_reports',
                'manage_users'  # Limited user management
            ],
            'system_admin': [
                # System admins get all permissions
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'update_patient_profile',
                'view_patient_basic_info',
                'update_patient_contact_info',
                'view_patient_medical_records',
                'create_medical_record',
                'update_patient_vitals',
                'view_own_appointments',
                'book_appointment',
                'cancel_own_appointment',
                'view_appointments',
                'manage_appointments',
                'schedule_appointments',
                'cancel_appointments',
                'prescribe_medication',
                'administer_medication',
                'order_tests',
                'view_billing',
                'manage_billing',
                'view_reports',
                'generate_reports',
                'manage_users',
                'system_configuration',
                'view_audit_logs',
                'manage_roles'
            ],
            'security_officer': [
                'view_own_profile',
                'update_own_profile',
                'view_audit_logs',
                'view_reports',
                'generate_reports',
                'system_configuration'  # Security-related configs only
            ],
            'compliance_officer': [
                'view_own_profile',
                'update_own_profile',
                'view_patient_profile',
                'view_patient_medical_records',
                'view_audit_logs',
                'view_reports',
                'generate_reports'
            ]
        }
    
    def _define_role_hierarchy(self) -> Dict[str, List[str]]:
        """Define role hierarchy for inheritance"""
        return {
            'system_admin': ['security_officer', 'compliance_officer', 'practice_manager'],
            'practice_manager': ['billing_specialist', 'medical_records_clerk', 'receptionist'],
            'physician': ['nurse_practitioner', 'physician_assistant'],
            'nurse_practitioner': ['nurse'],
            'physician_assistant': ['nurse'],
            'patient_guardian': ['patient']
        }
    
    def get_role_permissions(self, role: str) -> List[str]:
        """Get all permissions for a role"""
        if role not in self._role_permissions:
            return []
        
        permissions = set(self._role_permissions[role])
        
        # Add inherited permissions from role hierarchy
        for parent_role, child_roles in self._role_hierarchy.items():
            if role in child_roles:
                permissions.update(self._role_permissions.get(parent_role, []))
        
        return list(permissions)
    
    def has_permission(self, role: str, permission_code: str) -> bool:
        """Check if a role has a specific permission"""
        role_permissions = self.get_role_permissions(role)
        return permission_code in role_permissions
    
    def get_role_level(self, role: str) -> int:
        """Get the hierarchy level of a role (higher number = higher authority)"""
        # Define role levels based on hierarchy
        role_levels = {
            # Top level administrators
            'system_admin': 100,
            'security_officer': 90,
            'compliance_officer': 90,
            
            # Management level
            'practice_manager': 80,
            
            # Department specialists
            'billing_specialist': 60,
            'medical_records_clerk': 60,
            'receptionist': 50,
            
            # Medical professionals
            'physician': 70,
            'nurse_practitioner': 65,
            'physician_assistant': 65,
            'nurse': 60,
            'therapist': 55,
            'technician': 45,
            
            # Patients and guardians
            'patient_guardian': 20,
            'patient': 10
        }
        
        return role_levels.get(role, 0)
    
    def get_permission_details(self, permission_code: str) -> Optional[Permission]:
        """Get detailed information about a permission"""
        return self._permissions.get(permission_code)
    
    def get_permissions_by_category(self, category: PermissionCategory) -> List[Permission]:
        """Get all permissions in a category"""
        return [perm for perm in self._permissions.values() if perm.category == category]
    
    def get_sensitive_permissions(self) -> List[Permission]:
        """Get all sensitive permissions that require special handling"""
        return [perm for perm in self._permissions.values() if perm.is_sensitive]
    
    def get_mfa_required_permissions(self) -> List[Permission]:
        """Get all permissions that require MFA"""
        return [perm for perm in self._permissions.values() if perm.requires_mfa]
    
    def validate_role(self, role: str) -> bool:
        """Validate if a role exists"""
        return role in self._role_permissions
    
    def get_all_roles(self) -> List[str]:
        """Get list of all available roles"""
        return list(self._role_permissions.keys())
    
    def get_all_permissions(self) -> List[str]:
        """Get list of all permission codes"""
        return list(self._permissions.keys())
    
    def get_detailed_permissions(self, role: str) -> Dict:
        """Get detailed permissions with categories and descriptions for a role"""
        permissions = self.get_role_permissions(role)
        
        detailed_permissions = {
            'permissions': permissions,
            'role': role,
            'categories': {},
            'details': {}
        }
        
        # Group permissions by category
        for permission_code in permissions:
            permission = self._permissions.get(permission_code)
            if permission:
                category = permission.category.value
                
                if category not in detailed_permissions['categories']:
                    detailed_permissions['categories'][category] = []
                
                detailed_permissions['categories'][category].append(permission_code)
                detailed_permissions['details'][permission_code] = {
                    'name': permission.name,
                    'description': permission.description,
                    'category': category,
                    'level': permission.level.value,
                    'is_sensitive': permission.is_sensitive,
                    'requires_mfa': permission.requires_mfa,
                    'requires_justification': permission.requires_justification
                }
        
        return detailed_permissions


# Global instance - single source of truth
PERMISSIONS_CONFIG = PermissionsConfig()


# Convenience functions for backward compatibility
def get_role_permissions(role: str) -> List[str]:
    """Get permissions for a role"""
    return PERMISSIONS_CONFIG.get_role_permissions(role)


def has_permission(role: str, permission_code: str) -> bool:
    """Check if role has permission"""
    return PERMISSIONS_CONFIG.has_permission(role, permission_code)


def get_detailed_permissions(role: str) -> Dict:
    """Get detailed permissions for a role"""
    return PERMISSIONS_CONFIG.get_detailed_permissions(role)


# Export commonly used constants
ROLE_CHOICES = [
    # Patient Roles
    ('patient', 'Patient'),
    ('patient_guardian', 'Patient Guardian'),
    
    # Clinical Staff
    ('physician', 'Physician'),
    ('nurse', 'Nurse'),
    ('nurse_practitioner', 'Nurse Practitioner'),
    ('physician_assistant', 'Physician Assistant'),
    ('therapist', 'Therapist'),
    ('technician', 'Medical Technician'),
    
    # Administrative Staff
    ('receptionist', 'Receptionist'),
    ('billing_specialist', 'Billing Specialist'),
    ('medical_records_clerk', 'Medical Records Clerk'),
    ('practice_manager', 'Practice Manager'),
    
    # System Roles
    ('system_admin', 'System Administrator'),
    ('security_officer', 'Security Officer'),
    ('compliance_officer', 'Compliance Officer'),
]