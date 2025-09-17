import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
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
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  TextField,
  Fab,
  Tooltip,
  Badge,
} from '@mui/material';
// ✅ Correct Grid import for MUI v7
import Grid from '@mui/material/Grid';

import {
  CalendarToday as CalendarIcon,
  Add as AddIcon,
  AccessTime as AccessTimeIcon,
  Person as PersonIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';
import { useGetAppointmentsQuery } from '../../store/api/apiSlice';
import AppointmentScheduler from '../../components/appointments/AppointmentScheduler';
import AppointmentCalendar from '../../components/appointments/AppointmentCalendar';

interface Appointment {
  id: string;
  patientId: string;
  patientName: string;
  patientAvatar?: string;
  date: string;
  time: string;
  duration: number; // in minutes
  type: 'consultation' | 'follow-up' | 'check-up' | 'emergency';
  status:
    | 'scheduled'
    | 'confirmed'
    | 'in-progress'
    | 'completed'
    | 'cancelled'
    | 'no-show';
  provider: string;
  providerId: string; // Added missing providerId property
  notes?: string;
  room?: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({
  children,
  value,
  index,
  ...other
}) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`appointment-tabpanel-${index}`}
      aria-labelledby={`appointment-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const mockAppointments: Appointment[] = [
  {
    id: '1',
    patientId: '1',
    patientName: 'John Doe',
    date: '2024-01-25',
    time: '09:00',
    duration: 30,
    type: 'consultation',
    status: 'confirmed',
    provider: 'Dr. Smith',
    providerId: '1',
    room: 'Room 101',
    notes: 'Regular checkup',
  },
  {
    id: '2',
    patientId: '2',
    patientName: 'Jane Smith',
    date: '2024-01-25',
    time: '10:30',
    duration: 45,
    type: 'follow-up',
    status: 'scheduled',
    provider: 'Dr. Johnson',
    providerId: '2',
    room: 'Room 102',
  },
  {
    id: '3',
    patientId: '3',
    patientName: 'Mike Johnson',
    date: '2024-01-25',
    time: '14:00',
    duration: 60,
    type: 'check-up',
    status: 'in-progress',
    provider: 'Dr. Brown',
    providerId: '3',
    room: 'Room 103',
  },
  {
    id: '4',
    patientId: '4',
    patientName: 'Sarah Wilson',
    date: '2024-01-26',
    time: '11:00',
    duration: 30,
    type: 'consultation',
    status: 'scheduled',
    provider: 'Dr. Smith',
    providerId: '1',
    room: 'Room 101',
  },
];

const timeSlots = [
  '08:00',
  '08:30',
  '09:00',
  '09:30',
  '10:00',
  '10:30',
  '11:00',
  '11:30',
  '12:00',
  '12:30',
  '13:00',
  '13:30',
  '14:00',
  '14:30',
  '15:00',
  '15:30',
  '16:00',
  '16:30',
  '17:00',
  '17:30',
];

// Mock data for the new components
const mockPatients = [
  { id: '1', name: 'John Doe', email: 'john.doe@email.com', phone: '(555) 123-4567', dateOfBirth: '1985-06-15' },
  { id: '2', name: 'Jane Smith', email: 'jane.smith@email.com', phone: '(555) 234-5678', dateOfBirth: '1990-03-22' },
  { id: '3', name: 'Mike Johnson', email: 'mike.johnson@email.com', phone: '(555) 345-6789', dateOfBirth: '1978-11-08' },
  { id: '4', name: 'Sarah Wilson', email: 'sarah.wilson@email.com', phone: '(555) 456-7890', dateOfBirth: '1992-09-14' },
];

const mockProviders = [
  { id: '1', name: 'Smith', specialization: 'Cardiology', email: 'dr.smith@hospital.com', color: '#2196F3', availability: ['09:00-17:00'] },
  { id: '2', name: 'Johnson', specialization: 'Neurology', email: 'dr.johnson@hospital.com', color: '#4CAF50', availability: ['08:00-16:00'] },
  { id: '3', name: 'Brown', specialization: 'Orthopedics', email: 'dr.brown@hospital.com', color: '#FF9800', availability: ['10:00-18:00'] },
];

const mockAppointmentTypes = [
  { id: '1', name: 'Consultation', duration: 30, description: 'Initial consultation', color: '#2196F3' },
  { id: '2', name: 'Follow-up', duration: 20, description: 'Follow-up appointment', color: '#4CAF50' },
  { id: '3', name: 'Check-up', duration: 45, description: 'Regular check-up', color: '#FF9800' },
  { id: '4', name: 'Emergency', duration: 60, description: 'Emergency consultation', color: '#F44336' },
];

export const AppointmentsPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const [tabValue, setTabValue] = useState(0);
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0],
  );
  const [viewMode, setViewMode] = useState<'calendar' | 'list'>('calendar');
  const [schedulerOpen, setSchedulerOpen] = useState(false);
  const [newAppointmentOpen, setNewAppointmentOpen] = useState(false); // Added missing state
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

  const { refetch } = useGetAppointmentsQuery({
    date: selectedDate,
  });

  useEffect(() => {
    dispatch(setCurrentPage('appointments'));
    dispatch(
      setBreadcrumbs([{ label: 'Appointments', path: '/appointments' }]),
    );
  }, [dispatch]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'success';
      case 'scheduled':
        return 'info';
      case 'in-progress':
        return 'warning';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'error';
      case 'no-show':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'consultation':
        return 'primary';
      case 'follow-up':
        return 'secondary';
      case 'check-up':
        return 'info';
      case 'emergency':
        return 'error';
      default:
        return 'default';
    }
  };

  const getAppointmentsForDate = (date: string) => {
    return mockAppointments.filter((apt) => apt.date === date);
  };

  const getTodayAppointments = () => {
    const today = new Date().toISOString().split('T')[0];
    return getAppointmentsForDate(today);
  };

  const getUpcomingAppointments = () => {
    const today = new Date();
    return mockAppointments.filter((apt) => new Date(apt.date) > today);
  };

  // Handlers for the new components
  const handleNewAppointment = (date?: Date, providerId?: string) => {
    setEditingAppointment(null);
    setSchedulerOpen(true);
  };

  const handleAppointmentClick = (appointment: Appointment) => {
    setSelectedAppointment(appointment);
    // Could open a details dialog here
    console.log('Appointment clicked:', appointment);
  };

  const handleAppointmentEdit = (appointment: Appointment) => {
    setEditingAppointment(appointment);
    setSchedulerOpen(true);
  };

  const handleAppointmentDelete = async (appointmentId: string) => {
    try {
      // Here you would call the API to delete the appointment
      console.log('Deleting appointment:', appointmentId);
      // For now, just log it
      // await deleteAppointment(appointmentId);
      refetch();
    } catch (error) {
      console.error('Failed to delete appointment:', error);
    }
  };

  const handleAppointmentSubmit = async (appointmentData: any) => {
    try {
      // Here you would call the API to create/update the appointment
      console.log('Submitting appointment:', appointmentData);
      // For now, just log it
      // if (editingAppointment) {
      //   await updateAppointment(editingAppointment.id, appointmentData);
      // } else {
      //   await createAppointment(appointmentData);
      // }
      refetch();
    } catch (error) {
      console.error('Failed to submit appointment:', error);
      throw error;
    }
  };

  const handleDateRangeChange = (start: Date, end: Date) => {
    // Here you could update the date range for fetching appointments
    console.log('Date range changed:', start, end);
  };

  const renderCalendarView = () => {
    const appointmentsForDate = getAppointmentsForDate(selectedDate);

    return (
      <Grid container spacing={3}>
        {/* Date Selector */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <TextField
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                sx={{ minWidth: 200 }}
              />
              <Button
                variant="outlined"
                onClick={() =>
                  setSelectedDate(new Date().toISOString().split('T')[0])
                }
              >
                Today
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => refetch()}
              >
                Refresh
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Time Slots Grid */}
        <Grid size={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {new Date(selectedDate).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </Typography>
            <Grid container spacing={1}>
              {timeSlots.map((timeSlot) => {
                const appointment = appointmentsForDate.find(
                  (apt) => apt.time === timeSlot,
                );

                return (
                  <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={timeSlot}>
                    <Card
                      sx={{
                        minHeight: 100,
                        cursor: appointment ? 'pointer' : 'default',
                        bgcolor: appointment ? 'primary.light' : 'grey.50',
                        border: appointment ? 2 : 1,
                        borderColor: appointment
                          ? 'primary.main'
                          : 'grey.200',
                        '&:hover': {
                          bgcolor: appointment
                            ? 'primary.main'
                            : 'grey.100',
                          color: appointment ? 'white' : 'inherit',
                        },
                      }}
                      onClick={() =>
                        appointment &&
                        navigate(`/app/appointments/${appointment.id}`)
                      }
                    >
                      <CardContent
                        sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}
                      >
                        <Typography
                          variant="subtitle2"
                          fontWeight="bold"
                        >
                          {timeSlot}
                        </Typography>
                        {appointment ? (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2" noWrap>
                              {appointment.patientName}
                            </Typography>
                            <Chip
                              label={appointment.type}
                              size="small"
                              color={
                                getTypeColor(
                                  appointment.type,
                                ) as any
                              }
                              sx={{
                                mt: 0.5,
                                fontSize: '0.7rem',
                              }}
                            />
                            <Typography
                              variant="caption"
                              display="block"
                              sx={{ mt: 0.5 }}
                            >
                              {appointment.provider}
                            </Typography>
                          </Box>
                        ) : (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mt: 1 }}
                          >
                            Available
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  const renderListView = (appointments: Appointment[]) => {
    return (
      <List>
        {appointments.map((appointment) => (
          <ListItem
            key={appointment.id}
            sx={{
              border: 1,
              borderColor: 'grey.200',
              borderRadius: 1,
              mb: 1,
              cursor: 'pointer',
              '&:hover': { bgcolor: 'grey.50' },
            }}
            onClick={() => navigate(`/app/appointments/${appointment.id}`)}
          >
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                {appointment.patientAvatar ? (
                  <img
                    src={appointment.patientAvatar}
                    alt={appointment.patientName}
                  />
                ) : (
                  <PersonIcon />
                )}
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle1" fontWeight="medium">
                    {appointment.patientName}
                  </Typography>
                  <Chip
                    label={appointment.status}
                    size="small"
                    color={getStatusColor(appointment.status) as any}
                    variant="outlined"
                  />
                </Box>
              }
              secondary={
                <Box sx={{ mt: 0.5 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      mb: 0.5,
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                      }}
                    >
                      <CalendarIcon sx={{ fontSize: 14 }} />
                      <Typography variant="body2">
                        {new Date(
                          appointment.date,
                        ).toLocaleDateString()}
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                      }}
                    >
                      <AccessTimeIcon sx={{ fontSize: 14 }} />
                      <Typography variant="body2">
                        {appointment.time} ({appointment.duration}
                        min)
                      </Typography>
                    </Box>
                  </Box>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                    }}
                  >
                    <Typography variant="body2">
                      {appointment.provider}
                    </Typography>
                    {appointment.room && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                      >
                        {appointment.room}
                      </Typography>
                    )}
                    <Chip
                      label={appointment.type}
                      size="small"
                      color={getTypeColor(appointment.type) as any}
                    />
                  </Box>
                </Box>
              }
              slotProps={{
                primary: { component: 'div' },
                secondary: { component: 'div' }
              }}
            />
          </ListItem>
        ))}
      </List>
    );
  };

  return (
    <Box>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Typography variant="h4" component="h1" fontWeight="bold">
          Appointments
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            onClick={() =>
              setViewMode(
                viewMode === 'calendar' ? 'list' : 'calendar',
              )
            }
            color={viewMode === 'calendar' ? 'primary' : 'default'}
          >
            {viewMode === 'calendar' ? (
              <ViewListIcon />
            ) : (
              <ViewModuleIcon />
            )}
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setNewAppointmentOpen(true)}
          >
            New Appointment
          </Button>
        </Box>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab
            label={
              <Badge
                badgeContent={getTodayAppointments().length}
                color="primary"
              >
                Today
              </Badge>
            }
          />
          <Tab
            label={
              <Badge
                badgeContent={getUpcomingAppointments().length}
                color="secondary"
              >
                Upcoming
              </Badge>
            }
          />
          <Tab label="Calendar" />
          <Tab label="All Appointments" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Today's Appointments ({getTodayAppointments().length})
          </Typography>
          {getTodayAppointments().length > 0 ? (
            renderListView(getTodayAppointments())
          ) : (
            <Typography
              color="text.secondary"
              textAlign="center"
              sx={{ py: 4 }}
            >
              No appointments scheduled for today
            </Typography>
          )}
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Upcoming Appointments ({getUpcomingAppointments().length})
          </Typography>
          {getUpcomingAppointments().length > 0 ? (
            renderListView(getUpcomingAppointments())
          ) : (
            <Typography
              color="text.secondary"
              textAlign="center"
              sx={{ py: 4 }}
            >
              No upcoming appointments
            </Typography>
          )}
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <AppointmentCalendar
          appointments={mockAppointments.map(apt => ({
            id: apt.id,
            patientName: apt.patientName,
            patientId: apt.patientId,
            providerName: apt.provider,
            providerId: apt.providerId,
            appointmentType: apt.type,
            date: apt.date,
            time: apt.time,
            duration: apt.duration,
            status: apt.status,
            priority: 'medium' as const,
            location: apt.room || 'Main Hospital',
            notes: apt.notes,
          }))}
          providers={mockProviders}
          onAppointmentClick={handleAppointmentClick}
          onAppointmentEdit={handleAppointmentEdit}
          onAppointmentDelete={handleAppointmentDelete}
          onNewAppointment={handleNewAppointment}
          onDateRangeChange={handleDateRangeChange}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            All Appointments ({mockAppointments.length})
          </Typography>
          {renderListView(mockAppointments)}
        </Paper>
      </TabPanel>

      {/* Appointment Scheduler */}
      <AppointmentScheduler
        open={schedulerOpen}
        onClose={() => {
          setSchedulerOpen(false);
          setEditingAppointment(null);
        }}
        onSubmit={handleAppointmentSubmit}
        editingAppointment={editingAppointment}
        patients={mockPatients}
        providers={mockProviders}
        appointmentTypes={mockAppointmentTypes}
      />

      {/* Floating Action Button */}
      <Tooltip title="New Appointment" placement="left">
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 24, right: 24 }}
          onClick={handleNewAppointment}
        >
          <AddIcon />
        </Fab>
      </Tooltip>
    </Box>
  );
};

export default AppointmentsPage;
