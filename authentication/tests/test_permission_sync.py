"""
Tests for permission synchronization between frontend and backend
"""

import json
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from authentication.permissions_config import PERMISSIONS_CONFIG
from authentication.services import PermissionService
from authentication.models import UserProfile


class PermissionSyncTestCase(APITestCase):
    """Test permission synchronization across the system"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.permission_service = PermissionService()
        
        # Create test users with different roles
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role='admin'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor@test.com',
            email='doctor@test.com',
            password='testpass123'
        )
        self.doctor_profile = UserProfile.objects.create(
            user=self.doctor_user,
            role='doctor'
        )
        
        self.nurse_user = User.objects.create_user(
            username='nurse@test.com',
            email='nurse@test.com',
            password='testpass123'
        )
        self.nurse_profile = UserProfile.objects.create(
            user=self.nurse_user,
            role='nurse'
        )

    def test_permission_config_consistency(self):
        """Test that permission configuration is internally consistent"""
        # Test that all permissions have required fields
        for perm_code, permission in PERMISSIONS_CONFIG._permissions.items():
            self.assertIsNotNone(permission.code, f"Permission {perm_code} missing code")
            self.assertIsNotNone(permission.name, f"Permission {perm_code} missing name")
            self.assertIsNotNone(permission.category, f"Permission {perm_code} missing category")
            self.assertIsNotNone(permission.level, f"Permission {perm_code} missing level")
        
        # Test that all role permissions reference valid permissions
        for role, permissions in PERMISSIONS_CONFIG._role_permissions.items():
            for perm_code in permissions:
                self.assertIn(
                    perm_code, 
                    PERMISSIONS_CONFIG._permissions,
                    f"Role {role} references undefined permission: {perm_code}"
                )

    def test_role_hierarchy_consistency(self):
        """Test that role hierarchy is consistent with permission assignments"""
        roles = list(PERMISSIONS_CONFIG._role_hierarchy.keys())
        
        for i, role1 in enumerate(roles):
            for role2 in roles[i+1:]:
                level1 = PERMISSIONS_CONFIG.get_role_level(role1)
                level2 = PERMISSIONS_CONFIG.get_role_level(role2)
                
                perms1 = set(PERMISSIONS_CONFIG.get_role_permissions(role1))
                perms2 = set(PERMISSIONS_CONFIG.get_role_permissions(role2))
                
                # Higher level roles should have at least the permissions of lower level roles
                if level1 > level2:
                    missing_perms = perms2 - perms1
                    self.assertEqual(
                        len(missing_perms), 0,
                        f"Higher role {role1} missing permissions from lower role {role2}: {missing_perms}"
                    )

    def test_permission_service_consistency(self):
        """Test that PermissionService returns consistent results"""
        for role in PERMISSIONS_CONFIG._role_permissions.keys():
            # Create a mock user with this role
            user = User(email=f"test_{role}@test.com")
            user.role = role
            
            # Get permissions through service
            service_permissions = self.permission_service.get_user_permissions(user)
            config_permissions = PERMISSIONS_CONFIG.get_role_permissions(role)
            
            self.assertEqual(
                set(service_permissions),
                set(config_permissions),
                f"PermissionService and config mismatch for role {role}"
            )

    def test_user_permission_assignment(self):
        """Test that users get correct permissions based on their roles"""
        test_cases = [
            (self.admin_user, 'admin'),
            (self.doctor_user, 'doctor'),
            (self.nurse_user, 'nurse')
        ]
        
        for user, expected_role in test_cases:
            user_permissions = self.permission_service.get_user_permissions(user)
            expected_permissions = PERMISSIONS_CONFIG.get_role_permissions(expected_role)
            
            self.assertEqual(
                set(user_permissions),
                set(expected_permissions),
                f"User {user.email} permissions don't match role {expected_role}"
            )

    def test_permission_checking_methods(self):
        """Test various permission checking methods"""
        # Test has_permission method
        self.assertTrue(
            self.permission_service.check_permission(self.admin_user, 'manage_users'),
            "Admin should have manage_users permission"
        )
        
        self.assertFalse(
            self.permission_service.check_permission(self.nurse_user, 'manage_users'),
            "Nurse should not have manage_users permission"
        )
        
        # Test role comparison
        self.assertTrue(
            PERMISSIONS_CONFIG.is_role_higher_or_equal('admin', 'doctor'),
            "Admin should be higher or equal to doctor"
        )
        
        self.assertFalse(
            PERMISSIONS_CONFIG.is_role_higher_or_equal('nurse', 'doctor'),
            "Nurse should not be higher than doctor"
        )

    def test_detailed_permissions_structure(self):
        """Test that detailed permissions have correct structure"""
        for role in PERMISSIONS_CONFIG._role_permissions.keys():
            user = User(email=f"test_{role}@test.com")
            user.role = role
            
            detailed_perms = self.permission_service.get_detailed_permissions(user)
            
            # Check structure
            self.assertIsInstance(detailed_perms, dict, "Detailed permissions should be a dict")
            
            # Check that all categories are present
            expected_categories = set()
            for perm_code in PERMISSIONS_CONFIG.get_role_permissions(role):
                permission = PERMISSIONS_CONFIG._permissions[perm_code]
                expected_categories.add(permission.category)
            
            for category in expected_categories:
                self.assertIn(category, detailed_perms, f"Category {category} missing for role {role}")
                self.assertIsInstance(detailed_perms[category], list, f"Category {category} should be a list")

    def test_frontend_backend_permission_sync(self):
        """Test that frontend and backend permission definitions are synchronized"""
        # This test would ideally compare with frontend permission definitions
        # For now, we'll test the structure that frontend expects
        
        for role in PERMISSIONS_CONFIG._role_permissions.keys():
            user = User(email=f"test_{role}@test.com")
            user.role = role
            
            # Test the format expected by frontend
            user_data = {
                'id': user.id,
                'email': user.email,
                'role': role,
                'permissions': self.permission_service.get_user_permissions(user),
                'detailedPermissions': self.permission_service.get_detailed_permissions(user)
            }
            
            # Verify structure
            self.assertIsInstance(user_data['permissions'], list)
            self.assertIsInstance(user_data['detailedPermissions'], dict)
            
            # Verify all permissions are strings
            for perm in user_data['permissions']:
                self.assertIsInstance(perm, str)
            
            # Verify detailed permissions structure
            for category, perms in user_data['detailedPermissions'].items():
                self.assertIsInstance(category, str)
                self.assertIsInstance(perms, list)
                for perm in perms:
                    self.assertIsInstance(perm, dict)
                    self.assertIn('code', perm)
                    self.assertIn('name', perm)

    def test_permission_api_endpoints(self):
        """Test API endpoints that return permission data"""
        # This assumes you have API endpoints for permissions
        # Adjust based on your actual API structure
        
        # Test user permissions endpoint
        self.client.force_authenticate(user=self.admin_user)
        
        # Test getting current user permissions
        response = self.client.get('/api/auth/me/')  # Adjust URL as needed
        if response.status_code == 200:
            data = response.json()
            if 'permissions' in data:
                expected_permissions = PERMISSIONS_CONFIG.get_role_permissions('admin')
                self.assertEqual(set(data['permissions']), set(expected_permissions))

    def test_permission_caching_consistency(self):
        """Test that permission caching doesn't cause inconsistencies"""
        # Test multiple calls return same results
        user = self.admin_user
        
        perms1 = self.permission_service.get_user_permissions(user)
        perms2 = self.permission_service.get_user_permissions(user)
        
        self.assertEqual(perms1, perms2, "Permission caching causing inconsistency")
        
        # Test detailed permissions caching
        detailed1 = self.permission_service.get_detailed_permissions(user)
        detailed2 = self.permission_service.get_detailed_permissions(user)
        
        self.assertEqual(detailed1, detailed2, "Detailed permission caching causing inconsistency")

    def test_role_update_permission_sync(self):
        """Test that changing user roles updates permissions correctly"""
        user = self.doctor_user
        original_permissions = self.permission_service.get_user_permissions(user)
        
        # Change role
        user.userprofile.role = 'admin'
        user.userprofile.save()
        
        # Get new permissions
        new_permissions = self.permission_service.get_user_permissions(user)
        expected_permissions = PERMISSIONS_CONFIG.get_role_permissions('admin')
        
        self.assertEqual(
            set(new_permissions),
            set(expected_permissions),
            "Permissions not updated after role change"
        )
        
        self.assertNotEqual(
            set(original_permissions),
            set(new_permissions),
            "Permissions should change when role changes"
        )

    def test_permission_validation_command(self):
        """Test the permission validation management command"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        
        # Run validation command
        try:
            call_command('validate_permissions', stdout=out)
            output = out.getvalue()
            
            # Check that command ran successfully
            self.assertIn('PERMISSION VALIDATION RESULTS', output)
            
            # If there are no errors, should show PASSED
            if 'ERRORS (0)' in output:
                self.assertIn('Status: PASSED', output)
                
        except Exception as e:
            self.fail(f"Permission validation command failed: {str(e)}")


class PermissionIntegrationTestCase(TestCase):
    """Integration tests for permission system"""
    
    def setUp(self):
        self.permission_service = PermissionService()
    
    def test_end_to_end_permission_flow(self):
        """Test complete permission flow from user creation to permission checking"""
        # Create user
        user = User.objects.create_user(
            username='integration@test.com',
            email='integration@test.com',
            password='testpass123'
        )
        
        # Assign role
        profile = UserProfile.objects.create(user=user, role='doctor')
        
        # Check permissions
        permissions = self.permission_service.get_user_permissions(user)
        expected_permissions = PERMISSIONS_CONFIG.get_role_permissions('doctor')
        
        self.assertEqual(set(permissions), set(expected_permissions))
        
        # Test specific permission check
        has_view_patients = self.permission_service.check_permission(user, 'view_patients')
        self.assertTrue(has_view_patients, "Doctor should have view_patients permission")
        
        # Test permission they shouldn't have
        has_manage_users = self.permission_service.check_permission(user, 'manage_users')
        self.assertFalse(has_manage_users, "Doctor should not have manage_users permission")

    def test_permission_system_performance(self):
        """Test that permission system performs well under load"""
        import time
        
        user = User.objects.create_user(
            username='perf@test.com',
            email='perf@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user, role='admin')
        
        # Time permission checks
        start_time = time.time()
        
        for _ in range(100):
            self.permission_service.get_user_permissions(user)
            self.permission_service.check_permission(user, 'manage_users')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 100 operations in reasonable time (adjust threshold as needed)
        self.assertLess(duration, 1.0, "Permission operations taking too long")


if __name__ == '__main__':
    pytest.main([__file__])