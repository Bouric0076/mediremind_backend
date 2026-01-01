import React, { useEffect, useState } from 'react';
import { format, parseISO, isSameDay, isAfter } from 'date-fns';
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
  keyframes,
  TextField,
  InputAdornment,
} from '@mui/material';


import {
  CalendarToday as CalendarIcon,
  Add as AddIcon,
  AccessTime as AccessTimeIcon,
  Person as PersonIcon,
  Search as SearchIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
  Settings as SettingsIcon,
  Sms as SmsIcon,
} from '@mui/icons-material';

import { setBreadcrumbs, setCurrentPage, addToast } from '../../store/slices/uiSlice';
import { useGetAppointmentsQuery, useGetPatientsQuery, useGetStaffQuery, useGetAppointmentTypesQuery, useCreateAppointmentMutation, useSendManualSmsReminderMutation } from '../../store/api/apiSlice';
import AppointmentScheduler from '../../components/appointments/AppointmentScheduler';
import AppointmentCalendar from '../../components/appointments/AppointmentCalendar';

// Define the pulse animation
const pulseAnimation = keyframes`
  0% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  50% {
    transform: scale(1);
    opacity: 0.8;
  }
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
`;

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
  const [selectedAppointmentDate, setSelectedAppointmentDate] = useState<Date | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: appointmentsData, isLoading, error, refetch } = useGetAppointmentsQuery({
    date: selectedDate,
  });

  // Fetch patients and staff data
  const { data: patientsData } = useGetPatientsQuery({
    page: 1,
    limit: 1000, // Get all patients for selection
  });
  
  const { data: staffData } = useGetStaffQuery();
  
  // Fetch appointment types
  const { data: appointmentTypesData } = useGetAppointmentTypesQuery();
  
  const [createAppointment, { isLoading: isCreating }] = useCreateAppointmentMutation();
  const [sendManualSmsReminder, { isLoading: isSendingSms }] = useSendManualSmsReminderMutation();

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

  // Transform API data to match frontend interface
  const transformApiAppointment = (apiAppointment: any) => {
    return {
      id: apiAppointment.id,
      patientId: apiAppointment.patient_id || '',
      patientName: apiAppointment.patient_name || 'Unknown Patient',
      date: apiAppointment.appointment_date || apiAppointment.date,
      time: apiAppointment.start_time || apiAppointment.time,
      duration: apiAppointment.duration || 30,
      type: (apiAppointment.appointment_type_name || apiAppointment.type || 'consultation').toLowerCase().replace(' ', '-'),
      status: apiAppointment.status || 'scheduled',
      provider: apiAppointment.provider_name || apiAppointment.provider || 'Unknown Provider',
      providerId: apiAppointment.provider_id || '',
      notes: apiAppointment.notes || '',
      room: apiAppointment.room || 'Main Hospital',
      priority: apiAppointment.priority || 'medium',
      createdAt: apiAppointment.created_at || new Date().toISOString(),
      updatedAt: apiAppointment.updated_at || new Date().toISOString(),
    };
  };

  // Get appointments from API data
  const appointments = (appointmentsData?.appointments || []).map(transformApiAppointment);

  const getAppointmentsForDate = (date: string) => {
    return appointments.filter(apt => {
      if (!apt.date) return false;
      
      // Handle YYYY-MM-DD format from API
      const appointmentDate = parseISO(apt.date);
      const targetDate = parseISO(date);
      
      if (isNaN(appointmentDate.getTime())) {
        // Try parsing as simple date string
        const [year, month, day] = apt.date.split('-').map(Number);
        const aptDate = new Date(year, month - 1, day);
        return isSameDay(aptDate, targetDate);
      }
      
      return isSameDay(appointmentDate, targetDate);
    });
  };

  const getTodayAppointments = () => {
    const today = new Date().toISOString().split('T')[0];
    return getAppointmentsForDate(today);
  };

  const filterAppointmentsBySearch = (appointments: Appointment[]) => {
    if (!searchQuery.trim()) return appointments;
    
    const query = searchQuery.toLowerCase();
    return appointments.filter(apt => 
      apt.patientName.toLowerCase().includes(query) ||
      apt.provider.toLowerCase().includes(query) ||
      apt.type.toLowerCase().includes(query)
    );
  };

  const getUpcomingAppointments = () => {
    const today = new Date();
    return appointments.filter(apt => {
      if (!apt.date) return false;
      
      // Handle YYYY-MM-DD format from API
      let appointmentDate = parseISO(apt.date);
      
      if (isNaN(appointmentDate.getTime())) {
        // Try parsing as simple date string
        const [year, month, day] = apt.date.split('-').map(Number);
        appointmentDate = new Date(year, month - 1, day);
      }
      
      // Only include future appointments (excluding today)
      return isAfter(appointmentDate, today);
    }).sort((a, b) => {
      // Handle YYYY-MM-DD format from API
      let dateA = parseISO(a.date);
      let dateB = parseISO(b.date);
      
      if (isNaN(dateA.getTime())) {
        const [yearA, monthA, dayA] = a.date.split('-').map(Number);
        dateA = new Date(yearA, monthA - 1, dayA);
      }
      
      if (isNaN(dateB.getTime())) {
        const [yearB, monthB, dayB] = b.date.split('-').map(Number);
        dateB = new Date(yearB, monthB - 1, dayB);
      }
      
      return dateA.getTime() - dateB.getTime();
    });
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
  const handleNewAppointment = (selectedDate?: Date) => {
    setEditingAppointment(null);
    // Only set the date if it's today or in the future
    if (selectedDate) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const clickedDate = new Date(selectedDate);
      clickedDate.setHours(0, 0, 0, 0);
      
      if (clickedDate >= today) {
        setSelectedAppointmentDate(selectedDate);
      } else {
        setSelectedAppointmentDate(null);
      }
    } else {
      setSelectedAppointmentDate(null);
    }
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

  const handleSendSmsReminder = async (appointmentId: string) => {
    try {
      const result = await sendManualSmsReminder(appointmentId).unwrap();
      console.log('SMS reminder sent successfully:', result);
      dispatch(addToast({
        title: 'Success',
        message: 'SMS reminder sent successfully',
        type: 'success',
        duration: 3000,
      }));
    } catch (error) {
      console.error('Failed to send SMS reminder:', error);
      dispatch(addToast({
        title: 'Error',
        message: 'Failed to send SMS reminder. Please try again.',
        type: 'error',
        duration: 5000,
      }));
    }
  };

  const handleAppointmentSubmit = async (appointmentData: any) => {
    try {
      // Debug the date being processed
      console.log('handleAppointmentSubmit - appointmentData.date:', appointmentData.date);
      console.log('handleAppointmentSubmit - appointmentData.date type:', typeof appointmentData.date);
      console.log('handleAppointmentSubmit - appointmentData.date toISOString:', appointmentData.date?.toISOString());
      
      // Transform the appointment data to match Django API expectations
      const appointmentDate = appointmentData.date;
      let formattedDate = '';
      
      if (appointmentDate) {
        if (appointmentDate instanceof Date) {
          // Use format from date-fns to preserve local date instead of UTC conversion
          formattedDate = format(appointmentDate, 'yyyy-MM-dd');
        } else if (typeof appointmentDate === 'string') {
          formattedDate = appointmentDate;
        } else {
          console.warn('Unexpected date format:', appointmentDate);
          formattedDate = format(new Date(), 'yyyy-MM-dd');
        }
      }
      
      console.log('handleAppointmentSubmit - formattedDate:', formattedDate);
      
      const apiData = {
        patient_id: appointmentData.patientId,
        provider_id: appointmentData.providerId,
        appointment_type_id: appointmentData.appointmentTypeId,
        appointment_date: formattedDate,
        start_time: appointmentData.time ? appointmentData.time.toTimeString().split(' ')[0].substring(0, 5) : '',
        duration: appointmentData.duration || 30, // Include dynamic duration
        reason: appointmentData.notes || 'General appointment',
        priority: appointmentData.priority || 'medium',
        notes: appointmentData.notes || '',
        title: appointmentData.title || '',
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
            secondaryAction={
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Tooltip title="Send SMS Reminder">
                  <IconButton
                    edge="end"
                    aria-label="send-sms-reminder"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSendSmsReminder(appointment.id);
                    }}
                    disabled={isSendingSms}
                    color="primary"
                  >
                    <SmsIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            }
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
                        {(() => {
                          try {
                            const appointmentDate = parseISO(appointment.date);
                            if (isNaN(appointmentDate.getTime())) {
                              const [year, month, day] = appointment.date.split('-').map(Number);
                              const dateObj = new Date(year, month - 1, day);
                              return dateObj.toLocaleDateString();
                            }
                            return appointmentDate.toLocaleDateString();
                          } catch (error) {
                            return appointment.date;
                          }
                        })()}
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
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => navigate('/app/calendar')}
            sx={{ mr: 1 }}
          >
            Calendar Integration
          </Button>
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

      {/* Search Field */}
      <Paper sx={{ mb: 2, p: 2 }}>
        <TextField
          fullWidth
          placeholder="Search appointments by patient name, provider, or type..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
          }}
          size="small"
        />
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab
            label={
              <Badge
                badgeContent={filterAppointmentsBySearch(getTodayAppointments()).length}
                color="primary"
              >
                Today
              </Badge>
            }
          />
          <Tab
            label={
              <Badge
                badgeContent={filterAppointmentsBySearch(getUpcomingAppointments()).length}
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
            Today's Appointments ({isLoading ? '...' : filterAppointmentsBySearch(getTodayAppointments()).length})
          </Typography>
          {isLoading ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                <Box sx={{ width: 40, height: 40, animation: `${pulseAnimation} 1.5s infinite ease-in-out`, borderRadius: '50%', bgcolor: 'primary.light' }} />
              </Box>
              <Typography variant="body1" color="text.secondary">
                Loading appointments...
              </Typography>
            </Box>
          ) : error ? (
            <Typography color="error" textAlign="center" sx={{ py: 4 }}>
              Error loading appointments
            </Typography>
          ) : filterAppointmentsBySearch(getTodayAppointments()).length > 0 ? (
            renderListView(filterAppointmentsBySearch(getTodayAppointments()))
          ) : (
            <Typography
              color="text.secondary"
              textAlign="center"
              sx={{ py: 4 }}
            >
              {searchQuery ? 'No appointments match your search' : 'No appointments scheduled for today'}
            </Typography>
          )}
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Upcoming Appointments ({isLoading ? '...' : filterAppointmentsBySearch(getUpcomingAppointments()).length})
          </Typography>
          {isLoading ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                <Box sx={{ width: 40, height: 40, animation: 'pulse 1.5s infinite ease-in-out', borderRadius: '50%', bgcolor: 'primary.light' }} />
              </Box>
              <Typography variant="body1" color="text.secondary">
                Loading appointments...
              </Typography>
            </Box>
          ) : error ? (
            <Typography color="error" textAlign="center" sx={{ py: 4 }}>
              Error loading appointments
            </Typography>
          ) : filterAppointmentsBySearch(getUpcomingAppointments()).length > 0 ? (
            renderListView(filterAppointmentsBySearch(getUpcomingAppointments()))
          ) : (
            <Typography
              color="text.secondary"
              textAlign="center"
              sx={{ py: 4 }}
            >
              {searchQuery ? 'No appointments match your search' : 'No upcoming appointments'}
            </Typography>
          )}
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {isLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <Box sx={{ width: 40, height: 40, animation: 'pulse 1.5s infinite ease-in-out', borderRadius: '50%', bgcolor: 'primary.light' }} />
            </Box>
            <Typography variant="body1" color="text.secondary">
              Loading appointments...
            </Typography>
          </Box>
        ) : error ? (
          <Typography color="error" textAlign="center" sx={{ py: 4 }}>
            Error loading appointments
          </Typography>
        ) : (
          <AppointmentCalendar
            appointments={appointments.map(apt => ({
              id: apt.id,
              patientId: apt.patientId,
              patient: {
                id: apt.patientId,
                name: apt.patientName,
                date_of_birth: '',
                gender: 'other' as const,
                contact: {},
                status: 'active',
                registration_completed: false,
                created_at: '',
                updated_at: ''
              },
              doctorId: apt.providerId,
              doctor: {
                id: apt.providerId,
                email: '',
                full_name: apt.provider,
                role: 'doctor' as const,
                isActive: true,
                createdAt: '',
                updatedAt: ''
              },
              title: `${apt.type} - ${apt.patientName}`,
              description: apt.notes || '',
              startTime: `${apt.date}T${apt.time}`,
              endTime: `${apt.date}T${apt.time}`, // Will be calculated based on duration
              status: apt.status.replace('_', '-') as 'scheduled' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show' | 'rescheduled',
              type: apt.type as 'consultation' | 'follow_up' | 'emergency' | 'surgery' | 'therapy' | 'diagnostic' | 'vaccination',
              priority: apt.priority as 'low' | 'medium' | 'high' | 'urgent' | 'emergency',
              location: apt.room || 'Main Hospital',
              notes: apt.notes || '',
              reminders: [],
              createdAt: apt.createdAt,
              updatedAt: apt.updatedAt,
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
            All Appointments ({isLoading ? '...' : filterAppointmentsBySearch(appointments).length})
          </Typography>
          {isLoading ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                <Box sx={{ width: 40, height: 40, animation: 'pulse 1.5s infinite ease-in-out', borderRadius: '50%', bgcolor: 'primary.light' }} />
              </Box>
              <Typography variant="body1" color="text.secondary">
                Loading appointments...
              </Typography>
            </Box>
          ) : error ? (
            <Typography color="error" textAlign="center" sx={{ py: 4 }}>
              Error loading appointments
            </Typography>
          ) : filterAppointmentsBySearch(appointments).length > 0 ? (
            renderListView(filterAppointmentsBySearch(appointments))
          ) : (
            <Typography
              color="text.secondary"
              textAlign="center"
              sx={{ py: 4 }}
            >
              {searchQuery ? 'No appointments match your search' : 'No appointments found'}
            </Typography>
          )}
        </Paper>
      </TabPanel>

      {/* Appointment Scheduler */}
      <AppointmentScheduler
        open={schedulerOpen}
        onClose={() => {
          setSchedulerOpen(false);
          setSelectedAppointmentDate(null);
        }}
        onSubmit={handleAppointmentSubmit}
        patients={transformPatientData(patientsData?.patients || [])}
        providers={transformStaffData(staffData || [])}
        appointmentTypes={appointmentTypesData?.appointment_types || []}
        editingAppointment={editingAppointment}
        loading={isCreating}
        selectedDate={selectedAppointmentDate}
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
