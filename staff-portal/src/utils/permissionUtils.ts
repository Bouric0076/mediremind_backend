/**
 * Frontend Permission Utilities
 * ============================
 * 
 * This module provides frontend utilities for permission checking that sync
 * with the backend centralized permission configuration.
 */

// Permission types that match backend configuration
export const PermissionLevel = {
  READ: 'read',
  WRITE: 'write',
  ADMIN: 'admin'
} as const;

export type PermissionLevel = typeof PermissionLevel[keyof typeof PermissionLevel];

export const PermissionCategory = {
  PROFILE: 'profile',
  PATIENTS: 'patients',
  APPOINTMENTS: 'appointments',
  MEDICAL_RECORDS: 'medical_records',
  PRESCRIPTIONS: 'prescriptions',
  ADMINISTRATION: 'administration',
  BILLING: 'billing',
  REPORTS: 'reports'
} as const;

export type PermissionCategory = typeof PermissionCategory[keyof typeof PermissionCategory];

export interface Permission {
  code: string;
  name: string;
  description: string;
  category: PermissionCategory;
  level: PermissionLevel;
  is_sensitive?: boolean;
  requires_mfa?: boolean;
}

export interface DetailedPermissions {
  permissions: string[];
  role: string;
  categories: Record<string, string[]>;
  details: Record<string, Permission>;
}

// Role definitions that match backend
export const ROLE_CHOICES = [
  // Patient Roles
  { value: 'patient', label: 'Patient' },
  { value: 'patient_guardian', label: 'Patient Guardian' },
  
  // Clinical Staff
  { value: 'physician', label: 'Physician' },
  { value: 'nurse', label: 'Nurse' },
  { value: 'nurse_practitioner', label: 'Nurse Practitioner' },
  { value: 'physician_assistant', label: 'Physician Assistant' },
  { value: 'therapist', label: 'Therapist' },
  { value: 'technician', label: 'Medical Technician' },
  
  // Administrative Staff
  { value: 'receptionist', label: 'Receptionist' },
  { value: 'billing_specialist', label: 'Billing Specialist' },
  { value: 'medical_records_clerk', label: 'Medical Records Clerk' },
  { value: 'practice_manager', label: 'Practice Manager' },
  
  // System Roles
  { value: 'system_admin', label: 'System Administrator' },
  { value: 'security_officer', label: 'Security Officer' },
  { value: 'compliance_officer', label: 'Compliance Officer' },
] as const;

export type UserRole = typeof ROLE_CHOICES[number]['value'];

// Permission checking utilities
export class PermissionChecker {
  private userPermissions: string[] = [];
  private userRole: string = '';
  private detailedPermissions: DetailedPermissions | null = null;

  constructor(permissions: string[] = [], role: string = '') {
    this.userPermissions = permissions;
    this.userRole = role;
  }

  /**
   * Update user permissions and role
   */
  updatePermissions(permissions: string[], role: string, detailed?: DetailedPermissions) {
    this.userPermissions = permissions;
    this.userRole = role;
    this.detailedPermissions = detailed || null;
  }

  /**
   * Check if user has a specific permission
   */
  hasPermission(permissionCode: string): boolean {
    return this.userPermissions.includes(permissionCode);
  }

  /**
   * Check if user has any of the specified permissions
   */
  hasAnyPermission(permissionCodes: string[]): boolean {
    return permissionCodes.some(code => this.hasPermission(code));
  }

  /**
   * Check if user has all of the specified permissions
   */
  hasAllPermissions(permissionCodes: string[]): boolean {
    return permissionCodes.every(code => this.hasPermission(code));
  }

  /**
   * Check if user has a specific role
   */
  hasRole(role: string): boolean {
    return this.userRole === role;
  }

  /**
   * Check if user has any of the specified roles
   */
  hasAnyRole(roles: string[]): boolean {
    return roles.includes(this.userRole);
  }

  /**
   * Get permissions by category
   */
  getPermissionsByCategory(category: PermissionCategory): string[] {
    if (!this.detailedPermissions) return [];
    return this.detailedPermissions.categories[category] || [];
  }

  /**
   * Get permission details
   */
  getPermissionDetails(permissionCode: string): Permission | null {
    if (!this.detailedPermissions) return null;
    return this.detailedPermissions.details[permissionCode] || null;
  }

  /**
   * Check if permission requires MFA
   */
  requiresMFA(permissionCode: string): boolean {
    const details = this.getPermissionDetails(permissionCode);
    return details?.requires_mfa || false;
  }

  /**
   * Check if permission is sensitive
   */
  isSensitive(permissionCode: string): boolean {
    const details = this.getPermissionDetails(permissionCode);
    return details?.is_sensitive || false;
  }

  /**
   * Get all permissions for current role
   */
  getAllPermissions(): string[] {
    return [...this.userPermissions];
  }

  /**
   * Get current user role
   */
  getRole(): string {
    return this.userRole;
  }

  /**
   * Get role hierarchy level (for comparison)
   */
  getRoleLevel(): number {
    const roleLevels: Record<string, number> = {
      'patient': 1,
      'patient_guardian': 2,
      'receptionist': 10,
      'medical_records_clerk': 15,
      'billing_specialist': 20,
      'technician': 25,
      'nurse': 30,
      'therapist': 35,
      'physician_assistant': 40,
      'nurse_practitioner': 45,
      'physician': 50,
      'practice_manager': 60,
      'compliance_officer': 70,
      'security_officer': 80,
      'system_admin': 100
    };
    return roleLevels[this.userRole] || 0;
  }

  /**
   * Check if user has higher or equal role level
   */
  hasRoleLevel(minimumLevel: number): boolean {
    return this.getRoleLevel() >= minimumLevel;
  }

  /**
   * Get all available roles
   */
  getAllRoles(): UserRole[] {
    return ROLE_CHOICES.map(role => role.value);
  }

  /**
   * Get permissions for a specific role
   */
  getRolePermissions(role: UserRole): string[] {
    // This would typically come from backend configuration
    // For now, return empty array as this needs backend integration
    if (!this.detailedPermissions) return [];
    
    // If we have detailed permissions for the current user's role and it matches
    if (this.detailedPermissions.role === role) {
      return this.detailedPermissions.permissions;
    }
    
    // Otherwise return empty array - this should be populated from backend
    return [];
  }

  /**
   * Check if one role is higher or equal to another
   */
  isRoleHigherOrEqual(role1: UserRole, role2: UserRole): boolean {
    const roleLevels: Record<string, number> = {
      'patient': 1,
      'patient_guardian': 2,
      'receptionist': 10,
      'medical_records_clerk': 15,
      'billing_specialist': 20,
      'technician': 25,
      'nurse': 30,
      'therapist': 35,
      'physician_assistant': 40,
      'nurse_practitioner': 45,
      'physician': 50,
      'practice_manager': 60,
      'compliance_officer': 70,
      'security_officer': 80,
      'system_admin': 100
    };
    
    const level1 = roleLevels[role1] || 0;
    const level2 = roleLevels[role2] || 0;
    
    return level1 >= level2;
  }
}

// Global permission checker instance
export const permissionChecker = new PermissionChecker();

// Convenience functions
export const hasPermission = (permissionCode: string): boolean => {
  return permissionChecker.hasPermission(permissionCode);
};

export const hasAnyPermission = (permissionCodes: string[]): boolean => {
  return permissionChecker.hasAnyPermission(permissionCodes);
};

export const hasAllPermissions = (permissionCodes: string[]): boolean => {
  return permissionChecker.hasAllPermissions(permissionCodes);
};

export const hasRole = (role: string): boolean => {
  return permissionChecker.hasRole(role);
};

export const hasAnyRole = (roles: string[]): boolean => {
  return permissionChecker.hasAnyRole(roles);
};

export const requiresMFA = (permissionCode: string): boolean => {
  return permissionChecker.requiresMFA(permissionCode);
};

export const isSensitive = (permissionCode: string): boolean => {
  return permissionChecker.isSensitive(permissionCode);
};

// Permission constants for common checks
export const PERMISSIONS = {
  // Profile permissions
  VIEW_OWN_PROFILE: 'view_own_profile',
  UPDATE_OWN_PROFILE: 'update_own_profile',
  
  // Patient permissions
  VIEW_PATIENT_PROFILE: 'view_patient_profile',
  UPDATE_PATIENT_PROFILE: 'update_patient_profile',
  VIEW_PATIENT_BASIC_INFO: 'view_patient_basic_info',
  UPDATE_PATIENT_CONTACT_INFO: 'update_patient_contact_info',
  
  // Medical records permissions
  VIEW_PATIENT_MEDICAL_RECORDS: 'view_patient_medical_records',
  CREATE_MEDICAL_RECORD: 'create_medical_record',
  UPDATE_PATIENT_VITALS: 'update_patient_vitals',
  
  // Appointment permissions
  VIEW_OWN_APPOINTMENTS: 'view_own_appointments',
  BOOK_APPOINTMENT: 'book_appointment',
  CANCEL_OWN_APPOINTMENT: 'cancel_own_appointment',
  VIEW_APPOINTMENTS: 'view_appointments',
  MANAGE_APPOINTMENTS: 'manage_appointments',
  SCHEDULE_APPOINTMENTS: 'schedule_appointments',
  CANCEL_APPOINTMENTS: 'cancel_appointments',
  
  // Prescription permissions
  PRESCRIBE_MEDICATION: 'prescribe_medication',
  ADMINISTER_MEDICATION: 'administer_medication',
  ORDER_TESTS: 'order_tests',
  
  // Administration permissions
  MANAGE_USERS: 'manage_users',
  SYSTEM_CONFIGURATION: 'system_configuration',
  VIEW_AUDIT_LOGS: 'view_audit_logs',
  MANAGE_ROLES: 'manage_roles',
  
  // Billing permissions
  VIEW_BILLING: 'view_billing',
  MANAGE_BILLING: 'manage_billing',
  
  // Reports permissions
  VIEW_REPORTS: 'view_reports',
  GENERATE_REPORTS: 'generate_reports',
} as const;

export type PermissionCode = typeof PERMISSIONS[keyof typeof PERMISSIONS];