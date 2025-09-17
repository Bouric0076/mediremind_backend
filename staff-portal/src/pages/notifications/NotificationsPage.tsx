import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
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

  Badge,
  Menu,
  Tooltip,
  Fab,
} from '@mui/material';
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

  Description as TemplateIcon,

} from '@mui/icons-material';

import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';
import { useGetNotificationsQuery } from '../../store/api/apiSlice';

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
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'scheduled';
  scheduledAt?: string;
  sentAt?: string;
  deliveredAt?: string;
  templateId?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: 'appointment' | 'reminder' | 'alert' | 'marketing' | 'system';
}

interface NotificationTemplate {
  id: string;
  name: string;
  type: 'email' | 'sms' | 'phone';
  category: 'appointment' | 'reminder' | 'alert' | 'marketing' | 'system';
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

const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'email',
    recipient: {
      id: '1',
      name: 'John Doe',
      contact: 'john.doe@email.com'
    },
    subject: 'Appointment Reminder',
    message: 'Your appointment is scheduled for tomorrow at 9:00 AM',
    status: 'delivered',
    sentAt: '2024-01-24T10:00:00Z',
    deliveredAt: '2024-01-24T10:01:00Z',
    priority: 'medium',
    category: 'appointment'
  },
  {
    id: '2',
    type: 'sms',
    recipient: {
      id: '2',
      name: 'Jane Smith',
      contact: '+1 (555) 987-6543'
    },
    subject: 'Prescription Ready',
    message: 'Your prescription is ready for pickup',
    status: 'sent',
    sentAt: '2024-01-24T14:30:00Z',
    priority: 'high',
    category: 'alert'
  },
  {
    id: '3',
    type: 'email',
    recipient: {
      id: '3',
      name: 'Mike Johnson',
      contact: 'mike.johnson@email.com'
    },
    subject: 'Follow-up Required',
    message: 'Please schedule your follow-up appointment',
    status: 'pending',
    priority: 'medium',
    category: 'reminder'
  },
];

const mockTemplates: NotificationTemplate[] = [
  {
    id: '1',
    name: 'Appointment Reminder',
    type: 'email',
    category: 'appointment',
    subject: 'Appointment Reminder - {{date}} at {{time}}',
    content: 'Dear {{patientName}}, this is a reminder that you have an appointment scheduled for {{date}} at {{time}} with {{provider}}.',
    variables: ['patientName', 'date', 'time', 'provider'],
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-15T00:00:00Z'
  },
  {
    id: '2',
    name: 'Prescription Ready SMS',
    type: 'sms',
    category: 'alert',
    subject: 'Prescription Ready',
    content: 'Hi {{patientName}}, your prescription for {{medication}} is ready for pickup at our pharmacy.',
    variables: ['patientName', 'medication'],
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-10T00:00:00Z'
  },
];

export const NotificationsPage: React.FC = () => {
  const dispatch = useDispatch();
  
  const [tabValue, setTabValue] = useState(0);
  const [newNotificationOpen, setNewNotificationOpen] = useState(false);
  const [newTemplateOpen, setNewTemplateOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  
  // Mock queries - replace with actual API calls
  const { refetch } = useGetNotificationsQuery({});

  useEffect(() => {
    dispatch(setCurrentPage('notifications'));
    dispatch(setBreadcrumbs([
      { label: 'Notifications', path: '/notifications' }
    ]));
  }, [dispatch]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered': return 'success';
      case 'sent': return 'info';
      case 'pending': return 'warning';
      case 'scheduled': return 'secondary';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email': return <EmailIcon />;
      case 'sms': return <SmsIcon />;
      case 'phone': return <PhoneIcon />;
      default: return <NotificationsIcon />;
    }
  };



  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const renderNotificationsList = (notifications: Notification[]) => {
    return (
      <List>
        {notifications.map((notification) => (
          <ListItem
            key={notification.id}
            sx={{
              border: 1,
              borderColor: 'grey.200',
              borderRadius: 1,
              mb: 1,
              '&:hover': { bgcolor: 'grey.50' }
            }}
          >
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: `${getStatusColor(notification.status)}.main` }}>
                {getTypeIcon(notification.type)}
              </Avatar>
            </ListItemAvatar>
            <ListItemText
                primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography variant="subtitle1" fontWeight="medium">
                    {notification.subject}
                  </Typography>
                  <Chip
                    label={notification.priority}
                    size="small"
                    color={getPriorityColor(notification.priority) as any}
                    variant="outlined"
                  />
                  <Chip
                    label={notification.status}
                    size="small"
                    color={getStatusColor(notification.status) as any}
                  />
                </Box>
              }
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    To: {notification.recipient.name} ({notification.recipient.contact})
                  </Typography>
                  <Typography variant="body2" noWrap sx={{ mb: 0.5 }}>
                    {notification.message}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={notification.category}
                      size="small"
                      variant="outlined"
                    />
                    <Typography variant="caption" color="text.secondary">
                      {notification.sentAt ? 
                        `Sent: ${new Date(notification.sentAt).toLocaleString()}` :
                        notification.scheduledAt ?
                        `Scheduled: ${new Date(notification.scheduledAt).toLocaleString()}` :
                        'Not sent'
                      }
                    </Typography>
                  </Box>
                </Box>
              }
              slotProps={{
                primary: { component: 'div' },
                secondary: { component: 'div' }
              }}
            />
            <ListItemSecondaryAction>
              <IconButton
                onClick={(e) => handleMenuClick(e)}
                size="small"
              >
                <MoreVertIcon />
              </IconButton>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>
    );
  };

  const renderTemplatesList = () => {
    return (
      <Grid container spacing={2}>
        {mockTemplates.map((template) => (
          <Grid size={{ xs: 12, md: 6, lg: 4 }} key={template.id}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      {template.name}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                      <Chip
                        label={template.type}
                        size="small"
                        icon={getTypeIcon(template.type)}
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        label={template.category}
                        size="small"
                        color="secondary"
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                  <FormControlLabel
                    control={<Switch checked={template.isActive} size="small" />}
                    label="Active"
                    sx={{ ml: 1 }}
                  />
                </Box>
                
                <Typography variant="subtitle2" fontWeight="medium" gutterBottom>
                  Subject: {template.subject}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {template.content.substring(0, 100)}...
                </Typography>
                
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                  Variables: {template.variables.join(', ')}
                </Typography>
                
                <Typography variant="caption" color="text.secondary">
                  Updated: {new Date(template.updatedAt).toLocaleDateString()}
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                  <Button size="small" startIcon={<EditIcon />}>
                    Edit
                  </Button>
                  <Button size="small" startIcon={<SendIcon />}>
                    Use
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  const getNotificationsByStatus = (status: string) => {
    return mockNotifications.filter(n => n.status === status);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Notifications
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setNewNotificationOpen(true)}
          >
            Send Notification
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    Total Sent
                  </Typography>
                  <Typography variant="h4" component="div" fontWeight="bold">
                    {mockNotifications.filter(n => n.status === 'sent' || n.status === 'delivered').length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <SendIcon />
                </Avatar>
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
                  <Typography variant="h4" component="div" fontWeight="bold">
                    {getNotificationsByStatus('pending').length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <PendingIcon />
                </Avatar>
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
                    Failed
                  </Typography>
                  <Typography variant="h4" component="div" fontWeight="bold">
                    {getNotificationsByStatus('failed').length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'error.main' }}>
                  <ErrorIcon />
                </Avatar>
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
                    Templates
                  </Typography>
                  <Typography variant="h4" component="div" fontWeight="bold">
                    {mockTemplates.length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <TemplateIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab 
            label={
              <Badge badgeContent={mockNotifications.length} color="primary">
                All Notifications
              </Badge>
            } 
          />
          <Tab 
            label={
              <Badge badgeContent={getNotificationsByStatus('pending').length} color="warning">
                Pending
              </Badge>
            } 
          />
          <Tab label="Templates" />
          <Tab label="Settings" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            All Notifications ({mockNotifications.length})
          </Typography>
          {renderNotificationsList(mockNotifications)}
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Pending Notifications ({getNotificationsByStatus('pending').length})
          </Typography>
          {renderNotificationsList(getNotificationsByStatus('pending'))}
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">
            Notification Templates ({mockTemplates.length})
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setNewTemplateOpen(true)}
          >
            New Template
          </Button>
        </Box>
        {renderTemplatesList()}
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 3 }}>
            Notification Settings
          </Typography>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
                Email Settings
              </Typography>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable email notifications"
                sx={{ display: 'block', mb: 1 }}
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Send appointment reminders"
                sx={{ display: 'block', mb: 1 }}
              />
              <FormControlLabel
                control={<Switch />}
                label="Send marketing emails"
                sx={{ display: 'block', mb: 2 }}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
                SMS Settings
              </Typography>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable SMS notifications"
                sx={{ display: 'block', mb: 1 }}
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Send urgent alerts via SMS"
                sx={{ display: 'block', mb: 1 }}
              />
              <FormControlLabel
                control={<Switch />}
                label="Send promotional SMS"
                sx={{ display: 'block', mb: 2 }}
              />
            </Grid>
          </Grid>
        </Paper>
      </TabPanel>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <EditIcon sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <SendIcon sx={{ mr: 1 }} />
          Resend
        </MenuItem>
        <MenuItem onClick={handleMenuClose} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* New Notification Dialog */}
      <Dialog open={newNotificationOpen} onClose={() => setNewNotificationOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Send New Notification</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select label="Type">
                  <MenuItem value="email">Email</MenuItem>
                  <MenuItem value="sms">SMS</MenuItem>
                  <MenuItem value="phone">Phone</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Template</InputLabel>
                <Select label="Template">
                  {mockTemplates.map((template) => (
                    <MenuItem key={template.id} value={template.id}>
                      {template.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Recipient"
                placeholder="Enter recipient name or contact"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Subject"
                placeholder="Enter notification subject"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Message"
                placeholder="Enter notification message"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select label="Priority">
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="urgent">Urgent</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                type="datetime-local"
                label="Schedule For"
                InputLabelProps={{ shrink: true }}
                helperText="Leave empty to send immediately"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewNotificationOpen(false)}>Cancel</Button>
          <Button variant="outlined">Save as Draft</Button>
          <Button variant="contained" startIcon={<SendIcon />}>
            Send Now
          </Button>
        </DialogActions>
      </Dialog>

      {/* New Template Dialog */}
      <Dialog open={newTemplateOpen} onClose={() => setNewTemplateOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Template</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Template Name"
                placeholder="Enter template name"
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select label="Type">
                  <MenuItem value="email">Email</MenuItem>
                  <MenuItem value="sms">SMS</MenuItem>
                  <MenuItem value="phone">Phone</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Subject"
                placeholder="Enter template subject (use {{variable}} for dynamic content)"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Content"
                placeholder="Enter template content (use {{variable}} for dynamic content)"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Variables"
                placeholder="Enter comma-separated variables (e.g., patientName, date, time)"
                helperText="These variables can be used in the subject and content using {{variableName}}"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewTemplateOpen(false)}>Cancel</Button>
          <Button variant="contained">
            Create Template
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button */}
      <Tooltip title="Send New Notification">
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => setNewNotificationOpen(true)}
        >
          <SendIcon />
        </Fab>
      </Tooltip>
    </Box>
  );
};