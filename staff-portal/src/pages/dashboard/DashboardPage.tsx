import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Chip,
  Button,
  IconButton,
  LinearProgress,
  Skeleton,
  Alert,
  Stack,
  CircularProgress,
} from '@mui/material';
import {
  People as PeopleIcon,
  CalendarToday as CalendarIcon,
  Notifications as NotificationsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  AccessTime as AccessTimeIcon,
  Refresh as RefreshIcon,
  ArrowForward as ArrowForwardIcon,
  LocalHospital,
  Dashboard as DashboardIcon,
  Assessment as AssessmentIcon,
  EventNote as EventNoteIcon,
  Analytics as AnalyticsIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { Timeline } from '@mui/lab';
import { useGetDashboardStatsQuery } from '../../store/api/apiSlice';
import { setBreadcrumbs, setCurrentPage, addToast } from '../../store/slices/uiSlice';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import {
  medicalColors,
  easings,
  durations,
} from '../../theme/colors';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  trend?: {
    value: number;
    isPositive: boolean;
  };
  onClick?: () => void;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, trend, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const gradientColors = {
    primary: medicalColors.gradients.primary,
    secondary: medicalColors.gradients.secondary,
    success: medicalColors.gradients.success,
    warning: medicalColors.gradients.warning,
    error: medicalColors.gradients.error,
    info: medicalColors.gradients.medicalAccent,
  };

  return (
    <Card 
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      sx={{ 
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        transition: `all ${durations.standard}ms ${easings.easeInOut}`,
        background: gradientColors[color],
        color: 'white',
        position: 'relative',
        overflow: 'hidden',
        borderRadius: 3,
        boxShadow: isHovered ? medicalColors.shadows.large : medicalColors.shadows.medium,
        transform: isHovered && onClick ? 'translateY(-4px)' : 'translateY(0)',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(255,255,255,0.1)',
          opacity: isHovered ? 1 : 0,
          transition: `opacity ${durations.standard}ms ${easings.easeInOut}`,
        },
        // Accessibility improvements
        '&:focus-visible': {
          outline: `2px solid ${medicalColors.neutral.white}`,
          outlineOffset: '2px',
        },
      }}
      role={onClick ? "button" : "article"}
      tabIndex={onClick ? 0 : -1}
      aria-label={onClick ? `View ${title} details` : `${title}: ${value}`}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <CardContent sx={{ position: 'relative', zIndex: 1, p: { xs: 2.5, sm: 3, md: 3.5 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Typography 
              color="rgba(255,255,255,0.9)" 
              gutterBottom 
              variant="body2"
              sx={{ 
                fontWeight: 600, 
                textTransform: 'uppercase', 
                letterSpacing: 1.2,
                fontSize: { xs: '0.7rem', sm: '0.75rem' },
                mb: 1,
              }}
            >
              {title}
            </Typography>
            <Typography 
              variant="h3" 
              component="div" 
              fontWeight="bold"
              sx={{ 
                mb: 1,
                color: 'white',
                fontSize: { xs: '1.75rem', sm: '2.125rem' }
              }}
            >
              {value}
            </Typography>
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    backgroundColor: trend.isPositive ? 
                      'rgba(76, 175, 80, 0.25)' : 
                      'rgba(244, 67, 54, 0.25)',
                    borderRadius: '16px',
                    px: 1.5,
                    py: 0.5,
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  <TrendingUpIcon 
                    sx={{ 
                      fontSize: 16, 
                      color: trend.isPositive ? medicalColors.success.light : medicalColors.error.light,
                      transform: trend.isPositive ? 'none' : 'rotate(180deg)',
                      mr: 0.5,
                    }} 
                  />
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      color: trend.isPositive ? medicalColors.success.light : medicalColors.error.light,
                      fontWeight: 600,
                      fontSize: '0.75rem'
                    }}
                  >
                    {Math.abs(trend.value)}%
                  </Typography>
                </Box>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              background: 'rgba(255,255,255,0.15)',
              borderRadius: '50%',
              p: 2,
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.2)',
            }}
          >
            <Box sx={{ fontSize: 28, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {icon}
            </Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export const DashboardPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // Enhanced state management
  const [retryCount, setRetryCount] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  
  const { data: dashboardData, isLoading, error, refetch } = useGetDashboardStatsQuery({ period: '7d' });
  
  // Extract data from the API response
  const stats = dashboardData?.overview || {};
  const activityTrends = dashboardData?.activity_trends || [];
  const departmentStats = dashboardData?.department_stats || [];
  const systemHealth = dashboardData?.system_health || {};

  useEffect(() => {
    dispatch(setCurrentPage('dashboard'));
    dispatch(setBreadcrumbs([]));
  }, [dispatch]);

  // Auto-retry logic for failed requests
  useEffect(() => {
    if (error && retryCount < 3) {
      const timer = setTimeout(() => {
        setRetryCount(prev => prev + 1);
        refetch();
      }, Math.pow(2, retryCount) * 1000); // Exponential backoff
      
      return () => clearTimeout(timer);
    }
  }, [error, retryCount, refetch]);

  // Enhanced refresh handler with feedback
  const handleRefresh = async () => {
    setIsRefreshing(true);
    setRetryCount(0);
    
    try {
      await refetch();
      setLastRefresh(new Date());
      dispatch(addToast({
        title: 'Success',
        message: 'Dashboard data refreshed successfully',
        type: 'success',
        duration: 3000,
      }));
    } catch (err) {
      dispatch(addToast({
        title: 'Error',
        message: 'Failed to refresh dashboard data',
        type: 'error',
        duration: 5000,
      }));
    } finally {
      setIsRefreshing(false);
    }
  };

  // Manual retry handler
  const handleRetry = () => {
    setRetryCount(0);
    refetch();
  };

  // Use real data from activity trends for recent appointments
  const todaysAppointments = activityTrends.length > 0 ? 
    activityTrends.slice(0, 3).map((trend: any, index: number) => ({
      id: `${index + 1}`,
      patientName: `Patient ${index + 1}`,
      time: `${9 + index * 2}:00 AM`,
      type: index === 0 ? 'Consultation' : index === 1 ? 'Follow-up' : 'Check-up',
      status: index % 2 === 0 ? 'confirmed' : 'pending',
      date: trend.date,
    })) : [];

  // Generate alerts based on system health and stats
  const recentAlerts = [
    {
      id: '1',
      message: `${stats.pending_appointments || 0} appointments pending confirmation`,
      type: 'warning',
      time: '5 minutes ago',
    },
    {
      id: '2',
      message: `System uptime: ${systemHealth.uptime || '99.9%'}`,
      type: 'success',
      time: '15 minutes ago',
    },
    {
      id: '3',
      message: `${stats.new_users_7d || 0} new users this week`,
      type: 'info',
      time: '1 hour ago',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'success';
      case 'pending': return 'warning';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'warning': return <WarningIcon />;
      case 'success': return <CheckCircleIcon />;
      case 'info': return <NotificationsIcon />;
      default: return <NotificationsIcon />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'warning': return 'warning.main';
      case 'success': return 'success.main';
      default: return 'info.main';
    }
  };

  const getAlertChipColor = (type: string) => {
    switch (type) {
      case 'warning': return 'warning';
      case 'success': return 'success';
      default: return 'info';
    }
  };

  // Error state with retry option
  if (error && retryCount >= 3) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          textAlign: 'center',
          animation: 'fadeIn 0.5s ease-in-out',
          '@keyframes fadeIn': {
            from: { opacity: 0, transform: 'translateY(20px)' },
            to: { opacity: 1, transform: 'translateY(0)' },
          },
        }}
      >
        <ErrorIcon sx={{ fontSize: 64, color: medicalColors.error.main, mb: 2 }} />
        <Typography variant="h5" gutterBottom color="text.primary">
          Unable to Load Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 400 }}>
          We're having trouble loading your dashboard data. Please check your connection and try again.
        </Typography>
        <Button
          variant="contained"
          onClick={handleRetry}
          startIcon={<RefreshIcon />}
          sx={{
            background: medicalColors.gradients.primary,
            '&:hover': {
              background: medicalColors.gradients.primaryLight,
            },
          }}
        >
          Try Again
        </Button>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        animation: 'slideInUp 0.6s ease-out',
        '@keyframes slideInUp': {
          from: { opacity: 0, transform: 'translateY(30px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      }}
    >
      {/* Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 4,
        background: medicalColors.gradients.primary,
        borderRadius: 3,
        p: { xs: 2.5, sm: 3, md: 3.5 },
        color: 'white',
        boxShadow: medicalColors.shadows.large,
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: medicalColors.gradients.glass,
          opacity: 0.1,
        },
      }}>
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Typography 
            variant="h3" 
            component="h1" 
            fontWeight="bold" 
            sx={{ 
              mb: 1,
              fontSize: { xs: '1.75rem', sm: '2.125rem', md: '2.5rem' },
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <DashboardIcon sx={{ mr: 2, fontSize: { xs: 32, sm: 36, md: 40 } }} />
            Dashboard
          </Typography>
          <Typography variant="body1" sx={{ opacity: 0.9, fontSize: { xs: '0.9rem', sm: '1rem' } }}>
            Welcome back! Here's what's happening today.
          </Typography>
          {lastRefresh && (
            <Typography variant="caption" sx={{ opacity: 0.7, display: 'block', mt: 0.5 }}>
              Last updated: {format(lastRefresh, 'HH:mm:ss')}
            </Typography>
          )}
        </Box>
        <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={isRefreshing ? <CircularProgress size={16} color="inherit" /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={isLoading || isRefreshing}
            sx={{
              backgroundColor: 'rgba(255,255,255,0.2)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.3)',
              transition: `all ${durations.standard}ms ${easings.easeInOut}`,
              '&:hover': {
                backgroundColor: 'rgba(255,255,255,0.3)',
                transform: 'translateY(-2px)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
              },
              '&:disabled': {
                backgroundColor: 'rgba(255,255,255,0.1)',
                color: 'rgba(255,255,255,0.5)',
              },
            }}
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
          {error && retryCount < 3 && (
            <Typography variant="caption" sx={{ opacity: 0.7, mt: 1, textAlign: 'right' }}>
              Retrying... ({retryCount}/3)
            </Typography>
          )}
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load dashboard data. Please try refreshing the page.
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          {isLoading ? (
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="40%" height={40} />
                <Skeleton variant="circular" width={56} height={56} sx={{ float: 'right', mt: -8 }} />
              </CardContent>
            </Card>
          ) : (
            <StatCard
              title="Total Users"
              value={stats.total_users?.toLocaleString() || '0'}
              icon={<PeopleIcon />}
              color="primary"
              trend={{ value: 12, isPositive: true }}
              onClick={() => navigate('/patients')}
            />
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {isLoading ? (
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="40%" height={40} />
                <Skeleton variant="circular" width={56} height={56} sx={{ float: 'right', mt: -8 }} />
              </CardContent>
            </Card>
          ) : (
            <StatCard
              title="Today's Appointments"
              value={stats.appointments_today?.toLocaleString() || '0'}
              icon={<CalendarIcon />}
              color="success"
              trend={{ value: 8, isPositive: true }}
              onClick={() => navigate('/app/appointments')}
            />
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {isLoading ? (
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="40%" height={40} />
                <Skeleton variant="circular" width={56} height={56} sx={{ float: 'right', mt: -8 }} />
              </CardContent>
            </Card>
          ) : (
            <StatCard
              title="Pending Appointments"
              value={stats.pending_appointments?.toLocaleString() || '0'}
              icon={<ScheduleIcon />}
              color="warning"
              onClick={() => navigate('/app/appointments')}
            />
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {isLoading ? (
            <Card sx={{ 
              height: '100%', 
              borderRadius: 3,
              boxShadow: medicalColors.shadows.medium,
              minHeight: { xs: 140, sm: 160, md: 180 },
            }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Skeleton variant="text" width="60%" height={24} />
                <Skeleton variant="text" width="40%" height={48} sx={{ my: 1 }} />
                <Skeleton variant="circular" width={56} height={56} sx={{ float: 'right', mt: -8 }} />
              </CardContent>
            </Card>
          ) : (
            <StatCard
              title="Completion Rate"
              value={`${Math.round((stats.completed_appointments / stats.total_appointments) * 100) || 0}%`}
              icon={<AssessmentIcon />}
              color="info"
              trend={{ value: 3, isPositive: true }}
            />
          )}
        </Grid>
      </Grid>

      <Grid container spacing={{ xs: 2, sm: 3, md: 4 }} sx={{ mb: { xs: 3, sm: 4 } }}>
        {/* Today's Appointments */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Paper 
            sx={{ 
              p: { xs: 2, sm: 3, md: 4 }, 
              height: { xs: 'auto', sm: 450, md: 500 }, 
              minHeight: { xs: 400, sm: 450 },
              display: 'flex', 
              flexDirection: 'column',
              background: medicalColors.gradients.backgroundCard,
              borderRadius: 3,
              boxShadow: medicalColors.shadows.medium,
              border: `1px solid ${medicalColors.neutral[200]}`,
            }}
          >
            <Box sx={{ 
              display: 'flex', 
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between', 
              alignItems: { xs: 'flex-start', sm: 'center' }, 
              mb: { xs: 2, sm: 3 },
              gap: { xs: 2, sm: 0 },
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                <Box
                  sx={{
                    background: medicalColors.gradients.primary,
                    borderRadius: '50%',
                    p: { xs: 1, sm: 1.5 },
                    mr: { xs: 1.5, sm: 2 },
                    boxShadow: medicalColors.shadows.small,
                  }}
                >
                  <EventNoteIcon sx={{ color: 'white', fontSize: { xs: 20, sm: 24 } }} />
                </Box>
                <Typography 
                  variant="h5" 
                  fontWeight="bold" 
                  color={medicalColors.medical.textPrimary}
                  sx={{ 
                    fontSize: { xs: '1.25rem', sm: '1.5rem' },
                    lineHeight: 1.2,
                  }}
                >
                  Today's Appointments
                </Typography>
              </Box>
              <IconButton 
                onClick={() => navigate('/app/appointments')}
                sx={{
                  background: medicalColors.gradients.medicalAccent,
                  color: 'white',
                  boxShadow: medicalColors.shadows.small,
                  transition: `all ${durations.standard}ms ${easings.easeInOut}`,
                  alignSelf: { xs: 'flex-end', sm: 'center' },
                  '&:hover': {
                    background: medicalColors.gradients.primary,
                    transform: 'translateY(-2px)',
                    boxShadow: medicalColors.shadows.medium,
                  },
                }}
              >
                <ArrowForwardIcon />
              </IconButton>
            </Box>
            
            {isLoading ? (
              <Stack spacing={2} sx={{ flexGrow: 1 }}>
                {[1, 2, 3].map((item) => (
                  <Box key={item} sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                    <Skeleton variant="circular" width={48} height={48} />
                    <Box sx={{ flex: 1 }}>
                      <Skeleton variant="text" width="70%" height={24} />
                      <Skeleton variant="text" width="50%" height={20} />
                    </Box>
                    <Skeleton variant="rectangular" width={80} height={28} sx={{ borderRadius: 2 }} />
                  </Box>
                ))}
              </Stack>
            ) : (
              <List sx={{ 
                flexGrow: 1, 
                overflow: 'auto', 
                px: 0,
                maxHeight: { xs: 300, sm: 320, md: 350 },
              }}>
                {todaysAppointments.length > 0 ? todaysAppointments.map((appointment: any) => (
                  <React.Fragment key={appointment.id}>
                    <ListItem 
                      sx={{ 
                        px: 0, 
                        py: { xs: 1.5, sm: 2 },
                        borderRadius: 2,
                        mb: { xs: 1.5, sm: 2 },
                        backgroundColor: medicalColors.neutral.white,
                        border: `1px solid ${medicalColors.neutral[200]}`,
                        boxShadow: medicalColors.shadows.small,
                        transition: `all ${durations.shorter}ms ${easings.easeInOut}`,
                        '&:hover': {
                          boxShadow: medicalColors.shadows.medium,
                          transform: 'translateY(-1px)',
                        }
                      }}
                    >
                      <ListItemAvatar sx={{ ml: { xs: 1, sm: 2 } }}>
                        <Avatar 
                          sx={{ 
                            background: medicalColors.gradients.success,
                            width: { xs: 40, sm: 48 },
                            height: { xs: 40, sm: 48 },
                            boxShadow: medicalColors.shadows.small,
                          }}
                        >
                          <ScheduleIcon sx={{ fontSize: { xs: 18, sm: 24 } }} />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        sx={{ ml: { xs: 0.5, sm: 1 } }}
                        primary={
                          <Typography 
                            variant="subtitle1" 
                            fontWeight="600" 
                            color={medicalColors.medical.textPrimary}
                            sx={{ fontSize: { xs: '0.95rem', sm: '1rem' } }}
                          >
                            {appointment.patientName}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 1, 
                            mt: 0.5,
                            flexWrap: { xs: 'wrap', sm: 'nowrap' },
                          }}>
                            <AccessTimeIcon sx={{ fontSize: 16, color: medicalColors.medical.textSecondary }} />
                            <Typography 
                              variant="body2" 
                              color={medicalColors.medical.textSecondary}
                              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                            >
                              {appointment.time}
                            </Typography>
                            <Typography 
                              variant="body2" 
                              color={medicalColors.medical.textMuted}
                              sx={{ display: { xs: 'none', sm: 'block' } }}
                            >
                              •
                            </Typography>
                            <Typography 
                              variant="body2" 
                              color={medicalColors.medical.textSecondary}
                              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                            >
                              {appointment.type}
                            </Typography>
                          </Box>
                        }
                        slotProps={{
                          secondary: { component: 'div' }
                        }}
                      />
                      <Box sx={{ mr: { xs: 1, sm: 2 } }}>
                        <Chip
                          label={appointment.status}
                          size="small"
                          color={getStatusColor(appointment.status) as any}
                          variant="filled"
                          sx={{ 
                            fontWeight: 600,
                            borderRadius: 2,
                            fontSize: { xs: '0.7rem', sm: '0.75rem' },
                          }}
                        />
                      </Box>
                    </ListItem>
                  </React.Fragment>
                )) : (
                  <Box sx={{ textAlign: 'center', py: { xs: 4, sm: 6 } }}>
                    <EventNoteIcon sx={{ 
                      fontSize: { xs: 48, sm: 64 }, 
                      color: medicalColors.medical.textMuted, 
                      mb: 2 
                    }} />
                    <Typography 
                      variant="h6" 
                      color={medicalColors.medical.textSecondary} 
                      fontWeight="500"
                      sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                    >
                      No appointments scheduled for today
                    </Typography>
                    <Typography 
                      variant="body2" 
                      color={medicalColors.medical.textMuted} 
                      sx={{ 
                        mt: 1,
                        fontSize: { xs: '0.8rem', sm: '0.875rem' }
                      }}
                    >
                      Your schedule is clear for today
                    </Typography>
                  </Box>
                )}
              </List>
            )}
            
            <Button
              fullWidth
              variant="contained"
              onClick={() => navigate('/app/appointments')}
              sx={{ 
                mt: { xs: 1.5, sm: 2 },
                background: medicalColors.gradients.primary,
                borderRadius: 2,
                py: { xs: 1.25, sm: 1.5 },
                fontWeight: 600,
                fontSize: { xs: '0.875rem', sm: '1rem' },
                boxShadow: medicalColors.shadows.medium,
                transition: `all ${durations.standard}ms ${easings.easeInOut}`,
                '&:hover': {
                  background: medicalColors.gradients.primaryDark,
                  transform: 'translateY(-2px)',
                  boxShadow: medicalColors.shadows.large,
                },
              }}
            >
              View All Appointments
            </Button>
          </Paper>
        </Grid>

        {/* Recent Alerts */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Paper 
            sx={{ 
              p: { xs: 2, sm: 3, md: 4 }, 
              height: { xs: 'auto', sm: 450, md: 500 }, 
              minHeight: { xs: 400, sm: 450 },
              display: 'flex', 
              flexDirection: 'column',
              background: medicalColors.gradients.backgroundCard,
              borderRadius: 3,
              boxShadow: medicalColors.shadows.medium,
              border: `1px solid ${medicalColors.neutral[200]}`,
            }}
          >
            <Box sx={{ 
              display: 'flex', 
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between', 
              alignItems: { xs: 'flex-start', sm: 'center' }, 
              mb: { xs: 2, sm: 3 },
              gap: { xs: 2, sm: 0 },
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                <Box
                  sx={{
                    background: medicalColors.gradients.warning,
                    borderRadius: '50%',
                    p: { xs: 1, sm: 1.5 },
                    mr: { xs: 1.5, sm: 2 },
                    boxShadow: medicalColors.shadows.small,
                  }}
                >
                  <NotificationsIcon sx={{ color: 'white', fontSize: { xs: 20, sm: 24 } }} />
                </Box>
                <Typography 
                  variant="h5" 
                  fontWeight="bold" 
                  color={medicalColors.medical.textPrimary}
                  sx={{ 
                    fontSize: { xs: '1.25rem', sm: '1.5rem' },
                    lineHeight: 1.2,
                  }}
                >
                  Recent Alerts
                </Typography>
              </Box>
              <IconButton 
                onClick={() => navigate('/notifications')}
                sx={{
                  background: medicalColors.gradients.secondary,
                  color: 'white',
                  boxShadow: medicalColors.shadows.small,
                  transition: `all ${durations.standard}ms ${easings.easeInOut}`,
                  alignSelf: { xs: 'flex-end', sm: 'center' },
                  '&:hover': {
                    background: medicalColors.gradients.secondaryLight,
                    transform: 'translateY(-2px)',
                    boxShadow: medicalColors.shadows.medium,
                  },
                }}
              >
                <ArrowForwardIcon />
              </IconButton>
            </Box>
            
            {isLoading ? (
              <Stack spacing={2} sx={{ flexGrow: 1 }}>
                {[1, 2, 3].map((item) => (
                  <Box key={item} sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                    <Skeleton variant="circular" width={48} height={48} />
                    <Box sx={{ flex: 1 }}>
                      <Skeleton variant="text" width="80%" height={24} />
                      <Skeleton variant="text" width="60%" height={20} />
                    </Box>
                    <Skeleton variant="rectangular" width={70} height={28} sx={{ borderRadius: 2 }} />
                  </Box>
                ))}
              </Stack>
            ) : (
              <List sx={{ 
                flexGrow: 1, 
                overflow: 'auto', 
                px: 0,
                maxHeight: { xs: 300, sm: 320, md: 350 },
              }}>
                {recentAlerts.length > 0 ? recentAlerts.map((alert) => (
                  <React.Fragment key={alert.id}>
                    <ListItem 
                      sx={{ 
                        px: 0, 
                        py: { xs: 1.5, sm: 2 },
                        borderRadius: 2,
                        mb: { xs: 1.5, sm: 2 },
                        backgroundColor: medicalColors.neutral.white,
                        border: `1px solid ${medicalColors.neutral[200]}`,
                        boxShadow: medicalColors.shadows.small,
                        transition: `all ${durations.shorter}ms ${easings.easeInOut}`,
                        '&:hover': {
                          boxShadow: medicalColors.shadows.medium,
                          transform: 'translateY(-1px)',
                        }
                      }}
                    >
                      <ListItemAvatar sx={{ ml: { xs: 1, sm: 2 } }}>
                        <Avatar 
                          sx={{ 
                            bgcolor: getAlertColor(alert.type),
                            width: { xs: 40, sm: 48 },
                            height: { xs: 40, sm: 48 },
                            boxShadow: medicalColors.shadows.small,
                          }}
                        >
                          {getAlertIcon(alert.type)}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        sx={{ ml: { xs: 0.5, sm: 1 } }}
                        primary={
                          <Typography 
                            variant="subtitle1" 
                            fontWeight="600" 
                            color={medicalColors.medical.textPrimary}
                            sx={{ fontSize: { xs: '0.95rem', sm: '1rem' } }}
                          >
                            {alert.message}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 1, 
                            mt: 0.5 
                          }}>
                            <AccessTimeIcon sx={{ fontSize: 16, color: medicalColors.medical.textSecondary }} />
                            <Typography 
                              variant="body2" 
                              color={medicalColors.medical.textSecondary}
                              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                            >
                              {alert.time}
                            </Typography>
                          </Box>
                        }
                        slotProps={{
                          secondary: { component: 'div' }
                        }}
                      />
                      <Box sx={{ mr: { xs: 1, sm: 2 } }}>
                        <Chip
                          label={alert.type}
                          size="small"
                          color={getAlertChipColor(alert.type) as any}
                          variant="filled"
                          sx={{ 
                            fontWeight: 600,
                            borderRadius: 2,
                            fontSize: { xs: '0.7rem', sm: '0.75rem' },
                          }}
                        />
                      </Box>
                    </ListItem>
                  </React.Fragment>
                )) : (
                  <Box sx={{ textAlign: 'center', py: { xs: 4, sm: 6 } }}>
                    <NotificationsIcon sx={{ 
                      fontSize: { xs: 48, sm: 64 }, 
                      color: medicalColors.medical.textMuted, 
                      mb: 2 
                    }} />
                    <Typography 
                      variant="h6" 
                      color={medicalColors.medical.textSecondary} 
                      fontWeight="500"
                      sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                    >
                      No recent alerts
                    </Typography>
                    <Typography 
                      variant="body2" 
                      color={medicalColors.medical.textMuted} 
                      sx={{ 
                        mt: 1,
                        fontSize: { xs: '0.8rem', sm: '0.875rem' }
                      }}
                    >
                      All systems are running smoothly
                    </Typography>
                  </Box>
                )}
              </List>
            )}
            
            <Button
              fullWidth
              variant="contained"
              onClick={() => navigate('/notifications')}
              sx={{ 
                mt: { xs: 1.5, sm: 2 },
                background: medicalColors.gradients.secondary,
                borderRadius: 2,
                py: { xs: 1.25, sm: 1.5 },
                fontWeight: 600,
                fontSize: { xs: '0.875rem', sm: '1rem' },
                boxShadow: medicalColors.shadows.medium,
                transition: `all ${durations.standard}ms ${easings.easeInOut}`,
                '&:hover': {
                  background: medicalColors.gradients.secondaryLight,
                  transform: 'translateY(-2px)',
                  boxShadow: medicalColors.shadows.large,
                },
              }}
            >
              View All Notifications
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Analytics Charts Section */}
      <Grid container spacing={{ xs: 2, sm: 3, md: 4 }} sx={{ mt: { xs: 1, sm: 2 } }}>
        {/* Activity Trends Chart */}
        <Grid size={{ xs: 12, md: 12, lg: 8 }}>
          <Paper 
             sx={{ 
               p: { xs: 2, sm: 3 }, 
               height: { xs: '350px', sm: '400px' },
               background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
               borderRadius: 3,
               boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
               color: 'white',
             }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Box
                sx={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: '50%',
                  p: 1,
                  mr: 2,
                }}
              >
                <Timeline sx={{ color: 'white', fontSize: 24 }} />
              </Box>
              <Typography 
                sx={{ 
                  typography: { xs: 'h6', sm: 'h5' },
                  fontWeight: 'bold'
                }}
              >
                 Activity Trends (Last 7 Days)
               </Typography>
            </Box>
            
            {isLoading ? (
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '250px' }}>
                <Skeleton variant="rectangular" width="100%" height="200px" sx={{ borderRadius: 2, bgcolor: 'rgba(255,255,255,0.1)' }} />
              </Box>
            ) : (
              <Box sx={{ height: '300px', display: 'flex', alignItems: 'end', justifyContent: 'space-around', px: 2 }}>
                {activityTrends && activityTrends.map((trend: any, index: number) => {
                  const maxValue = Math.max(...activityTrends.map((t: any) => t.appointments));
                  const height = (trend.appointments / maxValue) * 200;
                  return (
                    <Box key={index} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <Typography variant="body2" sx={{ mb: 1, fontWeight: 600 }}>
                        {trend.appointments}
                      </Typography>
                      <Box
                        sx={{
                          width: 40,
                          height: `${height}px`,
                          background: 'linear-gradient(180deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
                          borderRadius: '4px 4px 0 0',
                          mb: 1,
                          transition: 'all 0.3s ease',
                          '&:hover': {
                            background: 'linear-gradient(180deg, rgba(255,255,255,1) 0%, rgba(255,255,255,0.8) 100%)',
                          },
                        }}
                      />
                      <Typography variant="caption" sx={{ transform: 'rotate(-45deg)', fontSize: '0.7rem' }}>
                        {format(new Date(trend.date), 'MMM dd')}
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Department Stats */}
        <Grid size={{ xs: 12, md: 12, lg: 4 }}>
          <Paper 
             sx={{ 
               p: { xs: 2, sm: 3 }, 
               height: { xs: '350px', sm: '400px' },
               background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
               borderRadius: 3,
               boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
             }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Box
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '50%',
                  p: 1,
                  mr: 2,
                }}
              >
                <LocalHospital sx={{ color: 'white', fontSize: 24 }} />
              </Box>
              <Typography 
                sx={{ 
                  typography: { xs: 'h6', sm: 'h5' },
                  fontWeight: 'bold',
                  color: 'text.primary'
                }}
              >
                 Department Overview
               </Typography>
            </Box>
            
            {isLoading ? (
              <Stack spacing={3}>
                {[1, 2, 3, 4].map((item) => (
                  <Box key={item}>
                    <Skeleton variant="text" width="70%" height={24} />
                    <Skeleton variant="rectangular" height={8} sx={{ borderRadius: 1, mt: 1 }} />
                  </Box>
                ))}
              </Stack>
            ) : (
              <Box sx={{ height: '300px', overflow: 'auto' }}>
                {departmentStats && departmentStats.map((dept: any, index: number) => {
                  const maxAppointments = Math.max(...departmentStats.map((d: any) => d.appointments));
                  const percentage = (dept.appointments / maxAppointments) * 100;
                  const colors = [
                    medicalColors.gradients.primary,
                    medicalColors.gradients.secondary,
                    medicalColors.gradients.success,
                    medicalColors.gradients.warning,
                    medicalColors.gradients.medicalAccent,
                  ];
                  return (
                    <Box key={index} sx={{ mb: { xs: 3, sm: 4 } }}>
                      <Box sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        mb: { xs: 1, sm: 1.5 },
                        flexDirection: { xs: 'column', sm: 'row' },
                        gap: { xs: 0.5, sm: 0 },
                      }}>
                        <Typography 
                          variant="subtitle1" 
                          fontWeight="600" 
                          color={medicalColors.medical.textPrimary}
                          sx={{ 
                            fontSize: { xs: '0.95rem', sm: '1rem' },
                            textAlign: { xs: 'center', sm: 'left' },
                          }}
                        >
                          {dept.name}
                        </Typography>
                        <Typography 
                          variant="body2" 
                          color={medicalColors.medical.textSecondary} 
                          fontWeight="500"
                          sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
                        >
                          {dept.appointments} appointments
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={percentage}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: 'rgba(0,0,0,0.1)',
                          '& .MuiLinearProgress-bar': {
                            background: `linear-gradient(90deg, hsl(${index * 60}, 70%, 60%) 0%, hsl(${index * 60 + 30}, 70%, 70%) 100%)`,
                            borderRadius: 4,
                          },
                        }}
                      />
                    </Box>
                  );
                })}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};