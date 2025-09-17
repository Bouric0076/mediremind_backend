import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  Toolbar,
  IconButton,
  Typography,
  Box,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  InputBase,
  alpha,
  useTheme,
  useMediaQuery,
  Tooltip,
  Chip,
  Paper,
  Stack,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  AccountCircle,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  DarkMode,
  LightMode,
  WifiOff,
  Wifi,
  LocalHospital,
  KeyboardArrowDown,
  Refresh,
} from '@mui/icons-material';
import type { RootState } from '../../store';
import {
  toggleSidebar,
  setSidebarMobile,
  setTheme,
  setGlobalSearchOpen,
  setGlobalSearchQuery,
} from '../../store/slices/uiSlice';
import { logout } from '../../store/slices/authSlice';
import { useLogoutMutation } from '../../store/api/apiSlice';

export const Header: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));
  
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  const [notificationMenuAnchor, setNotificationMenuAnchor] = useState<null | HTMLElement>(null);
  
  const { user } = useSelector((state: RootState) => state.auth);
  const { 
    theme: currentTheme, 
    sidebarMobile, 
    globalSearch,
    isOnline 
  } = useSelector((state: RootState) => state.ui);
  const { unread } = useSelector((state: RootState) => state.notifications);
  
  const [logoutMutation] = useLogoutMutation();

  const handleMenuToggle = () => {
    if (isMobile) {
      dispatch(setSidebarMobile(!sidebarMobile));
    } else {
      dispatch(toggleSidebar());
    }
  };

  const handleThemeToggle = () => {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    dispatch(setTheme(newTheme));
  };

  const handleSearchFocus = () => {
    dispatch(setGlobalSearchOpen(true));
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setGlobalSearchQuery(event.target.value));
  };

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationMenuAnchor(event.currentTarget);
  };

  const handleNotificationMenuClose = () => {
    setNotificationMenuAnchor(null);
  };

  const handleLogout = async () => {
    try {
      await logoutMutation().unwrap();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch(logout());
      navigate('/login');
    }
    handleUserMenuClose();
  };

  const handleProfile = () => {
    navigate('/settings');
    handleUserMenuClose();
  };

  const handleNotifications = () => {
    navigate('/notifications');
    handleNotificationMenuClose();
  };

  return (
    <Toolbar 
      sx={{ 
        gap: 2,
        background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
        boxShadow: '0 4px 20px rgba(25, 118, 210, 0.15)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        minHeight: '72px !important',
      }}
    >
      {/* Left Section */}
      <Stack direction="row" alignItems="center" spacing={2}>
        {/* Menu toggle */}
        <IconButton
          color="inherit"
          aria-label="toggle menu"
          onClick={handleMenuToggle}
          edge="start"
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
            },
            borderRadius: 2,
          }}
        >
          <MenuIcon />
        </IconButton>

        {/* Logo and title */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <LocalHospital 
            sx={{ 
              fontSize: 32, 
              color: 'white',
              filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))',
            }} 
          />
          <Box>
            <Typography
              variant="h5"
              noWrap
              component="div"
              sx={{ 
                display: { xs: 'none', sm: 'block' },
                fontWeight: 700,
                color: 'white',
                textShadow: '0 2px 4px rgba(0,0,0,0.2)',
                letterSpacing: '-0.5px',
              }}
            >
              MediRemind
            </Typography>
            <Typography
              variant="caption"
              sx={{ 
                display: { xs: 'none', md: 'block' },
                color: 'rgba(255, 255, 255, 0.8)',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '1px',
                fontSize: '0.7rem',
              }}
            >
              Staff Portal
            </Typography>
          </Box>
        </Box>

        {/* Connection status */}
        <Chip
          icon={isOnline ? <Wifi /> : <WifiOff />}
          label={isOnline ? 'Online' : 'Offline'}
          size="small"
          color={isOnline ? 'success' : 'error'}
          variant="filled"
          sx={{ 
            backgroundColor: isOnline ? 'rgba(76, 175, 80, 0.9)' : 'rgba(244, 67, 54, 0.9)',
            color: 'white',
            fontWeight: 600,
            '& .MuiChip-icon': {
              color: 'white',
            },
          }}
        />
      </Stack>

      {/* Spacer */}
      <Box sx={{ flexGrow: 1 }} />

      {/* Center Section - Search */}
      <Paper
        elevation={0}
        sx={{
          position: 'relative',
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.25)',
          },
          '&:focus-within': {
            backgroundColor: 'rgba(255, 255, 255, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.4)',
          },
          marginLeft: 0,
          width: '100%',
          maxWidth: 450,
          display: { xs: 'none', md: 'block' },
          transition: 'all 0.3s ease',
        }}
      >
        <Box
          sx={{
            padding: theme.spacing(0, 2),
            height: '100%',
            position: 'absolute',
            pointerEvents: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'rgba(255, 255, 255, 0.7)',
          }}
        >
          <SearchIcon />
        </Box>
        <InputBase
          placeholder="Search patients, appointments, records..."
          value={globalSearch.query}
          onChange={handleSearchChange}
          onFocus={handleSearchFocus}
          inputProps={{ 'aria-label': 'search' }}
          sx={{
            color: 'white',
            width: '100%',
            '& .MuiInputBase-input': {
              padding: theme.spacing(1.5, 1.5, 1.5, 0),
              paddingLeft: `calc(1em + ${theme.spacing(4)})`,
              transition: theme.transitions.create('width'),
              fontSize: '0.95rem',
              '&::placeholder': {
                color: 'rgba(255, 255, 255, 0.7)',
                opacity: 1,
              },
            },
          }}
        />
      </Paper>

      {/* Mobile search */}
      <IconButton
        color="inherit"
        aria-label="search"
        onClick={handleSearchFocus}
        sx={{ 
          display: { xs: 'block', md: 'none' },
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
          },
        }}
      >
        <SearchIcon />
      </IconButton>

      {/* Spacer */}
      <Box sx={{ flexGrow: 1 }} />

      {/* Right Section */}
      <Stack direction="row" alignItems="center" spacing={1}>
        {/* Refresh button */}
        <Tooltip title="Refresh Data">
          <IconButton 
            color="inherit" 
            sx={{
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
              },
            }}
          >
            <Refresh />
          </IconButton>
        </Tooltip>

        {/* Theme toggle */}
        <Tooltip title={`Switch to ${currentTheme === 'light' ? 'dark' : 'light'} mode`}>
          <IconButton 
            color="inherit" 
            onClick={handleThemeToggle}
            sx={{
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
              },
            }}
          >
            {currentTheme === 'light' ? <DarkMode /> : <LightMode />}
          </IconButton>
        </Tooltip>

        {/* Notifications */}
        <Tooltip title="Notifications">
          <IconButton
            color="inherit"
            aria-label="notifications"
            onClick={handleNotificationMenuOpen}
            sx={{
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
              },
            }}
          >
            <Badge 
              badgeContent={unread.length} 
              color="error"
              sx={{
                '& .MuiBadge-badge': {
                  backgroundColor: '#ff4444',
                  color: 'white',
                  fontWeight: 600,
                },
              }}
            >
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Tooltip>

        {/* User menu */}
        <Button
          color="inherit"
          aria-label="account"
          onClick={handleUserMenuOpen}
          endIcon={<KeyboardArrowDown />}
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
            },
            borderRadius: 2,
            px: 2,
            py: 1,
            textTransform: 'none',
            display: { xs: 'none', sm: 'flex' },
          }}
        >
          {user?.avatar ? (
            <Avatar
              src={user.avatar}
              alt={`${user.firstName} ${user.lastName}`}
              sx={{ width: 32, height: 32, mr: 1 }}
            />
          ) : (
            <Avatar sx={{ width: 32, height: 32, mr: 1, bgcolor: 'rgba(255, 255, 255, 0.2)' }}>
              <AccountCircle />
            </Avatar>
          )}
          <Box sx={{ textAlign: 'left', display: { xs: 'none', md: 'block' } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
              {user?.firstName} {user?.lastName}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8, lineHeight: 1 }}>
              {user?.role}
            </Typography>
          </Box>
        </Button>

        {/* Mobile user menu */}
        <IconButton
          color="inherit"
          aria-label="account"
          onClick={handleUserMenuOpen}
          sx={{ 
            display: { xs: 'block', sm: 'none' },
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          {user?.avatar ? (
            <Avatar
              src={user.avatar}
              alt={`${user.firstName} ${user.lastName}`}
              sx={{ width: 32, height: 32 }}
            />
          ) : (
            <AccountCircle />
          )}
        </IconButton>
      </Stack>

      {/* Notification Menu */}
      <Menu
        anchorEl={notificationMenuAnchor}
        open={Boolean(notificationMenuAnchor)}
        onClose={handleNotificationMenuClose}
        onClick={handleNotificationMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            minWidth: 300,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleNotifications}>
          <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
            <Typography variant="subtitle2">
              {unread.length} unread notifications
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Click to view all notifications
            </Typography>
          </Box>
        </MenuItem>
      </Menu>

      {/* User Menu */}
      <Menu
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={handleUserMenuClose}
        onClick={handleUserMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2">{user?.firstName} {user?.lastName}</Typography>
          <Typography variant="body2" color="text.secondary">
            {user?.email}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {user?.role}
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={handleProfile}>
          <SettingsIcon sx={{ mr: 2 }} />
          Settings
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <LogoutIcon sx={{ mr: 2 }} />
          Logout
        </MenuItem>
      </Menu>
    </Toolbar>
  );
};