import React from 'react';
import { useSelector } from 'react-redux';
import { Box, Typography, Alert } from '@mui/material';
import { Lock as LockIcon } from '@mui/icons-material';
import type { RootState } from '../../store';
import { hasPermission, hasAnyPermission, hasAllPermissions, hasRole, hasAnyRole } from '../../utils/permissionUtils';

interface PermissionGuardProps {
  children: React.ReactNode;
  
  // Permission-based access
  permission?: string;
  anyPermissions?: string[];
  allPermissions?: string[];
  
  // Role-based access
  role?: string;
  anyRoles?: string[];
  
  // Fallback content
  fallback?: React.ReactNode;
  showFallback?: boolean;
  
  // Custom access check function
  customCheck?: (user: any) => boolean;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  permission,
  anyPermissions,
  allPermissions,
  role,
  anyRoles,
  fallback,
  showFallback = true,
  customCheck,
}) => {
  const { user } = useSelector((state: RootState) => state.auth);

  // If no user is authenticated, deny access
  if (!user) {
    return showFallback ? (
      fallback || (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          p={4}
          textAlign="center"
        >
          <LockIcon color="disabled" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Authentication Required
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please log in to access this content.
          </Typography>
        </Box>
      )
    ) : null;
  }

  // Check custom access function first
  if (customCheck && !customCheck(user)) {
    return showFallback ? (
      fallback || (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          p={4}
          textAlign="center"
        >
          <LockIcon color="disabled" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Access Denied
          </Typography>
          <Typography variant="body2" color="text.secondary">
            You don't have permission to access this content.
          </Typography>
        </Box>
      )
    ) : null;
  }

  // Check single permission
  if (permission && !hasPermission(permission)) {
    return showFallback ? (
      fallback || (
        <Alert severity="warning" sx={{ m: 2 }}>
          <Typography variant="body2">
            You need the "{permission}" permission to access this content.
          </Typography>
        </Alert>
      )
    ) : null;
  }

  // Check any of multiple permissions
  if (anyPermissions && !hasAnyPermission(anyPermissions)) {
    return showFallback ? (
      fallback || (
        <Alert severity="warning" sx={{ m: 2 }}>
          <Typography variant="body2">
            You need one of the following permissions: {anyPermissions.join(', ')}
          </Typography>
        </Alert>
      )
    ) : null;
  }

  // Check all of multiple permissions
  if (allPermissions && !hasAllPermissions(allPermissions)) {
    return showFallback ? (
      fallback || (
        <Alert severity="warning" sx={{ m: 2 }}>
          <Typography variant="body2">
            You need all of the following permissions: {allPermissions.join(', ')}
          </Typography>
        </Alert>
      )
    ) : null;
  }

  // Check single role
  if (role && !hasRole(role)) {
    return showFallback ? (
      fallback || (
        <Alert severity="warning" sx={{ m: 2 }}>
          <Typography variant="body2">
            You need the "{role}" role to access this content.
          </Typography>
        </Alert>
      )
    ) : null;
  }

  // Check any of multiple roles
  if (anyRoles && !hasAnyRole(anyRoles)) {
    return showFallback ? (
      fallback || (
        <Alert severity="warning" sx={{ m: 2 }}>
          <Typography variant="body2">
            You need one of the following roles: {anyRoles.join(', ')}
          </Typography>
        </Alert>
      )
    ) : null;
  }

  // All checks passed, render children
  return <>{children}</>;
};

// Higher-order component version
export const withPermissionGuard = <P extends object>(
  Component: React.ComponentType<P>,
  guardProps: Omit<PermissionGuardProps, 'children'>
) => {
  return (props: P) => (
    <PermissionGuard {...guardProps}>
      <Component {...props} />
    </PermissionGuard>
  );
};

// Hook for permission checking in components
export const usePermissions = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  
  return {
    user,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    isAuthenticated: !!user,
  };
};