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
        {/* Enhanced Week headers */}
        <Grid container sx={{ mb: 1 }}>
          {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map((day, index) => (
            <Grid size={{ xs: 'grow' }} key={day}>
              <Box 
                p={2} 
                textAlign="center"
                sx={{
                  backgroundColor: 'grey.50',
                  borderRadius: '8px 8px 0 0',
                  borderBottom: '2px solid',
                  borderBottomColor: index === 0 || index === 6 ? 'error.light' : 'primary.light',
                }}
              >
                <Typography 
                  variant="subtitle1" 
                  sx={{ 
                    color: index === 0 || index === 6 ? 'error.main' : 'primary.main',
                    fontWeight: 600,
                    fontSize: '0.9rem',
                  }}
                >
                  {day.slice(0, 3)}
                </Typography>
                <Typography 
                  variant="caption" 
                  sx={{ 
                    color: 'text.secondary',
                    display: { xs: 'none', sm: 'block' },
                    fontSize: '0.75rem',
                  }}
                >
                  {day.slice(3)}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>

        {/* Enhanced Calendar grid */}
        {weeks.map((week, weekIndex) => (
          <Grid container key={weekIndex} sx={{ minHeight: 140, mb: 1 }}>
            {week.map((day, dayIndex) => {
              const dayEvents = calendarEvents.filter(event =>
                isSameDay(event.start, day)
              );
              const isCurrentMonth = isSameMonth(day, currentDate);
              const isTodayDate = isToday(day);
              const isWeekend = dayIndex === 0 || dayIndex === 6;

              return (
                <Grid size={{ xs: 'grow' }} key={day.toISOString()}>
                  <Paper
                    elevation={isTodayDate ? 4 : 1}
                    sx={{
                      height: 140,
                      p: 1.5,
                      cursor: 'pointer',
                      position: 'relative',
                      overflow: 'hidden',
                      background: isTodayDate 
                        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                        : isCurrentMonth 
                          ? 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)'
                          : 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
                      border: isTodayDate ? '2px solid #667eea' : '1px solid #e2e8f0',
                      borderRadius: 2,
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
                        borderColor: isTodayDate ? '#667eea' : 'primary.main',
                        '& .day-number': {
                          transform: 'scale(1.1)',
                        },
                      },
                      '&::before': isTodayDate ? {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
                        pointerEvents: 'none',
                      } : {},
                    }}
                    onClick={() => onNewAppointment(day)}
                  >
                    {/* Day number with enhanced styling */}
                    <Box 
                      sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        mb: 1,
                      }}
                    >
                      <Typography
                        className="day-number"
                        variant="h6"
                        sx={{
                          color: isTodayDate 
                            ? 'white'
                            : isCurrentMonth
                              ? isWeekend ? 'error.main' : 'text.primary'
                              : 'text.disabled',
                          fontWeight: isTodayDate ? 700 : isCurrentMonth ? 600 : 400,
                          fontSize: '1.1rem',
                          transition: 'transform 0.2s ease-in-out',
                          textShadow: isTodayDate ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                        }}
                      >
                        {format(day, 'd')}
                      </Typography>
                      
                      {/* Event count indicator */}
                      {dayEvents.length > 0 && (
                        <Box
                          sx={{
                            backgroundColor: isTodayDate ? 'rgba(255,255,255,0.3)' : 'primary.main',
                            color: isTodayDate ? 'white' : 'white',
                            borderRadius: '50%',
                            width: 20,
                            height: 20,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.7rem',
                            fontWeight: 600,
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                          }}
                        >
                          {dayEvents.length}
                        </Box>
                      )}
                    </Box>

                    {/* Enhanced appointment display */}
                     <Box sx={{ height: 'calc(100% - 40px)', overflow: 'hidden' }}>
                       {dayEvents.slice(0, 3).map((event, index) => {
                         const appointment = event.appointment;
                         const isUrgent = appointment.appointmentType?.toLowerCase().includes('urgent') || 
                                         appointment.appointmentType?.toLowerCase().includes('emergency');
                         const isFollowUp = appointment.appointmentType?.toLowerCase().includes('follow');
                         
                         return (
                           <Box
                             key={event.id}
                             sx={{
                               background: `linear-gradient(135deg, ${event.color} 0%, ${event.color}dd 100%)`,
                               color: 'white',
                               borderRadius: 2,
                               p: 1,
                               mb: 0.5,
                               fontSize: '0.7rem',
                               fontWeight: 500,
                               cursor: 'pointer',
                               position: 'relative',
                               overflow: 'hidden',
                               boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
                               border: isUrgent ? '1px solid #ff6b6b' : '1px solid rgba(255,255,255,0.2)',
                               transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                               '&:hover': {
                                 transform: 'translateX(3px) translateY(-1px)',
                                 boxShadow: '0 6px 20px rgba(0,0,0,0.2)',
                                 '& .appointment-time': {
                                   transform: 'scale(1.05)',
                                 },
                                 '& .status-indicator': {
                                   transform: 'scale(1.1) rotate(5deg)',
                                 },
                               },
                               '&::before': {
                                 content: '""',
                                 position: 'absolute',
                                 left: 0,
                                 top: 0,
                                 bottom: 0,
                                 width: 4,
                                 background: isUrgent 
                                   ? 'linear-gradient(180deg, #ff6b6b 0%, #ff8e8e 100%)'
                                   : 'linear-gradient(180deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.2) 100%)',
                                 borderRadius: '0 2px 2px 0',
                               },
                               '&::after': isUrgent ? {
                                 content: '"!"',
                                 position: 'absolute',
                                 top: 2,
                                 right: 4,
                                 width: 12,
                                 height: 12,
                                 backgroundColor: '#ff4757',
                                 color: 'white',
                                 borderRadius: '50%',
                                 display: 'flex',
                                 alignItems: 'center',
                                 justifyContent: 'center',
                                 fontSize: '0.6rem',
                                 fontWeight: 700,
                                 animation: 'pulse 2s infinite',
                                 '@keyframes pulse': {
                                   '0%': { transform: 'scale(1)', opacity: 1 },
                                   '50%': { transform: 'scale(1.1)', opacity: 0.8 },
                                   '100%': { transform: 'scale(1)', opacity: 1 },
                                 },
                               } : {},
                             }}
                             onClick={(e) => {
                               e.stopPropagation();
                               onAppointmentClick(event.appointment);
                             }}
                             onContextMenu={(e) => handleAppointmentContextMenu(e, event.appointment)}
                           >
                             {/* Time and Patient Info */}
                             <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                               <Typography 
                                 className="appointment-time"
                                 variant="caption" 
                                 sx={{ 
                                   fontWeight: 600,
                                   fontSize: '0.75rem',
                                   textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                                   transition: 'transform 0.2s ease',
                                 }}
                               >
                                 {appointment.time}
                               </Typography>
                               
                               {/* Status indicator */}
                               <Box
                                 className="status-indicator"
                                 sx={{
                                   width: 8,
                                   height: 8,
                                   borderRadius: '50%',
                                   backgroundColor: appointment.status === 'confirmed' ? '#4ade80' :
                                                  appointment.status === 'scheduled' ? '#fbbf24' :
                                                  appointment.status === 'completed' ? '#06b6d4' : '#ef4444',
                                   boxShadow: '0 0 0 2px rgba(255,255,255,0.3)',
                                   transition: 'transform 0.2s ease',
                                 }}
                               />
                             </Box>
                             
                             {/* Patient Name */}
                             <Typography 
                               variant="caption" 
                               sx={{ 
                                 display: 'block',
                                 overflow: 'hidden',
                                 textOverflow: 'ellipsis',
                                 whiteSpace: 'nowrap',
                                 fontWeight: 500,
                                 lineHeight: 1.2,
                                 mb: 0.25,
                                 textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                               }}
                             >
                               {appointment.patientName}
                             </Typography>
                             
                             {/* Appointment Type with Badge */}
                             <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                               <Typography 
                                 variant="caption" 
                                 sx={{ 
                                   overflow: 'hidden',
                                   textOverflow: 'ellipsis',
                                   whiteSpace: 'nowrap',
                                   opacity: 0.9,
                                   fontSize: '0.65rem',
                                   lineHeight: 1,
                                   flex: 1,
                                 }}
                               >
                                 {appointment.appointmentType}
                               </Typography>
                               
                               {/* Type badges */}
                               {isFollowUp && (
                                 <Box
                                   sx={{
                                     backgroundColor: 'rgba(255,255,255,0.2)',
                                     color: 'white',
                                     borderRadius: 0.5,
                                     px: 0.5,
                                     py: 0.25,
                                     fontSize: '0.5rem',
                                     fontWeight: 600,
                                     textTransform: 'uppercase',
                                     letterSpacing: 0.5,
                                   }}
                                 >
                                   F/U
                                 </Box>
                               )}
                             </Box>
                             
                             {/* Shimmer effect overlay */}
                             <Box
                               sx={{
                                 position: 'absolute',
                                 top: 0,
                                 left: '-100%',
                                 width: '100%',
                                 height: '100%',
                                 background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                                 transition: 'left 0.6s',
                                 pointerEvents: 'none',
                               }}
                               className="shimmer-overlay"
                             />
                           </Box>
                         );
                       })}
                      
                      {dayEvents.length > 3 && (
                        <Box
                          sx={{
                            backgroundColor: isTodayDate ? 'rgba(255,255,255,0.2)' : 'grey.100',
                            color: isTodayDate ? 'white' : 'text.secondary',
                            borderRadius: 1,
                            p: 0.5,
                            textAlign: 'center',
                            fontSize: '0.7rem',
                            fontWeight: 500,
                            border: `1px dashed ${isTodayDate ? 'rgba(255,255,255,0.3)' : 'grey.300'}`,
                          }}
                        >
                          +{dayEvents.length - 3} more
                        </Box>
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
            <Grid size={{ xs: 'grow' }} key={day.toISOString()}>
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
                  <Grid size={{ xs: 'grow' }} key={`${day.toISOString()}-${hour}`}>
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
      {/* Enhanced Calendar Header */}
      <Paper 
        elevation={0}
        sx={{ 
          p: 3, 
          mb: 3,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: 3,
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(255,255,255,0.05) 100%)',
            pointerEvents: 'none',
          }
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
          <Box display="flex" alignItems="center" gap={3}>
            <Box>
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 700,
                  textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  mb: 0.5
                }}
              >
                {getViewTitle()}
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  opacity: 0.9,
                  fontSize: '0.9rem'
                }}
              >
                {format(currentDate, 'EEEE, MMMM do, yyyy')}
              </Typography>
            </Box>
            {loading && (
              <CircularProgress 
                size={24} 
                sx={{ color: 'rgba(255,255,255,0.8)' }}
              />
            )}
          </Box>

          <Box display="flex" alignItems="center" gap={2}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => onNewAppointment()}
              sx={{
                backgroundColor: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255,255,255,0.3)',
                color: 'white',
                fontWeight: 600,
                px: 3,
                py: 1,
                borderRadius: 2,
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.3)',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                },
                transition: 'all 0.2s ease-in-out',
              }}
            >
              New Appointment
            </Button>

            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1,
                backgroundColor: 'rgba(255,255,255,0.15)',
                borderRadius: 2,
                p: 0.5,
                backdropFilter: 'blur(10px)',
              }}
            >
              <IconButton 
                onClick={() => navigateDate('prev')}
                sx={{ 
                  color: 'white',
                  '&:hover': { 
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    transform: 'scale(1.1)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                <ChevronLeft />
              </IconButton>
              <Button 
                variant="text" 
                onClick={() => navigateDate('today')}
                sx={{
                  color: 'white',
                  fontWeight: 500,
                  px: 2,
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.2)',
                  },
                }}
              >
                Today
              </Button>
              <IconButton 
                onClick={() => navigateDate('next')}
                sx={{ 
                  color: 'white',
                  '&:hover': { 
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    transform: 'scale(1.1)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                <ChevronRight />
              </IconButton>
            </Box>

            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 0.5,
                backgroundColor: 'rgba(255,255,255,0.15)',
                borderRadius: 2,
                p: 0.5,
                backdropFilter: 'blur(10px)',
              }}
            >
              <Button
                variant={viewMode === 'month' ? 'contained' : 'text'}
                startIcon={<CalendarMonth />}
                onClick={() => setViewMode('month')}
                size="small"
                sx={{
                  color: 'white',
                  backgroundColor: viewMode === 'month' ? 'rgba(255,255,255,0.3)' : 'transparent',
                  fontWeight: 500,
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.2)',
                  },
                }}
              >
                Month
              </Button>
              <Button
                variant={viewMode === 'week' ? 'contained' : 'text'}
                startIcon={<ViewWeek />}
                onClick={() => setViewMode('week')}
                size="small"
                sx={{
                  color: 'white',
                  backgroundColor: viewMode === 'week' ? 'rgba(255,255,255,0.3)' : 'transparent',
                  fontWeight: 500,
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.2)',
                  },
                }}
              >
                Week
              </Button>
              <Button
                variant={viewMode === 'day' ? 'contained' : 'text'}
                startIcon={<ViewDay />}
                onClick={() => setViewMode('day')}
                size="small"
                sx={{
                  color: 'white',
                  backgroundColor: viewMode === 'day' ? 'rgba(255,255,255,0.3)' : 'transparent',
                  fontWeight: 500,
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.2)',
                  },
                }}
              >
                Day
              </Button>
            </Box>
          </Box>
        </Box>

        {/* Enhanced Filters */}
        <Box 
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 3,
            backgroundColor: 'rgba(255,255,255,0.1)',
            borderRadius: 2,
            p: 2,
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.2)',
          }}
        >
          <Box display="flex" alignItems="center" gap={1}>
            <FilterIcon sx={{ color: 'rgba(255,255,255,0.8)' }} />
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', fontWeight: 500 }}>
              Filters:
            </Typography>
          </Box>
          
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel sx={{ color: 'rgba(255,255,255,0.8)' }}>Provider</InputLabel>
            <Select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              label="Provider"
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.3)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.5)',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.7)',
                },
                '& .MuiSvgIcon-root': {
                  color: 'rgba(255,255,255,0.8)',
                },
              }}
            >
              <MenuItem value="all">All Providers</MenuItem>
              {providers.map(provider => (
                <MenuItem key={provider.id} value={provider.id}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Avatar
                      sx={{
                        width: 24,
                        height: 24,
                        backgroundColor: provider.color,
                        fontSize: '0.75rem',
                        fontWeight: 600,
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

          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel sx={{ color: 'rgba(255,255,255,0.8)' }}>Status</InputLabel>
            <Select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              label="Status"
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.3)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.5)',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.7)',
                },
                '& .MuiSvgIcon-root': {
                  color: 'rgba(255,255,255,0.8)',
                },
              }}
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
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                      }}
                    />
                    {status.charAt(0).toUpperCase() + status.slice(1).replace('-', ' ')}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ ml: 'auto' }}>
            <Typography 
              variant="body2" 
              sx={{ 
                color: 'rgba(255,255,255,0.9)',
                fontWeight: 500,
                backgroundColor: 'rgba(255,255,255,0.2)',
                px: 2,
                py: 0.5,
                borderRadius: 1,
                backdropFilter: 'blur(5px)',
              }}
            >
              {calendarEvents.length} appointment{calendarEvents.length !== 1 ? 's' : ''}
            </Typography>
          </Box>
        </Box>
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