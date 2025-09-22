/**
 * Frontend permission validation utilities
 * Ensures consistency between frontend and backend permission systems
 */

import { permissionChecker, UserRole, Permission, DetailedPermissions } from './permissionUtils';

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  info: string[];
}

export interface PermissionSyncData {
  permissions: Permission[];
  roles: UserRole[];
  rolePermissions: Record<UserRole, Permission[]>;
  detailedPermissions: Record<UserRole, DetailedPermissions>;
}

export class PermissionValidator {
  private static instance: PermissionValidator;
  private backendSyncData: PermissionSyncData | null = null;

  public static getInstance(): PermissionValidator {
    if (!PermissionValidator.instance) {
      PermissionValidator.instance = new PermissionValidator();
    }
    return PermissionValidator.instance;
  }

  /**
   * Sync permission data from backend
   */
  public async syncWithBackend(): Promise<ValidationResult> {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      info: []
    };

    try {
      // Fetch permission data from backend API
      const response = await fetch('/api/permissions/sync/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || sessionStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        result.errors.push(`Failed to fetch backend permissions: ${response.statusText}`);
        result.isValid = false;
        return result;
      }

      this.backendSyncData = await response.json();
      result.info.push('Successfully synced with backend permissions');

      // Validate sync data
      const syncValidation = this.validateSyncData();
      result.errors.push(...syncValidation.errors);
      result.warnings.push(...syncValidation.warnings);
      result.info.push(...syncValidation.info);

      if (syncValidation.errors.length > 0) {
        result.isValid = false;
      }

    } catch (error) {
      result.errors.push(`Error syncing with backend: ${error instanceof Error ? error.message : 'Unknown error'}`);
      result.isValid = false;
    }

    return result;
  }

  /**
   * Validate frontend permission configuration
   */
  public validateFrontendConfig(): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      info: []
    };

    try {
      // Validate permission checker initialization
      if (!permissionChecker) {
        result.errors.push('Permission checker not initialized');
        result.isValid = false;
        return result;
      }

      // Validate permission structure
      const permissions = permissionChecker.getAllPermissions();
      const roles = permissionChecker.getAllRoles();

      result.info.push(`Frontend permissions count: ${permissions.length}`);
      result.info.push(`Frontend roles count: ${roles.length}`);

      // Check for duplicate permissions
      const permissionCodes = permissions.map(p => p);
      const duplicates = permissionCodes.filter((code, index) => permissionCodes.indexOf(code) !== index);
      if (duplicates.length > 0) {
        result.errors.push(`Duplicate permissions found: ${duplicates.join(', ')}`);
        result.isValid = false;
      }

      // Validate role hierarchy
      const hierarchyValidation = this.validateRoleHierarchy();
      result.errors.push(...hierarchyValidation.errors);
      result.warnings.push(...hierarchyValidation.warnings);

    } catch (error) {
      result.errors.push(`Error validating frontend config: ${error instanceof Error ? error.message : 'Unknown error'}`);
      result.isValid = false;
    }

    return result;
  }

  /**
   * Compare frontend and backend permissions
   */
  public compareWithBackend(): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      info: []
    };

    if (!this.backendSyncData) {
      result.errors.push('No backend sync data available. Run syncWithBackend() first.');
      result.isValid = false;
      return result;
    }

    try {
      const frontendPermissions = new Set(permissionChecker.getAllPermissions());
      const backendPermissions = new Set(this.backendSyncData.permissions);

      // Check for missing permissions in frontend
      const missingInFrontend = Array.from(backendPermissions).filter(p => !frontendPermissions.has(p));
      if (missingInFrontend.length > 0) {
        result.errors.push(`Permissions missing in frontend: ${missingInFrontend.join(', ')}`);
        result.isValid = false;
      }

      // Check for extra permissions in frontend
      const extraInFrontend = Array.from(frontendPermissions).filter(p => !backendPermissions.has(p));
      if (extraInFrontend.length > 0) {
        result.warnings.push(`Extra permissions in frontend: ${extraInFrontend.join(', ')}`);
      }

      // Compare role permissions
      const roleComparison = this.compareRolePermissions();
      result.errors.push(...roleComparison.errors);
      result.warnings.push(...roleComparison.warnings);
      result.info.push(...roleComparison.info);

      if (roleComparison.errors.length > 0) {
        result.isValid = false;
      }

    } catch (error) {
      result.errors.push(`Error comparing with backend: ${error instanceof Error ? error.message : 'Unknown error'}`);
      result.isValid = false;
    }

    return result;
  }

  /**
   * Validate user permissions against their role
   */
  public validateUserPermissions(userRole: UserRole, userPermissions: Permission[]): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      info: []
    };

    try {
      const expectedPermissions = permissionChecker.getRolePermissions(userRole);
      const userPermSet = new Set(userPermissions);
      const expectedPermSet = new Set(expectedPermissions);

      // Check for missing permissions
      const missing = Array.from(expectedPermSet).filter(p => !userPermSet.has(p));
      if (missing.length > 0) {
        result.errors.push(`User missing expected permissions for role ${userRole}: ${missing.join(', ')}`);
        result.isValid = false;
      }

      // Check for extra permissions
      const extra = Array.from(userPermSet).filter(p => !expectedPermSet.has(p));
      if (extra.length > 0) {
        result.warnings.push(`User has extra permissions beyond role ${userRole}: ${extra.join(', ')}`);
      }

      result.info.push(`User permissions validated for role: ${userRole}`);

    } catch (error) {
      result.errors.push(`Error validating user permissions: ${error instanceof Error ? error.message : 'Unknown error'}`);
      result.isValid = false;
    }

    return result;
  }

  /**
   * Run comprehensive validation
   */
  public async runFullValidation(): Promise<ValidationResult> {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      info: []
    };

    // Validate frontend configuration
    const frontendValidation = this.validateFrontendConfig();
    result.errors.push(...frontendValidation.errors);
    result.warnings.push(...frontendValidation.warnings);
    result.info.push(...frontendValidation.info);

    // Sync with backend
    const syncResult = await this.syncWithBackend();
    result.errors.push(...syncResult.errors);
    result.warnings.push(...syncResult.warnings);
    result.info.push(...syncResult.info);

    // Compare with backend if sync was successful
    if (syncResult.isValid) {
      const comparisonResult = this.compareWithBackend();
      result.errors.push(...comparisonResult.errors);
      result.warnings.push(...comparisonResult.warnings);
      result.info.push(...comparisonResult.info);
    }

    // Determine overall validity
    result.isValid = result.errors.length === 0;

    return result;
  }

  /**
   * Generate validation report
   */
  public generateReport(validationResult: ValidationResult): string {
    const lines: string[] = [];
    
    lines.push('='.repeat(60));
    lines.push('FRONTEND PERMISSION VALIDATION REPORT');
    lines.push('='.repeat(60));
    
    if (validationResult.errors.length > 0) {
      lines.push(`\nERRORS (${validationResult.errors.length}):`);
      validationResult.errors.forEach(error => {
        lines.push(`  ✗ ${error}`);
      });
    }
    
    if (validationResult.warnings.length > 0) {
      lines.push(`\nWARNINGS (${validationResult.warnings.length}):`);
      validationResult.warnings.forEach(warning => {
        lines.push(`  ⚠ ${warning}`);
      });
    }
    
    if (validationResult.info.length > 0) {
      lines.push(`\nINFO (${validationResult.info.length}):`);
      validationResult.info.forEach(info => {
        lines.push(`  ℹ ${info}`);
      });
    }
    
    lines.push('\n' + '-'.repeat(60));
    lines.push('SUMMARY:');
    lines.push(`  Errors: ${validationResult.errors.length}`);
    lines.push(`  Warnings: ${validationResult.warnings.length}`);
    lines.push(`  Info: ${validationResult.info.length}`);
    lines.push(`  Status: ${validationResult.isValid ? 'PASSED ✓' : 'FAILED ✗'}`);
    lines.push('-'.repeat(60));
    
    return lines.join('\n');
  }

  private validateSyncData(): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      info: []
    };

    if (!this.backendSyncData) {
      result.errors.push('No sync data to validate');
      result.isValid = false;
      return result;
    }

    const { permissions, roles, rolePermissions } = this.backendSyncData;

    // Validate structure
    if (!Array.isArray(permissions)) {
      result.errors.push('Backend permissions is not an array');
      result.isValid = false;
    }

    if (!Array.isArray(roles)) {
      result.errors.push('Backend roles is not an array');
      result.isValid = false;
    }

    if (typeof rolePermissions !== 'object') {
      result.errors.push('Backend rolePermissions is not an object');
      result.isValid = false;
    }

    // Validate role permissions reference valid permissions
    for (const [role, perms] of Object.entries(rolePermissions)) {
      if (!Array.isArray(perms)) {
        result.errors.push(`Role ${role} permissions is not an array`);
        result.isValid = false;
        continue;
      }

      for (const perm of perms) {
        if (!permissions.includes(perm)) {
          result.errors.push(`Role ${role} references undefined permission: ${perm}`);
          result.isValid = false;
        }
      }
    }

    result.info.push(`Backend sync data validated: ${permissions.length} permissions, ${roles.length} roles`);

    return result;
  }

  private validateRoleHierarchy(): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      info: []
    };

    try {
      const roles = permissionChecker.getAllRoles();
      
      // Check role hierarchy consistency
      for (let i = 0; i < roles.length; i++) {
        for (let j = i + 1; j < roles.length; j++) {
          const role1 = roles[i];
          const role2 = roles[j];
          
          const isRole1Higher = permissionChecker.isRoleHigherOrEqual(role1, role2);
          const isRole2Higher = permissionChecker.isRoleHigherOrEqual(role2, role1);
          
          // At least one should be true (or they're equal)
          if (!isRole1Higher && !isRole2Higher) {
            result.warnings.push(`Roles ${role1} and ${role2} have unclear hierarchy relationship`);
          }
        }
      }

      result.info.push('Role hierarchy validation completed');

    } catch (error) {
      result.errors.push(`Error validating role hierarchy: ${error instanceof Error ? error.message : 'Unknown error'}`);
      result.isValid = false;
    }

    return result;
  }

  private compareRolePermissions(): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: [],
      info: []
    };

    if (!this.backendSyncData) {
      result.errors.push('No backend data for comparison');
      result.isValid = false;
      return result;
    }

    const frontendRoles = permissionChecker.getAllRoles();
    const backendRoles = this.backendSyncData.roles;

    // Check for role mismatches
    const frontendRoleSet = new Set(frontendRoles);
    const backendRoleSet = new Set(backendRoles);

    const missingRoles = backendRoles.filter(role => !frontendRoleSet.has(role));
    const extraRoles = frontendRoles.filter(role => !backendRoleSet.has(role));

    if (missingRoles.length > 0) {
      result.errors.push(`Roles missing in frontend: ${missingRoles.join(', ')}`);
      result.isValid = false;
    }

    if (extraRoles.length > 0) {
      result.warnings.push(`Extra roles in frontend: ${extraRoles.join(', ')}`);
    }

    // Compare permissions for each role
    for (const role of backendRoles) {
      if (frontendRoleSet.has(role)) {
        const frontendPerms = new Set(permissionChecker.getRolePermissions(role));
        const backendPerms = new Set(this.backendSyncData.rolePermissions[role] || []);

        const missingPerms = Array.from(backendPerms).filter(p => !frontendPerms.has(p));
        const extraPerms = Array.from(frontendPerms).filter(p => !backendPerms.has(p));

        if (missingPerms.length > 0) {
          result.errors.push(`Role ${role} missing permissions in frontend: ${missingPerms.join(', ')}`);
          result.isValid = false;
        }

        if (extraPerms.length > 0) {
          result.warnings.push(`Role ${role} has extra permissions in frontend: ${extraPerms.join(', ')}`);
        }
      }
    }

    result.info.push('Role permission comparison completed');

    return result;
  }
}

// Export singleton instance
export const permissionValidator = PermissionValidator.getInstance();

// Utility functions for easy access
export const validatePermissions = () => permissionValidator.runFullValidation();
export const syncPermissions = () => permissionValidator.syncWithBackend();
export const validateUserPermissions = (role: UserRole, permissions: Permission[]) => 
  permissionValidator.validateUserPermissions(role, permissions);
export const generateValidationReport = (result: ValidationResult) => 
  permissionValidator.generateReport(result);