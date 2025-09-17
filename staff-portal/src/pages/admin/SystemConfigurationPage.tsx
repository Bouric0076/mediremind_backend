import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Switch,
  FormControlLabel,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,

  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,

} from '@mui/material';
import {
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,

  CloudSync as BackupIcon,

  Edit as EditIcon,
  Save as SaveIcon,

  Warning as WarningIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import type { RootState } from '../../store';

interface ConfigSection {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  settings: ConfigSetting[];
}

interface ConfigSetting {
  id: string;
  name: string;
  description: string;
  type: 'boolean' | 'text' | 'number' | 'select';
  value: any;
  options?: string[];
  required?: boolean;
  sensitive?: boolean;
}

const mockConfigSections: ConfigSection[] = [
  {
    id: 'general',
    title: 'General Settings',
    description: 'Basic system configuration',
    icon: <SettingsIcon />,
    settings: [
      {
        id: 'system_name',
        name: 'System Name',
        description: 'Display name for the healthcare system',
        type: 'text',
        value: 'MediRemind Healthcare Portal',
        required: true,
      },
      {
        id: 'maintenance_mode',
        name: 'Maintenance Mode',
        description: 'Enable maintenance mode to restrict access',
        type: 'boolean',
        value: false,
      },
      {
        id: 'session_timeout',
        name: 'Session Timeout (minutes)',
        description: 'Automatic logout time for inactive users',
        type: 'number',
        value: 30,
        required: true,
      },
    ],
  },
  {
    id: 'security',
    title: 'Security Settings',
    description: 'Authentication and security configuration',
    icon: <SecurityIcon />,
    settings: [
      {
        id: 'two_factor_auth',
        name: 'Two-Factor Authentication',
        description: 'Require 2FA for all users',
        type: 'boolean',
        value: true,
      },
      {
        id: 'password_policy',
        name: 'Password Policy',
        description: 'Minimum password requirements',
        type: 'select',
        value: 'strong',
        options: ['basic', 'medium', 'strong'],
      },
      {
        id: 'login_attempts',
        name: 'Max Login Attempts',
        description: 'Maximum failed login attempts before lockout',
        type: 'number',
        value: 5,
        required: true,
      },
    ],
  },
  {
    id: 'notifications',
    title: 'Notification Settings',
    description: 'Email and push notification configuration',
    icon: <NotificationsIcon />,
    settings: [
      {
        id: 'email_notifications',
        name: 'Email Notifications',
        description: 'Enable system email notifications',
        type: 'boolean',
        value: true,
      },
      {
        id: 'smtp_server',
        name: 'SMTP Server',
        description: 'Email server configuration',
        type: 'text',
        value: 'smtp.hospital.com',
        sensitive: true,
      },
      {
        id: 'notification_frequency',
        name: 'Notification Frequency',
        description: 'How often to send reminder notifications',
        type: 'select',
        value: 'daily',
        options: ['hourly', 'daily', 'weekly'],
      },
    ],
  },
  {
    id: 'backup',
    title: 'Backup & Storage',
    description: 'Data backup and storage settings',
    icon: <BackupIcon />,
    settings: [
      {
        id: 'auto_backup',
        name: 'Automatic Backup',
        description: 'Enable scheduled automatic backups',
        type: 'boolean',
        value: true,
      },
      {
        id: 'backup_frequency',
        name: 'Backup Frequency',
        description: 'How often to perform backups',
        type: 'select',
        value: 'daily',
        options: ['hourly', 'daily', 'weekly', 'monthly'],
      },
      {
        id: 'retention_days',
        name: 'Backup Retention (days)',
        description: 'How long to keep backup files',
        type: 'number',
        value: 30,
        required: true,
      },
    ],
  },
];

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`config-tabpanel-${index}`}
      aria-labelledby={`config-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SystemConfigurationPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [configValues, setConfigValues] = useState<Record<string, any>>({});
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleConfigChange = (settingId: string, value: any) => {
    setConfigValues(prev => ({ ...prev, [settingId]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    setSaveDialogOpen(true);
  };

  const confirmSave = () => {
    // Here you would typically save to backend
    console.log('Saving configuration:', configValues);
    setSaveDialogOpen(false);
    setHasChanges(false);
    setEditMode(false);
  };

  const renderSetting = (setting: ConfigSetting) => {
    const currentValue = configValues[setting.id] ?? setting.value;

    switch (setting.type) {
      case 'boolean':
        return (
          <FormControlLabel
            control={
              <Switch
                checked={currentValue}
                onChange={(e) => handleConfigChange(setting.id, e.target.checked)}
                disabled={!editMode}
              />
            }
            label={setting.name}
          />
        );
      case 'text':
        return (
          <TextField
            fullWidth
            label={setting.name}
            value={currentValue}
            onChange={(e) => handleConfigChange(setting.id, e.target.value)}
            disabled={!editMode}
            type={setting.sensitive ? 'password' : 'text'}
            required={setting.required}
            helperText={setting.description}
          />
        );
      case 'number':
        return (
          <TextField
            fullWidth
            label={setting.name}
            type="number"
            value={currentValue}
            onChange={(e) => handleConfigChange(setting.id, parseInt(e.target.value))}
            disabled={!editMode}
            required={setting.required}
            helperText={setting.description}
          />
        );
      case 'select':
        return (
          <FormControl fullWidth>
            <InputLabel>{setting.name}</InputLabel>
            <Select
              value={currentValue}
              label={setting.name}
              onChange={(e) => handleConfigChange(setting.id, e.target.value)}
              disabled={!editMode}
            >
              {setting.options?.map((option) => (
                <MenuItem key={option} value={option}>
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );
      default:
        return null;
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            System Configuration
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage system settings and configuration
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {hasChanges && (
            <Alert severity="warning" sx={{ mr: 2 }}>
              You have unsaved changes
            </Alert>
          )}
          {editMode ? (
            <>
              <Button
                variant="outlined"
                onClick={() => {
                  setEditMode(false);
                  setConfigValues({});
                  setHasChanges(false);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSave}
                disabled={!hasChanges}
              >
                Save Changes
              </Button>
            </>
          ) : (
            <Button
              variant="contained"
              startIcon={<EditIcon />}
              onClick={() => setEditMode(true)}
            >
              Edit Configuration
            </Button>
          )}
        </Box>
      </Box>

      {/* Warning for sensitive settings */}
      {editMode && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">Warning</Typography>
          Changing system configuration may affect system functionality. Please review changes carefully before saving.
        </Alert>
      )}

      {/* Configuration Sections */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            {mockConfigSections.map((section) => (
              <Tab key={section.id} label={section.title} />
            ))}
          </Tabs>
        </Box>

        {mockConfigSections.map((section, index) => (
          <TabPanel key={section.id} value={tabValue} index={index}>
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {section.icon}
                <Box sx={{ ml: 2 }}>
                  <Typography variant="h6">{section.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {section.description}
                  </Typography>
                </Box>
              </Box>
              <Divider />
            </Box>

            <Grid container spacing={3}>
              {section.settings.map((setting) => (
                <Grid size={{ xs: 12, md: 6 }} key={setting.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          {setting.name}
                          {setting.required && (
                            <Chip label="Required" size="small" color="error" sx={{ ml: 1 }} />
                          )}
                          {setting.sensitive && (
                            <Chip label="Sensitive" size="small" color="warning" sx={{ ml: 1 }} />
                          )}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {setting.description}
                        </Typography>
                      </Box>
                      {renderSetting(setting)}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </TabPanel>
        ))}
      </Paper>

      {/* Save Confirmation Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <WarningIcon color="warning" sx={{ mr: 1 }} />
            Confirm Configuration Changes
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to save these configuration changes?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Some changes may require a system restart to take effect.
          </Typography>
          {Object.keys(configValues).length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Changes to be saved:
              </Typography>
              <List dense>
                {Object.entries(configValues).map(([key, value]) => {
                  const setting = mockConfigSections
                    .flatMap(s => s.settings)
                    .find(s => s.id === key);
                  return (
                    <ListItem key={key}>
                      <ListItemText
                        primary={setting?.name || key}
                        secondary={`New value: ${value}`}
                      />
                    </ListItem>
                  );
                })}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={confirmSave} color="primary">
            Save Configuration
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SystemConfigurationPage;