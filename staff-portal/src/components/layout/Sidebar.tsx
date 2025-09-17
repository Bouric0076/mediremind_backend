import React, { useState, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Typography,
  Box,
  Divider,
  Avatar,
  Chip,
  Toolbar,
  useTheme,
  alpha,
  Paper,
  Stack,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  CalendarToday as CalendarIcon,
  Notifications as NotificationsIcon,
  Medication as MedicationIcon,
  Assessment as ReportsIcon,
  Settings as SettingsIcon,
  ExpandLess,
  ExpandMore,
  PersonAdd,
  EventAvailable,
  Analytics,
  AccountBox,
  // Staff Management Icons
  Group as StaffIcon,
  Badge as CredentialIcon,
  Person as ProfileIcon,
  // Billing & Financial Management Icons
  Receipt as BillingIcon,
  Payment as PaymentIcon,
  LocalHospital as InsuranceIcon,
  AccountBalance as InvoiceIcon,
  // Medical Records Management Icons
  MedicalServices as MedicalIcon,
  Note as NotesIcon,
  History as TimelineIcon,
  Folder as RecordsIcon,
  // System Administration Icons
  AdminPanelSettings as AdminIcon,
  ManageAccounts as UserManagementIcon,
  Tune as ConfigIcon,
} from '@mui/icons-material';
import type { RootState } from '../../store';
import { addRecentAction } from '../../store/slices/uiSlice';

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path?: string;
  children?: NavigationItem[];
  badge?: number;
  roles?: string[];
}

const navigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/app/dashboard',
  },
  {
    id: 'patients',
    label: 'Patients',
    icon: <PeopleIcon />,
    children: [
      {
        id: 'patients-list',
        label: 'All Patients',
        icon: <PeopleIcon />,
        path: '/app/patients',
      },
      {
        id: 'patients-add',
        label: 'Add Patient',
        icon: <PersonAdd />,
        path: '/app/patients/new',
      },
    ],
  },
  {
    id: 'appointments',
    label: 'Appointments',
    icon: <CalendarIcon />,
    children: [
      {
        id: 'appointments-calendar',
        label: 'Calendar',
        icon: <CalendarIcon />,
        path: '/app/appointments',
      },
      {
        id: 'appointments-schedule',
        label: 'Schedule',
        icon: <EventAvailable />,
        path: '/app/appointments/schedule',
      },
    ],
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: <NotificationsIcon />,
    path: '/app/notifications',
  },
  {
    id: 'prescriptions',
    label: 'Prescriptions',
    icon: <MedicationIcon />,
    path: '/app/prescriptions',
    roles: ['doctor', 'pharmacist', 'admin'],
  },
  {
    id: 'reports',
    label: 'Reports & Analytics',
    icon: <ReportsIcon />,
    children: [
      {
        id: 'reports-overview',
        label: 'Overview',
        icon: <ReportsIcon />,
        path: '/app/reports',
      },
      {
        id: 'reports-analytics',
        label: 'Analytics',
        icon: <Analytics />,
        path: '/app/analytics/dashboard',
        roles: ['admin', 'manager'],
      },
    ],
  },
  {
    id: 'staff',
    label: 'Staff Management',
    icon: <StaffIcon />,
    children: [
      {
        id: 'staff-directory',
        label: 'Staff Directory',
        icon: <StaffIcon />,
        path: '/app/staff/directory',
      },
      {
        id: 'staff-credentials',
        label: 'Credentials',
        icon: <CredentialIcon />,
        path: '/app/staff/credentials',
        roles: ['admin', 'hr'],
      },
    ],
  },
  {
    id: 'billing',
    label: 'Billing & Finance',
    icon: <BillingIcon />,
    children: [
      {
        id: 'billing-invoices',
        label: 'Invoice Management',
        icon: <InvoiceIcon />,
        path: '/app/billing/invoices',
        roles: ['admin', 'billing', 'finance'],
      },
      {
        id: 'billing-payments',
        label: 'Payment Processing',
        icon: <PaymentIcon />,
        path: '/app/billing/payments',
        roles: ['admin', 'billing', 'finance'],
      },
      {
        id: 'billing-insurance',
        label: 'Insurance Claims',
        icon: <InsuranceIcon />,
        path: '/app/billing/insurance',
        roles: ['admin', 'billing', 'finance'],
      },
    ],
  },
  {
    id: 'medical',
    label: 'Medical Records',
    icon: <MedicalIcon />,
    children: [
      {
        id: 'medical-records',
        label: 'Patient Records',
        icon: <RecordsIcon />,
        path: '/app/medical/records',
        roles: ['doctor', 'nurse', 'admin'],
      },
      {
        id: 'medical-notes',
        label: 'Clinical Notes',
        icon: <NotesIcon />,
        path: '/app/medical/notes',
        roles: ['doctor', 'nurse', 'admin'],
      },
      {
        id: 'medical-timeline',
        label: 'Medical Timeline',
        icon: <TimelineIcon />,
        path: '/app/medical/timeline',
        roles: ['doctor', 'nurse', 'admin'],
      },
    ],
  },
  {
    id: 'admin',
    label: 'System Administration',
    icon: <AdminIcon />,
    children: [
      {
        id: 'admin-users',
        label: 'User & Role Management',
        icon: <UserManagementIcon />,
        path: '/app/admin/users',
        roles: ['admin'],
      },
      {
        id: 'admin-config',
        label: 'System Configuration',
        icon: <ConfigIcon />,
        path: '/app/admin/config',
        roles: ['admin'],
      },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <SettingsIcon />,
    path: '/app/settings',
  },
];

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  
  const { user } = useSelector((state: RootState) => state.auth);
  const { sidebarCollapsed } = useSelector((state: RootState) => state.ui);
  const { unread } = useSelector((state: RootState) => state.notifications);
  
  const [expandedItems, setExpandedItems] = React.useState<string[]>(['patients', 'appointments', 'reports', 'staff', 'billing', 'medical', 'admin']);

  const handleItemClick = (item: NavigationItem) => {
    if (item.path) {
      navigate(item.path);
      dispatch(addRecentAction(item.id));
    } else if (item.children) {
      toggleExpanded(item.id);
    }
  };

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev => 
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const isItemActive = (item: NavigationItem): boolean => {
    if (item.path) {
      return location.pathname === item.path;
    }
    if (item.children) {
      return item.children.some(child => location.pathname === child.path);
    }
    return false;
  };

  const hasPermission = (item: NavigationItem): boolean => {
    if (!item.roles || !user?.role) return true;
    return item.roles.includes(user.role);
  };

  // NavigationItem component for improved design
  const NavigationItemComponent: React.FC<{
    item: NavigationItem;
    isCollapsed: boolean;
    currentPath: string;
    onNavigate: (path: string, itemId: string) => void;
    userRole?: string;
    level?: number;
  }> = ({ item, isCollapsed, currentPath, onNavigate, userRole, level = 0 }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const isActive = currentPath === item.path || (item.children && item.children.some(child => currentPath === child.path));
    const hasAccess = !item.roles || item.roles.includes(userRole || '');

    if (!hasAccess) return null;

    const handleClick = () => {
      if (item.children && item.children.length > 0) {
        setIsExpanded(!isExpanded);
      } else if (item.path) {
        onNavigate(item.path, item.id);
      }
    };

    const listItemSx = {
      mb: 0.5,
      mx: level === 0 ? 0 : 1,
      borderRadius: 2,
      overflow: 'hidden',
      '&:hover': {
        backgroundColor: alpha(theme.palette.primary.main, 0.08),
        transform: 'translateX(2px)',
      },
      transition: 'all 0.2s ease',
      ...(isActive && {
        backgroundColor: alpha(theme.palette.primary.main, 0.12),
        borderLeft: `4px solid ${theme.palette.primary.main}`,
        '&:hover': {
          backgroundColor: alpha(theme.palette.primary.main, 0.16),
        },
      }),
    };

    const buttonSx = {
      py: 1.5,
      px: isCollapsed ? 1 : 2,
      minHeight: 48,
      justifyContent: isCollapsed ? 'center' : 'flex-start',
      borderRadius: 2,
      '&:hover': {
        backgroundColor: 'transparent',
      },
    };

    const iconSx = {
      color: isActive ? theme.palette.primary.main : theme.palette.text.secondary,
      minWidth: isCollapsed ? 'auto' : 40,
      mr: isCollapsed ? 0 : 1.5,
      fontSize: 22,
      transition: 'all 0.2s ease',
      ...(isActive && {
        transform: 'scale(1.1)',
      }),
    };

    const textSx = {
      '& .MuiListItemText-primary': {
        fontSize: '0.9rem',
        fontWeight: isActive ? 600 : 500,
        color: isActive ? theme.palette.primary.main : theme.palette.text.primary,
        transition: 'all 0.2s ease',
      },
    };

    return (
      <>
        <ListItem sx={listItemSx} disablePadding>
          <ListItemButton onClick={handleClick} sx={buttonSx}>
            <ListItemIcon sx={iconSx}>
              {item.icon}
              {item.badge && (
                <Badge
                  badgeContent={item.badge}
                  color="error"
                  sx={{
                    position: 'absolute',
                    top: -8,
                    right: -8,
                    '& .MuiBadge-badge': {
                      fontSize: '0.7rem',
                      height: 16,
                      minWidth: 16,
                    },
                  }}
                />
              )}
            </ListItemIcon>
            {!isCollapsed && (
              <>
                <ListItemText primary={item.label} sx={textSx} />
                {item.children && item.children.length > 0 && (
                  <ExpandLess
                    sx={{
                      transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                      transition: 'transform 0.2s ease',
                      color: theme.palette.text.secondary,
                    }}
                  />
                )}
              </>
            )}
          </ListItemButton>
        </ListItem>
        
        {/* Submenu */}
        {item.children && item.children.length > 0 && !isCollapsed && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding sx={{ pl: 2 }}>
              {item.children.map((child) => (
                <NavigationItemComponent
                  key={child.id}
                  item={child}
                  isCollapsed={isCollapsed}
                  currentPath={currentPath}
                  onNavigate={onNavigate}
                  userRole={userRole}
                  level={level + 1}
                />
              ))}
            </List>
          </Collapse>
        )}
      </>
    );
  };

  const renderNavigationItem = (item: NavigationItem, level = 0) => {
    if (!hasPermission(item)) return null;

    const isActive = isItemActive(item);
    const isExpanded = expandedItems.includes(item.id);
    const hasChildren = item.children && item.children.length > 0;
    
    let badge = item.badge;
    if (item.id === 'notifications') {
      badge = unread.length;
    }

    const listItem = (
      <ListItem key={item.id} disablePadding sx={{ display: 'block' }}>
        <ListItemButton
          onClick={() => handleItemClick(item)}
          selected={isActive && !hasChildren}
          sx={{
            minHeight: 48,
            justifyContent: sidebarCollapsed ? 'center' : 'initial',
            px: 2.5,
            pl: level > 0 ? 4 : 2.5,
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
              '& .MuiListItemIcon-root': {
                color: 'primary.contrastText',
              },
            },
          }}
        >
          <ListItemIcon
            sx={{
              minWidth: 0,
              mr: sidebarCollapsed ? 'auto' : 3,
              justifyContent: 'center',
            }}
          >
            {badge && badge > 0 ? (
              <Badge badgeContent={badge} color="error">
                {item.icon}
              </Badge>
            ) : (
              item.icon
            )}
          </ListItemIcon>
          
          {!sidebarCollapsed && (
            <>
              <ListItemText 
                primary={item.label}
                primaryTypographyProps={{
                  fontSize: level > 0 ? '0.875rem' : '1rem',
                  fontWeight: isActive ? 600 : 400,
                }}
              />
              {hasChildren && (
                isExpanded ? <ExpandLess /> : <ExpandMore />
              )}
            </>
          )}
        </ListItemButton>
      </ListItem>
    );

    if (sidebarCollapsed) {
      return (
        <Tooltip key={item.id} title={item.label} placement="right">
          {listItem}
        </Tooltip>
      );
    }

    return (
      <React.Fragment key={item.id}>
        {listItem}
        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children!.map(child => renderNavigationItem(child, level + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  const theme = useTheme();
  const drawerWidth = 280;
  const isCollapsed = sidebarCollapsed;

  const handleNavigate = useCallback((path: string, itemId: string) => {
    navigate(path);
    dispatch(addRecentAction(itemId));
  }, [navigate, dispatch]);

  return (
    <Drawer
      variant="permanent"
      open={!isCollapsed}
      sx={{
        width: isCollapsed ? 64 : drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: isCollapsed ? 64 : drawerWidth,
          boxSizing: 'border-box',
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          overflowX: 'hidden',
          background: `linear-gradient(180deg, ${theme.palette.background.paper} 0%, ${alpha(theme.palette.primary.main, 0.05)} 100%)`,
          borderRight: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          backdropFilter: 'blur(10px)',
          boxShadow: '4px 0 20px rgba(0, 0, 0, 0.05)',
        },
      }}
    >
      <Toolbar />
      
      {/* User info section */}
      {!isCollapsed && (
        <Paper
          elevation={0}
          sx={{ 
            m: 2, 
            p: 2.5, 
            borderRadius: 3,
            background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
            color: 'white',
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.05"%3E%3Ccircle cx="30" cy="30" r="2"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
              opacity: 0.3,
            },
          }}
        >
          <Stack direction="row" alignItems="center" spacing={2} sx={{ position: 'relative', zIndex: 1 }}>
            <Avatar
              src={user?.avatar}
              alt={`${user?.firstName} ${user?.lastName}`}
              sx={{ 
                width: 48, 
                height: 48,
                border: '3px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              }}
            >
              {user?.firstName?.[0]}{user?.lastName?.[0]}
            </Avatar>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="subtitle1" noWrap sx={{ fontWeight: 700, mb: 0.5 }}>
                {user?.firstName} {user?.lastName}
              </Typography>
              <Chip
                label={user?.role}
                size="small"
                sx={{
                  height: 22,
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              />
            </Box>
          </Stack>
        </Paper>
      )}

      {/* Collapsed user info */}
      {isCollapsed && (
        <Box sx={{ p: 1, display: 'flex', justifyContent: 'center' }}>
          <Avatar
            src={user?.avatar}
            alt={`${user?.firstName} ${user?.lastName}`}
            sx={{ 
              width: 40, 
              height: 40,
              border: `2px solid ${theme.palette.primary.main}`,
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
            }}
          >
            {user?.firstName?.[0]}{user?.lastName?.[0]}
          </Avatar>
        </Box>
      )}

      {/* Navigation */}
      <List sx={{ flex: 1, py: 1, px: isCollapsed ? 0.5 : 1 }}>
        {navigationItems.map((item) => (
          <NavigationItemComponent
            key={item.id}
            item={item}
            isCollapsed={isCollapsed}
            currentPath={location.pathname}
            onNavigate={handleNavigate}
            userRole={user?.role}
          />
        ))}
      </List>

      {/* Footer */}
      {!isCollapsed && (
        <Paper
          elevation={0}
          sx={{ 
            m: 2, 
            p: 2, 
            borderRadius: 2,
            backgroundColor: alpha(theme.palette.primary.main, 0.05),
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
          }}
        >
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="caption" sx={{ fontWeight: 600, color: theme.palette.text.primary }}>
                MediRemind
              </Typography>
              <Typography variant="caption" sx={{ display: 'block', color: theme.palette.text.secondary }}>
                v2.1.0
              </Typography>
            </Box>
            <Chip
              label="Online"
              size="small"
              color="success"
              variant="outlined"
              sx={{ 
                height: 20,
                fontSize: '0.7rem',
                fontWeight: 600,
              }}
            />
          </Stack>
        </Paper>
      )}
    </Drawer>
  );
};