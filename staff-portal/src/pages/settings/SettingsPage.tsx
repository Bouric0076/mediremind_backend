import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Paper,
  Typography,
  Button,
  Tabs,
  Tab,
  Card,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  Avatar,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Alert,
} from '@mui/material';
import Grid from '@mui/material/Grid';

import {
  Person as PersonIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Palette as PaletteIcon,
  Language as LanguageIcon,
  Storage as StorageIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  CalendarMonth as CalendarIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material';
import type { RootState } from '../../store';
import { setBreadcrumbs, setCurrentPage, setTheme } from '../../store/slices/uiSlice';
import { logout } from '../../store/slices/authSlice';
import CalendarIntegrationSettings from '../../components/settings/CalendarIntegrationSettings';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

export const SettingsPage: React.FC = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth);
  const { theme } = useSelector((state: RootState) => state.ui);
  
  const [tabValue, setTabValue] = useState(0);
  const [editingProfile, setEditingProfile] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [profileData, setProfileData] = useState({
    firstName: user?.full_name?.split(' ')[0] || '',
    lastName: user?.full_name?.split(' ').slice(1).join(' ') || '',
    email: user?.email || '',
    phone: user?.phone || '',
    department: user?.department || '',
    role: user?.role || '',
  });
  
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    smsNotifications: true,
    pushNotifications: true,
    appointmentReminders: true,
    systemAlerts: true,
    marketingEmails: false,
  });
  
  const [systemSettings, setSystemSettings] = useState({
    language: 'en',
    timezone: 'UTC-5',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
    autoLogout: 30,
  });

  useEffect(() => {
    dispatch(setCurrentPage('settings'));
    dispatch(setBreadcrumbs([
      { label: 'Settings', path: '/settings' }
    ]));
  }, [dispatch]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleProfileSave = () => {
    // Implement profile update logic
    console.log('Saving profile:', profileData);
    setEditingProfile(false);
  };

  const handlePasswordChange = () => {
    // Implement password change logic
    console.log('Changing password');
    setChangePasswordOpen(false);
    setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
  };

  const handleNotificationSettingChange = (setting: string, value: boolean) => {
    setNotificationSettings(prev => ({ ...prev, [setting]: value }));
  };

  const handleSystemSettingChange = (setting: string, value: string | number) => {
    setSystemSettings(prev => ({ ...prev, [setting]: value }));
  };

  const handleThemeToggle = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    dispatch(setTheme(newTheme));
  };

  const handleLogout = () => {
    dispatch(logout());
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Settings
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab icon={<PersonIcon />} label="Profile" />
          <Tab icon={<SecurityIcon />} label="Security" />
          <Tab icon={<NotificationsIcon />} label="Notifications" />
          <Tab icon={<CalendarIcon />} label="Calendar" />
          <Tab icon={<PaletteIcon />} label="Appearance" />
          <Tab icon={<LanguageIcon />} label="System" />
          <Tab icon={<StorageIcon />} label="Data" />
        </Tabs>
      </Paper>

      {/* Profile Tab */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Avatar
                  sx={{ width: 120, height: 120, mx: 'auto', mb: 2, bgcolor: 'primary.main' }}
                >
                  {user?.full_name?.split(' ')[0]?.[0]}{user?.full_name?.split(' ')[1]?.[0]}
                </Avatar>
                <Typography variant="h6" fontWeight="bold">
                  {user?.full_name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {user?.role} • {user?.department}
                </Typography>
                <Button variant="outlined" startIcon={<EditIcon />}>
                  Change Photo
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, md: 8 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6" fontWeight="bold">
                    Profile Information
                  </Typography>
                  {!editingProfile ? (
                    <Button
                      variant="outlined"
                      startIcon={<EditIcon />}
                      onClick={() => setEditingProfile(true)}
                    >
                      Edit Profile
                    </Button>
                  ) : (
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        variant="outlined"
                        startIcon={<CancelIcon />}
                        onClick={() => setEditingProfile(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        variant="contained"
                        startIcon={<SaveIcon />}
                        onClick={handleProfileSave}
                      >
                        Save
                      </Button>
                    </Box>
                  )}
                </Box>
                
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="First Name"
                      value={profileData.firstName}
                      onChange={(e) => setProfileData({ ...profileData, firstName: e.target.value })}
                      disabled={!editingProfile}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      value={profileData.lastName}
                      onChange={(e) => setProfileData({ ...profileData, lastName: e.target.value })}
                      disabled={!editingProfile}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Email"
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      disabled={!editingProfile}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                     <TextField
                       fullWidth
                       label="Phone"
                       value={profileData.phone}
                       onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                       disabled={!editingProfile}
                     />
                   </Grid>
                   <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Department"
                      value={profileData.department}
                      disabled
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                     <TextField
                       fullWidth
                       label="Role"
                       value={profileData.role}
                       disabled
                     />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Security Tab */}
      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  Password & Authentication
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Change Password"
                      secondary="Update your account password"
                    />
                    <ListItemSecondaryAction>
                      <Button
                        variant="outlined"
                        onClick={() => setChangePasswordOpen(true)}
                      >
                        Change
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                  <ListItem>
                    <ListItemText
                      primary="Two-Factor Authentication"
                      secondary="Add an extra layer of security"
                    />
                    <ListItemSecondaryAction>
                      <Switch />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                  <ListItem>
                    <ListItemText
                      primary="Login Notifications"
                      secondary="Get notified of new sign-ins"
                    />
                    <ListItemSecondaryAction>
                      <Switch defaultChecked />
                    </ListItemSecondaryAction>
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  Active Sessions
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Current Session"
                      secondary="Windows • Chrome • 192.168.1.100"
                    />
                    <ListItemSecondaryAction>
                      <Chip label="Current" color="success" size="small" />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                  <ListItem>
                    <ListItemText
                      primary="Mobile Session"
                      secondary="iOS • Safari • 2 hours ago"
                    />
                    <ListItemSecondaryAction>
                      <Button size="small" color="error">
                        Revoke
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                </List>
                <Button
                  variant="outlined"
                  color="error"
                  fullWidth
                  sx={{ mt: 2 }}
                  onClick={handleLogout}
                >
                  Sign Out All Devices
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Notifications Tab */}
      <TabPanel value={tabValue} index={2}>
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>
              Notification Preferences
            </Typography>
            
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
                  Communication Channels
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.emailNotifications}
                      onChange={(e) => handleNotificationSettingChange('emailNotifications', e.target.checked)}
                    />
                  }
                  label="Email Notifications"
                  sx={{ display: 'block', mb: 1 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.smsNotifications}
                      onChange={(e) => handleNotificationSettingChange('smsNotifications', e.target.checked)}
                    />
                  }
                  label="SMS Notifications"
                  sx={{ display: 'block', mb: 1 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.pushNotifications}
                      onChange={(e) => handleNotificationSettingChange('pushNotifications', e.target.checked)}
                    />
                  }
                  label="Push Notifications"
                  sx={{ display: 'block' }}
                />
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
                  Notification Types
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.appointmentReminders}
                      onChange={(e) => handleNotificationSettingChange('appointmentReminders', e.target.checked)}
                    />
                  }
                  label="Appointment Reminders"
                  sx={{ display: 'block', mb: 1 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.systemAlerts}
                      onChange={(e) => handleNotificationSettingChange('systemAlerts', e.target.checked)}
                    />
                  }
                  label="System Alerts"
                  sx={{ display: 'block', mb: 1 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.marketingEmails}
                      onChange={(e) => handleNotificationSettingChange('marketingEmails', e.target.checked)}
                    />
                  }
                  label="Marketing Emails"
                  sx={{ display: 'block' }}
                />
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Button variant="contained" startIcon={<SaveIcon />}>
                Save Notification Settings
              </Button>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Calendar Integration Tab */}
      <TabPanel value={tabValue} index={3}>
        <CalendarIntegrationSettings />
      </TabPanel>

      {/* Appearance Tab */}
      <TabPanel value={tabValue} index={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>
              Appearance Settings
            </Typography>
            
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
                  Theme
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={theme === 'dark'}
                      onChange={handleThemeToggle}
                    />
                  }
                  label={`${theme === 'dark' ? 'Dark' : 'Light'} Mode`}
                  sx={{ display: 'block', mb: 2 }}
                />
                
                <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
                  Display
                </Typography>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Font Size</InputLabel>
                  <Select label="Font Size" defaultValue="medium">
                    <MenuItem value="small">Small</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="large">Large</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControl fullWidth>
                  <InputLabel>Sidebar Position</InputLabel>
                  <Select label="Sidebar Position" defaultValue="left">
                    <MenuItem value="left">Left</MenuItem>
                    <MenuItem value="right">Right</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
                  Preview
                </Typography>
                <Paper 
                  sx={{ 
                    p: 2, 
                    bgcolor: theme === 'dark' ? 'grey.900' : 'grey.50',
                    color: theme === 'dark' ? 'white' : 'black',
                    border: 1,
                    borderColor: 'divider'
                  }}
                >
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    Sample Header
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 1 }}>
                    This is how your interface will look with the current theme settings.
                  </Typography>
                  <Button variant="contained" size="small">
                    Sample Button
                  </Button>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* System Tab */}
      <TabPanel value={tabValue} index={5}>
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>
              System Preferences
            </Typography>
            
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={systemSettings.language}
                    label="Language"
                    onChange={(e) => handleSystemSettingChange('language', e.target.value)}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Spanish</MenuItem>
                    <MenuItem value="fr">French</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Timezone</InputLabel>
                  <Select
                    value={systemSettings.timezone}
                    label="Timezone"
                    onChange={(e) => handleSystemSettingChange('timezone', e.target.value)}
                  >
                    <MenuItem value="UTC-8">Pacific Time (UTC-8)</MenuItem>
                    <MenuItem value="UTC-5">Eastern Time (UTC-5)</MenuItem>
                    <MenuItem value="UTC+0">UTC</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Date Format</InputLabel>
                  <Select
                    value={systemSettings.dateFormat}
                    label="Date Format"
                    onChange={(e) => handleSystemSettingChange('dateFormat', e.target.value)}
                  >
                    <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                    <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
                    <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Time Format</InputLabel>
                  <Select
                    value={systemSettings.timeFormat}
                    label="Time Format"
                    onChange={(e) => handleSystemSettingChange('timeFormat', e.target.value)}
                  >
                    <MenuItem value="12h">12 Hour</MenuItem>
                    <MenuItem value="24h">24 Hour</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid size={{ xs: 12 }}>
                <TextField
                  fullWidth
                  type="number"
                  label="Auto Logout (minutes)"
                  value={systemSettings.autoLogout}
                  onChange={(e) => handleSystemSettingChange('autoLogout', parseInt(e.target.value))}
                  helperText="Automatically log out after period of inactivity"
                />
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Button variant="contained" startIcon={<SaveIcon />}>
                Save System Settings
              </Button>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Data Tab */}
      <TabPanel value={tabValue} index={6}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  Data Export
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Download your data in various formats
                </Typography>
                <Button variant="outlined" fullWidth sx={{ mb: 1 }}>
                  Export Patient Data
                </Button>
                <Button variant="outlined" fullWidth sx={{ mb: 1 }}>
                  Export Appointment History
                </Button>
                <Button variant="outlined" fullWidth>
                  Export All Data
                </Button>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  Data Management
                </Typography>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  These actions cannot be undone. Please proceed with caution.
                </Alert>
                <Button variant="outlined" color="error" fullWidth sx={{ mb: 1 }}>
                  Clear Cache
                </Button>
                <Button variant="outlined" color="error" fullWidth sx={{ mb: 1 }}>
                  Reset Preferences
                </Button>
                <Button variant="contained" color="error" fullWidth>
                  Delete Account
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Change Password Dialog */}
      <Dialog open={changePasswordOpen} onClose={() => setChangePasswordOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                type={showPassword ? 'text' : 'password'}
                label="Current Password"
                value={passwordData.currentPassword}
                onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                InputProps={{
                  endAdornment: (
                    <IconButton onClick={() => setShowPassword(!showPassword)}>
                      {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  ),
                }}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                type={showPassword ? 'text' : 'password'}
                label="New Password"
                value={passwordData.newPassword}
                onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                type={showPassword ? 'text' : 'password'}
                label="Confirm New Password"
                value={passwordData.confirmPassword}
                onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChangePasswordOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handlePasswordChange}>
            Change Password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};