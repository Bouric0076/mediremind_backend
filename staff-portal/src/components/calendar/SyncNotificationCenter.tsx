import React, { useState, useEffect } from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Box,
  IconButton,
  Typography,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Button,
  Chip,
  Paper,
  Fade,
} from '@mui/material';
import {
  Close as CloseIcon,
  Sync as SyncIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

export interface SyncNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  details?: string[];
  actions?: {
    label: string;
    action: () => void;
  }[];
  autoHide?: boolean;
  duration?: number;
}

interface SyncNotificationCenterProps {
  notifications: SyncNotification[];
  onDismiss: (id: string) => void;
  onDismissAll: () => void;
  onRetrySync?: () => void;
}

const SyncNotificationCenter: React.FC<SyncNotificationCenterProps> = ({
  notifications,
  onDismiss,
  onDismissAll,
  onRetrySync,
}) => {
  const [expandedNotifications, setExpandedNotifications] = useState<Set<string>>(new Set());
  const [activeNotification, setActiveNotification] = useState<SyncNotification | null>(null);

  // Auto-hide notifications
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];

    notifications.forEach(notification => {
      if (notification.autoHide !== false) {
        const duration = notification.duration || (notification.type === 'error' ? 8000 : 5000);
        const timer = setTimeout(() => {
          onDismiss(notification.id);
        }, duration);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [notifications, onDismiss]);

  // Show the most recent notification as active
  useEffect(() => {
    if (notifications.length > 0) {
      const latest = notifications[notifications.length - 1];
      setActiveNotification(latest);
    } else {
      setActiveNotification(null);
    }
  }, [notifications]);

  const toggleExpanded = (notificationId: string) => {
    setExpandedNotifications(prev => {
      const newSet = new Set(prev);
      if (newSet.has(notificationId)) {
        newSet.delete(notificationId);
      } else {
        newSet.add(notificationId);
      }
      return newSet;
    });
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon />;
      case 'error':
        return <ErrorIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'info':
        return <InfoIcon />;
      default:
        return <SyncIcon />;
    }
  };

  const getSeverity = (type: string): 'success' | 'error' | 'warning' | 'info' => {
    return type as 'success' | 'error' | 'warning' | 'info';
  };

  // Render individual notification
  const renderNotification = (notification: SyncNotification, isActive: boolean = false) => {
    const isExpanded = expandedNotifications.has(notification.id);
    const hasDetails = notification.details && notification.details.length > 0;
    const hasActions = notification.actions && notification.actions.length > 0;

    return (
      <Fade in key={notification.id}>
        <Paper
          elevation={isActive ? 8 : 2}
          sx={{
            mb: 1,
            borderRadius: 2,
            overflow: 'hidden',
            border: isActive ? '2px solid' : '1px solid',
            borderColor: isActive ? `${notification.type}.main` : 'divider',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          <Alert
            severity={getSeverity(notification.type)}
            icon={getIcon(notification.type)}
            sx={{
              '& .MuiAlert-message': { width: '100%' },
              '& .MuiAlert-action': { alignItems: 'flex-start', pt: 0.5 },
            }}
            action={
              <Box display="flex" alignItems="center" gap={1}>
                {(hasDetails || hasActions) && (
                  <IconButton
                    size="small"
                    onClick={() => toggleExpanded(notification.id)}
                    sx={{ color: 'inherit' }}
                  >
                    {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                )}
                <IconButton
                  size="small"
                  onClick={() => onDismiss(notification.id)}
                  sx={{ color: 'inherit' }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Box>
            }
          >
            <AlertTitle sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              {notification.title}
              <Chip
                label={format(notification.timestamp, 'HH:mm:ss')}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            </AlertTitle>
            <Typography variant="body2" sx={{ mb: hasDetails || hasActions ? 1 : 0 }}>
              {notification.message}
            </Typography>

            <Collapse in={isExpanded}>
              {hasDetails && (
                <Box sx={{ mt: 2, mb: hasActions ? 2 : 0 }}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Details:
                  </Typography>
                  <List dense sx={{ py: 0 }}>
                    {notification.details!.map((detail, index) => (
                      <ListItem key={index} sx={{ py: 0.25, px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 20 }}>
                          <Box
                            sx={{
                              width: 4,
                              height: 4,
                              borderRadius: '50%',
                              bgcolor: 'text.secondary',
                            }}
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={detail}
                          primaryTypographyProps={{
                            variant: 'body2',
                            fontSize: '0.85rem',
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {hasActions && (
                <Box display="flex" gap={1} flexWrap="wrap">
                  {notification.actions!.map((action, index) => (
                    <Button
                      key={index}
                      size="small"
                      variant="outlined"
                      onClick={action.action}
                      sx={{ fontSize: '0.75rem' }}
                    >
                      {action.label}
                    </Button>
                  ))}
                </Box>
              )}
            </Collapse>
          </Alert>
        </Paper>
      </Fade>
    );
  };

  // Active notification snackbar
  const activeSnackbar = activeNotification && (
    <Snackbar
      open={!!activeNotification}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      sx={{ mt: 8 }}
    >
      <Box>{renderNotification(activeNotification, true)}</Box>
    </Snackbar>
  );

  // Notification history (for persistent display)
  const notificationHistory = notifications.length > 1 && (
    <Box
      sx={{
        position: 'fixed',
        top: 120,
        right: 24,
        width: 400,
        maxHeight: '60vh',
        overflowY: 'auto',
        zIndex: 1300,
        '&::-webkit-scrollbar': {
          width: 6,
        },
        '&::-webkit-scrollbar-track': {
          background: 'transparent',
        },
        '&::-webkit-scrollbar-thumb': {
          background: 'rgba(0,0,0,0.2)',
          borderRadius: 3,
        },
      }}
    >
      <Paper
        elevation={4}
        sx={{
          p: 2,
          borderRadius: 2,
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="subtitle1" fontWeight={600}>
            Sync Notifications ({notifications.length})
          </Typography>
          <Box display="flex" gap={1}>
            {onRetrySync && (
              <IconButton size="small" onClick={onRetrySync} title="Retry Sync">
                <RefreshIcon fontSize="small" />
              </IconButton>
            )}
            <Button size="small" onClick={onDismissAll}>
              Clear All
            </Button>
          </Box>
        </Box>

        <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
          {notifications
            .slice()
            .reverse()
            .map(notification => renderNotification(notification))}
        </Box>
      </Paper>
    </Box>
  );

  return (
    <>
      {activeSnackbar}
      {notificationHistory}
    </>
  );
};

// Hook for managing sync notifications
export const useSyncNotifications = () => {
  const [notifications, setNotifications] = useState<SyncNotification[]>([]);

  const addNotification = (notification: Omit<SyncNotification, 'id' | 'timestamp'>) => {
    const newNotification: SyncNotification = {
      ...notification,
      id: `sync-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    setNotifications(prev => [...prev, newNotification]);
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const dismissAll = () => {
    setNotifications([]);
  };

  // Predefined notification creators
  const notifySuccess = (title: string, message: string, details?: string[]) => {
    addNotification({
      type: 'success',
      title,
      message,
      details,
      autoHide: true,
      duration: 4000,
    });
  };

  const notifyError = (title: string, message: string, details?: string[], actions?: SyncNotification['actions']) => {
    addNotification({
      type: 'error',
      title,
      message,
      details,
      actions,
      autoHide: false, // Errors should be manually dismissed
    });
  };

  const notifyWarning = (title: string, message: string, details?: string[]) => {
    addNotification({
      type: 'warning',
      title,
      message,
      details,
      autoHide: true,
      duration: 6000,
    });
  };

  const notifyInfo = (title: string, message: string, details?: string[]) => {
    addNotification({
      type: 'info',
      title,
      message,
      details,
      autoHide: true,
      duration: 5000,
    });
  };

  const notifySyncStart = () => {
    notifyInfo('Sync Started', 'Synchronizing with external calendars...');
  };

  const notifySyncComplete = (syncedCount: number, conflictCount: number = 0) => {
    if (conflictCount > 0) {
      notifyWarning(
        'Sync Completed with Conflicts',
        `Synced ${syncedCount} events, but found ${conflictCount} conflicts that need resolution.`,
        [`${syncedCount} events synchronized`, `${conflictCount} conflicts detected`]
      );
    } else {
      notifySuccess(
        'Sync Completed',
        `Successfully synchronized ${syncedCount} events from external calendars.`,
        [`${syncedCount} events synchronized`, 'No conflicts detected']
      );
    }
  };

  const notifySyncError = (error: string, retryAction?: () => void) => {
    notifyError(
      'Sync Failed',
      'Failed to synchronize with external calendars.',
      [error],
      retryAction ? [{ label: 'Retry', action: retryAction }] : undefined
    );
  };

  return {
    notifications,
    addNotification,
    dismissNotification,
    dismissAll,
    notifySuccess,
    notifyError,
    notifyWarning,
    notifyInfo,
    notifySyncStart,
    notifySyncComplete,
    notifySyncError,
  };
};

export default SyncNotificationCenter;