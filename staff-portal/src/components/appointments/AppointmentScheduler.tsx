import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Autocomplete,
  FormHelperText,
  Card,
  CardContent,

  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  DatePicker,
  TimePicker,
  LocalizationProvider,
} from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import {
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  Notes as NotesIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { format, isAfter, isBefore, parseISO, isSameDay } from 'date-fns';

interface Patient {
  id: string;
  name: string;
  email: string;
  phone: string;
  dateOfBirth: string;
}

interface Provider {
  id: string;
  name: string;
  specialization: string;
  email: string;
  availability: string[];
}

interface AppointmentType {
  id: string;
  name: string;
  description: string;
  code: string;
  default_duration: number;
  buffer_time: number;
  base_cost: string;
  requires_preparation: boolean;
  preparation_instructions: string;
  requires_fasting: boolean;
  is_active: boolean;
  color_code: string;
  created_at: string;
  updated_at: string;
}

interface TimeSlot {
  time: string;
  available: boolean;
  reason?: string;
  end_time?: string;
  duration?: number;
}

interface AppointmentFormData {
  patientId: string;
  providerId: string;
  appointmentTypeId: string;
  date: Date | null;
  time: Date | null;
  duration: number;
  location: string;
  notes: string;
  priority: 'low' | 'medium' | 'high';
  reminderPreferences: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
}

interface AppointmentSchedulerProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (appointmentData: AppointmentFormData) => Promise<void>;
  editingAppointment?: any;
  patients: Patient[];
  providers: Provider[];
  appointmentTypes: AppointmentType[];
  loading?: boolean;
  selectedDate?: Date | null;
}

const defaultFormData: AppointmentFormData = {
  patientId: '',
  providerId: '',
  appointmentTypeId: '',
  date: null,
  time: null,
  duration: 30,
  location: 'Main Hospital',
  notes: '',
  priority: 'medium',
  reminderPreferences: {
    email: true,
    sms: true,
    push: true,
  },
};

export const AppointmentScheduler: React.FC<AppointmentSchedulerProps> = ({
  open,
  onClose,
  onSubmit,
  editingAppointment,
  patients,
  providers,
  appointmentTypes,
  loading: externalLoading = false,
  selectedDate,
}) => {
  const [formData, setFormData] = useState<AppointmentFormData>(defaultFormData);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [checkingAvailability, setCheckingAvailability] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string>('');

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (open) {
      if (editingAppointment) {
        setFormData({
          patientId: editingAppointment.patientId || '',
          providerId: editingAppointment.providerId || '',
          appointmentTypeId: editingAppointment.appointmentTypeId || '',
          date: editingAppointment.date ? parseISO(editingAppointment.date) : null,
          time: editingAppointment.time ? parseISO(`2000-01-01T${editingAppointment.time}`) : null,
          duration: editingAppointment.duration || 30,
          location: editingAppointment.location || 'Main Hospital',
          notes: editingAppointment.notes || '',
          priority: editingAppointment.priority || 'medium',
          reminderPreferences: editingAppointment.reminderPreferences || {
            email: true,
            sms: true,
            push: true,
          },
        });
      } else {
        setFormData(defaultFormData);
      }
      setErrors({});
      setSubmitError('');
    }
  }, [open, editingAppointment]);

  // Auto-set date when selectedDate is provided from calendar click
  useEffect(() => {
    if (selectedDate && open && !editingAppointment) {
      setFormData(prev => ({
        ...prev,
        date: selectedDate,
      }));
    }
  }, [selectedDate, open, editingAppointment]);

  // Check availability when provider, date, or duration changes
  useEffect(() => {
    if (formData.providerId && formData.date) {
      // Generate default slots immediately for better UX
      const defaultSlots = generateDefaultTimeSlots(formData.date, formData.providerId);
      setAvailableSlots(defaultSlots);
      
      // Then check with backend for real availability
      checkProviderAvailability();
    } else {
      setAvailableSlots([]);
    }
  }, [formData.providerId, formData.date, formData.duration]);

  // Generate default time slots (30-minute intervals from 8 AM to 6 PM)
  const generateDefaultTimeSlots = (selectedDate: Date, providerId: string): TimeSlot[] => {
    const slots: TimeSlot[] = [];
    const provider = providers.find(p => p.id === providerId);
    
    // Default working hours: 8 AM to 6 PM
    let startHour = 8;
    let endHour = 18;
    
    // Use provider's availability if available
    if (provider?.availability && provider.availability.length > 0) {
      const availability = provider.availability[0]; // Use first availability slot
      const [start, end] = availability.split('-');
      if (start && end) {
        startHour = parseInt(start.split(':')[0]);
        endHour = parseInt(end.split(':')[0]);
      }
    }

    // Generate 30-minute slots
    for (let hour = startHour; hour < endHour; hour++) {
      for (let minute = 0; minute < 60; minute += 30) {
        const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        
        // Check if this time is in the past for today
        const slotDateTime = new Date(selectedDate);
        slotDateTime.setHours(hour, minute, 0, 0);
        const isInPast = isBefore(slotDateTime, new Date());
        
        slots.push({
          time: timeString,
          available: !isInPast,
          reason: isInPast ? 'Time has passed' : undefined
        });
      }
    }
    
    return slots;
  };

  const checkProviderAvailability = async () => {
    if (!formData.providerId || !formData.date) return;

    setCheckingAvailability(true);
    try {
      const dateStr = format(formData.date, 'yyyy-MM-dd');
      const excludeParam = editingAppointment ? `&exclude_appointment_id=${editingAppointment.id}` : '';
      const response = await fetch(
        `/api/appointments/time-slots/?provider_id=${formData.providerId}&date=${dateStr}&duration=${formData.duration}${excludeParam}`,
        {
          headers: {
            'Authorization': `Token ${localStorage.getItem('token')}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        // Transform the enhanced API response to match our TimeSlot interface
        const transformedSlots = data.available_slots?.map((slot: any) => ({
          time: slot.time,
          available: slot.available,
          reason: slot.reason,
          end_time: slot.end_time,
          duration: slot.duration
        })) || [];
        
        setAvailableSlots(transformedSlots);
        
        // Store additional data for better UX
        if (data.time_periods) {
          // Could use this for better grouping in the future
          console.log('Time periods available:', data.time_periods);
        }
        
        if (data.unavailable_slots && data.unavailable_slots.length > 0) {
          console.log('Unavailable slots:', data.unavailable_slots);
        }
      } else {
        console.error('Failed to check availability');
        // Fallback to generated slots if API fails
        const defaultSlots = generateDefaultTimeSlots(formData.date, formData.providerId);
        setAvailableSlots(defaultSlots);
      }
    } catch (error) {
      console.error('Error checking availability:', error);
      // Fallback to generated slots if API fails
      const defaultSlots = generateDefaultTimeSlots(formData.date, formData.providerId);
      setAvailableSlots(defaultSlots);
    } finally {
      setCheckingAvailability(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Patient validation
    if (!formData.patientId) {
      newErrors.patientId = 'Patient is required';
    } else {
      const selectedPatient = patients.find(p => p.id === formData.patientId);
      if (!selectedPatient) {
        newErrors.patientId = 'Selected patient is not valid';
      }
    }

    // Provider validation
    if (!formData.providerId) {
      newErrors.providerId = 'Provider is required';
    } else {
      const selectedProvider = providers.find(p => p.id === formData.providerId);
      if (!selectedProvider) {
        newErrors.providerId = 'Selected provider is not valid';
      }
    }

    // Appointment type validation
    if (!formData.appointmentTypeId) {
      newErrors.appointmentTypeId = 'Appointment type is required';
    } else {
      const selectedType = appointmentTypes.find(t => t.id === formData.appointmentTypeId);
      if (!selectedType) {
        newErrors.appointmentTypeId = 'Selected appointment type is not valid';
      }
    }

    // Date validation
    if (!formData.date) {
      newErrors.date = 'Date is required';
    } else {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (isBefore(formData.date, today)) {
        newErrors.date = 'Date cannot be in the past';
      }
      
      // Check if date is too far in the future (e.g., more than 1 year)
      const oneYearFromNow = new Date();
      oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1);
      if (isAfter(formData.date, oneYearFromNow)) {
        newErrors.date = 'Date cannot be more than 1 year in the future';
      }
    }

    // Time validation
    if (!formData.time) {
      newErrors.time = 'Time is required';
    } else if (formData.date && formData.providerId) {
      // Check if selected time is available
      const timeString = format(formData.time, 'HH:mm');
      const selectedSlot = availableSlots.find(slot => slot.time === timeString);
      
      if (!selectedSlot) {
        newErrors.time = 'Selected time is not available';
      } else if (!selectedSlot.available) {
        newErrors.time = selectedSlot.reason || 'Selected time is not available';
      }
      
      // Check if appointment is in the past for today
      if (formData.date && isSameDay(formData.date, new Date())) {
        const appointmentDateTime = new Date(formData.date);
        appointmentDateTime.setHours(formData.time.getHours(), formData.time.getMinutes());
        
        if (isBefore(appointmentDateTime, new Date())) {
          newErrors.time = 'Appointment time cannot be in the past';
        }
      }
    }

    // Location validation
    if (!formData.location.trim()) {
      newErrors.location = 'Location is required';
    } else if (formData.location.trim().length < 3) {
      newErrors.location = 'Location must be at least 3 characters';
    }

    // Duration validation
    if (!formData.duration || formData.duration < 15 || formData.duration > 240) {
      newErrors.duration = 'Duration must be between 15 and 240 minutes';
    } else if (formData.duration % 15 !== 0) {
      newErrors.duration = 'Duration must be in 15-minute increments';
    }

    // Priority validation
    if (!formData.priority) {
      newErrors.priority = 'Priority is required';
    }

    // Notes validation (optional but with length limit)
    if (formData.notes && formData.notes.length > 500) {
      newErrors.notes = 'Notes cannot exceed 500 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setSubmitError('');

    try {
      await onSubmit(formData);
      onClose();
    } catch (error: any) {
      setSubmitError(error.message || 'Failed to schedule appointment');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof AppointmentFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const handleReminderPreferenceChange = (type: keyof AppointmentFormData['reminderPreferences'], value: boolean) => {
    setFormData(prev => ({
      ...prev,
      reminderPreferences: {
        ...prev.reminderPreferences,
        [type]: value,
      },
    }));
  };

  const getSelectedPatient = () => patients.find(p => p.id === formData.patientId);
  const getSelectedProvider = () => providers.find(p => p.id === formData.providerId);


  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: '80vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <ScheduleIcon color="primary" />
            <Typography variant="h6">
              {editingAppointment ? 'Edit Appointment' : 'Schedule New Appointment'}
            </Typography>
          </Box>
        </DialogTitle>

        <DialogContent dividers>
          <Grid container spacing={3}>
            {/* Patient Selection */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Autocomplete
                options={patients}
                getOptionLabel={(option) => `${option.name} (${option.email})`}
                value={getSelectedPatient() || null}
                onChange={(_, value) => handleInputChange('patientId', value?.id || '')}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Patient"
                    error={!!errors.patientId}
                    helperText={errors.patientId}
                    InputProps={{
                      ...params.InputProps,
                      startAdornment: <PersonIcon color="action" sx={{ mr: 1 }} />,
                    }}
                  />
                )}
                renderOption={(props, option) => {
                  const { key, ...otherProps } = props;
                  return (
                    <Box component="li" key={key} {...otherProps}>
                      <Box>
                        <Typography variant="body1">{option.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {option.email} • {option.phone}
                        </Typography>
                      </Box>
                    </Box>
                  );
                }}
              />
            </Grid>

            {/* Provider Selection */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Autocomplete
                options={providers}
                getOptionLabel={(option) => `Dr. ${option.name} (${option.specialization})`}
                value={getSelectedProvider() || null}
                onChange={(_, value) => handleInputChange('providerId', value?.id || '')}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Provider"
                    error={!!errors.providerId}
                    helperText={errors.providerId}
                  />
                )}
                renderOption={(props, option) => {
                  const { key, ...otherProps } = props;
                  return (
                    <Box component="li" key={key} {...otherProps}>
                      <Box>
                        <Typography variant="body1">Dr. {option.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {option.specialization}
                        </Typography>
                      </Box>
                    </Box>
                  );
                }}
              />
            </Grid>

            {/* Appointment Type */}
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth error={!!errors.appointmentTypeId}>
                <InputLabel>Appointment Type</InputLabel>
                <Select
                  value={formData.appointmentTypeId}
                  onChange={(e) => {
                    const selectedType = appointmentTypes.find(t => t.id === e.target.value);
                    handleInputChange('appointmentTypeId', e.target.value);
                    if (selectedType) {
                      handleInputChange('duration', selectedType.default_duration);
                    }
                  }}
                  label="Appointment Type"
                >
                  {appointmentTypes.map((type) => (
                    <MenuItem key={type.id} value={type.id}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                        <Box display="flex" alignItems="center" gap={1}>
                          <Box
                            sx={{
                              width: 12,
                              height: 12,
                              borderRadius: '50%',
                              backgroundColor: type.color_code,
                              border: '1px solid rgba(0,0,0,0.1)'
                            }}
                          />
                          <Typography variant="body1" fontWeight="medium">
                            {type.name}
                          </Typography>
                        </Box>
                        <Chip
                           size="small"
                           label={`${type.default_duration} mins`}
                           sx={{ 
                             backgroundColor: type.color_code + '20',
                             color: type.color_code,
                             fontWeight: 'medium',
                             border: `1px solid ${type.color_code}40`
                           }}
                         />
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
                {errors.appointmentTypeId && (
                  <FormHelperText>{errors.appointmentTypeId}</FormHelperText>
                )}
              </FormControl>
            </Grid>

            {/* Priority */}
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={formData.priority}
                  onChange={(e) => handleInputChange('priority', e.target.value)}
                  label="Priority"
                >
                  <MenuItem value="low">
                    <Chip label="Low" color="default" size="small" />
                  </MenuItem>
                  <MenuItem value="medium">
                    <Chip label="Medium" color="warning" size="small" />
                  </MenuItem>
                  <MenuItem value="high">
                    <Chip label="High" color="error" size="small" />
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Date Selection */}
            <Grid size={{ xs: 12, md: 6 }}>
              <DatePicker
                label="Appointment Date"
                value={formData.date}
                onChange={(date) => handleInputChange('date', date)}
                minDate={new Date()}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    error: !!errors.date,
                    helperText: errors.date,
                  },
                }}
              />
            </Grid>

            {/* Time Selection */}
            <Grid size={{ xs: 12, md: 6 }}>
              <TimePicker
                label="Appointment Time"
                value={formData.time}
                onChange={(time) => handleInputChange('time', time)}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    error: !!errors.time,
                    helperText: errors.time,
                  },
                }}
              />
            </Grid>

            {/* Duration */}
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Duration (minutes)"
                type="number"
                value={formData.duration}
                onChange={(e) => handleInputChange('duration', parseInt(e.target.value) || 30)}
                error={!!errors.duration}
                helperText={errors.duration}
                inputProps={{ min: 15, max: 240, step: 15 }}
              />
            </Grid>

            {/* Available Time Slots */}
            {formData.providerId && formData.date && (
              <Grid size={{ xs: 12 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <ScheduleIcon color="primary" />
                      <Typography variant="h6">Available Time Slots</Typography>
                      {checkingAvailability && <CircularProgress size={20} />}
                      <IconButton
                        size="small"
                        onClick={checkProviderAvailability}
                        disabled={checkingAvailability}
                      >
                        <RefreshIcon />
                      </IconButton>
                    </Box>

                    {availableSlots.length > 0 ? (
                      <Box>
                        {/* Group slots by time periods */}
                        {[
                          { label: 'Morning', start: 6, end: 12 },
                          { label: 'Afternoon', start: 12, end: 17 },
                          { label: 'Evening', start: 17, end: 22 }
                        ].map(period => {
                          const periodSlots = availableSlots.filter(slot => {
                            const hour = parseInt(slot.time.split(':')[0]);
                            return hour >= period.start && hour < period.end;
                          });

                          if (periodSlots.length === 0) return null;

                          return (
                            <Box key={period.label} sx={{ mb: 2 }}>
                              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                                {period.label}
                              </Typography>
                              <Grid container spacing={1}>
                                {periodSlots.map((slot) => {
                                  const isSelected = formData.time && format(formData.time, 'HH:mm') === slot.time;
                                  const startTime = format(new Date(`2000-01-01T${slot.time}`), 'h:mm a');
                                  const endTime = slot.end_time ? format(new Date(`2000-01-01T${slot.end_time}`), 'h:mm a') : '';
                                  const duration = slot.duration || formData.duration;
                                  
                                  return (
                                    <Grid key={slot.time}>
                                      <Tooltip
                                        title={
                                          <Box>
                                            <Typography variant="body2">
                                              {slot.available ? 'Available' : slot.reason || 'Not available'}
                                            </Typography>
                                            {slot.available && (
                                              <Typography variant="caption" display="block">
                                                Duration: {duration} minutes
                                                {endTime && ` (until ${endTime})`}
                                              </Typography>
                                            )}
                                          </Box>
                                        }
                                        arrow
                                      >
                                        <Chip
                                          label={
                                            <Box sx={{ textAlign: 'center' }}>
                                              <Typography variant="body2" component="div">
                                                {startTime}
                                              </Typography>
                                              {slot.available && duration && (
                                                <Typography variant="caption" color="text.secondary">
                                                  {duration}min
                                                </Typography>
                                              )}
                                            </Box>
                                          }
                                          onClick={() => {
                                            if (slot.available) {
                                              const timeDate = new Date(`2000-01-01T${slot.time}`);
                                              handleInputChange('time', timeDate);
                                            }
                                          }}
                                          color={slot.available ? (isSelected ? 'success' : 'primary') : 'default'}
                                          variant={isSelected ? 'filled' : 'outlined'}
                                          disabled={!slot.available}
                                          icon={
                                            slot.available 
                                              ? (isSelected ? <CheckIcon /> : undefined)
                                              : <WarningIcon />
                                          }
                                          sx={{
                                            cursor: slot.available ? 'pointer' : 'not-allowed',
                                            opacity: slot.available ? 1 : 0.5,
                                            minWidth: '80px',
                                            height: 'auto',
                                            '& .MuiChip-label': {
                                              padding: '8px 12px',
                                            },
                                            ...(isSelected && {
                                              boxShadow: 2,
                                              transform: 'scale(1.05)',
                                            }),
                                            ...(slot.available && !isSelected && {
                                              '&:hover': {
                                                transform: 'scale(1.02)',
                                                boxShadow: 1,
                                              },
                                            }),
                                          }}
                                        />
                                      </Tooltip>
                                    </Grid>
                                  );
                                })}
                              </Grid>
                            </Box>
                          );
                        })}
                      </Box>
                    ) : (
                      <Typography color="text.secondary">
                        {checkingAvailability ? 'Checking availability...' : 'No available slots found'}
                      </Typography>
                    )}

                    {errors.time && (
                      <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                        {errors.time}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Location */}
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Location"
                value={formData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                error={!!errors.location}
                helperText={errors.location}
                InputProps={{
                  startAdornment: <LocationIcon color="action" sx={{ mr: 1 }} />,
                }}
              />
            </Grid>

            {/* Notes */}
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => handleInputChange('notes', e.target.value)}
                InputProps={{
                  startAdornment: <NotesIcon color="action" sx={{ mr: 1, alignSelf: 'flex-start', mt: 1 }} />,
                }}
              />
            </Grid>

            {/* Reminder Preferences */}
            <Grid size={{ xs: 12 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Reminder Preferences
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <input
                          type="checkbox"
                          checked={formData.reminderPreferences.email}
                          onChange={(e) => handleReminderPreferenceChange('email', e.target.checked)}
                        />
                        <Typography>Email Reminders</Typography>
                      </Box>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <input
                          type="checkbox"
                          checked={formData.reminderPreferences.sms}
                          onChange={(e) => handleReminderPreferenceChange('sms', e.target.checked)}
                        />
                        <Typography>SMS Reminders</Typography>
                      </Box>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <input
                          type="checkbox"
                          checked={formData.reminderPreferences.push}
                          onChange={(e) => handleReminderPreferenceChange('push', e.target.checked)}
                        />
                        <Typography>Push Notifications</Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Appointment Summary */}
            {formData.patientId && formData.providerId && formData.date && formData.time && (
              <Grid size={{ xs: 12 }}>
                <Card variant="outlined" sx={{ backgroundColor: 'primary.50' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                      Appointment Summary
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemIcon>
                          <PersonIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Patient"
                          secondary={getSelectedPatient()?.name}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <PersonIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Provider"
                          secondary={`Dr. ${getSelectedProvider()?.name}`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <ScheduleIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Date & Time"
                          secondary={`${format(formData.date, 'EEEE, MMMM d, yyyy')} at ${format(formData.time, 'h:mm a')}`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <LocationIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Location"
                          secondary={formData.location}
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Error Display */}
            {submitError && (
              <Grid size={{ xs: 12 }}>
                <Alert severity="error">{submitError}</Alert>
              </Grid>
            )}
          </Grid>
        </DialogContent>

        <DialogActions sx={{ p: 3 }}>
          <Button onClick={onClose} disabled={externalLoading || loading}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={externalLoading || loading || checkingAvailability}
            startIcon={externalLoading || loading ? <CircularProgress size={20} /> : null}
          >
            {externalLoading || loading ? 'Scheduling...' : editingAppointment ? 'Update Appointment' : 'Schedule Appointment'}
          </Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
};

export default AppointmentScheduler;