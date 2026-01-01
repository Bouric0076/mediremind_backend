import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Event as EventIcon,
  AccessTime as AccessTimeIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  LocationOn as LocationIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  Note as NoteIcon,
  Sms as SmsIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage, addToast } from '../../store/slices/uiSlice';
import { 
  useGetAppointmentQuery, 
  useUpdateAppointmentMutation, 
  useCancelAppointmentMutation,
  useSendManualSmsReminderMutation 
} from '../../store/api/apiSlice';

interface AppointmentDetails {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_phone?: string;
  patient_email?: string;
  provider_id: string;
  provider_name: string;
  appointment_type_name: string;
  appointment_date: string;
  start_time: string;
  duration: number;
  status: 'scheduled' | 'confirmed' | 'in-progress' | 'completed' | 'cancelled' | 'no-show';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  room?: string;
  notes?: string;
  formatted_datetime?: string;
}

export const AppointmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [rescheduleDialogOpen, setRescheduleDialogOpen] = useState(false);
  const [noShowDialogOpen, setNoShowDialogOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [rescheduleDate, setRescheduleDate] = useState('');
  const [rescheduleTime, setRescheduleTime] = useState('');
  const [noShowReason, setNoShowReason] = useState('');

  const { data: appointmentData, isLoading, error, refetch } = useGetAppointmentQuery(id!, {
    skip: !id,
  });

  const [updateAppointment] = useUpdateAppointmentMutation();
  const [cancelAppointment] = useCancelAppointmentMutation();
  const [sendSmsReminder] = useSendManualSmsReminderMutation();

  const appointment: AppointmentDetails = appointmentData?.appointment || appointmentData;

  useEffect(() => {
    dispatch(setCurrentPage('appointments'));
    dispatch(setBreadcrumbs([
      { label: 'Appointments', path: '/app/appointments' },
      { label: 'Appointment Details', path: `/app/appointments/${id}` }
    ]));
  }, [dispatch, id]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'info';
      case 'confirmed': return 'success';
      case 'in-progress': return 'warning';
      case 'completed': return 'success';
      case 'cancelled': return 'error';
      case 'no-show': return 'error';
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

  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const isPastAppointment = (date: string, time: string) => {
    const appointmentDateTime = new Date(`${date}T${time}`);
    const now = new Date();
    return appointmentDateTime < now;
  };

  const handleConfirmAppointment = async () => {
    try {
      await updateAppointment({
        id: id!,
        updates: { status: 'confirmed' }
      }).unwrap();
      
      dispatch(addToast({
        title: 'Success',
        message: 'Appointment confirmed successfully',
        type: 'success'
      }));
      
      refetch();
    } catch (_error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      dispatch(addToast({
        title: 'Error',
        message: 'Failed to confirm appointment',
        type: 'error'
      }));
    }
  };

  const handleCompleteAppointment = async () => {
    try {
      await updateAppointment({
        id: id!,
        updates: { status: 'completed' }
      }).unwrap();
      
      dispatch(addToast({
        title: 'Success',
        message: 'Appointment marked as completed',
        type: 'success'
      }));
      
      refetch();
    } catch (_error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      dispatch(addToast({
        title: 'Error',
        message: 'Failed to complete appointment',
        type: 'error'
      }));
    }
  };

  const handleCancelAppointment = async () => {
    if (!cancelReason.trim()) {
      dispatch(addToast({
        title: 'Warning',
        message: 'Please provide a cancellation reason',
        type: 'warning'
      }));
      return;
    }

    try {
      await cancelAppointment({
        id: id!,
        reason: cancelReason
      }).unwrap();
      
      dispatch(addToast({
        title: 'Success',
        message: 'Appointment cancelled successfully',
        type: 'success'
      }));
      
      setCancelDialogOpen(false);
      setCancelReason('');
      refetch();
    } catch (_error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      dispatch(addToast({
        title: 'Error',
        message: 'Failed to cancel appointment',
        type: 'error'
      }));
    }
  };

  const handleMarkNoShow = async () => {
    if (!noShowReason.trim()) {
      dispatch(addToast({
        title: 'Warning',
        message: 'Please provide a reason for no-show',
        type: 'warning'
      }));
      return;
    }

    try {
      await updateAppointment({
        id: id!,
        updates: { 
          status: 'no-show',
          notes: noShowReason
        }
      }).unwrap();
      
      dispatch(addToast({
        title: 'Success',
        message: 'Appointment marked as no-show',
        type: 'success'
      }));
      
      setNoShowDialogOpen(false);
      setNoShowReason('');
      refetch();
    } catch (_error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      dispatch(addToast({
        title: 'Error',
        message: 'Failed to mark appointment as no-show',
        type: 'error'
      }));
    }
  };

  const handleRescheduleAppointment = async () => {
    if (!rescheduleDate || !rescheduleTime) {
      dispatch(addToast({
        title: 'Warning',
        message: 'Please select both date and time',
        type: 'warning'
      }));
      return;
    }

    try {
      await updateAppointment({
        id: id!,
        updates: { 
          appointment_date: rescheduleDate,
          start_time: rescheduleTime
        }
      }).unwrap();
      
      dispatch(addToast({
        title: 'Success',
        message: 'Appointment rescheduled successfully',
        type: 'success'
      }));
      
      setRescheduleDialogOpen(false);
      setRescheduleDate('');
      setRescheduleTime('');
      refetch();
    } catch (_error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      dispatch(addToast({
        title: 'Error',
        message: 'Failed to reschedule appointment',
        type: 'error'
      }));
    }
  };

  const handleSendReminder = async () => {
    try {
      await sendSmsReminder(id!).unwrap();
      
      dispatch(addToast({
        title: 'Success',
        message: 'SMS reminder sent successfully',
        type: 'success'
      }));
    } catch (_error) { // eslint-disable-line @typescript-eslint/no-unused-vars
      dispatch(addToast({
        title: 'Error',
        message: 'Failed to send SMS reminder',
        type: 'error'
      }));
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !appointment) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load appointment details. Please try again.
      </Alert>
    );
  }

  const isPast = isPastAppointment(appointment.appointment_date, appointment.start_time);
  const canConfirm = appointment.status === 'scheduled';
  const canComplete = appointment.status === 'confirmed' || appointment.status === 'in-progress';
  const canCancel = appointment.status !== 'completed' && appointment.status !== 'cancelled';
  const canMarkNoShow = isPast && appointment.status === 'scheduled';
  const canReschedule = appointment.status !== 'completed' && appointment.status !== 'cancelled';

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/app/appointments')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Appointment Details</Typography>
      </Box>

      {/* Status Alert */}
      {isPast && appointment.status === 'scheduled' && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          This appointment is in the past and hasn't been updated. Please confirm if the patient showed up or mark as no-show.
        </Alert>
      )}

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Appointment Information */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
                <Typography variant="h6">Appointment Information</Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip 
                    label={appointment.status.replace('-', ' ').toUpperCase()} 
                    color={getStatusColor(appointment.status)}
                    size="small"
                  />
                  <Chip 
                    label={appointment.priority.toUpperCase()} 
                    color={getPriorityColor(appointment.priority)}
                    size="small"
                  />
                </Box>
              </Box>

              <Grid container spacing={3}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <EventIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Date"
                        secondary={formatDate(appointment.appointment_date)}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <AccessTimeIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Time"
                        secondary={formatTime(appointment.start_time)}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <ScheduleIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Duration"
                        secondary={`${appointment.duration} minutes`}
                      />
                    </ListItem>
                  </List>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <PersonIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Patient"
                        secondary={appointment.patient_name}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <PersonIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Provider"
                        secondary={appointment.provider_name}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <LocationIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Type"
                        secondary={appointment.appointment_type_name}
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>

              {appointment.room && (
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <LocationIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Room"
                      secondary={appointment.room}
                    />
                  </ListItem>
                </List>
              )}

              {appointment.notes && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    <NoteIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Notes
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {appointment.notes}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Actions */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actions
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {canConfirm && (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<CheckCircleIcon />}
                    onClick={handleConfirmAppointment}
                    fullWidth
                  >
                    Confirm Appointment
                  </Button>
                )}
                
                {canComplete && (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<CheckCircleIcon />}
                    onClick={handleCompleteAppointment}
                    fullWidth
                  >
                    Mark as Completed
                  </Button>
                )}
                
                {canCancel && (
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<CancelIcon />}
                    onClick={() => setCancelDialogOpen(true)}
                    fullWidth
                  >
                    Cancel Appointment
                  </Button>
                )}
                
                {canMarkNoShow && (
                  <Button
                    variant="outlined"
                    color="warning"
                    startIcon={<WarningIcon />}
                    onClick={() => setNoShowDialogOpen(true)}
                    fullWidth
                  >
                    Mark as No-Show
                  </Button>
                )}
                
                {canReschedule && (
                  <Button
                    variant="outlined"
                    startIcon={<ScheduleIcon />}
                    onClick={() => setRescheduleDialogOpen(true)}
                    fullWidth
                  >
                    Reschedule
                  </Button>
                )}
                
                <Button
                  variant="outlined"
                  startIcon={<SmsIcon />}
                  onClick={handleSendReminder}
                  fullWidth
                >
                  Send SMS Reminder
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Contact Information
              </Typography>
              
              {appointment.patient_phone && (
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <PhoneIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Phone"
                      secondary={appointment.patient_phone}
                    />
                  </ListItem>
                </List>
              )}
              
              {appointment.patient_email && (
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <EmailIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Email"
                      secondary={appointment.patient_email}
                    />
                  </ListItem>
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Cancel Dialog */}
      <Dialog open={cancelDialogOpen} onClose={() => setCancelDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Cancel Appointment</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Please provide a reason for cancelling this appointment.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Cancellation Reason"
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            placeholder="e.g., Patient requested cancellation, Provider unavailable, etc."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCancelAppointment} color="error" variant="contained">
            Confirm Cancellation
          </Button>
        </DialogActions>
      </Dialog>

      {/* No-Show Dialog */}
      <Dialog open={noShowDialogOpen} onClose={() => setNoShowDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Mark as No-Show</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            This appointment has passed without the patient showing up. Please provide any relevant details.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="No-Show Details"
            value={noShowReason}
            onChange={(e) => setNoShowReason(e.target.value)}
            placeholder="e.g., Patient didn't show up, no call received, etc."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoShowDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleMarkNoShow} color="warning" variant="contained">
            Mark as No-Show
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reschedule Dialog */}
      <Dialog open={rescheduleDialogOpen} onClose={() => setRescheduleDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Reschedule Appointment</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                type="date"
                label="New Date"
                value={rescheduleDate}
                onChange={(e) => setRescheduleDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                type="time"
                label="New Time"
                value={rescheduleTime}
                onChange={(e) => setRescheduleTime(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRescheduleDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRescheduleAppointment} color="primary" variant="contained">
            Reschedule
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};