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
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Fab,
  Tooltip,
  Badge,
} from '@mui/material';


import {
  CalendarToday as CalendarIcon,
  Add as AddIcon,
  AccessTime as AccessTimeIcon,
  Person as PersonIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
} from '@mui/icons-material';

import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';
import { useGetAppointmentsQuery, useGetPatientsQuery, useGetStaffQuery, useCreateAppointmentMutation } from '../../store/api/apiSlice';
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





// Transform API data to match component interface
const transformPatientData = (patients: any[]) => {
  return patients?.map(patient => ({
    id: patient.id,
    name: patient.name || 'Unknown Patient',
    email: patient.email,
    phone: patient.phone,
    dateOfBirth: patient.date_of_birth,
    age: patient.age,
    gender: patient.gender,
    status: patient.status,
  })) || [];
};

const transformStaffData = (staff: any[]) => {
  return staff?.map(member => ({
    id: member.id,
    name: member.name || 'Unknown Staff',
    specialization: member.specialization || member.department || 'General Practice',
    email: member.email,
    color: member.color || '#2196F3',
    availability: member.availability || ['09:00-17:00']
  })) || [];
};

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
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);

  const { data: appointmentsData, isLoading, error, refetch } = useGetAppointmentsQuery({
    date: selectedDate,
  });

  // Fetch patients and staff data
  const { data: patientsData, isLoading: patientsLoading } = useGetPatientsQuery({
    page: 1,
    limit: 1000, // Get all patients for selection
  });
  
  const { data: staffData, isLoading: staffLoading } = useGetStaffQuery();
  
  const [createAppointment, { isLoading: isCreating }] = useCreateAppointmentMutation();

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

  // Get appointments from API data
  const appointments = appointmentsData?.appointments || [];

  const getAppointmentsForDate = (date: string) => {
    return appointments.filter((apt) => apt.date === date);
  };

  const getTodayAppointments = () => {
    const today = new Date().toISOString().split('T')[0];
    return getAppointmentsForDate(today);
  };

  const getUpcomingAppointments = () => {
    const today = new Date();
    return appointments.filter((apt) => new Date(apt.date) > today);
  };

  // Helper function to convert AppointmentCalendar appointment to AppointmentsPage appointment
  const convertCalendarAppointment = (calendarAppointment: any): Appointment => {
    return {
      id: calendarAppointment.id,
      patientId: calendarAppointment.patientId,
      patientName: calendarAppointment.patientName,
      patientAvatar: calendarAppointment.patientAvatar,
      date: calendarAppointment.date,
      time: calendarAppointment.time,
      duration: calendarAppointment.duration,
      type: calendarAppointment.appointmentType as 'consultation' | 'follow-up' | 'check-up' | 'emergency',
      status: calendarAppointment.status,
      provider: calendarAppointment.providerName,
      providerId: calendarAppointment.providerId,
      notes: calendarAppointment.notes,
      room: calendarAppointment.location,
    };
  };

  // Handlers for the new components
  const handleNewAppointment = () => {
    setEditingAppointment(null);
    setSchedulerOpen(true);
  };

  const handleAppointmentClick = (appointment: Appointment) => {
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
      // Transform the appointment data to match API expectations
      const apiData = {
        patient_id: appointmentData.patientId,
        provider_id: appointmentData.providerId,
        appointment_type: appointmentData.appointmentType,
        date: appointmentData.date,
        time: appointmentData.time,
        duration: appointmentData.duration,
        location: appointmentData.location,
        priority: appointmentData.priority || 'medium',
        notes: appointmentData.notes,
        status: 'scheduled' as const,
        reminder_preferences: appointmentData.reminderPreferences,
      };

      if (editingAppointment) {
        // TODO: Implement update appointment when the API is available
        console.log('Updating appointment:', apiData);
        // await updateAppointment({ id: editingAppointment.id, updates: apiData });
      } else {
        await createAppointment(apiData).unwrap();
      }
      
      // Close the scheduler and refresh data
      setSchedulerOpen(false);
      setEditingAppointment(null);
      refetch();
    } catch (error) {
      console.error('Failed to submit appointment:', error);
      throw error;
    }
  };

  const handleDateRangeChange = (start: Date, end: Date) => {
    // Here you could update the date range for fetching appointments
    console.log('Date range changed:', start, end);
    // Update selected date to trigger API refetch
    setSelectedDate(start.toISOString().split('T')[0]);
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
            onClick={() => setSchedulerOpen(true)}
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
            Today's Appointments ({isLoading ? '...' : getTodayAppointments().length})
          </Typography>
          {isLoading ? (
            <Typography textAlign="center" sx={{ py: 4 }}>
              Loading appointments...
            </Typography>
          ) : error ? (
            <Typography color="error" textAlign="center" sx={{ py: 4 }}>
              Error loading appointments
            </Typography>
          ) : getTodayAppointments().length > 0 ? (
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
            Upcoming Appointments ({isLoading ? '...' : getUpcomingAppointments().length})
          </Typography>
          {isLoading ? (
            <Typography textAlign="center" sx={{ py: 4 }}>
              Loading appointments...
            </Typography>
          ) : error ? (
            <Typography color="error" textAlign="center" sx={{ py: 4 }}>
              Error loading appointments
            </Typography>
          ) : getUpcomingAppointments().length > 0 ? (
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
        {isLoading ? (
          <Typography textAlign="center" sx={{ py: 4 }}>
            Loading appointments...
          </Typography>
        ) : error ? (
          <Typography color="error" textAlign="center" sx={{ py: 4 }}>
            Error loading appointments
          </Typography>
        ) : (
          <AppointmentCalendar
            appointments={appointments.map(apt => ({
              id: apt.id,
              patientName: apt.patient?.firstName + ' ' + apt.patient?.lastName || 'Unknown Patient',
              patientId: apt.patientId,
              providerName: apt.doctor?.firstName + ' ' + apt.doctor?.lastName || 'Unknown Doctor',
              providerId: apt.doctorId,
              appointmentType: apt.type || 'consultation',
              date: apt.startTime.split('T')[0],
              time: apt.startTime.split('T')[1]?.substring(0, 5) || '00:00',
              duration: Math.round((new Date(apt.endTime).getTime() - new Date(apt.startTime).getTime()) / (1000 * 60)),
              status: apt.status.replace('_', '-') as 'scheduled' | 'confirmed' | 'in-progress' | 'completed' | 'cancelled' | 'no-show',
              priority: apt.priority as 'low' | 'medium' | 'high',
              location: apt.location || 'Main Hospital',
              notes: apt.notes,
            }))}
            providers={transformStaffData(staffData || [])}
            onAppointmentClick={(appointment) => handleAppointmentClick(convertCalendarAppointment(appointment))}
            onAppointmentEdit={(appointment) => handleAppointmentEdit(convertCalendarAppointment(appointment))}
            onAppointmentDelete={handleAppointmentDelete}
            onNewAppointment={handleNewAppointment}
            onDateRangeChange={handleDateRangeChange}
          />
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            All Appointments ({isLoading ? '...' : appointments.length})
          </Typography>
          {isLoading ? (
            <Typography textAlign="center" sx={{ py: 4 }}>
              Loading appointments...
            </Typography>
          ) : error ? (
            <Typography color="error" textAlign="center" sx={{ py: 4 }}>
              Error loading appointments
            </Typography>
          ) : appointments.length > 0 ? (
            renderListView(appointments)
          ) : (
            <Typography
              color="text.secondary"
              textAlign="center"
              sx={{ py: 4 }}
            >
              No appointments found
            </Typography>
          )}
        </Paper>
      </TabPanel>

      {/* Appointment Scheduler */}
      <AppointmentScheduler
        open={schedulerOpen}
        onClose={() => setSchedulerOpen(false)}
        onSubmit={handleAppointmentSubmit}
        patients={transformPatientData(patientsData?.patients || [])}
        providers={transformStaffData(staffData || [])}
        appointmentTypes={mockAppointmentTypes}
        editingAppointment={editingAppointment}
        loading={isCreating}
      />

      {/* Floating Action Button */}
      <Tooltip title="New Appointment" placement="left">
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 24, right: 24 }}
          onClick={() => handleNewAppointment()}
        >
          <AddIcon />
        </Fab>
      </Tooltip>
    </Box>
  );
};

export default AppointmentsPage;
