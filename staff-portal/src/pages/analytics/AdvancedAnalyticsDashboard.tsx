import React, { useState } from 'react';
import type { SelectChangeEvent } from '@mui/material';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Chip,
  Button,
  IconButton,
  Menu,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Tabs,
  Tab,
  Alert,
  LinearProgress,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  People as PeopleIcon,
  LocalHospital as HospitalIcon,
  AttachMoney as MoneyIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  MoreVert as MoreIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon,
  DateRange as DateIcon,
} from '@mui/icons-material';

// Mock data interfaces
interface KPIMetric {
  id: string;
  title: string;
  value: number | string;
  change: number;
  changeType: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  format: 'number' | 'currency' | 'percentage';
}

interface ChartData {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'pie' | 'area';
  data: any[];
  timeframe: string;
}

interface SystemAlert {
  id: string;
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
  resolved: boolean;
}

interface PerformanceMetric {
  id: string;
  name: string;
  value: number;
  target: number;
  unit: string;
  status: 'good' | 'warning' | 'critical';
}

// Mock data
const mockKPIs: KPIMetric[] = [
  {
    id: '1',
    title: 'Total Patients',
    value: 12847,
    change: 8.2,
    changeType: 'increase',
    icon: <PeopleIcon />,
    color: 'primary',
    format: 'number',
  },
  {
    id: '2',
    title: 'Monthly Revenue',
    value: 2847500,
    change: 12.5,
    changeType: 'increase',
    icon: <MoneyIcon />,
    color: 'success',
    format: 'currency',
  },
  {
    id: '3',
    title: 'Appointment Rate',
    value: 94.2,
    change: -2.1,
    changeType: 'decrease',
    icon: <ScheduleIcon />,
    color: 'warning',
    format: 'percentage',
  },
  {
    id: '4',
    title: 'System Uptime',
    value: 99.8,
    change: 0.3,
    changeType: 'increase',
    icon: <HospitalIcon />,
    color: 'success',
    format: 'percentage',
  },
];

const mockSystemAlerts: SystemAlert[] = [
  {
    id: '1',
    type: 'warning',
    title: 'High Server Load',
    message: 'Database server experiencing high CPU usage (85%)',
    timestamp: '2024-01-15T10:30:00Z',
    resolved: false,
  },
  {
    id: '2',
    type: 'info',
    title: 'Scheduled Maintenance',
    message: 'System maintenance scheduled for tonight at 2:00 AM',
    timestamp: '2024-01-15T09:15:00Z',
    resolved: false,
  },
  {
    id: '3',
    type: 'success',
    title: 'Backup Completed',
    message: 'Daily database backup completed successfully',
    timestamp: '2024-01-15T06:00:00Z',
    resolved: true,
  },
];

const mockPerformanceMetrics: PerformanceMetric[] = [
  {
    id: '1',
    name: 'Response Time',
    value: 245,
    target: 300,
    unit: 'ms',
    status: 'good',
  },
  {
    id: '2',
    name: 'Memory Usage',
    value: 78,
    target: 80,
    unit: '%',
    status: 'warning',
  },
  {
    id: '3',
    name: 'Error Rate',
    value: 0.2,
    target: 1.0,
    unit: '%',
    status: 'good',
  },
  {
    id: '4',
    name: 'Disk Usage',
    value: 92,
    target: 85,
    unit: '%',
    status: 'critical',
  },
];

// const mockChartData: ChartData[] = [
//   {
//     id: '1',
//     title: 'Patient Visits Trend',
//     type: 'line',
//     data: [120, 135, 142, 158, 165, 178, 185, 192, 205, 218, 225, 240],
//     timeframe: 'Last 12 months',
//   },
//   {
//     id: '2',
//     title: 'Revenue by Department',
//     type: 'pie',
//     data: [
//       { name: 'Cardiology', value: 450000 },
//       { name: 'Orthopedics', value: 380000 },
//       { name: 'Neurology', value: 320000 },
//       { name: 'Pediatrics', value: 280000 },
//       { name: 'Emergency', value: 250000 },
//     ],
//     timeframe: 'Current month',
//   },
// ];

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
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const AdvancedAnalyticsDashboard: React.FC = () => {
  
  const [tabValue, setTabValue] = useState(0);
  const [timeframe, setTimeframe] = useState('30d');
  const [refreshing, setRefreshing] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleTimeframeChange = (event: SelectChangeEvent) => {
    setTimeframe(event.target.value);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    setRefreshing(false);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const formatValue = (value: number | string, format: string) => {
    if (typeof value === 'string') return value;
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(value);
      case 'percentage':
        return `${value}%`;
      default:
        return new Intl.NumberFormat('en-US').format(value);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'primary';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <ErrorIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'success':
        return <CheckIcon />;
      default:
        return <InfoIcon />;
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Advanced Analytics Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Comprehensive system metrics and performance insights
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Timeframe</InputLabel>
            <Select
              value={timeframe}
              label="Timeframe"
              onChange={handleTimeframeChange}
            >
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
              <MenuItem value="1y">Last year</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            Refresh
          </Button>
          <IconButton onClick={handleMenuClick}>
            <MoreIcon />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={handleMenuClose}>
              <DownloadIcon sx={{ mr: 1 }} />
              Export Report
            </MenuItem>
            <MenuItem onClick={handleMenuClose}>
              <FilterIcon sx={{ mr: 1 }} />
              Advanced Filters
            </MenuItem>
            <MenuItem onClick={handleMenuClose}>
              <DateIcon sx={{ mr: 1 }} />
              Custom Date Range
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* System Alerts */}
      {mockSystemAlerts.filter(alert => !alert.resolved).length > 0 && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small">
              View All
            </Button>
          }
        >
          <Typography variant="subtitle2">
            {mockSystemAlerts.filter(alert => !alert.resolved).length} active system alerts require attention
          </Typography>
        </Alert>
      )}

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {mockKPIs.map((kpi) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={kpi.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom variant="body2">
                      {kpi.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {formatValue(kpi.value, kpi.format)}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                      {kpi.changeType === 'increase' ? (
                        <TrendingUp color="success" sx={{ fontSize: 16, mr: 0.5 }} />
                      ) : kpi.changeType === 'decrease' ? (
                        <TrendingDown color="error" sx={{ fontSize: 16, mr: 0.5 }} />
                      ) : null}
                      <Typography
                        variant="body2"
                        color={kpi.changeType === 'increase' ? 'success.main' : kpi.changeType === 'decrease' ? 'error.main' : 'text.secondary'}
                      >
                        {kpi.change > 0 ? '+' : ''}{kpi.change}%
                      </Typography>
                    </Box>
                  </Box>
                  <Avatar sx={{ bgcolor: `${kpi.color}.main` }}>
                    {kpi.icon}
                  </Avatar>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="analytics tabs">
            <Tab label="Overview" />
            <Tab label="Performance" />
            <Tab label="System Health" />
            <Tab label="Reports" />
          </Tabs>
        </Box>

        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {/* Chart Placeholders */}
            <Grid size={{ xs: 12, md: 8 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Patient Visits Trend
                  </Typography>
                  <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50' }}>
                    <Typography color="text.secondary">
                      Chart visualization would be rendered here
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Revenue Distribution
                  </Typography>
                  <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50' }}>
                    <Typography color="text.secondary">
                      Pie chart would be rendered here
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Performance Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {mockPerformanceMetrics.map((metric) => (
              <Grid size={{ xs: 12, sm: 6, md: 3 }} key={metric.id}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      {metric.name}
                    </Typography>
                    <Typography variant="h5" component="div">
                      {metric.value}{metric.unit}
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Target: {metric.target}{metric.unit}
                        </Typography>
                        <Chip 
                          label={metric.status} 
                          size="small" 
                          color={getStatusColor(metric.status) as any}
                        />
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(metric.value / metric.target) * 100}
                        color={getStatusColor(metric.status) as any}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* System Health Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Alerts
                  </Typography>
                  <List>
                    {mockSystemAlerts.map((alert) => (
                      <ListItem key={alert.id}>
                        <ListItemIcon>
                          {getAlertIcon(alert.type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={alert.title}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {alert.message}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {new Date(alert.timestamp).toLocaleString()}
                              </Typography>
                            </Box>
                          }
                        />
                        {alert.resolved && (
                          <Chip label="Resolved" size="small" color="success" />
                        )}
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Status
                  </Typography>
                  <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50' }}>
                    <Typography color="text.secondary">
                      System status dashboard would be rendered here
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Reports Tab */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Available Reports
                  </Typography>
                  <Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50' }}>
                    <Typography color="text.secondary">
                      Report generation interface would be rendered here
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default AdvancedAnalyticsDashboard;