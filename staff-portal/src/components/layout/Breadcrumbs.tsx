import React from 'react';
import { useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Breadcrumbs as MuiBreadcrumbs,
  Link,
  Typography,
  Box,
} from '@mui/material';
import {
  NavigateNext as NavigateNextIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import type { RootState } from '../../store';

interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: React.ReactNode;
}

const routeLabels: Record<string, string> = {
  '/app/dashboard': 'Dashboard',
  '/app/patients': 'Patients',
  '/app/patients/new': 'Add Patient',
  '/app/appointments': 'Appointments',
  '/app/appointments/schedule': 'Schedule',
  '/app/notifications': 'Notifications',
  '/app/prescriptions': 'Prescriptions',
  '/app/reports': 'Reports',
  '/app/analytics/dashboard': 'Analytics',
  '/app/settings': 'Settings',
};

export const Breadcrumbs: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { breadcrumbs: customBreadcrumbs } = useSelector((state: RootState) => state.ui);

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    // If custom breadcrumbs are set, use them
    if (customBreadcrumbs.length > 0) {
      return customBreadcrumbs.map(crumb => ({
        label: crumb.label,
        path: crumb.path,
        icon: crumb.icon ? <span>{crumb.icon}</span> : undefined,
      }));
    }

    // Generate breadcrumbs from current path
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [
      {
        label: 'Dashboard',
        path: '/dashboard',
        icon: <HomeIcon sx={{ fontSize: 16 }} />,
      },
    ];

    // Don't show breadcrumbs for dashboard itself
    if (location.pathname === '/dashboard' || location.pathname === '/') {
      return [];
    }

    let currentPath = '';
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      
      // Skip if it's the dashboard segment
      if (currentPath === '/dashboard') return;

      const label = routeLabels[currentPath] || segment.charAt(0).toUpperCase() + segment.slice(1);
      
      // For the last segment, don't include path (it's the current page)
      const isLast = index === pathSegments.length - 1;
      
      breadcrumbs.push({
        label,
        path: isLast ? undefined : currentPath,
      });
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  if (breadcrumbs.length === 0) {
    return null;
  }

  const handleBreadcrumbClick = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <MuiBreadcrumbs
        separator={<NavigateNextIcon fontSize="small" />}
        aria-label="breadcrumb"
        sx={{
          '& .MuiBreadcrumbs-separator': {
            mx: 1,
          },
        }}
      >
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;
          
          if (isLast || !crumb.path) {
            return (
              <Typography
                key={index}
                color="text.primary"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                  fontWeight: 500,
                }}
              >
                {crumb.icon}
                {crumb.label}
              </Typography>
            );
          }

          return (
            <Link
              key={index}
              component="button"
              variant="body2"
              onClick={() => handleBreadcrumbClick(crumb.path!)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                textDecoration: 'none',
                color: 'text.secondary',
                cursor: 'pointer',
                border: 'none',
                background: 'none',
                padding: 0,
                font: 'inherit',
                '&:hover': {
                  textDecoration: 'underline',
                  color: 'primary.main',
                },
              }}
            >
              {crumb.icon}
              {crumb.label}
            </Link>
          );
        })}
      </MuiBreadcrumbs>
    </Box>
  );
};