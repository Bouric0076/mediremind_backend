import React, { useEffect, useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Pagination,
  LinearProgress,
  Tooltip,
  Badge,
  CardHeader,
  Stack,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Phone as PhoneIcon,
  Add as AddIcon,
  Send as SendIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  BarChart as BarChartIcon,
  Warning as WarningIcon,
  HealthAndSafety as HealthIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';


import { 
  useGetNotificationsQuery, 
  useGetTemplatesQuery,
  useSendNotificationMutation,
  useGetNotificationMetricsQuery,
  useGetSystemHealthQuery,
  useGetRealTimeStatsQuery,
  useGetCurrentUserQuery
} from '../../store/api/apiSlice';

interface Notification {
  id: string;
  type: 'email' | 'sms' | 'phone' | 'push';
  recipient: {
    id: string;
    name: string;
    contact: string;
  };
  subject: string;
  message: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'scheduled' | 'processing' | 'completed' | 'retrying' | 'cancelled';
  scheduledAt?: string;
  sentAt?: string;
  deliveredAt?: string;
  templateId?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: 'appointment' | 'reminder' | 'alert' | 'marketing' | 'system' | 'confirmation' | 'cancellation' | 'manual';
  appointment?: {
    id: string;
    date: string;
    time: string;
    location: string;
  };
  error_message?: string;
  retry_count?: number;
  created_at: string;
}

interface NotificationTemplate {
  id: string;
  name: string;
  type: 'email' | 'sms' | 'phone';
  category: 'appointment' | 'reminder' | 'alert' | 'marketing' | 'system' | 'confirmation' | 'cancellation';
  subject: string;
  content: string;
  variables: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

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
      id={`notification-tabpanel-${index}`}
      aria-labelledby={`notification-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
    case 'delivered':
      return <CheckCircleIcon color="success" />;
    case 'pending':
    case 'scheduled':
      return <ScheduleIcon color="info" />;
    case 'processing':
    case 'retrying':
      return <CircularProgress size={20} />;
    case 'failed':
      return <ErrorIcon color="error" />;
    default:
      return <PendingIcon color="disabled" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
    case 'delivered':
      return 'success';
    case 'pending':
    case 'scheduled':
      return 'info';
    case 'processing':
    case 'retrying':
      return 'warning';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'urgent':
      return 'error';
    case 'high':
      return 'warning';
    case 'medium':
      return 'info';
    case 'low':
      return 'default';
    default:
      return 'default';
  }
};

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'email':
      return <EmailIcon />;
    case 'sms':
      return <SmsIcon />;
    case 'phone':
      return <PhoneIcon />;
    case 'push':
      return <NotificationsIcon />;
    default:
      return <NotificationsIcon />;
  }
};

export const NotificationsPage: React.FC = () => {
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Get current user and hospital context
  const { data: currentUser } = useGetCurrentUserQuery();
  const hospitalId = currentUser?.hospital_id || currentUser?.profile?.hospital_id;
  
  const [tabValue, setTabValue] = useState(0);
  const [newNotificationOpen, setNewNotificationOpen] = useState(false);

  
  // Pagination and filtering state
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [dateRange] = useState<{start?: string; end?: string}>({});
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // New notification form state
  const [newNotification, setNewNotification] = useState({
    type: 'email',
    recipient_id: '',
    subject: '',
    message: '',
    appointment_id: ''
  });

  // API queries
  // API queries with hospital context
  const { 
    data: notificationsData, 
    isLoading: notificationsLoading, 
    error: notificationsError,
    refetch: refetchNotifications 
  } = useGetNotificationsQuery({
    page,
    page_size: 20,
    status: statusFilter || undefined,
    task_type: categoryFilter || undefined,
    delivery_method: typeFilter || undefined
  });

  const { 
    data: templatesData, 
    isLoading: templatesLoading, 
    error: templatesError 
  } = useGetTemplatesQuery();

  // Monitoring queries
  const {
    data: metricsData,
    isLoading: metricsLoading,
    refetch: refetchMetrics
  } = useGetNotificationMetricsQuery({
    start_date: dateRange.start,
    end_date: dateRange.end,
    hospital_id: hospitalId || undefined
  });

  const {
    data: systemHealthData,
    isLoading: systemHealthLoading
  } = useGetSystemHealthQuery();

  const {
    data: realTimeStatsData,
    refetch: refetchRealTimeStats
  } = useGetRealTimeStatsQuery();

  const [sendNotification, { isLoading: sendingNotification }] = useSendNotificationMutation();

  useEffect(() => {
    // Set page title and breadcrumbs
    document.title = 'Notifications - MediRemind';
  }, []);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      refreshIntervalRef.current = setInterval(() => {
        refetchNotifications();
        refetchMetrics();
        refetchRealTimeStats();
      }, 30000); // Refresh every 30 seconds
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoRefresh, refetchNotifications, refetchMetrics, refetchRealTimeStats]);

  const handleRefreshAll = () => {
    refetchNotifications();
    refetchMetrics();
    refetchRealTimeStats();
  };



  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleStatusFilterChange = (event: SelectChangeEvent) => {
    setStatusFilter(event.target.value);
    setPage(1); // Reset to first page when filtering
  };

  const handleTypeFilterChange = (event: SelectChangeEvent) => {
    setTypeFilter(event.target.value);
    setPage(1);
  };

  const handleCategoryFilterChange = (event: SelectChangeEvent) => {
    setCategoryFilter(event.target.value);
    setPage(1);
  };

  const handleSendNotification = async () => {
    try {
      await sendNotification(newNotification).unwrap();
      setNewNotificationOpen(false);
      setNewNotification({
        type: 'email',
        recipient_id: '',
        subject: '',
        message: '',
        appointment_id: ''
      });
      refetchNotifications();
    } catch (error) {
      console.error('Failed to send notification:', error);
    }
  };

  const notifications = notificationsData?.notifications || [];
  const pagination = notificationsData?.pagination;
  const templates = templatesData?.templates || [];

  // Helper functions for metrics display
  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatNumber = (value: number) => value.toLocaleString();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with monitoring controls */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4" component="h1">
            Notifications
          </Typography>
          {hospitalId && (
            <Chip 
              label={`Hospital: ${hospitalId}`} 
              color="primary" 
              size="small"
              icon={<HealthIcon />}
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {/* System Health Indicator */}
          {!systemHealthLoading && systemHealthData && (
            <Tooltip title={`System Status: ${systemHealthData.status}`}>
              <Badge 
                color={getHealthStatusColor(systemHealthData.status) as any}
                variant="dot"
                overlap="circular"
              >
                <HealthIcon />
              </Badge>
            </Tooltip>
          )}
          
          {/* Auto-refresh toggle */}
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                size="small"
              />
            }
            label="Auto-refresh"
            sx={{ ml: 1 }}
          />
          
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshAll}
            disabled={notificationsLoading || metricsLoading}
            size="small"
          >
            Refresh All
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setNewNotificationOpen(true)}
            size="small"
          >
            Send Notification
          </Button>
        </Box>
      </Box>

      {/* Real-time Stats Cards */}
      {!metricsLoading && metricsData && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom variant="body2">
                      Total Notifications
                    </Typography>
                    <Typography variant="h4">
                      {formatNumber(metricsData.total_notifications)}
                    </Typography>
                  </Box>
                  <BarChartIcon color="primary" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom variant="body2">
                      Success Rate
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {formatPercentage(metricsData.success_rate)}
                    </Typography>
                  </Box>
                  <TrendingUpIcon color="success" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom variant="body2">
                      Pending
                    </Typography>
                    <Typography variant="h4" color="warning.main">
                      {formatNumber(metricsData.pending_count)}
                    </Typography>
                  </Box>
                  <PendingIcon color="warning" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom variant="body2">
                      Error Rate
                    </Typography>
                    <Typography variant="h4" color="error.main">
                      {formatPercentage(metricsData.failure_rate)}
                    </Typography>
                  </Box>
                  <TrendingDownIcon color="error" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="All Notifications" />
          <Tab label="Templates" />
          <Tab label="Analytics" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* Filters */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={handleStatusFilterChange}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="processing">Processing</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="retrying">Retrying</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Type</InputLabel>
              <Select
                value={typeFilter}
                label="Type"
                onChange={handleTypeFilterChange}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="email">Email</MenuItem>
                <MenuItem value="sms">SMS</MenuItem>
                <MenuItem value="push">Push</MenuItem>
                <MenuItem value="whatsapp">WhatsApp</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={handleCategoryFilterChange}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="reminder">Reminder</MenuItem>
                <MenuItem value="confirmation">Confirmation</MenuItem>
                <MenuItem value="update">Update</MenuItem>
                <MenuItem value="cancellation">Cancellation</MenuItem>
                <MenuItem value="manual">Manual</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Notifications List */}
          {notificationsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : notificationsError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load notifications. Please try again.
            </Alert>
          ) : notifications.length === 0 ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              No notifications found.
            </Alert>
          ) : (
            <>
              <List>
                {notifications.map((notification: Notification) => (
                  <ListItem key={notification.id} divider>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        {getTypeIcon(notification.type)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">
                            {notification.subject}
                          </Typography>
                          <Chip
                            label={notification.status}
                            size="small"
                            color={getStatusColor(notification.status) as any}
                            icon={getStatusIcon(notification.status)}
                          />
                          <Chip
                            label={notification.priority}
                            size="small"
                            color={getPriorityColor(notification.priority) as any}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            To: {notification.recipient.name} ({notification.recipient.contact})
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {notification.message}
                          </Typography>
                          {notification.appointment && (
                            <Typography variant="body2" color="text.secondary">
                              Appointment: {notification.appointment.date} at {notification.appointment.time}
                              {notification.appointment.location && ` - ${notification.appointment.location}`}
                            </Typography>
                          )}
                          {notification.error_message && (
                            <Typography variant="body2" color="error">
                              Error: {notification.error_message}
                            </Typography>
                          )}
                          <Typography variant="caption" color="text.secondary">
                            Created: {new Date(notification.created_at).toLocaleString()}
                            {notification.retry_count && notification.retry_count > 0 && (
                              ` • Retries: ${notification.retry_count}`
                            )}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton edge="end">
                        <MoreVertIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>

              {/* Pagination */}
              {pagination && pagination.total_pages > 1 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Pagination
                    count={pagination.total_pages}
                    page={page}
                    onChange={handlePageChange}
                    color="primary"
                  />
                </Box>
              )}
            </>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Templates */}
          {templatesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : templatesError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load templates. Please try again.
            </Alert>
          ) : (
            <Grid container spacing={3}>
               {templates.map((template: NotificationTemplate) => (
                 <Grid size={{ xs: 12, md: 6, lg: 4 }} key={template.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                        <Typography variant="h6" component="h3">
                          {template.name}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Chip
                            label={template.type}
                            size="small"
                            color="primary"
                          />
                          <Chip
                            label={template.category}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {template.subject}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {template.content.substring(0, 100)}...
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <FormControlLabel
                          control={<Switch checked={template.isActive} />}
                          label="Active"
                          disabled
                        />
                        <Box>
                          <IconButton size="small">
                            <EditIcon />
                          </IconButton>
                          <IconButton size="small">
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {/* Enhanced Analytics Dashboard */}
          <Grid container spacing={3}>
            {/* Delivery by Type Chart */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardHeader 
                  title="Delivery by Type" 
                  avatar={<BarChartIcon />}
                  action={
                    <Tooltip title="Distribution of notifications by delivery method">
                      <IconButton size="small">
                        <MoreVertIcon />
                      </IconButton>
                    </Tooltip>
                  }
                />
                <CardContent>
                  {metricsData?.delivery_by_type && Object.entries(metricsData.delivery_by_type).length > 0 ? (
                    <Stack spacing={2}>
                      {Object.entries(metricsData.delivery_by_type).map(([type, count]) => (
                        <Box key={type} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Typography variant="body2" sx={{ minWidth: 60, textTransform: 'capitalize' }}>
                            {type}
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={metricsData.total_notifications > 0 ? (count / metricsData.total_notifications) * 100 : 0}
                            sx={{ flex: 1, height: 8, borderRadius: 4 }}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {count}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  ) : (
                    <Alert severity="info">No delivery data available</Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Status Distribution */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardHeader 
                  title="Status Distribution" 
                  avatar={<CheckCircleIcon />}
                />
                <CardContent>
                  {metricsData?.delivery_by_status && Object.entries(metricsData.delivery_by_status).length > 0 ? (
                    <Stack spacing={2}>
                      {Object.entries(metricsData.delivery_by_status).map(([status, count]) => (
                        <Box key={status} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Chip 
                            label={status} 
                            size="small" 
                            color={getStatusColor(status) as any}
                            sx={{ minWidth: 80 }}
                          />
                          <LinearProgress 
                            variant="determinate" 
                            value={metricsData.total_notifications > 0 ? (count / metricsData.total_notifications) * 100 : 0}
                            sx={{ flex: 1, height: 8, borderRadius: 4 }}
                            color={getStatusColor(status) as any}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {count}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  ) : (
                    <Alert severity="info">No status data available</Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Hourly Performance */}
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardHeader 
                  title="Hourly Performance" 
                  avatar={<SpeedIcon />}
                  action={
                    <Stack direction="row" spacing={1}>
                      <Chip label="24h" size="small" variant="outlined" />
                      <Chip label="Success Rate" size="small" color="success" />
                    </Stack>
                  }
                />
                <CardContent>
                  {metricsData?.hourly_stats && metricsData.hourly_stats.length > 0 ? (
                    <Stack spacing={2}>
                      {metricsData.hourly_stats.map((stat) => (
                        <Box key={stat.hour} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Typography variant="body2" sx={{ minWidth: 60 }}>
                            {stat.hour}:00
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ minWidth: 40 }}>
                            {stat.count}
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={stat.success_rate * 100}
                            sx={{ flex: 1, height: 8, borderRadius: 4 }}
                            color={stat.success_rate > 0.9 ? 'success' : stat.success_rate > 0.7 ? 'warning' : 'error'}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {formatPercentage(stat.success_rate)}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  ) : (
                    <Alert severity="info">No hourly data available</Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Real-time System Stats */}
            {realTimeStatsData && (
              <Grid size={{ xs: 12 }}>
                <Card>
                  <CardHeader 
                    title="Real-time System Status" 
                    avatar={<StorageIcon />}
                    action={
                      <Stack direction="row" spacing={1}>
                        {realTimeStatsData.processing_rate && (
                          <Chip 
                            label={`${realTimeStatsData.processing_rate.toFixed(1)}/s`} 
                            size="small" 
                            color="primary" 
                            icon={<SpeedIcon />}
                          />
                        )}
                        {realTimeStatsData.error_rate && (
                          <Chip 
                            label={`${(realTimeStatsData.error_rate * 100).toFixed(1)}% errors`} 
                            size="small" 
                            color={realTimeStatsData.error_rate < 0.05 ? 'success' : 'warning'}
                            icon={<WarningIcon />}
                          />
                        )}
                      </Stack>
                    }
                  />
                  <CardContent>
                    <Grid container spacing={3}>
                      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Active Queues
                        </Typography>
                        <Typography variant="h5">
                          {realTimeStatsData.active_queues}
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Processing Rate
                        </Typography>
                        <Typography variant="h5" color="primary">
                          {realTimeStatsData.processing_rate?.toFixed(1) || 0}/s
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Error Rate
                        </Typography>
                        <Typography variant="h5" color={realTimeStatsData.error_rate < 0.05 ? 'success.main' : 'warning.main'}>
                          {formatPercentage(realTimeStatsData.error_rate || 0)}
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Total Queue Size
                        </Typography>
                        <Typography variant="h5">
                          {Object.values(realTimeStatsData.queue_sizes || {}).reduce((a, b) => a + b, 0)}
                        </Typography>
                      </Grid>
                    </Grid>
                    
                    {realTimeStatsData.recent_errors && realTimeStatsData.recent_errors.length > 0 && (
                      <Box sx={{ mt: 3 }}>
                        <Typography variant="h6" gutterBottom>
                          Recent Errors
                        </Typography>
                        <Stack spacing={1}>
                          {realTimeStatsData.recent_errors.slice(0, 5).map((error, index) => (
                            <Alert key={index} severity="error" sx={{ fontSize: '0.875rem' }}>
                              <Typography variant="caption" display="block" color="text.secondary">
                                {new Date(error.timestamp).toLocaleString()}
                              </Typography>
                              {error.error} (Count: {error.count})
                            </Alert>
                          ))}
                        </Stack>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        </TabPanel>
      </Paper>

      {/* Send Notification Dialog */}
      <Dialog open={newNotificationOpen} onClose={() => setNewNotificationOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Send New Notification</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={newNotification.type}
                label="Type"
                onChange={(e) => setNewNotification({ ...newNotification, type: e.target.value })}
              >
                <MenuItem value="email">Email</MenuItem>
                <MenuItem value="sms">SMS</MenuItem>
                <MenuItem value="push">Push Notification</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              label="Recipient ID"
              value={newNotification.recipient_id}
              onChange={(e) => setNewNotification({ ...newNotification, recipient_id: e.target.value })}
              helperText="Patient or staff ID"
            />
            
            <TextField
              fullWidth
              label="Subject"
              value={newNotification.subject}
              onChange={(e) => setNewNotification({ ...newNotification, subject: e.target.value })}
            />
            
            <TextField
              fullWidth
              label="Message"
              multiline
              rows={4}
              value={newNotification.message}
              onChange={(e) => setNewNotification({ ...newNotification, message: e.target.value })}
            />
            
            <TextField
              fullWidth
              label="Appointment ID (Optional)"
              value={newNotification.appointment_id}
              onChange={(e) => setNewNotification({ ...newNotification, appointment_id: e.target.value })}
              helperText="Link this notification to a specific appointment"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewNotificationOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSendNotification} 
            variant="contained"
            disabled={sendingNotification || !newNotification.recipient_id || !newNotification.message}
            startIcon={sendingNotification ? <CircularProgress size={20} /> : <SendIcon />}
          >
            {sendingNotification ? 'Sending...' : 'Send'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default NotificationsPage;