import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Button,
  Tooltip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Switch,
  Divider,
} from '@mui/material';
import {
  Sync as SyncIcon,
  SyncProblem as SyncProblemIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,

  CloudSync as CloudSyncIcon,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';
import type { CalendarIntegration } from '../../types/calendar';
import { calendarIntegrationService } from '../../services/calendarIntegrationService';

interface SyncStatusIndicatorProps {
  onSettingsClick?: () => void;
  compact?: boolean;
}

const SyncStatusIndicator: React.FC<SyncStatusIndicatorProps> = ({
  onSettingsClick,
  compact = false,
}) => {
  const [integrations, setIntegrations] = useState<CalendarIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detailsDialog, setDetailsDialog] = useState<{
    open: boolean;
    integration: CalendarIntegration | null;
  }>({ open: false, integration: null });

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await calendarIntegrationService.getIntegrations();
      setIntegrations(data);
    } catch (err) {
      setError('Failed to load calendar integrations');
      console.error('Error loading integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleManualSync = async (integrationId: string) => {
    try {
      setSyncing(integrationId);
      setError(null);
      await calendarIntegrationService.syncCalendar(Number(integrationId));
      await loadIntegrations(); // Refresh data
    } catch (err) {
      setError('Failed to sync calendar');
      console.error('Error syncing calendar:', err);
    } finally {
      setSyncing(null);
    }
  };

  const handleToggleSync = async (integrationId: string, enabled: boolean) => {
    try {
      await calendarIntegrationService.updateIntegration(Number(integrationId), {
        sync_enabled: enabled,
      });
      await loadIntegrations();
    } catch (err) {
      setError('Failed to update sync settings');
      console.error('Error updating sync settings:', err);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'pending':
        return <SyncIcon color="warning" />;
      case 'inactive':
        return <SyncProblemIcon color="disabled" />;
      default:
        return <WarningIcon color="warning" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'error':
        return 'error';
      case 'pending':
        return 'warning';
      case 'inactive':
        return 'default';
      default:
        return 'warning';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active';
      case 'error':
        return 'Error';
      case 'pending':
        return 'Syncing';
      case 'inactive':
        return 'Inactive';
      default:
        return 'Unknown';
    }
  };

  if (loading) {
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={24} />
            <Typography>Loading calendar sync status...</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (integrations.length === 0) {
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={2}>
              <CloudSyncIcon color="disabled" />
              <Typography color="text.secondary">
                No calendar integrations configured
              </Typography>
            </Box>
            {onSettingsClick && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<SettingsIcon />}
                onClick={onSettingsClick}
              >
                Setup Integration
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    const activeIntegrations = integrations.filter(i => i.sync_enabled);
    const hasErrors = integrations.some(i => i.sync_status === 'error');
    const isPending = integrations.some(i => i.sync_status === 'pending');

    return (
      <Box display="flex" alignItems="center" gap={1}>
        <Tooltip title={`${activeIntegrations.length} calendar(s) synced`}>
          <Chip
            icon={hasErrors ? <ErrorIcon /> : isPending ? <SyncIcon /> : <CheckCircleIcon />}
            label={`${activeIntegrations.length} synced`}
            color={hasErrors ? 'error' : isPending ? 'warning' : 'success'}
            size="small"
            variant="outlined"
          />
        </Tooltip>
        {onSettingsClick && (
          <IconButton size="small" onClick={onSettingsClick}>
            <SettingsIcon fontSize="small" />
          </IconButton>
        )}
      </Box>
    );
  }

  return (
    <>
      <Card sx={{ mb: 1, maxWidth: 400 }}>
        <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
            <Typography variant="subtitle2" display="flex" alignItems="center" gap={1} fontSize="0.875rem">
              <CloudSyncIcon fontSize="small" />
              Calendar Sync Status
            </Typography>
            {onSettingsClick && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<SettingsIcon />}
                onClick={onSettingsClick}
                sx={{ fontSize: '0.75rem', py: 0.5, px: 1 }}
              >
                Manage
              </Button>
            )}
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 1, py: 0.5 }} onClose={() => setError(null)}>
              <Typography variant="caption">{error}</Typography>
            </Alert>
          )}

          <List disablePadding sx={{ '& .MuiListItem-root': { py: 0.5 } }}>
            {integrations.map((integration, index) => (
              <React.Fragment key={integration.id}>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {getStatusIcon(integration.sync_status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Typography variant="body2" fontWeight={500}>
                          {integration.calendar_name}
                        </Typography>
                        <Chip
                          label={integration.provider.toUpperCase()}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.65rem', height: 20 }}
                        />
                        <Chip
                          label={getStatusText(integration.sync_status)}
                          size="small"
                          color={getStatusColor(integration.sync_status) as any}
                          sx={{ fontSize: '0.65rem', height: 20 }}
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        {integration.last_sync && (
                          <Typography variant="caption" display="block" fontSize="0.7rem">
                            Last sync: {formatDistanceToNow(new Date(integration.last_sync))} ago
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <Switch
                        checked={integration.sync_enabled}
                        onChange={(e) => handleToggleSync(integration.id.toString(), e.target.checked)}
                        size="small"
                      />
                      <Tooltip title="Manual sync">
                        <IconButton
                          size="small"
                          onClick={() => handleManualSync(integration.id.toString())}
                          disabled={syncing === integration.id.toString() || !integration.sync_enabled}
                          sx={{ p: 0.5 }}
                        >
                          {syncing === integration.id.toString() ? (
                            <CircularProgress size={14} />
                          ) : (
                            <RefreshIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < integrations.length - 1 && <Divider sx={{ my: 0.5 }} />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog
        open={detailsDialog.open}
        onClose={() => setDetailsDialog({ open: false, integration: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Calendar Integration Details
        </DialogTitle>
        <DialogContent>
          {detailsDialog.integration && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {detailsDialog.integration.calendar_name}
              </Typography>
              
              <Box display="flex" gap={1} mb={2}>
                <Chip
                  label={detailsDialog.integration.provider.toUpperCase()}
                  variant="outlined"
                />
                <Chip
                  label={getStatusText(detailsDialog.integration.sync_status)}
                  color={getStatusColor(detailsDialog.integration.sync_status) as any}
                />
              </Box>

              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>Calendar ID:</strong> {detailsDialog.integration.calendar_id}
              </Typography>

              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>Sync Enabled:</strong> {detailsDialog.integration.sync_enabled ? 'Yes' : 'No'}
              </Typography>

              {detailsDialog.integration.last_sync && (
                <Typography variant="body2" color="text.secondary" paragraph>
                  <strong>Last Sync:</strong> {format(new Date(detailsDialog.integration.last_sync), 'MMM d, yyyy h:mm a')}
                </Typography>
              )}

              {detailsDialog.integration.next_sync && (
                <Typography variant="body2" color="text.secondary" paragraph>
                  <strong>Next Sync:</strong> {format(new Date(detailsDialog.integration.next_sync), 'MMM d, yyyy h:mm a')}
                </Typography>
              )}

              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>Token Expires:</strong> {detailsDialog.integration.token_expiry ? format(new Date(detailsDialog.integration.token_expiry), 'MMM d, yyyy h:mm a') : 'N/A'}
              </Typography>

              <Typography variant="body2" color="text.secondary">
                <strong>Created:</strong> {format(new Date(detailsDialog.integration.created_at), 'MMM d, yyyy h:mm a')}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialog({ open: false, integration: null })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default SyncStatusIndicator;