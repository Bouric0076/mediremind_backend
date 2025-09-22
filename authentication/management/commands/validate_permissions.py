"""
Django management command to validate permission consistency
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from authentication.permissions_config import PERMISSIONS_CONFIG
from authentication.services import PermissionService
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Validate permission consistency across the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix inconsistencies automatically',
        )
        parser.add_argument(
            '--role',
            type=str,
            help='Validate permissions for a specific role only',
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Export validation results to JSON file',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting permission validation...')
        )
        
        validation_results = {
            'errors': [],
            'warnings': [],
            'info': [],
            'summary': {}
        }
        
        # Validate permission configuration
        self._validate_permission_config(validation_results)
        
        # Validate role permissions
        self._validate_role_permissions(validation_results, options.get('role'))
        
        # Validate user permissions
        self._validate_user_permissions(validation_results)
        
        # Check for orphaned permissions
        self._check_orphaned_permissions(validation_results)
        
        # Generate summary
        self._generate_summary(validation_results)
        
        # Display results
        self._display_results(validation_results)
        
        # Export results if requested
        if options.get('export'):
            self._export_results(validation_results, options['export'])
        
        # Fix issues if requested
        if options.get('fix'):
            self._fix_issues(validation_results)

    def _validate_permission_config(self, results):
        """Validate the centralized permission configuration"""
        self.stdout.write('Validating permission configuration...')
        
        try:
            # Check if all permissions have required fields
            for perm_code, permission in PERMISSIONS_CONFIG._permissions.items():
                if not permission.code:
                    results['errors'].append(f"Permission {perm_code} missing code")
                if not permission.name:
                    results['errors'].append(f"Permission {perm_code} missing name")
                if not permission.description:
                    results['warnings'].append(f"Permission {perm_code} missing description")
                if not permission.category:
                    results['errors'].append(f"Permission {perm_code} missing category")
                if not permission.level:
                    results['errors'].append(f"Permission {perm_code} missing level")
            
            # Check for duplicate permission codes
            permission_codes = list(PERMISSIONS_CONFIG._permissions.keys())
            duplicates = set([x for x in permission_codes if permission_codes.count(x) > 1])
            if duplicates:
                results['errors'].extend([f"Duplicate permission code: {code}" for code in duplicates])
            
            results['info'].append(f"Total permissions defined: {len(PERMISSIONS_CONFIG._permissions)}")
            
        except Exception as e:
            results['errors'].append(f"Error validating permission config: {str(e)}")

    def _validate_role_permissions(self, results, specific_role=None):
        """Validate role permission assignments"""
        self.stdout.write('Validating role permissions...')
        
        try:
            roles_to_check = [specific_role] if specific_role else PERMISSIONS_CONFIG._role_permissions.keys()
            
            for role in roles_to_check:
                if role not in PERMISSIONS_CONFIG._role_permissions:
                    results['errors'].append(f"Role {role} not found in configuration")
                    continue
                
                role_permissions = PERMISSIONS_CONFIG.get_role_permissions(role)
                
                # Check if all assigned permissions exist
                for perm_code in role_permissions:
                    if perm_code not in PERMISSIONS_CONFIG._permissions:
                        results['errors'].append(f"Role {role} has undefined permission: {perm_code}")
                
                # Check role hierarchy consistency
                self._check_role_hierarchy(role, results)
                
                results['info'].append(f"Role {role}: {len(role_permissions)} permissions")
                
        except Exception as e:
            results['errors'].append(f"Error validating role permissions: {str(e)}")

    def _validate_user_permissions(self, results):
        """Validate user permission assignments"""
        self.stdout.write('Validating user permissions...')
        
        try:
            permission_service = PermissionService()
            users_checked = 0
            
            for user in User.objects.filter(is_active=True):
                if hasattr(user, 'role'):
                    user_permissions = permission_service.get_user_permissions(user)
                    expected_permissions = PERMISSIONS_CONFIG.get_role_permissions(user.role)
                    
                    # Check for missing permissions
                    missing = set(expected_permissions) - set(user_permissions)
                    if missing:
                        results['warnings'].append(
                            f"User {user.email} missing permissions: {', '.join(missing)}"
                        )
                    
                    # Check for extra permissions
                    extra = set(user_permissions) - set(expected_permissions)
                    if extra:
                        results['info'].append(
                            f"User {user.email} has extra permissions: {', '.join(extra)}"
                        )
                    
                    users_checked += 1
            
            results['info'].append(f"Users validated: {users_checked}")
            
        except Exception as e:
            results['errors'].append(f"Error validating user permissions: {str(e)}")

    def _check_orphaned_permissions(self, results):
        """Check for permissions not assigned to any role"""
        self.stdout.write('Checking for orphaned permissions...')
        
        try:
            all_permissions = set(PERMISSIONS_CONFIG._permissions.keys())
            assigned_permissions = set()
            
            for role_perms in PERMISSIONS_CONFIG._role_permissions.values():
                assigned_permissions.update(role_perms)
            
            orphaned = all_permissions - assigned_permissions
            if orphaned:
                results['warnings'].extend([
                    f"Orphaned permission (not assigned to any role): {perm}" 
                    for perm in orphaned
                ])
            
        except Exception as e:
            results['errors'].append(f"Error checking orphaned permissions: {str(e)}")

    def _check_role_hierarchy(self, role, results):
        """Check role hierarchy consistency"""
        try:
            role_level = PERMISSIONS_CONFIG.get_role_level(role)
            role_permissions = set(PERMISSIONS_CONFIG.get_role_permissions(role))
            
            # Check if higher-level roles have at least the same permissions as lower-level roles
            # Get all roles and their levels
            all_roles = list(PERMISSIONS_CONFIG._role_permissions.keys())
            
            for other_role in all_roles:
                if other_role == role:
                    continue
                    
                other_level = PERMISSIONS_CONFIG.get_role_level(other_role)
                
                # If current role has higher level, it should have at least the same permissions as lower role
                if role_level > other_level:  # Current role is higher level
                    other_permissions = set(PERMISSIONS_CONFIG.get_role_permissions(other_role))
                    missing_from_higher = other_permissions - role_permissions
                    
                    if missing_from_higher:
                        results['warnings'].append(
                            f"Higher role {role} (level {role_level}) missing permissions from lower role {other_role} (level {other_level}): "
                            f"{', '.join(missing_from_higher)}"
                        )
                        
        except Exception as e:
            results['warnings'].append(f"Error checking role hierarchy for {role}: {str(e)}")

    def _generate_summary(self, results):
        """Generate validation summary"""
        results['summary'] = {
            'total_errors': len(results['errors']),
            'total_warnings': len(results['warnings']),
            'total_info': len(results['info']),
            'validation_passed': len(results['errors']) == 0
        }

    def _display_results(self, results):
        """Display validation results"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('PERMISSION VALIDATION RESULTS'))
        self.stdout.write('='*60)
        
        # Display errors
        if results['errors']:
            self.stdout.write(self.style.ERROR(f"\nERRORS ({len(results['errors'])}):"))
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(f"  ✗ {error}"))
        
        # Display warnings
        if results['warnings']:
            self.stdout.write(self.style.WARNING(f"\nWARNINGS ({len(results['warnings'])}):"))
            for warning in results['warnings']:
                self.stdout.write(self.style.WARNING(f"  ⚠ {warning}"))
        
        # Display info
        if results['info']:
            self.stdout.write(f"\nINFO ({len(results['info'])}):")
            for info in results['info']:
                self.stdout.write(f"  ℹ {info}")
        
        # Display summary
        summary = results['summary']
        self.stdout.write('\n' + '-'*60)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f"  Errors: {summary['total_errors']}")
        self.stdout.write(f"  Warnings: {summary['total_warnings']}")
        self.stdout.write(f"  Info: {summary['total_info']}")
        
        if summary['validation_passed']:
            self.stdout.write(self.style.SUCCESS("  Status: PASSED ✓"))
        else:
            self.stdout.write(self.style.ERROR("  Status: FAILED ✗"))
        
        self.stdout.write('-'*60)

    def _export_results(self, results, filename):
        """Export validation results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            self.stdout.write(
                self.style.SUCCESS(f"Validation results exported to {filename}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to export results: {str(e)}")
            )

    def _fix_issues(self, results):
        """Attempt to fix validation issues automatically"""
        self.stdout.write('\n' + self.style.WARNING('Attempting to fix issues...'))
        
        fixed_count = 0
        
        # This is a placeholder for automatic fixes
        # In a real implementation, you would add logic to fix specific issues
        
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"Fixed {fixed_count} issues automatically")
            )
        else:
            self.stdout.write(
                self.style.WARNING("No issues could be fixed automatically")
            )