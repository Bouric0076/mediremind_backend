/**
 * Calendar Integration Settings Component
 * Allows staff to connect and manage their Google Calendar integrations
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Divider,
  Grid,
  TextField,
  Tooltip,
} from '@mui/material';
import {
  Google as GoogleIcon,
  Sync as SyncIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import calendarIntegrationService from '../../services/calendarIntegrationService';
import type { CalendarIntegration } from '../../types/calendar';

const CalendarIntegrationSettings: React.FC = () => {
  const [integrations, setIntegrations] = useState<CalendarIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [hasGoogleConnection, setHasGoogleConnection] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; integration: CalendarIntegration | null }>({
    open: false,
    integration: null,
  });
  const [settingsDialog, setSettingsDialog] = useState<{ open: boolean; integration: CalendarIntegration | null }>({
    open: false,
    integration: null,
  });

  useEffect(() => {
    loadIntegrations();
  }, []);

  useEffect(() => {
    // Check if user has an active Google Calendar connection
    const hasActiveGoogleConnection = integrations.some(
      integration => integration.provider === 'google' && integration.status === 'active'
    );
    setHasGoogleConnection(hasActiveGoogleConnection);

    // Auto-disable sync for all integrations if no Google Calendar connection
    if (!hasActiveGoogleConnection && integrations.length > 0) {
      const syncEnabledIntegrations = integrations.filter(int => int.sync_enabled);
      if (syncEnabledIntegrations.length > 0) {
        // Disable sync for all integrations
        syncEnabledIntegrations.forEach(async (integration) => {
          try {
            const updated = await calendarIntegrationService.updateIntegration(
              integration.id,
              { sync_enabled: false }
            );
            setIntegrations(prev => 
              prev.map(int => int.id === integration.id ? updated : int)
            );
          } catch (err) {
            console.error('Failed to auto-disable sync for integration:', integration.id, err);
          }
        });
      }
    }
  }, [integrations]);

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      const data = await calendarIntegrationService.getIntegrations();
      setIntegrations(data);
      setError(null);
    } catch (err) {
      setError('Failed to load calendar integrations');
      console.error('Error loading integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectGoogle = async () => {
    try {
      setError(null);
      const integration = await calendarIntegrationService.openGoogleAuthPopup();
      setIntegrations(prev => [...prev, integration]);
      setSuccess('Google Calendar connected successfully!');
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to connect Google Calendar');
    }
  };

  const handleSync = async (integrationId: number) => {
    try {
      setSyncing(integrationId);
      setError(null);
      await calendarIntegrationService.syncCalendar(integrationId);
      
      // Update the integration's last sync time
      setIntegrations(prev => 
        prev.map(integration => 
          integration.id === integrationId 
            ? { ...integration, last_sync_at: new Date().toISOString() }
            : integration
        )
      );
      setSuccess('Calendar synced successfully!');
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to sync calendar');
    } finally {
      setSyncing(null);
    }
  };

  const handleToggleSync = async (integration: CalendarIntegration) => {
    // Prevent enabling sync if no Google Calendar connection
    if (!integration.sync_enabled && !hasGoogleConnection) {
      setError('Please connect your Google Calendar first before enabling sync.');
      return;
    }

    try {
      const updated = await calendarIntegrationService.updateIntegration(
        integration.id,
        { sync_enabled: !integration.sync_enabled }
      );
      setIntegrations(prev => 
        prev.map(int => int.id === integration.id ? updated : int)
      );
    } catch (err: any) {
      setError(err.message || 'Failed to update sync settings');
    }
  };

  const handleDelete = async () => {
    if (!deleteDialog.integration) return;
    
    try {
      await calendarIntegrationService.deleteIntegration(deleteDialog.integration.id);
      setIntegrations(prev => prev.filter(int => int.id !== deleteDialog.integration!.id));
      setDeleteDialog({ open: false, integration: null });
      setSuccess('Calendar integration removed successfully!');
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to remove integration');
    }
  };

  const handleUpdateSettings = async (integration: CalendarIntegration, calendarName: string) => {
    try {
      const updated = await calendarIntegrationService.updateIntegration(
        integration.id,
        { calendar_name: calendarName }
      );
      setIntegrations(prev => 
        prev.map(int => int.id === integration.id ? updated : int)
      );
      setSettingsDialog({ open: false, integration: null });
      setSuccess('Settings updated successfully!');
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to update settings');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'error': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircleIcon />;
      case 'error': return <ErrorIcon />;
      default: return <ScheduleIcon />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Calendar Integrations
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Connect your external calendars to sync appointments and avoid scheduling conflicts.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Warning when no Google Calendar is connected */}
      {!hasGoogleConnection && integrations.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
           <strong>Connect your Google Calendar</strong> to enable automatic appointment syncing and avoid scheduling conflicts.
          </Typography>
        </Alert>
      )}

      {!hasGoogleConnection && integrations.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Google Calendar not connected.</strong> Auto-sync has been disabled. Please connect your Google Calendar to enable syncing.
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Connect New Calendar */}
        <Grid size={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Connect Calendar
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Connect your Google Calendar to automatically sync appointments.
              </Typography>
              <Button
                variant="contained"
                startIcon={<GoogleIcon />}
                onClick={handleConnectGoogle}
                sx={{ mr: 2 }}
              >
                Connect Google Calendar
              </Button>
              <Button
                variant="outlined"
                disabled
                sx={{ opacity: 0.5 }}
              >
                Outlook Calendar (Coming Soon)
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Existing Integrations */}
        {integrations.length > 0 && (
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Connected Calendars
                </Typography>
                <List>
                  {integrations.map((integration, index) => (
                    <React.Fragment key={integration.id}>
                      <ListItem>
                        <Box display="flex" alignItems="center" mr={2}>
                          <GoogleIcon color="primary" />
                        </Box>
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center" gap={1}>
                              <Typography variant="subtitle1">
                                {integration.calendar_name}
                              </Typography>
                              <Chip
                                size="small"
                                label={integration.status}
                                color={getStatusColor(integration.status) as any}
                                icon={getStatusIcon(integration.status)}
                              />
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                Calendar ID: {integration.calendar_id}
                              </Typography>
                              {integration.last_sync_at && (
                                <Typography variant="body2" color="text.secondary">
                                  Last synced: {format(new Date(integration.last_sync_at), 'PPp')}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <Box display="flex" alignItems="center" gap={1}>
                            <FormControlLabel
                              control={
                                <Switch
                                  checked={integration.sync_enabled}
                                  onChange={() => handleToggleSync(integration)}
                                  size="small"
                                />
                              }
                              label="Sync"
                              labelPlacement="start"
                            />
                            <Tooltip title="Sync Now">
                              <IconButton
                                onClick={() => handleSync(integration.id)}
                                disabled={syncing === integration.id || !integration.sync_enabled}
                                size="small"
                              >
                                {syncing === integration.id ? (
                                  <CircularProgress size={20} />
                                ) : (
                                  <SyncIcon />
                                )}
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Settings">
                              <IconButton
                                onClick={() => setSettingsDialog({ open: true, integration })}
                                size="small"
                              >
                                <SettingsIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Remove">
                              <IconButton
                                onClick={() => setDeleteDialog({ open: true, integration })}
                                size="small"
                                color="error"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </ListItemSecondaryAction>
                      </ListItem>
                      {index < integrations.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, integration: null })}
      >
        <DialogTitle>Remove Calendar Integration</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove the integration with "{deleteDialog.integration?.calendar_name}"?
            This will stop syncing events from this calendar.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, integration: null })}>
            Cancel
          </Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Remove
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog
        open={settingsDialog.open}
        onClose={() => setSettingsDialog({ open: false, integration: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Calendar Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Calendar Name"
              defaultValue={settingsDialog.integration?.calendar_name}
              variant="outlined"
              id="calendar-name-input"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialog({ open: false, integration: null })}>
            Cancel
          </Button>
          <Button
            onClick={() => {
              const input = document.getElementById('calendar-name-input') as HTMLInputElement;
              if (settingsDialog.integration && input) {
                handleUpdateSettings(settingsDialog.integration, input.value);
              }
            }}
            variant="contained"
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CalendarIntegrationSettings;