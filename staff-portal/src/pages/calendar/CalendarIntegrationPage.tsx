/**
 * Calendar Integration Page
 * Dedicated page for users to connect and manage their calendar integrations
 * with clear instructions and visual feedback for the OAuth flow
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Paper,
  Divider,
} from '@mui/material';
import {
  Google as GoogleIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Sync as SyncIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
  Info as InfoIcon,
  Security as SecurityIcon,
  CloudSync as CloudSyncIcon,
  Event as EventIcon,

} from '@mui/icons-material';
import { format } from 'date-fns';
import calendarIntegrationService from '../../services/calendarIntegrationService';
import type { CalendarIntegration } from '../../types/calendar';

const CalendarIntegrationPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [integrations, setIntegrations] = useState<CalendarIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [syncing, setSyncing] = useState<number | null>(null);
  const [resolving, setResolving] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; integration: CalendarIntegration | null }>({
    open: false,
    integration: null,
  });

  const steps = [
    {
      label: 'Connect Your Calendar',
      description: 'Authorize MediRemind to access your Google Calendar',
    },
    {
      label: 'Sync Your Events',
      description: 'Import your existing calendar events to avoid conflicts',
    },
    {
      label: 'Enable Auto-Sync',
      description: 'Keep your calendars synchronized automatically',
    },
  ];

  useEffect(() => {
    loadIntegrations();
    
    // Handle OAuth callback from URL parameters
    const oauthCode = searchParams.get('calendar_oauth_code');
    const oauthState = searchParams.get('calendar_oauth_state');
    
    if (oauthCode && oauthState) {
      handleOAuthCallback(oauthCode, oauthState);
      // Clear the URL parameters after processing
      setSearchParams({});
    }
  }, [searchParams]);

  useEffect(() => {
    // Update active step based on integrations
    if (integrations.length === 0) {
      setActiveStep(0);
    } else if (integrations.some(int => int.last_sync_at)) {
      setActiveStep(2);
    } else {
      setActiveStep(1);
    }
  }, [integrations]);

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      // Use the original method without token refresh to avoid circular dependency
      const data = await calendarIntegrationService.getIntegrationsOriginal();
      setIntegrations(data);
      setError(null);
    } catch (err) {
      setError('Failed to load calendar integrations');
      console.error('Error loading integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthCallback = async (code: string, state: string) => {
    try {
      setConnecting(true);
      setError(null);
      const integration = await calendarIntegrationService.handleOAuthCallback(code, state);
      setIntegrations(prev => [...prev, integration]);
      setSuccess('Google Calendar connected successfully! You can now sync your events.');
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to complete Google Calendar integration. Please try again.');
    } finally {
      setConnecting(false);
    }
  };

  const handleConnectGoogle = async () => {
    try {
      setConnecting(true);
      setError(null);
      const integration = await calendarIntegrationService.openGoogleAuthPopup();
      setIntegrations(prev => [...prev, integration]);
      setSuccess('Google Calendar connected successfully! You can now sync your events.');
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to connect Google Calendar. Please try again.');
    } finally {
      setConnecting(false);
    }
  };

  const handleSync = async (integrationId: number) => {
    try {
      setSyncing(integrationId);
      setError(null);
      
      // Find the specific integration being synced
      const integration = integrations.find(int => int.id === integrationId);
      if (!integration) {
        setError('Integration not found.');
        setSyncing(null);
        return;
      }
      
      // Check if the integration is active and ready for sync
      if (integration.status !== 'active') {
        setError('Please ensure your calendar integration is active before syncing.');
        setSyncing(null);
        return;
      }
      
      await calendarIntegrationService.syncCalendar(integrationId);
      
      // Update the integration's last sync time
      setIntegrations(prev => 
        prev.map(integration => 
          integration.id === integrationId 
            ? { ...integration, last_sync_at: new Date().toISOString() }
            : integration
        )
      );
      setSuccess('Calendar synced successfully! Your events are now up to date.');
      setTimeout(() => setSuccess(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to sync calendar. Please try again.');
    } finally {
      setSyncing(null);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'error': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const handleActivate = async (integrationId: number) => {
    try {
      setResolving(integrationId);
      setError(null);
      
      // Find the specific integration being activated
      const integration = integrations.find(int => int.id === integrationId);
      if (!integration) {
        setError('Integration not found.');
        setResolving(null);
        return;
      }
      
      // For pending integrations, we'll retry the OAuth flow to activate them
      if (integration.status === 'pending') {
        // Redirect to the OAuth flow again
        const authResponse = await calendarIntegrationService.initiateGoogleAuth();
        window.location.href = authResponse.authorization_url;
      } else {
        // For other statuses, refresh the integration status
        await loadIntegrations();
        setSuccess('Integration status refreshed successfully!');
        setTimeout(() => setSuccess(null), 5000);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to activate integration. Please try again.');
    } finally {
      setResolving(null);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/settings')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold">
            Calendar Integration
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Connect your external calendars to sync appointments and avoid scheduling conflicts
          </Typography>
        </Box>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Left Column - Setup Process */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoIcon sx={{ mr: 1 }} />
                Setup Process
              </Typography>
              
              <Stepper activeStep={activeStep} orientation="vertical">
                {steps.map((step, index) => (
                  <Step key={step.label}>
                    <StepLabel>
                      <Typography variant="subtitle1" fontWeight="medium">
                        {step.label}
                      </Typography>
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {step.description}
                      </Typography>
                      
                      {index === 0 && integrations.length === 0 && (
                        <Button
                          variant="contained"
                          startIcon={connecting ? <CircularProgress size={20} /> : <GoogleIcon />}
                          onClick={handleConnectGoogle}
                          disabled={connecting}
                          sx={{ mb: 1 }}
                        >
                          {connecting ? 'Connecting...' : 'Connect Google Calendar'}
                        </Button>
                      )}
                      
                      {index === 1 && integrations.length > 0 && !integrations.some(int => int.last_sync_at) && (
                        <>
                          {integrations.some(int => int.status !== 'active') && (
                            <Alert severity="warning" sx={{ mb: 2 }}>
                              Please ensure your calendar integration is active before syncing events.
                            </Alert>
                          )}
                          <Button
                            variant="contained"
                            startIcon={<SyncIcon />}
                            onClick={() => handleSync(integrations[0].id)}
                            disabled={syncing !== null || integrations.some(int => int.status !== 'active')}
                          >
                            Sync Calendar Events
                          </Button>
                        </>
                      )}
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </CardContent>
          </Card>

          {/* Benefits Card */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <SecurityIcon sx={{ mr: 1 }} />
                Why Connect Your Calendar?
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <EventIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Avoid Double Bookings"
                    secondary="Automatically detect conflicts with your existing appointments"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CloudSyncIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Real-time Synchronization"
                    secondary="Keep all your calendars updated automatically"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <SecurityIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Secure & Private"
                    secondary="Your calendar data is encrypted and never shared"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Right Column - Connected Calendars */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Connected Calendars
              </Typography>
              
              {integrations.length === 0 ? (
                <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'grey.50' }}>
                  <ScheduleIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    No calendars connected yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Connect your Google Calendar to get started
                  </Typography>
                </Paper>
              ) : (
                <List>
                  {integrations.map((integration, index) => (
                    <React.Fragment key={integration.id}>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemIcon>
                          <GoogleIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle1">
                                {integration.calendar_name}
                              </Typography>
                              <Chip
                                size="small"
                                label={integration.status}
                                color={getStatusColor(integration.status) as any}
                                icon={<CheckCircleIcon />}
                              />
                            </Box>
                          }
                          secondary={
                            <>
                              <Typography variant="body2" color="text.secondary" component="span" display="block">
                                Provider: {integration.provider}
                              </Typography>
                              {integration.last_sync_at && (
                                <Typography variant="body2" color="text.secondary" component="span" display="block">
                                  Last synced: {format(new Date(integration.last_sync_at), 'MMM dd, yyyy HH:mm')}
                                </Typography>
                              )}
                            </>
                          }
                        />
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {integration.status === 'pending' && (
                            <Button
                              size="small"
                              variant="contained"
                              color="primary"
                              startIcon={resolving === integration.id ? <CircularProgress size={16} /> : <CheckCircleIcon />}
                              onClick={() => handleActivate(integration.id)}
                              disabled={resolving !== null || connecting}
                              title="Activate calendar integration by completing OAuth setup"
                            >
                              {resolving === integration.id ? 'Activating...' : 'Activate'}
                            </Button>
                          )}
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={syncing === integration.id ? <CircularProgress size={16} /> : <SyncIcon />}
                            onClick={() => handleSync(integration.id)}
                            disabled={syncing !== null || integration.status !== 'active'}
                            title={integration.status !== 'active' ? 'Integration must be active to sync' : 'Sync calendar events'}
                          >
                            {syncing === integration.id ? 'Syncing...' : 'Sync'}
                          </Button>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setDeleteDialog({ open: true, integration })}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      </ListItem>
                      {index < integrations.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
              
              {integrations.length > 0 && (
                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  <Button
                    variant="outlined"
                    startIcon={connecting ? <CircularProgress size={20} /> : <GoogleIcon />}
                    onClick={handleConnectGoogle}
                    disabled={connecting}
                    fullWidth
                  >
                    {connecting ? 'Connecting...' : 'Add Another Calendar'}
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
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
    </Box>
  );
};

export default CalendarIntegrationPage;