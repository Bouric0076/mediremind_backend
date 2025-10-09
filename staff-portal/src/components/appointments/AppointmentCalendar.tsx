import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Button,
  Chip,
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
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  ViewWeek,
  ViewDay,
  CalendarMonth,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
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
  startOfDay,
  endOfDay,
} from 'date-fns';
import type { Appointment } from '../../types';
import type { ExternalCalendarEvent, SyncConflict } from '../../types/calendar';

interface Provider {
  id: string;
  name: string;
  specialization: string;
  email: string;
  availability: string[];
  color?: string;
}
import calendarIntegrationService from '../../services/calendarIntegrationService';
import SyncStatusIndicator from '../calendar/SyncStatusIndicator';
import ConflictResolutionDialog from '../calendar/ConflictResolutionDialog';
import SyncNotificationCenter, { useSyncNotifications } from '../calendar/SyncNotificationCenter';


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
  const [showExternalEvents, setShowExternalEvents] = useState(false);
  const [externalEvents, setExternalEvents] = useState<ExternalCalendarEvent[]>([]);
  const [loadingExternal, setLoadingExternal] = useState(false);
  const [conflicts, setConflicts] = useState<SyncConflict[]>([]);
  const [showConflictDialog, setShowConflictDialog] = useState(false);
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
    appointment: Appointment;
  } | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    appointment: Appointment | null;
  }>({ open: false, appointment: null });

  // Sync notifications hook
  const {
    notifications,
    dismissNotification,
    dismissAll,
    notifySyncStart,
    notifySyncComplete,
    notifySyncError,
    notifyWarning,
  } = useSyncNotifications();

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

  // Load external calendar events with conflict detection
  useEffect(() => {
    const loadExternalEvents = async () => {
      if (!showExternalEvents) {
        setExternalEvents([]);
        setConflicts([]);
        return;
      }

      try {
        setLoadingExternal(true);
        notifySyncStart();
        
        // Check if user has any calendar integrations before making API calls
        const integrations = await calendarIntegrationService.getIntegrationsOriginal();
        if (integrations.length === 0) {
          console.log('No calendar integrations found. Skipping external events fetch.');
          setExternalEvents([]);
          setConflicts([]);
          notifySyncComplete(0, 0);
          return;
        }
        
        // Fetch events from all active integrations
        const allEvents: ExternalCalendarEvent[] = [];
        for (const integration of integrations) {
          if (integration.status === 'active') {
            try {
              const events = await calendarIntegrationService.getExternalEvents(
                integration.id,
                format(dateRange.start, 'yyyy-MM-dd'),
                format(dateRange.end, 'yyyy-MM-dd')
              );
              allEvents.push(...events);
            } catch (error) {
              console.error(`Failed to fetch events for integration ${integration.id}:`, error);
            }
          }
        }
        
        setExternalEvents(allEvents);

        // Check for conflicts between external events and internal appointments
        const detectedConflicts = await calendarIntegrationService.detectConflicts(
          appointments,
          allEvents
        );
        
        setConflicts(detectedConflicts);
        
        if (detectedConflicts.length > 0) {
          notifyWarning(
            'Sync Conflicts Detected',
            `Found ${detectedConflicts.length} conflicts between internal appointments and external events.`,
            [`${detectedConflicts.length} conflicts need resolution`]
          );
          setShowConflictDialog(true);
        }

        notifySyncComplete(allEvents.length, detectedConflicts.length);
      } catch (error) {
        console.error('Error loading external events:', error);
        setExternalEvents([]);
        setConflicts([]);
        notifySyncError(
          error instanceof Error ? error.message : 'Unknown sync error',
          () => loadExternalEvents()
        );
      } finally {
        setLoadingExternal(false);
      }
    };

    loadExternalEvents();
  }, [showExternalEvents, dateRange, appointments]);

  // Filter and convert appointments to calendar events
  const calendarEvents = useMemo(() => {
    // Internal appointments
    const internalEvents = appointments
      .filter(appointment => {
        // Filter by provider
        if (selectedProvider !== 'all' && appointment.doctorId !== selectedProvider) {
          return false;
        }

        // Filter by status
        if (selectedStatus !== 'all' && appointment.status !== selectedStatus) {
          return false;
        }

        // Filter by date range - check if startTime exists and is valid
        if (!appointment.startTime || !appointment.endTime) {
          console.warn('Appointment missing startTime or endTime:', appointment);
          return false;
        }

        try {
          const appointmentDate = parseISO(appointment.startTime);
          return appointmentDate >= dateRange.start && appointmentDate <= dateRange.end;
        } catch (error) {
          console.warn('Invalid appointment date format:', appointment.startTime, error);
          return false;
        }
      })
      .map(appointment => {
        try {
          const start = parseISO(appointment.startTime);
          const end = parseISO(appointment.endTime);

          const provider = providers.find(p => p.id === appointment.doctorId);
          const color = provider?.color || statusColors[appointment.status as keyof typeof statusColors];

          return {
            id: appointment.id,
            title: `${appointment.patient.name} - ${appointment.type}`,
            start,
            end,
            appointment,
            color,
            isExternal: false,
          };
        } catch (error) {
          console.error('Error parsing appointment dates:', appointment, error);
          return null;
        }
      })
      .filter(Boolean); // Remove any null entries from failed date parsing

    // External calendar events
    const externalCalendarEvents = showExternalEvents ? externalEvents
      .filter(event => {
        // Check if required fields exist and are valid
        if (!event.start_time || !event.end_time) {
          console.warn('External event missing start_time or end_time:', event);
          return false;
        }

        try {
          const eventStart = parseISO(event.start_time);
          return eventStart >= dateRange.start && eventStart <= dateRange.end;
        } catch (error) {
          console.warn('Invalid external event date format:', event.start_time, error);
          return false;
        }
      })
      .map(event => {
        try {
          return {
            id: `external-${event.id}`,
            title: `🔗 ${event.title}`,
            start: parseISO(event.start_time),
            end: parseISO(event.end_time),
            externalEvent: event,
            color: '#9E9E9E', // Gray color for external events
            isExternal: true,
          };
        } catch (error) {
          console.error('Error parsing external event dates:', event, error);
          return null;
        }
      })
      .filter(Boolean) : [];

    return [...internalEvents, ...externalCalendarEvents];
  }, [appointments, providers, selectedProvider, selectedStatus, dateRange, externalEvents, showExternalEvents]);

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

  // Conflict resolution handlers
  const handleConflictResolve = async (conflictId: string, resolution: 'keep_internal' | 'keep_external' | 'merge') => {
    try {
      await calendarIntegrationService.resolveConflict(conflictId, resolution);
      
      // Remove resolved conflict from state
      setConflicts(prev => prev.filter(c => c.id !== conflictId));
      
      // Refresh external events to reflect changes
      const integrations = await calendarIntegrationService.getIntegrationsOriginal();
      const allEvents: ExternalCalendarEvent[] = [];
      for (const integration of integrations) {
        if (integration.status === 'active') {
          try {
            const events = await calendarIntegrationService.getExternalEvents(
              integration.id,
              format(dateRange.start, 'yyyy-MM-dd'),
              format(dateRange.end, 'yyyy-MM-dd')
            );
            allEvents.push(...events);
          } catch (error) {
            console.error(`Failed to fetch events for integration ${integration.id}:`, error);
          }
        }
      }
      setExternalEvents(allEvents);
      
      notifySyncComplete(allEvents.length, conflicts.length - 1);
    } catch (error) {
      notifySyncError(
        error instanceof Error ? error.message : 'Failed to resolve conflict'
      );
    }
  };

  const handleResolveAllConflicts = async (resolution: 'keep_internal' | 'keep_external' | 'merge') => {
    try {
      await Promise.all(
        conflicts.map(conflict => 
          calendarIntegrationService.resolveConflict(conflict.id, resolution)
        )
      );
      
      // Clear all conflicts
      setConflicts([]);
      
      // Refresh external events
      const integrations = await calendarIntegrationService.getIntegrationsOriginal();
      const allEvents: ExternalCalendarEvent[] = [];
      for (const integration of integrations) {
        if (integration.status === 'active') {
          try {
            const events = await calendarIntegrationService.getExternalEvents(
              integration.id,
              format(dateRange.start, 'yyyy-MM-dd'),
              format(dateRange.end, 'yyyy-MM-dd')
            );
            allEvents.push(...events);
          } catch (error) {
            console.error(`Failed to fetch events for integration ${integration.id}:`, error);
          }
        }
      }
      setExternalEvents(allEvents);
      
      notifySyncComplete(allEvents.length, 0);
    } catch (error) {
      notifySyncError(
        error instanceof Error ? error.message : 'Failed to resolve conflicts'
      );
    }
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
                event && event.start && isSameDay(event.start, day)
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
                       {dayEvents.slice(0, 3).map((event) => {
                         // Check if event exists
                         if (!event) return null;
                         
                         // Check if this is an internal appointment or external event
                         const isInternalAppointment = 'appointment' in event;
                         const appointment = isInternalAppointment ? event.appointment : null;
                         
                         const isUrgent = appointment?.type?.toLowerCase().includes('urgent') || 
                                         appointment?.type?.toLowerCase().includes('emergency');
                         const isFollowUp = appointment?.type?.toLowerCase().includes('follow');
                         
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
                               if (isInternalAppointment && appointment) {
                                 onAppointmentClick(appointment);
                               }
                             }}
                             onContextMenu={(e) => {
                               if (isInternalAppointment && appointment) {
                                 handleAppointmentContextMenu(e, appointment);
                               }
                             }}
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
                                 {appointment?.startTime ? format(new Date(appointment.startTime), 'h:mm a') : ''}
                               </Typography>
                               
                               {/* Status indicator */}
                               <Box
                                 className="status-indicator"
                                 sx={{
                                   width: 8,
                                   height: 8,
                                   borderRadius: '50%',
                                   backgroundColor: appointment?.status === 'confirmed' ? '#4ade80' :
                                                  appointment?.status === 'scheduled' ? '#fbbf24' :
                                                  appointment?.status === 'completed' ? '#06b6d4' : '#ef4444',
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
                               {appointment?.patient?.name}
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
                                 {appointment?.type}
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
                  if (!event || !event.start) return false;
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
                      {dayHourEvents.map(event => {
                        if (!event) return null;
                        
                        const isInternalAppointment = 'appointment' in event;
                        const appointment = isInternalAppointment ? event.appointment : null;
                        
                        return (
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
                              if (isInternalAppointment && appointment) {
                                onAppointmentClick(appointment);
                              }
                            }}
                            onContextMenu={(e) => {
                              if (isInternalAppointment && appointment) {
                                handleAppointmentContextMenu(e, appointment);
                              }
                            }}
                          />
                        );
                      })}
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
      event && event.start && isSameDay(event.start, currentDate)
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
            const hourEvents = dayEvents.filter(event => event && event.start && event.start.getHours() === hour);

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
                  {hourEvents.map((event, index) => {
                    if (!event) return null;
                    
                    const isInternalAppointment = 'appointment' in event;
                    const appointment = isInternalAppointment ? event.appointment : null;
                    
                    return (
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
                          if (isInternalAppointment && appointment) {
                            onAppointmentClick(appointment);
                          }
                        }}
                        onContextMenu={(e) => {
                          if (isInternalAppointment && appointment) {
                            handleAppointmentContextMenu(e, appointment);
                          }
                        }}
                      >
                      <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                          <Typography variant="body2" fontWeight="bold">
                            {format(event.start, 'h:mm a')} - {format(event.end, 'h:mm a')}
                          </Typography>
                          <Typography variant="body2">
                            {isInternalAppointment && appointment ? appointment.patient?.name : event.title}
                          </Typography>
                          <Typography variant="caption">
                            {isInternalAppointment && appointment ? appointment.type : 'External Event'}
                          </Typography>
                        </CardContent>
                      </Card>
                    );
                  })}
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
            <SyncStatusIndicator />
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

          <FormControlLabel
            control={
              <Switch
                checked={showExternalEvents}
                onChange={(e) => setShowExternalEvents(e.target.checked)}
                sx={{
                  '& .MuiSwitch-switchBase.Mui-checked': {
                    color: 'white',
                  },
                  '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                    backgroundColor: 'rgba(255,255,255,0.5)',
                  },
                  '& .MuiSwitch-track': {
                    backgroundColor: 'rgba(255,255,255,0.3)',
                  },
                }}
              />
            }
            label={
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', fontWeight: 500 }}>
                  External Events
                </Typography>
                {loadingExternal && (
                  <CircularProgress size={16} sx={{ color: 'rgba(255,255,255,0.8)' }} />
                )}
              </Box>
            }
            sx={{ color: 'rgba(255,255,255,0.9)' }}
          />

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
              {calendarEvents.filter(e => e && !e.isExternal).length} appointment{calendarEvents.filter(e => e && !e.isExternal).length !== 1 ? 's' : ''}
              {showExternalEvents && externalEvents.length > 0 && (
                <span style={{ opacity: 0.8 }}>
                  {' '}+ {externalEvents.length} external
                </span>
              )}
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
            <strong>{deleteDialog.appointment?.patient?.name}</strong>?
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

      {/* Conflict Resolution Dialog */}
      <ConflictResolutionDialog
        open={showConflictDialog}
        conflicts={conflicts}
        onClose={() => setShowConflictDialog(false)}
        onResolve={handleConflictResolve}
        onResolveAll={handleResolveAllConflicts}
      />

      {/* Sync Notification Center */}
      <SyncNotificationCenter
        notifications={notifications}
        onDismiss={dismissNotification}
        onDismissAll={dismissAll}
        onRetrySync={() => {
          // Trigger a manual sync by toggling external events
          setShowExternalEvents(false);
          setTimeout(() => setShowExternalEvents(true), 100);
        }}
      />
    </Box>
  );
};

export default AppointmentCalendar;