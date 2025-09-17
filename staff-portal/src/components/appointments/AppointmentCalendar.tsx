import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Button,
  Chip,
  Tooltip,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  Avatar,
  Divider,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  TextField,
  Stack,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  Today,
  ViewWeek,
  ViewDay,
  CalendarMonth,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  MoreVert as MoreVertIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  addWeeks,
  addMonths,
  isSameDay,
  isSameMonth,
  isToday,
  parseISO,
  addMinutes,
  differenceInMinutes,
  startOfDay,
  endOfDay,
} from 'date-fns';

interface Appointment {
  id: string;
  patientName: string;
  patientId: string;
  providerName: string;
  providerId: string;
  appointmentType: string;
  date: string;
  time: string;
  duration: number;
  status: 'scheduled' | 'confirmed' | 'in-progress' | 'completed' | 'cancelled' | 'no-show';
  priority: 'low' | 'medium' | 'high';
  location: string;
  notes?: string;
  color?: string;
}

interface Provider {
  id: string;
  name: string;
  specialization: string;
  color: string;
}

interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  appointment: Appointment;
  color: string;
}

type ViewMode = 'month' | 'week' | 'day';

interface AppointmentCalendarProps {
  appointments: Appointment[];
  providers: Provider[];
  onAppointmentClick: (appointment: Appointment) => void;
  onAppointmentEdit: (appointment: Appointment) => void;
  onAppointmentDelete: (appointmentId: string) => void;
  onNewAppointment: (date?: Date, providerId?: string) => void;
  loading?: boolean;
  onDateRangeChange?: (start: Date, end: Date) => void;
}

const statusColors = {
  scheduled: '#2196F3',
  confirmed: '#4CAF50',
  'in-progress': '#FF9800',
  completed: '#9C27B0',
  cancelled: '#F44336',
  'no-show': '#795548',
};

const priorityColors = {
  low: '#4CAF50',
  medium: '#FF9800',
  high: '#F44336',
};

export const AppointmentCalendar: React.FC<AppointmentCalendarProps> = ({
  appointments,
  providers,
  onAppointmentClick,
  onAppointmentEdit,
  onAppointmentDelete,
  onNewAppointment,
  loading = false,
  onDateRangeChange,
}) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>('month');
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
    appointment: Appointment;
  } | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    appointment: Appointment | null;
  }>({ open: false, appointment: null });

  // Calculate date range based on view mode
  const dateRange = useMemo(() => {
    let start: Date;
    let end: Date;

    switch (viewMode) {
      case 'month':
        start = startOfWeek(startOfMonth(currentDate));
        end = endOfWeek(endOfMonth(currentDate));
        break;
      case 'week':
        start = startOfWeek(currentDate);
        end = endOfWeek(currentDate);
        break;
      case 'day':
        start = startOfDay(currentDate);
        end = endOfDay(currentDate);
        break;
      default:
        start = startOfWeek(startOfMonth(currentDate));
        end = endOfWeek(endOfMonth(currentDate));
    }

    return { start, end };
  }, [currentDate, viewMode]);

  // Notify parent of date range changes
  useEffect(() => {
    if (onDateRangeChange) {
      onDateRangeChange(dateRange.start, dateRange.end);
    }
  }, [dateRange, onDateRangeChange]);

  // Filter and convert appointments to calendar events
  const calendarEvents = useMemo(() => {
    return appointments
      .filter(appointment => {
        // Filter by provider
        if (selectedProvider !== 'all' && appointment.providerId !== selectedProvider) {
          return false;
        }

        // Filter by status
        if (selectedStatus !== 'all' && appointment.status !== selectedStatus) {
          return false;
        }

        // Filter by date range
        const appointmentDate = parseISO(appointment.date);
        return appointmentDate >= dateRange.start && appointmentDate <= dateRange.end;
      })
      .map(appointment => {
        const appointmentDate = parseISO(appointment.date);
        const [hours, minutes] = appointment.time.split(':').map(Number);
        const start = new Date(appointmentDate);
        start.setHours(hours, minutes, 0, 0);
        const end = addMinutes(start, appointment.duration);

        const provider = providers.find(p => p.id === appointment.providerId);
        const color = appointment.color || provider?.color || statusColors[appointment.status];

        return {
          id: appointment.id,
          title: `${appointment.patientName} - ${appointment.appointmentType}`,
          start,
          end,
          appointment,
          color,
        };
      });
  }, [appointments, providers, selectedProvider, selectedStatus, dateRange]);

  const navigateDate = (direction: 'prev' | 'next' | 'today') => {
    setCurrentDate(prev => {
      switch (direction) {
        case 'prev':
          switch (viewMode) {
            case 'month':
              return addMonths(prev, -1);
            case 'week':
              return addWeeks(prev, -1);
            case 'day':
              return addDays(prev, -1);
            default:
              return prev;
          }
        case 'next':
          switch (viewMode) {
            case 'month':
              return addMonths(prev, 1);
            case 'week':
              return addWeeks(prev, 1);
            case 'day':
              return addDays(prev, 1);
            default:
              return prev;
          }
        case 'today':
          return new Date();
        default:
          return prev;
      }
    });
  };

  const handleAppointmentContextMenu = (event: React.MouseEvent, appointment: Appointment) => {
    event.preventDefault();
    setContextMenu({
      mouseX: event.clientX - 2,
      mouseY: event.clientY - 4,
      appointment,
    });
  };

  const handleContextMenuClose = () => {
    setContextMenu(null);
  };

  const handleDeleteClick = (appointment: Appointment) => {
    setDeleteDialog({ open: true, appointment });
    handleContextMenuClose();
  };

  const handleDeleteConfirm = () => {
    if (deleteDialog.appointment) {
      onAppointmentDelete(deleteDialog.appointment.id);
    }
    setDeleteDialog({ open: false, appointment: null });
  };

  const renderMonthView = () => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart);
    const calendarEnd = endOfWeek(monthEnd);

    const days = [];
    let day = calendarStart;

    while (day <= calendarEnd) {
      days.push(day);
      day = addDays(day, 1);
    }

    const weeks = [];
    for (let i = 0; i < days.length; i += 7) {
      weeks.push(days.slice(i, i + 7));
    }

    return (
      <Box>
        {/* Week headers */}
        <Grid container>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <Grid size={{ xs: true }} key={day}>
              <Box p={1} textAlign="center">
                <Typography variant="subtitle2" color="text.secondary">
                  {day}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>

        {/* Calendar grid */}
        {weeks.map((week, weekIndex) => (
          <Grid container key={weekIndex} sx={{ minHeight: 120 }}>
            {week.map(day => {
              const dayEvents = calendarEvents.filter(event =>
                isSameDay(event.start, day)
              );

              return (
                <Grid size={{ xs: true }} key={day.toISOString()}>
                  <Paper
                    variant="outlined"
                    sx={{
                      height: 120,
                      p: 1,
                      backgroundColor: isToday(day) ? 'primary.50' : 'background.paper',
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                    }}
                    onClick={() => onNewAppointment(day)}
                  >
                    <Typography
                      variant="body2"
                      color={
                        isSameMonth(day, currentDate)
                          ? isToday(day)
                            ? 'primary.main'
                            : 'text.primary'
                          : 'text.disabled'
                      }
                      fontWeight={isToday(day) ? 'bold' : 'normal'}
                    >
                      {format(day, 'd')}
                    </Typography>

                    <Box mt={0.5}>
                      {dayEvents.slice(0, 3).map(event => (
                        <Chip
                          key={event.id}
                          label={event.title}
                          size="small"
                          sx={{
                            backgroundColor: event.color,
                            color: 'white',
                            fontSize: '0.7rem',
                            height: 20,
                            mb: 0.25,
                            display: 'block',
                            '& .MuiChip-label': {
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            },
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            onAppointmentClick(event.appointment);
                          }}
                          onContextMenu={(e) => handleAppointmentContextMenu(e, event.appointment)}
                        />
                      ))}
                      {dayEvents.length > 3 && (
                        <Typography variant="caption" color="text.secondary">
                          +{dayEvents.length - 3} more
                        </Typography>
                      )}
                    </Box>
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        ))}
      </Box>
    );
  };

  const renderWeekView = () => {
    const weekStart = startOfWeek(currentDate);
    const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
    const hours = Array.from({ length: 24 }, (_, i) => i);

    return (
      <Box>
        {/* Day headers */}
        <Grid container>
          <Grid size={{ xs: 1 }}>
            <Box p={1} />
          </Grid>
          {days.map(day => (
            <Grid size={{ xs: true }} key={day.toISOString()}>
              <Box p={1} textAlign="center">
                <Typography variant="subtitle2">
                  {format(day, 'EEE')}
                </Typography>
                <Typography
                  variant="h6"
                  color={isToday(day) ? 'primary.main' : 'text.primary'}
                  fontWeight={isToday(day) ? 'bold' : 'normal'}
                >
                  {format(day, 'd')}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>

        {/* Time grid */}
        <Box sx={{ maxHeight: 600, overflow: 'auto' }}>
          {hours.map(hour => (
            <Grid container key={hour} sx={{ minHeight: 60, borderTop: '1px solid', borderColor: 'divider' }}>
              <Grid size={{ xs: 1 }}>
                <Box p={1} textAlign="right">
                  <Typography variant="caption" color="text.secondary">
                    {format(new Date().setHours(hour, 0, 0, 0), 'h a')}
                  </Typography>
                </Box>
              </Grid>
              {days.map(day => {
                const dayHourEvents = calendarEvents.filter(event => {
                  const eventHour = event.start.getHours();
                  return isSameDay(event.start, day) && eventHour === hour;
                });

                return (
                  <Grid size={{ xs: true }} key={`${day.toISOString()}-${hour}`}>
                    <Box
                      sx={{
                        height: 60,
                        borderLeft: '1px solid',
                        borderColor: 'divider',
                        position: 'relative',
                        cursor: 'pointer',
                        '&:hover': {
                          backgroundColor: 'action.hover',
                        },
                      }}
                      onClick={() => {
                        const clickDate = new Date(day);
                        clickDate.setHours(hour, 0, 0, 0);
                        onNewAppointment(clickDate);
                      }}
                    >
                      {dayHourEvents.map(event => (
                        <Chip
                          key={event.id}
                          label={event.title}
                          size="small"
                          sx={{
                            position: 'absolute',
                            top: 2,
                            left: 2,
                            right: 2,
                            backgroundColor: event.color,
                            color: 'white',
                            fontSize: '0.7rem',
                            '& .MuiChip-label': {
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            },
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            onAppointmentClick(event.appointment);
                          }}
                          onContextMenu={(e) => handleAppointmentContextMenu(e, event.appointment)}
                        />
                      ))}
                    </Box>
                  </Grid>
                );
              })}
            </Grid>
          ))}
        </Box>
      </Box>
    );
  };

  const renderDayView = () => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const dayEvents = calendarEvents.filter(event =>
      isSameDay(event.start, currentDate)
    );

    return (
      <Box>
        <Box p={2} textAlign="center">
          <Typography variant="h5">
            {format(currentDate, 'EEEE, MMMM d, yyyy')}
          </Typography>
        </Box>

        <Box sx={{ maxHeight: 600, overflow: 'auto' }}>
          {hours.map(hour => {
            const hourEvents = dayEvents.filter(event => event.start.getHours() === hour);

            return (
              <Box
                key={hour}
                sx={{
                  display: 'flex',
                  minHeight: 80,
                  borderTop: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ width: 80, p: 1, textAlign: 'right' }}>
                  <Typography variant="caption" color="text.secondary">
                    {format(new Date().setHours(hour, 0, 0, 0), 'h a')}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    flex: 1,
                    borderLeft: '1px solid',
                    borderColor: 'divider',
                    position: 'relative',
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                  onClick={() => {
                    const clickDate = new Date(currentDate);
                    clickDate.setHours(hour, 0, 0, 0);
                    onNewAppointment(clickDate);
                  }}
                >
                  {hourEvents.map((event, index) => (
                    <Card
                      key={event.id}
                      sx={{
                        position: 'absolute',
                        top: 4,
                        left: 4 + (index * 8),
                        right: 4,
                        backgroundColor: event.color,
                        color: 'white',
                        cursor: 'pointer',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onAppointmentClick(event.appointment);
                      }}
                      onContextMenu={(e) => handleAppointmentContextMenu(e, event.appointment)}
                    >
                      <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                        <Typography variant="body2" fontWeight="bold">
                          {format(event.start, 'h:mm a')} - {format(event.end, 'h:mm a')}
                        </Typography>
                        <Typography variant="body2">
                          {event.appointment.patientName}
                        </Typography>
                        <Typography variant="caption">
                          {event.appointment.appointmentType}
                        </Typography>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              </Box>
            );
          })}
        </Box>
      </Box>
    );
  };

  const getViewTitle = () => {
    switch (viewMode) {
      case 'month':
        return format(currentDate, 'MMMM yyyy');
      case 'week':
        const weekStart = startOfWeek(currentDate);
        const weekEnd = endOfWeek(currentDate);
        return `${format(weekStart, 'MMM d')} - ${format(weekEnd, 'MMM d, yyyy')}`;
      case 'day':
        return format(currentDate, 'EEEE, MMMM d, yyyy');
      default:
        return '';
    }
  };

  return (
    <Box>
      {/* Calendar Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="h5">{getViewTitle()}</Typography>
            {loading && <CircularProgress size={20} />}
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => onNewAppointment()}
            >
              New Appointment
            </Button>

            <Divider orientation="vertical" flexItem />

            <IconButton onClick={() => navigateDate('prev')}>
              <ChevronLeft />
            </IconButton>
            <Button variant="outlined" onClick={() => navigateDate('today')}>
              Today
            </Button>
            <IconButton onClick={() => navigateDate('next')}>
              <ChevronRight />
            </IconButton>

            <Divider orientation="vertical" flexItem />

            <Button
              variant={viewMode === 'month' ? 'contained' : 'outlined'}
              startIcon={<CalendarMonth />}
              onClick={() => setViewMode('month')}
            >
              Month
            </Button>
            <Button
              variant={viewMode === 'week' ? 'contained' : 'outlined'}
              startIcon={<ViewWeek />}
              onClick={() => setViewMode('week')}
            >
              Week
            </Button>
            <Button
              variant={viewMode === 'day' ? 'contained' : 'outlined'}
              startIcon={<ViewDay />}
              onClick={() => setViewMode('day')}
            >
              Day
            </Button>
          </Box>
        </Box>

        {/* Filters */}
        <Stack direction="row" spacing={2} alignItems="center">
          <FilterIcon color="action" />
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Provider</InputLabel>
            <Select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              label="Provider"
            >
              <MenuItem value="all">All Providers</MenuItem>
              {providers.map(provider => (
                <MenuItem key={provider.id} value={provider.id}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Avatar
                      sx={{
                        width: 20,
                        height: 20,
                        backgroundColor: provider.color,
                        fontSize: '0.7rem',
                      }}
                    >
                      {provider.name.charAt(0)}
                    </Avatar>
                    Dr. {provider.name}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              label="Status"
            >
              <MenuItem value="all">All Status</MenuItem>
              {Object.keys(statusColors).map(status => (
                <MenuItem key={status} value={status}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        backgroundColor: statusColors[status as keyof typeof statusColors],
                      }}
                    />
                    {status.charAt(0).toUpperCase() + status.slice(1).replace('-', ' ')}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Typography variant="body2" color="text.secondary">
            {calendarEvents.length} appointment{calendarEvents.length !== 1 ? 's' : ''}
          </Typography>
        </Stack>
      </Paper>

      {/* Calendar Content */}
      <Paper sx={{ p: 2 }}>
        {viewMode === 'month' && renderMonthView()}
        {viewMode === 'week' && renderWeekView()}
        {viewMode === 'day' && renderDayView()}
      </Paper>

      {/* Context Menu */}
      <Menu
        open={contextMenu !== null}
        onClose={handleContextMenuClose}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        <MenuItem
          onClick={() => {
            if (contextMenu) {
              onAppointmentClick(contextMenu.appointment);
            }
            handleContextMenuClose();
          }}
        >
          <PersonIcon sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (contextMenu) {
              onAppointmentEdit(contextMenu.appointment);
            }
            handleContextMenuClose();
          }}
        >
          <EditIcon sx={{ mr: 1 }} />
          Edit Appointment
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            if (contextMenu) {
              handleDeleteClick(contextMenu.appointment);
            }
          }}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1 }} />
          Delete Appointment
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, appointment: null })}
      >
        <DialogTitle>Delete Appointment</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the appointment with{' '}
            <strong>{deleteDialog.appointment?.patientName}</strong>?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone. The patient will be notified of the cancellation.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, appointment: null })}>
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AppointmentCalendar;